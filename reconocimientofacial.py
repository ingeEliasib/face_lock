import sys
import os
import time
import ctypes
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import sysconfig
user_site = sysconfig.get_path('purelib', scheme='nt_user')
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

import cv2
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL - AJUSTABLE POR EL USUARIO
# ═══════════════════════════════════════════════════════════════════════════

UMBRAL_CONFIANZA = 70          # % mínimo para considerar rostro conocido (0-100)
TIEMPO_NO_RECONOCIDO = 10      # Segundos antes de bloquear si no se reconoce
INTERVALO_VERIFICACION = 2     # Segundos entre verificaciones (más fluido)

# ═══════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DISTANCIA_MAX = 120
ANCHO_VIDEO = 640
ALTO_VIDEO = 480
ANCHO_MOSTRAR = 500
ALTO_MOSTRAR = 375

ARCHIVO_LOG = "logs_security_core.txt"


def distancia_a_confianza(distancia: float) -> int:
    return int(max(0.0, (1.0 - distancia / DISTANCIA_MAX) * 100.0))


def escribir_log(texto):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{fecha}] {texto}\n")
    except Exception:
        pass


def log_error(tag, exc_info=None):
    detalle = "".join(traceback.format_exception(*exc_info)) if exc_info else traceback.format_exc()
    escribir_log(f" ERROR [{tag}]: {detalle}")


