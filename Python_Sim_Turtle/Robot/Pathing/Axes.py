from Robot.Pathing.Axis import Axis
from Robot.Pathing.Arrow import Arrow
import math
# Classe que representa o conjunto de eixos (sistema de coordenadas local) de um objeto
class Axes:

    # Método construtor da classe
    def __init__(self, parent, name, x_axis_color="black", y_axis_color="black", fixed=True):

        # Inicialização dos atributos da classe
        self.parent = parent                               # Objeto 'pai': Wheel ou Vehicle
        self.name = f'{self.parent.getName()}_{name}_axes' # Nome da instância
        self.fixed = fixed                                 # Orientação fixa (Vehicle) ou móvel (Wheel)

        # Cria os dois eixos (X e Y) utilizando a classe Axis
        self.x_axis = Axis(self, "x", x_axis_color, 30, 2)
        self.y_axis = Axis(self, "y", y_axis_color, 70, 2)

        # Cria uma instância de seta de orientação, se não for um referencial fixo
        self.arrow = Arrow(self)

        # Atualiza a orientação dos eixos, sendo fixa ou móvel
        self.updateOrientation()

    ''' Métodos getters e setters '''

    # Obtém o nome do conjunto de eixos
    def getName(self):
        return self.name

    # Obtém a posição do objeto, por meio do 'pai'
    def getPosition(self):
        # Sempre retorna a posição visual relativa ao centro da tela (0,0), igual à caixa
        return self.parent.turtle.pos()

    # Obtém o ângulo de orientação do objeto, por meio do 'pai'
    def getHeading(self):
        return self.parent.turtle.heading()

    # Obtém posição e orientação, por meio do objeto 'pai'
    def getOrientation(self):
        return [self.getPosition(), self.getHeading()]

    # Define uma nova posição para ambos os eixos
    def setPosition(self, new_position):
        
        self.x_axis.setPosition(new_position)
        self.y_axis.setPosition(new_position)

    # Define uma nova orientação para os eixos, ajustando cada um individualmente
    def setHeading(self, new_heading):
        
        self.x_axis.setHeading(new_heading - 90)
        self.y_axis.setHeading(new_heading)

    ''' Outros métodos '''

    # Atualiza a posição e a orientação dos eixos com base no estado atual do objeto 'pai'
    def updateOrientation(self, direction=0):
        # Obtém a posição e o heading do objeto 'pai' (sempre relativo ao centro da tela)
        parent_position = self.parent.turtle.pos()
        parent_heading = self.parent.turtle.heading()

        # Atualiza a posição dos eixos para coincidir com a posição visual do pai
        self.x_axis.setPosition(parent_position)
        self.y_axis.setPosition(parent_position)

        # Para eixos móveis, utiliza o heading do pai
        if not self.fixed:
            self.y_axis.setHeading(parent_heading)
            self.x_axis.setHeading(parent_heading + 90)
            self.arrow.setHeading(parent_heading + 90)
        # Para eixos fixos, usa o heading do 'avô' ou o do pai
        else:
            grandparent_heading = self.parent.parent.getHeading() if hasattr(self.parent, "parent") else parent_heading
            self.y_axis.setHeading(grandparent_heading)
            self.x_axis.setHeading(grandparent_heading + 90)
            self.arrow.setHeading(grandparent_heading + 90)

        # Atualiza a posição da seta com base no heading final, sempre relativa ao centro da tela
        final_heading = self.y_axis.getHeading() + 90
        angle = math.radians(final_heading % 360)
        arrow_position_x = parent_position[0] + 10.5 * self.y_axis.turtle.shapesize()[0] * math.cos(angle)
        arrow_position_y = parent_position[1] + 10.5 * self.y_axis.turtle.shapesize()[0] * math.sin(angle)
        self.arrow.setPosition((arrow_position_x, arrow_position_y))
