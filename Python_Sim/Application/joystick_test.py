
import turtle
import GVL
import uptime # Módulo para verificar o tempo de atividade do sistema
import struct # Módulo para empacotar e desempacotar dados binários 
import time   # Módulo com funções de manipulação de tempo  
import can    # Módulo Python-CAN para comunicação via barramento CAN

# Inicializa o pygame e o módulo de joystick

class Joystick:
    def __init__(self):
        # Constantes de configuração
        self.BITRATE = 500000     # Taxa de transmissão CAN em bits por segundo (500 kbps)
        self.CAN_CHANNEL = 0x200  # Canal (ID) da mensagem CAN enviada pela TTC (11 bits padrão)
        self.update_joystick()
        self.configCan()

    def update_joystick(self):
        
        self.eixo_esquerdo_x = 0#self.joystick.get_axis(0)  # Eixo X do analógico esquerdo
        self.eixo_esquerdo_y = 0#self.joystick.get_axis(1)  # Eixo Y do analógico esquerdo

        self.eixo_direito_x = 0#self.joystick.get_axis(2)  # Eixo X do analógico direito
        self.eixo_direito_y = 0#self.joystick.get_axis(3)  # Eixo Y do analógico direito (em alguns modelos é o 5)
        

        # Aqui você pode mover seu robô, por exemplo:
        # turtle.setheading(eixo_x * 180)
        # turtle.forward(eixo_y * 5)

        # Agenda a próxima leitura
        #turtle.ontimer(self.update_joystick, GVL.CONTROLLER_TICK)  # chama de novo em 100 ms

        return
    
    def getJoystickValues(self):
        return self.eixo_esquerdo_x, self.eixo_esquerdo_y, self.eixo_direito_x, self.eixo_direito_y

    def configCan(self):
        self.bus = can.interface.Bus(channel='PCAN_USBBUS1', interface='pcan', bitrate=self.BITRATE)
        self.loopHearCan()
        return
    
    def loopHearCan(self):
        # Aguarda nova mensagem CAN
        msg = self.bus.recv(timeout=.01)  
        
        # Se não há mensagens, continua
        if not (msg is None):
            # Filtra apenas mensagens com o ID esperado e exatamente 4 bytes
            if  not msg.is_extended_id and msg.arbitration_id == self.CAN_CHANNEL and msg.dlc >= 4:

                # Obtém os dados da mensagem
                data = msg.data

                # Decodifica dois inteiros de 2 bytes 
                Joystick_X_1 = struct.unpack('<h', data[0:2])[0]
                Joystick_Y_1 = struct.unpack('<h', data[2:4])[0]

                Joystick_X_2 = struct.unpack('<h', data[4:6])[0]
                Joystick_Y_2 = struct.unpack('<h', data[6:8])[0]

                # Converte para float com 1 casa decimal
                self.eixo_esquerdo_x = Joystick_X_1 / 10.0
                self.eixo_esquerdo_y = Joystick_Y_1 / 10.0

                self.eixo_direito_x = Joystick_X_2 / 10.0
                self.eixo_direito_y = Joystick_Y_2 / 10.0



                # Imprime os valores recebidos
                #print(f"Valor 1: {self.eixo_esquerdo_x:.1f}, Valor 2: {self.eixo_esquerdo_y:.1f}")
        
        turtle.ontimer(self.loopHearCan, GVL.CONTROLLER_TICK)
        return