import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_save_location_key,
    get_effective_save_directory,
    get_effective_challenge_file,
    get_effective_ladder_file,
    set_allowed_channel,
    set_input_style,
    set_save_location_key,
    set_delimiter,
    set_challenge_file,
    set_ladder_file,
)

from utils.audit import send_audit_log


def is_server_admin():
    """Return an app_commands check that passes only for server administrators.

    A user is considered an admin if they are the guild owner, or if they
    hold the Administrator or Manage Guild permission.

    Returns:
        app_commands.check: A decorator-compatible permission predicate.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            return False
        user = interaction.user
        if not isinstance(user, discord.Member):
            return False
        return (
            interaction.guild.owner_id == user.id
            or user.guild_permissions.administrator
        )

    return app_commands.check(predicate)


# ---------------------------------------------------------------------------
# Filename validation helpers
# ---------------------------------------------------------------------------

def _validate_csv_filename(filename: str) -> str | None:
    """Return an error message if the filename is invalid, otherwise None.

    Rules:
      - Must end with .csv
      - Must not contain path separators (/ or \\) to prevent directory traversal
      - Must not be empty after stripping whitespace

    Args:
        filename: The raw string provided by the user.

    Returns:
        str | None: A human-readable error string, or None if the filename is valid.
    """
    filename = filename.strip()
    if not filename:
        return "Filename must not be empty."
    if not filename.endswith(".csv"):
        return "Filename must end with `.csv`."
    if "/" in filename or "\\" in filename:
        return "Filename must not contain path separators (`/` or `\\`)."
    return None


class SettingsCog(commands.Cog):
    """Cog that exposes all /settings slash commands for server administrators.

    Every command in this cog is protected by is_server_admin() and
    app_commands.default_permissions(manage_guild=True), so regular users
    cannot accidentally change bot behaviour for the whole server.

    Attributes:
        bot: The running discord.py Bot instance.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialise the cog and attach the bot reference.

        Args:
            bot: The running discord.py Bot instance.
        """
        self.bot = bot

    settings = app_commands.Group(
        name="settings",
        description="Manage this server's bot settings (channels, input style, save locations, CSV filenames)."
    )

    # -----------------------------------------------------------------------
    # /settings show
    # -----------------------------------------------------------------------

    @settings.command(name="show", description="Show all current bot settings for this server.")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def show(self, interaction: discord.Interaction) -> None:
        """Display all effective settings for this server in an ephemeral message.

        Shows both guild-specific overrides and config.py fallback values so
        admins can see exactly how the bot is configured at a glance.
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        guild = interaction.guild
        challenge_channel_id = get_effective_allowed_channel(guild.id, "challenge")
        ladder_channel_id = get_effective_allowed_channel(guild.id, "ladder")
        input_style = get_effective_input_style(guild.id)
        save_location_key = get_effective_save_location_key(guild.id)
        save_directory = get_effective_save_directory(guild.id)
        challenge_file = get_effective_challenge_file(guild.id)
        ladder_file = get_effective_ladder_file(guild.id)

        challenge_channel = guild.get_channel(challenge_channel_id) if challenge_channel_id else None
        ladder_channel = guild.get_channel(ladder_channel_id) if ladder_channel_id else None

        message = (
            f"**Challenge channel:** {challenge_channel.mention if challenge_channel else 'Not set'}\n"
            f"**Ladder channel:** {ladder_channel.mention if ladder_channel else 'Not set'}\n"
            f"**Input style:** `{input_style}`\n"
            f"**Save location key:** `{save_location_key}`\n"
            f"**Resolved save directory:** `{save_directory}`\n"
            f"**Challenge CSV file:** `{challenge_file}`\n"
            f"**Ladder CSV file:** `{ladder_file}`"
        )

        await interaction.response.send_message(message, ephemeral=True)

    # -----------------------------------------------------------------------
    # Channel restriction commands
    # -----------------------------------------------------------------------

    @settings.command(name="set_channel", description="Restrict a mode to a specific channel.")
    @app_commands.describe(mode="Which mode to configure", channel="The channel to restrict it to.")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="challenge", value="challenge"),
            app_commands.Choice(name="ladder", value="ladder"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def set_channel(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_allowed_channel(interaction.guild.id, mode.value, channel.id)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        # Send private audit log after successful change
        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=set_channel mode={mode.value} channel={channel.id}"
        )

        await interaction.response.send_message(
            f"The `{mode.value}` mode is now restricted to {channel.mention}.",
            ephemeral=True,
        )

    @settings.command(name="clear_channel", description="Remove the channel restriction for a mode.")
    @app_commands.describe(mode="Which mode to clear the restriction for.")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="challenge", value="challenge"),
            app_commands.Choice(name="ladder", value="ladder"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def clear_channel(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_allowed_channel(interaction.guild.id, mode.value, None)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=clear_channel mode={mode.value}"
        )

        await interaction.response.send_message(
            f"The `{mode.value}` mode is no longer restricted to one channel.",
            ephemeral=True,
        )

     # -----------------------------------------------------------------------
    # Input style / delimiter
    # -----------------------------------------------------------------------

    @settings.command(
        name="set_input_style",
        description="Set the input style and delimiter used when parsing match lines.",
    )
    @app_commands.describe(
        style="Order of deck name and result in each match line.",
        delimiter="Separator between deck name and result.",
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="Deck, delimiter, result", value="deck_delimiter_result"),
        app_commands.Choice(name="Result, delimiter, deck", value="result_delimiter_deck"),
    ])
    @app_commands.choices(delimiter=[
        app_commands.Choice(name="vs", value=" vs "),
        app_commands.Choice(name="-", value=" - "),
        app_commands.Choice(name="|", value=" | "),
        app_commands.Choice(name="/", value=" / "),
    ])
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def set_input_style(
        self,
        interaction: discord.Interaction,
        style: app_commands.Choice[str],
        delimiter: app_commands.Choice[str],
    ) -> None:
        """Configure how the bot parses each match line submitted by users.

        Both style and delimiter are set together because they are tightly
        coupled — changing one without the other would produce confusing
        parse errors.

        Args:
            style:     The order of deck name and result (e.g. deck first or result first).
            delimiter: The separator string between the two parts.
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_input_style(interaction.guild.id, style.value)
            set_delimiter(interaction.guild.id, delimiter.value)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=set_input_style style={style.value} delimiter={delimiter.value}"
        )

        await interaction.response.send_message(
            f"Input style set to `{style.value}` and delimiter set to `{delimiter.value}`.",
            ephemeral=True,
        )

    @settings.command(name="reset_input_style", description="Reset input style and delimiter to the config defaults.")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_input_style_cmd(self, interaction: discord.Interaction) -> None:
        """Reset the input style and delimiter to the values defined in config.py."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_input_style(interaction.guild.id, None)
            set_delimiter(interaction.guild.id, None)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=reset_input_style"
        )

        await interaction.response.send_message(
            "Input style and delimiter reset to defaults.",
            ephemeral=True,
        )

    # -----------------------------------------------------------------------
    # Save location
    # -----------------------------------------------------------------------

    @settings.command(name="set_save_location", description="Set where this server's match data is stored.")
    @app_commands.describe(location="The storage policy to use for this server.")
    @app_commands.choices(
        location=[
            app_commands.Choice(name="server_specific", value="server_specific"),
            app_commands.Choice(name="shared", value="shared"),
            app_commands.Choice(name="archive", value="archive"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def set_save_location(
        self,
        interaction: discord.Interaction,
        location: app_commands.Choice[str],
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_save_location_key(interaction.guild.id, location.value)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        save_dir = get_effective_save_directory(interaction.guild.id)

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=set_save_location location={location.value} resolved_dir={save_dir}"
        )

        await interaction.response.send_message(
            f"Save location set to `{location.value}`.\nResolved directory: `{save_dir}`",
            ephemeral=True,
        )

    @settings.command(name="reset_save_location", description="Reset the save location to the config default.")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_save_location(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_save_location_key(interaction.guild.id, None)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=reset_save_location"
        )

        await interaction.response.send_message(
            "Save location reset to default.",
            ephemeral=True,
        )

    # -----------------------------------------------------------------------
    # CSV filename commands
    # -----------------------------------------------------------------------

    @settings.command(
        name="set_challenge_file",
        description="Set the CSV filename where challenge match data is saved.",
    )
    @app_commands.describe(filename="Bare filename ending in .csv (e.g. challenge_june.csv).")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def set_challenge_file_cmd(
        self,
        interaction: discord.Interaction,
        filename: str,
    ) -> None:
        """Set the CSV filename for challenge (metagame) data for this server.

        The file is created automatically with the correct headers the first
        time a match is submitted, so no manual setup is needed after running
        this command.

        Args:
            filename: A bare .csv filename (e.g. "challenge_june.csv").
                      Path separators are rejected for security.
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        error = _validate_csv_filename(filename)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        safe_filename = filename.strip()

        try:
            set_challenge_file(interaction.guild.id, safe_filename)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=set_challenge_file file={safe_filename}"
        )

        await interaction.response.send_message(
            f"Challenge CSV file set to `{safe_filename}`.\n"
            "The file will be created automatically on the first submission.",
            ephemeral=True,
        )

    @settings.command(
        name="set_ladder_file",
        description="Set the CSV filename where ladder match data is saved.",
    )
    @app_commands.describe(filename="Bare filename ending in .csv (e.g. ladder_june.csv).")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def set_ladder_file_cmd(
        self,
        interaction: discord.Interaction,
        filename: str,
    ) -> None:
        """Set the CSV filename for ladder data for this server.

        The file is created automatically with the correct headers the first
        time a match is submitted, so no manual setup is needed after running
        this command.

        Args:
            filename: A bare .csv filename (e.g. "ladder_june.csv").
                      Path separators are rejected for security.
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        error = _validate_csv_filename(filename)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        safe_filename = filename.strip()

        try:
            set_ladder_file(interaction.guild.id, safe_filename)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=set_ladder_file file={safe_filename}"
        )

        await interaction.response.send_message(
            f"Ladder CSV file set to `{safe_filename}`.\n"
            "The file will be created automatically on the first submission.",
            ephemeral=True,
        )

    @settings.command(
        name="reset_challenge_file",
        description="Reset the challenge CSV filename to the config.py default.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_challenge_file_cmd(self, interaction: discord.Interaction) -> None:
        """Reset the challenge CSV filename to the value defined in config.CHALLENGE_FILE."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_challenge_file(interaction.guild.id, None)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=reset_challenge_file"
        )

        await interaction.response.send_message(
            "Challenge CSV filename reset to default.",
            ephemeral=True,
        )

    @settings.command(
        name="reset_ladder_file",
        description="Reset the ladder CSV filename to the config.py default.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_ladder_file_cmd(self, interaction: discord.Interaction) -> None:
        """Reset the ladder CSV filename to the value defined in config.LADDER_FILE."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        try:
            set_ladder_file(interaction.guild.id, None)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        await send_audit_log(
            f"[SETTINGS] guild={interaction.guild.id} admin={interaction.user.id} action=reset_ladder_file"
        )

        await interaction.response.send_message(
            "Ladder CSV filename reset to default.",
            ephemeral=True,
        )

    # If user not admin tries to use it, returns ephemeral private error.
    @show.error
    @set_channel.error
    @clear_channel.error
    @set_input_style.error
    @reset_input_style_cmd.error
    @set_save_location.error
    @reset_save_location.error
    @set_challenge_file_cmd.error
    @set_ladder_file_cmd.error
    @reset_challenge_file_cmd.error
    @reset_ladder_file_cmd.error
    async def settings_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        # Permission failure
        if isinstance(error, app_commands.errors.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("Admin only.", ephemeral=True)
            else:
                await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        # Validation failure from setter helpers
        if isinstance(error, app_commands.errors.CommandInvokeError) and isinstance(error.original, ValueError):
            if interaction.response.is_done():
                await interaction.followup.send(str(error.original), ephemeral=True)
            else:
                await interaction.response.send_message(str(error.original), ephemeral=True)
            return

        raise error
    

    async def setup(bot):
        await bot.add_cog(SettingsCog(bot))