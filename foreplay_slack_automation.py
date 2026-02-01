#!/usr/bin/env python3
"""
Foreplay to Slack Automation
Fetches new ads from trusted brands and posts them to Slack #creative channel
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import time
from pathlib import Path

# Configuration - FAIL HARD if secrets missing
FOREPLAY_API_KEY = os.environ["FOREPLAY_API_KEY"]  # No fallback - will raise KeyError if missing
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]  # No fallback - will raise KeyError if missing

FOREPLAY_BASE_URL = 'https://public.api.foreplay.co'
SLACK_CHANNEL_ID = 'C01J7SM5NQP'  # #creative channel

# Brands to track
TRACKED_BRANDS = [
    'IM8',
    'Eadem',
    'Armra',
    'Fatty15',
    'Seed',
    'True Classic',
    'Magic Spoon Cereal',
    'Hims',
    'AG1'
]

# Days to look back for new ads
DAYS_LOOKBACK = 7

# Deduplication file
POSTED_ADS_FILE = Path(__file__).parent / 'posted_ads.json'

# UX controls
MAX_ADS_PER_BRAND = 10  # Cap to prevent channel spam
GROUP_ADS_BY_BRAND = True  # Group multiple ads per brand into one message


class DeduplicationStore:
    """Track which ads have already been posted"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.posted_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        """Load posted ad IDs from file"""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    return set(data.get('posted_ad_ids', []))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load deduplication file: {e}")
                return set()
        return set()

    def _save(self):
        """Save posted ad IDs to file"""
        try:
            data = {
                'posted_ad_ids': list(self.posted_ids),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save deduplication file: {e}")

    def is_posted(self, ad_id: str) -> bool:
        """Check if ad has been posted"""
        return ad_id in self.posted_ids

    def mark_posted(self, ad_id: str):
        """Mark ad as posted"""
        self.posted_ids.add(ad_id)
        self._save()

    def mark_batch_posted(self, ad_ids: List[str]):
        """Mark multiple ads as posted"""
        self.posted_ids.update(ad_ids)
        self._save()


class ForeplayAPI:
    """Wrapper for Foreplay API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = FOREPLAY_BASE_URL
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            # Log credit usage
            credits_remaining = response.headers.get('X-Credits-Remaining', 'N/A')
            credit_cost = response.headers.get('X-Credit-Cost', 'N/A')
            print(f"Credits remaining: {credits_remaining} | Cost: {credit_cost}")

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {'data': [], 'metadata': {'success': False}}

    def search_brands(self, brand_name: str) -> List[Dict]:
        """Search for brands by name"""
        params = {
            'query': brand_name,
            'limit': 10
        }
        result = self._make_request('/api/discovery/brands', params)
        return result.get('data', [])

    def get_brand_ads(self, brand_id: str, limit: int = 250) -> List[Dict]:
        """Get ads for a specific brand"""
        params = {
            'brand_id': brand_id,
            'limit': limit,
            'offset': 0
        }
        result = self._make_request('/api/brand/getAdsByBrandId', params)
        return result.get('data', [])

    def get_recent_ads_for_brands(
        self,
        brand_names: List[str],
        days_back: int = 7,
        dedup_store: Optional[DeduplicationStore] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get recent ads for multiple brands, organized by brand
        Returns: Dict mapping brand_name -> list of ads
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        ads_by_brand = {}

        for brand_name in brand_names:
            print(f"\nSearching for brand: {brand_name}")

            # Find the brand
            brands = self.search_brands(brand_name)
            if not brands:
                print(f"  No brand found for: {brand_name}")
                continue

            # Use first matching brand
            brand = brands[0]
            brand_id = brand.get('id')
            print(f"  Found brand ID: {brand_id} - {brand.get('name')}")

            # Get ads for this brand
            ads = self.get_brand_ads(brand_id)
            print(f"  Retrieved {len(ads)} total ads")

            # Filter for recent ads and deduplicate
            recent_ads = []
            for ad in ads:
                ad_id = ad.get('id')

                # Skip if already posted
                if dedup_store and dedup_store.is_posted(ad_id):
                    continue

                started_running = ad.get('started_running')
                if started_running:
                    # Parse the timestamp (Unix timestamp in milliseconds)
                    ad_date = datetime.fromtimestamp(started_running / 1000)
                    if ad_date >= cutoff_date:
                        ad['brand_name'] = brand.get('name')
                        recent_ads.append(ad)

            # Cap per brand to prevent spam
            if len(recent_ads) > MAX_ADS_PER_BRAND:
                print(f"  ⚠ Capping {len(recent_ads)} ads to {MAX_ADS_PER_BRAND} for channel health")
                recent_ads = recent_ads[:MAX_ADS_PER_BRAND]

            print(f"  Found {len(recent_ads)} new ads from last {days_back} days")

            if recent_ads:
                ads_by_brand[brand_name] = recent_ads

            # Small delay to be respectful to API
            time.sleep(0.5)

        return ads_by_brand


class SlackPoster:
    """Handle posting to Slack"""

    def __init__(self, webhook_url: str, channel_id: str = None):
        self.webhook_url = webhook_url
        self.channel_id = channel_id

    def format_grouped_brand_message(self, brand_name: str, ads: List[Dict]) -> Dict:
        """Format multiple ads from one brand into a single message"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 {brand_name} - {len(ads)} New Ad{'s' if len(ads) > 1 else ''}",
                    "emoji": True
                }
            }
        ]

        for i, ad in enumerate(ads):
            ad_name = ad.get('name', 'Untitled Ad')
            description = ad.get('description', '')
            headline = ad.get('headline', '')
            cta = ad.get('cta_title', '')
            platforms = ', '.join(ad.get('publisher_platform', []))
            thumbnail = ad.get('thumbnail', '')
            video_url = ad.get('video', '')
            image_url = ad.get('image', '')
            link_url = ad.get('link_url', '')
            display_format = ad.get('display_format', 'Unknown')

            # Add divider between ads (except first)
            if i > 0:
                blocks.append({"type": "divider"})

            # Ad title
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i+1}. {ad_name}*"
                }
            })

            # Add thumbnail/image
            media_url = thumbnail or video_url or image_url
            if media_url:
                blocks.append({
                    "type": "image",
                    "image_url": media_url,
                    "alt_text": ad_name
                })

            # Add details
            details_text = ""
            if headline:
                details_text += f"*Headline:* {headline}\n"
            if description and len(description) < 200:  # Avoid giant descriptions
                details_text += f"*Description:* {description}\n"
            if cta:
                details_text += f"*CTA:* {cta}\n"
            if platforms:
                details_text += f"*Platform:* {platforms}\n"
            if display_format:
                details_text += f"*Format:* {display_format}\n"

            # Video duration
            video_duration = ad.get('video_duration', '')
            if video_duration:
                details_text += f"*Duration:* {video_duration}s\n"

            # Start date
            started_running = ad.get('started_running')
            if started_running:
                start_date = datetime.fromtimestamp(started_running / 1000)
                details_text += f"*Started:* {start_date.strftime('%Y-%m-%d')}\n"

            if details_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": details_text
                    }
                })

            # Add link button if available
            if link_url:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Landing Page",
                                "emoji": True
                            },
                            "url": link_url
                        }
                    ]
                })

        blocks.append({"type": "divider"})

        return {"blocks": blocks}

    def post_grouped_ads(self, ads_by_brand: Dict[str, List[Dict]]) -> int:
        """Post ads grouped by brand"""
        successful_posts = 0

        for brand_name, ads in ads_by_brand.items():
            if not ads:
                continue

            message = self.format_grouped_brand_message(brand_name, ads)

            try:
                response = requests.post(self.webhook_url, json=message, timeout=30)
                response.raise_for_status()
                successful_posts += len(ads)
                print(f"  ✓ Posted {len(ads)} ads for {brand_name}")
                time.sleep(1)  # Rate limiting
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Failed to post {brand_name}: {e}")

        return successful_posts

    def post_summary(self, total_ads: int, brands_with_ads: List[str]) -> bool:
        """Post summary message"""
        summary_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Weekly Ad Update Complete",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Total new ads:* {total_ads}\n*Brands with new ads:* {', '.join(brands_with_ads) if brands_with_ads else 'None'}"
                }
            }
        ]

        message = {"blocks": summary_blocks}

        try:
            response = requests.post(self.webhook_url, json=message, timeout=30)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to post summary to Slack: {e}")
            return False


def main():
    """Main execution function"""
    print("=" * 60)
    print("Foreplay to Slack Automation")
    print("=" * 60)

    # Validate environment variables
    try:
        api_key = FOREPLAY_API_KEY
        webhook_url = SLACK_WEBHOOK_URL
    except KeyError as e:
        print(f"\n❌ ERROR: Missing required environment variable: {e}")
        print("Set FOREPLAY_API_KEY and SLACK_WEBHOOK_URL before running.")
        return 1

    # Initialize deduplication
    dedup = DeduplicationStore(POSTED_ADS_FILE)
    print(f"\nDeduplication: {len(dedup.posted_ids)} ads previously posted")

    # Initialize API client
    foreplay = ForeplayAPI(api_key)

    # Get recent ads organized by brand
    print(f"\nFetching ads from last {DAYS_LOOKBACK} days for {len(TRACKED_BRANDS)} brands...")
    ads_by_brand = foreplay.get_recent_ads_for_brands(
        TRACKED_BRANDS,
        DAYS_LOOKBACK,
        dedup_store=dedup
    )

    # Calculate totals
    total_ads = sum(len(ads) for ads in ads_by_brand.values())

    print(f"\n{'=' * 60}")
    print(f"Total new (unposted) ads found: {total_ads}")
    print(f"{'=' * 60}")

    if not ads_by_brand:
        print("\nNo new ads found in the specified time period.")
        return 0

    # Initialize Slack poster
    slack = SlackPoster(webhook_url, SLACK_CHANNEL_ID)

    # Post ads to Slack (grouped by brand)
    print("\nPosting ads to Slack...")
    successful_posts = slack.post_grouped_ads(ads_by_brand)

    # Mark all posted ads as complete
    all_posted_ids = [ad['id'] for ads in ads_by_brand.values() for ad in ads]
    dedup.mark_batch_posted(all_posted_ids)

    # Post summary
    brands_with_ads = sorted(list(ads_by_brand.keys()))
    slack.post_summary(successful_posts, brands_with_ads)

    print(f"\n{'=' * 60}")
    print(f"✅ Completed! Posted {successful_posts} ads across {len(brands_with_ads)} brands")
    print(f"{'=' * 60}")

    return 0


if __name__ == '__main__':
    exit(main())
