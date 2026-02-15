import pandas as pd
import re

EOS = "\uE000"  # End of Sentence
EOP = "\uE001"  # End of Paragraph
EOT = "\uE002"  # End of Story


input_csv = "raw_stories/merged_output.csv"
output_csv = "raw_stories/merged_output_with_special_tokens.csv"


def add_special_tokens(text):
    if pd.isna(text):
        return ""

    text = str(text).strip()

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split into paragraphs (blank line means new paragraph)
    paragraphs = re.split(r"\n\s*\n+", text)

    new_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if para == "":
            continue

        # Add EOS after sentence punctuation: ۔ ! ?
        para = re.sub(r"([۔!?])", r"\1 " + EOS + " ", para)

        # Remove extra spaces
        para = re.sub(r"\s+", " ", para).strip()

        new_paragraphs.append(para)

    # Join paragraphs with EOP token
    final_text = (" " + EOP + " ").join(new_paragraphs)

    # Add EOT at end
    final_text = final_text.strip() + " " + EOT

    return final_text


# Load CSV
df = pd.read_csv(input_csv)

# Your story column name
story_col = "story_text"

# Add new processed column
df["story_text_tokens"] = df[story_col].apply(add_special_tokens)

# Save output CSV
df.to_csv(output_csv, index=False, encoding="utf-8-sig")

# Show first 2 results
df[["story_title", "story_text_tokens"]].head(2)