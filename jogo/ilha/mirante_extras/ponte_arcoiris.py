"""Ponte de arco-íris — o Mundo do Dia visto do Mirante.

Um arco-íris noturno, baixo e discreto, nasce do horizonte à direita do céu. Ele tem 5 faixas, uma para cada
passo do Mundo do Dia (Aquecimento por fora, Chefão por dentro). Passo vencido hoje = faixa acesa, em cor suave;
passo que falta = faixa apagada, só uns pontinhos. Com os 5 passos feitos, o arco inteiro cintila devagar.
A sequência de dias com o Chefão vencido vira estrelinhas logo acima do arco (uma por dia, até 14).

Na margem fica uma plaquinha de madeira ("caminho do dia") com 5 pontinhos nas mesmas cores; ler a placa conta
o estado de cada passo, a sequência e, se o plano de hoje já foi montado, o tema novo do dia.
Nada aqui é inventado: tudo vem de ilha.dia e do save."""
import datetime as dt
import math

import pygame

from . import Base
from ..mirante import HZ, MADEIRA, MADEIRA_ESC, PE, SW, WW

FRACAO = 0.538
# cores suaves das faixas, de fora para dentro (vermelho → violeta), na ordem de dia.PASSOS
CORES = [(150, 70, 80), (150, 120, 60), (70, 130, 80), (60, 90, 150), (110, 70, 140)]
LARG = 2                         # espessura de cada faixa (px do céu)
R_FORA = 36                      # raio externo do arco
BAIXO = 22                       # o centro fica abaixo do topo dos montes: os pés do arco somem atrás deles
NIVEIS = 6                       # níveis de brilho pré-renderizados para a cintilação


def _passos():
    try:
        from .. import dia
        return [(k, n) for k, n, _ in dia.PASSOS]
    except Exception:
        return [("aquecer", "Aquecimento"), ("novo", "Tema novo do dia"), ("hoje", "Aulas de hoje"),
                ("semana", "Revisão da semana"), ("chefao", "Chefão do dia")]


