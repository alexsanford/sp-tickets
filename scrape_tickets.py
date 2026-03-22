#!/usr/bin/env python3
"""
Scrape ticket availability from Acadia University ticketing for Cinderella.
Reports available vs sold seats by section, ticket type, show, and overall.
"""

import asyncio
import argparse
import re
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, Page

BASE_URL = "https://acadiau.universitytickets.com"

# Show event IDs in chronological order
SHOWS = {
    "Fri May 8 7PM": 2677,
    "Sat May 9 2PM": 2683,
    "Sat May 9 7PM": 2684,
    "Sun May 10 2PM": 2685,
    "Fri May 15 7PM": 2686,
    "Sat May 16 2PM": 2687,
    "Sat May 16 7PM": 2688,
    "Sun May 17 2PM": 2689,
}

# Ticket types: which sections they allow, and which dropdown indices to use
# Dropdown order: P1-Adult(0), P1-Youth(1), P2-Adult(2), P2-Youth(3), P3-Adult(4), P3-Youth(5)
TICKET_TYPES = {
    "P1": {"sections": ["SEC-3", "SEC-4"], "dropdowns": [0, 1]},
    "P2": {"sections": ["SEC-2", "SEC-5"], "dropdowns": [2, 3]},
    "P3": {"sections": ["SEC-1", "SEC-6"], "dropdowns": [4, 5]},
}


@dataclass
class SectionStats:
    available: int = 0
    blocked: int = 0  # sold/unavailable
    other: int = 0    # other states (held, etc.)

    @property
    def total(self) -> int:
        return self.available + self.blocked + self.other

    @property
    def sold_pct(self) -> float:
        return (self.blocked / self.total * 100) if self.total > 0 else 0


@dataclass
class ShowStats:
    sections: dict[str, SectionStats] = field(default_factory=dict)
    
    def available_for_type(self, ticket_type: str) -> int:
        info = TICKET_TYPES.get(ticket_type, {})
        sections = info.get("sections", [])
        return sum(self.sections.get(s, SectionStats()).available for s in sections)


async def make_browser() -> Browser:
    """Create browser with Cloudflare bypass settings."""
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    return browser, p


async def new_context(browser: Browser):
    """Create a new context with anti-detection measures (fresh cookies)."""
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
    )
    await context.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined});')
    return context


async def wait_for_cloudflare(page: Page):
    """Wait for Cloudflare challenge to complete."""
    for _ in range(15):
        if 'Just a moment' not in await page.title():
            return
        await asyncio.sleep(1)
    raise Exception("Cloudflare challenge did not complete")


async def scrape_show(browser: Browser, event_id: int) -> ShowStats:
    """Scrape all sections for a single show by iterating through each ticket type."""
    stats = ShowStats()
    context = await new_context(browser)
    page = await context.new_page()
    
    try:
        # Load event page to establish session
        await page.goto(f"{BASE_URL}/w/event.aspx?id={event_id}", timeout=60000)
        await wait_for_cloudflare(page)
        
        # Get all dropdowns
        dropdowns = await page.locator('[id*="dropLimit"]').all()
        
        # Process each ticket type separately (P1, P2, P3)
        for tt_name, tt_info in TICKET_TYPES.items():
            # Reset all dropdowns to 0
            for dd in dropdowns:
                await dd.select_option('0')
            
            # Select only this ticket type's dropdowns
            for idx in tt_info["dropdowns"]:
                if idx < len(dropdowns):
                    await dropdowns[idx].select_option('1')
            
            # Go to section selection page
            await page.locator('#btnSelectSection').click()
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Get the correct ticket_id from the first section link on the page
            first_area = page.locator('area[href*="ticket_id="]').first
            href = await first_area.get_attribute('href') or ""
            match = re.search(r'ticket_id=(\d+)', href)
            ticket_id = match.group(1) if match else "1393"
            
            # Scrape sections for this ticket type
            for section in tt_info["sections"]:
                url = f"{BASE_URL}/w/events/Section.aspx?PackageID=0&event_id={event_id}&ticket_id={ticket_id}&cid=0&class_id=6&totalTix=1&vsection={section}"
                await page.goto(url, timeout=60000)
                await asyncio.sleep(1)
                
                available = await page.locator('.seat_available').count()
                blocked = await page.locator('.seat_blocked').count()
                other = await page.locator('.seat:not(.seat_available):not(.seat_blocked):not(.legend-seat)').count()
                stats.sections[section] = SectionStats(available=available, blocked=blocked, other=other)
            
            # Go back to event page for next ticket type
            await page.goto(f"{BASE_URL}/w/event.aspx?id={event_id}", timeout=60000)
            await asyncio.sleep(1)
            
    finally:
        await context.close()
    
    return stats


def print_report(all_stats: dict[str, ShowStats], verbose: bool):
    """Print the availability report."""
    
    total_available = 0
    total_blocked = 0
    
    print("\n" + "=" * 70)
    print("CINDERELLA TICKET AVAILABILITY REPORT")
    print("=" * 70)
    
    for show_name, stats in all_stats.items():
        show_available = sum(s.available for s in stats.sections.values())
        show_blocked = sum(s.blocked for s in stats.sections.values())
        total_available += show_available
        total_blocked += show_blocked
        
        print(f"\n{show_name}")
        print("-" * 40)
        
        if verbose:
            # Section-level details
            for section in ["SEC-1", "SEC-2", "SEC-3", "SEC-4", "SEC-5", "SEC-6"]:
                s = stats.sections.get(section, SectionStats())
                if s.total > 0:
                    print(f"  {section}: {s.available:3d} available / {s.blocked:3d} sold ({s.sold_pct:5.1f}% sold)")
            print()
        
        # Ticket type summary
        for tt in ["P1", "P2", "P3"]:
            avail = stats.available_for_type(tt)
            secs = TICKET_TYPES[tt]["sections"]
            print(f"  {tt} ({secs[0][-1]}&{secs[1][-1]}): {avail:3d} available")
        
        print(f"  Show total: {show_available} available, {show_blocked} sold")
    
    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)
    total_seats = total_available + total_blocked
    print(f"Total seats across all shows: {total_seats}")
    print(f"Available: {total_available} ({total_available/total_seats*100:.1f}%)")
    print(f"Sold:      {total_blocked} ({total_blocked/total_seats*100:.1f}%)")
    print()


async def main():
    parser = argparse.ArgumentParser(description="Scrape Cinderella ticket availability")
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="Show per-section details for debugging")
    args = parser.parse_args()
    
    browser, playwright = await make_browser()
    all_stats: dict[str, ShowStats] = {}
    
    try:
        for i, (show_name, event_id) in enumerate(SHOWS.items()):
            print(f"Scraping {show_name}... ({i+1}/{len(SHOWS)})", flush=True)
            all_stats[show_name] = await scrape_show(browser, event_id)
    finally:
        await browser.close()
        await playwright.stop()
    
    print_report(all_stats, args.verbose)


if __name__ == "__main__":
    asyncio.run(main())
