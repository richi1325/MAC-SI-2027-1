"""
pip install pygame
python lunar_lander_ga.py
"""

import math
import random
import sys

import pygame

ANCHO, ALTO = 800, 600
FPS = 60
TITULO = "Lunar Lander - Algoritmo Genetico"

GRAVEDAD = 0.12
EMPUJE_PRINCIPAL = 0.30
EMPUJE_LATERAL = 0.10
VEL_MAX = 6.0

ALTO_SUELO = 40
SUELO_Y = ALTO - ALTO_SUELO
ANCHO_PLATAFORMA = 160

NAVE_ANCHO = 20
NAVE_ALTO = 22

POBLACION = 100
PROB_MUTACION = 0.10
FUERZA_MUTACION = 0.30
PAUSA_EVOLUCION = 45
MAX_TIEMPO = 900
VELOCIDADES = [1, 2, 4, 8]

N_ENTRADAS = 5
N_SALIDAS = 3
N_GENES = N_SALIDAS * (N_ENTRADAS + 1)

K_VELOCIDAD = 25.0
P_TIEMPO = 0.05
BONUS_LANDEO = 800.0
PEN_CRASH = 500.0
PEN_LIMITE = 500.0
PEN_TIMEOUT = 400.0
V_LIMITE = 2.0
VX_LIMITE = 1.5

COLOR_CIELO = (12, 14, 30)
COLOR_ESTRELLA = (220, 220, 240)
COLOR_SUELO = (70, 70, 85)
COLOR_SUELO_BORDE = (110, 110, 130)
COLOR_PLATAFORMA = (60, 190, 110)
COLOR_PLATAFORMA_BORDE = (30, 120, 70)
COLOR_NAVE = (170, 175, 190)
COLOR_NAVE_MUERTA = (70, 70, 85)
COLOR_LIDER = (230, 80, 80)
COLOR_LLAMA = (255, 170, 40)
COLOR_TEXTO = (235, 235, 245)
COLOR_PANEL = (22, 26, 44)
COLOR_PANEL_BORDE = (74, 86, 118)
COLOR_TEXTO_SUAVE = (150, 160, 185)
COLOR_CHIP = (36, 42, 66)
COLOR_ACENTO = (255, 176, 64)
COLOR_VISION = (255, 200, 60)


