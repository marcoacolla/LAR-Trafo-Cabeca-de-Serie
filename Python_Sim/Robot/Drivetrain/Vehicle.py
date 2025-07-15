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
    def __init__(self, name, color, position, width=ROBOT_LENGTH, length=ROBOT_WIDTH):

        # Inicialização dos atributos da classe
        self.name = name     # Nome da instância
        self.width = width   # Comprimento do objeto
        self.length = length # Largura do objeto
        self.icr_bias = 0.5
        self.icr_global = None
        # Variáveis auxiliares para posicionamento das rodas
        half_length = self.length / 2 # Metade do comprimento do objeto
        half_width = self.width   / 2 # Metade da largura do objeto

        self.icr_curve_limit = 8
        
        

        # Inicialização da tartaruga que representa a instância da classe
        self.turtle = turtle.Turtle()
        self.turtle.pen(outline=8)
        self.turtle.color(color, "")
        self.turtle.shape("square")
        self.turtle.shapesize(stretch_wid=self.width/20, stretch_len=self.length/20)
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

        # Modo atual de curva do veículo
        self.curve_mode = "straight"

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
        
        rel_angle = self.normalize_angle((desired_angle - self.getHeading()))
        
        #print(self.wheels[0].getHeading())
        #print(self.normalize_angle(self.wheels[0].getHeading()))
        angular_lim = wheel.angular_limits
        print(self.wheels[0].should_reverse)
        if wheel.should_reverse:
            if wheel.name.endswith("COL_1_wheel") or wheel.name.endswith("COL_2_wheel"):
                angular_lim = angular_lim - 90
            else:
                angular_lim = angular_lim - 90

            if abs(rel_angle) < angular_lim:
                # Inverte o heading e indica que a roda deve andar ao contrário
                corrected_angle = desired_angle
                reverse = not wheel.should_reverse
            else:
                corrected_angle = (desired_angle + 180) % 360
                reverse = wheel.should_reverse
        else:
            if abs(rel_angle) > angular_lim:
                # Inverte o heading e indica que a roda deve andar ao contrário
                corrected_angle = (desired_angle + 180) % 360
                reverse = not wheel.should_reverse
            else:
                corrected_angle = desired_angle
                reverse = wheel.should_reverse

        return corrected_angle, reverse, desired_angle

    def steerWheels(self, curve_mode, diagonal_angle=0, curvature_radius=500, angle_offset=1, icr_bias=0.5):
        
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

        # Modo 'pivotal': robô gira em torno do próprio eixo
        elif curve_mode == "pivotal":
            
            # Atualiza o ângulo com base na fórmula
            steering_angle = math.degrees(math.atan2(ROBOT_LENGTH, ROBOT_WIDTH))
            
            self.wheels[0].setHeading(self.getHeading() + 360 - steering_angle)
            self.wheels[1].setHeading(self.getHeading() + 180 + steering_angle)
            self.wheels[2].setHeading(self.getHeading() + 360 + steering_angle)
            self.wheels[3].setHeading(self.getHeading() + 180 - steering_angle)
            
        # Modo 'curve': rodas internas e externas com alpha e beta
        elif curve_mode == "curve":
            # Usa o ICR atualizado da função já existente
            icr_x, icr_y = self.curvature.computeICR(angle_offset=angle_offset)
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
        if self.curve_mode == "straight":
            
            # Movimento em linha reta: deslocamento tangencial forward
            if direction == "forward":
                heading_rad = math.radians(self.getHeading())
                dx = step * - math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
                new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
                self.setPosition(new_center)

            # Movimento em linha reta: deslocamento tangencial backward
            elif direction == "backward":
                heading_rad = math.radians(self.getHeading())
                dx = step * math.sin(heading_rad)
                dy = step * - math.cos(heading_rad)
                new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
                self.setPosition(new_center)
            
            # Atualiza a posição de cada roda, considerando o deslocamento relativo
            for wheel in self.wheels:
                wheel.setPosition(self.getPosition())

            # Atualiza o desenho da trajetória (curvatura) de forma gráfica
            self.curvature.update()


        elif self.curve_mode == "diagonal":
            
            # Movimento em linha reta: deslocamento tangencial forward
            if direction == "forward":
                heading_rad = math.radians(self.wheels[0].getHeading())
                dx = step * - math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
                new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
                self.setPosition(new_center)

            # Movimento em linha reta: deslocamento tangencial backward
            elif direction == "backward":        
                heading_rad = math.radians(self.wheels[0].getHeading())
                dx = step * math.sin(heading_rad)
                dy = step * - math.cos(heading_rad)
                new_center = (self.getPosition()[0] + dx, self.getPosition()[1] + dy)
                self.setPosition(new_center)

            # Atualiza a posição de cada roda, usando a posição do veículo e considerando o deslocamento relativo
            for wheel in self.wheels:
                wheel.setPosition(self.getPosition())

            # Atualiza o desenho da trajetória (curvatura) de forma gráfica
            self.curvature.update()

        # Movimento pivotal: o veículo gira em torno de seu próprio eixo
        elif self.curve_mode == "pivotal":
            
            # Sentido anti-horário
            if direction == "forward":
                dtheta = -step / ROBOT_LENGTH
            # Sentido horário
            elif direction == "backward":
                dtheta = step / ROBOT_LENGTH
            
            # Atualiza o heading do veículo (em graus), garantindo a rotação ao redor de seu próprio eixo
            dtheta_deg = math.degrees(dtheta)
            new_heading = (self.getHeading() + dtheta_deg) % 360

            self.setHeading(new_heading)

            # Propaga a mudança de heading para cada roda
            for wheel in self.wheels:
                wheel.setHeading((wheel.getHeading() + dtheta_deg) % 360)

            # Atualiza a posição de cada roda
            for wheel in self.wheels:
                wheel.setPosition(self.getPosition())

            # Atualiza o desenho da trajetória (curvatura) de forma gráfica
            self.curvature.update()

        elif self.curve_mode == "curve":

            # Calcula o Centro Instantâneo de Rotação (ICR) com base na orientação das rodas

            icr = self.icr_global

            if icr is not None:
                # Movimento curvo: o veículo gira em torno do ICR
                icr_x, icr_y = icr
                cx, cy = self.getPosition()

                # Vetor do ICR até o centro do veículo
                dx = cx - icr_x
                dy = cy - icr_y
                R = math.sqrt(dx**2 + dy**2)
                if R < 1e-3:
                    R = ROBOT_LENGTH

                #Admite o ângulo incremental (dθ) como uma constante dada pelo step de 5 un. pelo comprimento do robô
                dtheta = ANGULAR_VEL_CONST

                if direction == "backward":
                    dtheta = -dtheta

                # calcula o comprimento de arco a ser andado com base no raio
                f_step = dtheta * R
                step = abs(f_step)

                # Aplica a rotação do vetor para obter a nova posição do centro do veículo
                new_dx = dx * math.cos(dtheta) - dy * math.sin(dtheta)
                new_dy = dx * math.sin(dtheta) + dy * math.cos(dtheta)
                new_center = (icr_x + new_dx, icr_y + new_dy)
                self.setPosition(new_center)

                # Atualiza o heading do veículo (em graus), garantindo a tangência com a curva
                dtheta_deg = math.degrees(dtheta)
                new_heading = (self.getHeading() + dtheta_deg) % 360
                self.setHeading(new_heading)

                # Propaga a mudança de heading para cada roda:
                # Como as rodas possuem um ângulo relativo já definido (pelo steering),
                # elas precisam ser incrementadas pelo mesmo ângulo do veículo.
                for wheel in self.wheels:
                    
                    wheel.setHeading((wheel.getHeading() + dtheta_deg) % 360)

            # Atualiza a posição de cada roda, usando a posição do veículo e considerando o deslocamento relativo
            for wheel in self.wheels:
                wheel.setPosition(self.getPosition())

            # Atualiza o desenho da trajetória (curvatura) de forma gráfica
            self.curvature.update()
