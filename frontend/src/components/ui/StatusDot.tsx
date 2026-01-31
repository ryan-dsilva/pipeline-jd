import React from 'react';

type StatusType = 'pending' | 'running' | 'complete' | 'error';

interface StatusDotProps {
  status: StatusType;
  size?: 'sm' | 'md';
}

const StatusDot: React.FC<StatusDotProps> = ({ status, size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'w-2 h-2' : 'w-3 h-3';

  const statusClasses = {
    pending: 'bg-border-medium',
    running: 'bg-teal animate-pulse',
    complete: 'bg-sage',
    error: 'bg-error',
  };

  return (
    <div
      className={`${sizeClasses} ${statusClasses[status]} rounded-full`}
      role="status"
      aria-label={`Status: ${status}`}
    />
  );
};

export default StatusDot;
