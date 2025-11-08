"""
LinkedIn Leads SaaS - FastAPI Backend
Main application with API endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
import os
import io
import csv
import pandas as pd

from database import get_db, init_db, LinkedInPost, Lead, Comment, UnipileAccount
from unipile_service import UnipileService, MockUnipileService
from lead_extractor import LeadExtractor

# Initialize FastAPI app
app = FastAPI(
    title="LinkedIn Leads Extractor API",
    description="Extract leads from LinkedIn posts (likes & comments)",
    version="1.0.0"
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ LinkedIn Leads SaaS API is ready!")


# Pydantic models for requests/responses
class PostURLRequest(BaseModel):
    post_url: str
    account_id: Optional[str] = None
    enrich: bool = False


class PostResponse(BaseModel):
    id: int
    post_url: str
    post_id: str
    total_likes: int
    total_comments: int
    status: str
    created_at: datetime
    last_scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    linkedin_profile_url: str
    full_name: Optional[str]
    headline: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    interaction_type: str
    liked: bool
    commented: bool
    comment_count: int
    enriched: bool

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_posts: int
    total_leads: int
    total_likes: int
    total_comments: int


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "LinkedIn Leads Extractor API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/accounts")
async def get_unipile_accounts(db: Session = Depends(get_db)):
    """Get all connected Unipile LinkedIn accounts"""
    try:
        # Check if we should use mock service (for testing)
        use_mock = os.getenv("USE_MOCK_UNIPILE", "false").lower() == "true"

        if use_mock:
            unipile = MockUnipileService()
        else:
            unipile = UnipileService()

        accounts = unipile.get_accounts()

        # Save accounts to database
        for acc in accounts:
            existing = db.query(UnipileAccount).filter(
                UnipileAccount.account_id == acc.get("id")
            ).first()

            if not existing:
                db_account = UnipileAccount(
                    account_id=acc.get("id"),
                    provider=acc.get("provider", "LINKEDIN"),
                    username=acc.get("username"),
                    status=acc.get("status")
                )
                db.add(db_account)

        db.commit()
        return {"accounts": accounts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/posts/extract")
async def extract_leads_from_post(
    request: PostURLRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Extract leads from a LinkedIn post URL
    This will scrape all likes and comments and save them to the database
    """
    try:
        # Get Unipile service
        use_mock = os.getenv("USE_MOCK_UNIPILE", "false").lower() == "true"
        unipile = MockUnipileService() if use_mock else UnipileService()

        # Get account_id (use first available if not provided)
        account_id = request.account_id
        if not account_id:
            accounts = unipile.get_accounts()
            if not accounts:
                raise HTTPException(
                    status_code=400,
                    detail="No Unipile accounts available. Please connect a LinkedIn account first."
                )
            account_id = accounts[0].get("id")

        # Create lead extractor
        extractor = LeadExtractor(db, unipile)

        # Extract leads
        result = extractor.extract_leads_from_post(request.post_url, account_id)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))

        # Enrich leads in background if requested
        if request.enrich:
            background_tasks.add_task(
                extractor.enrich_all_leads,
                result["post_id"],
                account_id
            )

        return {
            "message": "Leads extracted successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts", response_model=List[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all analyzed posts"""
    query = db.query(LinkedInPost)

    if status:
        query = query.filter(LinkedInPost.status == status)

    posts = query.order_by(LinkedInPost.created_at.desc()).offset(skip).limit(limit).all()
    return posts


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@app.get("/api/posts/{post_id}/leads", response_model=List[LeadResponse])
async def get_post_leads(
    post_id: int,
    skip: int = 0,
    limit: int = 100,
    interaction_type: Optional[str] = Query(None, description="Filter by: like, comment, both"),
    db: Session = Depends(get_db)
):
    """Get all leads from a specific post"""
    query = db.query(Lead).filter(Lead.post_id == post_id)

    if interaction_type:
        query = query.filter(Lead.interaction_type == interaction_type)

    leads = query.offset(skip).limit(limit).all()
    return leads


@app.post("/api/posts/{post_id}/enrich")
async def enrich_post_leads(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Enrich all leads from a post with additional profile data"""
    try:
        # Get Unipile service
        use_mock = os.getenv("USE_MOCK_UNIPILE", "false").lower() == "true"
        unipile = MockUnipileService() if use_mock else UnipileService()

        # Get account
        accounts = unipile.get_accounts()
        if not accounts:
            raise HTTPException(status_code=400, detail="No Unipile accounts available")

        account_id = accounts[0].get("id")

        # Create extractor and enrich in background
        extractor = LeadExtractor(db, unipile)
        background_tasks.add_task(extractor.enrich_all_leads, post_id, account_id)

        return {"message": "Enrichment started in background"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}/export/csv")
async def export_leads_csv(post_id: int, db: Session = Depends(get_db)):
    """Export leads from a post to CSV"""
    try:
        leads = db.query(Lead).filter(Lead.post_id == post_id).all()

        if not leads:
            raise HTTPException(status_code=404, detail="No leads found for this post")

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Full Name", "LinkedIn URL", "Headline", "Company", "Job Title",
            "Location", "Industry", "Interaction Type", "Liked", "Commented",
            "Comment Count", "Enriched"
        ])

        # Write data
        for lead in leads:
            writer.writerow([
                lead.full_name or "",
                lead.linkedin_profile_url or "",
                lead.headline or "",
                lead.company or "",
                lead.job_title or "",
                lead.location or "",
                lead.industry or "",
                lead.interaction_type or "",
                lead.liked,
                lead.commented,
                lead.comment_count,
                lead.enriched
            ])

        # Return CSV file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=leads_post_{post_id}.csv"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}/export/excel")
async def export_leads_excel(post_id: int, db: Session = Depends(get_db)):
    """Export leads from a post to Excel"""
    try:
        leads = db.query(Lead).filter(Lead.post_id == post_id).all()

        if not leads:
            raise HTTPException(status_code=404, detail="No leads found for this post")

        # Create DataFrame
        data = [{
            "Full Name": lead.full_name or "",
            "LinkedIn URL": lead.linkedin_profile_url or "",
            "Headline": lead.headline or "",
            "Company": lead.company or "",
            "Job Title": lead.job_title or "",
            "Location": lead.location or "",
            "Industry": lead.industry or "",
            "Interaction Type": lead.interaction_type or "",
            "Liked": lead.liked,
            "Commented": lead.commented,
            "Comment Count": lead.comment_count,
            "Enriched": lead.enriched
        } for lead in leads]

        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=leads_post_{post_id}.xlsx"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_posts = db.query(LinkedInPost).count()
    total_leads = db.query(Lead).count()
    total_likes = db.query(Lead).filter(Lead.liked == True).count()
    total_comments = db.query(Lead).filter(Lead.commented == True).count()

    return {
        "total_posts": total_posts,
        "total_leads": total_leads,
        "total_likes": total_likes,
        "total_comments": total_comments
    }


@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post and all its leads"""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )
