import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.guild_settings import (
    get_effective_allowed_channel,
    get_effective_input_style,
    get_effective_save_location_key,
    get_effective_save_directory,
    set_allowed_channel,
    set_input_style,
    set_save_location_key,
    set_delimiter
)


def is_server_admin():
    """
    Check if who calls is admin server.
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
            or user.guild_permissions.manage_guild
        )

    return app_commands.check(predicate)


class SettingsCog(commands.Cog):
    """
    This class is in charge of all the settings of the bot. Only to control by admins.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    settings = app_commands.Group(
        name="settings",
        description="Manage this server's bot settings, like where the information is saved or the input style"
    )

    @settings.command(name="show", description="Show current bot settings for this server")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def show(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        challenge_channel_id = get_effective_allowed_channel(guild.id, "challenge")
        ladder_channel_id = get_effective_allowed_channel(guild.id, "ladder")
        input_style = get_effective_input_style(guild.id)
        save_location_key = get_effective_save_location_key(guild.id)
        save_directory = get_effective_save_directory(guild.id)

        challenge_channel = guild.get_channel(challenge_channel_id) if challenge_channel_id else None
        ladder_channel = guild.get_channel(ladder_channel_id) if ladder_channel_id else None

        message = (
            f"**Challenge channel:** {challenge_channel.mention if challenge_channel else 'Not set'}\n"
            f"**Ladder channel:** {ladder_channel.mention if ladder_channel else 'Not set'}\n"
            f"**Input style:** `{input_style}`\n"
            f"**Save location key:** `{save_location_key}`\n"
            f"**Resolved save directory:** `{save_directory}`"
        )

        await interaction.response.send_message(message, ephemeral=True)

    @settings.command(name="set_channel", description="Set the allowed channel for a mode")
    @app_commands.describe(mode="Which mode to configure", channel="The allowed channel")
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
        channel: discord.TextChannel
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server",
                ephemeral=True
            )
            return

        set_allowed_channel(interaction.guild.id, mode.value, channel.id)

        await interaction.response.send_message(
            f"The `{mode.value}` mode is now restricted to {channel.mention}",
            ephemeral=True
        )

    @settings.command(name="clear_channel", description="Clear the allowed channel for a mode.")
    @app_commands.describe(mode="Which mode to clear")
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
        mode: app_commands.Choice[str]
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server",
                ephemeral=True
            )
            return

        set_allowed_channel(interaction.guild.id, mode.value, None)

        await interaction.response.send_message(
            f"The `{mode.value}` mode is no longer restricted to one channel",
            ephemeral=True
        )

    @settings.command(
        name="set_input_style",
        description="Set the input style and delimiter for this server."
    )
    @app_commands.describe(
        style="Choose the order of deck and result.",
        delimiter="Choose the separator between deck and result.",
    )
    @app_commands.choices(style=[
        app_commands.Choice(
            name="Deck, delimiter, result",
            value="deck_delimiter_result",
        ),
        app_commands.Choice(
            name="Result, delimiter, deck",
            value="result_delimiter_deck",
        ),
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
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        set_input_style(interaction.guild.id, style.value)
        set_delimiter(interaction.guild.id, delimiter.value)

        await interaction.response.send_message(
            f"Input style set to `{style.value}` and delimiter set to `{delimiter.value}`.",
            ephemeral=True,
        )

    @settings.command(name="reset_input_style", description="Reset input style to default")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_input_style_cmd(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        set_input_style(interaction.guild.id, None)

        await interaction.response.send_message(
            "Input style reset to default.",
            ephemeral=True
        )

    @settings.command(name="set_save_location", description="Set the save location policy")
    @app_commands.describe(location="Where this server's data should be stored")
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
        location: app_commands.Choice[str]
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server",
                ephemeral=True
            )
            return

        if location.value not in config.SAVE_LOCATION_MAP:
            await interaction.response.send_message(
                "That save location is not available",
                ephemeral=True
            )
            return

        set_save_location_key(interaction.guild.id, location.value)

        save_dir = get_effective_save_directory(interaction.guild.id)

        await interaction.response.send_message(
            f"Save location set to `{location.value}`.\nResolved directory: `{save_dir}`",
            ephemeral=True
        )

    @settings.command(name="reset_save_location", description="Reset save location to default")
    @app_commands.default_permissions(manage_guild=True)
    @is_server_admin()
    async def reset_save_location(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server",
                ephemeral=True
            )
            return

        set_save_location_key(interaction.guild.id, None)

        await interaction.response.send_message(
            "Save location reset to default",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))
