"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

interface ProjectSetupProps {
  onSubmit: (name: string, summary: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function ProjectSetup({ onSubmit, isLoading, error }: ProjectSetupProps) {
  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (name.trim()) onSubmit(name.trim(), summary.trim());
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create a project</CardTitle>
        <CardDescription>
          Give your project a name and a short description. The system uses this
          context across sessions to avoid repeating questions and to track how
          your prompts improve over time.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="project-name">Project name</Label>
            <Input
              id="project-name"
              placeholder="e.g. Customer support agent"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="project-summary">
              Summary <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Textarea
              id="project-summary"
              placeholder="What are you building? What kind of prompts will you be working on?"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              rows={3}
              className="resize-none text-sm"
              disabled={isLoading}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={isLoading || !name.trim()}>
            {isLoading ? "Creating…" : "Create project →"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
