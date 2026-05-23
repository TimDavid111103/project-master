"use client";

import { useState } from "react";
import { HomeView } from "@/components/HomeView";
import { NewProjectFlow } from "@/components/NewProjectFlow";
import { IdeationChatFlow } from "@/components/IdeationChatFlow";
import { ProjectDetailView } from "@/components/ProjectDetailView";
import { useProjects } from "@/hooks/useProjects";
import type { ProjectListItem } from "@/lib/types";

type AppView =
  | { kind: "home" }
  | { kind: "new-project" }
  | { kind: "ideation-chat"; projectId: string; projectName: string; initialMessage: string }
  | { kind: "project-detail"; projectId: string; projectName: string };

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
        onComplete={(projectId, projectName, roughIdea) => {
          setView({
            kind: "ideation-chat",
            projectId,
            projectName,
            initialMessage: roughIdea,
          });
        }}
        onCancel={goHome}
      />
    );
  }

  if (view.kind === "ideation-chat") {
    return (
      <IdeationChatFlow
        projectId={view.projectId}
        projectName={view.projectName}
        initialMessage={view.initialMessage}
        onComplete={() => {
          reload();
          setView({
            kind: "project-detail",
            projectId: view.projectId,
            projectName: view.projectName,
          });
        }}
        onBack={goHome}
      />
    );
  }

  if (view.kind === "project-detail") {
    return (
      <ProjectDetailView
        projectId={view.projectId}
        onBack={goHome}
        onStartChat={(roughIdea) =>
          setView({
            kind: "ideation-chat",
            projectId: view.projectId,
            projectName: view.projectName,
            initialMessage: roughIdea,
          })
        }
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
