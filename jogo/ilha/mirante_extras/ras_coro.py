"""Coro das rãs — vitórias-régias na beira do lago, com uma rã para cada dia de estudo das últimas duas semanas.

A conta é honesta e curta: dias distintos em que alguma questão foi respondida (campo "ult" do save) nos últimos
14 dias, contando hoje. Mínimo de uma rã (ela fica mesmo sem estudo), máximo de oito. De vez em quando uma delas
infla o papo e coaxa baixinho. No meio das folhas há uma flor de lótus que segue o relógio de verdade: fechada
durante o dia, abre devagar das 18 h até o amanhecer e volta a fechar entre 6 h e 9 h.

Interagir: o coro coaxa em sequência, uma rã por vez, e uma fala diz quantos dias elas representam."""
import math
import random
import time

import pygame

from . import Base
from ..mirante import GY, WW

try:
    import numpy as np
except ImportError:                                     # Android sem NumPy: as rãs ficam mudas
    np = None

VERDE_FOLHA, VERDE_CLARO, VERDE_ESC = (22, 54, 54), (42, 88, 76), (10, 26, 34)
RA, RA_CLARA, RA_ESC = (112, 162, 96), (160, 200, 120), (56, 98, 66)
OLHO = (236, 222, 150)
PAPO = (206, 214, 170)

# folhas: (dx, dy a partir de GY, largura). As mais altas estão mais longe, então são menores.
FOLHAS = [(-16, -4, 11), (-4, -7, 10), (9, -4, 12), (18, -10, 8), (-13, -13, 7), (4, -15, 7), (-19, -19, 5), (14, -19, 5)]
LOTUS_FOLHA = 1                                          # a flor nasce na folha do meio
# lugares das rãs: (índice da folha, deslocamento em x); os primeiros são os mais visíveis
VAGAS = [(0, -2), (2, 3), (3, 0), (4, 0), (2, -3), (5, 0), (0, 3), (1, 3)]

RA_SPR = [".e.e.",
          "GGGGG",
          "gGGGg",
          "g...g"]


def _sprite(linhas, pal):
    s = pygame.Surface((len(linhas[0]), len(linhas)), pygame.SRCALPHA)
    for y, ln in enumerate(linhas):
        for x, ch in enumerate(ln):
            if ch in pal:
                s.set_at((x, y), pal[ch])
    return s


