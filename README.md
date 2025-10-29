# Blue/Green Deployment with Nginx

Nginx-based Blue/Green deployment for Node.js apps with automatic failover.

## Quick Start
```bash
# Clone and setup
git clone <your-repo-url>
cd <repo-name>
cp .env.example .env

# Start services
docker-compose up -d

# Test
curl http://localhost:8080/version
```

## Services

- **Nginx**: `http://localhost:8080` (public endpoint)
- **Blue**: `http://localhost:8081` (direct access)
- **Green**: `http://localhost:8082` (direct access)

## Testing Failover
```bash
# Trigger chaos on Blue
curl -X POST http://localhost:8081/chaos/start?mode=error

# Traffic automatically switches to Green
curl http://localhost:8080/version

# Stop chaos
curl -X POST http://localhost:8081/chaos/stop
```

## Configuration

Edit `.env` to configure:
- `ACTIVE_POOL` - Set to `blue` or `green` to choose primary instance
- `RELEASE_ID_BLUE` / `RELEASE_ID_GREEN` - Release identifiers

Restart after changing:
```bash
docker-compose restart
```

## How It Works

- Blue is primary by default, Green is backup
- Nginx detects failures via health checks (`max_fails=2`, `fail_timeout=5s`)
- Failed requests automatically retry to backup instance
- Zero downtime failover with proper header forwarding

## Endpoints

- `GET /version` - Version info with headers
- `GET /healthz` - Health check
- `POST /chaos/start?mode=error` - Simulate downtime
- `POST /chaos/stop` - Stop simulation

## Stop Services
```bash
docker-compose down
```