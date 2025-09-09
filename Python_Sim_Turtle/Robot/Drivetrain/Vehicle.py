    
import math
import turtle
import GVL

from Robot.Drivetrain.Wheels import Wheel

from Robot.Pathing.Axes import Axes
from Robot.Pathing.Curvature import Curvature

ROBOT_LENGTH = GVL.ROBOT_LENGTH
ROBOT_WIDTH = GVL.ROBOT_WIDTH 
STEP = GVL.STEP
ANGULAR_VEL_CONST = GVL.ANGULAR_VEL_CONST

# Classe que representa o veículo: objeto principal da simulação
class Vehicle:

    # Método construtor da classe Roda
    def __init__(self, name, color, position=(0, 0), width=ROBOT_LENGTH, length=ROBOT_WIDTH):

        # Inicialização dos atributos da classe
        self.name = name     # Nome da instância
        self.width = width   # Comprimento do objeto
        self.length = length # Largura do objeto
        self.icr_bias = 0.5
        self.icr_global = None

        self.angle_offset = 0
        # Variáveis auxiliares para posicionamento das rodas
        half_length = self.length / 2 # Metade do comprimento do objeto
        half_width = self.width   / 2 # Metade da largura do objeto

        #self._freeze_icr = False
        
        

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.pen(outline=8)
        self.turtle.color(color, "")
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.length/20)
        self.turtle.penup()


        # Inicializa a posição lógica ANTES de criar as rodas
        self.logical_position = position if position is not None else (0, 0)

        # Array com as rodas do veículo
        self.wheels = [
            Wheel(self, "COL_1", -half_length,  half_width), # Coluna Traseira - Esquerda
            Wheel(self, "COL_2",  half_length,  half_width), # Coluna Frontal - Direita
            Wheel(self, "COL_3", -half_length, -half_width), # Coluna Traseira - Direita
            Wheel(self, "COL_4",  half_length, -half_width)  # Coluna Frontal - Direita
        ]

        self.lights = [True, False, True, False] # Estado das luzes (4)
        self.lights_turtle = turtle.Turtle()
        self.lights_turtle.hideturtle()
        self.lights_turtle.speed(0)
        self.lights_turtle.penup()

        # Curvatura do veículo e de suas rodas
        self.curvature = Curvature(self, color="CornflowerBlue")

        # Modo atual de curva do veículo
        self.curve_mode = "straight"

        # Inicialização dos sistemas de eixos que orientam a roda
        self.fixed_axes = Axes(self, "fixed", x_axis_color="green", y_axis_color="red", fixed=False)
        self.moving_axes = Axes(self, "fixed", x_axis_color="black", y_axis_color="black", fixed=True)
        self.logical_position = position
        self.turtle.goto(0, 0)

    ''' Métodos getters e setters '''

    # Obtém o nome da roda
    def getName(self):
        return self.name

    # Obtém a posição atual da roda
    def getPosition(self):
        # Retorna a posição lógica do robô, não a posição da turtle
        return self.logical_position

    # Obtém o ângulo de orientação atual da roda
    def getHeading(self):
        return self.turtle.heading()

    # Obtém posição e orientação da instância
    def getOrientation(self):
        return [self.getPosition(), self.getHeading()]

    # Define uma nova posição para a instância
    def setPosition(self, new_position):
        # Atualiza apenas a posição lógica do robô
        self.logical_position = new_position
        # Mantém a tartaruga do robô sempre no centro da tela
        self.turtle.goto(0, 0)
        # Atualiza a posição e orientação dos eixos
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()

    def draw_lights(self, start_x=0, start_y=-60, radius=10, spacing=30):
        """Desenha as luzes alinhadas sobre o robô, acompanhando posição e orientação."""
        colors = ['green', 'yellow', 'red', 'blue']
        self.lights_turtle.clear()
        # Posição central do robô
        cx, cy = self.turtle.position()
        heading = self.turtle.heading()
        # Luzes alinhadas na frente do robô
        base_offset = self.length/2 + 20  # distância da frente do robô
        for i, state in enumerate(self.lights):
            # Calcula posição relativa de cada luz
            angle_rad = math.radians(heading)
            # Alinha as luzes na frente, espaçadas lateralmente
            offset_x = base_offset * math.sin(angle_rad) + (i-1.5)*spacing*math.cos(angle_rad)
            offset_y = -base_offset * math.cos(angle_rad) + (i-1.5)*spacing*math.sin(angle_rad)
            x = cx + offset_x
            y = cy + offset_y
            self.lights_turtle.goto(x, y)
            self.lights_turtle.pendown()
            self.lights_turtle.fillcolor(colors[i] if state else 'gray')
            self.lights_turtle.begin_fill()
            self.lights_turtle.circle(radius)
            self.lights_turtle.end_fill()
            self.lights_turtle.penup()

    # Define uma nova orientação para a instância
    def setHeading(self, new_heading):


        # Atualia o heading do próprio veículo
        self.turtle.setheading(new_heading)

        # Atualiza a posição e orientação dos eixos
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()


    def normalize_angle(self,theta):
        """Retorna o ângulo no intervalo [-180, 180]"""
        ang = (theta % 360)
        rel = (ang - 0)  # 0 ainda é o topo
        rel = -rel  # inverter sentido pra horário
        if rel <= -180:
            rel += 360
        elif rel > 180:
            rel -= 360
        return rel

    def apply_steering_limits(self,desired_angle,wheel):
        """
        Aplica os limites de esterçamento: se o ângulo ultrapassa o permitido,
        gira a roda para o lado oposto e inverte o movimento.
        """
        if self.curve_mode == "pivotal":
            return desired_angle, False, desired_angle
        else:
            rel_angle = self.normalize_angle((desired_angle - self.getHeading()))
            angular_lim = wheel.angular_limits
            if wheel.should_reverse:
                angular_lim = angular_lim - 90

                if abs(rel_angle) < angular_lim:
                    corrected_angle = desired_angle
                    reverse = False
                else:
                    corrected_angle = (desired_angle + 180) % 360
                    reverse = True
            else:
                if abs(rel_angle) > angular_lim:
                    corrected_angle = (desired_angle + 180) % 360
                    reverse = True
                else:
                    corrected_angle = desired_angle
                    reverse = False

            return corrected_angle, reverse, desired_angle

    def steerWheels(self, curve_mode, diagonal_angle=0, angle_offset=1, icr_bias=0.5):
        #print(f"[DEBUG] steerWheels modo={curve_mode} | offset={angle_offset}")   
        # Modo 'straight': rodas todas alinhadas a 0°
        if curve_mode == "straight":

            # Atualiza o ângulo de forma fixa
            steering_angle = self.getHeading()

            self.wheels[0].setHeading(steering_angle)
            self.wheels[1].setHeading(steering_angle)
            self.wheels[2].setHeading(steering_angle)
            self.wheels[3].setHeading(steering_angle)

        # Modo 'diagonal': rodas todas com 'diagonal_angle'
        elif curve_mode == "diagonal":
            
            # atualiza o ângulo de forma fixa
            steering_angle = diagonal_angle

            self.wheels[0].setHeading(steering_angle)
            self.wheels[1].setHeading(steering_angle)
            self.wheels[2].setHeading(steering_angle)
            self.wheels[3].setHeading(steering_angle)
            
        elif curve_mode == "pivotal":
            # Atualiza o ângulo com base na fórmula
            steering_angle = math.degrees(math.atan2(ROBOT_LENGTH, ROBOT_WIDTH))
            self.wheels[0].setHeading(self.getHeading() + 360 - steering_angle)
            self.wheels[1].setHeading(self.getHeading() + 180 + steering_angle)
            self.wheels[2].setHeading(self.getHeading() + 360 + steering_angle)
            self.wheels[3].setHeading(self.getHeading() + 180 - steering_angle)
            # Atualiza o ICR global igual ao modo curve
            icr = self.curvature.computeICR(angle_offset=angle_offset)
            if icr is not None:
                icr_x, icr_y = icr
                self.icr_global = (icr_x, icr_y)
            
        # Modo 'curve': rodas internas e externas com alpha e beta
        elif curve_mode == "curve":
            # Usa o ICR atualizado da função já existente
            icr = self.curvature.computeICR(angle_offset=angle_offset)
            if icr is None:
                return
            icr_x, icr_y = icr
            self.icr_global = (icr_x, icr_y)

            theta_v = math.radians(self.getHeading())
            vx_v = math.cos(theta_v)
            vy_v = math.sin(theta_v)

            for wheel in self.wheels:
                wx, wy = wheel.getPosition()
                rx, ry = wx - icr_x, wy - icr_y  # vetor do ICR até a roda
                ang_r = math.degrees(math.atan2(ry, rx))  # ângulo do raio

                # Tangentes possíveis (±90° do raio)
                cand1 = (ang_r + 90) % 360
                cand2 = (ang_r - 90) % 360

                # Vetores candidatos
                vx1, vy1 = math.cos(math.radians(cand1)), math.sin(math.radians(cand1))
                vx2, vy2 = math.cos(math.radians(cand2)), math.sin(math.radians(cand2))

                # Produto escalar com a direção do veículo
                dot1 = vx1 * vx_v + vy1 * vy_v
                dot2 = vx2 * vx_v + vy2 * vy_v

                # Escolhe o que aponta mais pra frente
                #tangent = cand1 if dot1 > dot2 else cand2

                desired_tangent = cand1 if dot1 > dot2 else cand2

                if wheel.name.endswith("COL_1_wheel") or wheel.name.endswith("COL_2_wheel"):
                    next_angle = ((desired_tangent + 90) % 360)
                else:
                    next_angle = ((desired_tangent - 90) % 360)

                corrected_tangent, should_reverse, updated_desired = self.apply_steering_limits(next_angle,wheel)
                
                wheel.current_steering_angle = updated_desired
                wheel.should_reverse = should_reverse

                # Aplicar heading considerando a roda (mesmo esquema anterior com nomes)
                wheel.setHeading(corrected_tangent)

                # Armazene should_reverse se for necessário inverter sentido ao andar
                

                '''
                # Define o heading diretamente (sem +90/-90 fixo)
                if wheel.name == f'{self.getName()}_COL_1_wheel' or wheel.name == f'{self.getName()}_COL_2_wheel':
                    wheel.setHeading((tangent + 90) % 360)      # +90° → x-axis vira a tangente
                else:
                    wheel.setHeading((tangent - 90) % 360)
                '''

            '''
            R = curvature_radius + 10 * angle_offset

            cx, cy = self.getPosition()
            theta_v = math.radians(self.getHeading())

            # Aplica deslocamento com base no bias
            bias_offset = (0.5 - icr_bias) * self.length
            base_x = cx + bias_offset * math.cos(theta_v)
            base_y = cy + bias_offset * math.sin(theta_v)

            self.curvature_radius = R  # Atualiza o raio na instância

            
            icr_x = base_x - R * math.cos(theta_v)
            icr_y = base_y - R * math.sin(theta_v)
            

            vx_v, vy_v = math.cos(theta_v), math.sin(theta_v)

            for wheel in self.wheels:
                wx, wy = wheel.getPosition()

                rx = wx - icr_x
                ry = wy - icr_y

                ang_r = math.degrees(math.atan2(ry, rx)) % 360

                # Calcula as duas tangentes possíveis ao círculo
                cand1 = (ang_r + 90) % 360
                cand2 = (ang_r - 90) % 360

                # Avalia qual tangente aponta mais na direção do veículo
                vx1, vy1 = math.cos(math.radians(cand1)), math.sin(math.radians(cand1))
                vx2, vy2 = math.cos(math.radians(cand2)), math.sin(math.radians(cand2))

                dot1 = vx1 * vx_v + vy1 * vy_v
                dot2 = vx2 * vx_v + vy2 * vy_v

                tangent = cand1 if dot1 > dot2 else cand2
                
                
                if wheel.name == f'{self.getName()}_COL_1_wheel' or wheel.name == f'{self.getName()}_COL_2_wheel':
                    wheel.setHeading((tangent + 90) % 360)      # +90° → x-axis vira a tangente
                else:
                    wheel.setHeading((tangent - 90) % 360)
                '''
                
                
                

            

    # Atualiza o heading e a posição do veículo com base nos valores das rodas.
    def updatePositionFromWheels(self):

        pos_sum_x = 0.0          # Soma das posições X das rodas
        pos_sum_y = 0.0          # Soma das posições Y das rodas
        count = len(self.wheels) # Número total de rodas

        # Média atitimética das posições das rodas define as coordenadas do centro
        center_x = pos_sum_x / count
        center_y = pos_sum_y / count

        # Atualiza o heading e a posição do veículo com os valores calculados
        self.setPosition((center_x, center_y))
    
    #
    def makeMovement(self, direction, step=5.0):
        # Atualiza o ICR a cada movimento para modos curve/pivotal
        if self.curve_mode in ["curve", "pivotal"]:
            self.steerWheels(self.curve_mode, angle_offset=self.angle_offset, icr_bias=self.icr_bias)
        """
        Move o veículo (caixa) e faz as rodas acompanharem o movimento,
        atualizando todas para a nova posição do centro do veículo (grid).
        """
        #print(f"[DEBUG] ICR: {self.icr_global}, Mode: {self.curve_mode}")

        # Movimento em linha reta (modo 'straight')
        if self.curve_mode == "straight":
            if direction == "forward":
                heading_rad = math.radians(self.getHeading())
                dx = step * math.sin(heading_rad)
                dy = step * -math.cos(heading_rad)
            elif direction == "backward":
                heading_rad = math.radians(self.getHeading())
                dx = step * -math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
            else:
                dx = dy = 0
            new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
            self.setPosition(new_center)

        # Movimento diagonal (modo 'diagonal')
        elif self.curve_mode == "diagonal":
            if direction == "forward":
                heading_rad = math.radians(self.wheels[0].getHeading())
                dx = step * math.sin(heading_rad)
                dy = step * -math.cos(heading_rad)
            elif direction == "backward":
                heading_rad = math.radians(self.wheels[0].getHeading())
                dx = step * -math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
            else:
                dx = dy = 0
            new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
            self.setPosition(new_center)

        # Movimento curvo ou pivotal
        elif self.curve_mode == "curve" or self.curve_mode == "pivotal":
            icr = self.icr_global
            if icr is not None:
                icr_x, icr_y = icr
                cx, cy = self.getPosition()
                dx = cx - icr_x
                dy = cy - icr_y
                R = math.sqrt(dx**2 + dy**2)
                if R < 1e-3:
                    R = ROBOT_LENGTH
                dtheta = step / GVL.ROBOT_LENGTH
                if direction == "forward":
                    dtheta = -dtheta
                if self.curve_mode != "pivotal":
                    if self.angle_offset > -7:
                        dtheta = -dtheta
                f_step = dtheta * R
                step = abs(f_step)
                new_dx = dx * math.cos(dtheta) - dy * math.sin(dtheta)
                new_dy = dx * math.sin(dtheta) + dy * math.cos(dtheta)
                new_center = (icr_x + new_dx, icr_y + new_dy)
                self.setPosition(new_center)
                dtheta_deg = math.degrees(dtheta)
                new_heading = (self.getHeading() + dtheta_deg) % 360
                self.setHeading(new_heading)
                # As rodas acompanham a rotação do veículo
                for wheel in self.wheels:
                    wheel.setHeading((wheel.getHeading() + dtheta_deg) % 360)

        # Após qualquer movimento, todas as rodas acompanham a posição do centro (caixa)
        for wheel in self.wheels:
            wheel.setPosition(self.getPosition())

        # Se o modo usa ICR, alinhe o centro do robô ao ICR ao final do movimento
        if self.curve_mode in ["curve", "pivotal"] and self.icr_global is not None:
            self.setPosition(self.icr_global)
            for wheel in self.wheels:
                wheel.setPosition(self.getPosition())

        # Atualiza o desenho da trajetória (curvatura) de forma gráfica
        self.curvature.update()
