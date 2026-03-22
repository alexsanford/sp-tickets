"""
Exploration script v2 - more thorough page analysis
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore():
    print("=" * 60)
    print("EXPLORING PAGE STRUCTURE - V2")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = f"{BASE_URL}/w/event.aspx?id={EVENT_ID}"
            print(f"\nNavigating to: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)
            
            print(f"Page loaded: {page.url}")
            print(f"Title: {await page.title()}")
            
            html = await page.content()
            with open('/app/plan/event_page.html', 'w') as f:
                f.write(html)
            print(f"Saved HTML ({len(html)} bytes)")
            
            await page.screenshot(path='/app/plan/event_page.png', full_page=True)
            print("Saved screenshot")
            
            print("\n=== SELECT ELEMENTS ===")
            selects = await page.locator('select').all()
            print(f"Found {len(selects)} select elements")
            for s in selects:
                sid = await s.get_attribute('id')
                sname = await s.get_attribute('name')
                print(f"  - ID: {sid}, Name: {sname}")
            
            print("\n=== INPUT BUTTONS ===")
            inputs = await page.locator('input[type="button"], input[type="submit"]').all()
            print(f"Found {len(inputs)} button inputs")
            for inp in inputs:
                inp_id = await inp.get_attribute('id')
                inp_val = await inp.get_attribute('value')
                print(f"  - ID: {inp_id}, Value: {inp_val}")
            
            print("\n=== BUTTON ELEMENTS ===")
            buttons = await page.locator('button').all()
            print(f"Found {len(buttons)} button elements")
            for btn in buttons:
                btn_text = await btn.inner_text()
                btn_id = await btn.get_attribute('id')
                print(f"  - ID: {btn_id}, Text: {btn_text[:50]}")
            
            print("\n=== PAGE TEXT SEARCH ===")
            page_text = await page.inner_text()
            if 'Find Tickets' in page_text:
                print("Found 'Find Tickets'!")
            if 'GET TICKETS' in page_text:
                print("Found 'GET TICKETS'!")
            
            print("\n=== TICKET ROWS ===")
            rows = await page.locator('tr').all()
            for row in rows[:20]:
                text = await row.inner_text()
                if any(x in text for x in ['P1', 'P2', 'P3', 'Adult', 'Youth', '$']):
                    print(f"  {text[:100]}")
            
            print("\n=== DROPDOWN ELEMENTS ===")
            drops = await page.locator('[id*="drop" i]').all()
            print(f"Found {len(drops)} elements with 'drop' in ID")
            for d in drops[:10]:
                d_id = await d.get_attribute('id')
                d_tag = await d.evaluate('el => el.tagName')
                print(f"  - {d_tag}: {d_id}")
            
            print("\n=== QUANTITY/LIMIT ELEMENTS ===")
            limits = await page.locator('[id*="limit" i], [id*="quantity" i]').all()
            print(f"Found {len(limits)} quantity-related elements")
            for l in limits[:10]:
                l_id = await l.get_attribute('id')
                l_tag = await l.evaluate('el => el.tagName')
                print(f"  - {l_tag}: {l_id}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            print("\nDone.")

if __name__ == "__main__":
    asyncio.run(explore())
