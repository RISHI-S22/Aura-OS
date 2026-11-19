"use client";

import React, { useState } from "react";

export default function HomePage() {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
      setResponse(await res.json());
    } catch (err) {
      setResponse({ error: "Failed to reach AURA Core API on port 8000" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-5xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-3">
        AURA
      </h1>
      <p className="text-neutral-400 mb-8">Autonomous Universal Reasoning Assistant — Command Cockpit</p>

      <form onSubmit={handleDispatch} className="w-full max-w-2xl flex gap-3 mb-6">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Enter an autonomous command..."
          className="flex-1 rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-3 text-white focus:border-cyan-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-cyan-600 px-6 py-3 font-semibold text-white hover:bg-cyan-500 disabled:opacity-50"
        >
          {loading ? "Executing..." : "Dispatch"}
        </button>
      </form>

      {response && (
        <pre className="w-full max-w-2xl overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-xs text-cyan-300">
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
    </main>
  );
}
