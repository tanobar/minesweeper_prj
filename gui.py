import tkinter as tk


class MinesweeperGUI:
    def __init__(self, root, n_row, n_col, cell_size=40):
        self.n_row = n_row
        self.n_col = n_col
        self.cell_size = cell_size
        self.canvas = tk.Canvas(root, width=n_col*cell_size, height=n_row*cell_size)
        self.canvas.pack()

        
        k = [["?" for _ in range(n_col)] for _ in range(n_row)]
        
        self.draw_grid(k)

    def draw_grid(self, knowledge, game = ''):
        self.canvas.delete("all")  # clear previous drawing
        for x in range(self.n_col):
            for y in range(self.n_row):
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                value = knowledge[y][x]  # nota row=y, col=x
                if isinstance(value,int):
                    fill = "gray"
                elif value == "?":
                    fill = "lightgray"
                elif value == "X":
                    fill = "red"
                elif value == "M":
                    fill = "black"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="black")
                # disegna il numero se è un int>0
                if isinstance(value, int) and value >0:
                    self.canvas.create_text(
                        (x1+x2)//2, (y1+y2)//2, text=str(value), fill="black"
                    )
        if game == 'n':
                    center_x = self.n_col * self.cell_size // 2
                    center_y = self.n_row * self.cell_size // 2
                    self.canvas.create_text(
                        center_x,
                        center_y,   # shifted 20 pixels down
                        text="wtf bro :(",
                        fill="black",
                        font=("Helvetica", 30, "bold")
                    )
                    
        elif game == 'y':
            center_x = self.n_col * self.cell_size // 2
            center_y = self.n_row * self.cell_size // 2
            self.canvas.create_text(
                    center_x,
                    center_y, 
                    text="૮꒰ ˶• ༝ •˶꒱ა",
                    fill="black",
                    font=("Helvetica", 30, "bold")
            )
            
                    