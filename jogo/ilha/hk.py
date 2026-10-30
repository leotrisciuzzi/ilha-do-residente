"""Peças inspiradas no Hollow Knight, usadas por game.Jogo.

- Capa: um cachecol de verdade, feito de pontos ligados (verlet), preso ao pescoço e levado pelo vento do movimento.
- Rastro do dash: cópias escuras do herói que somem (a "sombra" do dash).
- Sombra: ao morrer, as moedas da fase ficam com uma sombra no lugar onde você caiu; encoste nela para recuperar.
  Morrer de novo antes disso apaga a sombra antiga (como no jogo original).
- Alma: enche ao bater em bichos e ao acertar questões; segurar ↓ parado no chão gasta 1/3 dela para ganhar uma vida
  (o "foco").
Tudo em pixel art na resolução do mundo; nada usa NumPy."""
import math
import random

import pygame

from . import art, heroi

ALMA_MAX, ALMA_FOCO, FOCO_QUADROS = 99, 33, 48
ALMA_GOLPE, ALMA_QUESTAO = 11, 33
DASH_QUADROS, DASH_VEL, DASH_ESPERA = 9, 5.2, 26


class Capa:
    """Cachecol de N pontos: o primeiro fica preso ao pescoço; os outros seguem com inércia, gravidade leve e um
    pouco de vento contrário ao movimento."""

    N, ELO = 7, 2.6

    def __init__(self, x, y, cor=(214, 52, 66)):
        self.p = [[x, y, x, y] for _ in range(self.N)]       # x, y, x_antes, y_antes
        self.cor = cor
        self.escura = tuple(int(c * 0.62) for c in cor)

    def update(self, ax, ay, vx, vy, t):
        p = self.p
        if math.hypot(ax - p[0][0], ay - p[0][1]) > 24:          # teletransporte (renascer, checkpoint): recomeça
            for q in p:
                q[:] = [ax, ay, ax, ay]
        p[0][:] = [ax, ay, ax, ay]
        for i in range(1, self.N):
            q = p[i]
            x, y = q[0], q[1]
            dx, dy = (x - q[2]) * 0.86, (y - q[3]) * 0.86            # inércia com atrito do ar
            onda = math.sin(t * 0.25 + i * 0.9) * 0.12 * i           # tremula
            q[2], q[3] = x, y
            q[0] = x + dx - vx * 0.06
            q[1] = y + dy + 0.16 - vy * 0.02 + onda
        for _ in range(2):                                            # mantém o comprimento de cada elo
            for i in range(1, self.N):
                a, b = p[i - 1], p[i]
                dx, dy = b[0] - a[0], b[1] - a[1]
                d = math.hypot(dx, dy) or 0.001
                k = (d - self.ELO) / d
                if i == 1:
                    b[0] -= dx * k
                    b[1] -= dy * k
                else:
                    a[0] += dx * k * 0.5
                    a[1] += dy * k * 0.5
                    b[0] -= dx * k * 0.5
                    b[1] -= dy * k * 0.5

    def draw(self, s, cam):
        cx, cy = cam
        pts = [(int(q[0] - cx), int(q[1] - cy)) for q in self.p]
        for i in range(len(pts) - 1):
            larg = 3 if i < 3 else 2
            pygame.draw.line(s, self.escura, (pts[i][0], pts[i][1] + 1), (pts[i + 1][0], pts[i + 1][1] + 1), larg)
            pygame.draw.line(s, self.cor, pts[i], pts[i + 1], larg - 1)
        x, y = pts[-1]
        s.fill(self.escura, (x - 1, y, 2, 3))                        # franjinha na ponta


_cache = {}


def silhueta(spr, cor, alfa):
    """Cópia do sprite numa cor só (para o rastro do dash e a sombra)."""
    ch = (id(spr), cor)
    if ch not in _cache:
        if len(_cache) > 200:
            _cache.clear()
        c = spr.copy()
        c.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        c.fill(cor + (0,), special_flags=pygame.BLEND_RGBA_ADD)
        _cache[ch] = (c, spr)                                    # guarda o original vivo: id() não é reaproveitado
    s = _cache[ch][0]
    s.set_alpha(alfa)
    return s


