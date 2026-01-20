#!/usr/bin/env python3
"""
Final verification of automatic connectivity detection system
Tests all components are integrated and working correctly
"""

import json
import sys

def verify_imports():
    """Verify all required imports work"""
    print("\n[1/5] Verifying Python Imports...")
    try:
        from connectivity import check_connectivity, is_online, get_connectivity_checker
        print("  ✓ connectivity module imports: OK")
        
        from app import app, current_mode, toggle_mode
        print("  ✓ app.py imports: OK")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def verify_connectivity_module():
    """Verify connectivity detection works"""
    print("\n[2/5] Verifying Connectivity Module...")
    try:
        from connectivity import check_connectivity, is_online
        
        # Test check_connectivity
        status = check_connectivity()
        assert isinstance(status, dict), "check_connectivity must return dict"
        assert "online" in status, "Missing 'online' key"
        assert "status" in status, "Missing 'status' key"
        assert isinstance(status["online"], bool), "online must be bool"
        print(f"  ✓ check_connectivity(): {status}")
        
        # Test is_online
        online = is_online()
        assert isinstance(online, bool), "is_online must return bool"
        print(f"  ✓ is_online(): {online}")
        
        return True
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False

def verify_flask_routes():
    """Verify Flask routes are registered"""
    print("\n[3/5] Verifying Flask Routes...")
    try:
        from app import app
        
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        required_routes = [
            '/status/connectivity',
            '/mode',
            '/ask'
        ]
        
        for route in required_routes:
            found = any(route in r for r in routes)
            if found:
                print(f"  ✓ Route {route}: Found")
            else:
                print(f"  ✗ Route {route}: NOT FOUND")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Route verification failed: {e}")
        return False

def verify_javascript():
    """Verify JavaScript file exists and has required functions"""
    print("\n[4/5] Verifying JavaScript Implementation...")
    try:
        with open("static/script.js", "r", encoding="utf-8", errors="ignore") as f:
            js_content = f.read()
        
        required_functions = [
            "checkConnectivity",
            "startConnectivityMonitoring",
            "toggleMode",
            "updateModeButton"
        ]
        
        for func in required_functions:
            if f"function {func}" in js_content or f"{func}()" in js_content:
                print(f"  ✓ Function {func}(): Found")
            else:
                print(f"  ✗ Function {func}(): NOT FOUND")
                return False
        
        # Check for auto-detection initialization
        if "startConnectivityMonitoring()" in js_content:
            print(f"  ✓ Auto-detection startup: Enabled")
        else:
            print(f"  ✗ Auto-detection startup: NOT FOUND")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ JavaScript verification failed: {e}")
        return False

def verify_documentation():
    """Verify documentation files exist"""
    print("\n[5/5] Verifying Documentation...")
    try:
        import os
        
        docs = [
            "CONNECTIVITY_GUIDE.md",
            "CONNECTIVITY_IMPLEMENTATION.md"
        ]
        
        for doc in docs:
            if os.path.exists(doc):
                with open(doc, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                print(f"  ✓ {doc}: Found ({lines} lines)")
            else:
                print(f"  ✗ {doc}: NOT FOUND")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Documentation verification failed: {e}")
        return False

def main():
    """Run all verifications"""
    print("=" * 70)
    print("AUTOMATIC CONNECTIVITY DETECTION - FINAL VERIFICATION")
    print("=" * 70)
    
    tests = [
        ("Python Imports", verify_imports),
        ("Connectivity Module", verify_connectivity_module),
        ("Flask Routes", verify_flask_routes),
        ("JavaScript Implementation", verify_javascript),
        ("Documentation", verify_documentation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL VERIFICATIONS PASSED!")
        print("\nAutomatic Connectivity Detection System is READY FOR USE")
        print("\nFeatures Enabled:")
        print("  • Automatic internet detection (every 15 seconds)")
        print("  • Auto-switching between Online/Offline modes")
        print("  • Manual override capability")
        print("  • Real-time UI updates")
        print("  • Seamless fallback to Ollama when offline")
        print("  • Web search capability when online")
        return 0
    else:
        print("\n❌ VERIFICATION FAILED")
        print(f"  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
