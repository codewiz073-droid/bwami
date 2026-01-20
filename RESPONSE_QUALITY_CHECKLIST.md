# RESPONSE QUALITY CHECKLIST
**Version**: 1.0  
**Date**: January 20, 2026  
**Purpose**: Ensure all responses meet quality and accuracy standards

---

## PRE-RESPONSE GENERATION CHECKLIST

### 1. Query Understanding
- [ ] Query is clearly understood
- [ ] User intent is identified
- [ ] Question is within system capabilities
- [ ] Context is relevant and current

### 2. Source Selection
- [ ] Sources are authoritative (official docs, academic, reputable news)
- [ ] Sources are not primarily promotional
- [ ] Multiple perspectives considered when appropriate
- [ ] Source URLs are verified and active

---

## RESPONSE GENERATION CHECKLIST

### 3. Content Accuracy
- [ ] Main claim directly answers the query
- [ ] Examples are concrete and verifiable
- [ ] No generic filler content ("100 examples", "comprehensive list" without specifics)
- [ ] Technical descriptions match the actual technology/concept

### 4. Date & Recency
- [ ] No future dates presented as current fact
- [ ] Dates are checked against current date (January 20, 2026)
- [ ] Outdated information is flagged with "As of [DATE]"
- [ ] Temporal language is accurate ("currently", "recently", "historically")

### 5. Fact-Checking
- [ ] Critical facts verified against multiple sources
- [ ] Policy/regulation claims attributed to official sources
- [ ] GitHub/repository references are verified (or marked as examples only)
- [ ] No unverifiable claims presented as fact

### 6. Source Credibility
- [ ] Primary sources cited when available
- [ ] Promotional content excluded or clearly marked
- [ ] Blog posts credited with author context (e.g., "according to [expert]'s blog")
- [ ] Wikipedia used only as overview, not primary source

### 7. Fact vs. Opinion Distinction
- [ ] Facts presented as facts with evidence
- [ ] Opinions labeled as opinions ("In my analysis...", "Some argue that...")
- [ ] Speculation marked as such ("Likely...", "Possibly...", "It's unclear whether...")
- [ ] Personal anecdotes distinguished from general information

---

## RESPONSE STRUCTURE CHECKLIST

### 8. Organization & Flow
- [ ] Direct answer appears first
- [ ] Information flows logically
- [ ] No arbitrary numbered lists (lists serve a purpose)
- [ ] Headings are descriptive and relevant

### 9. Clarity & Conciseness
- [ ] Language is clear and accessible
- [ ] No unnecessary jargon without explanation
- [ ] Sentences are direct and not overly complex
- [ ] Length is appropriate for topic (concise but complete)

