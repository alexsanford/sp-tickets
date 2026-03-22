"""
Final exploration: Navigate to seat selection page and analyze its structure.
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore():
    print("=" * 60)
    print("EXPLORING SEAT SELECTION PAGE")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        
        await context.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined});')
        
        page = await context.new_page()
        
        try:
            # Step 1: Load event page
            print(f"\n1. Loading event page...")
            await page.goto(f"{BASE_URL}/w/event.aspx?id={EVENT_ID}", timeout=60000)
            
            for i in range(10):
                if 'Just a moment' not in await page.title():
                    break
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
            print(f"   Title: {await page.title()}")
            
            # Step 2: Select 1 ticket from first dropdown
            print("\n2. Selecting 1 P1-Adult ticket...")
            dropdowns = await page.locator('[id*="dropLimit"]').all()
            print(f"   Found {len(dropdowns)} dropdowns")
            
            if dropdowns:
                await dropdowns[0].select_option('1')
                print("   Selected 1 ticket")
            
            # Step 3: Check buttons
            print("\n3. Checking buttons...")
            select_seats = page.locator('#btnSelectSection')
            find_tickets = page.locator('#btnAddCart')
            
            ss_disabled = await select_seats.first.is_disabled()
            ft_disabled = await find_tickets.first.is_disabled()
            print(f"   Select Seats disabled: {ss_disabled}")
            print(f"   Find Tickets disabled: {ft_disabled}")
            
            # Step 4: Click appropriate button
            print("\n4. Clicking button...")
            
            if not ss_disabled:
                print("   Clicking 'Select Seats'...")
                await select_seats.click()
            elif not ft_disabled:
                print("   Clicking 'Find Tickets'...")
                await find_tickets.click()
            else:
                print("   Both buttons disabled - selecting more tickets...")
                for dd in dropdowns:
                    await dd.select_option('1')
                await asyncio.sleep(1)
                if not ss_disabled:
                    await select_seats.click()
                else:
                    await find_tickets.click()
            
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            print(f"\n5. Result page:")
            print(f"   URL: {page.url}")
            print(f"   Title: {await page.title()}")
            
            # Take screenshot
            await page.screenshot(path='/app/plan/seat_page.png', full_page=True)
            print("   Saved: seat_page.png")
            
            # Save HTML
            html = await page.content()
            with open('/app/plan/seat_page.html', 'w') as f:
                f.write(html)
            print(f"   Saved: seat_page.html ({len(html)} bytes)")
            
            # Analyze elements
            print("\n6. Searching for seat elements...")
            
            selectors = [
                ('svg circle', 'SVG circles'),
                ('svg rect', 'SVG rects'),
                ('svg path', 'SVG paths'),
                ('svg', 'SVG root'),
                ('canvas', 'Canvas'),
                ('[class*="seat" i]', 'Seat class'),
                ('[class*="available" i]', 'Available'),
                ('[class*="taken" i]', 'Taken'),
                ('[class*="sold" i]', 'Sold'),
                ('[onclick]', 'Onclick'),
            ]
            
            for sel, name in selectors:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        print(f"   {name}: {count}")
                except:
                    pass
            
            # Get sample SVG circles
            print("\n7. Sample SVG circles:")
            circles = await page.locator('svg circle').all()
            for c in circles[:5]:
                try:
                    attrs = await c.evaluate('el => ({ cx: el.getAttribute("cx"), cy: el.getAttribute("cy"), r: el.getAttribute("r"), fill: el.getAttribute("fill"), cls: el.getAttribute("class") })')
                    print(f"   {attrs}")
                except:
                    pass
            
            # Check onclick elements
            print("\n8. Onclick elements:")
            onclicks = await page.locator('[onclick]').all()
            for el in onclicks[:5]:
                try:
                    tag = await el.evaluate('el => el.tagName')
                    oid = await el.get_attribute('id')
                    onclick = await el.get_attribute('onclick')
                    print(f"   {tag} id={oid}: {onclick[:60] if onclick else ''}")
                except:
                    pass
            
            # Page text
            print("\n9. Page text preview:")
            body_text = await page.locator('body').inner_text()
            for line in body_text.split('\n')[:15]:
                if line.strip():
                    print(f"   {line[:80]}")
            
            # JS data
            print("\n10. JavaScript data:")
            js = await page.evaluate('''() => {
                const results = {};
                for (let key in window) {
                    try {
                        let k = key.toLowerCase();
                        if ((k.includes('seat') || k.includes('venue') || k.includes('chart')) && typeof window[key] !== 'function') {
                            results[key] = typeof window[key];
                        }
                    } catch(e) {}
                }
                const svg = document.querySelector('svg');
                if (svg) {
                    results.hasSVG = true;
                    results.svgChildren = svg.querySelectorAll('*').length;
                }
                return results;
            }''')
            for k, v in js.items():
                print(f"   {k}: {v}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='/app/plan/error.png')
        
        finally:
            await browser.close()
            print("\n" + "=" * 60)
            print("EXPLORATION COMPLETE")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(explore())
