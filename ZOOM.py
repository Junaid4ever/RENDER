import subprocess
import sys
from flask import Flask, request, jsonify
import asyncio
import random
from playwright.async_api import async_playwright
import nest_asyncio
import os

nest_asyncio.apply()

app = Flask(__name__)

# Function to install dependencies
def install_dependencies():
    try:
        # Install playwright without its dependencies
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright==1.23.1', '--no-deps'])
        # Install playwright dependencies
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        # Install compatible version of pyee
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyee==8.2.2'])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print("Error installing dependencies:", e)
        sys.exit(1)

# Install dependencies before starting the app
install_dependencies()

# Hardcoded password for verification (if needed, can be modified dynamically)
HARDCODED_PASSWORD = "Fly@1234"

# Generate unique user names
def generate_unique_user():
    first_names = ["John", "Jane", "Alice", "Bob", "Chris"]
    last_names = ["Smith", "Doe", "Brown", "Johnson", "Lee"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Dynamic list to store joined members
joined_members = []

# Asynchronous function to join a meeting
async def join_meeting(browser, meeting_id, passcode, wait_time, member_name):
    try:
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to Zoom meeting join page
        print(f"{member_name} is attempting to join meeting {meeting_id}...")
        await page.goto(f'https://zoom.us/wc/join/{meeting_id}', timeout=60000)

        # Fill in the name and passcode, then join the meeting
        await page.fill('input[name="name"]', member_name)
        if passcode:
            await page.fill('input[name="password"]', passcode)
        await page.click('button[type="submit"]')

        # Wait for the meeting to stabilize
        await asyncio.sleep(wait_time)

        # Close context after waiting
        print(f"{member_name} stayed in the meeting for {wait_time} seconds.")
        joined_members.append(member_name)
        await context.close()

    except Exception as e:
        print(f"Error for {member_name}: {e}")

# Route for the main page
@app.route("/", methods=["GET", "POST"])
def index():
    global joined_members
    if request.method == "POST":
        # Get form data
        meeting_id = request.form.get("meeting_id")
        passcode = request.form.get("passcode")
        num_members = int(request.form.get("num_members"))
        wait_time = int(request.form.get("wait_time", 120))  # Wait time in seconds

        if not meeting_id or num_members < 1:
            return "Invalid meeting details. Please check your inputs."

        joined_members = []  # Reset the members list

        # Start the meeting join automation
        asyncio.run(start_meetings(meeting_id, passcode, num_members, wait_time))
        return jsonify({"status": "success", "members_joined": joined_members})

    # Render HTML Form
    return """
    <html>
        <head>
            <title>Zoom Meeting Automation</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; }
                h1 { color: #4CAF50; }
                form { background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                label { display: block; margin: 10px 0 5px; }
                input, button { padding: 10px; margin: 10px 0; width: 100%; }
                button { background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #45a049; }
                .members { margin-top: 20px; padding: 10px; background-color: #e7f3e7; border-left: 6px solid #4CAF50; }
            </style>
        </head>
        <body>
            <h1>Zoom Meeting Automation</h1>
            <form method="post">
                <label for="meeting_id">Meeting ID:</label>
                <input type="text" id="meeting_id" name="meeting_id" required>
                <label for="passcode">Meeting Passcode:</label>
                <input type="text" id="passcode" name="passcode">
                <label for="num_members">Number of Members:</label>
                <input type="number" id="num_members" name="num_members" required min="1">
                <label for="wait_time">Wait Time (seconds):</label>
                <input type="number" id="wait_time" name="wait_time" value="120">
                <button type="submit">Start Automation</button>
            </form>
            <div class="members">
                <h2>Joined Members:</h2>
                <ul id="members_list"></ul>
            </div>
            <script>
                setInterval(async function() {
                    const response = await fetch('/get_members');
                    const data = await response.json();
                    const membersList = document.getElementById('members_list');
                    membersList.innerHTML = '';
                    data.members.forEach(member => {
                        const li = document.createElement('li');
                        li.textContent = member;
                        membersList.appendChild(li);
                    });
                }, 5000);  // Refresh every 5 seconds
            </script>
        </body>
    </html>
    """

# Asynchronous function to start meetings
async def start_meetings(meeting_id, passcode, num_members, wait_time):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        tasks = []
        for i in range(num_members):
            member_name = generate_unique_user()
            tasks.append(join_meeting(browser, meeting_id, passcode, wait_time, member_name))
        await asyncio.gather(*tasks)
        await browser.close()

# Route to get the list of joined members
@app.route("/get_members")
def get_members():
    return jsonify({"members": joined_members})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
