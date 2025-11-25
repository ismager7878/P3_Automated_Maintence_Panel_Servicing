# nus_modbus.py
# Minimal Modbus RTU helpers: CRC16 (Modbus), build frame, parse response.

def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF

def append_crc(frame_without_crc: bytes) -> bytes:
    crc = crc16_modbus(frame_without_crc)
    # Modbus appends low byte first, then high byte
    return frame_without_crc + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def build_read_request(slave: int, func: int, addr: int, count: int) -> bytes:
    # addr and count are 16-bit
    pdu = bytes([slave, func, (addr >> 8) & 0xFF, addr & 0xFF, (count >> 8) & 0xFF, count & 0xFF])
    return append_crc(pdu)

def build_write_multiple(slave: int, start_addr: int, registers: bytes) -> bytes:
    # registers: bytes (2 * n registers)
    num_regs = len(registers) // 2
    pdu = bytes([slave, 16, (start_addr >> 8) & 0xFF, start_addr & 0xFF,
                 (num_regs >> 8) & 0xFF, num_regs & 0xFF, len(registers)]) + registers
    return append_crc(pdu)

def verify_and_strip_crc(frame: bytes) -> tuple[bool, bytes]:
    if len(frame) < 3:
        return False, b''
    payload = frame[:-2]
    recv_crc = frame[-2] | (frame[-1] << 8)
    calc = crc16_modbus(payload)
    return calc == recv_crc, payload
