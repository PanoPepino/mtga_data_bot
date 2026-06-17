import discord
from config import SESSION_TIMEOUT_SEC
from cogs.sessions import close_session


# cogs/views.py

import discord
from config import SESSION_TIMEOUT_SEC
from cogs.sessions import close_session


class AddRunView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=SESSION_TIMEOUT_SEC)
        self.user_id = user_id

    # To avoid any other user may modify a session that is not theirs
    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        """Only the user who started the session can press the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This isn't your session.", ephemeral=True
            )
            return False
        return True

    # In the fill-in form, some extra buttons will appear to add the info
    @discord.ui.button(label="➕ Add another run", style=discord.ButtonStyle.primary)
    async def add_run(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        from cogs.modals import ExtraRunModal   # avoid circular import
        await interaction.response.send_modal(ExtraRunModal(self.user_id))

    @discord.ui.button(label="✅ Done", style=discord.ButtonStyle.secondary)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        close_session(self.user_id)
        self.stop()
        await interaction.response.edit_message(content="Session closed. ✅", view=None)

    # In case someone takes more than 10 min, the session disconnects
    async def on_timeout(self):
        """Called automatically when SESSION_TIMEOUT_SEC elapses."""
        close_session(self.user_id)
