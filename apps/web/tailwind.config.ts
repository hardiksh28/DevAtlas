import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    // packages/ui ships unbuilt source, so its class names need to be
    // scanned too — otherwise Tailwind purges classes the app never
    // wrote itself and shared components render unstyled in production.
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
