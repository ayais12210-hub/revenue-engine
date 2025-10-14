import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Check, Sparkles, Zap, TrendingUp, Mail, FileText, Target, ArrowRight, Star, Loader2 } from 'lucide-react'
import { useProducts, useAnalytics } from './hooks/useCopyKitData.js'
import './App.css'

function App() {
  const [selectedPlan, setSelectedPlan] = useState(null)
  const { products, loading: productsLoading } = useProducts()
  const { analytics } = useAnalytics()

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Weekly Ad Creatives",
      description: "Generate 10+ high-converting ad variations every week across all major platforms."
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: "Landing Page Copy",
      description: "Complete landing page copy with headlines, CTAs, and body copy optimized for conversion."
    },
    {
      icon: <Mail className="w-6 h-6" />,
      title: "Email Sequences",
      description: "Pre-written email flows for welcome series, nurture campaigns, and promotional blasts."
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "A/B Testing Variants",
      description: "Automatic generation of multiple copy variants for split testing and optimization."
    }
  ]

  // Use dynamic products from API, fallback to hardcoded if loading/error
  const plans = products.length > 0 ? products : [
    {
      id: 'monthly',
      name: 'CopyKit Monthly',
      price: '£49',
      period: '/month',
      sku: 'COPYKIT-MONTHLY',
      description: 'Perfect for growing businesses',
      features: [
        'Weekly ad creative packs (10+ variants)',
        'Monthly landing page copy',
        'Email swipe files',
        'A/B testing variants',
        'Priority support',
        'Brand voice customization'
      ],
      popular: true,
      available: true
    },
    {
      id: 'bundle',
      name: 'Full Funnel Pack',
      price: '£199',
      period: 'one-time',
      sku: 'COPYKIT-BUNDLE',
      description: 'Complete funnel in one package',
      features: [
        'Complete funnel copy (awareness → conversion)',
        '50+ ad creatives',
        '5 landing pages',
        '3 email sequences',
        'Competitor analysis',
        'Lifetime access'
      ],
      popular: false,
      available: true
    },
    {
      id: 'briefing',
      name: 'Daily Briefing',
      price: '£15',
      period: '/month',
      sku: 'DAILYBRIEF-MONTHLY',
      description: 'Stay ahead of market trends',
      features: [
        'Daily market insights',
        'Trend analysis',
        'Audio briefing (TTS)',
        'Social media clips',
        'Trading & creator niches',
        'Archive access'
      ],
      popular: false,
      available: true
    }
  ]

  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Growth Marketing Lead",
      content: "CopyKit cut my ad creative time from 4 hours to 15 minutes. The AI understands my brand voice better than most copywriters I've hired.",
      rating: 5
    },
    {
      name: "Marcus Rodriguez",
      role: "SaaS Founder",
      content: "The Full Funnel Pack paid for itself in the first week. Our conversion rate jumped 34% after implementing the landing page copy.",
      rating: 5
    },
    {
      name: "James Thompson",
      role: "Day Trader",
      content: "The Daily Briefing keeps me ahead of market trends. It's like having a research team working overnight.",
      rating: 5
    }
  ]

  const handleCheckout = (plan) => {
    setSelectedPlan(plan)
    // In production, this would redirect to Stripe/PayPal checkout
    console.log('Checkout initiated for:', plan.sku, 'Selected plan:', selectedPlan)
    alert(`Checkout for ${plan.name} - ${plan.sku}\n\nIn production, this would redirect to Stripe or PayPal checkout.`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            <span className="text-xl font-bold">CopyKit</span>
          </div>
          <div className="hidden md:flex gap-6">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
            <a href="#testimonials" className="text-muted-foreground hover:text-foreground transition-colors">Testimonials</a>
          </div>
          <Button variant="outline">Sign In</Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <Badge variant="secondary" className="mb-4">
            <Sparkles className="w-3 h-3 mr-1" />
            AI-Powered Copywriting
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Transform Your Marketing with AI-Powered Copy That Converts
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Get weekly ad creatives, landing page copy, and email sequences crafted by advanced AI — designed to boost your conversion rates and save you hours of work.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="text-lg px-8" onClick={() => document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' })}>
              Start Your Free Trial
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8">
              See How It Works
            </Button>
          </div>
          <div className="flex items-center justify-center gap-8 pt-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              <span>7-Day Money-Back</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              <span>Cancel Anytime</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              <span>500+ Happy Users</span>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="bg-muted/50 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <h2 className="text-3xl md:text-4xl font-bold">Stop Wasting Time on Copy That Doesn't Convert</h2>
            <div className="grid md:grid-cols-2 gap-6 text-left">
              <Card className="border-destructive/50">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">❌ Spending hours writing ad copy that falls flat</p>
                </CardContent>
              </Card>
              <Card className="border-destructive/50">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">❌ Missing deadlines because you're stuck on headlines</p>
                </CardContent>
              </Card>
              <Card className="border-destructive/50">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">❌ Paying expensive copywriters for inconsistent results</p>
                </CardContent>
              </Card>
              <Card className="border-destructive/50">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">❌ Watching competitors outperform you with better messaging</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold">AI CopyKit: Your 24/7 Conversion Copywriter</h2>
            <p className="text-xl text-muted-foreground">Everything you need to create high-converting marketing copy</p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription className="text-base">{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-muted/50 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center space-y-4 mb-16">
              <h2 className="text-3xl md:text-4xl font-bold">Choose Your Growth Plan</h2>
              <p className="text-xl text-muted-foreground">Simple, transparent pricing that scales with your business</p>
              {analytics && (
                <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    <span>{analytics.totals?.orders || 0} orders</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4" />
                    <span>£{analytics.totals?.revenue || 0} revenue</span>
                  </div>
                </div>
              )}
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              {productsLoading ? (
                // Loading state
                Array.from({ length: 3 }).map((_, index) => (
                  <Card key={index} className="relative">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span className="text-muted-foreground">Loading...</span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Array.from({ length: 4 }).map((_, i) => (
                          <div key={i} className="h-4 bg-muted rounded animate-pulse" />
                        ))}
                      </div>
                    </CardContent>
                    <CardFooter>
                      <Button className="w-full" disabled>
                        Loading...
                      </Button>
                    </CardFooter>
                  </Card>
                ))
              ) : (
                plans.map((plan) => (
                  <Card key={plan.id} className={`relative ${plan.popular ? 'border-primary shadow-lg scale-105' : ''} ${!plan.available ? 'opacity-50' : ''}`}>
                    {plan.popular && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most Popular</Badge>
                    )}
                    {!plan.available && (
                      <Badge variant="secondary" className="absolute -top-3 right-4">Unavailable</Badge>
                    )}
                    <CardHeader>
                      <CardTitle className="text-2xl">{plan.name}</CardTitle>
                      <CardDescription>{plan.description}</CardDescription>
                      <div className="mt-4">
                        <span className="text-4xl font-bold">{plan.price}</span>
                        <span className="text-muted-foreground">{plan.period}</span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-3">
                        {plan.features.map((feature, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                            <span className="text-sm">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      <Button 
                        className="w-full" 
                        variant={plan.popular ? "default" : "outline"}
                        onClick={() => handleCheckout(plan)}
                        disabled={!plan.available}
                      >
                        {!plan.available ? 'Unavailable' : plan.period === 'one-time' ? 'Buy Now' : 'Start Free Trial'}
                      </Button>
                    </CardFooter>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="container mx-auto px-4 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold">Trusted by 500+ Marketers & Founders</h2>
            <p className="text-xl text-muted-foreground">See what our customers are saying</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex gap-1 mb-2">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <CardDescription className="text-base italic">"{testimonial.content}"</CardDescription>
                </CardHeader>
                <CardFooter className="flex-col items-start">
                  <p className="font-semibold">{testimonial.name}</p>
                  <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-primary-foreground py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <h2 className="text-3xl md:text-4xl font-bold">Ready to Transform Your Marketing?</h2>
            <p className="text-xl opacity-90">Join 500+ marketers who've already boosted their conversions with AI-powered copy.</p>
            <Button size="lg" variant="secondary" className="text-lg px-8" onClick={() => document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' })}>
              Start Your Free Trial Today
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-sm opacity-90">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4" />
                <span>7-Day Money-Back Guarantee</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4" />
                <span>Secure Payment via Stripe & PayPal</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4" />
                <span>Cancel Anytime</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-background py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold">CopyKit</span>
              </div>
              <p className="text-sm text-muted-foreground">AI-powered copywriting for modern marketers.</p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#features" className="hover:text-foreground transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Examples</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">About</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Legal</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Refund Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
            <p>© 2025 CopyKit. All rights reserved. GDPR Compliant.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

