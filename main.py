from apiUtils import *
from utils import *
import pandas as pd
from pathlib import Path
import asyncio


async def main():
    species = get_species()

    '''
    Results will be in the form:
    {
        species: str
        image_url: str
    }
    '''
    results = []

    species_counts = {}

    for sp in species:
        species_results = await get_bee_images_async(sp)

        results.extend(species_results)
        species_counts[sp] = len(species_results)
    
    print(len(results), 'images saved')


    # --- Write to entire_output.txt ---
    lines = [f"Species: {record['species']}\nImage URL: {record['image_url']}\n\n" for record in results]

    with open('output.txt', 'w') as f:
        f.writelines(lines)
    
    print('output.txt created.\n')

    
    # --- Write URLs to each species file in output folder
    out = Path('species_images')

    # First get the file contents for each species
    sp_files_contents = {}
    for record in results:
        sp = record['species']
        
        # If no content exists for this species, initialize it
        sp_files_contents.setdefault(sp, '')

        # Append the URL
        url = record['image_url']
        sp_files_contents[sp] += f'{url}\n'

    
    # Now write to each file

    # Create output folder if needed
    os.makedirs(out, exist_ok=True)

    for sp in sp_files_contents:
        with open(out / f'{sp}.txt', 'w') as f:
            f.write(sp_files_contents[sp])
        
        print(sp, 'file created.')


    # --- Copy bee_counts.csv and add GBIF counts
    df = pd.read_csv("bee_counts.csv")
    
    for sp in species_counts:
        # Update the GBIF and total file count for the row os this species
        mask = df.iloc[:, 1] == sp
        df.loc[mask, df.columns[7]] = species_counts[sp] # GBIF
        df.loc[mask, df.columns[2]] += species_counts[sp] # Total
    
    df.to_csv("BP-26_bee_counts.csv", index=False)

    print("\nCSV updated.")


if __name__ == '__main__':
    asyncio.run(main())