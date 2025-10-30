# Blue/Green Deployment with Nginx + Slack Alerts

Nginx-based Blue/Green deployment with automatic failover and real-time Slack monitoring.

## Quick Start
```bash
# Clone and setup
git clone https://github.com/codeagen/blue-green-nginx-deployment.git
cd blue-green-nginx-deployment
cp .env.example .env

# Add your Slack webhook to .env
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Start services
docker-compose up -d

# Test
curl http://localhost:8080/version
```

## Services

- **Nginx**: `http://localhost:8080` (public endpoint)
- **Blue**: `http://localhost:8081` (primary app)
- **Green**: `http://localhost:8082` (backup app)
- **Watcher**: Monitors logs and sends Slack alerts

## Configuration

Edit `.env`:
```properties
# Deployment
ACTIVE_POOL=blue
RELEASE_ID_BLUE=release-1.0.0
RELEASE_ID_GREEN=release-1.0.1

# Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
ERROR_RATE_THRESHOLD=2
WINDOW_SIZE=200
ALERT_COOLDOWN_SEC=300
```

## Testing Failover + Alerts
```bash
# Trigger chaos on Blue
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate traffic to trigger alerts
for i in {1..20}; do curl http://localhost:8080/version; done

# Check Slack for "Failover Detected" alert
# Traffic automatically switches to Green

# Stop chaos
curl -X POST http://localhost:8081/chaos/stop
```

## Testing Error Rate Alert
```bash
# Trigger errors
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate high volume
for i in {1..100}; do curl http://localhost:8080/version; done

# Check Slack for "High Error Rate" alert

# Stop chaos
curl -X POST http://localhost:8081/chaos/stop
```

## Viewing Logs
```bash
# Nginx logs (custom format with pool info)
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Watcher logs
docker-compose logs watcher -f

# App logs
docker-compose logs app_blue -f
```

**Log format:**
```
pool=blue release=release-1.0.0 status=200 upstream=app_blue:8081 request_time=0.005
```

## Alerts

The watcher sends Slack alerts for:
- **Failover events** - When traffic switches between Blue/Green
- **High error rate** - When >2% of requests fail (configurable)

See [runbook.md](runbook.md) for alert response procedures.

## Screenshots

Required screenshots are in `/screenshots/`:
- Failover alert in Slack
- High error rate alert in Slack
- Nginx log format example

## Endpoints

- `GET /version` - Version info with headers
- `GET /healthz` - Health check
- `POST /chaos/start?mode=error` - Simulate downtime
- `POST /chaos/stop` - Stop simulation

## Troubleshooting

**No Slack alerts?**
```bash
docker-compose logs watcher
curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"Test"}'
```

**No logs appearing?**
```bash
docker-compose exec nginx cat /var/log/nginx/access.log
```

## Stop Services
```bash
docker-compose down -v
```

---