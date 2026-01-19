import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "phi"

def ollama_response(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        r = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )
        r.raise_for_status()

        data = r.json()
        return data.get("response", "").strip() or "No response from Ollama"

    except requests.exceptions.ConnectionError:
        return "[Ollama not running] Please start `ollama serve`."

    except requests.exceptions.ReadTimeout:
        return "[Ollama timeout] Model is loading. Try again in a moment."

    except ValueError:
        return "[Ollama error] Invalid JSON response."

    except Exception as e:
        if "requires more system memory" in str(e).lower():
            return (
                "⚠️ Ollama needs more RAM.\n"
                "Close heavy apps or upgrade to 8GB+ RAM."
            )
        return f"[Ollama error] {e}"
