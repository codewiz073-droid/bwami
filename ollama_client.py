import os
import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "phi"

# Enable Ollama by default - it's local and doesn't require API keys
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true") == "true"

def ollama_response(prompt, system_prompt=None):
    """Get response from Ollama (non-streaming)
    
    Args:
        prompt: User message/query
        system_prompt: System context/instructions for the model
    """
    if not OLLAMA_ENABLED:
        return None

    # Build complete prompt with system context if provided
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
    else:
        full_prompt = prompt

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip() or "No response from Ollama"

    except requests.exceptions.ConnectionError:
        return None

    except requests.exceptions.ReadTimeout:
        return None

    except Exception as e:
        if "requires more system memory" in str(e).lower():
            return None
        return None


def ollama_response_streaming(prompt, system_prompt=None):
    """Get response from Ollama with streaming enabled (faster perceived response)
    
    Args:
        prompt: User message/query
        system_prompt: System context/instructions for the model
    """
    if not OLLAMA_ENABLED:
        return []

    # Build complete prompt with system context if provided
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
    else:
        full_prompt = prompt

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": True
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120, stream=True)
        r.raise_for_status()
        
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    response_text = data.get("response", "")
                    if response_text:
                        yield response_text
                except json.JSONDecodeError:
                    continue

    except requests.exceptions.ConnectionError:
        return
    except requests.exceptions.ReadTimeout:
        return
    except Exception as e:
        return
