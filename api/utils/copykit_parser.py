"""
CopyKit HTML parsing utilities
Extracts data from CopyKit HTML content including global environment variables,
metadata, and other relevant information.
"""

import json
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup


def parse_copykit_html(html_text: str) -> Dict:
    """
    Parse CopyKit HTML content and extract relevant data.
    
    Args:
        html_text (str): Raw HTML content from CopyKit URL
        
    Returns:
        Dict: Parsed data containing global_env, title, meta_description, etc.
        
    Example:
        >>> html = "<html><head><title>Test</title></head></html>"
        >>> result = parse_copykit_html(html)
        >>> print(result['title'])
        'Test'
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Extract global environment variables
        global_env = _extract_global_env(soup)
        
        # Extract metadata
        title = _extract_title(soup)
        meta_description = _extract_meta_description(soup)
        
        return {
            'global_env': global_env,
            'title': title,
            'meta_description': meta_description,
            'content_length': len(html_text)
        }
        
    except Exception as e:
        # Return error information if parsing fails
        return {
            'error': f"Failed to parse HTML: {str(e)}",
            'global_env': {},
            'title': None,
            'meta_description': None,
            'content_length': len(html_text) if html_text else 0
        }


def _extract_global_env(soup: BeautifulSoup) -> Dict:
    """
    Extract global environment variables from script tags.
    
    Args:
        soup: BeautifulSoup parsed HTML object
        
    Returns:
        Dict: Global environment variables or empty dict if not found
    """
    script_tags = soup.find_all('script')
    
    for script in script_tags:
        if script.string and '__manus__global_env' in script.string:
            # Extract the global environment object using regex
            env_match = re.search(r'__manus__global_env\s*=\s*({[^}]+})', script.string)
            if env_match:
                try:
                    return json.loads(env_match.group(1))
                except json.JSONDecodeError:
                    # If JSON parsing fails, continue to next script tag
                    continue
    
    return {}


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract page title from HTML.
    
    Args:
        soup: BeautifulSoup parsed HTML object
        
    Returns:
        str: Page title or None if not found
    """
    title_tag = soup.find('title')
    return title_tag.string if title_tag else None


def _extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract meta description content from HTML.
    
    Args:
        soup: BeautifulSoup parsed HTML object
        
    Returns:
        str: Meta description content or None if not found
    """
    meta_description_tag = soup.find('meta', attrs={'name': 'description'})
    return meta_description_tag.get('content') if meta_description_tag else None


def validate_parsed_data(data: Dict) -> bool:
    """
    Validate that parsed data contains expected structure.
    
    Args:
        data: Parsed data dictionary
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    required_keys = ['global_env', 'title', 'meta_description', 'content_length']
    
    # Check if all required keys are present
    if not all(key in data for key in required_keys):
        return False
    
    # Check if global_env is a dictionary
    if not isinstance(data['global_env'], dict):
        return False
    
    # Check if content_length is a positive integer
    if not isinstance(data['content_length'], int) or data['content_length'] < 0:
        return False
    
    return True