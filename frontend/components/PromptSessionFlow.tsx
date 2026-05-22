"use client";

import { useState } from "react";
import { useSession } from "@/hooks/useSession";
import type { IntentTranslation, UserAnswer } from "@/lib/types";

interface Props {
  projectId: string;
  projectName: string;
  onBack: () => void;
}

export function PromptSessionFlow({ projectId, projectName, onBack }: Props) {
  const session = useSession(projectId);

  if (session.view === "input") {
    return (
      <PromptInput
        projectName={projectName}
        onSubmit={session.submitPrompt}
        isLoading={session.isLoading}
        error={session.error}
        onBack={onBack}
      />
    );
  }

  if (session.view === "qa") {
    return (
      <QAPanel
        questions={session.questions}
        onSubmit={session.submitAnswers}
        isLoading={session.isLoading}
        error={session.error}
      />
    );
  }

  if (session.view === "results" && session.result) {
    return (
      <ResultsView
        prompt={session.result.original_prompt}
        translation={session.result.intent_translation}
        onAnalyzeAnother={() => {
          session.reset();
        }}
        onBackToProject={onBack}
      />
    );
  }

  return null;
}

function PromptInput({
  projectName,
  onSubmit,
  isLoading,
  error,
  onBack,
}: {
  projectName: string;
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
  error: string | null;
  onBack: () => void;
}) {
  const [prompt, setPrompt] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (prompt.trim()) onSubmit(prompt.trim());
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
        Analyze a prompt
      </h2>
      <p className="text-[var(--muted-foreground)] text-sm mb-8">
        Paste the system prompt you want to analyze. We'll ask a few questions,
        then give you a structured interpretation.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={10}
          placeholder="You are a helpful assistant…"
          className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 text-sm placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none font-mono"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={isLoading || !prompt.trim()}
          className="self-end px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity flex items-center gap-2"
        >
          {isLoading ? <Spinner /> : null}
          {isLoading ? "Generating questions…" : "Analyze →"}
        </button>
      </form>
    </div>
  );
}

function QAPanel({
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
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto px-4 py-20">
      <h2
        className="text-3xl font-semibold mb-2"
        style={{ fontFamily: "var(--font-lora), serif" }}
      >
        A few questions
      </h2>
      <p className="text-[var(--muted-foreground)] text-sm mb-8">
        Help us understand the context behind this prompt.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {questions.map((q, i) => (
          <div key={q.question_id} className="flex flex-col gap-1.5">
            <label
              className="text-sm font-medium"
              htmlFor={`q-${q.question_id}`}
            >
              {i + 1}. {q.question_text}
            </label>
            <textarea
              id={`q-${q.question_id}`}
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
          {isLoading ? "Analyzing prompt…" : "Get analysis →"}
        </button>
      </form>
    </div>
  );
}

function ResultsView({
  prompt,
  translation,
  onAnalyzeAnother,
  onBackToProject,
}: {
  prompt: string;
  translation: IntentTranslation;
  onAnalyzeAnother: () => void;
  onBackToProject: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto px-4 py-20">
      <h2
        className="text-3xl font-semibold mb-8"
        style={{ fontFamily: "var(--font-lora), serif" }}
      >
        Analysis
      </h2>

      {/* Original prompt */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 mb-6">
        <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
          Prompt
        </p>
        <p className="text-sm font-mono leading-relaxed whitespace-pre-wrap">
          {prompt}
        </p>
      </div>

      {/* What it instructs */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 mb-4">
        <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
          What it instructs
        </p>
        <p className="text-sm leading-relaxed">
          {translation.what_the_prompt_instructs}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {/* Assumptions */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
          <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-3">
            Assumptions made
          </p>
          {translation.assumptions_made.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {translation.assumptions_made.map((a, i) => (
                <li key={i} className="text-sm flex gap-2">
                  <span className="text-[var(--accent)] shrink-0 mt-0.5">•</span>
                  {a}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">None identified</p>
          )}
        </div>

        {/* Gaps */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
          <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-3">
            Potential gaps
          </p>
          {translation.potential_gaps.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {translation.potential_gaps.map((g, i) => (
                <li key={i} className="text-sm flex gap-2">
                  <span className="text-[var(--muted-foreground)] shrink-0 mt-0.5">○</span>
                  {g}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">None identified</p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <button
          onClick={onAnalyzeAnother}
          className="px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Analyze another prompt
        </button>
        <button
          onClick={onBackToProject}
          className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          Back to project
        </button>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
  );
}
