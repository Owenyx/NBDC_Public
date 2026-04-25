import requests
import aiohttp


excluded_dataset_keys = {
    'iNaturalist': '50c9509d-22c7-4a22-a47d-8c48425ef4a7',
    'BugGuide': '4fa7b334-ce0d-4e88-aaae-2e0c138d049e'
}

def get_bee_images(species_name):
    url = "https://api.gbif.org/v1/occurrence/search"

    offset = 0
    limit = 50
    count = 9999
    results = []

    session = requests.Session()

    while offset < count:
        params = [
            ("scientificName", species_name),
            ("mediaType", "StillImage"),
            ("limit", limit),
            ("offset", offset),
            ("basisOfRecord", "PRESERVED_SPECIMEN"),
            ("license", "CC0_1_0"),
            ("taxonKey", 7798)  # Apidae
        ]

        # Prepare request
        req = requests.Request("GET", url, params=params).prepare()

        print("Searching request:")
        print(req.url)

        response = session.send(req, timeout=20)
        response.raise_for_status()

        data = response.json()

        count = data['count']

        num_saved = 0

        for record in data.get("results", []):

            if record['datasetKey'] in excluded_dataset_keys.values():
                # Skip excluded datasets
                print('Skipping record from', record['datasetName'])
                continue 

            for media in record.get("media", []):
                if media.get("type") == "StillImage":

                    image_url = media.get("identifier")

                    if not image_url:
                        continue
                    
                    # Some images result in 404 errors, so each is validated
                    try:
                        head_resp = session.head(image_url, timeout=5, allow_redirects=True)

                        if head_resp.status_code == 200:
                            results.append({
                                "species": record.get("species"),
                                "image_url": image_url,
                            })
                            num_saved += 1
                        else:
                            print(f"Skipping broken image ({head_resp.status_code}): {image_url}")

                    except requests.RequestException:
                        print(f"Skipping unreachable image: {image_url}")

        print(f'Retrieved {num_saved} images\n')
        offset += limit

    return results


synonyms = {
    "Bombus (Psithyrus) bohemicus": "Bombus bohemicus",
    "Bombus (Psithyrus) flavidus": "Bombus flavidus",
    "Bombus (Psithyrus) insularis": "Bombus insularis",
    "Bombus polaris polaris": "Bombus polaris",
    "Bombus (Psithyrus) suckleyi": "Bombus suckleyi",
    "Coelioxys funeraria": "Coelioxys funerarius",
    "Coelioxys moesta": "Coelioxys moestus",
    "Coelioxys octodentata": "Coelioxys octodentatus",
    "Melissodes confusa": "Melissodes confusus",
    "Melissodes illata": "Melissodes illatus",
    "Melissodes lupina": "Melissodes lupinus",
    "Melissodes lutulenta": "Melissodes lutulentus",
    "Melissodes microsticta": "Melissodes microstictus",
    "Melissodes pallidisignata": "Melissodes pallidisignatus",
    "Melissodes perlusa": "Melissodes perlusus",
    "Melissodes semilupina": "Melissodes semilupinus",
}

async def get_bee_images_async(species_name):
    url = "https://api.gbif.org/v1/occurrence/search"
    offset = 0
    limit = 50
    count = 9999
    results = []

    search_species = synonyms.get(species_name, species_name)

    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        while offset < count:
            params = [
                ("scientificName", search_species),
                ("mediaType", "StillImage"),
                ("limit", limit),
                ("offset", offset),
                ("basisOfRecord", "PRESERVED_SPECIMEN"),
                ("license", "CC0_1_0"),
                ("taxonKey", 7798) # Apidae
            ]

            # Request print
            req = requests.models.PreparedRequest()
            req.prepare_url(url, params)
            print("Searching request:")
            print(req.url)          

            # Fetch GBIF page 
            data = await fetch_page(session, url, params)
            count = data["count"]

            num_saved = 0

            # Parse record
            for record in data.get("results", []):

                # Filter based on excluded keys
                if record.get("datasetKey") in excluded_dataset_keys.values():
                    print('Skipping record from', record.get("datasetName"))
                    continue

                for media in record.get("media", []):
                    if media.get("type") == "StillImage":

                        image_url = media.get("identifier")

                        if not image_url:
                            continue

                        results.append({
                            "species": species_name,
                            "image_url": image_url,
                        })
                        num_saved += 1

            print(f"Retrieved {num_saved} images\n")

            offset += limit

    return results


async def fetch_page(session, url, params):
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def validate_image(session, image_url):
    try:
        async with session.head(image_url, timeout=5) as resp:
            if resp.status < 400:
                return image_url
            else:
                print(f"Skipping broken image ({resp.status}): {image_url}")

    except Exception as e:
        print(f"Error validating image {image_url}: {str(e)}")

    return None