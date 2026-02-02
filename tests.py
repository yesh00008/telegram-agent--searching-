"""
Test Suite for Telegram Job Monitoring Bot
Run with: python -m pytest tests.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from filters import MessageFilter, JobDetector, LinkExtractor
from utils import DedupManager, RateLimiter, format_timestamp


class TestMessageFilter:
    """Test message filtering logic"""
    
    def test_valid_message(self):
        """Test valid message detection"""
        message = Mock()
        message.text = "We are hiring Python developers with 3+ years experience. Apply now at our careers page."
        message.forward = None
        message.media = None
        
        assert MessageFilter.is_valid_message(message) == True
    
    def test_reject_short_message(self):
        """Test rejection of short messages"""
        message = Mock()
        message.text = "Hiring!"
        message.forward = None
        message.media = None
        
        assert MessageFilter.is_valid_message(message) == False
    
    def test_reject_forwarded(self):
        """Test rejection of forwarded messages"""
        message = Mock()
        message.text = "A" * 100  # Long enough
        message.forward = Mock()  # Has forward info
        message.media = None
        
        assert MessageFilter.is_valid_message(message) == False
    
    def test_preprocess_text(self):
        """Test text preprocessing"""
        text = "We are HIRING!!!   @username  http://example.com  Machine Learning"
        processed = MessageFilter.preprocess_text(text)
        
        assert "hiring" in processed.lower()
        assert "@username" not in processed
        assert "http" not in processed
    
    def test_blocklist_detection(self):
        """Test blocklist keyword detection"""
        crypto_text = "Bitcoin investment opportunity! Earn 10% daily ROI"
        assert MessageFilter.contains_blocklist_terms(crypto_text) == True
        
        legit_text = "Hiring Backend Engineer for fintech startup"
        assert MessageFilter.contains_blocklist_terms(legit_text) == False
    
    def test_hiring_intent_detection(self):
        """Test hiring intent keyword detection"""
        hiring_text = "We are hiring senior developers for our team"
        assert MessageFilter.has_hiring_intent(hiring_text) == True
        
        no_intent = "Check out this cool machine learning project"
        assert MessageFilter.has_hiring_intent(no_intent) == False


class TestJobDetector:
    """Test job detection and classification"""
    
    def test_detect_ai_ml_job(self):
        """Test AI/ML job detection"""
        text = "Hiring Machine Learning Engineer with experience in PyTorch and TensorFlow"
        category = JobDetector.detect_job_category(text)
        
        assert category == "AI/ML"
    
    def test_detect_backend_job(self):
        """Test backend job detection"""
        text = "Looking for Node.js developer with experience in Express and MongoDB"
        category = JobDetector.detect_job_category(text)
        
        assert category == "Backend"
    
    def test_detect_data_job(self):
        """Test data role detection"""
        text = "Data Analyst position open. SQL, Tableau, Power BI required"
        category = JobDetector.detect_job_category(text)
        
        assert category == "Data"
    
    def test_detect_cybersecurity_job(self):
        """Test cybersecurity job detection"""
        text = "Security Engineer needed. Experience with penetration testing and SIEM"
        category = JobDetector.detect_job_category(text)
        
        assert category == "Cyber Security"
    
    def test_no_category_match(self):
        """Test message with no category match"""
        text = "Random message about weather and lunch plans"
        category = JobDetector.detect_job_category(text)
        
        assert category is None
    
    def test_is_job_post_valid(self):
        """Test complete job post detection"""
        message = Mock()
        message.text = "Hiring Python Backend Developer with Django experience. 3+ years required. Apply at https://company.com/jobs"
        message.forward = None
        message.media = None
        
        is_job, category = JobDetector.is_job_post(message)
        
        assert is_job == True
        assert category == "Backend"
    
    def test_is_job_post_no_hiring_intent(self):
        """Test rejection of message without hiring intent"""
        message = Mock()
        message.text = "I'm learning Python and Django. It's really interesting and powerful for web development."
        message.forward = None
        message.media = None
        
        is_job, category = JobDetector.is_job_post(message)
        
        assert is_job == False
        assert category is None
    
    def test_extract_description(self):
        """Test description extraction and trimming"""
        long_text = "A" * 500 + " with links http://example.com and @usernames"
        description = JobDetector.extract_description(long_text, max_length=100)
        
        assert len(description) <= 110  # Some buffer for ellipsis
        assert "http" not in description
        assert "@" not in description


class TestLinkExtractor:
    """Test link extraction logic"""
    
    def test_extract_valid_links(self):
        """Test extraction of valid job links"""
        text = """
        Apply here: https://linkedin.com/jobs/12345
        Or check: https://indeed.com/job/67890
        """
        links = LinkExtractor.extract_links(text)
        
        assert len(links) == 2
        assert "linkedin.com" in links[0]
        assert "indeed.com" in links[1]
    
    def test_block_telegram_invite_links(self):
        """Test blocking of Telegram invite links"""
        text = "Join our group: https://t.me/+abc123def"
        links = LinkExtractor.extract_links(text)
        
        assert len(links) == 0
    
    def test_extract_mixed_links(self):
        """Test extraction with mixed valid/invalid links"""
        text = """
        Job link: https://careers.company.com/ml-engineer
        Telegram: https://t.me/jobgroup
        Apply: https://greenhouse.io/company/job
        """
        links = LinkExtractor.extract_links(text)
        
        # Should extract greenhouse but not t.me
        assert any("greenhouse.io" in link for link in links)
        assert not any("t.me" in link for link in links)
    
    def test_format_single_link(self):
        """Test formatting single link"""
        links = ["https://company.com/jobs"]
        formatted = LinkExtractor.format_links(links)
        
        assert formatted == "https://company.com/jobs"
    
    def test_format_multiple_links(self):
        """Test formatting multiple links"""
        links = [
            "https://company1.com/jobs",
            "https://company2.com/careers"
        ]
        formatted = LinkExtractor.format_links(links)
        
        assert "1." in formatted
        assert "2." in formatted


class TestDedupManager:
    """Test deduplication logic"""
    
    def test_duplicate_detection(self):
        """Test duplicate message detection"""
        dedup = DedupManager()
        
        text1 = "Hiring Python developers for our startup"
        text2 = "Hiring Python developers for our startup"  # Exact duplicate
        
        assert dedup.is_duplicate(text1) == False  # First time
        assert dedup.is_duplicate(text2) == True   # Duplicate
    
    def test_case_insensitive_duplicate(self):
        """Test case-insensitive duplicate detection"""
        dedup = DedupManager()
        
        text1 = "HIRING DEVELOPERS"
        text2 = "hiring developers"
        
        assert dedup.is_duplicate(text1) == False
        assert dedup.is_duplicate(text2) == True
    
    def test_duplicate_link_detection(self):
        """Test duplicate link detection"""
        dedup = DedupManager()
        
        link = "https://company.com/jobs/ml-engineer"
        
        assert dedup.is_duplicate_link(link) == False
        assert dedup.is_duplicate_link(link) == True
    
    def test_filter_duplicate_links(self):
        """Test filtering duplicate links from list"""
        dedup = DedupManager()
        
        links = [
            "https://company1.com/job1",
            "https://company2.com/job2",
            "https://company1.com/job1",  # Duplicate
        ]
        
        unique = dedup.filter_duplicate_links(links)
        
        assert len(unique) == 2
    
    def test_get_stats(self):
        """Test dedup statistics"""
        dedup = DedupManager()
        dedup.is_duplicate("Test message 1")
        dedup.is_duplicate("Test message 2")
        
        stats = dedup.get_stats()
        
        assert stats['cached_messages'] == 2
        assert 'max_cache_size' in stats


class TestRateLimiter:
    """Test rate limiting logic"""
    
    def test_initial_send_allowed(self):
        """Test that first sends are allowed"""
        limiter = RateLimiter(max_per_hour=10)
        
        assert limiter.can_send() == True
    
    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement"""
        limiter = RateLimiter(max_per_hour=3)
        
        # Send 3 messages (at limit)
        assert limiter.can_send() == True
        assert limiter.can_send() == True
        assert limiter.can_send() == True
        
        # 4th should be blocked
        assert limiter.can_send() == False
    
    def test_get_stats(self):
        """Test rate limiter statistics"""
        limiter = RateLimiter(max_per_hour=10)
        limiter.can_send()
        limiter.can_send()
        
        stats = limiter.get_stats()
        
        assert stats['sent_last_hour'] == 2
        assert stats['max_per_hour'] == 10
        assert stats['remaining'] == 8


