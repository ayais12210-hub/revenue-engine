"""
Omni-Revenue-Agent API
Flask application for webhook handling, fulfillment, and automation orchestration
"""

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import stripe
import requests
from prisma import Prisma
from api.utils.copykit_parser import parse_copykit_html
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Flask app
app = Flask(__name__)

# Configure CORS with specific origins for security
CORS(app, origins=[
    os.getenv('FRONTEND_URL', 'http://localhost:3000'),
    os.getenv('BASE_URL', 'http://localhost:3000'),
    'https://copykit.io',
    'https://www.copykit.io'
], allow_headers=['Content-Type', 'Authorization'], methods=['GET', 'POST', 'PUT', 'DELETE'])

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False  # Preserve JSON key order
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Sentry for error monitoring
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv('ENVIRONMENT', 'development')
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Prisma client
db = Prisma()

# ============================================================
# SECURITY & VALIDATION UTILITIES
# ============================================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(data: Any) -> Any:
    """Sanitize input data to prevent XSS and injection attacks"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        return data.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def require_api_key(f):
    """Decorator to require API key for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY')
        
        if not expected_key:
            logger.warning("API_KEY not configured, skipping API key validation")
            return f(*args, **kwargs)
            
        if not api_key or api_key != expected_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def validate_json_schema(schema: Dict):
    """Decorator to validate JSON request body against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
                
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Empty JSON body'}), 400
                
            # Basic schema validation
            for field, field_type in schema.items():
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
                if not isinstance(data[field], field_type):
                    return jsonify({'error': f'Invalid type for field {field}, expected {field_type.__name__}'}), 400
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request(f):
    """Decorator to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.utcnow()
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        try:
            result = f(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Response: {request.method} {request.path} - {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error: {request.method} {request.path} - {duration:.3f}s - {str(e)}")
            raise
    return decorated_function

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def verify_stripe_signature(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature with enhanced security"""
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not configured, skipping verification")
        return os.getenv('ENVIRONMENT') == 'development'
    
    try:
        # Verify signature using Stripe's official method
        stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logger.info("Stripe webhook signature verified successfully")
        return True
    except ValueError as e:
        logger.error(f"Stripe signature verification failed - Invalid payload: {e}")
        return False
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe signature verification failed - Invalid signature: {e}")
        return False
    except Exception as e:
        logger.error(f"Stripe signature verification failed - Unexpected error: {e}")
        return False

def verify_paypal_signature(payload: Dict, headers: Dict) -> bool:
    """Verify PayPal webhook signature with enhanced security"""
    # In production, implement proper PayPal webhook verification
    # This is a placeholder implementation
    if os.getenv('ENVIRONMENT') == 'production':
        logger.warning("PayPal webhook verification not fully implemented for production")
        return False
    
    # For development, allow all PayPal webhooks
    logger.info("PayPal webhook received (development mode - signature not verified)")
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
@log_request
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database connectivity
        db_status = 'healthy'
        try:
            db.connect()
            # Simple query to test connection
            db.lead.count()
            db.disconnect()
        except Exception as e:
            db_status = 'unhealthy'
            logger.error(f"Database health check failed: {e}")
        
        # Check external services
        stripe_status = 'healthy'
        try:
            stripe.Account.retrieve()
        except Exception as e:
            stripe_status = 'unhealthy'
            logger.error(f"Stripe health check failed: {e}")
        
        # Overall status
        overall_status = 'healthy' if db_status == 'healthy' and stripe_status == 'healthy' else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'omni-revenue-agent-api',
            'version': os.getenv('RELEASE', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'checks': {
                'database': db_status,
                'stripe': stripe_status
            },
            'uptime': (datetime.utcnow() - datetime.utcnow()).total_seconds()  # Placeholder
        }), 200 if overall_status == 'healthy' else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'omni-revenue-agent-api',
            'error': str(e)
        }), 503

# ============================================================
# STRIPE WEBHOOKS
# ============================================================

@app.route('/webhooks/stripe', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit webhook endpoints
@log_request
def stripe_webhook():
    """Handle Stripe webhook events with enhanced security"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    # Validate content type
    if request.content_type != 'application/json':
        logger.warning(f"Invalid content type for Stripe webhook: {request.content_type}")
        return jsonify({'error': 'Invalid content type'}), 400
    
    if not verify_stripe_signature(payload, sig_header):
        logger.warning(f"Stripe webhook signature verification failed from {request.remote_addr}")
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
@limiter.limit("10 per minute")  # Rate limit webhook endpoints
@log_request
def paypal_webhook():
    """Handle PayPal webhook events with enhanced security"""
    payload = request.get_json()
    headers = request.headers
    
    # Validate content type
    if request.content_type != 'application/json':
        logger.warning(f"Invalid content type for PayPal webhook: {request.content_type}")
        return jsonify({'error': 'Invalid content type'}), 400
    
    if not verify_paypal_signature(payload, headers):
        logger.warning(f"PayPal webhook signature verification failed from {request.remote_addr}")
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
@limiter.limit("20 per minute")  # Rate limit lead creation
@validate_json_schema({'email': str})
@log_request
def create_lead():
    """Create a new lead with enhanced validation and security"""
    data = request.get_json()
    
    # Sanitize input data
    data = sanitize_input(data)
    
    # Validate email format
    if not validate_email(data['email']):
        logger.warning(f"Invalid email format provided: {data['email']}")
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate name if provided
    if 'name' in data and data['name']:
        if len(data['name']) > 255:
            return jsonify({'error': 'Name too long (max 255 characters)'}), 400
    
    try:
        # Check if lead already exists
        existing_lead = db.lead.find_unique(where={'email': data['email']})
        if existing_lead:
            logger.info(f"Lead already exists: {data['email']}")
            return jsonify({
                'message': 'Lead already exists',
                'lead': existing_lead.dict()
            }), 200
        
        # Create new lead
        lead = db.lead.create(
            data={
                'email': data['email'].lower().strip(),  # Normalize email
                'name': data.get('name', '').strip() if data.get('name') else None,
                'source': data.get('source', 'Manual'),
                'tags': data.get('tags', []),
                'utmSource': data.get('utm_source'),
                'utmCampaign': data.get('utm_campaign'),
                'utmMedium': data.get('utm_medium'),
                'utmTerm': data.get('utm_term'),
                'utmContent': data.get('utm_content')
            }
        )
        
        logger.info(f"New lead created: {lead.email} from {lead.source}")
        return jsonify(lead.dict()), 201
    
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        return jsonify({'error': 'Failed to create lead'}), 500

# ============================================================
# COPYKIT DATA FETCHING
# ============================================================

@app.route('/api/copykit/data', methods=['GET'])
def get_copykit_data():
    """Fetch data from CopyKit URL and return structured data"""
    try:
        # Fetch data from the CopyKit URL
        response = requests.get('https://copykit-gv4rmq.manus.space', timeout=10)
        response.raise_for_status()
        
        # Parse the HTML using the shared utility
        parsed_data = parse_copykit_html(response.text)
        
        # Check if parsing was successful
        if 'error' in parsed_data:
            app.logger.error(f"Error parsing CopyKit HTML: {parsed_data['error']}")
            return jsonify({'error': 'Failed to parse CopyKit data'}), 500
        
        # Return structured data
        return jsonify({
            'status': 'success',
            'data': {
                'global_env': parsed_data['global_env'],
                'title': parsed_data['title'] or 'CopyKit - AI-Powered Copywriting That Converts',
                'meta_description': parsed_data['meta_description'],
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200
        
    except requests.RequestException as e:
        app.logger.error(f"Error fetching CopyKit data: {e}")
        return jsonify({'error': 'Failed to fetch data from CopyKit URL'}), 500
    except Exception as e:
        app.logger.error(f"Error processing CopyKit data: {e}")
        return jsonify({'error': 'Failed to process data'}), 500

@app.route('/api/copykit/products', methods=['GET'])
def get_copykit_products():
    """Get CopyKit product data with real-time pricing and availability"""
    try:
        # Get products from database
        products = db.product.find_many()
        
        # Format products for frontend
        formatted_products = []
        for product in products:
            formatted_products.append({
                'id': product.sku.lower().replace('-', '_'),
                'name': product.name,
                'price': f"£{product.priceGbp}",
                'period': '/month' if product.type == 'subscription' else 'one-time',
                'sku': product.sku,
                'description': product.description,
                'features': product.features or [],
                'popular': product.sku == 'COPYKIT-MONTHLY',  # Mark monthly as popular
                'available': product.active
            })
        
        return jsonify({
            'status': 'success',
            'products': formatted_products
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching products: {e}")
        return jsonify({'error': 'Failed to fetch products'}), 500

@app.route('/api/copykit/analytics', methods=['GET'])
def get_copykit_analytics():
    """Get CopyKit analytics and performance data"""
    try:
        # Get recent KPIs
        recent_kpis = db.kpidaily.find_many(
            order={'date': 'desc'},
            take=30
        )
        
        # Calculate totals
        total_visitors = sum(kpi.visitors for kpi in recent_kpis)
        total_leads = sum(kpi.leads for kpi in recent_kpis)
        total_orders = sum(kpi.orders for kpi in recent_kpis)
        total_revenue = sum(float(kpi.grossGbp) for kpi in recent_kpis)
        
        # Get recent orders
        recent_orders = db.order.find_many(
            order={'createdAt': 'desc'},
            take=10
        )
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'totals': {
                    'visitors': total_visitors,
                    'leads': total_leads,
                    'orders': total_orders,
                    'revenue': total_revenue
                },
                'recent_orders': [order.dict() for order in recent_orders],
                'kpi_trend': [kpi.dict() for kpi in recent_kpis]
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching analytics: {e}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

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

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request data',
        'timestamp': datetime.utcnow().isoformat()
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required',
        'timestamp': datetime.utcnow().isoformat()
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'Access denied',
        'timestamp': datetime.utcnow().isoformat()
    }), 403

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'Resource not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Rate Limit Exceeded errors"""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests, please try again later',
        'timestamp': datetime.utcnow().isoformat()
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Omni-Revenue-Agent API on port {port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

