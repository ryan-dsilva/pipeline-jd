import { useMemo, useState } from "react";
import { marked } from "marked";
import type { Section, SectionDefinition } from "../lib/types";
import { regenerateSection, updateSection } from "../lib/api";
import { playBloop } from "../lib/sound";
import SectionEditor from "./SectionEditor";
import CollapsibleCard from "./ui/CollapsibleCard";
import IconButton from "./ui/IconButton";

// Configure marked to open all links in new tabs
const renderer = new marked.Renderer();
renderer.link = ({ href, title, text }) => {
  const titleAttr = title ? ` title="${title}"` : "";
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
};
marked.use({ renderer });

interface SectionPanelProps {
  definition: SectionDefinition;
  section: Section | undefined;
  jobId: string;
  onUpdate: () => void;
  defaultExpanded?: boolean;
}

const STATUS_DOT: Record<string, string> = {
  pending: "bg-border-medium",
  running: "bg-teal animate-pulse",
  complete: "bg-sage",
  failed: "bg-error",
};

export default function SectionPanel({
  definition,
  section,
  jobId,
  onUpdate,
  defaultExpanded = true,
}: SectionPanelProps) {
  const [editing, setEditing] = useState(false);
  const [viewRaw, setViewRaw] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const status = section?.status || "pending";

  // Content is from our own backend (Claude-generated markdown), not user-supplied HTML.
  // The marked library converts markdown to HTML in a controlled way.
  const contentHtml = useMemo(
    () =>
      section?.content_md ? (marked.parse(section.content_md) as string) : "",
    [section?.content_md],
  );

  const preview = section?.content_md
    ? section.content_md.replace(/[#*_`>\[\]]/g, "").slice(0, 150)
    : undefined;

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDraft(section?.content_md || "");
    setEditing(true);
    setViewRaw(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSection(jobId, definition.key, draft);
      setEditing(false);
      playBloop();
      onUpdate();
    } catch {
      /* keep editing */
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setRegenerating(true);
    try {
      await regenerateSection(jobId, definition.key);
      playBloop();
      onUpdate();
    } catch {
      /* ignore */
    } finally {
      setRegenerating(false);
    }
  };

  const toggleViewRaw = (e: React.MouseEvent) => {
    e.stopPropagation();
    setViewRaw(!viewRaw);
  };

  const actions = (
    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
      {status === "complete" && !editing && (
        <>
          <button
            onClick={toggleViewRaw}
            className="px-2 py-0.5 text-xs rounded text-text-secondary hover:text-text-primary hover:bg-cream mr-1"
          >
            {viewRaw ? "View Markdown" : "View Text"}
          </button>
          <button
            onClick={handleEdit}
            className="px-2 py-0.5 text-xs rounded text-text-secondary hover:text-text-primary hover:bg-cream"
          >
            Edit
          </button>
        </>
      )}
      {status !== "running" && (
        <IconButton
          label="Regenerate"
          onClick={handleRegenerate}
          disabled={regenerating}
        >
          <svg
            className={`w-3.5 h-3.5 ${regenerating ? "animate-spin" : ""}`}
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
  );

  const statusDot = (
    <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_DOT[status]}`} />
  );

  return (
    <CollapsibleCard
      id={`section-${definition.key}`}
      title={definition.label}
      defaultExpanded={defaultExpanded}
      editing={editing}
      actions={actions}
      statusDot={statusDot}
      preview={preview}
    >
      {status === "failed" && section?.error_message && (
        <p className="text-sm text-error">{section.error_message}</p>
      )}

      {status === "running" && (
        <p className="text-sm text-text-secondary animate-pulse">Generating...</p>
      )}

      {status === "pending" && (
        <p className="text-sm text-text-secondary">Not yet generated</p>
      )}

      {status === "complete" && editing ? (
        <div className="space-y-3">
          <SectionEditor content={draft} onChange={setDraft} />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 text-xs bg-brand-primary text-white rounded-md hover:bg-brand-primary/90 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-3 py-1.5 text-xs text-text-body rounded-md hover:bg-cream"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : status === "complete" && section?.content_md ? (
        viewRaw ? (
          <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto text-text-body">
            {section.content_md}
          </pre>
        ) : (
          <div
            className="prose prose-sm max-w-none text-text-body [&_li_p]:m-0 [&_p]:my-1.5 [&_ul]:my-2 [&_ol]:my-2"
            // Content sourced from our own backend (Claude-generated markdown)
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        )
      ) : null}
    </CollapsibleCard>
  );
}
