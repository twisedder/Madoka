from __future__ import annotations

from typing import Any, TYPE_CHECKING

import discord

from bot.auth import can_use_wallet, deny_runner, deny_wallet, is_runner
from bot.embeds import build_inspect_pages, build_purchase_embed

if TYPE_CHECKING:
    from bot.client import MadokaBot


async def _check_runner(interaction: discord.Interaction, owner_id: int) -> bool:
    if is_runner(interaction, owner_id):
        return True
    await deny_runner(interaction)
    return False


async def _inspect_payload(
    bot: MadokaBot,
    item: dict[str, Any],
    *,
    show_wallet: bool = False,
) -> tuple[list[discord.Embed], dict[str, Any] | None, str | None]:
    item_id = int(item.get("id") or 0)
    stub = bot.cache.find_stub(item_id)
    thumb = await bot.api.asset_thumbnail(item_id)
    balance: dict[str, Any] | None = None
    if show_wallet:
        try:
            balance = await bot.economy.balance()
        except Exception:
            balance = None
    pages = build_inspect_pages(item, stub=stub, thumbnail=thumb, balance=balance)
    return pages, stub, thumb


class BuyButton(discord.ui.Button):
    def __init__(
        self,
        *,
        bot: MadokaBot,
        item: dict[str, Any],
        owner_id: int,
    ) -> None:
        price = item.get("price")
        if price is None:
            price = item.get("lowestPrice")
        label = "Buy" if price is None else f"Buy · {int(price):,} R$"
        if item.get("isForSale") is False:
            label = "Offsale"
        super().__init__(
            label=label[:80],
            style=discord.ButtonStyle.success,
            disabled=item.get("isForSale") is False,
            row=2,
        )
        self.bot = bot
        self.item = item
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await _check_runner(interaction, self.owner_id):
            return
        if not can_use_wallet(interaction, self.bot.settings):
            await deny_wallet(interaction)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            outcome = await self.bot.economy.purchase(self.item)
        except Exception as e:
            await interaction.followup.send(f"Purchase failed: `{e}`", ephemeral=True)
            return
        await interaction.followup.send(
            embed=build_purchase_embed(self.item, outcome),
            ephemeral=True,
        )


class InspectView(discord.ui.View):
    def __init__(
        self,
        bot: MadokaBot,
        *,
        item: dict[str, Any],
        pages: list[discord.Embed],
        owner_id: int,
        allow_buy: bool = True,
        timeout: float = 600,
    ) -> None:
        super().__init__(timeout=timeout)
        self.bot = bot
        self.item = item
        self.pages = pages
        self.owner_id = owner_id
        self.page = 0
        if allow_buy:
            self.add_item(BuyButton(bot=bot, item=item, owner_id=owner_id))
        self._sync()

    def _embed(self) -> discord.Embed:
        return self.pages[self.page]

    def _sync(self) -> None:
        total = len(self.pages)
        self.prev_btn.disabled = self.page <= 0 or total <= 1
        self.next_btn.disabled = self.page >= total - 1 or total <= 1
        self.page_btn.label = f"{self.page + 1}/{total}"
        self.page_btn.disabled = True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await _check_runner(interaction, self.owner_id):
            return
        if self.page <= 0:
            await interaction.response.defer()
            return
        self.page -= 1
        self._sync()
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.primary, row=1)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await _check_runner(interaction, self.owner_id):
            return
        await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await _check_runner(interaction, self.owner_id):
            return
        if self.page >= len(self.pages) - 1:
            await interaction.response.defer()
            return
        self.page += 1
        self._sync()
        await interaction.response.edit_message(embed=self._embed(), view=self)


class InspectPickView(discord.ui.View):
    def __init__(
        self,
        bot: MadokaBot,
        *,
        query: str,
        results: list[dict[str, Any]],
        owner_id: int,
        allow_buy: bool = False,
        timeout: float = 600,
    ) -> None:
        super().__init__(timeout=timeout)
        self.bot = bot
        self.query = query
        self.results = results
        self.owner_id = owner_id
        self.allow_buy = allow_buy
        options: list[discord.SelectOption] = []
        for item in results[:25]:
            item_id = int(item.get("id") or 0)
            name = str(item.get("name") or item_id)
            price = item.get("price")
            if price is None:
                price = item.get("lowestPrice")
            desc = f"{int(price or 0):,} R$" if item.get("isForSale") is not False else "Offsale"
            options.append(
                discord.SelectOption(
                    label=name[:100],
                    description=f"ID {item_id} · {desc}"[:100],
                    value=str(item_id),
                )
            )
        select = discord.ui.Select(
            placeholder=f"Pick an item for '{query[:40]}'",
            options=options,
            row=0,
        )
        select.callback = self._on_pick
        self.pick = select
        self.add_item(select)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        if not await _check_runner(interaction, self.owner_id):
            return
        assert isinstance(interaction.data, dict)
        values = interaction.data.get("values") or []
        if not values:
            await interaction.response.defer()
            return
        item_id = int(values[0])
        item = next((r for r in self.results if int(r.get("id") or 0) == item_id), None)
        if item is None:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            return
        allow_buy = self.allow_buy and can_use_wallet(interaction, self.bot.settings)
        await interaction.response.defer(thinking=True)
        pages, _stub, _thumb = await _inspect_payload(
            self.bot,
            item,
            show_wallet=allow_buy,
        )
        view = InspectView(
            self.bot,
            item=item,
            pages=pages,
            owner_id=self.owner_id,
            allow_buy=allow_buy,
        )
        await interaction.edit_original_response(embed=pages[0], view=view)


async def send_inspect(
    interaction: discord.Interaction,
    bot: MadokaBot,
    item: dict[str, Any],
) -> None:
    allow_buy = can_use_wallet(interaction, bot.settings)
    pages, _stub, _thumb = await _inspect_payload(bot, item, show_wallet=allow_buy)
    view = InspectView(
        bot,
        item=item,
        pages=pages,
        owner_id=interaction.user.id,
        allow_buy=allow_buy,
    )
    await interaction.followup.send(embed=pages[0], view=view)
