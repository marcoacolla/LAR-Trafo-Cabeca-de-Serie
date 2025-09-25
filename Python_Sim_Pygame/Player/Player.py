import pygame
import math
from Player.Wheels import Wheel
from Player import GLV
from Player.Pathing.Curvature import Curvature  # adaptado para pygame

# Configurações do player
ROBOT_LENGTH   = 130 # Comprimento do robô ...... 350 cm
ROBOT_WIDTH   = 60 # Comprimento do robô ...... 125 cm
PLAYER_COLOR = (255, 220, 0)  # preto

class Player:
    
    
    step = 1.0
    is_transitioning = False

    transition_duration = [100]  # duração padrão da transição em ms
    def __init__(self, x, y, surface, camera):
        self.x = x
        self.y = y
        self.lenght = ROBOT_LENGTH
        self.width = ROBOT_WIDTH
        self.color = PLAYER_COLOR
        self.state = 'vivo'  # estados: 'vivo', 'morto'
        self.curve_mode = "straight"
        self.heading = 0
        self.camera = camera
        

        self.icr_global = None  # Centro Instantâneo de Rotação (ICR) global

        self.surface = surface
        self.curvature = Curvature(self)

        self.icr_bias = 0.5  # Bias do ICR (0.0 = esquerda, 1.0 = direita)
        self.angle_offset = 0

        # Offsets das rodas (relativo ao centro do veículo)
        half_w = self.width / 2
        half_l = self.lenght / 2

        self.wheels = [
            Wheel(self, "front_left",  -half_w, -half_l),
            Wheel(self, "front_right",  half_w, -half_l),
            Wheel(self, "rear_left",   -half_w,  half_l),
            Wheel(self, "rear_right",   half_w,  half_l),
        ]

        self.setMode("straight")

    def getName(self):
        return "player"
    
    def setPosition(self, pos):
        self.x, self.y = pos

    def getPosition(self):
        return (self.x, self.y)
    
    def getCameraRelativePosition(self):
        return (self.x - self.camera.camera_offset[0], self.y - self.camera.camera_offset[1])
    
    def setHeading(self, heading):
        self.heading = heading

    def getHeading(self):
        return self.heading  # Se quiser, pode adicionar rotação do player

    def draw(self, camera_offset=(0,0)):
        # cria uma superfície do tamanho do robô
        rect_surf = pygame.Surface((self.width, self.lenght), pygame.SRCALPHA)
        pygame.draw.rect(rect_surf, self.color, (0, 0, self.width, self.lenght), 6)

        # rotaciona a superfície pelo heading
        rotated_surf = pygame.transform.rotate(rect_surf, -self.heading)

        # centraliza no player
        rect = rotated_surf.get_rect(center=(self.x - camera_offset[0], self.y - camera_offset[1]))

        # desenha no surface principal
        self.surface.blit(rotated_surf, rect.topleft)

        # rodas
        for wheel in self.wheels:
            wheel.draw(self.surface, camera_offset)


    def move(self, keys, speed=5):
        isChangingCourse = False
        if self.state != 'vivo' or self.is_transitioning:
            return
        if self.curve_mode == "straight":
            if keys[pygame.K_a] or keys[pygame.K_d]:  # esquerda
                if keys[pygame.K_a]:
                    self.angle_offset = GLV.CURVE_MAX_RADIUS
                else:
                    self.angle_offset = -GLV.CURVE_MAX_RADIUS
                self.setMode("curve",curveStart=self.angle_offset)
            if keys[pygame.K_w]:  # cima
                self.y -= speed
            if keys[pygame.K_s]:  # baixo
                self.y += speed
        if self.curve_mode == "curve":
            nextStep = self.angle_offset
            if keys[pygame.K_a]:
                isChangingCourse = True
                nextStep = self.angle_offset - self.step
            if keys[pygame.K_d]:
                nextStep = self.angle_offset + self.step
                isChangingCourse = True
            if keys[pygame.K_q]:
                self.icr_bias = min(1.0, self.icr_bias + .1)
            if keys[pygame.K_e]:
                self.icr_bias = max(0.0, self.icr_bias - .1)
            
            if keys[pygame.K_w]:  # cima
                self.makeMovement("forward", step=speed)
            if keys[pygame.K_s]:  # baixo
                self.makeMovement("backward", step=speed)

            if nextStep > GLV.CURVE_MAX_RADIUS or nextStep < -GLV.CURVE_MAX_RADIUS:
                self.setMode("straight")
            if nextStep >= GLV.CURVE_MIN_RADIUS or nextStep <= -GLV.CURVE_MIN_RADIUS:
                self.angle_offset = nextStep

            if isChangingCourse:
                self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
                isChangingCourse = False

        
        # Atualiza posição de todas as rodas
        for wheel in self.wheels:
            wheel.setPosition((self.x, self.y))

    def set_dead(self):
        self.state = 'morto'

    def set_alive(self, x=None, y=None):
        self.state = 'vivo'
        if x is not None and y is not None:
            self.x = x
            self.y = y

    def setMode(self, mode, curveStart=0, duration=None):
        if self.is_transitioning:
            return  # evita sobreposição

        self.angle_offset = curveStart
        self.icr_bias = 0.5
        new_mode = mode

        def on_completion():
            self.is_transitioning = False
            if new_mode == "pivotal":
                self.steerWheels("curve", angle_offset=self.angle_offset)

        if duration is None:
            duration = 1000  # ms (1 segundo) → pode ser sua tabela transition_duration
        
        if new_mode in ["straight"]:
            for wheel in self.wheels:
                wheel.setHeading(45)
        else:
            self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)

        self.curve_mode = new_mode
        self.steerWheels(new_mode, angle_offset=self.angle_offset)


    def steerWheels(self, curve_mode, diagonal_angle=0, angle_offset=1, icr_bias=0.5):
        # (o mesmo código que você já fez, mas sem turtle)
        icr = self.icr_global
        if curve_mode == "straight":
            steering_angle = self.getHeading()
            for w in self.wheels:
                w.setHeading(steering_angle + 90)

        elif curve_mode == "diagonal":
            for w in self.wheels:
                w.setHeading(diagonal_angle)

        elif curve_mode == "pivotal":
            # ... mesmo cálculo que você já tem ...
            pass

        elif curve_mode == "curve":
            #icr = self.curvature.computeICR(angle_offset=angle_offset)
            if icr is None:
                return
            icr_x, icr_y = icr
            #self.icr_global = (icr_x, icr_y)

            theta_v = math.radians(self.getHeading())
            vx_v, vy_v = math.cos(theta_v), math.sin(theta_v)

            for wheel in self.wheels:
                wx, wy = wheel.getPosition()
                rx, ry = wx - icr_x, wy - icr_y
                ang_r = math.degrees(math.atan2(ry, rx))

                cand1 = (ang_r + 90) % 360
                cand2 = (ang_r - 90) % 360

                vx1, vy1 = math.cos(math.radians(cand1)), math.sin(math.radians(cand1))
                vx2, vy2 = math.cos(math.radians(cand2)), math.sin(math.radians(cand2))
                dot1 = vx1 * vx_v + vy1 * vy_v
                dot2 = vx2 * vx_v + vy2 * vy_v

                desired = cand1 if dot1 > dot2 else cand2
                wheel.setHeading(desired)

        self.curve_mode = curve_mode
    def is_dead(self):
        return self.state == 'morto'
    
    def get_hitbox(self):
        """
        Retorna o retângulo da hitbox do player.
        """

        hitbox = pygame.Rect(
            self.x - self.width // 2, 
            self.y - self.lenght // 2, 
            self.width, self.lenght)
        
        
        return hitbox
    

    def makeMovement(self, direction, step=5.0):
        # Atualiza o ICR sempre que necessário
        if self.curve_mode in ["curve", "pivotal"]:
            self.steerWheels(self.curve_mode, angle_offset=self.angle_offset, icr_bias=self.icr_bias)

        # Movimento em linha reta
        if self.curve_mode == "straight":
            heading_rad = math.radians(self.getHeading())
            if direction == "forward":
                dx = step * math.sin(heading_rad)
                dy = -step * math.cos(heading_rad)
            elif direction == "backward":
                dx = -step * math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
            else:
                dx = dy = 0
            self.setPosition((self.x + dx, self.y + dy))

        # Movimento diagonal
        elif self.curve_mode == "diagonal":
            heading_rad = math.radians(self.wheels[0].getHeading())
            if direction == "forward":
                dx = step * math.sin(heading_rad)
                dy = -step * math.cos(heading_rad)
            elif direction == "backward":
                dx = -step * math.sin(heading_rad)
                dy = step * math.cos(heading_rad)
            else:
                dx = dy = 0
            self.setPosition((self.x + dx, self.y + dy))

        # Movimento curvo ou pivotal
        elif self.curve_mode in ["curve", "pivotal"] and self.icr_global is not None:
            icr_x, icr_y = self.icr_global
            cx, cy = self.getPosition()

            # vetor centro → ICR
            dx = cx - icr_x
            dy = cy - icr_y
            R = math.sqrt(dx**2 + dy**2)
            if R < 1e-3:
                R = ROBOT_LENGTH

            # Ângulo girado nesse passo (Δθ = desloc / raio)
            dtheta = step / R
            if direction == "backward":
                dtheta = -dtheta

            # Atualiza posição do centro girando em torno do ICR
            new_dx = dx * math.cos(dtheta) - dy * math.sin(dtheta)
            new_dy = dx * math.sin(dtheta) + dy * math.cos(dtheta)
            new_center = (icr_x + new_dx, icr_y + new_dy)
            self.setPosition(new_center)

            # Atualiza heading
            dtheta_deg = math.degrees(dtheta)
            self.setHeading((self.getHeading() + dtheta_deg) % 360)

            # Roda acompanha o giro
            for wheel in self.wheels:
                wheel.setHeading((wheel.getHeading() + dtheta_deg) % 360)

        # Sincroniza rodas com o centro do player
        for wheel in self.wheels:
            wheel.setPosition(self.getPosition())

