"""
Database Models
User, Task, Memory, and other core entities
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


# ============================================================================
# Enums
# ============================================================================

import enum


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MemoryType(str, enum.Enum):
    """Memory type enumeration"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    PREFERENCE = "preference"
    PROJECT = "project"


# ============================================================================
# User Model
# ============================================================================

class User(Base):
    """
    User account model
    Stores user information and settings
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_email", "email"),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User info
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    api_key_hash = Column(String(255), nullable=True)
    preferences = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


# ============================================================================
# Task Model
# ============================================================================

class Task(Base):
    """
    Task model for tracking user requests and automated tasks
    Supports multi-step task planning and execution
    """
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_status", "status"),
        Index("idx_priority", "priority"),
        Index("idx_created_at", "created_at"),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Task info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=False)
    
    # Task execution
    status = Column(String(20), default=TaskStatus.PENDING.value, nullable=False, index=True)
    priority = Column(String(10), default=TaskPriority.MEDIUM.value, nullable=False)
    
    # Planning & execution
    steps = Column(JSON, default=[])  # List of task steps
    current_step = Column(Integer, default=0)
    execution_plan = Column(Text, nullable=True)  # LLM-generated plan
    
    # Results
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    tags = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    estimated_duration_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    execution_logs = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"


# ============================================================================
# Memory Model
# ============================================================================

class Memory(Base):
    """
    Memory model for storing context and learning
    Supports both short-term (conversation) and long-term (knowledge) memory
    Uses vector embeddings for semantic search
    """
    __tablename__ = "memories"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_memory_type", "memory_type"),
        Index("idx_created_at", "created_at"),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Memory content
    memory_type = Column(String(20), nullable=False)  # conversation, knowledge, preference, project
    content = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    
    # Vector embedding for semantic search
    embedding = Column(JSON, nullable=True)  # Store as JSON or reference to vector DB
    embedding_id = Column(String(255), nullable=True)  # ID in external vector DB
    
    # Importance and relevance
    importance_score = Column(Float, default=0.5)  # 0-1 scale
    relevance_score = Column(Float, default=0.5)  # 0-1 scale
    
    # Metadata
    tags = Column(JSON, default=[])
    source = Column(String(100), nullable=True)  # conversation, code, manual, etc.
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For auto-expiration of memories
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    def __repr__(self):
        return f"<Memory {self.title} ({self.memory_type})>"


# ============================================================================
# Execution Log Model
# ============================================================================

class ExecutionLog(Base):
    """
    Execution log for tracking task and tool execution
    Records commands, outputs, and performance metrics
    """
    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_task_id", "task_id"),
        Index("idx_created_at", "created_at"),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    
    # Execution details
    agent_type = Column(String(50), nullable=False)  # dev, web, browser, system, etc.
    tool_name = Column(String(100), nullable=False)
    command = Column(Text, nullable=False)
    
    # Input and output
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    
    # Status and performance
    status = Column(String(20), default="success")  # success, error, timeout, etc.
    execution_time_ms = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="execution_logs")
    task = relationship("Task", back_populates="execution_logs")
    
    def __repr__(self):
        return f"<ExecutionLog {self.tool_name} ({self.status})>"


# ============================================================================
# Chat Message Model (for conversation history)
# ============================================================================

class ChatMessage(Base):
    """
    Chat message history for context and learning
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Message content
    role = Column(String(10), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Metadata
    message_type = Column(String(50), default="text")  # text, voice, code, etc.
    tokens_used = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships (can add more)
    
    def __repr__(self):
        return f"<ChatMessage {self.role}>"
