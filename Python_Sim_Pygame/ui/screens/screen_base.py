class ScreenBase:
    def __init__(self, title):
        self.title = title
        self.options = []

    def add_option(self, label, callback=None):
        self.options.append((label, callback))

    def get_options(self):
        return list(self.options)
