"use client";

import React, { useState } from "react";

export default function HomePage() {
  const [command, setCommand] = useState("");
  const [liveMode, setLiveMode] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    setLoading(true);
    setEvents([]);
    setPendingSessionId(null);

    try {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws/commands");
      ws.onopen = () => {
        ws.send(JSON.stringify({ command, live_mode: liveMode }));
      };
      ws.onmessage = (msg) => {
        const parsed = JSON.parse(msg.data);
        setEvents((prev) => [...prev, parsed]);
        if (parsed.event === "pending_approval") {
          setPendingSessionId(parsed.session_id);
        }
        if (["completed", "pending_approval", "error"].includes(parsed.event)) {
          setLoading(false);
          ws.close();
        }
      };
      ws.onerror = async () => {
        const res = await fetch("http://127.0.0.1:8000/api/v1/commands", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command, live_mode: liveMode }),
        });
        const data = await res.json();
        setEvents([data]);
        if (data.status === "pending_approval") {
          setPendingSessionId(data.session_id);
        }
        setLoading(false);
      };
    } catch {
      setLoading(false);
    }
  };

  const handleApproveAndResume = async () => {
    if (!pendingSessionId) return;
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/sessions/${pendingSessionId}/resume`, {
        method: "POST",
      });
      const resumed = await res.json();
      setEvents((prev) => [...prev, { event: "resumed_completed", ...resumed }]);
      setPendingSessionId(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-5xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-3">
        AURA
      </h1>
      <p className="text-neutral-400 mb-6">Autonomous Universal Reasoning Assistant — Live Execution Cockpit</p>

      <form onSubmit={handleDispatch} className="w-full max-w-2xl space-y-3 mb-6">
        <div className="flex gap-3">
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
        </div>
        <label className="flex items-center gap-2 text-xs text-neutral-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={liveMode}
            onChange={(e) => setLiveMode(e.target.checked)}
            className="rounded border-neutral-700 bg-neutral-900 text-cyan-500"
          />
          Enable Live OS / Browser Actuation (uncheck for Safe Dry-Run)
        </label>
      </form>

      {pendingSessionId && (
        <div className="w-full max-w-2xl mb-4 flex items-center justify-between rounded-lg border border-amber-500/40 bg-amber-950/30 p-4">
          <span className="text-sm text-amber-200">
            Session <strong>{pendingSessionId}</strong> paused at human-in-the-loop approval gate.
          </span>
          <button
            onClick={handleApproveAndResume}
            disabled={loading}
            className="rounded-md bg-amber-500 px-4 py-2 text-xs font-bold text-black hover:bg-amber-400"
          >
            Approve &amp; Resume
          </button>
        </div>
      )}

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
