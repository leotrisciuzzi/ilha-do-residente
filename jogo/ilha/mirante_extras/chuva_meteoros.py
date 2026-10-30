"""Calendário de pedra — as grandes chuvas de meteoros do ano, marcadas numa laje à beira do lago.

Uma pedra em pé com um anel de oito entalhes, um para cada chuva anual importante. Quando a data de hoje cai na
janela de atividade de uma chuva, o entalhe dela acende e meteoros extras riscam o céu do Mirante, todos saindo
de um mesmo ponto radiante (a perspectiva de partículas paralelas entrando na atmosfera), mais frequentes perto do
pico. Fora das janelas a pedra fica apagada e o céu não ganha nada.

Datas e taxas seguem os valores consolidados (calendário da International Meteor Organization), arredondados para
baixo quando há variação de ano para ano. A "taxa horária zenital" (THZ) é um máximo teórico: céu perfeitamente
escuro e radiante no zênite. Na prática se vê bem menos, e isso é dito na fala.
"""
import datetime
import math
import random

import pygame

from . import Base
from ..mirante import HZ, LW, LUZ, MARGEM_CLARA, MARGEM_ESCURA, PAR_CEU, PE, WW

FRACAO = 0.234

# nome, início (mês, dia), pico, fim, constelação radiante, corpo de origem, THZ conservadora, observação
CHUVAS = [
    ("Quadrântidas", (12, 28), (1, 3), (1, 12), "Boieiro (Boötes), perto da antiga constelação Quadrans Muralis",
     "o asteroide 2003 EH1, provavelmente um cometa extinto", 80,
     "O pico é estreito, de poucas horas, e o radiante fica muito ao norte: do Brasil quase não se vê."),
    ("Líridas", (4, 14), (4, 22), (4, 30), "Lira (perto da estrela Vega)",
     "o cometa C/1861 G1 (Thatcher)", 18,
     "Do Brasil o radiante sobe pouco no céu, então a contagem real costuma ser baixa."),
    ("Eta Aquáridas", (4, 19), (5, 6), (5, 28), "Aquário",
     "o cometa 1P/Halley", 50,
     "É uma chuva melhor no hemisfério sul: no Brasil, a madrugada antes do amanhecer é a melhor hora."),
    ("Delta Aquáridas do Sul", (7, 12), (7, 30), (8, 23), "Aquário",
     "provavelmente o cometa 96P/Machholz (a ligação ainda é discutida)", 25,
     "Meteoros fracos e lentos; também favorece o hemisfério sul."),
    ("Perseidas", (7, 17), (8, 12), (8, 24), "Perseu",
     "o cometa 109P/Swift-Tuttle", 100,
     "É a mais famosa do hemisfério norte; do Brasil o radiante fica baixo ou abaixo do horizonte, e se vê pouco."),
    ("Oriônidas", (10, 2), (10, 21), (11, 7), "Órion (perto de Betelgeuse)",
     "o cometa 1P/Halley", 20,
     "Nesta época o radiante nasce antes da meia-noite; a melhor hora é a madrugada. Os meteoros são rápidos."),
    ("Leônidas", (11, 6), (11, 17), (11, 30), "Leão",
     "o cometa 55P/Tempel-Tuttle", 15,
     "Em alguns anos raros, quando a Terra cruza uma trilha fresca do cometa, já houve tempestades de milhares por hora."),
    ("Gemínidas", (12, 4), (12, 14), (12, 20), "Gêmeos (perto de Castor)",
     "o asteroide 3200 Faetonte", 120,
     "É a mais intensa do ano e boa também no Brasil, a partir do fim da noite."),
]


def _janela(ch, ano_pico):
    """Datas de início, pico e fim da chuva cujo pico cai em `ano_pico` (a Quadrântidas começa no ano anterior)."""
    _, ini, pico, fim = ch[:4]
    d_pico = datetime.date(ano_pico, *pico)
    d_ini = datetime.date(ano_pico - (1 if ini[0] > pico[0] else 0), *ini)
    d_fim = datetime.date(ano_pico, *fim)
    return d_ini, d_pico, d_fim


def ativa(hoje):
    """(índice, intensidade 0..1, janela) da chuva ativa hoje, a de maior intensidade; ou (None, 0, None)."""
    melhor = (None, 0.0, None)
    for i, ch in enumerate(CHUVAS):
        for ano in (hoje.year, hoje.year + 1):
            ini, pico, fim = _janela(ch, ano)
            if ini <= hoje <= fim:
                lado = (pico - ini).days if hoje <= pico else (fim - pico).days
                d = abs((hoje - pico).days) / max(1, lado)
                k = 0.15 + 0.85 * math.exp(-(d * 2.2) ** 2)          # forte perto do pico, fraco nas pontas
                k *= 0.45 + 0.55 * min(1.0, math.log10(ch[6]) / 2)    # chuvas fracas dão menos meteoros
                if k > melhor[1]:
                    melhor = (i, k, (ini, pico, fim))
    return melhor


