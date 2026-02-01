#!/usr/bin/env python3
"""
Quick test script to verify Foreplay API connectivity
"""

import requests
from datetime import datetime, timedelta

FOREPLAY_API_KEY = 'ZW3RDgCTZyNmrht0aFe3foC9Wocg0XWLzNXnWOmZ0WeeEtQ7hyOcPcPcPNUlVi_8UHBX4ur3r7KNbjHIhEuUmO-Q'
BASE_URL = 'https://public.api.foreplay.co'

headers = {
    'Authorization': FOREPLAY_API_KEY,
}

print("Testing Foreplay API Connection...")
print("=" * 60)

# Test 1: Search for a brand
print("\n1. Testing brand search for 'Hims'...")
response = requests.get(
    f"{BASE_URL}/api/discovery/brands",
    headers=headers,
    params={'query': 'Hims', 'limit': 5}
)

print(f"   Status: {response.status_code}")
print(f"   Credits Remaining: {response.headers.get('X-Credits-Remaining', 'N/A')}")
print(f"   Credit Cost: {response.headers.get('X-Credit-Cost', 'N/A')}")

if response.status_code == 200:
    data = response.json()
    brands = data.get('data', [])
    print(f"   Found {len(brands)} brands")

    if brands:
        brand = brands[0]
        print(f"\n   First match:")
        print(f"     - Name: {brand.get('name')}")
        print(f"     - ID: {brand.get('id')}")
        print(f"     - Category: {brand.get('category')}")

        # Test 2: Get ads for this brand
        brand_id = brand.get('id')
        print(f"\n2. Testing ad fetch for brand ID {brand_id}...")

        response = requests.get(
            f"{BASE_URL}/api/brand/getAdsByBrandId",
            headers=headers,
            params={'brand_id': brand_id, 'limit': 10, 'offset': 0}
        )

        print(f"   Status: {response.status_code}")
        print(f"   Credits Remaining: {response.headers.get('X-Credits-Remaining', 'N/A')}")
        print(f"   Credit Cost: {response.headers.get('X-Credit-Cost', 'N/A')}")

        if response.status_code == 200:
            ad_data = response.json()
            ads = ad_data.get('data', [])
            print(f"   Found {len(ads)} ads")

            if ads:
                # Check for recent ads
                cutoff = datetime.utcnow() - timedelta(days=7)
                recent_count = 0

                print(f"\n   Sample ads:")
                for i, ad in enumerate(ads[:3]):
                    started = ad.get('started_running')
                    if started:
                        ad_date = datetime.fromtimestamp(started / 1000)
                        is_recent = ad_date >= cutoff
                        if is_recent:
                            recent_count += 1

                        print(f"\n   Ad {i+1}:")
                        print(f"     - Name: {ad.get('name', 'N/A')[:60]}")
                        print(f"     - Format: {ad.get('display_format', 'N/A')}")
                        print(f"     - Started: {ad_date.strftime('%Y-%m-%d')}")
                        print(f"     - Recent (last 7d): {'✓' if is_recent else '✗'}")
                        print(f"     - Platforms: {', '.join(ad.get('publisher_platform', []))}")

                print(f"\n   Total ads from last 7 days: {recent_count}/{len(ads)}")
else:
    print(f"   Error: {response.text}")

print("\n" + "=" * 60)
print("API Test Complete!")
print("=" * 60)
