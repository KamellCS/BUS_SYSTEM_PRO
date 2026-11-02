"""Usuarios del sistema y actividad (solo administrador)."""
import tkinter as tk

from ... import session, utils
from ...errors import AppError
from ...services import auditoria, usuarios
from .. import theme as T
from ..shell import View
from ..widgets import Button, Card, DataTable, FormDialog

ROLES = [("admin", "Administrador"), ("trabajador", "Trabajador")]


class UsuariosView(View):
    titulo = "USUARIOS"
    subtitulo = "Cuentas de acceso: administradores y trabajadores (vendedores)"

    def build(self):
        Button(self.acciones, "+  Nuevo usuario", self._nuevo, "primary").pack(side="right")
        self.cuerpo.columnconfigure(0, weight=1)
        self.cuerpo.rowconfigure(0, weight=3)
        self.cuerpo.rowconfigure(1, weight=2)

        card = Card(self.cuerpo, "CUENTAS")
        card.grid(row=0, column=0, sticky="nsew")
        Button(card.actions, "Activar / Desactivar", self._estado, "danger", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Restablecer contraseña", self._reset, "accent", small=True).pack(side="right", padx=(6, 0))
        Button(card.actions, "Editar", self._editar, "outline", small=True).pack(side="right")
        self.tabla = DataTable(card.body, [
            ("user", "Usuario", 120, "w"), ("nombre", "Nombre", 200, "w"), ("rol", "Rol", 120, "center"),
            ("estado", "Estado", 90, "center"), ("ventas", "Boletos vendidos", 130, "center"),
            ("acceso", "Último acceso", 150, "center")], height=7, on_double=lambda u: self._editar())
        self.tabla.pack(fill="both", expand=True)

        act = Card(self.cuerpo, "ACTIVIDAD RECIENTE")
        act.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        self.t_audit = DataTable(act.body, [("fecha", "Fecha", 150, "center"), ("usuario", "Usuario", 110, "w"),
                                            ("accion", "Acción", 170, "w"), ("detalle", "Detalle", 420, "w")],
                                 height=6)
        self.t_audit.pack(fill="both", expand=True)
        self._cargar()

    def _cargar(self):
        self.tabla.set_rows(usuarios.listar(), lambda u: (
            u["username"] + ("  (tú)" if u["id"] == session.usuario_id() else ""), u["nombre_completo"],
            "Administrador" if u["rol"] == "admin" else "Trabajador", "Activo" if u["activo"] else "Inactivo",
            u["ventas"], utils.fecha_hora(u["ultimo_acceso"]) if u["ultimo_acceso"] else "Nunca"),
            tag=lambda u: None if u["activo"] else "muted")
        filas = auditoria.recientes(80)
        for i, f in enumerate(filas):
            f["id"] = i
        self.t_audit.set_rows(filas, lambda a: (utils.fecha_hora(a["fecha"]), a["usuario"], a["accion"],
                                                a["detalle"] or ""),
                              tag=lambda a: "bad" if "FALLIDO" in a["accion"] or "BLOQUEADO" in a["accion"] else None)

    def _sel(self):
        u = self.tabla.selected()
        if not u:
            self.info("Selecciona un usuario.", "Atención")
        return u

    def _nuevo(self):
        campos = [{"key": "username", "label": "Usuario", "required": True},
                  {"key": "rol", "label": "Rol", "type": "combo", "options": ROLES, "default": "trabajador",
                   "required": True},
                  {"key": "nombres", "label": "Nombres", "required": True},
                  {"key": "apellidos", "label": "Apellidos", "required": True},
                  {"key": "password", "label": "Contraseña", "type": "password", "required": True},
                  {"key": "password2", "label": "Repetir contraseña", "type": "password", "required": True}]
        d = FormDialog(self, "Nuevo usuario", campos, on_submit=usuarios.crear,
                       subtitle="Mínimo 6 caracteres con letras y números")
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _editar(self):
        u = self._sel()
        if not u:
            return
        campos = [{"key": "username", "label": "Usuario", "type": "readonly"},
                  {"key": "rol", "label": "Rol", "type": "combo", "options": ROLES},
                  {"key": "nombres", "label": "Nombres", "required": True},
                  {"key": "apellidos", "label": "Apellidos", "required": True}]
        d = FormDialog(self, f"Editar usuario @{u['username']}", campos, initial=u,
                       on_submit=lambda data: usuarios.actualizar(u["id"], data))
        self.wait_window(d)
        if d.result:
            self._cargar()

    def _reset(self):
        u = self._sel()
        if not u:
            return
        campos = [{"key": "password", "label": "Nueva contraseña", "type": "password", "required": True}]
        d = FormDialog(self, f"Restablecer contraseña de @{u['username']}", campos,
                       on_submit=lambda data: usuarios.restablecer_password(u["id"], data["password"]))
        self.wait_window(d)
        if d.result:
            self.info("Contraseña actualizada.")
            self._cargar()

    def _estado(self):
        u = self._sel()
        if not u:
            return
        try:
            usuarios.cambiar_estado(u["id"], not u["activo"])
        except AppError as e:
            return self.error(e)
        self._cargar()
