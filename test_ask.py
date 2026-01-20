import requests
import json

base_url = "http://localhost:5000"

try:
    # Step 1: Create guest session
    print("Step 1: Creating guest session...")
    guest_response = requests.post(f"{base_url}/auth/guest", timeout=10)
    print(f"Guest response status: {guest_response.status_code}")
    
    if guest_response.status_code != 200:
        print(f"Failed to create guest session: {guest_response.text}")
        exit(1)
    
    guest_data = guest_response.json()
    token = guest_data.get("token")
    print(f"Got token: {token[:20]}..." if token else "No token received")
    
    # Step 2: Send message to /ask with token
    print("\nStep 2: Sending message...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}" if token else "Bearer invalid"
    }
    data = {
        "message": "hello",
        "chat_id": "test123"
    }
    
    response = requests.post(f"{base_url}/ask", headers=headers, json=data, stream=True, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text[:200]}")
        exit(1)
    
    # Read events
    full_response = ""
    event_count = 0
    
    print("\nStep 3: Reading response stream...")
    for line in response.iter_lines():
        if line:
            try:
                if line.startswith(b'data: '):
                    data_str = line[6:].decode('utf-8')
                    event = json.loads(data_str)
                    event_count += 1
                    
                    if event.get('type') == 'status':
                        print(f"[STATUS] {event.get('text')}")
                    elif event.get('type') == 'text':
                        text = event.get('text', '')
                        full_response += text
                        if event_count <= 3:
                            print(f"[TEXT] {text[:60]}")
                    elif event.get('type') == 'done':
                        print(f"[DONE] Response complete")
                        
            except Exception as e:
                print(f"Parse error: {e}")
    
    print(f"\n=== RESULTS ===")
    print(f"Total events: {event_count}")
    print(f"Response length: {len(full_response)} chars")
    print(f"Response:\n{full_response[:500]}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

