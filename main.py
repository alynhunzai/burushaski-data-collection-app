from typing import List
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, SourceSentence, Translation, Validation, Dialect


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    dialect: Dialect


class UserRead(BaseModel):
    id: UUID
    username: str
    dialect: Dialect
    trust_score: float

    class Config:
        orm_mode = True


class SourceSentenceRead(BaseModel):
    id: UUID
    text: str
    language: str
    is_active: bool

    class Config:
        orm_mode = True


class TranslationCreate(BaseModel):
    source_id: UUID
    user_id: UUID
    translated_text: str = Field(..., min_length=1)


class TranslationRead(BaseModel):
    id: UUID
    source_id: UUID
    user_id: UUID
    translated_text: str
    net_votes: int
    is_verified: bool

    class Config:
        orm_mode = True


class ValidationCreate(BaseModel):
    translation_id: UUID
    user_id: UUID
    vote: int

    @validator("vote")
    def validate_vote(cls, value: int) -> int:
        if value not in (1, -1):
            raise ValueError("vote must be 1 or -1")
        return value


class ValidationRead(BaseModel):
    id: UUID
    translation_id: UUID
    user_id: UUID
    vote: int

    class Config:
        orm_mode = True


app = FastAPI(
    title="NLP Data Collection API",
    description="Backend service for collecting user translations, validations, and source sentences.",
    version="1.0.0",
)


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    user = User(
        username=user_in.username,
        dialect=user_in.dialect,
        trust_score=0.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/sentences/random", response_model=SourceSentenceRead)
def get_random_sentence(db: Session = Depends(get_db)) -> SourceSentence:
    sentence = (
        db.query(SourceSentence)
        .filter(SourceSentence.is_active.is_(True))
        .order_by(func.random())
        .first()
    )
    if sentence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active source sentences available.",
        )
    return sentence


@app.post("/translations/", response_model=TranslationRead, status_code=status.HTTP_201_CREATED)
def create_translation(translation_in: TranslationCreate, db: Session = Depends(get_db)) -> Translation:
    source = db.query(SourceSentence).get(translation_in.source_id)
    if source is None or not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source sentence not found or is not active.",
        )

    user = db.query(User).get(translation_in.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    translation = Translation(
        source_id=translation_in.source_id,
        user_id=translation_in.user_id,
        translated_text=translation_in.translated_text,
        net_votes=0,
        is_verified=False,
    )
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation


@app.get("/translations/unverified", response_model=List[TranslationRead])
def get_unverified_translations(db: Session = Depends(get_db)) -> List[Translation]:
    translations = (
        db.query(Translation)
        .filter(Translation.net_votes >= -2, Translation.net_votes <= 2)
        .all()
    )
    return translations


@app.post("/validations/", response_model=ValidationRead, status_code=status.HTTP_201_CREATED)
def create_validation(validation_in: ValidationCreate, db: Session = Depends(get_db)) -> Validation:
    translation = db.query(Translation).get(validation_in.translation_id)
    if translation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found.",
        )

    user = db.query(User).get(validation_in.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    validation = Validation(
        translation_id=validation_in.translation_id,
        user_id=validation_in.user_id,
        vote=validation_in.vote,
    )
    translation.net_votes += validation_in.vote

    db.add(validation)
    db.add(translation)
    db.commit()
    db.refresh(validation)
    return validation

@app.get("/sentences/{sentence_id}", response_model=SourceSentenceRead)
def get_sentence_by_id(sentence_id: UUID, db: Session = Depends(get_db)):
    sentence = db.query(SourceSentence).filter(SourceSentence.id == sentence_id).first()
    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sentence not found."
        )
    return sentence
