-- Omni-Revenue-Agent Database Schema
-- Migration: 001_initial_schema
-- Description: Core tables for leads, products, orders, and KPI tracking

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- LEADS TABLE
-- ============================================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    source VARCHAR(50) CHECK (source IN ('Typeform', 'Jotform', 'Webflow', 'Zapier', 'Manual')),
    tags TEXT[],
    
    -- UTM tracking
    utm_source VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_term VARCHAR(255),
    utm_content VARCHAR(255),
    
    -- Enrichment data
    enrichment_company VARCHAR(255),
    enrichment_role VARCHAR(255),
    enrichment_linkedin VARCHAR(500),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_utm_campaign ON leads(utm_campaign);

-- ============================================================
-- PRODUCTS TABLE
-- ============================================================
CREATE TABLE products (
    sku VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('subscription', 'one_time', 'bundle')) NOT NULL,
    price_gbp DECIMAL(10, 2) NOT NULL,
    payment_gateways TEXT[] NOT NULL,
    fulfilment_webhook VARCHAR(500),
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_products_type ON products(type);
CREATE INDEX idx_products_active ON products(active);

-- ============================================================
-- ORDERS TABLE
-- ============================================================
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gateway VARCHAR(50) CHECK (gateway IN ('stripe', 'paypal')) NOT NULL,
    gateway_transaction_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) CHECK (status IN ('paid', 'refunded', 'disputed', 'pending', 'failed')) NOT NULL,
    amount_gbp DECIMAL(10, 2) NOT NULL,
    buyer_email VARCHAR(255) NOT NULL,
    buyer_name VARCHAR(255),
    sku VARCHAR(100) NOT NULL REFERENCES products(sku),
    
    -- Metadata
    metadata JSONB,
    
    -- Fulfillment tracking
    fulfilled BOOLEAN DEFAULT false,
    fulfilled_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_orders_gateway ON orders(gateway);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_buyer_email ON orders(buyer_email);
CREATE INDEX idx_orders_sku ON orders(sku);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_gateway_transaction_id ON orders(gateway_transaction_id);

