import type { SectionDefinition, SectionStatus } from "../lib/types";
import type { SidebarMode } from "../hooks/useSidebarState";
import { getSectionIcon } from "../lib/sectionIcons";
import IconButton from "./ui/IconButton";
import Button from "./ui/Button";
import Tooltip from "./ui/Tooltip";
import { ChevronDoubleLeftIcon, EnvelopeOpenIcon } from "@heroicons/react/24/outline";

interface SectionNavProps {
  definitions: SectionDefinition[];
  statuses: Record<string, SectionStatus>;
  activeSection: string | null;
  onSectionClick: (key: string) => void;
  hasCoverLetter: boolean;
  onGenerateCoverLetter: () => void;
  onRegenerateCoverLetter: () => void;
  hasJdText: boolean;
  mode: SidebarMode;
  onToggle: () => void;
}

export default function SectionNav({
  definitions,
  statuses,
  activeSection,
  onSectionClick,
  hasCoverLetter,
  onGenerateCoverLetter,
  onRegenerateCoverLetter,
  hasJdText,
  mode,
  onToggle,
}: SectionNavProps) {
  const isWide = mode === "wide";
  const isNarrow = mode === "narrow";

  const analysisDefs = definitions
    .filter((d) => d.phase === "analysis")
    .sort((a, b) => a.order - b.order);
  const clDefs = definitions
    .filter((d) => d.phase === "cover_letter")
    .sort((a, b) => a.order - b.order);

  return (
    <nav
      className={`flex flex-col h-full ${isWide ? "w-[280px]" : "w-16"}`}
    >
      {/* Toggle button at top */}
      <div className={`shrink-0 border-b border-border-light ${isWide ? "px-3 py-2" : "px-1 py-2"}`}>
        <button
          onClick={onToggle}
          className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-text-secondary
            hover:text-text-primary hover:bg-cream transition-colors
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary
            ${isNarrow ? "justify-center" : ""}`}
        >
          <ChevronDoubleLeftIcon
            className={`w-4 h-4 shrink-0 transition-transform duration-300 ${isNarrow ? "rotate-180" : ""}`}
          />
          {isWide && <span>Collapse</span>}
        </button>
      </div>

      <div
        className={`flex-1 overflow-y-auto scrollbar-auto ${isWide ? "py-4 px-3" : "py-4 px-1"}`}
      >
        {/* Analysis group */}
        <div className="mb-6">
          {isWide ? (
            <h4 className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-2 px-2">
              Analysis
            </h4>
          ) : (
            <hr className="border-border-light mx-2 mb-2" />
          )}
          <ul className="space-y-0.5">
            {analysisDefs.map((d) => (
              <NavItem
                key={d.key}
                sectionKey={d.key}
                label={d.label}
                status={statuses[d.key] || "pending"}
                active={activeSection === d.key}
                onClick={() => onSectionClick(d.key)}
                wide={isWide}
              />
            ))}
          </ul>
        </div>

        {/* Cover Letter group */}
        <div className="mb-6">
          {isWide ? (
            <div className="flex items-center justify-between mb-2 px-2">
              <h4 className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider">
                Cover Letter
              </h4>
              {hasCoverLetter && (
                <IconButton
                  label="Regenerate cover letter"
                  size="sm"
                  onClick={onRegenerateCoverLetter}
                >
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
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                </IconButton>
              )}
            </div>
          ) : (
            <hr className="border-border-light mx-2 mb-2" />
          )}

          {hasCoverLetter ? (
            <ul className="space-y-0.5">
              {clDefs.map((d) => (
                <NavItem
                  key={d.key}
                  sectionKey={d.key}
                  label={d.label}
                  status={statuses[d.key] || "pending"}
                  active={activeSection === d.key}
                  onClick={() => onSectionClick(d.key)}
                  wide={isWide}
                />
              ))}
            </ul>
          ) : isWide ? (
            <div className="px-2">
              <Button
                size="sm"
                variant="secondary"
                className="w-full"
                onClick={onGenerateCoverLetter}
              >
                Generate Cover Letter
              </Button>
            </div>
          ) : (
            <div className="flex justify-center px-1">
              <Tooltip content="Generate Cover Letter">
                <IconButton
                  label="Generate Cover Letter"
                  size="md"
                  onClick={onGenerateCoverLetter}
                >
                  <EnvelopeOpenIcon className="w-5 h-5" />
                </IconButton>
              </Tooltip>
            </div>
          )}
        </div>

        {/* Reference group */}
        <div>
          {isWide ? (
            <h4 className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider mb-2 px-2">
              Reference
            </h4>
          ) : (
            <hr className="border-border-light mx-2 mb-2" />
          )}
          <ul className="space-y-0.5">
            <NavItem
              sectionKey="evidence_cleanup"
              label="Evidence Cleanup"
              status={statuses["evidence_cleanup"] || "pending"}
              active={activeSection === "evidence_cleanup_ref"}
              onClick={() => onSectionClick("evidence_cleanup_ref")}
              wide={isWide}
            />
            {hasJdText && (
              <NavItem
                sectionKey="raw_jd"
                label="Raw JD"
                status="complete"
                active={activeSection === "raw_jd"}
                onClick={() => onSectionClick("raw_jd")}
                wide={isWide}
              />
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}

function NavItem({
  sectionKey,
  label,
  status,
  active,
  onClick,
  wide,
}: {
  sectionKey: string;
  label: string;
  status: SectionStatus | "complete";
  active: boolean;
  onClick: () => void;
  wide: boolean;
}) {
  const Icon = getSectionIcon(sectionKey);
  const isFailed = status === "failed";

  const button = (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors
        ${wide ? "" : "justify-center"}
        ${
          active
            ? "bg-brand-primary/5 text-brand-primary font-medium"
            : "text-text-body hover:bg-cream hover:text-text-primary"
        }`}
      title={wide ? label : undefined}
    >
      <span className="relative shrink-0">
        <Icon className="w-5 h-5" />
        {isFailed && (
          <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-error" />
        )}
      </span>
      {wide && <span className="truncate">{label}</span>}
    </button>
  );

  if (!wide) {
    return (
      <li>
        <Tooltip content={label}>{button}</Tooltip>
      </li>
    );
  }

  return <li>{button}</li>;
}
