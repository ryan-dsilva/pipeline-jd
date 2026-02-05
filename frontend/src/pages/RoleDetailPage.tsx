import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { getJob, getSectionDefinitions } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { useSSE } from "../hooks/useSSE";
import { useSidebarState } from "../hooks/useSidebarState";
import { playBloop } from "../lib/sound";
import RoleHeader from "../components/RoleHeader";
import SectionNav from "../components/SectionNav";
import SectionPanel from "../components/SectionPanel";
import ChatBar from "../components/ChatBar";
import CollapsibleCard from "../components/ui/CollapsibleCard";
import ConfirmModal from "../components/ui/ConfirmModal";
import { ChevronDoubleRightIcon } from "@heroicons/react/24/outline";
import type { SectionDefinition, SectionStatus } from "../lib/types";

// Minimized-by-default section keys
const MINIMIZED_KEYS = new Set(["evidence_cleanup"]);

export default function RoleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [clConfirmOpen, setClConfirmOpen] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);
  const { mode, toggle, expand } = useSidebarState();

  const {
    data: job,
    loading,
    error,
    refresh,
  } = useApi(() => getJob(id!), [id]);

  const { data: definitions } = useApi(() => getSectionDefinitions(), []);
  const sse = useSSE();

  const handleSectionClick = useCallback((key: string) => {
    const el = document.getElementById(`section-${key}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveSection(key);
    }
  }, []);

  const handleRunAnalysis = useCallback(() => {
    sse.start(id!, "analyze");
    const check = setInterval(() => {
      if (!sse.running) {
        clearInterval(check);
        playBloop();
        refresh();
      }
    }, 1000);
  }, [id, sse, refresh]);

  // Auto-start analysis if job is in queue stage with completed extraction
  useEffect(() => {
    if (
      job &&
      job.pipeline_stage === "queue" &&
      job.extraction_status === "complete" &&
      !sse.running &&
      !sse.error
    ) {
      handleRunAnalysis();
    }
  }, [job?.id, job?.pipeline_stage, job?.extraction_status, job, sse.running, sse.error, handleRunAnalysis]);

  // Scroll spy with IntersectionObserver
  useEffect(() => {
    if (!mainRef.current) return;
    const sections = mainRef.current.querySelectorAll("[id^='section-']");
    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const key = entry.target.id.replace("section-", "");
            setActiveSection(key);
            break;
          }
        }
      },
      { rootMargin: "-80px 0px -60% 0px", threshold: 0.1 },
    );

    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, [job, definitions]);

  const handleRunCoverLetter = useCallback(() => {
    sse.start(id!, "cover-letter");
    const check = setInterval(() => {
      if (!sse.running) {
        clearInterval(check);
        playBloop();
        refresh();
      }
    }, 1000);
  }, [id, sse, refresh]);

  if (loading)
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-text-secondary animate-pulse">Loading...</p>
      </div>
    );
  if (error || !job)
    return (
      <p className="text-sm text-error p-8">{error || "Not found"}</p>
    );

  const defs = definitions || [];
  const sectionMap = new Map(job.sections.map((s) => [s.section_key, s]));

  // Merge SSE statuses
  const mergedStatuses: Record<string, SectionStatus> = {};
  for (const d of defs) {
    const section = sectionMap.get(d.key);
    mergedStatuses[d.key] =
      (sse.statuses[d.key] as SectionStatus) || section?.status || "pending";
  }

  // Sort definitions by order for display (Minto pyramid)
  const sortedDefs = [...defs].sort((a, b) => a.order - b.order);
  const analysisDefs = sortedDefs.filter(
    (d) => d.phase === "analysis" && d.key !== "evidence_cleanup",
  );
  const clDefs = sortedDefs.filter((d) => d.phase === "cover_letter");

  // Check if cover letter exists (any CL section has content)
  const hasCoverLetter = clDefs.some(
    (d) => sectionMap.get(d.key)?.status === "complete",
  );

  return (
    <div className="flex flex-col h-screen">
      <RoleHeader
        job={job}
        onRefresh={refresh}
        onRerunAnalysis={handleRunAnalysis}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div
          className={`border-r border-border-light bg-off-white shrink-0 overflow-hidden
            transition-[width] duration-300 ease-in-out
            ${mode === "collapsed" ? "w-10" : mode === "narrow" ? "w-16" : "w-[280px]"}`}
        >
          {mode === "collapsed" ? (
            <div className="px-1 py-2">
              <button
                onClick={expand}
                className="w-full flex justify-center px-1 py-1.5 rounded-md text-sm text-text-secondary
                  hover:text-text-primary hover:bg-cream transition-colors
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                aria-label="Expand sidebar"
              >
                <ChevronDoubleRightIcon className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <SectionNav
              definitions={sortedDefs}
              statuses={mergedStatuses}
              activeSection={activeSection}
              onSectionClick={handleSectionClick}
              hasCoverLetter={hasCoverLetter}
              onGenerateCoverLetter={handleRunCoverLetter}
              onRegenerateCoverLetter={() => setClConfirmOpen(true)}
              hasJdText={!!job.jd_text}
              mode={mode}
              onToggle={toggle}
            />
          )}
        </div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden bg-cream">
          <div ref={mainRef} className="flex-1 overflow-y-auto px-6 py-6">
            <div className="max-w-4xl mx-auto space-y-4">
              {sse.error && (
                <p className="text-sm text-error bg-error/10 px-3 py-2 rounded-md">
                  {sse.error}
                </p>
              )}

              {/* Analysis sections */}
              {analysisDefs.map((d) => (
                <SectionPanel
                  key={d.key}
                  definition={d}
                  section={sectionMap.get(d.key)}
                  jobId={id!}
                  onUpdate={refresh}
                  defaultExpanded={!MINIMIZED_KEYS.has(d.key)}
                />
              ))}

              {/* Cover letter sections */}
              {hasCoverLetter &&
                clDefs.map((d) => (
                  <SectionPanel
                    key={d.key}
                    definition={d}
                    section={sectionMap.get(d.key)}
                    jobId={id!}
                    onUpdate={refresh}
                    defaultExpanded={true}
                  />
                ))}

              {/* Evidence Cleanup (reference, minimized) */}
              {sectionMap.get("evidence_cleanup") && (
                <SectionPanel
                  definition={
                    defs.find((d) => d.key === "evidence_cleanup") ||
                    ({
                      key: "evidence_cleanup",
                      label: "Evidence Cleanup",
                      order: 20,
                      depends_on: [],
                      phase: "analysis",
                    } as SectionDefinition)
                  }
                  section={sectionMap.get("evidence_cleanup")}
                  jobId={id!}
                  onUpdate={refresh}
                  defaultExpanded={false}
                />
              )}

              {/* Raw JD (minimized) */}
              {job.jd_text && (
                <CollapsibleCard
                  id="section-raw_jd"
                  title="Raw JD"
                  defaultExpanded={false}
                  preview={job.jd_text.slice(0, 150)}
                >
                  {job.jd_url && (
                    <div className="mb-3">
                      <a
                        href={job.jd_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-brand-primary hover:underline break-all"
                      >
                        {job.jd_url}
                      </a>
                    </div>
                  )}
                  <pre className="text-sm text-text-body bg-off-white p-4 rounded whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {job.jd_text}
                  </pre>
                </CollapsibleCard>
              )}
            </div>
          </div>

          {/* Bottom chat bar */}
          <ChatBar jobId={id!} />
        </div>
      </div>

      <ConfirmModal
        open={clConfirmOpen}
        title="Regenerate cover letter?"
        description="This will regenerate all cover letter sections."
        confirmLabel="Regenerate"
        onConfirm={() => {
          setClConfirmOpen(false);
          handleRunCoverLetter();
        }}
        onCancel={() => setClConfirmOpen(false)}
      />
    </div>
  );
}
