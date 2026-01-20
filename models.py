from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    chats = relationship("Chat", back_populates="user", cascade="all, delete")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Response formatting preferences
    response_format = Column(String, default="formatted")  # "formatted" or "paragraph"
    use_lists = Column(Boolean, default=True)
    use_numbered = Column(Boolean, default=True)
    use_bullets = Column(Boolean, default=True)
    use_emojis = Column(Boolean, default=True)
    
    # Learning preferences
    remember_preferences = Column(Boolean, default=True)
    learning_mode = Column(Boolean, default=True)  # Learn from user interactions
    
    # Custom instructions
    custom_system_prompt = Column(Text, nullable=True)
    preferred_tone = Column(String, default="professional")  # professional, casual, formal, friendly
    preferred_language = Column(String, default="English")
    
    # Domain preferences (what user specializes in)
    specializations = Column(JSON, default={})  # {"Python": "expert", "React": "intermediate"}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for guest chats
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_guest = Column(Boolean, default=False)  # True if guest user

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
