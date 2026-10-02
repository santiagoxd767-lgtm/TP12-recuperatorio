"""
Mascota virtual tipo Pou, hecha con pygame.
Ejecutar:  python pou.py
Necesita:  pip install pygame   (y pou.png en la misma carpeta)
"""
import json
import math
import os
import random
import sys

# La ventana aparece arriba a la izquierda para que siempre se vea la barra de título
os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "80,30")

import pygame

# ---------------------------------------------------------------- configuración
ANCHO, ALTO = 480, 800
FPS = 60
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_GUARDADO = os.path.join(CARPETA, "guardado.json")

# Cuánto baja cada necesidad por segundo
DESGASTE = {"hambre": 1.2, "felicidad": 0.8, "energia": 0.6, "higiene": 0.7}

COLOR_FONDO_ARRIBA = (250, 214, 165)
COLOR_FONDO_ABAJO = (234, 180, 120)
COLOR_PISO = (186, 130, 82)
COLOR_BOTON = (255, 255, 255)
COLOR_BOTON_HOVER = (255, 240, 200)
COLOR_TEXTO = (70, 40, 30)

NOMBRES = {
    "hambre": "Comida",
    "felicidad": "Alegría",
    "energia": "Energía",
    "higiene": "Limpieza",
}
COLORES_BARRA = {
    "hambre": (240, 120, 60),
    "felicidad": (250, 200, 50),
    "energia": (90, 170, 240),
    "higiene": (90, 210, 170),
}


def limitar(valor, minimo=0, maximo=100):
    return max(minimo, min(maximo, valor))


# ---------------------------------------------------------------- estado de Pou
class Estado:
    """Guarda las necesidades (0 a 100) y las guarda/carga en un archivo."""

    def __init__(self):
        self.valores = {k: 80.0 for k in DESGASTE}
        self.monedas = 0
        self.cargar()

    def cargar(self):
        try:
            with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
            for k in self.valores:
                self.valores[k] = limitar(float(datos.get(k, 80)))
            self.monedas = int(datos.get("monedas", 0))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass

    def guardar(self):
        datos = dict(self.valores)
        datos["monedas"] = self.monedas
        try:
            with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
                json.dump(datos, f)
        except OSError:
            pass

    def cambiar(self, clave, cantidad):
        self.valores[clave] = limitar(self.valores[clave] + cantidad)

    def promedio(self):
        return sum(self.valores.values()) / len(self.valores)


# ---------------------------------------------------------------- botones
class Boton:
    def __init__(self, rect, texto, accion):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.accion = accion

    def dibujar(self, pantalla, fuente, mouse):
        color = COLOR_BOTON_HOVER if self.rect.collidepoint(mouse) else COLOR_BOTON
        pygame.draw.rect(pantalla, (0, 0, 0, 40), self.rect.move(0, 4), border_radius=16)
        pygame.draw.rect(pantalla, color, self.rect, border_radius=16)
        pygame.draw.rect(pantalla, COLOR_TEXTO, self.rect, 3, border_radius=16)
        img = fuente.render(self.texto, True, COLOR_TEXTO)
        pantalla.blit(img, img.get_rect(center=self.rect.center))


