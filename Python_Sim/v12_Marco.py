
'''
* Código para simulação de um veículo 4WS (Four-Wheel Steering)
* Criado pelo bolsista João Gabriel, em 15 de fevereiro de 2025
* Laboratory of Applied Robotics Raul Guenther - Projeto "TRAFO"
'''

''' Importação de módulos úteis ao projeto '''

import turtle # Biblioteca para construção e manipulação dos gráficos
import math   # Biblioteca para computar funções matemáticas
import time   # Biblioteca para administrar o tempo da simulação

from Robot.Pathing.Axis import Axis
from Robot.Pathing.Arrow import Arrow
from Robot.Pathing.Axes import Axes

from Robot.Drivetrain.Wheels import Wheel
from Robot.Drivetrain.Vehicle import Vehicle

from Application.Screen import Screen

import GVL



def main():

    turtle.tracer(0, 0)

    is_transitioning = False
    
    # Cria a tela e o veículo
    screen = Screen(title="Projeto TRAFO: Simulação de Veículo 4WS")
    plataforma = Vehicle("Plataforma", "DarkGoldenrod1", (0, 0))

    # Lista de modos pelos quais o 'curve_mode' vai comutar
    curvature_modes = ["straight", "diagonal", "pivotal"]
    current_mode_index = 0

    press_start_time = {"A": None, "D": None}
    is_pressed = {"A": False, "D": False}
    angle_step_base = 1


    # Offset de esterçamento para o modo 'curve'
    angle_offset = 0
    def setMode(mode):
        nonlocal current_mode_index, angle_offset, is_transitioning

        if is_transitioning:
            return
        plataforma.curvature.turtle.clear()

        new_mode = mode

        angle_offset = 0 # reseta sempre ao trocar
        plataforma.icr_bias = .5

        if new_mode in ["curve", "diagonal"]:
            smoothSteeringTransition(new_mode, target_angle=angle_offset)
        else:
            smoothSteeringTransition(new_mode)


        # Atualiza os gráficos
        
        plataforma.curvature.update(angle_offset=angle_offset)
        turtle.update()

    # Callback que alterna para o próximo modo
    def toggleMode():
        nonlocal current_mode_index, angle_offset, is_transitioning

        if is_transitioning:
            return

        next_index = (current_mode_index + 1) % len(curvature_modes)
        next_mode = curvature_modes[next_index]

        def goToNextMode():
            nonlocal current_mode_index
            current_mode_index = next_index
            setMode(next_mode)

        smoothSteeringTransition("straight",  on_complete=goToNextMode)

    def smoothSteeringTransition(mode, target_angle=0,radius=500, duration=300,prefer_clockwise=False, on_complete=None):
        nonlocal is_transitioning

        is_transitioning = True
        
        steps = 100
        interval = int(duration / steps)

        current_angles = [wheel.getHeading() for wheel in plataforma.wheels]

        # Função auxiliar para calcular os ângulos finais desejados (sem aplicar ainda)
        def computeTargetAngles():
            if mode == "straight":

                return [plataforma.getHeading()] * 4

            elif mode == "diagonal":
                return [target_angle] * 4

            elif mode == "pivotal":
                base = plataforma.getHeading()
                ang = math.degrees(math.atan2(GVL.ROBOT_LENGTH, GVL.ROBOT_WIDTH))
                return [
                    (base + 360 - ang) % 360,
                    (base + 180 + ang) % 360,
                    (base + 360 + ang) % 360,
                    (base + 180 - ang) % 360
                ]

            elif mode == "curve":
                R = radius + 10 * target_angle
                cx, cy = plataforma.getPosition()
                theta_v = math.radians(plataforma.getHeading())
                icr = (cx - R * math.cos(theta_v), cy - R * math.sin(theta_v))
                plataforma.curvature_radius = R
                vx_v, vy_v = math.cos(theta_v), math.sin(theta_v)
                final = []

                for wheel in plataforma.wheels:
                    wx, wy = wheel.getPosition()
                    rx, ry = wx - icr[0], wy - icr[1]
                    ang_r = math.degrees(math.atan2(ry, rx))

                    cand1 = (ang_r + 90) % 360
                    cand2 = (ang_r - 90) % 360

                    vx1, vy1 = math.cos(math.radians(cand1)), math.sin(math.radians(cand1))
                    vx2, vy2 = math.cos(math.radians(cand2)), math.sin(math.radians(cand2))

                    dot1 = vx1 * vx_v + vy1 * vy_v
                    dot2 = vx2 * vx_v + vy2 * vy_v

                    tangent = cand1 if dot1 > dot2 else cand2

                    if wheel.name.endswith("COL_1_wheel") or wheel.name.endswith("COL_2_wheel"):
                        final.append((tangent + 90) % 360)
                    else:
                        final.append((tangent - 90) % 360)

                return final

            else:
                return current_angles  # fallback: sem transição

        target_angles = computeTargetAngles()

        def interpolate(step):
            nonlocal is_transitioning
            if step > steps:
                plataforma.curve_mode = mode
                is_transitioning = False
                if on_complete:
                    on_complete()  # <- chama aqui!
                return

            for i, wheel in enumerate(plataforma.wheels):
                start = current_angles[i]
                end = target_angles[i]
                
                
                diff = (end - start + 540) %360 - 180 
                
                interpolated = (start + diff * (step / steps)) % 360
                wheel.setHeading(interpolated)

            
            turtle.update()
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.ontimer(lambda: interpolate(step + 1), interval)

        interpolate(1)


    # Callback para as teclas de ajuste de ângulo (aumenta)
    def updateAngleSpeed(key):
        nonlocal angle_offset

        if plataforma.curve_mode != "curve" or not is_pressed[key]:
            return

        now = time.time()
        duration = now - press_start_time[key]
        step = int(angle_step_base + duration * 3)

        if key == "D":
            angle_offset-=step

        elif key == "A":
            angle_offset = angle_offset + step

        plataforma.steerWheels("curve", angle_offset=angle_offset)
        
        if angle_offset > 100 or angle_offset < -200:
            setMode("straight")
        plataforma.curvature.update(angle_offset=angle_offset)
        turtle.update()

        # Chama de novo daqui a 30ms se ainda estiver pressionado
        turtle.ontimer(lambda: updateAngleSpeed(key), 30)

    def keyPressed_A():
        if plataforma.curve_mode == "curve" and not is_pressed["A"]:
            press_start_time["A"] = time.time()
            is_pressed["A"] = True
            updateAngleSpeed("A")
        elif plataforma.curve_mode == "diagonal":
            nonlocal angle_offset
            angle_offset += 1
            plataforma.steerWheels("diagonal", diagonal_angle=angle_offset)
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.update()
        elif plataforma.curve_mode == "straight":
            setMode("curve")

    def keyPressed_D():
        if plataforma.curve_mode == "curve" and not is_pressed["D"]:
            press_start_time["D"] = time.time()
            is_pressed["D"] = True
            updateAngleSpeed("D")
        elif plataforma.curve_mode == "diagonal":
            nonlocal angle_offset
            angle_offset -= 1
            plataforma.steerWheels("diagonal", diagonal_angle=angle_offset)
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.update()
        elif plataforma.curve_mode == "straight":
            setMode("curve")

    def keyPressed_Q():
        plataforma.icr_bias = max(0, plataforma.icr_bias - 0.05)  # permite extrapolar até um pouco antes da traseira
        if plataforma.curve_mode == "curve":
            plataforma.steerWheels("curve", angle_offset=angle_offset, icr_bias=plataforma.icr_bias)
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.update()

    def keyPressed_E():
        plataforma.icr_bias = min(1, plataforma.icr_bias + 0.05)  # extrapola até além da dianteira
        if plataforma.curve_mode == "curve":
            plataforma.steerWheels("curve", angle_offset=angle_offset, icr_bias=plataforma.icr_bias)
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.update()
    def keyReleased_A():
        is_pressed["A"] = False
        press_start_time["A"] = None

    def keyReleased_D():
        is_pressed["D"] = False
        press_start_time["D"] = None

    def ResetVehicle():
        setMode("straight")
        plataforma.setPosition((0, 0))
        for wheel in plataforma.wheels:
                wheel.setPosition(plataforma.getPosition())
        plataforma.curvature.update(angle_offset=angle_offset)
        turtle.update()

    # Callback para andar para frente
    def callMovement(direction):

        # Chama o novo método de movimento
        plataforma.makeMovement(direction, step=5.0)
        plataforma.curvature.update(angle_offset=angle_offset)

        # Atualiza os gráficos
        turtle.update()

    # Abre a escuta do turtle para o pressionamento de teclas
    turtle.listen()
    turtle.onkeypress(lambda: callMovement("forward"), "w") # Amarra o "W" para makeMovement no sentido forward
    turtle.onkeypress(lambda: callMovement("backward"), "s") # Amarra o "S" para makeMovement no sentido backward
    turtle.onkeypress(toggleMode,  "space")
    turtle.onkeypress(ResetVehicle,"r")

    turtle.onkeypress(keyPressed_A, "a")
    turtle.onkeyrelease(keyReleased_A, "a")

    turtle.onkeypress(keyPressed_D, "d")
    turtle.onkeyrelease(keyReleased_D, "d")

    turtle.onkeypress(keyPressed_Q, "q")
    turtle.onkeypress(keyPressed_E, "e")

    # Inicializa o veículo no modo "straight"
    plataforma.curve_mode = "straight"
    plataforma.steerWheels("straight")

    # Coloca o veículo em posição inicial
    plataforma.setPosition((90, 50))
    
    plataforma.updatePositionFromWheels()

    # Roda o loop principal da tela
    screen.mainLoop()
    
# Chamada incondicional da função principal
if __name__ == '__main__':
    main()