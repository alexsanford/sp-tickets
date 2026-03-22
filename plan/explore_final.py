"""
Final exploration - select tickets THEN click Select Seats
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore():
    print("=" * 60)
    print("TESTING SEAT SELECTION FLOW")
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
            url = f"{BASE_URL}/w/event.aspx?id={EVENT_ID}"
            print(f"\n1. Loading event page: {url}")
            await page.goto(url, timeout=60000)
            
            for i in range(10):
                if 'Just a moment' not in await page.title():
                    break
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
            print(f"   Loaded: {await page.title()}")
            
            # Find buttons and dropdowns
            print("\n2. Finding form elements...")
            find_tickets = page.locator('#btnAddCart')
            select_seats = page.locator('#btnSelectSection')
            dropdowns = await page.locator('[id*="dropLimit"]').all()
            
            print(f"   Dropdowns: {len(dropdowns)}")
            print(f"   Find Tickets: {await find_tickets.count()}")
            print(f"   Select Seats: {await select_seats.count()}")
            
            # Select 1 ticket from each dropdown to enable the buttons
            print("\n3. Selecting tickets from dropdowns...")
            for i, dd in enumerate(dropdowns):
                dd_id = await dd.get_attribute('id')
                parent = dd.locator('xpath=ancestor::tr[1]')
                parent_text = await parent.inner_text()
                ticket_name = parent_text.split('\n')[0][:30]
                
                await dd.select_option('1')
                print(f"   Selected: {ticket_name}")
            
            await asyncio.sleep(1)
            
            # Check button states
            ft_disabled = await find_tickets.first.is_disabled()
            ss_disabled = await select_seats.first.is_disabled()
            print(f"\n4. Button states after selection:")
            print(f"   Find Tickets disabled: {ft_disabled}")
            print(f"   Select Seats disabled: {ss_disabled}")
            
            # Now try Select Seats
            print("\n5. Clicking 'Select Seats' button...")
            
            if not ss_disabled:
                try:
                    async with page.expect_navigation(timeout=30000):
                        await select_seats.click()
                    print("   Navigation occurred!")
                except Exception as e:
                    print(f"   Navigation timeout or error: {e}")
                    await asyncio.sleep(3)
                
                current_url = page.url
                print(f"\n6. Result:")
                print(f"   URL: {current_url}")
                print(f"   Title: {await page.title()}")
                
                await page.screenshot(path='/app/plan/seat_selection_page.png', full_page=True)
                html = await page.content()
                with open('/app/plan/seat_selection_page.html', 'w') as f:
                    f.write(html)
                print(f"   Saved HTML: {len(html)} bytes")
                print(f"   Saved screenshot: seat_selection_page.png")
                
                # Analyze seat elements
                print("\n7. Looking for seat elements...")
                
                selectors = [
                    ('SVG circles', 'svg circle'),
                    ('SVG rects', 'svg rect'),
                    ('Seat divs', 'div[class*="seat" i]'),
                    ('Clickable seats', '[onclick*="seat" i]'),
                    ('Available', '[class*="available" i]'),
                    ('Taken/Sold', '[class*="taken" i], [class*="sold" i]'),
                ]
                
                for name, sel in selectors:
                    count = await page.locator(sel).count()
                    if count > 0:
                        print(f"   {name}: {count}")
                        if count <= 5:
                            for el in await page.locator(sel).all():
                                attrs = await el.evaluate('el => ({ tag: el.tagName, id: el.id, class: el.className, fill: el.getAttribute("fill") })')
                                print(f"      {attrs}")
                
                # Get page text
                page_text = await page.locator('body').inner_text()
                print(f"\n8. Page text preview:")
                for line in page_text.split('\n')[:15]:
                    if line.strip():
                        print(f"   {line[:80]}")
                
            else:
                print("   Select Seats still disabled - trying Find Tickets instead")
                
                if not ft_disabled:
                    try:
                        async with page.expect_navigation(timeout=30000):
                            await find_tickets.click()
                        print("   Navigation occurred!")
                    except:
                        await find_tickets.click()
                        await asyncio.sleep(3)
                    
                    print(f"   URL: {page.url}")
                    print(f"   Title: {await page.title()}")
                    
                    await page.screenshot(path='/app/plan/find_tickets_result.png', full_page=True)
                    html = await page.content()
                    with open('/app/plan/find_tickets_result.html', 'w') as f:
                        f.write(html)
                    print(f"   Saved: find_tickets_result.html ({len(html)} bytes)")
                    
                    page_text = await page.locator('body').inner_text()
                    print(f"\n   Page text preview:")
                    for line in page_text.split('\n')[:15]:
                        if line.strip():
                            print(f"   {line[:80]}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='/app/plan/error.png')
        
        finally:
            await browser.close()
            print("\n" + "=" * 60)
            print("DONE")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(explore())
