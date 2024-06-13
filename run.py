from app import create_app, socketio, discord_bot
import signal
import sys
import asyncio

app = create_app()

async def shutdown(signal, frame):
    print("Shutting down...")
    discord_bot.stop_bot()
    socketio.stop()
    
    loop = asyncio.get_event_loop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    signal.signal(signal.SIGINT, lambda s, f: asyncio.run(shutdown(s, f)))
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.run(shutdown(s, f)))

    discord_bot.start_bot(app)
    socketio.run(app, debug=True)
