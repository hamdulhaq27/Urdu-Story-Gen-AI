import pandas as pd
from collections import Counter
import json
import random

input_csv = "merged_output_with_special_tokens.csv"
merges_file = "bpe_merges.json"
unigram_output = "unigram_counts.json"
bigram_output = "bigram_counts.json"
trigram_output = "trigram_counts.json"

EOT = "\uE002"  # End of Story

# Load BPE merges
with open(merges_file, "r", encoding="utf-8") as f:
    merges = json.load(f)

print("Merges loaded, count:", len(merges))

def apply_bpe(word):
    if not word:
        return []
    tokens = list(word) + ["</w>"]
    for pair in merges:
        i = 0
        while i < len(tokens) - 1:
            if tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                tokens[i] = tokens[i] + tokens[i + 1]
                tokens.pop(i + 1)
            else:
                i += 1
    return tokens

def tokenize_story(story):
    words = story.split()
    final_tokens = []
    for word in words:
        bpe_tokens = apply_bpe(word)
        final_tokens.extend(bpe_tokens)
    return final_tokens

# Load data
df = pd.read_csv(input_csv)
story_col = "story_text_tokens"
stories = df[story_col].dropna().tolist()

print("Stories loaded:", len(stories))

unigram_counts = Counter()
bigram_counts = Counter()
trigram_counts = Counter()

# Build n-gram counts
for story in stories:
    tokens = tokenize_story(story)
    for i in range(len(tokens)):
        unigram_counts[(tokens[i],)] += 1
        if i >= 1:
            bigram_counts[(tokens[i-1], tokens[i])] += 1
        if i >= 2:
            trigram_counts[(tokens[i-2], tokens[i-1], tokens[i])] += 1

total_unigrams = sum(unigram_counts.values())
print("Unique tokens (vocab size):", len(unigram_counts))

# Weights - strong trigram preference now that merges are good
lambda1 = 0.03
lambda2 = 0.10
lambda3 = 0.87

def get_probability(w1, w2, w3):
    trigram = (w1, w2, w3)
    bigram = (w2, w3)
    unigram = (w3,)

    trigram_prob = 0
    bigram_prob = 0
    unigram_prob = 0

    denom_trigram = bigram_counts.get((w1, w2), 0)
    if denom_trigram > 0:
        trigram_prob = trigram_counts.get(trigram, 0) / denom_trigram

    denom_bigram = unigram_counts.get((w2,), 0)
    if denom_bigram > 0:
        bigram_prob = bigram_counts.get(bigram, 0) / denom_bigram

    if total_unigrams > 0:
        unigram_prob = unigram_counts.get(unigram, 0) / total_unigrams

    # Interpolation + tiny smoothing
    final_prob = (
        lambda3 * trigram_prob +
        lambda2 * bigram_prob +
        lambda1 * unigram_prob + 1e-8
    )
    return final_prob

def generate_next_token(w1, w2):
    candidates = []
    for token_tuple in unigram_counts.keys():
        c = token_tuple[0]
        prob = get_probability(w1, w2, c)
        if prob > 0:
            candidates.append((c, prob))

    if len(candidates) == 0:
        # fallback
        return random.choice(list(unigram_counts.keys()))[0]

    tokens = [c[0] for c in candidates]
    probs = [c[1] for c in candidates]

    # temperature
    temperature = 0.75
    probs = [p ** (1 / temperature) for p in probs]
    total = sum(probs)
    if total > 0:
        probs = [p / total for p in probs]
    else:
        probs = [1.0 / len(probs)] * len(probs)

    return random.choices(tokens, probs)[0]

def detokenize(tokens):
    parts = []
    current = ""
    for t in tokens:
        if t.endswith("</w>"):
            current += t[:-4]
            parts.append(current)
            current = ""
            parts.append(" ")
        else:
            current += t
    if current:
        parts.append(current)
    text = "".join(parts).strip()

    text = text.replace("\uE000", "\n\n")
    text = text.replace("\uE002", "")
    text = text.replace("\uE002</w>", "")
    return text

def generate_story(prefix, max_length=300):
    prefix_tokens = tokenize_story(prefix)
    if len(prefix_tokens) < 2:
        return prefix

    generated = prefix_tokens.copy()

    print("Prefix tokens (first 30):", prefix_tokens[:30])

    while len(generated) < max_length:
        w1 = generated[-2]
        w2 = generated[-1]
        next_token = generate_next_token(w1, w2)

        if next_token == EOT or next_token == EOT + "</w>":
            break

        generated.append(next_token)

    return detokenize(generated)

# Save model files
def convert_keys(d):
    return {"|||".join(k): v for k, v in d.items()}

with open(unigram_output, "w", encoding="utf-8") as f:
    json.dump(convert_keys(unigram_counts), f, ensure_ascii=False)

with open(bigram_output, "w", encoding="utf-8") as f:
    json.dump(convert_keys(bigram_counts), f, ensure_ascii=False)

with open(trigram_output, "w", encoding="utf-8") as f:
    json.dump(convert_keys(trigram_counts), f, ensure_ascii=False)

print("Trigram model training finished")

# Run example
prefix = "ایک دفعہ کا ذکر ہے کہ ایک چھوٹا بچہ جنگل میں گھوم رہا تھا۔ اچانک اس نے دیکھا کہ ایک پرانا بوڑھا آدمی درخت کے نیچے بیٹھا ہے اور"
story = generate_story(prefix)
print("\nGenerated Story:\n")
print(story)