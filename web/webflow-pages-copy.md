# Webflow Pages Copy & Structure

## Homepage (index.html)

### Hero Section
**Headline:** Transform Your Marketing with AI-Powered Copy That Converts

**Subheadline:** Get weekly ad creatives, landing page copy, and email sequences crafted by advanced AI — designed to boost your conversion rates and save you hours of work.

**CTA Primary:** Start Your Free Trial  
**CTA Secondary:** See How It Works

**Hero Image/Video:** Animated showcase of AI generating copy in real-time

---

### Problem Section
**Headline:** Stop Wasting Time on Copy That Doesn't Convert

**Pain Points:**
- Spending hours writing ad copy that falls flat
- Missing deadlines because you're stuck on headlines
- Paying expensive copywriters for inconsistent results
- Watching competitors outperform you with better messaging

---

### Solution Section
**Headline:** AI CopyKit: Your 24/7 Conversion Copywriter

**Features Grid:**

**1. Weekly Ad Creatives**
Generate 10+ high-converting ad variations every week across all major platforms (Facebook, Google, LinkedIn, TikTok).

**2. Landing Page Copy**
Complete landing page copy with headlines, subheadlines, CTAs, and body copy optimized for conversion.

**3. Email Sequences**
Pre-written email flows for welcome series, nurture campaigns, and promotional blasts.

**4. A/B Testing Variants**
Automatic generation of multiple copy variants for split testing.

---

### Pricing Section
**Headline:** Choose Your Growth Plan

**Plan 1: CopyKit Monthly**
- **Price:** £49/month
- **Features:**
  - Weekly ad creative packs (10+ variants)
  - Monthly landing page copy
  - Email swipe files
  - A/B testing variants
  - Priority support
- **CTA:** Start Monthly Plan

**Plan 2: CopyKit Full Funnel Pack**
- **Price:** £199 one-time
- **Features:**
  - Complete funnel copy (awareness → conversion)
  - 50+ ad creatives
  - 5 landing pages
  - 3 email sequences
  - Competitor analysis
  - Lifetime access
- **CTA:** Get Full Funnel Pack

**Plan 3: Daily Briefing**
- **Price:** £15/month or £99/year
- **Features:**
  - Daily market insights
  - Trend analysis
  - Audio briefing (ElevenLabs TTS)
  - Social media clips
  - Trading & creator niches
- **CTA:** Subscribe to Briefing

---

### Testimonials Section
**Headline:** Trusted by 500+ Marketers & Founders

**Testimonial 1:**
"CopyKit cut my ad creative time from 4 hours to 15 minutes. The AI understands my brand voice better than most copywriters I've hired."
— Sarah Chen, Growth Marketing Lead

**Testimonial 2:**
"The Full Funnel Pack paid for itself in the first week. Our conversion rate jumped 34% after implementing the landing page copy."
— Marcus Rodriguez, SaaS Founder

**Testimonial 3:**
"The Daily Briefing keeps me ahead of market trends. It's like having a research team working overnight."
— James Thompson, Day Trader

---

### FAQ Section
**Headline:** Frequently Asked Questions

**Q: How is this different from ChatGPT?**
A: CopyKit is purpose-built for conversion copywriting with specialized prompts, competitor analysis, and proven frameworks. It's trained on high-converting copy, not general text.

**Q: Can I cancel anytime?**
A: Yes! Monthly subscriptions can be cancelled anytime. You'll retain access until the end of your billing period.

**Q: What if I'm not satisfied?**
A: We offer a 7-day money-back guarantee on all purchases. No questions asked.

**Q: Do you support multiple brands?**
A: Yes! You can create separate brand profiles with different voice, tone, and positioning.

**Q: How quickly do I get my copy?**
A: Monthly subscribers receive weekly deliveries every Monday. Full Funnel Pack customers get everything within 48 hours.

---

### Final CTA Section
**Headline:** Ready to Transform Your Marketing?

**Subheadline:** Join 500+ marketers who've already boosted their conversions with AI-powered copy.

**CTA:** Start Your Free Trial Today

**Trust Badges:**
- 7-Day Money-Back Guarantee
- Secure Payment via Stripe & PayPal
- Cancel Anytime
- GDPR Compliant

---

## Pricing Page (pricing.html)

### Hero
**Headline:** Simple, Transparent Pricing

**Subheadline:** Choose the plan that fits your growth stage. All plans include our conversion-focused AI engine.

### Pricing Cards
(Same as homepage pricing section, but with expanded feature lists)

### Payment Options
**Stripe Checkout Embed:**
```html
<stripe-pricing-table 
  pricing-table-id="prctbl_xxxxx"
  publishable-key="pk_live_xxxxx">
</stripe-pricing-table>
```

**PayPal Alternative:**
```html
<div id="paypal-button-container"></div>
<script>
  paypal.Buttons({
    createOrder: function(data, actions) {
      return actions.order.create({
        purchase_units: [{
          amount: { value: '49.00' }
        }]
      });
    },
    onApprove: function(data, actions) {
      return actions.order.capture().then(function(details) {
        window.location.href = '/thank-you';
      });
    }
  }).render('#paypal-button-container');
</script>
```

