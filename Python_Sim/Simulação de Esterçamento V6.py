'''
* Código para simulação de um veículo 4WS (Four-Wheel Steering)
* Criado pelo bolsista João Gabriel, em 15 de fevereiro de 2025
* Laboratory of Applied Robotics Raul Guenther - Projeto "TRAFO"
'''

''' Importação de módulos úteis ao projeto '''

import turtle # Biblioteca para construção e manipulação dos gráficos
import math   # Biblioteca para computar funções matemáticas
import time   # Biblioteca para administrar o tempo da simulação

''' Constantes e variáveis globais do código '''
ROBOT_LENGHT   = 325 # Comprimento do robô ...... 350 cm
ROBOT_WIDHT    = 150 # Comprimento do robô ...... 125 cm
WHEEL_RADIUS   = 35  # Raio das rodas do robô ... 35 cm
TIRE_THICKNESS = 25  # Grossura do pneu ......... 25 cm

''' Definição de classes que vão compor a simulação '''

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
        self.setPosition(self.parent.getPosition())
        self.setHeading(self.parent.getHeading())

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

# Classe que represnta a ponta do eixo Y, para melhor visualização da orientação
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

        # Obtém a posição e o heading do objeto 'pai'
        parent_position = self.parent.getPosition()
        parent_heading = self.parent.getHeading()

        # Atualiza a posição dos eixos para coincidir com a posição do pai
        self.x_axis.setPosition(parent_position)
        self.y_axis.setPosition(parent_position)

         # Para eixos móveis, utiliza o heading do pai
        if not self.fixed:

            self.y_axis.setHeading(parent_heading)
            self.x_axis.setHeading(parent_heading + 90)
            self.arrow.setHeading(parent_heading + 90)

        # Para eixos fixos, usa o heading do 'avô' ou o do pai
        else:

            # Obtém o heading do 'avô' ou o do pai
            grandparent_heading = self.parent.parent.getHeading() if hasattr(self.parent, "parent") else parent_heading

            # Atualiza os headings
            self.y_axis.setHeading(grandparent_heading)
            self.x_axis.setHeading(grandparent_heading + 90)
            self.arrow.setHeading(grandparent_heading + 90)

        # Atualiza a posição da seta com base no heading final
        final_heading = self.y_axis.getHeading() + 90
        angle = math.radians(final_heading % 360)
        arrow_position_x = parent_position[0] + 10.5 * self.y_axis.turtle.shapesize()[0] * math.cos(angle)
        arrow_position_y = parent_position[1] + 10.5 * self.y_axis.turtle.shapesize()[0] * math.sin(angle)
        self.arrow.setPosition((arrow_position_x, arrow_position_y))

# Classe que representa uma roda que possui um sistema de coordenadas
class Wheel:

    # Método construtor da classe Roda
    def __init__(self, parent, name, x_offset, y_offset, color="azure4", width=2*WHEEL_RADIUS, lenght=TIRE_THICKNESS):

        # Inicialização dos atributos da classe
        self.parent = parent                                # Objeto 'pai': Vehicle
        self.name = f'{self.parent.getName()}_{name}_wheel' # Nome da instância
        self.width = width                                  # Largura do objeto
        self.lenght = lenght                                # Comprimento do objeto
        self.relative_position = (x_offset, y_offset)       # Deslocamento relativo ao centro do veículo

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.color(color)
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.lenght/20)
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

