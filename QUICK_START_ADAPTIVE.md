# Quick Start: Adaptive Learning & Formatted Responses

## For Users

### Getting Started

1. **Start the App**
   ```bash
   python app.py
   ```
   Visit: http://localhost:5000

2. **Chat as Guest** (No signup required)
   - Just start typing
   - AI responds with default formatting

3. **Create Account** (To customize)
   - Click 👤 → "Sign In"
   - Click "Create Account"
   - Fill in username, email, password
   - Submit

4. **Customize Responses**
   - Click 👤 → "⚙️ Preferences"
   - Toggle formatting options:
     - **Use Lists**: Break text into numbered items
     - **Use Bullets**: Add • for non-sequential items
     - **Use Emojis**: Add visual indicators (🔍, 💡, etc.)
   - Choose **Tone**: Professional, Casual, Technical
   - Set **Language**: English, Spanish, French, German, Japanese
   - Add **Specializations**: Your areas of expertise (Python, Web Dev, etc.)
   - Click **Save Preferences**

5. **See Changes Immediately**
   - Next response uses your new preferences
   - Responses automatically formatted according to your settings

### Example Settings Combinations

**Professional + No Emojis**
```
1. First point
2. Second point
3. Third point

Important: Key information
```

**Casual + With Emojis**
```
✨ Here's the cool part
💡 Quick tip: Something useful
🔥 Pro move: Advanced technique
```

**Technical + Lists**
```
1. Initialize module
2. Configure parameters
3. Deploy to production

Critical: Always validate before deployment
```

## For Developers

### Quick Integration

#### 1. Check User Preferences
```python
from auth import get_user_preferences

user_id = request.user_id  # From your auth system
prefs = get_user_preferences(user_id)

print(prefs)
# {
#   "use_lists": True,
#   "use_numbered": True,
#   "preferred_tone": "professional",
#   ...
# }
```

#### 2. Format a Response
```python
from response_formatter import format_response

raw_response = "Here are the steps. First do X. Then do Y. Finally do Z."

formatted = format_response(raw_response, prefs)
print(formatted)
# 1. Here are the steps
# 2. 📍 Do X
# 3. 📍 Do Y
# 4. 📍 Do Z
```

#### 3. In Your API Route
```python
@app.route("/chat", methods=["POST"])
def chat():
    user_id = get_user_id()  # Your auth
    message = request.json.get("message")
    
    # Generate response
    raw_response = ai_model.generate(message)
    
    # Load preferences
    prefs = get_user_preferences(user_id)
    
    # Format
    formatted = format_response(raw_response, prefs)
    
    # Return
    return jsonify({"response": formatted})
```

### API Reference

#### GET /user/preferences
Get user's response formatting preferences.

**Request:**
```
GET /user/preferences
Authorization: Bearer {token}
```

**Response:**
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

#### POST /user/preferences
Update user's response formatting preferences (account users only).

**Request:**
```
POST /user/preferences
Authorization: Bearer {token}
Content-Type: application/json

{
  "use_lists": true,
  "use_numbered": false,
  "use_bullets": true,
  "use_emojis": false,
  "preferred_tone": "casual",
  "preferred_language": "en",
  "specializations": ["Python", "Data Science"]
}
```

**Response:**
```json
{
  "status": "ok",
  "preferences": {
    "response_format": "formatted",
    "use_lists": true,
    ...
  }
}
```

### Code Examples

#### Example 1: Conditional Formatting
```python
def generate_response(user_id, query):
    response = comprehensive_response(query)
    prefs = get_user_preferences(user_id)
    
    # Skip formatting for technical users?
    if "DevOps" in prefs["specializations"]:
        # Just return raw response
        return response
    
    # Format for others
    return format_response(response, prefs)
```

#### Example 2: Using Specializations
```python
def personalized_response(user_id, query):
    prefs = get_user_preferences(user_id)
    specs = prefs["specializations"]
    
    # Tailor response based on expertise
    context = f"User expertise: {', '.join(specs)}"
    prompt = f"{context}\n\nQ: {query}"
    
    response = ai_model.generate(prompt)
    return format_response(response, prefs)
```

#### Example 3: Storing Preferences Locally (Frontend)
```javascript
// Save to localStorage
async function savePref(pref, value) {
  const prefs = JSON.parse(localStorage.getItem("userPrefs") || "{}");
  prefs[pref] = value;
  localStorage.setItem("userPrefs", JSON.stringify(prefs));
  
  // Also sync to server
  await fetch("/user/preferences", {
    method: "POST",
    headers: {"Authorization": `Bearer ${token}`},
    body: JSON.stringify(prefs)
  });
}

// Quick toggle
function toggleEmojis() {
  const enabled = localStorage.getItem("useEmojis") !== "false";
  savePref("useEmojis", !enabled);
}
```

## Common Tasks

### Change Response Format Globally
```python
# Set defaults for all new users
def create_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    db.add(user)
    db.commit()
    
    # Create preferences with custom defaults
    prefs = UserPreferences(
        user_id=user.id,
        response_format="formatted",
        use_lists=True,
        use_emojis=False,  # Your default
        preferred_tone="professional"
    )
    db.add(prefs)
    db.commit()
```

### Export User Preferences
```python
def export_prefs(user_id):
    prefs = get_user_preferences(user_id)
    
    # Convert to JSON
    import json
    return json.dumps(prefs, indent=2)

# Use it
json_str = export_prefs(user_id)
with open("user_prefs.json", "w") as f:
    f.write(json_str)
```

### Import User Preferences
```python
def import_prefs(user_id, json_str):
    import json
    prefs = json.loads(json_str)
    return update_user_preferences(user_id, prefs)

# Use it
with open("user_prefs.json", "r") as f:
    json_str = f.read()
    import_prefs(user_id, json_str)
```

## Troubleshooting

### Problem: Settings modal doesn't appear
**Solution:**
1. Check browser console (F12) for errors
2. Verify user is account user (not guest)
3. Check that CSS file loaded (check network tab)

### Problem: Changes not saving
**Solution:**
1. Check network tab - POST request should return 200
2. Verify JWT token is valid
3. Check database - user_preferences table exists
4. Check user_id exists in users table

### Problem: Responses still plain
**Solution:**
1. Verify format_response() called in /ask route
2. Check preferences are loading (add print statements)
3. Verify preferences have use_lists=true, etc.

### Problem: Formatting looks wrong
**Solution:**
1. Try resetting to defaults in settings
2. Clear browser cache (Ctrl+Shift+Delete)
3. Log out and log back in
4. Check database for corrupted data

## File Locations

```
my_ai_assistant/
├── models.py                  # UserPreferences model
├── auth.py                    # Preference functions
├── app.py                     # API routes
├── response_formatter.py      # Formatting logic (NEW)
├── templates/
│   └── index.html            # Settings modal
├── static/
│   ├── auth.js               # Preference load/save
│   ├── script.js             # Settings modal handlers
│   └── style.css             # Modal styling
└── ADAPTIVE_LEARNING_GUIDE.md # Full documentation
```

## Next Steps

1. ✅ **Basic Setup** - Users can customize response format
2. 🔄 **Specialization Tracking** - System learns user domains
3. 🎯 **Context-Aware Responses** - Tailor based on specializations
4. 📊 **Analytics** - Track which preferences users prefer
5. 🌐 **Multi-Language** - Full language support in responses

## Support

For issues or questions:
1. Check ADAPTIVE_LEARNING_GUIDE.md for detailed documentation
2. Review IMPLEMENTATION_COMPLETE.md for architecture
3. Run verify_adaptive_learning.py to diagnose issues
4. Check Flask debug output (terminal) for errors
