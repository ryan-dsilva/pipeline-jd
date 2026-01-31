import { useState } from "react";
import { Link } from "react-router-dom";
import type { JobDetail } from "../lib/types";
import Button from "./ui/Button";
import IconButton from "./ui/IconButton";
import Dropdown from "./ui/Dropdown";
import ConfirmModal from "./ui/ConfirmModal";
import Input from "./ui/Input";
import { updateJob, updateJobStage } from "../lib/api";

const STAGE_OPTIONS = [
  { key: "queue", label: "Queue" },
  { key: "analyzing", label: "Analyzing" },
  { key: "analyzed", label: "Analyzed" },
  { key: "cover_letter_gen", label: "Cover Letter" },
  { key: "ready", label: "Ready" },
  { key: "applied", label: "Applied" },
  { key: "ignored", label: "Ignored" },
];

const STAGE_DISPLAY: Record<string, string> = {
  queue: "Not Processed",
  analyzing: "Active",
  analyzed: "Active",
  cover_letter_gen: "Active",
  ready: "Active",
  applied: "Applied",
  ignored: "Ignored",
};

function scoreColor(score: number | null): string {
  if (score == null) return "text-text-secondary";
  if (score > 75) return "text-sage";
  if (score >= 50) return "text-teal";
  if (score >= 25) return "text-amber";
  return "text-error";
}

interface RoleHeaderProps {
  job: JobDetail;
  onRefresh: () => void;
  onRerunAnalysis: () => void;
}

export default function RoleHeader({
  job,
  onRefresh,
  onRerunAnalysis,
}: RoleHeaderProps) {
  const [editingCompany, setEditingCompany] = useState(false);
  const [companyValue, setCompanyValue] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const statusLabel = STAGE_DISPLAY[job.pipeline_stage] || job.pipeline_stage;

  const handleSaveCompany = async () => {
    try {
      await updateJob(job.id, { company: companyValue });
      setEditingCompany(false);
      onRefresh();
    } catch {
      /* keep editing */
    }
  };

  const handleStageChange = async (stage: string) => {
    await updateJobStage(job.id, stage);
    onRefresh();
  };

  const startEditCompany = () => {
    setCompanyValue(job.company || "");
    setEditingCompany(true);
  };

  return (
    <>
      <div className="sticky top-0 z-40 bg-white border-b border-border-light shadow-md px-6 py-2.5">
        <div className="flex items-center justify-between gap-4">
          {/* Left side: breadcrumb + metadata */}
          <div className="flex items-center gap-4 min-w-0">
            <Link
              to="/"
              className="text-sm text-text-secondary hover:text-text-primary shrink-0 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              <span className="font-semibold text-text-primary">Pipeline</span>
              <span className="text-text-secondary">:</span>
              <span>{statusLabel}</span>
            </Link>

            <span className={`text-lg font-bold tabular-nums ${scoreColor(job.score)}`}>
              {job.score ?? "—"}
            </span>

            <div className="flex items-center gap-1.5 min-w-0">
              {editingCompany ? (
                <div className="flex items-center gap-1.5">
                  <Input
                    value={companyValue}
                    onChange={(e) => setCompanyValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveCompany();
                      if (e.key === "Escape") setEditingCompany(false);
                    }}
                    className="w-36 text-sm font-semibold py-0.5 px-2"
                    autoFocus
                  />
                  <Button size="sm" onClick={handleSaveCompany}>
                    Save
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setEditingCompany(false)}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <span
                  className="text-sm font-semibold text-text-primary cursor-pointer hover:text-brand-primary truncate"
                  onClick={startEditCompany}
                  title="Click to edit company"
                >
                  {job.company || "(no company)"}
                </span>
              )}

              <span className="text-text-secondary">—</span>

              {job.jd_url ? (
                <a
                  href={job.jd_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-text-body hover:text-brand-primary truncate flex items-center gap-0.5"
                  title={job.role || ""}
                >
                  {job.role || "(no role)"}
                  <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              ) : (
                <span className="text-sm text-text-body truncate">
                  {job.role || "(no role)"}
                </span>
              )}
            </div>

            {job.hours != null && (
              <span className="text-sm text-text-secondary font-mono tabular-nums shrink-0">
                {job.hours}h
              </span>
            )}

            <IconButton
              label="Re-run analysis"
              onClick={() => setConfirmOpen(true)}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </IconButton>
          </div>

          {/* Right side: actions */}
          <div className="flex items-center gap-2 shrink-0">
            <Dropdown
              label="Move to"
              items={STAGE_OPTIONS}
              value={job.pipeline_stage}
              onChange={handleStageChange}
            />
            <Link to="/new">
              <Button size="sm">+ New Job</Button>
            </Link>
          </div>
        </div>
      </div>

      <ConfirmModal
        open={confirmOpen}
        title={`Re-run analysis for ${job.company || "this job"}?`}
        description="This will regenerate all analysis sections."
        confirmLabel="Re-run"
        onConfirm={() => {
          setConfirmOpen(false);
          onRerunAnalysis();
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}
