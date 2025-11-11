"""Joystick adapter that reads a radio-control joystick via CAN.

This preserves the original CAN-based logic but removes the turtle
timer dependency. Use `poll()` once per frame from the Pygame main loop
to process pending CAN messages non-blocking. The class exposes:

- Joystick() constructor — tries to open CAN bus; sets `available` flag
- poll() — non-blocking processing of any received CAN messages
- getJoystickValues() -> (lx, ly, rx, ry)
- getLightsValues() -> list of booleans
- currentMode, hasChangedMode for selector messages

If CAN is not available the adapter will set `available = False` and
main should fall back to keyboard control.
"""
import struct
import time
try:
    import can
except Exception:
    can = None
from Player import GLV as GVL
import Player.Player as player


class Joystick:
    def __init__(self):
        # CAN configuration (same as original)
        self.BITRATE = 500000
        self.CAN_CHANNEL_JOYSTICK = 0x200
        self.CAN_CHANNEL_SELETORA = 0x201
        self.CAN_CHANNEL_LIGHTS = 0x202
        self.CAN_CHANNEL_SPEED = 0x203

        # state
        self.lights = [False, False, False, False, False]
        self.eixo_esquerdo_x = 0.0
        self.eixo_esquerdo_y = 0.0
        self.eixo_direito_x = 0.0
        self.eixo_direito_y = 0.0
        self.currentMode = 0
        self.currentSpeed = 0
        self.hasChangedMode = False
        self.hasChangedSpeed = False

        self.bus = None
        self.available = False

        # try to open CAN bus
        try:
            self.configCan()
            self.available = True
        except Exception as e:
            # keep available False and continue; main will fallback to keyboard
            print(f"[Joystick] CAN not available: {e}. Falling back to keyboard.")

    def configCan(self):
        if can is None:
            raise RuntimeError("python-can is not installed")
        # create bus (this may raise if no hardware)
        self.bus = can.interface.Bus(channel='PCAN_USBBUS1', interface='pcan', bitrate=self.BITRATE)
        # drain any existing messages
        while True:
            msg = self.bus.recv(timeout=0.01)
            if msg is None:
                break

    def poll(self):
        """Non-blocking: read available CAN messages and update internal state.

        Call this once per frame from the Pygame main loop.
        """
        if not self.available or self.bus is None:
            return

        # read all currently-queued messages without blocking
        while True:
            try:
                msg = self.bus.recv(timeout=0.0)
            except Exception:
                # if bus errors happen, mark unavailable and stop
                self.available = False
                return
            if msg is None:
                break
            try:
                # only handle standard 11-bit frames as before
                if msg.is_extended_id:
                    continue
                data = msg.data
                if msg.arbitration_id == self.CAN_CHANNEL_JOYSTICK:
                    # expect 8 bytes: 4 signed 16-bit (little-endian)
                    if len(data) >= 8:
                        Joystick_X_1 = struct.unpack('<h', data[0:2])[0]
                        Joystick_Y_1 = struct.unpack('<h', data[2:4])[0]
                        Joystick_X_2 = struct.unpack('<h', data[4:6])[0]
                        Joystick_Y_2 = struct.unpack('<h', data[6:8])[0]
                        # original converted to float with 1 decimal place
                        self.eixo_esquerdo_x = Joystick_X_1 / 10.0
                        self.eixo_esquerdo_y = Joystick_Y_1 / 10.0
                        self.eixo_direito_x = Joystick_X_2 / 10.0
                        self.eixo_direito_y = Joystick_Y_2 / 10.0
                elif msg.arbitration_id == self.CAN_CHANNEL_SELETORA:
                    if len(data) >= 2:
                        selectedMode = struct.unpack('<h', data[0:2])[0]
                        if selectedMode != self.currentMode:
                            self.currentMode = selectedMode
                            self.hasChangedMode = True
                elif msg.arbitration_id == self.CAN_CHANNEL_LIGHTS:
                    if len(data) >= 1:
                        lightsState = struct.unpack('<B', data[0:1])[0]
                        # keep 5 lights as original
                        self.lights = [(lightsState & (1 << i)) != 0 for i in range(5)]
                elif msg.arbitration_id == self.CAN_CHANNEL_SPEED:
                    if len(data) >= 1:
                        selectedSpeed = struct.unpack('<B', data[0:1])[0]
                        if selectedSpeed != self.currentSpeed:
                            self.currentSpeed = selectedSpeed
                            self.hasChangedSpeed = True
            except Exception:
                # ignore malformed messages
                continue

    def getJoystickValues(self):
        # return left_x, left_y, right_x, right_y
        return self.eixo_esquerdo_x, self.eixo_esquerdo_y, self.eixo_direito_x, self.eixo_direito_y

    def getLightsValues(self):
        return self.lights
