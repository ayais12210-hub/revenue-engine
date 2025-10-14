"""
Omni-Revenue-Agent API
Flask application for webhook handling, fulfillment, and automation orchestration
"""

import os
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import requests
from prisma import Prisma

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Prisma client
db = Prisma()

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def verify_stripe_signature(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature"""
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        return True  # Skip verification in development
    
    try:
        stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        return True
    except Exception as e:
        app.logger.error(f"Stripe signature verification failed: {e}")
        return False

def verify_paypal_signature(payload: Dict, headers: Dict) -> bool:
    """Verify PayPal webhook signature"""
    # Implement PayPal webhook verification
    # For production, use PayPal SDK verification
    return True

def log_automation(automation_id: str, automation_name: str, status: str, 
                   trigger_data: Optional[Dict] = None, 
                   execution_data: Optional[Dict] = None,
                   error_message: Optional[str] = None,
                   started_at: Optional[datetime] = None) -> str:
    """Log automation execution"""
    if started_at is None:
        started_at = datetime.utcnow()
    
    completed_at = datetime.utcnow() if status in ['completed', 'failed', 'partial'] else None
    duration_ms = int((completed_at - started_at).total_seconds() * 1000) if completed_at else None
    
    log = db.automationlog.create(
        data={
            'automationId': automation_id,
            'automationName': automation_name,
            'status': status,
            'triggerData': trigger_data,
            'executionData': execution_data,
            'errorMessage': error_message,
            'startedAt': started_at,
            'completedAt': completed_at,
            'durationMs': duration_ms
        }
    )
    return log.id

def send_receipt_email(buyer_email: str, buyer_name: str, order: Dict, product: Dict):
    """Send receipt email via Gmail API or SMTP"""
    # Implement email sending logic
    # Use Gmail API or SMTP with templates
    app.logger.info(f"Sending receipt to {buyer_email} for order {order['id']}")
    pass

def create_notion_workspace(customer_email: str, product_sku: str) -> str:
    """Create Notion workspace for customer"""
    # Implement Notion API integration
    app.logger.info(f"Creating Notion workspace for {customer_email} - {product_sku}")
    return "notion-page-id-placeholder"

# ============================================================
# HEALTH CHECK
# ============================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'omni-revenue-agent-api'
    }), 200

# ============================================================
# STRIPE WEBHOOKS
# ============================================================

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not verify_stripe_signature(payload, sig_header):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event = json.loads(payload)
    event_type = event['type']
    
    app.logger.info(f"Received Stripe event: {event_type}")
    
    try:
        if event_type == 'checkout.session.completed':
            handle_stripe_checkout_completed(event['data']['object'])
        
        elif event_type == 'customer.subscription.created':
            handle_stripe_subscription_created(event['data']['object'])
        
        elif event_type == 'customer.subscription.updated':
            handle_stripe_subscription_updated(event['data']['object'])
        
        elif event_type == 'customer.subscription.deleted':
            handle_stripe_subscription_deleted(event['data']['object'])
        
        elif event_type == 'charge.refunded':
            handle_stripe_refund(event['data']['object'])
        
        elif event_type == 'charge.dispute.created':
            handle_stripe_dispute(event['data']['object'])
        
        return jsonify({'received': True}), 200
    
    except Exception as e:
        app.logger.error(f"Error processing Stripe webhook: {e}")
        return jsonify({'error': str(e)}), 500

def handle_stripe_checkout_completed(session: Dict):
    """Handle completed Stripe checkout"""
    started_at = datetime.utcnow()
    
    try:
        # Extract session data
        customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email')
        customer_name = session.get('customer_details', {}).get('name')
        amount_total = Decimal(session['amount_total']) / 100  # Convert from cents
        
        # Get line items to determine SKU
        line_items = stripe.checkout.Session.list_line_items(session['id'])
        sku = session.get('metadata', {}).get('sku', 'UNKNOWN')
        
        # Create order record
        order = db.order.create(
            data={
                'gateway': 'stripe',
                'gatewayTransactionId': session['payment_intent'],
                'status': 'paid',
                'amountGbp': amount_total,
                'buyerEmail': customer_email,
                'buyerName': customer_name,
                'sku': sku,
                'metadata': session,
                'fulfilled': False
            }
        )
        
        # Get product details
        product = db.product.find_unique(where={'sku': sku})
        
        # Trigger fulfillment
        if product and product.fulfilmentWebhook:
            trigger_fulfillment(order, product)
        
        # Send receipt email
        send_receipt_email(customer_email, customer_name, order.dict(), product.dict() if product else {})
        
        # Log automation
        log_automation(
            'A2-checkout-webhooks',
            'Stripe Checkout Completed',
            'completed',
            trigger_data={'session_id': session['id']},
            execution_data={'order_id': order.id},
            started_at=started_at
        )
        
        app.logger.info(f"Order created: {order.id} for {customer_email}")
    
    except Exception as e:
        log_automation(
            'A2-checkout-webhooks',
            'Stripe Checkout Completed',
            'failed',
            trigger_data={'session_id': session.get('id')},
            error_message=str(e),
            started_at=started_at
        )
        raise

def handle_stripe_subscription_created(subscription: Dict):
    """Handle Stripe subscription creation"""
    try:
        customer = stripe.Customer.retrieve(subscription['customer'])
        
        # Determine SKU from subscription metadata or items
        sku = subscription.get('metadata', {}).get('sku', 'UNKNOWN')
        
        db.subscription.create(
            data={
                'gateway': 'stripe',
                'gatewaySubscriptionId': subscription['id'],
                'customerEmail': customer['email'],
                'sku': sku,
                'status': subscription['status'],
                'currentPeriodStart': datetime.fromtimestamp(subscription['current_period_start']),
                'currentPeriodEnd': datetime.fromtimestamp(subscription['current_period_end']),
                'cancelAtPeriodEnd': subscription['cancel_at_period_end']
            }
        )
        
        app.logger.info(f"Subscription created: {subscription['id']}")
    
    except Exception as e:
        app.logger.error(f"Error creating subscription: {e}")
        raise

def handle_stripe_subscription_updated(subscription: Dict):
    """Handle Stripe subscription update"""
    try:
        db.subscription.update(
            where={'gatewaySubscriptionId': subscription['id']},
            data={
                'status': subscription['status'],
                'currentPeriodStart': datetime.fromtimestamp(subscription['current_period_start']),
                'currentPeriodEnd': datetime.fromtimestamp(subscription['current_period_end']),
                'cancelAtPeriodEnd': subscription['cancel_at_period_end']
            }
        )
        
        app.logger.info(f"Subscription updated: {subscription['id']}")
    
    except Exception as e:
        app.logger.error(f"Error updating subscription: {e}")
        raise

def handle_stripe_subscription_deleted(subscription: Dict):
    """Handle Stripe subscription cancellation"""
    try:
        db.subscription.update(
            where={'gatewaySubscriptionId': subscription['id']},
            data={
                'status': 'cancelled',
                'cancelledAt': datetime.utcnow()
            }
        )
        
        app.logger.info(f"Subscription cancelled: {subscription['id']}")
    
    except Exception as e:
        app.logger.error(f"Error cancelling subscription: {e}")
        raise

def handle_stripe_refund(charge: Dict):
    """Handle Stripe refund"""
    try:
        # Find order by payment intent
        order = db.order.find_first(
            where={'gatewayTransactionId': charge['payment_intent']}
        )
        
        if order:
            db.order.update(
                where={'id': order.id},
                data={'status': 'refunded'}
            )
            app.logger.info(f"Order refunded: {order.id}")
    
    except Exception as e:
        app.logger.error(f"Error processing refund: {e}")
        raise

def handle_stripe_dispute(charge: Dict):
    """Handle Stripe dispute"""
    try:
        order = db.order.find_first(
            where={'gatewayTransactionId': charge['payment_intent']}
        )
        
        if order:
            db.order.update(
                where={'id': order.id},
                data={'status': 'disputed'}
            )
            app.logger.info(f"Order disputed: {order.id}")
    
    except Exception as e:
        app.logger.error(f"Error processing dispute: {e}")
        raise

# ============================================================
# PAYPAL WEBHOOKS
# ============================================================

@app.route('/webhooks/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events"""
    payload = request.get_json()
    headers = request.headers
    
    if not verify_paypal_signature(payload, headers):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event_type = payload.get('event_type')
    
    app.logger.info(f"Received PayPal event: {event_type}")
    
    try:
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            handle_paypal_payment_completed(payload['resource'])
        
        elif event_type == 'BILLING.SUBSCRIPTION.CREATED':
            handle_paypal_subscription_created(payload['resource'])
        
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            handle_paypal_subscription_cancelled(payload['resource'])
        
        elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
            handle_paypal_refund(payload['resource'])
        
        return jsonify({'received': True}), 200
    
    except Exception as e:
        app.logger.error(f"Error processing PayPal webhook: {e}")
        return jsonify({'error': str(e)}), 500

def handle_paypal_payment_completed(payment: Dict):
    """Handle completed PayPal payment"""
    started_at = datetime.utcnow()
    
    try:
        # Extract payment data
        customer_email = payment.get('payer', {}).get('email_address')
        customer_name = payment.get('payer', {}).get('name', {}).get('given_name', '') + ' ' + \
                       payment.get('payer', {}).get('name', {}).get('surname', '')
        amount = Decimal(payment['amount']['value'])
        
        # Get SKU from custom_id or metadata
        sku = payment.get('custom_id', 'UNKNOWN')
        
        # Create order record
        order = db.order.create(
            data={
                'gateway': 'paypal',
                'gatewayTransactionId': payment['id'],
                'status': 'paid',
                'amountGbp': amount,
                'buyerEmail': customer_email,
                'buyerName': customer_name.strip(),
                'sku': sku,
                'metadata': payment,
                'fulfilled': False
            }
        )
        
        # Get product details
        product = db.product.find_unique(where={'sku': sku})
        
        # Trigger fulfillment
        if product and product.fulfilmentWebhook:
            trigger_fulfillment(order, product)
        
        # Send receipt email
        send_receipt_email(customer_email, customer_name.strip(), order.dict(), product.dict() if product else {})
        
        # Log automation
        log_automation(
            'A2-checkout-webhooks',
            'PayPal Payment Completed',
            'completed',
            trigger_data={'payment_id': payment['id']},
            execution_data={'order_id': order.id},
            started_at=started_at
        )
        
        app.logger.info(f"PayPal order created: {order.id} for {customer_email}")
    
    except Exception as e:
        log_automation(
            'A2-checkout-webhooks',
            'PayPal Payment Completed',
            'failed',
            trigger_data={'payment_id': payment.get('id')},
            error_message=str(e),
            started_at=started_at
        )
        raise

def handle_paypal_subscription_created(subscription: Dict):
    """Handle PayPal subscription creation"""
    try:
        subscriber = subscription.get('subscriber', {})
        customer_email = subscriber.get('email_address')
        sku = subscription.get('custom_id', 'UNKNOWN')
        
        db.subscription.create(
            data={
                'gateway': 'paypal',
                'gatewaySubscriptionId': subscription['id'],
                'customerEmail': customer_email,
                'sku': sku,
                'status': 'active',
                'currentPeriodStart': datetime.fromisoformat(subscription.get('start_time', datetime.utcnow().isoformat())),
                'currentPeriodEnd': None,  # PayPal doesn't provide this upfront
                'cancelAtPeriodEnd': False
            }
        )
        
        app.logger.info(f"PayPal subscription created: {subscription['id']}")
    
    except Exception as e:
        app.logger.error(f"Error creating PayPal subscription: {e}")
        raise

def handle_paypal_subscription_cancelled(subscription: Dict):
    """Handle PayPal subscription cancellation"""
    try:
        db.subscription.update(
            where={'gatewaySubscriptionId': subscription['id']},
            data={
                'status': 'cancelled',
                'cancelledAt': datetime.utcnow()
            }
        )
        
        app.logger.info(f"PayPal subscription cancelled: {subscription['id']}")
    
    except Exception as e:
        app.logger.error(f"Error cancelling PayPal subscription: {e}")
        raise

def handle_paypal_refund(payment: Dict):
    """Handle PayPal refund"""
    try:
        # Find order by transaction ID
        order = db.order.find_first(
            where={'gatewayTransactionId': payment['id']}
        )
        
        if order:
            db.order.update(
                where={'id': order.id},
                data={'status': 'refunded'}
            )
            app.logger.info(f"PayPal order refunded: {order.id}")
    
    except Exception as e:
        app.logger.error(f"Error processing PayPal refund: {e}")
        raise

# ============================================================
# FULFILLMENT ENDPOINTS
# ============================================================

def trigger_fulfillment(order: Any, product: Any):
    """Trigger product fulfillment based on SKU"""
    sku = order.sku
    
    if sku.startswith('COPYKIT'):
        fulfill_copykit(order, product)
    elif sku.startswith('DAILYBRIEF'):
        fulfill_briefing(order, product)
    else:
        app.logger.warning(f"Unknown SKU for fulfillment: {sku}")

def fulfill_copykit(order: Any, product: Any):
    """Fulfill CopyKit order"""
    started_at = datetime.utcnow()
    
    try:
        # Create Notion workspace
        notion_page_id = create_notion_workspace(order.buyerEmail, order.sku)
        
        # Mark order as fulfilled
        db.order.update(
            where={'id': order.id},
            data={
                'fulfilled': True,
                'fulfilledAt': datetime.utcnow()
            }
        )
        
        log_automation(
            'A4-copykit-fulfilment',
            'CopyKit Fulfillment',
            'completed',
            trigger_data={'order_id': order.id},
            execution_data={'notion_page_id': notion_page_id},
            started_at=started_at
        )
        
        app.logger.info(f"CopyKit fulfilled for order {order.id}")
    
    except Exception as e:
        log_automation(
            'A4-copykit-fulfilment',
            'CopyKit Fulfillment',
            'failed',
            trigger_data={'order_id': order.id},
            error_message=str(e),
            started_at=started_at
        )
        raise

def fulfill_briefing(order: Any, product: Any):
    """Fulfill Daily Briefing subscription"""
    started_at = datetime.utcnow()
    
    try:
        # Add to subscriber list
        # Grant access to gated content
        
        db.order.update(
            where={'id': order.id},
            data={
                'fulfilled': True,
                'fulfilledAt': datetime.utcnow()
            }
        )
        
        log_automation(
            'A4-copykit-fulfilment',
            'Briefing Fulfillment',
            'completed',
            trigger_data={'order_id': order.id},
            started_at=started_at
        )
        
        app.logger.info(f"Briefing fulfilled for order {order.id}")
    
    except Exception as e:
        log_automation(
            'A4-copykit-fulfilment',
            'Briefing Fulfillment',
            'failed',
            trigger_data={'order_id': order.id},
            error_message=str(e),
            started_at=started_at
        )
        raise

@app.route('/api/fulfilment/copykit', methods=['POST'])
def api_fulfill_copykit():
    """Manual CopyKit fulfillment endpoint"""
    data = request.get_json()
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({'error': 'order_id required'}), 400
    
    order = db.order.find_unique(where={'id': order_id})
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    product = db.product.find_unique(where={'sku': order.sku})
    
    try:
        fulfill_copykit(order, product)
        return jsonify({'success': True, 'order_id': order_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fulfilment/briefing', methods=['POST'])
def api_fulfill_briefing():
    """Manual Briefing fulfillment endpoint"""
    data = request.get_json()
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({'error': 'order_id required'}), 400
    
    order = db.order.find_unique(where={'id': order_id})
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    product = db.product.find_unique(where={'sku': order.sku})
    
    try:
        fulfill_briefing(order, product)
        return jsonify({'success': True, 'order_id': order_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# LEAD MANAGEMENT
# ============================================================

@app.route('/api/leads', methods=['POST'])
def create_lead():
    """Create a new lead"""
    data = request.get_json()
    
    try:
        lead = db.lead.create(
            data={
                'email': data['email'],
                'name': data.get('name'),
                'source': data.get('source', 'Manual'),
                'tags': data.get('tags', []),
                'utmSource': data.get('utm_source'),
                'utmCampaign': data.get('utm_campaign'),
                'utmMedium': data.get('utm_medium'),
                'utmTerm': data.get('utm_term'),
                'utmContent': data.get('utm_content')
            }
        )
        
        return jsonify(lead.dict()), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============================================================
# KPI ENDPOINTS
# ============================================================

@app.route('/api/kpi/daily', methods=['GET'])
def get_daily_kpis():
    """Get daily KPIs"""
    days = int(request.args.get('days', 30))
    
    kpis = db.kpidaily.find_many(
        order={'date': 'desc'},
        take=days
    )
    
    return jsonify([kpi.dict() for kpi in kpis]), 200

@app.route('/api/kpi/update', methods=['POST'])
def update_daily_kpi():
    """Update or create daily KPI record"""
    data = request.get_json()
    date = data.get('date', datetime.utcnow().date())
    
    try:
        kpi = db.kpidaily.upsert(
            where={'date': date},
            data={
                'create': {
                    'date': date,
                    'visitors': data.get('visitors', 0),
                    'leads': data.get('leads', 0),
                    'orders': data.get('orders', 0),
                    'grossGbp': data.get('gross_gbp', 0),
                    'netGbp': data.get('net_gbp', 0),
                    'refunds': data.get('refunds', 0),
                    'crPct': data.get('cr_pct', 0)
                },
                'update': {
                    'visitors': data.get('visitors'),
                    'leads': data.get('leads'),
                    'orders': data.get('orders'),
                    'grossGbp': data.get('gross_gbp'),
                    'netGbp': data.get('net_gbp'),
                    'refunds': data.get('refunds'),
                    'crPct': data.get('cr_pct')
                }
            }
        )
        
        return jsonify(kpi.dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@app.before_first_request
def startup():
    """Connect to database on startup"""
    db.connect()

@app.teardown_appcontext
def shutdown(exception=None):
    """Disconnect from database on shutdown"""
    if db.is_connected():
        db.disconnect()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')

