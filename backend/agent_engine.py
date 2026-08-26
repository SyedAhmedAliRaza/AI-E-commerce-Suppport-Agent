import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import settings
from services.chroma_service import chroma_service
from services.policy_service import policy_service
from services.sheets_service import sheets_service, safe_float
from services.email_service import email_service

def clean_markdown_for_sheets(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', text, flags=re.DOTALL)
    clean = re.sub(r'\*(.*?)\*', r'\1', clean, flags=re.DOTALL)
    clean = re.sub(r'`([^`]+)`', r'\1', clean)
    clean = clean.replace('*', '')
    return clean.strip()

class AgentEngine:
    def __init__(self):
        try:
            policy_service.load_and_index_policy()
        except Exception as e:
            print(f"Policy indexing notice: {e}")

    def process_message(
        self,
        user_message: str,
        session_id: str,
        customer_email: Optional[str] = None,
        order_id_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        chroma_service.store_chat_message(
            session_id=session_id,
            role="user",
            content=user_message,
            customer_email=customer_email or "",
            order_id=order_id_hint or ""
        )

        history = chroma_service.get_conversation_history(session_id, limit=5)

        detected_order_id = order_id_hint or self._extract_order_id(user_message, history)
        detected_email = customer_email or self._extract_email(user_message, history)

        intent = self._classify_intent(user_message)

        response_text = ""
        action_taken = "NONE"
        refund_details = None

        if intent == "REFUND_REQUEST":
            res = self._handle_refund_workflow(
                user_message=user_message,
                order_id=detected_order_id,
                email=detected_email,
                session_id=session_id
            )
            response_text = res["response_text"]
            action_taken = res["action_taken"]
            refund_details = res.get("refund_details")

        elif intent == "PRODUCT_QUERY":
            response_text = self._handle_product_query(user_message)
            action_taken = "PRODUCT_SEARCH"

        elif intent == "ORDER_STATUS":
            response_text = self._handle_order_status(detected_order_id, detected_email)
            action_taken = "ORDER_LOOKUP"

        elif intent == "POLICY_INQUIRY":
            response_text = self._handle_policy_inquiry(user_message)
            action_taken = "POLICY_RAG_SEARCH"

        else:
            response_text = self._handle_general_support(user_message, history)
            action_taken = "GENERAL_RESPONSE"

        chroma_service.store_chat_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
            customer_email=detected_email or "",
            order_id=detected_order_id or "",
            intent=intent
        )

        sheets_service.log_interaction(
            customer_email=detected_email or "anonymous",
            order_id=detected_order_id or "N/A",
            query=user_message,
            ai_response=clean_markdown_for_sheets(response_text),
            refund_eligibility=refund_details.get("eligibility", "N/A") if refund_details else "N/A",
            refund_action=action_taken
        )

        return {
            "session_id": session_id,
            "response": response_text,
            "intent": intent,
            "action_taken": action_taken,
            "detected_order_id": detected_order_id,
            "detected_email": detected_email,
            "refund_details": refund_details
        }

    def _classify_intent(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["refund", "return", "money back", "broken", "damaged", "defective", "send back", "cancel order"]):
            return "REFUND_REQUEST"
        if any(w in t for w in ["price", "cost", "discount", "stock", "available", "how much", "buy", "headphones", "keyboard", "monitor", "mouse", "specs"]):
            return "PRODUCT_QUERY"
        if any(w in t for w in ["order status", "where is my order", "tracking", "shipped", "delivery", "ord-"]):
            return "ORDER_STATUS"
        if any(w in t for w in ["policy", "warranty", "rules", "shipping cost", "how many days", "guarantee"]):
            return "POLICY_INQUIRY"
        return "GENERAL_SUPPORT"

    def _extract_order_id(self, text: str, history: List[Dict[str, Any]]) -> Optional[str]:
        match = re.search(r'ORD-\d{4}', text, re.IGNORECASE)
        if match:
            return match.group(0).upper()
        for msg in reversed(history):
            if msg.get("order_id"):
                return msg["order_id"]
            m = re.search(r'ORD-\d{4}', msg.get("content", ""), re.IGNORECASE)
            if m:
                return m.group(0).upper()
        return None

    def _extract_email(self, text: str, history: List[Dict[str, Any]]) -> Optional[str]:
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if match:
            return match.group(0).lower()
        for msg in reversed(history):
            if msg.get("customer_email"):
                return msg["customer_email"]
            m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', msg.get("content", ""))
            if m:
                return m.group(0).lower()
        return None

    def _handle_refund_workflow(
        self,
        user_message: str,
        order_id: Optional[str],
        email: Optional[str],
        session_id: str
    ) -> Dict[str, Any]:
        if not order_id:
            return {
                "response_text": "I can certainly help you with your return or refund request! Could you please provide your **Order ID** (e.g. `ORD-1001`) and the email address associated with the purchase?",
                "action_taken": "AWAITING_ORDER_ID",
                "refund_details": {"eligibility": "PENDING_INFO"}
            }

        order = sheets_service.lookup_order(order_id)
        if not order:
            return {
                "response_text": f"I checked our order database but could not find Order **#{order_id}**. Please double-check the Order ID or provide the customer email used during checkout.",
                "action_taken": "ORDER_NOT_FOUND",
                "refund_details": {"eligibility": "NOT_FOUND"}
            }

        order_status = str(order.get("Status", "")).upper()
        order_date_str = str(order.get("Order Date", ""))
        cust_name = order.get("Customer Name", "Valued Customer")
        cust_email = email or order.get("Customer Email", "")
        product_name = order.get("Product Name", "TechMania Electronics")
        total_paid = safe_float(order.get("Total Paid", 0))

        if order_status == "REFUND_APPROVED":
            return {
                "response_text": (
                    f"Order **#{order_id}** ({product_name}) has already been **APPROVED for a full refund** of **PKR {total_paid:,.2f}**.\n\n"
                    f"📧 An official confirmation email was sent to `{cust_email}` from `{email_service.sender_email}`.\n\n"
                    f"🏦 If you have not submitted your payout details yet, please provide your **Bank Name**, **Account Title**, **Account Number / IBAN**, and **Phone Number**."
                ),
                "action_taken": "ALREADY_REFUNDED",
                "refund_details": {"eligibility": "ALREADY_REFUNDED", "amount": total_paid}
            }

        policy_context = policy_service.get_policy_context_for_query(f"refund return rules 30 day {user_message}")

        days_since_order = 0
        try:
            o_date = datetime.strptime(order_date_str, "%Y-%m-%d")
            days_since_order = (datetime.now() - o_date).days
        except Exception:
            days_since_order = 10

        is_damaged_claim = any(w in user_message.lower() for w in ["damaged", "broken", "defective", "doa", "connector", "scratched"])

        is_eligible = False
        reasons = []

        if is_damaged_claim:
            is_eligible = True
            reasons.append("Item reported as damaged/defective upon arrival (TechMania 100% replacement/refund guarantee).")
        elif days_since_order <= 30:
            is_eligible = True
            reasons.append(f"Order delivered {days_since_order} days ago, which is within the TechMania 30-day money-back guarantee window.")
        else:
            is_eligible = False
            reasons.append(f"Order delivered {days_since_order} days ago, exceeding the 30-day policy return window.")

        reason_str = "; ".join(reasons)
        email_sent = email_service.send_refund_confirmation(
            customer_email=cust_email,
            customer_name=cust_name,
            order_id=order_id,
            product_name=product_name,
            refund_amount=total_paid,
            refund_reason=reason_str,
            is_eligible=is_eligible
        )

        if is_eligible:
            sheets_service.update_order_status(order_id, "REFUND_APPROVED")

            resp_text = (
                f"🎉 **Refund Approved for Order #{order_id}!**\n\n"
                f"• **Product**: {product_name}\n"
                f"• **Refund Amount**: **PKR {total_paid:,.2f}**\n"
                f"• **Status**: Updated to `REFUND_APPROVED` in system records.\n"
                f"• **Policy Evaluation**: According to TechMania return policy, your order is **ELIGIBLE** for a refund ({reasons[0]}).\n\n"
                f"📧 We have sent an official confirmation email to **{cust_email}** from `{email_service.sender_email}`.\n\n"
                f"🏦 **Action Required to Process Your Payout**:\n"
                f"Please reply to the email or reply directly here with your bank transfer details:\n"
                f"1. **Bank Name**\n"
                f"2. **Account Title / Full Name**\n"
                f"3. **Account Number / IBAN**\n"
                f"4. **Contact Phone Number**"
            )
            return {
                "response_text": resp_text,
                "action_taken": "REFUND_APPROVED_AND_EMAILED",
                "refund_details": {
                    "eligibility": "ELIGIBLE",
                    "amount": total_paid,
                    "order_id": order_id,
                    "customer_email": cust_email,
                    "reasons": reasons
                }
            }
        else:
            resp_text = (
                f"❌ **Refund Request Policy Update for Order #{order_id}**\n\n"
                f"• **Product**: {product_name}\n"
                f"• **Order Date**: {order_date_str} ({days_since_order} days ago)\n"
                f"• **Policy Evaluation**: Under TechMania standard return policy, returns must be initiated within **30 calendar days** of delivery. This order is **INELIGIBLE** for a money-back refund as it exceeds the 30-day window.\n\n"
                f"📧 An official email notification explaining the policy evaluation has been sent to **{cust_email}** from `{email_service.sender_email}`.\n\n"
                f"If your item arrived damaged or defective out-of-the-box, please let us know so we can assist under our hardware warranty!"
            )
            return {
                "response_text": resp_text,
                "action_taken": "REFUND_DECLINED_POLICY_EXPIRED",
                "refund_details": {
                    "eligibility": "INELIGIBLE",
                    "order_id": order_id,
                    "reasons": reasons
                }
            }

    def _generate_with_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        if not settings.has_gemini:
            return None
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            candidate_models = [
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-3.6-flash"
            ]
            
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(system_instruction=system_instruction)

            for model_name in candidate_models:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    if res and res.text:
                        return res.text.strip()
                except Exception:
                    continue
        except Exception as e:
            print(f"Gemini generation notice: {e}")
        return None

    def _handle_product_query(self, query: str) -> str:
        products = sheets_service.search_products(query)
        if not products:
            products = sheets_service.get_all_products()[:3]
            
        res = "🛍 **TechMania Product Catalog Information:**\n\n"
        for p in products[:4]:
            price = safe_float(p.get("Price", 0))
            disc = safe_float(p.get("Discount Percent", 0))
            final_price = price * (1.0 - disc / 100.0) if disc > 0 else price
            
            disc_str = f" 🔥 *(Save {disc:.0f}% off - regular PKR {price:,.2f})*" if disc > 0 else ""
            res += f"• **{p.get('Name')}** (`{p.get('Product ID')}`)\n"
            res += f"  - **Price**: **PKR {final_price:,.2f}**{disc_str}\n"
            res += f"  - **Stock Availability**: {p.get('Stock Quantity', 0)} units in stock\n"
            res += f"  - **Description**: {p.get('Description')}\n\n"
            
        ai_polished = self._generate_with_gemini(
            prompt=f"User asked: '{query}'\nHere is our product data:\n{res}\nFormat this information into a clear, enthusiastic, customer-friendly support response.",
            system_instruction="You are an helpful AI customer support representative for TechMania Electronics."
        )
        return ai_polished if ai_polished else res

    def _handle_order_status(self, order_id: Optional[str], email: Optional[str]) -> str:
        if not order_id:
            return "Please provide your **Order ID** (e.g. `ORD-1002`) so I can check the shipping and delivery status in our system."
            
        order = sheets_service.lookup_order(order_id, email)
        if not order:
            return f"I searched our database for Order **#{order_id}** but could not find a matching record. Please check the ID and try again."
            
        status = order.get("Status", "PROCESSING")
        status_icon = "🚚" if status == "SHIPPED" else "📦" if status == "DELIVERED" else "⏳"
        total_paid = safe_float(order.get("Total Paid", 0))
        
        return (
            f"📦 **Order Status for #{order_id}:**\n\n"
            f"• **Customer**: {order.get('Customer Name')}\n"
            f"• **Product**: {order.get('Product Name')}\n"
            f"• **Order Date**: {order.get('Order Date')}\n"
            f"• **Current Status**: {status_icon} **{status}**\n"
            f"• **Tracking Number**: `{order.get('Tracking Number', 'PENDING')}`\n"
            f"• **Total Amount**: PKR {total_paid:,.2f}"
        )

    def _handle_policy_inquiry(self, query: str) -> str:
        hits = chroma_service.search_policy(query, n_results=2)
        if not hits:
            default_resp = "TechMania offers a 30-day money-back guarantee on all eligible electronics in original packaging, plus 100% free returns for damaged/defective products!"
            ai_resp = self._generate_with_gemini(
                prompt=f"User query: {query}\nProvide a friendly response about TechMania store policy: {default_resp}",
                system_instruction="You are TechMania AI Support Agent."
            )
            return ai_resp if ai_resp else default_resp
            
        res = "📋 **TechMania Official Policy Details (Retrieved from Policy Doc):**\n\n"
        for hit in hits:
            res += f"**{hit['section']}**\n{hit['text']}\n\n"
            
        ai_resp = self._generate_with_gemini(
            prompt=f"User question: '{query}'\nPolicy context from official document:\n{res}\nSynthesize this into a clear, precise, friendly customer answer.",
            system_instruction="You are TechMania AI Support Agent."
        )
        return ai_resp if ai_resp else res

    def _handle_general_support(self, query: str, history: List[Dict[str, Any]]) -> str:
        fallback = (
            f"Hello! 👋 Welcome to **TechMania AI Support**. How can I help you today?\n\n"
            f"I can assist you with:\n"
            f"1. 🛍 **Product Prices, Discounts & Stock** (e.g., *'What is the price of Wireless Headphones?'*)\n"
            f"2. 📦 **Order Tracking & Status** (e.g., *'What is the status of ORD-1003?'*)\n"
            f"3. 📄 **Company Policy Queries** (e.g., *'What is your return policy?'*)\n"
            f"4. 💳 **Processing Refund Requests** (e.g., *'I want a refund for ORD-1001'*)"
        )
        ai_resp = self._generate_with_gemini(
            prompt=f"Customer message: '{query}'\nProvide a friendly welcome and offer assistance with products, order status, policies, and refunds at TechMania.",
            system_instruction="You are TechMania AI Support Assistant powered by Gemini."
        )
        return ai_resp if ai_resp else fallback

agent_engine = AgentEngine()
