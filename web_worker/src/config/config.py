"""
Configuration module for the secure web worker
"""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WebWorkerConfig:
    """Configuration for the web worker"""
    
    # Network settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_concurrent_requests: int = 10
    
    # Proxy settings
    proxy_url: Optional[str] = None
    proxy_auth: Optional[str] = None
    
    # Search API settings
    duckduckgo_enabled: bool = True
    bing_api_key: Optional[str] = None
    fallback_search_enabled: bool = True
    
    # Content filtering settings
    enable_domain_filtering: bool = True
    enable_keyword_filtering: bool = True
    enable_ml_filtering: bool = True
    
    # Safety settings
    max_content_size: int = 5 * 1024 * 1024  # 5MB
    allowed_schemes: List[str] = None
    blocked_domains_file: str = "blocked_domains.txt"
    sensitive_keywords_file: str = "sensitive_keywords.txt"
    
    # Caching settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_directory: str = "./cache"
    
    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds
    
    # Character permissions
    default_character_permissions: dict = None
    
    def __post_init__(self):
        if self.allowed_schemes is None:
            self.allowed_schemes = ["https"]
        
        if self.default_character_permissions is None:
            self.default_character_permissions = {
                "allow_internet_access": True,
                "max_request_per_hour": 100,
                "allowed_domains_only": [],
                "blocked_domains": []
            }


# Global configuration instance
config = WebWorkerConfig()


def load_config_from_env():
    """Load configuration from environment variables"""
    global config
    
    # Network settings
    config.timeout = int(os.getenv("WEB_WORKER_TIMEOUT", config.timeout))
    config.max_retries = int(os.getenv("WEB_WORKER_MAX_RETRIES", config.max_retries))
    config.retry_delay = float(os.getenv("WEB_WORKER_RETRY_DELAY", config.retry_delay))
    config.max_concurrent_requests = int(os.getenv("WEB_WORKER_MAX_CONCURRENT", config.max_concurrent_requests))
    
    # Proxy settings
    config.proxy_url = os.getenv("WEB_WORKER_PROXY_URL", config.proxy_url)
    config.proxy_auth = os.getenv("WEB_WORKER_PROXY_AUTH", config.proxy_auth)
    
    # Search API settings
    config.duckduckgo_enabled = os.getenv("DUCKDUCKGO_ENABLED", str(config.duckduckgo_enabled)).lower() == "true"
    config.bing_api_key = os.getenv("BING_API_KEY", config.bing_api_key)
    config.fallback_search_enabled = os.getenv("FALLBACK_SEARCH_ENABLED", str(config.fallback_search_enabled)).lower() == "true"
    
    # Content filtering settings
    config.enable_domain_filtering = os.getenv("ENABLE_DOMAIN_FILTERING", str(config.enable_domain_filtering)).lower() == "true"
    config.enable_keyword_filtering = os.getenv("ENABLE_KEYWORD_FILTERING", str(config.enable_keyword_filtering)).lower() == "true"
    config.enable_ml_filtering = os.getenv("ENABLE_ML_FILTERING", str(config.enable_ml_filtering)).lower() == "true"
    
    # Safety settings
    config.max_content_size = int(os.getenv("MAX_CONTENT_SIZE", config.max_content_size))
    config.blocked_domains_file = os.getenv("BLOCKED_DOMAINS_FILE", config.blocked_domains_file)
    config.sensitive_keywords_file = os.getenv("SENSITIVE_KEYWORDS_FILE", config.sensitive_keywords_file)
    
    # Caching settings
    config.cache_enabled = os.getenv("CACHE_ENABLED", str(config.cache_enabled)).lower() == "true"
    config.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", config.cache_ttl_seconds))
    config.cache_directory = os.getenv("CACHE_DIRECTORY", config.cache_directory)


# Load configuration from environment variables on import
load_config_from_env()