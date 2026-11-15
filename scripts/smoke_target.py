"""Temporary visible target used by the packaged-app smoke test."""

import tkinter as tk

root = tk.Tk()
root.title("ScreenTranslatorSmokeTarget")
root.geometry("760x180+200+200")
root.configure(bg="white")
tk.Label(
    root,
    text="Screen translator works",
    font=("Arial", 32, "bold"),
    bg="white",
    fg="black",
).pack(expand=True)
root.mainloop()
