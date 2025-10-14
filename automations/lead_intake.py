#!/usr/bin/env python3
"""
Lead Intake Automation (A1-lead-intake)
Triggered by Typeform/Jotform submissions via Zapier webhook

This script:
1. Receives lead data from form submissions
2. Upserts lead to Supabase
3. Enriches lead with Explorium
4. Adds to email list
5. Creates CRM records in Notion/Linear
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from prisma import Prisma

# Initialize database client
db = Prisma()

# Configuration
EXPLORIUM_API_KEY = os.getenv('EXPLORIUM_API_KEY', '')
NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
LINEAR_API_KEY = os.getenv('LINEAR_API_KEY', '')

def log_automation(automation_id: str, status: str, trigger_data: Dict = None, 
                   execution_data: Dict = None, error_message: str = None):
    """Log automation execution to database"""
    try:
        db.automationlog.create(
            data={
                'automationId': automation_id,
                'automationName': 'Lead Intake',
                'status': status,
                'triggerData': trigger_data or {},
                'executionData': execution_data or {},
                'errorMessage': error_message,
                'startedAt': datetime.utcnow(),
                'completedAt': datetime.utcnow() if status in ['completed', 'failed'] else None
            }
        )
    except Exception as e:
        print(f"Failed to log automation: {e}")

def upsert_lead(lead_data: Dict[str, Any]) -> str:
    """Upsert lead to database with duplicate guard on email"""
    try:
        # Check if lead exists
        existing_lead = db.lead.find_unique(
            where={'email': lead_data['email']}
        )
        
        if existing_lead:
            # Update existing lead
            lead = db.lead.update(
                where={'email': lead_data['email']},
                data={
                    'name': lead_data.get('name', existing_lead.name),
                    'source': lead_data.get('source', existing_lead.source),
                    'tags': list(set((existing_lead.tags or []) + lead_data.get('tags', []))),
                    'utmSource': lead_data.get('utm_source', existing_lead.utmSource),
                    'utmCampaign': lead_data.get('utm_campaign', existing_lead.utmCampaign),
                    'utmMedium': lead_data.get('utm_medium', existing_lead.utmMedium),
                    'utmTerm': lead_data.get('utm_term', existing_lead.utmTerm),
                    'utmContent': lead_data.get('utm_content', existing_lead.utmContent)
                }
            )
            print(f"Updated existing lead: {lead.email}")
        else:
            # Create new lead
            lead = db.lead.create(
                data={
                    'email': lead_data['email'],
                    'name': lead_data.get('name'),
                    'source': lead_data.get('source', 'Manual'),
                    'tags': lead_data.get('tags', []),
                    'utmSource': lead_data.get('utm_source'),
                    'utmCampaign': lead_data.get('utm_campaign'),
                    'utmMedium': lead_data.get('utm_medium'),
                    'utmTerm': lead_data.get('utm_term'),
                    'utmContent': lead_data.get('utm_content')
                }
            )
            print(f"Created new lead: {lead.email}")
        
        return lead.id
    
    except Exception as e:
        print(f"Error upserting lead: {e}")
        raise

def enrich_lead_with_explorium(email: str, lead_id: str) -> Dict[str, Any]:
    """Enrich lead with company, role, and LinkedIn using Explorium"""
    try:
        # Note: This is a placeholder for Explorium API integration
        # Actual implementation would use the Explorium MCP server or API
        
        # For now, return mock enrichment data
        enrichment = {
            'company': 'Example Corp',
            'role': 'Marketing Manager',
            'linkedin': f'https://linkedin.com/in/{email.split("@")[0]}'
        }
        
        # Update lead with enrichment data
        db.lead.update(
            where={'id': lead_id},
            data={
                'enrichmentCompany': enrichment['company'],
                'enrichmentRole': enrichment['role'],
                'enrichmentLinkedin': enrichment['linkedin']
            }
        )
        
        print(f"Enriched lead {email}: {enrichment}")
        return enrichment
    
    except Exception as e:
        print(f"Error enriching lead: {e}")
        return {}

def add_to_email_list(email: str, name: str, tags: list) -> bool:
    """Add lead to Gmail/ESP warm list"""
    try:
        # This would integrate with Gmail API or ESP (Mailchimp, SendGrid, etc.)
        # For now, just log
        print(f"Adding {email} to email list 'Warm Leads' with tags: {tags}")
        
        # TODO: Implement actual email list integration
        # Example with Gmail API:
        # - Create label "Warm Leads"
        # - Add contact to Google Contacts
        # - Tag with custom fields
        
        return True
    
    except Exception as e:
        print(f"Error adding to email list: {e}")
        return False

def create_notion_crm_record(lead_data: Dict, enrichment: Dict) -> Optional[str]:
    """Create CRM record in Notion"""
    try:
        if not NOTION_API_KEY:
            print("Notion API key not configured, skipping...")
            return None
        
        # Notion API integration
        # This would create a new page in a Notion database
        
        notion_url = "https://api.notion.com/v1/pages"
        headers = {
            'Authorization': f'Bearer {NOTION_API_KEY}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        # Note: You need to replace 'database_id' with your actual Notion database ID
        payload = {
            'parent': {'database_id': os.getenv('NOTION_CRM_DATABASE_ID', 'placeholder')},
            'properties': {
                'Email': {'email': lead_data['email']},
                'Name': {'title': [{'text': {'content': lead_data.get('name', 'Unknown')}}]},
                'Company': {'rich_text': [{'text': {'content': enrichment.get('company', '')}}]},
                'Role': {'rich_text': [{'text': {'content': enrichment.get('role', '')}}]},
                'Source': {'select': {'name': lead_data.get('source', 'Manual')}},
                'Tags': {'multi_select': [{'name': tag} for tag in lead_data.get('tags', [])]}
            }
        }
        
        # Uncomment to actually call Notion API
        # response = requests.post(notion_url, headers=headers, json=payload)
        # if response.status_code == 200:
        #     notion_page_id = response.json()['id']
        #     print(f"Created Notion CRM record: {notion_page_id}")
        #     return notion_page_id
        
        print(f"Would create Notion CRM record for {lead_data['email']}")
        return "notion-page-id-placeholder"
    
    except Exception as e:
        print(f"Error creating Notion record: {e}")
        return None

def create_linear_task_if_enterprise(lead_data: Dict, enrichment: Dict) -> Optional[str]:
    """Create Linear follow-up task if enterprise signal detected"""
    try:
        # Check for enterprise signals
        enterprise_signals = [
            'director' in enrichment.get('role', '').lower(),
            'vp' in enrichment.get('role', '').lower(),
            'head of' in enrichment.get('role', '').lower(),
            'chief' in enrichment.get('role', '').lower(),
            'ceo' in enrichment.get('role', '').lower(),
            'cto' in enrichment.get('role', '').lower(),
            'cmo' in enrichment.get('role', '').lower()
        ]
        
        if not any(enterprise_signals):
            print("No enterprise signals detected, skipping Linear task creation")
            return None
        
        if not LINEAR_API_KEY:
            print("Linear API key not configured, skipping...")
            return None
        
        # Linear API integration
        linear_url = "https://api.linear.app/graphql"
        headers = {
            'Authorization': LINEAR_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # GraphQL mutation to create issue
        mutation = """
        mutation CreateIssue($title: String!, $description: String!, $teamId: String!) {
          issueCreate(input: {
            title: $title,
            description: $description,
            teamId: $teamId,
            priority: 1
          }) {
            success
            issue {
              id
              title
            }
          }
        }
        """
        
        variables = {
            'title': f"Follow up with {lead_data.get('name', 'Unknown')} - {enrichment.get('company', '')}",
            'description': f"Enterprise lead detected:\n\nEmail: {lead_data['email']}\nRole: {enrichment.get('role', '')}\nCompany: {enrichment.get('company', '')}\nLinkedIn: {enrichment.get('linkedin', '')}\n\nSource: {lead_data.get('source', 'Unknown')}\nUTM Campaign: {lead_data.get('utm_campaign', 'N/A')}",
            'teamId': os.getenv('LINEAR_TEAM_ID', 'placeholder')
        }
        
        # Uncomment to actually call Linear API
        # response = requests.post(linear_url, headers=headers, json={'query': mutation, 'variables': variables})
        # if response.status_code == 200:
        #     result = response.json()
        #     if result['data']['issueCreate']['success']:
        #         issue_id = result['data']['issueCreate']['issue']['id']
        #         print(f"Created Linear task: {issue_id}")
        #         return issue_id
        
        print(f"Would create Linear task for enterprise lead: {lead_data['email']}")
        return "linear-issue-id-placeholder"
    
    except Exception as e:
        print(f"Error creating Linear task: {e}")
        return None

def process_lead(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main lead processing workflow"""
    automation_id = 'A1-lead-intake'
    
    try:
        print(f"Processing lead: {lead_data['email']}")
        
        # Step 1: Upsert lead to database
        lead_id = upsert_lead(lead_data)
        
        # Step 2: Enrich lead with Explorium
        enrichment = enrich_lead_with_explorium(lead_data['email'], lead_id)
        
        # Step 3: Add to email list
        add_to_email_list(
            lead_data['email'], 
            lead_data.get('name', ''), 
            lead_data.get('tags', [])
        )
        
        # Step 4: Create Notion CRM record
        notion_page_id = create_notion_crm_record(lead_data, enrichment)
        
        # Step 5: Create Linear task if enterprise signal
        linear_issue_id = create_linear_task_if_enterprise(lead_data, enrichment)
        
        # Log success
        execution_data = {
            'lead_id': lead_id,
            'enrichment': enrichment,
            'notion_page_id': notion_page_id,
            'linear_issue_id': linear_issue_id
        }
        
        log_automation(
            automation_id,
            'completed',
            trigger_data=lead_data,
            execution_data=execution_data
        )
        
        return {
            'success': True,
            'lead_id': lead_id,
            'execution_data': execution_data
        }
    
    except Exception as e:
        print(f"Error processing lead: {e}")
        log_automation(
            automation_id,
            'failed',
            trigger_data=lead_data,
            error_message=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main entry point for lead intake automation"""
    # This would be called by Zapier webhook or form submission handler
    
    # Example lead data (in production, this comes from webhook payload)
    example_lead_data = {
        'email': 'john.doe@example.com',
        'name': 'John Doe',
        'source': 'Typeform',
        'tags': ['copykit-interest', 'q4-2025'],
        'utm_source': 'google',
        'utm_campaign': 'copykit-launch',
        'utm_medium': 'cpc',
        'utm_term': 'ai copywriting',
        'utm_content': 'ad-variant-1'
    }
    
    try:
        # Connect to database
        db.connect()
        
        # Process lead
        result = process_lead(example_lead_data)
        
        print(f"\nLead processing result: {json.dumps(result, indent=2)}")
        
        if result['success']:
            print("\n✓ Lead intake automation completed successfully!")
        else:
            print(f"\n✗ Lead intake automation failed: {result['error']}")
            sys.exit(1)
    
    finally:
        # Disconnect from database
        if db.is_connected():
            db.disconnect()

if __name__ == '__main__':
    main()

