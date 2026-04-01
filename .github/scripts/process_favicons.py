#!/usr/bin/env python3
import os
import sys
import json
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta

def validate_url(url, timeout=5, verbose=False):
    """Validate if a URL is accessible and returns a valid response."""
    if not url or url.strip() == "":
        if verbose:
            print(f"    ⚠️  URL is empty or None")
        return False
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code >= 400:
            if verbose:
                print(f"    ❌ HEAD request failed with status {response.status_code}")
            return False
        if verbose:
            print(f"    ✓ HEAD request successful (status {response.status_code})")
        return True
    except Exception as e:
        if verbose:
            print(f"    ⚠️  HEAD request failed ({type(e).__name__}), trying GET...")
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            if response.status_code >= 400:
                if verbose:
                    print(f"    ❌ GET request failed with status {response.status_code}")
                return False
            if verbose:
                print(f"    ✓ GET request successful (status {response.status_code})")
            return True
        except Exception as e2:
            if verbose:
                print(f"    ❌ GET request failed: {type(e2).__name__}")
            return False

def is_streaming_url(url):
    """Check if URL is likely a streaming URL."""
    streaming_extensions = ['.mp3', '.aac', '.m3u', '.m3u8', '.pls', '.ogg', '.flac', '.wav']
    streaming_keywords = ['/stream', '/listen', '/radio', '/live']
    
    url_lower = url.lower()
    
    # Check for streaming file extensions
    for ext in streaming_extensions:
        if ext in url_lower:
            return True
    
    # Check for common streaming keywords in path
    parsed = urlparse(url)
    path = parsed.path.lower()
    for keyword in streaming_keywords:
        if keyword in path and not path.endswith('.html') and not path.endswith('/'):
            return True
    
    return False