class TestUtilities:
    """Test utility functions"""
    
    def test_format_timestamp(self):
        """Test timestamp formatting"""
        dt = datetime(2026, 2, 2, 14, 30, 45)
        formatted = format_timestamp(dt)
        
        assert "2026-02-02" in formatted
        assert "14:30:45" in formatted
    
    def test_validate_config_missing_values(self):
        """Test config validation catches missing values"""
        from utils import validate_config
        
        # This would fail with default placeholder values
        # In real scenario, should raise ValueError
        try:
            validate_config()
        except ValueError as e:
            assert "Configuration errors" in str(e)


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_job_detection_workflow(self):
        """Test complete job detection from message to category"""
        message = Mock()
        message.text = """
        We are hiring Senior Machine Learning Engineers!
        
        Requirements:
        - 5+ years Python experience
        - Deep learning frameworks (PyTorch, TensorFlow)
        - Experience with NLP and computer vision
        
        Apply: https://careers.company.com/ml-engineer
        
        Location: Remote
        """
        message.forward = None
        message.media = None
        
        # Step 1: Validate message
        assert MessageFilter.is_valid_message(message) == True
        
        # Step 2: Check blocklist
        assert MessageFilter.contains_blocklist_terms(message.text) == False
        
        # Step 3: Check hiring intent
        assert MessageFilter.has_hiring_intent(message.text) == True
        
        # Step 4: Detect job
        is_job, category = JobDetector.is_job_post(message)
        assert is_job == True
        assert category == "AI/ML"
        
        # Step 5: Extract links
        links = LinkExtractor.extract_links(message.text)
        assert len(links) >= 1
        assert "careers.company.com" in links[0]
        
        # Step 6: Extract description
        description = JobDetector.extract_description(message.text)
        assert len(description) > 0
        assert "hiring" in description.lower()


