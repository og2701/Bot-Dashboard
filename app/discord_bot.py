import discord
import asyncio
from threading import Thread
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.emojis = True

client = discord.Client(intents=intents)
loop = asyncio.get_event_loop()


def stop_bot():
    loop = asyncio.get_event_loop()
    loop.create_task(client.close())
    loop.stop()

def get_guild_info(client, guild_id):
    guild = client.get_guild(guild_id)
    if not guild:
        return {}, {}

    categories = {}
    for category in guild.categories:
        categories[category.name] = [(channel.id, channel.name) for channel in category.channels if isinstance(channel, discord.TextChannel)]

    no_category = [(channel.id, channel.name) for channel in guild.channels if isinstance(channel, discord.TextChannel) and channel.category is None]
    if no_category:
        categories['No Category'] = no_category

    server_info = {
        "member_count": guild.member_count,
        "channel_count": len(guild.channels),
        "text_channel_count": len([c for c in guild.channels if isinstance(c, discord.TextChannel)]),
        "voice_channel_count": len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)]),
        "category_count": len(guild.categories),
        "role_count": len(guild.roles),
        "emoji_count": len(guild.emojis),
        "sticker_count": len(guild.stickers),
        "bot_count": len([m for m in guild.members if m.bot]),
        "human_count": len([m for m in guild.members if not m.bot]),
    }

    return categories, server_info

async def send_discord_message(client, channel_id, message):
    channel = client.get_channel(channel_id)
    sent_message = await channel.send(message)
    member = channel.guild.get_member(client.user.id)
    role_color = member.top_role.color if member and member.top_role else discord.Color.default()
    timestamp = sent_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
    return {
        'success': True,
        'author': client.user.display_name,
        'color': str(role_color),
        'timestamp': timestamp
    }

def fetch_messages(client, channel_id, loop):
    channel = client.get_channel(channel_id)
    if channel:
        async def get_history():
            messages = []
            async for message in channel.history(limit=10):
                member = channel.guild.get_member(message.author.id)
                role_color = member.top_role.color if member and member.top_role else discord.Color.default()
                messages.append({
                    'author': message.author.display_name,
                    'content': message.content,
                    'color': str(role_color),
                    'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            return messages

        future = asyncio.run_coroutine_threadsafe(get_history(), loop)
        return future.result()
    return []

def get_emojis(client, guild_id):
    guild = client.get_guild(guild_id)
    emojis = [{'id': str(emoji.id), 'name': emoji.name, 'url': str(emoji.url)} for emoji in guild.emojis]
    return emojis

def create_emoji(client, guild_id, name, image, loop):
    guild = client.get_guild(guild_id)
    emoji = asyncio.run_coroutine_threadsafe(guild.create_custom_emoji(name=name, image=image), loop).result()
    return {'success': True}

def delete_emoji(client, guild_id, emoji_id, loop):
    guild = client.get_guild(guild_id)
    emoji = discord.utils.get(guild.emojis, id=emoji_id)
    if emoji:
        asyncio.run_coroutine_threadsafe(emoji.delete(), loop).result()
        return {'success': True}
    else:
        return {'success': False, 'error': 'Emoji not found'}

@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    member = message.guild.get_member(message.author.id)
    role_color = member.top_role.color if member and member.top_role else discord.Color.default()
    data = {
        'author': message.author.display_name,
        'content': message.content,
        'channel_id': message.channel.id,
        'color': str(role_color),
        'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    from app import socketio #ugly but avoids circular import
    socketio.emit('new_message', data)

def start_bot(app):
    def run_bot():
        with app.app_context():
            token = os.getenv('DISCORD_TOKEN')
            if not token:
                raise ValueError("No DISCORD_TOKEN found in environment variables")
            loop.run_until_complete(client.start(token))

    
    Thread(target=run_bot).start()
