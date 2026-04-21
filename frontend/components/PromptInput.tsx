"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function PromptInput({ onSubmit, isLoading, error }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (prompt.trim()) onSubmit(prompt.trim());
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Paste your prompt</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Textarea
            placeholder="Enter the prompt you want to improve..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={8}
            className="resize-none font-mono text-sm"
            disabled={isLoading}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={isLoading || !prompt.trim()}>
            {isLoading ? "Analyzing…" : "Analyze Prompt →"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
