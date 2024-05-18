from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit
import discord
import asyncio
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Set a simple password for login
LOGIN_PASSWORD = 'your_password_here'

# Read the bot token from the token.txt file
with open('token.txt', 'r') as file:
    TOKEN = file.read().strip()

# Define the constant for the server ID
GUILD_ID = 959493056242008184  # Replace with your actual server ID

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.emojis = True

client = discord.Client(intents=intents)

# Run the bot
loop = asyncio.get_event_loop()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == LOGIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if not client.is_ready():
        return "Bot is not ready. Please wait..."

    bot_name = client.user.name  # Fetch the bot's username
    bot_avatar_url = client.user.avatar.url  # Fetch the bot's avatar URL

    guild = client.get_guild(GUILD_ID)
    if not guild:
        return "Guild not found."

    categories = {}
    for category in guild.categories:
        categories[category.name] = [(channel.id, channel.name) for channel in category.channels if isinstance(channel, discord.TextChannel)]
    
    no_category = [(channel.id, channel.name) for channel in guild.channels if isinstance(channel, discord.TextChannel) and channel.category is None]
    if no_category:
        categories['No Category'] = no_category

    # Gather server statistics
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
    
    return render_template('index.html', categories=categories, selected_channel_id=None, bot_name=bot_name, bot_avatar_url=bot_avatar_url, server_info=server_info)

@app.route('/send_message', methods=['POST'])
def send_message():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    channel_id = int(request.form['channel_id'])
    message = request.form['message']
    channel = client.get_channel(channel_id)

    async def send_discord_message():
        sent_message = await channel.send(message)
        return sent_message

    sent_message = asyncio.run_coroutine_threadsafe(send_discord_message(), loop).result()

    member = channel.guild.get_member(client.user.id)
    role_color = member.top_role.color if member and member.top_role else discord.Color.default()
    timestamp = sent_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'success': True,
        'author': client.user.display_name,
        'color': str(role_color),
        'timestamp': timestamp
    })

@app.route('/get_last_messages/<channel_id>', methods=['GET'])
def get_last_messages(channel_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    channel = client.get_channel(int(channel_id))

    async def fetch_messages():
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

    messages = asyncio.run_coroutine_threadsafe(fetch_messages(), loop).result()
    return jsonify(messages)

@app.route('/get_emojis', methods=['GET'])
def get_emojis():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    guild = client.get_guild(GUILD_ID)
    emojis = [{'id': str(emoji.id), 'name': emoji.name, 'url': str(emoji.url)} for emoji in guild.emojis]
    return jsonify(emojis)

@app.route('/upload_emoji', methods=['POST'])
def upload_emoji():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    emoji_file = request.files['emoji-file']
    emoji_name = request.form['emoji-name']

    guild = client.get_guild(GUILD_ID)
    emoji = asyncio.run_coroutine_threadsafe(
        guild.create_custom_emoji(name=emoji_name, image=emoji_file.read()),
        loop
    ).result()

    return jsonify({'success': True})

@app.route('/delete_emoji/<emoji_id>', methods=['DELETE'])
def delete_emoji(emoji_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    guild = client.get_guild(GUILD_ID)
    emoji = discord.utils.get(guild.emojis, id=int(emoji_id))
    if emoji:
        asyncio.run_coroutine_threadsafe(emoji.delete(), loop).result()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Emoji not found'})

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
    socketio.emit('new_message', data)

def run_flask():
    socketio.run(app, debug=True, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    loop.run_until_complete(client.start(TOKEN))
