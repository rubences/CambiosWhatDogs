from pathlib import Path
from tkinter import ttk
import datetime
import queue
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED
)
class MyEventHandler(FileSystemEventHandler):
    def __init__(self, q):
        # Guardar referencia a la cola para poder utilizarla
        # en on_any_event().
        self._q = q
        super().__init__()
    
    def on_any_event(self, event):
        # Determinar el nombre de la operación.
        action = {
            EVENT_TYPE_CREATED: "Creado",
            EVENT_TYPE_DELETED: "Eliminado",
            EVENT_TYPE_MODIFIED: "Modificado",
            EVENT_TYPE_MOVED: "Movido",
        }[event.event_type]
        # Si es un movimiento, agregar la ruta de destino.
        if event.event_type == EVENT_TYPE_MOVED:
            action += f" ({event.dest_path})"
        # Agregar la información del evento a la cola, para que sea
        # procesada por loop_observer() en el hilo principal.
        # (No es conveniente modificar un control de Tk desde
        # un hilo secundario).
        self._q.put((
            # Nombre del archivo modificado.
            Path(event.src_path).name,
            # Acción ejecutada sobre ese archivo.
            action,
            # Hora en que se ejecuta la acción.
            datetime.datetime.now().strftime("%H:%M:%S")
        ))
def process_events(observer, q, modtree):
    # Chequear que el observador esté aún corriendo.
    if not observer.is_alive():
        return
    try:
        # Intentar obtener un evento de la cola.
        new_item = q.get_nowait()
    except queue.Empty:
        # Si no hay ninguno, continuar normalmente.
        pass
    else:
        # Si se pudo obtener un evento, agregarlo a la vista de árbol.
        modtree.insert("", 0, text=new_item[0], values=new_item[1:])
    # Volver a chequear dentro de medio segundo (500 ms).
    root.after(500, process_events, observer, q, modtree)
root = tk.Tk()
root.config(width=600, height=500)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.title("Registro de modificaciones en tiempo real")
modtree = ttk.Treeview(columns=("action", "time",))
modtree.heading("#0", text="Archivo")
modtree.heading("action", text="Acción")
modtree.heading("time", text="Hora")
modtree.grid(column=0, row=0, sticky="nsew")
# Observador de eventos de Watchdog.
observer = Observer()
# Cola para comunicación entre el observador y la aplicación de Tk.
# Para una explicación más detallada sobre la cola y Tk, véase
# https://www.recursospython.com/guias-y-manuales/tareas-en-segundo-plano-con-tcl-tk-tkinter/.
q = queue.Queue()
observer.schedule(MyEventHandler(q), ".", recursive=False)
observer.start()
# Programar función que procesa los eventos del observador.
# Para la función after(), véase
# https://www.recursospython.com/guias-y-manuales/la-funcion-after-en-tkinter/.
root.after(1, process_events, observer, q, modtree)
root.mainloop()
observer.stop()
observer.join()