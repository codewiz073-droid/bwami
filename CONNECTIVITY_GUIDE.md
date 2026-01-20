# Automatic Connectivity Detection Guide

## Overview

The AI Assistant now features **automatic connectivity detection** that intelligently switches between internet-based and offline (Ollama) modes based on your network availability.

## How It Works

### Backend Detection

**Location**: `connectivity.py`

The system performs automatic network detection using:
1. **Primary Method**: Socket connection to Google DNS (8.8.8.8:53)
2. **Fallback 1**: Socket connection to Cloudflare DNS (1.1.1.1:53)  
3. **Fallback 2**: Socket connection to port 80 (HTTP)

Each check has a 2-second timeout to avoid delays if network is unavailable.

### Frontend Monitoring

The frontend (`static/script.js`) periodically checks connectivity:
- **Initial Check**: On page load
- **Periodic Check**: Every 15 seconds
- **Display**: Shows current mode with "(Auto)" or "(Manual)" indicator

### Mode Switching

The system maintains two modes:

| Mode | Status | Uses | Features |
|------|--------|------|----------|
| **Online 🌐** | `🌐 Online (Auto)` | Internet + LLM + Web Search | Full capabilities, real-time info |
| **Offline 📡** | `📡 Offline (Auto)` | Local Ollama | Works without internet |

## Features

### ✅ Automatic Detection
- System detects WiFi/data connectivity automatically
- No manual configuration needed
- Responds to connectivity changes within 15 seconds

### ✅ Manual Override
- Click the mode button to toggle manual mode
- In manual mode, you can force online or offline
- Click again to return to automatic detection
- Shows "(Manual)" indicator when overridden

### ✅ Real-Time Updates
- Mode icon updates automatically as connectivity changes
- Hover over button to see current status
- No page reload needed

### ✅ Seamless Fallback
- If internet is lost, automatically uses Ollama
- If internet is restored, automatically uses web search again
- User experience remains smooth

## API Endpoints

### GET `/status/connectivity`
Returns current connectivity status:
```json
{
  "online": true,
  "status": "Online (Internet Available)",
  "mode": "🌐 Online"
}
```

### GET/POST `/mode`
Get or set current mode:

**GET Response** (Auto mode):
```json
{
  "mode": "online",
  "detectedOnline": true,
  "detectedStatus": "Online (Internet Available)"
}
```

**POST Request** (Manual mode):
```json
{
  "mode": "online"
}
```

**POST Response**:
```json
{
  "status": "ok",
  "mode": "online",
  "detectedOnline": true,
  "detectedStatus": "Online (Internet Available)"
}
```

## Configuration

### Default Settings
- **Check Interval**: 15 seconds (frontend)
- **Socket Timeout**: 2 seconds per attempt
- **Auto Mode**: Enabled by default

### Changing Check Interval (Advanced)

Edit `static/script.js`, find the `startConnectivityMonitoring()` function:

```javascript
// Change 15000 (15 seconds) to desired milliseconds
setInterval(checkConnectivity, 15000);
```

Common intervals:
- `5000` = 5 seconds (more responsive, higher CPU)
- `15000` = 15 seconds (balanced - default)
- `30000` = 30 seconds (less responsive, lower CPU)

## Troubleshooting

### Icon Not Updating
1. Check browser console (F12) for errors
2. Verify `/status/connectivity` endpoint is accessible
3. Refresh page and wait 15 seconds for next check

### Always Shows Offline
1. Check if Ollama service is running (should work offline)
2. Verify internet connection is working
3. Try manual connectivity test: Open DevTools → Network tab → Load `/status/connectivity`

### Connectivity Detection Not Working
1. Check network connectivity: `ping 8.8.8.8` in terminal
2. Check firewall settings (may block DNS port 53)
3. If behind corporate firewall, connectivity checks may fail - use manual mode

## Response Mode Examples

### Online Mode (🌐 Internet Available)
```
User: "What's the latest news about AI?"

System: [🌐 Online]
→ Uses web search to find current articles
→ Provides up-to-date information
→ Cites recent sources
```

### Offline Mode (📡 Using Ollama)
```
User: "What's the latest news about AI?"

System: [📡 Offline (Ollama)]
→ Uses local knowledge only
→ Provides general information from training data
→ No external sources available
```

## Technical Details

### Connectivity Check Flow
```
1. Frontend: Every 15 seconds, call GET /status/connectivity
2. Backend: connectivity.py checks internet availability
3. Response: {"online": bool, "status": string}
4. Frontend: Updates mode button if status changed
5. /ask route: Also performs connectivity check before response
```

### Dual Detection
The system checks connectivity **twice**:
1. **Per-request**: Each API call to `/ask` includes a connectivity check
2. **Periodic**: Frontend checks every 15 seconds for UI updates

This ensures both accurate mode selection and responsive UI updates.

## Performance Implications

- **Backend Check**: ~2 seconds max (due to timeouts)
  - But typically completes in <100ms with internet
  - Doesn't block request handling (async detection)

- **Frontend Checks**: ~2-3 seconds per periodic check
  - Runs in background, doesn't affect UI responsiveness
  - Only updates button if status changes

## Privacy & Security

- ✅ No data sent to external services (only connection test)
- ✅ Uses only standard DNS servers (Google, Cloudflare)
- ✅ No tracking or telemetry
- ✅ All checks performed locally

## Future Enhancements

Possible improvements for future versions:
- [ ] Configurable detection servers (proxy/firewall support)
- [ ] Connection quality measurement (network speed)
- [ ] Hybrid mode (use Ollama for fast local responses, web search for factual queries)
- [ ] Offline data synchronization when reconnecting
- [ ] Custom connectivity check interval in UI settings

## Summary

Your AI Assistant now:
1. **Automatically detects** when you're online or offline
2. **Intelligently switches** between internet and Ollama modes
3. **Shows clear indicators** of current mode and detection status
4. **Allows manual override** when needed
5. **Works seamlessly** across connectivity changes

No action needed - it works automatically! 🚀
