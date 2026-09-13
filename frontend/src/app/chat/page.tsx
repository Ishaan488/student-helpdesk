"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth, getAuthToken, removeAuthToken } from "@/lib/api";
import { Send, Bot, User, LogOut, Loader2, Sparkles, Activity, GitMerge, Database, BrainCircuit, ArrowDown, ChevronRight, X, Clock, Zap, MessageSquare, Plus } from "lucide-react";
import Link from "next/link";

interface Message {
  role: "user" | "assistant" | "human" | "ai";
  content: string;
}

interface Thread {
  id: string;
  title: string;
  summary: string | null;
  created_at: string;
}

const CodeBlock = ({ title, content }: { title?: string, content: any }) => (
  <div className="mt-3 text-[11px] font-mono bg-[#09090b] text-emerald-400 rounded-md overflow-hidden border border-slate-800 shadow-inner">
    {title && (
      <div className="px-3 py-1.5 bg-[#18181b] border-b border-slate-800 text-slate-400 font-sans font-medium text-xs flex items-center gap-1.5">
        <ChevronRight size={12} /> {title}
      </div>
    )}
    <div className="p-3 overflow-y-auto max-h-60">
      <pre className="whitespace-pre-wrap leading-relaxed">
        {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
      </pre>
    </div>
  </div>
);

const Badge = ({ label, value, icon: Icon }: { label: string, value: string, icon?: any }) => (
  <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-medium mr-2 mb-2">
    {Icon && <Icon size={12} className="text-indigo-400" />}
    <span className="text-indigo-400 opacity-70 uppercase tracking-wider text-[10px]">{label}</span> 
    {value}
  </span>
);

const Node = ({ active, visited, icon: Icon, label, description, logData, renderLog }: { active: boolean, visited: boolean, icon: any, label: string, description?: string, logData?: any, renderLog?: (data: any) => React.ReactNode }) => (
  <div className="flex flex-col gap-2">
    <div className={`relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-500 ${
      active 
        ? "bg-indigo-50 border-indigo-200 shadow-md transform scale-105 z-10" 
        : visited
          ? "bg-white border-indigo-100 shadow-sm"
          : "bg-white border-slate-200 opacity-60"
    }`}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-500 flex-shrink-0 ${
        active 
          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-200" 
          : visited
            ? "bg-indigo-100 text-indigo-600"
            : "bg-slate-100 text-slate-500"
      }`}>
        <Icon size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start">
          <p className={`font-semibold text-sm truncate transition-colors duration-500 ${active || visited ? "text-indigo-900" : "text-slate-700"}`}>
            {label}
          </p>
          {visited && logData?.latency_ms && (
            <span className="flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              <Clock size={10} /> {logData.latency_ms}ms
            </span>
          )}
        </div>
        {description && (
          <p className={`text-xs mt-0.5 truncate transition-colors duration-500 ${active || visited ? "text-indigo-600" : "text-slate-400"}`}>
            {description}
          </p>
        )}
      </div>
      {active && (
        <div className="absolute inset-0 rounded-xl border-2 border-indigo-500 opacity-20 animate-ping"></div>
      )}
    </div>
    
    {visited && logData && renderLog && (
      <div className="ml-14 p-3 bg-[#0F172A] rounded-xl border border-slate-800 shadow-lg">
        {renderLog(logData)}
      </div>
    )}
  </div>
);

const Arrow = ({ active, visited }: { active: boolean, visited: boolean }) => (
  <div className="flex justify-center -my-2 relative z-0">
    <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-white transition-all duration-500 ${
      active 
        ? "text-indigo-600 shadow-sm" 
        : visited
          ? "text-indigo-300"
          : "text-slate-300"
    }`}>
      <ArrowDown size={16} />
    </div>
  </div>
);

