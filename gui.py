import tkinter as tk


class MinesweeperGUI:
    def __init__(self, root, n, cell_size=40):
        self.n = n
        self.cell_size = cell_size
        self.canvas = tk.Canvas(root, width=n*cell_size, height=n*cell_size)
        self.canvas.pack()

        # Example state: -1 = unrevealed, 0 = safe, 1 = mine
        k = [["?" for _ in range(n)] for _ in range(n)]
        
        self.draw_grid(k)

    def draw_grid(self, knowledge, game = ''):
        self.canvas.delete("all")  # clear previous drawing
        for x in range(self.n):
            for y in range(self.n):
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                value = knowledge[y][x]  # notice row=y, col=x
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
                    self.canvas.create_text(
                        self.n * self.cell_size // 2,
                        self.n * self.cell_size // 2 + 20,   # shifted 20 pixels down
                        text="wtf bro :(",
                        fill="black",
                        font=("Helvetica", 30, "bold")
                    )
                    
        elif game == 'y':
            self.canvas.create_text(
                    self.n * self.cell_size // 2,
                    self.n * self.cell_size // 2 + 20,   # shifted 20 pixels down
                    text="૮꒰ ˶• ༝ •˶꒱ა",
                    fill="black",
                    font=("Helvetica", 30, "bold")
            )
            
                    