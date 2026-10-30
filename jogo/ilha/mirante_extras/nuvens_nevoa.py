"""Nuvens e névoa: o tempo que passa por cima e por baixo do céu do estudo.

No alto, poucas nuvens noturnas finas atravessam o céu devagar, com paralaxe própria (andam menos que o céu quando a
câmera desliza, como se estivessem mais longe que os montes e mais perto que as estrelas). São pixel art de bordas
pontilhadas, azul-acinzentadas e semitransparentes: escurecem um pouco as estrelas (e às vezes a lua) que cobrem, e
a borda virada para a lua fica prateada. São poucas de propósito — o céu é o estudo do jogador e não pode sumir.

Embaixo, sobre o lago, uma névoa rasteira em faixas horizontais muito suaves que ondulam e derivam. Ela segue a hora
local real: fina no começo da noite, mais densa de madrugada (0h–6h, com o pico perto das 4h), rala de dia.

Tudo é pré-renderizado no __init__; por quadro só há alguns blits."""
import math
import random
import time

import pygame

from . import Base
from ..mirante import LW, HZ, GY, PAR_CEU

PAR_NUVEM = 0.14            # paralaxe das nuvens (o céu usa PAR_CEU = 0.22; a câmera, 1)
CORPO = (66, 72, 108)       # azul-acinzentado do miolo
SOMBRA = (48, 52, 84)       # parte de baixo, mais escura
BORDA = (168, 168, 188)     # borda iluminada pela lua
NEVOA = (150, 160, 200)

# densidade da névoa ao longo do dia (hora local, fração 0–1): mais densa de madrugada
_CURVA = [(0, 0.55), (2, 0.85), (3.5, 1.0), (5, 1.0), (6.5, 0.6), (8, 0.25), (18, 0.25), (21, 0.35), (24, 0.55)]

_BAYER = ((0, 2), (3, 1))   # pontilhado 2×2 para as bordas em pixel art


def _densidade_hora(h):
    for (h0, d0), (h1, d1) in zip(_CURVA, _CURVA[1:]):
        if h0 <= h <= h1:
            f = (h - h0) / (h1 - h0)
            f = f * f * (3 - 2 * f)
            return d0 + (d1 - d0) * f
    return 0.4


