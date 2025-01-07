import subprocess
import sys
import os
import asyncio
import random
import nest_asyncio
from flask import Flask, request
from playwright.async_api import async_playwright
import indian_names

# Install dependencies and Playwright
def install_dependencies():
    try:
        # Install Python dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Install Playwright and browsers (Chromium)
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Dependencies and Playwright installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

# Ensure dependencies are installed when the script is run
install_dependencies()

# Flask setup
nest_asyncio.apply()
app = Flask(__name__)

# Hardcoded password for verification
HARDCODED_PASSWORD = "Fly@1234"

# Verify password function
def verify_password(password):
    return password == HARDCODED_PASSWORD

# Generate a unique user name
def generate_unique_user():
    first_name = indian_names.get_first_name()
    last_name = indian_names.get_last_name()
    return f"{first_name} {last_name}"

# Meeting joining logic using Playwright
async def join_meeting(browser, wait_time, meetingcode, passcode):
    user = generate_unique_user()
    print(f"{user} attempting to join with Chromium.")
    
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(f'http://app.zoom.us/wc/join/{meetingcode}', timeout=200000)

        for _ in range(5):
            await page.evaluate('() => { navigator.mediaDevices.getUserMedia({ audio: true, video: true }); }')

        try:
            await page.click('//button[@id="onetrust-accept-btn-handler"]', timeout=5000)
        except Exception:
            pass

        try:
            await page.click('//button[@id="wc_agree1"]', timeout=5000)
        except Exception:
            pass

        try:
            await page.wait_for_selector('input[type="text"]', timeout=200000)
            await page.fill('input[type="text"]', user)

            password_field_exists = await page.query_selector('input[type="password"]')
            if password_field_exists:
                await page.fill('input[type="password"]', passcode)
                join_button = await page.wait_for_selector('button.preview-join-button', timeout=200000)
                await join_button.click()
            else:
                join_button = await page.wait_for_selector('button.preview-join-button', timeout=200000)
                await join_button.click()
        except Exception:
            pass

        print(f"{user} will remain in the meeting for {wait_time} seconds ...")
        await asyncio.sleep(wait_time)

    except Exception as e:
        print(f"An error occurred: {e}")

    await context.close()

# Flask route for receiving form input
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get form data
        password = request.form.get("password")
        meetingcode = request.form.get("meetingcode")
        passcode = request.form.get("passcode")
        number = int(request.form.get("number"))
        wait_time = 7200  # Fixed wait time in seconds (you can modify this as needed)

        # Verify password
        if not verify_password(password):
            return "Invalid Password. Please try again."

        # Run the async script
        asyncio.run(start_meetings(number, meetingcode, passcode, wait_time))

        return f"Meeting joined successfully with {number} users!"

    # Render HTML form
    return """
    <form method="post">
        <label for="password">Enter Password:</label>
        <input type="password" id="password" name="password" required><br><br>
        <label for="meetingcode">Meeting ID:</label>
        <input type="text" id="meetingcode" name="meetingcode" required><br><br>
        <label for="passcode">Meeting Passcode:</label>
        <input type="text" id="passcode" name="passcode" required><br><br>
        <label for="number">Number of Users:</label>
        <input type="number" id="number" name="number" min="1" required><br><br>
        <button type="submit">Submit</button>
    </form>
    """

# Function to start multiple meetings
async def start_meetings(number, meetingcode, passcode, wait_time):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
            ]
        )

        tasks = [
            join_meeting(browser, wait_time, meetingcode, passcode)
            for _ in range(number)
        ]

        await asyncio.gather(*tasks)
        await browser.close()

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get the port from environment
    app.run(host="0.0.0.0", port=port, debug=True)
