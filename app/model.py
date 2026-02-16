from pathlib import Path
import json
import random
import re

BASE_PATH = Path(__file__).resolve().parent.parent

# Load trigram counts
with open(BASE_PATH / "data/processed/trigram_counts.json", encoding="utf-8") as f:
    raw_trigram_counts = json.load(f)

# Convert string keys back to tuples
trigram_counts = {}
for key, value in raw_trigram_counts.items():
    parts = key.split("|||")
    if len(parts) == 3:
        trigram_counts[(parts[0], parts[1], parts[2])] = value

# Tokenizer / Detokenizer
def tokenize(text):
    return text.strip().split()

def detokenize(tokens):
    """
    Clean tokens for readable Urdu text:
    - Remove broken symbols like </w>, <w/>,  etc.
    - Add spaces between words
    - Handle punctuation spacing
    """
    # Remove unwanted symbols
    clean_tokens = [
        t.replace("</w>", "").replace("<w/>", "").replace("", "").strip()
        for t in tokens if t.strip()
    ]

    # Join tokens with spaces
    text = " ".join(clean_tokens)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

# Predict next token with robust fallback
def predict_next(w1, w2):
    # Exact trigram match
    candidates = {c: cnt for (a, b, c), cnt in trigram_counts.items() if a == w1 and b == w2}
    if candidates:
        return random.choices(list(candidates.keys()), weights=list(candidates.values()))[0]

    # Partial match: last word only
    candidates2 = {c: cnt for (a, b, c), cnt in trigram_counts.items() if a == w2}
    if candidates2:
        return random.choices(list(candidates2.keys()), weights=list(candidates2.values()))[0]

    # Last resort: pick any random word from trigram table
    return random.choice(list({c for (_, _, c) in trigram_counts.keys()}))

# Generate tokens up to max_length
def generate_tokens(tokens, max_length):
    if len(tokens) < 2:
        # If very short prefix, pad with random words
        tokens = tokens + random.choices(list({c for (_, _, c) in trigram_counts.keys()}), k=2)

    while len(tokens) < max_length:
        next_token = predict_next(tokens[-2], tokens[-1])
        tokens.append(next_token)

    return tokens

# Full story generation
def generate_story(prefix: str, max_length: int = 100):
    tokens = tokenize(prefix)
    output_tokens = generate_tokens(tokens, max_length)
    return detokenize(output_tokens)
