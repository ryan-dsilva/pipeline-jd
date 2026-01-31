interface SegmentedControlItem {
  key: string;
  label: string;
  count?: number;
}

interface SegmentedControlProps {
  items: SegmentedControlItem[];
  value: string;
  onChange: (key: string) => void;
}

export default function SegmentedControl({
  items,
  value,
  onChange,
}: SegmentedControlProps) {
  return (
    <div className="inline-flex bg-cream rounded-lg p-0.5">
      {items.map((item) => (
        <button
          key={item.key}
          onClick={() => onChange(item.key)}
          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
            value === item.key
              ? "bg-white text-text-primary shadow-sm"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          {item.label}
          {item.count != null && (
            <span
              className={`ml-1.5 text-xs ${
                value === item.key ? "text-text-body" : "text-text-secondary"
              }`}
            >
              {item.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
