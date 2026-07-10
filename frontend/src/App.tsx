import { useEffect, useRef, useState, useCallback } from 'react';
import './index.css';

const initialState = {
  buttons: {
    square: false, cross: false, circle: false, triangle: false,
    l1: false, r1: false, l2_btn: false, r2_btn: false,
    share: false, options: false, l3: false, r3: false,
    ps: false, touchpad: false
  },
  dpad: {
    up: false, down: false, left: false, right: false
  },
  sticks: {
    lx: 0.0, ly: 0.0, rx: 0.0, ry: 0.0
  },
  triggers: {
    l2: 0.0, r2: 0.0
  },
  motion: {
    accelX: 0.0, accelY: 0.0, accelZ: 0.0,
    gyroPitch: 0.0, gyroYaw: 0.0, gyroRoll: 0.0
  }
};

function App() {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [started, setStarted] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const stateRef = useRef(JSON.parse(JSON.stringify(initialState)));
  const loopRef = useRef<number>(0);

  const startConnection = async () => {
    // Request device motion permission if on iOS 13+
    if (typeof (DeviceMotionEvent as any).requestPermission === 'function') {
      try {
        const permissionState = await (DeviceMotionEvent as any).requestPermission();
        if (permissionState === 'granted') {
          window.addEventListener('devicemotion', handleMotion);
        }
      } catch (e) {
        console.error("Gyro permission error", e);
      }
    } else {
      window.addEventListener('devicemotion', handleMotion);
    }

    setStarted(true);
    setConnecting(true);

    let wsUrl = "";
    // Check if we are on localtunnel, ngrok, or local IP
    if (window.location.protocol === 'https:') {
      wsUrl = `wss://${window.location.hostname}/ws`;
    } else {
      const port = window.location.port === '5173' ? '8000' : window.location.port;
      wsUrl = `ws://${window.location.hostname}:${port}/ws`;
    }
    
    console.log("Connecting to", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setConnecting(false);
    };

    ws.onclose = () => {
      setConnected(false);
      setConnecting(false);
    };

    ws.onerror = (e) => {
      console.error("WebSocket error", e);
      setConnecting(false);
    };

    wsRef.current = ws;

    const loop = () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(stateRef.current));
      }
      loopRef.current = requestAnimationFrame(loop);
    };
    loopRef.current = requestAnimationFrame(loop);
  };

  const handleMotion = (event: DeviceMotionEvent) => {
    // DeviceMotionEvent uses m/s^2 for accel, Cemuhook expects Gs (1G = 9.8m/s^2)
    if (event.accelerationIncludingGravity) {
      stateRef.current.motion.accelX = -(event.accelerationIncludingGravity.x || 0) / 9.8;
      stateRef.current.motion.accelY = -(event.accelerationIncludingGravity.y || 0) / 9.8;
      stateRef.current.motion.accelZ = -(event.accelerationIncludingGravity.z || 0) / 9.8;
    }
    // rotationRate is in degrees/second
    if (event.rotationRate) {
      stateRef.current.motion.gyroPitch = event.rotationRate.alpha || 0;
      stateRef.current.motion.gyroYaw = event.rotationRate.beta || 0;
      stateRef.current.motion.gyroRoll = event.rotationRate.gamma || 0;
    }
  };

  useEffect(() => {
    return () => {
      if (loopRef.current) cancelAnimationFrame(loopRef.current);
      if (wsRef.current) wsRef.current.close();
      window.removeEventListener('devicemotion', handleMotion);
    };
  }, []);

  const setBtn = useCallback((btn: string, val: boolean) => {
    stateRef.current.buttons[btn] = val;
    if (btn === 'l2_btn') stateRef.current.triggers.l2 = val ? 1.0 : 0.0;
    if (btn === 'r2_btn') stateRef.current.triggers.r2 = val ? 1.0 : 0.0;
    document.getElementById(`btn-${btn}`)?.classList.toggle('active', val);
  }, []);

  const setDpad = useCallback((dir: string, val: boolean) => {
    stateRef.current.dpad[dir] = val;
    document.getElementById(`dpad-${dir}`)?.classList.toggle('active', val);
  }, []);

  const handleJoystick = useCallback((e: React.TouchEvent | React.MouseEvent, side: 'l' | 'r') => {
    e.preventDefault();
    const zone = document.getElementById(`joy-zone-${side}`);
    const knob = document.getElementById(`joy-knob-${side}`);
    if (!zone || !knob) return;

    const rect = zone.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    let clientX, clientY;
    if ('touches' in e) {
      const touch = Array.from(e.touches).find(t => 
        t.clientX >= rect.left && t.clientX <= rect.right &&
        t.clientY >= rect.top && t.clientY <= rect.bottom
      ) || e.changedTouches[0];
      clientX = touch.clientX;
      clientY = touch.clientY;
    } else {
      clientX = (e as React.MouseEvent).clientX;
      clientY = (e as React.MouseEvent).clientY;
    }

    const maxDist = rect.width / 2;
    let dx = clientX - centerX;
    let dy = clientY - centerY;
    
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxDist) {
      dx = (dx / dist) * maxDist;
      dy = (dy / dist) * maxDist;
    }

    knob.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
    stateRef.current.sticks[`${side}x`] = dx / maxDist;
    stateRef.current.sticks[`${side}y`] = dy / maxDist;
  }, []);

  const resetJoystick = useCallback((side: 'l' | 'r') => {
    const knob = document.getElementById(`joy-knob-${side}`);
    if (knob) {
      knob.style.transform = `translate(-50%, -50%)`;
      stateRef.current.sticks[`${side}x`] = 0.0;
      stateRef.current.sticks[`${side}y`] = 0.0;
    }
    setBtn(`${side}3`, false);
  }, [setBtn]);

  const btnProps = (id: string, type: 'btn' | 'dpad', key: string) => ({
    id,
    onTouchStart: (e: React.TouchEvent) => { e.preventDefault(); type === 'btn' ? setBtn(key, true) : setDpad(key, true); },
    onTouchEnd: (e: React.TouchEvent) => { e.preventDefault(); type === 'btn' ? setBtn(key, false) : setDpad(key, false); },
    onMouseDown: () => type === 'btn' ? setBtn(key, true) : setDpad(key, true),
    onMouseUp: () => type === 'btn' ? setBtn(key, false) : setDpad(key, false),
    onMouseLeave: () => type === 'btn' ? setBtn(key, false) : setDpad(key, false),
  });

  return (
    <>
      <div className="rotate-message">Please rotate your device</div>
      
      {!started && (
        <div className="overlay start-overlay">
          <h1>PocketSense</h1>
          <button className="start-btn" onClick={startConnection}>
            Connect & Enable Gyro
          </button>
        </div>
      )}

      {started && !connected && (
        <div className="overlay">
          <h1>{connecting ? 'CONNECTING...' : 'DISCONNECTED'}</h1>
          <p>Make sure the server is running on the laptop.</p>
        </div>
      )}

      <div className="controller-container">
        <div className="left-section">
          <div className="shoulder-container left">
            <div className="trigger-btn" {...btnProps('btn-l2_btn', 'btn', 'l2_btn')}>L2</div>
            <div className="shoulder-btn" {...btnProps('btn-l1', 'btn', 'l1')}>L1</div>
          </div>
          
          <div className="dpad-container">
            <div className="dpad-btn dpad-up" {...btnProps('dpad-up', 'dpad', 'up')}>▲</div>
            <div className="dpad-btn dpad-down" {...btnProps('dpad-down', 'dpad', 'down')}>▼</div>
            <div className="dpad-btn dpad-left" {...btnProps('dpad-left', 'dpad', 'left')}>◀</div>
            <div className="dpad-btn dpad-right" {...btnProps('dpad-right', 'dpad', 'right')}>▶</div>
          </div>

          <div 
            id="joy-zone-l" 
            className="joystick-zone left"
            onTouchStart={(e) => handleJoystick(e, 'l')}
            onTouchMove={(e) => handleJoystick(e, 'l')}
            onTouchEnd={() => resetJoystick('l')}
            onMouseDown={(e) => handleJoystick(e, 'l')}
            onMouseMove={(e) => e.buttons === 1 && handleJoystick(e, 'l')}
            onMouseUp={() => resetJoystick('l')}
            onMouseLeave={() => resetJoystick('l')}
            onDoubleClick={() => { setBtn('l3', true); setTimeout(() => setBtn('l3', false), 100); }}
          >
            <div id="joy-knob-l" className="joystick-knob"></div>
          </div>
        </div>

        <div className="center-section">
          <div className="glass-panel touchpad" {...btnProps('btn-touchpad', 'btn', 'touchpad')}>
          </div>
          
          <div className="center-buttons">
            <div className="small-btn" {...btnProps('btn-share', 'btn', 'share')}>SHARE</div>
            <div className="small-btn" {...btnProps('btn-options', 'btn', 'options')}>OPTIONS</div>
          </div>
          
          <div className="ps-button" {...btnProps('btn-ps', 'btn', 'ps')}>PS</div>
        </div>

        <div className="right-section">
          <div className="shoulder-container right">
            <div className="shoulder-btn" {...btnProps('btn-r1', 'btn', 'r1')}>R1</div>
            <div className="trigger-btn" {...btnProps('btn-r2_btn', 'btn', 'r2_btn')}>R2</div>
          </div>
          
          <div className="action-buttons">
            <div className="action-btn btn-triangle" {...btnProps('btn-triangle', 'btn', 'triangle')}>△</div>
            <div className="action-btn btn-square" {...btnProps('btn-square', 'btn', 'square')}>□</div>
            <div className="action-btn btn-circle" {...btnProps('btn-circle', 'btn', 'circle')}>○</div>
            <div className="action-btn btn-cross" {...btnProps('btn-cross', 'btn', 'cross')}>✕</div>
          </div>

          <div 
            id="joy-zone-r" 
            className="joystick-zone right"
            onTouchStart={(e) => handleJoystick(e, 'r')}
            onTouchMove={(e) => handleJoystick(e, 'r')}
            onTouchEnd={() => resetJoystick('r')}
            onMouseDown={(e) => handleJoystick(e, 'r')}
            onMouseMove={(e) => e.buttons === 1 && handleJoystick(e, 'r')}
            onMouseUp={() => resetJoystick('r')}
            onMouseLeave={() => resetJoystick('r')}
            onDoubleClick={() => { setBtn('r3', true); setTimeout(() => setBtn('r3', false), 100); }}
          >
            <div id="joy-knob-r" className="joystick-knob"></div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