---

## Thank You Page (thank-you.html)

### Hero
**Headline:** Welcome to CopyKit! 🎉

**Subheadline:** Your account is being set up. Check your email for access instructions.

### What Happens Next
**Step 1:** Check your email (from hello@copykit.io)  
**Step 2:** Access your private Notion workspace  
**Step 3:** Download your first copy pack  
**Step 4:** Start implementing and watch conversions grow

### CTA
**Button:** Access Your Dashboard

---

## Members Area (members.html)

### Dashboard
**Headline:** Welcome back, [Name]!

**Quick Stats:**
- Copy Packs Delivered: 12
- Downloads This Month: 8
- Next Delivery: Monday, Oct 21

### Resources Grid
- **Latest Copy Pack** (Download)
- **Brand Voice Settings** (Edit)
- **Request Custom Brief** (Form)
- **Support** (Chat)

### Gated Content (Daily Briefing)
- Today's briefing article
- Audio player (ElevenLabs TTS)
- Video clip (InVideo)
- Archive access

---

## Stripe Checkout Configuration

### Product Setup (Stripe Dashboard)

**Product 1: CopyKit Monthly**
- Name: CopyKit Monthly Subscription
- Price: £49.00 GBP / month
- Billing: Recurring monthly
- Metadata: `sku=COPYKIT-MONTHLY`

**Product 2: CopyKit Bundle**
- Name: CopyKit Full Funnel Pack
- Price: £199.00 GBP
- Billing: One-time
- Metadata: `sku=COPYKIT-BUNDLE`

**Product 3: Daily Briefing**
- Name: Daily Briefing Monthly
- Price: £15.00 GBP / month
- Billing: Recurring monthly
- Metadata: `sku=DAILYBRIEF-MONTHLY`

### Checkout Session Code

```javascript
// Create Stripe Checkout Session
const stripe = Stripe('pk_live_xxxxx');

document.getElementById('checkout-button').addEventListener('click', async () => {
  const { error } = await stripe.redirectToCheckout({
    lineItems: [{
      price: 'price_xxxxx', // Price ID from Stripe
      quantity: 1,
    }],
    mode: 'subscription', // or 'payment' for one-time
    successUrl: 'https://yourdomain.com/thank-you',
    cancelUrl: 'https://yourdomain.com/pricing',
    customerEmail: 'user@example.com', // Pre-fill if available
    metadata: {
      sku: 'COPYKIT-MONTHLY'
    }
  });
  
  if (error) {
    console.error('Error:', error);
  }
});
```

---

## PayPal Checkout Configuration

### PayPal Button Integration

```html
<div id="paypal-button-container"></div>

<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&vault=true&intent=subscription"></script>

<script>
  // For subscriptions
  paypal.Buttons({
    style: {
      shape: 'rect',
      color: 'gold',
      layout: 'vertical',
      label: 'subscribe'
    },
    createSubscription: function(data, actions) {
      return actions.subscription.create({
        plan_id: 'P-xxxxx', // Plan ID from PayPal
        custom_id: 'COPYKIT-MONTHLY'
      });
    },
    onApprove: function(data, actions) {
      // Redirect to thank you page
      window.location.href = '/thank-you?subscription_id=' + data.subscriptionID;
    }
  }).render('#paypal-button-container');
  
  // For one-time payments
  paypal.Buttons({
    createOrder: function(data, actions) {
      return actions.order.create({
        purchase_units: [{
          amount: {
            value: '199.00',
            currency_code: 'GBP'
          },
          custom_id: 'COPYKIT-BUNDLE'
        }]
      });
    },
    onApprove: function(data, actions) {
      return actions.order.capture().then(function(details) {
        window.location.href = '/thank-you?order_id=' + data.orderID;
      });
    }
  }).render('#paypal-button-container');
</script>
```

---

## Webflow Embed Codes

### Stripe Pricing Table Embed
```html
<script async src="https://js.stripe.com/v3/pricing-table.js"></script>
<stripe-pricing-table 
  pricing-table-id="prctbl_xxxxx"
  publishable-key="pk_live_xxxxx">
</stripe-pricing-table>
```

### PayPal Smart Buttons
```html
<div id="paypal-container-monthly"></div>
<div id="paypal-container-bundle"></div>

<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&vault=true&intent=subscription"></script>
```

### Analytics Tracking
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>

<!-- Facebook Pixel -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

---

## DNS & Cloudflare Setup

### DNS Records
```
A     @       192.0.2.1       (Proxied)
CNAME www     yourdomain.com  (Proxied)
CNAME api     yourdomain.com  (Proxied)
```

### Cloudflare Page Rules
1. **Cache Everything:** `yourdomain.com/*` → Cache Level: Cache Everything
2. **Force HTTPS:** `http://yourdomain.com/*` → Always Use HTTPS
3. **API Bypass:** `yourdomain.com/api/*` → Cache Level: Bypass

---

## Supabase Auth Integration (Members Area)

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://xxxxx.supabase.co',
  'your-anon-key'
)

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Check session
const { data: { user } } = await supabase.auth.getUser()

// Protected content
if (!user) {
  window.location.href = '/login'
}
```

