from .screen_base import ScreenBase

class ControlScreen(ScreenBase):
    def __init__(self, player, goto):
        super().__init__('Controle')
        # Image placeholder and back option
        self.add_option('', None)  # Placeholder for image display
        self.add_option('Voltar', lambda: goto('Main'))
