"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface Props {
  onComplete: (projectId: string, projectName: string, roughIdea: string) => void;
  onCancel: () => void;
}

export function NewProjectFlow({ onComplete, onCancel }: Props) {
  const [name, setName] = useState("");
  const [roughIdea, setRoughIdea] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !roughIdea.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const project = await api.createProject({
        name: name.trim(),
        rough_idea: roughIdea.trim(),
      });
      onComplete(project.project_id, name.trim(), roughIdea.trim());
    } catch (err) {
      setIsLoading(false);
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-20">
      <button
        onClick={onCancel}
        className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-10 flex items-center gap-1 transition-colors"
      >
        ← Back
      </button>

      <h2
        className="text-3xl font-semibold mb-2"
        style={{ fontFamily: "var(--font-lora), serif" }}
      >
        New project
      </h2>
      <p className="text-[var(--muted-foreground)] text-sm mb-8">
        Describe your idea and we'll guide you through defining your project plan and tech stack.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium" htmlFor="project-name">
            Project name
          </label>
          <input
            id="project-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Freelance Invoice Tracker"
            className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium" htmlFor="rough-idea">
            What is your idea?
          </label>
          <textarea
            id="rough-idea"
            value={roughIdea}
            onChange={(e) => setRoughIdea(e.target.value)}
            placeholder="Describe what you want to build and what problem it solves…"
            rows={5}
            className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <button
          type="submit"
          disabled={isLoading || !name.trim() || !roughIdea.trim()}
          className="self-end px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity flex items-center gap-2"
        >
          {isLoading ? <Spinner /> : null}
          {isLoading ? "Creating project…" : "Start →"}
        </button>
      </form>
    </div>
  );
}

function Spinner() {
  return (
    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
  );
}