class Lander:
    def __init__(self, genes=None):
        if genes is None:
            self.genes = [random.uniform(-1.0, 1.0) for _ in range(N_GENES)]
        else:
            self.genes = list(genes)
        self.reiniciar(0.0, 0.0, 0.0, 0.0)

    def reiniciar(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.vivo = True
        self.aterrizo = False
        self.fitness = 0.0
        self.prop = [False, False, False]
        self.potencial_prev = None

    def entradas(self, plataforma_x):
        return [
            self.x / ANCHO,
            self.y / ALTO,
            self.vx / VEL_MAX,
            self.vy / VEL_MAX,
            plataforma_x / ANCHO,
        ]

    def propulsores(self, entradas):
        salidas = []
        k = 0
        for _ in range(N_SALIDAS):
            suma = 0.0
            for i in range(N_ENTRADAS):
                suma += self.genes[k] * entradas[i]
                k += 1
            suma += self.genes[k]
            k += 1
            salidas.append(suma > 0)
        return salidas

    def aplicar_fisica(self, prop):
        self.vy += GRAVEDAD
        if prop[0]:
            self.vy -= EMPUJE_PRINCIPAL
        if prop[1]:
            self.vx -= EMPUJE_LATERAL
        if prop[2]:
            self.vx += EMPUJE_LATERAL
        self.vx = max(-VEL_MAX, min(VEL_MAX, self.vx))
        self.vy = max(-VEL_MAX, min(VEL_MAX, self.vy))
        self.x += self.vx
        self.y += self.vy

    def dibujar(self, superficie, es_lider=False):
        if not self.vivo:
            color = COLOR_NAVE_MUERTA
        elif es_lider:
            color = COLOR_LIDER
        else:
            color = COLOR_NAVE

        x, y = int(self.x), int(self.y)
        cuerpo = [
            (x, y - NAVE_ALTO / 2),
            (x - NAVE_ANCHO / 2, y + NAVE_ALTO / 2),
            (x + NAVE_ANCHO / 2, y + NAVE_ALTO / 2),
        ]
        pygame.draw.polygon(superficie, color, cuerpo)
        pygame.draw.line(superficie, color, (x - NAVE_ANCHO / 2, y + NAVE_ALTO / 2),
                         (x - NAVE_ANCHO / 2, y + NAVE_ALTO / 2 + 5), 2)
        pygame.draw.line(superficie, color, (x + NAVE_ANCHO / 2, y + NAVE_ALTO / 2),
                         (x + NAVE_ANCHO / 2, y + NAVE_ALTO / 2 + 5), 2)

        if self.vivo and self.prop[0]:
            pygame.draw.polygon(superficie, COLOR_LLAMA, [
                (x - 6, y + NAVE_ALTO / 2),
                (x + 6, y + NAVE_ALTO / 2),
                (x, y + NAVE_ALTO / 2 + 14),
            ])
        if self.vivo and self.prop[1]:
            pygame.draw.polygon(superficie, COLOR_LLAMA, [
                (x - NAVE_ANCHO / 2, y),
                (x - NAVE_ANCHO / 2, y + 6),
                (x - NAVE_ANCHO / 2 - 12, y + 3),
            ])
        if self.vivo and self.prop[2]:
            pygame.draw.polygon(superficie, COLOR_LLAMA, [
                (x + NAVE_ANCHO / 2, y),
                (x + NAVE_ANCHO / 2, y + 6),
                (x + NAVE_ANCHO / 2 + 12, y + 3),
            ])


class Game:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption(TITULO)
        self.reloj = pygame.time.Clock()
        self.fuente_titulo = pygame.font.SysFont("verdana,arial,dejavusans", 14, bold=True)
        self.fuente = pygame.font.SysFont("verdana,arial,dejavusans", 12)
        self.fuente_mono = pygame.font.SysFont("consolas,dejavusansmono", 11)

        self.generacion = 0
        self.fitness_max_historico = 0.0
        self.mejor_genotipo = [0.0] * N_GENES
        self.pausa = 0
        self.tiempo = 0
        self.velocidad = 1
        self.boton_velocidad = pygame.Rect(ANCHO - 170, 16, 156, 38)
        self.mouse_pos = (-1, -1)

        self.estrellas = [(random.randint(0, ANCHO), random.randint(0, SUELO_Y))
                          for _ in range(90)]

        # ---------- POBLACION INICIAL ----------
        self.naves = [Lander() for _ in range(POBLACION)]
        self.reiniciar()

    def reiniciar(self):
        self.plataforma_x = random.uniform(140, ANCHO - 140)
        self.inicio_x = random.uniform(160, ANCHO - 160)
        self.inicio_y = 70.0
        self.inicio_vx = random.uniform(-1.5, 1.5)
        self.inicio_vy = random.uniform(0.0, 0.5)
        self.tiempo = 0
        self.pausa = 0
        for nave in self.naves:
            nave.reiniciar(self.inicio_x, self.inicio_y, self.inicio_vx, self.inicio_vy)

    ##################################################################
    ###################    ALGORITMO GENETICO    #####################
    ##################################################################
    def evolucionar(self):
        self.naves.sort(key=lambda n: n.fitness, reverse=True)
        self.fitness_max_historico = max(self.fitness_max_historico, self.naves[0].fitness)
        self.mejor_genotipo = list(self.naves[0].genes)
        self.generacion += 1

        # -------------------- SELECCION POR RULETA --------------------
        minimo = min(n.fitness for n in self.naves)
        seleccionados = [self.seleccion_ruleta(minimo) for _ in range(POBLACION)]

        # ---------------------- CRUZA DE UN PUNTO ---------------------
        nueva_poblacion = []
        for i in range(0, POBLACION, 2):
            padre1 = seleccionados[i]
            padre2 = seleccionados[(i + 1) % POBLACION]
            hijo1, hijo2 = self.cruzar(padre1, padre2)

            # -------------------------- MUTACION --------------------------
            self.mutar(hijo1)
            self.mutar(hijo2)

            nueva_poblacion.append(Lander(hijo1))
            if len(nueva_poblacion) < POBLACION:
                nueva_poblacion.append(Lander(hijo2))

        self.naves = nueva_poblacion
        self.reiniciar()

    def seleccion_ruleta(self, minimo):
        epsilon = 1e-6
        total = sum(n.fitness - minimo + epsilon for n in self.naves)
        giro = random.uniform(0.0, total)
        acumulado = 0.0
        for nave in self.naves:
            acumulado += nave.fitness - minimo + epsilon
            if acumulado >= giro:
                return nave
        return self.naves[-1]

    def cruzar(self, padre1, padre2):
        punto = random.randint(1, N_GENES - 1)
        hijo1 = padre1.genes[:punto] + padre2.genes[punto:]
        hijo2 = padre2.genes[:punto] + padre1.genes[punto:]
        return hijo1, hijo2

    def mutar(self, genes):
        for i in range(len(genes)):
            if random.random() < PROB_MUTACION:
                genes[i] += random.uniform(-FUERZA_MUTACION, FUERZA_MUTACION)
        return genes
    ##################################################################

    def todos_muertos(self):
        return all(not n.vivo for n in self.naves)

    def potencial(self, nave):
        dx = nave.x - self.plataforma_x
        dy = nave.y - SUELO_Y
        distancia = math.hypot(dx, dy)
        velocidad = math.hypot(nave.vx, nave.vy)
        return -(distancia + K_VELOCIDAD * velocidad)

    def revisar_estado(self, nave):
        if nave.x < -40 or nave.x > ANCHO + 40 or nave.y < -80:
            nave.fitness -= PEN_LIMITE
            nave.vivo = False
            return

        if nave.y + NAVE_ALTO / 2 >= SUELO_Y:
            en_plataforma = abs(nave.x - self.plataforma_x) <= ANCHO_PLATAFORMA / 2
            suave = abs(nave.vy) <= V_LIMITE and abs(nave.vx) <= VX_LIMITE
            if en_plataforma and suave:
                centro = 1.0 - abs(nave.x - self.plataforma_x) / (ANCHO_PLATAFORMA / 2)
                calidad = max(0.0, centro) * (1.0 - abs(nave.vy) / V_LIMITE)
                nave.fitness += BONUS_LANDEO * (0.5 + calidad)
                nave.aterrizo = True
            else:
                nave.fitness -= PEN_CRASH
            nave.vivo = False

    def actualizar(self):
        for _ in range(self.velocidad):
            self.paso()

    def paso(self):
        if self.pausa > 0:
            self.pausa -= 1
            if self.pausa == 0:
                self.evolucionar()
            return

        self.tiempo += 1
        for nave in self.naves:
            if not nave.vivo:
                continue

            entradas = nave.entradas(self.plataforma_x)
            nave.prop = nave.propulsores(entradas)
            nave.aplicar_fisica(nave.prop)

            # --------------------------- APTITUD --------------------------
            pot = self.potencial(nave)
            if nave.potencial_prev is None:
                nave.potencial_prev = pot
            nave.fitness += (pot - nave.potencial_prev) - P_TIEMPO
            nave.potencial_prev = pot

            self.revisar_estado(nave)

        if self.tiempo >= MAX_TIEMPO:
            for nave in self.naves:
                if nave.vivo:
                    nave.fitness -= PEN_TIMEOUT
                    nave.vivo = False
            self.pausa = PAUSA_EVOLUCION
        elif self.todos_muertos():
            self.pausa = PAUSA_EVOLUCION

    def dibujar_fondo(self):
        self.pantalla.fill(COLOR_CIELO)
        for ex, ey in self.estrellas:
            self.pantalla.set_at((ex, ey), COLOR_ESTRELLA)
        pygame.draw.rect(self.pantalla, COLOR_SUELO, (0, SUELO_Y, ANCHO, ALTO_SUELO))
        pygame.draw.rect(self.pantalla, COLOR_SUELO_BORDE, (0, SUELO_Y, ANCHO, 3))

    def dibujar_plataforma(self):
        x = int(self.plataforma_x - ANCHO_PLATAFORMA / 2)
        rect = pygame.Rect(x, SUELO_Y - 6, ANCHO_PLATAFORMA, 8)
        pygame.draw.rect(self.pantalla, COLOR_PLATAFORMA, rect, border_radius=3)
        pygame.draw.rect(self.pantalla, COLOR_PLATAFORMA_BORDE, rect, width=2, border_radius=3)

    def dibujar_vision(self, lider):
        if lider is None:
            return
        pygame.draw.line(self.pantalla, COLOR_VISION,
                         (int(lider.x), int(lider.y)),
                         (int(self.plataforma_x), SUELO_Y), 1)

    def dibujar_hud(self):
        vivas = sum(1 for n in self.naves if n.vivo)
        aterrizaron = sum(1 for n in self.naves if n.aterrizo)
        mejor_actual = max(self.naves, key=lambda n: n.fitness)

        filas = [
            ("Gen", str(self.generacion)),
            ("Vivas", f"{vivas} / {POBLACION}"),
            ("Aterrizajes", str(aterrizaron)),
            ("Record", f"{self.fitness_max_historico:.1f}"),
            ("Aptitud", f"{mejor_actual.fitness:.1f}"),
        ]

        pad = 12
        ancho_panel = 300
        alto_titulo = 26
        alto_fila = 20
        alto_panel = pad * 2 + alto_titulo + len(filas) * alto_fila + 72

        panel = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*COLOR_PANEL, 225), (0, 0, ancho_panel, alto_panel), border_radius=16)
        pygame.draw.rect(panel, (*COLOR_PANEL_BORDE, 255), (0, 0, ancho_panel, alto_panel), width=2, border_radius=16)

        panel.blit(self.fuente_titulo.render("LUNAR", True, COLOR_TEXTO), (pad, pad - 2))
        acento = self.fuente_titulo.render("GA", True, COLOR_ACENTO)
        panel.blit(acento, (pad + self.fuente_titulo.size("LUNAR")[0] + 6, pad - 2))
        pygame.draw.line(panel, (*COLOR_PANEL_BORDE, 255),
                         (pad, pad + alto_titulo - 8), (ancho_panel - pad, pad + alto_titulo - 8), 1)

        y = pad + alto_titulo
        for etiqueta, valor in filas:
            panel.blit(self.fuente.render(etiqueta, True, COLOR_TEXTO_SUAVE), (pad, y))
            der = self.fuente.render(valor, True, COLOR_TEXTO)
            panel.blit(der, (ancho_panel - pad - der.get_width(), y))
            y += alto_fila

        y += 4
        panel.blit(self.fuente.render("Mejor genoma", True, COLOR_ACENTO), (pad, y))
        y += 18
        nombres = ["motor", "izq", "der"]
        k = 0
        for j in range(N_SALIDAS):
            fila = " ".join(f"{mejor_actual.genes[k + i]:+.1f}" for i in range(N_ENTRADAS))
            sesgo = mejor_actual.genes[k + N_ENTRADAS]
            texto = f"{nombres[j]:<5}{fila}  b{sesgo:+.1f}"
            panel.blit(self.fuente_mono.render(texto, True, COLOR_TEXTO), (pad, y))
            y += 16
            k += N_ENTRADAS + 1

        self.pantalla.blit(panel, (ANCHO - 14 - ancho_panel, SUELO_Y - 10 - alto_panel))

    def dibujar_boton_velocidad(self):
        hover = self.boton_velocidad.collidepoint(self.mouse_pos)
        fondo = (92, 158, 236) if hover else (74, 144, 226)
        pygame.draw.rect(self.pantalla, fondo, self.boton_velocidad, border_radius=19)
        pygame.draw.rect(self.pantalla, (44, 104, 176), self.boton_velocidad, width=2, border_radius=19)
        etiqueta = self.fuente.render(f"Velocidad   x{self.velocidad}", True, (255, 255, 255))
        self.pantalla.blit(etiqueta, etiqueta.get_rect(center=self.boton_velocidad.center))
        pista = self.fuente.render("clic / teclas 1-4", True, (235, 242, 252))
        self.pantalla.blit(pista, (self.boton_velocidad.x + 4, self.boton_velocidad.bottom + 5))

    def cambiar_velocidad(self):
        i = VELOCIDADES.index(self.velocidad)
        self.velocidad = VELOCIDADES[(i + 1) % len(VELOCIDADES)]

    def dibujar(self):
        self.dibujar_fondo()
        self.dibujar_plataforma()

        vivas = [n for n in self.naves if n.vivo]
        lider = max(vivas, key=lambda n: n.fitness) if vivas else None
        self.dibujar_vision(lider)

        for nave in self.naves:
            if not nave.vivo:
                nave.dibujar(self.pantalla)
        for nave in self.naves:
            if nave.vivo and nave is not lider:
                nave.dibujar(self.pantalla)
        if lider is not None:
            lider.dibujar(self.pantalla, es_lider=True)

        self.dibujar_hud()
        self.dibujar_boton_velocidad()
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
                        self.fitness_max_historico = 0.0
                        self.mejor_genotipo = [0.0] * N_GENES
                        self.naves = [Lander() for _ in range(POBLACION)]
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
