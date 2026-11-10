import React from "react";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <div className="relative mb-6 flex items-center justify-center">
        <div className="absolute h-32 w-32 rounded-full bg-cyan-500/20 blur-xl animate-pulse"></div>
        <h1 className="text-6xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
          AURA
        </h1>
      </div>
      <p className="max-w-xl text-lg text-neutral-400">
        Autonomous Universal Reasoning Assistant — Command Center & Autonomous Agent Orchestration.
      </p>
      <div className="mt-8 flex gap-4">
        <span className="rounded-full border border-cyan-500/30 bg-cyan-950/30 px-4 py-1.5 text-sm font-mono text-cyan-300">
          Core Engine: Online
        </span>
        <span className="rounded-full border border-teal-500/30 bg-teal-950/30 px-4 py-1.5 text-sm font-mono text-teal-300">
          LangGraph: Active
        </span>
      </div>
    </main>
  );
}
