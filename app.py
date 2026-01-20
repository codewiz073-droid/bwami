from flask import (
    Flask,
    render_template,
    request,
    Response,
    jsonify,
    stream_with_context,
    session
)
import time
import json
import os
import sys
import uuid
import logging
import re
from functools import wraps
from html import escape
from datetime import timedelta
from logging.handlers import RotatingFileHandler

# Fix encoding for Windows console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from main import comprehensive_response
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

# =========================
# SECURITY IMPORTS
# =========================
try:
    from flask_cors import CORS
except ImportError:
    CORS = None
    
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    Limiter = None

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

# =========================
# APP SETUP WITH SECURITY
# =========================
app = Flask(__name__)

# Secret key management
secret_key = config['SECRET_KEY']
if not secret_key:
    # Default to development mode for direct execution
    secret_key = "dev-temp-key-" + str(uuid.uuid4())
    print("[WARN] Using temporary secret key for development only")

app.secret_key = secret_key

# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Only true in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SESSION_REFRESH_EACH_REQUEST=True,
    JSON_SORT_KEYS=False
)

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
    
    # Apply to app logger
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, log_level))
    
    # Suppress noisy logs
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    return app.logger

logger = setup_logging()

# =========================
# CORS PROTECTION
# =========================
if CORS:
    allowed_origins = config['ALLOWED_ORIGINS'].split(',') if config['ALLOWED_ORIGINS'] else []
    allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
    
    # Always enable CORS (for development: localhost, for production: configured origins)
    if not allowed_origins:
        # Development mode: allow all localhost origins
        allowed_origins = ['http://localhost:*', 'http://127.0.0.1:*', 'http://localhost:5000', 'http://127.0.0.1:5000']
    
    CORS(app, 
         origins=allowed_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'OPTIONS'])
    logger.info(f"CORS enabled for origins: {allowed_origins}")
else:
    logger.warning("flask-cors not installed - CORS protection disabled")

# =========================
# RATE LIMITING
# =========================
limiter = None
if Limiter:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    logger.info("Rate limiting enabled (flask-limiter available)")
else:
    logger.warning("flask-limiter not installed - Rate limiting disabled")

# =========================
# SECURITY HEADERS
# =========================
@app.after_request
def security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # HSTS only in production
    if os.getenv('FLASK_ENV') != 'development':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'"
    
    return response

# =========================
# ERROR HANDLERS
# =========================
@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(429)
def rate_limit_handler(error):
    logger.warning(f"Rate limit exceeded: {error}")
    return jsonify({"error": "Too many requests. Please try again later."}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}", exc_info=True)
    if app.debug:
        return jsonify({"error": str(error)}), 500
    return jsonify({"error": "Internal server error"}), 500

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

# =========================
# DATABASE INITIALIZATION
# =========================
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Auto-detect connectivity
connectivity_status = check_connectivity()
current_mode = {"online": connectivity_status["online"]}
logger.info(f"Initial connectivity status: {connectivity_status['status']}")
logger.info(f"Mode: {'[ONLINE - Internet]' if current_mode['online'] else '[OFFLINE - Ollama]'}")

# =========================
# RATE LIMITING HELPER
# =========================
def apply_rate_limit(limit_str):
    """Helper to apply rate limiting if enabled"""
    def decorator(f):
        if limiter and config.get('RATE_LIMIT_ENABLED', True):
            return limiter.limit(limit_str)(f)
        return f
    return decorator

# =========================
# AUTH ROUTES
# =========================
@app.route("/auth/guest", methods=["POST"])
@apply_rate_limit("10 per minute")
def guest_login():
    """Create guest session"""
    result = create_guest_session()
    response = jsonify(result)
    response.set_cookie("token", result["token"], max_age=86400*7, httponly=True, samesite="Lax")
    session["user_id"] = result["user_id"]
    session["is_guest"] = True
    return response


@app.route("/auth/signup", methods=["POST"])
@apply_rate_limit("5 per minute")
def signup():
    """Register new user"""
    data = request.json or {}
    username = sanitize_input(data.get("username", ""), max_length=100)
    email = sanitize_input(data.get("email", ""), max_length=254)
    password = data.get("password", "").strip()
    
    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400
    
    result, error = register_user(username, email, password)
    if error:
        return jsonify({"error": error}), 400
    
    response = jsonify(result)
    response.set_cookie("token", result["token"], max_age=86400*7, httponly=True, samesite="Lax")
    session["user_id"] = result["user_id"]
    session["is_guest"] = False
    return response


