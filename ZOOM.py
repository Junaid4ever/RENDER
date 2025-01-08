from flask import Flask, render_template_string, request
import asyncio
from playwright.async_api import async_playwright
import subprocess
import sys
import threading

app = Flask(__name__)

# Install dependencies
def install_dependencies():
    try:
        # Install playwright without its dependencies
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright==1.23.1', '--no-deps'])
        # Install playwright dependencies
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        # Install compatible pyee version and other dependencies
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyee==8.2.2'])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print("Error installing dependencies:", e)
        sys.exit(1)

install_dependencies()

# HTML Template with improved styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zoom Meeting Automation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 800px;
            margin: 50px auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #333333;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555555;
        }
        input[type="text"], input[type="number"], input[type="password"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #dddddd;
            border-radius: 4px;
        }
        button {
            display: block;
            width: 100%;
            padding: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        .members {
            margin-top: 20px;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 4px;
        }
        .error {
            color: red;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zoom Meeting Automation</h1>
        <form method="POST" action="/">
            <label for="meetingcode">Meeting Code:</label>
            <input type="text" id="meetingcode" name="meetingcode" required>
            <label for="passcode">Passcode:</label>
            <input type="password" id="passcode" name="passcode" required>
            <label for="number">Number of Members:</label>
            <input type="number" id="number" name="number" required>
            <label for="waittime">Wait Time (seconds):</label>
            <input type="number" id="waittime" name="waittime" required>
            <button type="submit">Start Automation</button>
        </form>
        <div class="members">
            <h3>Members Added:</h3>
            <ul id="member-list">
                {% for member in members %}
                <li>{{ member }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Flask Route
@app.route("/", methods=["GET", "POST"])
def index():
    members = []
    error_message = ""
    if request.method == "POST":
        meetingcode = request.form["meetingcode"]
        passcode = request.form["passcode"]
        number = int(request.form["number"])
        wait_time = int(request.form["waittime"])

        try:
            # Run automation in a background thread
            threading.Thread(target=lambda: asyncio.run(start_meetings(number, meetingcode, passcode, wait_time, members))).start()
        except Exception as e:
            error_message = f"Error: {str(e)}"

    return render_template_string(HTML_TEMPLATE, members=members, error_message=error_message)

# Generate unique member name
def generate_unique_user():
    from random import randint
    return f"User_{randint(1000, 9999)}"

# Playwright Automation
async def start_meetings(number, meetingcode, passcode, wait_time, members):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        tasks = [join_meeting(browser, meetingcode, passcode, wait_time, members) for _ in range(number)]
        await asyncio.gather(*tasks)
        await browser.close()

async def join_meeting(browser, meetingcode, passcode, wait_time, members):
    user = generate_unique_user()
    members.append(user)  # Add to member list for display
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(f"https://zoom.us/wc/join/{meetingcode}")
        await page.fill("input[type='text']", user)
        await page.fill("input[type='password']", passcode)
        await page.click("button.preview-join-button")
        await asyncio.sleep(wait_time)
    except Exception as e:
        print(f"Error for {user}: {e}")
    finally:
        await context.close()

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
