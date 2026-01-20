# System Prompt Architecture

## Overview
This project follows a **separation of concerns** principle where all instructions and behavioral guidelines are separated from the executable code.

## Core Capabilities & Architecture

### Intelligence Stack
The system is built on four core capabilities:

1. **Language Model Foundation**
   - Large language model with comprehensive knowledge
   - Advanced reasoning and context understanding
   - Multi-language and multi-domain support

2. **Information Synthesis**
   - Intelligent combination of multiple information sources
   - Smart extraction and contextualization
   - Direct addressing of user needs

3. **Real-Time Data Access**
   - Live web search integration
   - Current information retrieval
   - External verification capabilities

4. **Visual & Multimodal Support**
   - Image analysis and visual search
   - Object identification
   - Cross-modal reasoning

## File Organization

### System Prompt
- **File**: `system_prompt.txt`
- **Purpose**: Contains all instructions, guidelines, and behavioral rules for the AI assistant
- **Content**:
  - Core capabilities (language model, information synthesis, real-time data access, visual search)
  - 5 intelligence layers (intent detection, reasoning, formatting, domain-specific rules, validation)
  - Response quality checklist
  - Request classification guide
  - Essay writing guidelines
  - Math solving guidelines
  - Code generation guidelines
  - Domain-specific instructions
  - Supported technologies

### Core Application Files
- **main.py**: Loads `system_prompt.txt` and uses it when making API calls
- **app.py**: Flask web server (functional code only)
- **request_classifier.py**: Request type detection (functional code only)
- **essay_writer.py**: Academic essay generation (functional code only)
- **math_solver.py**: Mathematical problem solving (functional code only)
- **custom_rules.py**: Custom domain rules management (functional code only)

## How It Works

1. **Startup**: When `main.py` starts, it loads `system_prompt.txt`:
```python
def load_system_prompt(filename="system_prompt.txt"):
    """Load system prompt from external file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using fallback prompt.")
        return "You are a professional-grade intelligent assistant."

SYSTEM_PROMPT = load_system_prompt()
```

2. **API Calls**: When making requests to OpenAI or Ollama, the loaded prompt is used:
```python
def online_response(user_input):
    chat = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    return chat.choices[0].message.content
```

3. **No Instructions in Code**: All Python files contain only functional code:
   - Detection logic
   - API calls
   - Data processing
   - Response formatting
   - No behavioral instructions

## Benefits

✅ **Maintainability**: Easy to update instructions without touching code
✅ **Scalability**: Can have different system prompts for different use cases
✅ **Clarity**: Clear separation between "what to do" and "how to do it"
✅ **Flexibility**: Swap system prompts without code changes
✅ **Version Control**: Easier to track instruction changes vs code changes
✅ **Collaboration**: Non-programmers can update instructions

## Modifying Instructions

To change how the AI behaves:
1. Edit `system_prompt.txt`
2. Restart the application
3. Changes take effect immediately

No code changes required!

## Modifying Functionality

To change how the application works:
1. Edit the relevant Python file (`main.py`, `essay_writer.py`, etc.)
2. Changes only affect functionality, not behavior
3. System prompt remains unchanged

## File Dependencies

```
system_prompt.txt
        ↓
    main.py (loads prompt)
        ↓
    app.py (uses main.py)
```

All other files are independent utility modules with no embedded instructions.