@app.route("/auth/login", methods=["POST"])
@apply_rate_limit("5 per minute")
def login():
    """Login user"""
    data = request.json or {}
    username = sanitize_input(data.get("username", ""), max_length=100)
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400
    
    result, error = login_user(username, password)
    if error:
        return jsonify({"error": error}), 401
    
    response = jsonify(result)
    response.set_cookie("token", result["token"], max_age=86400*7, httponly=True, samesite="Lax")
    session["user_id"] = result["user_id"]
    session["is_guest"] = False
    return response


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout user"""
    session.clear()
    response = jsonify({"status": "ok"})
    response.set_cookie("token", "", max_age=0)
    return response


@app.route("/auth/status", methods=["GET"])
def auth_status():
    """Get current auth status"""
    user_id, is_guest = get_current_user_from_request()
    if user_id:
        return jsonify({
            "authenticated": True,
            "user_id": user_id,
            "is_guest": is_guest
        })
    return jsonify({"authenticated": False})


# =========================
# CONNECTIVITY STATUS
# =========================

@app.route("/status/connectivity", methods=["GET"])
def connectivity_status():
    """Get current connectivity status"""
    status = check_connectivity()
    return jsonify({
        "online": status["online"],
        "status": status["status"],
        "mode": "[ONLINE - Internet]" if status["online"] else "[OFFLINE - Ollama]"
    })


# =========================
# PREFERENCES ROUTES
# =========================

@app.route("/user/preferences", methods=["GET"])
def get_preferences():
    """Get user preferences"""
    user_id, is_guest = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    prefs = get_user_preferences(user_id)
    return jsonify(prefs)


@app.route("/user/preferences", methods=["POST"])
def update_preferences():
    """Update user preferences"""
    user_id, is_guest = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    if is_guest:
        return jsonify({"error": "Guests cannot save preferences"}), 403
    
    data = request.json or {}
    result = update_user_preferences(user_id, data)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result)


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# ASK / STREAM RESPONSE
# =========================
@app.route("/ask", methods=["POST"])
@apply_rate_limit("30 per minute")
def ask():
    try:
        data = request.json or {}
        user_input = sanitize_input(data.get("message", ""), max_length=5000)
        chat_id = sanitize_input(data.get("chat_id", "default"), max_length=100)

        if not user_input:
            return Response("", mimetype="text/event-stream")
        
        # Get current user
        user_id, is_guest = get_current_user_from_request()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Convert user_id to string for consistency with db
        user_id = str(user_id)

        # Save user message immediately
        save_message(chat_id, user_id, "user", user_input)
        
        # Get user preferences for response formatting
        user_prefs = get_user_preferences(int(user_id)) if not is_guest else {}
        
        # Auto-detect connectivity and update mode
        connectivity = check_connectivity()
        current_mode["online"] = connectivity["online"]

        def generate():
            full_response = ""
            
            # Show current mode to user
            mode_indicator = "[ONLINE]" if current_mode["online"] else "[OFFLINE]"
            yield f"data: {json.dumps({'type': 'status', 'text': f'{mode_indicator}'})}\n\n"

            # Let comprehensive_response handle everything with quality checking
            # Returns: (response_text, quality_report)
            logger.info(f"Processing request with mode: {current_mode['online']}")
            response_text, quality_report = comprehensive_response(user_input, mode="online" if current_mode["online"] else "offline")
            
            # Run quality check - REPLACES Wikipedia-only responses with web search
            from response_quality import check_response
            quality_check = check_response(response_text, query=user_input, response_type="general")
            
            # Use response (original, replaced, or truncated)
            response_text = quality_check.get('response_text', response_text)
            
            # Log if replacement occurred
            if quality_check.get('replaced', False):
                logger.info(f"Response replaced: Wikipedia-only detected, using web search results for: {user_input}")
            elif quality_check.get('blocked', False):
                logger.warning(f"Response would be blocked: {user_input}")
            
            # Log quality information
            confidence = quality_check.get('confidence_level', 'UNKNOWN')
            has_issues = len(quality_check.get('issues', [])) > 0
            replaced = quality_check.get('replaced', False)
            logger.info(f"Response confidence: {confidence}, Issues: {has_issues}, Replaced: {replaced}")
            
            # Apply formatting with quality metadata
            if not current_mode["online"]:
                response_text = format_response(
                    response_text, 
                    user_prefs,
                    confidence_level=quality_check.get('confidence_level'),
                    sources=quality_check.get('sources', [])
                )
            
            # Add replacement notice (but hide confidence from user)
            if quality_check.get('replaced', False):
                indicator = f"\n[VERIFIED - Web Search Results]\n[This response replaced Wikipedia content for accuracy]"
                response_text += indicator
            # Confidence levels are logged but not shown to user for cleaner interface

            # Stream response immediately (no artificial delays)
            for word in response_text.split():
                chunk = word + " "
                full_response += chunk
                yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"

            # Save assistant response
            save_message(chat_id, user_id, "assistant", full_response.strip())

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")
    
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# =========================
# VERIFIED WEB SEARCH ENDPOINT
# =========================
@app.route("/ask-verified", methods=["POST"])
@apply_rate_limit("20 per minute")
def ask_verified():
    """
    Enhanced /ask endpoint that verifies responses against live web search results.
    Prevents hallucinations by cross-checking against real sources.
    Returns confidence levels and verified sources.
    """
    try:
        data = request.json or {}
        user_input = sanitize_input(data.get("message", ""), max_length=5000)
        chat_id = sanitize_input(data.get("chat_id", "default"), max_length=100)

        if not user_input:
            return jsonify({"error": "No message provided"}), 400
        
        # Get current user
        user_id, is_guest = get_current_user_from_request()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Save user message
        user_id = str(user_id)
        save_message(chat_id, user_id, "user", user_input)
        
        # Get connectivity status
        connectivity = check_connectivity()
        current_mode["online"] = connectivity["online"]

        def generate_verified():
            """Generate response with web verification"""
            try:
                from web_search import search_web, fetch_page
                
                # Step 1: Generate initial response
                response_text, quality_report = comprehensive_response(user_input, mode="online")
                
                # Step 2: Perform web search for verification
                logger.info(f"Verifying response with web search: {user_input[:50]}")
                web_sources = search_web(user_input, max_results=3)
                
                # Step 3: Run quality check WITH web verification
                quality_check = check_response(
                    response_text,
                    sources=web_sources,
                    response_type="web_search",
                    query=user_input
                )
                
                # Step 4: Build response with verification metadata
                verification_badge = ""
                if quality_check['web_verified']:
                    verification_badge = "\n[VERIFIED] - Information checked against web sources"
                elif quality_check['verified_sources']:
                    verification_badge = f"\n[PARTIALLY VERIFIED] - Found {len(quality_check['verified_sources'])} supporting sources"
                else:
                    verification_badge = f"\n[UNVERIFIED] - Could not verify with web sources (Confidence: {quality_check['confidence_level']})"
                
                # Step 5: Stream response with verification
                full_response = response_text + verification_badge
                
                # Add sources if available
                if quality_check['verified_sources']:
                    full_response += "\n\nVerified Sources:"
                    for src in quality_check['verified_sources'][:3]:
                        full_response += f"\n- {src.get('title', 'Source')}: {src.get('url', 'No URL')}"
                
                # Stream the response
                for word in full_response.split():
                    chunk = word + " "
                    yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
                
                # Save assistant response
                save_message(chat_id, user_id, "assistant", full_response)
                
                # Final metadata
                yield f"data: {json.dumps({'type': 'metadata', 'confidence': quality_check['confidence_level'], 'verified': quality_check['web_verified'], 'sources_count': len(quality_check['verified_sources'])})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in verified response: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        
        return Response(generate_verified(), mimetype="text/event-stream")
    
    except Exception as e:
        logger.error(f"Error in /ask-verified: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# CHAT LIST
# =========================
@app.route("/chats")
def chats():
    user_id, is_guest = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(get_chat_list(str(user_id)))

# =========================
# CHAT HISTORY
# =========================
@app.route("/history/<chat_id>")
def history(chat_id):
    user_id, is_guest = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(get_chat_history(chat_id, str(user_id)))


# =========================
# DELETE CHAT
# =========================
@app.route("/delete/<chat_id>", methods=["DELETE"])
def delete_chat_route(chat_id):
    user_id, is_guest = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    success = delete_chat(chat_id, str(user_id))
    if not success:
        return jsonify({"error": "Chat not found or not authorized"}), 403
    
    return jsonify({"status": "ok"})


# =========================
# MODE TOGGLE
# =========================
@app.route("/mode", methods=["GET", "POST"])
def toggle_mode():
    if request.method == "POST":
        mode = request.json.get("mode", "online")
        current_mode["online"] = (mode == "online")
        
        # Get current connectivity info for response
        connectivity = check_connectivity()
        return jsonify({
            "status": "ok",
            "mode": mode,
            "detectedOnline": connectivity["online"],
            "detectedStatus": connectivity["status"]
        })

    # GET request: return current mode and detected connectivity
    connectivity = check_connectivity()
    return jsonify({
        "mode": "online" if current_mode["online"] else "offline",
        "detectedOnline": connectivity["online"],
        "detectedStatus": connectivity["status"]
    })


# =========================
# NO CACHE (DEV FRIENDLY)
# =========================
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
