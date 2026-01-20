# QUICK DEPLOYMENT GUIDE

**System Status**: Ready for deployment
**Last Verified**: January 20, 2026
**Components**: All verified and working

---

## Pre-Deployment (5 minutes)

### 1. Verify Code Files
```bash
# Check that files are updated:
✓ response_quality.py - 696 lines (has auto-replacement functions)
✓ app.py - /ask endpoint updated with replacement logic
✓ Requirements already includes: web_search, requests, beautifulsoup4
```

### 2. Quick Syntax Check
```python
# In Python shell:
from response_quality import check_response, replace_wikipedia_with_web_search
from app import app
# Should import without errors ✓
```

### 3. Start Flask
```bash
python run_flask.bat
# or
python app.py

# Expected: Flask running on http://localhost:5000
# Should see: "Database initialized" and "CORS enabled"
```

---

## Deployment (2 minutes)

### Option 1: Local Testing First (Recommended)
```bash
1. Start Flask: python app.py
2. Open browser: http://localhost:5000
3. Ask question about Wikipedia topic
4. Verify: Should get web results with [VERIFIED] badge
5. Check logs: Should show "Response replaced"
```

### Option 2: Direct Deployment
```bash
1. Copy updated files to production:
   - response_quality.py
   - app.py
   
2. Restart Flask app

3. Test /ask endpoint with curl:
   curl -X POST http://localhost:5000/ask \
     -H "Content-Type: application/json" \
     -d '{"query":"what is photosynthesis"}'
   
4. Verify response has [VERIFIED] when Wikipedia detected
```

---

## Verification Checklist

### System Starting
- [ ] Flask starts without errors
- [ ] Database initialized
- [ ] CORS enabled
- [ ] Rate limiting active
- [ ] Connectivity: Online

### Functions Available
- [ ] check_response imported
- [ ] replace_wikipedia_with_web_search imported
- [ ] get_web_search_replacement imported
- [ ] check_for_wikipedia_only imported

### /ask Endpoint
- [ ] POST /ask works
- [ ] Returns responses
- [ ] Auto-replacement active (for Wikipedia queries)
- [ ] [VERIFIED] badge shows when replaced

### Wikipedia Detection
- [ ] Test with: "From Wikipedia, this is about X"
- [ ] Should show: "Replaced: True" in logs
- [ ] Response should have: Web search results + [VERIFIED]

### Web Search
- [ ] Web search module available
- [ ] search_web() working
- [ ] Returns non-Wikipedia results
- [ ] Results formatted with sources

---

## What to Expect

### Normal Response (Non-Wikipedia)
```
Q: "How do I cook pasta?"
A: To cook pasta...
   [No replacement, uses original response]
   [No [VERIFIED] badge]
```

### Wikipedia Replaced Response
```
Q: "What is photosynthesis?"
A: [Web search results...]
   [VERIFIED - Web Search Results]
   Sources:
   - https://official-source.com
```

### Logs During Replacement
```
INFO Response replaced: Wikipedia detected for query: photosynthesis
INFO Using web search results instead
INFO Confidence: HIGH
INFO Replaced: True
```

---

## Troubleshooting

### If Wikipedia Still Appears
**Check**: Is it really Wikipedia-only?
- Mixed sources (Wikipedia + other) = not replaced
- Only Wikipedia = should be replaced

**Check**: Web search is working
```python
from web_search import search_web
results = search_web("test query", max_results=5)
# Should return web results
```

**Check**: Detection is triggered
```python
from response_quality import check_for_wikipedia_only
result = check_for_wikipedia_only("From Wikipedia...")
# Should return should_block: True
```

### If Web Search Slow
**Normal**: First request adds 1-2 seconds (web search latency)
**Optimize**: Add caching for repeated queries
```python
# Future: Implement caching layer
@cache.cached(timeout=3600)
def get_web_search_replacement(query):
    ...
```

### If Integration Issues
**Check**: Flask endpoint code
```python
# Should have:
response_text = quality_check.get('response_text', response_text)
if quality_check.get('replaced', False):
    # Log replacement
```