-- ============================================================
-- KPI DAILY TABLE
-- ============================================================
CREATE TABLE kpi_daily (
    date DATE PRIMARY KEY,
    visitors INTEGER DEFAULT 0,
    leads INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    gross_gbp DECIMAL(10, 2) DEFAULT 0,
    net_gbp DECIMAL(10, 2) DEFAULT 0,
    refunds INTEGER DEFAULT 0,
    cr_pct DECIMAL(5, 2) DEFAULT 0,
    
    -- Additional metrics
    stripe_orders INTEGER DEFAULT 0,
    paypal_orders INTEGER DEFAULT 0,
    stripe_gross_gbp DECIMAL(10, 2) DEFAULT 0,
    paypal_gross_gbp DECIMAL(10, 2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_kpi_daily_date ON kpi_daily(date DESC);

-- ============================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gateway VARCHAR(50) CHECK (gateway IN ('stripe', 'paypal')) NOT NULL,
    gateway_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL REFERENCES products(sku),
    status VARCHAR(50) CHECK (status IN ('active', 'cancelled', 'past_due', 'trialing', 'paused')) NOT NULL,
    
    -- Billing details
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_subscriptions_customer_email ON subscriptions(customer_email);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_gateway_subscription_id ON subscriptions(gateway_subscription_id);

-- ============================================================
-- CONTENT ASSETS TABLE
-- ============================================================
CREATE TABLE content_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) CHECK (type IN ('article', 'email', 'audio', 'video', 'copy', 'ad_creative')) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    file_url VARCHAR(1000),
    metadata JSONB,
    
    -- Association
    product_sku VARCHAR(100) REFERENCES products(sku),
    campaign_id VARCHAR(100),
    
    published BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_content_assets_type ON content_assets(type);
CREATE INDEX idx_content_assets_product_sku ON content_assets(product_sku);
CREATE INDEX idx_content_assets_published ON content_assets(published);
CREATE INDEX idx_content_assets_created_at ON content_assets(created_at DESC);

-- ============================================================
-- EMAIL CAMPAIGNS TABLE
-- ============================================================
CREATE TABLE email_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body_html TEXT,
    body_text TEXT,
    
    -- Targeting
    segment_tags TEXT[],
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metrics
    recipients_count INTEGER DEFAULT 0,
    opens_count INTEGER DEFAULT 0,
    clicks_count INTEGER DEFAULT 0,
    conversions_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_campaigns_scheduled_at ON email_campaigns(scheduled_at);
CREATE INDEX idx_email_campaigns_sent_at ON email_campaigns(sent_at);

-- ============================================================
-- AUTOMATION LOGS TABLE
-- ============================================================
CREATE TABLE automation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    automation_id VARCHAR(100) NOT NULL,
    automation_name VARCHAR(255),
    status VARCHAR(50) CHECK (status IN ('started', 'completed', 'failed', 'partial')) NOT NULL,
    
    -- Execution details
    trigger_data JSONB,
    execution_data JSONB,
    error_message TEXT,
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

CREATE INDEX idx_automation_logs_automation_id ON automation_logs(automation_id);
CREATE INDEX idx_automation_logs_status ON automation_logs(status);
CREATE INDEX idx_automation_logs_started_at ON automation_logs(started_at DESC);

-- ============================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kpi_daily_updated_at BEFORE UPDATE ON kpi_daily FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_assets_updated_at BEFORE UPDATE ON content_assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_campaigns_updated_at BEFORE UPDATE ON email_campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- SEED DATA - PRODUCTS
-- ============================================================
INSERT INTO products (sku, title, type, price_gbp, payment_gateways, fulfilment_webhook, description) VALUES
('COPYKIT-MONTHLY', 'CopyKit Monthly', 'subscription', 49.00, ARRAY['stripe', 'paypal'], '/api/fulfilment/copykit', 'Weekly ad creatives and landing copy subscription'),
('COPYKIT-BUNDLE', 'CopyKit Full Funnel Pack', 'one_time', 199.00, ARRAY['stripe', 'paypal'], '/api/fulfilment/copykit', 'Complete funnel copy package - one-time purchase'),
('DAILYBRIEF-MONTHLY', 'Daily Briefing Monthly', 'subscription', 15.00, ARRAY['stripe', 'paypal'], '/api/fulfilment/briefing', 'Daily markets and trends briefing with audio');

-- ============================================================
-- VIEWS FOR REPORTING
-- ============================================================

-- Daily revenue summary view
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT 
    DATE(created_at) as date,
    gateway,
    COUNT(*) as order_count,
    SUM(amount_gbp) as gross_gbp,
    SUM(CASE WHEN status = 'refunded' THEN amount_gbp ELSE 0 END) as refunded_gbp,
    SUM(CASE WHEN status = 'paid' THEN amount_gbp ELSE 0 END) as net_gbp
FROM orders
GROUP BY DATE(created_at), gateway
ORDER BY date DESC, gateway;

-- Active subscriptions summary
CREATE OR REPLACE VIEW v_active_subscriptions AS
SELECT 
    sku,
    gateway,
    COUNT(*) as active_count,
    SUM(p.price_gbp) as mrr_gbp
FROM subscriptions s
JOIN products p ON s.sku = p.sku
WHERE s.status = 'active'
GROUP BY sku, gateway;

-- Lead conversion funnel
CREATE OR REPLACE VIEW v_conversion_funnel AS
SELECT 
    DATE(l.created_at) as date,
    COUNT(DISTINCT l.id) as leads,
    COUNT(DISTINCT o.id) as orders,
    ROUND(COUNT(DISTINCT o.id)::NUMERIC / NULLIF(COUNT(DISTINCT l.id), 0) * 100, 2) as conversion_rate_pct
FROM leads l
LEFT JOIN orders o ON l.email = o.buyer_email AND DATE(o.created_at) >= DATE(l.created_at)
GROUP BY DATE(l.created_at)
ORDER BY date DESC;

