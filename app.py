print(">>> IMPORT START <<<")

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import json
import os
import sys
import uuid
import logging
import re
import traceback
from functools import wraps
from html import escape
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from typing import Generator, Optional

print(">>> FASTAPI IMPORTS OK <<<")

from groq_client import groq_response_streaming
from web_search import search_web, fetch_page
from response_formatter import format_response
from response_quality import check_response
from connectivity import check_connectivity, is_online
from auth import (
    create_guest_session,
    register_user,
    login_user,
    get_current_user_from_request,
    create_token,
    get_user_preferences,
    update_user_preferences
)
from database import (
    init_db,
    save_message,
    get_chat_list,
    get_chat_history,
    delete_chat
)

print(">>> CUSTOM IMPORTS OK <<<")

# =========================
# SECURITY IMPORTS
# =========================
CORS_AVAILABLE = True

print(">>> SECURITY IMPORTS OK <<<")

# =========================
# ENVIRONMENT VALIDATION
# =========================
class Config:
    """Centralized configuration with validation"""
    REQUIRED_ENV = {}  # No required env vars for development
    
    OPTIONAL_ENV = {
        'SECRET_KEY': (str, None),
        'DATABASE_URL': (str, None),
        'DEBUG': (bool, False),
        'LOG_LEVEL': (str, 'INFO'),
        'ALLOWED_ORIGINS': (str, ''),
        'RATE_LIMIT_ENABLED': (bool, True),
        'RENDER_EXTERNAL_URL': (str, ''),
    }
    
    @classmethod
    def validate(cls):
        config = {}
        errors = []
        
        # Check required
        for var, var_type in cls.REQUIRED_ENV.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"{var} is required")
            else:
                try:
                    config[var] = var_type(value)
                except ValueError:
                    errors.append(f"{var} must be of type {var_type.__name__}")
        
        # Check optional with defaults
        for var, (var_type, default) in cls.OPTIONAL_ENV.items():
            value = os.getenv(var, default)
            try:
                if var_type == bool:
                    config[var] = str(value).lower() in ('true', '1', 'yes')
                else:
                    config[var] = var_type(value) if value else default
            except ValueError:
                config[var] = default
        
        if errors:
            raise RuntimeError(f"Configuration errors: {', '.join(errors)}")
        
        return config

try:
    config = Config.validate()
except RuntimeError as e:
    print(f"[ERROR] Configuration validation failed: {e}")
    raise

print(">>> CONFIG OK <<<")

# =========================
# APP SETUP WITH SECURITY
# =========================
app = FastAPI(title="AI Assistant")

print(">>> APP INSTANCE OK <<<")

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print(">>> STATIC FILES MOUNTED <<<")

# Setup templates
if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")
    print(">>> TEMPLATES OK <<<")
else:
    templates = None
    print(">>> TEMPLATES DIRECTORY NOT FOUND <<<")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(">>> CORS ENABLED <<<")
print(">>> SESSION CONFIG OK <<<")

# =========================
# LOGGING SETUP
# =========================
def setup_logging():
    """Configure application logging"""
    log_level = config['LOG_LEVEL']
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # File handler (rotating)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024 * 10,
        backupCount=5
    )
    file_handler.setLevel(logging.WARNING)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(getattr(logging, log_level))
    
    return logger

logger = setup_logging()

print(">>> LOGGING OK <<<")

# =========================
# INPUT VALIDATION
# =========================
def sanitize_input(text, max_length=5000):
    """Validate and sanitize user input"""
    if not text or not isinstance(text, str):
        return ""
    
    # Length check
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated to {max_length} chars")
    
    # HTML escape
    text = escape(text)
    text = text.strip()
    
    # Remove suspicious patterns
    suspicious_patterns = [
        r'<script.*?>.*?</script>',
        r'on\w+\s*=',
        r'javascript:',
        r'data:text/html'
    ]
    for pattern in suspicious_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text

print(">>> INPUT VALIDATION OK <<<")

# =========================
# DATABASE INITIALIZATION
# =========================
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

print(">>> DATABASE OK <<<")

# Auto-detect connectivity
startup_connectivity = check_connectivity()
current_mode = {"online": startup_connectivity["online"]}
logger.info(f"Initial connectivity status: {startup_connectivity['status']}")
logger.info(f"Mode: [GROQ - Ultra-Fast Cloud Inference]")

print(">>> CONNECTIVITY OK <<<")

# =========================
# UTILITY FUNCTIONS
# =========================
def is_short_conversational(text: str) -> bool:
    """Determine if a query is short/conversational (no web search needed)"""
    text = text.strip().lower()
    return (
        len(text) < 6
        or text in {"hi", "hello", "hey", "yo", "sup", "ok", "thanks"}
    )

def is_browsing_query(text: str) -> bool:
    """Determine if a query needs web search (opposite of is_short_conversational)"""
    return not is_short_conversational(text)

print(">>> UTILITY FUNCTIONS OK <<<")

# =========================
# ROUTES
# =========================

from fastapi.responses import HTMLResponse

