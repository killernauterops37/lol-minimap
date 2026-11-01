# LoL Minimap

Aplicación de escritorio para Windows que muestra un área de pantalla ampliada en un segundo monitor. El punto de partida del repositorio se conserva en la etiqueta `v-0`.

## Iniciar

Necesitas Python 3.11 o posterior. Haz doble clic en `iniciar.bat`: la primera vez prepara un entorno local e instala las dependencias de `requirements.txt`.

1. Abre una partida de práctica y usa el modo ventana sin bordes.
2. Pulsa **Seleccionar área del minimapa** y arrastra alrededor del minimapa. Esc cancela. El recorte debe quedar dentro de un solo monitor.
3. Elige el segundo monitor y pulsa **Abrir vista ampliada**.
4. En esa ventana, F11 alterna pantalla completa, Espacio pausa y Esc sale de pantalla completa. Clic derecho cierra la vista.

La imagen conserva sus proporciones y el área seleccionada se guarda localmente. Para cambiarla, vuelve a seleccionar el área. Con un solo monitor puedes probar la vista, pero debes moverla fuera del recorte para evitar un efecto espejo.

## Alcance de esta primera versión

- Selección manual de un área y captura visual a un objetivo aproximado de 30 FPS, según el rendimiento del equipo.
- Selección del monitor de destino, ventana ajustable y pantalla completa.
- No incluye interacción con el minimapa: los clics y señales se realizan en el juego.
- No accede a la memoria ni modifica archivos de League of Legends. No es un producto de Riot ni cuenta con certificación de compatibilidad de Riot/Vanguard.
- Ampliar la imagen no añade detalle. Pantalla completa exclusiva o contenido protegido pueden producir capturas negras; prueba ventana sin bordes.
- Si cambias la distribución o resolución de las pantallas, reinicia la aplicación y selecciona el área de nuevo.

## Desarrollo

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Tecnologías: Python y Qt (PySide6 Essentials). El desarrollo local posterior a `v-0` todavía no constituye una versión publicada.
