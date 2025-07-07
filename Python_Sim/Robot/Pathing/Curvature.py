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
        wheels = self.vehicle.wheels

        def intersection(w1, w2):
            x0, y0 = w1.getPosition()
            theta0 = math.radians(w1.getHeading())
            dx0, dy0 = math.cos(theta0), math.sin(theta0)

            x1, y1 = w2.getPosition()
            theta1 = math.radians(w2.getHeading())
            dx1, dy1 = math.cos(theta1), math.sin(theta1)

            denom = dx0 * dy1 - dy0 * dx1
            if abs(denom) < 1e-6:
                return None

            t0 = ((x1 - x0) * dy1 - (y1 - y0) * dx1) / denom
            ix = x0 + t0 * dx0
            iy = y0 + t0 * dy0
            return (ix, iy)

        # Calcula interseção das rodas dianteiras (1 e 3) e traseiras (0 e 2)
        front_icr = intersection(wheels[1], wheels[3])
        rear_icr  = intersection(wheels[0], wheels[2])

        if front_icr and rear_icr:
            # Retorna a média dos dois pontos
            return ((front_icr[0] + rear_icr[0]) / 2, (front_icr[1] + rear_icr[1]) / 2)
        elif front_icr:
            return front_icr
        elif rear_icr:
            return rear_icr
        else:
            return None

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

        # Para cada roda, desenha um círculo individual com raio real a partir do ICR
        for wheel in self.vehicle.wheels:
            wx, wy = wheel.getPosition()
            dx = wx - icr[0]
            dy = wy - icr[1]
            r = math.sqrt(dx**2 + dy**2)

            # Desenha o círculo da trajetória da roda, com centro no ICR e raio r
            self.turtle.penup()
            self.turtle.goto(icr[0], icr[1] - r)
            self.turtle.setheading(0)
            self.turtle.pendown()
            self.turtle.pencolor("gray")
            self.turtle.circle(r)

        # Restaura a cor original para eventuais atualizações futuras
        self.turtle.pencolor(self.base_color)