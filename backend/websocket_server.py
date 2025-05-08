import asyncio
import json
import websockets
from fastapi import FastAPI, Request
import uvicorn
from threading import Thread

connected_clients = set()
app = FastAPI()

# WebSocket-server
async def websocket_handler(websocket):
    print("WebSocket client connected")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print("Received from client:", message)
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket client disconnected")
    finally:
        connected_clients.remove(websocket)

# HTTP POST-endpoint som tar emot detection-data
@app.post("/detection_output")
async def detection_output(request: Request):
    try:
        data = await request.json()
        print("Received detection:", data)
        await broadcast_to_clients(data)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}

# Funktion som skickar data till alla WebSocket-klienter
async def broadcast_to_clients(data):
    if connected_clients:
        message = json.dumps(data)
        await asyncio.gather(*[client.send(message) for client in connected_clients])

# Kör FastAPI på en egen tråd
def run_http_api():
    uvicorn.run(app, host="0.0.0.0", port=7000) #var man ska skicka json paket!!!!!!!!!!!!!!!!!!!!!!

# Kör WebSocket-servern separat på port 8765
async def start_websocket_server():
    print("WebSocket server listening on ws://localhost:1234")
    async with websockets.serve(websocket_handler, "0.0.0.0", 1234): #DETTA MÅSTE ÖVERRENSTÄMMA MED SRC/PAGES/INDEX.TSX
        await asyncio.Future()  # Kör för evigt

# Starta båda
if __name__ == "__main__":
    Thread(target=run_http_api, daemon=True).start()
    asyncio.run(start_websocket_server())
