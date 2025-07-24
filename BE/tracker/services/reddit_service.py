import praw
import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from ..models import RedditToken, Keyword, Mention
from ..enums import Platform

logger = logging.getLogger(__name__)


class RedditService:
    """Service for interacting with Reddit API using PRAW"""
    
    def __init__(self):
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.user_agent = settings.REDDIT_USER_AGENT
        self.base_url = settings.REDDIT_BASE_URL
        self.auth_url = settings.REDDIT_AUTH_URL
        
    def get_reddit_instance(self, access_token=None):
        """Get a PRAW Reddit instance"""
        if access_token:
            # Use OAuth token if provided
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                access_token=access_token
            )
        else:
            # Use application-only OAuth (read-only)
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
        
        return reddit
    
    def get_user_token(self, user_id):
        """Get Reddit token for a user"""
        try:
            token = RedditToken.objects.get(user_id=user_id, is_valid=True)
            return token
        except RedditToken.DoesNotExist:
            logger.warning(f"No valid Reddit token found for user {user_id}")
            return None
    
    def search_reddit(self, query, subreddit=None, limit=25, sort='relevance', time_filter='day', user_id=None):
        """
        Search Reddit for posts containing the query
        
        Args:
            query (str): Search query
            subreddit (str): Specific subreddit to search (optional)
            limit (int): Number of results to return
            sort (str): Sort method (relevance, hot, top, new, comments)
            time_filter (str): Time filter (hour, day, week, month, year, all)
            user_id (str): User ID for OAuth token (optional)
        
        Returns:
            list: List of Reddit posts
        """
        try:
            # Get user token if provided
            token = None
            if user_id:
                token = self.get_user_token(user_id)
            
            reddit = self.get_reddit_instance(access_token=token.access_token if token else None)
            
            if subreddit:
                # Search in specific subreddit
                subreddit_instance = reddit.subreddit(subreddit)
                search_results = subreddit_instance.search(
                    query, 
                    sort=sort, 
                    time_filter=time_filter, 
                    limit=limit
                )
            else:
                # Search across all of Reddit
                print(f"Searching across all of Reddit for query: {query}")
                search_results = reddit.subreddit('all').search(
                    query, 
                    sort=sort, 
                    time_filter=time_filter, 
                    limit=limit
                )
            
            posts = []
            for submission in search_results:
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'content': submission.selftext,
                    'url': submission.url,
                    'permalink': f"https://reddit.com{submission.permalink}",
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'created_utc': datetime.fromtimestamp(submission.created_utc),
                    'upvote_ratio': submission.upvote_ratio,
                    'is_self': submission.is_self,
                    'domain': submission.domain,
                }
                posts.append(post_data)
            
            logger.info(f"Found {len(posts)} Reddit posts for query: {query}")
            return posts
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {str(e)}")
            return []
    
    def search_comments(self, query, subreddit=None, limit=25, user_id=None):
        """
        Search Reddit comments for the query
        
        Args:
            query (str): Search query
            subreddit (str): Specific subreddit to search (optional)
            limit (int): Number of results to return
            user_id (str): User ID for OAuth token (optional)
        
        Returns:
            list: List of Reddit comments
        """
        try:
            # Get user token if provided
            token = None
            if user_id:
                token = self.get_user_token(user_id)
            
            reddit = self.get_reddit_instance(access_token=token.access_token if token else None)
            
            if subreddit:
                # Search comments in specific subreddit
                subreddit_instance = reddit.subreddit(subreddit)
                search_results = subreddit_instance.search(
                    query, 
                    sort='relevance', 
                    time_filter='day', 
                    limit=limit,
                    syntax='lucene'
                )
            else:
                # Search comments across all of Reddit
                search_results = reddit.subreddit('all').search(
                    query, 
                    sort='relevance', 
                    time_filter='day', 
                    limit=limit,
                    syntax='lucene'
                )
            
            comments = []
            for submission in search_results:
                # Get comments for each submission
                submission.comments.replace_more(limit=0)  # Don't load MoreComments
                for comment in submission.comments.list():
                    if query.lower() in comment.body.lower():
                        comment_data = {
                            'id': comment.id,
                            'content': comment.body,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'permalink': f"https://reddit.com{comment.permalink}",
                            'subreddit': comment.subreddit.display_name,
                            'score': comment.score,
                            'created_utc': datetime.fromtimestamp(comment.created_utc),
                            'parent_id': comment.parent_id,
                            'submission_title': submission.title,
                            'submission_url': f"https://reddit.com{submission.permalink}",
                        }
                        comments.append(comment_data)
                        
                        if len(comments) >= limit:
                            break
                
                if len(comments) >= limit:
                    break
            
            logger.info(f"Found {len(comments)} Reddit comments for query: {query}")
            return comments
            
        except Exception as e:
            logger.error(f"Error searching Reddit comments: {str(e)}")
            return []
    
    def monitor_keywords(self, keywords):
        """
        Monitor keywords and return new mentions
        
        Args:
            keywords (list): List of Keyword objects to monitor
        
        Returns:
            list: List of new mentions found
        """
        mentions = []
        
        for keyword in keywords:
            if keyword.platform in [Platform.REDDIT.value, Platform.ALL.value]:
                try:
                    # Search for posts - use first filter or 'all' if no filters
                    subreddit_filter = keyword.platform_specific_filters[0] if keyword.platform_specific_filters else 'all'
                    posts = self.search_reddit(
                        query=keyword.keyword,
                        subreddit=subreddit_filter,
                        limit=50,
                        time_filter='day',
                        user_id=keyword.user_id
                    )
                    
                    # Search for comments - use first filter or 'all' if no filters
                    comments = self.search_comments(
                        query=keyword.keyword,
                        subreddit=subreddit_filter,
                        limit=50,
                        user_id=keyword.user_id
                    )
                    
                    # Process posts
                    for post in posts:
                        mention = self._create_mention_from_post(keyword, post)
                        if mention:
                            mentions.append(mention)
                    
                    # Process comments
                    for comment in comments:
                        mention = self._create_mention_from_comment(keyword, comment)
                        if mention:
                            mentions.append(mention)
                            
                except Exception as e:
                    logger.error(f"Error monitoring keyword {keyword.keyword}: {str(e)}")
                    continue
        
        return mentions
    
    def _create_mention_from_post(self, keyword, post):
        """Create a Mention object from a Reddit post"""
        try:
            # Check if mention already exists
            existing_mention = Mention.objects.filter(
                source_url=post['permalink'],
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=post['content'] or post['title'],
                title=post['title'],
                author=post['author'],
                source_url=post['permalink'],
                platform=Platform.REDDIT.value,
                subreddit=post['subreddit'],
                mention_date=post['created_utc']
            )
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from post: {str(e)}")
            return None
    
    def _create_mention_from_comment(self, keyword, comment):
        """Create a Mention object from a Reddit comment"""
        try:
            # Check if mention already exists
            existing_mention = Mention.objects.filter(
                source_url=comment['permalink'],
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=comment['content'],
                title=comment.get('submission_title', ''),
                author=comment['author'],
                source_url=comment['permalink'],
                platform=Platform.REDDIT.value,
                subreddit=comment['subreddit'],
                mention_date=comment['created_utc']
            )
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from comment: {str(e)}")
            return None
    
    def get_subreddit_info(self, subreddit_name):
        """Get information about a subreddit"""
        try:
            reddit = self.get_reddit_instance()
            subreddit = reddit.subreddit(subreddit_name)
            
            return {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.description,
                'subscribers': subreddit.subscribers,
                'active_user_count': subreddit.active_user_count,
                'public_description': subreddit.public_description,
                'url': f"https://reddit.com/r/{subreddit.display_name}",
                'created_utc': datetime.fromtimestamp(subreddit.created_utc),
            }
            
        except Exception as e:
            logger.error(f"Error getting subreddit info for {subreddit_name}: {str(e)}")
            return None
    
    def validate_token(self, access_token):
        """Validate a Reddit access token"""
        try:
            reddit = self.get_reddit_instance(access_token=access_token)
            # Try to access user info to validate token
            user = reddit.user.me()
            return {
                'valid': True,
                'username': user.name,
                'karma': user.link_karma + user.comment_karma,
                'created_utc': datetime.fromtimestamp(user.created_utc)
            }
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return {'valid': False, 'error': str(e)}
