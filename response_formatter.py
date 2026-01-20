"""Format responses based on user preferences"""
import re
from response_quality import (
    check_response_quality,
    CONFIDENCE_LEVELS,
    add_confidence_marker
)


def format_response(text, preferences=None, confidence_level=None, sources=None):
    """
    Format response based on user preferences with quality markers.
    
    Args:
        text: Raw response text from AI
        preferences: Dict with keys:
            - response_format: "formatted" or "plain" (default: "formatted")
            - use_lists: bool (default: True)
            - use_numbered: bool (default: True)
            - use_bullets: bool (default: True)
            - use_emojis: bool (default: True)
            - preferred_tone: "professional", "casual", "technical" (default: "professional")
            - include_confidence: bool (default: True)
        confidence_level: str - "HIGH", "MEDIUM", or "LOW"
        sources: List[str] - sources used in response
    
    Returns:
        Formatted text with quality markers
    """
    if not preferences:
        preferences = {}
    
    response_format = preferences.get("response_format", "formatted")
    include_confidence = preferences.get("include_confidence", True)
    
    # If user wants plain format, return as-is (but still include confidence if requested)
    if response_format == "plain":
        if include_confidence and confidence_level:
            return add_confidence_marker(text, confidence_level, sources)
        return text
    
    # Otherwise apply formatting
    use_lists = preferences.get("use_lists", True)
    use_numbered = preferences.get("use_numbered", True)
    use_bullets = preferences.get("use_bullets", True)
    use_emojis = preferences.get("use_emojis", True)
    
    formatted = text
    
    # Step 1: Structure paragraphs into clearer sections
    if use_lists:
        formatted = _structure_into_lists(formatted, use_numbered, use_bullets)
    
    # Step 2: Add visual separators for better readability
    formatted = _add_visual_separators(formatted)
    
    # Step 3: Emphasize key points
    formatted = _emphasize_key_points(formatted)
    
    # Step 4: Add emojis if requested
    if use_emojis:
        formatted = _add_relevant_emojis(formatted)
    
    # Step 5: Add confidence markers and sources
    if include_confidence and confidence_level:
        formatted = add_confidence_marker(formatted, confidence_level, sources)
    
    return formatted


def _structure_into_lists(text, use_numbered=True, use_bullets=True):
    """
    Convert dense paragraphs into lists where appropriate.
    Intelligently breaks up long text into digestible chunks.
    """
    lines = text.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines but preserve spacing
        if not stripped:
            result.append("")
            continue
        
        # Check if line is already formatted as a list item
        if re.match(r'^[\d]+[\.\)]\s+', stripped) or re.match(r'^[-•]\s+', stripped):
            result.append(line)
            continue
        
        # Break up long sentences into logical chunks
        if len(stripped) > 120 and any(word in stripped.lower() for word in [',', 'and', 'also', 'additionally']):
            # Split by common conjunctions
            parts = re.split(r',\s+|(?<=\w)\s+(?:and|also|additionally|furthermore|moreover)\s+', stripped)
            if len(parts) > 1:
                # Format as bullet points
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        if use_bullets:
                            result.append(f"• {part}")
                        elif use_numbered:
                            result.append(f"{i+1}. {part}")
                        else:
                            result.append(f"- {part}")
                continue
        
        # Otherwise keep the line as-is
        result.append(line)
    
    return '\n'.join(result)


def _format_list(items, use_numbered=True, use_bullets=True):
    """Format list items with appropriate prefix"""
    if not items:
        return []
    
    formatted = []
    for i, item in enumerate(items, 1):
        if use_numbered and i == 1:  # First item can be numbered
            formatted.append(f"1. {item}")
        elif use_numbered and len(items) > 1:
            formatted.append(f"{i}. {item}")
        elif use_bullets:
            formatted.append(f"• {item}")
        else:
            formatted.append(f"- {item}")
    
    return formatted


def _add_visual_separators(text):
    """Add headers and line breaks for better readability"""
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        result.append(line)
        
        # Add separator after potential headers/section titles
        if stripped and len(stripped) < 60 and stripped[0].isupper():
            # Check if it looks like a header
            if i + 1 < len(lines) and lines[i + 1].strip():
                # Add blank line for spacing
                result.append("")
        
        # Break up very long paragraphs with line breaks
        if len(stripped) > 150 and '.' in stripped:
            # Check if next line exists and isn't already separated
            if i + 1 < len(lines) and lines[i + 1].strip():
                # Insert line break for readability
                result.append("")
    
    return '\n'.join(result)


def _emphasize_key_points(text):
    """Make key points stand out with emphasis markers"""
    # Emphasize common important words
    important_patterns = [
        (r'\b(important|critical|must|required|note|remember|key)\b', r'**\1**'),
        (r'\b(warning|caution|attention)\b', r'⚠️ \1'),
        (r'\b(success|completed|done|finished)\b', r'✅ \1'),
    ]
    
    result = text
    for pattern, replacement in important_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def _add_relevant_emojis(text):
    """Add relevant emojis to enhance readability"""
    emoji_map = {
        r'step[\s\d]+': '📍',
        r'example': '💡',
        r'note': '📝',
        r'code': '💻',
        r'question': '❓',
        r'answer': '✅',
        r'error': '❌',
        r'warning': '⚠️',
        r'tip': '💡',
        r'important': '⭐',
        r'summary': '📊',
        r'list': '📋',
        r'check': '✓',
        r'number': '🔢',
    }
    
    result = text
    
    for pattern, emoji in emoji_map.items():
        # Only add emoji if not already present in line
        lines = result.split('\n')
        new_lines = []
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                if emoji not in line:  # Don't add duplicate emojis
                    line = emoji + ' ' + line
            new_lines.append(line)
        result = '\n'.join(new_lines)
    
    return result


def apply_tone(text, tone="professional"):
    """Apply tone adjustments to text"""
    if tone == "casual":
        # Make it more conversational
        text = text.replace("please", "hey")
        text = text.replace("Unfortunately,", "Sadly,")
    elif tone == "technical":
        # Make it more precise
        text = text.replace("basically", "technically")
        text = text.replace("really", "fundamentally")
    
    return text


# Example usage for testing
if __name__ == "__main__":
    sample = """
    There are several important steps to follow. First, you need to set up your environment. 
    Second, install the dependencies. Third, configure your settings. Note that this is critical.
    
    You should also remember to check the documentation. It's important to follow the guidelines.
    
    For example, if you encounter an error, check the logs. Make sure to read the error message carefully.
    """
    
    prefs = {
        "response_format": "formatted",
        "use_lists": True,
        "use_numbered": True,
        "use_bullets": True,
        "use_emojis": True,
        "preferred_tone": "professional"
    }
    
    print("BEFORE:")
    print(sample)
    print("\n" + "="*50 + "\n")
    print("AFTER:")
    print(format_response(sample, prefs))
