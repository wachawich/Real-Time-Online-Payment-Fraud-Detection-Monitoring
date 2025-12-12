# --- Stage 1: Build Stage ---
# เปลี่ยนจาก node:18-alpine เป็น node:20-alpine
FROM node:20-alpine AS builder 

WORKDIR /app

# Copy dependency files
COPY package.json yarn.lock ./
RUN yarn install

# Copy all source code
COPY . .

# Build Next.js (output: .next)
RUN yarn build

# --- Stage 2: Production Runner ---
# เปลี่ยนจาก node:18-alpine เป็น node:20-alpine เช่นกัน
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3001

# Copy only necessary build artifacts
COPY --from=builder /app/package.json ./
COPY --from=builder /app/yarn.lock ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# ตั้งค่า Port ตามที่คุณต้องการ (3001)
EXPOSE 3001
CMD ["yarn", "start"]