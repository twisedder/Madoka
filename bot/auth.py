from __future__ import annotations

import discord

from config.settings import Settings


def can_use_wallet(interaction: discord.Interaction, settings: Settings) -> bool:
    return interaction.user is not None and interaction.user.id == settings.wallet_owner_id


async def deny_wallet(interaction: discord.Interaction) -> None:
    if interaction.response.is_done():
        await interaction.followup.send("Only the wallet owner can use bot currency.", ephemeral=True)
        return
    await interaction.response.send_message("Only the wallet owner can use bot currency.", ephemeral=True)


def is_runner(interaction: discord.Interaction, owner_id: int) -> bool:
    return interaction.user is not None and interaction.user.id == owner_id


async def deny_runner(interaction: discord.Interaction) -> None:
    if interaction.response.is_done():
        await interaction.followup.send("Only the command runner can use this.", ephemeral=True)
        return
    await interaction.response.send_message("Only the command runner can use this.", ephemeral=True)
