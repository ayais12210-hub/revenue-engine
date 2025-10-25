-- Migration: 002_seed_data.sql
-- Description: Seed initial data for the revenue engine system
-- Author: AI Assistant
-- Date: 2025-01-27

-- ============================================================
-- SEED PRODUCTS
-- ============================================================

INSERT INTO products (sku, title, type, price_gbp, payment_gateways, fulfilment_webhook, description, active, created_at, updated_at) VALUES
('COPYKIT-MONTHLY', 'CopyKit Monthly Subscription', 'subscription', 49.00, ARRAY['stripe', 'paypal'], 'https://api.copykit.io/api/fulfilment/copykit', 'Weekly AI-powered ad creatives and landing page copy delivered to your Notion workspace', true, NOW(), NOW()),
('COPYKIT-BUNDLE', 'Full Funnel Pack', 'one_time', 199.00, ARRAY['stripe', 'paypal'], 'https://api.copykit.io/api/fulfilment/copykit', 'Complete funnel copy package with 50+ ad creatives, 5 landing pages, and 3 email sequences', true, NOW(), NOW()),
('DAILYBRIEF-MONTHLY', 'Daily Briefing Subscription', 'subscription', 15.00, ARRAY['stripe', 'paypal'], 'https://api.copykit.io/api/fulfilment/briefing', 'Daily market insights, trend analysis, and audio briefings delivered to your inbox', true, NOW(), NOW())
ON CONFLICT (sku) DO UPDATE SET
    title = EXCLUDED.title,
    type = EXCLUDED.type,
    price_gbp = EXCLUDED.price_gbp,
    payment_gateways = EXCLUDED.payment_gateways,
    fulfilment_webhook = EXCLUDED.fulfilment_webhook,
    description = EXCLUDED.description,
    active = EXCLUDED.active,
    updated_at = NOW();

-- ============================================================
-- SEED SAMPLE LEADS (for testing)
-- ============================================================

