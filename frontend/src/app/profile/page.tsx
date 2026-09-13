"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "@/lib/api";
import { User, Loader2, Save, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<any>(null);
  
  const [profileData, setProfileData] = useState({
    college_id: "",
    branch: "",
    batch: 2026,
    cgpa: 0.0,
    active_backlogs: 0
  });
  
  const [message, setMessage] = useState({ text: "", type: "" });

  useEffect(() => {
    // Check auth and role
    fetchWithAuth("/auth/me")
      .then((data) => {
        if (data.role !== "STUDENT") {
          router.push("/admin");
        } else {
          setUser(data);
          // If student profile is nested in response, populate it
          if (data.student_profile) {
            setProfileData({
              college_id: data.student_profile.college_id || "",
              branch: data.student_profile.branch || "",
              batch: data.student_profile.batch || 2026,
              cgpa: data.student_profile.cgpa || 0.0,
              active_backlogs: data.student_profile.active_backlogs || 0
            });
          }
          setLoading(false);
        }
      })
      .catch(() => {
        router.push("/login");
      });
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ text: "", type: "" });

    try {
      await fetchWithAuth("/students/me", {
        method: "PUT",
        body: JSON.stringify(profileData),
      });
      setMessage({ text: "Profile updated successfully!", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to update profile", type: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/chat" className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-slate-600">
              <ArrowLeft size={18} />
            </Link>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">My Profile</h1>
          </div>
          <div className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {user?.email}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 sm:p-8 border-b border-slate-200 bg-slate-50/50 flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shadow-inner">
              <User size={32} />
            </div>
            <div>
              <h2 className="text-lg font-medium text-slate-900">Academic Details</h2>
              <p className="text-sm text-slate-500">Keep your academic details up to date for accurate placement drive eligibility.</p>
            </div>
          </div>

          <form onSubmit={handleSave} className="p-6 sm:p-8 space-y-6">
            <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              
              <div className="sm:col-span-3">
                <label className="block text-sm font-medium text-slate-700">College ID / Enrollment No.</label>
                <div className="mt-1">
                  <input
                    type="text"
                    name="college_id"
                    value={profileData.college_id}
                    disabled
                    className="shadow-sm block w-full sm:text-sm border-slate-200 rounded-md bg-slate-50 text-slate-500 py-2.5 px-3 border cursor-not-allowed"
                    title="College ID cannot be changed"
                  />
                </div>
              </div>

              <div className="sm:col-span-3">
                <label className="block text-sm font-medium text-slate-700">Branch / Major</label>
                <div className="mt-1">
                  <input
                    type="text"
                    name="branch"
                    value={profileData.branch}
                    onChange={handleChange}
                    required
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-slate-300 rounded-md py-2.5 px-3 border transition-colors"
                  />
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700">Graduation Year</label>
                <div className="mt-1">
                  <input
                    type="number"
                    name="batch"
                    value={profileData.batch}
                    onChange={handleChange}
                    required
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-slate-300 rounded-md py-2.5 px-3 border transition-colors"
                  />
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700">Current CGPA</label>
                <div className="mt-1">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    name="cgpa"
                    value={profileData.cgpa}
                    onChange={handleChange}
                    required
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-slate-300 rounded-md py-2.5 px-3 border transition-colors"
                  />
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700">Active Backlogs</label>
                <div className="mt-1">
                  <input
                    type="number"
                    min="0"
                    name="active_backlogs"
                    value={profileData.active_backlogs}
                    onChange={handleChange}
                    required
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-slate-300 rounded-md py-2.5 px-3 border transition-colors"
                  />
                </div>
              </div>
            </div>

            {message.text && (
              <div className={`p-4 rounded-md ${message.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                <p className="text-sm font-medium">{message.text}</p>
              </div>
            )}

            <div className="pt-4 border-t border-slate-200 flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex justify-center items-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-70 transition-colors"
              >
                {saving ? (
                  <>
                    <Loader2 size={16} className="animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={16} className="mr-2" />
                    Save Profile
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
