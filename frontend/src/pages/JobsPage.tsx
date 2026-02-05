import { useMemo, useState } from "react";
import { listJobs } from "../lib/api";
import { useApi } from "../hooks/useApi";
import JobsTable from "../components/JobsTable";
import SegmentedControl from "../components/ui/SegmentedControl";

type Tab = "active" | "applied" | "ignored" | "not_processed";

const ACTIVE_STAGES = new Set([
  "analyzing",
  "analyzed",
  "cover_letter_gen",
  "ready",
]);

export default function JobsPage() {
  const [tab, setTab] = useState<Tab>("active");

  // Fetch all jobs so we can compute counts
  const { data: allJobs, loading, refresh } = useApi(() => listJobs(), []);
  const jobs = allJobs || [];

  const counts = useMemo(() => {
    const c = { active: 0, applied: 0, ignored: 0, not_processed: 0 };
    for (const j of jobs) {
      if (j.pipeline_stage === "applied") c.applied++;
      else if (j.pipeline_stage === "ignored") c.ignored++;
      else if (j.pipeline_stage === "queue" && j.extraction_status === "failed") c.not_processed++;
      else if (ACTIVE_STAGES.has(j.pipeline_stage)) c.active++;
    }
    return c;
  }, [jobs]);

  const filtered = useMemo(() => {
    switch (tab) {
      case "active":
        return jobs.filter((j) => ACTIVE_STAGES.has(j.pipeline_stage));
      case "applied":
        return jobs.filter((j) => j.pipeline_stage === "applied");
      case "ignored":
        return jobs.filter((j) => j.pipeline_stage === "ignored");
      case "not_processed":
        return jobs.filter((j) => j.pipeline_stage === "queue" && j.extraction_status === "failed");
    }
  }, [jobs, tab]);

  const tabItems = [
    { key: "active", label: "Active", count: counts.active },
    { key: "applied", label: "Applied", count: counts.applied },
    { key: "ignored", label: "Ignored", count: counts.ignored },
    { key: "not_processed", label: "Not Processed", count: counts.not_processed },
  ];

  return (
    <div>
      <div className="mb-6">
        <SegmentedControl
          items={tabItems}
          value={tab}
          onChange={(k) => setTab(k as Tab)}
        />
      </div>

      <JobsTable
        jobs={filtered}
        loading={loading}
        onRefresh={refresh}
      />
    </div>
  );
}
