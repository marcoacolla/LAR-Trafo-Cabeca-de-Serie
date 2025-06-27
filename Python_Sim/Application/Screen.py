import turtle

# Classe para gerenciamento da tela
class Screen:

    # Método construtor da classe
    def __init__(self, title):

        # Inicialização da tartaruga que representa a instância da classe
        self.screen = turtle.Screen()
        self.screen.setup(width=1.0, height=1.0)
        self.screen.title(title)

    # Roda o loop de animações
    def mainLoop(self):
        turtle.update()
        turtle.mainloop()
