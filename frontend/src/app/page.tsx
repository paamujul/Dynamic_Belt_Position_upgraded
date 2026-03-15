"use client";

import { useState } from "react";

export default function Home() {
  const [timeFrame, setTimeFrame] = useState("0.05");
  const [masterFile, setMasterFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{
    excelUrl?: string;
    animationUrl?: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!masterFile) {
      setMessage("Please upload a master CSV file.");
      return;
    }

    setLoading(true);
    setMessage("Processing... this might take a minute as it runs the pipeline.");
    setResults(null);

    const formData = new FormData();
    formData.append("time_frame", timeFrame);
    formData.append("master_file", masterFile);

    try {
      const res = await fetch("http://localhost:8000/api/run", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to run pipeline");
      }

      const data = await res.json();
      setMessage(data.message);
      setResults({
        excelUrl: `http://localhost:8000${data.vertical_distances_path}`,
        animationUrl: `http://localhost:8000${data.output_dir}`,
      });
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center">
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
            Dynamic Belt Position Pipeline
          </h1>
          <p className="text-gray-400">Process XSENSOR frames and calculate belt positions</p>
        </header>

        <section className="bg-gray-800 rounded-2xl p-6 shadow-xl border border-gray-700">
          <h2 className="text-2xl font-semibold mb-4 text-blue-400">Basic Instructions</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-300">
            <li>Upload your master XSENSOR CSV file containing sequentially stacked frames.</li>
            <li>Input the target Time Frame (e.g. <code className="bg-gray-900 px-1 rounded text-pink-400">0.05</code>) you wish to isolate.</li>
            <li>The system will extract that frame, reset its time to 0, and run the pipeline.</li>
            <li>Results will appear below once processing is complete.</li>
          </ul>
        </section>

        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-2xl p-6 shadow-xl border border-gray-700 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Time Frame
              </label>
              <input
                type="number"
                step="0.01"
                value={timeFrame}
                onChange={(e) => setTimeFrame(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Master CSV File
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setMasterFile(e.target.files[0]);
                  }
                }}
                className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white file:mr-4 file:py-1 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 transition"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg font-bold text-lg transition-all ${
              loading 
                ? "bg-gray-600 cursor-not-allowed" 
                : "bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-400 hover:to-purple-500 hover:shadow-lg hover:shadow-blue-500/25"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running Pipeline...
              </span>
            ) : (
              "Run Pipeline"
            )}
          </button>
        </form>

        {message && (
          <div className="p-4 rounded-lg bg-gray-800 border-l-4 border-blue-500 text-gray-200">
            {message}
          </div>
        )}

        {results && (
          <div className="bg-gray-800 rounded-2xl p-6 shadow-xl border border-gray-700 space-y-6 animate-fade-in">
            <h3 className="text-2xl font-bold border-b border-gray-700 pb-2">Results</h3>
            
            <div className="flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4">
              <a 
                href={results.excelUrl} 
                download
                className="flex-1 bg-gray-900 border border-gray-600 rounded-xl p-4 hover:border-blue-500 transition group flex items-center justify-between"
              >
                <div>
                  <h4 className="font-semibold text-blue-400 group-hover:text-blue-300">Vertical Distances</h4>
                  <p className="text-sm text-gray-400 mt-1">Download the generated Excel file</p>
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
              </a>
              
              <a 
                href={results.animationUrl} 
                download
                className="flex-1 bg-gray-900 border border-gray-600 rounded-xl p-4 hover:border-purple-500 transition group flex items-center justify-between"
              >
                <div>
                  <h4 className="font-semibold text-purple-400 group-hover:text-purple-300">Belt Position Animation</h4>
                  <p className="text-sm text-gray-400 mt-1">View the generated MP4/GIF output</p>
                </div>
                <svg className="w-6 h-6 text-gray-400 group-hover:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </a>
            </div>
            
            <div className="mt-6">
              <h4 className="text-lg font-medium text-gray-300 mb-2">Animation Preview</h4>
              <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700 flex items-center justify-center p-4">
                 <video controls src={results.animationUrl} className="max-w-full rounded-md shadow-lg h-auto max-h-96" />
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
