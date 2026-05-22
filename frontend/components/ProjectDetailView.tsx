"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { ProjectHistoryResponse, PromptSessionRecord } from "@/lib/types";

interface Props {
  projectId: string;
  onBack: () => void;
  onAnalyzePrompt: () => void;
  onRunSetup: () => void;
}

export function ProjectDetailView({
  projectId,
  onBack,
  onAnalyzePrompt,
  onRunSetup,
}: Props) {
  const [data, setData] = useState<ProjectHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api
      .projectHistory(projectId)
      .then((d) => {
        setData(d);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load project.");
        setIsLoading(false);
      });
  }, [projectId]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-600 text-sm">{error ?? "Project not found."}</p>
        <button
          onClick={onBack}
          className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        >
          ← Back
        </button>
      </div>
    );
  }

  const needsSetup = !data.definition;

  return (
    <div className="min-h-screen flex flex-col max-w-3xl mx-auto px-4 py-20">
      {/* Back */}
      <button
        onClick={onBack}
        className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-10 flex items-center gap-1 transition-colors self-start"
      >
        ← All projects
      </button>

      {/* Project header */}
      <div className="mb-8">
        <h2
          className="text-3xl font-semibold mb-1"
          style={{ fontFamily: "var(--font-lora), serif" }}
        >
          {data.name}
        </h2>
        <p className="text-[var(--muted-foreground)] text-sm">{data.rough_idea}</p>
      </div>

      {/* Definition card */}
      {data.definition ? (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 mb-8">
          <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
            Project definition
          </p>
          <p className="text-sm leading-relaxed">{data.definition}</p>
        </div>
      ) : (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 mb-8 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-amber-800 mb-1">
              Project setup incomplete
            </p>
            <p className="text-xs text-amber-700">
              Complete the setup Q&A to enable memory-powered analysis sessions.
            </p>
          </div>
          <button
            onClick={onRunSetup}
            className="shrink-0 text-sm font-medium text-amber-800 border border-amber-300 rounded-lg px-3 py-1.5 hover:bg-amber-100 transition-colors"
          >
            Complete setup
          </button>
        </div>
      )}

      {/* Analyze button */}
      <div className="mb-10">
        <button
          onClick={onAnalyzePrompt}
          disabled={needsSetup}
          className="px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
        >
          Analyze a prompt
        </button>
      </div>

      {/* Past sessions */}
      {data.sessions.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-4">
            Past sessions
          </h3>
          <div className="flex flex-col gap-3">
            {data.sessions.map((session) => (
              <SessionCard
                key={session.session_id}
                session={session}
                isExpanded={expanded === session.session_id}
                onToggle={() =>
                  setExpanded((prev) =>
                    prev === session.session_id ? null : session.session_id
                  )
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SessionCard({
  session,
  isExpanded,
  onToggle,
}: {
  session: PromptSessionRecord;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const t = session.intent_translation;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full text-left px-5 py-4 flex items-start justify-between gap-4 hover:bg-[var(--secondary)] transition-colors"
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium line-clamp-2">{session.original_prompt}</p>
          <p className="text-xs text-[var(--muted-foreground)] mt-0.5">
            {formatDate(session.created_at)}
          </p>
        </div>
        <span className="text-[var(--muted-foreground)] text-sm shrink-0">
          {isExpanded ? "↑" : "↓"}
        </span>
      </button>

      {isExpanded && (
        <div className="px-5 pb-5 border-t border-[var(--border)] pt-4 flex flex-col gap-4">
          <div>
            <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-1.5">
              What it instructs
            </p>
            <p className="text-sm leading-relaxed">{t.what_the_prompt_instructs}</p>
          </div>

          {t.assumptions_made.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-1.5">
                Assumptions made
              </p>
              <ul className="flex flex-col gap-1">
                {t.assumptions_made.map((a, i) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-[var(--accent)] shrink-0">•</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {t.potential_gaps.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-1.5">
                Potential gaps
              </p>
              <ul className="flex flex-col gap-1">
                {t.potential_gaps.map((g, i) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-[var(--muted-foreground)] shrink-0">○</span>
                    {g}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div className="w-6 h-6 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