class Sombra:
    """A sombra que guarda as moedas perdidas na morte."""

    def __init__(self, x, y, moedas):
        self.x, self.y, self.moedas = x, y, moedas
        self.t = 0
        self.vivo = True

    def update(self, g):
        self.t += 1
        p = g.p
        if math.hypot(p.cx - self.x, (p.y + p.h / 2) - (self.y - 14)) < 16:
            self.vivo = False
            g.moedas += self.moedas
            g.alma = min(ALMA_MAX, g.alma + ALMA_QUESTAO)
            g.texto(self.x, self.y - 34, f"+{self.moedas} MOEDAS DA SOMBRA", (200, 190, 255))
            g.particulas_burst(self.x, self.y - 14, (40, 30, 70), 18, 2.5)
            g.particulas_burst(self.x, self.y - 14, (230, 230, 255), 10, 2.0)
            g.audio.tocar("resgate")
            g.shake = 8
            g.parada = 6

    def draw(self, s, cam):
        spr = heroi.heroi("parado", self.t // 3, True, -1)
        sil = silhueta(spr, (26, 20, 44), 220)
        bob = int(math.sin(self.t * 0.06) * 3)
        x = int(self.x - spr.get_width() / 2 - cam[0] + math.sin(self.t * 0.03) * 2)
        y = int(self.y - spr.get_height() - cam[1] + bob - 6)
        s.blit(sil, (x, y))
        cx = x + spr.get_width() // 2 - 2
        olho = (255, 255, 255) if (self.t // 70) % 9 else (26, 20, 44)
        s.fill(olho, (cx - 3, y + 12, 2, 3))                          # olhos brancos, como a sombra do jogo
        s.fill(olho, (cx + 2, y + 12, 2, 3))
        for k in range(3):                                            # fiapos escuros subindo
            fx = x + 8 + (self.t * 0.7 + k * 9) % (spr.get_width() - 16)
            fy = y + spr.get_height() - 4 - ((self.t + k * 13) % 24)
            s.fill((50, 40, 80), (int(fx), int(fy), 1, 2))
        t = art.texto_px(str(self.moedas), (200, 190, 255))
        s.blit(t, (cx - t.get_width() // 2 + 2, y - 8))


def vaso_alma(s, x, y, alma, t, focando=0):
    """O vaso de alma do HUD: um círculo que enche de baixo para cima (branco-azulado), brilha quando dá para focar."""
    r = 7
    pygame.draw.circle(s, (20, 18, 34), (x, y), r + 1)
    k = alma / ALMA_MAX
    if k > 0:
        topo = int(y + r - 2 * r * k)
        for yy in range(max(topo, y - r), y + r + 1):
            meia = int(math.sqrt(max(0, r * r - (yy - y) ** 2)))
            onda = int(math.sin(t * 0.15 + yy) * 0.8) if yy == topo else 0
            s.fill((210, 226, 255), (x - meia + onda, yy, 2 * meia + 1, 1))
    cor = (255, 255, 255) if alma >= ALMA_FOCO and (t // 20) % 2 else (150, 160, 200)
    pygame.draw.circle(s, cor, (x, y), r + 1, 1)
    if focando:
        pygame.draw.circle(s, (255, 255, 255), (x, y), r + 3, 1)


def particulas_foco(g, p):
    """Partículas brancas indo para o herói enquanto ele foca."""
    a = random.uniform(0, math.tau)
    d = random.uniform(14, 22)
    x, y = p.cx + math.cos(a) * d, p.y + p.h / 2 + math.sin(a) * d
    g.efeito(x, y, "ponto", (230, 236, 255), -math.cos(a) * d / 14, -math.sin(a) * d / 14, 14)
