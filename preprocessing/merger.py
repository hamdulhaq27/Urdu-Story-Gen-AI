import pandas as pd
import os

# ==== FILE PATHS ====
file1 = "raw_stories/urdupoint_stories.csv"
file2 = "rekhta_stories/rekhta_stories.csv"

# ==== COLUMN NAME THAT HAS IDS ====
id_column = "story_id"

# ==== READ FILES WITH UTF-8 ====
df1 = pd.read_csv(file1, encoding="utf-8")
df2 = pd.read_csv(file2, encoding="utf-8")

# ==== FUNCTION TO ADD 251 TO ID ====
def update_id(id_val):
    try:
        prefix, num = str(id_val).split("_")
        new_num = int(num) + 250
        return f"{prefix}_{new_num:04d}"
    except:
        return id_val

# ==== APPLY TO SECOND CSV ====
df2[id_column] = df2[id_column].apply(update_id)

# ==== MERGE ROW-WISE ====
merged_df = pd.concat([df1, df2], ignore_index=True)

# ==== SAVE OUTPUT WITH UTF-8 (VERY IMPORTANT) ====
output_path = "raw_stories/merged_output.csv"

merged_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"   # ← BEST for Urdu + Excel compatibility
)

print("✅ UTF-8 safe merge completed!")
