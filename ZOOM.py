import subprocess
import sys
import asyncio
import random
from flask import Flask, request
from playwright.async_api import async_playwright
import nest_asyncio
import os
import indian_names

nest_asyncio.apply()

app = Flask(__name__)

# Hardcoded password for verification
HARDCODED_PASSWORD = "Fly@1234"

# Store member names to display on the webpage
member_names = []

# Dependency installation
def install_dependencies():
    try:
        # Install playwright without its dependencies
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright==1.23.1', '--no-deps'])
        # Install playwright dependencies
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        # Install specific compatible version of pyee
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyee==9.0.4'])
        # Install indian_names
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'indian_names'])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print("Error installing dependencies:", e)
        sys.exit(1)


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
    member_names.append(user)  # Add user to member names list
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


@app.route("/", methods=["GET", "POST"])
def index():
    global member_names
    member_names = []  # Reset member names list for each new session

    if request.method == "POST":
        password = request.form.get("password")
        meetingcode = request.form.get("meetingcode")
        passcode = request.form.get("passcode")
        number = int(request.form.get("number"))

        print(f"Received form data: Password={password}, MeetingCode={meetingcode}, Passcode={passcode}, Number={number}")

        if not verify_password(password):
            return """
            <div style="text-align: center; font-family: Arial, sans-serif; color: red;">
                <h2>Invalid Password!</h2>
                <a href="/" style="color: #007bff; text-decoration: none;">Go Back</a>
            </div>
            """

        asyncio.run(start_meetings(number, meetingcode, passcode, 7200))

        return f"""
        <div style="text-align: center; font-family: Arial, sans-serif; color: green;">
            <h2>Meeting joined successfully!</h2>
            <p>Members added to the meeting:</p>
            <ul>
                {''.join(f'<li>{name}</li>' for name in member_names)}
            </ul>
            <a href="/" style="color: #007bff; text-decoration: none;">Go Back</a>
        </div>
        """

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zoom Meeting Automation</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(to right, #6a11cb, #2575fc);
                color: #fff;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .form-container {
                background: rgba(0, 0, 0, 0.7);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                width: 400px;
                text-align: center;
            }
            .form-container h1 {
                margin-bottom: 20px;
                color: #00d9ff;
            }
            .form-container label {
                display: block;
                text-align: left;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .form-container input {
                width: 100%;
                padding: 10px;
                margin-bottom: 15px;
                border: none;
                border-radius: 5px;
                box-sizing: border-box;
            }
            .form-container input[type="password"],
            .form-container input[type="text"],
            .form-container input[type="number"] {
                background: #f3f3f3;
                color: #333;
            }
            .form-container button {
                width: 100%;
                padding: 10px;
                background: #00d9ff;
                border: none;
                border-radius: 5px;
                color: #333;
                font-weight: bold;
                cursor: pointer;
            }
            .form-container button:hover {
                background: #00c2e0;
            }
            a {
                color: #00d9ff;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="form-container">
            <h1>Zoom Meeting Automation</h1>
            <form method="post">
                <label for="password">Enter Password:</label>
                <input type="password" id="password" name="password" required>
                
                <label for="meetingcode">Meeting ID:</label>
                <input type="text" id="meetingcode" name="meetingcode" required>
                
                <label for="passcode">Meeting Passcode:</label>
                <input type="text" id="passcode" name="passcode" required>
                
                <label for="number">Number of Users:</label>
                <input type="number" id="number" name="number" min="1" required>
                
                <button type="submit">Submit</button>
            </form>
        </div>
    </body>
    </html>
    """


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


if __name__ == "__main__":
    install_dependencies()  # Install dependencies
    port = int(os.environ.get("PORT", 5000))  # Get the port from environment
    app.run(host="0.0.0.0", port=port, debug=True)
