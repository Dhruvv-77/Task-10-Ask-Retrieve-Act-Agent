"use client";

import React from "react";
import { StepEvent } from "../lib/api";
import { AgentStepTrace } from "./AgentStepTrace";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: StepEvent[];
  sources_used?: string[];
  tools_used?: string[];
  needs_clarification?: boolean;
}

interface MessageBubbleProps {
  message: ChatMessage;
}

const SOURCE_COLORS = [
  { bg: "rgba(16,185,129,0.12)", border: "rgba(16,185,129,0.3)", text: "#6ee7b7" },
  { bg: "rgba(34,211,238,0.12)", border: "rgba(34,211,238,0.3)", text: "#67e8f9" },
  { bg: "rgba(168,85,247,0.12)", border: "rgba(168,85,247,0.3)", text: "#d8b4fe" },
];

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div
      className="animate-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: "20px",
        width: "100%",
      }}
    >
      {/* Role label */}
      <div style={{
        fontSize: "10px",
        fontWeight: 600,
        color: "var(--text-muted)",
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom: "5px",
        paddingLeft: isUser ? 0 : "4px",
        paddingRight: isUser ? "4px" : 0,
      }}>
        {isUser ? "You" : "✦ Agent"}
      </div>

      <div style={{ maxWidth: "80%", display: "flex", flexDirection: "column", gap: "8px" }}>
        {/* Main bubble */}
        <div
          style={{
            padding: "14px 18px",
            borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
            background: isUser
              ? "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)"
              : "var(--bg-elevated)",
            color: "var(--text-primary)",
            fontSize: "14px",
            lineHeight: "1.65",
            boxShadow: isUser
              ? "0 4px 20px rgba(99,102,241,0.35)"
              : "var(--shadow-md)",
            border: isUser ? "none" : "1px solid var(--border-subtle)",
            whiteSpace: "pre-wrap",
            fontWeight: 400,
          }}
        >
          {message.content}

          {/* Clarification badge */}
          {message.needs_clarification && (
            <div style={{
              marginTop: "12px",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "8px",
              background: "rgba(245,158,11,0.15)",
              border: "1px solid rgba(245,158,11,0.35)",
              fontSize: "12px",
              fontWeight: 600,
              color: "#fcd34d",
            }}>
              ⏳ Waiting for your clarification
            </div>
          )}
        </div>

        {/* Source & Tool badges */}
        {!isUser && ((message.sources_used && message.sources_used.length > 0) || (message.tools_used && message.tools_used.length > 0)) && (
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", paddingLeft: "2px" }}>
            {message.sources_used?.map((src, i) => {
              const c = SOURCE_COLORS[i % SOURCE_COLORS.length];
              return (
                <div key={src} style={{
                  display: "flex", alignItems: "center", gap: "5px",
                  padding: "4px 10px",
                  borderRadius: "999px",
                  background: c.bg,
                  border: `1px solid ${c.border}`,
                  fontSize: "11px",
                  color: c.text,
                  fontWeight: 500,
                }}>
                  <span style={{ fontSize: "10px" }}>📄</span> {src}
                </div>
              );
            })}
            {message.tools_used?.map(tl => (
              <div key={tl} style={{
                display: "flex", alignItems: "center", gap: "5px",
                padding: "4px 10px",
                borderRadius: "999px",
                background: "rgba(249,115,22,0.12)",
                border: "1px solid rgba(249,115,22,0.3)",
                fontSize: "11px",
                color: "#fdba74",
                fontWeight: 500,
              }}>
                <span style={{ fontSize: "10px" }}>🔧</span> {tl}
              </div>
            ))}
          </div>
        )}

        {/* Agent Step Trace */}
        {!isUser && message.steps && message.steps.length > 0 && (
          <AgentStepTrace steps={message.steps} />
        )}
      </div>
    </div>
  );
};
