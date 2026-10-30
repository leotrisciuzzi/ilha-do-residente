"""Lua de verdade — a lua do Mirante passa a ter a fase real da lua de hoje.

Cálculo: a idade média da lua sai do mês sinódico (29,530588853 dias) contado a partir de uma lua nova de
referência (2000-01-06 18:14 UTC). Essa média erra até ~14 h, porque a órbita da lua é elíptica; por isso a
fase de agora usa o ângulo de fase com as correções principais de Meeus (Astronomical Algorithms, eq. 48.4), e as
datas da próxima cheia e da próxima nova usam o algoritmo do capítulo 49 (erro de poucos minutos). Tudo em
Python puro, sem rede.

Lado iluminado (convenção do hemisfério sul, o Leo está no Brasil): quem olha para a lua do hemisfério sul está
virado para o norte, e o Sol, depois do pôr, fica à esquerda (a oeste). Por isso a lua CRESCENTE aparece acesa
à ESQUERDA, desenhando um "C" (aqui a lua "não mente": C de crescente), e a MINGUANTE aparece acesa à DIREITA.
No hemisfério norte é o espelho disso. Perto do equador a lua crescente baixa no horizonte aparece deitada
(como um sorriso); o desenho simplifica para esquerda/direita.

Desenho: o sprite 17×17 do Mirante (disco de raio 7 com centro em (8, 8), recortado em crescente fixo) é
coberto por um disco próprio com a parte escura em tom de "luz cinérea" e o terminador elíptico. A máscara é
refeita só quando a fase muda de verdade, e a fase é recalculada no máximo uma vez por minuto.

A plaquinha na margem conta o nome da fase, a porcentagem iluminada e as datas da próxima cheia e da próxima nova.
"""
import math
import time
from datetime import datetime, timedelta, timezone

import pygame

from . import Base
from ..mirante import LUA, LUZ, MADEIRA, MADEIRA_ESC, PE, WW

SINODICO = 29.530588853
REF_NOVA = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
JD_UNIX = 2440587.5                               # dia juliano de 1970-01-01 00:00 UTC
DELTA_T = 69.0 / 86400                            # TT − UTC (~69 s nesta década)


def _jd(dt):
    return JD_UNIX + dt.timestamp() / 86400


def _dt(jd):
    return datetime.fromtimestamp((jd - JD_UNIX) * 86400, tz=timezone.utc)


def idade_media(dt):
    """Idade média (dias desde a última lua nova) pelo mês sinódico e a lua nova de referência."""
    return ((dt - REF_NOVA).total_seconds() / 86400) % SINODICO


def fase(dt):
    """→ (fração do ciclo 0–1, fração iluminada 0–1). Ângulo de fase com correções de Meeus 48.4."""
    T = (_jd(dt) + DELTA_T - 2451545.0) / 36525
    r = math.radians
    D = r((297.8501921 + 445267.1114034 * T) % 360)   # elongação média
    M = r((357.5291092 + 35999.0502909 * T) % 360)    # anomalia do sol
    Mp = r((134.9633964 + 477198.8675055 * T) % 360)  # anomalia da lua
    i = (180 - math.degrees(D) - 6.289 * math.sin(Mp) + 2.100 * math.sin(M) - 1.274 * math.sin(2 * D - Mp)
         - 0.658 * math.sin(2 * D) - 0.214 * math.sin(2 * Mp) - 0.110 * math.sin(D))
    k = (1 + math.cos(r(i))) / 2
    p = ((180 - i) % 360) / 360                        # 0 nova, 0,25 quarto crescente, 0,5 cheia...
    return p, k


