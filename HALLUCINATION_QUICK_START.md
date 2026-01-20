# Hallucination Prevention - Quick Start Guide

## What Changed

The system now **automatically prevents hallucinations** by:
1. Checking responses against live web sources
2. Deprioritizing Wikipedia (score reduced from 0.70 to 0.35)
3. Detecting false claims and unverifiable references
4. Assigning confidence levels to all responses
5. Providing verified sources to users

---

## For Users

### Standard Usage (Automatic Hallucination Detection)

**Send a question:**
```
POST /ask
{
  "message": "What is Python?",
  "user_id": "user_123"
}
```

**You'll get:**
- Response text
- Confidence level: HIGH, MEDIUM, or LOW
- Issues detected (if any)
- Hallucination flag (if detected)

### Best Practice: Use `/ask-verified` for Sensitive Topics

For important information, use the verified endpoint:
```
POST /ask-verified
{
  "message": "What is the current version of Python?",
  "user_id": "user_123"
}
```

**You'll get:**
- Response with live web verification
- [VERIFIED] badge if sources confirm information
- Links to official sources
- Confidence level based on multiple sources

---

## For Developers

### Integration Example

```python
from response_quality import check_response

# Check any response for hallucinations
result = check_response(
    response_text="Python was created in 1991",
    query="When was Python created?",
    response_type="web_search"
)

# Get results
if result['confidence_level'] == 'LOW':
    print(f"WARNING: Low confidence response")
    print(f"Issues: {result['issues']}")
    
if result['hallucinations_detected']:
    print("Hallucination detected - do not publish")
    
if result['verified_sources']:
    print(f"Verified sources: {result['verified_sources']}")
```

### What Gets Flagged as Hallucination

