import requests
import json

def generate(prompt, url="http://127.0.0.1:1234/v1/chat/completions"):
    payload = {
        "model": "google/gemma-4-e4b",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(url, json=payload)

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"Non-JSON response from server: {response.text}")

    if "choices" not in data:
        raise RuntimeError(f"LLM error response: {data}")

    return data["choices"][0]["message"]["content"]