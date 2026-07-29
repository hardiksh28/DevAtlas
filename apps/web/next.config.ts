import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the Dockerfile's runtime stage — bundles a minimal
  // server + only the dependencies actually used, instead of shipping
  // node_modules wholesale into the image.
  output: "standalone",
  // "ui" is a pnpm workspace package with untranspiled TSX source (no
  // build step of its own) — Next needs to know to run it through its
  // own compiler rather than treating it as pre-built node_modules code.
  transpilePackages: ["ui"],
};

export default nextConfig;
