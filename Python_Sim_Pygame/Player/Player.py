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
    # transition state
    transition_start_ms = None
    transition_duration_ms = 500  # meio segundo
    transition_from_angles = None  # per-wheel starting angles for interpolation
    transition_to_angles = None

    # --- NOVO ---
    key_hold_time = {"A": 0, "D": 0}
    max_hold_boost = 4.0   # multiplicador máximo (4x mais rápido)
    accel_rate = 0.004     # quanto mais rápido acelera (ajuste fino)

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
        self.lights = [False, False, False, False, False]  # Estado das luzes (4 luzes)
        self.sirene = False  # Estado da sirene (ligada/desligada)
        

        self.icr_global = None  # Centro Instantâneo de Rotação (ICR) global

        self.surface = surface
        self.curvature = Curvature(self)
        # Movement speed configuration
        # base_speed is the reference step used by movement calls (previous default was 5.0)
        # speed_modes contains multipliers: 'rápida' is 100%, 'média' 60%, 'lenta' 30%
        # Note: the user asked that the new fastest mode be slower than the previous
        # default; to preserve that intent the base_speed can be adjusted if desired.
        self.base_speed = 3.0
        self.speed_modes = {"rápida": 1.0, "média": 0.6, "lenta": 0.3}
        self.speed_mode = "rápida"

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
        # icamento cursor (0.0..1.0) used by the special 'icamento' mode UI
        self.icamento_cursor = 0.5

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
    
    def circle_to_square(lx, ly):

        if lx == 0 and ly == 0:
            return 0, 0
        new_x = lx * math.sqrt(1 - (ly**2) / 2)
        new_y = ly * math.sqrt(1 - (lx**2) / 2)
        return new_x, new_y
    
    def drawLights(self, camera_or_offset=(0,0)):

         # Configurações das luzes (posição local x, y e cor)
        # Layout:
        #  R R
        #   B
        #  G G
        light_positions = [
            (-8, -13, (255, 0, 0), self.lights[0],0),   # vermelho esquerdo
            (8, -13, (255, 0, 0), self.lights[0],0),    # vermelho direito

            (0, 0, (0, 0, 255), self.lights[3],0),      # azul no centro

            (-8,0, (255,200,0), self.lights[2],0),
            (8,0, (255,200,0), self.lights[2],0),

            (-8, 13, (0, 225, 0), self.lights[1],0),    # verde esquerdo
            (8, 13, (0, 225, 0), self.lights[1],0),     # verde direito




            (12, 45, (200, 200, 255), self.lights[4], 15),
            (-12, 45, (200, 200, 255), self.lights[4], 15), # branco
            (12, -45, (200, 200, 255), self.lights[4], 15),
            (-12, -45, (200, 200, 255), self.lights[4], 15), 
        ]

        # Dimensões da barra (largura x altura)
        BAR_WIDTH = 7  # comprimento da barra
        BAR_HEIGHT = 20  # espessura da barra

        cx, cy = self.getPosition()

        # Função de conversão pra tela (com ou sem câmera)
        if hasattr(camera_or_offset, 'world_to_screen'):
            to_screen = lambda x, y: camera_or_offset.world_to_screen((x, y))
        else:
            camx, camy = camera_or_offset
            to_screen = lambda x, y: (x - camx, y - camy)

        # Ângulo do robô em radianos
        theta = math.radians(self.getHeading())
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        for lx, ly, color, isOn, size in light_positions:
            # Rotaciona posição da luz
            rx = lx * cos_t - ly * sin_t
            ry = lx * sin_t + ly * cos_t
            wx, wy = cx + rx, cy + ry

            colorToUse = color if isOn else (150, 150, 150)
            # Cria superfície temporária para a barra
            if size != 0:
                BAR_HEIGHT = size
                BAR_WIDTH = size
            bar_surf = pygame.Surface((BAR_WIDTH, BAR_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, colorToUse, (0, 0, BAR_WIDTH, BAR_HEIGHT))

            # Rotaciona a barra conforme o heading
            rotated_bar = pygame.transform.rotate(bar_surf, -self.getHeading())

            # Converte posição para tela
            sx, sy = to_screen(wx, wy)
            rect = rotated_bar.get_rect(center=(int(sx), int(sy)))

            # Desenha no surface principal
            self.surface.blit(rotated_bar, rect.topleft)



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

        self.drawLights(camera_or_offset)

        # desenha no surface principal
        self.surface.blit(rotated_surf, rect.topleft)
        
        # rodas
        for wheel in self.wheels:
            wheel.draw(self.surface, camera_or_offset)


    def move(self, keys, speed=5):
        isChangingCourse = False
        # progress any in-progress transition first
        self.update_transition()
        # block inputs during transition or if dead
        if self.is_transitioning:
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
            # --- calcula tempo de tecla pressionada ---
            now = pygame.time.get_ticks()
            dt = 16  # valor aproximado entre frames (~60fps)

            if keys[pygame.K_a]:
                self.key_hold_time["A"] += dt
                self.key_hold_time["D"] = 0
                isChangingCourse = True
                hold_factor = min(self.max_hold_boost,
                                1.0 + self.accel_rate * self.key_hold_time["A"])
                nextStep = self.angle_offset - self.step * hold_factor

            elif keys[pygame.K_d]:
                self.key_hold_time["D"] += dt
                self.key_hold_time["A"] = 0
                isChangingCourse = True
                hold_factor = min(self.max_hold_boost,
                                1.0 + self.accel_rate * self.key_hold_time["D"])
                nextStep = self.angle_offset + self.step * hold_factor

            else:
                # reseta tempos quando solta as teclas
                self.key_hold_time["A"] = 0
                self.key_hold_time["D"] = 0
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
                # If the requested angle_offset goes beyond allowed radius,
                # switch back to straight mode immediately (not via toggle_mode
                # which cycles through unrelated modes). This avoids a visual
                # glitch caused by an unintended transition path.
                if nextStep > GLV.CURVE_MAX_RADIUS or nextStep < -GLV.CURVE_MAX_RADIUS:
                    # force immediate switch to straight; clear angle offset
                    try:
                        self.setMode('straight')
                    except Exception:
                        # fallback to direct assignment if setMode fails
                        self.curve_mode = 'straight'
                    self.angle_offset = 0
                    nextStep = 0
                    
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

        elif self.curve_mode == "icamento":
            # In icamento mode: allow normal straight movement while
            # W/S also move the icamento cursor (used by a UI element).
            CURSOR_STEP = 0.025 * max(1.0, speed / 3.0)
            if keys[pygame.K_w]:
                # move cursor up
                self.icamento_cursor = max(0.0, self.icamento_cursor - CURSOR_STEP)
                self.makeMovement("forward", step=speed)
            if keys[pygame.K_s]:
                # move cursor down
                self.icamento_cursor = min(1.0, self.icamento_cursor + CURSOR_STEP)
                self.makeMovement("backward", step=speed)

        
        # Atualiza posição de todas as rodas
        for wheel in self.wheels:
            wheel.setPosition((self.x, self.y))

    def move_with_joystick(self, axes, speed=5):
        """Control the player using joystick axes.
        axes: (left_x, left_y, right_x, right_y)
        left_y controls forward/back movement (axis centered at 0).
        left_x controls angle_offset (mapped to CURVE_MAX_RADIUS) when in curve modes.
        right_x controls icr_bias (mapped from -1..1 -> 0..1).
        For icamento mode left_y moves the cursor up/down.
        """
        lx, ly, rx, ry = axes
        # small deadzone to avoid drift
        DEAD = 0.12
        lx_treated, ly_treated = lx, ly
        rx_treated, ry_treated = rx,ry
        # Progress any in-progress transition first
        self.update_transition()
        if self.is_transitioning:
            return

        # Movement magnitude scaled by axis |ly|
        move_amt = 0.0
        if abs(ry) > DEAD:
            # assume joystick up is negative (common convention); treat negative as forward
            move_amt = min(1.0, abs(ry_treated))

        # Map right_x (-1..1) to icr_bias (0..1)
        try:
            self.icr_bias = max(0.0, min(1.0, (ly_treated + 1.0) / 2.0))
        except Exception:
            pass

        # Mode-specific handling
        if self.curve_mode == 'straight':
            if move_amt > 0:
                if ry < 0:
                    self.makeMovement('backward', step=speed * move_amt)
                else:
                    self.makeMovement('forward', step=speed * move_amt)
            if abs(rx) > DEAD:
                # switch to curve mode with angle_offset mapped from left_x
                try:
                    new_offset = rx_treated * GLV.CURVE_MAX_RADIUS
                    # clamp
                    new_offset = max(-GLV.CURVE_MAX_RADIUS, min(GLV.CURVE_MAX_RADIUS, new_offset))
                    self.setMode('curve', curveStart=new_offset)
                    self.angle_offset = new_offset
                except Exception:
                    pass

        elif self.curve_mode in ("curve", "pivotal"):
            if self.curve_mode == "curve":
                if abs(rx) < DEAD:
                    self.setMode('straight')
                # Map left_x to angle_offset
                try:
                    # módulo de lx entre 0 e 1
                    mag = abs(rx_treated)
                    expo = 2.5
                    mag = mag ** (1/expo)
                    # interpolação invertida: mag=0 → max, mag=1 → min
                    radius = GLV.CURVE_MAX_RADIUS - (GLV.CURVE_MAX_RADIUS - GLV.CURVE_MIN_RADIUS) * mag
                    # aplica o sinal de lx (pra direita/esquerda)
                    new_offset = math.copysign(radius, -rx_treated)

                    self.angle_offset = new_offset
                except Exception:
                    pass
            else:
                # pivotal mode: left_x controls angle_offset directly
                if abs(rx) > DEAD:
                    self.angle_offset = -rx_treated * GLV.CURVE_MIN_RADIUS
                else:
                    self.angle_offset = 0

            # update icr and steering when bias/angle change
            try:
                self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
                self.steerWheels('curve', angle_offset=self.angle_offset, icr_bias=self.icr_bias)
            except Exception:
                pass
            
            if self.curve_mode == 'curve':
                if move_amt > 0:
                    if rx_treated < 0:
                        if ry_treated < 0 :
                            self.makeMovement('forward', step=speed * move_amt)
                        else:
                            self.makeMovement('backward', step=speed * move_amt)
                    else:
                        if ry_treated < 0 :
                            self.makeMovement('backward', step=speed * move_amt)
                        else:
                            self.makeMovement('forward', step=speed * move_amt)
            else:  # pivotal
                move_amt = abs(lx_treated)
                if move_amt > DEAD:
                    if lx_treated < 0:
                        self.makeMovement('backward', step=speed * move_amt)
                    else:
                        self.makeMovement('forward', step=speed * move_amt)

        elif self.curve_mode == 'diagonal':
            # allow rotation of wheel headings via left_x and movement via left_y
            if abs(rx) > DEAD:
                WHEEL_TURN_STEP = 5.0 * rx_treated
                for w in self.wheels:
                    w.setHeading((w.getHeading() + WHEEL_TURN_STEP) % 360)
            if move_amt > 0:
                if ry < 0:
                    self.makeMovement('backward', step=speed * move_amt)
                else:
                    self.makeMovement('forward', step=speed * move_amt)

        elif self.curve_mode == 'icamento':
            # left_y moves the cursor; also moves vehicle
            CURSOR_SENS = 0.035
            if abs(ry) > DEAD:
                # negative ly -> move up (decrease cursor)
                self.icamento_cursor = max(0.0, min(1.0, self.icamento_cursor + (-ry_treated) * CURSOR_SENS))
                if ry < 0:
                    self.makeMovement('forward', step=speed * move_amt)
                else:
                    self.makeMovement('backward', step=speed * move_amt)

        # sync wheel positions
        for wheel in self.wheels:
            wheel.setPosition(self.getPosition())

    def set_dead(self):
        self.state = 'morto'

    def set_alive(self, x=None, y=None):
        # Respect any death lock set by external logic (e.g. trafo-caused death)
        try:
            now = pygame.time.get_ticks()
            if getattr(self, 'death_lock_until', 0) > now:
                # still locked; ignore attempts to revive
                return
        except Exception:
            # if pygame isn't available for timing, fall back to immediate revive
            pass

        self.state = 'vivo'
        if x is not None and y is not None:
            self.x = x
            self.y = y
    def setMode(self, mode, curveStart=0, duration=None):
        # Start a mode-change transition that lasts `transition_duration_ms`.
        # While transitioning: inputs are ignored and wheel headings interpolate
        # from their current values back to default for the new mode.
        if self.is_transitioning:
            return  # avoid overlapping transitions

        prev_mode = self.curve_mode

        self.angle_offset = curveStart
        self.icr_bias = 0.5
        new_mode = mode
        self.icr_global = None

        # temporarily save current headings
        from_angles = [w.getHeading() for w in self.wheels]

        # determine destination headings depending on the mode
        to_angles = []
        if new_mode == "straight":
            # wheels align with vehicle heading
            target = (self.getHeading() + 90) % 360
            to_angles = [target for _ in self.wheels]
        elif new_mode == "diagonal":
            self.angle_offset = None
            diagonal_angle = (self.getHeading() + 90) % 360
            to_angles = [diagonal_angle for _ in self.wheels]
        elif new_mode in ["curve", "pivotal"]:
            # For curved modes, compute ICR and desired wheel headings now
            prev_temp_mode = self.curve_mode
            prev_icr = self.icr_global
            self.curve_mode = new_mode
            if new_mode in ["curve", "pivotal"]:
                self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
            # compute desired headings without mutating wheels yet
            desired = []
            icr = self.icr_global
            if icr is None:
                # fallback: align with heading
                desired = [(self.getHeading() + 90) % 360 for _ in self.wheels]
            else:
                icr_x, icr_y = icr
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
                    desired_angle = cand1 if dot1 > dot2 else cand2
                    desired.append(desired_angle)
            to_angles = desired
            # restore previous
            self.curve_mode = prev_temp_mode
            self.icr_global = prev_icr

        # If switching straight -> curve, perform immediate switch (no transition)
        if prev_mode == 'straight' and new_mode == 'curve':
            # set logical mode
            self.curve_mode = new_mode
            print("Immediate straight->curve mode switch")
            # compute ICR and immediately apply wheel steering for curve
            self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
            try:
                self.steerWheels('curve', angle_offset=self.angle_offset, icr_bias=self.icr_bias)
            except Exception:
                pass
            return

        # ensure lists have correct length
        if len(to_angles) != len(self.wheels):
            to_angles = [ (self.getHeading()+90) % 360 for _ in self.wheels]

        # start transition
        self.is_transitioning = True
        self.transition_start_ms = pygame.time.get_ticks()
        self.transition_from_angles = from_angles
        self.transition_to_angles = to_angles

        # finally update the logical mode state now (so UI shows it)
        self.curve_mode = new_mode
        print(self.icr_global  )
        # compute global ICR for modes that need it
        if self.curve_mode in ["curve", "pivotal"]:
            self.icr_global = self.curvature.computeICR(angle_offset=self.angle_offset)
        else:
            self.icr_global = None

    # --- speed mode helpers ---
    def set_speed_mode(self, mode_name):
        """Set current speed mode if available. mode_name should be one of the keys
        in self.speed_modes (e.g. 'rápida', 'média', 'lenta')."""
        if mode_name in self.speed_modes:
            self.speed_mode = mode_name

    def get_speed_multiplier(self):
        return float(self.speed_modes.get(self.speed_mode, 1.0))


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

    def update_transition(self):
        """Call regularly (each frame) to progress an ongoing mode-change transition.
        Interpolates wheel headings from transition_from_angles -> transition_to_angles
        over self.transition_duration_ms milliseconds. When complete, finalize state.
        """
        if not self.is_transitioning:
            return
        now = pygame.time.get_ticks()
        elapsed = now - (self.transition_start_ms or now)
        t = min(1.0, float(elapsed) / float(self.transition_duration_ms))

        # simple shortest-angle interpolation for each wheel
        for i, wheel in enumerate(self.wheels):
            a0 = self.transition_from_angles[i] % 360
            a1 = self.transition_to_angles[i] % 360
            # compute shortest delta
            delta = (a1 - a0 + 180) % 360 - 180
            interp = (a0 + delta * t) % 360
            wheel.setHeading(interp)

        # At halfway (or end) ensure wheel positions are synced
        for wheel in self.wheels:
            wheel.setPosition(self.getPosition())

        if t >= 1.0:
            # transition finished: snap to target headings
            for i, wheel in enumerate(self.wheels):
                try:
                    wheel.setHeading(self.transition_to_angles[i] % 360)
                except Exception:
                    pass
            self.is_transitioning = False
            self.transition_start_ms = None
            self.transition_from_angles = None
            self.transition_to_angles = None

    def toggle_mode(self):
        """Cycle through robot modes: straight -> diagonal -> pivotal -> curve -> straight."""
        # include new 'icamento' mode after 'pivotal'; 'curve' is not part of the cycle
        modes = ['straight', 'diagonal', 'pivotal', 'icamento']
        try:
            try:
                idx = modes.index(self.curve_mode)
            except ValueError:
                idx = 0
            next_mode = modes[(idx + 1) % len(modes)]
            # For curve mode use a default curveStart of 0

            self.setMode(next_mode)
            self.angle_offset = 0
        except Exception:
            pass

    def handle_event(self, event):
        """Handle incoming pygame events (keyboard)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_mode()
    def is_dead(self):
        return self.state == 'morto'
    

    def get_rotated_hitbox(self):
        """
        Retorna as partes da hitbox rotacionadas:
        - Duas linhas conectando as duas rodas frontais e as duas traseiras
        - Quatro polígonos pequenos representando as rodas (obtidos de Wheel)
        """
        # Use Wheel objects to obtain wheel polygons in world coords.
        hitbox_parts = []
        # append wheel polygons
        for wheel in self.wheels:
            try:
                wheel_poly = wheel.get_rotated_wheel_hitbox()
                hitbox_parts.append(("wheel", wheel_poly))
            except Exception:
                # fallback: ignore if wheel polygon unavailable
                continue

        # edges: connect front-left to front-right, and rear-left to rear-right
        # also add the two lateral side edges (left and right) as special parts
        # Side edges indicate death for obstacles but should not affect trafo pickup
        try:
            fl = self.wheels[0].getPosition()
            fr = self.wheels[1].getPosition()
            rl = self.wheels[2].getPosition()
            rr = self.wheels[3].getPosition()
            # front and rear horizontal edges
            hitbox_parts.append(("edge", (fl, fr)))
            hitbox_parts.append(("edge", (rl, rr)))
            # lateral edges (left and right) - special: used for obstacle collision
            hitbox_parts.append(("side", (fl, rl)))
            hitbox_parts.append(("side", (fr, rr)))
        except Exception:
            pass

        return hitbox_parts

    def get_body_polygon(self):
        """
        Returns a simple rotated rectangle polygon that represents the vehicle body
        (used for pickup checks and other full-body queries).
        """
        cx, cy = self.x, self.y
        half_w = self.width / 2.0
        half_l = self.lenght / 2.0
        theta = math.radians(self.getHeading())
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        corners = [(-half_w, -half_l), (half_w, -half_l), (half_w, half_l), (-half_w, half_l)]
        poly = []
        for dx, dy in corners:
            wx = cx + dx * cos_t - dy * sin_t
            wy = cy + dx * sin_t + dy * cos_t
            poly.append((wx, wy))
        return poly

    def get_hitbox_polygon(self, camera_or_offset=(0, 0)):
        """
        Retorna as partes da hitbox rotacionadas (linhas e rodas)
        convertidas para coordenadas de tela.
        """
        parts = self.get_rotated_hitbox()
        cam = camera_or_offset

        def to_screen(pt):
            if hasattr(cam, 'world_to_screen'):
                return cam.world_to_screen(pt)
            else:
                camx, camy = cam
                return (pt[0] - camx, pt[1] - camy)

        screen_parts = []
        for kind, data in parts:
            if kind == "edge":
                p1, p2 = map(to_screen, data)
                screen_parts.append(("edge", (p1, p2)))
            elif kind == "side":
                p1, p2 = map(to_screen, data)
                screen_parts.append(("side", (p1, p2)))
            elif kind == "wheel":
                screen_parts.append(("wheel", [to_screen(p) for p in data]))

        return screen_parts

    def _point_in_poly(self, x, y, poly):
        """Ray-casting point-in-polygon test (poly is list of (x,y))."""
        inside = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
            if intersect:
                inside = not inside
            j = i
        return inside

    def try_pickup(self, trafo):
        """Attempt to pick up a Trafo object. Pickup succeeds only if the Trafo's
        bounding rectangle is fully contained inside the player's rotated hitbox.
        On success, marks the trafo as picked and attaches it to the player."""
        if trafo.picked:
            return False
        # player's body polygon in world coords (use rectangle approximation)
        poly = self.get_body_polygon()
        # check all four corners of trafo rect are inside poly
        rect = trafo.get_rect()
        corners = [
            (rect.left, rect.top),
            (rect.right, rect.top),
            (rect.right, rect.bottom),
            (rect.left, rect.bottom),
        ]
        all_inside = True
        for (cx, cy) in corners:
            if not self._point_in_poly(cx + 0.0, cy + 0.0, poly):
                all_inside = False
                break
        if all_inside:
            try:
                trafo.pick(self)
            except Exception:
                return False
            return True

        # Fallback: accept pickup if center of trafo is inside player's hitbox
        try:
            if self._point_in_poly(trafo.x, trafo.y, poly):
                trafo.pick(self)
                return True
        except Exception:
            pass

        # Final fallback: pickup if center distance is small enough
        try:
            px, py = self.getPosition()
            dx = trafo.x - px
            dy = trafo.y - py
            dist = math.hypot(dx, dy)
            # allowable radius: smallest half-dimension of player minus half trafo size
            half_w = self.width / 2.0
            half_h = self.lenght / 2.0
            allow_radius = max(0.0, min(half_w, half_h) - (trafo.size / 2.0))
            if allow_radius <= 0:
                # if trafo is large, be permissive and allow if centers are closer than avg half-dim
                allow_radius = max(half_w, half_h) * 0.6
            if dist <= allow_radius:
                trafo.pick(self)
                return True
        except Exception:
            pass

        return False
    

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
            base_dtheta = math.radians(DEGREES_PER_STEP)

            # Limit the angular change so the arc length per movement call
            # never exceeds the requested linear `step`. Compute a candidate
            # angular change that makes the arc length equal to `step`:
            #   dtheta_candidate = step / R
            # Then cap the angular change to the base angular velocity so we
            # don't rotate faster than the vehicle allows.
            eps = 1e-6
            dtheta = min(base_dtheta, float(step) / max(R, eps))

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

    def draw_icamento_ui(self, screen):
        """Draw the icamento UI: a vertical yellow bar on the right and a gray cursor.
        This UI is now always visible; when not active (not in 'icamento' mode) it
        is drawn dimmed to indicate inactivity but still shows the current cursor
        position for reference.
        """
        # determine whether the icamento mode is currently active
        active = (self.curve_mode == 'icamento')
        try:
            # UI dimensions (screen-space)
            bar_w = 48
            bar_h = int(screen.get_height() * 0.6)
            padding_right = 18
            bar_x = screen.get_width() - bar_w - padding_right
            bar_y = screen.get_height() // 2 - bar_h // 2

            # gray moving rectangle (background) - draw it first so yellow sits on top
            # make the gray rect slightly narrower than the yellow bar (more subtle)
            gray_w = max(8, bar_w - 8)
            # gray height equal to bar_h
            gray_h = bar_h 

            # compute vertical range for gray's top position
            # min_top: almost completely inside the yellow bar, only a small head visible
            head_visible = max(6, int(bar_h * 0.08))
            min_top = bar_y - head_visible
            # apply a small downward offset to the initial position range so the
            # gray bar starts slightly lower than before
            offset_down = int(bar_h * 0.06)
            min_top += offset_down
            # max_top: half of the gray rect outside the yellow (i.e., gray top such that
            # half the gray extends below the bar)
            #max_top = bar_y + bar_h - (gray_h // 2) + offset_down

            # interpolate top position by icamento_cursor (0..1) - only vertical movement
            #gray_top = int(min_top + (max_top - min_top) * self.icamento_cursor)

            # center gray horizontally behind the yellow bar
            gray_x = bar_x + (bar_w // 2) - (gray_w // 2)

            # draw gray background bar (static)
            pygame.draw.rect(screen, (120, 120, 120), (gray_x, bar_y, gray_w, gray_h))

            # draw moving yellow rectangle on top to create illusion of the gray
            # sliding down while the yellow moves up. The yellow rect is narrower
            # vertically and moves between min_top..max_top as icamento_cursor changes.
            # make yellow taller so that at its lowest position it covers the gray
            yellow_h = bar_h #max(20, min(bar_h, int(bar_h * 0.85)))
            min_yellow_top = bar_y + bar_h - yellow_h  # bottom-aligned position
            max_yellow_top = bar_y - int(bar_h * 0.18)  # allow moving above the bar a bit
            # interpolate top by icamento_cursor so that increasing cursor moves yellow up
            yellow_top = int(min_yellow_top + (max_yellow_top - min_yellow_top) * float(self.icamento_cursor))
            yellow_x = bar_x + (bar_w // 2) - (bar_w // 2)

            if active:
                yellow_col = (220, 180, 20)
            else:
                yellow_col = (120, 100, 12)
            pygame.draw.rect(screen, yellow_col, (bar_x, yellow_top, bar_w, yellow_h))

            # if active and cursor >= 0.8 show a small READY indicator near the bar
            try:
                if active and self.icamento_cursor >= 0.8:
                    f = pygame.font.SysFont(None, 18)
                    txt = f.render('ICAMENTO READY', True, (40, 200, 40))
                    tx = bar_x - txt.get_width() - 8
                    ty = bar_y + bar_h - txt.get_height() - 8
                    screen.blit(txt, (tx, ty))
            except Exception:
                pass
        except Exception:
            pass

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


