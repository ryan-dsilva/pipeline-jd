import { type ButtonHTMLAttributes, forwardRef } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  size?: "sm" | "md";
}

const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, size = "sm", className = "", children, ...props }, ref) => {
    const sizeStyles = size === "sm" ? "p-1" : "p-1.5";
    return (
      <button
        ref={ref}
        aria-label={label}
        title={label}
        className={`inline-flex items-center justify-center rounded-md text-text-secondary
          hover:text-text-primary hover:bg-cream transition-colors
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary
          active:scale-[0.95] disabled:opacity-50 disabled:pointer-events-none
          ${sizeStyles} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  },
);

IconButton.displayName = "IconButton";
export default IconButton;
