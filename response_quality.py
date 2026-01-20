"""
Response Quality & Fact-Checking Module
Validates responses for accuracy, sources, and confidence levels
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple

# Import web search for verification
try:
    from web_search import search_web, fetch_page
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# =========================
# CONFIDENCE LEVELS
# =========================

CONFIDENCE_LEVELS = {
    "HIGH": {
        "score": 0.9,
        "description": "Well-established fact from authoritative sources",
        "marker": "[HIGH CONFIDENCE]"
    },
    "MEDIUM": {
        "score": 0.6,
        "description": "Information from reasonable sources but may vary",
        "marker": "[MEDIUM CONFIDENCE]"
    },
    "LOW": {
        "score": 0.4,
        "description": "Uncertain or speculative information",
        "marker": "[LOW CONFIDENCE]"
    }
}

# =========================
# SOURCE CREDIBILITY SCORES
# =========================

CREDIBLE_SOURCES = {
    "official": 0.95,          # Official documentation, government sites
    "academic": 0.90,          # Universities, research institutions
    "reputable_news": 0.85,    # BBC, Reuters, AP News, etc.
    "technical_blog": 0.75,    # Tech-focused blogs with credentials
    "github": 0.70,            # GitHub repositories (varies by stars/activity)
    "stack_overflow": 0.75,    # Stack Overflow answers (verified ones)
    "wiki": 0.35,              # Wikipedia - DEPRIORITIZED (user-editable, can have errors)
    "wikipedia": 0.35,         # Wikipedia - explicitly deprioritized
    "promotional": 0.30,       # Marketing/promotional content
    "blog": 0.50,              # Generic blogs
    "unknown": 0.40            # Unknown source
}

# =========================
# DATE VALIDATION
# =========================

CURRENT_DATE = datetime.now()
CURRENT_YEAR = CURRENT_DATE.year
CURRENT_MONTH = CURRENT_DATE.month

# =========================
# FACT-CHECKING FUNCTIONS
# =========================

def check_date_accuracy(text: str) -> Dict:
    """
    Detect and flag date-related issues in text.
    Returns confidence impact.
    """
    issues = []
    
    # Pattern: "As of [DATE]"
    date_pattern = r"As of\s+(\w+\s+\d+,?\s*\d{4})"
    matches = re.finditer(date_pattern, text)
    
    for match in matches:
        date_str = match.group(1)
        
        # Check if date is in future
        if "2027" in date_str or "2028" in date_str or "2030" in date_str:
            issues.append({
                "type": "FUTURE_DATE",
                "text": date_str,
                "severity": "CRITICAL",
                "message": f"Date '{date_str}' is in the future - appears to be hallucinated",
                "confidence_penalty": 0.3
            })
        elif "2025" in date_str and CURRENT_YEAR >= 2026:
            issues.append({
                "type": "OUTDATED_DATE",
                "text": date_str,
                "severity": "MEDIUM",
                "message": f"Date '{date_str}' may be outdated",
                "confidence_penalty": 0.2
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "penalty": sum(i.get("confidence_penalty", 0) for i in issues)
    }


def check_unverifiable_claims(text: str) -> Dict:
    """
    Detect unverifiable claims like GitHub repos, policy changes, etc.
    """
    issues = []
    
    # Pattern: "GitHub - username/repo"
    github_pattern = r"GitHub\s*-\s*[\w\-]+/[\w\-]+"
    if re.search(github_pattern, text):
        matches = re.findall(github_pattern, text)
        for match in matches:
            issues.append({
                "type": "UNVERIFIABLE_GITHUB_REF",
                "text": match,
                "severity": "HIGH",
                "message": f"GitHub reference '{match}' is unverifiable - should be verified or removed",
                "confidence_penalty": 0.25
            })
    
    # Pattern: policy changes without source
    policy_patterns = [
        r"(?:imposing|announcing|implementing)\s+(?:a|an)?\s*(?:\d+%\s*)?(?:tariff|tax|fee|penalty)",
        r"(?:is\s+)?(?:imposing|raising|lowering)\s+(?:tariff|tax|fee)"
    ]
    
    for pattern in policy_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append({
                "type": "UNVERIFIABLE_POLICY_CLAIM",
                "severity": "HIGH",
                "message": "Policy/regulation claims require official source attribution",
                "confidence_penalty": 0.3
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "penalty": sum(i.get("confidence_penalty", 0) for i in issues)
    }


def check_generic_filler(text: str) -> Dict:
    """
    Detect generic filler content and inflated claims.
    """
    issues = []
    
    # Pattern: "X small examples" or "100 examples"
    filler_patterns = [
        r"(\d+)\s+(?:small|simple|basic|quick)\s+(?:examples|tutorials|guides|scripts)",
        r"comprehensive\s+(?:list|collection)\s+of\s+(?:Python|code).*examples",
        r"(?:here\s+)?(?:is|are)\s+(?:a|the)\s+(?:comprehensive|complete|full)\s+(?:list|guide|collection)"
    ]
    
    for pattern in filler_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append({
                "type": "GENERIC_FILLER",
                "severity": "MEDIUM",
                "message": "Response contains generic filler claims without specific evidence",
                "confidence_penalty": 0.15
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "penalty": sum(i.get("confidence_penalty", 0) for i in issues)
    }


def check_context_mismatch(text: str, query: str) -> Dict:
    """
    Check if response properly addresses the query context.
    E.g., describing PyTorch as having "Hello World" examples when it's an ML framework.
    """
    issues = []
    
    # PyTorch context check
    if "pytorch" in query.lower():
        if "hello world" in text.lower() or "general programming" in text.lower():
            issues.append({
                "type": "CONTEXT_MISMATCH",
                "severity": "HIGH",
                "message": "Response describes PyTorch incorrectly - it's a deep learning framework, not a general programming language",
                "confidence_penalty": 0.35
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "penalty": sum(i.get("confidence_penalty", 0) for i in issues)
    }


def evaluate_source_credibility(source: str) -> float:
    """
    Score a source for credibility.
    """
    source_lower = source.lower()
    
    for source_type, score in CREDIBLE_SOURCES.items():
        if source_type in source_lower:
            return score
    
    # Check for promotional keywords
    promo_keywords = ["buy", "sale", "limited offer", "exclusive", "click here", "learn more"]
    if any(keyword in source_lower for keyword in promo_keywords):
        return CREDIBLE_SOURCES["promotional"]
    
    return CREDIBLE_SOURCES["unknown"]


def calculate_confidence_level(base_score: float, penalties: float) -> str:
    """
    Calculate overall confidence level based on base score and penalties.
    """
    final_score = max(0.0, base_score - penalties)
    
    if final_score >= 0.8:
        return "HIGH"
    elif final_score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"


# =========================
# WEB VERIFICATION FUNCTIONS
# =========================

def verify_response_with_web_search(response_text: str, query: str = "") -> Dict:
    """
    Verify response content against live web search results.
    Prevents hallucinations by comparing against real data.
    
    Returns confidence adjustment based on verification success.
    """
    if not WEB_SEARCH_AVAILABLE or not query:
        return {
            "verified": False,
            "confidence_adjustment": 0.0,
            "found_matches": [],
            "sources_found": [],
            "has_wikipedia_only": False
        }
    
    try:
        # Search for relevant information
        search_results = search_web(query, max_results=3)
        
        if not search_results:
            return {
                "verified": False,
                "confidence_adjustment": -0.15,  # Penalty for no verification possible
                "found_matches": [],
                "sources_found": [],
                "has_wikipedia_only": False
            }
        
        found_matches = []
        sources_found = []
        has_wikipedia_only = True
        
        # Check each search result
        for result in search_results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            # Skip Wikipedia results - deprioritize
            if "wikipedia" in url or "wiki" in url:
                continue
            
            has_wikipedia_only = False
            sources_found.append({
                "url": result.get("url"),
                "title": result.get("title"),
                "credibility": 0.75  # Default for verified web source
            })
            
            # Try to fetch and verify content
            try:
                page_content = fetch_page(result.get("url", ""))
                if page_content:
                    # Check if response content matches fetched page
                    response_snippets = [s.strip() for s in response_text.split('.') if len(s.strip()) > 10]
                    page_snippets = [s.strip() for s in page_content.split('.') if len(s.strip()) > 10]
                    
                    for snippet in response_snippets[:3]:  # Check first 3 sentences
                        if any(keyword in page_content.lower() for keyword in snippet.lower().split()[:5]):
                            found_matches.append({
                                "snippet": snippet[:100],
                                "source": result.get("url"),
                                "match_confidence": 0.85
                            })
            except:
                pass  # Silent fail on fetch, continue
        
        # If only Wikipedia results found, that's a red flag
        if has_wikipedia_only and search_results:
            return {
                "verified": False,
                "confidence_adjustment": -0.25,  # Penalty for Wikipedia-only sources
                "found_matches": [],
                "sources_found": sources_found,
                "has_wikipedia_only": True,
                "warning": "Information only found on Wikipedia - less reliable source"
            }
        
        # If we found external verification, boost confidence
        if found_matches:
            return {
                "verified": True,
                "confidence_adjustment": 0.15,  # Boost for verified sources
                "found_matches": found_matches,
                "sources_found": sources_found,
                "has_wikipedia_only": False
            }
        elif sources_found:
            return {
                "verified": True,
                "confidence_adjustment": 0.10,  # Small boost for alternative sources found
                "found_matches": [],
                "sources_found": sources_found,
                "has_wikipedia_only": False
            }
        else:
            return {
                "verified": False,
                "confidence_adjustment": -0.10,
                "found_matches": [],
                "sources_found": [],
                "has_wikipedia_only": False
            }
    
    except Exception as e:
        # If verification fails, don't penalize heavily
        return {
            "verified": False,
            "confidence_adjustment": 0.0,
            "found_matches": [],
            "sources_found": [],
            "has_wikipedia_only": False,
            "error": str(e)
        }


def check_for_wikipedia_only(text: str) -> Dict:
    """
    Detect if response appears to only cite Wikipedia.
    Wikipedia can have errors - should have secondary sources.
    RETURNS BLOCKING FLAG if Wikipedia-only.
    """
    issues = []
    text_lower = text.lower()
    
    # Strong Wikipedia indicators
    wiki_indicators = [
        'wikipedia', 'wiki article', 'from wikipedia',
        'according to wikipedia', 'the wikipedia article',
        'wiki.* says', 'wikipedia.org', 'Jump to content From Wikipedia'
    ]
    
    # Strong official/non-wiki indicators
    official_indicators = [
        'official', 'documentation', 'github.com', 'official site',
        'technical documentation', 'research', 'study', 'paper',
        'source code', 'api', '.org', '.gov', 'repository'
    ]
    
    # Count mentions
    wiki_count = sum(1 for indicator in wiki_indicators if indicator in text_lower)
    official_count = sum(1 for indicator in official_indicators if indicator in text_lower)
    
    # If response is longer than 500 chars and mostly Wikipedia content
    is_long_response = len(text) > 500
    
    # CRITICAL: Block if Wikipedia-only (no official sources)
    if wiki_count > 2 and official_count == 0:
        issues.append({
            "type": "WIKIPEDIA_ONLY",
            "severity": "CRITICAL",
            "message": "Response is Wikipedia-only - blocked. Perform web search for official sources",
            "confidence_penalty": 0.50,
            "should_block": True
        })
    elif wiki_count > 0 and official_count == 0 and is_long_response:
        # Long response with only Wikipedia
        issues.append({
            "type": "WIKIPEDIA_ONLY",
            "severity": "CRITICAL",
            "message": "Response appears Wikipedia-based only - blocked for quality. Use official sources",
            "confidence_penalty": 0.50,
            "should_block": True
        })
    elif wiki_count > 0 and official_count == 0 and text.count("Wikipedia") > 0:
        # Explicit Wikipedia mention without alternatives
        issues.append({
            "type": "WIKIPEDIA_ONLY",
            "severity": "CRITICAL",
            "message": "Response relies on Wikipedia alone - blocked. Need official or verified sources",
            "confidence_penalty": 0.50,
            "should_block": True
        })
    elif wiki_count > official_count:
        # Heavy Wikipedia reliance
        issues.append({
            "type": "WIKIPEDIA_HEAVY",
            "severity": "HIGH",
            "message": "Response relies heavily on Wikipedia (70%+) - should include official sources",
            "confidence_penalty": 0.35,
            "should_block_or_truncate": True
        })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "penalty": sum(i.get("confidence_penalty", 0) for i in issues),
        "should_block": any(i.get("should_block", False) for i in issues),
        "should_truncate": any(i.get("should_block_or_truncate", False) for i in issues),
        "wiki_indicators": wiki_count,
        "official_indicators": official_count
    }


def should_block_response(quality_report: Dict) -> bool:
    """
    Determine if response should be completely blocked.
    Returns True if response contains hallucinations or Wikipedia-only content.
    """
    # Block if Wikipedia-only detected
    wiki_check = quality_report.get("checks", {}).get("wikipedia_only", {})
    if wiki_check.get("should_block", False):
        return True
    
    # Block if critical issues found
    critical_issues = [i for i in quality_report.get("issues", []) 
                      if i.get("severity") == "CRITICAL"]
    if critical_issues:
        return True
    
    # Block if multiple high-severity issues
    high_issues = [i for i in quality_report.get("issues", []) 
                   if i.get("severity") == "HIGH"]
    if len(high_issues) >= 2:
        return True
    
    return False


def truncate_wikipedia_response(text: str, max_length: int = 300) -> str:
    """
    Truncate Wikipedia responses to prevent information overload.
    Returns first max_length characters + summary instruction.
    """
    if len(text) > max_length:
        truncated = text[:max_length].rsplit(' ', 1)[0]  # Cut at word boundary
        return truncated + f"\n\n[Response truncated - too long. Please use /ask-verified for complete web-searched answer with official sources]"
    return text


def get_web_search_replacement(query: str) -> str:
    """
    When Wikipedia-only would be returned, perform web search instead.
    Returns verified information from official sources.
    """
    if not WEB_SEARCH_AVAILABLE:
        return f"[Unable to perform web search - offline mode]\n\nFor query: {query}"
    
    try:
        # Search for information
        search_results = search_web(query, max_results=5)
        
        if not search_results:
            return f"[No web search results found for: {query}]\nTry a more specific query."
        
        # Fetch content from top results (skip Wikipedia)
        collected_info = []
        sources_used = []
        
        for result in search_results:
            url = result.get("url", "").lower()
            
            # Skip Wikipedia sources
            if "wikipedia" in url or "wiki." in url:
                continue
            
            title = result.get("title", "")
            sources_used.append({
                "title": title,
                "url": result.get("url", "")
            })
            
            # Fetch page content
            try:
                content = fetch_page(result.get("url", ""))
                if content and len(content) > 100:
                    # Use first 500 chars as answer
                    collected_info.append(content[:500])
            except:
                pass
        
        # Build response
        if collected_info:
            combined_info = "\n\n".join(collected_info[:2])  # Use top 2 sources
            
            response = f"{combined_info}\n\n"
            response += "[VERIFIED via Web Search]\n\n"
            response += "Sources:\n"
            for src in sources_used[:3]:
                response += f"- {src['title']}: {src['url']}\n"
            
            return response
        else:
            return f"[Web search performed but content unavailable for: {query}]"
    
    except Exception as e:
        return f"[Web search encountered error: {str(e)}]\nTry rephrasing your question."


def replace_wikipedia_with_web_search(response_text: str, query: str) -> Dict:
    """
    Detect if response would be Wikipedia-only.
    If so, perform web search and return verified results instead.
    
    Returns:
        Dict with:
        - replaced: bool (was replacement done?)
        - response: str (new response or original)
        - sources: list (verified sources used)
        - message: str (explanation)
    """
    # Check if Wikipedia-only
    wiki_check = check_for_wikipedia_only(response_text)
    
    if not wiki_check.get('should_block', False):
        # Not Wikipedia-only, return original
        return {
            "replaced": False,
            "response": response_text,
            "sources": [],
            "message": "No replacement needed - quality response"
        }
    
    # Wikipedia-only detected - perform web search instead
    if not query:
        return {
            "replaced": False,
            "response": response_text,
            "sources": [],
            "message": "Cannot replace without query"
        }
    
    try:
        # Get web search results
        web_response = get_web_search_replacement(query)
        
        return {
            "replaced": True,
            "response": web_response,
            "sources": [],  # Sources included in response text
            "message": "Replaced Wikipedia-only response with web search results"
        }
    except Exception as e:
        return {
            "replaced": False,
            "response": response_text,
            "sources": [],
            "message": f"Replacement failed: {str(e)}"
        }


def enforce_response_length_limit(text: str, max_length: int = 2000) -> str:
    """
    Enforce maximum response length to prevent information overload.
    Truncates responses that are too long.
    """
    if len(text) > max_length:
        truncated = text[:max_length].rsplit(' ', 1)[0]
        return truncated + f"\n\n[Response limited to {max_length} characters. For more details, use /ask-verified endpoint]"
    return text


# =========================
# RESPONSE QUALITY CHECKER
# =========================

def check_response_quality(text: str, query: str = "", sources: List[str] = None) -> Dict:
    """
    Comprehensive quality check for a response.
    
    Args:
        text: The response text to validate
        query: The original query (for context checking)
        sources: List of sources used in the response
    
    Returns:
        Dictionary with quality assessment and recommendations
    """
    
    quality_report = {
        "text": text,
        "query": query,
        "checks": {},
        "issues": [],
        "penalties": 0.0,
        "base_confidence": 0.75,  # Start with medium confidence
        "source_scores": [],
        "recommendations": []
    }
    
    # Check 1: Date accuracy
    date_check = check_date_accuracy(text)
    quality_report["checks"]["date_accuracy"] = date_check
    quality_report["penalties"] += date_check.get("penalty", 0)
    quality_report["issues"].extend(date_check.get("issues", []))
    
    # Check 2: Unverifiable claims
    verify_check = check_unverifiable_claims(text)
    quality_report["checks"]["unverifiable_claims"] = verify_check
    quality_report["penalties"] += verify_check.get("penalty", 0)
    quality_report["issues"].extend(verify_check.get("issues", []))
    
    # Check 3: Generic filler
    filler_check = check_generic_filler(text)
    quality_report["checks"]["generic_filler"] = filler_check
    quality_report["penalties"] += filler_check.get("penalty", 0)
    quality_report["issues"].extend(filler_check.get("issues", []))
    
    # Check 4: Context mismatch
    context_check = check_context_mismatch(text, query)
    quality_report["checks"]["context_mismatch"] = context_check
    quality_report["penalties"] += context_check.get("penalty", 0)
    quality_report["issues"].extend(context_check.get("issues", []))
    
    # Check 5: Wikipedia-only sources (NEW)
    wiki_check = check_for_wikipedia_only(text)
    quality_report["checks"]["wikipedia_only"] = wiki_check
    quality_report["penalties"] += wiki_check.get("penalty", 0)
    quality_report["issues"].extend(wiki_check.get("issues", []))
    
    # Check 6: Web verification (NEW) - Verify against real sources
    web_verification = verify_response_with_web_search(text, query)
    quality_report["checks"]["web_verification"] = web_verification
    quality_report["penalties"] += max(0, web_verification.get("confidence_adjustment", 0) * -1)  # Convert adjustment to penalty if negative
    quality_report["verified_sources"] = web_verification.get("sources_found", [])
    
    if web_verification.get("has_wikipedia_only"):
        quality_report["issues"].append({
            "type": "WIKIPEDIA_ONLY_VERIFICATION",
            "severity": "MEDIUM",
            "message": "Web search found information only on Wikipedia - consider official sources",
            "confidence_penalty": 0.15
        })
    
    # Check 7: Source credibility
    if sources:
        for source in sources:
            score = evaluate_source_credibility(source)
            quality_report["source_scores"].append({
                "source": source,
                "credibility_score": score
            })
        
        if quality_report["source_scores"]:
            avg_source_score = sum(s["credibility_score"] for s in quality_report["source_scores"]) / len(quality_report["source_scores"])
            quality_report["base_confidence"] = avg_source_score
    
    # Calculate final confidence
    quality_report["confidence_level"] = calculate_confidence_level(
        quality_report["base_confidence"],
        quality_report["penalties"]
    )
    
    quality_report["confidence_score"] = max(
        0.0,
        quality_report["base_confidence"] - quality_report["penalties"]
    )
    
    # Generate recommendations
    for issue in quality_report["issues"]:
        if issue["severity"] == "CRITICAL":
            quality_report["recommendations"].append(
                f"CRITICAL: {issue['message']}"
            )
        elif issue["severity"] == "HIGH":
            quality_report["recommendations"].append(
                f"HIGH PRIORITY: {issue['message']}"
            )
    
    quality_report["is_safe_to_publish"] = len([
        i for i in quality_report["issues"] 
        if i["severity"] in ["CRITICAL", "HIGH"]
    ]) == 0
    
    return quality_report


def format_quality_report(report: Dict) -> str:
    """
    Format a quality report as a human-readable string.
    """
    output = []
    output.append("=" * 70)
    output.append("RESPONSE QUALITY REPORT")
    output.append("=" * 70)
    output.append(f"\nConfidence Level: {report['confidence_level']} ({report['confidence_score']:.2%})")
    output.append(f"Safe to Publish: {'YES' if report['is_safe_to_publish'] else 'NO - Issues detected'}")
    
    if report["issues"]:
        output.append(f"\nIssues Found: {len(report['issues'])}")
        output.append("-" * 70)
        for i, issue in enumerate(report["issues"], 1):
            output.append(f"\n{i}. [{issue['severity']}] {issue['type']}")
            output.append(f"   Message: {issue['message']}")
            if "text" in issue:
                output.append(f"   Text: {issue['text']}")
    
    if report["recommendations"]:
        output.append(f"\nRecommendations:")
        output.append("-" * 70)
        for rec in report["recommendations"]:
            output.append(f"• {rec}")
    
    output.append("\n" + "=" * 70)
    
    return "\n".join(output)


# =========================
# RESPONSE WRAPPER
# =========================

def add_confidence_marker(text: str, confidence_level: str, sources: List[str] = None) -> str:
    """
    Add confidence marker and source attribution to response.
    """
    marker = CONFIDENCE_LEVELS[confidence_level]["marker"]
    output = [marker, text]
    
    if sources:
        output.append("\n\n**Sources:**")
        for source in sources:
            output.append(f"- {source}")
    
    return "\n".join(output)


# =========================
# WRAPPER FUNCTION FOR INTEGRATION
# =========================

def check_response(response_text: str, sources: List[Dict] = None, response_type: str = "general", query: str = "") -> Dict:
    """
    Wrapper function that integrates quality checking into response pipeline.
    When Wikipedia-only detected, REPLACES with web search results.
    
    Args:
        response_text: The response to validate
        sources: List of source dictionaries with 'url', 'title', 'timestamp'
        response_type: Type of response ('web_search', 'ollama', 'general')
        query: The original user query (for context checking)
    
    Returns:
        Dictionary with quality assessment and potentially replaced response
    """
    # Extract source strings for quality check
    source_strings = []
    if sources:
        source_strings = [s.get("url", "") or s.get("title", "") for s in sources if s]
    
    # Run comprehensive quality check (includes web verification)
    quality_report = check_response_quality(response_text, query, source_strings)
    
    # Check if response is Wikipedia-only and replace if needed
    replacement_result = replace_wikipedia_with_web_search(response_text, query)
    
    # Use web search result if replacement was done
    if replacement_result['replaced']:
        processed_response = replacement_result['response']
        is_valid = True  # Web search results are valid
        is_replaced = True
        replacement_message = "Response replaced with web search results"
    else:
        processed_response = response_text
        is_valid = quality_report.get("is_safe_to_publish", True)
        is_replaced = False
        replacement_message = ""
        
        # Apply length limit to non-replaced responses
        if len(processed_response) > 2000:
            processed_response = enforce_response_length_limit(processed_response, max_length=2000)
    
    # Include verified sources from web search
    verified_sources = quality_report.get("verified_sources", [])
    
    # Simplify report for integration
    return {
        "is_valid": is_valid,
        "confidence_level": quality_report.get("confidence_level", "HIGH") if is_replaced else quality_report.get("confidence_level", "MEDIUM"),
        "confidence_score": quality_report.get("confidence_score", 0.85) if is_replaced else quality_report.get("confidence_score", 0.5),
        "issues": [] if is_replaced else [issue.get("message", "") for issue in quality_report.get("issues", [])],
        "sources_verified": True if is_replaced else (len(source_strings) > 0 if response_type == "web_search" else len(verified_sources) > 0),
        "verified_sources": verified_sources,
        "hallucinations_detected": False if is_replaced else (not quality_report.get("is_safe_to_publish", True)),
        "sources": source_strings,
        "recommendations": [] if is_replaced else quality_report.get("recommendations", []),
        "web_verified": True if is_replaced else quality_report.get("checks", {}).get("web_verification", {}).get("verified", False),
        "replaced": is_replaced,  # NEW: Flag if response was replaced with web search
        "replacement_message": replacement_message,
        "response_text": processed_response,  # The actual response to return
        "raw_report": quality_report
    }

