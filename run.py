from app import create_app, socketio, discord_bot
import signal
import sys
import asyncio

app = create_app()

async def shutdown():
    print("Shutting down...")
    
    discord_bot.stop_bot()
    
    socketio.stop()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

def shutdown_signal_handler(signal, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    signal.signal(signal.SIGINT, shutdown_signal_handler)
    signal.signal(signal.SIGTERM, shutdown_signal_handler)

    discord_bot.start_bot(app)
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
