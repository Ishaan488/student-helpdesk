"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth, getAuthToken, removeAuthToken } from "@/lib/api";
import { Send, Bot, User, LogOut, Loader2, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I am your College Placement Intelligence Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!getAuthToken()) {
      router.push("/login");
    }
  }, [router]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleLogout = () => {
    removeAuthToken();
    router.push("/login");
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const response = await fetchWithAuth("/chat/message", {
        method: "POST",
        body: JSON.stringify({ message: userMsg })
      });

      setMessages(prev => [...prev, { role: "assistant", content: response.response }]);
    } catch (error: any) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${error.message || "Failed to process request."}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      
      {/* Sidebar (Optional, keeping it clean and minimal) */}
      <div className="hidden md:flex w-64 flex-col bg-white border-r border-slate-200">
        <div className="p-4 border-b border-slate-200 flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-slate-900 flex items-center justify-center text-white">
            <Sparkles size={16} />
          </div>
          <span className="font-medium tracking-tight">Intelligence Desk</span>
        </div>
        <div className="flex-1 p-4">
          <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-3">Capabilities</p>
          <ul className="space-y-2 text-sm text-slate-600">
            <li>• Eligibility Checks</li>
            <li>• Upcoming Drives</li>
            <li>• Company Facts</li>
          </ul>
        </div>
        <div className="p-4 border-t border-slate-200">
          <button 
            onClick={handleLogout}
            className="flex items-center text-sm text-slate-600 hover:text-slate-900 transition-colors w-full"
          >
            <LogOut size={16} className="mr-2" />
            Sign out
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        
        {/* Mobile Header */}
        <div className="md:hidden p-4 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-slate-900" />
            <span className="font-medium">Intelligence Desk</span>
          </div>
          <button onClick={handleLogout} className="text-slate-600">
            <LogOut size={18} />
          </button>
        </div>

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 max-w-3xl mx-auto ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-slate-200 text-slate-700" : "bg-slate-900 text-white"}`}>
                {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`flex-1 rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                msg.role === "user" 
                  ? "bg-slate-100 text-slate-900 ml-12" 
                  : "bg-white border border-slate-200 text-slate-800 shadow-sm mr-12 whitespace-pre-wrap"
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-4 max-w-3xl mx-auto">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl px-5 py-3.5 flex items-center gap-2 shadow-sm">
                <Loader2 size={16} className="animate-spin text-slate-400" />
                <span className="text-sm text-slate-500">Agent is analyzing records...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-slate-200">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about placement drives, eligibility, or companies..."
              className="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition-all text-sm"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-2 p-1.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 disabled:hover:bg-slate-900 transition-colors"
            >
              <Send size={16} />
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[11px] text-slate-400">Agentic responses are based on deterministic database records.</span>
          </div>
        </div>

      </div>
    </div>
  );
}
