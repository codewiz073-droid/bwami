"""
Groq API Integration for ultra-fast LLM inference
Provides 100+ tokens per second inference speed with advanced features:
- Rate limiting (30 requests/minute)
- Model switching and validation
- Streaming support
- Comprehensive error handling
- Rate limit monitoring
"""
import os
import requests
import json
import time
from typing import Optional, Generator, Dict

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_ENABLED = os.getenv("GROQ_ENABLED", "false").lower() in ["true", "1", "yes"]

# Rate Limiting
RATE_LIMIT_REQUESTS = 30  # Requests per minute
RATE_LIMIT_WINDOW = 60    # Seconds
_request_times = []

# Available Groq Models with metadata
AVAILABLE_MODELS = {
    "mixtral-8x7b-32768": {"name": "Mixtral 8x7B", "speed": "Fast", "capability": "Balanced", "recommended": True},
    "llama-2-70b-chat": {"name": "Llama 2 70B", "speed": "Medium", "capability": "Very High", "recommended": False},
    "llama-2-13b-chat": {"name": "Llama 2 13B", "speed": "Very Fast", "capability": "High", "recommended": False},
    "gemma-7b-it": {"name": "Gemma 7B", "speed": "Very Fast", "capability": "Good", "recommended": False},
}


def _check_rate_limit() -> bool:
    """Check and enforce rate limiting (30 req/min)"""
    global _request_times
    now = time.time()
    
    # Remove old timestamps outside window
    _request_times = [t for t in _request_times if now - t < RATE_LIMIT_WINDOW]
    
    # Check if limit exceeded
    if len(_request_times) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request timestamp
    _request_times.append(now)
    return True


def get_rate_limit_status() -> Dict:
    """Get current rate limit status"""
    now = time.time()
    active_requests = [t for t in _request_times if now - t < RATE_LIMIT_WINDOW]
    
    return {
        "requests_in_window": len(active_requests),
        "limit": RATE_LIMIT_REQUESTS,
        "requests_remaining": max(0, RATE_LIMIT_REQUESTS - len(active_requests)),
        "window_seconds": RATE_LIMIT_WINDOW,
        "status": "OK" if len(active_requests) < RATE_LIMIT_REQUESTS else "LIMITED"
    }


def validate_model(model: str) -> bool:
    """Validate if model exists"""
    return model in AVAILABLE_MODELS


def get_available_models() -> Dict:
    """Get list of available Groq models with details"""
    return AVAILABLE_MODELS


def groq_response(prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> Optional[str]:
    """Get response from Groq API (non-streaming)
    
    Args:
        prompt: User message/query
        system_prompt: System context/instructions for the model
        model: Specific model to use (overrides default)
        
    Returns:
        Response text or None if error
    """
    if not GROQ_API_KEY:
        return None
    
    # Rate limit check
    if not _check_rate_limit():
        status = get_rate_limit_status()
        print(f"  [GROQ] Rate limit exceeded: {status['requests_in_window']}/{status['limit']} requests")
        return None
    
    # Model validation
    selected_model = model or GROQ_MODEL
    if not validate_model(selected_model):
        print(f"  [GROQ] Invalid model '{selected_model}'")
        return None
    
    # Build messages with system prompt if provided
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(
            f"{GROQ_API_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if r.status_code == 401:
            print("  [GROQ] Invalid API key - authentication failed")
            return None
        elif r.status_code == 429:
            print("  [GROQ] API rate limit exceeded - try again later")
            return None
        elif r.status_code >= 500:
            print(f"  [GROQ] Server error ({r.status_code}) - try again later")
            return None
        
        r.raise_for_status()
        data = r.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            response_text = data["choices"][0]["message"]["content"]
            return response_text.strip() or "No response from Groq"
        return None
        
    except requests.exceptions.Timeout:
        print("  [GROQ] Request timeout (30s)")
        return None
    except requests.exceptions.ConnectionError:
        print("  [GROQ] Connection error - check internet")
        return None
    except Exception as e:
        print(f"  [GROQ] Error: {e}")
        return None


def groq_response_streaming(prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> Generator[str, None, None]:
    """Get response from Groq API with streaming enabled (ultra-fast!)
    
    Args:
        prompt: User message/query
        system_prompt: System context/instructions for the model
        model: Specific model to use (overrides default)
        
    Yields:
        Response chunks as they arrive
    """
    if not GROQ_API_KEY:
        return
    
    # Rate limit check
    if not _check_rate_limit():
        status = get_rate_limit_status()
        print(f"  [GROQ] Rate limit exceeded during streaming")
        return
    
    # Model validation
    selected_model = model or GROQ_MODEL
    if not validate_model(selected_model):
        print(f"  [GROQ] Invalid model '{selected_model}' for streaming")
        return
    
    # Build messages with system prompt if provided
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.post(
            f"{GROQ_API_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=30,
            stream=True
        )
        
        if r.status_code == 401:
            print("  [GROQ] Invalid API key during streaming")
            return
        elif r.status_code == 429:
            print("  [GROQ] API rate limit during streaming")
            return
        
        r.raise_for_status()
        
        for line in r.iter_lines():
            if line:
                line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
                        
    except requests.exceptions.Timeout:
        print("  [GROQ] Stream timeout")
        return
    except requests.exceptions.ConnectionError:
        print("  [GROQ] Stream connection error")
        return
    except Exception as e:
        print(f"  [GROQ] Stream error: {e}")
        return


def check_groq_api_key() -> Dict:
    """
    Validate Groq API key is working
    
    Returns:
        Dict with status, message, and model info
    """
    if not GROQ_API_KEY:
        return {
            "valid": False,
            "message": "GROQ_API_KEY not configured",
            "models_available": 0
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        r = requests.get(
            f"{GROQ_API_URL}/models",
            headers=headers,
            timeout=10
        )
        
        if r.status_code == 401:
            return {
                "valid": False,
                "message": "Invalid GROQ_API_KEY - authentication failed",
                "models_available": 0
            }
        elif r.status_code == 200:
            return {
                "valid": True,
                "message": "GROQ API is ready",
                "models_available": len(AVAILABLE_MODELS),
                "recommended_model": "mixtral-8x7b-32768"
            }
        else:
            return {
                "valid": False,
                "message": f"API returned status {r.status_code}",
                "models_available": 0
            }
    except requests.exceptions.Timeout:
        return {
            "valid": False,
            "message": "API timeout - Groq unreachable",
            "models_available": 0
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error checking API: {str(e)}",
            "models_available": 0
        }


def get_groq_status() -> Dict:
    """Get complete Groq integration status"""
    api_key_check = check_groq_api_key()
    
    return {
        "groq_configured": bool(GROQ_API_KEY),
        "groq_enabled": GROQ_ENABLED,
        "default_model": GROQ_MODEL,
        "model_valid": validate_model(GROQ_MODEL),
        "api_valid": api_key_check.get("valid", False),
        "rate_limit_status": get_rate_limit_status(),
        "available_models": list(AVAILABLE_MODELS.keys()),
        "recommended_model": "mixtral-8x7b-32768",
        "api_check_message": api_key_check.get("message", "Unknown")
    }