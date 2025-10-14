"""
Sentry Configuration for Omni-Revenue-Agent
Error tracking, performance monitoring, and alerting
"""

import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
RELEASE = os.getenv('RELEASE', '1.0.0')

def init_sentry(app=None):
    """
    Initialize Sentry SDK with Flask integration
    
    Args:
        app: Flask application instance (optional)
    """
    if not SENTRY_DSN:
        print("⚠️  Sentry DSN not configured, skipping initialization")
        return
    
    # Configure integrations
    integrations = [
        FlaskIntegration(
            transaction_style='url'
        ),
        LoggingIntegration(
            level=None,  # Capture all logs
            event_level=None  # Send errors as events
        )
    ]
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=integrations,
        environment=ENVIRONMENT,
        release=RELEASE,
        
        # Performance monitoring
        traces_sample_rate=1.0 if ENVIRONMENT == 'development' else 0.1,
        
        # Error sampling
        sample_rate=1.0,
        
        # Send default PII (Personally Identifiable Information)
        send_default_pii=False,
        
        # Attach stack traces to messages
        attach_stacktrace=True,
        
        # Maximum breadcrumbs
        max_breadcrumbs=50,
        
        # Before send hook to filter events
        before_send=before_send_hook,
        
        # Before breadcrumb hook
        before_breadcrumb=before_breadcrumb_hook
    )
    
    print(f"✓ Sentry initialized for environment: {ENVIRONMENT}")

def before_send_hook(event, hint):
    """
    Filter or modify events before sending to Sentry
    
    Args:
        event: Sentry event dictionary
        hint: Additional context
    
    Returns:
        Modified event or None to drop the event
    """
    # Don't send events in development (optional)
    if ENVIRONMENT == 'development':
        print(f"[Sentry] Would send event: {event.get('message', 'No message')}")
        # Uncomment to actually send in development:
        # return event
        return None
    
    # Filter out specific errors
    if 'exception' in event:
        exc_type = event['exception']['values'][0]['type']
        
        # Don't send 404 errors
        if exc_type == 'NotFound':
            return None
        
        # Don't send validation errors
        if exc_type == 'ValidationError':
            return None
    
    return event

def before_breadcrumb_hook(crumb, hint):
    """
    Filter or modify breadcrumbs before adding to event
    
    Args:
        crumb: Breadcrumb dictionary
        hint: Additional context
    
    Returns:
        Modified breadcrumb or None to drop it
    """
    # Filter out noisy breadcrumbs
    if crumb.get('category') == 'httplib':
        # Only keep failed HTTP requests
        if crumb.get('data', {}).get('status_code', 0) < 400:
            return None
    
    return crumb

# ============================================================
# CUSTOM BREADCRUMBS
# ============================================================

def add_order_breadcrumb(order_id: str, gateway: str, amount: float):
    """Add breadcrumb for order creation"""
    sentry_sdk.add_breadcrumb(
        category='order',
        message=f'Order created: {order_id}',
        level='info',
        data={
            'order_id': order_id,
            'gateway': gateway,
            'amount_gbp': amount
        }
    )

def add_email_breadcrumb(recipient: str, subject: str, success: bool):
    """Add breadcrumb for email sending"""
    sentry_sdk.add_breadcrumb(
        category='email',
        message=f'Email sent to {recipient}',
        level='info' if success else 'warning',
        data={
            'recipient': recipient,
            'subject': subject,
            'success': success
        }
    )

def add_asset_breadcrumb(asset_type: str, asset_id: str):
    """Add breadcrumb for asset rendering"""
    sentry_sdk.add_breadcrumb(
        category='asset',
        message=f'Asset rendered: {asset_type}',
        level='info',
        data={
            'asset_type': asset_type,
            'asset_id': asset_id
        }
    )

# ============================================================
# ALERT RULES CONFIGURATION
# ============================================================

ALERT_RULES = [
    {
        'name': 'Checkout Error Spike',
        'description': 'Alert when checkout errors exceed threshold',
        'conditions': {
            'error_type': 'CheckoutError',
            'threshold_per_min': 5,
            'time_window': '1m'
        },
        'actions': [
            'email:ops@yourdomain.com',
            'slack:#alerts'
        ]
    },
    {
        'name': 'Webhook Failure',
        'description': 'Alert on any webhook processing failure',
        'conditions': {
            'error_type': 'WebhookError',
            'threshold_per_min': 1,
            'time_window': '1m'
        },
        'actions': [
            'email:ops@yourdomain.com',
            'pagerduty:high'
        ]
    },
    {
        'name': 'Database Connection Error',
        'description': 'Alert on database connection failures',
        'conditions': {
            'error_type': 'DatabaseError',
            'threshold_per_min': 3,
            'time_window': '5m'
        },
        'actions': [
            'email:ops@yourdomain.com',
            'slack:#critical'
        ]
    },
    {
        'name': 'Payment Gateway Timeout',
        'description': 'Alert when payment gateway requests timeout',
        'conditions': {
            'error_type': 'TimeoutError',
            'tags': {'service': 'payment'},
            'threshold_per_min': 5,
            'time_window': '5m'
        },
        'actions': [
            'email:ops@yourdomain.com'
        ]
    },
    {
        'name': 'High Error Rate',
        'description': 'Alert when overall error rate exceeds 5%',
        'conditions': {
            'error_rate_pct': 5,
            'time_window': '10m'
        },
        'actions': [
            'email:ops@yourdomain.com',
            'slack:#alerts'
        ]
    }
]

