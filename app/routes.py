from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from .discord_bot import client, loop, get_guild_info, send_discord_message, fetch_messages, get_emojis, create_emoji, delete_emoji
import asyncio

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    while not client.is_ready():
        asyncio.sleep(1)

    bot_name = client.user.name 
    bot_avatar_url = client.user.avatar.url

    categories, server_info = get_guild_info(client, current_app.config['GUILD_ID'])

    return render_template('index.html', categories=categories, selected_channel_id=None, bot_name=bot_name, bot_avatar_url=bot_avatar_url, server_info=server_info)

@main.route('/send_message', methods=['POST'])
def send_message():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    channel_id = int(request.form['channel_id'])
    message = request.form['message']

    result = asyncio.run_coroutine_threadsafe(send_discord_message(client, channel_id, message), loop).result()
    return jsonify(result)

@main.route('/get_last_messages/<channel_id>', methods=['GET'])
def get_last_messages(channel_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    messages = fetch_messages(client, int(channel_id), loop)
    return jsonify(messages)

@main.route('/get_emojis', methods=['GET'])
def get_emojis_route():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    emojis = get_emojis(client, current_app.config['GUILD_ID'])
    return jsonify(emojis)

@main.route('/upload_emoji', methods=['POST'])
def upload_emoji():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    emoji_file = request.files['emoji-file']
    emoji_name = request.form['emoji-name']

    result = create_emoji(client, current_app.config['GUILD_ID'], emoji_name, emoji_file.read(), loop)
    return jsonify(result)

@main.route('/delete_emoji/<emoji_id>', methods=['DELETE'])
def delete_emoji_route(emoji_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    result = delete_emoji(client, current_app.config['GUILD_ID'], int(emoji_id), loop)
    return jsonify(result)
