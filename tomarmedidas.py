import sys, os, cv2, numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Inyección de ruta (soporte multi-versión)
rutas_pip = [
    os.path.expanduser(r"~\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"),
    os.path.join(os.environ.get('APPDATA', ''), 'Python', 'Python313', 'site-packages'),
]
for ruta in rutas_pip:
    if os.path.exists(ruta) and ruta not in sys.path:
        sys.path.append(ruta)

class Registrador:
    def __init__(self, window):
        self.window = window
        self.window.title("Entrenamiento de Rostro - Captura Manual")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ── NUEVO: Detector DNN (más robusto) ─────────────────────────────
        # Descarga los archivos del modelo desde:
        # https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_uint8/
        # O usa los que vienen con OpenCV contrib
        self.net = cv2.dnn.readNetFromCaffe(
            "deploy.prototxt",           # Arquitectura del modelo
            "res10_300x300_ssd_iter_140000_fp16.caffemodel"  # Pesos
        )
        self.confianza_minima = 0.5  # Umbral de detección
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.cap = cv2.VideoCapture(0)
        
        # Mejorar calidad de cámara
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Estado
        self.muestras = []
        self.total_fotos = 10
        self.frame_actual = None

        # ── UI mejorada ──────────────────────────────────────────────────
        self.lbl_video = tk.Label(window)
        self.lbl_video.pack()

        self.lbl_progreso = tk.Label(
            window, text="Fotos capturadas: 0 / 10",
            font=("Consolas", 11), fg="gray"
        )
        self.lbl_progreso.pack(pady=2)

        self.lbl_instrucciones = tk.Label(
            window,
            text="Presione CAPTURAR cuando esté listo\nPuede girar e inclinar la cabeza libremente",
            font=("Arial", 12, "bold"), fg="blue", justify="center"
        )
        self.lbl_instrucciones.pack(pady=8)

        # Frame de botones
        frame_btns = tk.Frame(window)
        frame_btns.pack(pady=5)

        self.btn_capturar = tk.Button(
            frame_btns, text="📸  CAPTURAR",
            command=self.capturar_manual,
            bg="#1a7a1a", fg="white",
            font=("Arial", 13, "bold"),
            width=18, height=2
        )
        self.btn_capturar.pack(side="left", padx=10)

        self.btn_deshacer = tk.Button(
            frame_btns, text="↩ Deshacer última",
            command=self.deshacer_ultima,
            bg="#8B0000", fg="white",
            font=("Arial", 10),
            width=16
        )
        self.btn_deshacer.pack(side="left", padx=10)

        self.btn_guardar = tk.Button(
            window, text="💾  Guardar Modelo",
            command=self.finalizar_entrenamiento,
            bg="#003580", fg="white",
            font=("Arial", 11, "bold"),
            width=22, state="disabled"
        )
        self.btn_guardar.pack(pady=8)

        self.sugerencias = [
            "Frente neutral", "Sonría", "Perfil derecho",
            "Perfil izquierdo", "Mirando arriba",
            "Mirando abajo", "Inclinado derecha",
            "Inclinado izquierda", "Cerca de cámara",
            "Lejos de cámara"
        ]

        self.actualizar()

    # ── NUEVO: Detección con DNN ─────────────────────────────────────────
    def detectar_rostro_dnn(self, frame):
        """Detecta rostros usando red neuronal profunda"""
        (h, w) = frame.shape[:2]
        
        # Preparar imagen para la red neuronal
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)  # Valores medios para normalización
        )
        
        self.net.setInput(blob)
        detecciones = self.net.forward()
        
        rostros = []
        for i in range(detecciones.shape[2]):
            confianza = detecciones[0, 0, i, 2]
            
            if confianza > self.confianza_minima:
                # Obtener coordenadas
                box = detecciones[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x2, y2) = box.astype("int")
                
                # Asegurar que esté dentro de la imagen
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                if x2 > x and y2 > y:  # Rectángulo válido
                    rostros.append({
                        'x': x, 
                        'y': y, 
                        'w': x2 - x, 
                        'h': y2 - y,
                        'confianza': confianza
                    })
        
        # Ordenar por confianza (mejor primero)
        rostros.sort(key=lambda r: r['confianza'], reverse=True)
        return rostros

    # ── Bucle de video mejorado ──────────────────────────────────────────
    def actualizar(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            self.frame_actual = frame.copy()

            # Usar DNN para detección
            rostros = self.detectar_rostro_dnn(frame)
            
            # Dibujar detecciones
            for rostro in rostros:
                x, y, w, h = rostro['x'], rostro['y'], rostro['w'], rostro['h']
                conf = rostro['confianza']
                
                # Rectángulo principal
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Etiqueta con confianza
                cv2.putText(
                    frame, 
                    f"Rostro ({conf:.0%})", 
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 255, 0), 
                    2
                )
                
                # Puntos de referencia (ojos, nariz, boca aproximados)
                # Esto ayuda visualmente a ver la calidad de detección
                centro_x = x + w//2
                centro_y = y + h//2
                cv2.circle(frame, (centro_x, centro_y), 3, (255, 0, 0), -1)

            # Mostrar FPS para debug
            cv2.putText(
                frame,
                f"Detector: DNN | Rostros: {len(rostros)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)

        self.window.after(15, self.actualizar)

    # ── Captura manual mejorada ──────────────────────────────────────────
    def capturar_manual(self):
        if self.frame_actual is None:
            return

        if len(self.muestras) >= self.total_fotos:
            messagebox.showinfo("Info", "Ya tiene 10 fotos. Guarde el modelo.")
            return

        # Usar DNN para detectar
        gray = cv2.cvtColor(self.frame_actual, cv2.COLOR_BGR2GRAY)
        rostros = self.detectar_rostro_dnn(self.frame_actual)

        if len(rostros) == 0:
            self.lbl_instrucciones.config(
                text="⚠ No se detectó rostro. Asegúrese de estar frente a la cámara.",
                fg="red"
            )
            return

        # Usar el rostro con mayor confianza
        mejor_rostro = rostros[0]
        x, y, w, h = mejor_rostro['x'], mejor_rostro['y'], mejor_rostro['w'], mejor_rostro['h']
        
        rostro = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
        self.muestras.append(rostro)

        n = len(self.muestras)
        self.lbl_progreso.config(text=f"Fotos capturadas: {n} / {self.total_fotos}")

        if n < self.total_fotos:
            siguiente = self.sugerencias[n] if n < len(self.sugerencias) else "Cualquier ángulo"
            self.lbl_instrucciones.config(
                text=f"✅ Foto {n} guardada — Siguiente: {siguiente}",
                fg="green"
            )
        else:
            self.lbl_instrucciones.config(
                text="✅ ¡10 fotos completadas! Presione 'Guardar Modelo'.",
                fg="darkgreen"
            )
            self.btn_guardar.config(state="normal")
            self.btn_capturar.config(state="disabled")

    # ── Deshacer ──────────────────────────────────────────────────────────
    def deshacer_ultima(self):
        if self.muestras:
            self.muestras.pop()
            n = len(self.muestras)
            self.lbl_progreso.config(text=f"Fotos capturadas: {n} / {self.total_fotos}")
            self.lbl_instrucciones.config(
                text=f"Foto eliminada. Total: {n}. Siga capturando.",
                fg="orange"
            )
            self.btn_guardar.config(state="disabled")
            self.btn_capturar.config(state="normal")
        else:
            self.lbl_instrucciones.config(text="No hay fotos que deshacer.", fg="gray")

    # ── Guardar modelo ────────────────────────────────────────────────────
    def finalizar_entrenamiento(self):
        if len(self.muestras) < 5:
            messagebox.showwarning("Pocas muestras", "Necesita al menos 5 fotos para entrenar.")
            return

        self.lbl_instrucciones.config(text="Procesando modelo...", fg="blue")
        self.window.update()

        etiquetas = np.array([1] * len(self.muestras))
        self.recognizer.train(self.muestras, etiquetas)
        self.recognizer.write("modelo_rostro.yml")

        messagebox.showinfo(
            "Modelo Guardado",
            f"Modelo entrenado con {len(self.muestras)} imágenes.\n"
            "Archivo: modelo_rostro.yml"
        )
        self.on_closing()

    def on_closing(self):
        if self.cap.isOpened():
            self.cap.release()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Registrador(root)
    root.mainloop()
