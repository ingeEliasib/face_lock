"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SECURITY CORE DNN - v2.0                                ║
║                 Sistema de Bloqueo Facial Inteligente                      ║
║                   Desarrollado por Ing. Elíasib Cadena M.                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import ctypes
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Inyección de ruta (soporte multi-versión)
import sysconfig
user_site = sysconfig.get_path('purelib', scheme='nt_user')
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

import cv2
import numpy as np

# ── NUEVO: Detección nativa de eventos de sesión Windows ──────────────────────
try:
    import threading
    import win32con
    import win32gui
    import win32ts

    WM_WTSSESSION_CHANGE = 0x2B1
    WTS_SESSION_LOCK     = 0x7
    WTS_SESSION_UNLOCK   = 0x8

    class SessionWatcher:
        """
        Escucha eventos de bloqueo/desbloqueo de Windows usando la API nativa.
        Corre en un hilo de fondo y llama a los callbacks registrados.
        No toca ninguna lógica existente; solo notifica.
        """
        def __init__(self):
            self._callbacks_unlock = []
            self._callbacks_lock   = []
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        def on_unlock(self, fn):
            """Registra una función que se llama cuando Windows se desbloquea."""
            self._callbacks_unlock.append(fn)

        def on_lock(self, fn):
            """Registra una función que se llama cuando Windows se bloquea."""
            self._callbacks_lock.append(fn)

        def _wnd_proc(self, hwnd, msg, wparam, lparam):
            if msg == WM_WTSSESSION_CHANGE:
                if wparam == WTS_SESSION_UNLOCK:
                    escribir_log("🔓 [SessionWatcher] Windows desbloqueado (evento nativo)")
                    for fn in self._callbacks_unlock:
                        try:
                            fn()
                        except Exception:
                            pass
                elif wparam == WTS_SESSION_LOCK:
                    escribir_log("🔒 [SessionWatcher] Windows bloqueado (evento nativo)")
                    for fn in self._callbacks_lock:
                        try:
                            fn()
                        except Exception:
                            pass
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        def _run(self):
            try:
                wc = win32gui.WNDCLASS()
                wc.lpfnWndProc  = self._wnd_proc
                wc.lpszClassName = "SecurityCoreSW"
                wc.hInstance    = win32gui.GetModuleHandle(None)
                win32gui.RegisterClass(wc)
                hwnd = win32gui.CreateWindow(
                    wc.lpszClassName, "SecurityCoreSW",
                    0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
                )
                win32ts.WTSRegisterSessionNotification(hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
                win32gui.PumpMessages()          # Bloquea el hilo esperando mensajes
            except Exception:
                pass                            # Si falla, el polling existente sigue funcionando

    SESSION_WATCHER_DISPONIBLE = True

except ImportError:
    SESSION_WATCHER_DISPONIBLE = False          # pywin32 no instalado → solo polling
# ─────────────────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL
# ═══════════════════════════════════════════════════════════════════════════

UMBRAL_CONFIANZA = 70          # % mínimo para considerar rostro conocido (0-100)
TIEMPO_NO_RECONOCIDO = 10      # Segundos antes de bloquear si no se reconoce
TIEMPO_ESPERA_DESBLOQUEO = 2   # Segundos de espera tras desbloquear Windows

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))


if getattr(sys, 'frozen', False):
    # Si está corriendo como .exe → carpeta donde está el ejecutable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si está corriendo como script normal → carpeta del archivo .py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


DISTANCIA_MAX = 120
ANCHO_VIDEO = 640
ALTO_VIDEO = 480
ANCHO_MOSTRAR = 500
ALTO_MOSTRAR = 375
ARCHIVO_LOG = "logs_security_core.txt"

# Colores de la interfaz
COLOR_FONDO = "#0a0a0f"
COLOR_PANEL = "#13131f"
COLOR_VERDE = "#00ff88"
COLOR_ROJO = "#ff4444"
COLOR_NARANJA = "#ffaa00"
COLOR_AZUL = "#0088ff"
COLOR_MORADO = "#9b59b6"


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES UTILITARIAS
# ═══════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL (LAUNCHER)
# ═══════════════════════════════════════════════════════════════════════════

