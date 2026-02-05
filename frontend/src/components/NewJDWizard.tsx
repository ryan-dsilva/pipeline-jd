import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  createJob,
  fetchJobDescription,
  analyzeJobText,
  type JobFetchResult,
  type SectionHeading,
} from "../lib/api";
import Input from "./ui/Input";
import Button from "./ui/Button";
import ExpandableTextarea from "./ui/ExpandableTextarea";

interface NewJDWizardProps {
  open: boolean;
  onClose: () => void;
}

type WizardStage = "url-entry" | "confirmation" | "edit";

interface ExtractionMetadata {
  confidence: number;
  wordCount: number;
  htmlWordCount: number;
  sectionHeadings: SectionHeading[];
  methodUsed: string;
}

// ── Confidence Badge Component ──────────────────────────────────

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  const isHigh = percentage >= 80;
  const isMedium = percentage >= 60 && percentage < 80;

  const colorClass = isHigh
    ? "bg-green-100 text-green-800 border-green-300"
    : isMedium
      ? "bg-yellow-100 text-yellow-800 border-yellow-300"
      : "bg-red-100 text-red-800 border-red-300";

  const icon = isHigh ? "✓" : "⚠";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${colorClass}`}
    >
      {icon} {percentage}% confident
    </span>
  );
}

// ── Section Chips Component ─────────────────────────────────────

function SectionChips({ headings }: { headings: SectionHeading[] }) {
  if (headings.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {headings.map((heading, idx) => (
        <span
          key={idx}
          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-bg-secondary text-text-secondary border border-border-primary"
        >
          {heading.name}{" "}
          <span className="ml-1 text-text-tertiary">({heading.word_count})</span>
        </span>
      ))}
    </div>
  );
}

// ── Metadata Bar Component ──────────────────────────────────────

function MetadataBar({
  metadata,
  isAnalyzing,
}: {
  metadata: ExtractionMetadata | null;
  isAnalyzing: boolean;
}) {
  if (isAnalyzing) {
    return (
      <div className="bg-bg-secondary rounded-lg p-3 border border-border-primary">
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
          Analyzing...
        </div>
      </div>
    );
  }

  if (!metadata) return null;

  const extractionRatio =
    metadata.htmlWordCount > 0
      ? Math.round((metadata.wordCount / metadata.htmlWordCount) * 100)
      : 100;

  return (
    <div className="bg-bg-secondary rounded-lg p-3 border border-border-primary">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <ConfidenceBadge confidence={metadata.confidence} />
        <span className="text-text-secondary">·</span>
        <span className="text-text-secondary">
          {metadata.wordCount} words · {extractionRatio}% of page
        </span>
        <span className="text-text-secondary">·</span>
        <span className="text-text-tertiary">{metadata.methodUsed}</span>
      </div>
      <SectionChips headings={metadata.sectionHeadings} />
    </div>
  );
}

// ── Warning Banner Component ────────────────────────────────────

function WarningBanner({ message }: { message: string }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start gap-2">
      <span className="text-yellow-600">⚠</span>
      <p className="text-sm text-yellow-800">{message}</p>
    </div>
  );
}

// ── Main Wizard Component ───────────────────────────────────────

export default function NewJDWizard({ open, onClose }: NewJDWizardProps) {
  const navigate = useNavigate();
  const [stage, setStage] = useState<WizardStage>("url-entry");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<ExtractionMetadata | null>(null);
  const [fetchResult, setFetchResult] = useState<JobFetchResult | null>(null);

  // Reset state when closing
  const handleClose = () => {
    setStage("url-entry");
    setJdUrl("");
    setJdText("");
    setError(null);
    setLoading(false);
    setMetadata(null);
    setFetchResult(null);
    onClose();
  };

  // Stage 1: URL Entry → Continue to fetch/analyze
  const handleContinue = async () => {
    setError(null);
    setLoading(true);

    try {
      // Case 1: User provided text → analyze it
      if (jdText.trim()) {
        setIsAnalyzing(true);
        const result = await analyzeJobText(jdText.trim());
        setMetadata({
          confidence: 1.0, // User-provided text is trusted
          wordCount: result.word_count,
          htmlWordCount: result.word_count, // Same as word count for manual entry
          sectionHeadings: result.section_headings,
          methodUsed: "manual",
        });
        setIsAnalyzing(false);
        setStage("confirmation");
        setLoading(false);
        return;
      }

      // Case 2: URL only → fetch from URL
      if (jdUrl.trim()) {
        const result = await fetchJobDescription(jdUrl.trim());
        setFetchResult(result);

        if (result.success && result.jd_text) {
          setJdText(result.jd_text);
          setMetadata({
            confidence: result.confidence,
            wordCount: result.word_count,
            htmlWordCount: result.html_word_count,
            sectionHeadings: result.section_headings,
            methodUsed: result.method_used,
          });
          setStage("confirmation");
        } else {
          // Fetch failed → show error and let user paste manually
          setError(
            result.error_message ||
              "Failed to fetch job description. Please paste it manually."
          );
        }
        setLoading(false);
        return;
      }

      setError("Please provide a URL or paste the job description");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An error occurred";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Edit button click
  const handleEdit = () => {
    setStage("edit");
  };

  // Handle Back button
  const handleBack = () => {
    if (stage === "edit") {
      setStage("confirmation");
    } else if (stage === "confirmation") {
      setStage("url-entry");
      // Clear fetched data when going back
      setJdText("");
      setMetadata(null);
      setFetchResult(null);
    }
    setError(null);
  };

  // Re-analyze text on blur in edit mode
  const handleTextBlur = useCallback(async () => {
    if (stage !== "edit" || !jdText.trim()) return;

    setIsAnalyzing(true);
    try {
      const result = await analyzeJobText(jdText.trim());
      setMetadata((prev) => ({
        confidence: prev?.confidence ?? 1.0,
        wordCount: result.word_count,
        htmlWordCount: prev?.htmlWordCount ?? result.word_count,
        sectionHeadings: result.section_headings,
        methodUsed: prev?.methodUsed ?? "manual",
      }));
    } catch {
      // Silently fail re-analysis
    } finally {
      setIsAnalyzing(false);
    }
  }, [stage, jdText]);

  // Create job
  const handleCreateJob = async () => {
    setError(null);
    setLoading(true);

    try {
      const job = await createJob({
        jd_url: jdUrl.trim(),
        jd_text: jdText.trim(),
        jd_fetch_status: fetchResult?.success ? "success" : "manual",
        jd_fetch_confidence: metadata?.confidence,
      });
      handleClose();
      navigate(`/jobs/${job.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create job";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  const showLowConfidenceWarning =
    metadata && metadata.confidence < 0.8 && stage === "confirmation";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/40 transition-opacity"
        onClick={handleClose}
      />
      <div className="relative bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Back button */}
        {stage !== "url-entry" && (
          <button
            onClick={handleBack}
            className="mb-4 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            ← Back
          </button>
        )}

        {/* Title */}
        <h2 className="text-lg font-semibold mb-4 text-text-primary">
          {stage === "url-entry" && "Add New Job"}
          {stage === "confirmation" && "Confirm Job Description"}
          {stage === "edit" && "Edit Job Description"}
        </h2>

        {/* Error message */}
        {error && (
          <div className="text-sm text-error bg-error/5 px-3 py-2 rounded-md border border-error/20 mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* URL Display (confirmation/edit stages) or Input (url-entry) */}
          {stage === "url-entry" ? (
            <div>
              <label className="block text-sm font-medium mb-1 text-text-primary">
                JD URL <span className="text-error">*</span>
              </label>
              <Input
                variant="url"
                value={jdUrl}
                onChange={(e) => setJdUrl(e.target.value)}
                placeholder="https://boards.greenhouse.io/..."
                disabled={loading}
                autoFocus
              />
              <p className="text-xs text-text-secondary mt-1">
                We'll automatically fetch the job description from this URL
              </p>
            </div>
          ) : (
            <div className="text-sm text-text-secondary truncate">
              {jdUrl || "(No URL provided)"}
            </div>
          )}

          {/* Metadata bar (confirmation/edit stages) */}
          {(stage === "confirmation" || stage === "edit") && (
            <MetadataBar metadata={metadata} isAnalyzing={isAnalyzing} />
          )}

          {/* Low confidence warning */}
          {showLowConfidenceWarning && (
            <WarningBanner message="Content may be incomplete. Please review and edit if needed." />
          )}

          {/* JD Text */}
          {stage === "url-entry" && (
            <div>
              <label className="block text-sm font-medium mb-1 text-text-primary">
                JD Text{" "}
                <span className="text-text-secondary">(optional)</span>
              </label>
              <ExpandableTextarea
                value={jdText}
                onChange={setJdText}
                placeholder="Paste job description here if you prefer..."
                disabled={loading}
                collapsedRows={3}
                expandedRows={10}
              />
              <p className="text-xs text-text-secondary mt-1">
                Leave blank to auto-fetch, or paste the full job description here
              </p>
            </div>
          )}

          {stage === "confirmation" && (
            <div>
              <ExpandableTextarea
                value={jdText}
                onChange={setJdText}
                placeholder=""
                readOnly
                collapsedRows={3}
                expandedRows={10}
              />
            </div>
          )}

          {stage === "edit" && (
            <div>
              <ExpandableTextarea
                value={jdText}
                onChange={setJdText}
                placeholder="Edit the job description..."
                disabled={loading}
                collapsedRows={10}
                expandedRows={20}
                onBlur={handleTextBlur}
              />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6">
          <Button variant="secondary" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>

          {stage === "url-entry" && (
            <Button
              onClick={handleContinue}
              disabled={loading || (!jdUrl.trim() && !jdText.trim())}
            >
              {loading ? "Processing..." : "Continue →"}
            </Button>
          )}

          {stage === "confirmation" && (
            <>
              <Button variant="secondary" onClick={handleEdit} disabled={loading}>
                Edit
              </Button>
              <Button onClick={handleCreateJob} disabled={loading || !jdText.trim()}>
                {loading ? "Creating..." : "Create Job"}
              </Button>
            </>
          )}

          {stage === "edit" && (
            <Button onClick={handleCreateJob} disabled={loading || !jdText.trim()}>
              {loading ? "Creating..." : "Create Job"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
