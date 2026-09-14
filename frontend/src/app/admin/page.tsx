"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "@/lib/api";
import { Shield, Upload, FileText, Loader2, LogOut, Eye, EyeOff } from "lucide-react";
import Link from "next/link";

export default function AdminDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [accessLevel, setAccessLevel] = useState("ALL");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    // Check if user is admin
    fetchWithAuth("/auth/me")
      .then((data) => {
        if (data.role !== "ADMIN" && data.role !== "TPO") {
          router.push("/chat");
        } else {
          setUser(data);
          setLoading(false);
        }
      })
      .catch(() => {
        router.push("/login");
      });
  }, [router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage({ text: "", type: "" });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("description", description);
    formData.append("access_level", accessLevel);

    try {
      const res = await fetchWithAuth("/knowledge/upload", {
        method: "POST",
        body: formData, // fetchWithAuth will automatically omit Content-Type for FormData
      });

      setMessage({ text: "Document uploaded and indexed successfully!", type: "success" });
      setFile(null);
      setDescription("");
      setAccessLevel("ALL");
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      // Refresh documents
      fetchDocuments();
      
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to upload document", type: "error" });
    } finally {
      setUploading(false);
    }
  };

  const [documents, setDocuments] = useState<any[]>([]);
  const [studentsList, setStudentsList] = useState<any[]>([]);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [escalationTab, setEscalationTab] = useState<"OPEN" | "RESOLVED">("OPEN");
  const [replyText, setReplyText] = useState<{ [key: string]: string }>({});
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      const data = await fetchWithAuth("/knowledge/");
      setDocuments(data);
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  };

  const fetchStudents = async () => {
    try {
      const data = await fetchWithAuth("/students/");
      setStudentsList(data);
    } catch (err) {
      console.error("Failed to fetch students", err);
    }
  };

  const fetchEscalations = async () => {
    try {
      const data = await fetchWithAuth("/escalations/");
      setEscalations(data);
    } catch (err) {
      console.error("Failed to fetch escalations", err);
    }
  };

  const handleResolveEscalation = async (id: string) => {
    if (!replyText[id] || replyText[id].trim() === "") {
      alert("Reply text cannot be empty.");
      return;
    }
    
    setResolvingId(id);
    try {
      await fetchWithAuth(`/escalations/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ reply_text: replyText[id] })
      });
      alert("Ticket resolved and reply sent to student!");
      setReplyText(prev => ({ ...prev, [id]: "" }));
      fetchEscalations();
    } catch (err: any) {
      alert("Failed to resolve ticket: " + err.message);
    } finally {
      setResolvingId(null);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this document? This will remove it from the knowledge base forever.")) return;
    
    try {
      await fetchWithAuth(`/knowledge/${documentId}`, {
        method: "DELETE"
      });
      setMessage({ text: "Document deleted successfully", type: "success" });
      fetchDocuments();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to delete document", type: "error" });
    }
  };

  useEffect(() => {
    if (user && (user.role === "ADMIN" || user.role === "TPO")) {
      fetchDocuments();
      fetchStudents();
      fetchEscalations();
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-slate-900">Admin Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600">{user?.email}</span>
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  router.push("/login");
                }}
                className="text-slate-400 hover:text-slate-500"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        <div className="md:grid md:grid-cols-3 md:gap-6 mb-12">
          <div className="md:col-span-1">
            <div className="px-4 sm:px-0">
              <h3 className="text-lg font-medium leading-6 text-slate-900">Knowledge Base</h3>
              <p className="mt-1 text-sm text-slate-600">
                Upload PDFs (Placement Policies, JDs, Handbooks) to the vector database. The agent will read these to answer unstructured questions.
              </p>
            </div>
          </div>
          
          <div className="mt-5 md:mt-0 md:col-span-2">
            <form onSubmit={handleUpload}>
              <div className="shadow sm:rounded-md sm:overflow-hidden">
                <div className="px-4 py-5 bg-white space-y-6 sm:p-6 border border-slate-200">
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700">
                      Document Description
                    </label>
                    <div className="mt-1">
                      <input
                        type="text"
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 px-3 py-2 border"
                        placeholder="e.g. 2026 TCS Placement Policy"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700">
                      Access Level
                    </label>
                    <div className="mt-1">
                      <select
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 px-3 py-2 border bg-white"
                        value={accessLevel}
                        onChange={(e) => setAccessLevel(e.target.value)}
                      >
                        <option value="ALL">ALL (Students, TPO, Admins)</option>
                        <option value="STUDENT">STUDENT Only</option>
                        <option value="TPO">TPO Only</option>
                        <option value="ADMIN">ADMIN Only</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700">
                      PDF File
                    </label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-md">
                      <div className="space-y-1 text-center">
                        <FileText className="mx-auto h-12 w-12 text-slate-400" />
                        <div className="flex text-sm text-slate-600 justify-center">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                          >
                            <span>Upload a file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              accept=".pdf"
                              className="sr-only"
                              onChange={handleFileChange}
                              required
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-slate-500">
                          PDF up to 10MB
                        </p>
                        {file && (
                          <p className="text-sm font-medium text-blue-600 mt-2">
                            Selected: {file.name}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="px-4 py-3 bg-slate-50 text-right sm:px-6 flex justify-between items-center border-t border-slate-200">
                  <div className="text-sm">
                    {message.text && (
                      <span className={message.type === 'error' ? 'text-red-600' : 'text-green-600 font-medium'}>
                        {message.text}
                      </span>
                    )}
                  </div>
                  <button
                    type="submit"
                    disabled={!file || uploading}
                    className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {uploading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        Upload & Index
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Uploaded Documents List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-slate-200">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center border-b border-slate-200 bg-slate-50">
            <div>
              <h3 className="text-lg leading-6 font-medium text-slate-900">Uploaded Documents</h3>
              <p className="mt-1 max-w-2xl text-sm text-slate-500">All PDFs currently indexed in FAISS.</p>
            </div>
            <div className="text-sm text-slate-500">
              Total: {documents.length}
            </div>
          </div>
          <div className="border-t border-slate-200">
            {documents.length === 0 ? (
              <div className="text-center py-10 text-sm text-slate-500">
                No documents uploaded yet.
              </div>
            ) : (
              <ul role="list" className="divide-y divide-slate-200">
                {documents.map((doc) => (
                  <li key={doc.id} className="pl-4 pr-4 py-4 sm:pl-6 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex flex-col">
                        <p className="text-sm font-medium text-blue-600 truncate">{doc.filename}</p>
                        <p className="text-sm text-slate-500 mt-1">{doc.description}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2 text-sm text-slate-500">
                        <span className="font-mono text-[10px] text-slate-400 bg-slate-100 px-2 py-1 rounded">
                          {new Date(doc.created_at).toLocaleString()}
                        </span>
                        <button 
                          onClick={() => handleDelete(doc.id)}
                          className="text-xs text-red-600 hover:text-red-800 bg-red-50 hover:bg-red-100 px-2 py-1 rounded transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Escalated Queries Section */}
        <div className="mt-12 bg-white shadow overflow-hidden sm:rounded-lg border border-slate-200">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center border-b border-slate-200 bg-red-50">
            <div>
              <h3 className="text-lg leading-6 font-medium text-red-900">Escalated Queries (Human-in-the-Loop)</h3>
              <p className="mt-1 max-w-2xl text-sm text-red-700">Queries the AI could not answer or where the student explicitly requested human assistance.</p>
            </div>
            <div className="text-sm font-medium text-red-700 bg-red-100 px-3 py-1 rounded-full">
              {escalations.filter(t => t.status === "OPEN").length} Open Tickets
            </div>
          </div>
          
          <div className="bg-white border-b border-slate-200">
            <nav className="-mb-px flex" aria-label="Tabs">
              <button
                onClick={() => setEscalationTab("OPEN")}
                className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm ${
                  escalationTab === "OPEN"
                    ? "border-red-500 text-red-600"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                }`}
              >
                Open Tickets
              </button>
              <button
                onClick={() => setEscalationTab("RESOLVED")}
                className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm ${
                  escalationTab === "RESOLVED"
                    ? "border-green-500 text-green-600"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                }`}
              >
                Resolved History
              </button>
            </nav>
          </div>

          <div className="border-t border-slate-200">
            {escalationTab === "OPEN" && (
              escalations.filter(t => t.status === "OPEN").length === 0 ? (
                <div className="text-center py-10 text-sm text-slate-500">
                  No open escalations. The AI is handling everything!
                </div>
              ) : (
                <ul role="list" className="divide-y divide-slate-200">
                  {escalations.filter(t => t.status === "OPEN").map((ticket) => (
                    <li key={ticket.id} className="p-4 sm:px-6 hover:bg-slate-50 transition-colors">
                      <div className="flex flex-col gap-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium text-slate-900">Student: {ticket.user_email}</p>
                            <p className="text-sm text-slate-700 mt-1 bg-slate-100 p-3 rounded border border-slate-200">
                              "{ticket.query_text}"
                            </p>
                          </div>
                          <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-2 py-1 rounded shrink-0">
                            {new Date(ticket.created_at).toLocaleString()}
                          </span>
                        </div>
                        
                        <div className="flex gap-3">
                          <textarea
                            className="flex-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 px-3 py-2 border"
                            placeholder="Type your response to the student..."
                            rows={2}
                            value={replyText[ticket.id] || ""}
                            onChange={(e) => setReplyText(prev => ({ ...prev, [ticket.id]: e.target.value }))}
                          />
                          <button
                            onClick={() => handleResolveEscalation(ticket.id)}
                            disabled={resolvingId === ticket.id}
                            className="self-end inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                          >
                            {resolvingId === ticket.id ? "Resolving..." : "Resolve & Reply"}
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )
            )}

            {escalationTab === "RESOLVED" && (
              escalations.filter(t => t.status === "RESOLVED").length === 0 ? (
                <div className="text-center py-10 text-sm text-slate-500">
                  No resolved tickets yet.
                </div>
              ) : (
                <ul role="list" className="divide-y divide-slate-200">
                  {escalations.filter(t => t.status === "RESOLVED").map((ticket) => (
                    <li key={ticket.id} className="p-4 sm:px-6 hover:bg-slate-50 transition-colors">
                      <div className="flex flex-col gap-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium text-slate-900">Student: {ticket.user_email}</p>
                            <p className="text-sm text-slate-700 mt-1 bg-slate-100 p-3 rounded border border-slate-200">
                              <span className="font-semibold block mb-1">Query:</span>
                              "{ticket.query_text}"
                            </p>
                          </div>
                          <span className="font-mono text-[10px] text-green-700 bg-green-100 px-2 py-1 rounded shrink-0">
                            Resolved: {ticket.resolved_at ? new Date(ticket.resolved_at).toLocaleString() : "Unknown"}
                          </span>
                        </div>
                        
                        <div className="bg-blue-50 p-3 rounded border border-blue-100 mt-2">
                          <p className="text-sm text-blue-900 font-semibold mb-1">Your Reply:</p>
                          <p className="text-sm text-blue-800 whitespace-pre-wrap">{ticket.admin_reply}</p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )
            )}
          </div>
        </div>

        {/* Create Student Section */}
        <div className="mt-12 md:grid md:grid-cols-3 md:gap-6 mb-12">
          <div className="md:col-span-1">
            <div className="px-4 sm:px-0">
              <h3 className="text-lg font-medium leading-6 text-slate-900">User Management</h3>
              <p className="mt-1 text-sm text-slate-600">
                Register a new student account. They will use these credentials to access the intelligence platform.
              </p>
            </div>
          </div>
          
          <div className="mt-5 md:mt-0 md:col-span-2">
            <form onSubmit={async (e) => {
              e.preventDefault();
              const form = e.target as HTMLFormElement;
              const data = new FormData(form);
              try {
                await fetchWithAuth("/auth/register", {
                  method: "POST",
                  body: JSON.stringify(Object.fromEntries(data)),
                });
                alert("Student registered successfully!");
                form.reset();
                fetchStudents();
              } catch (err: any) {
                alert("Registration failed: " + err.message);
              }
            }}>
              <div className="shadow sm:rounded-md sm:overflow-hidden">
                <div className="px-4 py-5 bg-white space-y-6 sm:p-6 border border-slate-200">
                  <div className="grid grid-cols-6 gap-6">
                    <div className="col-span-6 sm:col-span-3">
                      <label className="block text-sm font-medium text-slate-700">Email address</label>
                      <input type="email" name="email" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                    <div className="col-span-6 sm:col-span-3">
                      <label className="block text-sm font-medium text-slate-700">Password</label>
                      <div className="relative mt-1">
                        <input type={showPassword ? "text" : "password"} name="password" required className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 pr-10 border" />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                    <div className="col-span-6 sm:col-span-2">
                      <label className="block text-sm font-medium text-slate-700">College ID</label>
                      <input type="text" name="college_id" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                    <div className="col-span-6 sm:col-span-2">
                      <label className="block text-sm font-medium text-slate-700">Branch</label>
                      <input type="text" name="branch" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                    <div className="col-span-6 sm:col-span-2">
                      <label className="block text-sm font-medium text-slate-700">Batch (Year)</label>
                      <input type="number" name="batch" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                    <div className="col-span-6 sm:col-span-3">
                      <label className="block text-sm font-medium text-slate-700">CGPA</label>
                      <input type="number" step="0.01" name="cgpa" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                    <div className="col-span-6 sm:col-span-3">
                      <label className="block text-sm font-medium text-slate-700">Active Backlogs</label>
                      <input type="number" name="active_backlogs" defaultValue="0" required className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md text-slate-900 py-2 px-3 border" />
                    </div>
                  </div>
                </div>
                <div className="px-4 py-3 bg-slate-50 text-right sm:px-6 border-t border-slate-200">
                  <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900">
                    Register Student
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Registered Students List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-slate-200 mb-12">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center border-b border-slate-200 bg-slate-50">
            <div>
              <h3 className="text-lg leading-6 font-medium text-slate-900">Registered Students</h3>
              <p className="mt-1 max-w-2xl text-sm text-slate-500">All registered student accounts.</p>
            </div>
            <div className="text-sm text-slate-500">
              Total: {studentsList.length}
            </div>
          </div>
          <div className="border-t border-slate-200">
            {studentsList.length === 0 ? (
              <div className="text-center py-10 text-sm text-slate-500">
                No students registered yet.
              </div>
            ) : (
              <ul role="list" className="divide-y divide-slate-200">
                {studentsList.map((student) => (
                  <li key={student.id} className="pl-4 pr-4 py-4 sm:pl-6 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex flex-col">
                        <p className="text-sm font-medium text-slate-900">{student.user?.email}</p>
                        <p className="text-sm text-slate-500 mt-1">
                          ID: <span className="font-mono text-xs">{student.college_id}</span> • 
                          Branch: {student.branch} • 
                          Batch: {student.batch} • 
                          CGPA: {student.cgpa}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2 text-sm text-slate-500">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${student.user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {student.user?.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <span className="font-mono text-[10px] text-slate-400 bg-slate-100 px-2 py-1 rounded">
                          {new Date(student.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
