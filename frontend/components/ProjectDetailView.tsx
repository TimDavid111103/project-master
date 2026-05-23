"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { ProjectDetailResponse, TechStackItem } from "@/lib/types";

interface Props {
  projectId: string;
  onBack: () => void;
  onStartChat: (roughIdea: string) => void;
}

export function ProjectDetailView({ projectId, onBack, onStartChat }: Props) {
  const [data, setData] = useState<ProjectDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api
      .getProject(projectId)
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

  return (
    <div className="min-h-screen flex flex-col max-w-3xl mx-auto px-4 py-20">
      <button
        onClick={onBack}
        className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-10 flex items-center gap-1 transition-colors self-start"
      >
        ← All projects
      </button>

      {/* Header */}
      <div className="mb-8">
        <h2
          className="text-3xl font-semibold mb-1"
          style={{ fontFamily: "var(--font-lora), serif" }}
        >
          {data.name}
        </h2>
        <p className="text-[var(--muted-foreground)] text-sm">{data.rough_idea}</p>
      </div>

      {/* Incomplete state */}
      {!data.is_complete && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 mb-8 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-amber-800 mb-1">
              Project planning incomplete
            </p>
            <p className="text-xs text-amber-700">
              Continue the conversation to generate your project plan and tech stack.
            </p>
          </div>
          <button
            onClick={() => onStartChat(data.rough_idea)}
            className="shrink-0 text-sm font-medium text-amber-800 border border-amber-300 rounded-lg px-3 py-1.5 hover:bg-amber-100 transition-colors"
          >
            Continue planning
          </button>
        </div>
      )}

      {/* Project plan */}
      {data.project_plan && (
        <div className="mb-8">
          <h3 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-4">
            Project plan
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <PlanCard label="Vision" value={data.project_plan.vision} />
            <PlanCard label="Target audience" value={data.project_plan.target_audience} />
            <PlanCard label="Problem addressed" value={data.project_plan.problem_addressed} />
            <PlanCard label="MVP scope" value={data.project_plan.mvp_scope} />
          </div>
        </div>
      )}

      {/* Tech stack */}
      {data.tech_stack && (
        <>
          <div className="mb-8">
            <h3 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-4">
              MVP tech stack
            </h3>
            <TechStackGrid items={data.tech_stack.mvp} />
          </div>

          <div>
            <h3 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-4">
              Full product tech stack
            </h3>
            <TechStackGrid items={data.tech_stack.full_product} />
          </div>
        </>
      )}
    </div>
  );
}

function PlanCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
        {label}
      </p>
      <p className="text-sm leading-relaxed">{value}</p>
    </div>
  );
}

function TechStackGrid({ items }: { items: TechStackItem[] }) {
  return (
    <div className="flex flex-col gap-3">
      {items.map((item, i) => (
        <div
          key={i}
          className="rounded-xl border border-[var(--border)] bg-[var(--card)] px-5 py-4"
        >
          <div className="flex items-start justify-between gap-4 mb-1">
            <p className="text-sm font-medium">{item.name}</p>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--secondary)] text-[var(--muted-foreground)] shrink-0">
              {item.category}
            </span>
          </div>
          <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
            {item.rationale}
          </p>
        </div>
      ))}
    </div>
  );
}

function Spinner() {
  return (
    <div className="w-6 h-6 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
  );
}
