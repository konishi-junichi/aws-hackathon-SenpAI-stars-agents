#!/usr/bin/env python3
import requests
import json

def test_agent():
    url = "http://localhost:8080"
    
    test_cases = [
        {"prompt": "Hello! Can you introduce yourself?"},
        {"prompt": "Calculate 15 * 7 + 3"},
        {"prompt": "Tell me a joke!"},
        {"prompt": "What's the square root of 144?"}
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: {test['prompt']}")
        
        try:
            response = requests.post(url, json=test, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_agent()