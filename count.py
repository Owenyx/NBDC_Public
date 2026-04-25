from utils import *

# Copy bee_counts.csv and add GBIF counts
df = pd.read_csv("bee_counts.csv")

root = Path('GBIF')
for sp in get_subfolders(root):
    count = count_files_in_dir_tree(root / sp)

    # Update the GBIF and total file count for the row os this species
    mask = df.iloc[:, 1] == sp
    df.loc[mask, df.columns[7]] = count # GBIF
    df.loc[mask, df.columns[2]] += count # Total

df.to_csv("BP-26_bee_counts_downloaded.csv", index=False)

print("\nCSV updated.")