# Classe que representa o veículo: objeto principal da simulação
class Vehicle:

    # Método construtor da classe Roda
    def __init__(self, name, color, position, width=ROBOT_LENGHT, lenght=ROBOT_WIDHT):

        # Inicialização dos atributos da classe
        self.name = name     # Nome da instância
        self.width = width   # Comprimento do objeto
        self.lenght = lenght # Largura do objeto

        # Variáveis auxiliares para posicionamento das rodas
        half_length = self.lenght / 2 # Metade do comprimento do objeto
        half_width = self.width   / 2 # Metade da largura do objeto

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.pen(outline=8)
        self.turtle.color(color, "")
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.lenght/20)
        self.turtle.penup()

        # Array com as rodas do veículo
        self.wheels = [
            Wheel(self, "COL_1", -half_length,  half_width), # Coluna Traseira - Esquerda
            Wheel(self, "COL_2",  half_length,  half_width), # Coluna Frontal - Direita
            Wheel(self, "COL_3", -half_length, -half_width), # Coluna Traseira - Direita
            Wheel(self, "COL_4",  half_length, -half_width)  # Coluna Frontal - Direita
        ]

        # Curvatura do veículo e de suas rodas
        self.curvature = Curvature(self, color="CornflowerBlue")

        # Inicialização dos sistemas de eixos que orientam a roda
        self.fixed_axes = Axes(self, "fixed", x_axis_color="green", y_axis_color="red", fixed=False)
        self.moving_axes = Axes(self, "fixed", x_axis_color="black", y_axis_color="black", fixed=True)

        # Posiciona o carro com base nas coordenadas fornecidas
        self.setPosition(position)

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

        # Atualiza a posição do próprio veículo
        self.turtle.goto(new_position)

        # Atualiza a posição e orientação dos eixos
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()

    # Define uma nova orientação para a instância
    def setHeading(self, new_heading):

        # Atualia o heading do próprio veículo
        self.turtle.setheading(new_heading)

        # Atualiza a posição e orientação dos eixos
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()

    # Gera uma trajetória para o veículo e suas rodas, de acordo com o modo e parâmetros de movimento
    def generateTrajectory(self, curvature_mode, direction="", diagonal_angle=0, curvature_radius=0):
        
        # Robô andando em linha reta
        if curvature_mode == "straight":
            
            # Ângulo de esterçamento nulo
            steering_angle = 0
            
            # Esterça as rodas com o ângulo fornecido
            self.wheels[0].setHeading(steering_angle)
            self.wheels[1].setHeading(steering_angle)
            self.wheels[2].setHeading(steering_angle)
            self.wheels[3].setHeading(steering_angle)

        # Robô andando em diagonal
        elif curvature_mode == "diagonal":

            # Ângulo de esterçamento definido pelo usuário
            steering_angle = diagonal_angle

            # Esterça as rodas com o ângulo fornecido
            self.wheels[0].setHeading(steering_angle)
            self.wheels[1].setHeading(steering_angle)
            self.wheels[2].setHeading(steering_angle)
            self.wheels[3].setHeading(steering_angle)

        # Robô girando em torno do próprio eixo
        elif curvature_mode == "pivotal":

            # Calcula o ângulo utilizando trigonometria
            steering_angle = math.degrees(math.atan2(ROBOT_LENGHT, ROBOT_WIDHT))

            # Esterça as rodas com o ângulo fornecido
            self.wheels[0].setHeading(360 - steering_angle)
            self.wheels[1].setHeading(180 + steering_angle)
            self.wheels[2].setHeading(360 + steering_angle)
            self.wheels[3].setHeading(180 - steering_angle)    
        
        # Modo de curva
        elif curvature_mode == "curve":
            
            # Calcula os ângulos utilizando trigonometria
            alpha = math.degrees(math.atan(ROBOT_LENGHT/(2*curvature_radius - ROBOT_WIDHT))) # Ângulo das rodas de dentro da curva
            beta =  math.degrees(math.atan(ROBOT_LENGHT/(2*curvature_radius + ROBOT_WIDHT))) # Ângulo das rodas de fora da curva

            # Esterça as rodas com o ângulo fornecido, no sentido horário
            if direction == "clockwise":
                self.wheels[0].setHeading(alpha)
                self.wheels[1].setHeading(beta)
                self.wheels[2].setHeading(-alpha)
                self.wheels[3].setHeading(-beta)    
            
            # Esterça as rodas com o ângulo fornecido, no sentido anti-horário
            elif direction == "counterclockwise":  
                self.wheels[0].setHeading(-alpha)
                self.wheels[1].setHeading(-beta)
                self.wheels[2].setHeading(alpha)
                self.wheels[3].setHeading(beta)    
        
        # Atualiza a curvatura do veículo
        self.curvature.update()

    # Atualiza o heading e a posição do veículo com base nos valores das rodas.
    def updatePositionFromWheels(self):

        pos_sum_x = 0.0          # Soma das posições x das rodas
        pos_sum_y = 0.0          # Soma das posições y das rodas
        count = len(self.wheels) # Número total de rodas

        # Média atitimética das posições das rodas define as coordenadas do centro
        center_x = pos_sum_x / count
        center_y = pos_sum_y / count

        # Atualiza o heading e a posição do veículo com os valores calculados
        self.setPosition((center_x, center_y))
    
    def updateHeadingFromWheels(self):
        pass

    
        
