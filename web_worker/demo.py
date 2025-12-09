"""
Demo script for the Secure Web Worker
Demonstrates the key functionality of the web worker system
"""

import asyncio
import json
from datetime import datetime
from src.python.web_worker import WebWorker, SearchResult
from src.config.config import config


async def demo_basic_search():
    """Demo basic search functionality"""
    print("=== Basic Search Demo ===")
    
    web_worker = WebWorker()
    
    try:
        # Perform a search
        results = await web_worker.search("Python programming tutorials")
        print(f"Found {len(results)} results")
        
        # Display first few results
        for i, result in enumerate(results[:3]):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.title}")
            print(f"  URL: {result.url}")
            print(f"  Snippet: {result.snippet[:100]}...")
            print(f"  Source: {result.source}")
            print(f"  Time: {result.timestamp}")
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def demo_content_fetching():
    """Demo content fetching with security checks"""
    print("=== Content Fetching Demo ===")
    
    web_worker = WebWorker()
    
    try:
        # First, perform a search to get a valid URL
        results = await web_worker.search("Python official website")
        
        if results:
            # Fetch content from the first result
            sample_url = results[0].url
            print(f"Fetching content from: {sample_url}")
            
            content = await web_worker.fetch_content(sample_url)
            
            if content:
                print(f"Successfully fetched {len(content)} characters")
                print(f"Content preview: {content[:200]}...")
            else:
                print("Failed to fetch content (may have been blocked by filters)")
        else:
            print("No search results found")
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def demo_character_permissions():
    """Demo character permission system"""
    print("=== Character Permissions Demo ===")
    
    web_worker = WebWorker()
    
    try:
        # Check default permissions
        default_perm = web_worker.permission_manager.get_permission("demo_user")
        print(f"Default permissions for demo_user:")
        print(f"  Internet access: {default_perm.allow_internet_access}")
        print(f"  Max requests/hour: {default_perm.max_request_per_hour}")
        print(f"  Allowed domains: {default_perm.allowed_domains_only}")
        print(f"  Blocked domains: {default_perm.blocked_domains}")
        
        # Test rate limiting
        print(f"\nTesting rate limiting...")
        for i in range(3):
            can_request = web_worker.permission_manager.can_make_request("demo_user")
            print(f"  Request {i+1}: {'Allowed' if can_request else 'Denied'}")
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def demo_security_features():
    """Demo security features"""
    print("=== Security Features Demo ===")
    
    web_worker = WebWorker()
    
    try:
        # Show current security settings
        print(f"Security Configuration:")
        print(f"  Domain filtering enabled: {config.enable_domain_filtering}")
        print(f"  Keyword filtering enabled: {config.enable_keyword_filtering}")
        print(f"  ML filtering enabled: {config.enable_ml_filtering}")
        print(f"  Max content size: {config.max_content_size} bytes")
        print(f"  Allowed schemes: {config.allowed_schemes}")
        
        # Test content filter
        print(f"\nTesting content filter...")
        test_url = "https://example.com"
        test_content = "This page contains information about Python programming."
        
        is_safe = web_worker.content_filter.is_content_safe(test_url, test_content)
        print(f"  Is content safe: {is_safe}")
        
        # Test with potentially unsafe content
        unsafe_content = "This page contains personal information like passwords and credit card numbers."
        is_safe_unsafe = web_worker.content_filter.is_content_safe(test_url, unsafe_content)
        print(f"  Is unsafe content safe: {is_safe_unsafe}")
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def demo_caching():
    """Demo caching functionality"""
    print("=== Caching Demo ===")
    
    web_worker = WebWorker()
    
    try:
        # Perform a search
        query = "machine learning basics"
        print(f"First search for: '{query}'")
        start_time = datetime.now()
        results1 = await web_worker.search(query)
        first_time = datetime.now() - start_time
        print(f"  Found {len(results1)} results in {first_time.total_seconds():.2f}s")
        
        # Perform the same search again (should be cached)
        print(f"Second search for: '{query}' (should be faster due to caching)")
        start_time = datetime.now()
        results2 = await web_worker.search(query)
        second_time = datetime.now() - start_time
        print(f"  Found {len(results2)} results in {second_time.total_seconds():.2f}s")
        
        print(f"  Cache effectiveness: {(first_time.total_seconds() / (second_time.total_seconds() + 0.001)):.2f}x speedup")
        print(f"  Current cache size: {len(web_worker.cache.cache)} items")
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def demo_system_health():
    """Demo system health monitoring"""
    print("=== System Health Demo ===")
    
    web_worker = WebWorker()
    
    try:
        health = web_worker.get_health_status()
        print("System Health Status:")
        print(json.dumps(health, indent=2, default=str))
        
        print("\n" + "="*50 + "\n")
        
    finally:
        await web_worker.close()


async def run_all_demos():
    """Run all demo functions"""
    print("Secure Web Worker - Comprehensive Demo\n")
    print("This demo showcases the key features of the secure web worker system.\n")
    
    await demo_basic_search()
    await demo_content_fetching()
    await demo_character_permissions()
    await demo_security_features()
    await demo_caching()
    await demo_system_health()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_all_demos())