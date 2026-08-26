import { ChatResponse, Product, Order, AuditLog, SystemHealth } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<SystemHealth | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  customerEmail?: string,
  orderId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      customer_email: customerEmail,
      order_id: orderId,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Server error' }));
    throw new Error(err.detail || 'Failed to send message');
  }

  return await res.json();
}

export async function fetchChatHistory(sessionId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.messages || [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

export async function fetchProducts(): Promise<Product[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/products`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.products || [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

export async function fetchOrders(): Promise<Order[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/orders`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.orders || [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

export async function fetchLogs(): Promise<AuditLog[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/logs`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.logs || [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

export async function uploadPolicyDocx(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/policy/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload error' }));
    throw new Error(err.detail || 'Failed to upload policy document');
  }

  return await res.json();
}

export async function reindexPolicy() {
  const res = await fetch(`${API_BASE_URL}/policy/reindex`, {
    method: 'POST',
  });
  return await res.json();
}
