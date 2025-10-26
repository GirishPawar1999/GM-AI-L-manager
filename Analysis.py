#!/usr/bin/env python3
"""
Email Summarization & Tone-Aware Reply Generation
-------------------------------------------------
Author: Girish Pawar
Purpose: Fine-tune a summarization model for email thread summarization,
detect tone via sentiment analysis, and generate context-aware replies.
"""

import os
import re
import torch
import numpy as np
import pandas as pd
from datasets import load_dataset, Dataset
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainer, Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq, pipeline
)
from evaluate import load as load_metric
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# -------------------------
# 1. SETUP
# -------------------------
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
LOCAL_MODEL_DIR = "./distilbart_finetuned"
BATCH_SIZE = 4
EPOCHS = 1
MAX_SOURCE_LEN = 512
MAX_TARGET_LEN = 150

os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

device = 0 if torch.cuda.is_available() else -1
print(f"✅ Using {'GPU' if device==0 else 'CPU'} for training.")

# -------------------------
# 2. LOAD TOKENIZER & MODEL
# -------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# -------------------------
# 3. LOAD DATASET
# -------------------------
print("⏳ Loading dataset from HuggingFace...")
hf_dataset = load_dataset("sidhq/email-thread-summary")
train_df = pd.DataFrame(hf_dataset["train"])

# -------------------------
# 4. DATA CLEANING
# -------------------------
def clean_email_text(text):
    """Remove signatures, email addresses, and redundant formatting."""
    if text is None:
        return ""
    text = re.sub(r"-----Original Message-----.*", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"__+|--+|\*\*+", " ", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def flatten_thread(thread):
    """Flatten email thread into a single text block."""
    if not isinstance(thread, dict):
        return ""
    subject = thread.get("subject", "")
    messages = thread.get("messages", [])
    cleaned = [clean_email_text(m.get("body", "")) for m in messages if isinstance(m, dict)]
    return subject + "\n" + "\n".join(cleaned)

train_df["flat_text"] = train_df["thread"].apply(flatten_thread)
train_df["summary"] = train_df["summary"].fillna("")

# -------------------------
# 5. TOKENIZATION
# -------------------------
def tokenize(batch):
    """Tokenize input (email thread) and target (summary)."""
    inputs = tokenizer(batch["flat_text"], max_length=MAX_SOURCE_LEN, truncation=True)
    targets = tokenizer(batch["summary"], max_length=MAX_TARGET_LEN, truncation=True)
    inputs["labels"] = targets["input_ids"]
    return inputs

train_dataset = Dataset.from_pandas(train_df)
tokenized_train = train_dataset.map(tokenize, batched=True)

# -------------------------
# 6. DATA COLLATOR
# -------------------------
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# -------------------------
# 7. TRAINING ARGUMENTS
# -------------------------
training_args = Seq2SeqTrainingArguments(
    output_dir=LOCAL_MODEL_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    weight_decay=0.01,
    num_train_epochs=EPOCHS,
    save_total_limit=2,
    logging_steps=50,
    fp16=device == 0,
    evaluation_strategy="epoch",
    push_to_hub=False
)

# -------------------------
# 8. EVALUATION METRIC (ROUGE)
# -------------------------
rouge_metric = load_metric("rouge")

def compute_metrics(eval_pred):
    """Compute ROUGE scores to evaluate summarization quality."""
    preds, labels = eval_pred
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    result = rouge_metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {k: round(v.mid.fmeasure * 100, 2) for k, v in result.items()}
    return result

# -------------------------
# 9. TRAINER
# -------------------------
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

print("⏳ Starting fine-tuning...")
trainer.train()
trainer.save_model(LOCAL_MODEL_DIR)
print(f"✅ Fine-tuned model saved at {LOCAL_MODEL_DIR}")

# -------------------------
# 10. SENTIMENT ANALYSIS (TONE DETECTION)
# -------------------------
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

def detect_tone(text):
    """Return sentiment tone label."""
    score = sia.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    return "Neutral"

# -------------------------
# 11. SUMMARIZATION PIPELINE
# -------------------------
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)

# -------------------------
# 12. REPLY GENERATION (FLAN-T5)
# -------------------------
reply_generator = pipeline("text2text-generation", model="google/flan-t5-base", device=device)

def summarize_and_reply(email_text):
    """Summarize email, detect tone, and generate context-aware reply."""
    summary = summarizer(email_text, max_length=120, min_length=30, do_sample=False)[0]["summary_text"]
    tone = detect_tone(email_text)
    prompt = f"The email tone is {tone}. Generate a polite, context-aware reply to this summary:\n{summary}"
    reply = reply_generator(prompt, max_length=80)[0]["generated_text"]
    return {"summary": summary, "tone": tone, "suggested_reply": reply}

# -------------------------
# 13. TESTING
# -------------------------
email_text = """
Subject: Meeting Reminder - Project Phoenix

Hi Team,
This is a friendly reminder that we have our Project Phoenix status update meeting tomorrow at 10:00 AM.
We'll discuss progress on deliverables and finalize the next sprint plan.
Best regards,
Sarah
"""

result = summarize_and_reply(email_text)

print("\n📨 Original Email:\n", email_text)
print("\n🧠 Summary:\n", result["summary"])
print("\n🎭 Tone:", result["tone"])
print("\n✉️ Suggested Reply:\n", result["suggested_reply"])

# -------------------------
# 14. EVALUATION INSIGHT
# -------------------------
# After training, ROUGE-L values and qualitative summaries are used
# to assess performance. Tone-based responses provide interpretability.
