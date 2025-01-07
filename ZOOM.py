from flask import Flask, request, jsonify
import asyncio
import random
from playwright.async_api import async_playwright
import nest_asyncio
import indian_names

# Apply nest_asyncio to allow asyncio to run in a thread
nest_asyncio.apply()

app = Flask(__name__)

# Hardcoded password
HARDCODED_PASSWORD = "Fly@1234"

# Verify password function
def verify_password(password):
    return password == HARDCODED_PASSWORD

# Generate a unique user name
def generate_unique_user():
    first_name = indian_names.get_first_name()
    last_name = indian_names.get_last_name()
    return f"{first_name} {last_name}"

async def join_meeting(browser, wait_time, meetingcode, passcode):
    user = generate_unique_user()
    print(f"{user} attempting to join with Chromium.")
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(f'http://app.zoom.us/wc/join/{meetingcode}', timeout=200000)
        await asyncio.sleep(wait_time)  # Simulate meeting attendance
        print(f"{user} completed meeting session.")
    except Exception as e:
        print(f"An error occurred for {user}: {e}")
    finally:
        await context.close()

@app.route("/run", methods=["POST"])
def run_script():
    data = request.json
    password = data.get("password")
    if not verify_password(password):
        return jsonify({"error": "Invalid password"}), 403

    number = int(data.get("number", 1))
    meetingcode = data.get("meetingcode")
    passcode = data.get("passcode")
    wait_time = int(data.get("wait_time", 7200))

    async def run_async():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            tasks = [
                asyncio.create_task(join_meeting(browser, wait_time, meetingcode, passcode))
                for _ in range(number)
            ]
            await asyncio.gather(*tasks)
            await browser.close()

    asyncio.run(run_async())
    return jsonify({"message": "Script started successfully!"})

@app.route("/")
def home():
    return "Welcome to the Zoom Automation Service!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
