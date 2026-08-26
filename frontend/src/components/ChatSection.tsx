'use client';

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage, ChatResponse } from '@/types';
import { sendMessage } from '@/lib/api';
import { Send, Bot, User, ShieldCheck, Mail, Hash } from 'lucide-react';

export const ChatSection: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('session_demo_1');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `Hello! 👋 Welcome to **TechMania AI Customer Support**.\n\nI can assist you with:\n• 🛍 **Product Prices, Discounts & Stock Availability**\n• 📦 **Order Tracking & Shipping Status**\n• 📄 **Company Policy Rules**\n• 💳 **Refund Requests & Automated Email Confirmations**\n\nHow can I help you today?`,
      timestamp: '09:00 AM',
    },
  ]);
  const [inputValue, setInputValue] = useState<string>('');
  const [customerEmail, setCustomerEmail] = useState<string>('');
  const [orderIdHint, setOrderIdHint] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      customer_email: customerEmail,
      order_id: orderIdHint,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setIsLoading(true);

    try {
      const res: ChatResponse = await sendMessage(
        text,
        sessionId,
        customerEmail || undefined,
        orderIdHint || undefined
      );

      const botMsg: ChatMessage = {
        role: 'assistant',
        content: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: res.intent,
        order_id: res.detected_order_id,
        customer_email: res.detected_email,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ Sorry, I encountered an issue connecting to the Python FastAPI backend. Please check that `main.py` is running on `http://localhost:8000`.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = () => {
    const newId = `session_${Math.random().toString(36).substring(2, 9)}`;
    setSessionId(newId);
    setMessages([
      {
        role: 'assistant',
        content: `Hello! 👋 Welcome to **TechMania AI Customer Support**.\n\nI can assist you with:\n• 🛍 **Product Prices, Discounts & Stock Availability**\n• 📦 **Order Tracking & Shipping Status**\n• 📄 **Company Policy Rules**\n• 💳 **Refund Requests & Automated Email Confirmations**\n\nHow can I help you today?`,
        timestamp: '09:00 AM',
      },
    ]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <div className="lg:col-span-1 space-y-4">
        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Customer Details</span>
            </h3>
            <button
              onClick={handleNewSession}
              className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline font-medium"
            >
              <span>New Session</span>
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 flex items-center gap-1">
                <Mail className="w-3.5 h-3.5 text-cyan-400" /> Customer Email
              </label>
              <input
                type="email"
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                placeholder="Enter email (optional)"
                className="w-full px-3 py-1.5 rounded-lg glass-input text-xs"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 flex items-center gap-1">
                <Hash className="w-3.5 h-3.5 text-cyan-400" /> Target Order ID
              </label>
              <input
                type="text"
                value={orderIdHint}
                onChange={(e) => setOrderIdHint(e.target.value.toUpperCase())}
                placeholder="Enter Order ID (optional)"
                className="w-full px-3 py-1.5 rounded-lg glass-input text-xs font-mono uppercase"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="lg:col-span-3 glass-panel rounded-2xl border border-slate-800 flex flex-col h-[650px] shadow-2xl overflow-hidden">
        <div className="px-6 py-3.5 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">
                TechMania Support Assistant
              </h2>
            </div>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div key={idx} className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    isUser
                      ? 'bg-gradient-to-tr from-cyan-600 to-blue-600 text-white'
                      : 'bg-slate-800 border border-slate-700 text-cyan-400'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                  isUser
                    ? 'bg-gradient-to-r from-cyan-600/90 to-cyan-700/90 text-white shadow-lg shadow-cyan-900/20 rounded-tr-none'
                    : 'glass-card border border-slate-700/60 text-slate-200 rounded-tl-none'
                }`}>
                  <div className="prose prose-invert max-w-none text-sm leading-relaxed font-normal">
                    <ReactMarkdown
                      components={{
                        strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 my-2">{children}</ul>,
                        li: ({ children }) => <li className="text-slate-200">{children}</li>,
                        code: ({ children }) => <code className="bg-slate-900 text-cyan-300 font-mono text-xs px-1.5 py-0.5 rounded border border-slate-700">{children}</code>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  <div suppressHydrationWarning className={`text-[10px] mt-2 text-right ${isUser ? 'text-cyan-200/70' : 'text-slate-500'}`}>
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400">
                <Bot className="w-4 h-4 animate-bounce" />
              </div>
              <div className="glass-card rounded-2xl px-4 py-3 border border-slate-700/60 text-slate-400 text-xs flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                Thinking...
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              id="input-chat-message"
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about products, order status, policy, or request a refund..."
              className="flex-1 px-4 py-3 rounded-xl glass-input text-sm placeholder-slate-500"
            />
            <button
              id="btn-send-message"
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-500 text-white font-medium text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-lg shadow-cyan-600/30"
            >
              <span>Send</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