def _evento(k):
    """Meeus cap. 49: k inteiro = lua nova, k + 0,5 = lua cheia. Devolve o datetime UTC."""
    T = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T ** 2 - 0.000000150 * T ** 3 + 0.00000000073 * T ** 4)
    r = math.radians
    M = r(2.5534 + 29.10535670 * k - 0.0000014 * T ** 2 - 0.00000011 * T ** 3)
    Mp = r(201.5643 + 385.81693528 * k + 0.0107582 * T ** 2 + 0.00001238 * T ** 3 - 0.000000058 * T ** 4)
    F = r(160.7108 + 390.67050284 * k - 0.0016118 * T ** 2 - 0.00000227 * T ** 3 + 0.000000011 * T ** 4)
    Om = r(124.7746 - 1.56375588 * k + 0.0020672 * T ** 2 + 0.00000215 * T ** 3)
    E = 1 - 0.002516 * T - 0.0000074 * T ** 2
    s = math.sin
    nova = abs(k - round(k)) < 0.01
    a = (-0.40720, 0.17241, 0.01608, 0.01039, 0.00739, -0.00514, 0.00208) if nova else \
        (-0.40614, 0.17302, 0.01614, 0.01043, 0.00734, -0.00515, 0.00209)
    jde += (a[0] * s(Mp) + a[1] * E * s(M) + a[2] * s(2 * Mp) + a[3] * s(2 * F) + a[4] * E * s(Mp - M)
            + a[5] * E * s(Mp + M) + a[6] * E * E * s(2 * M) - 0.00111 * s(Mp - 2 * F) - 0.00057 * s(Mp + 2 * F)
            + 0.00056 * E * s(2 * Mp + M) - 0.00042 * s(3 * Mp) + 0.00042 * E * s(M + 2 * F)
            + 0.00038 * E * s(M - 2 * F) - 0.00024 * E * s(2 * Mp - M) - 0.00017 * s(Om))
    return _dt(jde - DELTA_T)


def proximo(dt, cheia):
    """Próxima lua cheia (cheia=True) ou nova depois de dt."""
    k = math.floor((dt.year + (dt.timetuple().tm_yday - 1) / 365.25 - 2000) * 12.3685) - 2
    k += 0.5 if cheia else 0
    while True:
        ev = _evento(k)
        if ev > dt:
            return ev
        k += 1


NOMES = ["nova", "crescente", "quarto crescente", "crescente gibosa", "cheia", "minguante gibosa",
         "quarto minguante", "minguante"]


def nome_fase(p):
    """Fases "pontuais" (nova, quartos, cheia) valem ±1 dia em torno do instante exato."""
    j = 1 / SINODICO
    for alvo, n in ((0, 0), (0.25, 2), (0.5, 4), (0.75, 6), (1, 0)):
        if abs(p - alvo) <= j:
            return NOMES[n]
    return NOMES[1 + 2 * int(p / 0.25)]


def mascara(p, k):
    """Sprite 17×17 da lua na fase dada (hemisfério sul: crescente acesa à esquerda)."""
    s = pygame.Surface((17, 17), pygame.SRCALPHA)
    escura = (40, 40, 74, 235)                     # luz cinérea: o disco escuro ainda se nota
    crater = [(6, 10, (210, 204, 186)), (9, 5, (220, 214, 194)), (10, 11, (226, 220, 200)), (4, 7, (228, 222, 204))]
    R = 7.4
    cresc = p < 0.5
    for y in range(17):
        dy = y - 8
        if dy * dy > R * R:
            continue
        w = math.sqrt(R * R - dy * dy)
        xt = w * (2 * k - 1)                       # terminador: −w (nada aceso) … +w (tudo aceso)
        for x in range(17):
            dx = x - 8
            if dx * dx + dy * dy > R * R:
                continue
            u = dx if cresc else -dx               # crescente: aceso à esquerda (dx < xt); minguante: à direita
            luz = max(0.0, min(1.0, xt - u + 0.5))   # meia-luz de 1 px no terminador
            cor = LUA
            for cx, cy, cc in crater:
                if (x, y) == (cx, cy):
                    cor = cc
            borda = dx * dx + dy * dy > (R - 1) ** 2
            if borda and luz > 0:
                cor = tuple(int(c * 0.9) for c in cor)
            r_ = [int(escura[i] + (cor[i] - escura[i]) * luz) for i in range(3)]
            s.set_at((x, y), (*r_, int(escura[3] + (255 - escura[3]) * luz)))
    return s


