from .screen_base import ScreenBase

class SensoresScreen(ScreenBase):
    def __init__(self, player, goto):
        super().__init__('Sensores')
        self.add_option('Sensor A: --', None)
        self.add_option('Sensor B: --', None)
        self.add_option('Sensor C: --', None)
        self.add_option('Voltar', lambda: goto('Main'))
