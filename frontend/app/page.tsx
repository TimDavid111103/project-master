"use client";

import { ProjectSetup } from "@/components/ProjectSetup";
import { PromptInput } from "@/components/PromptInput";
import { QAPanel } from "@/components/QAPanel";
import { ResultsView } from "@/components/ResultsView";
import { useSession } from "@/hooks/useSession";

export default function Home() {
  const session = useSession();

  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-start py-16 px-4">
      <header className="mb-12 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Prompt Master</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste a prompt. Answer a few questions. Get a structured analysis.
        </p>
      </header>

      {session.view === "project" && (
        <ProjectSetup
          onSubmit={session.createProject}
          isLoading={session.isLoading}
          error={session.error}
        />
      )}

      {session.view === "input" && (
        <PromptInput
          onSubmit={session.submitPrompt}
          isLoading={session.isLoading}
          error={session.error}
        />
      )}

      {session.view === "qa" && (
        <QAPanel
          questions={session.questions}
          onSubmit={session.submitAnswers}
          isLoading={session.isLoading}
          error={session.error}
        />
      )}

      {session.view === "results" && session.result && (
        <ResultsView result={session.result} onReset={session.reset} />
      )}
    </main>
  );
}
