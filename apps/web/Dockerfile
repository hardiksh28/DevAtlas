# Build context is the monorepo root (not apps/web) so pnpm workspace
# packages (e.g. packages/ui) resolve correctly. See docker-compose.yml.

FROM node:20-alpine AS base
RUN corepack enable

FROM base AS deps
WORKDIR /repo
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web/package.json apps/web/package.json
COPY packages/ui/package.json packages/ui/package.json
RUN pnpm install --frozen-lockfile || pnpm install

FROM base AS builder
WORKDIR /repo
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY . .
RUN pnpm --filter web build

# --- Runtime: Next.js standalone output, non-root user ---
FROM base AS runner
WORKDIR /repo
ENV NODE_ENV=production
RUN addgroup --system nodejs && adduser --system --ingroup nodejs nextjs

COPY --from=builder /repo/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/static ./apps/web/.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "apps/web/server.js"]
