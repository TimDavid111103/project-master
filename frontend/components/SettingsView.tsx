"use client";

import { useState, useEffect, useRef } from "react";
import { AsteriskLogo } from "./AsteriskLogo";

const STORAGE_KEY = "project_master_user_tech_stack";

interface Props {
  onClose: () => void;
}

export function SettingsView({ onClose }: Props) {
  const [items, setItems] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setItems(JSON.parse(stored) as string[]);
    }
    inputRef.current?.focus();
  }, []);

  function save(next: string[]): void {
    setItems(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  function addItem(): void {
    const trimmed = input.trim();
    if (!trimmed || items.includes(trimmed)) return;
    save([...items, trimmed]);
    setInput("");
  }

  function removeItem(item: string): void {
    save(items.filter((i) => i !== item));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>): void {
    if (e.key === "Enter") {
      e.preventDefault();
      addItem();
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-20">
      {/* Header */}
      <div className="w-full max-w-2xl">
        <button
          onClick={onClose}
          className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-10 flex items-center gap-1 transition-colors"
        >
          ← Back
        </button>

        <div className="flex items-center gap-3 mb-2">
          <AsteriskLogo size={28} />
          <h1
            className="text-3xl font-semibold tracking-tight"
            style={{ fontFamily: "var(--font-lora), serif" }}
          >
            Settings
          </h1>
        </div>
        <p className="text-[var(--muted-foreground)] text-sm mb-12">
          Configure your preferences across all projects.
        </p>

        {/* Your tech stack section */}
        <div className="border border-[var(--border)] rounded-2xl bg-[var(--card)] p-6">
          <h2
            className="text-lg font-semibold mb-1"
            style={{ fontFamily: "var(--font-lora), serif" }}
          >
            Your tech stack
          </h2>
          <p className="text-[var(--muted-foreground)] text-sm mb-5">
            Technologies you already use. These will be heavily prioritised when
            generating tech stack recommendations for any new project.
          </p>

          {/* Input */}
          <div className="flex gap-2 mb-5">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. Next.js, PostgreSQL, Stripe…"
              className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
            />
            <button
              onClick={addItem}
              disabled={!input.trim()}
              className="px-5 py-2.5 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            >
              Add
            </button>
          </div>

          {/* Tag cloud */}
          {items.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)] italic">
              No technologies added yet.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {items.map((item) => (
                <TechTag key={item} label={item} onRemove={() => removeItem(item)} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TechTag({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--secondary)] text-sm font-medium text-[var(--foreground)]">
      {label}
      <button
        onClick={onRemove}
        aria-label={`Remove ${label}`}
        className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors leading-none"
      >
        ×
      </button>
    </span>
  );
}
