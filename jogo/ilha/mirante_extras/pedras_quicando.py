"""Pedras quicando — um montinho de pedras chatas na beira do lago.

A Lume pega uma pedra e atira na água, rumo ao horizonte. O número de quiques vem do acerto geral do jogador
(acertos ÷ respostas no save, em dezenas: 73% → 7), com uma variação de um para mais ou para menos, porque
pedra de verdade também não obedece. Cada quique é mais curto e mais rápido que o anterior, e a perspectiva
encolhe tudo conforme a pedra se afasta; em cada toque nasce um anel de ondulação que se abre e some.
Uma pedra por vez. O recorde vale enquanto o jogo estiver aberto (não vai para o save).
"""
import math
import random

import pygame

from . import Base
from ..mirante import GY, HZ, LW, LUZ, MARGEM_CLARA, MARGEM_ESCURA, PE, WW

try:
    import numpy as np
except ImportError:          # Android sem NumPy: usa o "quica" pronto do jogo
    np = None

_RECORDE = {"n": 0, "jogadas": 0}        # vale para a sessão inteira (sobrevive a sair e voltar ao Mirante)

# montinho: (dx, dy, largura, altura, cor) de baixo para cima
PEDRAS = [(-6, 0, 9, 3, (58, 64, 92)), (2, 0, 8, 3, (66, 70, 100)), (-3, -2, 9, 3, (78, 82, 114)),
          (-1, -4, 7, 2, (92, 96, 130)), (4, -2, 5, 2, (60, 66, 96))]


