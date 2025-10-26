import torch
import json
import sys
import re
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    pipeline,
)
from bs4 import BeautifulSoup

# ========== 1. DEVICE CHECK ==========
if torch.cuda.is_available():
    device = 0
    print(f"✅ CUDA available. Using GPU: {torch.cuda.get_device_name(0)}", file=sys.stderr)
else:
    device = -1
    print("⚠️ CUDA not available. Using CPU instead.", file=sys.stderr)

# ========== 2. MODEL LOADING ==========
print("⏳ Loading DistilBART summarizer, sentiment analyzer, and reply generator...", file=sys.stderr)

# Summarization model (DistilBART)
summarizer_model = "sshleifer/distilbart-cnn-12-6"
tokenizer_sum = AutoTokenizer.from_pretrained(summarizer_model)
model_sum = AutoModelForSeq2SeqLM.from_pretrained(summarizer_model)
summarizer = pipeline("summarization", model=model_sum, tokenizer=tokenizer_sum, device=device)

# Sentiment / tone model
tone_model = "distilbert-base-uncased-finetuned-sst-2-english"
tone_analyzer = pipeline("sentiment-analysis", model=tone_model, device=device)

# Smart Reply model
reply_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    device=device
)

print("✅ Models loaded successfully", file=sys.stderr)

# ========== 3. LOAD DATABASE AND TEMPLATES ==========
def load_json_file(filepath):
    """Load JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON from {filepath}: {e}", file=sys.stderr)
        return None

def save_json_file(filepath, data):
    """Save JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {filepath}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Error saving {filepath}: {e}", file=sys.stderr)
        return False

# ========== 4. CLEAN TEXT ==========
def clean_text(text):
    """Remove HTML tags and clean text"""
    if not text:
        return ""
    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()
    # Remove excessive whitespace, newlines, tabs
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.,!?\-]', '', text)
    return text.strip()

def is_html(text):
    """Check if text contains HTML"""
    if not text:
        return False
    return bool(re.search(r'<[^>]+>', text))

# ========== 5. IMPROVED CATEGORIZE EMAIL ==========
def categorize_email(subject, body, snippet, templates):
    """Categorize email based on keywords from template.json with improved matching"""
    subject_text = clean_text(subject).lower()
    body_text = clean_text(body).lower()
    snippet_text = clean_text(snippet).lower()
    
    combined_text = f"{subject_text} {subject_text} {body_text} {snippet_text}"
    
    categories = []
    category_scores = {}

    for rule in templates.get('rules', []):
        category = rule.get('category', '')
        keywords = rule.get('keywords', [])
        
        score = 0
        matched_keywords = []
        
        for kw in keywords:
            kw_lower = kw.lower().strip()
            if not kw_lower:
                continue
                
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            
            subject_matches = len(re.findall(pattern, subject_text))
            body_matches = len(re.findall(pattern, body_text))
            snippet_matches = len(re.findall(pattern, snippet_text))
            
            if subject_matches > 0:
                score += subject_matches * 3
                matched_keywords.append(kw)
            if body_matches > 0:
                score += body_matches * 2
                if kw not in matched_keywords:
                    matched_keywords.append(kw)
            if snippet_matches > 0:
                score += snippet_matches * 1
                if kw not in matched_keywords:
                    matched_keywords.append(kw)
        
        if score > 0:
            category_scores[category.lower()] = {
                'score': score,
                'matched': matched_keywords
            }

    for cat, data in category_scores.items():
        if data['score'] >= 2:
            categories.append(cat)
            print(f"  ✓ Matched category '{cat}' (score: {data['score']}, keywords: {', '.join(data['matched'])})", file=sys.stderr)

    return categories

