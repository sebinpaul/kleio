import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ClerkUserService:
    """Service for interacting with Clerk API to get user information"""
    
    def __init__(self):
        self.secret_key = os.environ.get("CLERK_SECRET_KEY")
        self.api_url = "https://api.clerk.com/v1"
        
        if not self.secret_key:
            logger.warning("CLERK_SECRET_KEY not found in environment variables")
    
    def get_user_email(self, clerk_user_id: str) -> Optional[str]:
        """Get user email from Clerk API"""
        try:
            if not self.secret_key:
                logger.error("Cannot get user email: CLERK_SECRET_KEY not configured")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/users/{clerk_user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Successfully retrieved user data for {clerk_user_id}")
                
                # Get primary email address
                primary_email_id = user_data.get('primary_email_address_id')
                email_addresses = user_data.get('email_addresses', [])
                
                # Try to find primary email first
                if primary_email_id:
                    for email_data in email_addresses:
                        if email_data.get('id') == primary_email_id:
                            email = email_data.get('email_address')
                            logger.info(f"Found primary email for user {clerk_user_id}: {email}")
                            return email
                
                # Fallback to first verified email
                for email_data in email_addresses:
                    if email_data.get('verification', {}).get('status') == 'verified':
                        email = email_data.get('email_address')
                        logger.info(f"Found verified email for user {clerk_user_id}: {email}")
                        return email
                
                # Fallback to first email if no verified ones
                if email_addresses:
                    email = email_addresses[0].get('email_address')
                    logger.info(f"Found first email for user {clerk_user_id}: {email}")
                    return email
                
                logger.warning(f"No email addresses found for user {clerk_user_id}")
                return None
            
            elif response.status_code == 404:
                logger.error(f"User not found in Clerk: {clerk_user_id}")
                return None
            else:
                logger.error(f"Clerk API error for user {clerk_user_id}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout getting user email from Clerk for user {clerk_user_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting user email from Clerk for user {clerk_user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user email from Clerk for user {clerk_user_id}: {e}")
            return None
    
    def get_user_info(self, clerk_user_id: str) -> Optional[dict]:
        """Get full user information from Clerk API"""
        try:
            if not self.secret_key:
                logger.error("Cannot get user info: CLERK_SECRET_KEY not configured")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/users/{clerk_user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Clerk API error for user {clerk_user_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info from Clerk for user {clerk_user_id}: {e}")
            return None
    
    def is_user_valid(self, clerk_user_id: str) -> bool:
        """Check if a user exists and is valid in Clerk"""
        try:
            user_info = self.get_user_info(clerk_user_id)
            return user_info is not None
        except Exception as e:
            logger.error(f"Error checking user validity for {clerk_user_id}: {e}")
            return False

# Global instance
clerk_user_service = ClerkUserService() 