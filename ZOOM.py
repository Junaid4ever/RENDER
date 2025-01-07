from quart import Quart, request, render_template, jsonify
import asyncio
from playwright.async_api import async_playwright
import nest_asyncio

nest_asyncio.apply()

app = Quart(__name__)

# Hardcoded password for verification
HARDCODED_PASSWORD = "Fly@1234"

def verify_password(password):
    return password == HARDCODED_PASSWORD

async def join_meeting(meetingcode, passcode, number):
    # Simulated meeting joining logic
    print(f"Joining meeting {meetingcode} with passcode {passcode} for {number} users.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(f"http://app.zoom.us/wc/join/{meetingcode}")
            # Add any other Zoom interaction here
            print(f"Successfully joined the Zoom meeting {meetingcode}")
        except Exception as e:
            print(f"Error while joining the meeting: {e}")
        await browser.close()

@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        # Get form data
        password = await request.form.get("password")
        meetingcode = await request.form.get("meetingcode")
        passcode = await request.form.get("passcode")
        number = int(await request.form.get("number"))

        # Verify password
        if not verify_password(password):
            return "Invalid Password. Please try again."

        # Run the async script
        await join_meeting(meetingcode, passcode, number)

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

if __name__ == "__main__":
    app.run(debug=True)
