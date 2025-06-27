import turtle
import math

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

        # force the ICR on the vehicle's local X axis in curve mode
        if self.vehicle.curve_mode == "curve":
            cx, cy = self.vehicle.getPosition()
            θ = math.radians(self.vehicle.getHeading())
            R = self.vehicle.curvature_radius
            # point R units along the heading direction
            icr_x = cx - R * math.cos(θ)
            icr_y = cy - R * math.sin(θ)
            return (icr_x, icr_y)
        
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
            if abs(denominator) < 1E-6:
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
            
            # Limpa desenhos anteriores
            self.turtle.clear()
        
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