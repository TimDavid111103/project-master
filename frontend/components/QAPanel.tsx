"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { ClarifyingQuestion, UserAnswer } from "@/lib/types";

interface QAPanelProps {
  questions: ClarifyingQuestion[];
  onSubmit: (answers: UserAnswer[]) => void;
  isLoading: boolean;
  error: string | null;
}

export function QAPanel({ questions, onSubmit, isLoading, error }: QAPanelProps) {
  const [answers, setAnswers] = useState<Record<string, string>>(
    Object.fromEntries(questions.map((q) => [q.question_id, ""]))
  );

  function handleChange(questionId: string, value: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const userAnswers: UserAnswer[] = questions.map((q) => ({
      question_id: q.question_id,
      answer_text: answers[q.question_id] ?? "",
    }));
    onSubmit(userAnswers);
  }

  const allAnswered = questions.every((q) => answers[q.question_id]?.trim());

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Answer a few questions</CardTitle>
        <p className="text-sm text-muted-foreground">
          Help us understand your intent so we can improve your prompt.
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {questions.map((q, i) => (
            <div key={q.question_id} className="flex flex-col gap-2">
              <div className="flex items-start gap-2">
                <Badge variant="outline" className="mt-0.5 shrink-0">
                  {i + 1}
                </Badge>
                <p className="text-sm font-medium">{q.question_text}</p>
              </div>
              <Textarea
                placeholder="Your answer…"
                value={answers[q.question_id] ?? ""}
                onChange={(e) => handleChange(q.question_id, e.target.value)}
                rows={3}
                className="resize-none text-sm"
                disabled={isLoading}
              />
              {i < questions.length - 1 && <Separator className="mt-2" />}
            </div>
          ))}
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" disabled={isLoading || !allAnswered}>
            {isLoading ? "Generating…" : "Generate Improved Prompt →"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
