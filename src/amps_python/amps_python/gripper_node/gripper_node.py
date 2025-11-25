#!/usr/bin/env python3
# src/gripper_node.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
import threading
import queue
import time
import asyncio

from amps_cpp.action import MoveGripper
from amps_python.resources.nus_modbus import build_read_request, build_write_multiple, verify_and_strip_crc

from bleak import BleakClient

# NUS UUIDs
NUS_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

DEVICE_ADDR = "58:CF:79:D9:F7:32"  # ESP32 MAC
DEVICE_NAME = "UR Robotiq Gripper"  # device name
SLAVE_ID = 0x09                     # Robotiq slave id

class GripperNode(Node):
    def __init__(self):
        super().__init__("gripper_node")
        self.get_logger().info("Starting gripper node")

        # status: small atomic dict, updated by BLE worker
        self.status = {
            "position": 0,    # 0..255
            "current": 0,
            "gobj": 0,        # object detection bits from byte0 (gOBJ)
            "gact": 0,
            "ggto": 0,
            "moving": False,
            "ts": time.time(),
        }

        # queue -> BLE worker
        self.cmd_q = queue.Queue()

        # start BLE worker thread
        self.ble_thread = threading.Thread(target=self._ble_thread_main, daemon=True)
        self.ble_thread.start()

        # action server
        self._action_srv = ActionServer(self, MoveGripper, 'gripper/move', self.execute_cb)

    # ---------------- BLE thread & asyncio ----------------
    def _ble_thread_main(self):
        while True:
            try:
                asyncio.run(self._ble_main())
            except Exception as e:
                self.get_logger().error(f"BLE thread error: {e}")
            time.sleep(1.0)  # reconnect delay

    async def _ble_main(self):
        async with BleakClient(DEVICE_ADDR, timeout=5.0) as client:
            self.get_logger().info("BLE connected")
            await client.start_notify(NUS_RX, self._handle_rx)

            while True:
                # process queued commands
                await self._process_cmds(client)

                # If device doesn't push status automatically, poll:
                req = build_read_request(SLAVE_ID, 3, 0x07D0, 3)  # read 3 registers from 0x07D0
                self.get_logger().info(f"ble main sending read request: {req.hex()}")
                # send raw bytes + LF
                await client.write_gatt_char(NUS_TX, req + b'\n')

                await asyncio.sleep(0.05)  # 20Hz poll (manual notes recommend up to 200Hz, use 50Hz safe)

    async def _process_cmds(self, client):
        try:
            while True:
                cmd = self.cmd_q.get_nowait()
                if cmd["type"] == "move":
                    # The Robotiq example uses FC16 writing 3 registers starting 0x03E8
                    # Byte layout: registers 0x03E8 (ACTION REQUEST + options), 0x03E9 (position), 0x03EA (speed+force)
                    # We'll build the register bytes accordingly (little-endian data area per manual note)
                    action_byte = cmd.get("action", 0x09)  # rACT + rGTO = typical 0x09 for activate+gto (or 0x09 per example)
                    # But to "go to" we should set rGTO=1 in ACTION REQUEST (bit value), manual examples use 0x09
                    rpr = int(cmd["position"]) & 0xFF
                    rsp = int(cmd["speed"]) & 0xFF
                    rfr = int(cmd["force"]) & 0xFF
                    # registers are 16-bit words. Example encodings in manual show two bytes per register.
                    # Compose registers bytes (big-endian register words): for writing we follow examples from manual.
                    # We'll write 3 registers (6 bytes): reg0 = action_byte << 8 | 0x00, reg1 = 0x00 << 8 | rpr, reg2 = (rsp<<8) | rfr
                    reg0 = bytes([action_byte, 0x00])
                    reg1 = bytes([0x00, rpr])
                    reg2 = bytes([rsp, rfr])
                    regs = reg0 + reg1 + reg2
                    frame = build_write_multiple(SLAVE_ID, 0x03E8, regs)
                    await client.write_gatt_char(NUS_TX, frame + b'\n')
                    self.status["moving"] = True
        except queue.Empty:
            return

    # ---------------- RX handler ----------------
    def _handle_rx(self, sender, data: bytearray):
        # BLE notifications arrive here. They may contain raw modbus frames possibly with LF.
        b = bytes(data).strip()
        # Some devices might send multiple frames at once, but keep minimal: assume single frame
        ok, payload = verify_and_strip_crc(b)
        if not ok:
            # maybe the LF separates: try strip trailing LF or CRLF earlier; already stripped
            return
        # payload is bytes without CRC. Parse slave, function, rest
        if len(payload) < 2:
            return
        slave = payload[0]
        func = payload[1]
        # handle read response (function 3 with N bytes)
        if func == 3 or func == 4:
            # payload[2] = byte count
            if len(payload) >= 3:
                bytecount = payload[2]
                data_bytes = payload[3:3+bytecount]
                # Manual: first register (07D0) has bytes 0..1 => gripper status, reserved
                # second register 07D1 -> fault + position echo
                # third register 07D2 -> position + current
                # Parse with examples from manual.
                if bytecount >= 6:
                    b0 = data_bytes[0]  # GRIPPER STATUS low byte
                    b1 = data_bytes[1]  # reserved
                    b2 = data_bytes[2]
                    b3 = data_bytes[3]
                    b4 = data_bytes[4]
                    b5 = data_bytes[5]
                    # position usually in byte 4 (index 4)
                    position = b4
                    current = b5
                    # decode gOBJ/gGTO/gACT bits from b0 per manual if needed
                    gobj = (b0 >> 6) & 0x03
                    ggto = (b0 >> 1) & 0x01
                    gact = b0 & 0x01
                    self.status.update({
                        "position": position,
                        "current": current,
                        "gobj": gobj,
                        "ggto": ggto,
                        "gact": gact,
                        "moving": (ggto == 1 and gobj == 0),  # simple heuristic: gGTO==1 and gOBJ==0 -> moving
                        "ts": time.time(),
                    })

    # ---------------- Action server ----------------
    async def execute_cb(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(f"Action goal: pos={goal.position} speed={goal.speed} force={goal.force}")

        # enqueue the move command to BLE worker
        self.cmd_q.put({
            "type": "move",
            "position": int(goal.position),
            "speed": int(goal.speed),
            "force": int(goal.force),
            # "action": 0x09,  # optional explicit action byte
        })

        feedback = MoveGripper.Feedback()

        # Wait loop: poll shared status and publish feedback.
        start = time.time()
        timeout = 10.0  # seconds
        while True:
            # handle cancel
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info("Goal canceled")
                result = MoveGripper.Result()
                result.success = False
                result.message = "canceled"
                return result

            cur = self.status
            feedback.current_position = int(cur["position"])
            feedback.current_force = int(cur["current"])
            feedback.moving = bool(cur["moving"])
            goal_handle.publish_feedback(feedback)

            # success condition per manual: gOBJ indicates stopped due to contact OR fingers at requested pos
            # The manual shows gOBJ==2 or 3 indicate stopped; we'll treat moving==False as finished.
            if not cur["moving"]:
                self.get_logger().info("Move finished by status")
                result = MoveGripper.Result()
                result.success = True
                result.message = "ok"
                goal_handle.succeed()
                return result

            if time.time() - start > timeout:
                self.get_logger().warn("Move timeout")
                result = MoveGripper.Result()
                result.success = False
                result.message = "timeout"
                goal_handle.abort()
                return result

            await asyncio.sleep(0.02)


def main(args=None):
    rclpy.init(args=args)
    node = GripperNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
