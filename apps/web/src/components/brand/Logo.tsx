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
}

/** Full lockup: mark + “DevAtlas” wordmark. */
export function DevAtlasLogo({ size = 24, monochrome = false, className }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 text-ink ${className ?? ""}`}>
      <DevAtlasMark monochrome={monochrome} style={{ width: size, height: size }} />
      <span
        className="font-semibold tracking-tight"
        style={{ fontSize: Math.round(size * 0.78) }}
      >
        DevAtlas
      </span>
    </span>
  );
}
