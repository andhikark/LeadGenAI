import nodriver as uc

async def test_cookie_session():
    browser = await uc.start(
        headless=False,
        no_sandbox=True,
    )
    await browser.cookies.load("linkedin_headless_session.dat")
    page = await browser.get("https://www.linkedin.com")
    await page.wait(10)

uc.loop().run_until_complete(test_cookie_session())
