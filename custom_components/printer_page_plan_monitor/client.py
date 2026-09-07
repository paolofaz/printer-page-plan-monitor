from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import aiohttp

from .const import PRODUCT_USAGE_PATH


@dataclass
class PrinterData:
    subscription_impressions: int
    ink_black: int | None
    ink_cyan: int | None
    ink_magenta: int | None
    ink_yellow: int | None


class LEDMPrinterClient:
    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._host = host.strip().rstrip("/")
        if not self._host.startswith(("http://", "https://")):
            self._host = f"http://{self._host}"

    @property
    def url(self) -> str:
        return f"{self._host}{PRODUCT_USAGE_PATH}"

    async def async_get_data(self) -> PrinterData:
        async with asyncio.timeout(10):
            async with self._session.get(self.url) as response:
                response.raise_for_status()
                text = await response.text()

        root = ET.fromstring(text)
        subscription = None
        inks: dict[str, int | None] = {
            "Black": None,
            "Cyan": None,
            "Magenta": None,
            "Yellow": None,
        }

        for elem in root.iter():
            local = elem.tag.rsplit("}", 1)[-1]
            if local == "SubscriptionImpressions" and elem.text:
                subscription = int(elem.text)

        for consumable in root.iter():
            if consumable.tag.rsplit("}", 1)[-1] != "Consumable":
                continue
            color = None
            level = None
            for child in consumable.iter():
                local = child.tag.rsplit("}", 1)[-1]
                if local == "MarkerColor" and child.text:
                    color = child.text.strip()
                elif local == "ConsumableRawPercentageLevelRemaining" and child.text:
                    level = int(child.text)
            if color in inks:
                inks[color] = level

        if subscription is None:
            raise ValueError("SubscriptionImpressions not found")

        return PrinterData(
            subscription_impressions=subscription,
            ink_black=inks["Black"],
            ink_cyan=inks["Cyan"],
            ink_magenta=inks["Magenta"],
            ink_yellow=inks["Yellow"],
        )
