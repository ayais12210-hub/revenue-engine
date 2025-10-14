# Revenue Engine Deployment Guide

This comprehensive guide walks you through deploying the entire Revenue Engine system from scratch. By the end of this guide, you will have a fully operational autonomous revenue-generation system running in production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Deployment (Supabase)](#database-deployment-supabase)
3. [API Deployment (Docker/Cloud Run)](#api-deployment-dockercloud-run)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Payment Gateway Setup](#payment-gateway-setup)
6. [Automation & Scheduling](#automation--scheduling)
7. [Monitoring & Observability](#monitoring--observability)
8. [DNS & Domain Configuration](#dns--domain-configuration)
9. [Post-Deployment Testing](#post-deployment-testing)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] A domain name (e.g., `copykit.io`)
- [ ] Accounts created for all required services:
  - [ ] Supabase (database)
  - [ ] Vercel (frontend hosting)
  - [ ] Docker Hub or Google Cloud (backend hosting)
  - [ ] Stripe (payments)
  - [ ] PayPal for Business (payments)
  - [ ] Cloudflare (DNS and CDN)
  - [ ] Sentry (error monitoring)
  - [ ] OpenRouter or OpenAI (LLM)
  - [ ] ElevenLabs (text-to-speech)
  - [ ] Polygon.io (market data)
  - [ ] Firecrawl (web scraping)
- [ ] All API keys and credentials documented
- [ ] Git repository created and code pushed

---

## Database Deployment (Supabase)

### Step 1: Create a Supabase Project

1. Go to [Supabase](https://supabase.com) and sign in.
2. Click **New Project**.
3. Fill in the project details:
   - **Name**: `omni-revenue-agent`
   - **Database Password**: Generate a strong password and save it securely.
   - **Region**: Choose the region closest to your users.
4. Click **Create new project** and wait for provisioning to complete.

### Step 2: Get Your Database Connection String

1. In your Supabase project dashboard, go to **Settings** → **Database**.
2. Copy the **Connection string** under the **Connection pooling** section.
3. Replace `[YOUR-PASSWORD]` with the password you set in Step 1.
4. Save this as your `DATABASE_URL` environment variable.

### Step 3: Run Database Migrations

You can apply the schema using either raw SQL or Prisma.

**Option A: Using SQL Editor (Supabase)**

1. In your Supabase dashboard, go to **SQL Editor**.
2. Click **New query**.
3. Copy the contents of `database/001_initial_schema.sql` and paste it into the editor.
4. Click **Run** to execute the migration.

**Option B: Using Prisma CLI**

1. Install Prisma CLI:
   ```bash
   npm install -g prisma
   ```

2. Set your `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres"
   ```

3. Generate Prisma client and push schema:
   ```bash
   cd database
   prisma generate
   prisma db push
   ```

### Step 4: Verify Tables

1. Go to **Table Editor** in Supabase.
2. Verify that all tables have been created:
   - `leads`
   - `products`
   - `orders`
   - `subscriptions`
   - `kpi_daily`
   - `content_assets`
   - `email_campaigns`
   - `automation_logs`

---

## API Deployment (Docker/Cloud Run)

### Option A: Deploy to Google Cloud Run

**Step 1: Build and Push Docker Image**

1. Install Google Cloud SDK:
   ```bash
   curl https://sdk.cloud.google.com | bash
   gcloud init
   ```

2. Authenticate Docker with Google Container Registry:
   ```bash
   gcloud auth configure-docker
   ```

3. Build and tag your Docker image:
   ```bash
   docker build -t gcr.io/[YOUR-PROJECT-ID]/omni-revenue-agent-api:latest .
   docker push gcr.io/[YOUR-PROJECT-ID]/omni-revenue-agent-api:latest
   ```

**Step 2: Deploy to Cloud Run**

1. Deploy the container:
   ```bash
   gcloud run deploy omni-revenue-agent-api \
     --image gcr.io/[YOUR-PROJECT-ID]/omni-revenue-agent-api:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL="[YOUR-DATABASE-URL]",STRIPE_SECRET_KEY="[YOUR-KEY]"
   ```

2. Note the service URL provided (e.g., `https://omni-revenue-agent-api-xxxxx-uc.a.run.app`).

**Step 3: Configure Environment Variables**

1. Go to Google Cloud Console → Cloud Run → Your Service.
2. Click **Edit & Deploy New Revision**.
3. Under **Variables & Secrets**, add all required environment variables from your `.env` file.
4. Click **Deploy**.

### Option B: Deploy to DigitalOcean App Platform

1. Go to [DigitalOcean](https://cloud.digitalocean.com) and create a new App.
2. Connect your Git repository.
3. Select **Dockerfile** as the build method.
4. Configure environment variables in the App settings.
5. Deploy!

---

## Frontend Deployment (Vercel)

### Step 1: Prepare the Frontend

1. Ensure your React app is in `web/copykit-landing`.
2. Test the build locally:
   ```bash
   cd web/copykit-landing
   pnpm run build
   ```

### Step 2: Deploy to Vercel

1. Go to [Vercel](https://vercel.com) and sign in.
2. Click **Add New Project**.
3. Import your Git repository.
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `web/copykit-landing`
   - **Build Command**: `pnpm run build`
   - **Output Directory**: `dist`
5. Add environment variables if needed (e.g., `VITE_API_URL`).
6. Click **Deploy**.

### Step 3: Configure Custom Domain

1. In your Vercel project, go to **Settings** → **Domains**.
2. Add your custom domain (e.g., `copykit.io`).
3. Follow the instructions to update your DNS records.

---

## Payment Gateway Setup

### Stripe Configuration

**Step 1: Create Products in Stripe**

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → **Products**.
2. Create three products:

   **Product 1: CopyKit Monthly**
   - Name: `CopyKit Monthly Subscription`
   - Price: `£49.00 GBP` / month
   - Billing: Recurring monthly
   - Metadata: `sku=COPYKIT-MONTHLY`

   **Product 2: CopyKit Bundle**
   - Name: `CopyKit Full Funnel Pack`
   - Price: `£199.00 GBP`
   - Billing: One-time
   - Metadata: `sku=COPYKIT-BUNDLE`

   **Product 3: Daily Briefing**
   - Name: `Daily Briefing Monthly`
   - Price: `£15.00 GBP` / month
   - Billing: Recurring monthly
   - Metadata: `sku=DAILYBRIEF-MONTHLY`

**Step 2: Configure Webhooks**

1. Go to **Developers** → **Webhooks**.
2. Click **Add endpoint**.
3. Enter your webhook URL: `https://your-api-domain.com/webhooks/stripe`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `charge.refunded`
   - `charge.dispute.created`
5. Copy the **Signing secret** and save it as `STRIPE_WEBHOOK_SECRET`.

**Step 3: Get API Keys**

1. Go to **Developers** → **API keys**.
2. Copy the **Secret key** and save it as `STRIPE_SECRET_KEY`.
3. Copy the **Publishable key** for use in your frontend.

### PayPal Configuration

**Step 1: Create PayPal App**

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com).
2. Click **Apps & Credentials**.
3. Create a new app.
4. Copy the **Client ID** and **Secret**.

**Step 2: Create Subscription Plans**

1. Go to **Products** → **Subscriptions**.
2. Create plans for each subscription product.
3. Note the **Plan ID** for each.

**Step 3: Configure Webhooks**

1. Go to **Webhooks**.
2. Add a new webhook: `https://your-api-domain.com/webhooks/paypal`
3. Subscribe to events:
   - `PAYMENT.CAPTURE.COMPLETED`
   - `BILLING.SUBSCRIPTION.CREATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `PAYMENT.CAPTURE.REFUNDED`

---

## Automation & Scheduling

### Option A: Cron Jobs (Linux Server)

1. SSH into your server.
2. Edit crontab:
   ```bash
   crontab -e
   ```

3. Add the daily briefing job:
   ```cron
   0 7 * * * /usr/bin/python3 /path/to/automations/daily_briefing.py >> /var/log/daily-briefing.log 2>&1
   ```

### Option B: Google Cloud Scheduler

1. Go to Google Cloud Console → Cloud Scheduler.
2. Create a new job:
   - **Name**: `daily-briefing`
   - **Frequency**: `0 7 * * *` (7 AM daily)
   - **Target**: HTTP
   - **URL**: `https://your-api-domain.com/automations/daily-briefing`
   - **HTTP method**: POST
3. Save and enable the job.

### Option C: Zapier Scheduled Triggers

1. Create a new Zap in Zapier.
2. **Trigger**: Schedule by Zapier → Every Day at 7:00 AM.
3. **Action**: Webhooks by Zapier → POST to `https://your-api-domain.com/automations/daily-briefing`.

---

## Monitoring & Observability

### Sentry Setup

1. Go to [Sentry](https://sentry.io) and create a new project.
2. Select **Flask** as the platform.
3. Copy the **DSN** and save it as `SENTRY_DSN`.
4. The `sentry_config.py` file will automatically initialize Sentry when the API starts.

### Cloudflare Rate Limiting

1. Go to Cloudflare Dashboard → Your Domain → Security → WAF.
2. Create rate limiting rules:
   - **Rule 1**: Limit `/api/*` to 120 requests per minute per IP.
   - **Rule 2**: Limit `/webhooks/*` to 60 requests per minute per IP.

---

## DNS & Domain Configuration

### Cloudflare DNS Setup

1. Add your domain to Cloudflare.
2. Update your domain registrar's nameservers to Cloudflare's.
3. Add DNS records:

   | Type  | Name | Content                          | Proxy Status |
   |-------|------|----------------------------------|--------------|
   | A     | @    | [Vercel IP from Vercel settings] | Proxied      |
   | CNAME | www  | yourdomain.com                   | Proxied      |
   | CNAME | api  | [Cloud Run URL]                  | Proxied      |

4. Enable **Always Use HTTPS** under SSL/TLS settings.

---

## Post-Deployment Testing

### Manual Testing Checklist

- [ ] Visit your domain and verify the homepage loads.
- [ ] Click through to the pricing page.
- [ ] Initiate a Stripe checkout (use test mode).
- [ ] Complete a test purchase with Stripe test card `4242 4242 4242 4242`.
- [ ] Verify the order appears in the Supabase `orders` table.
- [ ] Check that the webhook was received (check API logs).
- [ ] Verify email receipt was sent (if configured).
- [ ] Test PayPal checkout flow.
- [ ] Access the members area and verify authentication is required.

### Automated Testing

Run the E2E test suite:

```bash
pytest tests/e2e_tests.py -v
```

---

## Troubleshooting

### Issue: Database connection fails

**Solution**: Verify your `DATABASE_URL` is correct and includes the password. Check that your IP is allowed in Supabase settings (or use connection pooling).

### Issue: Stripe webhook not receiving events

**Solution**: 
1. Verify the webhook URL is correct and publicly accessible.
2. Check the webhook signing secret matches `STRIPE_WEBHOOK_SECRET`.
3. Look at the webhook logs in Stripe Dashboard → Developers → Webhooks.

### Issue: Frontend shows 404 on routes

**Solution**: Ensure your `vercel.json` includes rewrites for SPA routing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Issue: Automation scripts not running

**Solution**: 
1. Check cron job syntax with `crontab -l`.
2. Verify the Python path is correct.
3. Check logs for errors: `tail -f /var/log/daily-briefing.log`.

---

## Next Steps

After successful deployment:

1. **Set up monitoring alerts** in Sentry for critical errors.
2. **Configure backup strategy** for your database.
3. **Enable HTTPS** and verify SSL certificates are valid.
4. **Test the full user journey** from landing page to fulfillment.
5. **Monitor KPIs** in the `kpi_daily` table.
6. **Scale resources** as needed based on traffic.

Congratulations! Your Revenue Engine is now live and generating revenue autonomously.