# ============================================================
# PERFORMANCE MONITORING
# ============================================================

def track_automation_performance(automation_id: str, duration_ms: int, status: str):
    """
    Track automation performance metrics
    
    Args:
        automation_id: Automation identifier
        duration_ms: Execution duration in milliseconds
        status: Execution status (completed, failed, partial)
    """
    with sentry_sdk.start_transaction(op='automation', name=automation_id) as transaction:
        transaction.set_tag('automation_id', automation_id)
        transaction.set_tag('status', status)
        transaction.set_measurement('duration_ms', duration_ms, 'millisecond')
        
        # Add context
        sentry_sdk.set_context('automation', {
            'id': automation_id,
            'duration_ms': duration_ms,
            'status': status
        })

def track_webhook_performance(webhook_type: str, duration_ms: int, success: bool):
    """
    Track webhook processing performance
    
    Args:
        webhook_type: Type of webhook (stripe, paypal)
        duration_ms: Processing duration in milliseconds
        success: Whether processing succeeded
    """
    with sentry_sdk.start_transaction(op='webhook', name=webhook_type) as transaction:
        transaction.set_tag('webhook_type', webhook_type)
        transaction.set_tag('success', success)
        transaction.set_measurement('duration_ms', duration_ms, 'millisecond')

# ============================================================
# ERROR CAPTURE HELPERS
# ============================================================

def capture_checkout_error(error: Exception, gateway: str, amount: float, customer_email: str):
    """Capture checkout error with context"""
    sentry_sdk.set_context('checkout', {
        'gateway': gateway,
        'amount_gbp': amount,
        'customer_email': customer_email
    })
    sentry_sdk.capture_exception(error)

def capture_webhook_error(error: Exception, webhook_type: str, payload: dict):
    """Capture webhook error with context"""
    sentry_sdk.set_context('webhook', {
        'type': webhook_type,
        'payload': payload
    })
    sentry_sdk.capture_exception(error)

def capture_automation_error(error: Exception, automation_id: str, trigger_data: dict):
    """Capture automation error with context"""
    sentry_sdk.set_context('automation', {
        'id': automation_id,
        'trigger_data': trigger_data
    })
    sentry_sdk.capture_exception(error)

# ============================================================
# USAGE EXAMPLES
# ============================================================

"""
# In your Flask app:
from sentry_config import init_sentry

app = Flask(__name__)
init_sentry(app)

# In webhook handlers:
from sentry_config import add_order_breadcrumb, capture_webhook_error

try:
    # Process webhook
    add_order_breadcrumb(order_id, gateway, amount)
except Exception as e:
    capture_webhook_error(e, 'stripe', payload)

# In automation scripts:
from sentry_config import track_automation_performance

start_time = time.time()
try:
    # Run automation
    pass
finally:
    duration_ms = int((time.time() - start_time) * 1000)
    track_automation_performance('A3-briefing-daily', duration_ms, 'completed')
"""

# ============================================================
# SENTRY ALERT RULES (Configure in Sentry Dashboard)
# ============================================================

SENTRY_DASHBOARD_CONFIG = """
To configure alert rules in Sentry:

1. Go to Sentry Dashboard → Alerts → Create Alert Rule

2. For "Checkout Error Spike":
   - Condition: When the count of events is more than 5 in 1 minute
   - Filter: error.type equals CheckoutError
   - Action: Send email to ops@yourdomain.com

3. For "Webhook Failure":
   - Condition: When the count of events is more than 1 in 1 minute
   - Filter: error.type equals WebhookError
   - Action: Send email + Slack notification

4. For "Database Connection Error":
   - Condition: When the count of events is more than 3 in 5 minutes
   - Filter: error.type equals DatabaseError
   - Action: Send email + PagerDuty alert

5. For "Payment Gateway Timeout":
   - Condition: When the count of events is more than 5 in 5 minutes
   - Filter: error.type equals TimeoutError AND tag.service equals payment
   - Action: Send email notification

6. For "High Error Rate":
   - Condition: When the error rate is above 5% in 10 minutes
   - Action: Send email + Slack notification to #critical
"""

if __name__ == '__main__':
    # Test Sentry configuration
    init_sentry()
    
    # Test error capture
    try:
        raise Exception("Test error for Sentry")
    except Exception as e:
        sentry_sdk.capture_exception(e)
    
    print("✓ Sentry test error sent")

