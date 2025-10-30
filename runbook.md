# DevOps Alert Runbook

## Overview
This runbook explains what each alert means and how operators should respond.

---

## Alert Types

### Failover Detected

**Alert Message:**
```
Failover Detected!
Pool changed: blue → green
Time: 2025-10-30 20:45:32
```

**What It Means:**
Traffic has automatically switched from one pool (Blue/Green) to another due to the primary pool becoming unhealthy.

**Operator Actions:**
1. **Check the failed pool's health:**
```bash
   # Check container status
   docker-compose ps
   
   # Check logs of the failed pool
   docker-compose logs app_blue    # if Blue failed
   docker-compose logs app_green   # if Green failed
```

2. **Investigate the root cause:**
   - Check application logs for errors
   - Verify resource usage (CPU, memory)
   - Check recent deployments or changes

3. **Restore service:**
```bash
   # Restart the failed container
   docker-compose restart app_blue
   
   # Verify it's healthy
   curl http://localhost:8081/version
```

4. **Monitor recovery:**
   - Watch for traffic to return to the primary pool
   - Confirm no more failover alerts

**Expected Recovery Time:** 2-5 minutes

---

###  High Error Rate

**Alert Message:**
```
 High Error Rate!
Error rate: 5.2% (threshold: 2%)
Last 200 requests
Time: 2025-10-30 20:45:32
```

**What It Means:**
More than the configured threshold (default 2%) of requests are failing with 5xx errors over the recent request window.

**Operator Actions:**
1. **Check current traffic distribution:**
```bash
   # Check which pool is serving traffic
   curl -i http://localhost:8080/version
```

2. **Review upstream logs:**
```bash
   # Check both pools for errors
   docker-compose logs app_blue --tail=100
   docker-compose logs app_green --tail=100
```

3. **Check nginx logs:**
```bash
   docker-compose logs nginx --tail=100
```

4. **Immediate actions:**
   - If one pool is causing errors, consider manual failover:
```bash
     # Update .env to switch ACTIVE_POOL
     # Then reload
     docker-compose restart nginx
```
   - If both pools are unhealthy, investigate deployment or infrastructure issues

5. **Long-term fixes:**
   - Roll back recent deployment if applicable
   - Scale resources if needed
   - Fix application bugs causing errors

**Expected Resolution Time:** 5-15 minutes

---

## Alert Management

### Suppressing Alerts During Maintenance

If you're performing planned maintenance or testing:

1. **Stop the watcher temporarily:**
```bash
   docker-compose stop watcher
```

2. **Perform your maintenance:**
```bash
   # Example: manual pool toggle
   curl -X POST http://localhost:8081/chaos/start?mode=error
   # ... testing ...
   curl -X POST http://localhost:8081/chaos/stop
```

3. **Restart the watcher:**
```bash
   docker-compose start watcher
```

### Alert Cooldown

Alerts have a built-in cooldown period (default: 300 seconds / 5 minutes) to prevent spam.

If you need to adjust:
```bash
# Edit .env
ALERT_COOLDOWN_SEC=600  # 10 minutes
```

---

## Thresholds Configuration

### Error Rate Threshold
Default: 2%

Adjust in `.env`:
```properties
ERROR_RATE_THRESHOLD=5  # Increase to 5% if needed
```

### Window Size
Default: 200 requests

Adjust in `.env`:
```properties
WINDOW_SIZE=500  # Increase window for smoother averaging
```

---

## Testing Alerts

### Test Failover Alert
```bash
# Trigger chaos on active pool
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate traffic to trigger failover
for i in {1..20}; do curl http://localhost:8080/version; done

# Check Slack for failover alert

# Stop chaos
curl -X POST http://localhost:8081/chaos/stop
```

### Test Error Rate Alert
```bash
# Trigger errors
curl -X POST http://localhost:8081/chaos/start?mode=error

# Generate enough requests to breach threshold
for i in {1..100}; do curl http://localhost:8080/version; done

# Check Slack for error rate alert

# Stop chaos
curl -X POST http://localhost:8081/chaos/stop
```

---

## Monitoring Health

### Check All Services
```bash
docker-compose ps
```

### View Watcher Logs
```bash
docker-compose logs watcher -f
```

### View Nginx Access Logs
```bash
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Check Slack Webhook
```bash
curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"Test alert from runbook"}'
```

---

## Escalation

If issues persist after following this runbook:

 **Gather diagnostic information:**
```bash
   docker-compose logs > debug.log
   docker-compose ps >> debug.log
```


## Quick Reference

| Alert Type | Severity | Response Time | Action |
|------------|----------|---------------|--------|
| Failover | Medium | 5 min | Check failed pool logs |
| High Error Rate | High | Immediate | Check all upstream logs |
| Recovery | Info | N/A | Monitor for stability |

---