class MenuPrincipal:
    """Ventana principal de selección de módulo"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Security Core DNN - Launcher")
        self.root.geometry("550x480")
        self.root.configure(bg=COLOR_FONDO)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.salir)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.root.winfo_screenheight() // 2) - (480 // 2)
        self.root.geometry(f"550x480+{x}+{y}")
        
        self._crear_ui()
        self.root.mainloop()
    
    def _crear_ui(self):
        # Título principal
        frame_titulo = tk.Frame(self.root, bg=COLOR_FONDO, pady=20)
        frame_titulo.pack(fill="x")
        
        tk.Label(frame_titulo, text="SECURITY CORE DNN", 
                font=("Consolas", 22, "bold"), fg=COLOR_VERDE, bg=COLOR_FONDO).pack()
        
        tk.Label(frame_titulo, text="Sistema de Bloqueo Facial Inteligente", 
                font=("Consolas", 10), fg="#888888", bg=COLOR_FONDO).pack(pady=(5, 0))
        
        # Separador
        tk.Frame(self.root, bg=COLOR_VERDE, height=2, width=400).pack(pady=10)
        
        # Estado del sistema
        frame_estado = tk.Frame(self.root, bg=COLOR_PANEL, padx=20, pady=15)
        frame_estado.pack(fill="x", padx=30, pady=10)
        
        modelo_existe = os.path.exists(os.path.join(BASE_DIR, "modelo_rostro.yml"))
        dnn_existe = (os.path.exists(os.path.join(BASE_DIR, "deploy.prototxt")) and 
                     os.path.exists(os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000_fp16.caffemodel")))
        
        if modelo_existe:
            tk.Label(frame_estado, text="✅ Modelo facial: ENCONTRADO", 
                    font=("Consolas", 9), fg=COLOR_VERDE, bg=COLOR_PANEL).pack(anchor="w")
        else:
            tk.Label(frame_estado, text="⚠ Modelo facial: NO ENCONTRADO - Ejecute Entrenamiento", 
                    font=("Consolas", 9), fg=COLOR_NARANJA, bg=COLOR_PANEL).pack(anchor="w")
        
        if dnn_existe:
            tk.Label(frame_estado, text="✅ Red neuronal DNN: CARGADA", 
                    font=("Consolas", 9), fg=COLOR_VERDE, bg=COLOR_PANEL).pack(anchor="w")
        else:
            tk.Label(frame_estado, text="❌ Red neuronal DNN: FALTAN ARCHIVOS", 
                    font=("Consolas", 9), fg=COLOR_ROJO, bg=COLOR_PANEL).pack(anchor="w")
        
        tk.Label(frame_estado, 
                text=f"Umbral: {UMBRAL_CONFIANZA}% | Timeout: {TIEMPO_NO_RECONOCIDO}s | Espera desbloqueo: {TIEMPO_ESPERA_DESBLOQUEO}s",
                font=("Consolas", 8), fg="#666666", bg=COLOR_PANEL).pack(anchor="w", pady=(5, 0))
        
        # Botones de módulos
        frame_botones = tk.Frame(self.root, bg=COLOR_FONDO, pady=20)
        frame_botones.pack(expand=True)
        
        # Botón: MODO MONITOREO
        btn_monitoreo = tk.Button(
            frame_botones, 
            text="🔒  INICIAR MONITOREO\n(Reconocimiento en tiempo real)",
            command=self.iniciar_monitoreo,
            bg="#003580", fg="white",
            font=("Consolas", 12, "bold"),
            width=40, height=3,
            relief="flat", cursor="hand2",
            activebackground="#004aaa", activeforeground="white"
        )
        btn_monitoreo.pack(pady=8)
        
        tk.Label(frame_botones, text="Bloquea el PC si no detecta tu rostro", 
                font=("Arial", 8), fg="#888888", bg=COLOR_FONDO).pack()
        
        # Separador pequeño
        tk.Frame(frame_botones, bg="#222222", height=1, width=300).pack(pady=15)
        
        # Botón: MODO ENTRENAMIENTO
        btn_entrenamiento = tk.Button(
            frame_botones, 
            text="📸  ENTRENAR ROSTRO\n(Capturar muestras faciales)",
            command=self.iniciar_entrenamiento,
            bg="#1a5c1a", fg="white",
            font=("Consolas", 12, "bold"),
            width=40, height=3,
            relief="flat", cursor="hand2",
            activebackground="#228822", activeforeground="white"
        )
        btn_entrenamiento.pack(pady=8)
        
        tk.Label(frame_botones, text="Captura tu rostro en diferentes ángulos para mejorar precisión", 
                font=("Arial", 8), fg="#888888", bg=COLOR_FONDO).pack()
        
        # Pie
        frame_pie = tk.Frame(self.root, bg=COLOR_FONDO, pady=15)
        frame_pie.pack(side="bottom", fill="x")
        
        tk.Label(frame_pie, text="© 2024 Ing. Elíasib Cadena M. | Security Core DNN v2.0", 
                font=("Consolas", 7), fg="#555555", bg=COLOR_FONDO).pack()
        
        btn_salir = tk.Button(
            frame_pie, text="✕  SALIR", command=self.salir,
            bg="#8B0000", fg="white",
            font=("Consolas", 10, "bold"),
            width=15, relief="flat", cursor="hand2"
        )
        btn_salir.pack(pady=5)
    
    def iniciar_monitoreo(self):
        """Cierra el menú y abre el módulo de monitoreo"""
        self.root.withdraw()  # Oculta el menú en lugar de destruirlo
        
        # Crear nueva ventana para el monitor
        ventana_monitor = tk.Toplevel()
        ventana_monitor.protocol("WM_DELETE_WINDOW", lambda: self._volver_al_menu(ventana_monitor))
        
        try:
            app = MonitorFacial(ventana_monitor, callback_volver=lambda: self._volver_al_menu(ventana_monitor))
        except Exception as e:
            log_error("iniciar_monitoreo")
            messagebox.showerror("Error", f"Error al iniciar monitoreo:\n{e}")
            self._volver_al_menu(ventana_monitor)
    
    def iniciar_entrenamiento(self):
        """Cierra el menú y abre el módulo de entrenamiento"""
        self.root.withdraw()
        
        ventana_entrenamiento = tk.Toplevel()
        ventana_entrenamiento.protocol("WM_DELETE_WINDOW", lambda: self._volver_al_menu(ventana_entrenamiento))
        
        try:
            app = Registrador(ventana_entrenamiento, callback_volver=lambda: self._volver_al_menu(ventana_entrenamiento))
        except Exception as e:
            log_error("iniciar_entrenamiento")
            messagebox.showerror("Error", f"Error al iniciar entrenamiento:\n{e}")
            self._volver_al_menu(ventana_entrenamiento)
    
    def _volver_al_menu(self, ventana_hija):
        """Destruye la ventana hija y muestra el menú principal"""
        try:
            ventana_hija.destroy()
        except Exception:
            pass
        self.root.deiconify()  # Muestra el menú de nuevo
        # Actualizar estado
        for widget in self.root.winfo_children():
            widget.destroy()
        self._crear_ui()
    
    def salir(self):
        self.root.destroy()
        sys.exit(0)


# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO DE MONITOREO FACIAL
# ═══════════════════════════════════════════════════════════════════════════

class MonitorFacial:
    def __init__(self, window, callback_volver=None):
        self.window = window
        self.callback_volver = callback_volver
        self.window.title("Security Core DNN - Monitoreo")
        self.window.geometry(f"{ANCHO_MOSTRAR + 40}x{ALTO_MOSTRAR + 200}")
        self.window.configure(bg="#111111")
        self.window.minsize(400, 480)

        # Estado del sistema
        self.cap = None
        self.net = None
        self.recognizer = None
        self.frame_actual = None
        
        # Control de detección
        self.confianza_minima_dnn = 0.5
        self.tiempo_sin_reconocer = None
        self.en_pausa = False
        self.esperando_desbloqueo = False
        self.tiempo_desbloqueo = None
        self.bloqueo_activo = False

        # ── NUEVO: flag que SessionWatcher activa al detectar desbloqueo nativo ──
        self._unlock_nativo_detectado = False

        escribir_log(f"🔒 MÓDULO MONITOREO INICIADO | Umbral: {UMBRAL_CONFIANZA}% | Timeout: {TIEMPO_NO_RECONOCIDO}s")

        # ── NUEVO: arrancar el watcher nativo si pywin32 está disponible ─────────
        if SESSION_WATCHER_DISPONIBLE:
            try:
                self._session_watcher = SessionWatcher()
                self._session_watcher.on_unlock(self._al_desbloquear_nativo)
                self._session_watcher.on_lock(self._al_bloquear_nativo)
                escribir_log("✅ SessionWatcher nativo activo (pywin32)")
            except Exception:
                self._session_watcher = None
                escribir_log("⚠ SessionWatcher: fallo al iniciar, usando solo polling")
        else:
            self._session_watcher = None
            escribir_log("⚠ SessionWatcher: pywin32 no disponible, usando solo polling")
        # ─────────────────────────────────────────────────────────────────────────

        if not self._cargar_recursos():
            self.window.destroy()
            if self.callback_volver:
                self.callback_volver()
            return

        temp_label = tk.Label(window, text="INICIANDO SISTEMA...\nCargando red neuronal", 
                             font=("Consolas", 12, "bold"), fg="#00ff88", bg="#111111")
        temp_label.pack(expand=True)
        window.update()
        time.sleep(1.5)
        temp_label.destroy()

        if not self._iniciar_camara():
            self.window.destroy()
            if self.callback_volver:
                self.callback_volver()
            return

        self._crear_ui()
        self.actualizar_frame()

    def _cargar_recursos(self):
        try:
            modelo_path = os.path.join(BASE_DIR, "modelo_rostro.yml")
            if not os.path.exists(modelo_path):
                escribir_log(" ERROR: No se encuentra modelo_rostro.yml")
                messagebox.showerror("Error", 
                    "No se encuentra 'modelo_rostro.yml'.\n\n"
                    "Ejecute primero el ENTRENAMIENTO desde el menú principal.")
                return False

            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(modelo_path)
            escribir_log(" ✓ Modelo facial cargado")

            prototxt_path = os.path.join(BASE_DIR, "deploy.prototxt")
            model_path = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000_fp16.caffemodel")
            
            if not os.path.exists(prototxt_path) or not os.path.exists(model_path):
                escribir_log(" ERROR: Archivos DNN no encontrados")
                messagebox.showerror("Error", 
                    "Faltan archivos del detector DNN:\n\n"
                    "- deploy.prototxt\n"
                    "- res10_300x300_ssd_iter_140000_fp16.caffemodel")
                return False
            
            self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            escribir_log(" ✓ Red neuronal DNN cargada")
            return True
            
        except Exception as e:
            log_error("cargar_recursos")
            messagebox.showerror("Error", f"Error al cargar recursos:\n{e}")
            return False

    def _iniciar_camara(self):
        try:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                escribir_log(" ERROR: No se pudo abrir la camara")
                messagebox.showerror("Error", "No se pudo acceder a la camara.")
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_VIDEO)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_VIDEO)
            escribir_log(" ✓ Camara iniciada")
            return True
        except Exception as e:
            log_error("iniciar_camara")
            messagebox.showerror("Error", f"Error al iniciar camara:\n{e}")
            return False

    def detectar_rostro_dnn(self, frame):
        if self.net is None:
            return []
            
        (h, w) = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, (300, 300), 
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
                        'x': x, 'y': y, 
                        'w': x2 - x, 'h': y2 - y,
                        'confianza': confianza
                    })
        
        rostros.sort(key=lambda r: r['confianza'], reverse=True)
        return rostros

    def _crear_ui(self):
        self.lbl_video = tk.Label(self.window, bg="black")
        self.lbl_video.pack(pady=(10, 2))

        frame_info = tk.Frame(self.window, bg="#1a1a2e", pady=8)
        frame_info.pack(fill="x", padx=10)

        self.lbl_estado = tk.Label(frame_info, text="ESPERANDO ROSTRO...", 
                                   font=("Consolas", 14, "bold"), fg="#00ff88", bg="#1a1a2e")
        self.lbl_estado.pack(pady=(0, 5))

        self.lbl_contador = tk.Label(frame_info, text="", 
                                     font=("Consolas", 28, "bold"), fg="#ff4444", bg="#1a1a2e")
        self.lbl_contador.pack(pady=(0, 5))

        self.lbl_confianza = tk.Label(frame_info, text="Confianza: ---", 
                                      font=("Consolas", 10), fg="#cccccc", bg="#1a1a2e")
        self.lbl_confianza.pack()

        self.lbl_umbral = tk.Label(frame_info, 
                                   text=f"Umbral: {UMBRAL_CONFIANZA}% | Timeout: {TIEMPO_NO_RECONOCIDO}s", 
                                   font=("Consolas", 7), fg="#888888", bg="#1a1a2e")
        self.lbl_umbral.pack(pady=(5, 0))

        frame_btns = tk.Frame(self.window, bg="#111111", pady=8)
        frame_btns.pack()

        tk.Button(frame_btns, text=" PAUSAR", command=self.pausar, 
                 bg="#f39c12", fg="white", font=("Arial", 9, "bold"), 
                 width=12, relief="flat").pack(side="left", padx=3)

        tk.Button(frame_btns, text=" REANUDAR", command=self.reanudar, 
                 bg="#27ae60", fg="white", font=("Arial", 9, "bold"), 
                 width=12, relief="flat").pack(side="left", padx=3)

        tk.Button(frame_btns, text=" VOLVER AL MENÚ", command=self.volver_menu, 
                 bg="#003580", fg="white", font=("Arial", 9, "bold"), 
                 width=15, relief="flat").pack(side="left", padx=3)

    def volver_menu(self):
        """Vuelve al menú principal"""
        self._cerrar_camara()
        escribir_log(" Volviendo al menú principal")
        self.window.destroy()
        if self.callback_volver:
            self.callback_volver()

    # ── NUEVO: callbacks del SessionWatcher ───────────────────────────────────
    def _al_desbloquear_nativo(self):
        """
        Llamado desde el hilo de SessionWatcher cuando Windows se desbloquea.
        Solo activa el flag; el bucle principal (hilo Tkinter) lo procesa.
        """
        self._unlock_nativo_detectado = True

    def _al_bloquear_nativo(self, *_):
        """Opcional: registra en log cuando Windows se bloquea por evento nativo."""
        pass   # El bloqueo ya lo gestiona bloquear_pc(); aquí solo logueamos si se quiere
    # ─────────────────────────────────────────────────────────────────────────

    def bloquear_pc(self):
        if self.bloqueo_activo:
            escribir_log("[DIAG][bloquear_pc] Llamado pero bloqueo_activo=True, ignorando")
            return
            
        self.bloqueo_activo = True
        escribir_log("🔒 BLOQUEO DEL SISTEMA - Rostro no reconocido")
        
        self.lbl_estado.config(text="¡BLOQUEO ACTIVADO!", fg="#ff0000")
        self.lbl_contador.config(text="🔒", font=("Consolas", 36, "bold"))
        self.lbl_confianza.config(text="Rostro no reconocido - PC bloqueado")
        self.window.update()
        time.sleep(1.5)
        
        self._cerrar_camara()
        
        self.lbl_video.configure(image='', 
                                text="PC BLOQUEADO\n\nCuando desbloquee Windows\nel sistema se reactivará automáticamente", 
                                fg="#ff4444", font=("Consolas", 12, "bold"), bg="#111111")
        
        self.esperando_desbloqueo = True
        self.tiempo_desbloqueo = None
        escribir_log(f"[DIAG][bloquear_pc] esperando_desbloqueo=True | SessionWatcher activo={self._session_watcher is not None}")
        
        try:
            ctypes.windll.user32.LockWorkStation()
            escribir_log("[DIAG][bloquear_pc] LockWorkStation() ejecutado correctamente")
        except Exception as e:
            escribir_log(f"[DIAG][bloquear_pc] ERROR en LockWorkStation(): {e}")
            log_error("bloquear_pc")

    def pausar(self):
        self.en_pausa = True
        self.bloqueo_activo = False
        self._cerrar_camara()
        self.lbl_video.configure(image='', text="SISTEMA PAUSADO\nPresione REANUDAR para continuar", 
                                fg="#f39c12", font=("Consolas", 12, "bold"), bg="#111111")
        self.lbl_estado.config(text="SISTEMA PAUSADO", fg="#f39c12")
        self.lbl_contador.config(text="⏸", font=("Consolas", 28, "bold"))
        self.lbl_confianza.config(text="Confianza: ---")
        escribir_log("⏸ Sistema pausado por usuario")

    def reanudar(self):
        escribir_log("▶ Sistema reanudado")
        self.en_pausa = False
        self.esperando_desbloqueo = False
        self.bloqueo_activo = False
        self.tiempo_sin_reconocer = None
        self.tiempo_desbloqueo = None
        self._unlock_nativo_detectado = False   # ── limpiar flag nativo
        escribir_log("[DIAG][reanudar] Flags reseteados, iniciando cámara...")
        
        if self._iniciar_camara():
            self.lbl_estado.config(text="SISTEMA ACTIVO", fg="#00ff88")
            self.lbl_contador.config(text="")
            self.lbl_confianza.config(text="Confianza: ---")
        else:
            self.lbl_estado.config(text="ERROR DE CÁMARA", fg="#ff0000")
            self.lbl_contador.config(text="⚠")

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

        if self.esperando_desbloqueo:
            # ── DIAGNÓSTICO: estado completo en cada tick mientras espera desbloqueo ──
            flag_nativo  = self._unlock_nativo_detectado
            poll_result  = self._esta_bloqueado()   # True = sigue bloqueado
            desbloqueado = flag_nativo or not poll_result
            self._unlock_nativo_detectado = False

            escribir_log(
                f"[DIAG][esperando_desbloqueo] "
                f"flag_nativo={flag_nativo} | "
                f"_esta_bloqueado()={poll_result} | "
                f"desbloqueado={desbloqueado} | "
                f"tiempo_desbloqueo={'SET' if self.tiempo_desbloqueo else 'NONE'}"
            )
            # ─────────────────────────────────────────────────────────────────────────

            if not desbloqueado:
                escribir_log("[DIAG] → PC sigue bloqueado, reintentando en 2s")
                self.window.after(2000, self.actualizar_frame)
                return
            else:
                if self.tiempo_desbloqueo is None:
                    self.tiempo_desbloqueo = ahora
                    escribir_log(
                        f"[DIAG] → Desbloqueo detectado (vía {'evento nativo' if flag_nativo else 'polling'}). "
                        f"Iniciando cuenta regresiva de {TIEMPO_ESPERA_DESBLOQUEO}s"
                    )
                    self.lbl_estado.config(text=f"DESBLOQUEADO - Reactivando en {TIEMPO_ESPERA_DESBLOQUEO}s...", 
                                          fg="#f39c12")
                
                tiempo_espera     = ahora - self.tiempo_desbloqueo
                segundos_faltantes = max(0, TIEMPO_ESPERA_DESBLOQUEO - int(tiempo_espera))
                escribir_log(f"[DIAG] → Cuenta regresiva: {segundos_faltantes}s restantes")
                
                if segundos_faltantes > 0:
                    self.lbl_contador.config(text=str(segundos_faltantes), 
                                            fg="#f39c12", 
                                            font=("Consolas", 28, "bold"))
                    self.window.after(500, self.actualizar_frame)
                    return
                
                escribir_log("✅ Sistema reactivado después del desbloqueo → llamando reanudar()")
                self.reanudar()
                
        if self.en_pausa and not self.esperando_desbloqueo:
            self.window.after(1000, self.actualizar_frame)
            return

        if self.cap is None or not self.cap.isOpened():
            if not self._iniciar_camara():
                self.lbl_estado.config(text="ERROR DE CÁMARA - Reintentando...", fg="#ff0000")
                self.window.after(1000, self.actualizar_frame)
                return
            self.tiempo_sin_reconocer = None
            self.lbl_contador.config(text="")

        ret, frame = self.cap.read()
        if not ret:
            self.window.after(100, self.actualizar_frame)
            return

        frame = cv2.flip(frame, 1)
        self.frame_actual = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        rostros = self.detectar_rostro_dnn(frame)

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

                    if conf >= UMBRAL_CONFIANZA:
                        rostro_reconocido = True
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, f"OK {conf}%", (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        break
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame, f"NO {conf}%", (x, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                except Exception:
                    continue

        if rostro_reconocido:
            self.tiempo_sin_reconocer = None
            self.bloqueo_activo = False
            self.lbl_estado.config(text="✅ ROSTRO RECONOCIDO", fg="#00ff88")
            self.lbl_contador.config(text="")
            self.lbl_confianza.config(text=f"Confianza: {mejor_confianza}% | Dist: {mejor_distancia:.1f}")
        else:
            if self.tiempo_sin_reconocer is None:
                self.tiempo_sin_reconocer = ahora
            
            tiempo_transcurrido = ahora - self.tiempo_sin_reconocer
            segundos_restantes = max(0, TIEMPO_NO_RECONOCIDO - int(tiempo_transcurrido))
            
            if len(rostros) > 0:
                self.lbl_estado.config(text="⚠ ROSTRO NO RECONOCIDO", fg="#ffaa00")
                self.lbl_confianza.config(text=f"Confianza: {mejor_confianza}% (mín: {UMBRAL_CONFIANZA}%)")
            else:
                self.lbl_estado.config(text="🔍 BUSCANDO ROSTRO...", fg="#ffaa00")
                self.lbl_confianza.config(text="Confianza: ---")
            
            if segundos_restantes > 0:
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
                self.lbl_contador.config(text="¡BLOQUEO!", fg="#ff0000", 
                                        font=("Consolas", 36, "bold"))
                self.window.update()
                self.bloquear_pc()
                # CORRECCIÓN: programar el siguiente tick para que el bucle
                # siga corriendo y pueda detectar cuando se desbloquea Windows
                escribir_log("[DIAG] Bucle reiniciado tras bloquear_pc(), esperando desbloqueo...")
                self.window.after(2000, self.actualizar_frame)
                return

        cv2.putText(frame, f"DNN | Umbral: {UMBRAL_CONFIANZA}%", 
                   (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

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
                escribir_log("[DIAG][_esta_bloqueado] OpenInputDesktop devolvió 0 → bloqueado=True")
                return True
            name = ctypes.create_unicode_buffer(256)
            needed = ctypes.c_uint(0)
            if user32.GetUserObjectInformationW(hdesk, 2, name, 512, ctypes.byref(needed)):
                user32.CloseDesktop(hdesk)
                bloqueado = name.value != "Default"
                escribir_log(f"[DIAG][_esta_bloqueado] Desktop='{name.value}' → bloqueado={bloqueado}")
                return bloqueado
            user32.CloseDesktop(hdesk)
            escribir_log("[DIAG][_esta_bloqueado] GetUserObjectInformationW falló → bloqueado=False")
            return False
        except Exception as e:
            escribir_log(f"[DIAG][_esta_bloqueado] EXCEPCIÓN: {e} → bloqueado=True")
            return True


# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO DE ENTRENAMIENTO FACIAL
# ═══════════════════════════════════════════════════════════════════════════

class Registrador:
    def __init__(self, window, callback_volver=None):
        self.window = window
        self.callback_volver = callback_volver
        self.window.title("Entrenamiento de Rostro - Security Core DNN")
        self.window.configure(bg="#111111")
        self.window.minsize(550, 600)

        self.net = cv2.dnn.readNetFromCaffe(
            "deploy.prototxt",
            "res10_300x300_ssd_iter_140000_fp16.caffemodel"
        )
        self.confianza_minima = 0.5
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._cargar_modelo_existente()
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.muestras = []
        self.frame_actual = None
        
        MIN_FOTOS_RECOMENDADAS = 15
        CANTIDAD_SUGERENCIAS = 25

        # UI
        tk.Label(window, text="ENTRENAMIENTO DE ROSTRO", 
                font=("Consolas", 16, "bold"), fg="#00ff88", bg="#111111").pack(pady=(10, 5))

        self.lbl_video = tk.Label(window, bg="black")
        self.lbl_video.pack(pady=5)

        frame_info = tk.Frame(window, bg="#1a1a2e", pady=5)
        frame_info.pack(fill="x", padx=10)

        self.lbl_progreso = tk.Label(
            frame_info, 
            text=f"Fotos capturadas: 0 (Mínimo recomendado: 15)",
            font=("Consolas", 10, "bold"), fg="#ffaa00", bg="#1a1a2e"
        )
        self.lbl_progreso.pack(pady=2)

        self.lbl_calidad = tk.Label(
            frame_info,
            text="Calidad: ---",
            font=("Consolas", 9), fg="#888888", bg="#1a1a2e"
        )
        self.lbl_calidad.pack()

        self.lbl_instrucciones = tk.Label(
            window,
            text="📸 Presione CAPTURAR para cada pose\nPuede tomar CUANTAS fotos desee para mejorar precisión",
            font=("Arial", 11, "bold"), fg="#00aaff", bg="#111111", justify="center"
        )
        self.lbl_instrucciones.pack(pady=8)

        self.lbl_sugerencia = tk.Label(
            window,
            text="Sugerencia: Frente neutral",
            font=("Consolas", 11), fg="#f39c12", bg="#111111"
        )
        self.lbl_sugerencia.pack(pady=2)

        frame_btns = tk.Frame(window, bg="#111111")
        frame_btns.pack(pady=8)

        self.btn_capturar = tk.Button(
            frame_btns, text="📸  CAPTURAR",
            command=self.capturar_manual,
            bg="#1a7a1a", fg="white",
            font=("Arial", 13, "bold"),
            width=16, height=2,
            relief="flat", cursor="hand2"
        )
        self.btn_capturar.pack(side="left", padx=5)

        self.btn_deshacer = tk.Button(
            frame_btns, text="↩ Deshacer",
            command=self.deshacer_ultima,
            bg="#8B0000", fg="white",
            font=("Arial", 10),
            width=10, relief="flat", cursor="hand2"
        )
        self.btn_deshacer.pack(side="left", padx=5)

        frame_btns2 = tk.Frame(window, bg="#111111")
        frame_btns2.pack(pady=5)

        self.btn_guardar = tk.Button(
            frame_btns2, text="💾  Guardar Modelo",
            command=self.finalizar_entrenamiento,
            bg="#003580", fg="white",
            font=("Arial", 11, "bold"),
            width=16, relief="flat", cursor="hand2", state="disabled"
        )
        self.btn_guardar.pack(side="left", padx=5)

        self.btn_auto = tk.Button(
            frame_btns2, text="⚡ Auto-Captura (5)",
            command=self.auto_captura,
            bg="#6c3483", fg="white",
            font=("Arial", 10),
            width=14, relief="flat", cursor="hand2"
        )
        self.btn_auto.pack(side="left", padx=5)

        tk.Button(
            window, text="↩ VOLVER AL MENÚ", command=self.volver_menu,
            bg="#c0392b", fg="white",
            font=("Arial", 9, "bold"),
            width=18, relief="flat", cursor="hand2"
        ).pack(pady=8)

        tk.Label(window, 
                text="💡 Tome fotos en diferentes ángulos, distancias e iluminaciones\n"
                     "Cuantas más muestras, mejor será el reconocimiento",
                font=("Arial", 8), fg="#666666", bg="#111111", justify="center"
        ).pack(pady=5)

        self.sugerencias = [
            "Frente neutral mirando a cámara",
            "Sonría ligeramente",
            "Sonría ampliamente",
            "Gire cabeza 15° a la derecha",
            "Gire cabeza 30° a la derecha (perfil parcial)",
            "Gire cabeza 15° a la izquierda",
            "Gire cabeza 30° a la izquierda (perfil parcial)",
            "Incline cabeza hacia arriba",
            "Incline cabeza hacia abajo",
            "Incline cabeza a la derecha",
            "Incline cabeza a la izquierda",
            "Acerque el rostro (30cm)",
            "Aléjese de la cámara (brazo extendido)",
            "Con lentes (si usa)",
            "Sin lentes (si usa)",
            "Con gorro o sombrero",
            "Expresión seria",
            "Ceja levantada",
            "Ojos cerrados suavemente",
            "Mire hacia la esquina superior derecha",
            "Mire hacia la esquina superior izquierda",
            "Mire hacia abajo a la derecha",
            "Mire hacia abajo a la izquierda",
            "Media sonrisa lateral",
            "Cualquier expresión natural"
        ]

        self.actualizar_video()

    def _cargar_modelo_existente(self):
        if os.path.exists("modelo_rostro.yml"):
            try:
                self.recognizer.read("modelo_rostro.yml")
                respuesta = messagebox.askyesno(
                    "Modelo Existente",
                    "Se encontró 'modelo_rostro.yml'.\n\n"
                    "¿Desea CONTINUAR el entrenamiento\n"
                    "añadiendo más fotos a este modelo?\n\n"
                    "• 'Sí': Sus nuevas fotos se sumarán al modelo existente\n"
                    "• 'No': Empezará desde cero"
                )
                if not respuesta:
                    self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            except Exception:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()

    def volver_menu(self):
        """Vuelve al menú principal"""
        self.on_closing()
        self.window.destroy()
        if self.callback_volver:
            self.callback_volver()

    def detectar_rostro_dnn(self, frame):
        if self.net is None:
            return []
            
        (h, w) = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        self.net.setInput(blob)
        detecciones = self.net.forward()
        
        rostros = []
        for i in range(detecciones.shape[2]):
            confianza = detecciones[0, 0, i, 2]
            
            if confianza > self.confianza_minima:
                box = detecciones[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x2, y2) = box.astype("int")
                
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                if x2 > x and y2 > y:
                    rostros.append({
                        'x': x, 'y': y, 
                        'w': x2 - x, 'h': y2 - y,
                        'confianza': confianza
                    })
        
        rostros.sort(key=lambda r: r['confianza'], reverse=True)
        return rostros

    def actualizar_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            self.frame_actual = frame.copy()

            rostros = self.detectar_rostro_dnn(frame)
            
            for rostro in rostros:
                x, y, w, h = rostro['x'], rostro['y'], rostro['w'], rostro['h']
                conf = rostro['confianza']
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"DNN: {conf:.0%}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                centro_x = x + w//2
                centro_y = y + h//2
                cv2.circle(frame, (centro_x, centro_y), 3, (255, 0, 0), -1)

            n = len(self.muestras)
            cv2.putText(frame, f"Muestras: {n}", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = img.resize((500, 375), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)

        self.window.after(15, self.actualizar_video)

    def _actualizar_sugerencia(self):
        n = len(self.muestras)
        if n < len(self.sugerencias):
            self.lbl_sugerencia.config(text=f"Sugerencia: {self.sugerencias[n]}")
        else:
            idx = n % len(self.sugerencias)
            self.lbl_sugerencia.config(text=f"Sugerencia: {self.sugerencias[idx]}")

    def capturar_manual(self):
        if self.frame_actual is None:
            return

        gray = cv2.cvtColor(self.frame_actual, cv2.COLOR_BGR2GRAY)
        rostros = self.detectar_rostro_dnn(self.frame_actual)

        if len(rostros) == 0:
            self.lbl_instrucciones.config(
                text="⚠ No se detectó rostro. Reubíquese.",
                fg="red"
            )
            return

        mejor_rostro = rostros[0]
        x, y, w, h = mejor_rostro['x'], mejor_rostro['y'], mejor_rostro['w'], mejor_rostro['h']
        conf = mejor_rostro['confianza']
        
        rostro = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
        self.muestras.append(rostro)

        n = len(self.muestras)
        MIN_FOTOS = 15
        
        if n >= MIN_FOTOS:
            self.lbl_progreso.config(
                text=f"✅ Fotos capturadas: {n} (Mínimo: {MIN_FOTOS}) ¡Excelente!",
                fg="#00ff88"
            )
            self.btn_guardar.config(state="normal", bg="#00aa55")
        else:
            self.lbl_progreso.config(
                text=f"Fotos capturadas: {n} / {MIN_FOTOS} mínimo",
                fg="#ffaa00"
            )
            if n >= 5:
                self.btn_guardar.config(state="normal")
        
        self.lbl_calidad.config(
            text=f"Calidad detección: {conf:.0%} | Tamaño rostro: {w}x{h}px"
        )
        self.lbl_instrucciones.config(
            text=f"✅ Foto {n} guardada. ¡Siga capturando!",
            fg="green"
        )
        
        self._actualizar_sugerencia()

    def auto_captura(self):
        self.btn_auto.config(state="disabled", text="Capturando...")
        self.lbl_instrucciones.config(
            text="⚡ Auto-captura en progreso... Cambie de pose lentamente",
            fg="#9b59b6"
        )
        
        def capturar_automaticamente(contador=5):
            if contador > 0 and self.window.winfo_exists():
                self.capturar_manual()
                self.window.update()
                self.window.after(1500, lambda: capturar_automaticamente(contador - 1))
            else:
                self.btn_auto.config(state="normal", text="⚡ Auto-Captura (5)")
                self.lbl_instrucciones.config(
                    text=f"✅ Auto-captura completada. Total: {len(self.muestras)} fotos",
                    fg="green"
                )
        
        capturar_automaticamente()

    def deshacer_ultima(self):
        if self.muestras:
            self.muestras.pop()
            n = len(self.muestras)
            self.lbl_progreso.config(
                text=f"Fotos capturadas: {n} (última eliminada)",
                fg="#ffaa00"
            )
            self.lbl_instrucciones.config(
                text=f"↩ Última foto eliminada. Total: {n}.",
                fg="orange"
            )
            self._actualizar_sugerencia()
            
            if n < 5:
                self.btn_guardar.config(state="disabled", bg="#003580")
        else:
            self.lbl_instrucciones.config(text="No hay fotos que deshacer.", fg="gray")

    def finalizar_entrenamiento(self):
        if len(self.muestras) < 5:
            messagebox.showwarning("Pocas muestras", 
                                  "Necesita al menos 5 fotos para entrenar.\n\n"
                                  f"Actualmente tiene: {len(self.muestras)}")
            return

        if len(self.muestras) < 15:
            continuar = messagebox.askyesno(
                "Pocas muestras",
                f"Solo tiene {len(self.muestras)} fotos.\n"
                "Se recomiendan al menos 15.\n\n"
                "¿Desea guardar de todos modos?"
            )
            if not continuar:
                return

        self.lbl_instrucciones.config(text="🔄 Entrenando modelo...", fg="blue")
        self.btn_guardar.config(state="disabled", text="Entrenando...")
        self.window.update()

        try:
            etiquetas = np.array([1] * len(self.muestras))
            self.recognizer.train(self.muestras, etiquetas)
            self.recognizer.write("modelo_rostro.yml")
            
            messagebox.showinfo(
                "✅ Modelo Guardado",
                f"Entrenamiento completado exitosamente:\n\n"
                f"📸 Fotos utilizadas: {len(self.muestras)}\n"
                f"📁 Archivo: modelo_rostro.yml\n\n"
                f"💡 Consejo: Si el reconocimiento no es preciso,\n"
                f"   ejecute el entrenamiento de nuevo y añada\n"
                f"   más fotos en ángulos diferentes."
            )
            self.volver_menu()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al entrenar el modelo:\n{e}")
            self.btn_guardar.config(state="normal", text="💾  Guardar Modelo")

    def on_closing(self):
        if self.cap.isOpened():
            self.cap.release()


# ═══════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def manejar_excepcion_global(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log_error("GLOBAL", (exc_type, exc_value, exc_traceback))


if __name__ == "__main__":
    sys.excepthook = manejar_excepcion_global
    
    print("=" * 60)
    print("  SECURITY CORE DNN - v2.0")
    print("  Sistema de Bloqueo Facial Inteligente")
    print("  Desarrollado por Ing. Elíasib Cadena M.")
    print("=" * 60)
    
    escribir_log("🚀 Security Core DNN v2.0 INICIADO")
    
    # Iniciar el menú principal
    MenuPrincipal()