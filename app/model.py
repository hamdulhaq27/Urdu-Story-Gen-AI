from pathlib import Path
import json
import random
import time

# Make random generator truly random
random.seed(time.time())

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
    clean_tokens = [
        t.replace("</w>", "").replace("<w/>", "").replace("", "").strip()
        for t in tokens if t.strip()
    ]
    return " ".join(clean_tokens)

def weighted_choice(candidates: dict, temperature: float = 1.0):
    words = list(candidates.keys())
    weights = list(candidates.values())
    # apply temperature scaling
    scaled = [w ** (1/temperature) for w in weights]
    return random.choices(words, weights=scaled, k=1)[0]

def predict_next(w1, w2):
    # Prefer trigrams starting with w1,w2
    candidates = {c: cnt for (a,b,c), cnt in trigram_counts.items() if a==w1 and b==w2}
    if candidates:
        return weighted_choice(candidates, temperature=1.2)

    # Fall back to trigrams where second word is w2
    candidates2 = {c: cnt for (a,b,c), cnt in trigram_counts.items() if b==w2}
    if candidates2:
        return weighted_choice(candidates2, temperature=1.3)

    # Last resort: pick random word
    return random.choice(ALL_WORDS)

def generate_tokens(tokens, max_length):
    # ensure at least 2 starting tokens
    if len(tokens) < 2:
        tokens += random.choices(ALL_WORDS, k=2)

    # Keep track of last 3 words to avoid repetition
    last_words = set(tokens[-3:])

    while len(tokens) < max_length:
        next_word = predict_next(tokens[-2], tokens[-1])

        # optionally avoid repeating last few words
        if next_word in last_words:
            next_word = random.choice(ALL_WORDS)

        tokens.append(next_word)
        last_words = set(tokens[-3:])

    return tokens

def generate_story(prefix: str, max_length: int = 100):
    tokens = tokenize(prefix)
    output_tokens = generate_tokens(tokens, max_length)
    return detokenize(output_tokens)