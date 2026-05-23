"use client";

import { useState, useEffect, useRef } from "react";
import { useIdeationChat } from "@/hooks/useIdeationChat";

interface Props {
  projectId: string;
  projectName: string;
  initialMessage: string;
  onComplete: () => void;
  onBack: () => void;
}

export function IdeationChatFlow({
  projectId,
  projectName,
  initialMessage,
  onComplete,
  onBack,
}: Props) {
  const chat = useIdeationChat(projectId);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    if (!hasStarted) {
      setHasStarted(true);
      chat.sendMessage(initialMessage);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (chat.view === "done") {
      onComplete();
    }
  }, [chat.view, onComplete]);

  if (chat.view === "analyzing") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Generating your project plan and tech stack…
        </p>
      </div>
    );
  }

  return (
    <ChatInterface
      projectName={projectName}
      messages={chat.messages}
      isLoading={chat.isLoading}
      error={chat.error}
      onSend={chat.sendMessage}
      onBack={onBack}
    />
  );
}

function ChatInterface({
  projectName,
  messages,
  isLoading,
  error,
  onSend,
  onBack,
}: {
  projectName: string;
  messages: { role: string; content: string }[];
  isLoading: boolean;
  error: string | null;
  onSend: (msg: string) => void;
  onBack: () => void;
}) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (trimmed && !isLoading) {
      setInput("");
      onSend(trimmed);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto px-4 py-20">
      <button
        onClick={onBack}
        className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-10 flex items-center gap-1 transition-colors self-start"
      >
        ← {projectName}
      </button>

      <h2
        className="text-3xl font-semibold mb-2"
        style={{ fontFamily: "var(--font-lora), serif" }}
      >
        Define your project
      </h2>
      <p className="text-[var(--muted-foreground)] text-sm mb-8">
        Answer a few questions so we can build your project plan and recommend the right tech stack.
      </p>

      {/* Message list */}
      <div className="flex flex-col gap-4 mb-6 flex-1">
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-[var(--muted-foreground)]">
            <Spinner size="sm" />
            <span className="text-sm">Thinking…</span>
          </div>
        )}
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 mt-auto">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          placeholder="Your answer… (Enter to send, Shift+Enter for new line)"
          disabled={isLoading}
          className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="self-end px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity flex items-center gap-2"
        >
          {isLoading ? <Spinner size="sm" /> : null}
          {isLoading ? "Waiting…" : "Send →"}
        </button>
      </form>
    </div>
  );
}

function MessageBubble({
  role,
  content,
}: {
  role: string;
  content: string;
}) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
            : "border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)]"
        }`}
      >
        {content}
      </div>
    </div>
  );
}

function Spinner({ size = "sm" }: { size?: "sm" | "lg" }) {
  const cls =
    size === "lg"
      ? "w-8 h-8 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin"
      : "w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin";
  return <span className={cls} />;
}
