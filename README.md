# 🔒 Security Core DNN - Bloqueo Facial Inteligente
# BLOQUEAR SESION WINDOWS POR ROSTRO IA
Este proyecto lo he creado con el proposito de bloquear mi sesion del pc en caso de levantarme del puesto y no depender de el bloqueo temporal de windows ya que
muchas veces como desarrolladores tenemos que leer la pantalla y estamos en el pc , pero Windows bloquea el pc sin tener en cuenta que lo estamos usando o si 
nos levantamos deprisa y se nos olvida bloquear el pc y dejamos a largo plazo el bloqueo cualquiera puede usarlo, esta herramienta permite por iteneligencia artificial
identificar si eres tu ya que tiene un espacio para entrenarla cuando eres tu y ademas tambie identifica si no estas en el puesto cuando sabe que no eres tu o que no 
estas en el puesto en ese  momento bloquea la sesion de Windows, este programa no tiene salida a lared ni Wifi ni Ethernet no la requiere para su uso la ia es OFFLINE
no tiene datos tuyos previos debes entrenarla en el momento de usarla aconsejo tomar minimo 30 fotos , la IA no envia tus datos a ningun lugar solo los guarda en la 
carpeta donde esta isntalado y los puedes borrar en cualquier momento el archivo cuando esta entrenado se llama modelo_rostro.yml lo puedes borrar pero ya no reconocera
tu rostro en esta version es necesario remplazar el exe cuando el programa ya esta isntalado por el que subi hoy 15 Mayo 2026 en la carpeta c porque no reconoce archivos
apesar de que si los crea modelo_rostro.yml pero no los encuentra y es que no contemple que debia leer archivos externos cuando lo comprimi.
si quieres crear tu propio exe el codigo esta en ejecutable.py puedes ajustar el humbral el tiempo de espera actual 30 s etc puedes modificar el codigo a tu antojo.
lo usare y estare lanzado mejoras según vea como me funciona 
**Sistema pasivo de bloqueo de PC basado en reconocimiento facial con Deep Learning**

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-DNN-green?logo=opencv)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Estable-success)

---

## 📖 Tabla de Contenidos

