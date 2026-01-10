import asyncio
import json
from pathlib import Path
import time
import aiofiles
import httpx
from typing import Dict, Any, List

from pydantic import BaseModel
from app.utils import time_async


class NSEClient:
    BASE_URL = "https://www.nseindia.com"
    API_PATH = "/api/NextApi/apiClient/GetQuoteApi"

    def __init__(self, timeout: float = 10.0):
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=self._base_headers(),
        )
        self._warmed = False

    @staticmethod
    def _base_headers() -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }

    def _warmup_headers(self) -> Dict[str, str]:
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
        }

    def _api_headers(self, symbol: str) -> Dict[str, str]:
        return {
            "Accept": "*/*",
            "Referer": f"{self.BASE_URL}/get-quote/equity/{symbol}",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }

    async def warm_up(self) -> None:
        if self._warmed:
            return
        r = await self.client.get(
            self.BASE_URL,
            headers=self._warmup_headers(),
        )

        if r.status_code != 200:
            raise RuntimeError(
                f"NSE warmup failed: {r.status_code}"
            )

        self._warmed = True

    async def fetch_quote(self, symbol: str) -> Dict[str, Any]:
        await self.warm_up()

        params = {
            "functionName": "getSymbolData",
            "marketType": "N",
            "series": "EQ",
            "symbol": symbol,
        }

        r = await self.client.get(
            f"{self.BASE_URL}{self.API_PATH}",
            params=params,
            headers=self._api_headers(symbol),
        )

        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.client.aclose()

class NSEData(BaseModel):
    close : float
    day_change_pct : float 
    year_high : float
    year_low : float 
    total_volume : float
    delivery_volume : float
    delivery_pct : float

async def fetch_eod_data(
    symbols: List[str],
    *,
    delay_seconds: float = 0.0,
) -> Dict[str, NSEData]:
    """
    Fetch NSE EOD data for a list of symbols.

    Returns:
        {
            "TCS": NSEData(...),
            "INFY": NSEData(...),
        }
    """
    client = NSEClient()
    results: Dict[str, NSEData] = {}

    try:
        for symbol in symbols:
            try:
                raw = await client.fetch_quote(symbol)

                equity_response = raw.get("equityResponse")
                if not equity_response:
                    raise ValueError("Missing equityResponse")

                eq = equity_response[0]

                nse_data = NSEData(
                    close=eq["metaData"]["closePrice"],
                    day_change_pct=eq["metaData"]["pChange"],
                    year_high=eq["priceInfo"]["yearHigh"],
                    year_low=eq["priceInfo"]["yearLow"],
                    total_volume=eq["tradeInfo"]["quantitytraded"],
                    delivery_volume=eq["tradeInfo"]["deliveryquantity"],
                    delivery_pct=eq["tradeInfo"]["deliveryToTradedQuantity"],
                )

                results[symbol] = nse_data

                # NSE politeness
                await asyncio.sleep(delay_seconds)

            except httpx.HTTPStatusError as e:
                print(f"⚠️ NSE HTTP error for {symbol}: {e.response.status_code}")

            except httpx.RequestError as e:
                print(f"🌐 Network error for {symbol}: {e}")

            except KeyError as e:
                print(f"🧩 Schema error for {symbol}: missing {e}")

            except ValueError as e:
                print(f"❌ Data error for {symbol}: {e}")

            except Exception as e:
                print(f"🔥 Unexpected error for {symbol}: {e}")

    finally:
        await client.close()

    return results

if __name__ == '__main__':
    @time_async("NSE fetch (3 symbols)")
    async def main():
        data = await fetch_eod_data(["TCS", "INFY", "RELIANCE"])
        for sym, d in data.items():
            print(sym, d.model_dump())

    asyncio.run(main())