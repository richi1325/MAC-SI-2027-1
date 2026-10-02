"""
pip install pygame
python flappy_ga.py
"""

import math
import random
import sys

import pygame

ANCHO, ALTO = 600, 800
FPS = 60
TITULO = "Flappy Bird - Algoritmo Genetico"

GRAVEDAD = 0.65
IMPULSO_SALTO = -10.0
RADIO_PAJARO = 12
X_PAJARO = 110

ANCHO_TUBERIA = 70
HUECO = 190
VELOCIDAD_TUBERIA = 3
DISTANCIA_ENTRE_TUBERIAS = 300
MARGEN_HUECO = 60

ALTO_SUELO = 60
SUELO_Y = ALTO - ALTO_SUELO

POBLACION = 150
PROB_MUTACION = 0.30
FUERZA_MUTACION = 0.30
PAUSA_EVOLUCION = 45
VELOCIDADES = [1, 2, 4, 8]

COLOR_CIELO_TOPE = (70, 150, 226)
COLOR_CIELO_BASE = (198, 232, 252)
COLOR_NUBE = (255, 255, 255)
COLOR_SUELO = (104, 190, 88)
COLOR_SUELO_OSCURO = (74, 150, 66)
COLOR_TIERRA = (226, 192, 142)
COLOR_TIERRA_OSCURO = (200, 164, 114)
COLOR_TUBO_CLARO = (152, 224, 144)
COLOR_TUBO_OSCURO = (56, 148, 72)
COLOR_TUBO_BORDE = (36, 104, 50)
COLOR_PAJARO = (128, 142, 166)
COLOR_PAJARO_BORDE = (84, 96, 118)
COLOR_PAJARO_MUERTO = (198, 205, 216)
COLOR_PICO = (255, 150, 48)
COLOR_LIDER = (255, 178, 54)
COLOR_LIDER_BORDE = (212, 118, 22)
COLOR_VISION = (255, 176, 64)
COLOR_TEXTO = (46, 54, 70)
COLOR_TEXTO_SUAVE = (124, 136, 154)
COLOR_ACENTO = (255, 138, 76)
COLOR_ROJO = (222, 60, 58)
COLOR_PANEL = (250, 252, 255)
COLOR_PANEL_BORDE = (208, 219, 235)
COLOR_CHIP = (238, 243, 250)


