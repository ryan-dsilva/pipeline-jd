import { type ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "tertiary" | "ghost" | "danger";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantStyles: Record<Variant, string> = {
  primary:
    "bg-brand-primary text-white hover:bg-brand-primary/90 focus-visible:ring-brand-primary shadow-sm",
  secondary:
    "bg-transparent text-teal border-2 border-teal hover:bg-teal/5 focus-visible:ring-teal",
  tertiary:
    "text-text-primary hover:text-text-primary/70 focus-visible:ring-text-primary",
  ghost:
    "text-text-secondary hover:bg-border-light/50 focus-visible:ring-border-medium",
  danger:
    "text-error border-2 border-error/30 hover:bg-error/5 focus-visible:ring-error",
};

const sizeStyles: Record<Size, string> = {
  sm: "px-2.5 py-1 text-xs",
  md: "px-4 py-2 text-sm",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={`inline-flex items-center justify-center font-medium rounded-md transition-colors
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1
          active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none
          ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
export default Button;
