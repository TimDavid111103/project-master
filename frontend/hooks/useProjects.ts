"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { ProjectListItem } from "@/lib/types";

interface ProjectsState {
  projects: ProjectListItem[];
  isLoading: boolean;
  error: string | null;
}

export function useProjects() {
  const [state, setState] = useState<ProjectsState>({
    projects: [],
    isLoading: true,
    error: null,
  });

  async function load() {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const projects = await api.listProjects();
      setState({ projects, isLoading: false, error: null });
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to load projects.",
      }));
    }
  }

  useEffect(() => {
    load();
  }, []);

  return { ...state, reload: load };
}
