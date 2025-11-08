"""
Database models and connection setup for LinkedIn Leads SaaS
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./linkedin_leads.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LinkedInPost(Base):
    """LinkedIn post that was analyzed"""
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_url = Column(String, unique=True, index=True, nullable=False)
    post_id = Column(String, unique=True, index=True)
    author_name = Column(String)
    author_profile_url = Column(String)
    content = Column(Text)
    posted_at = Column(DateTime)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime)
    status = Column(String, default="pending")  # pending, processing, completed, failed

    # Relationships
    leads = relationship("Lead", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Lead(Base):
    """A person who liked or commented on a LinkedIn post"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("linkedin_posts.id", ondelete="CASCADE"))

    # Basic LinkedIn info
    linkedin_profile_url = Column(String, index=True)
    full_name = Column(String)
    headline = Column(String)
    profile_picture_url = Column(String)

    # Enriched data
    company = Column(String)
    job_title = Column(String)
    location = Column(String)
    industry = Column(String)
    email = Column(String)
    phone = Column(String)

    # Interaction type
    interaction_type = Column(String)  # like, comment, both
    commented = Column(Boolean, default=False)
    liked = Column(Boolean, default=False)
    comment_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    enriched = Column(Boolean, default=False)
    enrichment_data = Column(JSON)  # Store additional enrichment data

    # Relationships
    post = relationship("LinkedInPost", back_populates="leads")
    comments = relationship("Comment", back_populates="lead")


class Comment(Base):
    """Comments on LinkedIn posts"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("linkedin_posts.id", ondelete="CASCADE"))
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"))

    comment_id = Column(String, unique=True)
    content = Column(Text)
    likes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    posted_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("LinkedInPost", back_populates="comments")
    lead = relationship("Lead", back_populates="comments")


class Workspace(Base):
    """User workspaces to organize multiple scraping projects"""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UnipileAccount(Base):
    """Store Unipile account connections"""
    __tablename__ = "unipile_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, nullable=False)
    provider = Column(String, default="LINKEDIN")
    username = Column(String)
    status = Column(String)  # VALID, INVALID, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    init_db()
