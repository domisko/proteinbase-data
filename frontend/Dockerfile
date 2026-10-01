FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
# Vite serves the app and proxies /api to the backend (API_PROXY_TARGET).
CMD ["npm", "run", "dev"]
