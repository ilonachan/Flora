from tkinter import Canvas
import tkinter as tk

def window_fn():
    """
    Just a first dip into what making a Tkinter GUI looks like
    """
    window = tk.Tk()
    window.title("Canvas")
    window.config(bg="grey")
    window.geometry("400x400")
    window.resizable(False, False)

    my_canvas = Canvas(width = 350, height = 350, bg = "white")
    my_canvas.pack(pady=20)
    my_canvas.create_line(50,0,200,350, fill="red")

    window.mainloop()

class window(tk.Tk):
    def __init__(self, width, height):
        super().__init__()
        
        self.title("Canvas")
        self.config(bg = "grey")
        self.geometry(f'{width}x{height}')
        
        self.canvas = Canvas(self)
        self.canvas.pack(expand=1, fill=tk.BOTH)
        
        self.oval_element = self.canvas.create_oval(20, 20, 100, 100, width=2, fill="white")
        def enter_oval(event):
            self.canvas.itemconfigure(self.oval_element, fill="blue")
        def leave_oval(event):
            self.canvas.itemconfigure(self.oval_element, fill="white")
        self.canvas.tag_bind(self.oval_element, '<Enter>', enter_oval)
        self.canvas.tag_bind(self.oval_element, '<Leave>', leave_oval)
        
        self.canvas.pack()

def window_class():
    win = window(400, 400)
    win.mainloop()

if __name__ == "__main__":
    window_class()