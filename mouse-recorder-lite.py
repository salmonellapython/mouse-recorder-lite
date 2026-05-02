"""
mouse-recorder-lite v2.0
Fare hareketlerini kaydeder ve tekrar oynatır.
Hiçbir veri internet üzerinden gönderilmez.

"""

import time
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
import json

class mouserecorderliteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("mouse-recorder-lite V2.0")
        self.root.geometry("400x250")

        self.actions = []
        self.recording = False
        self.playing = False
        self.mouse_ctrl = MouseController()

        self.mouse_listener = None
        self.kb_listener = None

        self.create_menu()

        self.label_status = tk.Label(root, text="Durum: Hazır", font=("Segoe UI", 11))
        self.label_status.pack(pady=15)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.btn_record = tk.Button(btn_frame, text="Kayıt Başlat (F9)", width=18, height=2,
                                    command=self.toggle_record, bg="#4CAF50", fg="white")
        self.btn_record.grid(row=0, column=0, padx=10)

        self.btn_play = tk.Button(btn_frame, text="Oynat (F10)", width=18, height=2,
                                  command=self.toggle_play, bg="#2196F3", fg="white", state="disabled")
        self.btn_play.grid(row=0, column=1, padx=10)

        tk.Button(root, text="Programdan Çık", width=30, height=2,
                  command=self.on_closing, bg="#f44336", fg="white").pack(pady=20)

        self.start_listeners()

    # ================= MENU =================
    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Kaydı Aç (.json)", command=self.import_actions)
        file_menu.add_command(label="Kaydı Kaydet (.json)", command=self.export_actions)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.on_closing)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Kayıtları Göster", command=self.show_actions)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about)

        menubar.add_cascade(label="Dosya", menu=file_menu)
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        menubar.add_cascade(label="Yardım", menu=help_menu)

        self.root.config(menu=menubar)

    # ================= ABOUT =================
    def show_about(self):
        messagebox.showinfo(
            "Hakkında",
            "mouse-recorder-lite V2.0\n\n"
            "Fare hareketlerini kaydeder ve tekrar oynatır.\n\n"
            "✔ Açık kaynak olarak paylaşılabilir\n\n"
            "✔ F9   - Kayıt Başlat\n\n"
            "✔ F10  - Oynat\n\n"
            "✔ Çıkış- Programdan çıkış\n\n"
            "Geliştirici: S@lmonell@"
        )

    # ================= LISTENERS =================
    def start_listeners(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.kb_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener.start()
        self.kb_listener.start()

    def on_move(self, x, y):
        if self.recording:
            self.actions.append(('move', x, y, time.perf_counter()))

    def on_click(self, x, y, button, pressed):
        if self.recording and pressed:
            self.actions.append(('click', x, y, str(button), time.perf_counter()))

    def on_scroll(self, x, y, dx, dy):
        if self.recording:
            self.actions.append(('scroll', x, y, dx, dy, time.perf_counter()))

    def on_press(self, key):
        if key == keyboard.Key.f9:
            self.toggle_record()
        elif key == keyboard.Key.f10:
            self.toggle_play()
        elif key == keyboard.Key.esc:
            self.on_closing()

    # ================= RECORD =================
    def toggle_record(self):
        self.recording = not self.recording

        if self.recording:
            self.actions.clear()
            self.label_status.config(text="Kayıt DEVAM EDİYOR...", fg="green")
            self.btn_record.config(text="Kayıt Durdur", bg="#f44336")
            self.btn_play.config(state="disabled")
        else:
            count = len(self.actions)
            self.label_status.config(text=f"Kayıt bitti - {count} eylem", fg="blue")
            self.btn_record.config(text="Kayıt Başlat", bg="#4CAF50")
            if count > 0:
                self.btn_play.config(state="normal")

    # ================= PLAY =================
    def toggle_play(self):
        if not self.actions:
            messagebox.showwarning("Uyarı", "Kayıt yok!")
            return

        self.playing = not self.playing

        if self.playing:
            self.label_status.config(text="Oynatma çalışıyor...", fg="purple")
            self.btn_play.config(text="Durdur", bg="#f44336")
            self.btn_record.config(state="disabled")
            threading.Thread(target=self.play_loop, daemon=True).start()
        else:
            self.label_status.config(text="Durduruldu", fg="blue")
            self.btn_play.config(text="Oynat", bg="#2196F3")
            self.btn_record.config(state="normal")

    def play_loop(self):
        while self.playing and self.actions:
            start_time = time.perf_counter()
            base_time = self.actions[0][-1]

            for action in self.actions:
                if not self.playing:
                    break

                delay = (start_time + (action[-1] - base_time)) - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)

                if action[0] == 'move':
                    self.mouse_ctrl.position = (action[1], action[2])
                elif action[0] == 'click':
                    self.mouse_ctrl.position = (action[1], action[2])
                    btn = Button.left if 'left' in action[3] else Button.right
                    self.mouse_ctrl.click(btn)
                elif action[0] == 'scroll':
                    self.mouse_ctrl.position = (action[1], action[2])
                    self.mouse_ctrl.scroll(action[3], action[4])

    # ================= JSON =================
    def export_actions(self):
        if not self.actions:
            messagebox.showwarning("Uyarı", "Kayıt yok!")
            return

        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.actions, f, indent=2)

    def import_actions(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.actions = json.load(f)
                self.btn_play.config(state="normal")
                self.label_status.config(text="Kayıt yüklendi", fg="green")
            except:
                messagebox.showerror("Hata", "Dosya okunamadı!")

    # ================= VIEW =================
    def show_actions(self):
        win = tk.Toplevel(self.root)
        win.title("Kayıtlar")

        text = tk.Text(win, width=70, height=20)
        text.pack()

        for a in self.actions:
            text.insert(tk.END, str(a) + "\n")

    # ================= CLOSE =================
    def on_closing(self):
        self.playing = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.kb_listener:
            self.kb_listener.stop()
        self.root.destroy()

# Açık kaynak kodlu uygulamam  alıntı yapıldığında geliştirici ismi lüften paylaşın S@lmonell@

if __name__ == "__main__":
    root = tk.Tk()
    app = mouserecorderliteApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