# ========== 6. IMPROVED TONE DETECTION ==========
def detect_tone_advanced(text, sentiment_result):
    """Enhanced tone detection with dynamic weighting, extended keywords, and better confidence scaling"""
    if not text:
        return "Neutral", 0.5

    text_lower = text.lower()

    strong_positive = [
        "excellent", "outstanding", "amazing", "fantastic", "incredible",
        "wonderful", "brilliant", "delighted", "thrilled", "ecstatic", "success",
        "accomplished", "grateful", "appreciated", "congratulations", "congrats",
        "pleased", "proud", "love", "adore", "satisfied", "impressive"
    ]

    mild_positive = [
        "thank", "thanks", "good", "great", "nice", "well", "fine", "better",
        "okay", "pleasure", "cheers", "best", "appreciate", "helpful", "positive"
    ]

    strong_negative = [
        "angry", "furious", "terrible", "horrible", "awful", "frustrated",
        "disappointed", "upset", "devastated", "hate", "disgusted", "bad",
        "worst", "incompetent", "mistake", "error", "failed", "failure",
        "unacceptable", "useless", "broken", "problematic"
    ]

    mild_negative = [
        "sorry", "apologize", "issue", "concern", "delay", "problem", "regret",
        "cannot", "won't", "unable", "inconvenience", "unfortunately",
        "trouble", "complaint", "uncertain", "confused", "waiting", "pending"
    ]

    neutral_indicators = [
        "update", "information", "notice", "reminder", "fyi", "meeting",
        "schedule", "policy", "terms", "review", "confirm", "confirmation",
        "details", "reference", "attachment", "response", "report", "status"
    ]

    formal_tone = [
        "dear", "sincerely", "regards", "faithfully", "please find",
        "attached", "enclosed", "document", "submission", "application"
    ]

    urgency_tone = [
        "urgent", "immediately", "asap", "important", "critical",
        "deadline", "priority", "action required", "respond soon"
    ]

    motivational_positive = [
        "keep going", "well done", "great job", "good work",
        "you can do it", "don't give up", "proud of you", "congrats again"
    ]

    def count_weighted(words, weight=1.0):
        return sum(weight for kw in words if kw in text_lower)

    pos_score = (
        count_weighted(strong_positive, 2.0)
        + count_weighted(mild_positive, 1.0)
        + count_weighted(motivational_positive, 1.5)
    )
    neg_score = (
        count_weighted(strong_negative, 2.0)
        + count_weighted(mild_negative, 1.0)
    )
    neutral_score = count_weighted(neutral_indicators, 0.5)
    urgency_score = count_weighted(urgency_tone, 1.5)
    formal_score = count_weighted(formal_tone, 0.5)

    label = sentiment_result.get("label", "NEUTRAL").upper()
    model_conf = sentiment_result.get("score", 0.5)

    tone = "Neutral"
    combined_conf = 0.6

    if label == "POSITIVE" and pos_score > neg_score:
        tone = "Positive"
        combined_conf = 0.7 + (pos_score * 0.03)
    elif label == "NEGATIVE" and neg_score > pos_score:
        tone = "Negative"
        combined_conf = 0.7 + (neg_score * 0.03)
    elif pos_score > neg_score + 1:
        tone = "Positive"
        combined_conf = 0.6 + (pos_score * 0.02)
    elif neg_score > pos_score + 1:
        tone = "Negative"
        combined_conf = 0.6 + (neg_score * 0.02)
    elif urgency_score > 0:
        tone = "Negative" if neg_score > 0 else "Neutral"
        combined_conf = 0.65 + (urgency_score * 0.05)
    elif formal_score > 1 and neutral_score > 1:
        tone = "Neutral"
        combined_conf = 0.7
    else:
        tone = "Neutral"
        combined_conf = 0.5 + (abs(pos_score - neg_score) * 0.02)

    combined_conf = (combined_conf + model_conf) / 2
    combined_conf = min(round(combined_conf, 2), 0.99)

    print(
        f"🧩 Tone={tone}, Pos={pos_score:.1f}, Neg={neg_score:.1f}, Urgency={urgency_score:.1f}, Model={label}({model_conf:.2f})",
        file=sys.stderr,
    )

    return tone, combined_conf

# ========== 7. SMART REPLY GENERATION ==========
def generate_smart_reply(email_subject, email_body, email_snippet):
    """Generate smart reply suggestions using Flan-T5"""
    try:
        # Use snippet or body for context
        email_text = clean_text(email_body) if email_body and len(email_body) < 500 else clean_text(email_snippet)
        
        # Limit text length
        if len(email_text) > 300:
            email_text = email_text[:300]
        
        # Create prompt
        prompt = f"Write a polite and professional email reply to this message:\n\nSubject: {email_subject}\nMessage: {email_text}\n\nReply:"
        
        # Generate reply
        response = reply_generator(prompt, max_length=150, min_length=20, do_sample=False)[0]['generated_text']
        
        print(f"  🤖 Generated smart reply: {response[:50]}...", file=sys.stderr)
        return response.strip()
        
    except Exception as e:
        print(f"  ⚠️ Smart reply generation failed: {e}", file=sys.stderr)
        return "Thank you for your email. I'll get back to you shortly."

