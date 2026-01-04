import logging
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

class BaseAutomationBot:
    """
    Clase base para todos los bots de automatización (GitHub, Render, Neon).
    Maneja el ciclo de vida de Playwright.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def start(self):
        """Inicia el navegador"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        logger.info(f"[{self.__class__.__name__}] Browser started (Headless: {self.headless})")

    async def stop(self):
        """Cierra el navegador y limpia recursos"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"[{self.__class__.__name__}] Browser stopped")

    async def screenshot(self, path: str):
        """Toma un screenshot para depuración"""
        if self.page:
            await self.page.screenshot(path=path)

    async def wait_and_click(self, selector: str, timeout: int = 5000):
        """Espera y hace clic en un elemento"""
        await self.page.wait_for_selector(selector, state='visible', timeout=timeout)
        await self.page.click(selector)

    async def wait_and_fill(self, selector: str, text: str, timeout: int = 5000):
        """Espera y rellena un campo"""
        await self.page.wait_for_selector(selector, state='visible', timeout=timeout)
        await self.page.fill(selector, text)
