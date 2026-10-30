"""Sinos de vento — um poste de madeira na margem com um mensageiro dos ventos de cinco tubinhos.

De tempos em tempos (20 a 60 s) passa uma rajada suave: os tubos balançam como pêndulos amortecidos, o badalo
encosta em alguns deles e cada toque acende o tubo por um instante e soa a nota dele. As cinco notas formam uma
escala pentatônica (dó, ré, mi, sol, lá), então qualquer combinação soa bem. O timbre é sintetizado na entrada:
senoides com as razões inarmônicas de um tubo livre (1 : 2,76 : 5,40), decaimento exponencial de uns 2 s e uma
leve batida entre parciais quase iguais. Sem áudio (ou no mudo) a peça continua só visual.

Ao tocar, a Lume puxa o sino: sai uma frase curta de 5 a 7 notas e uma linha sobre pausa e respiração."""
import math
import random

import pygame

from . import Base
from ..mirante import LW, MADEIRA, MADEIRA_ESC, PE, WW

FRACAO = 0.308
FREQS = [523.25, 587.33, 659.26, 783.99, 880.00]       # dó5 ré5 mi5 sol5 lá5 (pentatônica de dó)
COMPR = [13, 12, 11, 10, 9]                              # tubo mais longo = nota mais grave
VOLUME = 0.11

TUBO = (150, 162, 196)
TUBO_CLARO = (206, 216, 240)
TUBO_ESC = (84, 92, 128)
FIO = (70, 74, 104)
BRILHO = (190, 210, 255)

# frases da Lume (índices das notas); todas pentatônicas, terminam em repouso
FRASES = [[0, 2, 3, 4, 3, 2], [4, 3, 2, 1, 0], [2, 3, 4, 2, 1, 0, 0], [0, 1, 2, 4, 3], [3, 4, 3, 2, 1, 2, 0],
          [1, 2, 3, 2, 0, 1]]

FALAS = [
    "Antes da próxima questão: inspire devagar, solte o ar mais devagar ainda. Duas vezes. Pronto.",
    "O sino não tem pressa. Três respirações lentas e a cabeça volta mais limpa para o estudo.",
    "Solte os ombros e a mandíbula, respire fundo uma vez. Depois, a próxima.",
    "Uma pausa de um minuto também conta como estudo. Respire até o som acabar e volte.",
    "Olhe para longe um pouco, deixe os olhos descansarem do texto, respire. Então siga.",
    "Inspire contando quatro, expire contando seis. Quando o último tubo calar, recomece.",
]


def _sintetizar():
    """Cria os 5 pygame.mixer.Sound do sino, no formato atual do mixer. Devolve [] se algo não bater."""
    try:
        import numpy as np
        ini = pygame.mixer.get_init()
        if not ini:
            return []
        sr, fmt, canais = ini
        if fmt != -16:
            return []
        dur = 2.6
        t = np.arange(int(sr * dur)) / sr
        ataque = np.minimum(1.0, t / 0.004)
        sons = []
        for i, f in enumerate(FREQS):
            onda = np.zeros_like(t)
            # (razão, amplitude, constante de decaimento em s): parciais altas morrem antes
            for r, a, tau in [(1.0, 1.0, 0.75), (1.0035, 0.35, 0.7), (2.756, 0.42, 0.32), (5.404, 0.18, 0.12),
                              (8.933, 0.06, 0.05)]:
                if f * r < sr * 0.45:
                    onda += a * np.sin(2 * np.pi * f * r * t + i * r) * np.exp(-t / tau)
            onda *= ataque
            onda /= max(1e-6, float(np.max(np.abs(onda))))
            pcm = (onda * 0.9 * 32767).astype(np.int16)
            if canais == 2:
                pan = 0.3 + 0.1 * i                              # tubos espalhados da esquerda para a direita
                esq = (pcm * math.cos(pan * math.pi / 2) * 1.2).clip(-32767, 32767).astype(np.int16)
                dir_ = (pcm * math.sin(pan * math.pi / 2) * 1.2).clip(-32767, 32767).astype(np.int16)
                arr = np.ascontiguousarray(np.stack([esq, dir_], axis=1))
            elif canais == 1:
                arr = pcm
            else:
                arr = np.ascontiguousarray(np.repeat(pcm[:, None], canais, axis=1))
            s = pygame.sndarray.make_sound(arr)
            s.set_volume(VOLUME)
            sons.append(s)
        return sons
    except Exception:
        return []


