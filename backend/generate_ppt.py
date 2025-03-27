import requests
import os
url = "https://api.slidespeak.co/api/v1/presentation/generate"
headers = {
    "Content-Type": "application/json",
    "x-api-key": os.environ.get("TOGETHER_API_KEY")
}
payload = {
    "plain_text": "Key moments in the French Revolution",
    "length": 6,
    "template": "default",
    "language": "ORIGINAL",
    "fetch_images": True,
    "tone": "default",
    "verbosity": "standard",
    "custom_user_instructions": "Make sure to mention the storming of the Bastille"
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())