class MonitorFacial:
    def __init__(self, window):
        self.window = window
        self.window.title("Security Core DNN")
        self.window.geometry(f"{ANCHO_MOSTRAR + 40}x{ALTO_MOSTRAR + 200}")
        self.window.configure(bg="#111111")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.minsize(400, 480)

        # Estado del sistema
        self.cap = None
        self.net = None
        self.recognizer = None
        self.frame_actual = None
        
        # Control de detección
        self.confianza_minima_dnn = 0.5
        self.ultima_verificacion = time.time()
        self.tiempo_sin_reconocer = None
        self.rostro_detectado = False
        self.en_pausa = False
        self.esperando_desbloqueo = False

        escribir_log(f" Security Core DNN INICIADO | Umbral: {UMBRAL_CONFIANZA}% | Timeout: {TIEMPO_NO_RECONOCIDO}s")

        if not self._cargar_recursos():
            return

        # Pantalla de carga
        temp_label = tk.Label(window, text="INICIANDO SISTEMA...\nCargando red neuronal", 
                             font=("Consolas", 12, "bold"), fg="#00ff88", bg="#111111")
        temp_label.pack(expand=True)
        window.update()
        time.sleep(2)
        temp_label.destroy()

        if not self._iniciar_camara():
            return

        self._crear_ui()
        self.actualizar_frame()

    def _cargar_recursos(self):
        try:
            # Cargar modelo de reconocimiento facial
            modelo_path = os.path.join(BASE_DIR, "modelo_rostro.yml")
            if not os.path.exists(modelo_path):
                escribir_log(" ERROR: No se encuentra modelo_rostro.yml")
                messagebox.showerror("Error", 
                    "No se encuentra 'modelo_rostro.yml'.\n\n"
                    "Ejecute primero el programa de entrenamiento.")
                self.window.destroy()
                return False

            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(modelo_path)
            escribir_log(" ✓ Modelo facial cargado")

            # Cargar red neuronal DNN
            prototxt_path = os.path.join(BASE_DIR, "deploy.prototxt")
            model_path = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000_fp16.caffemodel")
            
            if not os.path.exists(prototxt_path) or not os.path.exists(model_path):
                escribir_log(" ERROR: Archivos DNN no encontrados")
                messagebox.showerror("Error", 
                    "Faltan archivos del detector DNN:\n\n"
                    "- deploy.prototxt\n"
                    "- res10_300x300_ssd_iter_140000_fp16.caffemodel")
                self.window.destroy()
                return False
            
            self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            escribir_log(" ✓ Red neuronal DNN cargada")
            return True
            
        except Exception as e:
            log_error("cargar_recursos")
            messagebox.showerror("Error", f"Error al cargar recursos:\n{e}")
            self.window.destroy()
            return False

    def _iniciar_camara(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                escribir_log(" ERROR: No se pudo abrir la camara")
                messagebox.showerror("Error", "No se pudo acceder a la camara.")
                self.window.destroy()
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_VIDEO)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_VIDEO)
            escribir_log(" ✓ Camara iniciada")
            return True
        except Exception as e:
            log_error("iniciar_camara")
            messagebox.showerror("Error", f"Error al iniciar camara:\n{e}")
            self.window.destroy()
            return False

    def detectar_rostro_dnn(self, frame):
        """Detecta rostros usando red neuronal profunda (múltiples ángulos)"""
        if self.net is None:
            return []
            
        (h, w) = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        self.net.setInput(blob)
        detecciones = self.net.forward()
        
        rostros = []
        for i in range(detecciones.shape[2]):
            confianza = detecciones[0, 0, i, 2]
            
            if confianza > self.confianza_minima_dnn:
                box = detecciones[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x2, y2) = box.astype("int")
                
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                if x2 > x and y2 > y:
                    rostros.append({
                        'x': x, 
                        'y': y, 
                        'w': x2 - x, 
                        'h': y2 - y,
                        'confianza': confianza
                    })
        
        rostros.sort(key=lambda r: r['confianza'], reverse=True)
        return rostros

    def _crear_ui(self):
        # Video
        self.lbl_video = tk.Label(self.window, bg="black")
        self.lbl_video.pack(pady=(10, 2))

        # Panel de información
        frame_info = tk.Frame(self.window, bg="#1a1a2e", pady=8)
        frame_info.pack(fill="x", padx=10)

        # Estado principal
        self.lbl_estado = tk.Label(frame_info, text="ESPERANDO ROSTRO...", 
                                   font=("Consolas", 14, "bold"), fg="#00ff88", bg="#1a1a2e")
        self.lbl_estado.pack(pady=(0, 5))

        # Contador regresivo
        self.lbl_contador = tk.Label(frame_info, text="", 
                                     font=("Consolas", 28, "bold"), fg="#ff4444", bg="#1a1a2e")
        self.lbl_contador.pack(pady=(0, 5))

        # Confianza y distancia
        self.lbl_confianza = tk.Label(frame_info, text="Confianza: ---", 
                                      font=("Consolas", 10), fg="#cccccc", bg="#1a1a2e")
        self.lbl_confianza.pack()

        # Umbral configurado
        self.lbl_umbral = tk.Label(frame_info, 
                                   text=f"Umbral configurado: {UMBRAL_CONFIANZA}% | Timeout: {TIEMPO_NO_RECONOCIDO}s", 
                                   font=("Consolas", 8), fg="#888888", bg="#1a1a2e")
        self.lbl_umbral.pack(pady=(5, 0))

        # Botones
        frame_btns = tk.Frame(self.window, bg="#111111", pady=8)
        frame_btns.pack()

        tk.Button(frame_btns, text=" PAUSAR", command=self.pausar, 
                 bg="#f39c12", fg="white", font=("Arial", 9, "bold"), 
                 width=14, relief="flat").pack(side="left", padx=4)

        tk.Button(frame_btns, text=" REANUDAR", command=self.reanudar, 
                 bg="#27ae60", fg="white", font=("Arial", 9, "bold"), 
                 width=14, relief="flat").pack(side="left", padx=4)

        tk.Button(frame_btns, text=" SALIR", command=self.on_closing, 
                 bg="#c0392b", fg="white", font=("Arial", 9, "bold"), 
                 width=14, relief="flat").pack(side="left", padx=4)

    def bloquear_pc(self):
        """Bloquea la estación de trabajo"""
        escribir_log(" BLOQUEO DEL SISTEMA - Rostro no reconocido")
        self.lbl_estado.config(text="BLOQUEANDO...", fg="#ff0000")
        self.window.update()
        time.sleep(1)
        try:
            ctypes.windll.user32.LockWorkStation()
        except Exception as e:
            log_error("bloquear_pc")
        
        # Entrar en modo espera
        self.en_pausa = True
        self.esperando_desbloqueo = True
        self._cerrar_camara()
        self.lbl_video.configure(image='', text="SISTEMA BLOQUEADO\nEsperando desbloqueo...", 
                                fg="#ff4444", font=("Consolas", 14, "bold"), bg="#111111")
        self.lbl_contador.config(text="")

    def pausar(self):
        self.en_pausa = True
        self._cerrar_camara()
        self.lbl_estado.config(text="SISTEMA PAUSADO", fg="#f39c12")
        self.lbl_contador.config(text="")
        escribir_log(" Sistema pausado por usuario")

    def reanudar(self):
        self.en_pausa = False
        self.esperando_desbloqueo = False
        self.tiempo_sin_reconocer = None
        self.lbl_contador.config(text="")
        self.lbl_estado.config(text="REANUDANDO...", fg="#00ff88")
        escribir_log(" Sistema reanudado por usuario")

    def _cerrar_camara(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def actualizar_frame(self):
        try:
            self._loop_actualizar_frame()
        except Exception:
            log_error("actualizar_frame")
            self.window.after(2000, self.actualizar_frame)

    def _loop_actualizar_frame(self):
        ahora = time.time()

        # Modo espera por bloqueo
        if self.esperando_desbloqueo:
            # Verificar si ya se desbloqueó
            if not self._esta_bloqueado():
                if not hasattr(self, 'tiempo_desbloqueo'):
                    self.tiempo_desbloqueo = ahora
                
                if ahora - self.tiempo_desbloqueo < 2.0:
                    self.window.after(500, self.actualizar_frame)
                    return
                
                delattr(self, 'tiempo_desbloqueo')
                self.esperando_desbloqueo = False
                self.en_pausa = False
                self.tiempo_sin_reconocer = None
                escribir_log(" PC desbloqueado - reanudando monitoreo")
            else:
                self.window.after(2000, self.actualizar_frame)
                return

        # Modo pausa manual
        if self.en_pausa:
            self.window.after(1000, self.actualizar_frame)
            return

        # Reactivar cámara si es necesario
        if self.cap is None or not self.cap.isOpened():
            try:
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.window.after(1000, self.actualizar_frame)
                    return
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_VIDEO)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_VIDEO)
                self.tiempo_sin_reconocer = None
                self.lbl_contador.config(text="")
            except Exception:
                self.window.after(1000, self.actualizar_frame)
                return

        # Capturar frame
        ret, frame = self.cap.read()
        if not ret:
            self.window.after(100, self.actualizar_frame)
            return

        frame = cv2.flip(frame, 1)
        self.frame_actual = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar rostros con DNN
        rostros = self.detectar_rostro_dnn(frame)

        # ── LÓGICA DE RECONOCIMIENTO ─────────────────────────────────────
        rostro_reconocido = False
        mejor_confianza = 0
        mejor_distancia = 999

        if len(rostros) > 0:
            for rostro in rostros:
                try:
                    x, y, w, h = rostro['x'], rostro['y'], rostro['w'], rostro['h']
                    rostro_img = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                    _, dist = self.recognizer.predict(rostro_img)
                    conf = distancia_a_confianza(dist)
                    
                    if conf > mejor_confianza:
                        mejor_confianza = conf
                        mejor_distancia = dist

                    # ¿Cumple con el umbral configurado?
                    if conf >= UMBRAL_CONFIANZA:
                        rostro_reconocido = True
                        # Dibujar rectángulo verde
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, f"OK {conf}%", (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        break
                    else:
                        # Dibujar rectángulo rojo (rostro no reconocido)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame, f"NO {conf}%", (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                except Exception:
                    log_error("predict_rostro")
                    continue

        # ── ACTUALIZAR ESTADO Y CONTADOR ─────────────────────────────────
        if rostro_reconocido:
            # Rostro reconocido - resetear contador
            self.tiempo_sin_reconocer = None
            self.lbl_estado.config(text="✓ ROSTRO RECONOCIDO", fg="#00ff88")
            self.lbl_contador.config(text="")
            self.lbl_confianza.config(text=f"Confianza: {mejor_confianza}% | Distancia: {mejor_distancia:.1f}")
        else:
            # No reconocido - iniciar/continuar contador
            if self.tiempo_sin_reconocer is None:
                self.tiempo_sin_reconocer = ahora
            
            tiempo_transcurrido = ahora - self.tiempo_sin_reconocer
            segundos_restantes = max(0, TIEMPO_NO_RECONOCIDO - int(tiempo_transcurrido))
            
            if len(rostros) > 0:
                self.lbl_estado.config(text="⚠ ROSTRO NO RECONOCIDO", fg="#ffaa00")
                self.lbl_confianza.config(text=f"Confianza: {mejor_confianza}% (mínimo: {UMBRAL_CONFIANZA}%)")
            else:
                self.lbl_estado.config(text="SIN ROSTRO DETECTADO", fg="#ffaa00")
                self.lbl_confianza.config(text="Confianza: ---")
            
            # Mostrar contador regresivo
            if segundos_restantes > 0:
                # Efecto visual: más rojo y grande cuando se acerca a 0
                if segundos_restantes <= 3:
                    color = "#ff0000"
                    tamaño = 36
                elif segundos_restantes <= 5:
                    color = "#ff4444"
                    tamaño = 32
                else:
                    color = "#ffaa00"
                    tamaño = 28
                    
                self.lbl_contador.config(text=str(segundos_restantes), 
                                        fg=color, 
                                        font=("Consolas", tamaño, "bold"))
            else:
                # Tiempo agotado - BLOQUEAR
                self.lbl_contador.config(text="¡BLOQUEO!", fg="#ff0000", 
                                        font=("Consolas", 36, "bold"))
                self.window.update()
                self.bloquear_pc()
                return

        # Marca de agua DNN
        cv2.putText(frame, f"DNN Multi-angulo | Umbral: {UMBRAL_CONFIANZA}%", 
                   (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

        # Mostrar frame
        img = Image.fromarray(cv2.cvtColor(cv2.resize(frame, (ANCHO_MOSTRAR, ALTO_MOSTRAR)), cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        self.lbl_video.imgtk = imgtk
        self.lbl_video.configure(image=imgtk)
        
        self.window.after(15, self.actualizar_frame)

    def _esta_bloqueado(self):
        try:
            user32 = ctypes.windll.user32
            hdesk = user32.OpenInputDesktop(0, False, 0)
            if hdesk == 0:
                return True
            name = ctypes.create_unicode_buffer(256)
            needed = ctypes.c_uint(0)
            if user32.GetUserObjectInformationW(hdesk, 2, name, 512, ctypes.byref(needed)):
                user32.CloseDesktop(hdesk)
                return name.value != "Default"
            user32.CloseDesktop(hdesk)
            return False
        except Exception:
            return True

    def on_closing(self):
        escribir_log(" SISTEMA CERRADO POR USUARIO")
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self.window.destroy()


def manejar_excepcion_global(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log_error("GLOBAL", (exc_type, exc_value, exc_traceback))


if __name__ == "__main__":
    sys.excepthook = manejar_excepcion_global
    
    print("=" * 60)
    print("  SECURITY CORE DNN - RECONOCIMIENTO FACIAL")
    print("=" * 60)
    print(f"  Umbral de confianza: {UMBRAL_CONFIANZA}%")
    print(f"  Tiempo sin reconocer: {TIEMPO_NO_RECONOCIDO} segundos")
    print(f"  Detector: DNN Multi-ángulo")
    print("=" * 60)
    
    escribir_log(" Aplicacion iniciada")
    root = tk.Tk()
    try:
        app = MonitorFacial(root)
        if hasattr(app, 'window') and app.window.winfo_exists():
            root.mainloop()
    except Exception:
        log_error("main")
        messagebox.showerror("Error Fatal", "Error al iniciar la aplicacion.")
