import discord
from discord import app_commands, Intents, Interaction, Client
from discord.utils import get
import aiohttp
import asyncio
from flask import current_app
from threading import Thread
import datetime

#registered servers and active sessions
servers = {}
active_sessions = {}

class DiplomacyClient(Client):
    def __init__(self):
        intents = Intents.default()
        intents.presences = True
        intents.members = True
        intents.messages = True
        intents.guilds = True
        intents.message_content = True

        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        global tree
        if not self.synced:
            await tree.sync()
            self.synced = True

        print(f"Logged in as {self.user}")

        for guild in self.guilds:
            existing_channel = get(guild.text_channels, name='diplomacy-channel')
            if existing_channel:
                webhook = await self.get_or_create_webhook(existing_channel, f"{guild.name} Diplomacy")
                servers[guild.id] = {'channel': existing_channel.id, 'webhook': webhook.url}
                print(f"Automatically registered {guild.name} with existing diplomacy channel")

        self.loop.create_task(self.check_inactive_sessions())

    async def on_message(self, message):
        if message.author == self.user or message.webhook_id:
            return

        for (guild_id_a, guild_id_b), active_session in active_sessions.items():
            if active_session['active']:
                if message.channel.id in [servers[guild_id_a]['channel'], servers[guild_id_b]['channel']]:
                    target_webhook_url = None
                    if message.guild.id == guild_id_a:
                        target_webhook_url = active_session.get('webhook_b')
                    elif message.guild.id == guild_id_b:
                        target_webhook_url = active_session.get('webhook_a')

                    if target_webhook_url:
                        if message.content.strip():
                            async with aiohttp.ClientSession() as session_http:
                                webhook = discord.Webhook.from_url(target_webhook_url, session=session_http)
                                await webhook.send(
                                    content=message.content,
                                    username=f"{message.author.display_name} ({message.guild.name})",
                                    avatar_url=message.author.avatar.url
                                )
                                active_session['last_message_time'] = discord.utils.utcnow()
                                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                log_message = f"{timestamp} | {message.author.display_name} ({message.guild.name}): {message.content}\n"
                                active_session['log'].append(log_message)

    async def get_or_create_webhook(self, channel, name):
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == name:
                return webhook
        if len(webhooks) >= 15:
            await webhooks[0].delete()
        webhook = await channel.create_webhook(name=name)
        return webhook

    async def check_inactive_sessions(self):
        while True:
            now = discord.utils.utcnow()
            to_remove = []
            for (guild_id_a, guild_id_b), active_session in list(active_sessions.items()):
                if (now - active_session['last_message_time']).total_seconds() > 30: #30 sec inactivity timeout --> hangup
                    to_remove.append((guild_id_a, guild_id_b))
                    try:
                        await self.get_channel(servers[guild_id_a]['channel']).send(
                            embed=discord.Embed(description="Diplomatic chat session has ended due to inactivity.", color=discord.Color.red())
                        )
                    except Exception as e:
                        print(f"Failed to send message to guild {guild_id_a}: {e}")
                    try:
                        await self.get_channel(servers[guild_id_b]['channel']).send(
                            embed=discord.Embed(description="Diplomatic chat session has ended due to inactivity.", color=discord.Color.red())
                        )
                    except Exception as e:
                        print(f"Failed to send message to guild {guild_id_b}: {e}")
                    await self.save_and_send_log(guild_id_a, guild_id_b, active_session)
            for key in to_remove:
                del active_sessions[key]
            await asyncio.sleep(30)

    async def save_and_send_log(self, guild_id_a, guild_id_b, active_session):
        log_filename = f"diplomacy_log_{guild_id_a}_{guild_id_b}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
        with open(f'/tmp/{log_filename}', 'w') as log_file:
            log_file.writelines(active_session['log'])

        log_channel = self.get_channel(1242202414094745671)
        if log_channel:
            await log_channel.send(file=discord.File(f'/tmp/{log_filename}'))
        else:
            print("Log channel not found.")

