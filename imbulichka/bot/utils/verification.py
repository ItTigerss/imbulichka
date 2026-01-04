import discord
from discord.ui import Button, View

class VerificationView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success)
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "✅ Verification system coming soon!",
            ephemeral=True
        )