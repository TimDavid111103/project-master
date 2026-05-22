"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type {
  ClarifyingQuestion,
  ProjectSetupContext,
  UserAnswer,
} from "@/lib/types";

export type SetupView = "idea" | "qa" | "done";

interface ProjectSetupState {
  view: SetupView;
  projectId: string | null;
  setupContext: ProjectSetupContext | null;
  questions: ClarifyingQuestion[];
  projectDefinition: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: ProjectSetupState = {
  view: "idea",
  projectId: null,
  setupContext: null,
  questions: [],
  projectDefinition: null,
  isLoading: false,
  error: null,
};

export function useProjectSetup() {
  const [state, setState] = useState<ProjectSetupState>(initialState);

  async function createAndStart(name: string, roughIdea: string): Promise<void> {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const project = await api.createProject({ name, rough_idea: roughIdea });
      const setup = await api.setupStart(project.project_id);
      setState((s) => ({
        ...s,
        isLoading: false,
        view: "qa",
        projectId: project.project_id,
        setupContext: setup.setup_context,
        questions: setup.questions,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  async function startExisting(existingProjectId: string): Promise<void> {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const setup = await api.setupStart(existingProjectId);
      setState((s) => ({
        ...s,
        isLoading: false,
        view: "qa",
        projectId: existingProjectId,
        setupContext: setup.setup_context,
        questions: setup.questions,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  async function submitAnswers(answers: UserAnswer[]): Promise<string | null> {
    if (!state.setupContext) return null;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await api.setupRespond(state.projectId!, {
        setup_context: state.setupContext,
        answers,
      });
      setState((s) => ({
        ...s,
        isLoading: false,
        view: "done",
        projectDefinition: data.project_definition,
      }));
      return data.project_id;
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
      return null;
    }
  }

  function reset(): void {
    setState(initialState);
  }

  return { ...state, createAndStart, startExisting, submitAnswers, reset };
}
