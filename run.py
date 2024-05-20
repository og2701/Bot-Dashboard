from app import create_app, socketio, discord_bot, diplomacy_bot

app = create_app()

if __name__ == "__main__":
    discord_bot.start_bot(app)
    diplomacy_bot.start_bot(app)
    socketio.run(app, debug=True)
