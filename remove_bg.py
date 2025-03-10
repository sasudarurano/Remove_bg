import tkinter as tk
from tkinter import filedialog, messagebox
from rembg import remove, new_session
from PIL import Image, ImageTk
import os
import shutil
import zipfile
import threading
import queue

class BgRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Background Remover")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        self.label = tk.Label(root, text="Pilih Gambar:", font=("Arial", 14, "bold"), bg="#f0f0f0")
        self.label.pack(pady=10)

        self.btn_select = tk.Button(root, text="Pilih Gambar", command=self.select_images, font=("Arial", 12), bg="#4CAF50", fg="white", padx=10, pady=5)
        self.btn_select.pack(pady=5)

        self.frame_canvas = tk.Frame(root)
        self.frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.frame_canvas, bg="white")
        self.scrollbar = tk.Scrollbar(self.frame_canvas, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.window_frame = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_remove = tk.Button(root, text="Hapus Background", command=self.start_remove_bg, state=tk.DISABLED, font=("Arial", 12), bg="#f57c00", fg="white", padx=10, pady=5)
        self.btn_remove.pack(pady=5)

        self.btn_save = tk.Button(root, text="Simpan Gambar", command=self.save_image, state=tk.DISABLED, font=("Arial", 12), bg="#2196F3", fg="white", padx=10, pady=5)
        self.btn_save.pack(pady=5)

        self.loading_label = tk.Label(root, text="", font=("Arial", 12), bg="#f0f0f0")
        self.loading_label.pack()

        self.image_paths = []
        self.processed_images = []
        self.image_labels = []
        self.queue = queue.Queue()
        self.session = new_session("u2net")

    def select_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_paths:
            self.image_paths = file_paths
            self.display_images()
            self.btn_remove.config(state=tk.NORMAL)

    def display_images(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.image_labels = []
        for path in self.image_paths:
            img = Image.open(path)
            img_preview = img.copy()
            img_preview.thumbnail((300, 200))
            img_tk = ImageTk.PhotoImage(img_preview)
            
            frame = tk.Frame(self.scroll_frame)
            frame.pack(pady=5)
            lbl = tk.Label(frame, image=img_tk)
            lbl.image = img_tk
            lbl.pack()
            text = tk.Label(frame, text=os.path.basename(path), font=("Arial", 10), bg="white")
            text.pack()
            self.image_labels.append(lbl)
    
    def start_remove_bg(self):
        self.btn_remove.config(state=tk.DISABLED)
        self.loading_label.config(text="Memproses... Mohon tunggu")
        self.root.update()
        
        self.processed_images = []
        threading.Thread(target=self.remove_bg, daemon=True).start()

    def remove_bg(self):
        for path in self.image_paths:
            try:
                img = Image.open(path).convert("RGBA")
                processed_img = remove(img, session=self.session)
                self.queue.put((processed_img, os.path.basename(path)))
            except Exception as e:
                print(f"Gagal memproses {path}: {e}")
                self.queue.put((None, os.path.basename(path)))
        
        self.root.after(100, self.display_processed_images)

    def display_processed_images(self):
        while not self.queue.empty():
            img, filename = self.queue.get()
            if img:
                self.processed_images.append((img, filename))
                img_preview = img.copy()
                img_preview.thumbnail((300, 200))
                img_tk = ImageTk.PhotoImage(img_preview)
                
                frame = tk.Frame(self.scroll_frame)
                frame.pack(pady=5)
                lbl = tk.Label(frame, image=img_tk)
                lbl.image = img_tk
                lbl.pack()
                text = tk.Label(frame, text=f"Processed: {filename}", font=("Arial", 10), bg="white")
                text.pack()
                self.image_labels.append(lbl)
        
        self.loading_label.config(text="")
        self.btn_save.config(state=tk.NORMAL)
        messagebox.showinfo("Selesai", "Semua file sudah diproses, silahkan simpan.")

    def save_image(self):
        if self.processed_images:
            if len(self.processed_images) == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
                if save_path:
                    self.processed_images[0][0].save(save_path)
                    messagebox.showinfo("Sukses", "Gambar berhasil disimpan!")
            else:
                save_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])
                if save_path:
                    temp_dir = "temp_output"
                    os.makedirs(temp_dir, exist_ok=True)
                    for img, filename in self.processed_images:
                        img.save(os.path.join(temp_dir, filename), format="PNG")
                    with zipfile.ZipFile(save_path, "w") as zipf:
                        for file in os.listdir(temp_dir):
                            zipf.write(os.path.join(temp_dir, file), file)
                    shutil.rmtree(temp_dir)
                    messagebox.showinfo("Sukses", "Gambar berhasil disimpan dalam file ZIP!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BgRemoverApp(root)
    root.mainloop()