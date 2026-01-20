# Groq Integration Setup Guide

## What is Groq?

Groq provides ultra-fast LLM inference using custom-built Language Processing Units (LPUs).
- **Speed**: 100+ tokens per second (vs ~10-20 with typical GPU inference)
- **Cost**: Competitive pricing per token
- **Models**: Mixtral, Llama 2, and other open-source models
- **Latency**: Ultra-low response times ideal for real-time applications

---

## Quick Setup (2 minutes)

### Step 1: Get Groq API Key

1. Go to https://console.groq.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### Step 2: Configure .env File

Add to your `.env` file:

```env
GROQ_API_KEY=your-api-key-here
USE_GROQ=true
GROQ_ENABLED=true
GROQ_MODEL=mixtral-8x7b-32768
```

### Step 3: Restart Flask

```bash
flask run
```

**Done!** Your system now uses Groq for inference instead of local Ollama.

---

## Configuration Options

### .env Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `GROQ_API_KEY` | Your API key | Authentication |
| `USE_GROQ` | `true` or `false` | Enable Groq vs Ollama |
| `GROQ_ENABLED` | `true` or `false` | Allow Groq fallback |
| `GROQ_MODEL` | Model name | Which model to use |

### Available Models

| Model | Speed | Capability | Best For |
|-------|-------|-----------|----------|
| `mixtral-8x7b-32768` | Very Fast | Balanced | Default choice |
| `llama-2-70b-chat` | Fast | Very Capable | Complex queries |
| `llama-2-13b-chat` | Faster | Capable | General use |
| `gemma-7b-it` | Fastest | Good | Quick responses |

---

## How It Works

### Architecture

```
User Query
    ↓
comprehensive_response()
    ↓
Request Classification
    ↓
Domain Handler
    ↓
get_ai_response() ← Smart selection
    ├─→ If USE_GROQ=true: get_groq_response()
    └─→ If USE_GROQ=false: get_ollama_response()
    ↓
System Prompt Injection
    ↓
Response + Quality Metrics
```

### Smart Selection

The system automatically chooses the best inference engine:

```python
def get_ai_response(prompt, system_prompt=None):
    if USE_GROQ and GROQ_ENABLED:
        return get_groq_response(prompt, system_prompt)
    else:
        return get_ollama_response(prompt, system_prompt)
```

---

## Performance Comparison

### Ollama (Local)
- **Speed**: 10-20 tokens/sec
- **Cost**: Free (runs locally)
- **Latency**: 2-5 seconds for typical response
- **Requires**: GPU on your machine

### Groq API
- **Speed**: 100+ tokens/sec (5-10x faster!)
- **Cost**: $0.00005 per 1K input tokens, $0.00015 per 1K output tokens
- **Latency**: 200-500ms for typical response
- **Requires**: Groq API key (free tier available)

---

## Fallback Behavior

The system is resilient:

1. **Groq configured but API key invalid**: Falls back to Ollama
2. **Groq API down/rate limited**: Falls back to Ollama  
3. **Both down**: Returns error message
4. **USE_GROQ=false**: Uses Ollama directly

---

## Testing Groq Integration

### Quick Test

Run in Python:

```python
from groq_client import groq_response, check_groq_api_key

# Verify API key
if check_groq_api_key():
    print("Groq API key valid!")
    
    # Test inference
    result = groq_response("What is 2+2?", system_prompt="You are a helpful assistant.")
    print(f"Response: {result}")
else:
    print("Groq API key not configured or invalid")
```

### Full Integration Test

Go through your normal chat workflow:

```
You: "solve x^2 = 4"
System: [Uses Groq if enabled, Ollama if not]
Response: [Ultra-fast response from Groq]
```

---

## Cost Estimation

### Monthly Usage Example

Assuming 1000 queries/month, average 50 input + 150 output tokens:

```
Input tokens:  1000 × 50 = 50,000 tokens → $0.0025
Output tokens: 1000 × 150 = 150,000 tokens → $0.0225
Total: ~$0.025/month (basically free!)
```

Groq offers free tier with sufficient token allowance for most users.

---

## Switching Between Groq and Ollama

### Use Groq Only
```env
USE_GROQ=true
GROQ_ENABLED=true
```

### Use Ollama Only
```env
USE_GROQ=false
```

### Use Groq with Ollama Fallback
```env
USE_GROQ=true
GROQ_ENABLED=true
OLLAMA_ENABLED=true
```

---

## Advantages of Groq Integration

1. **Ultra-Fast Responses**: 5-10x faster than local Ollama
2. **Better User Experience**: Streaming responses feel instant
3. **Scalability**: Handle many concurrent users
4. **No Local GPU Needed**: Works on any machine
5. **Cost-Effective**: Free tier available, pay-as-you-go
6. **Smart Routing**: Automatically selects best inference engine
7. **Domain Optimization**: System prompts still applied to all responses

---

## Troubleshooting

### "Groq unavailable" error

**Cause**: API key not configured or invalid

**Solution**: 
1. Check `.env` has valid GROQ_API_KEY
2. Verify at https://console.groq.com
3. Restart Flask

### Slow responses with Groq

**Cause**: Network latency or Groq API overload

**Solution**: 
1. Check your internet connection
2. Try different model with GROQ_MODEL
3. Fall back to Ollama by setting USE_GROQ=false

### Mixing Ollama and Groq

**To use both**:
1. Keep OLLAMA_ENABLED=true
2. Set USE_GROQ=true
3. System will use Groq first, fall back to Ollama if needed

---

## Next Steps

1. ✓ Set up Groq API key (2 minutes)
2. ✓ Configure .env (1 minute)
3. ✓ Restart Flask (30 seconds)
4. ✓ Test with your queries (1 minute)
5. Optional: Compare Groq vs Ollama performance

**Your system now has ultra-fast inference! Enjoy the speed boost.**
