"""
SQLAlchemy models for the NLP data collection app.

This module defines the database models using SQLAlchemy ORM.
All models use UUID primary keys and are designed for PostgreSQL.
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
import uuid

from database import Base


class Dialect(PyEnum):
    """Enumeration for user dialects."""
    HUNZA = "Hunza"
    NAGAR = "Nagar"
    YASIN = "Yasin"


class User(Base):
    """
    User model representing contributors to the NLP project.

    Attributes:
        id: Unique identifier (UUID)
        username: Unique username
        dialect: User's dialect (Hunza, Nagar, or Yasin)
        trust_score: Trust score based on validation history (default 0.0)
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    dialect = Column(Enum(Dialect), nullable=False)
    trust_score = Column(Float, default=0.0)


class SourceSentence(Base):
    """
    Source sentence model for original texts to be translated.

    Attributes:
        id: Unique identifier (UUID)
        text: The original text content
        language: Language of the text (default 'English')
        is_active: Whether the sentence is active for translation (default True)
    """
    __tablename__ = "source_sentences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
    language = Column(String, default="English")
    is_active = Column(Boolean, default=True)


class Translation(Base):
    """
    Translation model for user-submitted translations of source sentences.

    Attributes:
        id: Unique identifier (UUID)
        source_id: Foreign key to SourceSentence
        user_id: Foreign key to User who created the translation
        translated_text: The translated text
        net_votes: Net validation votes (positive - negative)
        is_verified: Whether the translation is verified
    """
    __tablename__ = "translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("source_sentences.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    translated_text = Column(String, nullable=False)
    net_votes = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)


class Validation(Base):
    """
    Validation model for user votes on translations.

    Attributes:
        id: Unique identifier (UUID)
        translation_id: Foreign key to Translation being validated
        user_id: Foreign key to User who voted
        vote: Vote value (1 for upvote, -1 for downvote)
    """
    __tablename__ = "validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    translation_id = Column(UUID(as_uuid=True), ForeignKey("translations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vote = Column(Integer, nullable=False)

    # Ensure vote is either 1 or -1
    __table_args__ = (
        CheckConstraint('vote IN (1, -1)', name='check_vote_value'),
    )