# ---------------------------------------------------------------- mini juego
class MiniJuegoSalto:
    """Pou salta de plataforma en plataforma y junta monedas (estilo Pou Sky Jump).

    Controles: flechas o A/D, o mantené apretado el mouse y Pou va hacia él.
    Esc o el botón II pausan el juego.
    """

    GRAVEDAD = 1500.0
    SALTO = -820.0
    VEL_LATERAL = 380.0
    ANCHO_PLATAFORMA = 90
    ALTO_PLATAFORMA = 22

    def __init__(self, sprite, fuente, fuente_grande, moneda=None):
        self.moneda = moneda
        ancho = 64
        alto = int(sprite.get_height() * ancho / sprite.get_width())
        self.sprite = pygame.transform.smoothscale(sprite, (ancho, alto))
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.boton_pausa = Boton((ANCHO - 70, 10, 60, 50), "II", None)
        self.boton_continuar = Boton((120, 330, 240, 60), "Continuar", None)
        self.boton_otra = Boton((120, 400, 240, 60), "Jugar de nuevo", None)
        self.boton_salir = Boton((120, 470, 240, 60), "Salir", None)
        self.reiniciar()

    # ------------------------------------------------------------ estado
    def reiniciar(self):
        self.estado = "jugando"  # jugando / pausa / fin
        self.x = ANCHO / 2
        self.y = ALTO - 60.0  # y = donde están los pies de Pou
        self.vy = self.SALTO
        self.puntos = 0.0
        self.monedas = 0
        self.plataformas = [{"x": ANCHO / 2 - self.ANCHO_PLATAFORMA / 2, "y": ALTO - 60.0, "vx": 0.0}]
        self.items = []  # monedas
        self.rellenar()

    def rellenar(self):
        """Crea plataformas nuevas hasta llenar la parte de arriba de la pantalla."""
        if not self.plataformas:
            self.plataformas.append({"x": ANCHO / 2 - 45, "y": ALTO - 60.0, "vx": 0.0})
        while min(p["y"] for p in self.plataformas) > -60:
            arriba = min(p["y"] for p in self.plataformas)
            # los huecos se van agrandando de a poco (nunca más de lo que Pou puede saltar)
            hueco = random.uniform(70, min(150, 90 + self.puntos / 25))
            y = arriba - hueco
            x = random.uniform(0, ANCHO - self.ANCHO_PLATAFORMA)
            vx = 0.0
            if self.puntos > 150 and random.random() < 0.2:
                vx = random.choice([-1, 1]) * random.uniform(60, 120)
            self.plataformas.append({"x": x, "y": y, "vx": vx})
            if vx == 0 and random.random() < 0.3:
                self.items.append({"x": x + self.ANCHO_PLATAFORMA / 2, "y": y - 30})

    # ------------------------------------------------------------ lógica
    def actualizar(self, dt, mouse_x, mouse_apretado, teclas):
        if self.estado != "jugando":
            return
        dt = min(dt, 1 / 30)

        # Movimiento lateral
        mov = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            mov -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            mov += 1
        if mov:
            self.x += mov * self.VEL_LATERAL * dt
        elif mouse_apretado:
            paso = self.VEL_LATERAL * 1.3 * dt
            self.x += max(-paso, min(paso, mouse_x - self.x))
        # Si sale por un costado, aparece por el otro
        if self.x < -20:
            self.x = ANCHO + 20
        elif self.x > ANCHO + 20:
            self.x = -20

        # Plataformas que se mueven
        for p in self.plataformas:
            p["x"] += p["vx"] * dt
            if p["x"] < 0:
                p["x"] = 0
                p["vx"] = abs(p["vx"])
            elif p["x"] > ANCHO - self.ANCHO_PLATAFORMA:
                p["x"] = ANCHO - self.ANCHO_PLATAFORMA
                p["vx"] = -abs(p["vx"])

        # Física
        y_anterior = self.y
        self.vy += self.GRAVEDAD * dt
        self.y += self.vy * dt

        # Rebote: solo cuando Pou está cayendo y atraviesa la parte de arriba de una plataforma
        if self.vy > 0:
            for p in self.plataformas:
                if (
                    y_anterior <= p["y"] + 4
                    and self.y >= p["y"]
                    and p["x"] - 25 <= self.x <= p["x"] + self.ANCHO_PLATAFORMA + 25
                ):
                    self.y = p["y"]
                    self.vy = self.SALTO
                    break

        # Monedas
        alto_pou = self.sprite.get_height()
        for it in self.items[:]:
            if abs(it["x"] - self.x) < 40 and self.y - alto_pou - 10 <= it["y"] <= self.y + 10:
                self.items.remove(it)
                self.monedas += 1

        # Cámara: cuando Pou sube mucho, baja todo el mundo
        limite = ALTO * 0.42
        if self.y < limite:
            d = limite - self.y
            self.y = limite
            for p in self.plataformas:
                p["y"] += d
            for it in self.items:
                it["y"] += d
            self.puntos += d / 10
            self.plataformas = [p for p in self.plataformas if p["y"] < ALTO + 40]
            self.items = [it for it in self.items if it["y"] < ALTO + 40]
            self.rellenar()

        # Se cayó
        if self.y > ALTO + alto_pou:
            self.estado = "fin"

    def manejar_evento(self, e, pos):
        """Devuelve "salir" cuando hay que volver a la casa de Pou."""
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.estado == "jugando":
                self.estado = "pausa"
            elif self.estado == "pausa":
                self.estado = "jugando"
            return None
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.estado == "jugando":
                if self.boton_pausa.rect.collidepoint(pos):
                    self.estado = "pausa"
            elif self.estado == "pausa":
                if self.boton_continuar.rect.collidepoint(pos):
                    self.estado = "jugando"
                elif self.boton_salir.rect.collidepoint(pos):
                    return "salir"
            elif self.estado == "fin":
                if self.boton_otra.rect.collidepoint(pos):
                    self.reiniciar()
                elif self.boton_salir.rect.collidepoint(pos):
                    return "salir"
        return None

    # ------------------------------------------------------------ dibujo
    def texto_con_borde(self, pantalla, texto, fuente, pos, centrado=False):
        borde = fuente.render(texto, True, (60, 35, 20))
        frente = fuente.render(texto, True, (255, 255, 255))
        r = frente.get_rect(center=pos) if centrado else frente.get_rect(topleft=pos)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            pantalla.blit(borde, r.move(dx, dy))
        pantalla.blit(frente, r)

    def dibujar_plataforma(self, pantalla, p):
        r = pygame.Rect(int(p["x"]), int(p["y"]), self.ANCHO_PLATAFORMA, self.ALTO_PLATAFORMA)
        pygame.draw.rect(pantalla, (120, 120, 130), r, border_radius=8)
        pygame.draw.rect(pantalla, (70, 70, 80), r, 3, border_radius=8)
        pygame.draw.rect(pantalla, (170, 110, 50), (r.x + 4, r.y, r.w - 8, 5), border_radius=3)
        for dx in (18, 45, 70):
            pygame.draw.circle(pantalla, (90, 90, 100), (r.x + dx, r.y + 14), 5, 2)

    def dibujar(self, pantalla, mouse):
        pantalla.fill((236, 166, 92))

        for p in self.plataformas:
            self.dibujar_plataforma(pantalla, p)

        for it in self.items:
            c = (int(it["x"]), int(it["y"]))
            if self.moneda:
                pantalla.blit(self.moneda, self.moneda.get_rect(center=c))
            else:  # por si falta moneda.png
                pygame.draw.circle(pantalla, (150, 110, 0), c, 14)
                pygame.draw.circle(pantalla, (255, 215, 0), c, 11)

        # Pou: se estira un poco al subir/bajar rápido
        factor = 1 + min(abs(self.vy) / 2500, 0.2)
        w = int(self.sprite.get_width() / factor ** 0.5)
        h = int(self.sprite.get_height() * factor)
        img = pygame.transform.smoothscale(self.sprite, (w, h))
        pantalla.blit(img, img.get_rect(midbottom=(int(self.x), int(self.y))))
        # Si está cerca de un borde, también se dibuja del otro lado
        if self.x < 32:
            pantalla.blit(img, img.get_rect(midbottom=(int(self.x) + ANCHO, int(self.y))))
        elif self.x > ANCHO - 32:
            pantalla.blit(img, img.get_rect(midbottom=(int(self.x) - ANCHO, int(self.y))))

        # Marcador
        self.texto_con_borde(pantalla, f"Puntos: {int(self.puntos)}", self.fuente_grande, (12, 10))
        self.texto_con_borde(pantalla, f"Monedas: {self.monedas}", self.fuente, (12, 50))
        if self.moneda:
            pantalla.blit(self.moneda, (170, 46))
        self.boton_pausa.dibujar(pantalla, self.fuente, mouse)

        if self.estado in ("pausa", "fin"):
            velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            velo.fill((0, 0, 0, 130))
            pantalla.blit(velo, (0, 0))
            if self.estado == "pausa":
                self.texto_con_borde(pantalla, "Pausa", self.fuente_grande, (ANCHO // 2, 270), True)
                self.boton_continuar.dibujar(pantalla, self.fuente, mouse)
                self.boton_salir.dibujar(pantalla, self.fuente, mouse)
            else:
                self.texto_con_borde(pantalla, "¡Se terminó!", self.fuente_grande, (ANCHO // 2, 250), True)
                self.texto_con_borde(
                    pantalla, f"{int(self.puntos)} puntos  |  {self.monedas} monedas",
                    self.fuente, (ANCHO // 2, 305), True,
                )
                self.boton_otra.dibujar(pantalla, self.fuente, mouse)
                self.boton_salir.dibujar(pantalla, self.fuente, mouse)


# ---------------------------------------------------------------- juego
class Juego:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Mi Pou")

        # Ventana normal (no pantalla completa): se adapta al alto de tu monitor
        # para que entre completa, y se puede agrandar/achicar arrastrando los bordes.
        try:
            alto_escritorio = pygame.display.get_desktop_sizes()[0][1]
        except Exception:
            alto_escritorio = 768
        alto_ventana = min(ALTO, alto_escritorio - 140)
        ancho_ventana = int(ANCHO * alto_ventana / ALTO)
        pygame.display.set_mode((ancho_ventana, alto_ventana), pygame.RESIZABLE)

        # Todo se dibuja en esta superficie fija de 480x800 y después se
        # escala al tamaño real de la ventana.
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()

        self.fuente = pygame.font.SysFont("arial", 22, bold=True)
        self.fuente_chica = pygame.font.SysFont("arial", 16, bold=True)
        self.fuente_grande = pygame.font.SysFont("arial", 30, bold=True)

        ruta = os.path.join(CARPETA, "pou.png")
        if not os.path.exists(ruta):
            print("Falta pou.png en la carpeta del juego.")
            sys.exit(1)
        self.sprite = pygame.image.load(ruta).convert_alpha()
        # Tamaño base del Pou en pantalla
        ancho_base = 300
        alto_base = int(self.sprite.get_height() * ancho_base / self.sprite.get_width())
        self.sprite = pygame.transform.smoothscale(self.sprite, (ancho_base, alto_base))
        self.base_w, self.base_h = ancho_base, alto_base

        # Logo de la escuela en la pared (semitransparente para que no tape todo)
        self.logo = None
        ruta_logo = os.path.join(CARPETA, "logo.png")
        if os.path.exists(ruta_logo):
            logo = pygame.image.load(ruta_logo).convert_alpha()
            ancho_logo = 200
            alto_logo = int(logo.get_height() * ancho_logo / logo.get_width())
            self.logo = pygame.transform.smoothscale(logo, (ancho_logo, alto_logo))
            self.logo.set_alpha(95)  # 0 = invisible, 255 = opaco

        # Bandera en la pared, al costado del logo
        self.bandera = None
        ruta_bandera = os.path.join(CARPETA, "bandera.png")
        if os.path.exists(ruta_bandera):
            bandera = pygame.image.load(ruta_bandera).convert_alpha()
            ancho_bandera = 120
            alto_bandera = int(bandera.get_height() * ancho_bandera / bandera.get_width())
            self.bandera = pygame.transform.smoothscale(bandera, (ancho_bandera, alto_bandera))
            self.bandera.set_alpha(170)  # 0 = invisible, 255 = opaco

        # Imagen de las monedas del mini juego
        self.moneda = None
        ruta_moneda = os.path.join(CARPETA, "moneda.png")
        if os.path.exists(ruta_moneda):
            moneda = pygame.image.load(ruta_moneda).convert_alpha()
            self.moneda = pygame.transform.smoothscale(moneda, (34, 34))

        self.estado = Estado()

        # Escena actual: "casa" o "salto" (el mini juego)
        self.escena = "casa"
        self.minijuego = MiniJuegoSalto(self.sprite, self.fuente, self.fuente_grande, self.moneda)

        # Posición del Pou (apoyado en el piso)
        self.piso_y = 610
        self.pou_x = ANCHO // 2
        self.salto = 0.0            # altura actual del salto
        self.vel_salto = 0.0
        self.squash_extra = 0.0     # deformación extra al tocarlo
        self.tiempo = 0.0

        # Modos: "normal", "durmiendo"
        self.modo = "normal"
        self.mensaje = ""
        self.mensaje_t = 0.0

        # Efectos
        self.comida = None          # dict con la comida que cae
        self.masticar_t = 0.0
        self.burbujas = []          # lista de burbujas del baño
        self.banando_t = 0.0
        self.corazones = []
        self.zzz = []

        # Botones
        y = ALTO - 90
        w, h, sep = 100, 60, 10
        x0 = (ANCHO - (4 * w + 3 * sep)) // 2
        self.botones = [
            Boton((x0 + 0 * (w + sep), y, w, h), "Comer", self.accion_comer),
            Boton((x0 + 1 * (w + sep), y, w, h), "Jugar", self.accion_jugar),
            Boton((x0 + 2 * (w + sep), y, w, h), "Dormir", self.accion_dormir),
            Boton((x0 + 3 * (w + sep), y, w, h), "Bañar", self.accion_banar),
        ]

    # ------------------------------------------------------------ ventana
    def calcular_vista(self):
        """Devuelve escala y posición con la que se muestra el juego en la ventana."""
        w, h = pygame.display.get_surface().get_size()
        escala = min(w / ANCHO, h / ALTO)
        nw, nh = max(1, int(ANCHO * escala)), max(1, int(ALTO * escala))
        return escala, (w - nw) // 2, (h - nh) // 2, nw, nh

    def a_logico(self, pos):
        """Convierte la posición del mouse en la ventana a la del juego (480x800)."""
        escala, ox, oy, _, _ = self.calcular_vista()
        return (int((pos[0] - ox) / escala), int((pos[1] - oy) / escala))

    def presentar(self):
        """Escala el juego al tamaño de la ventana y lo muestra."""
        ventana = pygame.display.get_surface()
        _, ox, oy, nw, nh = self.calcular_vista()
        ventana.fill((40, 25, 20))
        ventana.blit(pygame.transform.smoothscale(self.pantalla, (nw, nh)), (ox, oy))
        pygame.display.flip()

    # ------------------------------------------------------------ acciones
    def decir(self, texto, segundos=2.5):
        self.mensaje = texto
        self.mensaje_t = segundos

    def accion_comer(self):
        if self.modo != "normal" or self.comida:
            return
        tipo = random.choice(["manzana", "pizza", "helado"])
        self.comida = {"tipo": tipo, "y": 60.0, "vel": 0.0}

    def accion_jugar(self):
        if self.modo != "normal":
            return
        if self.estado.valores["energia"] < 10:
            self.decir("Estoy muy cansado...")
            return
        self.escena = "salto"
        self.minijuego.reiniciar()

    def terminar_minijuego(self):
        """Vuelve a la casa y da los premios del mini juego."""
        mj = self.minijuego
        self.estado.monedas += mj.monedas
        self.estado.cambiar("felicidad", 15 + min(25, int(mj.puntos) // 40))
        self.estado.cambiar("energia", -10)
        self.estado.cambiar("hambre", -5)
        self.escena = "casa"
        self.vel_salto = 14
        self.decir(f"¡{int(mj.puntos)} puntos y {mj.monedas} monedas!", 3.5)
        for _ in range(5):
            self.nuevo_corazon()

    def accion_dormir(self):
        if self.modo == "durmiendo":
            self.modo = "normal"
            self.decir("¡Buen día!")
        else:
            self.modo = "durmiendo"
            self.decir("Zzz... (tocá de nuevo para despertar)", 3)

    def accion_banar(self):
        if self.modo != "normal":
            return
        self.banando_t = 3.0
        self.burbujas = [
            {
                "x": self.pou_x + random.randint(-150, 150),
                "y": self.piso_y - random.randint(0, 300),
                "r": random.randint(8, 24),
                "vel": random.uniform(0.3, 1.2),
            }
            for _ in range(35)
        ]

    def nuevo_corazon(self):
        self.corazones.append(
            {
                "x": self.pou_x + random.randint(-80, 80),
                "y": self.piso_y - self.base_h + random.randint(0, 80),
                "vida": 1.0,
            }
        )

    # ------------------------------------------------------------ actualizar
    def actualizar(self, dt):
        if self.escena == "salto":
            mouse = self.a_logico(pygame.mouse.get_pos())
            apretado = pygame.mouse.get_pressed()[0]
            self.minijuego.actualizar(dt, mouse[0], apretado, pygame.key.get_pressed())
            return
        self.tiempo += dt

        # Desgaste de necesidades (más lento si duerme)
        for k, v in DESGASTE.items():
            if self.modo == "durmiendo":
                if k == "energia":
                    self.estado.cambiar(k, 6 * dt)
                else:
                    self.estado.cambiar(k, -v * 0.3 * dt)
            else:
                self.estado.cambiar(k, -v * dt)

        if self.modo == "durmiendo" and self.estado.valores["energia"] >= 100:
            self.modo = "normal"
            self.decir("¡Descansé de maravilla!")

        # Salto
        if self.salto > 0 or self.vel_salto > 0:
            self.salto += self.vel_salto
            self.vel_salto -= 0.8
            if self.salto <= 0:
                self.salto = 0
                self.vel_salto = 0
                self.squash_extra = 0.15
        # La deformación extra vuelve a cero suavemente
        self.squash_extra *= 0.9

        # Comida cayendo
        if self.comida:
            self.comida["vel"] += 0.6
            self.comida["y"] += self.comida["vel"]
            if self.comida["y"] >= self.piso_y - self.base_h * 0.45:
                self.comida = None
                self.masticar_t = 1.2
                self.estado.cambiar("hambre", 30)
                self.estado.cambiar("felicidad", 5)
                self.decir("¡Ñam ñam!")

        if self.masticar_t > 0:
            self.masticar_t -= dt

        # Baño
        if self.banando_t > 0:
            self.banando_t -= dt
            self.estado.cambiar("higiene", 30 * dt)
            for b in self.burbujas:
                b["y"] -= b["vel"]
            if self.banando_t <= 0:
                self.burbujas = []
                self.decir("¡Qué limpito!")

        # Corazones
        for c in self.corazones:
            c["y"] -= 1.5
            c["vida"] -= dt * 0.8
        self.corazones = [c for c in self.corazones if c["vida"] > 0]

        # Zzz
        if self.modo == "durmiendo" and random.random() < 0.03:
            self.zzz.append({"x": self.pou_x + 90, "y": self.piso_y - self.base_h, "vida": 1.0})
        for z in self.zzz:
            z["y"] -= 1
            z["x"] += math.sin(z["y"] * 0.05)
            z["vida"] -= dt * 0.6
        self.zzz = [z for z in self.zzz if z["vida"] > 0]

        # Mensaje
        if self.mensaje_t > 0:
            self.mensaje_t -= dt

    # ------------------------------------------------------------ dibujo
    def dibujar_fondo(self):
        for y in range(ALTO):
            t = y / ALTO
            color = tuple(
                int(COLOR_FONDO_ARRIBA[i] * (1 - t) + COLOR_FONDO_ABAJO[i] * t) for i in range(3)
            )
            pygame.draw.line(self.pantalla, color, (0, y), (ANCHO, y))
        if self.logo:
            self.pantalla.blit(self.logo, self.logo.get_rect(center=(ANCHO // 2, 270)))
        if self.bandera:
            self.pantalla.blit(self.bandera, self.bandera.get_rect(center=(405, 225)))
        pygame.draw.rect(self.pantalla, COLOR_PISO, (0, self.piso_y, ANCHO, ALTO - self.piso_y))
        pygame.draw.line(self.pantalla, (140, 95, 60), (0, self.piso_y), (ANCHO, self.piso_y), 4)

    def dibujar_barras(self):
        x, y = 15, 15
        ancho, alto = 105, 14
        for i, (k, v) in enumerate(self.estado.valores.items()):
            bx = x + i * (ancho + 12)
            etiqueta = self.fuente_chica.render(NOMBRES[k], True, COLOR_TEXTO)
            self.pantalla.blit(etiqueta, (bx, y))
            pygame.draw.rect(self.pantalla, (255, 255, 255), (bx, y + 22, ancho, alto), border_radius=7)
            relleno = int(ancho * v / 100)
            if relleno > 0:
                pygame.draw.rect(
                    self.pantalla, COLORES_BARRA[k], (bx, y + 22, relleno, alto), border_radius=7
                )
            pygame.draw.rect(self.pantalla, COLOR_TEXTO, (bx, y + 22, ancho, alto), 2, border_radius=7)

        monedas = self.fuente.render(f"Monedas: {self.estado.monedas}", True, COLOR_TEXTO)
        self.pantalla.blit(monedas, (15, 60))

    def dibujar_pou(self):
        # "Respiración": se estira y achata suavemente
        respiracion = math.sin(self.tiempo * 2.5) * 0.02
        escala_y = 1 + respiracion - self.squash_extra
        escala_x = 1 - respiracion + self.squash_extra

        # Masticar: movimiento rápido
        if self.masticar_t > 0:
            escala_y += math.sin(self.tiempo * 25) * 0.04

        # Si duerme, se achata un poco
        if self.modo == "durmiendo":
            escala_y *= 0.95

        w = int(self.base_w * escala_x)
        h = int(self.base_h * escala_y)
        img = pygame.transform.smoothscale(self.sprite, (w, h))

        # Si está triste o sucio se oscurece un poco
        if self.estado.promedio() < 30:
            img.fill((200, 200, 200, 255), special=pygame.BLEND_RGBA_MULT)

        rect = img.get_rect(midbottom=(self.pou_x, self.piso_y + 10 - self.salto))

        # Sombra
        sombra_w = int(w * (0.9 - self.salto / 600))
        sombra = pygame.Surface((max(sombra_w, 10), 24), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 60), sombra.get_rect())
        self.pantalla.blit(sombra, sombra.get_rect(center=(self.pou_x, self.piso_y + 14)))

        self.pantalla.blit(img, rect)
        self.rect_pou = rect

        # Antifaz para dormir, pegado a los ojos del sprite
        if self.modo == "durmiendo":
            self.dibujar_antifaz(rect)

    def dibujar_antifaz(self, rect):
        """Dibuja un antifaz sobre los ojos. Las posiciones son proporcionales
        al tamaño del sprite, así siempre queda justo sobre los ojos."""
        w, h = rect.size
        azul, azul_osc, claro = (80, 90, 175), (40, 45, 110), (170, 180, 245)
        cy = 0.245  # altura de los ojos (proporción del alto del sprite)

        def punto(fx, fy):
            return (rect.left + int(w * fx), rect.top + int(h * fy))

        # Elástico que va por la cabeza
        tira = pygame.Rect(0, 0, int(w * 0.50), max(6, int(h * 0.05)))
        tira.center = punto(0.5, cy)
        pygame.draw.rect(self.pantalla, azul_osc, tira, border_radius=6)

        # Un parche sobre cada ojo
        ancho_p, alto_p = int(w * 0.215), int(h * 0.28)
        for fx in (0.405, 0.595):
            parche = pygame.Rect(0, 0, ancho_p, alto_p)
            parche.center = punto(fx, cy)
            pygame.draw.ellipse(self.pantalla, azul, parche)
            pygame.draw.ellipse(self.pantalla, azul_osc, parche, 4)
            # Ojito cerrado dibujado en el antifaz
            ojo = pygame.Rect(0, 0, int(ancho_p * 0.55), int(alto_p * 0.45))
            ojo.center = parche.center
            pygame.draw.arc(self.pantalla, claro, ojo, math.pi, 2 * math.pi, 3)

    def dibujar_comida(self):
        if not self.comida:
            return
        x, y = self.pou_x, int(self.comida["y"])
        t = self.comida["tipo"]
        if t == "manzana":
            pygame.draw.circle(self.pantalla, (220, 40, 40), (x, y), 28)
            pygame.draw.ellipse(self.pantalla, (60, 160, 60), (x + 2, y - 40, 22, 12))
            pygame.draw.line(self.pantalla, (90, 60, 30), (x, y - 26), (x, y - 38), 4)
        elif t == "pizza":
            pygame.draw.polygon(self.pantalla, (250, 200, 80), [(x - 30, y - 25), (x + 30, y - 25), (x, y + 30)])
            pygame.draw.polygon(self.pantalla, (180, 110, 40), [(x - 30, y - 25), (x + 30, y - 25), (x, y + 30)], 3)
            pygame.draw.circle(self.pantalla, (200, 50, 50), (x - 8, y - 8), 6)
            pygame.draw.circle(self.pantalla, (200, 50, 50), (x + 10, y - 12), 6)
            pygame.draw.circle(self.pantalla, (200, 50, 50), (x, y + 8), 5)
        else:  # helado
            pygame.draw.polygon(self.pantalla, (220, 170, 90), [(x - 16, y), (x + 16, y), (x, y + 38)])
            pygame.draw.circle(self.pantalla, (250, 160, 200), (x, y - 6), 20)
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x - 6, y - 12), 5)

    def dibujar_efectos(self):
        # Burbujas del baño
        for b in self.burbujas:
            pygame.draw.circle(self.pantalla, (255, 255, 255), (int(b["x"]), int(b["y"])), b["r"], 3)
            pygame.draw.circle(
                self.pantalla, (255, 255, 255), (int(b["x"] - b["r"] // 3), int(b["y"] - b["r"] // 3)), 3
            )
        # Corazones
        for c in self.corazones:
            self.dibujar_corazon(int(c["x"]), int(c["y"]), c["vida"])
        # Zzz
        for z in self.zzz:
            txt = self.fuente_grande.render("Z", True, (80, 80, 160))
            txt.set_alpha(int(255 * z["vida"]))
            self.pantalla.blit(txt, (z["x"], z["y"]))

    def dibujar_corazon(self, x, y, vida):
        s = pygame.Surface((30, 30), pygame.SRCALPHA)
        color = (240, 60, 100, int(255 * vida))
        pygame.draw.circle(s, color, (9, 10), 8)
        pygame.draw.circle(s, color, (21, 10), 8)
        pygame.draw.polygon(s, color, [(2, 13), (28, 13), (15, 27)])
        self.pantalla.blit(s, (x, y))

    def dibujar_mensaje(self):
        if self.mensaje_t > 0 and self.mensaje:
            txt = self.fuente.render(self.mensaje, True, COLOR_TEXTO)
            caja = txt.get_rect(center=(ANCHO // 2, 140)).inflate(30, 20)
            pygame.draw.rect(self.pantalla, (255, 255, 255), caja, border_radius=14)
            pygame.draw.rect(self.pantalla, COLOR_TEXTO, caja, 3, border_radius=14)
            self.pantalla.blit(txt, txt.get_rect(center=caja.center))
        else:
            # Pou avisa cuando necesita algo
            necesidad = min(self.estado.valores, key=self.estado.valores.get)
            if self.estado.valores[necesidad] < 25 and self.modo == "normal":
                frases = {
                    "hambre": "Tengo hambre...",
                    "felicidad": "Estoy aburrido...",
                    "energia": "Tengo sueño...",
                    "higiene": "Necesito un baño...",
                }
                txt = self.fuente.render(frases[necesidad], True, (160, 40, 40))
                self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, 140)))

    def dibujar(self):
        if self.escena == "salto":
            mouse = self.a_logico(pygame.mouse.get_pos())
            self.minijuego.dibujar(self.pantalla, mouse)
            self.presentar()
            return
        self.dibujar_fondo()
        self.dibujar_barras()
        self.dibujar_pou()
        self.dibujar_comida()
        self.dibujar_efectos()
        self.dibujar_mensaje()

        mouse = self.a_logico(pygame.mouse.get_pos())
        for b in self.botones:
            b.dibujar(self.pantalla, self.fuente, mouse)

        # De noche: se oscurece la pantalla
        if self.modo == "durmiendo":
            oscuro = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            oscuro.fill((10, 10, 50, 140))
            self.pantalla.blit(oscuro, (0, 0))
            # Los botones y el mensaje se vuelven a dibujar encima para que se lean
            self.dibujar_mensaje()
            for b in self.botones:
                b.dibujar(self.pantalla, self.fuente, mouse)

        self.presentar()

    # ------------------------------------------------------------ eventos
    def acariciar(self):
        if self.modo != "normal":
            return
        self.estado.cambiar("felicidad", 4)
        self.squash_extra = 0.12
        self.nuevo_corazon()

    def manejar_eventos(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if self.escena == "salto":
                pos = self.a_logico(pygame.mouse.get_pos())
                if self.minijuego.manejar_evento(e, pos) == "salir":
                    self.terminar_minijuego()
                continue
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = self.a_logico(e.pos)
                for b in self.botones:
                    if b.rect.collidepoint(pos):
                        b.accion()
                        break
                else:
                    if hasattr(self, "rect_pou") and self.rect_pou.collidepoint(pos):
                        self.acariciar()
        return True

    # ------------------------------------------------------------ bucle principal
    def ejecutar(self):
        corriendo = True
        while corriendo:
            dt = self.reloj.tick(FPS) / 1000
            corriendo = self.manejar_eventos()
            self.actualizar(dt)
            self.dibujar()
        self.estado.guardar()
        pygame.quit()


if __name__ == "__main__":
    Juego().ejecutar()
