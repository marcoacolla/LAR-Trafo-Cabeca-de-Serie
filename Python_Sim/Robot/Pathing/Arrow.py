import turtle
# Classe que representa a ponta do eixo Y, para melhor visualização da orientação
class Arrow:

     # Método construtor da classe
    def __init__(self, parent):

        # Inicialização dos atributos da classe
        self.parent = parent                         # Objeto 'pai': Axes
        self.name = f'{self.parent.getName()}_arrow' # Nome da instância

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.color(self.parent.y_axis.turtle.color()[0])
        self.turtle.shape("classic")
        self.turtle.shapesize(0.3*self.parent.y_axis.turtle.shapesize()[0])
        self.turtle.penup()

        # Posiciona e orienta o eixo com base no objeto 'pai'
        self.setPosition(self.parent.y_axis.getPosition())
        self.setHeading(self.parent.y_axis.getHeading())

    ''' Métodos getters e setters '''

    # Obtém o nome da instância
    def getName(self):
        return self.name

    # Obtém a posição da instância
    def getPosition(self):
        return self.turtle.pos()

    # Obtém o ângulo de orientação da instância
    def getHeading(self):
        return self.turtle.heading()

    # Obtém posição e orientação da instância
    def getOrientation(self):
        return [self.getPosition(), self.getHeading()]

    # Define uma nova posição para a instância
    def setPosition(self, new_position):
        self.turtle.goto(new_position)

    # Define uma nova orientação para a instância
    def setHeading(self, new_heading):
        self.turtle.setheading(new_heading)