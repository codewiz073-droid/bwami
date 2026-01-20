"""Network connectivity detection module"""
import socket
import threading
import time
from functools import wraps


class ConnectivityChecker:
    """Checks if device has internet connectivity"""
    
    def __init__(self, check_interval=30):
        """
        Initialize connectivity checker
        
        Args:
            check_interval: Seconds between checks (default 30)
        """
        self.is_online = True  # Default to online
        self.check_interval = check_interval
        self.checking = False
        
    def check_internet(self):
        """
        Check if internet is available by attempting to reach reliable DNS servers
        
        Returns:
            bool: True if internet available, False if offline
        """
        try:
            # Try to connect to Google's DNS server (fastest timeout)
            # If this fails, try other methods
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (socket.error, socket.timeout):
            pass
        
        try:
            # Fallback: try to reach cloudflare DNS
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            return True
        except (socket.error, socket.timeout):
            pass
        
        try:
            # Another fallback: try HTTPS connection to a reliable server
            socket.create_connection(("8.8.8.8", 80), timeout=2)
            return True
        except (socket.error, socket.timeout):
            pass
        
        return False
    
    def start_monitoring(self):
        """Start background thread to monitor connectivity"""
        if self.checking:
            return
        
        self.checking = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring connectivity"""
        self.checking = False
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.checking:
            try:
                self.is_online = self.check_internet()
            except Exception as e:
                print(f"Connectivity check error: {e}")
                self.is_online = False
            
            time.sleep(self.check_interval)
    
    def get_status(self):
        """Get current connectivity status"""
        # Do a quick check instead of relying on background thread
        self.is_online = self.check_internet()
        return {
            "online": self.is_online,
            "status": "Online (Internet Available)" if self.is_online else "Offline (Using Ollama)"
        }


# Global instance
_connectivity_checker = ConnectivityChecker()


def get_connectivity_checker():
    """Get the global connectivity checker instance"""
    return _connectivity_checker


def check_connectivity():
    """Quick check of current connectivity"""
    return _connectivity_checker.get_status()


def is_online():
    """Return True if device has internet, False otherwise"""
    return _connectivity_checker.get_status()["online"]


# Example usage in Flask
def require_connectivity_check(f):
    """Decorator to check connectivity before request"""
    @wraps(f)
    def decorated(*args, **kwargs):
        status = check_connectivity()
        # Continue regardless of connectivity
        # (Flask route should handle both modes)
        return f(*args, **kwargs)
    return decorated
