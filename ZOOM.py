!pip install indian_names

import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
import nest_asyncio
import indian_names

nest_asyncio.apply()

# Flag to indicate whether the script is running
running = True

# Event to synchronize threads
join_audio_event = asyncio.Event()

# Hardcoded password (for verifying)
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
    global join_audio_event
    global running

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

        # Ensure microphone permissions are enabled
        try:
            for _ in range(5):
                await page.evaluate('() => { navigator.mediaDevices.getUserMedia({ audio: true, video: true }); }')
                await asyncio.sleep(2)
            print(f"{user} microphone permissions enabled.")
        except Exception as e:
            print(f"{user} failed to enable microphone permissions. {e}")

        # Try to click the 'join audio by computer' button once
        retry_count = 5
        while retry_count > 0:
            try:
                await page.wait_for_selector('button.zm-btn.join-audio-by-voip__join-btn.zm-btn--primary.zm-btn__outline--white.zm-btn--lg', timeout=300000)
                mic_button_locator = await page.query_selector('button.zm-btn.join-audio-by-voip__join-btn.zm-btn--primary.zm-btn__outline--white.zm-btn--lg')
                if mic_button_locator:
                    await mic_button_locator.evaluate_handle('node => node.click()')
                    print(f"{user} successfully joined audio.")
                    join_audio_event.set()
                    break
                else:
                    raise Exception("Join audio button not found.")
            except Exception as e:
                print(f"Attempt {5 - retry_count + 1}: {user} failed to join audio. Retrying... {e}")
                retry_count -= 1
                await asyncio.sleep(2)

        if retry_count == 0:
            print(f"{user} failed to join audio after multiple attempts.")

        print(f"{user} will remain in the meeting for {wait_time} seconds ...")
        try:
            await asyncio.sleep(wait_time)
        except asyncio.CancelledError:
            print(f"{user} has been interrupted and will exit.")
    except Exception as e:
        print(f"An error occurred: {e}")

    await context.close()

async def main():
    global running
    
    # Prompt user for input
    number = int(input("Enter number of users: "))
    meetingcode = input("Enter the meeting ID: ")
    passcode = input("Enter the meeting password: ")
    wait_time = 7200  # Fixed wait time in seconds (you can prompt the user for this too if needed)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[ 
                '--no-sandbox', 
                '--disable-dev-shm-usage', 
                '--use-fake-ui-for-media-stream', 
                '--use-fake-device-for-media-stream', 
                f'--disk-cache-size={random.randint(200, 5000)}000000', 
                f'--max-active-views={random.randint(5, 1000)}'  
            ]
        )

        tasks = []
        for _ in range(number):
            task = asyncio.create_task(join_meeting(browser, wait_time, meetingcode, passcode))
            tasks.append(task)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            running = False
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        await browser.close()

if __name__ == "__main__":
    password = input("Enter the script password: ")

    if verify_password(password):
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            running = False
            print("Script interrupted by user.")
    else:
        print("Wrong password. GET LOST.")
