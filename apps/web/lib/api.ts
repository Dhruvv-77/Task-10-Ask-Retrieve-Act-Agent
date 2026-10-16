export interface StepEvent {
  type: "step";
  step: "plan" | "retrieval" | "tool_call" | "clarify";
  detail: any;
}

export interface FinalEvent {
  type: "final";
  content: string;
  sources_used: string[];
  tools_used: string[];
  conversation_id: string;
  message_id?: string;
  needs_clarification?: boolean;
}

export interface StreamCallbacks {
  onStep: (step: StepEvent) => void;
  onFinal: (final: FinalEvent) => void;
  onError: (err: Error) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(
  message: string,
  conversationId: string | null,
  callbacks: StreamCallbacks
) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat API responded with HTTP ${response.status}`);
    }

    if (!response.body) {
      throw new Error("ReadableStream not supported by browser/environment.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;
        const lines = block.split("\n");
        let eventType = "message";
        let dataStr = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.substring(7).trim();
          } else if (line.startsWith("data: ")) {
            dataStr = line.substring(6).trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          if (eventType === "step") {
            callbacks.onStep(parsed as StepEvent);
          } else if (eventType === "final") {
            callbacks.onFinal(parsed as FinalEvent);
          } else if (eventType === "error") {
            callbacks.onError(new Error(parsed.detail || "Server error in stream"));
          }
        } catch (jsonErr) {
          console.warn("Failed to parse SSE event payload:", dataStr, jsonErr);
        }
      }
    }
  } catch (err: any) {
    callbacks.onError(err);
  }
}