def _mezcla(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _aclarar(color, t):
    return _mezcla(color, (255, 255, 255), t)


def _oscurecer(color, t):
    return _mezcla(color, (0, 0, 0), t)


_GRAD_CACHE = {}


def gradiente_horizontal(ancho):
    if ancho in _GRAD_CACHE:
        return _GRAD_CACHE[ancho]
    base = pygame.Surface((ancho, 1))
    for x in range(ancho):
        base.set_at((x, 0), _mezcla(COLOR_TUBO_CLARO, COLOR_TUBO_OSCURO, x / max(1, ancho - 1)))
    _GRAD_CACHE[ancho] = base
    return base


_PAJARO_CACHE = {}


def imagen_pajaro(estado, fase):
    clave = (estado, fase)
    if clave in _PAJARO_CACHE:
        return _PAJARO_CACHE[clave]

    if estado == "lider":
        cuerpo = COLOR_LIDER
        ala = _oscurecer(COLOR_LIDER, 0.20)
        pico = (255, 120, 40)
        borde = COLOR_LIDER_BORDE
        alpha = 255
    elif estado == "muerto":
        cuerpo = COLOR_PAJARO_MUERTO
        ala = _oscurecer(COLOR_PAJARO_MUERTO, 0.12)
        pico = (226, 205, 180)
        borde = (168, 176, 190)
        alpha = 120
    else:
        cuerpo = COLOR_PAJARO
        ala = _oscurecer(COLOR_PAJARO, 0.18)
        pico = COLOR_PICO
        borde = COLOR_PAJARO_BORDE
        alpha = 210

    escala = 4
    R = RADIO_PAJARO * escala
    lado = (RADIO_PAJARO * 2 + 18) * escala
    surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
    cx = cy = lado // 2

    dy_ala = (-3, 0, 3, 0)[fase % 4] * escala
    pygame.draw.ellipse(surf, ala, (cx - R - 2 * escala, cy - 4 * escala + dy_ala, 16 * escala, 11 * escala))
    pygame.draw.circle(surf, cuerpo, (cx, cy), R)
    pygame.draw.circle(surf, _aclarar(cuerpo, 0.24), (cx - 3 * escala, cy + 4 * escala), int((RADIO_PAJARO - 5) * escala))
    pygame.draw.polygon(surf, pico, [
        (cx + R - 2 * escala, cy - 2 * escala),
        (cx + R + 7 * escala, cy + 1 * escala),
        (cx + R - 2 * escala, cy + 5 * escala),
    ])
    pygame.draw.circle(surf, (255, 255, 255), (cx + 4 * escala, cy - 4 * escala), 4 * escala)
    pygame.draw.circle(surf, (35, 38, 48), (cx + 5 * escala, cy - 4 * escala), 2 * escala)
    pygame.draw.circle(surf, borde, (cx, cy), R, escala + 1)

    img = pygame.transform.smoothscale(surf, (lado // escala, lado // escala))
    if alpha < 255:
        img.set_alpha(alpha)
    _PAJARO_CACHE[clave] = img
    return img


_GLOW = None


def imagen_glow():
    global _GLOW
    if _GLOW is not None:
        return _GLOW
    lado = (RADIO_PAJARO + 16) * 2
    surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
    c = lado // 2
    for i in range(8, 0, -1):
        pygame.draw.circle(surf, (255, 200, 80, int(72 * (9 - i) / 8)), (c, c), RADIO_PAJARO + i * 2)
    _GLOW = surf
    return surf


def _crear_nube(escala):
    w, h = int(170 * escala), int(72 * escala)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for px, py, pr in ((0.20, 0.62, 0.17), (0.42, 0.42, 0.23), (0.64, 0.50, 0.21), (0.82, 0.66, 0.14)):
        pygame.draw.circle(surf, COLOR_NUBE, (int(px * w), int(py * h)), int(pr * w))
    surf.set_alpha(150)
    return surf


class Bird:
    def __init__(self, genes=None):
        self.x = X_PAJARO
        self.y = ALTO / 2.0
        self.vy = 0.0
        self.vivo = True
        self.fitness = 0
        self.puntaje = 0
        if genes is None:
            self.genes = [random.uniform(-1.0, 1.0) for _ in range(3)]
        else:
            self.genes = list(genes)

    @property
    def peso_dx(self):
        return self.genes[0]

    @property
    def peso_dy(self):
        return self.genes[1]

    @property
    def sesgo(self):
        return self.genes[2]

    def saltar(self):
        self.vy = IMPULSO_SALTO

    def pensar(self, dx, dy):
        salida = (dx * self.peso_dx) + (dy * self.peso_dy) + self.sesgo
        return salida > 0

    def aplicar_fisica(self):
        if not self.vivo:
            return
        self.vy += GRAVEDAD
        self.y += self.vy

    def rect(self):
        return pygame.Rect(
            int(self.x - RADIO_PAJARO),
            int(self.y - RADIO_PAJARO),
            RADIO_PAJARO * 2,
            RADIO_PAJARO * 2,
        )

    def colisiona(self, tuberias):
        if self.y - RADIO_PAJARO <= 0:
            return True
        if self.y + RADIO_PAJARO >= SUELO_Y:
            return True
        cuerpo = self.rect()
        for tuberia in tuberias:
            if cuerpo.colliderect(tuberia.rect_sup) or cuerpo.colliderect(tuberia.rect_inf):
                return True
        return False

    def dibujar(self, superficie, es_lider=False, t=0):
        if not self.vivo:
            estado = "muerto"
        elif es_lider:
            estado = "lider"
        else:
            estado = "normal"
        fase = int(t * 0.3) % 4 if self.vivo else 0
        img = imagen_pajaro(estado, fase)
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        if es_lider and self.vivo:
            glow = imagen_glow()
            superficie.blit(glow, glow.get_rect(center=rect.center))
        superficie.blit(img, rect)


class Pipe:
    def __init__(self, x):
        self.x = x
        self.ancho = ANCHO_TUBERIA
        self.hueco = HUECO
        minimo = MARGEN_HUECO
        maximo = SUELO_Y - MARGEN_HUECO - self.hueco
        self.gap_y = random.randint(minimo, maximo)
        self.contada = False
        self.rect_sup = pygame.Rect(self.x, 0, self.ancho, self.gap_y)
        self.rect_inf = pygame.Rect(
            self.x,
            self.gap_y + self.hueco,
            self.ancho,
            ALTO - (self.gap_y + self.hueco),
        )

    @property
    def centro_hueco(self):
        return self.gap_y + self.hueco / 2.0

    def actualizar(self):
        self.x -= VELOCIDAD_TUBERIA
        self.rect_sup.x = self.x
        self.rect_inf.x = self.x

    def fuera_de_pantalla(self):
        return self.x + self.ancho < 0

    def dibujar(self, superficie):
        for rect in (self.rect_sup, self.rect_inf):
            grad = pygame.transform.scale(gradiente_horizontal(self.ancho), (rect.w, rect.h))
            superficie.blit(grad, rect.topleft)
            pygame.draw.rect(superficie, COLOR_TUBO_BORDE, rect, width=3, border_radius=5)

        cap_w = self.ancho + 16
        cap_h = 26
        cap_x = self.x - 8
        for cap in (pygame.Rect(cap_x, self.gap_y - cap_h, cap_w, cap_h),
                    pygame.Rect(cap_x, self.gap_y + self.hueco, cap_w, cap_h)):
            grad = pygame.transform.scale(gradiente_horizontal(cap_w), (cap.w, cap.h))
            superficie.blit(grad, cap.topleft)
            pygame.draw.rect(superficie, COLOR_TUBO_BORDE, cap, width=3, border_radius=8)


class Game:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption(TITULO)
        self.reloj = pygame.time.Clock()
        self.fuente_titulo = pygame.font.SysFont("verdana,arial,dejavusans", 15, bold=True)
        self.fuente = pygame.font.SysFont("verdana,arial,dejavusans", 12)
        self.fuente_pequena = pygame.font.SysFont("verdana,arial,dejavusans", 11)
        self.fuente_grande = pygame.font.SysFont("verdana,arial,dejavusans", 40, bold=True)

        self.generacion = 0
        self.fitness_max_historico = 0
        self.pipes_max_historico = 0
        self.mejor_genotipo = [0.0, 0.0, 0.0]
        self.pausa = 0
        self.velocidad = 1
        self.boton_velocidad = pygame.Rect(ANCHO - 170, 16, 156, 38)
        self.mouse_pos = (-1, -1)
        self.frames = 0
        self.cielo = None
        self.nubes = None
        self.capa_vision = None
        self._gen_banner = -1
        self.banner_timer = 90

        # ---------- POBLACION INICIAL ----------
        self.pajaros = [Bird() for _ in range(POBLACION)]
        self.tuberias = []
        self.reiniciar()

    def reiniciar(self):
        self.tuberias = [Pipe(ANCHO)]
        self.pausa = 0

    ##################################################################
    ###################    ALGORITMO GENETICO    #####################
    ##################################################################
    def evolucionar(self):
        self.pajaros.sort(key=lambda p: p.fitness, reverse=True)
        self.fitness_max_historico = max(self.fitness_max_historico, self.pajaros[0].fitness)
        self.mejor_genotipo = list(self.pajaros[0].genes)
        self.generacion += 1

        # -------------------- SELECCION POR RULETA --------------------
        suma_aptitud = sum(p.fitness for p in self.pajaros)
        seleccionados = [self.seleccion_ruleta(suma_aptitud) for _ in range(POBLACION)]

        # ---------------------- CRUZA DE UN PUNTO ---------------------
        nueva_poblacion = []
        for i in range(0, POBLACION, 2):
            padre1 = seleccionados[i]
            padre2 = seleccionados[(i + 1) % POBLACION]
            hijo1, hijo2 = self.cruzar(padre1, padre2)

            # -------------------------- MUTACION --------------------------
            self.mutar(hijo1)
            self.mutar(hijo2)

            nueva_poblacion.append(Bird(hijo1))
            if len(nueva_poblacion) < POBLACION:
                nueva_poblacion.append(Bird(hijo2))

        self.pajaros = nueva_poblacion
        self.reiniciar()

    def seleccion_ruleta(self, suma_aptitud):
        if suma_aptitud <= 0:
            return random.choice(self.pajaros)
        giro = random.uniform(0.0, suma_aptitud)
        acumulado = 0.0
        for pajaro in self.pajaros:
            acumulado += pajaro.fitness
            if acumulado >= giro:
                return pajaro
        return self.pajaros[-1]

    def cruzar(self, padre1, padre2):
        punto = random.randint(1, len(padre1.genes) - 1)
        genes_hijo1 = padre1.genes[:punto] + padre2.genes[punto:]
        genes_hijo2 = padre2.genes[:punto] + padre1.genes[punto:]
        return genes_hijo1, genes_hijo2

    def mutar(self, genes):
        for i in range(len(genes)):
            if random.random() < PROB_MUTACION:
                genes[i] += random.uniform(-FUERZA_MUTACION, FUERZA_MUTACION)
        return genes
    ##################################################################

    def todos_muertos(self):
        return all(not p.vivo for p in self.pajaros)

    def siguiente_tuberia(self):
        for tuberia in self.tuberias:
            if tuberia.x + tuberia.ancho > X_PAJARO:
                return tuberia
        return None

    def actualizar(self):
        for _ in range(self.velocidad):
            self.paso()

    def paso(self):
        if self.pausa > 0:
            self.pausa -= 1
            if self.pausa == 0:
                self.evolucionar()
            return

        for tuberia in self.tuberias:
            tuberia.actualizar()
        self.tuberias = [t for t in self.tuberias if not t.fuera_de_pantalla()]

        if self.tuberias[-1].x <= ANCHO - DISTANCIA_ENTRE_TUBERIAS:
            self.tuberias.append(Pipe(ANCHO))

        for tuberia in self.tuberias:
            if not tuberia.contada and tuberia.x + tuberia.ancho < X_PAJARO:
                tuberia.contada = True
                for pajaro in self.pajaros:
                    if pajaro.vivo:
                        pajaro.puntaje += 1

        objetivo = self.siguiente_tuberia()
        for pajaro in self.pajaros:
            if not pajaro.vivo:
                continue

            if objetivo is not None:
                dx = objetivo.x - pajaro.x
                dy = pajaro.y - objetivo.centro_hueco
                if pajaro.pensar(dx, dy):
                    pajaro.saltar()

            pajaro.aplicar_fisica()

            # --------------------- APTITUD: frames vivos --------------------
            pajaro.fitness += 1

            if pajaro.colisiona(self.tuberias):
                pajaro.vivo = False

        if self.todos_muertos():
            self.pausa = PAUSA_EVOLUCION

    def preparar_fondo(self):
        self.cielo = pygame.Surface((ANCHO, ALTO))
        for y in range(ALTO):
            self.cielo.fill(_mezcla(COLOR_CIELO_TOPE, COLOR_CIELO_BASE, y / (ALTO - 1)), (0, y, ANCHO, 1))
        self.nubes = []
        for _ in range(6):
            img = _crear_nube(random.uniform(0.5, 1.1))
            self.nubes.append([random.uniform(0, ANCHO), random.uniform(30, 320), img, random.uniform(0.15, 0.55)])

    def dibujar_fondo(self):
        if self.cielo is None:
            self.preparar_fondo()
        self.pantalla.blit(self.cielo, (0, 0))
        for nube in self.nubes:
            nube[0] -= nube[3]
            if nube[0] < -nube[2].get_width():
                nube[0] = ANCHO + random.uniform(0, 200)
                nube[1] = random.uniform(30, 320)
            self.pantalla.blit(nube[2], (int(nube[0]), int(nube[1])))

    def dibujar_suelo(self):
        pygame.draw.rect(self.pantalla, COLOR_TIERRA, (0, SUELO_Y + 14, ANCHO, ALTO - SUELO_Y - 14))
        pygame.draw.rect(self.pantalla, COLOR_SUELO, (0, SUELO_Y, ANCHO, 14))
        pygame.draw.rect(self.pantalla, COLOR_SUELO_OSCURO, (0, SUELO_Y + 11, ANCHO, 3))
        pygame.draw.rect(self.pantalla, COLOR_TIERRA_OSCURO, (0, SUELO_Y + 14, ANCHO, 4))
        offset = (self.frames * VELOCIDAD_TUBERIA) % 28
        for x in range(-28, ANCHO + 28, 28):
            base_x = x - offset
            pygame.draw.polygon(self.pantalla, COLOR_SUELO_OSCURO, [
                (base_x, SUELO_Y + 2), (base_x + 6, SUELO_Y - 5), (base_x + 12, SUELO_Y + 2)
            ])
            pygame.draw.circle(self.pantalla, COLOR_TIERRA_OSCURO, (base_x + 14, SUELO_Y + 34), 3)

    def dibujar_vision(self, lider, objetivo):
        if lider is None or objetivo is None:
            return
        if self.capa_vision is None:
            self.capa_vision = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.capa_vision.fill((0, 0, 0, 0))
        origen = (int(lider.x), int(lider.y))
        pygame.draw.line(self.capa_vision, (*COLOR_VISION, 110), origen,
                         (int(objetivo.x), int(lider.y)), 2)
        pygame.draw.line(self.capa_vision, (*COLOR_VISION, 110), origen,
                         (int(objetivo.x), int(objetivo.centro_hueco)), 2)
        pygame.draw.circle(self.capa_vision, (*COLOR_VISION, 160),
                           (int(objetivo.x), int(objetivo.centro_hueco)), 7, 2)
        self.pantalla.blit(self.capa_vision, (0, 0))

    def dibujar_hud(self):
        vivos = sum(1 for p in self.pajaros if p.vivo)
        mejor_actual = max(self.pajaros, key=lambda p: p.fitness)
        max_puntaje = max(p.puntaje for p in self.pajaros)
        self.pipes_max_historico = max(self.pipes_max_historico, max_puntaje)

        filas = [
            ("Gen", str(self.generacion), COLOR_TEXTO),
            ("Vivos", f"{vivos} / {POBLACION}", COLOR_TEXTO),
            ("Record", str(self.fitness_max_historico), COLOR_TEXTO),
            ("Aptitud", str(mejor_actual.fitness), COLOR_TEXTO),
            ("Tuberias max", str(self.pipes_max_historico), COLOR_ROJO),
        ]

        pad = 12
        ancho_panel = 224
        alto_titulo = 26
        alto_fila = 21
        alto_panel = pad * 2 + alto_titulo + len(filas) * alto_fila + 46

        panel = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*COLOR_PANEL, 234), (0, 0, ancho_panel, alto_panel), border_radius=16)
        pygame.draw.rect(panel, (*COLOR_PANEL_BORDE, 255), (0, 0, ancho_panel, alto_panel), width=2, border_radius=16)

        panel.blit(self.fuente_titulo.render("FLAPPY", True, COLOR_TEXTO), (pad, pad - 2))
        acento = self.fuente_titulo.render("GA", True, COLOR_ACENTO)
        panel.blit(acento, (pad + self.fuente_titulo.size("FLAPPY")[0] + 6, pad - 2))
        pygame.draw.line(panel, (*COLOR_PANEL_BORDE, 255),
                         (pad, pad + alto_titulo - 8), (ancho_panel - pad, pad + alto_titulo - 8), 1)

        y = pad + alto_titulo
        for etiqueta, valor, color in filas:
            panel.blit(self.fuente.render(etiqueta, True, COLOR_TEXTO_SUAVE), (pad, y))
            der = self.fuente.render(valor, True, color)
            panel.blit(der, (ancho_panel - pad - der.get_width(), y))
            y += alto_fila

        y += 4
        panel.blit(self.fuente_pequena.render("Mejor genotipo", True, COLOR_ACENTO), (pad, y))
        y += 18
        genes = [("dx", mejor_actual.genes[0]), ("dy", mejor_actual.genes[1]), ("b", mejor_actual.genes[2])]
        hueco = 6
        ancho_chip = (ancho_panel - pad * 2 - hueco * 2) // 3
        for i, (nombre, valor) in enumerate(genes):
            chip = pygame.Rect(pad + i * (ancho_chip + hueco), y, ancho_chip, 22)
            pygame.draw.rect(panel, (*COLOR_CHIP, 255), chip, border_radius=7)
            pygame.draw.rect(panel, (*COLOR_PANEL_BORDE, 255), chip, width=1, border_radius=7)
            txt = self.fuente_pequena.render(f"{nombre} {valor:+.2f}", True, COLOR_TEXTO)
            panel.blit(txt, txt.get_rect(center=chip.center))

        self.pantalla.blit(panel, (ANCHO - 14 - ancho_panel, SUELO_Y - 12 - alto_panel))

    def dibujar_boton_velocidad(self):
        hover = self.boton_velocidad.collidepoint(self.mouse_pos)
        fondo = (92, 158, 236) if hover else (74, 144, 226)
        pygame.draw.rect(self.pantalla, fondo, self.boton_velocidad, border_radius=19)
        pygame.draw.rect(self.pantalla, (44, 104, 176), self.boton_velocidad, width=2, border_radius=19)
        etiqueta = self.fuente.render(f"Velocidad   x{self.velocidad}", True, (255, 255, 255))
        self.pantalla.blit(etiqueta, etiqueta.get_rect(center=self.boton_velocidad.center))
        pista = self.fuente_pequena.render("clic / teclas 1-4", True, (235, 242, 252))
        self.pantalla.blit(pista, (self.boton_velocidad.x + 4, self.boton_velocidad.bottom + 5))

    def dibujar_banner(self):
        if self.banner_timer <= 0:
            return
        alpha = min(255, self.banner_timer * 7)
        texto = self.fuente_grande.render(f"GENERACION  {self._gen_banner}", True, (255, 255, 255))
        w = texto.get_width() + 90
        h = texto.get_height() + 44
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (44, 54, 74, 210), (0, 0, w, h), border_radius=22)
        surf.blit(texto, texto.get_rect(center=(w // 2, h // 2)))
        surf.set_alpha(alpha)
        self.pantalla.blit(surf, (ANCHO // 2 - w // 2, ALTO // 2 - h // 2 - 60))

    def cambiar_velocidad(self):
        i = VELOCIDADES.index(self.velocidad)
        self.velocidad = VELOCIDADES[(i + 1) % len(VELOCIDADES)]

    def dibujar(self):
        self.frames += 1
        if self.generacion != self._gen_banner:
            self._gen_banner = self.generacion
            self.banner_timer = 90
        if self.banner_timer > 0:
            self.banner_timer -= 1

        self.dibujar_fondo()

        for tuberia in self.tuberias:
            tuberia.dibujar(self.pantalla)

        self.dibujar_suelo()

        vivos = [p for p in self.pajaros if p.vivo]
        lider = max(vivos, key=lambda p: p.fitness) if vivos else None

        self.dibujar_vision(lider, self.siguiente_tuberia())

        for pajaro in self.pajaros:
            if not pajaro.vivo:
                pajaro.dibujar(self.pantalla, t=self.frames)
        for pajaro in self.pajaros:
            if pajaro.vivo and pajaro is not lider:
                pajaro.dibujar(self.pantalla, t=self.frames)
        if lider is not None:
            lider.dibujar(self.pantalla, es_lider=True, t=self.frames)

        self.dibujar_hud()
        self.dibujar_boton_velocidad()
        self.dibujar_banner()

        pygame.display.flip()

    def ejecutar(self):
        ejecutando = True
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        ejecutando = False
                    elif evento.key == pygame.K_r:
                        self.generacion = 0
                        self.fitness_max_historico = 0
                        self.pipes_max_historico = 0
                        self.mejor_genotipo = [0.0, 0.0, 0.0]
                        self.pajaros = [Bird() for _ in range(POBLACION)]
                        self.reiniciar()
                    elif evento.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        self.velocidad = VELOCIDADES[evento.key - pygame.K_1]
                elif evento.type == pygame.MOUSEMOTION:
                    self.mouse_pos = evento.pos
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.boton_velocidad.collidepoint(evento.pos):
                        self.cambiar_velocidad()

            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().ejecutar()