client = DiplomacyClient()
tree = app_commands.CommandTree(client)

@tree.command(name="register", description="Register a server for diplomacy")
async def register(interaction: Interaction):
    try:
        await interaction.response.defer() #this bs not needed if i run this bot seperately
    except discord.errors.NotFound:
        print(f"Failed to defer interaction {interaction.id}: Interaction not found")
        return
    except Exception as e:
        print(f"Unexpected error when deferring interaction {interaction.id}: {e}")
        return

    existing_channel = get(interaction.guild.text_channels, name='diplomacy-channel')
    if interaction.guild.id in servers:
        await interaction.followup.send(
            embed=discord.Embed(description=f"{interaction.guild.name} is already registered.", color=discord.Color.blue())
        )
    elif existing_channel:
        webhook = await client.get_or_create_webhook(existing_channel, f"{interaction.guild.name} Diplomacy")
        servers[interaction.guild.id] = {'channel': existing_channel.id, 'webhook': webhook.url}
        await interaction.followup.send(
            embed=discord.Embed(description=f"{interaction.guild.name} is now registered with the existing diplomacy channel.", color=discord.Color.blue())
        )
    else:
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        diplomacy_channel = await interaction.guild.create_text_channel('diplomacy-channel', overwrites=overwrites)
        webhook = await client.get_or_create_webhook(diplomacy_channel, f"{interaction.guild.name} Diplomacy")
        servers[interaction.guild.id] = {'channel': diplomacy_channel.id, 'webhook': webhook.url}
        await interaction.followup.send(
            embed=discord.Embed(description=f"Registered {interaction.guild.name} with diplomacy channel {diplomacy_channel.mention}", color=discord.Color.green())
        )


