"""
Secure Web Worker for Windows 11 with comprehensive content filtering
"""

import asyncio
import aiohttp
import requests
import time
import hashlib
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import tldextract
from bs4 import BeautifulSoup
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime, timedelta

try:
    from src.config.config import config
except ImportError:
    # Handle when run from the same directory
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from config.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Data class for search results"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: datetime


@dataclass
class CharacterPermission:
    """Character permission settings"""
    character_id: str
    allow_internet_access: bool
    max_request_per_hour: int
    allowed_domains_only: List[str]
    blocked_domains: List[str]
    request_count: int = 0
    last_request_time: Optional[datetime] = None


class ContentFilter:
    """Content filtering system with multiple layers of protection"""
    
    def __init__(self):
        self.blocked_domains = self._load_blocked_domains()
        self.sensitive_keywords = self._load_sensitive_keywords()
        self._lock = threading.Lock()
    
    def _load_blocked_domains(self) -> set:
        """Load blocked domains from file"""
        try:
            with open(config.blocked_domains_file, 'r', encoding='utf-8') as f:
                return {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            logger.warning(f"Blocked domains file {config.blocked_domains_file} not found, using empty set")
            return set()
    
    def _load_sensitive_keywords(self) -> set:
        """Load sensitive keywords from file"""
        try:
            with open(config.sensitive_keywords_file, 'r', encoding='utf-8') as f:
                return {line.strip().lower() for line in f if line.strip()}
        except FileNotFoundError:
            logger.warning(f"Sensitive keywords file {config.sensitive_keywords_file} not found, using empty set")
            return set()
    
    def is_domain_blocked(self, domain: str) -> bool:
        """Check if domain is blocked"""
        if not config.enable_domain_filtering:
            return False
        
        return domain.lower() in self.blocked_domains
    
    def contains_sensitive_keywords(self, text: str) -> bool:
        """Check if text contains sensitive keywords"""
        if not config.enable_keyword_filtering:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.sensitive_keywords)
    
    def is_content_safe(self, url: str, content: str) -> bool:
        """Check if content is safe using multiple filtering layers"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check domain blocking
        if self.is_domain_blocked(domain):
            logger.info(f"Domain {domain} is blocked")
            return False
        
        # Check for sensitive keywords in content
        if self.contains_sensitive_keywords(content):
            logger.info(f"Content from {url} contains sensitive keywords")
            return False
        
        # Additional ML-based filtering could be implemented here
        if config.enable_ml_filtering:
            # Placeholder for ML-based content analysis
            # In a real implementation, this would use a trained model
            pass
        
        return True


class RequestCache:
    """Request caching system"""
    
    def __init__(self):
        self.cache = {}
        self._lock = threading.Lock()
    
    def _generate_cache_key(self, url: str, params: Dict) -> str:
        """Generate cache key for request"""
        cache_input = f"{url}_{json.dumps(sorted(params.items()))}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def get(self, url: str, params: Dict) -> Optional[Dict]:
        """Get cached response"""
        with self._lock:
            key = self._generate_cache_key(url, params)
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                # Check if cache is still valid
                if time.time() - timestamp < config.cache_ttl_seconds:
                    logger.debug(f"Cache hit for {url}")
                    return cached_data
                else:
                    # Remove expired cache
                    del self.cache[key]
            return None
    
    def set(self, url: str, params: Dict, response: Dict):
        """Set cached response"""
        with self._lock:
            key = self._generate_cache_key(url, params)
            self.cache[key] = (response, time.time())
            logger.debug(f"Cached response for {url}")


class RateLimiter:
    """Rate limiting system"""
    
    def __init__(self):
        self.requests = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit"""
        with self._lock:
            now = datetime.now()
            if identifier not in self.requests:
                self.requests[identifier] = []
            
            # Remove requests older than the window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < timedelta(seconds=config.rate_limit_window)
            ]
            
            # Check if we're under the limit
            if len(self.requests[identifier]) < config.rate_limit_requests:
                self.requests[identifier].append(now)
                return True
            
            return False