- [¿Por qué Security Core?](#-por-qué-security-core)
- [Características](#-características)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Configuración](#-configuración)
- [Arquitectura Técnica](#-arquitectura-técnica)
- [Solución de Problemas](#-solución-de-problemas)
- [Créditos](#-créditos)
- [Licencia](#-licencia)

---

## 🤔 ¿Por qué Security Core?

### El problema con el bloqueo tradicional de Windows

Windows bloquea la pantalla después de un tiempo de **inactividad del teclado/mouse**. Esto presenta problemas:

- ❌ Estás **leyendo un documento** largo → PC se bloquea
- ❌ Estás **corrigiendo código** visualmente → PC se bloquea
- ❌ Estás **pensando** frente a la pantalla → PC se bloquea
- ❌ Te levantas 5 segundos a buscar algo → PC **NO** se bloquea (el tiempo no se cumplió)

### La solución: Security Core DNN

Security Core es un sistema **pasivo y no invasivo** que:

- ✅ **Detecta si TÚ estás frente a la PC** usando reconocimiento facial con Deep Learning
- ✅ **NO se bloquea mientras estás presente**, sin importar si usas teclado/mouse o no
- ✅ **Bloquea INSTANTÁNEAMENTE** si detecta un rostro desconocido (otra persona)
- ✅ **Bloquea después de X segundos** si no hay nadie frente a la cámara (te levantaste)
- ✅ **Reconoce múltiples ángulos**: perfil, inclinado, cerca, lejos
- ✅ **Protege información sensible** contra accesos no autorizados
┌─────────────────────────────────────────────────────────┐
│ SECURITY CORE DNN │
│ │
│ 👤 Tú frente a la PC → ✅ No bloquea │
│ 🚶 Tú te levantas → ⏱ Cuenta regresiva │
│ 👤 Otra persona se sienta → 🔒 Bloqueo inmediato │
│ 🔓 Windows desbloqueado → 🔍 Verifica de nuevo │
│ │
└─────────────────────────────────────────────────────────┘

text

---

## ✨ Características

### 🎯 Reconocimiento Facial Avanzado
- **DNN (Deep Neural Network)** para detección multi-ángulo
- **LBPH (Local Binary Patterns Histograms)** para reconocimiento
- Reconocimiento de perfil, inclinaciones y diferentes distancias
- Umbral de confianza configurable

### 🔒 Seguridad
- Bloqueo automático de Windows al detectar rostro desconocido
- Contador regresivo configurable (10-30 segundos)
- Sin ventanas emergentes molestas
- Modo hibernación cuando Windows está bloqueado
- Rearmado automático al desbloquear

### 🎨 Interfaz
- Visualización en tiempo real de detección
- Barra de progreso y calidad de captura
- Sugerencias de poses para mejor entrenamiento
- Contador regresivo con efectos visuales

### ⚙️ Flexibilidad
- Umbral de confianza ajustable (50-95%)
- Tiempo de espera configurable
- Captura ilimitada de muestras para entrenamiento
- Modo auto-captura para entrenamiento rápido
- Carga incremental de modelos existentes

---

## 🔧 Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| **Python 3.8+** | Lenguaje principal |
| **OpenCV 4.x** | Procesamiento de imágenes y DNN |
| **Caffe DNN Model** | Detección facial multi-ángulo (SSD) |
| **LBPH Face Recognizer** | Reconocimiento biométrico |
| **Tkinter + PIL** | Interfaz gráfica |
| **NumPy** | Operaciones matriciales |
| **ctypes** | Llamadas a API de Windows |

### Modelos de Deep Learning utilizados
deploy.prototxt ← Arquitectura SSD
res10_300x300_ssd_iter_140000_fp16.caffemodel ← Pesos pre-entrenados

text

- **Entrenado con:** 10,000+ imágenes de rostros
- **Precisión:** 97%+ en detección frontal y perfil
- **Entrada:** 300×300 píxeles
- **Salida:** Coordenadas + confianza por detección

---

## 📁 Estructura del Proyecto
face_lock/
│
├── entrenador_rostro.py # Programa de entrenamiento (captura de muestras)
├── monitor_facial.py # Programa principal de monitoreo y bloqueo
│
├── deploy.prototxt # Arquitectura de la red neuronal (DNN)
├── res10_300x300_ssd_iter_140000_fp16.caffemodel # Pesos del modelo DNN
├── modelo_rostro.yml # Modelo entrenado con tu rostro (se genera)
│
├── logs_security_core.txt # Registro de eventos del sistema
├── fallidos/ # Carpeta con fotos de intentos fallidos (opcional)
│
└── README.md # Este archivo

text

### Diagrama de flujo del sistema

```mermaid
graph TD
    A[Inicio] --> B[Cargar modelo DNN + LBPH]
    B --> C[Iniciar cámara]
    C --> D[Loop principal]
    D --> E{Capturar frame}
    E --> F[Detección DNN]
    F --> G{¿Rostro detectado?}
    G -->|Sí| H[Reconocimiento LBPH]
    G -->|No| I[Iniciar/Continuar contador]
    H --> J{¿Confianza ≥ Umbral?}
    J -->|Sí| K[Resetear contador ✓]
    J -->|No| I
    I --> L{¿Tiempo agotado?}
    L -->|Sí| M[Bloquear Windows 🔒]
    L -->|No| D
    K --> D
    M --> N[Esperar desbloqueo]
    N --> O{¿Windows desbloqueado?}
    O -->|Sí| P[Esperar 2s + Reactivar]
    O -->|No| N
    P --> D
💻 Requisitos del Sistema
Hardware
Cámara web funcional (integrada o USB)

Procesador: Intel Core i3 o superior (recomendado i5 para DNN)

RAM: 4 GB mínimo (8 GB recomendado)

Espacio: ~100 MB para el proyecto

Software
Windows 10/11 (64-bit)

Python 3.8 - 3.13 (versión estable)

Pip actualizado

📥 Instalación
1. Clonar o descargar el proyecto
bash
git clone https://github.com/tuusuario/security-core-dnn.git
cd security-core-dnn
O descarga el ZIP y extráelo en una carpeta.

2. Instalar Python
Descarga e instala Python desde python.org

IMPORTANTE: Marca ✅ "Add Python to PATH"

Usa una versión estable (3.11, 3.12 o 3.13)

3. Instalar dependencias
bash
pip install opencv-python opencv-contrib-python numpy pillow tk
4. Verificar archivos del modelo DNN
Asegúrate de tener estos archivos en la carpeta del proyecto:

deploy.prototxt

res10_300x300_ssd_iter_140000_fp16.caffemodel

Si no los tienes, descárgalos:

bash
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt" -OutFile "deploy.prototxt"
Invoke-WebRequest -Uri "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20180205_uint8/res10_300x300_ssd_iter_140000_fp16.caffemodel" -OutFile "res10_300x300_ssd_iter_140000_fp16.caffemodel"
🚀 Uso
Paso 1: Entrenar tu rostro
Ejecuta el programa de entrenamiento:

bash
python entrenador_rostro.py
Siéntate frente a la cámara

Presiona CAPTURAR en diferentes poses:

Frente, perfil derecho, perfil izquierdo

Arriba, abajo, inclinado

Cerca, lejos, con/sin lentes

Toma mínimo 15 fotos (recomendado 25-30)

Presiona GUARDAR MODELO

💡 Consejo: Usa el botón AUTO-CAPTURA para tomar 5 fotos automáticas mientras giras lentamente la cabeza.

Paso 2: Iniciar el monitor
bash
python monitor_facial.py
El sistema:

Muestra "✅ ROSTRO RECONOCIDO" cuando estás frente a la cámara

Inicia contador regresivo si no detecta tu rostro

Bloquea Windows al llegar a 0 o detectar rostro desconocido

Paso 3 (Opcional): Ejecutar al iniciar Windows
Crea un acceso directo y cópialo en:

text
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
⚙️ Configuración
Edita las variables al inicio de monitor_facial.py:

python
# ═══════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL - AJUSTABLE
# ═══════════════════════════════════════════════

UMBRAL_CONFIANZA = 65          # % mínimo para reconocerte (50-90)
TIEMPO_NO_RECONOCIDO = 20      # Segundos antes de bloquear (10-60)
TIEMPO_ESPERA_DESBLOQUEO = 2   # Segundos de espera tras desbloquear
Recomendaciones de umbral
Umbral	Comportamiento
50-60%	Más permisivo, acepta más variaciones
65-75%	Balance recomendado ⭐
80-90%	Más estricto, necesita coincidencia muy cercana
🏗️ Arquitectura Técnica
Sistema de Detección (DNN)
text
Entrada: Frame de cámara (640×480)
    ↓
Preprocesamiento: Redimensionar a 300×300 + Normalización
    ↓
Red Neuronal: SSD (Single Shot Detector) con base Caffe
    ↓
Salida: Coordenadas (x,y,w,h) + Confianza (0-1)
    ↓
Filtro: Solo detecciones > 50% confianza
Sistema de Reconocimiento (LBPH)
text
Entrada: Región del rostro detectado
    ↓
Preprocesamiento: Escala de grises + Redimensionar 200×200
    ↓
LBPH: Comparación de patrones binarios locales
    ↓
Salida: ID de persona + Distancia (menor = más similar)
    ↓
Conversión: Distancia → Confianza (0-100%)
    ↓
Decisión: ¿Confianza ≥ UMBRAL_CONFIANZA?
Fórmula de conversión Distancia → Confianza
text
confianza = max(0, (1 - distancia / DISTANCIA_MAX) × 100)

Donde:
  DISTANCIA_MAX = 120 (umbral de distancia del modelo LBPH)
  distancia = valor devuelto por el reconocedor
Máquina de Estados del Sistema
text
[ACTIVO] ←→ [PAUSADO]
   ↓
[BLOQUEO]
   ↓
[ESPERANDO_DESBLOQUEO]
   ↓
[REACTIVANDO] → [ACTIVO]
🔍 Solución de Problemas
La cámara no enciende
bash
# Verificar que la cámara está disponible
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
Cierre otras apps que usen la cámara (Zoom, Teams, navegador)

Revise permisos de cámara en Configuración de Windows

Error "No module named 'PIL'"
bash
pip install pillow
Error "No module named 'cv2'"
bash
pip install opencv-python opencv-contrib-python
Error con archivos DNN
Verifique que deploy.prototxt y res10_300x300_ssd_iter_140000_fp16.caffemodel estén en la misma carpeta que los scripts

No cambie los nombres de estos archivos

Falsos positivos (no te reconoce)
Aumente las muestras de entrenamiento (25+ fotos)

Baje el umbral a 55-60%

Asegúrese de tener fotos en diferentes ángulos e iluminaciones

Falsos negativos (reconoce a otros como tú)
Suba el umbral a 75-80%

Vuelva a entrenar desde cero

👨‍💻 Créditos
Desarrollador
Ing. Elíasib Cadena M.

Ingeniero de Software

Especialista en Visión Artificial y Machine Learning

GitHub | LinkedIn

Agradecimientos
OpenCV team por las herramientas de visión artificial

Comunidad de Python por las librerías utilizadas

Intel por los modelos pre-entrenados de Caffe

📄 Licencia
MIT License

Copyright (c) 2024 Ing. Elíasib Cadena M.

Se concede permiso por la presente, de forma gratuita, a cualquier persona que obtenga una copia de este software y los archivos de documentación asociados, para tratar con el Software sin restricciones, incluidos, entre otros, los derechos de uso, copia, modificación, fusión, publicación, distribución, sublicencia y/o venta de copias del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO.

📊 Estadísticas del Proyecto
text
Líneas de código:     ~1,200
Módulos:              2 principales (entrenador + monitor)
Dependencias:         5 librerías
Modelos ML:           2 (DNN + LBPH)
Tiempo de respuesta:  ~30ms por frame
Precisión detección:  97%+
🎯 Roadmap
Soporte para múltiples usuarios

Notificaciones por Telegram/WhatsApp

Registro de accesos con fotos

Interfaz web de monitoreo remoto

Empaquetado como .exe portable

Soporte para Linux/macOS
crear exe
python -m PyInstaller --onefile --windowed --name="IAFaceLock" --icon=icon.ico ejecutable.py

<p align="center"> <b>Security Core DNN</b><br> <i>Protegiendo tu información, respetando tu tiempo</i><br><br> <sub>© 2024 Ing. Elíasib Cadena M. - Todos los derechos reservados</sub> </p> ```
