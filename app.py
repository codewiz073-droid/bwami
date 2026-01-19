from flask import (
    Flask,
    render_template,
    request,
    Response,
    jsonify,
    stream_with_context
)
import time
import json
import os

from main import comprehensive_response
from web_search import search_web, fetch_page

# Database helpers (ONLY place DB is handled)
from db import (
    init_db,
    save_message,
    get_chat_list,
    get_chat_history,
    delete_chat
)

# =========================
# APP SETUP
# =========================
app = Flask(__name__)

# Initialize DB ONCE on startup
init_db()
print("✅ Database initialized")

# =========================
# GLOBAL MODE SWITCH
# =========================
current_mode = {"online": True}  # True = Online, False = Offline

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# ASK / STREAM RESPONSE
# =========================
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    user_input = data.get("message", "").strip()
    chat_id = data.get("chat_id", "default")

    if not user_input:
        return Response("", mimetype="text/event-stream")

    # Save user message immediately
    save_message(chat_id, "user", user_input)

    def generate():
        full_response = ""
        web_context = ""

        # Optional web search trigger
        if user_input.lower().startswith(("search:", "web:", "current:")):
            if current_mode["online"]:
                yield f"data: {json.dumps({'type': 'status', 'text': 'Searching web...'})}\n\n"

                try:
                    query = user_input.split(":", 1)[1].strip()
                    sources = search_web(query)

                    for src in sources[:2]:
                        page = fetch_page(src["url"])
                        if page:
                            web_context += page[:500] + "\n"

                except Exception as e:
                    print("Web search error:", e)

        # Generate AI response
        if current_mode["online"] and web_context:
            prompt = f"{user_input}\n\n[Web info]\n{web_context}"
            response_text = comprehensive_response(prompt, mode="online")
        else:
            response_text = comprehensive_response(user_input, mode="offline")

        # Stream word-by-word
        for word in response_text.split():
            chunk = word + " "
            full_response += chunk
            yield f"data: {json.dumps({'type': 'text', 'text': chunk})}\n\n"
            time.sleep(0.01)

        # Save assistant response
        save_message(chat_id, "assistant", full_response.strip())

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# =========================
# CHAT LIST
# =========================
@app.route("/chats")
def chats():
    return jsonify(get_chat_list())


# =========================
# CHAT HISTORY
# =========================
@app.route("/history/<chat_id>")
def history(chat_id):
    return jsonify(get_chat_history(chat_id))


# =========================
# DELETE CHAT
# =========================
@app.route("/delete/<chat_id>", methods=["DELETE"])
def delete_chat_route(chat_id):
    delete_chat(chat_id)
    return jsonify({"status": "ok"})


# =========================
# MODE TOGGLE
# =========================
@app.route("/mode", methods=["GET", "POST"])
def toggle_mode():
    if request.method == "POST":
        mode = request.json.get("mode", "online")
        current_mode["online"] = (mode == "online")
        return jsonify({"status": "ok", "mode": mode})

    return jsonify({
        "mode": "online" if current_mode["online"] else "offline"
    })


# =========================
# NO CACHE (DEV FRIENDLY)
# =========================
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
