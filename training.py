#!/usr/bin/env python3
import os
import re
import torch
import numpy as np
import pandas as pd
from datasets import load_dataset, Dataset
from transformers import (AutoTokenizer, AutoModelForSeq2SeqLM,
                          Seq2SeqTrainer, Seq2SeqTrainingArguments,
                          DataCollatorForSeq2Seq, pipeline)
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# -------------------------
# 1. SETUP
# -------------------------
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
LOCAL_MODEL_DIR = "./distilbart_finetuned"
BATCH_SIZE = 4
EPOCHS = 1  # adjust as needed
MAX_SOURCE_LEN = 512
MAX_TARGET_LEN = 150

os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

# Device
device = 0 if torch.cuda.is_available() else -1
print(f"✅ Using {'GPU' if device==0 else 'CPU'}")

# -------------------------
# 2. LOAD TOKENIZER & MODEL
# -------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# -------------------------
# 3. LOAD DATASET
# -------------------------
print("⏳ Loading HuggingFace dataset...")
hf_dataset = load_dataset("sidhq/email-thread-summary")
train_df = pd.DataFrame(hf_dataset["train"])

# -------------------------
# 4. CLEAN & PREPROCESS
# -------------------------
def clean_email_text(text):
    if text is None: return ""
    text = re.sub(r"-----Original Message-----.*", " ", text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r"__+|--+|\*\*+", " ", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def flatten_thread(thread):
    subject = thread.get("subject","") if isinstance(thread, dict) else ""
    messages = thread.get("messages",[]) if isinstance(thread, dict) else []
    cleaned_messages = [clean_email_text(m.get("body","")) for m in messages if isinstance(m, dict)]
    flat_text = subject + " \n " + " \n ".join(cleaned_messages)
    return flat_text

train_df["flat_text"] = train_df["thread"].apply(flatten_thread)
train_df["summary"] = train_df["summary"].fillna("")

# -------------------------
# 5. TOKENIZATION
# -------------------------
def tokenize(batch):
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
# 7. TRAINING ARGS (compatible older transformers)
# -------------------------
training_args = Seq2SeqTrainingArguments(
    output_dir=LOCAL_MODEL_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    weight_decay=0.01,
    save_total_limit=2,
    num_train_epochs=EPOCHS,
    logging_steps=50,
    fp16=device==0,
    push_to_hub=False
)

# -------------------------
# 8. TRAINER
# -------------------------
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    tokenizer=tokenizer,
    data_collator=data_collator
)

print("⏳ Starting fine-tuning...")
trainer.train()
print(f"✅ Fine-tuned model saved at {LOCAL_MODEL_DIR}")
trainer.save_model(LOCAL_MODEL_DIR)

# -------------------------
# 9. TONE DETECTION
# -------------------------
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

def detect_tone(text):
    score = sia.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# -------------------------
# 10. SUMMARIZATION + TONE-AWARE REPLY
# -------------------------
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)

def summarize_and_reply(email_text):
    summary = summarizer(email_text, max_length=120, min_length=30, do_sample=False)[0]["summary_text"]
    tone = detect_tone(email_text)
    reply = ""
    if tone == "Positive":
        reply = f"Thank you for your update. {summary}"
    elif tone == "Negative":
        reply = f"I noticed some concerns in your message. {summary} Let's address them promptly."
    else:
        reply = f"Noted. {summary}"
    return {"summary": summary, "tone": tone, "suggested_reply": reply}

# -------------------------
# 11. TEST ON HARD-CODED EMAIL
# -------------------------
email_text = """
Subject: Meeting Reminder - Project Phoenix

Hi Team,

This is a friendly reminder that we have our Project Phoenix status update meeting tomorrow at 10:00 AM in the main conference room.
We’ll discuss progress on deliverables, blockers, and finalize the next sprint plan. Please ensure that your reports and updated task lists are ready.
If you have any urgent issues that need to be added to the agenda, email me tonight.

Best regards,
Sarah Johnson
Project Manager
"""

result = summarize_and_reply(email_text)
print("\n📨 Original Email:\n", email_text)
print("\n🧠 Summarized Content:\n", result["summary"])
print("\n🎭 Detected Tone:", result["tone"])
print("\n✉️ Suggested Reply:\n", result["suggested_reply"])
