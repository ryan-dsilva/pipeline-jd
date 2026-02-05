import { useRef, useState, useEffect } from "react";

interface ExpandableTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  collapsedRows?: number;
  expandedRows?: number;
  className?: string;
  onBlur?: () => void;
}

export default function ExpandableTextarea({
  value,
  onChange,
  placeholder,
  disabled = false,
  readOnly = false,
  collapsedRows = 3,
  expandedRows = 10,
  className = "",
  onBlur,
}: ExpandableTextareaProps) {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Calculate if content fits in collapsed state
  const fitsInCollapsed = () => {
    if (!textareaRef.current) return true;
    const lineHeight = parseInt(
      getComputedStyle(textareaRef.current).lineHeight || "20"
    );
    const maxCollapsedHeight = lineHeight * collapsedRows;
    textareaRef.current.style.height = "auto";
    const scrollHeight = textareaRef.current.scrollHeight;
    return scrollHeight <= maxCollapsedHeight;
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    // Collapse if content fits
    if (fitsInCollapsed()) {
      setIsFocused(false);
    }
    onBlur?.();
  };

  // Determine current rows based on state
  const currentRows = isFocused ? expandedRows : collapsedRows;

  // Check if we need to stay expanded (content doesn't fit)
  useEffect(() => {
    if (!isFocused && !fitsInCollapsed()) {
      // Content doesn't fit, stay expanded
      setIsFocused(true);
    }
  }, [value, isFocused, collapsedRows]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onFocus={handleFocus}
      onBlur={handleBlur}
      placeholder={placeholder}
      disabled={disabled}
      readOnly={readOnly}
      rows={currentRows}
      className={`w-full px-3 py-2 border border-border-primary rounded-md font-mono text-sm
        focus:ring-2 focus:ring-primary/50 focus:border-primary
        disabled:bg-bg-secondary disabled:cursor-not-allowed
        read-only:bg-bg-secondary
        transition-[height] duration-200 ease-in-out resize-none ${className}`}
    />
  );
}
