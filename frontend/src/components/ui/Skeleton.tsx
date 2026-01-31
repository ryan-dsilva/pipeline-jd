interface SkeletonProps {
  className?: string;
}

export function SkeletonLine({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`h-4 bg-border-light/30 rounded animate-pulse ${className}`}
    />
  );
}

export function SkeletonBlock({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`h-24 bg-border-light/30 rounded-lg animate-pulse ${className}`}
    />
  );
}

export function SkeletonTableRow() {
  return (
    <tr className="border-b border-border-light/50">
      <td className="py-3 pr-4">
        <SkeletonLine className="w-28" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-40" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-12" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-10" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-20" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-16" />
      </td>
      <td className="py-3 pr-4">
        <SkeletonLine className="w-14" />
      </td>
    </tr>
  );
}
