"""
Consolidated Database Module
Handles all SQLAlchemy setup and database operations
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid

# =========================
# DATABASE CONFIGURATION
# =========================

# SQLite (local)
DATABASE_URL = "sqlite:///./chats.db"

# PostgreSQL example:
# DATABASE_URL = "postgresql://user:password@localhost/chatdb"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================
# INITIALIZATION
# =========================

def init_db():
    """Create all tables"""
    from models import User, Chat, Message
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# DATABASE OPERATIONS
# =========================

def save_message(chat_id, user_id, role, content):
    """Save a message to the database"""
    db = SessionLocal()
    try:
        from models import Chat, Message
        
        # Normalize inputs
        chat_id_str = str(chat_id)
        user_id_int = int(user_id) if isinstance(user_id, (int, str)) else user_id
        
        # Get or create chat (using title field to store chat_id)
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
        
        # Add message
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
        print(f"Error saving message: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def get_chat_list(user_id):
    """Get list of chats for a user"""
    db = SessionLocal()
    try:
        from models import Chat, Message
        
        user_id_int = int(user_id) if isinstance(user_id, (int, str)) else user_id
        chats = db.query(Chat).filter(Chat.user_id == user_id_int).order_by(Chat.created_at.desc()).all()
        result = []
        for chat in chats:
            # Get first message as title if not set
            first_msg = db.query(Message).filter(Message.chat_id == chat.id).first()
            title = chat.title
            if not title or title == "New Chat" or title == "default":
                if first_msg:
                    # Use first 50 chars of first message as title
                    title = first_msg.content[:50] + ("..." if len(first_msg.content) > 50 else "")
                else:
                    title = "Empty Chat"
            result.append([str(chat.id), title])
        return result
    except Exception as e:
        print(f"Error getting chat list: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()


def get_chat_history(chat_id, user_id):
    """Get message history for a chat (with user verification)"""
    db = SessionLocal()
    try:
        from models import Chat, Message
        
        chat_id_str = str(chat_id)
        user_id_int = int(user_id) if isinstance(user_id, (int, str)) else user_id
        
        # Verify user owns this chat
        chat = db.query(Chat).filter(
            Chat.title == chat_id_str,
            Chat.user_id == user_id_int
        ).first()
        
        if not chat:
            return []  # User doesn't own this chat
        
        # Get all messages for this chat
        messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()
        result = []
        for msg in messages:
            result.append([msg.role, msg.content])
        return result
    except Exception as e:
        print(f"Error getting chat history: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()


def delete_chat(chat_id, user_id):
    """Delete a chat (with user verification)"""
    db = SessionLocal()
    try:
        from models import Chat, Message
        
        chat_id_str = str(chat_id)
        user_id_int = int(user_id) if isinstance(user_id, (int, str)) else user_id
        
        # Verify user owns this chat
        chat = db.query(Chat).filter(
            Chat.title == chat_id_str,
            Chat.user_id == user_id_int
        ).first()
        
        if not chat:
            return False  # User doesn't own this chat
        
        # Delete all messages first
        db.query(Message).filter(Message.chat_id == chat.id).delete()
        
        # Delete chat
        db.delete(chat)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting chat: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
