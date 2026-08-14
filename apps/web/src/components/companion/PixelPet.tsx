"use client";

import { useEffect, useState } from "react";

import { PIXEL_PET_BODY, getPixelPetSpec, type PixelGrid } from "@/lib/pixel-pets";

const BODY_COLS = 12;
const BODY_ROWS = 12;

/** Composes topper + body + per-cell overrides into one final grid of
 * resolved hex colors (or null for transparent) — pure, no rendering
 * concerns, so it's cheap to recompute per blink-tick without touching
 * the DOM structure until the actual color values change. */
function composeRows(species: string, blinking: boolean): (string | null)[][] {
  const spec = getPixelPetSpec(species);
  const body: string[][] = PIXEL_PET_BODY.slice(0, BODY_ROWS).map((row) =>
    row.slice(0, BODY_COLS).padEnd(BODY_COLS, ".").split(""),
  );

  for (const { row, col, char } of spec.bodyOverrides ?? []) {
    if (body[row]) body[row]![col] = char;
  }

  const topperRows: string[][] = (spec.topper ?? []).map((row) =>
    row.padEnd(BODY_COLS, ".").split(""),
  );

  const colorOf = (char: string): string | null => {
    if (char === ".") return null;
    if (char === "B") return spec.bodyColor;
    if (char === "L") return spec.bellyColor;
    if (char === "E") return blinking ? spec.bodyColor : spec.eyeColor;
    return spec.accentColor; // any other letter is this species' one accent (topper/beak/shell/fin)
  };

  const resolvedTopper = topperRows.map((row) => row.map(colorOf));
  const resolvedBody = body.map((row) => row.map(colorOf));
  return [...resolvedTopper, ...resolvedBody];
}

interface PixelPetProps {
  species: string | null | undefined;
  /** Pixel (cell) size in CSS px. 6-10 reads as a crisp small icon; 14+ for a hero-sized companion. */
  size?: number;
  /** Gentle up/down idle loop. Off for tiny inline uses (icon-sized). */
  idle?: boolean;
  /** One-shot attention bounce — pass a changing key from the parent to retrigger it. */
  bounceKey?: number;
  className?: string;
}

/** Renders one of PIXEL_PETS as a grid of solid-color cells — plain
 * divs, not an SVG/canvas/image, so pixels stay perfectly crisp at any
 * integer size with zero asset loading and no `image-rendering` hacks
 * a raster sprite sheet would need. */
export function PixelPet({ species, size = 8, idle = true, bounceKey, className }: PixelPetProps) {
  const [blinking, setBlinking] = useState(false);

  useEffect(() => {
    if (!idle) return;
    // Blink roughly every 3.5-6s, held for ~150ms — irregular interval
    // reads as "alive", a fixed one reads as a broken loop.
    let timeout: ReturnType<typeof setTimeout>;
    const scheduleBlink = () => {
      const delay = 3500 + Math.random() * 2500;
      timeout = setTimeout(() => {
        setBlinking(true);
        setTimeout(() => setBlinking(false), 150);
        scheduleBlink();
      }, delay);
    };
    scheduleBlink();
    return () => clearTimeout(timeout);
  }, [idle]);

  const rows = composeRows(species ?? "bot", blinking);
  const cols = rows[0]?.length ?? BODY_COLS;

  return (
    <div
      key={bounceKey}
      className={`pixel-pet-sprite inline-grid select-none ${idle ? "pixel-pet-idle" : ""} ${
        bounceKey !== undefined ? "pixel-pet-bounce" : ""
      } ${className ?? ""}`}
      style={{
        gridTemplateColumns: `repeat(${cols}, ${size}px)`,
        gridTemplateRows: `repeat(${rows.length}, ${size}px)`,
      }}
      role="img"
      aria-label={`${getPixelPetSpec(species).label} companion`}
    >
      {rows.flatMap((row, r) =>
        row.map((color, c) => (
          <span
            key={`${r}-${c}`}
            style={{ width: size, height: size, background: color ?? "transparent" }}
          />
        )),
      )}
    </div>
  );
}
