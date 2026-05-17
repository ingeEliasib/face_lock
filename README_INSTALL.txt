╔══════════════════════════════════════════════════════════════════════════════╗
║                    SECURITY CORE DNN - v2.0                                ║
║                 Sistema de Bloqueo Facial Inteligente                      ║
║                   Desarrollado por Ing. Elíasib Cadena M.                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

              INFORMACIÓN IMPORTANTE ANTES DE INSTALAR
              =========================================

-------------------------------------------------------------------------------
REQUISITOS DEL SISTEMA
-------------------------------------------------------------------------------

  • Sistema Operativo: Windows 10 o Windows 11 (64-bit)
  • Cámara web funcional (integrada o USB)
  • Procesador: Intel Core i3 o superior (recomendado i5)
  • Memoria RAM: 4 GB mínimo (8 GB recomendado)
  • Espacio en disco: 500 MB disponibles
  • Resolución de cámara: 640x480 o superior

-------------------------------------------------------------------------------
ANTES DE USAR EL SOFTWARE
-------------------------------------------------------------------------------

  1. Asegúrese de que su cámara web esté conectada y funcionando
  2. Cierre otras aplicaciones que puedan usar la cámara (Zoom, Teams, Skype)
  3. Ajuste la iluminación de su espacio de trabajo
  4. Siéntese en la posición habitual donde usa su computadora

-------------------------------------------------------------------------------
CONFIGURACIÓN INICIAL
-------------------------------------------------------------------------------

  ⚠ IMPORTANTE: Antes de usar el modo de monitoreo, DEBE realizar el 
  entrenamiento facial. Este proceso toma aproximadamente 3-5 minutos.

  PASO 1: Abra Security Core DNN
  PASO 2: Seleccione "ENTRENAR ROSTRO"
  PASO 3: Capture al menos 15 fotos de su rostro en diferentes ángulos:
          - Frente, perfil derecho, perfil izquierdo
          - Arriba, abajo, inclinado
          - Cerca, lejos de la cámara
          - Con y sin lentes (si aplica)
  PASO 4: Guarde el modelo facial
  PASO 5: Reinicie la aplicación y seleccione "INICIAR MONITOREO"

-------------------------------------------------------------------------------
ARCHIVOS NECESARIOS
-------------------------------------------------------------------------------

  El instalador incluye los siguientes archivos:

  • SecurityCore.exe          - Aplicación principal
  • deploy.prototxt           - Arquitectura de red neuronal DNN
  • *.caffemodel              - Pesos del modelo de detección facial

  Archivos que se generarán durante el uso:

  • modelo_rostro.yml         - Su modelo facial entrenado (se crea al entrenar)
  • logs_security_core.txt    - Registro de eventos del sistema

-------------------------------------------------------------------------------
FUNCIONAMIENTO
-------------------------------------------------------------------------------

  ¿Cómo funciona el sistema?

  • MONITOREO: El sistema usa la cámara para detectar si USTED está frente
    a la computadora. Si otra persona se sienta o usted se aleja por más
    del tiempo configurado, el PC se bloquea automáticamente.

  • ENTRENAMIENTO: Captura muestras de su rostro en diferentes posiciones
    para crear un modelo biométrico único. Más muestras = mejor precisión.

  • NO ES INVASIVO: No transmite datos, no graba video, no almacena imágenes
    en la nube. Todo el procesamiento es LOCAL en su computadora.

-------------------------------------------------------------------------------
SOLUCIÓN DE PROBLEMAS COMUNES
-------------------------------------------------------------------------------

  PROBLEMA: La cámara no funciona
  SOLUCIÓN: Verifique que ninguna otra app esté usando la cámara.
            Revise los permisos de cámara en Configuración de Windows.

  PROBLEMA: No reconoce mi rostro
  SOLUCIÓN: Realice el entrenamiento nuevamente con más fotos (25+).
            Ajuste el umbral de confianza en la configuración del código.

  PROBLEMA: El PC se bloquea muy rápido
  SOLUCIÓN: Aumente la variable TIEMPO_NO_RECONOCIDO en el código fuente.

  PROBLEMA: Bloquea con alguien similar a mí
  SOLUCIÓN: Aumente UMBRAL_CONFIANZA a 75-80% en el código fuente.

-------------------------------------------------------------------------------
AVISO DE PRIVACIDAD
-------------------------------------------------------------------------------

  • Las imágenes capturadas durante el entrenamiento se almacenan SOLO en
    su equipo local.

  • El modelo facial generado (modelo_rostro.yml) contiene datos biométricos
    codificados. No los comparta.

  • Las fotos de intentos fallidos se guardan en la carpeta "fallidos/" y
    se eliminan automáticamente después de 5 capturas.

  • Este software NO requiere conexión a internet.
  • Este software NO transmite datos a servidores externos.
  • Este software NO contiene publicidad ni telemetría.

-------------------------------------------------------------------------------
CONTACTO Y SOPORTE
-------------------------------------------------------------------------------

  Desarrollador: Ing. Elíasib Cadena M.
  
  Para reportar errores, sugerencias o solicitar características:
  • Repositorio: https://github.com/tuusuario/security-core-dnn

-------------------------------------------------------------------------------
VERSIÓN
-------------------------------------------------------------------------------

  Security Core DNN v2.0
  Fecha de publicación: 2024

  Tecnologías utilizadas:
  • Python, OpenCV, Caffe DNN, LBPH Face Recognizer
  • Detección facial: Red Neuronal SSD (97%+ precisión)
  • Reconocimiento: Patrones Binarios Locales (LBPH)

-------------------------------------------------------------------------------

          Al hacer clic en "Siguiente", usted acepta los términos
          de la licencia y confirma haber leído esta información.

===============================================================================