**HIGH RISK (Automatically Blocked/Flagged):**
- Future dates: "As of March 25, 2025" (when it's 2026)
- Unverifiable references: "GitHub - unknown-repo"
- False framework descriptions: "PyTorch is a programming language"
- Wikipedia-only sources for technical topics
- Conflicting or inconsistent information

**MEDIUM RISK (Confidence Reduced):**
- Generic filler content
- Promotional language
- Unverified claims
- Single source only

**LOW RISK (Normal Processing):**
- Multi-source verification
- Official documentation references
- Recent news from reputable outlets
- Academic citations

---

## Configuration

### Adjust Source Scores

Edit `response_quality.py` to change how sources are scored:

```python
CREDIBLE_SOURCES = {
    "official": 0.95,           # Official sites - trusted most
    "academic": 0.90,           # University research
    "reputable_news": 0.85,     # BBC, Reuters, etc
    "technical_blog": 0.75,     # Tech blogs
    "wiki": 0.35,               # Wikipedia (LOW)
    "unknown": 0.40,            # Unknown source
}
```

### Adjust Penalty Thresholds

Control how much each issue reduces confidence:

```python
# In check_date_accuracy()
"confidence_penalty": 0.3  # How much to penalize future dates

# In check_for_wikipedia_only()
"confidence_penalty": 0.20  # How much to penalize Wikipedia-only
```

---

## Examples

### Example 1: Response with Hallucination (Detected)

**User asks:** "What's the latest version of Python as of March 2025?"

**System detects:**
- Future date reference (March 2025 is future from Jan 2026)
- Unverifiable claim

**Response:**
```
Python 3.13 is the latest version (hallucinated info...)

[CONFIDENCE: LOW] - Issues: Date 'March 2025' is outdated; 
Information not verifiable with current web sources
[UNVERIFIED] - Could not confirm with web search
```

### Example 2: Response with Web Verification

**User asks:** "What is Python programming language?"

**System performs:**
- Web search for "Python programming language"
- Finds official python.org
- Matches response against official content
- Boosts confidence

**Response:**
```
Python is a high-level, interpreted programming language...

[VERIFIED] - Information checked against web sources

Verified Sources:
- Python Official: https://www.python.org
- Python Documentation: https://docs.python.org/3/
```

### Example 3: Wikipedia-Only Source (Flagged)

**User asks:** "Tell me about machine learning"

**System detects:**
- Only Wikipedia mentioned
- No official sources found
- Generic content

**Response:**
```
Machine learning is a field of artificial intelligence (Wikipedia definition)...

[CONFIDENCE: LOW] - Information only found on Wikipedia
[UNVERIFIED] - Consider consulting official academic sources
Recommendation: Verify with academic institutions or official ML frameworks
```

---

## Monitoring Quality

### Check Quality of Responses

```python
# Enable quality logging
import logging
logging.getLogger('app').setLevel(logging.INFO)

# Now all responses log their confidence level
# Check app logs for: "Response confidence: HIGH" or "LOW"
```

### Quality Metrics to Watch

1. **Confidence Distribution:**
   - HIGH: 60%+ (Desired)
   - MEDIUM: 30-40% (Acceptable)
   - LOW: <10% (Investigate)

2. **Hallucination Rate:**
   - <2% of responses (Target)
   - Track with `hallucinations_detected` flag

3. **Web Verification Rate:**
   - 70%+ for `/ask-verified` (Target)
   - Check `web_verified` flag

4. **Wikipedia Dependency:**
   - <5% of responses (Target)
   - Monitor via `verified_sources`

---

## Testing

### Test Case 1: Future Date Detection

```bash
curl -X POST http://localhost:5000/ask-verified \
  -H "Content-Type: application/json" \
  -d '{
    "message": "As of March 25, 2025, what is the status?",
    "user_id": "test"
  }'
```

**Expected:** LOW confidence, hallucination detected

### Test Case 2: Official Source Verification

```bash
curl -X POST http://localhost:5000/ask-verified \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?",
    "user_id": "test"
  }'
```

**Expected:** HIGH/MEDIUM confidence, verified sources listed

### Test Case 3: Unverifiable Claim

```bash
curl -X POST http://localhost:5000/ask-verified \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about GitHub - mysterious-repo/code",
    "user_id": "test"
  }'
```

**Expected:** LOW confidence, unverifiable claim flagged

---

## Troubleshooting

### Issue: Low confidence on valid responses

**Cause:** Too many strict checks or wrong source scores

**Fix:**
1. Adjust `CREDIBLE_SOURCES` scores
2. Reduce penalty amounts
3. Check if Wikipedia is too heavily penalized

### Issue: Hallucinations still appearing

**Cause:** New hallucination patterns not detected

**Fix:**
1. Add new detection pattern in `response_quality.py`
2. Increase penalty for existing patterns
3. Use `/ask-verified` endpoint for critical info

### Issue: Web verification very slow

**Cause:** Web search taking too long

**Fix:**
1. Reduce `max_results` in `search_web()` call
2. Enable caching for common queries
3. Use timeout limits on fetches

---

## API Reference

### Response Format

All responses from `/ask` and `/ask-verified` include:

```json
{
  "confidence_level": "HIGH|MEDIUM|LOW",
  "confidence_score": 0.0-1.0,
  "hallucinations_detected": true|false,
  "issues": ["issue 1", "issue 2"],
  "verified_sources": [
    {
      "url": "https://source.com",
      "title": "Source Title",
      "credibility": 0.85
    }
  ],
  "web_verified": true|false,
  "sources": ["source1", "source2"]
}
```

### Quality Check Levels

```
CRITICAL (Red Flag):   -0.35 to -0.3 confidence
HIGH (Warning):        -0.25 to -0.2 confidence
MEDIUM (Caution):      -0.15 confidence
LOW (Note):            -0.1 confidence
```

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| Hallucination Detection | Basic | **Advanced with web verification** |
| Wikipedia Scoring | 0.70 | **0.35 (Deprioritized)** |
| Confidence Levels | Manual | **Automatic with source credibility** |
| Web Verification | No | **Yes, built-in** |
| Source Attribution | Limited | **Complete with credibility scores** |

**Result:** Trustworthy, verifiable responses with transparent confidence indicators.
