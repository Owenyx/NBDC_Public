from playwright.async_api import Page
from utils import *
from browser_utils import *


async def scrape_species(page: Page, species: str) -> str:
    '''Returns all src fields of all species images across paginated pages'''

    base_url = page.url

    all_srcs = []
    page_num = 1

    while True:
        # Replace page parameter
        paginated_url = re.sub(r'page=\d+', f'page={page_num}', base_url)

        await page.goto(paginated_url, wait_until="domcontentloaded")
        
        print(f'{species} - p. {page_num}')


        # Check for "no results" message
        no_results = page.locator(
            "h3:has-text('Your query did not return any results')"
        )

        if await no_results.first.is_visible(): # If no results, exit loop
            break


        # Wait for images to exist (important for dynamic pages)
        imgs = page.locator('img[alt="Image Associated With the Occurrence"]')

        if not await imgs.first.is_visible():
            break # Exit if no images as fallback

        srcs = await imgs.evaluate_all(
            "imgs => imgs.map(img => img.src)"
        )


        all_srcs.extend(srcs)
        page_num += 1

    return species, all_srcs


async def main():
    with open('urls.txt') as f:
        urls = [line.strip() for line in f.readlines()]

    species = get_species()

    scraper = PlaywrightScraperPool(scrape_species)

    await scraper.start()

    url_args_pairs = [(url, (sp,)) for url, sp in zip(urls, species)]

    try:
        sp_srcs_pairs: List[Tuple[str, List[str]]] = await scraper.run(url_args_pairs)

    finally:
        await scraper.close() # Always close scraper


    # Build dict mapping species name to srcs list
    srcs_map = {}
    for sp, srcs in sp_srcs_pairs:
        srcs_map[sp] = srcs


    # Create a file for each species with srcs that contains all its srcs
    os.makedirs('image_urls', exist_ok=True)

    for sp in srcs_map:
        srcs = srcs_map[sp]

        if len(srcs) == 0:
            continue
        
        with open(f'image_urls/{sp}.txt', 'w') as f:
            f.write('\n'.join(srcs))

    print('Done')


if __name__ == "__main__":
    asyncio.run(main())