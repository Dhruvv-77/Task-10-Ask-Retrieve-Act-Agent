"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { MessageBubble, ChatMessage } from "./MessageBubble";
import { sendChatMessage, StepEvent } from "../lib/api";

const SUGGESTED_PROMPTS = [
  "What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?",
  "What GPA is required for Dean's Honor List, and does STU-2045 qualify?",
  "Check course details and available seats for CS-301",
  "Register student STU-1001 for course AI-402",
];

export const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [currentSteps, setCurrentSteps] = useState<StepEvent[]>([]);
  const [activeStepLabel, setActiveStepLabel] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, currentSteps]);

  const handleSubmit = async (e: React.FormEvent | null, overrideText?: string) => {
    if (e) e.preventDefault();
    const userText = (overrideText || input).trim();
    if (!userText || isStreaming) return;

    setInput("");
    const userMsg: ChatMessage = { id: "user-" + Date.now(), role: "user", content: userText };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setCurrentSteps([]);
    setActiveStepLabel("Planning...");

    const assistantMsgId = "asst-" + Date.now();
    const tempSteps: StepEvent[] = [];

    await sendChatMessage(userText, conversationId, {
      onStep: (step) => {
        tempSteps.push(step);
        setCurrentSteps([...tempSteps]);
        const labels: Record<string, string> = {
          plan: "🧠 Planning & classifying intent...",
          retrieval: "📚 Retrieving from knowledge base...",
          tool_call: "🔧 Executing tool via MCP...",
          clarify: "💬 Generating clarification...",
        };
        setActiveStepLabel(labels[step.step] || "⚙️ Processing...");
      },
      onFinal: (final) => {
        setConversationId(final.conversation_id);
        const assistantMsg: ChatMessage = {
          id: final.message_id || assistantMsgId,
          role: "assistant",
          content: final.content,
          steps: [...tempSteps],
          sources_used: final.sources_used,
          tools_used: final.tools_used,
          needs_clarification: final.needs_clarification,
        };
        setMessages(prev => [...prev, assistantMsg]);
        setCurrentSteps([]);
        setActiveStepLabel("");
        setIsStreaming(false);
        setTimeout(() => inputRef.current?.focus(), 100);
      },
      onError: (err) => {
        const errorMsg: ChatMessage = {
          id: assistantMsgId,
          role: "assistant",
          content: `⚠️ Error: ${err.message}`,
          steps: [...tempSteps],
        };
        setMessages(prev => [...prev, errorMsg]);
        setCurrentSteps([]);
        setActiveStepLabel("");
        setIsStreaming(false);
      },
    });
  };

  const isEmpty = messages.length === 0;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      width: "100%",
      background: "var(--bg-base)",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Animated background orbs */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden"
      }}>
        <div style={{
          position: "absolute", top: "-20%", left: "-10%",
          width: "600px", height: "600px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)",
          animation: "orbFloat 18s ease-in-out infinite",
        }} />
        <div style={{
          position: "absolute", bottom: "-15%", right: "-10%",
          width: "500px", height: "500px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(34,211,238,0.08) 0%, transparent 70%)",
          animation: "orbFloat 22s ease-in-out infinite reverse",
        }} />
      </div>

      {/* Header */}
      <header style={{
        position: "relative", zIndex: 10,
        padding: "14px 28px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(11,16,32,0.85)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          {/* Logo */}
          <div style={{
            width: "38px", height: "38px", borderRadius: "10px",
            background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "18px", flexShrink: 0,
            boxShadow: "0 0 20px rgba(99,102,241,0.4)",
          }}>✦</div>
          <div>
            <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
              University Campus Agent
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
              LangGraph · Ollama · University RAG · MCP Tools
            </div>
          </div>
        </div>

        {/* Status pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {[
            { label: "Ollama", color: "var(--accent-green)" },
            { label: "MCP :9000", color: "var(--accent-cyan)" },
            { label: "Redis", color: "var(--accent-orange)" },
          ].map(s => (
            <div key={s.label} style={{
              display: "flex", alignItems: "center", gap: "5px",
              padding: "4px 10px",
              borderRadius: "999px",
              background: "var(--bg-glass)",
              border: "1px solid var(--border-subtle)",
              fontSize: "11px",
              color: "var(--text-secondary)",
              fontWeight: 500,
            }}>
              <span style={{
                width: "6px", height: "6px", borderRadius: "50%",
                background: s.color,
                boxShadow: `0 0 6px ${s.color}`,
                animation: "pulse-glow 2s ease-in-out infinite",
              }} />
              {s.label}
            </div>
          ))}
        </div>
      </header>

      {/* Message area */}
      <div style={{
        position: "relative", zIndex: 5,
        flex: 1,
        overflowY: "auto",
        padding: "28px 20px",
        display: "flex",
        flexDirection: "column",
        maxWidth: "860px",
        width: "100%",
        margin: "0 auto",
        alignSelf: "stretch",
      }}>
        {isEmpty ? (
          /* Welcome screen */
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            gap: "32px", textAlign: "center",
            animation: "fadeSlideIn 0.6s ease",
          }}>
            <div>
              <div style={{
                width: "70px", height: "70px", borderRadius: "20px",
                background: "linear-gradient(135deg, #4f46e5, #7c3aed, #22d3ee)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "32px", margin: "0 auto 20px",
                boxShadow: "0 0 40px rgba(99,102,241,0.35), 0 0 80px rgba(99,102,241,0.1)",
              }}>🎓</div>
              <h1 style={{
                fontSize: "28px", fontWeight: 800, letterSpacing: "-0.03em",
                background: "linear-gradient(135deg, #f1f5f9 30%, #818cf8)",
                WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                marginBottom: "10px",
              }}>
                University Campus AI Agent
              </h1>
              <p style={{ color: "var(--text-secondary)", fontSize: "14px", maxWidth: "440px", lineHeight: 1.6 }}>
                Ask me about university academic policies, grading scales, exam attendance rules, course catalog lookup, or student records — powered by local Ollama AI.
              </p>
            </div>

            {/* Capability tags */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
              {[
                { icon: "📚", text: "RAG Knowledge Base" },
                { icon: "🔧", text: "MCP Tool Calling" },
                { icon: "🧠", text: "Local Ollama AI" },
                { icon: "🔒", text: "Human-in-the-Loop" },
              ].map(c => (
                <div key={c.text} style={{
                  display: "flex", alignItems: "center", gap: "6px",
                  padding: "6px 14px", borderRadius: "999px",
                  background: "var(--bg-glass)", border: "1px solid var(--border-medium)",
                  fontSize: "12px", color: "var(--text-secondary)", fontWeight: 500,
                }}>
                  <span>{c.icon}</span> {c.text}
                </div>
              ))}
            </div>

            {/* Suggested prompts */}
            <div style={{ width: "100%", maxWidth: "640px" }}>
              <p style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 }}>Try these</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                {SUGGESTED_PROMPTS.map(p => (
                  <button key={p}
                    onClick={() => handleSubmit(null, p)}
                    style={{
                      padding: "12px 14px",
                      borderRadius: "12px",
                      border: "1px solid var(--border-medium)",
                      background: "var(--bg-glass)",
                      color: "var(--text-secondary)",
                      fontSize: "12px",
                      textAlign: "left",
                      cursor: "pointer",
                      lineHeight: 1.4,
                      transition: "all 0.2s ease",
                      fontFamily: "inherit",
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.background = "var(--bg-glass-hover)";
                      (e.currentTarget as HTMLElement).style.borderColor = "var(--border-accent)";
                      (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.background = "var(--bg-glass)";
                      (e.currentTarget as HTMLElement).style.borderColor = "var(--border-medium)";
                      (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                    }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </>
        )}

        {/* Live streaming indicator */}
        {isStreaming && (
          <div className="animate-in" style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
            <div style={{
              display: "inline-flex", alignItems: "center", gap: "10px",
              padding: "12px 18px", borderRadius: "18px 18px 18px 4px",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              width: "fit-content", maxWidth: "80%",
            }}>
              <div style={{ display: "flex", gap: "4px" }}>
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
              <span style={{ fontSize: "13px", color: "var(--text-secondary)", fontWeight: 500 }}>
                {activeStepLabel}
              </span>
            </div>
            {currentSteps.length > 0 && (
              <div style={{ display: "flex", gap: "5px", flexWrap: "wrap", paddingLeft: "4px" }}>
                {currentSteps.map((s, i) => (
                  <div key={i} style={{
                    padding: "3px 9px",
                    borderRadius: "999px",
                    background: "rgba(99,102,241,0.1)",
                    border: "1px solid rgba(99,102,241,0.3)",
                    fontSize: "10px",
                    color: "var(--accent-blue-light)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}>
                    ✓ {s.step}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div style={{
        position: "relative", zIndex: 10,
        padding: "16px 20px 20px",
        background: "rgba(11,16,32,0.90)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderTop: "1px solid var(--border-subtle)",
      }}>
        <form onSubmit={handleSubmit}
          style={{
            maxWidth: "860px", margin: "0 auto",
            display: "flex", gap: "10px", alignItems: "flex-end",
          }}
        >
          <div style={{ flex: 1, position: "relative" }}>
            <input
              ref={inputRef}
              type="text"
              id="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about university policies, course details, or student records…"
              disabled={isStreaming}
              autoComplete="off"
              style={{
                width: "100%",
                padding: "14px 20px",
                borderRadius: "14px",
                border: "1px solid var(--border-medium)",
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontSize: "14px",
                outline: "none",
                fontFamily: "inherit",
                transition: "border-color 0.2s ease, box-shadow 0.2s ease",
              }}
              onFocus={e => {
                e.currentTarget.style.borderColor = "var(--accent-blue)";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.15)";
              }}
              onBlur={e => {
                e.currentTarget.style.borderColor = "var(--border-medium)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>
          <button
            id="send-button"
            type="submit"
            disabled={isStreaming || !input.trim()}
            style={{
              padding: "14px 22px",
              borderRadius: "14px",
              border: "none",
              background: isStreaming || !input.trim()
                ? "var(--bg-elevated)"
                : "linear-gradient(135deg, #4f46e5, #7c3aed)",
              color: isStreaming || !input.trim() ? "var(--text-muted)" : "#fff",
              fontSize: "14px",
              fontWeight: 600,
              cursor: isStreaming || !input.trim() ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", gap: "8px",
              transition: "all 0.2s ease",
              boxShadow: isStreaming || !input.trim() ? "none" : "0 0 20px rgba(99,102,241,0.3)",
              flexShrink: 0,
              fontFamily: "inherit",
            }}
          >
            {isStreaming ? (
              <><span className="spinner">⟳</span> Processing</>
            ) : (
              <><span>↑</span> Send</>
            )}
          </button>
        </form>
        <p style={{ textAlign: "center", fontSize: "11px", color: "var(--text-muted)", marginTop: "10px" }}>
          Powered by local Ollama · <span style={{ color: "var(--accent-blue-light)" }}>qwen2.5:7b-instruct</span> · 100% offline & private
        </p>
      </div>
    </div>
  );
};
