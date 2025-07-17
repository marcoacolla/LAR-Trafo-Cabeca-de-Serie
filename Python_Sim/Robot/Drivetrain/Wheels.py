import turtle
import math
import GVL
from Robot.Pathing.Axes import Axes

WHEEL_RADIUS = GVL.WHEEL_RADIUS
TIRE_THICKNESS = GVL.TIRE_THICKNESS

# Classe que representa uma roda que possui um sistema de coordenadas
class Wheel:

    # Método construtor da classe Roda
    def __init__(self, parent, name, x_offset, y_offset, color="azure4", width=2*WHEEL_RADIUS, length=TIRE_THICKNESS):

        # Inicialização dos atributos da classe
        self.parent = parent                                # Objeto 'pai': Vehicle
        self.name = f'{self.parent.getName()}_{name}_wheel' # Nome da instância
        self.width = width                                  # Largura do objeto
        self.length = length                                # Comprimento do objeto
        self.relative_position = (x_offset, y_offset)       # Deslocamento relativo ao centro do veículo

        self.current_steering_angle = None
        self.should_reverse = False
        self.last_desired_angle = None

        self.angular_limits = 130
        
        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.color(color)
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.length/20)
        self.turtle.penup()

        # Inicialização dos sistemas de eixos que orientam a roda
        self.fixed_axes = Axes(self, "fixed", x_axis_color="red", y_axis_color="red", fixed=False)
        self.moving_axes = Axes(self, "fixed", x_axis_color="black", y_axis_color="black", fixed=True)

        # Posiciona e orienta o eixo com base no objeto 'pai'
        self.setPosition(self.parent.getPosition())
        self.setHeading(self.parent.getHeading())

    ''' Métodos getters e setters '''

    # Obtém o nome da roda
    def getName(self):
        return self.name

    # Obtém a posição atual da roda
    def getPosition(self):
        return self.turtle.pos()

    # Obtém o ângulo de orientação atual da roda
    def getHeading(self):
        return self.turtle.heading()

    # Obtém posição e orientação da instância
    def getOrientation(self):
        return [self.getPosition(), self.getHeading()]

    # Define uma nova posição para a instância
    def setPosition(self, new_position):

        angle = math.radians(self.parent.getHeading())  # Ângulo do objeto 'pai'
        relative_x, relative_y = self.relative_position # Posição relativa ao veículo

        # Calcula a posição absoluta utilizando trigonometria
        rotated_x = relative_x * math.cos(angle) - relative_y * math.sin(angle)
        rotated_y = relative_x * math.sin(angle) + relative_y * math.cos(angle)
        absolute_pos = (new_position[0] + rotated_x, new_position[1] + rotated_y)

        # Manda as rodas a uma posição absoluta
        self.turtle.goto(absolute_pos)

        self.fixed_axes.updateOrientation()  # Atualiza os eixos fixos
        self.moving_axes.updateOrientation() # Atualiza os eixos móveis

    # Define uma nova orientação para a instância
    def setHeading(self, new_heading):
        self.turtle.setheading(new_heading)
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()
