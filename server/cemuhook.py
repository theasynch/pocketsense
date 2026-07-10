import asyncio
import struct
import binascii
import time
import zlib

class CemuhookProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.clients = set()
        self.packet_count = 0
        self.transport = None
        self.server_id = 12345678

    def connection_made(self, transport):
        self.transport = transport
        print("Cemuhook UDP Server listening on port 26760")

    def datagram_received(self, data, addr):
        if len(data) < 16:
            return
        magic = data[0:4]
        if magic != b'DSUC':
            return
        
        protocol_ver = struct.unpack('<H', data[4:6])[0]
        packet_len = struct.unpack('<H', data[6:8])[0]
        crc = struct.unpack('<I', data[8:12])[0]
        client_id = struct.unpack('<I', data[12:16])[0]

        message_type = struct.unpack('<I', data[16:20])[0]

        if message_type == 0x100000: # Protocol Version Information
            self.send_protocol_info(addr)
        elif message_type == 0x100001: # Ports Information
            self.send_ports_info(addr)
            self.clients.add(addr)

    def _build_header(self, message_type, payload):
        # 16-byte header
        # D S U S, protocol ver (1001), packet len, crc32 (0 for now, calculate later), server id
        magic = b'DSUS'
        version = 1001
        packet_len = len(payload) + 4 # +4 for message_type
        server_id = self.server_id

        header = struct.pack('<4sHHII', magic, version, packet_len, 0, server_id)
        msg_type_bytes = struct.pack('<I', message_type)
        
        full_packet = header + msg_type_bytes + payload
        
        # Calculate CRC32 of everything except the CRC32 field itself
        # So we calculate CRC of magic + version + packet_len + 0 + server_id + type + payload
        crc = zlib.crc32(full_packet) & 0xffffffff
        
        # Replace CRC in header
        header = struct.pack('<4sHHII', magic, version, packet_len, crc, server_id)
        return header + msg_type_bytes + payload

    def send_protocol_info(self, addr):
        # type 0x100000
        payload = struct.pack('<H', 1001)
        packet = self._build_header(0x100000, payload)
        self.transport.sendto(packet, addr)

    def send_ports_info(self, addr):
        # type 0x100001
        # Pad ID (0), State (2=Connected), Model (2=DS4), Connection (2=Bluetooth), MAC (6 bytes), Battery (0xEE)
        payload = struct.pack('<BBBB6sB', 0, 2, 2, 2, b'\x00\x11\x22\x33\x44\x55', 0xEE)
        payload += b'\x00' # terminator
        packet = self._build_header(0x100001, payload)
        self.transport.sendto(packet, addr)

    def broadcast_data(self, state):
        if not self.clients:
            return
            
        self.packet_count += 1
        
        # type 0x100002
        # Pad ID (0), State (2), Model (2), Connection (2), MAC (6), Battery (0xEE), IsActive (1)
        part1 = struct.pack('<BBBB6sBB', 0, 2, 2, 2, b'\x00\x11\x22\x33\x44\x55', 0xEE, 1)
        
        # Packet Counter (4)
        part2 = struct.pack('<I', self.packet_count)
        
        # Buttons 1 & 2 (2 bytes) -> We are sending 0 since vgamepad handles buttons.
        # But wait, DS4W might override if it's 0. Let's send 0s for now.
        part3 = struct.pack('<H', 0)
        
        # PS button (1 byte)
        part4 = struct.pack('<B', 0)
        
        # Touch, Lx, Ly, Rx, Ry, L2, R2 (7 bytes) -> all 0
        part5 = struct.pack('<BBBBBBB', 0, 128, 128, 128, 128, 0, 0)
        
        # Motion data
        motion = state.get('motion', {})
        accel_x = motion.get('accelX', 0.0)
        accel_y = motion.get('accelY', 0.0)
        accel_z = motion.get('accelZ', 0.0)
        
        pitch = motion.get('gyroPitch', 0.0)
        yaw = motion.get('gyroYaw', 0.0)
        roll = motion.get('gyroRoll', 0.0)
        
        # Cemuhook expects Gs for accel, deg/s for gyro.
        # 6 floats -> 24 bytes
        # Pitch, Yaw, Roll, AccelX, AccelY, AccelZ
        part6 = struct.pack('<ffffff', pitch, yaw, roll, accel_x, accel_y, accel_z)
        
        # Timestamp (8 bytes microsecond)
        timestamp = int(time.time() * 1000000)
        part7 = struct.pack('<Q', timestamp)
        
        payload = part1 + part2 + part3 + part4 + part5 + b'\x00\x00' + part6 + part7 # Added 2 bytes padding? No, let's check packet size.
        # Wait, the official spec:
        # 0: pad id (1)
        # 1: state (1)
        # 2: model (1)
        # 3: connection (1)
        # 4: mac (6)
        # 10: battery (1)
        # 11: is active (1)
        # 12: packet counter (4)
        # 16: buttons (2) -> bitmask
        # 18: PS button (1)
        # 19: reserved (1) 
        # 20: lx (1)
        # 21: ly (1)
        # 22: rx (1)
        # 23: ry (1)
        # 24: l2 (1)
        # 25: r2 (1)
        # 26: first touch (6)
        # 32: second touch (6)
        # 38: accel x (4)
        # 42: accel y (4)
        # 46: accel z (4)
        # 50: pitch (4)
        # 54: yaw (4)
        # 58: roll (4)
        # 62: sensor timestamp (8)
        
        # Let's rebuild properly:
        b_pad = struct.pack('<BBBB6sBB', 0, 2, 2, 2, b'\x00\x11\x22\x33\x44\x55', 0xEE, 1) # 12 bytes
        b_packet = struct.pack('<I', self.packet_count) # 4 bytes
        b_buttons = struct.pack('<HBB', 0, 0, 0) # 4 bytes (buttons, ps, reserved)
        b_sticks = struct.pack('<BBBBBB', 128, 128, 128, 128, 0, 0) # 6 bytes (lx, ly, rx, ry, l2, r2)
        b_touch = b'\x00' * 12 # 12 bytes
        b_motion = struct.pack('<ffffff', accel_x, accel_y, accel_z, pitch, yaw, roll) # 24 bytes
        b_time = struct.pack('<Q', timestamp) # 8 bytes
        
        payload = b_pad + b_packet + b_buttons + b_sticks + b_touch + b_motion + b_time # 70 bytes total payload
        
        packet = self._build_header(0x100002, payload)
        
        for client in list(self.clients):
            try:
                self.transport.sendto(packet, client)
            except Exception:
                self.clients.remove(client)
