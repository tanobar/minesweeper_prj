import tkinter as tk


class MinesweeperGUI:
    def __init__(self, root, n_row, n_col, m, cell_size=40):
        self.n_row = n_row
        self.n_col = n_col
        self.cell_size = cell_size

        # Get screen size to auto-scale cell size
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        # reserve space above the grid for the "mines left" box
        self.header_height = 50  

        # Compute max cell size so board fits on screen
        max_cell_w = (screen_w - 100) // n_col
        max_cell_h = (screen_h - 200 - self.header_height) // n_row
        self.cell_size = min(max_cell_w, max_cell_h, 40)
        # total canvas size = grid + header
        canvas_width = n_col * cell_size
        canvas_height = n_row * cell_size + self.header_height

        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
        self.canvas.pack()

        # colors for numbers
        self.colors = ["blue", "green", "red", "purple",
                       "lightblue", "darkgreen", "black", "black"]

        # start with fully unknown knowledge
        k = [["?" for _ in range(n_col)] for _ in range(n_row)]

        # draw initial board with mines counter
        self.draw_grid(k, m)

    def draw_grid(self, knowledge, mines_left, game=''):
        self.canvas.delete("all")  # clear previous drawing

        # --- Draw mines left box at the top ---
        box_width = 140
        box_height = 40
        center_x = (self.n_col * self.cell_size) // 2
        x1 = center_x - box_width // 2
        y1 = (self.header_height - box_height) // 2
        x2 = center_x + box_width // 2
        y2 = y1 + box_height

        self.canvas.create_rectangle(x1, y1, x2, y2,
                                    fill="lightyellow", outline="black")
        self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                text=f"Mines left: {mines_left}",
                                font=("Helvetica", 14, "bold"),
                                fill="red")

        # --- Draw the grid below the header ---
        for x in range(self.n_col):
            for y in range(self.n_row):
                x1 = x * self.cell_size
                y1 = y * self.cell_size + self.header_height
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                value = knowledge[y][x]  # row=y, col=x

                if isinstance(value, int):
                    fill = "gray"
                elif value == "?":
                    fill = "lightgray"
                elif value == "X":
                    fill = "red"
                elif value == "M":
                    fill = "black"
                else:
                    fill = "white"

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                            fill=fill, outline="black")

                if isinstance(value, int) and value > 0:
                    self.canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text=str(value),
                        fill=self.colors[value - 1]
                    )

        if game in ('n', 'y'):
            center_x = self.n_col * self.cell_size // 2
            center_y = self.header_height + (self.n_row * self.cell_size) // 2
            text = "wtf bro :(" if game == 'n' else "૮꒰ ˶• ༝ •˶꒱ა"
            self.canvas.create_text(
                center_x, center_y,
                text=text,
                fill="black",
                font=("Helvetica", 30, "bold")
            )