def _halo(raio, cor, forca):
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1))
    for r in range(raio, 0, -1):
        k = (1 - r / raio) ** 2 * forca
        pygame.draw.circle(s, tuple(min(255, int(c * k)) for c in cor), (raio, raio), r)
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x0 = WW * FRACAO
        self.lugares = [("sinos_vento", self.x0, "tocar o sino de vento")]
        self.rng = random.Random()
        au = mirante.app.audio
        self.sons = _sintetizar() if (au.ok and not au.mudo) else []
        # física: ângulo e velocidade de cada tubo e do badalo
        self.ang = [0.0] * 5
        self.vel = [0.0] * 5
        self.bad, self.bad_v = 0.0, 0.0
        self.luz = [0.0] * 5                                  # brilho de cada tubo (0..1), decai
        self.rajada_t = self.rng.randint(300, 900)            # a primeira chega mais cedo
        self.rajada = 0.0                                     # força atual do vento (0..1)
        self.rajada_dur, self.rajada_i, self.rajada_max = 0, 0, 0.0
        self.fila = []                                        # [(quadro, nota)] da frase da Lume
        self.frase_i = self.rng.randrange(len(FRASES))
        self.fala_i = self.rng.randrange(len(FALAS))
        self.riscos = []                                      # traços de vento [x, y, vida]
        # brilhos prontos em 4 intensidades (nada de criar Surface por quadro)
        self.halos = [_halo(6, BRILHO, f) for f in (0.3, 0.5, 0.7, 0.9)]
        self.poste = self._poste()

    # --------------------------------------------------------- arte fixa
    def _poste(self):
        """Poste com braço e o disquinho de onde pendem os tubos (sem os tubos, que se movem)."""
        s = pygame.Surface((24, 66), pygame.SRCALPHA)
        px = 18                                               # poste à direita; o braço vai para a esquerda
        pygame.draw.rect(s, MADEIRA_ESC, (px - 1, 2, 3, 64))
        pygame.draw.line(s, MADEIRA, (px, 3), (px, 65))
        for y in (14, 31, 47, 56):                                # nós da madeira
            s.set_at((px, y), MADEIRA_ESC)
        pygame.draw.rect(s, MADEIRA_ESC, (2, 3, px, 2))       # braço
        pygame.draw.line(s, MADEIRA, (3, 3), (px, 3))
        pygame.draw.line(s, MADEIRA_ESC, (px - 4, 5), (px - 1, 8))   # mão-francesa
        pygame.draw.rect(s, (40, 30, 34), (px - 2, 63, 5, 3))  # base enterrada
        pygame.draw.line(s, FIO, (8, 5), (8, 8))              # fio até o disco
        pygame.draw.rect(s, TUBO_ESC, (3, 8, 11, 2))          # disco de suspensão
        pygame.draw.line(s, TUBO, (4, 8), (12, 8))
        return s

    # --------------------------------------------------------- som e toques
    def _soar(self, i):
        au = self.mirante.app.audio
        if self.sons and au.ok and not au.mudo:
            try:
                self.sons[i].play()
            except pygame.error:
                pass

    def _tocar(self, i, forca=1.0):
        self.luz[i] = min(1.0, self.luz[i] + 0.75 * forca + 0.25)
        self.vel[i] += (0.05 if self.rng.random() < 0.5 else -0.05) * forca
        self._soar(i)

    def interagir(self, nome):
        frase = FRASES[self.frase_i % len(FRASES)]
        self.frase_i += 1
        t, q = self.mirante.t, 6
        self.fila = []
        for k, n in enumerate(frase):
            q += 15 + (8 if k == len(frase) - 1 else 0) + self.rng.randint(-2, 2)
            self.fila.append((t + q, n))
        self.bad_v += 0.06
        self.mirante._falar([FALAS[self.fala_i % len(FALAS)]])
        self.fala_i += 1

    # --------------------------------------------------------- quadro a quadro
    def update(self):
        t = self.mirante.t
        # rajadas: envelope suave (seno) de 3 a 6 s
        if self.rajada_dur:
            self.rajada_i += 1
            self.rajada = math.sin(math.pi * self.rajada_i / self.rajada_dur) ** 2 * self.rajada_max
            if self.rajada_i >= self.rajada_dur:
                self.rajada_dur, self.rajada = 0, 0.0
                self.rajada_t = self.rng.randint(1200, 3600)
        else:
            self.rajada_t -= 1
            if self.rajada_t <= 0:
                self.rajada_dur, self.rajada_i = self.rng.randint(180, 360), 0
                self.rajada_max = self.rng.uniform(0.55, 1.0)
        # pêndulos amortecidos empurrados pelo vento (com um pouco de turbulência por tubo)
        w = self.rajada
        for i in range(5):
            empurra = w * (0.010 + 0.006 * math.sin(t * 0.13 + i * 1.7))
            self.vel[i] += -self.ang[i] * (0.012 + i * 0.002) + empurra * 0.6 - self.vel[i] * 0.025
            self.ang[i] += self.vel[i]
            self.luz[i] *= 0.955
        self.bad_v += -self.bad * 0.02 + w * 0.012 * math.sin(t * 0.21) - self.bad_v * 0.03
        self.bad += self.bad_v
        # toques do vento: mais prováveis quanto mais forte a rajada
        if w > 0.15 and self.rng.random() < w * 0.045:
            i = self.rng.randrange(5)
            if self.luz[i] < 0.4:
                self._tocar(i, 0.5 + 0.5 * w)
        # frase da Lume
        while self.fila and self.fila[0][0] <= t:
            _, n = self.fila.pop(0)
            self._tocar(n, 1.0)
            self.bad_v += 0.02
        # traços de vento
        if w > 0.3 and self.rng.random() < w * 0.08:
            self.riscos.append([self.x0 - 50 + self.rng.uniform(-20, 10), PE - self.rng.uniform(24, 64), 0])
        for r in self.riscos:
            r[0] += 1.2 + w
            r[2] += 1
        self.riscos = [r for r in self.riscos if r[2] < 70]

    def draw_margem(self, m, cam):
        x = self.x0 - cam
        if not (-40 < x < LW + 40):
            return
        for rx, ry, vida in self.riscos:                       # vento: risquinhos claros que somem
            sx = rx - cam
            a = 1 - abs(vida - 35) / 35
            c = int(40 + 50 * a)
            pygame.draw.line(m, (c, c + 6, c + 30), (sx, ry), (sx + 4, ry + math.sin(vida * 0.2)))
        bx, by = int(x) - 13, PE - 64                          # canto da superfície do poste
        m.blit(self.poste, (bx, by))
        # tubos pendurados do disco (y = by + 10), espaçados de 2 px
        topo = by + 10
        for i in range(5):
            cx = bx + 4 + i * 2
            a = self.ang[i] + self.bad * 0.25
            L = COMPR[i]
            fio = 2
            ax, ay = cx + math.sin(a) * fio, topo + fio
            ex, ey = ax + math.sin(a) * L, ay + math.cos(a) * L
            pygame.draw.line(m, FIO, (cx, topo), (ax, ay))
            g = self.luz[i]
            if g > 0.06:
                h = self.halos[min(3, int(g * 4))]
                mx, my = (ax + ex) / 2, (ay + ey) / 2
                m.blit(h, (mx - 6, my - 6), special_flags=pygame.BLEND_RGB_ADD)
            cor = tuple(int(c0 + (255 - c0) * g * 0.8) for c0 in (TUBO if i % 2 else TUBO_CLARO))
            pygame.draw.line(m, cor, (ax, ay), (ex, ey))
            m.set_at((int(ax), int(ay)), TUBO_CLARO if g < 0.3 else (255, 255, 255))
        # badalo (disco) e a velinha de vento abaixo dele
        cx = bx + 8
        a = self.bad
        dx, dy = cx + math.sin(a) * 9, topo + math.cos(a) * 9
        pygame.draw.line(m, FIO, (cx, topo), (dx, dy))
        pygame.draw.rect(m, MADEIRA, (dx - 1, dy, 3, 1))
        vx, vy = dx + math.sin(a * 1.6) * 5, dy + math.cos(a * 1.6) * 5
        pygame.draw.line(m, FIO, (dx, dy + 1), (vx, vy))
        pygame.draw.rect(m, (110, 70, 96), (vx - 1, vy, 3, 4))
