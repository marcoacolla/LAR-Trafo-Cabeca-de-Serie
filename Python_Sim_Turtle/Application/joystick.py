
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
        self.CAN_CHANNEL_JOYSTICK = 0x200 # Canal (ID) da mensagem CAN enviada pela TTC (11 bits padrão)
        self.CAN_CHANNEL_SELETORA = 0x201
        self.update_joystick()
        self.can_available = False
        try:
            self.configCan()
            self.can_available = True
        except Exception as e:
            print(f"[Joystick] CAN não disponível: {e}\nModo teclado liberado.")

    def update_joystick(self):
        
        self.eixo_esquerdo_x = 0
        self.eixo_esquerdo_y = 0

        self.eixo_direito_x = 0
        self.eixo_direito_y = 0
        
        self.currentMode = 0
        self.hasChangedMode = False

        return
    
    def getJoystickValues(self):
        return self.eixo_esquerdo_x, self.eixo_esquerdo_y, self.eixo_direito_x, self.eixo_direito_y

    def configCan(self):
        self.bus = can.interface.Bus(channel='PCAN_USBBUS1', interface='pcan', bitrate=self.BITRATE)
        # Limpa mensagens antigas que já estão na fila
        while True:
            msg = self.bus.recv(timeout=0.1)
            if msg is None:
                break
        self.loopHearCan()
        return
    
    def loopHearCan(self):
        if not getattr(self, 'can_available', True):
            return
        # Aguarda nova mensagem CAN
        msg = self.bus.recv(timeout=.01)  
        # Se não há mensagens, continua
        if not (msg is None):
            # Filtra apenas mensagens com o ID esperado e exatamente 4 bytes
            if  not msg.is_extended_id and msg.dlc >= 2:
                # Obtém os dados da mensagem
                data = msg.data
                if msg.arbitration_id == self.CAN_CHANNEL_JOYSTICK:
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
                elif msg.arbitration_id == self.CAN_CHANNEL_SELETORA:
                    # Decodifica dois inteiros de 2 bytes 
                    selectedMode = struct.unpack('<h', data[0:2])[0]
                    if selectedMode != self.currentMode:
                        self.currentMode = selectedMode
                        self.hasChangedMode = True
        turtle.ontimer(self.loopHearCan, GVL.CONTROLLER_TICK)
        return