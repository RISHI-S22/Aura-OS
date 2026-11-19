"use client";

import React, { useState } from "react";

export default function HomePage() {
  const [command, setCommand] = useState("");
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    setLoading(true);
    setEvents([]);

    try {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws/commands");
      ws.onopen = () => {
        ws.send(JSON.stringify({ command }));
      };
      ws.onmessage = (msg) => {
        const parsed = JSON.parse(msg.data);
        setEvents((prev) => [...prev, parsed]);
        if (["completed", "pending_approval", "error"].includes(parsed.event)) {
          setLoading(false);
          ws.close();
        }
      };
      ws.onerror = async () => {
        const res = await fetch("http://127.0.0.1:8000/api/v1/commands", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command }),
        });
        setEvents([await res.json()]);
        setLoading(false);
      };
    } catch {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-5xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-3">
        AURA
      </h1>
      <p className="text-neutral-400 mb-8">Autonomous Universal Reasoning Assistant — Live Execution Cockpit</p>

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
          {loading ? "Streaming..." : "Dispatch"}
        </button>
      </form>

      <div className="w-full max-w-2xl space-y-3">
        {events.map((ev, idx) => (
          <pre
            key={idx}
            className="overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-xs text-cyan-300"
          >
            {JSON.stringify(ev, null, 2)}
          </pre>
        ))}
      </div>
    </main>
  );
}