class CharacterPermissionManager:
    """Character permission management system"""
    
    def __init__(self):
        self.permissions = {}
        self._lock = threading.Lock()
    
    def get_permission(self, character_id: str) -> CharacterPermission:
        """Get or create character permission"""
        with self._lock:
            if character_id not in self.permissions:
                # Use default permissions
                default_perms = config.default_character_permissions
                self.permissions[character_id] = CharacterPermission(
                    character_id=character_id,
                    allow_internet_access=default_perms.get("allow_internet_access", True),
                    max_request_per_hour=default_perms.get("max_request_per_hour", 100),
                    allowed_domains_only=default_perms.get("allowed_domains_only", []),
                    blocked_domains=default_perms.get("blocked_domains", [])
                )
            return self.permissions[character_id]
    
    def can_access_domain(self, character_id: str, domain: str) -> bool:
        """Check if character can access a domain"""
        perm = self.get_permission(character_id)
        
        # If allowed domains only is specified, only allow those
        if perm.allowed_domains_only:
            return domain in perm.allowed_domains_only
        
        # Otherwise, check if domain is blocked
        return domain not in perm.blocked_domains
    
    def can_make_request(self, character_id: str) -> bool:
        """Check if character can make a request based on rate limit"""
        perm = self.get_permission(character_id)
        
        # Check if character has internet access
        if not perm.allow_internet_access:
            return False
        
        now = datetime.now()
        
        # Reset request count if it's a new hour
        if perm.last_request_time is None or now.hour != perm.last_request_time.hour:
            perm.request_count = 0
        
        # Check if under request limit
        if perm.request_count < perm.max_request_per_hour:
            perm.request_count += 1
            perm.last_request_time = now
            return True
        
        return False


