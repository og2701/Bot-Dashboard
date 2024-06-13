from app import create_app, socketio, discord_bot
import asyncio

app = create_app()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    discord_bot.start_bot(app)
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
