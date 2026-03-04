# Accessibility Platform — Frontend Dockerfile
# Multi-stage build: Node build → Nginx serve

# Development stage — Vite dev server with hot reload
FROM node:20-alpine AS development

WORKDIR /app

# Install dependencies first for better layer caching
# --ignore-scripts prevents husky from running
COPY package*.json ./
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start Vite dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage — Generate production assets
FROM node:20-alpine AS build

WORKDIR /app

# Accept build arguments for Firebase config
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_APP_ID
ARG VITE_USE_FIREBASE_EMULATOR

# Expose arguments as environment variables for the build
ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID
ENV VITE_USE_FIREBASE_EMULATOR=$VITE_USE_FIREBASE_EMULATOR

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --ignore-scripts

# Copy source and env files
COPY . .

# Create a .env.production dynamically from build args so Vite picks up the correct values
# This avoids the build being influenced by a checked-in .env.production file.
RUN printf "VITE_FIREBASE_API_KEY=%s\nVITE_FIREBASE_AUTH_DOMAIN=%s\nVITE_FIREBASE_PROJECT_ID=%s\nVITE_FIREBASE_APP_ID=%s\nVITE_USE_FIREBASE_EMULATOR=%s\n" \
    "$VITE_FIREBASE_API_KEY" "$VITE_FIREBASE_AUTH_DOMAIN" "$VITE_FIREBASE_PROJECT_ID" "$VITE_FIREBASE_APP_ID" "$VITE_USE_FIREBASE_EMULATOR" \
    > .env.production

# Build production assets (Vite will read .env.production)
RUN npm run build

# Production stage — Serve with Nginx
FROM nginx:1.25-alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
