FROM oven/bun:latest AS build
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install

COPY . .
RUN bun run build

FROM oven/bun:slim AS runner
WORKDIR /app

COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules

EXPOSE 3000

CMD ["bun", "run", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
