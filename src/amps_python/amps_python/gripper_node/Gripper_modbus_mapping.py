# Modbus address and register definitions
GRIPPER_ADDRESS = 0x09

# Gripper Input Registers
GRIPPER_INPUT_REG_OFFSET = 0x03E8
GRIPPER_ACTION_REQUEST_REG = 0x0000
GRIPPER_POSITION_REQUEST_REG = 0x0003
GRIPPER_SPEED_REQUEST_REG = 0x0004
GRIPPER_FORCE_REQUEST_REG = 0x0005

# Gripper Output Registers
GRIPPER_OUTPUT_REG_OFFSET = 0x07D0
GRIPPER_STATUS_REG = 0x0000
GRIPPER_FAULT_STATUS_REG = 0x0002
GRIPPER_POSITION_REQUEST_ECHO_REG = 0x0003
GRIPPER_POSITION_REG = 0x0004
GRIPPER_CURRENT_REG = 0x0005

## Gripper Action Request Mapping
# rACT: First action to be made prior to any other actions, rACT bit will activate the Gripper. Clear rACT to reset the Gripper and clear fault status.
# 0 - Deactivate Gripper.
# 1 - Activate Gripper (must stay on after activation routine is completed).
GRIPPER_ACTION_REQUEST_ACTIVATE_GRIPPER_BIT = 2**0

# rGTO: The "Go To" action moves the Gripper fingers to the requested position using the configuration defined by the other registers.
# 0 - Stop.
# 1 - Move to requested position.
GRIPPER_ACTION_REQUEST_GO_TO_BIT = 2**3

# rATR: Automatic Release routine action slowly opens the Gripper fingers until all motion axes reach their mechanical limits. After all
# motion is completed, the Gripper sends a fault signal and needs to be reactivated before any other motion is performed. The rATR bit
# overrides all other commands excluding the activation bit (rACT).
# 0 - Normal.
# 1 - Emergency auto-release.
GRIPPER_ACTION_REQUEST_AUTO_RELEASE_BIT = 2**4

# rARD: Auto-release direction. When auto-releasing, rARD commands the direction of the movement. The rARD bit should be set prior
# to or at the same time as the rATR bit, as the motion direction is set when the auto-release is initiated.
# 0 - Closing auto-release
# 1 - Opening auto-release
GRIPPER_ACTION_REQUEST_AUTO_RELEASE_DIR_BIT = 2**5


## Gripper Status Register Mapping
GRIPPER_STATUS__BIT = 2**0



# def EstablishAndEnsureConnection():
#   while (not bluetoothConnected):
#     if (BLE.hasClient()):
#       bluetoothConnected = true;
#       Serial.println("Bluetooth client connected!");
#     else:
#       Serial.println("Bluetooth client not connected, waiting...");
#       delay(500);

#   while (not gripperConnected):
#     regValue = RTU.readHoldingRegister(gripperAddress, 0x0000)
#     softSerial.write(requestMsg, sizeof(requestMsg))
#     softSerial.flush()
#     softSerial.available()

#         if (regValue != 0xFFFF)
#     {
#       gripperConnected = true;
#       Serial.println("Robotiq Gripper connected!");
#     }
#     else
#     {
#       Serial.println("Robotiq Gripper not found, retrying...");
#       delay(500);
#     }
#   }
# }


#     uint8_t address = cmd[0];
#     uint8_t function = cmd[1];
#     if (function == 0x03) // Read Holding Registers
#     {
#       uint16_t startReg = (cmd[2] << 8) | cmd[3];
#       uint16_t numRegs = (cmd[4] << 8) | cmd[5];
#       RTU.readHoldingRegister(address, startReg, numRegs);
#       for (uint16_t i = 0; i < numRegs; i++)
#       {
#         uint16_t regValue = RTU.readHoldingRegister(address, startReg + i);
#         BLE.write((regValue >> 8) & 0xFF);
#         BLE.write(regValue & 0xFF);
#       }
#     }
#     if (function == 0x04) // Read Input Registers
#     {
#     }
#     if (function == 0x16) // Preset Multiple Registers
#     {
#       /* code */
#     }
