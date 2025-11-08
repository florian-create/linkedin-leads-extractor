"""
Service to interact with Unipile API for LinkedIn data extraction
Documentation: https://docs.unipile.com
"""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class UnipileService:
    def __init__(self):
        self.api_key = os.getenv("UNIPILE_API_KEY")
        self.base_url = os.getenv("UNIPILE_BASE_URL", "https://api.unipile.com/v1")
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def get_accounts(self) -> List[Dict]:
        """Get all connected LinkedIn accounts"""
        try:
            response = requests.get(
                f"{self.base_url}/accounts",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching accounts: {e}")
            return []

    def get_post_details(self, account_id: str, post_url: str) -> Optional[Dict]:
        """
        Get LinkedIn post details
        Note: Unipile might require the post to be fetched through their messaging endpoints
        """
        try:
            # Extract post ID from URL
            # LinkedIn post URLs are typically like:
            # https://www.linkedin.com/posts/username_activity-1234567890-abcd
            post_id = self._extract_post_id(post_url)

            # Try to fetch post details (this endpoint may vary based on Unipile's actual API)
            response = requests.get(
                f"{self.base_url}/posts/{post_id}",
                headers=self.headers,
                params={"account_id": account_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching post details: {e}")
            return None

    def get_post_reactions(self, account_id: str, post_id: str) -> List[Dict]:
        """
        Get all reactions (likes) on a LinkedIn post
        """
        try:
            # Unipile endpoint for reactions
            response = requests.get(
                f"{self.base_url}/posts/{post_id}/reactions",
                headers=self.headers,
                params={
                    "account_id": account_id,
                    "limit": 100  # Adjust based on Unipile's pagination
                }
            )
            response.raise_for_status()
            data = response.json()

            reactions = []
            if isinstance(data, dict) and "items" in data:
                reactions = data["items"]
            elif isinstance(data, list):
                reactions = data

            return reactions
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching reactions: {e}")
            return []

    def get_post_comments(self, account_id: str, post_id: str) -> List[Dict]:
        """
        Get all comments on a LinkedIn post
        """
        try:
            response = requests.get(
                f"{self.base_url}/posts/{post_id}/comments",
                headers=self.headers,
                params={
                    "account_id": account_id,
                    "limit": 100
                }
            )
            response.raise_for_status()
            data = response.json()

            comments = []
            if isinstance(data, dict) and "items" in data:
                comments = data["items"]
            elif isinstance(data, list):
                comments = data

            return comments
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching comments: {e}")
            return []

    def get_profile_details(self, account_id: str, profile_url: str) -> Optional[Dict]:
        """
        Get detailed profile information for enrichment
        """
        try:
            # Extract LinkedIn username from profile URL
            username = self._extract_username_from_url(profile_url)

            response = requests.get(
                f"{self.base_url}/users/{username}",
                headers=self.headers,
                params={"account_id": account_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching profile details: {e}")
            return None

    def search_posts(self, account_id: str, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for LinkedIn posts based on a query
        """
        try:
            response = requests.get(
                f"{self.base_url}/search/posts",
                headers=self.headers,
                params={
                    "account_id": account_id,
                    "query": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data if isinstance(data, list) else []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching posts: {e}")
            return []

    @staticmethod
    def _extract_post_id(post_url: str) -> str:
        """Extract post ID from LinkedIn URL"""
        # LinkedIn URLs: https://www.linkedin.com/posts/username_activity-1234567890-abcd
        # or: https://www.linkedin.com/feed/update/urn:li:activity:1234567890

        if "activity-" in post_url:
            # Extract the activity ID after "activity-"
            parts = post_url.split("activity-")
            if len(parts) > 1:
                post_id = parts[1].split("-")[0]
                return post_id
        elif "urn:li:activity:" in post_url:
            parts = post_url.split("urn:li:activity:")
            if len(parts) > 1:
                return parts[1].split("/")[0]

        # Return the full URL if we can't extract an ID
        return post_url

    @staticmethod
    def _extract_username_from_url(profile_url: str) -> str:
        """Extract LinkedIn username from profile URL"""
        # https://www.linkedin.com/in/username/
        if "/in/" in profile_url:
            parts = profile_url.split("/in/")
            if len(parts) > 1:
                username = parts[1].rstrip("/").split("/")[0]
                return username
        return profile_url


# Alternative: Mock service for testing without Unipile API
class MockUnipileService(UnipileService):
    """Mock service for testing purposes"""

    def get_accounts(self) -> List[Dict]:
        return [{
            "id": "mock_account_123",
            "provider": "LINKEDIN",
            "username": "test@example.com",
            "status": "VALID"
        }]

    def get_post_reactions(self, account_id: str, post_id: str) -> List[Dict]:
        """Return mock reactions"""
        return [
            {
                "id": "reaction_1",
                "author": {
                    "name": "John Doe",
                    "profile_url": "https://linkedin.com/in/johndoe",
                    "headline": "CEO at TechCorp",
                    "profile_picture": "https://example.com/photo1.jpg"
                },
                "reaction_type": "LIKE",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "reaction_2",
                "author": {
                    "name": "Jane Smith",
                    "profile_url": "https://linkedin.com/in/janesmith",
                    "headline": "CTO at StartupXYZ",
                    "profile_picture": "https://example.com/photo2.jpg"
                },
                "reaction_type": "LIKE",
                "created_at": datetime.utcnow().isoformat()
            }
        ]

    def get_post_comments(self, account_id: str, post_id: str) -> List[Dict]:
        """Return mock comments"""
        return [
            {
                "id": "comment_1",
                "content": "Great post! Very insightful.",
                "author": {
                    "name": "Alice Johnson",
                    "profile_url": "https://linkedin.com/in/alicejohnson",
                    "headline": "Marketing Director",
                    "profile_picture": "https://example.com/photo3.jpg"
                },
                "likes_count": 5,
                "replies_count": 2,
                "created_at": datetime.utcnow().isoformat()
            }
        ]

    def get_profile_details(self, account_id: str, profile_url: str) -> Optional[Dict]:
        """Return mock profile details"""
        return {
            "name": "John Doe",
            "headline": "CEO at TechCorp",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "industry": "Technology",
            "profile_url": profile_url
        }
