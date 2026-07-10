from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import vgamepad as vg
import json
import asyncio
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("New phone connected!")
    gamepad = vg.VDS4Gamepad()
    
    button_map = {
        "square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
        "cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
        "circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
        "triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
        "l1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
        "r1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
        "l2_btn": vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT,
        "r2_btn": vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT,
        "share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
        "options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
        "l3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
        "r3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
        "ps": vg.DS4_BUTTONS.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
        "touchpad": vg.DS4_BUTTONS.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD,
    }

    try:
        while True:
            data = await websocket.receive_text()
            state = json.loads(data)
            
            gamepad.reset()
            
            for btn, is_pressed in state.get('buttons', {}).items():
                if is_pressed and btn in button_map:
                    if btn in ["ps", "touchpad"]:
                        gamepad.press_special_button(button_map[btn])
                    else:
                        gamepad.press_button(button_map[btn])

            dpad = state.get('dpad', {})
            up = dpad.get('up', False)
            down = dpad.get('down', False)
            left = dpad.get('left', False)
            right = dpad.get('right', False)

            if up and left:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST)
            elif up and right:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST)
            elif down and left:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST)
            elif down and right:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST)
            elif up:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH)
            elif down:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH)
            elif left:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST)
            elif right:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST)
            else:
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)

            sticks = state.get('sticks', {})
            lx = sticks.get('lx', 0.0)
            ly = sticks.get('ly', 0.0)
            rx = sticks.get('rx', 0.0)
            ry = sticks.get('ry', 0.0)
            
            gamepad.left_joystick_float(x_value_float=lx, y_value_float=-ly)
            gamepad.right_joystick_float(x_value_float=rx, y_value_float=-ry)

            triggers = state.get('triggers', {})
            l2 = triggers.get('l2', 0.0)
            r2 = triggers.get('r2', 0.0)
            
            gamepad.left_trigger_float(value_float=l2)
            gamepad.right_trigger_float(value_float=r2)

            gamepad.update()

    except WebSocketDisconnect:
        print("Phone disconnected")

if __name__ == "__main__":
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    
    print(f"\n======================================")
    print(f"Phone Console Server Started!")
    print(f"Open this URL on your phone's browser:")
    print(f"http://{IP}:8000")
    print(f"======================================\n")
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="error")
