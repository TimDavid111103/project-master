"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ChatMessage, PipelineAnalyzeResponse, ProjectPlan } from "@/lib/types";

export type ChatView = "chat" | "analyzing" | "done";

interface IdeationChatState {
  view: ChatView;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  result: PipelineAnalyzeResponse | null;
}

const initialState: IdeationChatState = {
  view: "chat",
  messages: [],
  isLoading: false,
  error: null,
  result: null,
};

export function useIdeationChat(projectId: string) {
  const [state, setState] = useState<IdeationChatState>(initialState);

  async function sendMessage(userMessage: string): Promise<void> {
    setState((s) => ({ ...s, isLoading: true, error: null }));

    const updatedHistory: ChatMessage[] = [
      ...state.messages,
      { role: "user", content: userMessage },
    ];

    try {
      const response = await api.pipelineChat({
        user_message: userMessage,
        conversation_history: state.messages,
      });

      const newMessages: ChatMessage[] = [
        ...updatedHistory,
        { role: "assistant", content: response.agent_message },
      ];

      if (response.is_complete && response.project_plan) {
        setState((s) => ({
          ...s,
          messages: newMessages,
          isLoading: false,
          view: "analyzing",
        }));
        await runAnalysis(response.project_plan, newMessages);
      } else {
        setState((s) => ({
          ...s,
          messages: newMessages,
          isLoading: false,
        }));
      }
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  async function runAnalysis(
    projectPlan: ProjectPlan,
    messages: ChatMessage[]
  ): Promise<void> {
    try {
      const stored = localStorage.getItem("project_master_user_tech_stack");
      const userTechStack: string[] = stored ? (JSON.parse(stored) as string[]) : [];

      const result = await api.pipelineAnalyze({
        project_id: projectId,
        project_plan: projectPlan,
        user_tech_stack: userTechStack,
      });
      setState((s) => ({
        ...s,
        messages,
        view: "done",
        result,
        isLoading: false,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        view: "chat",
        isLoading: false,
        error: err instanceof Error ? err.message : "Analysis failed.",
      }));
    }
  }

  function reset(): void {
    setState(initialState);
  }

  return { ...state, sendMessage, reset };
}
