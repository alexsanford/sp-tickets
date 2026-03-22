"""
Explore the actual seat selection page by clicking through to a section.
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://acadiau.universitytickets.com"
EVENT_ID = 2677

async def explore():
    print("=" * 60)
    print("EXPLORING INDIVIDUAL SEAT PAGE")
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
            
            # Step 2: Select 1 ticket
            print("\n2. Selecting 1 P1-Adult ticket...")
            dropdowns = await page.locator('[id*="dropLimit"]').all()
            print(f"   Found {len(dropdowns)} dropdowns")
            
            if dropdowns:
                await dropdowns[0].select_option('1')
                print("   Selected 1 ticket")
            
            await asyncio.sleep(1)
            
            # Step 3: Click Select Seats
            print("\n3. Clicking 'Select Seats'...")
            await page.locator('#btnSelectSection').click()
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            print(f"   Section page: {page.url}")
            
            # Step 4: Navigate directly to Section 3
            print("\n4. Navigating to Section 3 seat page...")
            
            # Build the section URL directly
            section_url = f"{BASE_URL}/w/events/Section.aspx?PackageID=0&PackageQty=&event_id={EVENT_ID}&ticket_id=1393&cid=0&class_id=6&SameSeats=false&SameSeatsMultiVenue=false&totalTix=1&pos=0&SelectedASEvents=&SelectedGAEvents=&PackageVenue=&ChangeSeats=False&OrigSection=&vsection=SEC-3"
            print(f"   URL: {section_url}")
            await page.goto(section_url, timeout=60000)
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            print(f"\n5. Seat selection page:")
            print(f"   URL: {page.url}")
            print(f"   Title: {await page.title()}")
            
            # Take screenshot
            await page.screenshot(path='/app/plan/individual_seats.png', full_page=True)
            print("   Saved: individual_seats.png")
            
            # Save HTML
            html = await page.content()
            with open('/app/plan/individual_seats.html', 'w') as f:
                f.write(html)
            print(f"   Saved: individual_seats.html ({len(html)} bytes)")
            
            # Analyze seat elements
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
                ('[class*="held" i]', 'Held'),
                ('[onclick]', 'Onclick'),
                ('[data-seat]', 'data-seat'),
                ('[data-row]', 'data-row'),
                ('[data-section]', 'data-section'),
            ]
            
            for sel, name in selectors:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        print(f"   {name}: {count}")
                except:
                    pass
            
            # Get sample SVG elements
            print("\n7. Sample SVG elements:")
            
            # Circles
            circles = await page.locator('svg circle').all()
            print(f"   Circles: {len(circles)}")
            for c in circles[:10]:
                try:
                    attrs = await c.evaluate("""el => ({
                        cx: el.getAttribute("cx"),
                        cy: el.getAttribute("cy"),
                        r: el.getAttribute("r"),
                        fill: el.getAttribute("fill"),
                        cls: el.getAttribute("class"),
                        style: el.getAttribute("style"),
                        onclick: el.getAttribute("onclick") ? "yes" : "no"
                    })""")
                    print(f"      {attrs}")
                except:
                    pass
            
            # Rects
            rects = await page.locator('svg rect').all()
            print(f"   Rects: {len(rects)}")
            for r in rects[:5]:
                try:
                    attrs = await r.evaluate("""el => ({
                        x: el.getAttribute("x"),
                        y: el.getAttribute("y"),
                        width: el.getAttribute("width"),
                        height: el.getAttribute("height"),
                        fill: el.getAttribute("fill"),
                        cls: el.getAttribute("class")
                    })""")
                    print(f"      {attrs}")
                except:
                    pass
            
            # Check for seat-related JavaScript objects
            print("\n8. JavaScript seat data:")
            js = await page.evaluate('''() => {
                const results = {};
                
                // Look for seat-related global variables
                for (let key in window) {
                    try {
                        let k = key.toLowerCase();
                        if ((k.includes('seat') || k.includes('venue') || k.includes('chart') || k.includes('map')) && 
                            typeof window[key] !== 'function') {
                            let val = window[key];
                            if (typeof val === 'object') {
                                results[key] = JSON.stringify(val).substring(0, 200);
                            } else {
                                results[key] = String(val).substring(0, 200);
                            }
                        }
                    } catch(e) {}
                }
                
                // SVG analysis
                const svg = document.querySelector('svg');
                if (svg) {
                    results.hasSVG = true;
                    results.svgChildren = svg.querySelectorAll('*').length;
                    
                    // Get unique fill colors
                    const fills = new Set();
                    svg.querySelectorAll('[fill]').forEach(el => fills.add(el.getAttribute('fill')));
                    results.uniqueFills = Array.from(fills).slice(0, 20).join(', ');
                    
                    // Get unique classes
                    const classes = new Set();
                    svg.querySelectorAll('[class]').forEach(el => {
                        el.getAttribute('class').split(' ').forEach(c => classes.add(c));
                    });
                    results.uniqueClasses = Array.from(classes).filter(c => c).slice(0, 20).join(', ');
                }
                
                return results;
            }''')
            for k, v in js.items():
                print(f"   {k}: {v}")
            
            # Page text
            print("\n9. Page text preview:")
            body_text = await page.locator('body').inner_text()
            for line in body_text.split('\n')[:20]:
                if line.strip():
                    print(f"   {line[:80]}")
            
            # Look for seat count info
            print("\n10. Looking for seat availability info...")
            seat_info = await page.evaluate('''() => {
                const body = document.body.innerText;
                const results = {};
                
                // Look for patterns like "X seats available" or "X of Y seats"
                const patterns = [
                    /(\d+)\s*seats?\s*available/i,
                    /(\d+)\s*of\s*(\d+)\s*seats?/i,
                    /available[:\s]*(\d+)/i,
                    /sold[:\s]*(\d+)/i,
                    /remaining[:\s]*(\d+)/i,
                ];
                
                patterns.forEach(p => {
                    const match = body.match(p);
                    if (match) results[p.source] = match[0];
                });
                
                return results;
            }''')
            for k, v in seat_info.items():
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