def _placa():
    """Plaquinha de madeira (13×24): poste alto, para a tábua aparecer acima da Lume, e uma meia-lua pintada."""
    s = pygame.Surface((13, 24), pygame.SRCALPHA)
    pygame.draw.rect(s, MADEIRA_ESC, (6, 8, 2, 16))          # poste
    s.set_at((6, 12), MADEIRA)
    s.set_at((7, 18), MADEIRA)
    pygame.draw.rect(s, MADEIRA_ESC, (0, 0, 13, 9))
    pygame.draw.rect(s, MADEIRA, (1, 1, 11, 7))
    pygame.draw.line(s, (120, 84, 70), (1, 1), (11, 1))      # quina de cima mais clara
    pygame.draw.circle(s, LUA, (6, 4), 2)
    pygame.draw.rect(s, MADEIRA, (7, 2, 3, 5))               # meia-lua: quarto crescente, acesa à esquerda
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.wx = WW * 0.198
        self.lugares = [("lua_real", self.wx, "a lua de hoje")]
        self.placa = _placa()
        self.chave = None
        self.sprite = None
        self.p, self.k = 0.0, 0.0
        self.ultimo = -1e9
        self._atualizar()

    def _atualizar(self):
        """Recalcula a fase (no máximo 1× por minuto) e só refaz a máscara se ela mudou visivelmente."""
        agora = time.monotonic()
        if agora - self.ultimo < 60:
            return
        self.ultimo = agora
        self.p, self.k = fase(datetime.now(timezone.utc))
        chave = (self.p < 0.5, round(self.k * 60))
        if chave != self.chave:
            self.chave = chave
            self.sprite = mascara(self.p, self.k)

    def update(self):
        if self.mirante.t % 600 == 0:
            self._atualizar()

    def draw_ceu(self, ceu, ox):
        if self.sprite is None:
            return
        m = self.mirante
        lx, ly = m.lua_pos[0] - m.cam * 0.08, m.lua_pos[1]
        ceu.blit(self.sprite, (lx, ly))

    def draw_margem(self, m, cam):
        x = self.wx - cam
        if -16 < x < m.get_width() + 16:
            m.blit(self.placa, (int(x) - 6, PE - 24))
            if abs(self.mirante.x - self.wx) < 14:                # a meia-lua acende quando a Lume chega perto
                m.set_at((int(x) - 1, PE - 20), LUZ)

    def interagir(self, nome):
        self.ultimo = -1e9
        self._atualizar()
        agora = datetime.now(timezone.utc)
        nome_f = nome_fase(self.p)
        pct = round(self.k * 100)
        local = lambda d: d.astimezone()                       # horário do aparelho (no Brasil, de Brasília)
        fmt = lambda d: f"{local(d):%d/%m/%Y}, por volta das {local(d):%H:%M}"
        cheia, nova = proximo(agora, True), proximo(agora, False)
        lado = "à esquerda" if self.p < 0.5 else "à direita"
        if nome_f == "nova":
            p1 = f"Hoje a lua está nova: só {pct}% do disco voltado para cá está iluminado, e ela quase some no céu."
        elif nome_f == "cheia":
            p1 = f"Hoje a lua está cheia: {pct}% do disco iluminado."
        else:
            p1 = f"Hoje a lua está {nome_f}, com {pct}% do disco iluminado, aceso {lado} (como se vê do hemisfério sul)."
        self.mirante._falar([
            p1 + " A lua deste céu acompanha a de verdade.",
            f"Próxima lua cheia: {fmt(cheia)}. Próxima lua nova: {fmt(nova)}.",
            "No hemisfério sul a lua crescente acende do lado esquerdo e desenha um C. A conta é feita aqui mesmo, "
            "sem internet, pelo ciclo de 29,53 dias com as correções da órbita.",
        ])
