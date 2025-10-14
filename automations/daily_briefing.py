#!/usr/bin/env python3
"""
Daily Briefing Automation (A3-briefing-daily)
Runs daily at 07:00 BST to generate market briefing content

Schedule: 0 7 * * * (Daily at 7 AM BST)
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from openai import OpenAI
from prisma import Prisma

# Initialize clients
db = Prisma()
openai_client = OpenAI()  # Uses OPENAI_API_KEY from env

# Configuration
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
INVIDEO_API_KEY = os.getenv('INVIDEO_API_KEY')

def log_automation(automation_id: str, status: str, trigger_data: Dict = None, 
                   execution_data: Dict = None, error_message: str = None):
    """Log automation execution to database"""
    started_at = datetime.utcnow()
    
    try:
        db.automationlog.create(
            data={
                'automationId': automation_id,
                'automationName': 'Daily Briefing Generation',
                'status': status,
                'triggerData': trigger_data or {},
                'executionData': execution_data or {},
                'errorMessage': error_message,
                'startedAt': started_at,
                'completedAt': datetime.utcnow() if status in ['completed', 'failed'] else None
            }
        )
    except Exception as e:
        print(f"Failed to log automation: {e}")

def fetch_polygon_market_data() -> Dict[str, Any]:
    """Fetch market movers and sector performance from Polygon.io"""
    try:
        # Get previous trading day
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Fetch top gainers
        gainers_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers?apiKey={POLYGON_API_KEY}"
        gainers_response = requests.get(gainers_url)
        gainers_data = gainers_response.json()
        
        # Fetch top losers
        losers_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/losers?apiKey={POLYGON_API_KEY}"
        losers_response = requests.get(losers_url)
        losers_data = losers_response.json()
        
        # Fetch market indices
        indices_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_API_KEY}"
        indices_response = requests.get(indices_url)
        indices_data = indices_response.json()
        
        return {
            'gainers': gainers_data.get('tickers', [])[:5],
            'losers': losers_data.get('tickers', [])[:5],
            'indices': indices_data.get('tickers', [])[:3],
            'date': yesterday
        }
    
    except Exception as e:
        print(f"Error fetching Polygon data: {e}")
        return {'error': str(e)}

def scrape_trending_sources() -> List[Dict[str, str]]:
    """Scrape trending sources using Firecrawl"""
    try:
        # List of trending sources to scrape
        sources = [
            'https://techcrunch.com',
            'https://www.theverge.com',
            'https://news.ycombinator.com',
            'https://www.bloomberg.com/markets',
            'https://www.cnbc.com/markets/'
        ]
        
        trending_content = []
        
        for source in sources[:3]:  # Limit to 3 for speed
            try:
                # Use Firecrawl API to scrape
                response = requests.post(
                    'https://api.firecrawl.dev/v0/scrape',
                    headers={
                        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'url': source,
                        'formats': ['markdown']
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    trending_content.append({
                        'source': source,
                        'content': data.get('markdown', '')[:1000]  # First 1000 chars
                    })
            except Exception as e:
                print(f"Error scraping {source}: {e}")
                continue
        
        return trending_content
    
    except Exception as e:
        print(f"Error in Firecrawl scraping: {e}")
        return []

def generate_briefing_content(market_data: Dict, trending_content: List[Dict]) -> Dict[str, str]:
    """Generate briefing content using LLM"""
    try:
        # Prepare context
        context = f"""
        Market Data:
        - Top Gainers: {json.dumps(market_data.get('gainers', [])[:3], indent=2)}
        - Top Losers: {json.dumps(market_data.get('losers', [])[:3], indent=2)}
        
        Trending Topics:
        {json.dumps(trending_content, indent=2)}
        """
        
        # Generate article using OpenAI
        article_response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst and content creator. Generate a daily briefing that synthesizes market data and trending topics into a 5-point thesis with contrarian insights. Write in a professional yet engaging tone."
                },
                {
                    "role": "user",
                    "content": f"Based on this data, create a daily briefing:\n\n{context}\n\nStructure:\n1. Market Overview (2-3 sentences)\n2. Key Movers Analysis (3-4 sentences)\n3. Trending Topics Synthesis (3-4 sentences)\n4. Contrarian Take (2-3 sentences)\n5. Action Items (3 bullet points)"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        article_content = article_response.choices[0].message.content
        
        # Generate email version
        email_response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an email copywriter. Convert this briefing into an engaging email with a compelling subject line and clear CTA."
                },
                {
                    "role": "user",
                    "content": f"Convert this briefing into an email:\n\n{article_content}\n\nInclude:\n- Subject line\n- Preheader\n- Body with HTML formatting\n- CTA to upgrade/subscribe"
                }
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        email_content = email_response.choices[0].message.content
        
        return {
            'article': article_content,
            'email': email_content,
            'title': f"Daily Briefing - {datetime.now().strftime('%B %d, %Y')}"
        }
    
    except Exception as e:
        print(f"Error generating content: {e}")
        return {
            'article': '',
            'email': '',
            'title': '',
            'error': str(e)
        }

def generate_audio_briefing(text: str) -> str:
    """Generate audio briefing using ElevenLabs TTS"""
    try:
        from elevenlabs import ElevenLabs
        
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Generate audio
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Default voice
            model_id="eleven_monolingual_v1"
        )
        
        # Save audio file
        audio_filename = f"briefing_{datetime.now().strftime('%Y%m%d')}.mp3"
        audio_path = f"/tmp/{audio_filename}"
        
        with open(audio_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        # TODO: Upload to storage (S3, Cloudflare R2, etc.)
        # For now, return local path
        return audio_path
    
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""

def generate_video_clip(script: str) -> str:
    """Generate short video clip using InVideo API"""
    try:
        # InVideo API integration
        # Note: This is a placeholder - actual InVideo API may differ
        response = requests.post(
            'https://api.invideo.io/v1/videos',
            headers={
                'Authorization': f'Bearer {INVIDEO_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'script': script[:500],  # Limit for short clip
                'duration': 45,
                'template': 'news_briefing',
                'voice': 'professional_male'
            }
        )
        
        if response.status_code == 200:
            video_data = response.json()
            return video_data.get('video_url', '')
        else:
            print(f"InVideo API error: {response.status_code}")
            return ""
    
    except Exception as e:
        print(f"Error generating video: {e}")
        return ""

def publish_to_webflow(content: Dict) -> bool:
    """Publish briefing to Webflow blog"""
    try:
        # Webflow API integration
        # This would use the Webflow CMS API to create a new blog post
        print(f"Publishing to Webflow: {content['title']}")
        # TODO: Implement Webflow API integration
        return True
    
    except Exception as e:
        print(f"Error publishing to Webflow: {e}")
        return False

def save_to_database(content: Dict, audio_url: str, video_url: str) -> str:
    """Save content assets to database"""
    try:
        asset = db.contentasset.create(
            data={
                'type': 'article',
                'title': content['title'],
                'content': content['article'],
                'metadata': {
                    'email_version': content['email'],
                    'audio_url': audio_url,
                    'video_url': video_url,
                    'generated_at': datetime.utcnow().isoformat()
                },
                'published': True,
                'publishedAt': datetime.utcnow()
            }
        )
        
        return asset.id
    
    except Exception as e:
        print(f"Error saving to database: {e}")
        return ""

def send_email_campaign(content: Dict) -> bool:
    """Send email to subscribers via Gmail API"""
    try:
        # Get active Daily Briefing subscribers
        subscribers = db.subscription.find_many(
            where={
                'sku': 'DAILYBRIEF-MONTHLY',
                'status': 'active'
            }
        )
        
        print(f"Sending email to {len(subscribers)} subscribers")
        
        # TODO: Implement Gmail API or SMTP sending
        # For now, just log
        for subscriber in subscribers:
            print(f"Would send to: {subscriber.customerEmail}")
        
        return True
    
    except Exception as e:
        print(f"Error sending emails: {e}")
        return False

def update_daily_kpi():
    """Update KPI for today"""
    try:
        today = datetime.now().date()
        
        # Count today's metrics
        leads_count = db.lead.count(
            where={'createdAt': {'gte': datetime.combine(today, datetime.min.time())}}
        )
        
        orders = db.order.find_many(
            where={'createdAt': {'gte': datetime.combine(today, datetime.min.time())}}
        )
        
        orders_count = len(orders)
        gross_gbp = sum(float(order.amountGbp) for order in orders)
        refunds_count = sum(1 for order in orders if order.status == 'refunded')
        
        # Upsert KPI record
        db.kpidaily.upsert(
            where={'date': today},
            data={
                'create': {
                    'date': today,
                    'leads': leads_count,
                    'orders': orders_count,
                    'grossGbp': gross_gbp,
                    'refunds': refunds_count
                },
                'update': {
                    'leads': leads_count,
                    'orders': orders_count,
                    'grossGbp': gross_gbp,
                    'refunds': refunds_count
                }
            }
        )
        
        print(f"Updated KPI for {today}: {leads_count} leads, {orders_count} orders, £{gross_gbp:.2f} gross")
    
    except Exception as e:
        print(f"Error updating KPI: {e}")

def main():
    """Main automation workflow"""
    automation_id = 'A3-briefing-daily'
    started_at = datetime.utcnow()
    
    print(f"Starting Daily Briefing automation at {started_at}")
    
    try:
        # Connect to database
        db.connect()
        
        # Step 1: Fetch market data
        print("Fetching Polygon.io market data...")
        market_data = fetch_polygon_market_data()
        
        # Step 2: Scrape trending sources
        print("Scraping trending sources with Firecrawl...")
        trending_content = scrape_trending_sources()
        
        # Step 3: Generate briefing content
        print("Generating briefing content with LLM...")
        content = generate_briefing_content(market_data, trending_content)
        
        if 'error' in content:
            raise Exception(f"Content generation failed: {content['error']}")
        
        # Step 4: Generate audio
        print("Generating audio with ElevenLabs...")
        audio_url = generate_audio_briefing(content['article'])
        
        # Step 5: Generate video clip
        print("Generating video with InVideo...")
        video_url = generate_video_clip(content['article'])
        
        # Step 6: Save to database
        print("Saving to database...")
        asset_id = save_to_database(content, audio_url, video_url)
        
        # Step 7: Publish to Webflow
        print("Publishing to Webflow...")
        publish_to_webflow(content)
        
        # Step 8: Send email campaign
        print("Sending email campaign...")
        send_email_campaign(content)
        
        # Step 9: Update KPIs
        print("Updating daily KPIs...")
        update_daily_kpi()
        
        # Log success
        execution_data = {
            'asset_id': asset_id,
            'audio_url': audio_url,
            'video_url': video_url,
            'market_data_points': len(market_data.get('gainers', [])),
            'trending_sources': len(trending_content)
        }
        
        log_automation(automation_id, 'completed', 
                      trigger_data={'scheduled': True}, 
                      execution_data=execution_data)
        
        print(f"Daily Briefing automation completed successfully!")
        
    except Exception as e:
        print(f"Error in automation: {e}")
        log_automation(automation_id, 'failed', 
                      trigger_data={'scheduled': True},
                      error_message=str(e))
        sys.exit(1)
    
    finally:
        # Disconnect from database
        if db.is_connected():
            db.disconnect()

if __name__ == '__main__':
    main()

