# UptimeRobot Setup for TGIndex

## Why UptimeRobot?

Render.com free tier **sleeps after 15 minutes** of inactivity. UptimeRobot pings your server every 5 minutes to keep it awake.

## Free Tier

- **50 monitors** (you need 1)
- **5-minute intervals**
- **Email alerts** when server is down
- **No credit card** required

## Setup Steps

### 1. Create Account

1. Go to https://uptimerobot.com/
2. Click **Register for FREE**
3. Sign up with email

### 2. Add Monitor

1. Click **Add New Monitor**
2. Choose **Monitor Type**: `HTTP(s)`
3. Fill in:
   - **Friendly Name**: `TGIndex API`
   - **URL**: `https://your-app-name.onrender.com/ping`
   - **Monitoring Interval**: `5 minutes`
4. Click **Create Monitor**

### 3. Endpoints to Monitor

| Endpoint | Purpose |
|----------|---------|
| `https://your-app.onrender.com/ping` | Simple ping (recommended) |
| `https://your-app.onrender.com/api/v1/system/health` | Health check with DB status |
| `https://your-app.onrender.com/` | Root endpoint |

**Recommended**: Use `/ping` — fastest response, no DB check.

### 4. Verify

1. Go to **Dashboard** in UptimeRobot
2. You should see your monitor with **UP** status
3. Check **Logs** to see ping history

## How It Works

```
UptimeRobot (every 5 min) → GET /ping → Server stays awake
                                          ↓
                                    Render doesn't sleep
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Monitor shows DOWN | Check Render logs, ensure app is deployed |
| Server still sleeps | Verify UptimeRobot is pinging correct URL |
| Response time slow | First request after sleep takes ~30s to wake |

## Alternative: Cron Job on Another Server

If you have access to any Linux server:

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * curl -s https://your-app.onrender.com/ping > /dev/null 2>&1
```
