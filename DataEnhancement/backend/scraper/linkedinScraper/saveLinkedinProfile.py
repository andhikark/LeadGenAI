import nodriver as uc

async def save_cookies_from_gui_login():
    browser = await uc.start(
        headless=False,  # GUI mode so you can log in manually
        no_sandbox=True,
        browser_executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )

    await browser.get("https://www.linkedin.com/login")
    input("🔐 Log in manually in the Chrome window, then press ENTER here to save cookies...")

    await browser.cookies.save("linkedin_headless_session.dat")
    print("✅ Cookies saved to 'linkedin_headless_session.dat'")

if __name__ == "__main__":
    uc.loop().run_until_complete(save_cookies_from_gui_login())
