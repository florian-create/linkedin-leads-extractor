"""
Lead extraction and processing service
Extracts leads from LinkedIn posts (likes + comments) and enriches the data
"""
from typing import Dict, List, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session
from database import LinkedInPost, Lead, Comment
from unipile_service import UnipileService
import re


class LeadExtractor:
    def __init__(self, db: Session, unipile_service: UnipileService):
        self.db = db
        self.unipile = unipile_service

    def extract_leads_from_post(self, post_url: str, account_id: str) -> Dict:
        """
        Main function to extract all leads from a LinkedIn post
        Returns summary of extraction
        """
        # Check if post already exists
        existing_post = self.db.query(LinkedInPost).filter(
            LinkedInPost.post_url == post_url
        ).first()

        if existing_post:
            post = existing_post
            post.status = "processing"
            post.last_scraped_at = datetime.utcnow()
        else:
            # Create new post record
            post_id = self.unipile._extract_post_id(post_url)
            post = LinkedInPost(
                post_url=post_url,
                post_id=post_id,
                status="processing",
                last_scraped_at=datetime.utcnow()
            )
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

        try:
            # Extract reactions (likes)
            print(f"🔍 Extracting reactions from post: {post_url}")
            reactions = self.unipile.get_post_reactions(account_id, post.post_id)
            likes_count = len(reactions)

            # Extract comments
            print(f"💬 Extracting comments from post: {post_url}")
            comments = self.unipile.get_post_comments(account_id, post.post_id)
            comments_count = len(comments)

            # Update post stats
            post.total_likes = likes_count
            post.total_comments = comments_count

            # Track unique profiles
            unique_profiles: Set[str] = set()
            lead_details: Dict[str, Dict] = {}

            # Process reactions (likes)
            for reaction in reactions:
                author = reaction.get("author", {})
                profile_url = author.get("profile_url") or author.get("url")

                if profile_url and profile_url not in unique_profiles:
                    unique_profiles.add(profile_url)
                    lead_details[profile_url] = {
                        "full_name": author.get("name"),
                        "headline": author.get("headline"),
                        "profile_picture_url": author.get("profile_picture") or author.get("picture"),
                        "liked": True,
                        "commented": False,
                        "comment_count": 0,
                        "interaction_type": "like"
                    }
                elif profile_url in lead_details:
                    lead_details[profile_url]["liked"] = True

            # Process comments
            for comment in comments:
                author = comment.get("author", {})
                profile_url = author.get("profile_url") or author.get("url")

                if profile_url:
                    if profile_url not in unique_profiles:
                        unique_profiles.add(profile_url)
                        lead_details[profile_url] = {
                            "full_name": author.get("name"),
                            "headline": author.get("headline"),
                            "profile_picture_url": author.get("profile_picture") or author.get("picture"),
                            "liked": False,
                            "commented": True,
                            "comment_count": 1,
                            "interaction_type": "comment"
                        }
                    else:
                        lead_details[profile_url]["commented"] = True
                        lead_details[profile_url]["comment_count"] += 1
                        # Update interaction type
                        if lead_details[profile_url]["liked"]:
                            lead_details[profile_url]["interaction_type"] = "both"
                        else:
                            lead_details[profile_url]["interaction_type"] = "comment"

                # Save comment to database
                self._save_comment(post.id, comment)

            # Save leads to database
            saved_leads = 0
            for profile_url, details in lead_details.items():
                lead = self._save_lead(post.id, profile_url, details)
                if lead:
                    saved_leads += 1

            # Update post status
            post.status = "completed"
            post.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "post_id": post.id,
                "post_url": post_url,
                "stats": {
                    "total_likes": likes_count,
                    "total_comments": comments_count,
                    "unique_leads": len(unique_profiles),
                    "leads_saved": saved_leads
                }
            }

        except Exception as e:
            post.status = "failed"
            self.db.commit()
            print(f"❌ Error extracting leads: {e}")
            return {
                "success": False,
                "error": str(e),
                "post_url": post_url
            }

    def _save_lead(self, post_id: int, profile_url: str, details: Dict) -> Optional[Lead]:
        """Save or update a lead in the database"""
        try:
            # Check if lead already exists for this post
            existing_lead = self.db.query(Lead).filter(
                Lead.post_id == post_id,
                Lead.linkedin_profile_url == profile_url
            ).first()

            if existing_lead:
                # Update existing lead
                for key, value in details.items():
                    setattr(existing_lead, key, value)
                lead = existing_lead
            else:
                # Create new lead
                lead = Lead(
                    post_id=post_id,
                    linkedin_profile_url=profile_url,
                    **details
                )
                self.db.add(lead)

            self.db.commit()
            self.db.refresh(lead)
            return lead

        except Exception as e:
            print(f"❌ Error saving lead {profile_url}: {e}")
            self.db.rollback()
            return None

    def _save_comment(self, post_id: int, comment_data: Dict) -> Optional[Comment]:
        """Save a comment to the database"""
        try:
            comment_id = comment_data.get("id")

            # Check if comment already exists
            existing_comment = self.db.query(Comment).filter(
                Comment.comment_id == comment_id
            ).first()

            if existing_comment:
                return existing_comment

            # Create new comment
            comment = Comment(
                post_id=post_id,
                comment_id=comment_id,
                content=comment_data.get("content", ""),
                likes_count=comment_data.get("likes_count", 0),
                replies_count=comment_data.get("replies_count", 0),
                posted_at=self._parse_datetime(comment_data.get("created_at"))
            )

            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            return comment

        except Exception as e:
            print(f"❌ Error saving comment: {e}")
            self.db.rollback()
            return None

    def enrich_lead(self, lead_id: int, account_id: str) -> bool:
        """Enrich a lead with additional profile information"""
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return False

            # Get profile details from Unipile
            profile_data = self.unipile.get_profile_details(
                account_id,
                lead.linkedin_profile_url
            )

            if profile_data:
                # Update lead with enriched data
                lead.company = profile_data.get("company")
                lead.job_title = profile_data.get("headline") or profile_data.get("job_title")
                lead.location = profile_data.get("location")
                lead.industry = profile_data.get("industry")
                lead.enriched = True
                lead.enrichment_data = profile_data

                self.db.commit()
                return True

            return False

        except Exception as e:
            print(f"❌ Error enriching lead {lead_id}: {e}")
            self.db.rollback()
            return False

    def enrich_all_leads(self, post_id: int, account_id: str) -> Dict:
        """Enrich all leads from a specific post"""
        try:
            leads = self.db.query(Lead).filter(
                Lead.post_id == post_id,
                Lead.enriched == False
            ).all()

            enriched_count = 0
            failed_count = 0

            for lead in leads:
                if self.enrich_lead(lead.id, account_id):
                    enriched_count += 1
                else:
                    failed_count += 1

            return {
                "success": True,
                "total_leads": len(leads),
                "enriched": enriched_count,
                "failed": failed_count
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not date_string:
            return None

        try:
            # Try ISO format
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        except:
            try:
                # Try common formats
                return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            except:
                return None