export default function ChatPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I am your College Placement Intelligence Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [visitedNodes, setVisitedNodes] = useState<Set<string>>(new Set());
  const [debugData, setDebugData] = useState<any>({});
  const [memoryState, setMemoryState] = useState<any>(null);
  const [showStateModal, setShowStateModal] = useState(false);
  
  // Profile Modal State
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [profileData, setProfileData] = useState({
    college_id: "", branch: "", batch: 2026, cgpa: 0.0, active_backlogs: 0
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState({ text: "", type: "" });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!getAuthToken()) {
      router.push("/login");
    } else {
      loadThreads();
      fetchWithAuth("/auth/me").then(data => {
        setUser(data);
        if (data.student_profile) {
          setProfileData({
            college_id: data.student_profile.college_id || "",
            branch: data.student_profile.branch || "",
            batch: data.student_profile.batch || 2026,
            cgpa: data.student_profile.cgpa || 0.0,
            active_backlogs: data.student_profile.active_backlogs || 0
          });
        }
      }).catch(() => router.push("/login"));
    }
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMessage({ text: "", type: "" });
    try {
      await fetchWithAuth("/students/me", {
        method: "PUT",
        body: JSON.stringify(profileData),
      });
      setProfileMessage({ text: "Profile updated successfully!", type: "success" });
      setTimeout(() => setShowProfileModal(false), 1500);
    } catch (err: any) {
      setProfileMessage({ text: err.message || "Failed to update profile", type: "error" });
    } finally {
      setSavingProfile(false);
    }
  };

  const loadThreads = async () => {
    try {
      const data = await fetchWithAuth("/chat/threads");
      setThreads(data);
    } catch (e) {
      console.error("Failed to load threads", e);
    }
  };

  const handleNewChat = () => {
    setCurrentThreadId(null);
    setMessages([{ role: "assistant", content: "Hello! I am your College Placement Intelligence Assistant. How can I help you today?" }]);
    setVisitedNodes(new Set());
    setDebugData({});
    setMemoryState(null);
  };

  const loadThreadMessages = async (threadId: string) => {
    try {
      setCurrentThreadId(threadId);
      setVisitedNodes(new Set());
      setDebugData({});
      setMemoryState(null);
      
      const msgs = await fetchWithAuth(`/chat/threads/${threadId}/messages`);
      if (msgs && msgs.length > 0) {
        setMessages(msgs.map((m: any) => ({
          role: m.role === "human" ? "user" : "assistant",
          content: m.content
        })));
      } else {
        setMessages([{ role: "assistant", content: "Hello! How can I help you today?" }]);
      }
    } catch (e) {
      console.error("Failed to load messages", e);
    }
  };

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
    
    setActiveNode("input");
    setVisitedNodes(new Set(["input"]));
    setDebugData({});
    setMemoryState(null);

    try {
      const payload: any = { message: userMsg };
      if (currentThreadId) {
        payload.thread_id = currentThreadId;
      }
      
      const response = await fetchWithAuth("/chat/message", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      if (!currentThreadId && response.thread_id) {
        setCurrentThreadId(response.thread_id);
        loadThreads(); // Refresh thread list to show the new one
      }

      setDebugData(response.debug_log || {});
      setMemoryState(response.memory_state || null);

      const trace = response.trace || [];
      if (trace.length > 0) {
        for (const node of trace) {
          setActiveNode(node);
          setVisitedNodes(prev => new Set(prev).add(node));
          await new Promise(resolve => setTimeout(resolve, 1500)); 
        }
      }

      setActiveNode(null);
      setMessages(prev => [...prev, { role: "assistant", content: response.response }]);
    } catch (error: any) {
      setActiveNode(null);
      setMessages(prev => [...prev, { role: "assistant", content: `⚠️ ${error.message || "Failed to process request."}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      
      {/* Sidebar - Enhanced with Threads */}
      <div className="hidden md:flex w-64 flex-col bg-white border-r border-slate-200">
        <div className="p-4 border-b border-slate-200 flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-indigo-600 flex items-center justify-center text-white shadow-sm">
            <Sparkles size={16} />
          </div>
          <span className="font-semibold tracking-tight">Intelligence Desk</span>
        </div>
        
        <div className="p-4">
          <button 
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg text-sm font-medium transition-colors border border-indigo-200"
          >
            <Plus size={16} /> New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-2">
          <div className="px-2 pb-2">
            <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-2">Recent Threads</p>
            {threads.length === 0 ? (
              <p className="text-xs text-slate-500 py-2">No past conversations.</p>
            ) : (
              <ul className="space-y-1">
                {threads.map(thread => (
                  <li key={thread.id}>
                    <button
                      onClick={() => loadThreadMessages(thread.id)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg text-sm truncate transition-colors flex items-center gap-2 ${
                        currentThreadId === thread.id 
                          ? "bg-indigo-50 text-indigo-700 font-medium" 
                          : "text-slate-600 hover:bg-slate-100"
                      }`}
                    >
                      <MessageSquare size={14} className={currentThreadId === thread.id ? "text-indigo-500" : "text-slate-400"} />
                      <span className="truncate">{thread.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex flex-col gap-3">
          <button 
            onClick={() => setShowProfileModal(true)}
            className="flex items-center text-sm text-slate-600 hover:text-slate-900 transition-colors w-full"
          >
            <User size={16} className="mr-2" />
            My Profile
          </button>
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
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <div className="md:hidden p-4 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-indigo-600" />
            <span className="font-semibold">Intelligence Desk</span>
          </div>
          <button onClick={handleLogout} className="text-slate-600">
            <LogOut size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 max-w-3xl mx-auto ${msg.role === "user" || msg.role === "human" ? "flex-row-reverse" : ""}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === "user" || msg.role === "human" ? "bg-slate-200 text-slate-700" : "bg-indigo-600 text-white shadow-sm"}`}>
                {msg.role === "user" || msg.role === "human" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`flex-1 rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                msg.role === "user" || msg.role === "human"
                  ? "bg-white border border-slate-200 text-slate-900 ml-12 shadow-sm" 
                  : "bg-white border border-slate-200 text-slate-800 shadow-sm mr-12 whitespace-pre-wrap"
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          
          {isLoading && !activeNode && (
            <div className="flex gap-4 max-w-3xl mx-auto">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-600 text-white shadow-sm flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl px-5 py-3.5 flex items-center gap-2 shadow-sm">
                <Loader2 size={16} className="animate-spin text-slate-400" />
                <span className="text-sm text-slate-500">Agentic workflow running...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)] relative z-10">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about placement drives, eligibility, or companies..."
              className="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:bg-white transition-all text-sm shadow-inner"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-sm"
            >
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </form>
          {currentThreadId && (
            <div className="max-w-3xl mx-auto mt-2 text-center">
               <span className="text-[10px] text-slate-400 font-mono">Thread ID: {currentThreadId}</span>
            </div>
          )}
        </div>

        {/* State Modal */}
        {showStateModal && (
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
            <div className="bg-slate-900 w-full max-w-4xl max-h-full rounded-2xl shadow-2xl flex flex-col border border-slate-700">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Database size={18} className="text-emerald-400" />
                  <h3 className="text-emerald-400 font-mono font-bold text-lg">Graph Memory State</h3>
                </div>
                <button onClick={() => setShowStateModal(false)} className="text-slate-400 hover:text-white transition-colors">
                  <X size={20} />
                </button>
              </div>
              <div className="p-4 overflow-y-auto font-mono text-xs text-emerald-300">
                <pre>{JSON.stringify(memoryState, null, 2)}</pre>
              </div>
            </div>
          </div>
        )}

        {/* Profile Modal */}
        {showProfileModal && (
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-md rounded-2xl shadow-xl flex flex-col">
              <div className="p-4 border-b border-slate-200 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900">My Profile</h3>
                <button onClick={() => setShowProfileModal(false)} className="text-slate-400 hover:text-slate-600">
                  <X size={20} />
                </button>
              </div>
              <div className="p-5 overflow-y-auto max-h-[80vh]">
                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">College ID</label>
                    <input type="text" value={profileData.college_id} disabled className="mt-1 block w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-md text-slate-500 sm:text-sm" />
                    <p className="mt-1 text-xs text-slate-500">Contact admin to change College ID.</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Branch</label>
                    <input type="text" required value={profileData.branch} onChange={(e) => setProfileData({...profileData, branch: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-slate-900" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Batch (Graduation Year)</label>
                    <input type="number" required value={profileData.batch} onChange={(e) => setProfileData({...profileData, batch: parseInt(e.target.value)})} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-slate-900" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">CGPA</label>
                    <input type="number" step="0.01" required value={profileData.cgpa} onChange={(e) => setProfileData({...profileData, cgpa: parseFloat(e.target.value)})} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-slate-900" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Active Backlogs</label>
                    <input type="number" required value={profileData.active_backlogs} onChange={(e) => setProfileData({...profileData, active_backlogs: parseInt(e.target.value)})} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-slate-900" />
                  </div>
                  
                  {profileMessage.text && (
                    <div className={`p-2 rounded text-sm ${profileMessage.type === 'error' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                      {profileMessage.text}
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-200 mt-4 flex justify-end">
                    <button type="button" onClick={() => setShowProfileModal(false)} className="mr-3 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none">
                      Cancel
                    </button>
                    <button type="submit" disabled={savingProfile} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none disabled:opacity-50">
                      {savingProfile ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Advanced Real-time Architecture Trace Panel */}
      <div className="hidden lg:flex w-[480px] flex-col bg-slate-50 border-l border-slate-200 shadow-xl z-20">
        <div className="p-5 border-b border-slate-200 bg-white flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2 text-slate-900 font-bold tracking-tight">
              <Activity size={18} className="text-indigo-600" />
              <span>Agentic Console</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Live LangGraph telemetry & payloads</p>
          </div>
          <div className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold uppercase rounded tracking-wider animate-pulse flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div> LIVE
          </div>
        </div>
        
        <div className="flex-1 p-6 flex flex-col justify-start overflow-y-auto pb-24">
           <Node 
              active={activeNode === 'input'} 
              visited={visitedNodes.has('input')}
              icon={User} 
              label="1. User Input Received" 
              description={currentThreadId ? "Graph execution started (Thread Memory Injected)" : "Graph execution started"}
            />
           
           <Arrow 
              active={activeNode === 'classify_node'} 
              visited={visitedNodes.has('classify_node')}
            />
           
           <Node 
              active={activeNode === 'classify_node'} 
              visited={visitedNodes.has('classify_node')}
              icon={GitMerge} 
              label="2. Semantic Router" 
              description="Classifying natural language intent"
              logData={debugData.classify_node}
              renderLog={(data) => (
                <>
                  <div className="flex flex-wrap">
                    <Badge label="Intent" value={data.classified_intent} />
                    <Badge label="Entity" value={data.extracted_company || 'None'} />
                  </div>
                  <CodeBlock title="Routing Decision" content={data.action} />
                </>
              )}
            />
           
           <Arrow 
              active={activeNode === 'execute_tool_node'} 
              visited={visitedNodes.has('execute_tool_node')}
            />
           
           <Node 
              active={activeNode === 'execute_tool_node'} 
              visited={visitedNodes.has('execute_tool_node')}
              icon={Database} 
              label="3. Tool Execution" 
              description="PostgreSQL / FAISS Vector Search"
              logData={debugData.execute_tool_node}
              renderLog={(data) => (
                <>
                  <p className="text-slate-400 text-xs mb-2 italic">{data.action}</p>
                  {data.raw_query && <CodeBlock title="Query Compiled" content={data.raw_query} />}
                  <CodeBlock title="Raw Payload Fetched" content={data.raw_payload} />
                </>
              )}
            />
           
           <Arrow 
              active={activeNode === 'generate_response_node'} 
              visited={visitedNodes.has('generate_response_node')}
            />
           
           <Node 
              active={activeNode === 'generate_response_node'} 
              visited={visitedNodes.has('generate_response_node')}
              icon={BrainCircuit} 
              label="4. LLM Synthesis" 
              description="Injecting ground-truth payload to LLM"
              logData={debugData.generate_response_node}
              renderLog={(data) => (
                <>
                  <div className="flex flex-wrap">
                    <Badge label="Model" value={data.model} />
                    <Badge label="Temp" value={data.temperature.toString()} />
                    {data.tokens && (
                      <Badge icon={Zap} label="Tokens" value={`${data.tokens.prompt} In | ${data.tokens.completion} Out`} />
                    )}
                  </div>
                  <CodeBlock title="Generated System Prompt" content={data.system_prompt} />
                </>
              )}
            />
        </div>
        
        {/* Footer actions */}
        <div className="p-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-30">
          <button 
            disabled={!memoryState}
            onClick={() => setShowStateModal(true)}
            className="w-full py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 disabled:hover:bg-slate-900 transition-colors flex items-center justify-center gap-2"
          >
            <Database size={16} />
            View Raw Memory State
          </button>
        </div>
      </div>
    </div>
  );
}
