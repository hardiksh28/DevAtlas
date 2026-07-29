import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

// Semantic tokens only — raw palette values live in globals.css as CSS
// variables (one place to tune light/dark). Components must use these
// semantic names (bg-canvas, text-ink, border-line, …), never raw
// Tailwind palette colors, so a theme change never means a find/replace
// across the app.
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    // packages/ui ships unbuilt source, so its class names need to be
    // scanned too — otherwise Tailwind purges classes the app never
    // wrote itself and shared components render unstyled in production.
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Page + panel surfaces
        canvas: token("canvas"),
        surface: {
          DEFAULT: token("surface"),
          muted: token("surface-muted"),
        },
        // Borders/dividers ("line" so classes read border-line, not border-border)
        line: {
          DEFAULT: token("line"),
          strong: token("line-strong"),
        },
        // Text
        ink: {
          DEFAULT: token("ink"),
          secondary: token("ink-secondary"),
          muted: token("ink-muted"),
          faint: token("ink-faint"),
        },
        // Brand accent (indigo). `accent` is for solid fills (buttons,
        // rings); `accent-ink` is the readable text/icon shade per theme.
        accent: {
          DEFAULT: token("accent"),
          hover: token("accent-hover"),
          soft: token("accent-soft"),
          ink: token("accent-ink"),
        },
        success: {
          DEFAULT: token("success"),
          soft: token("success-soft"),
          ink: token("success-ink"),
        },
        danger: {
          DEFAULT: token("danger"),
          hover: token("danger-hover"),
          soft: token("danger-soft"),
          ink: token("danger-ink"),
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", ...defaultTheme.fontFamily.sans],
        mono: ["var(--font-mono)", ...defaultTheme.fontFamily.mono],
      },
      boxShadow: {
        // Low-opacity, small-radius shadows only — panels rely on 1px
        // borders for definition, shadows just lift overlays.
        raised: "0 1px 2px 0 rgb(15 18 25 / 0.05)",
        overlay: "0 10px 30px -8px rgb(15 18 25 / 0.18), 0 2px 8px -2px rgb(15 18 25 / 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
