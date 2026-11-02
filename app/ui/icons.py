"""Íconos vectoriales dibujados en Canvas (sin imágenes externas ni emojis)."""
import math
import tkinter as tk

from . import theme


def rounded_rect(cv: tk.Canvas, x1, y1, x2, y2, r=10, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def gradient(cv: tk.Canvas, x1, y1, x2, y2, c1, c2, tag="grad", step=3, horizontal=False):
    largo = int((x2 - x1) if horizontal else (y2 - y1))
    for i in range(0, max(largo, 1), step):
        color = theme.mix(c1, c2, i / max(largo, 1))
        if horizontal:
            cv.create_rectangle(x1 + i, y1, x1 + i + step, y2, fill=color, outline="", tags=tag)
        else:
            cv.create_rectangle(x1, y1 + i, x2, y1 + i + step, fill=color, outline="", tags=tag)


# ------------------------------------------------------------------ íconos
_hole = "#ffffff"


def draw(cv, name, cx, cy, s=22, color="#ffffff", tags=(), bg="#ffffff"):
    """Dibuja el ícono `name`. `bg` es el color del fondo (para los huecos)."""
    global _hole
    _hole = bg
    fn = _ICONOS.get(name)
    if fn:
        fn(cv, cx, cy, s, color, tags)


def _lw(s):
    return max(1.6, s / 11)


def _dashboard(cv, cx, cy, s, c, t):
    q = s * 0.42
    for dx in (-1, 1):
        for dy in (-1, 1):
            x = cx + (dx * 0.06 * s if dx > 0 else -q - 0.06 * s)
            y = cy + (dy * 0.06 * s if dy > 0 else -q - 0.06 * s)
            rounded_rect(cv, x, y, x + q, y + q, r=s * 0.08, fill=c, outline="", tags=t)


def _seat(cv, cx, cy, s, c, t):
    rounded_rect(cv, cx - s * .30, cy - s * .48, cx + s * .10, cy + s * .14, r=s * .1, fill=c, outline="", tags=t)
    rounded_rect(cv, cx - s * .38, cy + s * .08, cx + s * .38, cy + s * .30, r=s * .08, fill=c, outline="", tags=t)
    cv.create_line(cx - s * .26, cy + s * .30, cx - s * .26, cy + s * .48, fill=c, width=_lw(s), tags=t)
    cv.create_line(cx + s * .26, cy + s * .30, cx + s * .26, cy + s * .48, fill=c, width=_lw(s), tags=t)
    cv.create_line(cx + s * .38, cy + s * .08, cx + s * .38, cy - s * .12, fill=c, width=_lw(s), tags=t)


def _seats(cv, cx, cy, s, c, t):
    q = s * .26
    for i in range(3):
        for j in range(2):
            x = cx - s * .45 + j * (q + s * .08) + (s * .14 if j else 0)
            y = cy - s * .45 + i * (q + s * .07)
            rounded_rect(cv, x, y, x + q, y + q, r=s * .05, fill=c, outline="", tags=t)


def _idcard(cv, cx, cy, s, c, t):
    rounded_rect(cv, cx - s * .45, cy - s * .38, cx + s * .45, cy + s * .38, r=s * .1,
                 outline=c, fill="", width=_lw(s), tags=t)
    cv.create_oval(cx - s * .30, cy - s * .18, cx - s * .08, cy + s * .04, fill=c, outline="", tags=t)
    cv.create_arc(cx - s * .36, cy + s * .04, cx - s * .02, cy + s * .34, start=0, extent=180,
                  fill=c, outline="", style="chord", tags=t)
    for k, w in ((-.12, .28), (.02, .22), (.16, .26)):
        cv.create_line(cx + s * .06, cy + s * k, cx + s * (.06 + w), cy + s * k, fill=c,
                       width=_lw(s), capstyle="round", tags=t)


def _bus(cv, cx, cy, s, c, t):
    """Bus de frente (logo)."""
    rounded_rect(cv, cx - s * .38, cy - s * .48, cx + s * .38, cy + s * .36, r=s * .14, fill=c, outline="", tags=t)
    hueco = _hole
    rounded_rect(cv, cx - s * .28, cy - s * .36, cx + s * .28, cy - s * .02, r=s * .06, fill=hueco, outline="", tags=t)
    cv.create_oval(cx - s * .26, cy + s * .10, cx - s * .14, cy + s * .22, fill=hueco, outline="", tags=t)
    cv.create_oval(cx + s * .14, cy + s * .10, cx + s * .26, cy + s * .22, fill=hueco, outline="", tags=t)
    cv.create_rectangle(cx - s * .30, cy + s * .34, cx - s * .16, cy + s * .50, fill=c, outline="", tags=t)
    cv.create_rectangle(cx + s * .16, cy + s * .34, cx + s * .30, cy + s * .50, fill=c, outline="", tags=t)
    cv.create_line(cx - s * .38, cy - s * .30, cx - s * .48, cy - s * .30, cx - s * .48, cy - s * .12,
                   fill=c, width=_lw(s), tags=t)
    cv.create_line(cx + s * .38, cy - s * .30, cx + s * .48, cy - s * .30, cx + s * .48, cy - s * .12,
                   fill=c, width=_lw(s), tags=t)


def _route(cv, cx, cy, s, c, t):
    x, y = cx - s * .12, cy - s * .08
    cv.create_oval(x - s * .26, y - s * .36, x + s * .26, y + s * .16, fill=c, outline="", tags=t)
    cv.create_polygon(x - s * .22, y, x + s * .22, y, x, y + s * .44, fill=c, outline="", tags=t)
    cv.create_oval(x - s * .09, y - s * .19, x + s * .09, y - s * .01, fill=_hole, outline="", tags=t)
    ox, oy, r = cx + s * .26, cy + s * .26, s * .2
    cv.create_oval(ox - r, oy - r, ox + r, oy + r, outline=c, width=_lw(s), fill=_hole, tags=t)
    cv.create_line(ox, oy - r * .55, ox, oy, ox + r * .5, oy, fill=c, width=_lw(s) * .8, tags=t)


def _chart(cv, cx, cy, s, c, t):
    base = cy + s * .42
    for i, h in enumerate((.35, .62, .85)):
        x = cx - s * .36 + i * s * .27
        rounded_rect(cv, x, base - s * h, x + s * .18, base, r=s * .04, fill=c, outline="", tags=t)
    cv.create_line(cx - s * .46, base + s * .04, cx + s * .46, base + s * .04, fill=c, width=_lw(s), tags=t)


def _gear(cv, cx, cy, s, c, t):
    pts = []
    for i in range(32):
        ang = i * math.pi / 16
        r = s * (.48 if (i // 2) % 2 == 0 else .36)
        pts += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
    cv.create_polygon(pts, fill=c, outline="", tags=t)
    r = s * .15
    cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill=_hole, outline="", tags=t)


def _logout(cv, cx, cy, s, c, t):
    w = _lw(s)
    cv.create_line(cx + s * .05, cy - s * .42, cx - s * .40, cy - s * .42, cx - s * .40, cy + s * .42,
                   cx + s * .05, cy + s * .42, fill=c, width=w, joinstyle="round", tags=t)
    cv.create_line(cx - s * .12, cy, cx + s * .45, cy, fill=c, width=w, arrow="last",
                   arrowshape=(s * .25, s * .25, s * .12), tags=t)


def _users(cv, cx, cy, s, c, t):
    for dx, k in ((-.16, 1.0), (.2, .85)):
        x = cx + s * dx
        r = s * .15 * k
        cv.create_oval(x - r, cy - s * .32 - r, x + r, cy - s * .32 + r, fill=c, outline="", tags=t)
        cv.create_arc(x - s * .28 * k, cy - s * .08, x + s * .28 * k, cy + s * .55, start=0, extent=180,
                      fill=c, outline="", style="chord", tags=t)


def _person(cv, cx, cy, s, c, t):
    r = s * .2
    cv.create_oval(cx - r, cy - s * .40, cx + r, cy - s * .40 + 2 * r, fill=c, outline="", tags=t)
    cv.create_arc(cx - s * .38, cy - s * .02, cx + s * .38, cy + s * .70, start=0, extent=180,
                  fill=c, outline="", style="chord", tags=t)


def _person_plus(cv, cx, cy, s, c, t):
    _person(cv, cx - s * .1, cy, s * .9, c, t)
    w = _lw(s) * 1.2
    cv.create_line(cx + s * .30, cy + s * .02, cx + s * .30, cy + s * .38, fill=c, width=w, tags=t)
    cv.create_line(cx + s * .12, cy + s * .20, cx + s * .48, cy + s * .20, fill=c, width=w, tags=t)


def _driver(cv, cx, cy, s, c, t):
    w = _lw(s)
    r = s * .44
    cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline=c, width=w, tags=t)
    cv.create_oval(cx - s * .1, cy - s * .1, cx + s * .1, cy + s * .1, fill=c, outline="", tags=t)
    cv.create_line(cx - r, cy, cx + r, cy, fill=c, width=w, tags=t)
    cv.create_line(cx, cy, cx, cy + r, fill=c, width=w, tags=t)


def _bell(cv, cx, cy, s, c, t):
    cv.create_polygon(cx - s * .34, cy + s * .24, cx - s * .26, cy - s * .05, cx - s * .2, cy - s * .30,
                      cx, cy - s * .40, cx + s * .2, cy - s * .30, cx + s * .26, cy - s * .05,
                      cx + s * .34, cy + s * .24, smooth=True, fill=c, outline="", tags=t)
    cv.create_rectangle(cx - s * .38, cy + s * .2, cx + s * .38, cy + s * .28, fill=c, outline="", tags=t)
    cv.create_oval(cx - s * .09, cy + s * .30, cx + s * .09, cy + s * .46, fill=c, outline="", tags=t)


def _calendar(cv, cx, cy, s, c, t):
    w = _lw(s) * .9
    rounded_rect(cv, cx - s * .42, cy - s * .32, cx + s * .42, cy + s * .44, r=s * .08, outline=c,
                 fill="", width=w, tags=t)
    cv.create_line(cx - s * .42, cy - s * .08, cx + s * .42, cy - s * .08, fill=c, width=w, tags=t)
    for dx in (-.2, .2):
        cv.create_line(cx + s * dx, cy - s * .46, cx + s * dx, cy - s * .2, fill=c, width=w, tags=t)


def _menu(cv, cx, cy, s, c, t):
    for dy in (-.3, 0, .3):
        cv.create_line(cx - s * .42, cy + s * dy, cx + s * .42, cy + s * dy, fill=c,
                       width=_lw(s), capstyle="round", tags=t)


def _suitcase(cv, cx, cy, s, c, t):
    rounded_rect(cv, cx - s * .46, cy - s * .22, cx + s * .46, cy + s * .42, r=s * .1, fill=c, outline="", tags=t)
    cv.create_line(cx - s * .16, cy - s * .22, cx - s * .16, cy - s * .40, cx + s * .16, cy - s * .40,
                   cx + s * .16, cy - s * .22, fill=c, width=_lw(s), tags=t)
    cv.create_line(cx - s * .46, cy + s * .06, cx + s * .46, cy + s * .06, fill="#ffffff", width=_lw(s) * .7, tags=t)


def _money(cv, cx, cy, s, c, t):
    rounded_rect(cv, cx - s * .48, cy - s * .28, cx + s * .48, cy + s * .28, r=s * .06, fill=c, outline="", tags=t)
    r = s * .14
    cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#ffffff", outline="", tags=t)
    for dx in (-.34, .34):
        cv.create_oval(cx + s * dx - s * .04, cy - s * .04, cx + s * dx + s * .04, cy + s * .04,
                       fill="#ffffff", outline="", tags=t)


def _lock(cv, cx, cy, s, c, t):
    w = _lw(s)
    cv.create_arc(cx - s * .24, cy - s * .48, cx + s * .24, cy, start=0, extent=180, style="arc",
                  outline=c, width=w, tags=t)
    cv.create_line(cx - s * .24, cy - s * .24, cx - s * .24, cy - s * .02, fill=c, width=w, tags=t)
    cv.create_line(cx + s * .24, cy - s * .24, cx + s * .24, cy - s * .02, fill=c, width=w, tags=t)
    rounded_rect(cv, cx - s * .38, cy - s * .04, cx + s * .38, cy + s * .44, r=s * .08, fill=c, outline="", tags=t)


def _search(cv, cx, cy, s, c, t):
    r = s * .28
    w = _lw(s)
    cv.create_oval(cx - r - s * .08, cy - r - s * .08, cx + r - s * .08, cy + r - s * .08, outline=c, width=w, tags=t)
    cv.create_line(cx + s * .12, cy + s * .12, cx + s * .42, cy + s * .42, fill=c, width=w * 1.3,
                   capstyle="round", tags=t)


def _stairs(cv, cx, cy, s, c, t):
    pts = [cx - s * .45, cy + s * .4]
    for i in range(4):
        x = cx - s * .45 + i * s * .22
        y = cy + s * .4 - (i + 1) * s * .2
        pts += [x, y, x + s * .22, y]
    cv.create_line(*pts, fill=c, width=_lw(s), tags=t)


def _check(cv, cx, cy, s, c, t):
    cv.create_line(cx - s * .35, cy, cx - s * .08, cy + s * .28, cx + s * .4, cy - s * .3,
                   fill=c, width=_lw(s) * 1.3, capstyle="round", joinstyle="round", tags=t)


def _ticket(cv, cx, cy, s, c, t):
    rounded_rect(cv, cx - s * .48, cy - s * .30, cx + s * .48, cy + s * .30, r=s * .06, fill=c, outline="", tags=t)
    for dx in (-.48, .48):
        r = s * .1
        cv.create_oval(cx + s * dx - r, cy - r, cx + s * dx + r, cy + r, fill="#ffffff", outline="", tags=t)
    cv.create_line(cx + s * .18, cy - s * .24, cx + s * .18, cy + s * .24, fill="#ffffff", dash=(2, 2), tags=t)


_ICONOS = {
    "dashboard": _dashboard, "seat": _seat, "seats": _seats, "idcard": _idcard, "bus": _bus,
    "route": _route, "chart": _chart, "gear": _gear, "logout": _logout, "users": _users,
    "person": _person, "person_plus": _person_plus, "driver": _driver, "bell": _bell,
    "calendar": _calendar, "menu": _menu, "suitcase": _suitcase, "money": _money, "lock": _lock,
    "search": _search, "stairs": _stairs, "check": _check, "ticket": _ticket,
}


# ------------------------------------------------------------------ bus grande (login)
def draw_bus_side(cv, x, y, w, body="#ffffff", accent=None, glass="#0d3366", tags=()):
    """Bus de perfil (mirando a la derecha) para la pantalla de login."""
    accent = accent or theme.ACCENT
    h = w * 0.42
    rounded_rect(cv, x, y, x + w, y + h, r=w * .07, fill=body, outline="", tags=tags)
    # parabrisas frontal
    cv.create_polygon(x + w * .86, y + h * .12, x + w * .965, y + h * .12, x + w * .985, y + h * .55,
                      x + w * .86, y + h * .55, fill=glass, outline="", tags=tags)
    # ventanas laterales
    for i in range(5):
        wx = x + w * (.05 + i * .147)
        rounded_rect(cv, wx, y + h * .12, wx + w * .127, y + h * .50, r=w * .015, fill=glass, outline="", tags=tags)
    # franja de color de la empresa
    cv.create_rectangle(x + w * .01, y + h * .60, x + w * .99, y + h * .70, fill=accent, outline="", tags=tags)
    cv.create_rectangle(x + w * .01, y + h * .72, x + w * .99, y + h * .75, fill=theme.WARNING, outline="", tags=tags)
    # puerta
    cv.create_rectangle(x + w * .79, y + h * .14, x + w * .84, y + h * .92, fill=theme.mix(glass, body, .25),
                        outline="", tags=tags)
    # faro y luz trasera
    cv.create_oval(x + w * .955, y + h * .78, x + w * .99, y + h * .88, fill="#ffd34d", outline="", tags=tags)
    cv.create_rectangle(x + w * .005, y + h * .78, x + w * .02, y + h * .9, fill="#ff5a5a", outline="", tags=tags)
    # ruedas
    for wx in (.2, .7):
        r = w * .075
        ccx, ccy = x + w * wx, y + h * .98
        cv.create_oval(ccx - r * 1.25, ccy - r * 1.25, ccx + r * 1.25, ccy + r * 1.25, fill=body, outline="", tags=tags)
        cv.create_oval(ccx - r, ccy - r, ccx + r, ccy + r, fill="#1a2433", outline="", tags=tags)
        cv.create_oval(ccx - r * .45, ccy - r * .45, ccx + r * .45, ccy + r * .45, fill="#c9d3e0", outline="", tags=tags)
    return h


def window_icon(root) -> tk.PhotoImage:
    """Ícono de 32x32 para la barra de título (bus turquesa)."""
    img = tk.PhotoImage(master=root, width=32, height=32)
    img.put(theme.SIDEBAR_TOP, to=(0, 0, 32, 32))
    img.put(theme.ACCENT, to=(7, 4, 25, 26))
    img.put("#0b2b5a", to=(9, 7, 23, 15))
    img.put("#ffd34d", to=(9, 19, 12, 22))
    img.put("#ffd34d", to=(20, 19, 23, 22))
    img.put(theme.ACCENT, to=(8, 26, 12, 29))
    img.put(theme.ACCENT, to=(20, 26, 24, 29))
    return img
