"""A constelação de hoje — as questões respondidas desde a meia-noite formam um desenho próprio no céu.

Cada questão cuja última resposta foi hoje vira uma estrela num canto alto e à esquerda do céu. O lugar de cada
estrela vem do id da questão (sempre o mesmo), e as estrelas são ligadas por linhas finas na ordem do horário
em que foram respondidas: o traço é o caminho do dia. Ao entrar no Mirante, o traço se desenha aos poucos.
Acertos são estrelas claras; erros, brasas. Num dia sem questões, sobra só um pontinho tímido.

Na margem fica a pedra de contar: sete risquinhos, um por dia da última semana, acesos nos dias com estudo.
Interagir com ela mostra o número de hoje, a porcentagem de acerto e um histórico curto dos últimos 7 dias.
Os dias contam cada questão pela data da última resposta (o save não guarda as respostas anteriores)."""
import math
import random
import time

import pygame

from . import Base
from ..mirante import HZ, MARGEM_CLARA, MARGEM_ESCURA, PE, SW, WW, _h

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
QUADROS_POR_TRACO = 5          # velocidade com que o traço do dia se desenha


def _meia_noite(dias_atras=0):
    """Timestamp da meia-noite local de `dias_atras` dias atrás (mktime normaliza o dia e o horário de verão)."""
    lt = time.localtime()
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday - dias_atras, 0, 0, 0, 0, 0, -1))


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.lugares = [("pedra_contar", WW * 0.161, "ler a pedra de contar")]
        # região do céu (coordenadas do céu)
        self.x0, self.x1 = SW * 0.05, SW * 0.22
        self.y0, self.y1 = 4, HZ * 0.35
        qs = mirante.app.save.d.get("q", {}) or {}
        hoje0 = _meia_noite(0)
        hoje = []
        for qid, st in qs.items():
            try:
                ult = float(st.get("ult", 0) or 0)
            except (TypeError, ValueError, AttributeError):
                continue
            if ult >= hoje0:
                hoje.append((ult, str(qid), bool(st.get("ok"))))
        hoje.sort()
        self.n = len(hoje)
        self.certas = sum(1 for _, _, ok in hoje if ok)
        # posições determinísticas por id, afastando das já postas (para não empilhar)
        self.pts = []                                   # [x, y, ok, fase]
        for _, qid, ok in hoje:
            rng = random.Random(_h("hoje:" + qid))
            for tent in range(12):
                x = rng.uniform(self.x0, self.x1)
                y = rng.uniform(self.y0, self.y1)
                if all((x - p[0]) ** 2 + (y - p[1]) ** 2 >= 9 for p in self.pts) or tent == 11:
                    break
            self.pts.append((x, y, ok, (_h(qid) % 628) / 100.0))
        # últimos 7 dias (de 6 dias atrás até hoje)
        cortes = [_meia_noite(k) for k in range(6, -1, -1)] + [float("inf")]
        self.semana = []
        for k in range(7):
            a, b = cortes[k], cortes[k + 1]
            n = 0
            for st in qs.values():
                try:
                    u = float(st.get("ult", 0) or 0)
                except (TypeError, ValueError, AttributeError):
                    continue
                if a <= u < b:
                    n += 1
            self.semana.append((DIAS[time.localtime(a + 3600 * 12).tm_wday], n))
        self.t0 = mirante.t
        self.traco, self.assados = None, 0              # traço já desenhado (só os segmentos antigos, apagados)
        self.pedra = self._fazer_pedra()

    # --------------------------------------------------------- peças desenhadas uma vez
    def _fazer_pedra(self):
        s = pygame.Surface((16, 11), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (54, 58, 84), (0, 1, 16, 10))
        pygame.draw.ellipse(s, (74, 78, 108), (1, 1, 13, 6))
        pygame.draw.ellipse(s, (40, 42, 64), (2, 7, 13, 4))
        return s

    def _assar(self, ate):
        """Grava na superfície do traço (preta, somada ao céu) os segmentos já apagados, até o índice `ate`."""
        if self.traco is None:
            self.traco = pygame.Surface((int(self.x1 - self.x0) + 12, int(self.y1 - self.y0) + 12))
            self.assados = 0
        bx, by = self.x0 - 6, self.y0 - 6
        while self.assados < ate:
            a, b = self.pts[self.assados], self.pts[self.assados + 1]
            pygame.draw.aaline(self.traco, self._cor_linha(a, b, 0.4), (a[0] - bx, a[1] - by), (b[0] - bx, b[1] - by))
            self.assados += 1

    @staticmethod
    def _cor_linha(a, b, k=1.0):
        base = (52, 64, 108) if (a[2] and b[2]) else (70, 44, 62)
        return tuple(int(v * k) for v in base)

    # --------------------------------------------------------- ganchos
    def interagir(self, nome):
        if self.n == 0:
            p1 = "Hoje ainda nenhuma questão. O canto do céu à esquerda, lá no alto, guarda só um pontinho esperando."
        else:
            pct = round(100 * self.certas / self.n)
            q = "questão" if self.n == 1 else "questões"
            p1 = (f"Hoje: {self.n} {q}, {self.certas} certa{'s' if self.certas != 1 else ''} ({pct}%). "
                  "Lá no alto, à esquerda, elas formam a constelação do dia, ligadas na ordem em que você respondeu.")
        hist = " · ".join(f"{d} {n}" for d, n in self.semana)
        p2 = (f"Últimos 7 dias: {hist}. "
              "Cada questão conta no dia da sua última resposta.")
        self.t0 = self.mirante.t                       # redesenha o traço, para ver o caminho de novo
        if self.traco is not None:
            self.traco.fill((0, 0, 0))
            self.assados = 0
        self.mirante._falar([p1, p2])

    def draw_ceu(self, ceu, ox):
        t = self.mirante.t
        if self.x1 - ox < -4:                           # fora da tela
            return
        if not self.pts:                                # dia vazio: um pontinho tímido
            k = 0.5 + 0.5 * math.sin(t * 0.02)
            v = int(40 + 30 * k)
            ceu.set_at((int((self.x0 + self.x1) / 2 - ox), int((self.y0 + self.y1) / 2)), (v, v, v + 30))
            return
        segs = len(self.pts) - 1
        feito = min(segs, (t - self.t0) / QUADROS_POR_TRACO)   # quantos traços já desenhados (fracionário)
        inteiros = int(feito)
        recentes = 0 if inteiros >= segs else 8                # ao fim da animação tudo fica apagado igual
        self._assar(max(0, inteiros - recentes))
        if self.assados:
            ceu.blit(self.traco, (self.x0 - 6 - ox, self.y0 - 6), special_flags=pygame.BLEND_RGB_ADD)
        for i in range(self.assados, inteiros):                 # os traços recentes brilham mais
            a, b = self.pts[i], self.pts[i + 1]
            k = max(0.4, 1.0 - (inteiros - i) / 8)
            pygame.draw.aaline(ceu, self._cor_linha(a, b, k), (a[0] - ox, a[1]), (b[0] - ox, b[1]))
        if inteiros < segs:                                     # o traço em andamento
            a, b = self.pts[inteiros], self.pts[inteiros + 1]
            f = feito - inteiros
            px, py = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            pygame.draw.aaline(ceu, (90, 104, 160), (a[0] - ox, a[1]), (px - ox, py))
            ceu.set_at((int(px - ox), int(py)), (200, 210, 255))
            mostra = inteiros + 1
        else:
            mostra = len(self.pts)
        halo = self.mirante.halo[3]
        for i, (x, y, ok, fase) in enumerate(self.pts[:mostra]):
            sx = int(x - ox)
            if sx < -3 or sx > ceu.get_width() + 3:
                continue
            tw = 0.75 + 0.25 * math.sin(t * 0.05 + fase)
            if ok:                                      # acerto: estrela clara, levemente azulada
                v = int(170 + 85 * tw)
                ceu.blit(halo, (sx - 3, int(y) - 3), special_flags=pygame.BLEND_RGB_ADD)
                ceu.set_at((sx, int(y)), (v, v, 255))
            else:                                       # erro: brasa que tremula
                v = int(110 + 60 * tw)
                ceu.set_at((sx, int(y)), (v + 60, v - 40, v - 80))
                ceu.set_at((sx + 1, int(y)), (int(v * 0.5), int(v * 0.18), 10))
        if mostra == len(self.pts):                     # a última resposta do dia pisca de leve
            x, y = self.pts[-1][0] - ox, self.pts[-1][1]
            if (t // 40) % 3 == 0:
                pygame.draw.circle(ceu, (60, 66, 110), (int(x), int(y)), 3, 1)

    def draw_margem(self, m, cam):
        x = WW * 0.161 - cam
        if not -20 < x < m.get_width() + 20:
            return
        t = self.mirante.t
        bx, by = int(x - 8), int(PE - 9)
        m.blit(self.pedra, (bx, by))
        # sete risquinhos: um por dia da semana; acesos nos dias com estudo, o de hoje mais quente
        for k, (_, n) in enumerate(self.semana):
            rx = bx + 2 + k * 2
            if n == 0:
                cor = (40, 42, 64)
            elif k == 6:
                p = 0.8 + 0.2 * math.sin(t * 0.06)
                cor = (int(255 * p), int(210 * p), int(130 * p))
            else:
                cor = (150, 160, 200)
            pygame.draw.line(m, cor, (rx, by + 3), (rx, by + 5))
        m.set_at((bx + 3, by + 10), MARGEM_CLARA)
        m.set_at((bx + 12, by + 10), MARGEM_ESCURA)
