from .screen_base import ScreenBase

class MainScreen(ScreenBase):
    def __init__(self, player, goto):
        super().__init__('Main')
        # example options
        self.add_option(f'Mode: {getattr(player, "curve_mode", "unknown")}', None)
        self.add_option('Sensores', lambda: goto('Sensores'))
        self.add_option('Toggle Hardcore', lambda: goto('Main'))
        self.add_option('Reset Trafo', lambda: goto('Main'))
