FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# trong mạng compose, /api đi thẳng vào service api; Caddy vẫn là đường chính
ARG API_PROXY_URL=http://api:8000
ENV API_PROXY_URL=$API_PROXY_URL
# TIP-13: staging bật banner + noindex; đặt =0 khi build production
ARG NEXT_PUBLIC_STAGING=1
ENV NEXT_PUBLIC_STAGING=$NEXT_PUBLIC_STAGING
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
