"use client";

import { AsteriskLogo } from "./AsteriskLogo";
import type { ProjectListItem } from "@/lib/types";

interface Props {
  projects: ProjectListItem[];
  isLoading: boolean;
  error: string | null;
  onNewProject: () => void;
  onSelectProject: (project: ProjectListItem) => void;
  onOpenSettings: () => void;
}

export function HomeView({
  projects,
  isLoading,
  error,
  onNewProject,
  onSelectProject,
  onOpenSettings,
}: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-20 relative">
      {/* Settings gear */}
      <button
        onClick={onOpenSettings}
        aria-label="Open settings"
        className="absolute top-6 right-6 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
      >
        <GearIcon />
      </button>

      {/* Header */}
      <div className="flex flex-col items-center gap-4 mb-16">
        <AsteriskLogo size={48} />
        <h1
          className="text-4xl font-semibold tracking-tight"
          style={{ fontFamily: "var(--font-lora), serif" }}
        >
          Project Master
        </h1>
        <p className="text-[var(--muted-foreground)] text-base max-w-sm text-center">
          Turn your idea into a project plan and tech stack
        </p>
      </div>

      {/* Projects section */}
      <div className="w-full max-w-2xl">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <p className="text-center text-red-600 text-sm">{error}</p>
        ) : projects.length === 0 ? (
          <EmptyState onNewProject={onNewProject} />
        ) : (
          <ProjectList
            projects={projects}
            onNewProject={onNewProject}
            onSelectProject={onSelectProject}
          />
        )}
      </div>
    </div>
  );
}

function EmptyState({ onNewProject }: { onNewProject: () => void }) {
  return (
    <div className="flex flex-col items-center gap-6 py-12">
      <p className="text-[var(--muted-foreground)] text-sm">
        No projects yet. Create one to get started.
      </p>
      <NewProjectButton onClick={onNewProject} />
    </div>
  );
}

function ProjectList({
  projects,
  onNewProject,
  onSelectProject,
}: {
  projects: ProjectListItem[];
  onNewProject: () => void;
  onSelectProject: (p: ProjectListItem) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
          Your projects
        </h2>
        <NewProjectButton onClick={onNewProject} small />
      </div>
      {projects.map((project) => (
        <button
          key={project.project_id}
          onClick={() => onSelectProject(project)}
          className="w-full text-left rounded-xl border border-[var(--border)] bg-[var(--card)] px-5 py-4 hover:border-[var(--ring)] hover:bg-[var(--secondary)] transition-colors group"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-[var(--foreground)] truncate">
                {project.name}
              </p>
              <p className="text-sm text-[var(--muted-foreground)] mt-0.5 line-clamp-2">
                {project.rough_idea}
              </p>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  project.is_complete
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700"
                }`}
              >
                {project.is_complete ? "Complete" : "Draft"}
              </span>
              <span className="text-xs text-[var(--muted-foreground)]">
                {formatDate(project.created_at)}
              </span>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

function NewProjectButton({
  onClick,
  small,
}: {
  onClick: () => void;
  small?: boolean;
}) {
  if (small) {
    return (
      <button
        onClick={onClick}
        className="text-sm font-medium text-[var(--accent)] hover:opacity-80 transition-opacity"
      >
        + New project
      </button>
    );
  }
  return (
    <button
      onClick={onClick}
      className="px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-sm font-medium hover:opacity-90 transition-opacity"
    >
      New project
    </button>
  );
}

function LoadingSpinner() {
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

function GearIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}
