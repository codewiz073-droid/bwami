"""
Test the new sophisticated routing architecture
"""
import sys
sys.path.insert(0, '.')

from request_classifier import RequestClassifier

def test_classification():
    """Test request classification routing"""
    classifier = RequestClassifier()
    
    test_cases = [
        ("solve x^2 + 2x + 1 = 0", "math"),
        ("write an essay about climate change", "essay"),
        ("create a python function that calculates fibonacci", "code"),
        ("translate hello to spanish", "translation"),
        ("write a creative story about dragons", "creative"),
        ("compare pros and cons of remote work", "analysis"),
        ("hello, how are you?", "greeting"),
        ("what are your capabilities?", "capabilities"),
    ]
    
    print("=" * 60)
    print("TESTING REQUEST CLASSIFICATION ROUTING")
    print("=" * 60)
    
    for query, expected_type in test_cases:
        detected = classifier.classify(query)
        status = "✓ PASS" if detected == expected_type else "✗ FAIL"
        print(f"\n{status}")
        print(f"  Query: {query}")
        print(f"  Expected: {expected_type}")
        print(f"  Detected: {detected}")
    
    print("\n" + "=" * 60)
    print("ROUTING LAYER 2 DETECTION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_classification()
