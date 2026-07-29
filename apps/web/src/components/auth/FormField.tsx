import type { InputHTMLAttributes } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

/**
 * Shared across every auth form (login/register/forgot/reset) — five
 * near-identical label+input+focus-ring blocks is exactly the "three
 * similar lines" threshold where extracting one component pays for
 * itself instead of being premature abstraction.
 */
export function FormField({ label, id, ...props }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        {...props}
      />
    </div>
  );
}
