from __future__ import annotations

import asyncio
from typing import Any

from madxka.http import MadxkaHttp


CURRENCY_ROBUX = 1


def purchase_payload(item: dict[str, Any]) -> dict[str, Any]:
    asset_id = int(item.get("id") or 0)
    seller = item.get("creatorTargetId")
    if seller is None and isinstance(item.get("lowestSellerData"), dict):
        seller = item["lowestSellerData"].get("sellerId")
    price = item.get("price")
    if price is None:
        price = item.get("lowestPrice")
    if price is None:
        price = 0
    return {
        "assetId": asset_id,
        "expectedPrice": int(price),
        "expectedSellerId": int(seller or 1),
        "userAssetId": None,
        "expectedCurrency": CURRENCY_ROBUX,
    }


class EconomyService:
    def __init__(self, http: MadxkaHttp) -> None:
        self.http = http
        self._user: dict[str, Any] | None = None

    async def session_user(self, *, refresh: bool = False) -> dict[str, Any]:
        if self._user is not None and not refresh:
            return self._user
        self._user = await self.http.authenticated_user()
        return self._user

    async def balance(self) -> dict[str, Any]:
        user = await self.session_user()
        uid = int(user.get("id") or 0)
        currency = await self.http.user_currency(uid)
        return {
            "user": user,
            "robux": int(currency.get("robux") or 0),
            "tickets": int(currency.get("tickets") or 0),
        }

    async def purchase(self, item: dict[str, Any]) -> dict[str, Any]:
        asset_id = int(item.get("id") or 0)
        if not asset_id:
            raise ValueError("missing asset id")
        body = purchase_payload(item)
        result = await self.http.purchase_product(asset_id, body)
        return {
            "request": body,
            "result": result,
            "purchased": bool(result.get("purchased")),
            "reason": str(result.get("reason") or ""),
        }

    async def purchase_all_free(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        bought: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        failed: list[tuple[dict[str, Any], str]] = []

        for item in items:
            asset_id = int(item.get("id") or 0)
            name = str(item.get("name") or asset_id)
            try:
                outcome = await self.purchase(item)
            except Exception as e:
                err = str(e)
                if "already owned" in err.lower():
                    skipped.append(item)
                else:
                    failed.append((item, err))
                await asyncio.sleep(0.12)
                continue

            if outcome.get("purchased"):
                bought.append(item)
            else:
                reason = str(outcome.get("reason") or "")
                if "already owned" in reason.lower():
                    skipped.append(item)
                else:
                    failed.append((item, reason or "purchase declined"))

            await asyncio.sleep(0.12)

        return {
            "scanned": len(items),
            "bought": bought,
            "skipped": skipped,
            "failed": failed,
        }
