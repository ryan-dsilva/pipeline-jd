import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Job } from "../lib/types";
import Badge, { verdictBadgeVariant } from "./ui/Badge";
import IconButton from "./ui/IconButton";
import ConfirmModal from "./ui/ConfirmModal";
import EmptyState from "./ui/EmptyState";
import Button from "./ui/Button";
import Input from "./ui/Input";
import { SkeletonTableRow } from "./ui/Skeleton";
import { startPipelineSSE } from "../lib/api";
import { playBloop } from "../lib/sound";

interface Props {
  jobs: Job[];
  loading?: boolean;
  onRefresh?: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  queue: "Queue",
  analyzing: "Analyzing",
  analyzed: "Analyzed",
  cover_letter_gen: "Cover Letter",
  ready: "Ready",
  applied: "Applied",
  ignored: "Ignored",
};

type SortKey =
  | "company"
  | "role"
  | "score"
  | "hours"
  | "verdict"
  | "pipeline_stage"
  | "date_added";
type SortDir = "asc" | "desc";

function relativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths}mo ago`;
}

function scoreColor(score: number | null): string {
  if (score == null) return "text-text-secondary";
  if (score > 75) return "text-sage font-semibold";
  if (score >= 50) return "text-teal font-medium";
  if (score >= 25) return "text-amber font-medium";
  return "text-error font-medium";
}

export default function JobsTable({
  jobs,
  loading,
  onRefresh,
}: Props) {
  const navigate = useNavigate();
  const [sortKey, setSortKey] = useState<SortKey>("date_added");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filter, setFilter] = useState("");
  const [confirmJob, setConfirmJob] = useState<Job | null>(null);
  const [rerunning, setRerunning] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!filter.trim()) return jobs;
    const q = filter.toLowerCase();
    return jobs.filter(
      (j) =>
        j.company?.toLowerCase().includes(q) ||
        j.role?.toLowerCase().includes(q),
    );
  }, [jobs, filter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "company":
          cmp = (a.company || "").localeCompare(b.company || "");
          break;
        case "role":
          cmp = (a.role || "").localeCompare(b.role || "");
          break;
        case "score":
          cmp = (a.score ?? -1) - (b.score ?? -1);
          break;
        case "hours":
          cmp = (a.hours ?? -1) - (b.hours ?? -1);
          break;
        case "verdict":
          cmp = (a.verdict || "").localeCompare(b.verdict || "");
          break;
        case "pipeline_stage":
          cmp = a.pipeline_stage.localeCompare(b.pipeline_stage);
          break;
        case "date_added":
          cmp =
            new Date(a.date_added || a.created).getTime() -
            new Date(b.date_added || b.created).getTime();
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "date_added" ? "desc" : "asc");
    }
  };

  const handleRerun = (job: Job, e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmJob(job);
  };

  const confirmRerun = async () => {
    if (!confirmJob) return;
    const jobId = confirmJob.id;
    setConfirmJob(null);
    setRerunning(jobId);
    try {
      await startPipelineSSE(
        jobId,
        "analyze",
        () => {},
        () => {
          setRerunning(null);
          playBloop();
          onRefresh?.();
        },
        () => setRerunning(null),
      );
    } catch {
      setRerunning(null);
    }
  };

  const SortHeader = ({
    label,
    colKey,
    className = "",
  }: {
    label: string;
    colKey: SortKey;
    className?: string;
  }) => (
    <th
      className={`py-2.5 pr-4 font-medium text-text-secondary text-left cursor-pointer select-none hover:text-text-primary ${className}`}
      onClick={() => handleSort(colKey)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {sortKey === colKey && (
          <svg
            className="w-3 h-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d={sortDir === "asc" ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
            />
          </svg>
        )}
      </span>
    </th>
  );

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-border-light shadow-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-light">
              <th className="py-2.5 pr-4 pl-4 font-medium text-text-secondary text-left">Company</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Role</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Score</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Hours</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Verdict</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Stage</th>
              <th className="py-2.5 pr-4 font-medium text-text-secondary text-left">Added</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonTableRow key={i} />
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-border-light shadow-md">
        <EmptyState
          title="No jobs found"
          description="Add a new job to get started with analysis."
          action={
            <Button size="sm" onClick={() => navigate("/new")}>
              + New Job
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <>
      <div className="mb-3">
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by company or role..."
          className="w-full max-w-xs"
        />
      </div>

      <div className="bg-white rounded-lg border border-border-light shadow-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-light">
              <SortHeader label="Company" colKey="company" className="pl-4" />
              <SortHeader label="Role" colKey="role" />
              <SortHeader label="Score" colKey="score" />
              <SortHeader label="Hours" colKey="hours" />
              <SortHeader label="Verdict" colKey="verdict" />
              <SortHeader label="Stage" colKey="pipeline_stage" />
              <SortHeader label="Added" colKey="date_added" />
              <th className="py-2.5 pr-4 w-8" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((job) => (
              <tr
                key={job.id}
                onClick={() => navigate(`/jobs/${job.id}`)}
                className="border-b border-border-light/50 hover:bg-bg-off-white cursor-pointer transition-colors"
              >
                <td className="py-2.5 pr-4 pl-4 font-medium text-text-primary">
                  {job.company || "(unknown)"}
                </td>
                <td className="py-2.5 pr-4 text-text-body max-w-[200px] truncate">
                  {job.role || "(unknown)"}
                </td>
                <td className={`py-2.5 pr-4 font-mono tabular-nums ${scoreColor(job.score)}`}>
                  {job.score != null ? job.score : "—"}
                </td>
                <td className="py-2.5 pr-4 font-mono tabular-nums text-text-body">
                  {job.hours != null ? `${job.hours}h` : "—"}
                </td>
                <td className="py-2.5 pr-4">
                  {job.verdict ? (
                    <Badge variant={verdictBadgeVariant(job.verdict)}>
                      {job.verdict}
                    </Badge>
                  ) : (
                    <span className="text-text-secondary">—</span>
                  )}
                </td>
                <td className="py-2.5 pr-4 text-text-secondary text-xs">
                  {STAGE_LABELS[job.pipeline_stage] || job.pipeline_stage}
                </td>
                <td className="py-2.5 pr-4 text-text-secondary text-xs font-mono tabular-nums">
                  {relativeDate(job.date_added || job.created)}
                </td>
                <td className="py-2.5 pr-4">
                  <IconButton
                    label="Re-run analysis"
                    onClick={(e) => handleRerun(job, e)}
                    disabled={rerunning === job.id}
                  >
                    <svg
                      className={`w-4 h-4 ${rerunning === job.id ? "animate-spin" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </IconButton>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmModal
        open={!!confirmJob}
        title={`Re-run analysis for ${confirmJob?.company || "this job"}?`}
        description="This will regenerate all analysis sections."
        confirmLabel="Re-run"
        onConfirm={confirmRerun}
        onCancel={() => setConfirmJob(null)}
      />
    </>
  );
}
