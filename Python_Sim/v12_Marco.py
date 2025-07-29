
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
from Application.UI import UI

import GVL



def main():

    turtle.tracer(0, 0)

    is_transitioning = False
    
    # Cria a tela e o veículo
    
    screen = Screen(title="Projeto TRAFO: Simulação de Veículo 4WS")
    ui = UI(screen)
    plataforma = Vehicle("Plataforma", "DarkGoldenrod1", (0, 0))

    # Lista de modos pelos quais o 'curve_mode' vai comutar
    curvature_modes = ["straight", "diagonal", "pivotal", "içamento"]
    current_mode_index = 0

    press_start_time = {"A": None, "D": None}
    is_pressed = {"A": False, "D": False}
    angle_step_base = 1

    init_angle_offset = 200
    icr_curve_limit = 8

    # Offset de esterçamento para o modo 'curve'
    angle_offset = 100
    def setMode(mode, curveStart=0):
        nonlocal current_mode_index, angle_offset, is_transitioning

        if is_transitioning:
            return
        plataforma.curvature.turtle.clear()

        new_mode = mode

        angle_offset = curveStart # reseta sempre ao trocar

        plataforma.icr_bias = .5
        def on_completion():
            if new_mode == "pivotal":
                plataforma.steerWheels("curve", angle_offset=angle_offset)
            else:
                return
        
        if new_mode in ["curve", "diagonal", "pivotal"]:
            smoothSteeringTransition(new_mode, target_angle=angle_offset, on_complete=on_completion)
                
        else:
            smoothSteeringTransition(new_mode)


        # Atualiza os gráficos
        plataforma.curvature.update(angle_offset=angle_offset)
        turtle.update()

    # Callback que alterna para o próximo modo
    def toggleMode():
        nonlocal current_mode_index, is_transitioning

        if is_transitioning:
            return

        next_index = (current_mode_index + 1) % len(curvature_modes)
        next_mode = curvature_modes[next_index]

        def goToNextMode():
            nonlocal current_mode_index
            current_mode_index = next_index
            setMode(next_mode)
            ui.update_mode_display(next_mode)

        smoothSteeringTransition("straight",  on_complete=goToNextMode)

    def smoothSteeringTransition(mode, target_angle=0, duration=100, prefer_clockwise=False, on_complete=None):
        nonlocal is_transitioning
        is_transitioning = True

        steps = 100
        interval = int(duration / steps)

        current_angles = [wheel.getHeading() for wheel in plataforma.wheels]

        # Aplica os novos steerings e coleta os alvos
        plataforma.steerWheels(
            curve_mode=mode,
            diagonal_angle=target_angle,
            angle_offset=target_angle
        )

        # Coleta os headings-alvo atualizados pelas rodas
        target_angles = [wheel.getHeading() for wheel in plataforma.wheels]

        def interpolate(step):
            nonlocal is_transitioning

            if step > steps:
                plataforma.curve_mode = mode
                #ui.update_mode_display(mode)
                is_transitioning = False
                if on_complete:
                    on_complete()
                return

            for i, wheel in enumerate(plataforma.wheels):
                start = current_angles[i]
                end = target_angles[i]

                # Cálculo do menor caminho angular
                diff = (end - start + 360) % 360
                if not prefer_clockwise and diff > 180:
                    diff -= 360  # força anti-horário
                elif prefer_clockwise and diff < 180:
                    diff -= 360  # força horário

                interpolated = (start + diff * (step / steps)) % 360
                wheel.setHeading(interpolated)

            turtle.update()
            plataforma.curvature.update(angle_offset=target_angle)
            turtle.ontimer(lambda: interpolate(step + 1), interval)

        interpolate(1)


    # Callback para as teclas de ajuste de ângulo (aumenta)
    def updateAngleSpeed(key):
        nonlocal angle_offset, is_transitioning

        if (plataforma.curve_mode != "curve" and plataforma.curve_mode != "pivotal") or not is_pressed[key] or is_transitioning:
            return
        now = time.time()
        duration = now - press_start_time[key]
        step = int(angle_step_base + duration * 3)
        
        if key == "D":
            next_step = angle_offset + step
        elif key == "A":
            next_step = angle_offset - step

        if plataforma.curve_mode == "curve":
            if next_step >= icr_curve_limit or next_step <= -icr_curve_limit:
                angle_offset = next_step
        elif plataforma.curve_mode == "pivotal":
            if next_step <= icr_curve_limit and next_step >= -icr_curve_limit:
                angle_offset = next_step

        plataforma.steerWheels("curve", angle_offset=angle_offset)
        if angle_offset > 220 or angle_offset < -220:
            setMode("straight")
        else:
            plataforma.curvature.update(angle_offset=angle_offset)
        turtle.update()

        # Chama de novo daqui a 30ms se ainda estiver pressionado
        turtle.ontimer(lambda: updateAngleSpeed(key), 30)

    def keyPressed_A():
        if (plataforma.curve_mode == "curve" or plataforma.curve_mode == "pivotal") and not is_pressed["A"]:
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
            setMode("curve", init_angle_offset)

    def keyPressed_D():
        if (plataforma.curve_mode == "curve" or plataforma.curve_mode == "pivotal") and not is_pressed["D"]:
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
            setMode("curve", -init_angle_offset)

    def keyPressed_Q():
        plataforma.icr_bias = max(0, plataforma.icr_bias - 0.05)  # permite extrapolar até um pouco antes da traseira
        if plataforma.curve_mode == "curve" or plataforma.curve_mode == "pivotal":
            plataforma.steerWheels("curve", angle_offset=angle_offset, icr_bias=plataforma.icr_bias)
            plataforma.curvature.update(angle_offset=angle_offset)
            turtle.update()

    def keyPressed_E():
        plataforma.icr_bias = min(1, plataforma.icr_bias + 0.05)  # extrapola até além da dianteira
        if plataforma.curve_mode == "curve" or plataforma.curve_mode == "pivotal":
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
        ui.update_mode_display("straight")
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
        ui.clear_break()

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

    turtle.onkeyrelease(ui.draw_break, "w")
    turtle.onkeyrelease(ui.draw_break, "s")

    turtle.onkeypress(keyPressed_D, "d")
    turtle.onkeyrelease(keyReleased_D, "d")

    turtle.onkeypress(keyPressed_Q, "q")
    turtle.onkeypress(keyPressed_E, "e")

    # Inicializa o veículo no modo "straight"
    plataforma.curve_mode = "straight"
    ui.draw_box()
    ui.draw_menubar()
    ui.draw_break()
    ui.update_mode_display("straight")
    plataforma.steerWheels("straight")

    # Coloca o veículo em posição inicial
    plataforma.setPosition((90, 50))
    
    plataforma.updatePositionFromWheels()

    # Roda o loop principal da tela
    screen.mainLoop()
    
# Chamada incondicional da função principal
if __name__ == '__main__':
    main()