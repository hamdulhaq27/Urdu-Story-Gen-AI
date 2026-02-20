from pathlib import Path
import json
import random

BASE_PATH = Path(__file__).resolve().parent.parent

with open(BASE_PATH / "data/processed/trigram_counts.json", encoding="utf-8") as f:
    raw_trigram_counts = json.load(f)

trigram_counts = {}
for key, value in raw_trigram_counts.items():
    parts = key.split("|||")
    if len(parts) == 3:
        trigram_counts[(parts[0], parts[1], parts[2])] = value

ALL_WORDS = list({c for (_, _, c) in trigram_counts.keys()})

def tokenize(text):
    return text.strip().split()

def detokenize(tokens):
    clean_tokens = [t.replace("</w>", "").replace("<w/>", "").replace("", "").strip()
                    for t in tokens if t.strip()]
    return " ".join(clean_tokens)

def weighted_choice(candidates: dict, temperature: float = 1.0):
    words = list(candidates.keys())
    weights = list(candidates.values())
    scaled = [w ** (1/temperature) for w in weights]
    return random.choices(words, weights=scaled, k=1)[0]

def predict_next(w1, w2):
    candidates = {c: cnt for (a,b,c), cnt in trigram_counts.items() if a==w1 and b==w2}
    if candidates:
        return weighted_choice(candidates, temperature=1.2)

    candidates2 = {c: cnt for (a,b,c), cnt in trigram_counts.items() if b==w2}
    if candidates2:
        return weighted_choice(candidates2, temperature=1.2)

    return random.choice(ALL_WORDS)

def generate_tokens(tokens, max_length):
    if len(tokens) < 2:
        tokens = tokens + random.choices(ALL_WORDS, k=2)
    while len(tokens) < max_length:
        tokens.append(predict_next(tokens[-2], tokens[-1]))
    return tokens

def generate_story(prefix: str, max_length: int = 100):
    tokens = tokenize(prefix)
    output_tokens = generate_tokens(tokens, max_length)
    return detokenize(output_tokens)