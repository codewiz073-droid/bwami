# Adaptive Learning & Formatted Responses System

## Overview
The AI Assistant now features adaptive learning and intelligent response formatting based on user preferences. The system learns user preferences over time and tailors responses to their communication style.

## Key Features

### 1. User Preferences Storage
- **Database Model**: `UserPreferences` table stores per-user preferences
- **Data Stored**:
  - `response_format`: "formatted" or "plain"
  - `use_lists`: Boolean (enable list formatting)
  - `use_numbered`: Boolean (enable numbered lists)
  - `use_bullets`: Boolean (enable bullet points)
  - `use_emojis`: Boolean (enable emoji indicators)
  - `preferred_tone`: "professional", "casual", or "technical"
  - `preferred_language`: "en", "es", "fr", "de", "ja" (extensible)
  - `custom_system_prompt`: Optional custom system prompt
  - `specializations`: JSON array of user expertise areas
  - `learning_mode`: Boolean (auto-learns user preferences)

### 2. Response Formatting
The system automatically formats responses based on user preferences:

#### Features:
- **Structured Lists**: Converts paragraphs into clear list items (numbered or bulleted)
- **Visual Separators**: Adds section breaks for better readability
- **Key Point Emphasis**: Highlights important words (important, critical, note, etc.)
- **Emoji Indicators**: Adds relevant emojis for quick scanning (🔍, 💡, ⚠️, ✅, etc.)
- **Tone Adjustment**: Adapts language to user's preferred tone

#### Example:
**Before (Plain):**
```
There are several steps to follow. First install dependencies. 
Second configure settings. Third run the application. Note that 
this is critical for proper operation.
```

**After (Formatted):**
```
1. 📍 Install dependencies
2. 📍 Configure settings  
3. 📍 Run the application

⭐ Important: This is critical for proper operation
```

### 3. Preferences API

#### GET `/user/preferences`
Returns current user preferences.
```bash
curl -H "Authorization: Bearer {token}" http://localhost:5000/user/preferences
```

Response:
```json
{
  "response_format": "formatted",
  "use_lists": true,
  "use_numbered": true,
  "use_bullets": true,
  "use_emojis": true,
  "preferred_tone": "professional",
  "preferred_language": "en",
  "custom_system_prompt": null,
  "specializations": ["Python", "Web Development"]
}
```

#### POST `/user/preferences`
Update user preferences (account users only).
```bash
curl -X POST -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "use_lists": true,
    "use_numbered": true,
    "use_bullets": true,
    "use_emojis": false,
    "preferred_tone": "casual",
    "specializations": ["Python", "Data Science"]
  }' \
  http://localhost:5000/user/preferences
```

### 4. Settings UI

Located in the user menu (top-right 👤 button):

#### For Account Users:
- **⚙️ Preferences** button appears
- Opens settings modal with:
  - Response Format toggles (lists, numbered, bullets, emojis)
  - Communication Style (tone, language)
  - Learning Mode toggle
  - Specialization input (comma-separated)
  - Save/Reset buttons

#### For Guests:
- Settings button does not appear
- Must sign up to customize preferences

### 5. Response Formatting Pipeline

Flow:
1. User sends message → `/ask` route
2. AI generates response via `comprehensive_response()`
3. **User preferences loaded** via `get_user_preferences(user_id)`
4. **Response formatted** via `format_response(text, preferences)`
5. Formatted response streamed to client
6. **Message saved** with original text (before formatting for consistency)

### 6. Adaptive Learning (Specializations)

Users can specify their areas of expertise:
- Python
- Web Development
- Data Science
- Machine Learning
- etc.

These specializations can be used to:
- Tailor response examples to user's domain
- Adjust technical depth
- Suggest relevant resources
- Future: Generate context-aware system prompts

## Implementation Details

### Files Modified:

1. **models.py**
   - Added `UserPreferences` SQLAlchemy model
   - One-to-one relationship with `User` model
   - Auto-creates default preferences for new users

2. **auth.py**
   - `get_user_preferences(user_id)`: Loads preferences from DB
   - `update_user_preferences(user_id, preferences)`: Saves preferences

3. **app.py**
   - `GET /user/preferences`: Retrieve user preferences
   - `POST /user/preferences`: Update preferences
   - `/ask` route: Loads preferences before formatting response

