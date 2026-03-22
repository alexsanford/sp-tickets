"""
Exploration script with Cloudflare bypass attempt
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore():
    print("=" * 60)
    print("EXPLORING WITH CLOUDFLARE BYPASS")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        
        page = await context.new_page()
        
        try:
            url = f"{BASE_URL}/w/event.aspx?id={EVENT_ID}"
            print(f"\n1. Navigating to: {url}")
            
            await page.goto(url, timeout=90000)
            
            print(f"   Initial URL: {page.url}")
            print(f"   Title: {await page.title()}")
            
            # Wait for Cloudflare challenge to complete (if present)
            print("\n2. Waiting for page to fully load...")
            for i in range(30):
                await asyncio.sleep(1)
                title = await page.title()
                current_url = page.url
                print(f"   [{i+1}s] Title: {title[:50]}")
                
                if 'Just a moment' not in title and 'challenge' not in current_url.lower():
                    print("   Cloudflare challenge passed!")
                    break
            
            await asyncio.sleep(2)
            
            print(f"\n3. Final state:")
            print(f"   URL: {page.url}")
            print(f"   Title: {await page.title()}")
            
            await page.screenshot(path='/app/plan/loaded_page.png', full_page=True)
            print("   Screenshot saved: loaded_page.png")
            
            html = await page.content()
            with open('/app/plan/loaded_page.html', 'w') as f:
                f.write(html)
            print(f"   HTML saved: loaded_page.html ({len(html)} bytes)")
            
            # Find ticket elements
            print("\n4. Finding ticket elements...")
            
            selects = await page.locator('select').all()
            print(f"   Select elements: {len(selects)}")
            for s in selects:
                sid = await s.get_attribute('id')
                sname = await s.get_attribute('name')
                print(f"      - ID: {sid}")
            
            dropdowns = await page.locator('[id*="dropLimit"]').all()
            print(f"   dropLimit elements: {len(dropdowns)}")
            
            buttons = await page.locator('input[type="button"], button').all()
            print(f"   Button elements: {len(buttons)}")
            for btn in buttons:
                try:
                    btn_id = await btn.get_attribute('id')
                    btn_val = await btn.get_attribute('value')
                    btn_text = await btn.inner_text() if await btn.evaluate('el => el.tagName') == 'BUTTON' else ''
                    print(f"      - {btn_id}: {btn_val or btn_text}")
                except:
                    pass
            
            # Check page text for clues
            print("\n5. Checking page content...")
            body = page.locator('body')
            body_text = await body.inner_text()
            
            if 'Cinderella' in body_text:
                print("   Found 'Cinderella' - on correct page!")
            if 'P1' in body_text or 'P2' in body_text or 'P3' in body_text:
                print("   Found ticket pricing sections!")
            if 'Find Tickets' in body_text or 'GET TICKETS' in body_text:
                print("   Found ticket button text!")
            
            # Try to find table rows with ticket info
            print("\n6. Looking for ticket table...")
            tables = await page.locator('table').all()
            print(f"   Tables found: {len(tables)}")
            
            for i, table in enumerate(tables[:3]):
                text = await table.inner_text()
                if text.strip():
                    print(f"   Table {i+1}:")
                    for line in text.split('\n')[:5]:
                        print(f"      {line[:80]}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='/app/plan/error.png')
        
        finally:
            await browser.close()
            print("\nDone.")

if __name__ == "__main__":
    asyncio.run(explore())
