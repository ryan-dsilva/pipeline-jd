import { useState, useRef, useEffect } from "react";

interface DropdownItem {
  key: string;
  label: string;
}

interface DropdownProps {
  items: DropdownItem[];
  value: string;
  onChange: (key: string) => void;
  label?: string;
}

export default function Dropdown({
  items,
  value,
  onChange,
  label = "Select",
}: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const selected = items.find((i) => i.key === value);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-text-primary bg-white border border-border-light rounded-md hover:bg-off-white transition-colors"
      >
        {label} {selected?.label || value}
        <svg
          className={`w-4 h-4 text-text-secondary transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-1 w-48 bg-white border border-border-light rounded-md shadow-lg py-1">
          {items.map((item) => (
            <button
              key={item.key}
              onClick={() => {
                onChange(item.key);
                setOpen(false);
              }}
              className={`w-full text-left px-3 py-1.5 text-sm transition-colors ${
                item.key === value
                  ? "bg-brand-primary/5 text-brand-primary font-medium"
                  : "text-text-primary hover:bg-off-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
