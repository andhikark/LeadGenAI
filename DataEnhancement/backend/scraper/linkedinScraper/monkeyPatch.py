import nodriver as uc
from nodriver import cdp
from nodriver.core import tab as _tab

# Save original start so we can wrap it
_original_start = uc.start

async def _fixed_prepare_headless(self: _tab.Tab):
    if getattr(self, "_prep_headless_done", False):
        return

    resp = await self._send_oneshot(cdp.browser.get_version())
    if resp:
        await self._send_oneshot(
            cdp.network.set_user_agent_override(
                user_agent=resp[3].replace("Headless", "")
            )
        )
        self._prep_headless_done = True
        return

    raise RuntimeError("Headless UA patch failed")

# Patched start function
async def patched_start(*args, **kwargs):
    browser = await _original_start(*args, **kwargs)

    # Patch the initial main tab
    try:
        browser.main_tab._prepare_headless = _fixed_prepare_headless.__get__(browser.main_tab, _tab.Tab)
    except Exception:
        pass

    # Patch every tab created by .get()
    original_get = browser.get

    async def wrapped_get(*a, **kw):
        tab = await original_get(*a, **kw)
        try:
            tab._prepare_headless = _fixed_prepare_headless.__get__(tab, _tab.Tab)
        except Exception:
            pass
        return tab

    browser.get = wrapped_get
    return browser

# Apply global override
uc.start = patched_start
