FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/package.json
COPY telegram-mini-app/package.json ./telegram-mini-app/package.json
COPY packages/contracts/package.json ./packages/contracts/package.json
RUN pnpm install --frozen-lockfile --filter @bet-score/web...
COPY frontend ./frontend
COPY packages/contracts ./packages/contracts
RUN pnpm --filter @bet-score/web build

FROM node:22-alpine AS runtime
WORKDIR /app/frontend
ENV NODE_ENV=production
RUN addgroup -S betscore && adduser -S betscore -G betscore
COPY --from=build /app ./
USER betscore
EXPOSE 3000
CMD ["node_modules/.bin/next", "start", "--port", "3000"]
