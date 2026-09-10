import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-900 font-sans p-6">
      <div className="max-w-2xl w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-900 text-white mb-8 shadow-md">
          <Sparkles size={32} />
        </div>
        
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900 mb-6">
          College Placement Intelligence
        </h1>
        
        <p className="text-lg text-slate-600 mb-10 max-w-xl mx-auto leading-relaxed">
          A secure, deterministically-driven AI assistant for students. Check eligibility, explore company facts, and track upcoming drives instantly.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link 
            href="/login" 
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-slate-900 hover:bg-slate-800 transition-colors w-full sm:w-auto shadow-sm"
          >
            Access Intelligence Desk
            <ArrowRight size={18} className="ml-2" />
          </Link>
          <a 
            href="http://127.0.0.1:8000/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center px-6 py-3 border border-slate-200 text-base font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 transition-colors w-full sm:w-auto"
          >
            View API Docs
          </a>
        </div>
      </div>
      
      <div className="absolute bottom-8 text-sm text-slate-400">
        Secured by FastApi • Powered by LangGraph
      </div>
    </div>
  );
}
