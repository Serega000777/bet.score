FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json ./
RUN pnpm install --frozen-lockfile=false
COPY . .
RUN pnpm build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S sportai && adduser -S sportai -G sportai
COPY --from=build /app ./
USER sportai
EXPOSE 3000
CMD ["npm", "run", "start"]