# ========== 8. PROCESS EMAIL ==========
def process_email(email_data, templates, ai_settings):
    """Analyze a single email for summary, tone, and smart reply"""
    try:
        email_id = email_data.get('id', 'unknown')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        snippet = email_data.get('snippet', '')

        # Check if body is HTML
        if is_html(body):
            print(f"  📧 Email {email_id}: HTML detected, using snippet for summary", file=sys.stderr)
            text_for_summary = f"Subject: {subject}\n\n{clean_text(snippet)}"
        else:
            plain_text = clean_text(body) if body else clean_text(snippet)
            text_for_summary = f"Subject: {subject}\n\n{plain_text}"

        # Truncate if too long
        if len(text_for_summary) > 3000:
            text_for_summary = text_for_summary[:3000]

        # Generate summary if enabled and text is long enough
        if ai_settings.get("emailSummarization", True) and len(text_for_summary.split()) > 30:
            try:
                summary_result = summarizer(
                    text_for_summary, 
                    max_length=120, 
                    min_length=30, 
                    do_sample=False,
                    truncation=True
                )[0]["summary_text"]
            except Exception as e:
                print(f"  ⚠️ Summarization failed: {e}", file=sys.stderr)
                summary_result = text_for_summary[:120]
        else:
            summary_result = text_for_summary[:120]

        # Detect tone
        tone_text = text_for_summary[:512]
        try:
            tone_result = tone_analyzer(tone_text)[0]
            tone, confidence = detect_tone_advanced(tone_text, tone_result)
        except Exception as e:
            print(f"  ⚠️ Tone detection failed: {e}", file=sys.stderr)
            tone = "Neutral"
            confidence = 0.5

        # Categorize email
        categories = categorize_email(subject, body, snippet, templates)
        
        if categories:
            print(f"  ✓ Categorized as: {', '.join(categories)}", file=sys.stderr)

        # Generate smart reply if enabled
        smart_reply = None
        if ai_settings.get("smartReplyGeneration", True):
            smart_reply = generate_smart_reply(subject, body, snippet)

        result = {
            "aiSummary": {
                "summary": summary_result,
                "tone": tone,
                "confidence": round(confidence, 2)
            },
            "categories": categories
        }
        
        if smart_reply:
            result["smartReply"] = smart_reply

        return result

    except Exception as e:
        print(f"⚠️ Error processing email {email_data.get('id', 'unknown')}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        
        return {
            "aiSummary": {
                "summary": clean_text(email_data.get('snippet', 'Unable to generate summary'))[:120],
                "tone": "Neutral",
                "confidence": 0.0
            },
            "categories": []
        }

# ========== 9. MAIN EXECUTION ==========
def main():
    # Load AI settings first
    print("📂 Loading AI_settings.json...", file=sys.stderr)
    ai_settings = load_json_file("AI_settings.json")
    if not ai_settings:
        print("⚠️ AI settings not found, using defaults", file=sys.stderr)
        ai_settings = {
            "emailSummarization": True, 
            "aiAutoCategorization": True,
            "smartReplyGeneration": True
        }
    
    # Check if AI processing is disabled
    if not ai_settings.get("emailSummarization", True):
        print("ℹ️ Email summarization is disabled, skipping AI processing", file=sys.stderr)
        sys.exit(0)
    
    # Load database
    print("📂 Loading database.json...", file=sys.stderr)
    database = load_json_file("database.json")
    if not database:
        print("❌ Failed to load database.json", file=sys.stderr)
        sys.exit(1)

    # Load templates
    print("📂 Loading template.json...", file=sys.stderr)
    templates = load_json_file("template.json")
    if not templates:
        print("❌ Failed to load template.json", file=sys.stderr)
        sys.exit(1)

    emails = database.get('emails', [])
    if not emails:
        print("⚠️ No emails found in database", file=sys.stderr)
        sys.exit(0)

    print(f"📧 Processing {len(emails)} emails...", file=sys.stderr)

    # Process each email
    updated_count = 0
    for idx, email in enumerate(emails, 1):
        # Only process emails without aiSummary or with new_email flag
        if email.get('new_email', False) or not email.get('aiSummary'):
            print(f"  Processing email {idx}/{len(emails)}: {email.get('subject', 'No subject')[:50]}...", file=sys.stderr)
            
            analysis = process_email(email, templates, ai_settings)
            
            # Update email with AI summary
            email['aiSummary'] = analysis['aiSummary']
            
            # Add smart reply if available
            if 'smartReply' in analysis:
                email['smartReply'] = analysis['smartReply']
            
            # Add categories to labels if auto-categorization is enabled
            if ai_settings.get("aiAutoCategorization", True):
                existing_labels = email.get('labels', [])
                new_categories = analysis['categories']
                
                # Remove old AI categories first
                ai_categories = [r['category'].lower() for r in templates.get('rules', [])]
                existing_labels = [l for l in existing_labels if l not in ai_categories]
                
                # Merge new categories with existing labels
                all_labels = list(set(existing_labels + new_categories))
                email['labels'] = all_labels
            
            # Clear new_email flag after processing
            email['new_email'] = False
            
            updated_count += 1
        else:
            print(f"  Skipping email {idx}/{len(emails)}: Already processed", file=sys.stderr)

    print(f"✅ Updated {updated_count} emails", file=sys.stderr)

    # Save updated database
    print("💾 Saving updated database...", file=sys.stderr)
    if save_json_file("database.json", database):
        print("✅ Processing complete!", file=sys.stderr)
    else:
        print("❌ Failed to save database", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()