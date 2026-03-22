"""
Explore the ticket selection flow - what happens when we click Find Tickets?
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore_flow():
    print("=" * 60)
    print("EXPLORING TICKET SELECTION FLOW")
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
        
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        try:
            # Step 1: Load event page
            print("\n1. Loading event page...")
            await page.goto(f"{BASE_URL}/w/event.aspx?id={EVENT_ID}", timeout=60000)
            await asyncio.sleep(3)
            print(f"   Loaded: {await page.title()}")
            
            # Step 2: Check what buttons are available
            print("\n2. Checking available buttons...")
            
            find_tickets_btn = page.locator('#btnAddCart')
            select_seats_btn = page.locator('#btnSelectSection')
            
            find_count = await find_tickets_btn.count()
            select_count = await select_seats_btn.count()
            
            print(f"   Find Tickets button: {find_count}")
            print(f"   Select Seats button: {select_count}")
            
            # Step 3: Look at the dropdowns
            print("\n3. Examining ticket dropdowns...")
            dropdowns = await page.locator('[id*="dropLimit"]').all()
            
            for i, dd in enumerate(dropdowns):
                dd_id = await dd.get_attribute('id')
                parent = dd.locator('xpath=ancestor::tr[1]')
                parent_text = await parent.inner_text()
                lines = [l.strip() for l in parent_text.split('\n') if l.strip()]
                ticket_name = lines[0] if lines else 'Unknown'
                print(f"   {i+1}. {ticket_name[:40]} (ID: ...{dd_id[-30:]})")
            
            # Step 4: Select 1 ticket from first dropdown
            print("\n4. Selecting 1 ticket from P1-Adult...")
            first_dropdown = dropdowns[0]
            await first_dropdown.select_option('1')
            await asyncio.sleep(0.5)
            print("   Selected!")
            
            # Check if button is now enabled
            is_disabled = await find_tickets_btn.first.is_disabled()
            print(f"   Find Tickets disabled: {is_disabled}")
            
            # Step 5: Click Find Tickets
            print("\n5. Clicking 'Find Tickets'...")
            
            initial_url = page.url
            
            try:
                async with page.expect_navigation(timeout=30000):
                    await find_tickets_btn.click()
                print(f"   Navigation occurred!")
            except Exception as nav_err:
                print(f"   No navigation: {nav_err}")
                await find_tickets_btn.click()
                await asyncio.sleep(3)
            
            current_url = page.url
            print(f"   URL before: {initial_url}")
            print(f"   URL after:  {current_url}")
            
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle')
            
            # Step 6: Analyze new page
            print("\n6. Analyzing resulting page...")
            print(f"   Title: {await page.title()}")
            
            await page.screenshot(path='/app/plan/after_find_tickets.png', full_page=True)
            print("   Screenshot: after_find_tickets.png")
            
            html = await page.content()
            with open('/app/plan/after_find_tickets.html', 'w') as f:
                f.write(html)
            print(f"   HTML saved: after_find_tickets.html ({len(html)} bytes)")
            
            # Check for seat selection elements
            print("\n7. Looking for seat selection elements...")
            
            seat_selectors = [
                ('SVG circles', 'svg circle'),
                ('SVG rects', 'svg rect'),
                ('Seat divs', 'div[class*="seat" i]'),
                ('Seat buttons', 'button[class*="seat" i]'),
                ('Canvas', 'canvas'),
                ('Image maps', 'map, area'),
                ('Available', '[class*="available" i]'),
                ('Taken/Sold', '[class*="taken" i], [class*="sold" i]'),
                ('Section', '[class*="section" i]'),
                ('Row', '[class*="row" i]:not([role="row"])'),
            ]
            
            found = {}
            for name, selector in seat_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        found[name] = count
                        print(f"   {name}: {count}")
                        
                        if count <= 10:
                            for el in await page.locator(selector).all():
                                try:
                                    attrs = await el.evaluate('''el => ({
                                        tag: el.tagName,
                                        id: el.id,
                                        className: el.className,
                                        fill: el.getAttribute('fill'),
                                        stroke: el.getAttribute('stroke'),
                                        data: Object.keys(el.dataset).map(k => k + '=' + el.dataset[k])
                                    })''')
                                    print(f"      {attrs}")
                                except:
                                    pass
                except Exception as e:
                    pass
            
            # Check for any seat-related JavaScript
            print("\n8. Checking for seat data in JavaScript...")
            js_data = await page.evaluate('''() => {
                const results = {};
                
                // Common variable names
                const vars = ['seats', 'seatMap', 'venueMap', 'seatChart', 'chart', 
                              'sections', 'availableSeats', 'selectedSeats'];
                
                for (const v of vars) {
                    if (window[v]) {
                        results[v] = typeof window[v] === 'object' ? 
                            JSON.stringify(window[v]).substring(0, 200) : 
                            String(window[v]).substring(0, 200);
                    }
                }
                
                // Check for SVG with seats
                const svg = document.querySelector('svg');
                if (svg) {
                    results.hasSVG = true;
                    results.svgChildren = svg.children.length;
                }
                
                return results;
            }''')
            
            if js_data:
                for key, val in js_data.items():
                    print(f"   {key}: {val}")
            
            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Initial URL: {initial_url}")
            print(f"Final URL: {current_url}")
            print(f"URL changed: {initial_url != current_url}")
            print(f"Elements found: {found}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='/app/plan/flow_error.png')
        
        finally:
            await browser.close()
            print("\nDone.")

if __name__ == "__main__":
    asyncio.run(explore_flow())