@app.get("/")
async def home(request: Request):
    """Serve home page using Jinja2 template"""
    if templates is None:
        return HTMLResponse(content="<h1>AI Assistant API</h1><p>Templates not found</p>")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask(req: Request):
    """Streaming POST endpoint - returns SSE stream for frontend consumption"""
    logger.info(">>> /ask HIT (POST) <<<")

    try:
        raw_body = await req.body()
        try:
            data = json.loads(raw_body.decode("utf-8-sig")) or {}
        except Exception:
            logger.warning("[ASK] Invalid JSON body received")
            def error_gen():
                yield f"data: {json.dumps({'type': 'error', 'text': 'Invalid JSON'})}\n\n"
            return StreamingResponse(error_gen(), media_type="text/event-stream")

        user_input = sanitize_input(data.get("message", ""), max_length=5000)
        chat_id = sanitize_input(data.get("chat_id", "default"), max_length=100)

        if not user_input:
            def empty_gen():
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return StreamingResponse(empty_gen(), media_type="text/event-stream")

        user_id = 0
        save_message(chat_id, user_id, "user", user_input)
        logger.info(f"[ASK] Input: {user_input}")

        def generate() -> Generator[str, None, None]:
            """Generator for streaming SSE response"""
            try:
                # Immediate heartbeat
                yield f"data: {json.dumps({'type': 'status', 'text': '[stream open]'})}\n\n"
                
                # 🚀 FAST PATH — NO BROWSING
                if is_short_conversational(user_input):
                    logger.info("[ASK] Conversational -> Groq only")
                    stream = groq_response_streaming(user_input)
                    if stream is None:
                        yield f"data: {json.dumps({'type': 'text', 'text': '[Groq API not available]'})}\n\n"
                    else:
                        full_text = ""
                        for chunk in stream:
                            logger.info(f"[GROQ] chunk: {chunk}")
                            full_text += chunk
                            yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
                        if full_text:
                            save_message(chat_id, user_id, "assistant", full_text)
                else:
                    # 🌍 BROWSING PATH
                    logger.info("[ASK] Browsing query detected")
                    search_results = search_web(user_input, max_results=3)

                    if not search_results:
                        msg = "I couldn't find relevant information."
                        yield f"data: {json.dumps({'type': 'text', 'text': msg})}\n\n"
                    else:
                        extracted = []
                        for r in search_results:
                            try:
                                url = r.get("url") or r.get("link")
                                if not url:
                                    continue
                                content = fetch_page(url)
                                if content:
                                    extracted.append(content[:800])
                            except Exception as e:
                                logger.warning(f"[BROWSE] Failed to fetch: {e}")
                                continue

                        if not extracted:
                            msg = "I found sources but couldn't extract content."
                            yield f"data: {json.dumps({'type': 'text', 'text': msg})}\n\n"
                        else:
                            context = "\n---\n".join(extracted)
                            logger.info("[GROQ] starting streaming for browsing query")
                            stream = groq_response_streaming(f"Answer using these sources:\n{context}\n\nQuestion: {user_input}")
                            if stream is None:
                                yield f"data: {json.dumps({'type': 'text', 'text': '[Groq API not available]'})}\n\n"
                            else:
                                full_text = ""
                                for chunk in stream:
                                    logger.info(f"[GROQ] chunk: {chunk}")
                                    full_text += chunk
                                    yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
                                if full_text:
                                    save_message(chat_id, user_id, "assistant", full_text)
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            except Exception as e:
                logger.error(f"[ERROR] Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception:
        logger.error("[ASK] Fatal error", exc_info=True)
        def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'text': 'Internal server error'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream", status_code=500)

@app.get("/chats")
async def chats_list(req: Request):
    """Get list of chats for current user"""
    try:
        user_id = "debug-user"
        chat_list = get_chat_list(user_id)
        return JSONResponse({"chats": chat_list})
    except Exception as e:
        logger.error(f"[CHATS] Error: {e}", exc_info=True)
        return JSONResponse({"chats": []}, status_code=200)


@app.get("/history/{chat_id}")
async def chat_history(chat_id: str, req: Request):
    """Get chat history"""
    try:
        user_id = "debug-user"
        messages = get_chat_history(chat_id, user_id)
        return JSONResponse({"messages": messages})
    except Exception as e:
        logger.error(f"[HISTORY] Error: {e}", exc_info=True)
        return JSONResponse({"messages": []}, status_code=200)


@app.delete("/delete/{chat_id}")
async def delete_chat_endpoint(chat_id: str, req: Request):
    """Delete a chat"""
    try:
        user_id = "debug-user"
        delete_chat(chat_id, user_id)
        return JSONResponse({"status": "deleted"})
    except Exception as e:
        logger.error(f"[DELETE] Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/mode")
async def get_mode():
    """Get current mode (online/offline)"""
    return JSONResponse({"mode": "online"})


@app.post("/mode")
async def set_mode(req: Request):
    """Set mode (online/offline)"""
    try:
        data = await req.json()
        mode = data.get("mode", "online")
        return JSONResponse({"mode": mode})
    except Exception:
        return JSONResponse({"mode": "online"})


@app.get("/status/connectivity")
async def connectivity_status():
    """Get connectivity status"""
    try:
        online = is_online()
        return JSONResponse({
            "online": online,
            "status": "Online (Using Groq Cloud Inference)" if online else "Offline",
            "mode": "[GROQ - Ultra-Fast Cloud Inference]"
        })
    except Exception:
        return JSONResponse({
            "online": True,
            "status": "Online (Using Groq Cloud Inference)",
            "mode": "[GROQ - Ultra-Fast Cloud Inference]"
        })


print(">>> ROUTES OK <<<")
print(">>> IMPORT COMPLETE <<<")

if __name__ == "__main__":
    print(">>> BEFORE RUN <<<")
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        import uvicorn
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8080,
            log_level="info"
        )
    except Exception as e:
        print(f">>> ERROR RUNNING: {e} <<<", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        print(">>> AFTER RUN <<<")
        sys.stdout.flush()
        sys.stderr.flush()

