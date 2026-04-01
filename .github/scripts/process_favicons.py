#!/usr/bin/env python3
import os
import sys
import json
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

def validate_url(url, timeout=10):
    """Validate if a URL is accessible and returns a valid response."""
    if not url or url.strip() == "":
        return False
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code >= 400:
            return False
        return True
    except:
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            if response.status_code >= 400:
                return False
            return True
        except:
            return False

def find_favicon_from_homepage(homepage_url):
    """Try to find a favicon from the homepage."""
    if not homepage_url or homepage_url.strip() == "":
        return None
    
    try:
        response = requests.get(homepage_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find favicon in various ways
        # 1. Look for <link rel="icon">
        icon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if icon_link and icon_link.get('href'):
            favicon_url = urljoin(homepage_url, icon_link['href'])
            if validate_url(favicon_url):
                return favicon_url
        
        # 2. Look for <link rel="shortcut icon">
        shortcut_icon = soup.find('link', rel='shortcut icon')
        if shortcut_icon and shortcut_icon.get('href'):
            favicon_url = urljoin(homepage_url, shortcut_icon['href'])
            if validate_url(favicon_url):
                return favicon_url
        
        # 3. Try default /favicon.ico
        parsed_url = urlparse(homepage_url)
        default_favicon = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        if validate_url(default_favicon):
            return default_favicon
        
        # 4. Look for apple-touch-icon
        apple_icon = soup.find('link', rel=lambda x: x and 'apple-touch-icon' in x.lower())
        if apple_icon and apple_icon.get('href'):
            favicon_url = urljoin(homepage_url, apple_icon['href'])
            if validate_url(favicon_url):
                return favicon_url
        
        # 5. Look for og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            favicon_url = urljoin(homepage_url, og_image['content'])
            if validate_url(favicon_url):
                return favicon_url
        
    except Exception as e:
        print(f"Error finding favicon from homepage {homepage_url}: {e}")
    
    return None

def find_favicon_google(station_name, homepage_url):
    """Use Google's favicon service as a fallback."""
    if not homepage_url or homepage_url.strip() == "":
        return None
    
    try:
        parsed_url = urlparse(homepage_url)
        domain = parsed_url.netloc
        
        # Google's favicon service
        google_favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
        if validate_url(google_favicon):
            return google_favicon
    except:
        pass
    
    return None

def process_station(station):
    """Process a single station and validate/find its favicon."""
    name = station.get('name', '').strip()
    url = station.get('url', '').strip()
    url_resolved = station.get('url_resolved', url).strip()
    favicon = station.get('favicon', '').strip()
    homepage = station.get('homepage', '').strip()
    
    # Use url_resolved if available, otherwise use url
    stream_url = url_resolved if url_resolved else url
    
    result = {
        'name': name,
        'url': stream_url,
        'favicon': None
    }
    
    # Step 1: Validate existing favicon
    if favicon and validate_url(favicon):
        result['favicon'] = favicon
        print(f"✓ Valid favicon for {name}: {favicon}")
        return result
    
    print(f"✗ Invalid or missing favicon for {name}")
    
    # Step 2: Try to find favicon from homepage
    if homepage:
        print(f"  → Searching favicon from homepage: {homepage}")
        found_favicon = find_favicon_from_homepage(homepage)
        if found_favicon:
            result['favicon'] = found_favicon
            print(f"  ✓ Found favicon from homepage: {found_favicon}")
            return result
    
    # Step 3: Try Google's favicon service
    if homepage:
        print(f"  → Trying Google favicon service")
        google_favicon = find_favicon_google(name, homepage)
        if google_favicon:
            result['favicon'] = google_favicon
            print(f"  ✓ Found favicon via Google: {google_favicon}")
            return result
    
    # Step 4: If still no favicon, try to extract domain from stream URL
    if not result['favicon'] and stream_url:
        try:
            parsed = urlparse(stream_url)
            domain_url = f"{parsed.scheme}://{parsed.netloc}"
            print(f"  → Trying to find favicon from stream domain: {domain_url}")
            found_favicon = find_favicon_from_homepage(domain_url)
            if found_favicon:
                result['favicon'] = found_favicon
                print(f"  ✓ Found favicon from stream domain: {found_favicon}")
                return result
            
            # Try Google service with stream domain
            google_favicon = find_favicon_google(name, domain_url)
            if google_favicon:
                result['favicon'] = google_favicon
                print(f"  ✓ Found favicon via Google (stream domain): {google_favicon}")
                return result
        except:
            pass
    
    print(f"  ✗ Could not find valid favicon for {name}")
    return result

def main():
    country_code = os.environ.get('COUNTRY_CODE')
    
    if not country_code:
        print("Error: COUNTRY_CODE environment variable not set")
        sys.exit(1)
    
    print(f"Processing favicons for country: {country_code}")
    
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
    
    # Process each station
    results = []
    for i, station in enumerate(stations, 1):
        print(f"\n[{i}/{len(stations)}] Processing: {station.get('name', 'Unknown')}")
        result = process_station(station)
        results.append(result)
        
        # Add a small delay to avoid overwhelming servers
        time.sleep(0.5)
    
    # Save results
    output_dir = "radio/stations/favicons"
    os.makedirs(output_dir, exist_ok=True)
    
    country_lower = country_code.lower()
    output_file = os.path.join(output_dir, country_lower)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ Results saved to: {output_file}")
    print(f"Total stations processed: {len(results)}")
    
    # Statistics
    with_favicon = sum(1 for r in results if r['favicon'])
    without_favicon = len(results) - with_favicon
    print(f"Stations with favicon: {with_favicon}")
    print(f"Stations without favicon: {without_favicon}")

if __name__ == '__main__':
    main()
