"use client";

import React, { useState } from "react";
import { StepEvent } from "../lib/api";

interface AgentStepTraceProps {
  steps: StepEvent[];
}

const STEP_META: Record<string, { icon: string; label: string; color: string; bg: string; border: string }> = {
  plan: { icon: "🧠", label: "Plan", color: "#818cf8", bg: "rgba(99,102,241,0.1)", border: "rgba(99,102,241,0.3)" },
  retrieval: { icon: "📚", label: "Retrieve", color: "#22d3ee", bg: "rgba(34,211,238,0.1)", border: "rgba(34,211,238,0.3)" },
  tool_call: { icon: "🔧", label: "Tool Call", color: "#fb923c", bg: "rgba(251,146,60,0.1)", border: "rgba(251,146,60,0.3)" },
  clarify: { icon: "💬", label: "Clarify", color: "#facc15", bg: "rgba(250,204,21,0.1)", border: "rgba(250,204,21,0.3)" },
};

export const AgentStepTrace: React.FC<AgentStepTraceProps> = ({ steps }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  if (!steps || steps.length === 0) return null;

  // Build compact summary
  const summaryParts: string[] = [];
  for (const s of steps) {
    if (s.step === "plan") {
      summaryParts.push(`Planned [${s.detail?.decision || "classify"}]`);
    } else if (s.step === "retrieval") {
      const chunks = s.detail?.chunks || [];
      const topScore = chunks.length > 0 ? chunks[0].score : "none";
      summaryParts.push(`Retrieved ${chunks.length} docs (score ${topScore})`);
    } else if (s.step === "tool_call") {
      const toolName = s.detail?.tool || "tool";
      summaryParts.push(`Called ${toolName}`);
    } else if (s.step === "clarify") {
      summaryParts.push("Clarification triggered");
    }
  }
  summaryParts.push("Answered");

  return (
    <div style={{
      borderRadius: "12px",
      border: "1px solid var(--border-subtle)",
      background: "rgba(8,12,24,0.6)",
      backdropFilter: "blur(10px)",
      overflow: "hidden",
      fontSize: "12px",
    }}>
      {/* Toggle header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: "100%",
          padding: "9px 13px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "var(--text-muted)",
          fontFamily: "inherit",
          textAlign: "left",
          borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none",
          transition: "background 0.15s",
        }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
        onMouseLeave={e => (e.currentTarget.style.background = "none")}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
          {/* Step pills in header */}
          <div style={{ display: "flex", gap: "4px", flexShrink: 0 }}>
            {steps.map((s, i) => {
              const meta = STEP_META[s.step] || { icon: "⚙️", color: "#94a3b8", bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.2)", label: s.step };
              return (
                <div key={i} style={{
                  width: "22px", height: "22px",
                  borderRadius: "6px",
                  background: meta.bg,
                  border: `1px solid ${meta.border}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "11px",
                }} title={meta.label}>
                  {meta.icon}
                </div>
              );
            })}
            <div style={{
              width: "22px", height: "22px",
              borderRadius: "6px",
              background: "rgba(16,185,129,0.1)",
              border: "1px solid rgba(16,185,129,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "11px",
            }}>✓</div>
          </div>
          <span style={{ color: "var(--text-muted)", fontSize: "11px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {summaryParts.join(" → ")}
          </span>
        </div>
        <span style={{ fontSize: "10px", color: "var(--text-muted)", flexShrink: 0, marginLeft: "8px" }}>
          {isOpen ? "▲" : "▼"} {isOpen ? "Hide" : "Trace"}
        </span>
      </button>

      {/* Expanded timeline */}
      {isOpen && (
        <div style={{ padding: "12px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", position: "relative" }}>
            {/* Vertical line */}
            <div style={{
              position: "absolute", left: "15px", top: "8px", bottom: "8px",
              width: "1px", background: "var(--border-subtle)",
            }} />

            {steps.map((st, idx) => {
              const meta = STEP_META[st.step] || { icon: "⚙️", color: "#94a3b8", bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.2)", label: st.step };
              return (
                <div key={idx} style={{ paddingLeft: "36px", position: "relative" }}>
                  {/* Step icon on timeline */}
                  <div style={{
                    position: "absolute", left: "6px", top: "8px",
                    width: "20px", height: "20px", borderRadius: "6px",
                    background: meta.bg, border: `1px solid ${meta.border}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "10px", zIndex: 1,
                  }}>
                    {meta.icon}
                  </div>

                  <div style={{
                    borderRadius: "10px",
                    border: `1px solid ${meta.border}`,
                    background: meta.bg,
                    overflow: "hidden",
                  }}>
                    <button
                      onClick={() => setSelectedStep(selectedStep === idx ? null : idx)}
                      style={{
                        width: "100%", padding: "8px 12px",
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                        background: "none", border: "none", cursor: "pointer",
                        fontFamily: "inherit", textAlign: "left",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{
                          fontSize: "10px", fontWeight: 700,
                          textTransform: "uppercase", letterSpacing: "0.08em",
                          color: meta.color,
                        }}>
                          Step {idx + 1} — {meta.label}
                        </span>
                        {st.step === "plan" && st.detail?.decision && (
                          <span style={{
                            fontSize: "10px", padding: "2px 7px", borderRadius: "999px",
                            background: meta.bg, border: `1px solid ${meta.border}`,
                            color: meta.color, fontWeight: 600,
                          }}>
                            {st.detail.decision}
                          </span>
                        )}
                        {st.step === "retrieval" && st.detail?.chunks && (
                          <span style={{
                            fontSize: "10px", padding: "2px 7px", borderRadius: "999px",
                            background: meta.bg, border: `1px solid ${meta.border}`,
                            color: meta.color, fontWeight: 600,
                          }}>
                            {st.detail.chunks.length} docs
                          </span>
                        )}
                        {st.step === "tool_call" && st.detail?.tool && (
                          <span style={{
                            fontSize: "10px", padding: "2px 7px", borderRadius: "999px",
                            background: meta.bg, border: `1px solid ${meta.border}`,
                            color: meta.color, fontWeight: 600,
                            fontFamily: "'JetBrains Mono', monospace",
                          }}>
                            {st.detail.tool}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {selectedStep === idx ? "▲" : "▼"} JSON
                      </span>
                    </button>

                    {selectedStep === idx && (
                      <pre style={{
                        margin: "0 12px 10px",
                        padding: "10px",
                        borderRadius: "8px",
                        background: "rgba(0,0,0,0.4)",
                        color: meta.color,
                        fontSize: "11px",
                        overflowX: "auto",
                        lineHeight: 1.6,
                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                        border: `1px solid ${meta.border}`,
                      }}>
                        {JSON.stringify(st.detail, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Final answered step */}
            <div style={{ paddingLeft: "36px", position: "relative" }}>
              <div style={{
                position: "absolute", left: "6px", top: "8px",
                width: "20px", height: "20px", borderRadius: "6px",
                background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.4)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "10px", zIndex: 1,
              }}>✓</div>
              <div style={{
                padding: "8px 12px", borderRadius: "10px",
                background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.25)",
              }}>
                <span style={{ fontSize: "10px", fontWeight: 700, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Response Delivered
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
