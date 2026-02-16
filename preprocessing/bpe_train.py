import pandas as pd
from collections import Counter, defaultdict
import json


input_csv = "merged_output_with_special_tokens.csv"

merges_output = "bpe_merges.json"
vocab_output = "bpe_vocab.json"
vocab_limit = 250


def build_word_frequency(stories):

    word_freq = Counter()
    for story in stories:
        words = story.split()
        
        for word in words:

            # Convert word into characters and add end of word token
            char_word = " ".join(list(word)) + " </w>"
            word_freq[char_word] += 1

    return word_freq


def get_pair_frequency(word_freq):

    pair_freq = defaultdict(int)
    for word, freq in word_freq.items():

        tokens = word.split()

        # Count adjacent token pairs
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            pair_freq[pair] += freq

    return pair_freq


def merge_pair(pair, word_freq):

    merged_freq = {}

    # Join pair into single token
    pair_str = " ".join(pair)
    merged_token = "".join(pair)

    for word in word_freq:

        # Replace pair with merged token
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


# Load CSV
df = pd.read_csv(input_csv)

# Your story column name
story_col = "story_text_tokens"

stories = df[story_col].dropna().tolist()


# Build initial word frequency dictionary
word_freq = build_word_frequency(stories)

# Build initial vocabulary
vocab = build_vocab(word_freq)

merges = []

print("Starting BPE training...")


# Keep merging pairs until vocab size reaches limit
while len(vocab) < vocab_limit:

    pair_freq = get_pair_frequency(word_freq)

    if len(pair_freq) == 0:
        break

    # Find most frequent pair
    best_pair = max(pair_freq, key=pair_freq.get)

    # Merge best pair in corpus
    word_freq = merge_pair(best_pair, word_freq)
    merges.append(best_pair)

    # Update vocabulary
    vocab = build_vocab(word_freq)
    print("Current vocab size:", len(vocab))


# Save merges file
with open(merges_output, "w", encoding="utf-8") as f:
    json.dump(merges, f, ensure_ascii=False)

# Save vocabulary file
with open(vocab_output, "w", encoding="utf-8") as f:
    json.dump(list(vocab), f, ensure_ascii=False)

print("BPE training finished")
