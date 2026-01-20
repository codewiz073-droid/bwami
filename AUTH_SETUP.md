"""
USER AUTHENTICATION SYSTEM SETUP GUIDE
=====================================

FEATURES IMPLEMENTED:
✅ User accounts (register, login, logout)
✅ Guest mode (temporary guest sessions)
✅ JWT token-based authentication
✅ Password hashing (werkzeug)
✅ Session management (Flask sessions)
✅ Frontend login/signup modals
✅ User menu (top-right corner)

DATABASE CHANGES:
- Added User model with username, email, password_hash
- Updated Chat model with user_id and is_guest fields
- Messages automatically link to chats which link to users

FILES CREATED/MODIFIED:
- auth.py (NEW) - Backend authentication logic
- models.py (UPDATED) - Added User model, updated Chat/Message
- database.py (UPDATED) - Added init_db() to create all tables
- app.py (UPDATED) - Added auth routes (/auth/*)
- static/auth.js (NEW) - Frontend authentication UI
- static/style.css (UPDATED) - Auth modal & user menu styles
- templates/index.html (UPDATED) - Auth modal & user menu HTML
- static/script.js (UPDATED) - Pass auth token with requests
- requirements.txt (UPDATED) - Added PyJWT

AUTHENTICATION FLOW:

1. USER VISITS APP
   ↓
   Frontend checks /auth/status
   ↓
   If not authenticated → Show auth modal
   If authenticated → Show app

2. LOGIN/SIGNUP
   User fills form → POST /auth/login or /auth/signup
   Backend creates user & returns JWT token
   Frontend stores token in localStorage
   Frontend stores user_id in session

3. GUEST MODE
   User clicks "Continue as Guest"
   → POST /auth/guest creates temporary user
   → Returns JWT token (user_id with is_guest=true)
   → Guest can use app without creating account

4. SUBSEQUENT REQUESTS
   Frontend attaches token: Authorization: Bearer <token>
   Backend verifies token and extracts user_id
   All chats/messages linked to user_id

5. LOGOUT
   POST /auth/logout clears session
   Frontend clears localStorage token
   Frontend shows auth modal again

ENVIRONMENT VARIABLES:
Set in .env file:
  SECRET_KEY=your-secure-key-here  (change for production)
  
Default secret key is used if not set (NOT for production!)

API ENDPOINTS:

POST /auth/signup
  Body: { username, email, password }
  Returns: { user_id, is_guest, token, username }

POST /auth/login  
  Body: { username, password }
  Returns: { user_id, is_guest, token, username }

POST /auth/guest
  No body required
  Returns: { user_id, is_guest, token, username }

POST /auth/logout
  Clears session

GET /auth/status
  Returns: { authenticated: bool, user_id?, is_guest? }

CHAT STORAGE:
- Account users: Chats stored in DB, linked to user_id
- Guest users: Temporary chats, linked to guest user_id
- All chats searchable via /chats endpoint (user-specific)

FRONTEND COMPONENTS:

Auth Modal:
  - Login form (username, password)
  - Signup form (username, email, password)
  - Guest button on both forms
  - Form switching via links

User Menu (top-right 👤):
  - Shows "Guest User" or "Account User"
  - Logout button
  - Closes when clicking elsewhere

Token Storage:
  - Stored in localStorage as auth_token
  - Passed in Authorization header with requests
  - Expires in 7 days

TESTING:

1. Test Guest Mode:
   Click "Continue as Guest" → Should show app
   Verify chats are saved
   Refresh page → Chats still visible

2. Test Signup:
   Click "Sign up" → Fill form → Create account
   Verify user menu shows "Account User"

3. Test Login:
   Create account, logout, login again with same credentials

4. Test Token:
   Open DevTools → Application → LocalStorage
   Should see auth_token value
   
PRODUCTION CONSIDERATIONS:
⚠️  Change SECRET_KEY in environment
⚠️  Use HTTPS only (secure cookies)
⚠️  Consider token expiration policy
⚠️  Hash passwords (already done via werkzeug)
⚠️  Rate limit auth endpoints
⚠️  Validate email addresses
⚠️  Add email verification for signup
⚠️  Implement password reset flow

TROUBLESHOOTING:

"Unauthorized" error on /ask or /chats:
  → Check localStorage for auth_token
  → Check browser console for errors
  → Clear localStorage and re-login

Auth modal appears after login:
  → Token might be expired
  → Check if SECRET_KEY changed between requests
  → Clear browser data and try again

Guest session persists after refresh:
  → This is expected behavior
  → Token stored in localStorage survives refresh
  → Logout to clear it
"""
