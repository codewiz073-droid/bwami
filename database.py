"""
Consolidated Database Module
Handles all SQLAlchemy setup and database operations
SAFE for guest/debug users
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# =========================
# DATABASE CONFIGURATION
# =========================

DATABASE_URL = "sqlite:///./chats.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================
# USER ID NORMALIZATION
# =========================

def normalize_user_id(user_id):
    """
    Normalize user_id safely.

    Returns:
    - int if numeric
    - None for guest / debug / anonymous users
    """
    if isinstance(user_id, int):
        return user_id
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)
    return None

# =========================
# INITIALIZATION
# =========================

def init_db():
    """Create all tables"""
    from models import User, Chat, Message
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# DATABASE OPERATIONS
# =========================

def save_message(chat_id, user_id, role, content):
    """Save a message safely (supports guest users)"""
    db = SessionLocal()
    try:
        from models import Chat, Message

        chat_id_str = str(chat_id)
        user_id_int = normalize_user_id(user_id)

        chat = db.query(Chat).filter(
            Chat.title == chat_id_str,
            Chat.user_id == user_id_int
        ).first()

        if not chat:
            chat = Chat(
                title=chat_id_str,
                user_id=user_id_int
            )
            db.add(chat)
            db.flush()

        message = Message(
            chat_id=chat.id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"[DB] save_message error: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        db.close()

def get_chat_list(user_id):
    """Get all chats for a user"""
    db = SessionLocal()
    try:
        from models import Chat, Message

        user_id_int = normalize_user_id(user_id)

        chats = (
            db.query(Chat)
            .filter(Chat.user_id == user_id_int)
            .order_by(Chat.created_at.desc())
            .all()
        )

        result = []
        for chat in chats:
            first_msg = (
                db.query(Message)
                .filter(Message.chat_id == chat.id)
                .order_by(Message.created_at.asc())
                .first()
            )

            title = chat.title
            if not title or title in ("New Chat", "default"):
                if first_msg:
                    title = first_msg.content[:50]
                    if len(first_msg.content) > 50:
                        title += "..."
                else:
                    title = "Empty Chat"

            result.append([str(chat.id), title])

        return result

    except Exception as e:
        print(f"[DB] get_chat_list error: {e}")
        import traceback; traceback.print_exc()
        return []
    finally:
        db.close()

def get_chat_history(chat_id, user_id):
    """Get full chat history (ownership enforced)"""
    db = SessionLocal()
    try:
        from models import Chat, Message

        chat_id_str = str(chat_id)
        user_id_int = normalize_user_id(user_id)

        chat = db.query(Chat).filter(
            Chat.title == chat_id_str,
            Chat.user_id == user_id_int
        ).first()

        if not chat:
            return []

        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at.asc())
            .all()
        )

        return [[msg.role, msg.content] for msg in messages]

    except Exception as e:
        print(f"[DB] get_chat_history error: {e}")
        import traceback; traceback.print_exc()
        return []
    finally:
        db.close()

def delete_chat(chat_id, user_id):
    """Delete a chat safely"""
    db = SessionLocal()
    try:
        from models import Chat, Message

        chat_id_str = str(chat_id)
        user_id_int = normalize_user_id(user_id)

        chat = db.query(Chat).filter(
            Chat.title == chat_id_str,
            Chat.user_id == user_id_int
        ).first()

        if not chat:
            return False

        db.query(Message).filter(Message.chat_id == chat.id).delete()
        db.delete(chat)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"[DB] delete_chat error: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        db.close()
