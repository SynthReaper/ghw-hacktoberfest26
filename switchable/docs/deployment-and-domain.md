# Production Deployment and .tech Domain Setup Guide

This guide details the procedure for deploying **Open-Switch** to Render using the Blueprint (`render.yaml`), attaching a persistent disk, and binding a custom `.tech` domain claimed via the Hacktoberfest Week 2 partner perks.

---

## 1. Architecture Overview

```
                      +----------------------------------+
                      |         User / Visitor           |
                      +----------------------------------+
                                       |
                                       v
                      +----------------------------------+
                      | HTTPS: https://openswitch.tech    |
                      | (Cloudflare / Radix .tech DNS)   |
                      +----------------------------------+
                                       | CNAME
                                       v
                      +----------------------------------+
                      | Render Web Service               |
                      | open-switch.onrender.com         |
                      +----------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
        +---------------------+                 +---------------------+
        |  Docker Container   |                 |   Persistent Disk   |
        |  FastAPI + Uvicorn  | <=============> |   /var/data         |
        |  Port 8000 (Non-root|                 |   - openswitch.db   |
        |  appuser)           |                 |   - reports/        |
        +---------------------+                 +---------------------+
```

---

## 2. Render Blueprint Deployment

1. **Prerequisites**:
   - Push repository to GitHub.
   - Render account (use the $25 promotional credits from `hacktoberfest.com/my/promos`).

2. **Deploy via Blueprint**:
   - Open [dashboard.render.com](https://dashboard.render.com).
   - Click **New +** -> **Blueprint**.
   - Connect the repository `switchable`.
   - Render will parse `render.yaml` and discover:
     - Web service: `open-switch` (Docker runtime)
     - Persistent disk: `openswitch-data` (1 GB mounted at `/var/data`)
     - Health check: `/health`

3. **Configure Environment Secrets** (Marked `sync: false` in `render.yaml`):
   Set the following variables in the Render dashboard:
   - `SENTRY_DSN`: `https://...@sentry.io/...` (for error tracking and gen_ai agent spans)
   - `DO_MODEL_ACCESS_KEY`: DigitalOcean GenAI access token
   - `BACKBOARD_API_KEY`: Backboard inference token
   - `TINKER_API_KEY`: Tinker LoRA fine-tuning token
   - `BASELINE_API_KEY`: Closed-API key for incumbent evaluation baseline

4. **Verify Health**:
   Once build completes, verify:
   ```bash
   curl -I https://open-switch.onrender.com/health
   # Returns: HTTP/2 200 with {"status": "ok", "mode": "hosted", "version": "0.1.0"}
   ```

---

## 3. Claiming and Configuring the .tech Domain (T-030)

1. **Claim Free .tech Domain**:
   - Navigate to `hacktoberfest.com/my/promos`.
   - Copy the Radix .tech promo voucher code (1 year free registration).
   - Visit [get.tech](https://get.tech) and search for a domain (e.g. `openswitch.tech` or `open-switch.tech`).
   - Checkout with the promo code.

2. **Configure DNS Records** (at registrar or DNS provider):
   Create the following DNS records pointing to Render:

   | Record Type | Name / Host | Target / Value | TTL | Note |
   |-------------|-------------|----------------|-----|------|
   | **CNAME**   | `@` or `demo` | `open-switch.onrender.com` | Automatic / 300 | Primary domain |
   | **CNAME**   | `www`       | `open-switch.onrender.com` | Automatic / 300 | Web redirect |

3. **Bind Custom Domain in Render**:
   - Go to the `open-switch` web service in the Render Dashboard.
   - Click **Settings** -> **Custom Domains**.
   - Add `openswitch.tech` (and `www.openswitch.tech`).
   - Render will verify DNS records and automatically issue an SSL/TLS certificate via Let's Encrypt within 5 minutes.

4. **Verification**:
   ```bash
   curl -I https://openswitch.tech/health
   # Returns: HTTP/2 200 with {"status": "ok"}
   ```

---

## 4. Production Safety Invariants

- **Read-Only / Local Mode Fallback**: If `OPENSWITCH_MODE=local`, non-localhost requests are blocked.
- **Kill Switch**: If needed, set `KILL_SWITCH=true` in Render environment variables. All new evaluation experiments and fine-tunes will immediately return HTTP 503 and render an emergency pause banner on the UI.
- **Daily Spend Cap**: Enforced by `GLOBAL_DAILY_BUDGET_USD=5.0`.
- **Demo Data Cleanup**: In demo mode, records older than 24 hours are purged automatically during startup and periodic cycles.
