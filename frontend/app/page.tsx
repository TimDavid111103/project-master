"use client";

import { useState } from "react";
import { HomeView } from "@/components/HomeView";
import { NewProjectFlow } from "@/components/NewProjectFlow";
import { ProjectDetailView } from "@/components/ProjectDetailView";
import { PromptSessionFlow } from "@/components/PromptSessionFlow";
import { useProjects } from "@/hooks/useProjects";
import type { ProjectListItem } from "@/lib/types";

type AppView =
  | { kind: "home" }
  | { kind: "new-project" }
  | { kind: "project-detail"; projectId: string; projectName: string }
  | { kind: "prompt-session"; projectId: string; projectName: string }
  | { kind: "project-setup"; projectId: string };

export default function Home() {
  const { projects, isLoading, error, reload } = useProjects();
  const [view, setView] = useState<AppView>({ kind: "home" });

  function goHome() {
    reload();
    setView({ kind: "home" });
  }

  if (view.kind === "new-project") {
    return (
      <NewProjectFlow
        onComplete={(projectId) => {
          reload();
          setView({ kind: "project-detail", projectId, projectName: "Project" });
        }}
        onCancel={goHome}
      />
    );
  }

  if (view.kind === "project-detail") {
    return (
      <ProjectDetailView
        projectId={view.projectId}
        onBack={goHome}
        onAnalyzePrompt={() =>
          setView({
            kind: "prompt-session",
            projectId: view.projectId,
            projectName: view.projectName,
          })
        }
        onRunSetup={() =>
          setView({
            kind: "project-setup",
            projectId: view.projectId,
          })
        }
      />
    );
  }

  if (view.kind === "prompt-session") {
    return (
      <PromptSessionFlow
        projectId={view.projectId}
        projectName={view.projectName}
        onBack={() =>
          setView({
            kind: "project-detail",
            projectId: view.projectId,
            projectName: view.projectName,
          })
        }
      />
    );
  }

  if (view.kind === "project-setup") {
    return (
      <NewProjectFlow
        existingProjectId={view.projectId}
        onComplete={(projectId) => {
          reload();
          const proj = projects.find((p) => p.project_id === projectId);
          setView({
            kind: "project-detail",
            projectId,
            projectName: proj?.name ?? "Project",
          });
        }}
        onCancel={() => {
          const proj = projects.find((p) => p.project_id === view.projectId);
          setView({
            kind: "project-detail",
            projectId: view.projectId,
            projectName: proj?.name ?? "Project",
          });
        }}
      />
    );
  }

  return (
    <HomeView
      projects={projects}
      isLoading={isLoading}
      error={error}
      onNewProject={() => setView({ kind: "new-project" })}
      onSelectProject={(project: ProjectListItem) =>
        setView({
          kind: "project-detail",
          projectId: project.project_id,
          projectName: project.name,
        })
      }
    />
  );
}
