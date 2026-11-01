import os
import ssl
from pathlib import Path

import httpx

# Load SARVAM_API_KEY from this project's .env into the environment if not already set.
for line in Path(__file__).with_name(".env").read_text(encoding="utf-8").splitlines():
    name, separator, value = line.partition("=")
    if separator and name.strip() == "SARVAM_API_KEY":
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))

api_key = os.environ.get("SARVAM_API_KEY")
if not api_key:
    raise SystemExit("Add your Sarvam API key to .env, then run this script again.")

from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key=api_key,
    httpx_client=httpx.Client(verify=ssl.create_default_context()),
)
response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(response.choices[0].message.content)
