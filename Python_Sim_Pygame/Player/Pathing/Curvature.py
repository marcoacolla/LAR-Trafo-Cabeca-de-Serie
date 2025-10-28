import pygame
import math

# Classe que representa a curvatura descrita como trajetória pelos objetos
class Curvature:

    # Método construtor da classe
    def __init__(self, parent, color="blue"):

        # Inicialização dos atributos da classe
        self.vehicle = parent   # Veículo cuja trajetória será gerada
        self.base_color = color # Define a cor base para os desenhos
        self.surface = parent.surface  # Superfície onde será desenhado

    def clear(self):
        self.surface.fill((255, 255, 255))
    
    # Calcula o Centro Instantâneo de Rotação com base na interseção das linhas de direção das rodas
    def computeICR(self, angle_offset=0):
        wheels = self.vehicle.wheels
        if self.vehicle.curve_mode in ["curve", "pivotal"]:
            # Cálculo idêntico para ambos os modos
            # Use posições em coordenadas do mundo (globais)
            cx, cy = self.vehicle.getPosition()  # centro do robô (mundo)
            theta = math.radians(self.vehicle.getHeading())

            # O bias_offset é ao longo do eixo Y local do robô
            bias_offset = (self.vehicle.icr_bias - 0.5) * self.vehicle.lenght
            # Eixo Y local: 90 graus em relação ao heading do robô
            perp_angle = theta + math.pi / 2
            base_x = cx + bias_offset * math.cos(perp_angle)
            base_y = cy + bias_offset * math.sin(perp_angle)

            # Usa o raio de curvatura (deve estar definido)
            R = 10 * angle_offset

            # Calcula o ICR a partir do ponto base deslocado, na direção do heading do robô
            icr_x = base_x - R * math.cos(theta)
            icr_y = base_y - R * math.sin(theta)

            # Retorna em coordenadas do mundo (globais)
            return (icr_x, icr_y)
        
        def intersection(w1, w2):
            # Use posições em coordenadas do mundo para calcular a interseção
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
            # Retorna em coordenadas do mundo
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
    def update(self, surface):
        # Decide what to draw depending on the current vehicle mode.
        mode = getattr(self.vehicle, 'curve_mode', 'straight')

        # For straight and diagonal modes: draw long helper rays following
        # each wheel's heading. Do NOT draw the ICR circle in these modes to
        # avoid the tiny-center-circle visual glitch; the long rays are useful
        # guidance for driver in both straight and diagonal modes.
        if mode in ["straight", "diagonal"]:
            for wheel in self.vehicle.wheels:
                wheel_pos = wheel.getCameraRelativePosition()  # posição visual (tela)
                wheel_heading = wheel.getHeading() - 90
                line_length = 1000
                angle_rad = math.radians(wheel_heading)
                # convenção: heading=0 aponta para cima na tela, e cresce no sentido horário
                end_x = wheel_pos[0] + line_length * math.sin(angle_rad)
                end_y = wheel_pos[1] - line_length * math.cos(angle_rad)
                w = 2
                cam = self.vehicle.camera
                if hasattr(cam, 'scale'):
                    w = max(1, int(round(w * cam.scale)))
                pygame.draw.line(self.surface, self.base_color,
                                 wheel_pos, (end_x, end_y), w)
            return

        # Preferir o ICR global já calculado pelo veículo (fixo no mundo)
        # se disponível; caso contrário, calcule localmente.
        if getattr(self.vehicle, 'icr_global', None) is not None:
            icr = self.vehicle.icr_global
        else:
            icr = self.computeICR(angle_offset=self.vehicle.angle_offset)
        # Todas as posições desenhadas são relativas ao centro da tela (0,0)

        # Se não foi possível determinar o círculo, desenha as retas da trajetória
        # (desenhamos usando coordenadas projetadas para a tela)
        if icr is None:
            for wheel in self.vehicle.wheels:
                wheel_pos = wheel.getCameraRelativePosition()  # posição visual (tela)
                wheel_heading = wheel.getHeading() - 90
                line_length = 1000
                angle_rad = math.radians(wheel_heading)
                # convenção: heading=0 aponta para cima na tela, e cresce no sentido horário
                end_x = wheel_pos[0] + line_length * math.sin(angle_rad)
                end_y = wheel_pos[1] - line_length * math.cos(angle_rad)
                w = 2
                cam = self.vehicle.camera
                if hasattr(cam, 'scale'):
                    w = max(1, int(round(w * cam.scale)))
                pygame.draw.line(self.surface, self.base_color,
                                 wheel_pos, (end_x, end_y), w)
            return

        # icr retornado por computeICR está em coordenadas do mundo
        # Converta posições para coordenadas relativas à câmera apenas para desenhar
        cam = self.vehicle.camera
        if hasattr(cam, 'world_to_screen'):
            vehicle_center = cam.world_to_screen(self.vehicle.getPosition())
            icr_vis = cam.world_to_screen(icr)
        else:
            cam_off = cam.camera_offset
            vehicle_center_world = self.vehicle.getPosition()
            vehicle_center = (vehicle_center_world[0] - cam_off[0], vehicle_center_world[1] - cam_off[1])
            icr_vis = (icr[0] - cam_off[0], icr[1] - cam_off[1])

        dx = vehicle_center[0] - icr_vis[0]
        dy = vehicle_center[1] - icr_vis[1]
        main_radius = math.sqrt(dx*dx + dy*dy)
        # círculo principal de curvatura
        w = 1
        cam = self.vehicle.camera
        if hasattr(cam, 'scale'):
            w = max(1, int(round(w * cam.scale)))
        pygame.draw.circle(self.surface, self.base_color,
                           (int(icr_vis[0]), int(icr_vis[1])), int(main_radius), w)

        # ponto do ICR (vis)
        radius_vis = 5
        if hasattr(cam, 'scale'):
            radius_vis = int(round(radius_vis * cam.scale))
        pygame.draw.circle(self.surface, self.base_color,
                           (int(icr_vis[0]), int(icr_vis[1])), radius_vis)


        # linhas veículo/rodas -> ICR
        for wheel in self.vehicle.wheels:
            wheel_pos = wheel.getCameraRelativePosition(cam)  # posição visual (usa scale)
            w = 1
            if hasattr(cam, 'scale'):
                w = max(1, int(round(w * cam.scale)))
            pygame.draw.line(self.surface, self.base_color,
                             wheel_pos, icr_vis, w)

        w = 1
        if hasattr(cam, 'scale'):
            w = max(1, int(round(w * cam.scale)))
        pygame.draw.line(self.surface, self.base_color,
                         vehicle_center, icr_vis, w)

        # círculos individuais para cada roda
        for wheel in self.vehicle.wheels:
            # use posições do mundo para calcular ângulos corretamente (evita problemas
            # com a inversão do eixo Y na tela)
            wx_world, wy_world = wheel.getPosition()
            # projeção para tela
            if hasattr(cam, 'world_to_screen'):
                wx_vis, wy_vis = cam.world_to_screen((wx_world, wy_world))
            else:
                wx_vis = wx_world - cam_off[0]
                wy_vis = wy_world - cam_off[1]

            dx = wx_vis - icr_vis[0]
            dy = wy_vis - icr_vis[1]
            r = int(math.sqrt(dx**2 + dy**2))
            w = 1
            if hasattr(cam, 'scale'):
                w = max(1, int(round(w * cam.scale)))
            pygame.draw.circle(self.surface, (128, 128, 128),
                               (int(icr_vis[0]), int(icr_vis[1])), r, w)

            # Ângulo do raio em coordenadas do mundo (vetor do wheel -> icr)
            angle_to_icr = math.atan2(icr[1] - wy_world, icr[0] - wx_world)

            # Heading da roda = tangente ao círculo = perpendicular ao raio
            wheel_heading = math.degrees(angle_to_icr + math.pi/2)

            # Normalize para [0,360)
            wheel_heading = wheel_heading % 360
            # Não atualiza o heading da roda aqui — o steering é responsabilidade
            # do Player (setMode / steerWheels). Aqui apenas desenhamos a ajuda
            # visual da curvatura.