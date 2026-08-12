import type { SVGProps } from "react";

interface MarkProps extends SVGProps<SVGSVGElement> {
  /** Render the whole mark in currentColor (footer, one-color contexts)
   * instead of the default ink bezel + accent needle. */
  monochrome?: boolean;
}

/**
 * The DevAtlas mark: a compass bezel with an offset needle pointing
 * north-east — orientation and forward motion, drawn with engineering
 * plainness. The bezel inherits `currentColor` so it follows the
 * surrounding text color in light and dark themes; the needle carries
 * the accent unless `monochrome` is set. Scales from 16px favicons to
 * hero sizes because it is two shapes with no fine detail.
 */
export function DevAtlasMark({ monochrome = false, ...props }: MarkProps) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" fill="none" {...props}>
      <circle cx="16" cy="16" r="12.5" stroke="currentColor" strokeWidth="2.5" />
      <path
        d="M23.5 8.5 18 18 8.5 23.5 14 14Z"
        className={monochrome ? undefined : "fill-accent dark:fill-accent-ink"}
        fill={monochrome ? "currentColor" : undefined}
      />
    </svg>
  );
}

interface LogoProps {
  /** Overall size of the mark in px; the wordmark scales with it. */
  size?: number;
  monochrome?: boolean;
  className?: string;
  /** Render for placement on a black/dark surface (navbar, footer) — ink text becomes white. */
  dark?: boolean;
}

/** Full lockup: mark + “DevAtlas” wordmark. */
export function DevAtlasLogo({ size = 26, monochrome = false, className, dark = false }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${dark ? "text-white" : "text-ink"} ${className ?? ""}`}>
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-lg border shadow-sm transition-transform group-hover:scale-105 ${
          dark ? "bg-white/10 border-white/20" : "bg-surface border-line"
        }`}
      >
        <DevAtlasMark monochrome={monochrome} style={{ width: size - 4, height: size - 4 }} />
      </span>
      <span className={`font-extrabold tracking-tight text-xl ${dark ? "text-white" : "text-ink"}`}>
        Dev<span className={dark ? "text-accent" : "text-accent-ink"}>Atlas</span>
      </span>
    </span>
  );
}
