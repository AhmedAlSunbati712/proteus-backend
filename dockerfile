# Gateway Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build TypeScript (if needed)
RUN npm run build || true

# Expose port
EXPOSE 3000

# Start the gateway
CMD ["node", "dist/index.js"]