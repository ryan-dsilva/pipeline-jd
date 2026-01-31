type BadgeVariant =
  | "emerald"
  | "blue"
  | "amber"
  | "rose"
  | "gray"
  | "indigo";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  emerald: "bg-sage/10 text-sage ring-sage/20",
  blue: "bg-teal/10 text-teal ring-teal/20",
  amber: "bg-amber/10 text-amber ring-amber/20",
  rose: "bg-error/10 text-error ring-error/20",
  gray: "bg-border-light/30 text-text-body ring-border-medium/20",
  indigo: "bg-brand-primary/10 text-brand-primary ring-brand-primary/20",
};

export default function Badge({
  variant = "gray",
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

export function verdictBadgeVariant(verdict: string | null): BadgeVariant {
  switch (verdict) {
    case "STRONG PURSUE":
      return "emerald";
    case "PURSUE":
      return "blue";
    case "PASS":
      return "amber";
    case "HARD PASS":
      return "rose";
    default:
      return "gray";
  }
}
