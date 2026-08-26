import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from zoneinfo import ZoneInfo
from config import settings

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.SENDER_EMAIL or "support@techmania.com"
        self.logs_dir = os.path.join(settings.BASE_DIR, "email_logs")
        os.makedirs(self.logs_dir, exist_ok=True)

    def send_refund_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: str,
        product_name: str,
        refund_amount: float,
        refund_reason: str,
        is_eligible: bool = True
    ) -> bool:
        if is_eligible:
            subject = f"TechMania Refund Approved & Details Required - Order #{order_id}"
            badge_html = '<div class="badge badge-success">✓ Refund Approved - Policy Verified</div>'
            policy_summary = (
                f"Great news! Your refund request for Order <strong>#{order_id}</strong> has been evaluated "
                f"and <strong>APPROVED</strong> according to the TechMania Customer Return & Refund Policy."
            )
            bank_request_html = f"""
            <div class="bank-box">
              <h3>🏦 Action Required: Please Provide Your Bank & Contact Details</h3>
              <p>To transfer your refund of <strong>PKR {refund_amount:,.2f}</strong>, please reply to this email (<strong>{self.sender_email}</strong>) or send your details in the chat portal with the following information:</p>
              <ul>
                <li><strong>Bank Name:</strong> (e.g. Meezan Bank, HBL, Allied Bank, etc.)</li>
                <li><strong>Account Title / Full Name:</strong></li>
                <li><strong>Account Number / IBAN:</strong></li>
                <li><strong>Contact Phone Number:</strong></li>
              </ul>
              <p style="font-size: 13px; color: #1e40af; margin-bottom: 0;"><em>Once received, our finance team will credit the refund within 1-3 business days.</em></p>
            </div>
            """
        else:
            subject = f"TechMania Refund Request Update - Order #{order_id}"
            badge_html = '<div class="badge badge-error">❌ Refund Request Declined</div>'
            policy_summary = (
                f"We have evaluated your refund request for Order <strong>#{order_id}</strong> against "
                f"the TechMania 30-Day Money-Back Guarantee Policy."
            )
            bank_request_html = """
            <div class="info-box">
              <h3>ℹ️ Policy Assistance & Support Options</h3>
              <p>Under TechMania terms, standard refunds are restricted to requests within 30 days of delivery. However, if your product arrived damaged or is covered under manufacturer warranty, our support team can assist you with a replacement or repair!</p>
            </div>
            """

        asia_tz = ZoneInfo("Asia/Karachi")
        timestamp = datetime.now(asia_tz).strftime("%B %d, %Y at %I:%M %p PKT")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #0e7490, #0284c7); padding: 30px; text-align: center; color: white; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-bottom: 20px; }}
            .badge-success {{ background: #dcfce7; color: #15803d; }}
            .badge-error {{ background: #fee2e2; color: #b91c1c; }}
            .table-details {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .table-details td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}
            .table-details td.label {{ font-weight: bold; color: #64748b; width: 40%; }}
            .table-details td.value {{ color: #0f172a; text-align: right; }}
            .bank-box {{ background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 20px; border-radius: 10px; margin: 20px 0; color: #1e3a8a; }}
            .bank-box h3 {{ margin-top: 0; font-size: 16px; color: #1e40af; }}
            .bank-box ul {{ margin: 10px 0; padding-left: 20px; }}
            .bank-box li {{ margin-bottom: 6px; }}
            .info-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .info-box h3 {{ margin-top: 0; font-size: 16px; color: #334155; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>TechMania Support</h1>
              <p>Official Refund Notification & Policy Evaluation</p>
            </div>
            <div class="content">
              {badge_html}
              <p>Dear <strong>{customer_name or 'Valued Customer'}</strong>,</p>
              <p>{policy_summary}</p>
              
              <table class="table-details">
                <tr>
                  <td class="label">Order ID:</td>
                  <td class="value">#{order_id}</td>
                </tr>
                <tr>
                  <td class="label">Product:</td>
                  <td class="value">{product_name}</td>
                </tr>
                <tr>
                  <td class="label">Refund Amount:</td>
                  <td class="value"><strong style="color: #0e7490; font-size: 18px;">PKR {refund_amount:,.2f}</strong></td>
                </tr>
                <tr>
                  <td class="label">Evaluation Date:</td>
                  <td class="value">{timestamp}</td>
                </tr>
                <tr>
                  <td class="label">Policy Notes:</td>
                  <td class="value">{refund_reason}</td>
                </tr>
              </table>

              {bank_request_html}

              <p>If you have any questions, feel free to reply directly to this email (<strong>{self.sender_email}</strong>) or reach out to TechMania Support.</p>
              <p>Warm regards,<br><strong>TechMania Customer Support Team</strong></p>
            </div>
            <div class="footer">
              TechMania Inc. • Official Customer Support • {self.sender_email}
            </div>
          </div>
        </body>
        </html>
        """
        
        log_filename = f"email_{order_id}_{int(datetime.now().timestamp())}.html"
        log_filepath = os.path.join(self.logs_dir, log_filename)
        try:
            with open(log_filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception:
            pass

        if settings.has_smtp:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.sender_email
                msg["To"] = customer_email
                msg.attach(MIMEText(html_content, "html"))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.sender_email, customer_email, msg.as_string())
                return True
            except Exception as e:
                print(f"SMTP Dispatch Notice ({e}). Email logged to file.")
                return False
        else:
            return True

email_service = EmailService()
