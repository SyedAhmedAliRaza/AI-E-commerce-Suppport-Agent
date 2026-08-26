export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  intent?: string;
  order_id?: string;
  customer_email?: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  intent: string;
  action_taken: string;
  detected_order_id?: string;
  detected_email?: string;
  refund_details?: {
    eligibility: string;
    amount?: number;
    order_id?: string;
    customer_email?: string;
    reasons?: string[];
  };
}

export interface Product {
  'Product ID': string;
  Name: string;
  Category: string;
  Price: number;
  'Discount Percent': number;
  'Stock Quantity': number;
  Description: string;
}

export interface Order {
  'Order ID': string;
  'Customer Name': string;
  'Customer Email': string;
  'Product ID': string;
  'Product Name': string;
  'Order Date': string;
  Status: string;
  Quantity: number;
  'Total Paid': number;
  'Tracking Number': string;
}

export interface AuditLog {
  'Interaction ID': string;
  Timestamp: string;
  'Customer Email': string;
  'Order ID': string;
  'Query / Request': string;
  'AI Response Summary': string;
  'Refund Eligibility': string;
  'Refund Action Taken': string;
}

export interface SystemHealth {
  status: string;
  company: string;
  chroma_db_status: string;
  chroma_policy_chunks: number;
  chroma_chat_messages: number;
  use_live_sheets: boolean;
  has_smtp: boolean;
  has_gemini: boolean;
}
