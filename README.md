# payment-gateway

Payment processing gateway with PCI compliance

## Tech Stack
- **Language**: java
- **Team**: commerce
- **Platform**: Walmart Global K8s

## Quick Start
```bash
docker build -t payment-gateway:latest .
docker run -p 8080:8080 payment-gateway:latest
curl http://localhost:8080/health
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /ready | Readiness probe |
| GET | /metrics | Prometheus metrics |
# PR 2 - 2026-04-15T18:47:32
