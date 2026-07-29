interface SkeletonProps {
  className?: string;
}

/** Loading placeholder block — size it with className (h-*, w-*). */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-md bg-surface-muted ${className ?? ""}`}
    />
  );
}

/** Card-shaped skeleton matching ProjectCard's layout. */
export function CardSkeleton() {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-surface p-4">
      <Skeleton className="h-9 w-9" />
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-full" />
      </div>
      <Skeleton className="h-3 w-24" />
    </div>
  );
}