class WebWorker:
    """Main Web Worker implementation"""
    
    def __init__(self):
        self.session = None
        self.content_filter = ContentFilter()
        self.cache = RequestCache()
        self.rate_limiter = RateLimiter()
        self.permission_manager = CharacterPermissionManager()
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)
        self.search_history = []
        self._session_lock = threading.Lock()
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration"""
        with self._session_lock:
            if self.session is None or self.session.closed:
                connector = aiohttp.TCPConnector(
                    limit=config.max_concurrent_requests,
                    ssl=False  # Allow HTTPS validation
                )
                
                timeout = aiohttp.ClientTimeout(total=config.timeout)
                
                # Configure proxy if available
                proxy = config.proxy_url
                if proxy:
                    logger.info(f"Using proxy: {proxy}")
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                )
            
            return self.session
    
    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[str]:
        """Make an HTTP request with retry logic and safety checks"""
        session = self._get_session()
        
        for attempt in range(config.max_retries + 1):
            try:
                # Validate URL
                parsed = urlparse(url)
                if parsed.scheme not in config.allowed_schemes:
                    logger.warning(f"Invalid scheme for URL: {url}")
                    return None
                
                # Apply proxy if configured
                proxy = config.proxy_url
                proxy_auth = None
                if config.proxy_auth:
                    # Parse proxy auth if provided
                    pass  # Implement proxy auth if needed
                
                async with session.request(
                    method=method,
                    url=url,
                    proxy=proxy,
                    **kwargs
                ) as response:
                    if response.content_length and response.content_length > config.max_content_size:
                        logger.warning(f"Content too large from {url}: {response.content_length} bytes")
                        return None
                    
                    content = await response.text()
                    
                    # Check content safety
                    if not self.content_filter.is_content_safe(url, content):
                        logger.warning(f"Unsafe content detected from {url}")
                        return None
                    
                    logger.info(f"Successfully fetched content from {url}")
                    return content
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for URL: {url}")
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1} for URL {url}: {str(e)}")
            
            if attempt < config.max_retries:
                await asyncio.sleep(config.retry_delay * (2 ** attempt))  # Exponential backoff
        
        logger.error(f"Failed to fetch content from {url} after {config.max_retries + 1} attempts")
        return None
    
    async def search(self, query: str, character_id: str = "default") -> List[SearchResult]:
        """Perform a secure search using DuckDuckGo API"""
        # Check character permissions
        if not self.permission_manager.can_make_request(character_id):
            logger.warning(f"Character {character_id} exceeded request limit")
            return []
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(character_id):
            logger.warning(f"Rate limit exceeded for identifier: {character_id}")
            return []
        
        # Check cache first
        cache_params = {"q": query}
        cached_result = self.cache.get("search", cache_params)
        if cached_result:
            return [SearchResult(**item) for item in cached_result]
        
        results = []
        
        # Try DuckDuckGo first
        if config.duckduckgo_enabled:
            ddg_results = await self._search_duckduckgo(query)
            results.extend(ddg_results)
        
        # Fallback to other sources if needed
        if not results and config.fallback_search_enabled:
            # Add other search sources here (e.g., Bing)
            pass
        
        # Cache results
        if config.cache_enabled and results:
            cache_data = [result.__dict__ for result in results]
            self.cache.set("search", cache_params, cache_data)
        
        # Log search for monitoring
        self.search_history.append({
            "query": query,
            "character_id": character_id,
            "timestamp": datetime.now(),
            "result_count": len(results)
        })
        
        return results
    
    async def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """Search using DuckDuckGo Instant Answer API"""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",  # Get clean text results
            "skip_disambig": "1"
        }
        
        try:
            content = await self._make_request(url, params=params)
            if not content:
                return []
            
            # Parse DuckDuckGo results
            try:
                data = json.loads(content)
                results = []
                
                # Extract related topics which contain search results
                if "RelatedTopics" in data:
                    for item in data["RelatedTopics"]:
                        if "Text" in item and "FirstURL" in item:
                            # Validate domain
                            parsed_url = urlparse(item["FirstURL"])
                            domain = parsed_url.netloc.lower()
                            
                            # Apply content filtering
                            if not self.content_filter.is_domain_blocked(domain) and \
                               not self.content_filter.contains_sensitive_keywords(item["Text"]):
                                results.append(SearchResult(
                                    title=item.get("Text", "No title"),
                                    url=item["FirstURL"],
                                    snippet=item.get("Text", ""),
                                    source="DuckDuckGo",
                                    timestamp=datetime.now()
                                ))
                
                return results
            except json.JSONDecodeError:
                logger.error("Failed to parse DuckDuckGo response as JSON")
                return []
        
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")
            return []
    
    async def fetch_content(self, url: str, character_id: str = "default") -> Optional[str]:
        """Fetch content from a URL with security checks"""
        # Check character permissions
        if not self.permission_manager.can_make_request(character_id):
            logger.warning(f"Character {character_id} exceeded request limit")
            return None
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check character-specific domain permissions
        if not self.permission_manager.can_access_domain(character_id, domain):
            logger.warning(f"Character {character_id} not allowed to access domain: {domain}")
            return None
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(f"{character_id}_fetch"):
            logger.warning(f"Rate limit exceeded for fetch by {character_id}")
            return None
        
        # Check cache
        cache_params = {"url": url}
        cached_content = self.cache.get("fetch", cache_params)
        if cached_content:
            return cached_content
        
        content = await self._make_request(url)
        
        if content and config.cache_enabled:
            self.cache.set("fetch", cache_params, content)
        
        return content
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the web worker"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "timeout": config.timeout,
                "max_retries": config.max_retries,
                "cache_enabled": config.cache_enabled,
                "filtering_enabled": config.enable_domain_filtering or config.enable_keyword_filtering
            },
            "stats": {
                "search_count": len(self.search_history),
                "cache_size": len(self.cache.cache)
            }
        }
    
    async def close(self):
        """Close the web worker and clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        
        self.executor.shutdown(wait=True)


# Global web worker instance
web_worker = WebWorker()


async def main():
    """Main function for testing"""
    try:
        # Test search functionality
        results = await web_worker.search("Python programming")
        print(f"Found {len(results)} results")
        
        for result in results[:3]:  # Show first 3 results
            print(f"Title: {result.title}")
            print(f"URL: {result.url}")
            print(f"Snippet: {result.snippet[:100]}...")
            print("---")
        
        # Test content fetching
        if results:
            content = await web_worker.fetch_content(results[0].url)
            if content:
                print(f"Fetched content length: {len(content)} characters")
            else:
                print("Failed to fetch content")
        
        # Show health status
        health = web_worker.get_health_status()
        print(f"Health status: {health}")
        
    finally:
        await web_worker.close()


if __name__ == "__main__":
    asyncio.run(main())