### 10. Formatting Consistency
- [ ] Headings follow hierarchy (# ## ### not random)
- [ ] Lists use consistent bullet points or numbering
- [ ] Code examples are clearly marked
- [ ] Emphasis (bold, italics) used sparingly and meaningfully

---

## CONFIDENCE & TRANSPARENCY CHECKLIST

### 11. Confidence Signaling
- [ ] Response includes confidence level marker
  - [HIGH CONFIDENCE] for well-established facts
  - [MEDIUM CONFIDENCE] for reasonable information with variation
  - [LOW CONFIDENCE] for uncertain/speculative information

### 12. Source Attribution
- [ ] Sources listed at end of response
- [ ] Source credibility indicated (official, academic, blog, etc.)
- [ ] URLs provided when helpful
- [ ] Attribution format consistent

### 13. Uncertainty Acknowledgment
- [ ] Unknown information flagged as such
- [ ] Speculative claims labeled clearly
- [ ] Conflicting information acknowledged
- [ ] Knowledge limitations acknowledged

---

## CONTEXT-SPECIFIC CHECKLIST

### 14. Technology/Framework Accuracy
For technical topics:
- [ ] Framework/tool correctly described
  - ✗ PyTorch is NOT a general programming language
  - ✗ Don't describe ML frameworks with "Hello World" examples as primary feature
- [ ] Use cases are appropriate
- [ ] Version-specific information is noted
- [ ] Contradictions with user query are resolved

### 15. Policy/Regulation Claims
For policy information:
- [ ] Source is official government/regulatory body
- [ ] Effective dates are specific and verified
- [ ] Applicability (which jurisdictions) is clear
- [ ] Current status is distinguished from proposals

### 16. Statistical/Numerical Information
For data claims:
- [ ] Source of data is cited
- [ ] Date of data is provided
- [ ] Context/definitions are clear ("GDP per capita vs. total GDP")
- [ ] Potential biases in data source are noted

---

## PRE-PUBLICATION CHECKLIST

### 17. Final Quality Scan
- [ ] Run through response_quality.py checker
- [ ] Review all flagged issues
- [ ] Confidence score is appropriate for content
- [ ] All recommendations addressed

### 18. Fact-Check Results
- [ ] No CRITICAL or HIGH severity issues
- [ ] Date accuracy check: PASSED
- [ ] Unverifiable claims: None or properly attributed
- [ ] Generic filler: None detected
- [ ] Context mismatch: None

### 19. Safety Check
- [ ] Response ready for publication (is_safe_to_publish = TRUE)
- [ ] Confidence level matches content quality
- [ ] Sources are appropriate and credited
- [ ] No hallucinations or made-up references

### 20. User Experience Check
- [ ] Response is helpful and actionable
- [ ] Tone is appropriate and conversational
- [ ] Length is appropriate for topic
- [ ] Call-to-action (if needed) is clear

---

## USAGE GUIDE

### For Manual Responses:
Go through checklist items 1-19 before submitting.

### For Automated Responses:
1. Generate initial response
2. Run response_quality.py check
3. Review any flagged issues
4. Revise response if needed
5. Re-check if major revisions made
6. Publish only if is_safe_to_publish = TRUE

### Example Quality Report Output:
```
Confidence Level: HIGH (89%)
Safe to Publish: YES

No issues found.

Sources:
- Official PyTorch Documentation
- IEEE Research Paper
```

---

## COMMON FAILURE PATTERNS TO AVOID

### ❌ Pattern 1: Future Dates
**BAD**: "As of March 25, 2025, PyTorch supports..."
**GOOD**: "As of January 20, 2026, PyTorch currently supports..."

### ❌ Pattern 2: Unverified References
**BAD**: "GitHub - shuozhenchen/hello-world has 100 examples"
**GOOD**: "The official PyTorch tutorials website provides examples..."

### ❌ Pattern 3: Generic Filler
**BAD**: "Here are 100 small Python examples covering most topics"
**GOOD**: "Here are 5 specific examples: 1) Variables, 2) Functions, 3) Loops, 4) Lists, 5) Dictionaries"

### ❌ Pattern 4: Context Mismatch
**BAD**: "PyTorch is a programming language with Hello World examples"
**GOOD**: "PyTorch is a deep learning framework for building neural networks"

### ❌ Pattern 5: Unsourced Policy Claims
**BAD**: "Canada is imposing a retaliatory 20% tariff"
**GOOD**: "According to the Canadian Department of Finance (as of January 2026), ..."

---

## CONFIDENCE LEVEL GUIDELINES

### HIGH CONFIDENCE (90%+)
✓ Established facts from primary sources
✓ Official documentation or government sources
✓ Peer-reviewed academic research
✓ Multiple reputable sources in agreement

Examples:
- "Python is an interpreted programming language" [HIGH]
- "PyTorch is a deep learning framework by Meta" [HIGH]

### MEDIUM CONFIDENCE (60-80%)
✓ Information from reputable secondary sources
✓ Expert opinions with reasonable basis
✓ Industry best practices
✓ Information that may vary by context or version

Examples:
- "Most data scientists prefer PyTorch for X use case" [MEDIUM]
- "The typical learning curve for PyTorch is approximately 2-4 weeks" [MEDIUM]

### LOW CONFIDENCE (0-50%)
✓ Speculative information
✓ Information from unclear sources
✓ Incomplete or conflicting information
✓ Personal anecdotes or limited samples

Examples:
- "Beginners might find PyTorch easier than other frameworks" [LOW]
- "Future versions of PyTorch may include X feature" [LOW]

---

## ESCALATION PROCEDURE

If response receives LOW confidence or has issues:
1. Don't publish immediately
2. Try to find better sources
3. Add confidence marker and uncertainty language
4. OR mark for human review
5. Document reasoning for any exceptions

---

## REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-20 | Initial checklist creation |

---

**Last Updated**: January 20, 2026  
**Maintainer**: Quality Assurance System
