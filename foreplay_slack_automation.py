#!/usr/bin/env python3
"""
Foreplay to Slack - MAXIMUM CREDIT EFFICIENCY
Only 3 ads per brand = ~15 credits per run (was 2,250!)
Format: Brand → 2 ad links + 1 copy sample
"""

import os, requests, json, time, random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set
from pathlib import Path

FOREPLAY_API_KEY = os.environ["FOREPLAY_API_KEY"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
FOREPLAY_BASE_URL = 'https://public.api.foreplay.co'

TRACKED_BRANDS = [
    'AG1',
    'ARMRA',
    'Auri Nutrition',
    'BOOM Beauty',
    'CarMax',
    'Carvana',
    'Curology',
    'Dossier',
    'Eadem',
    'fatty15',
    'hims',
    'ILIA Beauty',
    'IM8',
    'Jones Road Beauty',
    'Lumin',
    'MAËLYS Cosmetics',
    'Magic Spoon Cereal',
    'MaryRuth\'s',
    'Mejuri',
    'MUD\\WTR',
    'Nood',
    'Peddle',
    'Prose',
    'Pura Vida',
    'Qure Skincare',
    'rhode',
    'Ritual',
    'Seed',
    'Shibumi Shade',
    'SKIMS',
    'True Classic',
    'YETI'
]
DAYS_LOOKBACK = 7
POSTED_ADS_FILE = Path(__file__).parent / 'posted_ads.json'
API_FETCH_LIMIT = 10  # Fetch 10 to ensure we find ads with visuals (skip DCO/text-only)

# Weekly inspirational messages to energize designers
INSPO_MESSAGES = [
    "Your mood board is crying. Fix it with this week's inspo 💅",
    "Imagine launching something mid. Couldn't be you after this 🎯",
    "Weekly creative fuel incoming. You're about to be unstoppable 🎨",
    "This week's ads hit different. In the best way 💎",
    "Plot twist: Your next breakthrough idea is probably in here ✨",
    "The good stuff just landed. Time to raise your own bar 🔥",
    "The brands that get it just dropped gold. Let's study 📚",
    "Your brain is about to be very happy with what's coming 💅",
    "Fresh creative just dropped. Consider yourself ahead of the curve 👀",
    "New week, new level unlocked. Ready when you are ⚡",
    "Monday energy: Let's make something people actually want to see 💫",
    "This week's lineup is chef's kiss. Dig in 👩‍🍳",
    "Consider this your secret weapon for the week ahead 🗡️",
    "The algorithm gods have blessed us. Don't waste it 🙏",
    "Warning: These ads might make you rethink everything. Proceed ✨"
]

class DeduplicationStore:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.posted_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    return set(json.load(f).get('posted_ad_ids', []))
            except: return set()
        return set()

    def _save(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump({'posted_ad_ids': list(self.posted_ids), 'last_updated': datetime.now(timezone.utc).isoformat()}, f, indent=2)
        except: pass

    def is_posted(self, ad_id: str) -> bool:
        return ad_id in self.posted_ids

    def mark_batch_posted(self, ad_ids: List[str]):
        self.posted_ids.update(ad_ids)
        self._save()


class ForeplayAPI:
    def __init__(self, api_key: str):
        self.headers = {'Authorization': api_key}

    def _request(self, endpoint: str, params: dict) -> dict:
        try:
            r = requests.get(f'{FOREPLAY_BASE_URL}{endpoint}', headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            print(f"Credits: {r.headers.get('X-Credits-Remaining', '?')} | Cost: {r.headers.get('X-Credit-Cost', '?')}")
            return r.json()
        except: return {'data': []}

    def get_recent_ads(self, brand_names: List[str], days_back: int, dedup: DeduplicationStore, target_brands: int = 5) -> Dict[str, List[Dict]]:
        """
        Randomly check brands until we have target_brands with new ads.
        This saves credits by not checking all brands every time.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        results = {}

        # Randomize brand order
        remaining_brands = brand_names.copy()
        random.shuffle(remaining_brands)

        print(f"\nTarget: Find {target_brands} brands with new ads")
        print(f"Total brands available: {len(remaining_brands)}")

        while len(results) < target_brands and remaining_brands:
            brand = remaining_brands.pop(0)
            print(f"\nSearching: {brand}")
            brands = self._request('/api/discovery/brands', {'query': brand, 'limit': 1}).get('data', [])
            if not brands: continue
            
            brand_id = brands[0]['id']
            print(f"  Found: {brands[0]['name']}")
            
            # Only fetch 3 ads to minimize credits!
            ads = self._request('/api/spyder/brand/ads', {'brand_id': brand_id, 'limit': API_FETCH_LIMIT}).get('data', [])
            print(f"  Retrieved: {len(ads)} ads")
            
            recent = []
            skipped_dedup = 0
            skipped_country = 0
            skipped_date = 0

            for ad in ads:
                ad_id = ad.get('id')

                # Check dedup
                if dedup.is_posted(ad_id):
                    skipped_dedup += 1
                    continue

                # Filter: USA only
                countries = ad.get('countries', [])
                if countries and 'US' not in countries and 'USA' not in countries:
                    skipped_country += 1
                    print(f"    Skipped (non-US): {ad_id[:8]}... countries={countries}")
                    continue

                # Check date
                ts = ad.get('started_running')
                if ts and datetime.fromtimestamp(ts/1000, tz=timezone.utc) >= cutoff:
                    recent.append(ad)
                else:
                    skipped_date += 1

            print(f"  Filtered: {skipped_dedup} already posted, {skipped_country} non-US, {skipped_date} too old")
            
            if recent:
                recent.sort(key=lambda x: (bool(x.get('video')), x.get('started_running', 0)), reverse=True)
                results[brand] = recent[:3]  # Max 3
                print(f"  New ads: {len(results[brand])}")
            
            time.sleep(0.5)

        print(f"\n🎯 Found {len(results)} brands with new ads (checked {len(brand_names) - len(remaining_brands)} total)")
        return results


class SlackPoster:
    def __init__(self, webhook: str):
        self.webhook = webhook

    def post_weekly_inspiration(self, ads_by_brand: Dict[str, List[Dict]]):
        """Simple format: Brand + visuals + copy sample"""
        # Pick a random inspirational message
        inspo_message = random.choice(INSPO_MESSAGES)

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "✨ Creative Inspo of the Week"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"_{inspo_message}_"}},
            {"type": "divider"}
        ]

        for brand, ads in sorted(ads_by_brand.items()):
            # Pre-check: Does this brand have anything to show?
            has_visuals = any((ad.get('thumbnail') or ad.get('video') or ad.get('image')) for ad in ads)
            has_copy = any(((ad.get('headline') or '').strip() or (ad.get('description') or '').strip()) for ad in ads)

            if not has_visuals and not has_copy:
                # Skip brands with no displayable content
                continue

            blocks.append({"type": "divider"})

            # Brand header
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{brand}*"}
            })

            # Show up to 2 ads that have actual visuals (prioritize visual ads)
            visuals_shown = 0
            for ad in ads:
                if visuals_shown >= 2:
                    break

                # Get media URLs
                thumbnail = ad.get('thumbnail')
                video = ad.get('video')
                image = ad.get('image')
                media = thumbnail or video or image

                if not media:
                    continue  # Skip ads without visuals

                fmt = ad.get('display_format', 'Ad')

                # Show thumbnail/image inline
                blocks.append({
                    "type": "image",
                    "image_url": media,
                    "alt_text": f"{brand} {fmt}"
                })

                # Add clickable link to video if available
                if video:
                    blocks.append({
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": f"<{video}|▶️ Watch Video> • _{fmt}_"}]
                    })
                else:
                    blocks.append({
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": f"_{fmt}_"}]
                    })

                visuals_shown += 1

            # Show copy sample if available
            for ad in ads:
                headline = (ad.get('headline') or '').strip()
                desc = (ad.get('description') or '').strip()
                cta = (ad.get('cta_title') or '').strip()

                # Build copy text if available
                if headline or desc:
                    copy_text = ""
                    if headline: copy_text += f"_{headline}_\n"
                    if desc: copy_text += (desc[:180] + "..." if len(desc) > 180 else desc)
                    if cta: copy_text += f"\n*CTA:* {cta}"

                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Copy Sample:*\n{copy_text}"}
                    })

                break  # Only 1 copy sample per brand

        # Footer
        total_brands = len(ads_by_brand)
        total_ads = sum(len(ads) for ads in ads_by_brand.values())
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_{total_ads} new ads from {total_brands} brands_"}]
        })

        try:
            requests.post(self.webhook, json={"blocks": blocks}, timeout=30).raise_for_status()
            print(f"\n✅ Posted! {total_brands} brands with {total_ads} ads")
            return True
        except Exception as e:
            print(f"\n✗ Failed: {e}")
            return False


def main():
    print("=" * 60)
    print("Foreplay to Slack - MAXIMUM EFFICIENCY")
    print(f"Fetching only {API_FETCH_LIMIT} ads/brand (~15 credits!)")
    print("=" * 60)
    
    dedup = DeduplicationStore(POSTED_ADS_FILE)
    print(f"\nDedup: {len(dedup.posted_ids)} previously posted")
    
    api = ForeplayAPI(FOREPLAY_API_KEY)
    ads_by_brand = api.get_recent_ads(TRACKED_BRANDS, DAYS_LOOKBACK, dedup)
    
    total = sum(len(ads) for ads in ads_by_brand.values())
    print(f"\n{'=' * 60}")
    print(f"Found: {total} new ads across {len(ads_by_brand)} brands")
    print(f"{'=' * 60}")

    if not ads_by_brand:
        print("\nNo new ads from any brands in the lookback period.")
        return 0
    
    slack = SlackPoster(SLACK_WEBHOOK_URL)
    slack.post_weekly_inspiration(ads_by_brand)
    
    all_ids = [ad['id'] for ads in ads_by_brand.values() for ad in ads]
    dedup.mark_batch_posted(all_ids)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Complete! Used minimal credits")
    print(f"{'=' * 60}")
    return 0


if __name__ == '__main__':
    exit(main())
