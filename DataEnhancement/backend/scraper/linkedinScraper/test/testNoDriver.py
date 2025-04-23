import nodriver as uc

async def test():
    print("🚀 Launching Chrome via Nodriver...")
    browser = await uc.start()
    page = await browser.get("https://example.com")
    html = await page.get_content()
    print("✅ Page loaded successfully!")
    print(html[:500])

    # Correctly close the tab
    await page.close()

if __name__ == "__main__":
    uc.loop().run_until_complete(test())
