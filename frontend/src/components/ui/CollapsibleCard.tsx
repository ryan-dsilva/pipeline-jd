import { useState, useRef, useEffect } from "react";

interface CollapsibleCardProps {
  id?: string;
  title: string;
  defaultExpanded?: boolean;
  editing?: boolean;
  actions?: React.ReactNode;
  statusDot?: React.ReactNode;
  preview?: string;
  children: React.ReactNode;
}

export default function CollapsibleCard({
  id,
  title,
  defaultExpanded = true,
  editing = false,
  actions,
  statusDot,
  preview,
  children,
}: CollapsibleCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | undefined>(
    defaultExpanded ? undefined : 0,
  );

  useEffect(() => {
    if (!contentRef.current) return;
    if (expanded) {
      setHeight(contentRef.current.scrollHeight);
      const timer = setTimeout(() => setHeight(undefined), 200);
      return () => clearTimeout(timer);
    } else {
      setHeight(contentRef.current.scrollHeight);
      requestAnimationFrame(() => setHeight(0));
    }
  }, [expanded]);

  // Always expand when entering edit mode
  useEffect(() => {
    if (editing) setExpanded(true);
  }, [editing]);

  return (
    <div
      id={id}
      className={`border rounded-lg bg-white shadow-md transition-colors ${
        editing
          ? "border-teal ring-2 ring-teal/20"
          : "border-border-light"
      }`}
    >
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer select-none"
        onClick={() => !editing && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 min-w-0">
          {statusDot}
          <h3 className="text-sm font-medium text-text-primary truncate">
            {title}
          </h3>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {actions}
          <svg
            className={`w-4 h-4 text-text-secondary transition-transform duration-200 ${
              expanded ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      <div
        ref={contentRef}
        className="overflow-hidden transition-[height] duration-200 ease-in-out"
        style={{ height: height != null ? `${height}px` : "auto" }}
      >
        <div className="px-4 pb-4">
          {children}
        </div>
      </div>

      {!expanded && preview && (
        <div className="px-4 pb-3 text-sm text-text-body line-clamp-2">
          {preview}
        </div>
      )}
    </div>
  );
}
