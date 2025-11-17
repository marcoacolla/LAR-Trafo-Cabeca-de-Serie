from .screen_base import ScreenBase

class JoystickScreen(ScreenBase):
    def __init__(self, player, goto, control_mode):
        super().__init__('Joystick')
        self.add_option('Control: ' + control_mode.upper(), None)
        self.add_option('Set Speed Rápida', lambda: goto('Joystick'))
        self.add_option('Set Speed Média', lambda: goto('Joystick'))
        self.add_option('Set Speed Lenta', lambda: goto('Joystick'))
