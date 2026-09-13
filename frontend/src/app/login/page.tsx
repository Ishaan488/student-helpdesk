"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL, setAuthToken } from "@/lib/api";
import { Lock, Mail, Loader2, ArrowRight, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Invalid credentials. Please try again.");
      }

      const data = await response.json();
      setAuthToken(data.access_token);
      
      // Fetch user profile to route dynamically
      const userRes = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      
      if (userRes.ok) {
        const userData = await userRes.json();
        if (userData.role === "ADMIN" || userData.role === "TPO") {
          router.push("/admin");
        } else {
          router.push("/chat");
        }
      } else {
        router.push("/chat"); // Fallback
      }
      
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-900 font-sans p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-900 text-white mb-4">
            <Lock size={20} />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Sign in to your account</h1>
          <p className="text-sm text-slate-500 mt-2">Enter your college credentials to access the intelligence platform.</p>
        </div>

        {error && (
          <div className="mb-6 p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail size={18} />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-slate-900 focus:border-slate-900 sm:text-sm outline-none transition-all text-slate-900"
                placeholder="name@college.edu"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock size={18} />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-10 py-2.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-slate-900 focus:border-slate-900 sm:text-sm outline-none transition-all text-slate-900"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-70 transition-all"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : (
              <>
                Sign in
                <ArrowRight size={16} className="ml-2" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