def _tic(vol):
    """Um 'tic' de água: estalo curto de ruído filtrado + um tom agudo que cai, bem baixinho."""
    sr = pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 44100
    n = int(sr * 0.05)
    t = np.arange(n) / sr
    env = np.exp(-t * 90)
    ruido = np.convolve(np.random.uniform(-1, 1, n), np.ones(6) / 6, mode="same")
    tom = np.sin(2 * np.pi * np.cumsum(np.linspace(1500, 700, n)) / sr)
    a = (0.55 * ruido + 0.45 * tom) * env * vol
    a = (np.clip(a, -1, 1) * 32000).astype(np.int16)
    canais = pygame.mixer.get_init()[2] if pygame.mixer.get_init() else 2
    return pygame.sndarray.make_sound(np.column_stack([a, a]) if canais == 2 else a)


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.px = WW * 0.685
        self.lugares = [("pedras", self.px, "atirar uma pedra no lago")]
        self.monte = self._montinho()
        self.voo = None            # pedra no ar: dict com os trechos e o tempo
        self.aneis = []            # [x, y, escala, idade, forca]
        self.gotas = []            # [x, y, vx, vy, vida]
        self.sons = []
        try:
            au = mirante.app.audio
            if np is not None and au.ok and not au.mudo:
                self.sons = [_tic(v) for v in (0.12, 0.09, 0.065, 0.045)]
        except Exception:
            self.sons = []

    # ------------------------------------------------------------ desenhos prontos
    def _montinho(self):
        s = pygame.Surface((20, 9), pygame.SRCALPHA)
        for dx, dy, w, h, cor in PEDRAS:
            r = pygame.Rect(10 + dx - w // 2, 5 + dy, w, h)
            pygame.draw.ellipse(s, (14, 18, 30), r.move(0, 1))           # sombra
            pygame.draw.ellipse(s, cor, r)
            s.fill(tuple(min(255, c + 34) for c in cor), (r.x + 2, r.y, max(1, w - 5), 1))   # brilho da lua
        return s

    # ------------------------------------------------------------ física
    def _acerto(self):
        c = e = 0
        try:
            for st in (self.mirante.app.save.d.get("q") or {}).values():
                c += int(st.get("c", 0) or 0)
                e += int(st.get("e", 0) or 0)
        except Exception:
            return None
        return None if c + e == 0 else c / (c + e)

    @staticmethod
    def _chao(s):
        """Ponto da água a uma distância s (em px de pista): y sobe para o horizonte e a escala encolhe."""
        k = math.exp(-s / 62.0)
        y = HZ + 3 + (GY - 6 - HZ) * k
        return y, 0.18 + 0.82 * k

    def interagir(self, nome):
        if self.voo is not None:
            return                                           # uma pedra por vez
        taxa = self._acerto()
        if taxa is None:
            base = 2
            n = random.randint(1, 3)
        else:
            base = int(taxa * 100) // 10
            n = max(1, base + random.choice((-1, 0, 1)))
        m = self.mirante
        lado = m.dir if m.dir in (-1, 1) else 1
        x0, y0 = m.x + lado * 4, PE - 9                      # a mão da Lume
        # pista: distâncias dos toques (o último toque é onde ela afunda)
        passos = [16.0] + [26.0 * 0.79 ** k for k in range(n)]
        trechos, s = [], 0.0
        ax, ay = x0, y0
        for i, comp in enumerate(passos):
            s += comp
            y, esc = self._chao(s)
            x = x0 + lado * s * 0.78 + math.sin(s * 0.05) * 3     # leve curva, como pedra de verdade
            if i == 0:
                alt, dur = 9.0, 16
            else:
                alt = max(1.0, comp * 0.42 * esc)
                dur = int(6 + comp * 0.55)
            trechos.append((ax, ay, x, y, alt, dur, esc))
            ax, ay = x, y
        self.voo = {"trechos": trechos, "i": 0, "f": 0, "n": n, "taxa": taxa, "pos": (x0, y0, 0.0, 1.0),
                    "fim": 0}

    def _toque(self, x, y, esc, i, afunda):
        self.aneis.append([x, y, esc, 0, 1.3 if afunda else 1.0])
        k = 2 if afunda else 3
        for _ in range(k + (3 if afunda else 0)):
            self.gotas.append([x, y, random.uniform(-0.4, 0.4) * esc * 2, -random.uniform(0.4, 0.9) * (1.5 if afunda else 1) * esc - 0.2,
                               random.randint(8, 14)])
        try:
            if afunda:
                return
            if self.sons:
                self.sons[min(i, len(self.sons) - 1)].play()
            elif not self.mirante.app.audio.mudo:
                self.mirante.app.audio.tocar("quica")
        except Exception:
            pass

    def update(self):
        v = self.voo
        if v is not None:
            if v["fim"]:
                v["fim"] -= 1
                if v["fim"] == 0:
                    self._acabou(v)
                    self.voo = None
            else:
                ax, ay, bx, by, alt, dur, esc = v["trechos"][v["i"]]
                v["f"] += 1
                u = min(1.0, v["f"] / dur)
                h = 4 * alt * u * (1 - u)
                v["pos"] = (ax + (bx - ax) * u, ay + (by - ay) * u, h, esc)
                if u >= 1.0:
                    ultimo = v["i"] == len(v["trechos"]) - 1
                    self._toque(bx, by, esc, v["i"], ultimo)
                    v["i"] += 1
                    v["f"] = 0
                    if ultimo:
                        v["fim"] = 40                            # espera o anel abrir antes de falar
        for a in self.aneis:
            a[3] += 1
        self.aneis = [a for a in self.aneis if a[3] < 70]
        for g in self.gotas:
            g[0] += g[2]
            g[1] += g[3]
            g[3] += 0.12
            g[4] -= 1
        self.gotas = [g for g in self.gotas if g[4] > 0]

    def _acabou(self, v):
        n, taxa = v["n"], v["taxa"]
        _RECORDE["jogadas"] += 1
        antes = _RECORDE["n"]
        _RECORDE["n"] = max(antes, n)
        q = "1 quique." if n == 1 else f"{n} quiques."
        if taxa is None:
            pag = [f"{q} Ainda não há respostas salvas, então esta pedra quicou por conta própria."]
        else:
            pag = [f"{q} Seu acerto geral está em {int(taxa * 100)}%."]
            if _RECORDE["jogadas"] == 1:
                pag[0] += " A pedra segue o acerto em dezenas, com um quique a mais ou a menos de sorte."
        if _RECORDE["jogadas"] > 1:
            if n > antes:
                pag[0] += f" Novo recorde desta sessão: {n}."
            else:
                pag[0] += f" Recorde desta sessão: {_RECORDE['n']}."
        try:
            if not self.mirante.fala:
                self.mirante._falar(pag)
        except Exception:
            pass

    # ------------------------------------------------------------ desenho
    def draw_lago(self, m, cam):
        for x, y, esc, idade, forca in self.aneis:                # anéis de ondulação (achatados pela perspectiva)
            for atraso, peso in ((0, 1.0), (14, 0.6)):
                u = (idade - atraso) / 56.0
                if not 0 < u < 1:
                    continue
                rx = (1.5 + 9 * forca * u) * esc + 1
                ry = max(1.0, rx * 0.28)
                b = (1 - u) ** 1.4 * peso * forca
                cor = (int(70 * b), int(90 * b), int(140 * b))
                r = pygame.Rect(0, 0, int(rx * 2), int(ry * 2) + 1)
                r.center = (int(x - cam), int(y))
                if r.right < 0 or r.left > LW:
                    continue
                s = pygame.Surface(r.size)
                pygame.draw.ellipse(s, cor, (0, 0, r.w, r.h), 1)
                m.blit(s, r.topleft, special_flags=pygame.BLEND_RGB_ADD)
        v = self.voo
        if v is not None and not v["fim"] and v["i"] > 0:          # reflexo da pedra na água
            x, y, h, esc = v["pos"]
            m.set_at((int(x - cam), int(y + h * 0.6)), (40, 46, 74))

    def draw_margem(self, m, cam):
        x = self.px - cam
        if -20 < x < LW + 20:
            m.blit(self.monte, (int(x) - 10 + 8, PE - 8))
            m.set_at((int(x) - 3 + 8, PE - 4), MARGEM_CLARA)
            m.set_at((int(x) + 7 + 8, PE + 1), MARGEM_ESCURA)

    def draw_frente(self, m, cam):
        for gx, gy, _, _, vida in self.gotas:
            b = min(1.0, vida / 8)
            m.set_at((int(gx - cam), int(gy)), (int(150 * b), int(170 * b), int(220 * b)))
        v = self.voo
        if v is None or v["fim"]:
            return
        x, y, h, esc = v["pos"]
        sx, sy = int(x - cam), int(y - h)
        if not (-3 < sx < LW + 3):
            return
        perto = esc > 0.75
        cor = (150, 150, 170) if not perto else (196, 176, 150)    # perto da Lume, a luz dela esquenta a pedra
        if esc > 0.45:
            m.fill(cor, (sx - 1, sy, 2, 1))
            m.set_at((sx, sy + 1), (70, 72, 96))
        else:
            m.set_at((sx, sy), cor)
        if perto:
            m.set_at((sx - 1, sy - 1), tuple(min(255, c + 40) for c in LUZ[:3]) if v["i"] == 0 else cor)
