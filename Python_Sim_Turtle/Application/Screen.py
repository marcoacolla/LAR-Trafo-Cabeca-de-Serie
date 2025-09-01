import turtle
# Classe para gerenciamento da tela
class Screen:

    # Método construtor da classe
    def __init__(self, title):
        # Inicialização da tartaruga que representa a instância da classe
        self.screen = turtle.Screen()
        self.screen.setup(width=1.0, height=1.0)
        self.screen.title(title)
        # Cor de fundo suave
        self.screen.bgcolor("#e0e7ef")  # azul claro
        # Pegar largura e altura atuais
        self.screen_width = self.screen.window_width()
        self.screen_height = self.screen.window_height()
        # Cria turtle do grid para redesenho
        self.grid = turtle.Turtle()
        self.grid.hideturtle()
        self.grid.speed(0)
        self.grid.color("#b0b8c8")
        self.grid.penup()
        self.grid_step = 100
        self.camera_offset = (0, 0)
        self.draw_grid()

    def draw_grid(self):
        self.grid.clear()
        ox, oy = self.camera_offset
        step = self.grid_step
        # Linhas verticais
        for x in range(-self.screen_width//2, self.screen_width//2+1, step):
            self.grid.penup()
            self.grid.goto(x - ox % step, -self.screen_height//2)
            self.grid.pendown()
            self.grid.goto(x - ox % step, self.screen_height//2)
        # Linhas horizontais
        for y in range(-self.screen_height//2, self.screen_height//2+1, step):
            self.grid.penup()
            self.grid.goto(-self.screen_width//2, y - oy % step)
            self.grid.pendown()
            self.grid.goto(self.screen_width//2, y - oy % step)
        self.grid.penup()

    def update_camera(self, robo_x, robo_y):
        # Atualiza o offset da câmera para centralizar o robô
        # O grid se move no sentido oposto ao movimento lógico do robô
        self.camera_offset = (-robo_x, -robo_y)
        self.draw_grid()

    # Roda o loop de animações
    def mainLoop(self):
        turtle.update()
        turtle.mainloop()
