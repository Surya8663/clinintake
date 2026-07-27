import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3002;
const PYTHON_BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8020';

console.log(`[Express BFF] Starting Metrics Dashboard Node.js BFF Proxy -> ${PYTHON_BACKEND_URL}`);

// Proxy API requests to Python FastAPI metrics-dashboard backend
app.use('/api', createProxyMiddleware({
  target: PYTHON_BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '',
  },
}));

// Serve static frontend assets from dist folder
app.use(express.static(path.join(__dirname, 'dist')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[Express BFF] Metrics Dashboard server listening on port ${PORT}`);
});
