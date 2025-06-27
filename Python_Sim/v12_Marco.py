
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



def main():

    turtle.tracer(0, 0)

    
    # Cria a tela e o veículo
    screen = Screen(title="Projeto TRAFO: Simulação de Veículo 4WS")
    plataforma = Vehicle("Plataforma", "DarkGoldenrod1", (0, 0))

    # Lista de modos pelos quais o 'curve_mode' vai comutar
    curvature_modes = ["straight", "curve", "diagonal", "pivotal"]
    current_mode_index = 0

    # Offset de esterçamento para o modo 'curve'
    angle_offset = 0

    # Callback que alterna para o próximo modo
    def toggleMode():

        nonlocal current_mode_index, angle_offset

        plataforma.curvature.turtle.clear()
        
        # Avança para o próximo modo, em loop
        current_mode_index = (current_mode_index + 1) % len(curvature_modes)
        plataforma.curve_mode = curvature_modes[current_mode_index]

        # Ajusta rodas conforme o novo modo
        if plataforma.curve_mode == "straight":
            plataforma.steerWheels("straight")
        elif plataforma.curve_mode == "curve":
            plataforma.steerWheels("curve", angle_offset=0)
        elif plataforma.curve_mode == "diagonal":
            plataforma.steerWheels("diagonal", diagonal_angle=0)
        elif plataforma.curve_mode == "pivotal":
            plataforma.steerWheels("pivotal")
        
        # Atualiza os gráficos
        plataforma.curvature.update()
        turtle.update()
    
    # Callback para as teclas de ajuste de ângulo (aumenta)
    def keyPressed_A():

        nonlocal angle_offset
        angle_offset += 1

        if plataforma.curve_mode == "curve":
            plataforma.steerWheels("curve", angle_offset=angle_offset)

        elif plataforma.curve_mode == "diagonal":
            plataforma.steerWheels("diagonal", diagonal_angle=angle_offset)

        # Atualiza os gráficos
        plataforma.curvature.update()
        turtle.update()

    # Callback para as teclas de ajuste de ângulo (diminui)
    def keyPressed_D():

        nonlocal angle_offset
        angle_offset -= 1

        if plataforma.curve_mode == "curve":
            plataforma.steerWheels("curve", angle_offset=angle_offset)

        elif plataforma.curve_mode == "diagonal":
            plataforma.steerWheels("diagonal", diagonal_angle=angle_offset)

        # Atualiza os gráficos
        plataforma.curvature.update()
        turtle.update()

    def ResetVehicle():
        plataforma.setPosition((0, 0))
        for wheel in plataforma.wheels:
                wheel.setPosition(plataforma.getPosition())
        plataforma.curvature.update()
        turtle.update()

    # Callback para andar para frente
    def callMovement(direction):

        # Chama o novo método de movimento
        plataforma.makeMovement(direction, step=5.0)

        # Atualiza os gráficos
        turtle.update()

    # Abre a escuta do turtle para o pressionamento de teclas
    turtle.listen()
    turtle.onkeypress(lambda: callMovement("forward"), "w")  # Amarra o "W" para makeMovement no sentido forward
    turtle.onkeypress(lambda: callMovement("backward"), "s") # Amarra o "S" para makeMovement no sentido backward

    # Associa teclas às funções
    turtle.listen()
    turtle.onkeypress(keyPressed_A, "a")
    turtle.onkeypress(keyPressed_D, "d")
    turtle.onkeypress(toggleMode,  "space")
    turtle.onkeypress(ResetVehicle,"r")

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