def proxima(hoje):
    """(índice, dias até o início, dias até o pico) da próxima chuva que ainda vai começar."""
    melhor = None
    for i, ch in enumerate(CHUVAS):
        for ano in (hoje.year, hoje.year + 1, hoje.year + 2):
            ini, pico, _ = _janela(ch, ano)
            if ini > hoje:
                if melhor is None or (ini - hoje).days < melhor[1]:
                    melhor = (i, (ini - hoje).days, (pico - hoje).days)
                break
    return melhor


def _dias(n):
    return "amanhã" if n == 1 else f"em {n} dias"


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x = WW * FRACAO
        self.lugares = [("calendario_pedra", self.x, "ler o calendário de pedra")]
        self.hoje = datetime.date.today()
        self.i_ativa, self.forca, self.janela = ativa(self.hoje)
        self.rng = random.Random()
        self.meteoros = []                    # [x, y, dx, dy, vida, vida_total, comprimento] em coordenadas do céu
        self.espera = 60
        # radiante: fixo no céu, acima e à direita de onde a pedra fica na tela (diferente para cada chuva)
        ox_pedra = max(0.0, min(WW - LW, self.x - LW * 0.5)) * PAR_CEU
        i = self.i_ativa if self.i_ativa is not None else 0
        r = random.Random(i * 7 + 3)
        self.rad = (ox_pedra + LW * (0.38 + r.uniform(0, 0.3)), HZ * (0.16 + r.uniform(0, 0.16)))
        self.pedra = self._pedra()

    # ------------------------------------------------------------ desenho pronto da pedra
    def _pedra(self):
        """Um disco de pedra em pé sobre um pedestal baixo, com o anel do ano entalhado."""
        s = pygame.Surface((24, 30), pygame.SRCALPHA)
        corpo, claro, escuro, fundo = (62, 66, 98), (98, 104, 140), (30, 32, 56), (44, 46, 76)
        pygame.draw.rect(s, escuro, (5, 21, 14, 9))                   # pedestal
        pygame.draw.rect(s, corpo, (6, 21, 12, 8))
        pygame.draw.line(s, claro, (6, 21), (6, 28))
        pygame.draw.rect(s, escuro, (3, 27, 18, 3))                   # laje do chão
        pygame.draw.line(s, corpo, (4, 27), (19, 27))
        pygame.draw.circle(s, escuro, (12, 11), 11)                   # disco
        pygame.draw.circle(s, corpo, (12, 11), 10)
        pygame.draw.arc(s, claro, (2, 1, 20, 20), math.pi * 0.5, math.pi * 1.05)   # borda que a lua ilumina
        pygame.draw.circle(s, fundo, (12, 11), 5)                     # miolo rebaixado
        pygame.draw.circle(s, escuro, (12, 11), 5, 1)
        for k in range(4):                                            # raios do miolo (uma estrela de quatro pontas)
            ang = k * math.pi / 2
            s.set_at((int(12 + math.cos(ang) * 3), int(11 + math.sin(ang) * 3)), escuro)
        s.set_at((12, 11), claro)
        s.set_at((17, 16), (60, 92, 76))                              # líquen
        s.set_at((18, 15), (60, 92, 76))
        s.set_at((9, 24), (60, 92, 76))
        return s

    def _pos_entalhe(self, i):
        # ano começando no alto, em sentido horário, mais ou menos pelo mês do pico
        mes, dia = CHUVAS[i][2]
        ang = -math.pi / 2 + 2 * math.pi * ((mes - 1) + dia / 31) / 12
        return 12 + math.cos(ang) * 7.6, 11 + math.sin(ang) * 7.6

    # ------------------------------------------------------------ céu
    def update(self):
        if self.i_ativa is None:
            return
        for m in self.meteoros:
            m[0] += m[2]
            m[1] += m[3]
            m[4] -= 1
        self.meteoros = [m for m in self.meteoros if m[4] > 0]
        self.espera -= 1
        if self.espera <= 0 and len(self.meteoros) < 3:
            # perto do pico de uma chuva forte: um a cada ~1,5 s; nas pontas da janela, a cada ~10 s
            self.espera = int(self.rng.expovariate(1.0) * (70 + 520 * (1 - self.forca))) + 12
            ang = self.rng.uniform(0, 2 * math.pi)
            if math.sin(ang) < -0.5:                                  # quase nada sobe para fora do céu
                ang = -ang
            r0 = self.rng.uniform(4, 30)                              # nasce já afastado do radiante
            v = self.rng.uniform(1.6, 2.6)
            vida = self.rng.randint(14, 26)
            self.meteoros.append([self.rad[0] + math.cos(ang) * r0, self.rad[1] + math.sin(ang) * r0,
                                  math.cos(ang) * v, math.sin(ang) * v, vida, vida, self.rng.randint(6, 11)])

    def draw_ceu(self, ceu, ox):
        if self.i_ativa is None:
            return
        for x, y, dx, dy, vida, total, comp in self.meteoros:
            sx = x - ox
            if sx < -20 or sx > LW + 20 or y > HZ:
                continue
            f = math.sin(math.pi * vida / total)                       # acende e apaga
            n = math.hypot(dx, dy) or 1
            ux, uy = dx / n, dy / n
            for k in range(comp):
                g = f * (1 - k / comp)
                if g < 0.06:
                    break
                cor = (int(200 * g), int(225 * g), int(255 * g))       # meteoros frios, levemente azulados
                ceu.fill(cor, (int(sx - ux * k), int(y - uy * k), 1, 1), special_flags=pygame.BLEND_RGB_ADD)
            if f > 0.6:
                ceu.set_at((int(sx), int(y)), (255, 255, 250))

    # ------------------------------------------------------------ margem
    def draw_margem(self, m, cam):
        px = self.x - cam
        if not -20 < px < LW + 20:
            return
        base = PE + 1
        pygame.draw.ellipse(m, MARGEM_ESCURA, (px - 13, base - 2, 26, 5))  # sombra
        m.blit(self.pedra, (px - 12, base - 30))
        t = self.mirante.t
        alvo = self.i_ativa
        prox = proxima(self.hoje) if alvo is None else None
        for i in range(len(CHUVAS)):
            ex, ey = self._pos_entalhe(i)
            x, y = int(px - 12 + ex), int(base - 30 + ey)
            if i == alvo:
                pulso = 0.7 + 0.3 * math.sin(t * 0.06)
                m.set_at((x, y), tuple(int(c * pulso) for c in LUZ))
                m.blit(self.mirante.halo[3], (x - 3, y - 3), special_flags=pygame.BLEND_RGB_ADD)
            elif prox and i == prox[0]:
                m.set_at((x, y), (110, 120, 170))                        # a próxima: só um tom mais claro
            else:
                m.set_at((x, y), (26, 28, 48))
        # pedrinhas aos pés
        pygame.draw.rect(m, MARGEM_CLARA, (px - 14, base, 3, 2))
        pygame.draw.rect(m, MARGEM_CLARA, (px + 11, base + 1, 2, 1))

    # ------------------------------------------------------------ fala
    def interagir(self, nome):
        hoje = self.hoje
        p = []
        if self.i_ativa is not None:
            ch = CHUVAS[self.i_ativa]
            ini, pico, fim = self.janela
            dp = (pico - hoje).days
            quando = ("O pico é hoje." if dp == 0 else f"O pico é {_dias(dp)}, em {pico.day}/{pico.month}." if dp > 0
                      else f"O pico foi há {-dp} dia{'s' if dp < -1 else ''}, em {pico.day}/{pico.month}.")
            p.append(f"Um entalhe aceso: {ch[0]} estão ativas agora, de {ini.day}/{ini.month} a {fim.day}/{fim.month}. "
                     f"{quando} Os meteoros extras no céu do Mirante saem do radiante dela.")
            p.append(f"O radiante fica em {ch[4]}. Os meteoros são grãos deixados por {ch[5]}; a Terra cruza essa "
                     f"trilha todo ano na mesma época, por isso a data se repete.")
            p.append(f"No pico, a taxa horária zenital é de cerca de {ch[6]} meteoros por hora: é o máximo teórico, "
                     f"com céu perfeitamente escuro e o radiante bem alto. Na prática, mesmo longe da cidade, "
                     f"se vê bem menos. Longe do pico, menos ainda.")
            p.append(ch[7])
        else:
            p.append("Nenhum entalhe aceso: hoje não há nenhuma das grandes chuvas anuais em atividade, então o céu "
                     "fica só com os meteoros esporádicos de sempre.")
        pr = proxima(hoje)
        if pr:
            ch = CHUVAS[pr[0]]
            p.append(f"A próxima a começar: {ch[0]}, {_dias(pr[1])}, com pico {_dias(pr[2])}. Radiante em "
                     f"{ch[4].split(' (')[0]}; origem: {ch[5]}; cerca de {ch[6]} por hora no pico, em condições ideais.")
        p.append("As datas mudam um ou dois dias de um ano para outro, e a Lua cheia perto do pico apaga a maioria "
                 "dos meteoros fracos. Para ver de verdade: lugar escuro, uns 20 minutos para os olhos se acostumarem, "
                 "e olhar para o céu aberto, não direto para o radiante.")
        self.mirante._falar(p)
