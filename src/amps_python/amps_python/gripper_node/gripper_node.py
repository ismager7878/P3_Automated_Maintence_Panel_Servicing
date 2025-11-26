from ast import In
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

        # status dict, updated by BLE worker
        self.status = {
            #"position": 0,    # 0..255
            #"current": 0,
            "gOBJ": 0,          # Object detection 
                                # 0 = In motion towards requested position
                                # 1 = Stopped object detected opening
                                # 2 = Stopped object detected closing
                                # 3 = Stopped at requested position no object detected

            "gACT": 0,          # Activation status bit (gACT)
                                # 0 = Gripper resetting
                                # 1 = Activated

            "gGTO": 0,          # Go to status bit (gGTO)
                                # 0 = Stopped or performing activation
                                # 1 = Moving to requested position

            "gFLT": 0,          # Fault code (gFLT)
            "gCU": 0,           # Current position 0..255 0 = fully open, 255 = fully closed
            "gPO" : 0,          # Gripper current draw 0..255 multiply by 10 to get current in mA
            "moving": False,
            "ts": time.time(),  # Data timestamp
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

                # Poll status registers
                req = build_read_request(SLAVE_ID, 3, 0x07D0, 3)  # read 3 registers from 0x07D0
                self.get_logger().info(f"ble main sending read request: {req.hex()}")
                # send raw bytes + LF
                await client.write_gatt_char(NUS_TX, req + b'\n')

                await asyncio.sleep(0.1)  # 10Hz poll (manual recommend up to 200Hz but use 10Hz to be safe)

    async def _process_cmds(self, client):
        try:
            while True:
                # Safely retrieve a command 
                cmd = self.cmd_q.get_nowait()
                
                # Prepare action byte
                if cmd["type"] == "move":
                    action_byte = 0x09  # rACT=1 + rGTO=1
                if cmd["type"] == "reset":
                    action_byte = 0x00  # clears rACT and rGTO
                if cmd["type"] == "init":
                    action_byte = 0x08  # rACT=1, rGTO=0
                
                # Prepare 8-bit registers
                rPR = int(cmd["position"]) & 0xFF
                rSP = int(cmd["speed"]) & 0xFF
                rFR = int(cmd["force"]) & 0xFF

                # Build  16-bit register
                reg0 = bytes([action_byte, 0x00])
                reg1 = bytes([0x00, rPR])
                reg2 = bytes([rSP, rFR])
                regs = reg0 + reg1 + reg2
                
                # Build modbus frame and send to gripper
                frame = build_write_multiple(SLAVE_ID, 0x03E8, regs)
                await client.write_gatt_char(NUS_TX, frame + b'\n')
                self.status["moving"] = True  # set moving true on command send
        except queue.Empty:
            return

    # ---------------- RX handler ----------------
    def _handle_rx(self, sender, data: bytearray):
        # Clear LF from data.
        b = bytes(data).strip()
        ok, payload = verify_and_strip_crc(b)
        if not ok:
            self.get_logger().error("Received invalid CRC data, maybe too much was stripped by doing .strip()?")
            return
        # Return early if the payload is too short.
        if len(payload) < 2:
            return
        slave = payload[0]
        func = payload[1]
        # If the function is read response (3 or 4), parse the data.
        if func == 3 or func == 4:
            # Assure again that payload is long enough to contain byte count.
            if len(payload) >= 3:
                byteCount = payload[2]
                data_bytes = payload[3:3+byteCount]
                try:
                    b0 = data_bytes[0]
                    b1 = data_bytes[1]
                    b2 = data_bytes[2]
                    b3 = data_bytes[3]
                    b4 = data_bytes[4]
                    b5 = data_bytes[5]
                except IndexError:
                    self.get_logger().warn("Received data too short to parse full gripper status")

                position = b4
                current = b5
                gobj = (b0 >> 6) & 0x03
                ggto = (b0 >> 3) & 0x01
                gact = b0 & 0x01
                gflt = b2 & 0x0F
                moving = (ggto == 1 and gobj == 0)
                self.status.update({
                    "gOBJ": gobj,
                    "gACT": gact,
                    "gGTO": ggto,
                    "gFLT": gflt,
                    "gCU": position,
                    "gPO": current,
                    "moving": moving,
                    "ts": time.time(),
                })

    # ---------------- Action server ----------------
    async def execute_cb(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(f"Action goal: type={goal.type} pos={goal.position} speed={goal.speed} force={goal.force}")

        # Build the move command and put in queue for BLE worker
        self.cmd_q.put({
            "type": str(goal.type),
            "position": int(goal.position),
            "speed": int(goal.speed),
            "force": int(goal.force),
        })

        feedback = MoveGripper.Feedback()

        # Wait loop: poll shared status and publish feedback.
        start = time.time()
        timeout = 10.0  # seconds
        while True:
            # Handle cancel
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

            # If not moving anymore then we are done
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