def _folha(w):
    """Vitória-régia vista de lado: elipse achatada com um corte em V e a borda clara."""
    h = max(2, w // 3 + 1)
    s = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, VERDE_ESC, (0, 1, w + 2, h + 1))
    pygame.draw.ellipse(s, VERDE_FOLHA, (1, 0, w, h))
    pygame.draw.line(s, VERDE_CLARO, (2, 0), (w - 2, 0))
    cx = w // 2 + 1 + w // 5                             # o corte não fica no centro
    pygame.draw.polygon(s, (0, 0, 0, 0), [(cx, h // 2 + 1), (cx - 1, h + 2), (cx + 1, h + 2)])
    return s


def _lotus(p):
    """Flor de lótus aberta na fração p (0 = botão fechado, 1 = aberta)."""
    s = pygame.Surface((15, 10), pygame.SRCALPHA)
    bx, by = 7, 8
    pygame.draw.line(s, VERDE_CLARO, (bx, by), (bx, 9))
    rosa, rosa_esc, rosa_cla = (226, 150, 190), (160, 90, 140), (250, 206, 226)
    abre = 0.12 + 1.15 * p                               # meia-abertura das pétalas externas (radianos)
    comp = 5 + 1.2 * p
    for k, lado in enumerate((-1, 1, -0.55, 0.55, -0.15, 0.15)):
        ang = lado * abre * (1 if abs(lado) == 1 else 0.85)
        L = comp * (0.85 if abs(lado) < 0.5 else 1.0)
        tx, ty = bx + math.sin(ang) * L, by - math.cos(ang) * L
        cor = rosa_esc if abs(lado) == 1 else (rosa if abs(lado) > 0.3 else rosa_cla)
        lx, ly = math.cos(ang) * 1.6, math.sin(ang) * 1.6
        pygame.draw.polygon(s, cor, [(bx - lx, by - ly), (tx, ty), (bx + lx, by + ly)])
    if p > 0.45:                                         # miolo aparece quando abre
        pygame.draw.rect(s, (250, 210, 110), (bx - 1, by - 2, 3, 1))
    return s


def _abertura_agora():
    """Fração de abertura pela hora real: abre das 18 h às 5 h, fecha de 6 h a 9 h, fechada de dia."""
    lt = time.localtime()
    h = lt.tm_hour + lt.tm_min / 60
    if h >= 18 or h < 5:
        return min(1.0, ((h - 18) % 24) / 11)
    if h < 6:
        return 1.0
    if h < 9:
        return 1 - (h - 6) / 3
    return 0.0


def _dias_estudo(save):
    hoje = time.localtime()
    meia_noite = time.mktime(hoje[:3] + (0, 0, 0, 0, 0, -1))
    desde = meia_noite - 13 * 86400 - 3600             # 14 dias contando hoje (folga para horário de verão)
    dias = set()
    for st in (save.d.get("q") or {}).values():
        try:
            u = float(st.get("ult") or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        if desde <= u <= time.time() + 86400:
            dias.add(time.localtime(u)[:3])
    return len(dias)


def _coaxo(sr, canais, tom):
    """Coaxar curto e grave: pulsos rápidos sobre um tom que desce, misturados com ruído passado num filtro."""
    dur = 0.22
    n = int(sr * dur)
    t = np.arange(n) / sr
    f = np.linspace(150 * tom, 100 * tom, n)
    fase = 2 * np.pi * np.cumsum(f) / sr
    corpo = np.sin(fase) + 0.35 * np.sin(2 * fase)
    pulsos = (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t)) ** 3          # o "trrr" da garganta
    ruido = np.random.default_rng(int(tom * 100)).uniform(-1, 1, n)
    ruido = np.convolve(ruido, np.ones(24) / 24, mode="same") * 3     # passa-baixa simples
    env = np.minimum(1, t / 0.012) * np.clip((dur - t) / 0.09, 0, 1)
    a = (0.75 * corpo + 0.4 * ruido) * pulsos * env
    a = a / max(1e-6, np.abs(a).max()) * 0.8
    a = (a * 32000).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([a, a]) if canais == 2 else a)


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x0 = WW * 0.574
        self.lugares = [("ras_coro", self.x0, "ouvir o coro das rãs")]
        try:
            self.dias = _dias_estudo(mirante.app.save)
        except Exception:
            self.dias = 0
        self.n = max(1, min(8, self.dias))
        self.folhas = [(dx, dy, _folha(w), w) for dx, dy, w in FOLHAS]
        pal = {"G": RA, "g": RA_ESC, "e": OLHO}
        self.ra = _sprite(RA_SPR, pal)
        self.ra_lua = _sprite(RA_SPR, {"G": RA_CLARA, "g": RA, "e": OLHO})   # rã no meio do coaxo, mais clara
        self.lotus_est = [_lotus(k / 7) for k in range(8)]
        self.abre = _abertura_agora()
        rng = random.Random(7)
        self.fase = [rng.uniform(0, 6.28) for _ in range(8)]
        self.papo = [0] * 8                              # quadros restantes de coaxo de cada rã
        self.prox = rng.randint(160, 360)
        self.fila = []                                   # coro em sequência: [(quadro_de_início, rã)]
        self.sons = None
        au = mirante.app.audio
        if np is not None and au.ok and not au.mudo:
            try:
                sr, _, canais = pygame.mixer.get_init()
                self.sons = [_coaxo(sr, canais, tom) for tom in (1.0, 0.86, 1.15)]
                for s in self.sons:
                    s.set_volume(0.08)
            except Exception:
                self.sons = None

    def _coaxar(self, i):
        self.papo[i] = 34
        au = self.mirante.app.audio
        if self.sons and au.ok and not au.mudo:
            try:
                s = self.sons[i % len(self.sons)]
                perto = abs(self.mirante.x - self.x0) < 200
                s.set_volume(0.08 if perto else 0.03)
                s.play()
            except Exception:
                pass

    def interagir(self, nome):
        t = self.mirante.t
        self.fila = [(t + 10 + 26 * k, i) for k, i in enumerate(range(self.n))]
        if self.dias == 0:
            texto = ("1 rã: nenhum dia de estudo nas últimas duas semanas. Esta fica aqui de qualquer jeito, "
                     "esperando o próximo dia sem pressa.")
        elif self.dias == 1:
            texto = "1 rã: 1 dia de estudo nas últimas duas semanas. Cada dia que você estuda traz mais uma para o coro."
        else:
            texto = (f"{self.n} rãs: {self.dias} dias de estudo nas últimas duas semanas. "
                     "Elas só ficam enquanto o dia cabe nessa janela; depois, outra toma o lugar.")
            if self.dias > 8:
                texto = (f"8 rãs, que é o que cabe nas folhas: {self.dias} dias de estudo nas últimas duas semanas. "
                         "O coro está cheio.")
        self.mirante._falar([texto])

    def update(self):
        t = self.mirante.t
        for i in range(8):
            if self.papo[i]:
                self.papo[i] -= 1
        while self.fila and self.fila[0][0] <= t:
            self._coaxar(self.fila.pop(0)[1])
        if not self.fila:
            self.prox -= 1
            if self.prox <= 0:
                self.prox = random.randint(240, 620)
                self._coaxar(random.randrange(self.n))
        if t % 1800 == 0:                                # a flor acompanha o relógio, sem pressa
            self.abre = _abertura_agora()

    def draw_lago(self, m, cam):
        bx = self.x0 - cam
        if not -30 < bx < m.get_width() + 30:
            return
        t = self.mirante.t
        pos = []
        for k, (dx, dy, spr, w) in enumerate(self.folhas):
            bob = round(math.sin(t * 0.03 + k * 1.7) * 0.5)
            x, y = int(bx + dx - w / 2), GY + dy + bob
            m.blit(spr, (x, y))
            pos.append((x + w / 2 + 1, y))
        # lótus
        lx, ly = pos[LOTUS_FOLHA]
        flor = self.lotus_est[min(7, int(self.abre * 7 + 0.5))]
        m.blit(flor, (int(lx - 7), int(ly - 8)))
        if self.abre > 0.5:
            m.fill((18, 8, 14), (int(lx - 3), int(ly - 4), 7, 3), special_flags=pygame.BLEND_RGB_ADD)
        # rãs
        for i in range(self.n):
            fi, ox = VAGAS[i]
            fx, fy = pos[fi]
            x, y = int(fx + ox - 2), int(fy - 3)
            p = self.papo[i]
            m.blit(self.ra_lua if p else self.ra, (x, y))
            if p:                                        # o papo infla e esvazia
                r = 1 + int(2.2 * math.sin(math.pi * (34 - p) / 34))
                pygame.draw.ellipse(m, PAPO, (x + 2 - r // 2 - 1, y + 2, r + 2, max(2, r)))
            elif (t + int(self.fase[i] * 100)) % 300 < 4:   # piscadinha
                m.fill(RA, (x + 1, y, 1, 1))
                m.fill(RA, (x + 3, y, 1, 1))
