import turtle

class UI:
    def __init__(self, screen):
        self.a_screen = screen
        # Calcular posição do canto superior esquerdo (ajustar um pouco para não cortar o texto)
        self.mode_text_x = -(self.a_screen.screen_width) // 2 + 60
        self.mode_text_y = -self.a_screen.screen_height // 2 + 110
        # Cria uma turtle só pra texto
        self.status_turtle = turtle.Turtle()
        self.break_turtle = turtle.Turtle()
        self.error_turtle = turtle.Turtle()
        self.menu_turtle = turtle.Turtle()

        self.break_turtle.hideturtle()
        self.error_turtle.hideturtle()
        self.status_turtle.hideturtle()
        self.menu_turtle.hideturtle()

        self.status_turtle.penup()
        self.status_turtle.goto(self.mode_text_x, self.mode_text_y)  # posição no topo esquerdo da tela
        self.status_turtle.color("blue")   # cor do texto
        self.status_turtle.speed(0)

        
    def draw_ui_box(self, x, y, width, height):
        turtle.penup()
        turtle.goto(x, y)
        turtle.pendown()
        turtle.pensize(2)
        turtle.color("red")
        
        for _ in range(2):
            turtle.forward(width)
            turtle.right(90)
            turtle.forward(height)
            turtle.right(90)
        
        turtle.penup()
        turtle.hideturtle()

    def draw_break(self):
        self.break_turtle.clear()
        self.break_turtle.hideturtle()
        self.break_turtle.penup()
        self.break_turtle.goto(self.mode_text_x - 20, self.mode_text_y+ 1)
        self.break_turtle.color("blue")
        self.break_turtle.write("⍟", font=("Arial", 14, "bold"))

    def clear_break(self):
        self.break_turtle.clear()

    def show_error(self):
        self.error_turtle.clear()
        self.error_turtle.hideturtle()
        self.error_turtle.penup()
        self.error_turtle.goto(self.mode_text_x - 30, self.mode_text_y - 60)
        self.error_turtle.color("blue")
        self.error_turtle.write("! Aviso ERRO", font=("Arial", 14, "bold"))

    def clear_error(self):
        self.error_turtle.clear()

    def update_mode_display(self, mode):
        self.status_turtle.clear()
        if mode == "straight":
            modeToWrite = "Normal"
        elif mode == "pivotal":
            modeToWrite = "Rotaçao"
        elif mode == "diagonal":
            modeToWrite = "Desliza"
        elif mode == "içamento":
            modeToWrite = "Içamento"
        self.status_turtle.write(f"Modo: {modeToWrite}", font=("Arial", 14, "bold"))
    
    def draw_menubar(self):
        self.menu_turtle.clear()
        self.menu_turtle.penup()
        self.menu_turtle.goto(self.mode_text_x + 170, self.mode_text_y - 60)
        self.menu_turtle.color("blue")
        self.menu_turtle.write("Menu ->", font=("Arial", 14, "bold"))

    def draw_box(self):
        box_width = 300
        box_height = 100
        self.draw_ui_box(((-self.a_screen.screen_width) // 2) + 10, ((-self.a_screen.screen_height) // 2) + 140, box_width, box_height)
        #self.draw_error_message("Erro: Curvatura inválida")