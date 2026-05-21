"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { SessionRespondResponse } from "@/lib/types";

interface ResultsViewProps {
  result: SessionRespondResponse;
  onReset: () => void;
}

const DIMENSION_LABELS: Record<keyof SessionRespondResponse["analysis"], string> = {
  intent_accuracy: "Intent accuracy",
  technical_language: "Technical language",
  standards_alignment: "Standards alignment",
};

export function ResultsView({ result, onReset }: ResultsViewProps) {
  const [debugOpen, setDebugOpen] = useState(false);

  const dimensions = (
    Object.keys(DIMENSION_LABELS) as Array<keyof typeof DIMENSION_LABELS>
  ).map((key) => ({ key, label: DIMENSION_LABELS[key], ...result.analysis[key] }));

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">Original prompt</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-muted-foreground">
            {result.original_prompt}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Prompt analysis</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {dimensions.map(({ key, label, grade, explanation }, i) => (
            <div key={key}>
              {i > 0 && <Separator className="mb-4" />}
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium">{label}</span>
                <Badge>{grade}</Badge>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{explanation}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Collapsible open={debugOpen} onOpenChange={setDebugOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            {debugOpen ? "Hide" : "Show"} debug info
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <Card className="mt-2">
            <CardContent className="pt-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                Retrieved documents ({result.retrieved_documents.length})
              </p>
              {result.retrieved_documents.length === 0 ? (
                <p className="text-xs text-muted-foreground">No documents matched.</p>
              ) : (
                result.retrieved_documents.map((doc, i) => (
                  <div key={doc.doc_id} className="mb-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-muted-foreground font-mono">
                        #{i + 1} · score {doc.similarity_score} · {doc.chunk_level}
                      </span>
                    </div>
                    <p className="text-xs font-mono leading-relaxed line-clamp-3">
                      {doc.content}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      <Button variant="outline" onClick={onReset} className="self-start">
        ← Start over
      </Button>
    </div>
  );
}
