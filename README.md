'''
# Revenue Engine

This project is a fully-autonomous revenue generation system built from the **Revenue Engine** specification. It integrates multiple services to create, market, sell, and fulfill digital products, with a focus on daily, automated cash flow to Stripe and PayPal.

## Table of Contents

- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Project Structure](#project-structure)
- [Database Setup](#database-setup)
- [API Setup](#api-setup)
- [Frontend Setup](#frontend-setup)
- [Automation Setup](#automation-setup)
- [Testing](#testing)
- [Deployment](#deployment)
  - [Frontend (Vercel)](#frontend-vercel)
  - [Backend (Docker)](#backend-docker)
- [Environment Variables](#environment-variables)
- [Revenue Strategies](#revenue-strategies)

---

## Architecture

The system is built on a modern, decoupled architecture:

- **Frontend**: A React-based landing page built with Vite, Tailwind CSS, and shadcn/ui. Designed for deployment on Vercel.
- **Backend**: A Flask API that handles webhooks (Stripe, PayPal), fulfillment logic, and lead management. Designed for deployment as a Docker container.
- **Database**: A PostgreSQL database managed with Prisma. The schema is designed for Supabase but is compatible with any PostgreSQL provider.
- **Automations**: Python scripts for recurring tasks like the daily briefing generation, which can be run as cron jobs or triggered by services like Zapier.
- **Testing**: End-to-end tests using Playwright and error monitoring with Sentry.

### Core Components

| Component         | Technology/Service | Purpose                                                              |
| ----------------- | ------------------ | -------------------------------------------------------------------- |
| **Web Properties**  | React, Webflow     | Sales pages, checkout, and member areas.                             |
| **Payments**        | Stripe, PayPal     | Processing subscriptions and one-time payments.                      |
| **Database**        | Supabase/Postgres  | Storing leads, products, orders, and KPIs.                           |
| **API & Webhooks**  | Flask, Vercel Edge | Handling payment events, fulfillment, and lead intake.               |
| **Content Gen**     | OpenAI, ElevenLabs | Generating blog articles, email copy, and audio briefings.           |
| **Automation**      | Python, Zapier     | Orchestrating daily tasks, lead nurturing, and fulfillment.          |
| **Observability**   | Sentry, Playwright | Monitoring for errors, performance, and running E2E tests.           |
| **Deployment**      | Vercel, Docker     | Hosting the frontend and backend services.                           |

---

## Getting Started

### Quick Start (Recommended)

The easiest way to get started is using our automated setup script:

```bash
# Clone the repository
git clone <repository-url>
cd omni-revenue-agent

# Run the setup script
./scripts/setup.sh

# Or with Docker Compose
docker-compose up -d
```

The setup script will:
- Check all prerequisites
- Install dependencies
- Set up the database
- Build Docker images
- Start all services
- Run initial tests

### Manual Setup

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (v3.9+)
- [Docker](https://www.docker.com/)
- [pnpm](https://pnpm.io/)
- Access to a PostgreSQL database (e.g., a free Supabase project)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd omni-revenue-agent
    ```

2.  **Create and configure your environment file:**

    ```bash
    cp .env.example .env
    ```

    Fill in the required values in the `.env` file. See the [Environment Variables](#environment-variables) section for details.

3.  **Install dependencies for each component:**

    ```bash
    # API dependencies
    pip install -r api/requirements.txt

    # Frontend dependencies
    cd web/copykit-landing
    pnpm install
    cd ../../

    # Automation dependencies
    pip install -r automations/requirements.txt

    # Testing dependencies
    pip install -r tests/requirements.txt
    playwright install
    ```

4.  **Set up the database:**

    ```bash
    # Run database migrations
    python scripts/migrate.py
    ```

---

## Project Structure

```
/omni-revenue-agent
├── api/                    # Flask backend API
│   ├── app.py              # Main Flask application
│   └── requirements.txt    # Python dependencies
├── automations/            # Standalone automation scripts
│   ├── daily_briefing.py   # A3-briefing-daily automation
│   └── lead_intake.py      # A1-lead-intake automation
├── database/               # Database schema and migrations
│   ├── 001_initial_schema.sql # Raw SQL for initial setup
│   └── schema.prisma       # Prisma schema for ORM
├── docs/                   # Documentation files
├── tests/                  # Testing suite
│   ├── e2e_tests.py        # Playwright E2E tests
│   └── sentry_config.py    # Sentry configuration
├── web/                    # Frontend applications
│   └── copykit-landing/    # React landing page project
├── .env.example            # Example environment variables
├── Dockerfile              # Dockerfile for the API
├── README.md               # This file
└── vercel.json             # Vercel deployment configuration
```

---

## Database Setup

1.  **Get your PostgreSQL connection string** from your provider (e.g., Supabase).

2.  **Set the `DATABASE_URL`** in your `.env` file. This URL must include the password for your database user.

3.  **Apply the initial schema:**

    You can either run the `001_initial_schema.sql` file directly against your database or use Prisma to migrate the schema.

    **Using Prisma:**

    ```bash
    # Generate the Prisma client
    prisma generate

    # Push the schema to the database
    prisma db push
    ```

    This will create all the tables, enums, and relationships defined in `database/schema.prisma`.

---

## API Setup

The Flask API is the core of the system, handling webhooks and fulfillment.

1.  **Ensure all dependencies are installed:**

    ```bash
    pip install -r api/requirements.txt
    ```

2.  **Run the development server:**

    ```bash
    python api/app.py
    ```

    The API will be running at `http://localhost:5000`.

3.  **For production, use a WSGI server like Gunicorn:**

    ```bash
    gunicorn --bind 0.0.0.0:5000 api.app:app
    ```

---

## Frontend Setup

The React landing page is built with Vite and includes a comprehensive monitoring dashboard.

1.  **Navigate to the project directory:**

    ```bash
    cd web/copykit-landing
    ```

2.  **Ensure dependencies are installed:**

    ```bash
    pnpm install
    ```

3.  **Start the development server:**

    ```bash
    pnpm run dev
    ```

    The frontend will be available at `http://localhost:5173`.

### Monitoring Dashboard

Access the real-time monitoring dashboard at `http://localhost:3000/dashboard` to view:

- **System Health**: Database, Stripe, and API status
- **Revenue Metrics**: Real-time revenue and order tracking
- **Conversion Analytics**: Lead-to-order conversion rates
- **Performance Charts**: Interactive revenue and traffic charts
- **Recent Orders**: Live order feed with status updates
- **KPI Trends**: Historical performance data

The dashboard automatically refreshes every 30 seconds and provides comprehensive insights into your revenue engine performance.

---

## Automation Setup

The automation scripts are designed to be run on a schedule.

### Daily Briefing (`A3-briefing-daily`)

This script fetches market data, scrapes news, generates content with an LLM, and creates audio/video assets.

-   **To run manually:**

    ```bash
    python automations/daily_briefing.py
    ```

-   **To schedule with cron:**

    Add the following line to your crontab to run the script daily at 7 AM BST:

    ```cron
    0 7 * * * /usr/bin/python3 /path/to/omni-revenue-agent/automations/daily_briefing.py
    ```

### Lead Intake (`A1-lead-intake`)

This script is designed to be triggered by a webhook from a form service (like Typeform or Jotform) via Zapier.

1.  Set up a webhook in your form provider.
2.  Configure the webhook to send a `POST` request to your API endpoint (e.g., `https://your-api-domain.com/api/leads`).
3.  The `lead_intake.py` script contains the logic that will be executed by the API when a new lead is received.

---

## Testing

The project includes an E2E test suite using Playwright.

1.  **Ensure testing dependencies are installed:**

    ```bash
    pip install -r tests/requirements.txt
    playwright install
    ```

2.  **Make sure both the frontend and backend development servers are running.**

3.  **Run the test suite:**

    ```bash
    pytest tests/e2e_tests.py
    ```

---

## Deployment

### Frontend (Vercel)

The frontend is optimized for deployment on Vercel.

1.  **Create a new project on Vercel** and connect it to your Git repository.
2.  **Configure the project settings:**
    -   **Framework Preset**: `Vite`
    -   **Build Command**: `pnpm run build`
    -   **Output Directory**: `web/copykit-landing/dist`
    -   **Install Command**: `cd web/copykit-landing && pnpm install`
3.  **Add your environment variables** to the Vercel project settings.
4.  **Deploy!** Vercel will automatically build and deploy your site.

The `vercel.json` file is included to ensure correct routing and configuration.

### Backend (Docker)

The Flask API is designed to be deployed as a Docker container.

1.  **Build the Docker image:**

    ```bash
    docker build -t omni-revenue-agent-api -f Dockerfile .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d -p 5000:5000 --env-file .env omni-revenue-agent-api
    ```

    This will start the API container and expose it on port 5000. You can deploy this container to any service that supports Docker, such as AWS ECS, Google Cloud Run, or DigitalOcean App Platform.

---

## Environment Variables

Create a `.env` file in the root directory and add the following variables. See `.env.example` for a template.

| Variable                      | Description                                                  |
| ----------------------------- | ------------------------------------------------------------ |
| `DATABASE_URL`                | **Required.** PostgreSQL connection string.                  |
| `SECRET_KEY`                  | **Required.** Flask secret key for session management.         |
| `STRIPE_SECRET_KEY`           | **Required.** Your Stripe secret API key.                      |
| `STRIPE_WEBHOOK_SECRET`       | **Required.** Your Stripe webhook signing secret.              |
| `PAYPAL_CLIENT_ID`            | **Required.** Your PayPal client ID.                         |
| `PAYPAL_CLIENT_SECRET`        | **Required.** Your PayPal client secret.                     |
| `OPENROUTER_API_KEY`          | **Required.** Your OpenRouter API key.                       |
| `COHERE_API_KEY`              | **Required.** Your Cohere API key.                           |
| `ELEVENLABS_API_KEY`          | **Required.** Your ElevenLabs API key.                       |
| `INVIDEO_API_KEY`             | API key for InVideo.                                         |
| `SENTRY_DSN`                  | DSN for Sentry error monitoring.                             |
| `POLYGON_API_KEY`             | API key for Polygon.io financial data.                       |
| `FIRECRAWL_API_KEY`           | API key for Firecrawl web scraping.                          |
| `EXPLORIUM_API_KEY`           | API key for Explorium data enrichment.                       |
| `NOTION_API_KEY`              | API key for Notion integration.                              |
| `LINEAR_API_KEY`              | API key for Linear integration.                              |
| `NOTION_CRM_DATABASE_ID`      | ID of the Notion database for CRM records.                   |
| `LINEAR_TEAM_ID`              | ID of the Linear team for creating tasks.                    |

---

## 🚀 New Features & Enhancements

### Enhanced Security
- **Rate Limiting**: Comprehensive rate limiting with Redis backend
- **Input Validation**: Advanced input sanitization and validation
- **CORS Configuration**: Secure cross-origin resource sharing
- **API Key Authentication**: Secure API endpoints with key-based auth
- **Webhook Verification**: Enhanced Stripe and PayPal webhook security

### Monitoring & Analytics
- **Real-time Dashboard**: Comprehensive monitoring dashboard with live metrics
- **Health Checks**: Detailed system health monitoring
- **Performance Metrics**: Request timing and error tracking
- **Revenue Analytics**: Advanced KPI tracking and visualization
- **Automated Alerts**: Sentry integration for error monitoring

### Database Management
- **Migration System**: Automated database migration runner
- **Seed Data**: Pre-populated sample data for testing
- **Performance Indexes**: Optimized database queries
- **Analytics Views**: Pre-built views for common queries
- **Data Validation**: Comprehensive data integrity checks

### Development Experience
- **Docker Compose**: One-command local development setup
- **Hot Reloading**: Automatic code reloading in development
- **Comprehensive Logging**: Structured logging throughout the system
- **API Documentation**: Complete API documentation with examples
- **Setup Scripts**: Automated environment setup and configuration

### Production Ready
- **Error Handling**: Comprehensive error handling and recovery
- **Graceful Degradation**: System continues working when services fail
- **Scalability**: Designed for horizontal scaling
- **Monitoring**: Built-in health checks and metrics
- **Security**: Production-grade security features

---

## Revenue Strategies

This system is pre-configured with two primary revenue strategies:

1.  **AI CopyKit Micro-SaaS (`S1-copykit`)**
    -   **Offer**: A £49/month subscription for weekly ad creatives and landing page copy, or a £199 one-time purchase for a full funnel pack.
    -   **Stack**: Webflow, Stripe, PayPal, Supabase, Zapier, Notion.

2.  **Daily Markets & Trends Briefing (`S2-signal-briefing`)**
    -   **Offer**: A £15/month newsletter and audio brief with trading and creator economy insights.
    -   **Stack**: Gmail, Webflow/Notion, Stripe, PayPal, ElevenLabs, InVideo.

These strategies are designed to generate recurring and one-time revenue through automated content creation and fulfillment.
'''
