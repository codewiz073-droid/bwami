"""Authentication helpers for user login/signup/logout"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from database import SessionLocal
from models import User, UserPreferences


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"


def create_token(user_id, is_guest=False):
    """Create JWT token for user"""
    payload = {
        "user_id": user_id,
        "is_guest": is_guest,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token):
    """Verify JWT token and return user_id, None if invalid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id"), payload.get("is_guest", False)
    except:
        return None, False


def get_current_user_from_request():
    """Extract user_id and is_guest from request (token or session)"""
    # Try token first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user_id, is_guest = verify_token(token)
        if user_id:
            return user_id, is_guest
    
    # Try session
    if "user_id" in session:
        return session.get("user_id"), session.get("is_guest", False)
    
    return None, False


def require_auth(f):
    """Decorator: require user to be logged in (account or guest)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id, is_guest = get_current_user_from_request()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, user_id=user_id, is_guest=is_guest, **kwargs)
    return decorated


def create_guest_session():
    """Create a guest user and token"""
    db = SessionLocal()
    try:
        # Create temporary guest user
        guest = User(
            username=f"guest_{datetime.utcnow().timestamp()}",
            email=f"guest_{datetime.utcnow().timestamp()}@guest.local",
            password_hash="",
            is_active=True
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)
        
        token = create_token(guest.id, is_guest=True)
        return {
            "user_id": guest.id,
            "is_guest": True,
            "token": token,
            "username": "Guest"
        }
    finally:
        db.close()


def register_user(username, email, password):
    """Register new user account"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return None, "User already exists"
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default preferences for new user
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        db.commit()
        
        token = create_token(user.id, is_guest=False)
        return {
            "user_id": user.id,
            "is_guest": False,
            "token": token,
            "username": username
        }, None
    except Exception as e:
        return None, str(e)
    finally:
        db.close()


def login_user(username, password):
    """Authenticate user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.check_password(password):
            return None, "Invalid username or password"
        
        token = create_token(user.id, is_guest=False)
        return {
            "user_id": user.id,
            "is_guest": False,
            "token": token,
            "username": username
        }, None
    finally:
        db.close()


def get_user_preferences(user_id):
    """Get user preferences or create default"""
    db = SessionLocal()
    try:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if not prefs:
            # Create default preferences if not exists
            prefs = UserPreferences(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return {
            "response_format": prefs.response_format,
            "use_lists": prefs.use_lists,
            "use_numbered": prefs.use_numbered,
            "use_bullets": prefs.use_bullets,
            "use_emojis": prefs.use_emojis,
            "preferred_tone": prefs.preferred_tone,
            "preferred_language": prefs.preferred_language,
            "custom_system_prompt": prefs.custom_system_prompt,
            "specializations": prefs.specializations or {}
        }
    finally:
        db.close()


def update_user_preferences(user_id, preferences):
    """Update user preferences"""
    db = SessionLocal()
    try:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user_id)
            db.add(prefs)
        
        # Update allowed fields
        if "response_format" in preferences:
            prefs.response_format = preferences["response_format"]
        if "use_lists" in preferences:
            prefs.use_lists = preferences["use_lists"]
        if "use_numbered" in preferences:
            prefs.use_numbered = preferences["use_numbered"]
        if "use_bullets" in preferences:
            prefs.use_bullets = preferences["use_bullets"]
        if "use_emojis" in preferences:
            prefs.use_emojis = preferences["use_emojis"]
        if "preferred_tone" in preferences:
            prefs.preferred_tone = preferences["preferred_tone"]
        if "preferred_language" in preferences:
            prefs.preferred_language = preferences["preferred_language"]
        if "custom_system_prompt" in preferences:
            prefs.custom_system_prompt = preferences["custom_system_prompt"]
        if "specializations" in preferences:
            prefs.specializations = preferences["specializations"]
        
        prefs.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prefs)
        
        return {
            "status": "ok",
            "preferences": {
                "response_format": prefs.response_format,
                "use_lists": prefs.use_lists,
                "use_numbered": prefs.use_numbered,
                "use_bullets": prefs.use_bullets,
                "use_emojis": prefs.use_emojis,
                "preferred_tone": prefs.preferred_tone,
                "preferred_language": prefs.preferred_language,
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
