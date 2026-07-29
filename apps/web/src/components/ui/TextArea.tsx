import { forwardRef, type TextareaHTMLAttributes } from "react";

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  hint?: string;
  optional?: boolean;
};

/** Labeled textarea matching FormField's styling — used by the project
 * create/settings forms for descriptions. */
export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, id, hint, optional = false, className, ...props },
  ref,
) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink-secondary">
        {label} {optional && <span className="font-normal text-ink-faint">(optional)</span>}
      </label>
      <textarea
        ref={ref}
        id={id}
        aria-describedby={hint ? `${id}-hint` : undefined}
        className={`w-full rounded-md border border-line-strong bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-faint transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 focus:ring-offset-0 ${className ?? ""}`}
        {...props}
      />
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-ink-faint">
          {hint}
        </p>
      )}
    </div>
  );
});
