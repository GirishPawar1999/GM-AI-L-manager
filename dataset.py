#!/usr/bin/env python3
"""
gm_ai_data_analysis.py (patched + tone export)

Standalone script to:
- Load Hugging Face "sidhq/email-thread-summary" dataset
- Optionally download Kaggle dataset
- Perform Data Quality checks, Data Preparation, Feature Engineering
- Produce visualizations for presentation (saved to ./outputs)

This version includes:
- Robust plotting (NaN handling, index alignment)
- Per-message tone export (hf_message_tones.csv)
- Tone distribution chart
"""

import os
import re
import argparse
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

# --- Optional libraries ---
try:
    from datasets import load_dataset
except Exception:
    raise ImportError("Please install 'datasets': pip install datasets")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
except Exception:
    nltk = None

# ---------------------------
# Setup
# ---------------------------
OUT_DIR = "./outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def save_fig(fig, name):
    try:
        path = os.path.join(OUT_DIR, name)
        fig.savefig(path, bbox_inches="tight", dpi=150)
        print(f"Saved: {path}")
    except Exception as e:
        print(f"Failed to save figure {name}: {e}")

# ---------------------------
# Load HuggingFace dataset
# ---------------------------
def load_hf_dataset(hf_name="sidhq/email-thread-summary"):
    print("Loading Hugging Face dataset:", hf_name)
    ds = load_dataset(hf_name)
    dfs = {}
    for split in ds.keys():
        print(f" - Converting split '{split}' to pandas")
        df = pd.DataFrame(ds[split])
        dfs[split] = df
        print(f"   {split}: {len(df)} rows")
    return dfs

# ---------------------------
# Cleaning & flattening
# ---------------------------
def clean_email_text(text):
    if text is None:
        return ""
    text = re.sub(r"-----Original Message-----.*", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"__+|--+|\*\*+", " ", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def flatten_thread(thread):
    if not isinstance(thread, dict):
        return "", "", []
    subject = thread.get("subject", "") or ""
    messages = thread.get("messages", []) or []
    cleaned_messages = []
    for m in messages:
        body = m.get("body", "") if isinstance(m, dict) else str(m)
        cleaned_messages.append(clean_email_text(body))
    flat = subject + " \n " + " \n ".join(cleaned_messages)
    return flat, subject, cleaned_messages

# ---------------------------
# Feature engineering
# ---------------------------
URGENCY_KEYWORDS = ["urgent", "asap", "immediately", "important", "priority", "deadline", "due"]
MEETING_KEYWORDS = ["zoom", "google meet", "meet", "meeting", "invite", "calendar", "ms teams"]
ZOOM_REGEX = re.compile(r"\b(zoom\.us|zoom)\b", flags=re.I)
URL_REGEX = re.compile(r"https?://\S+")

def derive_features_from_thread(row):
    thread = row["thread"] if isinstance(row, pd.Series) and "thread" in row else row
    flat, subject, cleaned_messages = flatten_thread(thread)
    num_messages = len(cleaned_messages)
    total_words = sum(len(m.split()) for m in cleaned_messages)
    num_chars = sum(len(m) for m in cleaned_messages)
    contains_urgent = any(any(kw in (m or "").lower() for kw in URGENCY_KEYWORDS) for m in cleaned_messages)
    contains_meeting = any(any(kw in (m or "").lower() for kw in MEETING_KEYWORDS) for m in cleaned_messages)
    has_zoom = any(bool(ZOOM_REGEX.search(m or "")) for m in cleaned_messages)
    url_count = sum(len(URL_REGEX.findall(m or "")) for m in cleaned_messages)
    avg_msg_len = (total_words / num_messages) if num_messages > 0 else 0
    return {
        "flat_text": flat,
        "subject": subject,
        "cleaned_messages": cleaned_messages,
        "num_messages": int(num_messages),
        "total_words": int(total_words),
        "num_chars": int(num_chars),
        "avg_message_words": float(avg_msg_len),
        "contains_urgent": int(bool(contains_urgent)),
        "contains_meeting": int(bool(contains_meeting)),
        "has_zoom": int(bool(has_zoom)),
        "url_count": int(url_count)
    }

# ---------------------------
# Tone detection
# ---------------------------
def ensure_nltk_and_sia():
    global nltk
    if nltk is None:
        import nltk as _nltk
        nltk = _nltk
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except Exception:
        print("Downloading VADER lexicon...")
        nltk.download("vader_lexicon")
    return SentimentIntensityAnalyzer()

def compute_thread_sentiment(cleaned_messages, sia):
    scores = [sia.polarity_scores(m)["compound"] for m in cleaned_messages if m and m.strip()]
    return float(np.mean(scores)) if scores else 0.0

def export_message_tones(df, sia, fname="hf_message_tones.csv"):
    rows = []
    for idx, row in df.iterrows():
        subject = row.get("subject", "")
        msgs = row.get("cleaned_messages", [])
        if not isinstance(msgs, list):
            continue
        for midx, msg in enumerate(msgs):
            if not msg.strip():
                continue
            score = sia.polarity_scores(msg)["compound"]
            if score >= 0.05:
                tone = "Positive"
            elif score <= -0.05:
                tone = "Negative"
            else:
                tone = "Neutral"
            rows.append({
                "thread_index": idx,
                "subject": subject,
                "message_index": midx,
                "message_text": msg[:300],
                "compound_score": score,
                "tone": tone
            })
    if rows:
        out_df = pd.DataFrame(rows)
        out_csv = os.path.join(OUT_DIR, fname)
        out_df.to_csv(out_csv, index=False)
        print(f"Message-level tones saved to: {out_csv}")
        # Plot distribution
        tone_counts = Counter(out_df["tone"])
        fig = plt.figure(figsize=(5,4))
        plt.bar(tone_counts.keys(), tone_counts.values())
        plt.title("Tone Distribution (per message)")
        save_fig(fig, "tone_distribution.png")
        plt.close(fig)

# ---------------------------
# Visualization helpers
# ---------------------------
def plot_hist(series, title, xlabel, ylabel="Count", bins=30, fname="plot.png"):
    try:
        fig = plt.figure(figsize=(7,4))
        plt.hist(series.dropna(), bins=bins)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        save_fig(fig, fname)
        plt.close(fig)
    except Exception as e:
        print(f"plot_hist failed for {fname}: {e}")

def plot_bar_from_counts(counter, topn=10, title="", xlabel="", fname="bar.png"):
    try:
        items = counter.most_common(topn)
        if not items:
            return
        keys, vals = zip(*items)
        fig = plt.figure(figsize=(8,4))
        plt.bar(range(len(keys)), vals)
        plt.xticks(range(len(keys)), keys, rotation=45, ha="right")
        plt.title(title)
        plt.xlabel(xlabel)
        save_fig(fig, fname)
        plt.close(fig)
    except Exception as e:
        print(f"plot_bar_from_counts failed for {fname}: {e}")

def plot_scatter(x, y, title, xlabel, ylabel, fname):
    try:
        x_s = pd.Series(np.ravel(x)).astype(float)
        y_s = pd.Series(np.ravel(y)).astype(float)
        mask = (~x_s.isna()) & (~y_s.isna())
        x_clean, y_clean = x_s[mask], y_s[mask]
        if len(x_clean) == 0:
            return
        fig = plt.figure(figsize=(7,5))
        plt.scatter(x_clean, y_clean, alpha=0.6, s=8)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True, alpha=0.3)
        save_fig(fig, fname)
        plt.close(fig)
    except Exception as e:
        print(f"plot_scatter failed for {fname}: {e}")