def find_favicon_from_homepage(homepage_url):
    """Try to find a favicon from the homepage."""
    if not homepage_url or homepage_url.strip() == "":
        return None
    
    # Skip if URL looks like a streaming URL
    if is_streaming_url(homepage_url):
        print(f"  ⚠️  Skipping streaming URL: {homepage_url}")
        return None
    
    try:
        # Use shorter timeout and stream=True to detect content type early
        response = requests.get(
            homepage_url, 
            timeout=3,  # Reduced timeout
            stream=True,  # Stream to check headers first
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            allow_redirects=True
        )
        
        if response.status_code != 200:
            return None
        
        # Check Content-Type to avoid processing audio streams
        content_type = response.headers.get('Content-Type', '').lower()
        if any(t in content_type for t in ['audio/', 'video/', 'application/octet-stream']):
            print(f"  ⚠️  Skipping non-HTML content: {content_type}")
            return None
        
        # Only download content if it's HTML
        if 'text/html' not in content_type and 'text/' not in content_type:
            print(f"  ⚠️  Unexpected content type: {content_type}")
            return None
        
        # Download the actual content with size limit
        content = b''
        max_size = 1024 * 1024  # 1MB limit
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size:
                print(f"  ⚠️  Content too large, skipping")
                return None
        
        soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
        
        # Try to find favicon in various ways
        # 1. Look for <link rel="icon">
        icon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if icon_link and icon_link.get('href'):
            favicon_url = urljoin(homepage_url, icon_link['href'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
        # 2. Look for <link rel="shortcut icon">
        shortcut_icon = soup.find('link', rel='shortcut icon')
        if shortcut_icon and shortcut_icon.get('href'):
            favicon_url = urljoin(homepage_url, shortcut_icon['href'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
        # 3. Try default /favicon.ico
        parsed_url = urlparse(homepage_url)
        default_favicon = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        if validate_url(default_favicon, verbose=True):
            return default_favicon
        
        # 4. Look for apple-touch-icon
        apple_icon = soup.find('link', rel=lambda x: x and 'apple-touch-icon' in x.lower())
        if apple_icon and apple_icon.get('href'):
            favicon_url = urljoin(homepage_url, apple_icon['href'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
        # 5. Look for twitter:image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            favicon_url = urljoin(homepage_url, twitter_image['content'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
        # 6. Look for og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            favicon_url = urljoin(homepage_url, og_image['content'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
        # 7. Look for manifest.json
        manifest_link = soup.find('link', rel='manifest')
        if manifest_link and manifest_link.get('href'):
            try:
                manifest_url = urljoin(homepage_url, manifest_link['href'])
                manifest_response = requests.get(manifest_url, timeout=3)
                if manifest_response.status_code == 200:
                    manifest_data = manifest_response.json()
                    if 'icons' in manifest_data and len(manifest_data['icons']) > 0:
                        # Get the largest icon
                        largest_icon = max(manifest_data['icons'], key=lambda x: int(x.get('sizes', '0x0').split('x')[0]) if 'sizes' in x else 0)
                        if 'src' in largest_icon:
                            favicon_url = urljoin(homepage_url, largest_icon['src'])
                            if validate_url(favicon_url, verbose=True):
                                return favicon_url
            except:
                pass
        
        # 8. Try different apple-touch-icon sizes
        for size in ['180x180', '152x152', '144x144', '120x120', '114x114', '76x76', '72x72', '60x60', '57x57']:
            apple_icon_sized = soup.find('link', rel=f'apple-touch-icon-{size}')
            if apple_icon_sized and apple_icon_sized.get('href'):
                favicon_url = urljoin(homepage_url, apple_icon_sized['href'])
                if validate_url(favicon_url, verbose=True):
                    return favicon_url
        
        # 9. Look for any image in the header/logo area
        header_logo = soup.find(['img'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['logo', 'brand', 'header']))
        if header_logo and header_logo.get('src'):
            favicon_url = urljoin(homepage_url, header_logo['src'])
            if validate_url(favicon_url, verbose=True):
                return favicon_url
        
    except requests.Timeout:
        print(f"  ⏱️  Timeout accessing homepage: {homepage_url}")
    except requests.RequestException as e:
        print(f"  ❌ Request error for homepage {homepage_url}: {type(e).__name__}")
    except Exception as e:
        print(f"  ❌ Error finding favicon from homepage {homepage_url}: {type(e).__name__}")
    
    return None

def find_favicon_external_services(station_name, homepage_url):
    """Try external favicon services as fallback."""
    if not homepage_url or homepage_url.strip() == "":
        return None
    
    try:
        parsed_url = urlparse(homepage_url)
        domain = parsed_url.netloc
        
        if not domain:
            return None
        
        # 1. Try DuckDuckGo favicon service (often better quality)
        print(f"    → Trying DuckDuckGo favicon service")
        ddg_favicon = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
        if validate_url(ddg_favicon, verbose=True):
            return ddg_favicon
        
        # 2. Try Clearbit Logo API
        print(f"    → Trying Clearbit Logo API")
        clearbit_logo = f"https://logo.clearbit.com/{domain}"
        if validate_url(clearbit_logo, verbose=True):
            return clearbit_logo
        
        # 3. Try Google's favicon service
        print(f"    → Trying Google favicon service")
        google_favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=512"
        if validate_url(google_favicon, verbose=True):
            return google_favicon
        
        # 4. Try Favicon Kit
        print(f"    → Trying Favicon Kit")
        faviconkit = f"https://api.faviconkit.com/{domain}/512"
        if validate_url(faviconkit, verbose=True):
            return faviconkit
        
    except Exception as e:
        print(f"    ⚠️  Error with external services: {type(e).__name__}")
    
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
    if favicon:
        print(f"  → Validating existing favicon: {favicon}")
        if validate_url(favicon, verbose=True):
            result['favicon'] = favicon
            print(f"✓ Valid favicon for {name}")
            return result
        else:
            print(f"✗ Existing favicon is invalid or unreachable")
    else:
        print(f"✗ No favicon provided in API data for {name}")
    
    # Step 2: Try to find favicon from homepage
    if homepage:
        print(f"  → Searching favicon from homepage: {homepage}")
        found_favicon = find_favicon_from_homepage(homepage)
        if found_favicon:
            result['favicon'] = found_favicon
            print(f"  ✓ Found favicon from homepage: {found_favicon}")
            return result
    
    # Step 3: Try external favicon services
    if homepage:
        print(f"  → Trying external favicon services")
        external_favicon = find_favicon_external_services(name, homepage)
        if external_favicon:
            result['favicon'] = external_favicon
            print(f"  ✓ Found favicon via external service: {external_favicon}")
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
            
            # Try external services with stream domain
            external_favicon = find_favicon_external_services(name, domain_url)
            if external_favicon:
                result['favicon'] = external_favicon
                print(f"  ✓ Found favicon via external service (stream domain): {external_favicon}")
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
    print("=" * 80)
    
    # Process each station
    results = []
    start_time = time.time()
    success_count = 0
    failed_count = 0
    
    for i, station in enumerate(stations, 1):
        station_name = station.get('name', 'Unknown')
        
        # Progress header
        percentage = (i / len(stations)) * 100
        print(f"\n{'='*80}")
        print(f"[{i}/{len(stations)}] ({percentage:.1f}%) Processing: {station_name}")
        print(f"{'='*80}")
        
        result = process_station(station)
        results.append(result)
        
        # Track success/failure
        if result['favicon']:
            success_count += 1
        else:
            failed_count += 1
        
        # Show progress summary every 10 stations or at the end
        if i % 10 == 0 or i == len(stations):
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(stations) - i) * avg_time
            eta = datetime.now() + timedelta(seconds=remaining)
            
            print(f"\n{'─'*80}")
            print(f"📊 PROGRESS SUMMARY")
            print(f"{'─'*80}")
            print(f"  Processed: {i}/{len(stations)} ({percentage:.1f}%)")
            print(f"  ✓ Success: {success_count} ({(success_count/i)*100:.1f}%)")
            print(f"  ✗ Failed:  {failed_count} ({(failed_count/i)*100:.1f}%)")
            print(f"  ⏱️  Elapsed: {timedelta(seconds=int(elapsed))}")
            if i < len(stations):
                print(f"  ⏳ Remaining: ~{timedelta(seconds=int(remaining))}")
                print(f"  🎯 ETA: {eta.strftime('%H:%M:%S')}")
            print(f"{'─'*80}\n")
        
        # Add a small delay to avoid overwhelming servers
        time.sleep(0.5)
    
    # Filter out stations without favicons
    results_with_favicon = [r for r in results if r['favicon']]
    
    # Save results (only stations with favicons)
    output_dir = "radio/stations/favicons"
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
