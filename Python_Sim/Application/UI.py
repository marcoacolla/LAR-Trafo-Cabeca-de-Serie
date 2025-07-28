import turtle
class UI:
    def __init__(self, screen):
        # Calcular posição do canto superior esquerdo (ajustar um pouco para não cortar o texto)
        text_x = -(screen.screen_width) // 2 + 20
        text_y = screen.screen_height // 2 - 40
        # Cria uma turtle só pra texto
        self.status_turtle = turtle.Turtle()
        self.status_turtle.hideturtle()
        self.status_turtle.penup()
        self.status_turtle.goto(text_x, text_y)  # posição no topo esquerdo da tela
        self.status_turtle.color("blue")   # cor do texto
        self.status_turtle.speed(0)

        
        
    def update_mode_display(self, mode):
        self.status_turtle.clear()
        self.status_turtle.write(f"Modo de curva: {mode}", font=("Arial", 14, "bold"))