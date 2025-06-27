import turtle

# Classe que representa um eixo que compõe o sistema de coordenadas local de um objeto
class Axis:

    # Método construtor da classe
    def __init__(self, parent, name, color, width, lenght):

        # Inicialização dos atributos da classe
        self.parent = parent                               # Objeto 'pai': Axes
        self.name = f'{self.parent.getName()}_{name}_axis' # Nome da instância
        self.width = width                                 # Largura do objeto
        self.lenght = lenght                               # Comprimento do objeto

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.color(color)
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.lenght/20)
        self.turtle.penup()

        # Posiciona e orienta o eixo com base no objeto 'pai'
        #self.setPosition(self.parent.getPosition())
        #self.setHeading(self.parent.getHeading())

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