def _nuvem(rng, lado):
    """Uma nuvem fina: soma de bolhas achatadas (topo encaroçado, base reta), quantizada em níveis com pontilhado.
    `lado` = −1/+1: de que lado está a lua (a borda desse lado fica prateada)."""
    w, h = rng.randint(46, 68), rng.randint(14, 17)
    base = h * 0.72
    bolhas = []
    n = rng.randint(5, 8)
    for i in range(n):
        cx = w * (0.2 + 0.6 * (i + rng.uniform(-0.3, 0.3)) / max(1, n - 1))
        meio = 1 - abs(cx / w - 0.5) * 2                     # bolhas do meio são mais altas
        sy = rng.uniform(1.6, 2.4) + 3.6 * meio * rng.uniform(0.4, 1.0)
        bolhas.append((cx, base - sy * 0.75, sy * 1.25 + rng.uniform(1.5, 3.0), sy, rng.uniform(0.85, 1.0)))
    for cx in (w * 0.12, w * 0.88):                          # fiapos compridos dos lados
        bolhas.append((cx + rng.uniform(-3, 3), base - 1, rng.uniform(8, 12), 1.1, 0.5))

    def d(x, y):                                             # máximo das bolhas (caroços) + um pouco da soma (véu)
        s, mx = 0.0, 0.0
        for cx, cy, sx, sy, a in bolhas:
            dx, dy = (x - cx) / sx, (y - cy) / sy
            q = dx * dx + dy * dy
            if q < 9:
                e = a * math.exp(-q)
                s += e
                mx = max(mx, e)
        s = mx + 0.3 * (s - mx)
        if y > base:                                         # base achatada que se desfaz
            s *= max(0.0, 1 - (y - base) / 2.5)
        return s

    campo = [[d(x + 0.5, y + 0.5) for x in range(w)] for y in range(h)]
    niv = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = campo[y][x]
            lim = (_BAYER[y % 2][x % 2] + 0.5) / 4
            niv[y][x] = 2 if v > 0.55 + 0.06 * lim else (1 if v > 0.1 + 0.3 * lim else 0)

    def nv(x, y):
        return niv[y][x] if 0 <= x < w and 0 <= y < h else 0

    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            k = niv[y][x]
            if not k:
                continue
            if k == 2:
                fundo = y > base - 2 or nv(x, y + 2) < 2
                cor, a = (SOMBRA if fundo else CORPO), 112
                perto = x / w if lado > 0 else 1 - x / w        # quanto este ponto encara a lua
                beira = nv(x, y - 1) < 2 or nv(x + lado, y - 1) < 2 or nv(x + lado, y) < 2
                if beira and perto > 0.42:                       # borda prateada do lado da lua
                    cor, a = BORDA, 128
                elif beira and perto > 0.18 or nv(x + lado, y - 2) < 2 and perto > 0.5:
                    cor = tuple((c1 + c2) // 2 for c1, c2 in zip(CORPO, BORDA))
            else:
                cor, a = CORPO, 58
            s.set_at((x, y), (*cor, a))
    return s


def _faixa(rng, larg, alt, a_max):
    """Faixa de névoa sem emenda (as ondas têm período que divide a largura), suave na vertical e na horizontal."""
    s = pygame.Surface((larg, alt), pygame.SRCALPHA)
    ondas = [(rng.randint(1, 3), rng.uniform(0, 6.28), 0.5), (rng.randint(4, 7), rng.uniform(0, 6.28), 0.3),
             (rng.randint(9, 14), rng.uniform(0, 6.28), 0.2)]
    for x in range(larg):
        u = x / larg * 6.2832
        k = sum(p * math.sin(u * n + f) for n, f, p in ondas)            # −1..1
        dens = max(0.0, 0.55 + 0.6 * k)                                     # manchas mais e menos densas
        meio = alt / 2 + math.sin(u * ondas[1][0] + 1.3) * alt * 0.12       # a faixa sobe e desce ao longo do x
        esp = alt * (0.32 + 0.18 * (k + 1) / 2)
        for y in range(alt):
            q = (y + 0.5 - meio) / max(esp, 0.5)
            v = dens * math.exp(-q * q)
            a = int(a_max * v)
            if a > 1:
                s.set_at((x, y), (*NEVOA, min(255, a)))
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        rng = random.Random(4207)
        # cada forma em duas versões: borda à esquerda e à direita (a que encara a lua é escolhida no desenho)
        self.formas = []
        for _ in range(4):
            semente = rng.random()
            self.formas.append({l: _nuvem(random.Random(semente), l) for l in (-1, 1)})
        self.vao = LW + 150                                     # “pista” circular por onde as nuvens passam
        self.nuvens = []                                        # [forma, x0, y, velocidade]
        alturas = [HZ * 0.10, HZ * 0.30, HZ * 0.19, HZ * 0.44]
        for i in range(4):
            self.nuvens.append((i, rng.uniform(0, self.vao), int(alturas[i]), rng.uniform(0.018, 0.04)))
        # névoa: faixas da mais distante (fina, perto do horizonte) para a mais próxima
        alt_lago = GY - HZ
        self.larg = LW * 2
        self.faixas = []
        for i, (fy, fa, am, par, v) in enumerate([(0.02, 3, 70, 0.25, 0.010), (0.16, 5, 60, 0.40, 0.016),
                                                  (0.38, 7, 52, 0.60, 0.022), (0.64, 9, 46, 0.85, 0.030)]):
            sup = _faixa(rng, self.larg, fa, am)
            self.faixas.append([sup, HZ + int(alt_lago * fy), par, v, rng.uniform(0, 6.28)])
        self.dens = None
        self._hora_t = -99999
        self._atualizar_densidade()

    def _atualizar_densidade(self):
        lt = time.localtime()
        d = _densidade_hora(lt.tm_hour + lt.tm_min / 60)
        if self.dens is None or abs(d - self.dens) > 0.01:
            self.dens = d
            for f in self.faixas:
                f[0].set_alpha(int(255 * d))

    def update(self):
        t = self.mirante.t
        if t - self._hora_t > 1800:                             # a cada ~30 s basta
            self._hora_t = t
            self._atualizar_densidade()

    def draw_ceu(self, ceu, ox):
        t = self.mirante.t
        cam = ox / PAR_CEU
        lua_x = self.mirante.lua_pos[0] - cam * 0.08 + 8           # centro da lua na tela do céu
        for i, x0, y, v in self.nuvens:
            x = int((x0 + t * v - cam * PAR_NUVEM) % self.vao) - 75
            sup = self.formas[i][1 if x + sup_meia(self.formas[i][1]) < lua_x else -1]
            if x > LW or x + sup.get_width() < 0:
                continue
            ceu.blit(sup, (x, y + int(math.sin(t * 0.004 + x0) * 1.2)))

    def draw_lago(self, m, cam):
        t = self.mirante.t
        for sup, y, par, v, fase in self.faixas:
            x = -int((t * v + cam * par) % self.larg)
            yy = y + int(round(math.sin(t * 0.006 + fase)))
            m.blit(sup, (x, yy))
            if x + self.larg < LW:
                m.blit(sup, (x + self.larg, yy))


def sup_meia(s):
    return s.get_width() // 2
