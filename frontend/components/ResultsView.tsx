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

export function ResultsView({ result, onReset }: ResultsViewProps) {
  const [debugOpen, setDebugOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  async function copyRevised() {
    await navigator.clipboard.writeText(result.revised_prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

        <Card className="border-primary/40">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Revised prompt</CardTitle>
            <Button variant="outline" size="sm" onClick={copyRevised}>
              {copied ? "Copied!" : "Copy"}
            </Button>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
              {result.revised_prompt}
            </pre>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">What changed and why</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{result.analysis}</p>
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
            <CardContent className="pt-4 flex flex-col gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                  Reformulated query
                </p>
                <div className="flex flex-wrap gap-1 mb-1">
                  <Badge>{result.reformulated_query.category}</Badge>
                  {result.reformulated_query.concept_tags.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground font-mono">
                  {result.reformulated_query.query_text}
                </p>
              </div>
              <Separator />
              <div>
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
                          #{i + 1} · score {doc.similarity_score}
                        </span>
                      </div>
                      <p className="text-xs font-mono leading-relaxed line-clamp-3">
                        {doc.content}
                      </p>
                    </div>
                  ))
                )}
              </div>
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
