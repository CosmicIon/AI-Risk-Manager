import re
import logging

logger = logging.getLogger(__name__)

def sanitize_input(text: str) -> str:
    """
    Sanitizes user input for defense against prompt injections and control character exploits.
    
    1. Strips non-printable control characters.
    2. Removes common prompt injection patterns (e.g. 'ignore previous instructions').
    3. Truncates inputs exceeding 10,000 characters to prevent denial of service via token exhaustion.
    """
    if not text:
        return text
        
    original_len = len(text)
    
    # 1. Truncate to 10,000 chars
    text = text[:10000]
    
    # 2. Strip non-printable control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 3. Detect and escape prompt injection keywords
    injection_patterns = [
        r"(?i)\bignore previous instructions\b",
        r"(?i)\bsystem:\b",
        r"(?i)\bassistant:\b",
        r"(?i)\bdisregard all prior\b"
    ]
    
    sanitized = False
    for pattern in injection_patterns:
        if re.search(pattern, text):
            sanitized = True
            text = re.sub(pattern, "[REDACTED]", text)
            
    if sanitized or original_len > 10000:
        logger.warning(
            f"Input sanitized. Truncated from {original_len} to {len(text)}. "
            f"Prompt injection patterns redacted: {sanitized}"
        )
        
    return text