4. **response_formatter.py** (New)
   - `format_response()`: Main formatting function
   - `_structure_into_lists()`: Convert text to lists
   - `_add_visual_separators()`: Add section breaks
   - `_emphasize_key_points()`: Highlight important words
   - `_add_relevant_emojis()`: Add contextual emojis

5. **templates/index.html**
   - Settings modal with preference controls
   - Settings button in user menu (account users only)

6. **static/auth.js**
   - `loadPreferences()`: Fetch preferences from server
   - `savePreferences()`: Save preferences to server
   - Settings button visibility toggle in `updateUserMenu()`

7. **static/script.js**
   - `setupSettingsModal()`: Initialize settings UI
   - Modal open/close/save handlers
   - Load preferences on settings button click

8. **static/style.css**
   - Settings modal styling (.settings-modal, .settings-container, etc.)
   - Form inputs and toggles styling
   - Responsive layout for settings

### New Module: response_formatter.py

Provides intelligent text formatting:
```python
from response_formatter import format_response

prefs = {
    "use_lists": True,
    "use_numbered": True,
    "use_bullets": True,
    "use_emojis": True,
    "preferred_tone": "professional"
}

formatted = format_response(raw_text, prefs)
```

## Usage Examples

### For Users:

1. **Access Settings** (Account Users Only):
   - Click 👤 in top-right
   - Click "⚙️ Preferences"
   - Toggle formatting options
   - Click "Save Preferences"

2. **Customize Response Format**:
   - Enable/disable lists, numbers, bullets, emojis
   - Choose tone (professional, casual, technical)
   - Set language preference
   - Specify specializations (for future tailoring)

3. **Automatic Formatting**:
   - All responses automatically formatted per preferences
   - Changes apply immediately to future messages
   - Learning Mode enabled by default (can be disabled)

### For Developers:

1. **Check User Preferences**:
```python
from auth import get_user_preferences
prefs = get_user_preferences(user_id)
print(prefs["preferred_tone"])  # "professional"
```

2. **Format Response**:
```python
from response_formatter import format_response
response = comprehensive_response(query)
formatted = format_response(response, user_prefs)
```

3. **Update Preferences**:
```python
from auth import update_user_preferences
update_user_preferences(user_id, {
    "preferred_tone": "casual",
    "use_emojis": False
})
```

## Default Preferences

New users get these defaults:
```json
{
  "response_format": "formatted",
  "use_lists": true,
  "use_numbered": true,
  "use_bullets": true,
  "use_emojis": true,
  "preferred_tone": "professional",
  "preferred_language": "en",
  "custom_system_prompt": null,
  "specializations": [],
  "learning_mode": true
}
```

## Future Enhancements

1. **Context-Aware System Prompts**
   - Use specializations to generate custom system prompts
   - Example: "The user is an expert in Python and Web Development. Tailor examples accordingly."

2. **Learning from Feedback**
   - Track which response formats users engage with most
   - Auto-adjust preferences based on usage patterns

3. **Domain-Specific Responses**
   - Different formatting for different domains
   - Technical responses use code blocks, lists
   - Creative responses use narrative formatting

4. **Export/Import Preferences**
   - Share preference profiles
   - Cloud sync across devices

5. **Response History Analysis**
   - Show insights about preference usage
   - Suggest optimizations

## Security & Privacy

- Preferences tied to user_id (no cross-user access)
- Only account users can save preferences
- Guest preferences not persisted
- Preferences returned only to their owner
- POST endpoint checks `is_guest` flag

## Testing

Test the system:
```bash
# 1. Start Flask server
python app.py

# 2. Sign up for account
POST /auth/signup
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}

# 3. Update preferences
POST /user/preferences
Authorization: Bearer {token}
{
  "use_emojis": false,
  "preferred_tone": "casual"
}

# 4. Get preferences
GET /user/preferences
Authorization: Bearer {token}

# 5. Send message and observe formatted response
POST /ask
Authorization: Bearer {token}
{
  "message": "Explain how to learn Python",
  "chat_id": "test-chat"
}
```

## Notes

- Response formatting happens **server-side** during streaming
- Original response text is saved to database (unformatted)
- Formatting is applied per-user, not globally
- Guests get default formatting (cannot customize)
- Performance impact is minimal (formatting ~milliseconds)
