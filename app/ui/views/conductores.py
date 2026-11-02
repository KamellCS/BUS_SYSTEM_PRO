"""Conductores (solo administrador)."""
from ...errors import AppError
from ...services import catalogos
from ..shell import View
from ..widgets import Button, Card, DataTable, FormDialog

CAMPOS = [
    {"key": "dni", "label": "DNI", "required": True},
    {"key": "licencia", "label": "N° de licencia", "required": True},
    {"key": "nombres", "label": "Nombres", "required": True},
    {"key": "apellidos", "label": "Apellidos", "required": True},
    {"key": "telefono", "label": "Teléfono"},
]


class ConductoresView(View):
    titulo = "CONDUCTORES"
    subtitulo = "Personal de conducción asignado a los horarios y viajes"

    def build(self):
        Button(self.acciones, "+  Nuevo conductor", self._nuevo, "primary").pack(side="right")
        card = Card(self.cuerpo, "PERSONAL")
        card.pack(fill="both", expand=True)
        Button(card.actions, "Eliminar", self._eliminar, "danger", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Activar / Desactivar", self._estado, "accent", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Editar", self._editar, "outline", small=True).pack(side="right")
        self.tabla = DataTable(card.body, [
            ("dni", "DNI", 100, "center"), ("nombres", "Nombres", 150, "w"), ("apellidos", "Apellidos", 200, "w"),
            ("licencia", "Licencia", 130, "center"), ("tel", "Teléfono", 120, "center"),
            ("estado", "Estado", 100, "center"), ("viajes", "Viajes programados", 150, "center")],
            height=16, on_double=lambda c: self._editar())
        self.tabla.pack(fill="both", expand=True)
        self._cargar()

    def _cargar(self):
        self.tabla.set_rows(catalogos.listar_conductores(),
                            lambda c: (c["dni"], c["nombres"], c["apellidos"], c["licencia"], c["telefono"] or "—",
                                       "Activo" if c["activo"] else "Inactivo", c["viajes_programados"]),
                            tag=lambda c: None if c["activo"] else "muted")

    def _sel(self):
        c = self.tabla.selected()
        if not c:
            self.info("Selecciona un conductor.", "Atención")
        return c

    def _nuevo(self):
        d = FormDialog(self, "Nuevo conductor", CAMPOS, on_submit=catalogos.guardar_conductor)
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _editar(self):
        c = self._sel()
        if not c:
            return
        d = FormDialog(self, "Editar conductor", CAMPOS, initial=c,
                       on_submit=lambda data: catalogos.guardar_conductor(data, c["id"]))
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _estado(self):
        c = self._sel()
        if not c:
            return
        try:
            catalogos.cambiar_estado_conductor(c["id"], not c["activo"])
        except AppError as e:
            return self.error(e)
        self._cargar()

    def _eliminar(self):
        c = self._sel()
        if not c or not self.confirmar(f"¿Eliminar a {c['nombre_completo']}?"):
            return
        try:
            catalogos.eliminar_conductor(c["id"])
        except AppError as e:
            return self.error(e)
        self._cargar()
