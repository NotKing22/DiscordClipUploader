import time
import tkinter as tk
from tkinter import messagebox, Entry, LabelFrame, END, filedialog
from tkinter.ttk import Progressbar
from threading import Thread, Event
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path

import pyperclip
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from utils import get_video_info_and_shortlink
import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DiscordClipUploader:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord clip uploader v2.0")
        self.root.geometry("500x580")
        self.root.configure(bg="#36393F")

        # Caminho do .ico no titulo usando resource_path
        self.root.iconbitmap(resource_path('monkey.ico'))

        self.file_path = ""
        self.upload_speed = tk.StringVar()
        self.eta = tk.StringVar()
        self.cancel_upload_event = Event()

        self.label = tk.Label(self.root, text="Nome do Clip:", bg="#36393F", fg="white")
        self.label.pack(pady=10)

        self.text_field = Entry(self.root, width=30, bg="white", fg="black")  # Alterado de #36393F para black
        self.text_field.pack(pady=3)

        # Botão de seleção de nome do clip
        self.btn_select_name = tk.Button(self.root, text="Nome Automático", command=self.set_clip_name, bg="#7289DA", fg="white")
        self.btn_select_name.pack(pady=10)

        self.frame = LabelFrame(self.root, text="Arraste e solte os arquivos aqui", width=400, height=200, bg="#2C2F33", fg="white")
        self.frame.pack(pady=15)

        self.frame.drop_target_register(DND_FILES)
        self.frame.dnd_bind('<<Drop>>', self.drop)
        self.frame.bind("<Button-1>", self.browse_file)

        self.btn_upload = tk.Button(self.root, text="Upload", command=self.upload_file, padx=50, pady=5, bg="#7289DA", fg="white")
        self.btn_upload.pack(pady=10)

        # Botão de cancelar upload começa oculto
        self.btn_cancel_upload = tk.Button(self.root, text="Cancelar Upload", command=self.cancel_upload, padx=50, pady=5, bg="red", fg="white")
        self.btn_cancel_upload.pack(pady=10)
        self.btn_cancel_upload.pack_forget()  # Ocultar inicialmente

        self.lbl_drag_and_drop = tk.Label(self.root,
                                          text="Arraste um arquivo para a caixa acima, ou clique para selecionar um arquivo.\n Em seguida, pressione o botão",
                                          bg="#36393F", fg="white")
        self.lbl_drag_and_drop.pack()

        self.progress = None
        self.lbl_speed = None
        self.lbl_eta = None

    def clear_progress_elements(self):
        if self.progress:
            self.progress.destroy()
        if self.lbl_speed:
            self.lbl_speed.destroy()
        if self.lbl_eta:
            self.lbl_eta.destroy()

    def upload_file(self):
        if not self.file_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo primeiro")
            return

        # Se o nome do clip estiver vazio, atribuir "⠀" (nome sem texto visivel)
        if not self.text_field.get():
            self.text_field.insert(0, "⠀")

        self.clear_progress_elements()

        self.progress = Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.lbl_speed = tk.Label(self.root, textvariable=self.upload_speed, bg="#36393F", fg="white")
        self.lbl_speed.pack()
        self.lbl_eta = tk.Label(self.root, textvariable=self.eta, bg="#36393F", fg="white")
        self.lbl_eta.pack()

        # Desabilitar o campo de nome botões de upload e "Nome Automático" durante o upload
        self.text_field.config(state='disabled')
        self.btn_upload.config(state='disabled')
        self.btn_select_name.config(state='disabled')  # Desabilitar o botão "Nome Automático"

        # Exibir o botão de cancelar upload
        self.btn_cancel_upload.pack()  # Exibir o botão
        self.btn_cancel_upload.config(state='normal')

        # Iniciar a thread de upload
        upload_thread = Thread(target=self.upload_threaded)
        self.cancel_upload_event.clear()
        upload_thread.start()

    def upload_threaded(self):
        start_time = time.time()

        def callback(monitor):
            if self.cancel_upload_event.is_set():
                raise Exception("Upload cancelado")

            elapsed_time = time.time() - start_time
            speed = monitor.bytes_read / elapsed_time / (1024 * 1024)  # MB/s
            self.upload_speed.set(f"Velocidade: {speed:.2f} MB/s")

            if speed > 0:
                remaining_time = (monitor.len - monitor.bytes_read) / (speed * 1024 * 1024)  # segundos
                self.eta.set(f"Tempo restante: {remaining_time:.2f} segundos")

            self.progress['value'] = (monitor.bytes_read / monitor.len) * 100
            self.root.update_idletasks()

        multipart_data = MultipartEncoder(
            fields={
                'files[]': (Path(self.file_path).name, open(self.file_path, 'rb'), 'text/plain')
            }
        )

        monitor = MultipartEncoderMonitor(multipart_data, callback)

        url = 'https://up1.fileditch.com/upload.php'

        try:
            response = requests.post(url, data=monitor, headers={'Content-Type': monitor.content_type})
            self.eta.set("Quase lá...")

            if response.status_code == 200:
                try:
                    json_response = response.json()  # Capturando erro de JSON
                    link = json_response['files'][0]['url']

                    tocopy = "[" + self.text_field.get() + "](" + get_video_info_and_shortlink(link, self.file_path) + ")"
                    pyperclip.copy(tocopy)
                    messagebox.showinfo("Sucesso!", "O link do clip foi copiado para a área de transferência! Você pode enviá-lo no Discord.")
                except ValueError as ve:
                    messagebox.showerror("Erro", f"Falha no upload!\nResposta inesperada do servidor (não é JSON): {response.text}\nErro: {ve}")
                except KeyError as ke:
                    messagebox.showerror("Erro", f"Falha no upload!\nFormato de resposta inválido: {response.json()}\nErro: {ke}")
            else:
                messagebox.showerror("Erro", f"Falha no upload!\nCódigo de status: {response.status_code}\nResposta do servidor: {response.text}")
        except requests.RequestException as re:
            messagebox.showerror("Erro", f"Falha na requisição!\nErro: {str(re)}")
        except Exception as e:
            if str(e) == "Upload cancelado":
                messagebox.showinfo("Cancelado", "O upload foi cancelado com sucesso!")
            else:
                messagebox.showerror("Erro", f"Falha no upload!\nTipo de erro: {type(e).__name__}\nErro: {str(e)}")

        # Restabelecer o estado dos botões e do campo de texto ao finalizar o upload
        self.progress['value'] = 0
        self.upload_speed.set("")
        self.eta.set("")
        self.file_path = ""
        self.frame.config(text="Arraste e solte os arquivos aqui")
        self.text_field.config(state='normal')
        self.text_field.delete(0, END)
        self.btn_upload.config(state='normal')
        self.btn_select_name.config(state='normal')  # Restaura o state do botão "Nome Automático"
        self.btn_cancel_upload.pack_forget()  # Ocultar o botão após inicio do upload

    def cancel_upload(self):
        self.cancel_upload_event.set()

    def set_clip_name(self):
        if self.file_path:
            clip_name = Path(self.file_path).stem
            self.text_field.delete(0, END)
            self.text_field.insert(0, clip_name)
        else:
            self.text_field.delete(0, END)

    def drop(self, event):
        if event.data.startswith('{'):
            event.data = event.data[1:]
        if event.data.endswith('}'):
            event.data = event.data[:-1]
        self.file_path = event.data
        self.frame.config(text=f"Arquivo selecionado: {Path(self.file_path).name}")

    def browse_file(self, event):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path = file_path
            self.frame.config(text=f"Arquivo selecionado: {Path(self.file_path).name}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = DiscordClipUploader(root)
    app.run()
