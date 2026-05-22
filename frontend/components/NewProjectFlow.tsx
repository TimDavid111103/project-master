"use client";

import { useState, useEffect } from "react";
import { useProjectSetup } from "@/hooks/useProjectSetup";
import type { UserAnswer } from "@/lib/types";

interface Props {
  onComplete: (projectId: string) => void;
  onCancel: () => void;
  existingProjectId?: string;
}

export function NewProjectFlow({ onComplete, onCancel, existingProjectId }: Props) {
  const setup = useProjectSetup();

  useEffect(() => {
    if (existingProjectId && setup.view === "idea") {
      setup.startExisting(existingProjectId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [existingProjectId]);

  if (setup.view === "idea" || (existingProjectId && setup.isLoading)) {
    // If existing project, show a loading state while setup/start is called
    if (existingProjectId) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <Spinner />
        </div>
      );
    }
    return (
      <IdeaForm
        onSubmit={setup.createAndStart}
        isLoading={setup.isLoading}
        error={setup.error}
        onCancel={onCancel}
      />
    );
  }

  if (setup.view === "qa") {
    return (
      <SetupQA
        questions={setup.questions}
        onSubmit={async (answers) => {
          const projectId = await setup.submitAnswers(answers);
          if (projectId) onComplete(projectId);
        }}
        isLoading={setup.isLoading}
        error={setup.error}
      />
    );
  }

  // "done" — shouldn't render (onComplete fires)
  return null;
}

function IdeaForm({
  onSubmit,
  isLoading,
  error,
  onCancel,
}: {
  onSubmit: (name: string, roughIdea: string) => void;
  isLoading: boolean;
  error: string | null;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [roughIdea, setRoughIdea] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (name.trim() && roughIdea.trim()) {
      onSubmit(name.trim(), roughIdea.trim());
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
        Describe your AI tool and we'll ask a few clarifying questions to
        understand its purpose.
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
            placeholder="e.g. Instagram Caption Generator"
            className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium" htmlFor="rough-idea">
            What is this tool trying to do?
          </label>
          <textarea
            id="rough-idea"
            value={roughIdea}
            onChange={(e) => setRoughIdea(e.target.value)}
            placeholder="Describe your AI tool's purpose, intended users, and what problems it solves..."
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
          {isLoading ? "Generating questions…" : "Continue"}
        </button>
      </form>
    </div>
  );
}

function SetupQA({
  questions,
  onSubmit,
  isLoading,
  error,
}: {
  questions: { question_id: string; question_text: string; rationale: string }[];
  onSubmit: (answers: UserAnswer[]) => void;
  isLoading: boolean;
  error: string | null;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>(
    Object.fromEntries(questions.map((q) => [q.question_id, ""]))
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const userAnswers: UserAnswer[] = questions.map((q) => ({
      question_id: q.question_id,
      answer_text: answers[q.question_id] ?? "",
    }));
    onSubmit(userAnswers);
  }

  const allAnswered = questions.every((q) => answers[q.question_id]?.trim());

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-20">
      <h2
        className="text-3xl font-semibold mb-2"
        style={{ fontFamily: "var(--font-lora), serif" }}
      >
        A few quick questions
      </h2>
      <p className="text-[var(--muted-foreground)] text-sm mb-8">
        Your answers help us build a project definition that improves every
        analysis session.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {questions.map((q, i) => (
          <div key={q.question_id} className="flex flex-col gap-1.5">
            <label
              className="text-sm font-medium"
              htmlFor={`sq-${q.question_id}`}
            >
              {i + 1}. {q.question_text}
            </label>
            <textarea
              id={`sq-${q.question_id}`}
              value={answers[q.question_id] ?? ""}
              onChange={(e) =>
                setAnswers((prev) => ({
                  ...prev,
                  [q.question_id]: e.target.value,
                }))
              }
              rows={3}
              className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
              placeholder="Your answer…"
            />
          </div>
        ))}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={isLoading || !allAnswered}
          className="self-end px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity flex items-center gap-2"
        >
          {isLoading ? <Spinner /> : null}
          {isLoading ? "Building project…" : "Create project"}
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
