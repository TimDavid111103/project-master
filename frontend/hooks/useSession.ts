"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type {
  ClarifyingQuestion,
  SessionContext,
  SessionRespondResponse,
  UserAnswer,
} from "@/lib/types";

export type View = "input" | "qa" | "results";

interface SessionState {
  view: View;
  originalPrompt: string;
  sessionContext: SessionContext | null;
  questions: ClarifyingQuestion[];
  result: SessionRespondResponse | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: SessionState = {
  view: "input",
  originalPrompt: "",
  sessionContext: null,
  questions: [],
  result: null,
  isLoading: false,
  error: null,
};

export function useSession() {
  const [state, setState] = useState<SessionState>(initialState);

  async function submitPrompt(prompt: string): Promise<void> {
    setState((s) => ({ ...s, isLoading: true, error: null, originalPrompt: prompt }));
    try {
      const data = await api.sessionStart({ original_prompt: prompt });
      setState((s) => ({
        ...s,
        isLoading: false,
        view: "qa",
        sessionContext: data.session_context,
        questions: data.questions,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  async function submitAnswers(answers: UserAnswer[]): Promise<void> {
    if (!state.sessionContext) return;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await api.sessionRespond({
        session_context: state.sessionContext,
        answers,
      });
      setState((s) => ({ ...s, isLoading: false, view: "results", result: data }));
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  function reset(): void {
    setState(initialState);
  }

  return { ...state, submitPrompt, submitAnswers, reset };
}
