import pandas as pd
from collections import Counter, defaultdict
import json

input_csv = "merged_output_with_special_tokens.csv"
merges_output = "bpe_merges.json"
vocab_output = "bpe_vocab.json"
vocab_limit = 500        

def build_word_frequency(stories):
    word_freq = Counter()
    for story in stories:
        words = story.split()
        for word in words:
            char_word = " ".join(list(word)) + " </w>"
            word_freq[char_word] += 1
    return word_freq

def get_pair_frequency(word_freq):
    pair_freq = defaultdict(int)
    for word, freq in word_freq.items():
        tokens = word.split()
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            pair_freq[pair] += freq
    return pair_freq

def merge_pair(pair, word_freq):
    merged_freq = {}
    pair_str = " ".join(pair)
    merged_token = "".join(pair)
    for word in word_freq:
        new_word = word.replace(pair_str, merged_token)
        merged_freq[new_word] = word_freq[word]
    return merged_freq

def build_vocab(word_freq):
    vocab = set()
    for word in word_freq:
        tokens = word.split()
        for token in tokens:
            vocab.add(token)
    return vocab

# Load data
df = pd.read_csv(input_csv)
story_col = "story_text_tokens"
stories = df[story_col].dropna().tolist()

word_freq = build_word_frequency(stories)
vocab = build_vocab(word_freq)

merges = []

print("Starting BPE training...")
print("Initial vocab size:", len(vocab))

# Force more merges
target_merges = vocab_limit - len(vocab)  

while len(merges) < target_merges:
    pair_freq = get_pair_frequency(word_freq)

    if len(pair_freq) == 0:
        print("No more pairs to merge!")
        break

    best_pair = max(pair_freq, key=pair_freq.get)
    freq = pair_freq[best_pair]

    word_freq = merge_pair(best_pair, word_freq)
    merges.append(best_pair)

    # Optional: rebuild vocab only every 10 merges to save time
    if len(merges) % 10 == 0:
        vocab = build_vocab(word_freq)
        print(f"Merge {len(merges)}: {best_pair} (freq {freq}) → vocab now {len(vocab)}")

print("Final vocab size:", len(build_vocab(word_freq)))
print("Total merges performed:", len(merges))

# Save
with open(merges_output, "w", encoding="utf-8") as f:
    json.dump(merges, f, ensure_ascii=False)

with open(vocab_output, "w", encoding="utf-8") as f:
    json.dump(list(build_vocab(word_freq)), f, ensure_ascii=False)

print("BPE training finished")