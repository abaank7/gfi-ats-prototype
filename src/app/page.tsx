"use client";

import React, { useState, useEffect } from "react";
import { 
  Upload, FileText, ChevronDown, ChevronUp, AlertTriangle, 
  CheckCircle, Briefcase, GraduationCap, XCircle 
} from "lucide-react";
// Next.js automatically resolves JSON imports
import baseCandidates from "@/data/candidates.json";

// Types matching the Pydantic backend schema
interface Candidate {
  filename: string;
  status: "SUCCESS" | "EXTRACTION_FAILED";
  skills: string[];
  total_years_experience: number;
  education: string;
  projects: string[];
  classification: "LCA" | "UI/UX" | "Both" | "Neither/Uncertain";
  lca_score: number;
  lca_reasoning: string;
  ui_ux_score: number;
  ui_ux_reasoning: string;
  source_link: string;
}

export default function ATSDashboard() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activeTab, setActiveTab] = useState<"LCA" | "UI/UX">("LCA");
  const [isUploading, setIsUploading] = useState(false);
  
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null); // NEW

  // 1. Initialize data on load (Base + LocalStorage)
  useEffect(() => {
    const stored = localStorage.getItem("uploaded_candidates");
    const uploadedCandidates: Candidate[] = stored ? JSON.parse(stored) : [];
    
    // Cast baseCandidates to any to bypass strict TS JSON typing, then to Candidate[]
    const allCandidates = [...uploadedCandidates, ...(baseCandidates as any as Candidate[])];
    setCandidates(allCandidates);
  }, []);

  // 2. Handle Live File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // const res = await fetch("/api/upload", {
      //   method: "POST",
      //   body: formData,
      const API_BASE = process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "";
      
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      
      const newCandidate: Candidate = await res.json();
      
      // Prepend the new candidate to the UI state
      setCandidates((prev) => {
        const updated = [newCandidate, ...prev];
        // Save ONLY the uploaded candidates to localStorage to persist across refreshes
        const stored = JSON.parse(localStorage.getItem("uploaded_candidates") || "[]");
        localStorage.setItem("uploaded_candidates", JSON.stringify([newCandidate, ...stored]));
        return updated;
      });
      
      // Auto-expand the newly uploaded candidate so HR can immediately see the result
      setExpandedId(newCandidate.filename);
      // Auto-switch tab if they are a strong fit for the other role
      if (newCandidate.ui_ux_score > newCandidate.lca_score) setActiveTab("UI/UX");
      else setActiveTab("LCA");

      // NEW: Show success toast
      setToastMessage(`Successfully processed: ${newCandidate.filename}`);
      setTimeout(() => setToastMessage(null), 4000);

      // NEW: Auto-scroll to the newly added candidate after React renders it
      setTimeout(() => {
        const element = document.getElementById(`candidate-${newCandidate.filename}`);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 300);

    } catch (err) {
      alert("Upload failed. Please ensure your backend is running.");
      console.error(err);
    } finally {
      setIsUploading(false);
      // Reset input so the same file can be uploaded again if needed
      e.target.value = "";
    }
  };

  // 3. Sort candidates based on the active tab
  const sortedCandidates = [...candidates].sort((a, b) => {
    if (activeTab === "LCA") return b.lca_score - a.lca_score;
    return b.ui_ux_score - a.ui_ux_score;
  });

  // UI Helper functions
  const getScoreColor = (score: number) => {
    if (score >= 75) return "text-emerald-600 font-bold";
    if (score >= 50) return "text-amber-600 font-bold";
    return "text-red-500 font-medium";
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6 md:p-10 font-sans">
      
      {/* HEADER & UPLOAD */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">GFI Recruitment Dashboard</h1>
          <p className="text-gray-500 mt-1">AI-Powered Parsing & Ranking Prototype</p>
        </div>
        
        <div className="relative">
          <input 
            type="file" 
            accept=".pdf,.docx" 
            onChange={handleFileUpload} 
            disabled={isUploading}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
          <button 
            disabled={isUploading}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-white font-semibold transition-all shadow-sm
              ${isUploading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'}`}
          >
            {isUploading ? (
              <span className="flex items-center gap-2 animate-pulse">
                Processing AI...
              </span>
            ) : (
              <>
                <Upload size={18} />
                Test Live Resume
              </>
            )}
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto">
        {/* TABS */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab("LCA")}
            className={`pb-4 px-6 font-semibold text-sm transition-all ${
              activeTab === "LCA" 
                ? "border-b-2 border-indigo-600 text-indigo-600" 
                : "text-gray-400 hover:text-gray-700"
            }`}
          >
            Role 1: LifeCycle Assessment (LCA)
          </button>
          <button
            onClick={() => setActiveTab("UI/UX")}
            className={`pb-4 px-6 font-semibold text-sm transition-all ${
              activeTab === "UI/UX" 
                ? "border-b-2 border-indigo-600 text-indigo-600" 
                : "text-gray-400 hover:text-gray-700"
            }`}
          >
            Role 2: UI/UX Design Intern
          </button>
        </div>

        {/* CANDIDATE LIST */}
        <div className="space-y-4">
          {sortedCandidates.map((candidate, idx) => {
            const isExpanded = expandedId === candidate.filename;
            const isError = candidate.status === "EXTRACTION_FAILED";
            const currentScore = activeTab === "LCA" ? candidate.lca_score : candidate.ui_ux_score;
            const currentReasoning = activeTab === "LCA" ? candidate.lca_reasoning : candidate.ui_ux_reasoning;

            return (
              <div 
                id={`candidate-${candidate.filename}`}
                key={`${candidate.filename}-${idx}`} 
                className={`bg-white rounded-xl shadow-sm border transition-all ${
                  isError ? "border-red-200" : "border-gray-200 hover:border-indigo-300"
                }`}
              >
                {/* ROW HEADER (Always Visible) */}
                <div 
                  onClick={() => setExpandedId(isExpanded ? null : candidate.filename)}
                  className="p-5 flex flex-col md:flex-row items-center justify-between cursor-pointer gap-4"
                >
                  <div className="flex items-center gap-4 w-full md:w-1/3">
                    {isError ? (
                      <AlertTriangle className="text-red-500 shrink-0" size={24} />
                    ) : (
                      <FileText className="text-indigo-500 shrink-0" size={24} />
                    )}
                    <div className="truncate">
                      <h3 className="font-semibold text-gray-900 truncate" title={candidate.filename}>
                        {candidate.filename}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          isError ? "bg-red-100 text-red-700" :
                          candidate.classification === activeTab ? "bg-emerald-100 text-emerald-700" : 
                          candidate.classification === "Both" ? "bg-purple-100 text-purple-700" :
                          "bg-gray-100 text-gray-600"
                        }`}>
                          {isError ? "Parse Error" : candidate.classification}
                        </span>
                        <a 
                          href={candidate.source_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-blue-500 hover:underline"
                        >
                          {candidate.source_link === "#uploaded-live" ? "Live Upload" : "Source Link"}
                        </a>
                      </div>
                    </div>
                  </div>

                  {!isError && (
                    <div className="hidden md:flex gap-8 text-sm text-gray-600 w-full md:w-1/3 justify-center">
                      <span className="flex items-center gap-1"><Briefcase size={16}/> {candidate.total_years_experience} yrs</span>
                      <span className="flex items-center gap-1 truncate max-w-37.5" title={candidate.education}>
                        <GraduationCap size={16}/> {candidate.education}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between w-full md:w-1/3 md:justify-end gap-6">
                    <div className="flex flex-col items-end">
                      <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Match Score</span>
                      <span className={`text-2xl ${getScoreColor(currentScore)}`}>
                        {isError ? "N/A" : `${currentScore}/100`}
                      </span>
                    </div>
                    {isExpanded ? <ChevronUp className="text-gray-400" /> : <ChevronDown className="text-gray-400" />}
                  </div>
                </div>

                {/* EXPANDED DETAILS (AI Reasoning & Data) */}
                {isExpanded && (
                  <div className="p-5 border-t border-gray-100 bg-gray-50 rounded-b-xl">
                    
                    {/* The specific requirement: Show Human-Readable Reasoning */}
                    <div className={`mb-6 p-4 rounded-lg border ${isError ? 'bg-red-50 border-red-100' : 'bg-indigo-50 border-indigo-100'}`}>
                      <h4 className={`text-sm font-bold flex items-center gap-2 mb-1 ${isError ? 'text-red-800' : 'text-indigo-900'}`}>
                        {isError ? <XCircle size={16}/> : <CheckCircle size={16}/>}
                        AI Reasoning ({activeTab})
                      </h4>
                      <p className={`text-sm leading-relaxed ${isError ? 'text-red-700' : 'text-indigo-800'}`}>
                        {currentReasoning}
                      </p>
                    </div>

                    {!isError && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Extracted Skills</h4>
                          <div className="flex flex-wrap gap-2">
                            {candidate.skills.length > 0 ? candidate.skills.map((skill, i) => (
                              <span key={i} className="bg-white border border-gray-200 text-gray-700 text-xs px-2.5 py-1 rounded-md shadow-sm">
                                {skill}
                              </span>
                            )) : <span className="text-sm text-gray-500 italic">No skills extracted.</span>}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Relevant Projects</h4>
                          <ul className="space-y-2">
                            {candidate.projects.length > 0 ? candidate.projects.map((proj, i) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                <span className="text-indigo-400 mt-0.5">•</span> 
                                <span className="leading-snug">{proj}</span>
                              </li>
                            )) : <li className="text-sm text-gray-500 italic">No specific projects found.</li>}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* NEW: Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 transition-all">
          <CheckCircle size={20} className="text-emerald-400" />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}
    </div>
  );
}