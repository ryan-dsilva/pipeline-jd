import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'text' | 'textarea' | 'url';
  error?: boolean;
  rows?: number;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', variant = 'text', error = false, ...props }, ref) => {
    const baseClasses = 'bg-white border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-colors';
    const borderClasses = error
      ? 'border-error/50 focus:ring-error'
      : 'border-border-light focus:ring-brand-primary';
    const textClasses = 'text-text-primary placeholder-text-secondary';

    if (variant === 'textarea') {
      return (
        <textarea
          ref={ref as any}
          className={`${baseClasses} ${borderClasses} ${textClasses} ${className} resize-none`}
          {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
        />
      );
    }

    return (
      <input
        ref={ref}
        type={variant === 'url' ? 'url' : 'text'}
        className={`${baseClasses} ${borderClasses} ${textClasses} ${className}`}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';

export default Input;
