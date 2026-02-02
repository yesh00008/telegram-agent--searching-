"""
Message Filtering and Job Detection Module
Implements keyword-based job detection with intelligent filtering
"""

import re
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from config import (
    JOB_CATEGORIES,
    HIRING_INTENT_KEYWORDS,
    BLOCKLIST_KEYWORDS,
    MIN_MESSAGE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    ENABLE_LINK_EXTRACTION,
    VALID_JOB_DOMAINS,
    BLOCKED_LINK_PATTERNS
)

logger = logging.getLogger(__name__)


class MessageFilter:
    """Handles message filtering and validation"""
    
    @staticmethod
    def is_valid_message(message) -> bool:
        """
        Check if message should be processed
        Filters out: media-only, forwards, short messages, etc.
        """
        # Check if message has text
        if not message.text or not message.text.strip():
            logger.debug("Rejected: No text content")
            return False
        
        # Check minimum length
        if len(message.text.strip()) < MIN_MESSAGE_LENGTH:
            logger.debug(f"Rejected: Too short ({len(message.text)} chars)")
            return False
        
        # Ignore forwarded messages (often spam/ads)
        if message.forward:
            logger.debug("Rejected: Forwarded message")
            return False
        
        # Ignore media-only messages
        if message.media and not message.text:
            logger.debug("Rejected: Media-only message")
            return False
        
        return True
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Clean and normalize text for analysis
        Removes extra whitespace, special characters, converts to lowercase
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs for cleaner keyword matching (we extract them separately)
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove Telegram usernames
        text = re.sub(r'@\w+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s\-\/]', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def contains_blocklist_terms(text: str) -> bool:
        """Check if message contains any blocklisted keywords"""
        text_lower = text.lower()
        
        for term in BLOCKLIST_KEYWORDS:
            if term.lower() in text_lower:
                logger.debug(f"Rejected: Contains blocklisted term '{term}'")
                return True
        
        return False
    
    @staticmethod
    def has_hiring_intent(text: str) -> bool:
        """Check if message contains hiring intent keywords"""
        text_lower = text.lower()
        
        for keyword in HIRING_INTENT_KEYWORDS:
            if keyword.lower() in text_lower:
                logger.debug(f"Hiring intent detected: '{keyword}'")
                return True
        
        return False


class JobDetector:
    """Detects and classifies job-related messages"""
    
    @staticmethod
    def is_fresher_job(text: str) -> bool:
        """Check if job is EXPLICITLY for 2026 passouts or freshers - STRICT FILTER"""
        text_lower = text.lower()
        import re
        
        # First, reject if experience > 0 is required
        experience_patterns = [
            r'(\d+)\+?\s*(year|yr|yrs|years)\s*(of)?\s*experience',
            r'experience\s*:\s*(\d+)',
            r'exp\s*:\s*(\d+)',
            r'(\d+)-(\d+)\s*(year|yr|yrs|years)',
            r'minimum\s*(\d+)\s*(year|yr|yrs|years)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        exp_value = match[0] if match[0].isdigit() else '0'
                    else:
                        exp_value = match if match.isdigit() else '0'
                    
                    if int(exp_value) > 0:
                        logger.debug(f"Rejected: Requires {exp_value}+ years experience")
                        return False
        
        # Check for EXPLICIT 2026 passout mentions
        passout_2026_patterns = [
            '2026 passout', '2026 pass out', '2026 graduate', '2026 batch',
            'passout 2026', 'batch 2026', 'graduating 2026', '2026 passing',
            'batch of 2026', '2026 graduation', 'class of 2026'
        ]
        
        for pattern in passout_2026_patterns:
            if pattern in text_lower:
                logger.info(f"✓ Found 2026 passout: {pattern}")
                return True
        
        # Check for EXPLICIT fresher/0 experience keywords
        fresher_keywords = [
            'fresher', 'freshers', '0 experience', 'zero experience',
            'no experience', 'no experience required', 'no prior experience',
            'entry level', 'entry-level', 'trainee', 'fresher job',
            'graduate trainee', 'campus hire', 'campus hiring',
            'fresh graduate', 'recent graduate'
        ]
        
        for keyword in fresher_keywords:
            if keyword in text_lower:
                logger.info(f"✓ Found fresher keyword: {keyword}")
                return True
        
        # STRICT: If no 2026 or fresher mention, REJECT
        logger.debug("Rejected: No explicit 2026 or fresher mention")
        return False
    
    @staticmethod
    def detect_job_category(text: str) -> Optional[str]:
        """
        Detect job category based on keywords with improved accuracy
        Returns category name or None if no match
        Uses weighted scoring for better precision
        """
        processed_text = MessageFilter.preprocess_text(text)
        original_text = text.lower()
        
        # Track matches for each category
        category_scores = {}
        
        for category, keywords in JOB_CATEGORIES.items():
            match_count = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Check for exact matches (higher weight)
                if keyword_lower in processed_text:
                    match_count += 2
                
                # Check for word boundary matches in original text
                if re.search(r'\b' + re.escape(keyword_lower) + r'\b', original_text):
                    match_count += 3
            
            if match_count > 0:
                category_scores[category] = match_count
        
        # Return category with highest match count (minimum threshold of 2)
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] >= 2:
                logger.info(f"Job category detected: {best_category[0]} (score: {best_category[1]})")
                return best_category[0]
        
        return None
    
    @staticmethod
    def is_job_post(message) -> Tuple[bool, Optional[str]]:
        """
        Main job detection logic - FILTERS FOR 2026 PASSOUTS/FRESHERS ONLY
        Returns (is_job, category) tuple
        """
        # Step 1: Basic validation
        if not MessageFilter.is_valid_message(message):
            return False, None
        
        text = message.text
        
        # Step 2: Check blocklist
        if MessageFilter.contains_blocklist_terms(text):
            return False, None
        
        # Step 3: Check hiring intent (required)
        if not MessageFilter.has_hiring_intent(text):
            logger.debug("Rejected: No hiring intent keywords found")
            return False, None
        
        # Step 4: Check if it's for freshers/2026 passouts ONLY
        if not JobDetector.is_fresher_job(text):
            logger.debug("Rejected: Not for freshers/2026 passouts")
            return False, None
        
        # Step 5: Detect job category
        category = JobDetector.detect_job_category(text)
        
        if category:
            logger.info(f"Job post detected in category: {category}")
            return True, category
        else:
            logger.debug("Rejected: No matching job category")
            return False, None
    
    @staticmethod
    def extract_description(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
        """
        Extract and format a clean short description
        Removes URLs and trims to specified length
        """
        # Remove URLs
        clean_text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove Telegram usernames
        clean_text = re.sub(r'@\w+', '', clean_text)
        
        # Remove excessive newlines
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
        
        # Trim to max length
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return clean_text.strip()


class LinkExtractor:
    """Extracts and validates job links from messages"""
    
    @staticmethod
    def extract_links(text: str) -> List[str]:
        """
        Extract valid job links from message text
        Filters out Telegram invite links and spam
        """
        if not ENABLE_LINK_EXTRACTION:
            return []
        
        # Find all URLs in text
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        valid_links = []
        
        for url in urls:
            # Skip blocked link patterns (Telegram invites, etc.)
            if any(blocked in url.lower() for blocked in BLOCKED_LINK_PATTERNS):
                logger.debug(f"Skipped blocked link: {url}")
                continue
            
            # Check if domain is in valid job domains list
            is_valid_domain = any(domain in url.lower() for domain in VALID_JOB_DOMAINS)
            
            # If no specific domain validation, allow HTTPS links that aren't blocked
            if is_valid_domain or (url.startswith('https://') and not any(blocked in url.lower() for blocked in BLOCKED_LINK_PATTERNS)):
                valid_links.append(url)
                logger.debug(f"Valid job link extracted: {url}")
        
        return valid_links
    
    @staticmethod
    def format_links(links: List[str]) -> str:
        """Format links for display in alert message"""
        if not links:
            return "No links found"
        
        if len(links) == 1:
            return links[0]
        
        # Multiple links - format as numbered list
        formatted = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links)])
        return formatted