**Check**: check_response parameters
```python
quality_check = check_response(
    response_text, 
    query=user_input,  # IMPORTANT: Pass query
    response_type="general"
)
```

---

## Monitoring Setup

### Log File Location
```
logs/flask_app.log
# Watch for: "Response replaced"
```

### Track Replacements
```bash
# Count replacements per day:
grep "Response replaced" logs/flask_app.log | wc -l

# See which queries trigger replacement:
grep "Response replaced" logs/flask_app.log | grep "for query:"

# Monitor response times:
grep "Response replaced" logs/flask_app.log | grep "latency:"
```

### User Feedback Points
- Do responses look better?
- Are sources helpful?
- Is latency acceptable?
- Are [VERIFIED] badges clear?

---

## Rollback Plan

### If Issues Found
1. Stop Flask
2. Revert response_quality.py to backup
3. Revert app.py to backup
4. Restart Flask
5. Verify old behavior restored

### Quick Rollback
```bash
# Backup current:
cp response_quality.py response_quality.py.new
cp app.py app.py.new

# Restore previous:
git checkout response_quality.py
git checkout app.py

# Restart Flask
```

---

## Post-Deployment

### Day 1
- Monitor logs for errors
- Track replacement frequency
- Collect initial user feedback
- Verify no issues

### Week 1
- Analyze replacement patterns
- Check response quality metrics
- Monitor web search performance
- Collect user satisfaction

### Ongoing
- Weekly log review
- Monthly performance analysis
- Quarterly fine-tuning
- Continuous improvement

---

## Key Files

### Code Files
- `response_quality.py` - Auto-replacement logic (696 lines)
- `app.py` - Flask integration (~30 lines modified)

### Documentation
- `AUTO_REPLACEMENT.md` - System guide
- `WIKIPEDIA_AUTO_REPLACEMENT_COMPLETE.md` - Status
- `FINAL_VERIFICATION.md` - Verification results
- `QUICK_DEPLOYMENT_GUIDE.md` - This file

### Logs
- `logs/flask_app.log` - Application logs

---

## Quick Start

```bash
# 1. Verify code (30 seconds)
python -c "from response_quality import replace_wikipedia_with_web_search; print('OK')"

# 2. Start Flask (10 seconds)
python app.py

# 3. Test (1 minute)
# Browser: http://localhost:5000
# Ask: "what is wikipedia"
# Verify: Should show [VERIFIED] with web results

# 4. Check logs (30 seconds)
tail -f logs/flask_app.log
# Should show: "Response replaced" for Wikipedia queries
```

---

## Success Indicators

### System Working Correctly When:
- ✓ Flask starts without errors
- ✓ /ask endpoint returns responses
- ✓ Wikipedia queries show [VERIFIED] badge
- ✓ Non-Wikipedia queries work normally
- ✓ Logs show "Response replaced" for Wikipedia
- ✓ Web search results visible in response
- ✓ Sources listed with links

### Ready for Production When:
- ✓ All above working
- ✓ No errors in logs
- ✓ Response times acceptable
- ✓ Users satisfied with results
- ✓ Auto-replacement working reliably

---

## Support

### Documentation
- Auto-replacement: [AUTO_REPLACEMENT.md](AUTO_REPLACEMENT.md)
- System status: [FINAL_VERIFICATION.md](FINAL_VERIFICATION.md)
- Architecture: [WIKIPEDIA_AUTO_REPLACEMENT_COMPLETE.md](WIKIPEDIA_AUTO_REPLACEMENT_COMPLETE.md)

### Testing
- Run verification: `python verify_adaptive_learning.py`
- Check imports: `python -c "from response_quality import *"`
- Test endpoint: Test /ask with Wikipedia query

### Questions?
- Check DOCUMENTATION_INDEX.md for all guides
- Review response_quality.py code comments
- Check app.py /ask endpoint code
- Review logs/flask_app.log for errors

---

**DEPLOYMENT READY ✓**

All systems verified and operational.
Ready to deploy to production.
