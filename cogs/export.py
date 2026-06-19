# cogs/export.py
#
# Exposes the /export slash command.
#
# Usage:
#   /export file:<filename.csv>   — sends the named CSV as an attachment.
#   /export file:all              — bundles every CSV in the guild's save
#                                   directory into a single .zip file and
#                                   sends that instead.
#
# Access: server admins only (same guard as /settings).

import io
import zipfile
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from cogs.settings import is_server_admin
from utils.guild_settings import (
    get_effective_save_directory,
    get_effective_challenge_file,
    get_effective_ladder_file,
)

# Discord's upload limit for regular bots.
_MAX_BYTES = 8 * 1024 * 1024  # 8 MB

# The magic keyword that triggers the "export everything" path.
_ALL_KEYWORD = "all"


class ExportCog(commands.Cog):
    """Cog that exposes /export — download one or all CSV data files.

    Attributes:
        bot: The running discord.py Bot instance.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Autocomplete — suggests the two known filenames + the magic "all"
    # ------------------------------------------------------------------

    async def _file_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Return autocomplete suggestions for the `file` parameter.

        Suggests the guild's configured challenge file, ladder file, and the
        special value "all".  Filters by whatever the user has typed so far.

        Args:
            interaction: The Discord interaction triggering autocomplete.
            current:     The partial string the user has typed so far.

        Returns:
            A list of up to 25 matching Choice objects.
        """
        if interaction.guild is None:
            return []

        guild_id = interaction.guild.id
        challenge_file = get_effective_challenge_file(guild_id)
        ladder_file = get_effective_ladder_file(guild_id)

        suggestions = [challenge_file, ladder_file, _ALL_KEYWORD]
        return [
            app_commands.Choice(name=s, value=s)
            for s in suggestions
            if current.lower() in s.lower()
        ][:25]

    # ------------------------------------------------------------------
    # /export
    # ------------------------------------------------------------------

    @app_commands.command(
        name="export",
        description='Export match data. Type a CSV filename or "all" to get a .zip of everything.',
    )
    @app_commands.describe(
        file='CSV filename to export (e.g. challenge_2026_06.csv), or "all" for a full zip.'
    )
    @app_commands.autocomplete(file=_file_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def export(
        self,
        interaction: discord.Interaction,
        file: str,
    ) -> None:
        """Send one CSV or a zip of all CSVs for this server (admin-only).

        When `file` is the literal string "all", every .csv file found in
        the guild's resolved save directory is bundled into an in-memory
        zip archive and returned as a single attachment.  Otherwise the
        named file is sent directly.

        Args:
            file: A bare .csv filename, or the string "all".
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command must be used in a server.",
                ephemeral=True,
            )
            return

        guild_id = interaction.guild.id
        save_dir = Path(get_effective_save_directory(guild_id))

        # ----------------------------------------------------------------
        # Branch: export ALL csv files as a zip
        # ----------------------------------------------------------------
        if file.strip().lower() == _ALL_KEYWORD:
            await self._export_all(interaction, save_dir, guild_id)
            return

        # ----------------------------------------------------------------
        # Branch: export a single named CSV
        # ----------------------------------------------------------------
        await self._export_single(interaction, save_dir, file.strip())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _export_single(
        self,
        interaction: discord.Interaction,
        save_dir: Path,
        filename: str,
    ) -> None:
        """Validate and send a single CSV file.

        Args:
            interaction: The originating Discord interaction.
            save_dir:    Resolved save directory for this guild.
            filename:    Bare CSV filename provided by the user.
        """
        # Basic safety check — no path traversal.
        if "/" in filename or "\\" in filename:
            await interaction.response.send_message(
                "❌ Filename must not contain path separators.",
                ephemeral=True,
            )
            return

        if not filename.endswith(".csv"):
            await interaction.response.send_message(
                "❌ Filename must end with `.csv`.",
                ephemeral=True,
            )
            return

        csv_path = save_dir / filename

        if not csv_path.exists():
            await interaction.response.send_message(
                f"❌ No file named `{filename}` found in this server's data directory.\n"
                "Has anyone submitted matches to that file yet?",
                ephemeral=True,
            )
            return

        if csv_path.stat().st_size > _MAX_BYTES:
            await interaction.response.send_message(
                f"⚠️ `{filename}` exceeds 8 MB and cannot be sent via Discord.\n"
                "Please retrieve it from the server filesystem directly.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"📄 Here is `{filename}` for this server:",
            file=discord.File(csv_path, filename=filename),
            ephemeral=True,
        )

    async def _export_all(
        self,
        interaction: discord.Interaction,
        save_dir: Path,
        guild_id: int,
    ) -> None:
        """Bundle every CSV in the guild's save directory into a zip and send it.

        The zip is built entirely in memory (io.BytesIO) so no temporary file
        is written to disk.

        Args:
            interaction: The originating Discord interaction.
            save_dir:    Resolved save directory for this guild.
            guild_id:    The Discord guild ID (used for the zip filename).
        """
        if not save_dir.exists():
            await interaction.response.send_message(
                "❌ No data directory found for this server.\n"
                "Has anyone submitted matches yet?",
                ephemeral=True,
            )
            return

        csv_files = sorted(save_dir.glob("*.csv"))

        if not csv_files:
            await interaction.response.send_message(
                "❌ No CSV files found in this server's data directory.\n"
                "Has anyone submitted matches yet?",
                ephemeral=True,
            )
            return

        # Build zip in memory.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for csv_path in csv_files:
                zf.write(csv_path, arcname=csv_path.name)

        zip_size = buffer.tell()

        if zip_size > _MAX_BYTES:
            await interaction.response.send_message(
                f"⚠️ The combined zip ({zip_size / 1024 / 1024:.1f} MB) exceeds Discord's 8 MB limit.\n"
                "Please retrieve the files from the server filesystem directly.",
                ephemeral=True,
            )
            return

        buffer.seek(0)
        zip_name = f"mtga_data_{guild_id}.zip"
        file_list = ", ".join(f"`{f.name}`" for f in csv_files)

        await interaction.response.send_message(
            f"📦 Here is a zip of all data files for this server:\n{file_list}",
            file=discord.File(buffer, filename=zip_name),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    """Register the ExportCog with the bot.

    Args:
        bot: The running discord.py Bot instance.
    """
    await bot.add_cog(ExportCog(bot))