# Classe que representa a curvatura descrita como trajetória pelos objetos
class Curvature:

    # Método construtor da classe
    def __init__(self, parent, color="blue"):

        # Inicialização dos atributos da classe
        self.vehicle = parent   # Veículo cuja trajetória será gerada
        self.base_color = color # Define a cor base para os desenhos

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.color(self.base_color)
        self.turtle.hideturtle()
        self.turtle.speed(0)
        self.turtle.pensize(2)
        self.turtle.penup()

    # Calcula o Centro Instantâneo de Rotação com base na interseção das linhas de direção das rodas
    def computeICR(self):

        # Função auxiliar para calcular a interseção de duas linhas de direção
        def computeIntersection(wheel_a, wheel_b):

            # Obtém as coordenadas e a orientação da roda A
            x0, y0 = wheel_a.getPosition()
            theta0 = math.radians(wheel_a.getHeading()) # Converte o ângulo da roda para radianos
            d0 = (math.cos(theta0), math.sin(theta0))   # Direção da roda A como um vetor unitário

            # Obtém as coordenadas e a orientação da roda B
            x1, y1 = wheel_b.getPosition()
            theta1 = math.radians(wheel_b.getHeading()) # Converte o ângulo da roda B para radianos
            d1 = (math.cos(theta1), math.sin(theta1))   # Direção da roda B como um vetor unitário

            # Calcula o denominador da fórmula de interseção (produto vetorial entre as direções)
            denominator = d0[0]*d1[1] - d0[1]*d1[0]

            # Se o denominador for muito pequeno, as linhas são paralelas
            if abs(denominator) < 1e-6:
                return None

            # Calcula o parâmetro t0 (parâmetro escalar da reta) para a interseção entre as duas linhas
            t0 = ((x1 - x0)*d1[1] - (y1 - y0)*d1[0]) / denominator

            # Calcula as coordenadas do ponto de interseção (ICR)
            icr_x = x0 + t0 * d0[0]
            icr_y = y0 + t0 * d0[1]

            # Retorna o ponto de interseção como uma tupla (x, y)
            return (icr_x, icr_y)

        # Cálculo da interseção das rodas dianteiras (índices 1 e 3)
        front_icr = computeIntersection(self.vehicle.wheels[1], self.vehicle.wheels[3])

        # Cálculo da interseção das rodas traseiras (índices 0 e 2)
        rear_icr = computeIntersection(self.vehicle.wheels[0], self.vehicle.wheels[2])

        # Se não houver interseção, retorna None
        if front_icr is None and rear_icr is None:
            return None
        elif front_icr is None:
            return rear_icr
        elif rear_icr is None:
            return front_icr

        # Se houver duas interseções, retorna a média entre elas como o ICR
        else:
            icr_x = (front_icr[0] + rear_icr[0]) / 2
            icr_y = (front_icr[1] + rear_icr[1]) / 2
            return (icr_x, icr_y)

    # Função que atualiza o desenho da trajetória de curvatura
    def update(self):

        # Calcula o Centro Instantâneo de Rotação (ICR)
        icr = self.computeICR()

        # Ne não foi possível determinar o círculo, desenha as retas da trajetória
        if icr is None:
            
            # Percorre as rodas do veículo
            for wheel in self.vehicle.wheels:

                # Obtém a orientação de cada roda
                wheel_pos = wheel.getPosition()
                wheel_heading = wheel.getHeading() + 90

                # Define um comprimento arbitrário pra reta, em pixels
                line_length = 250

                # Calcula o ponto final da reta usando trigonometria
                angle_rad = math.radians(wheel_heading)
                end_x = wheel_pos[0] + line_length * math.cos(angle_rad)
                end_y = wheel_pos[1] + line_length * math.sin(angle_rad)

                # Desenha a reta
                self.turtle.penup()
                self.turtle.goto(wheel_pos)
                self.turtle.pendown()
                self.turtle.pencolor(self.base_color)
                self.turtle.goto(end_x, end_y)

            # Sai da função após desenhar as retas
            return

        # Cálculo do raio principal (distância entre o centro do veículo e o ICR)
        vehicle_center = self.vehicle.getPosition()
        dx = vehicle_center[0] - icr[0]
        dy = vehicle_center[1] - icr[1]
        main_radius = math.sqrt(dx*dx + dy*dy)

        # Limpa desenhos anteriores
        self.turtle.clear()

        # Desenha o círculo de curvatura principal
        self.turtle.penup()
        self.turtle.goto(icr[0] + main_radius, icr[1])
        self.turtle.setheading(90)
        self.turtle.pendown()
        self.turtle.pencolor(self.base_color)
        self.turtle.circle(main_radius)

        # Desenha um pequeno círculo preenchido no ICR
        small_radius = 5
        self.turtle.penup()
        self.turtle.goto(icr[0], icr[1] - small_radius)
        self.turtle.setheading(0)
        self.turtle.pendown()
        self.turtle.begin_fill()
        self.turtle.circle(small_radius)
        self.turtle.end_fill()

        # Desenha linhas conectando centros das rodas e veículo ao ICR
        for wheel in self.vehicle.wheels:
            wheel_pos = wheel.getPosition()
            self.turtle.penup()
            self.turtle.goto(wheel_pos)
            self.turtle.pendown()
            self.turtle.goto(icr)

        # Desenha uma linha conectando o centro do veículo ao ICR
        self.turtle.penup()
        self.turtle.goto(vehicle_center)
        self.turtle.pendown()
        self.turtle.goto(icr)

        #Calcula e desenha os raios médios das rodas da esquerda e direita
        left_middle_radius = []  # Lista para armazenar os raios das rodas da esquerda
        right_middle_radius = [] # Lista para armazenar os raios das rodas da direita

        # Percorre todas as rodas do veículo
        for wheel in self.vehicle.wheels:

            # Calcula a distância do ICR para cada roda
            pos = wheel.getPosition()
            dist = math.sqrt((pos[0] - icr[0])**2 + (pos[1] - icr[1])**2)

            # Se a roda está à esquerda
            if wheel.relative_position[0] < 0:
                left_middle_radius.append(dist)

            # Se a roda está à direita
            elif wheel.relative_position[0] > 0:
                right_middle_radius.append(dist)

        # Se houver rodas à esquerda, desenha o círculo para a curva da esquerda
        if left_middle_radius:

            # Calcula o raio médio das rodas da esquerda
            left_avg = sum(left_middle_radius) / len(left_middle_radius)

            # Posiciona a tartaruga para desenhar
            self.turtle.penup()
            self.turtle.goto(icr[0] + left_avg, icr[1])
            self.turtle.setheading(90)
            self.turtle.pendown()
            self.turtle.pencolor("grey")
            self.turtle.circle(left_avg)

        # Se houver rodas à direita, desenha o círculo para a curva da direita
        if right_middle_radius:

            # Calcula o raio médio das rodas da direita
            right_avg = sum(right_middle_radius) / len(right_middle_radius)

            # Posiciona a tartaruga para desenhar
            self.turtle.penup()
            self.turtle.goto(icr[0] + right_avg, icr[1])
            self.turtle.setheading(90)
            self.turtle.pendown()
            self.turtle.pencolor("grey")
            self.turtle.circle(right_avg)

        # Restaura a cor original para eventuais atualizações futuras
        self.turtle.pencolor(self.base_color)

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

# Função principal do programa
def main():
    turtle.tracer(0, 0)
    screen = Screen(title="Projeto TRAFO: Simulação de Veículo 4WS")

    # Instancia o veículo
    plataforma = Vehicle("Plataforma", "DarkGoldenrod1", (0, 0))
    
    # Gera a trajetória da plataforma no momento atual
    plataforma.generateTrajectory("curve", direction="counterclockwise", curvature_radius=300)

    # Atualiza a posição do veículo
    plataforma.setPosition((90, 50))
    plataforma.updatePositionFromWheels()
    
    # Roda os gráficos no loop principal da tela
    screen.mainLoop()

# Chamada incondicional da função principal
if __name__ == '__main__':
    main()