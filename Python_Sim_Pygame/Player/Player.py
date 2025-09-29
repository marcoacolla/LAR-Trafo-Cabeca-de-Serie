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
    def __init__(self, spawnpoint, surface, camera):
        self.x = spawnpoint[0]
        self.y = spawnpoint[1]
        self.lenght = ROBOT_LENGTH
        self.width = ROBOT_WIDTH
        self.color = PLAYER_COLOR
        self.state = 'vivo'  # estados: 'vivo', 'morto'
        self.curve_mode = "straight"
        self.heading = 0
        self.camera = camera
        self.modes = ["straight", "curve", "pivotal", "diagonal"]
        

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
    
    def getCameraRelativePosition(self, camera_or_offset=None):
        """Return screen coordinates for the player's center. Accepts either a Camera
        instance or a (x,y) offset tuple. If None, uses self.camera."""
        cam = camera_or_offset if camera_or_offset is not None else self.camera
        if hasattr(cam, 'world_to_screen'):
            return cam.world_to_screen((self.x, self.y))
        else:
            return (self.x - cam[0], self.y - cam[1])
    
    def setHeading(self, heading):
        self.heading = heading

    def getHeading(self):
        return self.heading  # Se quiser, pode adicionar rotação do player

    def draw(self, camera_or_offset=(0,0)):
        # Draw robot scaled to camera: create base surface in world units then scale to screen pixels
        cam = camera_or_offset if camera_or_offset is not None else self.camera

        # compute screen size from world dimensions
        sw = max(1, int(round(self.width * (cam.scale if hasattr(cam, 'scale') else 1.0))))
        sh = max(1, int(round(self.lenght * (cam.scale if hasattr(cam, 'scale') else 1.0))))

        rect_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        # border thickness scales with camera
        border = 6
        if hasattr(cam, 'scale'):
            border = max(1, int(round(border * cam.scale)))
        # Draw full rect fill then border to keep visual consistent
        pygame.draw.rect(rect_surf, self.color, (0, 0, sw, sh), border)

        # rotaciona a superfície pelo heading (rotation operates on screen pixels)
        rotated_surf = pygame.transform.rotate(rect_surf, -self.heading)

        # centraliza no player (project world center to screen)
        if hasattr(cam, 'world_to_screen'):
            center = cam.world_to_screen((self.x, self.y))
        else:
            center = (self.x - camera_or_offset[0], self.y - camera_or_offset[1])
        rect = rotated_surf.get_rect(center=center)

        # desenha no surface principal
        self.surface.blit(rotated_surf, rect.topleft)

        # rodas
        for wheel in self.wheels:
            wheel.draw(self.surface, camera_or_offset)


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
                self.makeMovement("forward", step=speed)
            if keys[pygame.K_s]:  # baixo
                self.makeMovement("backward", step=speed)
        elif self.curve_mode == "curve" or self.curve_mode == "pivotal":
            nextStep = self.angle_offset
            if keys[pygame.K_a]:
                isChangingCourse = True
                nextStep = self.angle_offset - self.step
            if keys[pygame.K_d]:
                nextStep = self.angle_offset + self.step
                isChangingCourse = True
            if keys[pygame.K_q]:
                self.icr_bias = min(1.0, self.icr_bias + .1)
                isChangingCourse = True
            if keys[pygame.K_e]:
                self.icr_bias = max(0.0, self.icr_bias - .1)
                isChangingCourse = True
            
            if keys[pygame.K_w]:  # cima
                self.makeMovement("forward", step=speed)
            if keys[pygame.K_s]:  # baixo
                self.makeMovement("backward", step=speed)

            if self.curve_mode == "curve":
                if nextStep > GLV.CURVE_MAX_RADIUS or nextStep < -GLV.CURVE_MAX_RADIUS:
                    self.setMode('straight')
                if nextStep >= GLV.CURVE_MIN_RADIUS or nextStep <= -GLV.CURVE_MIN_RADIUS:
                    self.angle_offset = nextStep
            if self.curve_mode == "pivotal":
                if abs(nextStep) <= GLV.CURVE_MIN_RADIUS:
                    self.angle_offset = nextStep
                    
            if isChangingCourse:
                self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
                # atualiza imediatamente o steering das rodas para refletir a
                # nova curvatura mesmo sem movimento
                try:
                    self.steerWheels("curve", angle_offset=self.angle_offset, icr_bias=self.icr_bias)
                except Exception:
                    pass
                isChangingCourse = False

        elif self.curve_mode == "diagonal":
            # In diagonal mode: A/D rotate wheel headings, W/S move along wheel direction
            WHEEL_TURN_STEP = 5.0  # degrees per tick when holding A/D
            if keys[pygame.K_a]:
                for w in self.wheels:
                    w.setHeading((w.getHeading() - WHEEL_TURN_STEP) % 360)
            if keys[pygame.K_d]:
                for w in self.wheels:
                    w.setHeading((w.getHeading() + WHEEL_TURN_STEP) % 360)
            if keys[pygame.K_w]:
                self.makeMovement("forward", step=speed)
            if keys[pygame.K_s]:
                self.makeMovement("backward", step=speed)

        
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
                # em modo straight as rodas alinham com o heading do robô
                wheel.setHeading(self.getHeading())
            # ensure no lingering ICR remains when switching to straight
            self.icr_global = None

        # set mode before computing ICR so computeICR can use mode-specific formula
        self.curve_mode = new_mode

        # Only compute a global ICR for modes that require curvature
        if self.curve_mode in ["curve", "pivotal"]:
            self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
        else:
            # ensure no lingering ICR in modes that don't use it
            self.icr_global = None

        # If entering diagonal mode, initialize wheel headings defasadas em 45 graus
        diagonal_angle = 0
        if new_mode == "diagonal":
            diagonal_angle = (self.getHeading() + 90) % 360
            for wheel in self.wheels:
                wheel.setHeading(diagonal_angle)

        # steer wheels for the new mode; pass diagonal_angle so steerWheels won't override
        self.steerWheels(new_mode, diagonal_angle=diagonal_angle, angle_offset=self.angle_offset)


    def steerWheels(self, curve_mode, diagonal_angle=0, angle_offset=1, icr_bias=0.5):
        # (o mesmo código que você já fez, mas sem turtle)
        icr = self.icr_global
        if curve_mode == "straight":
            # Em modo straight queremos que as rodas fiquem alinhadas com o heading do robô
            for w in self.wheels:
                w.setHeading(self.getHeading() + 90)

        elif curve_mode == "diagonal":
            for w in self.wheels:
                w.setHeading(diagonal_angle)

        elif curve_mode == "curve" or curve_mode == "pivotal" :
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

    def toggle_mode(self):
        """Cycle through robot modes: straight -> diagonal -> pivotal -> curve -> straight."""
        modes = ['straight', 'diagonal', 'pivotal']
        self.angle_offset = 0
        try:
            try:
                idx = modes.index(self.curve_mode)
            except ValueError:
                idx = 0
            next_mode = modes[(idx + 1) % len(modes)]
            # For curve mode use a default curveStart of 0

            self.setMode(next_mode)
        except Exception:
            pass

    def handle_event(self, event):
        """Handle incoming pygame events (keyboard)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_mode()
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

    def get_rotated_hitbox(self):
        """
        Retorna os 4 vértices (x,y) da hitbox rotacionada no mundo.
        Ordem: top-left, top-right, bottom-right, bottom-left (clockwise)
        """
        cx, cy = self.getPosition()
        w, h = self.width, self.lenght
        # offsets do centro para os cantos (antes da rotação)
        hw, hh = w / 2.0, h / 2.0
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]

        theta = math.radians(self.getHeading())
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        world_corners = []
        for rx, ry in corners:
            # rotaciona o offset e soma à posição do centro
            wx = cx + (rx * cos_t - ry * sin_t)
            wy = cy + (rx * sin_t + ry * cos_t)
            world_corners.append((wx, wy))

        return world_corners

    def get_hitbox_polygon(self, camera_or_offset=(0,0)):
        """
        Retorna os pontos da hitbox rotacionada já convertidos para coordenadas de tela
        (aplicando camera_offset) — útil para desenhar.
        """
        pts = self.get_rotated_hitbox()
        cam = camera_or_offset
        if hasattr(cam, 'world_to_screen'):
            return [cam.world_to_screen(p) for p in pts]
        else:
            camx, camy = cam
            return [(p[0] - camx, p[1] - camy) for p in pts]
    

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
            # movement direction should follow the wheel visual tangent used in Curvature.update
            # Curvature draws wheel heading tangent as angle_to_icr + 90, so the movement direction
            # corresponds to wheel_heading - 90 degrees (to align with screen/world conventions used)
            wheel_heading = self.wheels[0].getHeading()
            heading_rad = math.radians(wheel_heading - 90)
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

            # Use a constant angular change per movement step so rotation speed
            # is independent of the turning radius. We'll choose a small constant
            # angular increment (degrees) per call and convert to radians.
            DEGREES_PER_STEP = 2.0  # degrees per movement step (tweakable)
            dtheta = math.radians(DEGREES_PER_STEP)
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

    def respawn(self, spawnpoint):
        """
        Reset completo do player para estado inicial.
        spawnpoint: (x,y) ou None — se fornecido, posiciona o player ali.
        """
        # Restore basic state
        if spawnpoint is not None:
            try:
                x, y = spawnpoint
                self.set_alive(x, y)
            except Exception:
                # fallback: set position directly
                self.set_alive()
                self.setPosition(spawnpoint)
        else:
            self.set_alive()

        # Reset orientation and motion-related parameters
        self.setHeading(0)
        self.curve_mode = "straight"
        self.icr_global = None
        self.angle_offset = 0
        self.icr_bias = 0.5
        self.is_transitioning = False

        # Ensure wheels sync with center and default heading
        for wheel in self.wheels:
            wheel.setPosition(self.getPosition())
            wheel.setHeading(45)
            # clear any per-wheel transient state
            if hasattr(wheel, 'last_desired_angle'):
                wheel.last_desired_angle = None
            if hasattr(wheel, 'should_reverse'):
                wheel.should_reverse = False

        # Make sure mode logic applies consistent wheel headings
        try:
            self.setMode('straight')
        except Exception:
            pass