def _faixa(i, viva, ganho=1.0):
    """Uma faixa do arco numa Surface preta (para BLEND_RGB_ADD). Apagada = pontilhada e fraca."""
    r1 = R_FORA - i * LARG
    r0 = r1 - LARG
    w, h = R_FORA * 2 + 2, R_FORA + 2
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    cx, cy = R_FORA + 1, R_FORA + 1                     # centro do círculo na base da Surface (no horizonte)
    cor = CORES[i]
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if not r0 <= d < r1:
                continue
            ang = math.atan2(cy - y, x - cx)            # 0..pi
            # as pontas somem perto do horizonte, como um arco de luar
            pe = min(1.0, (cy - y) / (R_FORA * 0.7)) ** 1.3
            if viva:
                f = 0.42 * pe * ganho
            else:
                if int(ang * r1 / 2.2) % 3:            # pontilhado ao longo do arco
                    continue
                f = 0.2 * pe
            if f > 0.02:
                s.set_at((x, y), tuple(int(v * f) for v in cor))
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x = WW * FRACAO
        self.lugares = [("caminho_dia", self.x, "ler a placa do caminho do dia")]
        self.passos = _passos()
        self.vivas = [_faixa(i, True) for i in range(5)]
        self.apagadas = [_faixa(i, False) for i in range(5)]
        # arco completo em vários brilhos (cintilação barata: só escolher qual blitar)
        self.cheio = []
        for n in range(NIVEIS):
            g = 0.75 + 0.5 * n / (NIVEIS - 1)
            s = pygame.Surface(self.vivas[0].get_size())
            s.fill((0, 0, 0))
            for i in range(5):
                s.blit(_faixa(i, True, g), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            self.cheio.append(s)
        self.cx_ceu = SW * 0.64                        # centro do arco no céu
        self.feitos, self.seq = [False] * 5, 0
        self._ler()

    # ------------------------------------------------------------- estado
    def _ler(self):
        try:
            from .. import dia
            save, hoje = self.mirante.app.save, dt.date.today()
            self.feitos = [bool(dia.feito(save, hoje, k)) for k, _ in self.passos]
            self.seq = int(dia.sequencia(save, hoje))
        except Exception:
            self.feitos, self.seq = [False] * 5, 0

    def update(self):
        if self.mirante.t % 300 == 0:                   # o save só muda fora daqui; reler de vez em quando basta
            self._ler()

    # ------------------------------------------------------------- céu
    def draw_ceu(self, ceu, ox):
        x0 = self.cx_ceu - ox - R_FORA - 1
        if x0 > ceu.get_width() or x0 + R_FORA * 2 + 2 < 0:
            return
        y0 = HZ - BAIXO - R_FORA - 1
        t = self.mirante.t
        if all(self.feitos):
            n = int((0.5 + 0.5 * math.sin(t * 0.025)) * (NIVEIS - 1) + 0.5)
            ceu.blit(self.cheio[n], (x0, y0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            for i, f in enumerate(self.feitos):
                ceu.blit((self.vivas if f else self.apagadas)[i], (x0, y0), special_flags=pygame.BLEND_RGB_ADD)
        # a sequência: uma estrelinha por dia, sobre o arco
        k = min(self.seq, 14)
        if k:
            h3 = self.mirante.halo[3]
            cx, cy = self.cx_ceu - ox, HZ - BAIXO
            for j in range(k):
                a = math.pi * (0.82 - 0.64 * (j + 0.5) / 14) if k < 14 else math.pi * (0.82 - 0.64 * j / 13)
                r = R_FORA + 5 + (j % 2) * 2
                sx, sy = cx + math.cos(a) * r, cy - math.sin(a) * r
                pisca = 0.5 + 0.5 * math.sin(t * 0.04 + j * 1.7)
                if pisca > 0.25:
                    ceu.blit(h3, (sx - 3, sy - 3), special_flags=pygame.BLEND_RGB_ADD)
                ceu.set_at((int(sx), int(sy)), (255, 244, 200) if pisca > 0.5 else (200, 190, 160))

    # ------------------------------------------------------------- margem: a placa
    def draw_margem(self, m, cam):
        px = int(self.x - cam)
        if not -12 < px < m.get_width() + 12:
            return
        pygame.draw.line(m, MADEIRA_ESC, (px, PE - 11), (px, PE))
        pygame.draw.rect(m, MADEIRA_ESC, (px - 7, PE - 19, 15, 8))
        pygame.draw.rect(m, MADEIRA, (px - 6, PE - 18, 13, 6))
        t = self.mirante.t
        for i, f in enumerate(self.feitos):
            x, y = px - 4 + i * 2, PE - 16 + (i % 2)
            if f:
                cor = tuple(min(255, int(v * 1.6)) for v in CORES[i])
                m.set_at((x, y), cor)
            else:
                m.set_at((x, y), (60, 42, 44))
        if all(self.feitos) and (t // 20) % 6 == 0:
            m.blit(self.mirante.halo[4], (px - 4, PE - 19), special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------- fala
    def interagir(self, nome):
        self._ler()
        n = sum(self.feitos)
        linhas = [f"{nome_p}: {'feito' if f else 'falta'}." for (_, nome_p), f in zip(self.passos, self.feitos)]
        p1 = f"Caminho do dia — {n} de 5 passos hoje. " + " ".join(linhas)
        if self.seq == 0:
            p2 = "Sequência: nenhum dia seguido com o Chefão vencido ainda. Cada dia fechado vira uma estrelinha sobre o arco."
        elif self.seq == 1:
            p2 = "Sequência: 1 dia com o Chefão vencido. Ele está lá em cima, como uma estrelinha sobre o arco."
        else:
            p2 = f"Sequência: {self.seq} dias seguidos com o Chefão vencido. Cada um é uma estrelinha sobre o arco" + \
                 (" (o céu mostra até 14)." if self.seq > 14 else ".")
        paginas = [p1, p2]
        try:
            plano = getattr(self.mirante.app, "_dia", None)
            if isinstance(plano, dict) and plano.get("data", dt.date.today()) == dt.date.today():
                rot = plano["passos"]["novo"]["rotulo"]
                if rot:
                    paginas.append(f"No plano de hoje, o passo 2 é: {rot}.")
        except Exception:
            pass
        if n == 5:
            paginas.append("Os 5 passos de hoje estão feitos; o arco inteiro acende. Amanhã ele recomeça apagado.")
        else:
            paginas.append("Cada passo vencido acende uma faixa do arco no céu, de fora para dentro. "
                           "O Mundo do Dia é o primeiro item do menu.")
        self.mirante._falar(paginas)
