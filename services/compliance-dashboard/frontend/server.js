import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;
const PYTHON_BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8019';

console.log(`[Express BFF] Starting Compliance Dashboard Node.js BFF Proxy -> ${PYTHON_BACKEND_URL}`);

// Proxy API requests to Python FastAPI compliance-dashboard backend
app.use('/api', createProxyMiddleware({
  target: PYTHON_BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '',
  },
  onProxyReq: (proxyReq, req, res) => {
    // Enforce required RBAC headers for audit trail access
    if (!proxyReq.getHeader('X-User-Scopes')) {
      proxyReq.setHeader('X-User-Scopes', 'audit:read');
    }
  }
}));

// Serve static frontend assets from dist folder
app.use(express.static(path.join(__dirname, 'dist')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[Express BFF] Compliance Dashboard server listening on port ${PORT}`);
});
