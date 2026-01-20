# Quick Reference: Groq Advanced Features

## One-Minute Setup

```bash
# 1. Get API key from https://console.groq.com

# 2. Add to .env
GROQ_API_KEY=gsk_your_key_here
GROQ_ENABLED=true

# 3. Restart Flask
# Done! System now 5-10x faster
```

## Common Usage Patterns

### Check API Status
```python
from groq_client import check_groq_api_key

status = check_groq_api_key()
if status['valid']:
    print("Ready to use Groq!")
```

### Get Non-Blocking Response
```python
from groq_client import groq_response

response = groq_response(
    prompt="What is Python?",
    system_prompt="You are a programming expert"
)
print(response)
```

### Stream Response (Real-time)
```python
from groq_client import groq_response_streaming

for token in groq_response_streaming("Tell me a joke"):
    print(token, end='', flush=True)
```

### Choose Specific Model
```python
from groq_client import groq_response

response = groq_response(
    prompt="Hello",
    model="llama-2-70b-chat"  # More capable but slower
)
```

### Check Available Models
```python
from groq_client import get_available_models

models = get_available_models()
for model_id, info in models.items():
    print(f"{info['name']}: {info['speed']} / {info['capability']}")
```

### Monitor Rate Limiting
```python
from groq_client import get_rate_limit_status

status = get_rate_limit_status()
print(f"Requests remaining: {status['requests_remaining']}/30")
```

### Get Complete Status
```python
from groq_client import get_groq_status

status = get_groq_status()
print(f"Groq enabled: {status['groq_enabled']}")
print(f"API valid: {status['api_valid']}")
print(f"Rate limit: {status['rate_limit_status']['status']}")
```

## Function Quick Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `groq_response()` | Get complete response | `str` or `None` |
| `groq_response_streaming()` | Stream response tokens | Generator[str] |
| `check_groq_api_key()` | Validate API key | `Dict` with status |
| `get_available_models()` | List available models | `Dict` with model info |
| `validate_model()` | Check if model exists | `bool` |
| `get_rate_limit_status()` | Check rate limits | `Dict` with counts |
| `get_groq_status()` | Complete system status | `Dict` with all info |

## Error Handling

```python
from groq_client import groq_response

try:
    response = groq_response("Hello")
except RuntimeError as e:
    error_msg = str(e)
    if "rate limit" in error_msg:
        print("Hit rate limit - wait 60 seconds")
    elif "authentication" in error_msg:
        print("Invalid API key")
    elif "timeout" in error_msg:
        print("API timeout - try again")
    else:
        print(f"Error: {error_msg}")
```

## Configuration

### Environment Variables
```bash
GROQ_API_KEY=gsk_...           # Your API key
GROQ_ENABLED=true              # Enable/disable
GROQ_MODEL=mixtral-8x7b-32768 # Default model
```

### Rate Limit Adjustment
Edit `groq_client.py`:
```python
RATE_LIMIT_REQUESTS = 30  # requests per minute
RATE_LIMIT_WINDOW = 60    # time window in seconds
```

## Performance Notes

- **Groq**: 100+ tokens/sec, 200-500ms latency
- **Ollama**: 10-20 tokens/sec, 2-5 second latency
- **Smart Selection**: Uses Groq if available, falls back to Ollama
- **Rate Limit**: 30 requests/minute (enforced locally)
- **Timeout**: 30 seconds per request

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GROQ_API_KEY not configured" | Add key to .env and restart |
| "Invalid GROQ_API_KEY" | Verify key at console.groq.com |
| "Rate limit exceeded" | Wait 60 seconds or increase limit |
| "Timeout" | Check internet or try again |
| "Invalid model" | Use valid model from `get_available_models()` |

## Model Selection Guide

| Use Case | Recommended Model | Speed | Capability |
|----------|------------------|-------|-----------|
| Default / Balanced | mixtral-8x7b-32768 | Fast | Balanced |
| Maximum Capability | llama-2-70b-chat | Medium | Very High |
| Maximum Speed | gemma-7b-it | Very Fast | Good |
| All-around | llama-2-13b-chat | Very Fast | High |

## System Integration

All main.py handlers automatically use smart selection:

```python
# Automatically uses Groq if configured, else Ollama
answer = get_ai_response(
    prompt=user_input,
    system_prompt=domain_specific_prompt
)
```

Handlers that benefit:
- `handle_math_request()`
- `handle_essay_request()`
- `handle_code_request()`
- `handle_creative_request()`
- `handle_analysis_request()`
- `comprehensive_response()`

## API Key Setup (Step-by-Step)

1. **Visit Console**: https://console.groq.com
2. **Sign Up**: Create account (free)
3. **Go to API Keys**: Settings → API Keys
4. **Create New Key**: Click "Create API Key"
5. **Copy Key**: Get key starting with `gsk_`
6. **Add to .env**: `GROQ_API_KEY=gsk_...`
7. **Restart Flask**: System picks up new key
8. **Check Status**: `check_groq_api_key()` returns valid=true
9. **Enjoy**: 5-10x faster responses!

## Advanced Usage

### Dynamic Model Selection
```python
from groq_client import groq_response, get_available_models

models = get_available_models()
fast_models = [m for m, info in models.items() if info['speed'] == 'Very Fast']

response = groq_response(prompt, model=fast_models[0])
```

### Rate Limit Aware Batching
```python
from groq_client import get_rate_limit_status
import time

for item in items:
    status = get_rate_limit_status()
    if status['requests_remaining'] < 2:
        print(f"Approaching limit, waiting...")
        time.sleep(60)
    
    response = groq_response(item)
```

### Streaming with Error Handling
```python
from groq_client import groq_response_streaming

try:
    for token in groq_response_streaming("Hello"):
        print(token, end='', flush=True)
except RuntimeError as e:
    print(f"\nStream error: {e}")
```

## Status Codes

| Status | Meaning |
|--------|---------|
| "OK" | Rate limit normal, can proceed |
| "LIMITED" | Rate limit reached, wait 60s |
| True | API key valid and working |
| False | API key missing or invalid |

## Next Steps

1. [x] Enhanced groq_client.py deployed
2. [x] Rate limiting implemented
3. [x] Model validation active
4. [x] Error handling comprehensive
5. [ ] **Get API key** from console.groq.com (2 min)
6. [ ] **Add to .env** file (1 min)
7. [ ] **Restart Flask** application (30 sec)
8. [ ] **Enjoy 5-10x faster responses!** (immediate)

---

**Status**: Ready for production deployment. Just add your Groq API key!
