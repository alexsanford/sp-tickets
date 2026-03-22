"""
Simpler exploration script that saves page content and analyzes structure.
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def main():
    print("Starting exploration...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to event page
            url = f"{BASE_URL}/w/event.aspx?id={EVENT_ID}"
            print(f"Navigating to: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)  # Wait for JS to execute
            
            print(f"Page loaded: {page.url}")
            print(f"Title: {await page.title()}")
            
            # Save full HTML
            html = await page.content()
            with open('/app/plan/event_page.html', 'w') as f:
                f.write(html)
            print(f"Saved HTML ({len(html)} bytes)")
            
            # Take screenshot
            await page.screenshot(path='/app/plan/event_page.png', full_page=True)
            print("Saved screenshot")
            
            # Find all select elements
            print("\n=== SELECT ELEMENTS ===")
            selects = await page.locator('select').all()
            print(f"Found {len(selects)} select elements")
            for s in selects:
                sid = await s.get_attribute('id')
                sname = await s.get_attribute('name')
                print(f"  - ID: {sid}, Name: {sname}")
            
            # Find all input elements
            print("\n=== INPUT ELEMENTS ===")
            inputs = await page.locator('input[type="button"], input[type="submit"]').all()
            print(f"Found {len(inputs)} button inputs")
            for inp in inputs:
                inp_id = await inp.get_attribute('id')
                inp_val = await inp.get_attribute('value')
                print(f"  - ID: {inp_id}, Value: {inp_val}")
            
            # Find all button elements
            print("\n=== BUTTON ELEMENTS ===")
            buttons = await page.locator('button').all()
            print(f"Found {len(buttons)} button elements")
            for btn in buttons:
                btn_text = await btn.inner_text()
                btn_id = await btn.get_attribute('id')
                print(f"  - ID: {btn_id}, Text: {btn_text[:50]}")
            
            # Look for elements containing "ticket" or "find"
            print("\n=== SEARCHING FOR RELEVANT TEXT ===")
            page_text = await page.inner_text()
            
            # Check for "Find Tickets"
            if 'Find Tickets' in page_text:
                print("Found 'Find Tickets' in page text!")
            if 'GET TICKETS' in page_text:
                print("Found 'GET TICKETS' in page text!")
            
            # Look for ticket type labels
            print("\n=== TICKET TYPE INFO ===")
            rows = await page.locator('tr').all()
            for row in rows[:20]:
                text = await row.inner_text()
                if any(x in text for x in ['P1', 'P2', 'P3', 'Adult', 'Youth', '$']):
                    print(f"  Row: {text[:100]}")
            
            # Check for any dropdowns with "drop" in the id
            print("\n=== DROPDOWN SEARCH ===")
            drop_selects = await page.locator('[id*="drop" i]').all()
            print(f"Found {len(drop_selects)} elements with 'drop' in ID")
            for ds in drop_selects[:10]:
                ds_id = await ds.get_attribute('id')
                ds_tag = await ds.evaluate('el => el.tagName')
                print(f"  - {ds_tag}: {ds_id}")
            
            # Check for any select with "limit" in the id/name
            limit_selects = await page.locator('[id*="limit" i], [name*="limit" i]').all()
            print(f"\nFound {len(limit_selects)} elements with 'limit' in ID/name")
            for ls in limit_selects[:10]:
                ls_id = await ls.get_attribute('id')
                ls_tag = await ls.evaluate('el => el.tagName')
                print(f"  - {ls_tag}: {ls_id}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())