INSERT INTO leads (id, email, name, source, tags, utm_source, utm_campaign, utm_medium, utm_term, utm_content, enrichment_company, enrichment_role, enrichment_linkedin, created_at, updated_at) VALUES
(gen_random_uuid(), 'test@example.com', 'Test User', 'Manual', ARRAY['test', 'demo'], 'google', 'copykit_test', 'cpc', 'ai copywriting', 'banner_ad', 'Example Corp', 'Marketing Manager', 'https://linkedin.com/in/testuser', NOW(), NOW()),
(gen_random_uuid(), 'demo@company.com', 'Demo User', 'Webflow', ARRAY['demo', 'enterprise'], 'facebook', 'copykit_enterprise', 'social', 'b2b copywriting', 'video_ad', 'Demo Company', 'VP Marketing', 'https://linkedin.com/in/demouser', NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- SEED SAMPLE KPI DATA (last 30 days)
-- ============================================================

-- Generate sample KPI data for the last 30 days
WITH date_series AS (
    SELECT generate_series(
        CURRENT_DATE - INTERVAL '29 days',
        CURRENT_DATE,
        INTERVAL '1 day'
    )::date AS date
),
random_data AS (
    SELECT 
        date,
        -- Random visitors between 50-200
        (50 + random() * 150)::int AS visitors,
        -- Random leads between 2-15 (3-7.5% conversion)
        (2 + random() * 13)::int AS leads,
        -- Random orders between 0-5 (0-2.5% conversion)
        (random() * 5)::int AS orders,
        -- Random revenue based on orders
        (random() * 5)::int * 49.00 AS gross_gbp,
        -- Random refunds (0-1 per day)
        (random() * 2)::int AS refunds,
        -- Random conversion rate
        (random() * 5)::numeric(5,2) AS cr_pct
    FROM date_series
)
INSERT INTO kpi_daily (
    date, visitors, leads, orders, gross_gbp, net_gbp, refunds, cr_pct,
    stripe_orders, paypal_orders, stripe_gross_gbp, paypal_gross_gbp,
    created_at, updated_at
)
SELECT 
    date,
    visitors,
    leads,
    orders,
    gross_gbp,
    gross_gbp - (refunds * 49.00), -- Net revenue
    refunds,
    cr_pct,
    -- Split orders between Stripe and PayPal (70/30)
    (orders * 0.7)::int AS stripe_orders,
    (orders * 0.3)::int AS paypal_orders,
    (gross_gbp * 0.7) AS stripe_gross_gbp,
    (gross_gbp * 0.3) AS paypal_gross_gbp,
    NOW(),
    NOW()
FROM random_data
ON CONFLICT (date) DO UPDATE SET
    visitors = EXCLUDED.visitors,
    leads = EXCLUDED.leads,
    orders = EXCLUDED.orders,
    gross_gbp = EXCLUDED.gross_gbp,
    net_gbp = EXCLUDED.net_gbp,
    refunds = EXCLUDED.refunds,
    cr_pct = EXCLUDED.cr_pct,
    stripe_orders = EXCLUDED.stripe_orders,
    paypal_orders = EXCLUDED.paypal_orders,
    stripe_gross_gbp = EXCLUDED.stripe_gross_gbp,
    paypal_gross_gbp = EXCLUDED.paypal_gross_gbp,
    updated_at = NOW();

-- ============================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================

-- Indexes for leads table
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_utm_campaign ON leads(utm_campaign);

-- Indexes for orders table
CREATE INDEX IF NOT EXISTS idx_orders_gateway ON orders(gateway);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_email ON orders(buyer_email);
CREATE INDEX IF NOT EXISTS idx_orders_sku ON orders(sku);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_gateway_transaction_id ON orders(gateway_transaction_id);

-- Indexes for subscriptions table
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_email ON subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_gateway_subscription_id ON subscriptions(gateway_subscription_id);

-- Indexes for kpi_daily table
CREATE INDEX IF NOT EXISTS idx_kpi_daily_date ON kpi_daily(date DESC);

-- Indexes for content_assets table
CREATE INDEX IF NOT EXISTS idx_content_assets_type ON content_assets(type);
CREATE INDEX IF NOT EXISTS idx_content_assets_product_sku ON content_assets(product_sku);
CREATE INDEX IF NOT EXISTS idx_content_assets_published ON content_assets(published);
CREATE INDEX IF NOT EXISTS idx_content_assets_created_at ON content_assets(created_at DESC);

-- Indexes for automation_logs table
CREATE INDEX IF NOT EXISTS idx_automation_logs_automation_id ON automation_logs(automation_id);
CREATE INDEX IF NOT EXISTS idx_automation_logs_status ON automation_logs(status);
CREATE INDEX IF NOT EXISTS idx_automation_logs_started_at ON automation_logs(started_at DESC);

-- ============================================================
-- CREATE VIEWS FOR ANALYTICS
-- ============================================================

-- Daily revenue summary view
CREATE OR REPLACE VIEW daily_revenue_summary AS
SELECT 
    date,
    visitors,
    leads,
    orders,
    gross_gbp,
    net_gbp,
    refunds,
    cr_pct,
    -- Calculate conversion rates
    CASE WHEN visitors > 0 THEN (leads::float / visitors * 100) ELSE 0 END AS lead_conversion_rate,
    CASE WHEN leads > 0 THEN (orders::float / leads * 100) ELSE 0 END AS order_conversion_rate,
    CASE WHEN visitors > 0 THEN (orders::float / visitors * 100) ELSE 0 END AS overall_conversion_rate,
    -- Calculate average order value
    CASE WHEN orders > 0 THEN (gross_gbp / orders) ELSE 0 END AS avg_order_value
FROM kpi_daily
ORDER BY date DESC;

-- Monthly revenue summary view
CREATE OR REPLACE VIEW monthly_revenue_summary AS
SELECT 
    DATE_TRUNC('month', date) AS month,
    SUM(visitors) AS total_visitors,
    SUM(leads) AS total_leads,
    SUM(orders) AS total_orders,
    SUM(gross_gbp) AS total_gross_gbp,
    SUM(net_gbp) AS total_net_gbp,
    SUM(refunds) AS total_refunds,
    AVG(cr_pct) AS avg_conversion_rate,
    SUM(stripe_orders) AS stripe_orders,
    SUM(paypal_orders) AS paypal_orders,
    SUM(stripe_gross_gbp) AS stripe_revenue,
    SUM(paypal_gross_gbp) AS paypal_revenue
FROM kpi_daily
GROUP BY DATE_TRUNC('month', date)
ORDER BY month DESC;

-- Product performance view
CREATE OR REPLACE VIEW product_performance AS
SELECT 
    p.sku,
    p.title,
    p.type,
    p.price_gbp,
    COUNT(o.id) AS total_orders,
    SUM(o.amount_gbp) AS total_revenue,
    AVG(o.amount_gbp) AS avg_order_value,
    COUNT(CASE WHEN o.status = 'paid' THEN 1 END) AS successful_orders,
    COUNT(CASE WHEN o.status = 'refunded' THEN 1 END) AS refunded_orders,
    COUNT(CASE WHEN o.status = 'disputed' THEN 1 END) AS disputed_orders,
    COUNT(CASE WHEN o.fulfilled = true THEN 1 END) AS fulfilled_orders
FROM products p
LEFT JOIN orders o ON p.sku = o.sku
GROUP BY p.sku, p.title, p.type, p.price_gbp
ORDER BY total_revenue DESC;

-- ============================================================
-- GRANT PERMISSIONS
-- ============================================================

-- Grant read permissions to analytics user (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analytics_user') THEN
        GRANT SELECT ON daily_revenue_summary TO analytics_user;
        GRANT SELECT ON monthly_revenue_summary TO analytics_user;
        GRANT SELECT ON product_performance TO analytics_user;
    END IF;
END $$;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Verify data was inserted correctly
SELECT 'Products' as table_name, COUNT(*) as count FROM products
UNION ALL
SELECT 'Leads', COUNT(*) FROM leads
UNION ALL
SELECT 'KPI Daily', COUNT(*) FROM kpi_daily
UNION ALL
SELECT 'Daily Revenue Summary', COUNT(*) FROM daily_revenue_summary
UNION ALL
SELECT 'Monthly Revenue Summary', COUNT(*) FROM monthly_revenue_summary
UNION ALL
SELECT 'Product Performance', COUNT(*) FROM product_performance;