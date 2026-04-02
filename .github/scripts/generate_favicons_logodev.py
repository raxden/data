#!/usr/bin/env python3
"""
Generate favicons using Logo.dev API for radio stations.
This script processes stations and generates favicon URLs using logo.dev service.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Logo.dev API token from environment variable
LOGODEV_TOKEN = os.environ.get('LOGO_TOKEN', '').strip()

if not LOGODEV_TOKEN:
    print("Error: LOGO_TOKEN environment variable not set")
    sys.exit(1)

print(f"✓ LOGO_TOKEN loaded (length: {len(LOGODEV_TOKEN)} chars)")

def extract_domain(url):
    """Extract domain from URL."""
    if not url or url.strip() == "":
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except:
        return None

def generate_logodev_url(domain):
    """Generate logo.dev URL for a given domain."""
    if not domain:
        return None
    
    return f"https://img.logo.dev/{domain}?token={LOGODEV_TOKEN}"

def validate_url(url, timeout=5, verbose=False):
    """Validate if a URL is accessible and returns a valid response."""
    if not url or url.strip() == "":
        if verbose:
            print(f"    ⚠️  URL is empty")
        return False
    
    # Logo.dev doesn't support HEAD requests - skip directly to GET
    if 'logo.dev' in url:
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            if response.status_code < 400:
                if verbose:
                    print(f"    ✓ GET request successful (status {response.status_code})")
                return True
            else:
                if verbose:
                    print(f"    ❌ GET request failed with status {response.status_code}")
                return False
        except Exception as e:
            if verbose:
                print(f"    ❌ GET request failed: {type(e).__name__}")
            return False
    
    # For other URLs, try HEAD first
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code < 400:
            if verbose:
                print(f"    ✓ HEAD request successful (status {response.status_code})")
            return True
        else:
            if verbose:
                print(f"    ❌ HEAD request failed with status {response.status_code}")
            return False
    except Exception as e:
        if verbose:
            print(f"    ⚠️  HEAD request failed ({type(e).__name__}), trying GET...")
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            if response.status_code < 400:
                if verbose:
                    print(f"    ✓ GET request successful (status {response.status_code})")
                return True
            else:
                if verbose:
                    print(f"    ❌ GET request failed with status {response.status_code}")
                return False
        except Exception as e2:
            if verbose:
                print(f"    ❌ GET request failed: {type(e2).__name__}")
            return False

def process_station(station):
    """Process a single station and generate logo.dev favicon URL."""
    name = station.get('name', '').strip()
    url = station.get('url', '').strip()
    url_resolved = station.get('url_resolved', url).strip()
    homepage = station.get('homepage', '').strip()
    
    # Use url_resolved if available, otherwise use url
    stream_url = url_resolved if url_resolved else url
    
    result = {
        'name': name,
        'url': stream_url,
        'favicon': None
    }
    
    # Try to extract domain from homepage
    if homepage:
        domain = extract_domain(homepage)
        if domain:
            favicon_url = generate_logodev_url(domain)
            if validate_url(favicon_url, verbose=False):
                result['favicon'] = favicon_url
                return result
    
    # If homepage didn't work, try stream URL domain
    if not result['favicon'] and stream_url:
        domain = extract_domain(stream_url)
        if domain:
            favicon_url = generate_logodev_url(domain)
            if validate_url(favicon_url, verbose=False):
                result['favicon'] = favicon_url
                return result
    
    return result

def main():
    country_code = os.environ.get('COUNTRY_CODE')
    
    if not country_code:
        print("Error: COUNTRY_CODE environment variable not set")
        sys.exit(1)
    
    print(f"Generating favicons with logo.dev for country: {country_code}")
    
    # Fetch stations from API
    api_url = f"https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/{country_code}"
    print(f"Fetching stations from: {api_url}")
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        stations = response.json()
    except Exception as e:
        print(f"Error fetching stations: {e}")
        sys.exit(1)
    
    print(f"Found {len(stations)} stations")
    print("=" * 80)
    
    # Process each station
    results = []
    start_time = time.time()
    success_count = 0
    failed_count = 0
    
    for i, station in enumerate(stations, 1):
        result = process_station(station)
        results.append(result)
        
        # Track success/failure
        if result['favicon']:
            success_count += 1
        else:
            failed_count += 1
        
        # Show progress summary every 50 stations or at the end
        if i % 50 == 0 or i == len(stations):
            percentage = (i / len(stations)) * 100
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(stations) - i) * avg_time
            eta = datetime.now() + timedelta(seconds=remaining)
            
            print(f"[{i}/{len(stations)}] {percentage:.1f}% | ✓ {success_count} | ✗ {failed_count} | {timedelta(seconds=int(elapsed))} elapsed", flush=True)
        
        # Small delay to avoid overwhelming servers
        time.sleep(0.1)
    
    # Filter out stations without favicons
    results_with_favicon = [r for r in results if r['favicon']]
    
    # Save results (only stations with favicons)
    output_dir = "radio/stations/favicons_logodev"
    os.makedirs(output_dir, exist_ok=True)
    
    country_lower = country_code.lower()
    output_file = os.path.join(output_dir, country_lower)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_with_favicon, f, ensure_ascii=False, indent=4)
    
    # Final statistics
    total_time = time.time() - start_time
    with_favicon = len(results_with_favicon)
    without_favicon = len(results) - with_favicon
    
    print(f"\n{'='*80}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"  📁 File: {output_file}")
    print(f"  📊 Total stations processed: {len(results)}")
    print(f"  ✓ Saved with favicon: {with_favicon} ({(with_favicon/len(results))*100:.1f}%)")
    print(f"  ✗ Excluded (no favicon): {without_favicon} ({(without_favicon/len(results))*100:.1f}%)")
    print(f"  ⏱️  Total time: {timedelta(seconds=int(total_time))}")
    print(f"  ⚡ Avg time/station: {total_time/len(results):.2f}s")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