@tree.command(name="call", description="Initiate a diplomatic chat with another server")
async def call(interaction: Interaction, target_guild_id: str):
    try:
        await interaction.response.defer()
    except discord.errors.NotFound:
        print(f"Failed to defer interaction {interaction.id}: Interaction not found")
        return
    except Exception as e:
        print(f"Unexpected error when deferring interaction {interaction.id}: {e}")
        return

    target_guild_id = int(target_guild_id)
    print(f"Attempting to call {target_guild_id} from {interaction.guild.id}")
    print(f"Servers registered: {servers}")

    if interaction.guild.id in servers and target_guild_id in servers:
        target_guild = client.get_guild(target_guild_id)
        if target_guild:
            target_channel = target_guild.get_channel(servers[target_guild_id]['channel'])

            buttons = [
                discord.ui.Button(style=discord.ButtonStyle.green, label="Accept", custom_id="accept"),
                discord.ui.Button(style=discord.ButtonStyle.red, label="Deny", custom_id="deny")
            ]
            view = discord.ui.View()
            for button in buttons:
                view.add_item(button)

            embed = discord.Embed(
                title="Diplomatic Call Request",
                description=f"{interaction.guild.name} is requesting a diplomatic chat with {target_guild.name}.",
                color=discord.Color.blue()
            )
            await target_channel.send(embed=embed, view=view)
            active_sessions[(interaction.guild.id, target_guild_id)] = {
                'active': False, 
                'last_message_time': discord.utils.utcnow(), 
                'initiator': interaction.guild.id,
                'log': [f"Connection initiated by {interaction.guild.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
            }
            await interaction.followup.send(
                embed=discord.Embed(description=f"Calling {target_guild.name} for a diplomatic chat.", color=discord.Color.blue())
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(description="Target server not found.", color=discord.Color.red())
            )
    else:
        await interaction.followup.send(
            embed=discord.Embed(description="Both servers need to be registered for diplomacy.", color=discord.Color.red())
        )

@client.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data['custom_id']
        if custom_id in ["accept", "deny"]:
            for (guild_id_a, guild_id_b), active_session in active_sessions.items():
                if active_session['initiator'] != interaction.guild.id:
                    target_guild_id = guild_id_a if interaction.guild.id == guild_id_b else guild_id_b
                    original_message = interaction.message

                    if custom_id == "accept":
                        webhook_a_channel = client.get_guild(guild_id_a).get_channel(servers[guild_id_a]['channel'])
                        webhook_b_channel = client.get_guild(guild_id_b).get_channel(servers[guild_id_b]['channel'])
                        webhook_a = await client.get_or_create_webhook(webhook_a_channel, f"{interaction.guild.name} Diplomacy")
                        webhook_b = await client.get_or_create_webhook(webhook_b_channel, f"{client.get_guild(guild_id_a).name} Diplomacy")
                        active_session['webhook_a'] = webhook_a.url
                        active_session['webhook_b'] = webhook_b.url
                        active_session['active'] = True
                        active_session['log'].append(f"Connection accepted by {interaction.guild.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                        embed = discord.Embed(
                            title="Diplomatic Chat Accepted",
                            description=f"{interaction.guild.name} has accepted the diplomatic chat request.",
                            color=discord.Color.green()
                        )
                        await original_message.edit(embed=embed, view=None)

                        target_channel = client.get_channel(servers[target_guild_id]['channel'])
                        await target_channel.send(embed=discord.Embed(
                            description=f"{interaction.guild.name} has accepted the diplomatic chat request with {client.get_guild(target_guild_id).name}.",
                            color=discord.Color.green()
                        ))

                    elif custom_id == "deny":
                        active_session['log'].append(f"Connection denied by {interaction.guild.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        await client.save_and_send_log(guild_id_a, guild_id_b, active_session)
                        del active_sessions[(guild_id_a, guild_id_b)]

                        embed = discord.Embed(
                            title="Diplomatic Chat Denied",
                            description=f"{interaction.guild.name} has denied the diplomatic chat request.",
                            color=discord.Color.red())
                        await original_message.edit(embed=embed, view=None)

                        target_channel = client.get_channel(servers[target_guild_id]['channel'])
                        await target_channel.send(embed=discord.Embed(
                            description=f"{client.get_guild(target_guild_id).name} has denied the diplomatic chat request with {interaction.guild.name}.",
                            color=discord.Color.red())
                        )

                    break

@tree.command(name="hangup", description="Hang up a diplomatic chat")
async def hangup(interaction: Interaction):
    try:
        await interaction.response.defer()
    except discord.errors.NotFound:
        print(f"Failed to defer interaction {interaction.id}: Interaction not found")
        return
    except Exception as e:
        print(f"Unexpected error when deferring interaction {interaction.id}: {e}")
        return

    guild_id = interaction.guild.id
    active_session_found = False

    to_remove = []

    for (guild_id_a, guild_id_b), active_session in active_sessions.items():
        if guild_id in [guild_id_a, guild_id_b] and active_session['active']:
            target_guild_id = guild_id_a if guild_id == guild_id_b else guild_id_b
            try:
                await client.get_channel(servers[target_guild_id]['channel']).send(
                    embed=discord.Embed(description=f"{interaction.guild.name} has hung up the diplomatic chat.", color=discord.Color.orange())
                )
            except Exception as e:
                print(f"Failed to send message to target guild {target_guild_id}: {e}")

            to_remove.append((guild_id_a, guild_id_b))
            active_session_found = True

    for key in to_remove:
        active_session = active_sessions[key]
        active_session['log'].append(f"Connection ended by {interaction.guild.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        await client.save_and_send_log(*key, active_session)
        del active_sessions[key]

    if active_session_found:
        await interaction.followup.send(
            embed=discord.Embed(description="Diplomatic chat session has been hung up.", color=discord.Color.orange())
        )
    else:
        await interaction.followup.send(
            embed=discord.Embed(description="There is no active diplomatic chat session to hang up.", color=discord.Color.red())
        )

def start_bot(app):
    def run_bot():
        with app.app_context():
            token = current_app.config['DISCORD_TOKEN']
            client.run(token)
    
    Thread(target=run_bot).start()