def plot_pca_tfidf(texts, labels_binary, fname="pca.png"):
    try:
        texts = list(texts)
        if not texts:
            return
        vec = TfidfVectorizer(max_features=1000, stop_words="english")
        X = vec.fit_transform(texts).toarray()
        coords = PCA(n_components=2, random_state=42).fit_transform(X)
        c = np.array(labels_binary)
        if len(c) != coords.shape[0]:
            c = np.resize(c, coords.shape[0])
        fig = plt.figure(figsize=(7,6))
        plt.scatter(coords[:,0], coords[:,1], c=c, cmap="coolwarm", alpha=0.6, s=12)
        plt.title("PCA of TF-IDF (by urgency)")
        plt.xlabel("PC1")
        plt.ylabel("PC2")
        save_fig(fig, fname)
        plt.close(fig)
    except Exception as e:
        print(f"plot_pca_tfidf failed for {fname}: {e}")

# ---------------------------
# Main analysis
# ---------------------------
def analyze_hf_and_kaggle():
    dfs = load_hf_dataset()
    df = dfs.get("train")
    print(f"Using {len(df)} threads.")

    # QC
    df["num_messages"] = df["thread"].apply(lambda t: len(t.get("messages", [])) if isinstance(t, dict) else 0)
    df["summary_len_words"] = df["summary"].apply(lambda s: len(str(s).split()))
    df[["num_messages","summary_len_words"]].to_csv(os.path.join(OUT_DIR,"hf_data_qc.csv"), index=False)

    plot_hist(df["num_messages"], "Messages per Thread", "Number of messages", bins=20, fname="messages_per_thread.png")
    plot_hist(df["summary_len_words"], "Summary Length (words)", "Words in summary", bins=20, fname="summary_length_hist.png")

    # Features
    feats = df.apply(lambda r: pd.Series(derive_features_from_thread(r)), axis=1)
    df = pd.concat([df, feats], axis=1)

    subj_counts = Counter(df["subject"].fillna("").astype(str))
    plot_bar_from_counts(subj_counts, topn=10, title="Top Subjects", xlabel="Subject", fname="top_subjects.png")

    urgent_count = int(df["contains_urgent"].sum())
    fig = plt.figure(figsize=(4,3))
    plt.bar(["no_urgent","urgent"], [len(df)-urgent_count, urgent_count])
    plt.title("Urgency (keyword heuristic)")
    save_fig(fig,"urgent_count.png")
    plt.close(fig)

    plot_scatter(df["num_messages"], df["total_words"], "Total words vs Number of messages",
                 "Number of messages", "Total words", "words_vs_messages.png")

    # Tone
    sia = ensure_nltk_and_sia()
    df["avg_sentiment"] = df["cleaned_messages"].apply(lambda msgs: compute_thread_sentiment(msgs, sia))
    plot_hist(df["avg_sentiment"], "Average Thread Sentiment", "Compound sentiment", bins=30, fname="avg_sentiment_hist.png")

    export_message_tones(df, sia)

    # PCA
    plot_pca_tfidf(df["flat_text"].fillna(""), df["contains_urgent"], fname="pca_tfidf_urgent.png")

    print("\nAnalysis complete. Outputs in:", os.path.abspath(OUT_DIR))

if __name__ == "__main__":
    analyze_hf_and_kaggle()
