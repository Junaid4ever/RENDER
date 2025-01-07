from quart import Quart, request, render_template, jsonify
import asyncio
from playwright.async_api import async_playwright
import random
import nest_asyncio
import indian_names

nest_asyncio.apply()

app = Quart(__name__)

# Hardcoded password for verifying
HARDCODED_PASSWORD = "Fly@1234"

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

        await page.wait_for_selector('button.zm-btn.join-audio-by-voip__join-btn.zm-btn--primary.zm-btn__outline--white.zm-btn--lg', timeout=300000)
        mic_button_locator = await page.query_selector('button.zm-btn.join-audio-by-voip__join-btn.zm-btn--primary.zm-btn__outline--white.zm-btn--lg')
        if mic_button_locator:
            await mic_button_locator.evaluate_handle('node => node.click()')
            print(f"{user} successfully joined audio.")
        
        print(f"{user} will remain in the meeting for {wait_time} seconds ...")
        await asyncio.sleep(wait_time)
    except Exception as e:
        print(f"An error occurred: {e}")

    await context.close()

@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        # Get form data
        password = await request.form.get("password")
        meetingcode = await request.form.get("meetingcode")
        passcode = await request.form.get("passcode")
        number = int(await request.form.get("number"))
        wait_time = 7200  # Fixed wait time in seconds

        # Verify password
        if not verify_password(password):
            return "Invalid Password. Please try again."

        # Run the async script
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--use-fake-ui-for-media-stream',
                    '--use-fake-device-for-media-stream'
                ]
            )

            tasks = []
            for _ in range(number):
                task = asyncio.create_task(join_meeting(browser, wait_time, meetingcode, passcode))
                tasks.append(task)

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except KeyboardInterrupt:
                for task in tasks:
                    task.cancel()

            await browser.close()

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
