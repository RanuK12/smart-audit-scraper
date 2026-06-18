import asyncio
from playwright.async_api import async_playwright


class AuditEngine:
    """Base class for Playwright-based product auditing."""

    @staticmethod
    def validate_product(price: float, name: str) -> bool:
        """
        Validate a product based on its price and name.

        Returns True if the price is positive and the name is non‑empty.
        """
        return price > 0 and bool(name.strip())


async def launch_browser():
    """
    Launch a headless Chromium browser and return a tuple
    (page, browser, playwright) for further use.
    """
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    return page, browser, p


async def scrape_products():
    """
    Navigate to a demo e‑commerce site (books.toscrape.com),
    extract product names and prices, validate each product
    with AuditEngine, and print a summary report.
    """
    page, browser, playwright = await launch_browser()
    try:
        # Navigate to the demo site
        await page.goto("https://books.toscrape.com/")
        # Wait for at least one product element to appear
        await page.wait_for_selector(".product_pod", timeout=10000)

        products = await page.query_selector_all(".product_pod")
        valid_count = 0
        invalid_count = 0

        for product in products:
            # Extract product name (title attribute of the <a> inside <h3>)
            title_el = await product.query_selector("h3 a")
            name = await title_el.get_attribute("title") if title_el else ""

            # Extract price text (inside <p class="price_color">)
            price_el = await product.query_selector(".price_color")
            price_text = await price_el.inner_text() if price_el else ""

            # Parse the price (remove £ sign and any commas)
            price = 0.0
            if price_text:
                cleaned = price_text.replace("£", "").replace(",", "").strip()
                try:
                    price = float(cleaned)
                except ValueError:
                    price = 0.0

            # Validate using the AuditEngine
            if AuditEngine.validate_product(price, name):
                valid_count += 1
            else:
                invalid_count += 1

        print(f"Summary: {valid_count} valid products, {invalid_count} invalid products")

    finally:
        await browser.close()
        await playwright.stop()


async def main():
    """Entry point for the auditing script."""
    await scrape_products()


if __name__ == "__main__":
    asyncio.run(main())
