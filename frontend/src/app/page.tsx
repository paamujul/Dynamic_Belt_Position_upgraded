"use client";

import { useState } from "react";

export default function Home() {
  const [cmmFile, setCmmFile] = useState<File | null>(null);
  const [sternumFile, setSternumFile] = useState<File | null>(null);
  const [pressureFiles, setPressureFiles] = useState<FileList | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cmmFile || !sternumFile || !pressureFiles || pressureFiles.length === 0) {
      setError("Please select all required files.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("cmm_data", cmmFile);
    formData.append("sternum_data", sternumFile);
    
    Array.from(pressureFiles).forEach((file) => {
      formData.append("pressure_data", file);
    });

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to process data.");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "interpolated_belt_chest_data.xlsx";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      
      // Optionally reset the form
      setCmmFile(null);
      setSternumFile(null);
      setPressureFiles(null);
      (document.getElementById("upload-form") as HTMLFormElement).reset();

    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage || "An unexpected error occurred. Check the server logs.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans selection:bg-indigo-500/30">
      {/* Decorative background gradients */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px]" />
      </div>

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-16 flex flex-col items-center justify-center min-h-screen">
        <div className="text-center mb-12 space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-br from-white to-slate-400 bg-clip-text text-transparent">
            Dynamic Belt Position
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Upload your testing data below to calculate the dynamic belt position for the Hybrid III 5th percentile female dummy. 
            The pipeline will process the data and automatically download the results.
          </p>
        </div>

        <form 
          id="upload-form"
          onSubmit={handleSubmit}
          className="w-full max-w-2xl bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl transition-all duration-300"
        >
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-8">
            {/* CMM Data Input */}
            <div className="space-y-2 group">
              <label className="block text-sm font-medium text-slate-300 group-focus-within:text-indigo-400 transition-colors">
                CMM Data (Left Rear Passenger.xlsx)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={(e) => setCmmFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-slate-400
                    file:mr-4 file:py-3 file:px-4
                    file:rounded-xl file:border-0
                    file:text-sm file:font-semibold
                    file:bg-indigo-500/10 file:text-indigo-400
                    hover:file:bg-indigo-500/20
                    focus:outline-none transition-all cursor-pointer bg-white/5 rounded-xl border border-white/5 focus-within:border-indigo-500/50"
                />
              </div>
            </div>

            {/* Sternum Deflection Data Input */}
            <div className="space-y-2 group">
              <label className="block text-sm font-medium text-slate-300 group-focus-within:text-indigo-400 transition-colors">
                Sternum Deflection Data (Chest deflection.xlsx)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={(e) => setSternumFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-slate-400
                    file:mr-4 file:py-3 file:px-4
                    file:rounded-xl file:border-0
                    file:text-sm file:font-semibold
                    file:bg-indigo-500/10 file:text-indigo-400
                    hover:file:bg-indigo-500/20
                    focus:outline-none transition-all cursor-pointer bg-white/5 rounded-xl border border-white/5 focus-within:border-indigo-500/50"
                />
              </div>
            </div>

            {/* Pressure Sensor Data Input */}
            <div className="space-y-2 group">
              <label className="block text-sm font-medium text-slate-300 group-focus-within:text-indigo-400 transition-colors">
                Pressure Sensor Data (Multiple CSV files)
              </label>
              <div className="relative">
                <input
                  type="file"
                  multiple
                  accept=".csv"
                  onChange={(e) => setPressureFiles(e.target.files)}
                  className="block w-full text-sm text-slate-400
                    file:mr-4 file:py-3 file:px-4
                    file:rounded-xl file:border-0
                    file:text-sm file:font-semibold
                    file:bg-indigo-500/10 file:text-indigo-400
                    hover:file:bg-indigo-500/20
                    focus:outline-none transition-all cursor-pointer bg-white/5 rounded-xl border border-white/5 focus-within:border-indigo-500/50"
                />
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Select all the frame data CSV files exported from XSensor.
              </p>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-white/10">
            <button
              type="submit"
              disabled={isLoading || !cmmFile || !sternumFile || !pressureFiles}
              className="w-full relative group overflow-hidden rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-4 px-6 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing Pipeline...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Execute Calculator
                </span>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