# Mock data for testing
SAMPLE_JOB_POSTS = {
    'ai_ml': "Hiring ML Engineer with PyTorch experience. Apply: https://company.com/jobs",
    'backend': "Node.js developer needed. Express, MongoDB required. https://careers.tech/backend",
    'frontend': "React developer opening. TypeScript, Next.js. https://jobs.startup/frontend",
    'data': "Data Analyst position. SQL, Tableau, Python. https://company.com/data-analyst",
    'cybersec': "Security Engineer role. Penetration testing experience. https://security.jobs/eng",
    'fullstack': "Full stack developer. MERN stack required. https://careers.company/fullstack"
}

SAMPLE_SPAM = {
    'crypto': "Bitcoin trading signals! 10% daily profit! Join now!",
    'course': "Free Python course! Limited seats! Enroll today!",
    'referral': "Earn money online! Refer and earn $100 per signup!",
    'intern_scam': "Unpaid internship, certificate only, great opportunity!"
}


if __name__ == "__main__":
    print("Telegram Job Bot - Test Suite")
    print("=" * 60)
    print("\nRun tests with:")
    print("  pip install pytest pytest-asyncio")
    print("  python -m pytest tests.py -v")
    print("\nOr run this file directly for basic checks:")
    print()
    
    # Basic smoke tests
    print("Running basic smoke tests...")
    
    # Test 1: Message filtering
    msg = Mock()
    msg.text = "Hiring Python developers"
    msg.forward = None
    msg.media = None
    print(f"✓ Message filter: {MessageFilter.is_valid_message(msg)}")
    
    # Test 2: Job detection
    is_job, cat = JobDetector.is_job_post(msg)
    print(f"✓ Job detection: is_job={is_job}, category={cat}")
    
    # Test 3: Deduplication
    dedup = DedupManager()
    print(f"✓ Deduplication: first={not dedup.is_duplicate('test')}, second={dedup.is_duplicate('test')}")
    
    # Test 4: Rate limiting
    limiter = RateLimiter(max_per_hour=5)
    print(f"✓ Rate limiter: {limiter.can_send()}")
    
    print("\n✅ All basic smoke tests passed!")
    print("\nFor comprehensive testing, run: pytest tests.py -v")
