"""A tartaruga da margem.

Uma tartaruguinha atravessa a margem inteira, devagar: leva uns doze minutos de jogo para ir de uma ponta à outra
e, ao chegar, vira e volta. Onde ela começa depende da hora do relógio (sempre a mesma posição para a mesma hora),
então quem volta ao Mirante encontra a tartaruga num ponto diferente do caminho. Se a Lume passa correndo perto,
ela recolhe a cabeça e as patas no casco e espera um pouco. Conversar com ela rende uma frase curta sobre
constância e revisão espaçada — o assunto preferido de quem anda a 0,025 pixel por quadro.

Lugar móvel: como o Mirante lê `lugares` só no início, a cada quadro a tupla "tartaruga" é trocada na lista do
Mirante pela posição atual."""
import time

import pygame

from . import Base
from .. import art
from ..mirante import PE, WW

QUADROS_TRAVESSIA = 12 * 60 * 60          # ~12 minutos a 60 quadros/s para cruzar a margem
X_MIN, X_MAX = 14.0, WW - 14.0
VEL = (X_MAX - X_MIN) / QUADROS_TRAVESSIA
ROTULO = "falar com a tartaruga"

PAL = {"O": (12, 16, 28), "S": (52, 98, 96), "s": (96, 150, 124), "L": (150, 196, 170), "B": (126, 110, 80),
       "h": (118, 148, 120), "k": (240, 226, 170)}

# virada para a direita; a cabeça ocupa as colunas 12–15
CASCO = [
    "....OOOOO.......",
    "..OOLLLLLOO.....",
    ".OsSSsSsSSsO....",
    ".OSSsSSSsSSO....",
    "OBBBBBBBBBBBO...",
]
CABECA = ["............OO..", "...........OhkO.", "...........OhhO."]   # linhas 1–3 (cabeça para fora)
PATAS = ["..hh.....hh.....", "...hh...hh......"]                      # dois passos
PATAS_DENTRO = ["..OO.....OO....."]

FRASES = [
    "Cheguei aqui revisando um passo por dia.",
    "Atravesso esta margem em doze minutos. Ninguém nunca me cronometrou, mas eu sei.",
    "Corri uma vez. Esqueci tudo no caminho de volta.",
    "Revisão espaçada é isto: voltar ao mesmo lugar logo antes de esquecer onde ele fica.",
    "Eu não estudo muito por dia. Só não paro.",
    "Quando não lembro, volto. Quando lembro, volto mais tarde. Esse é o método inteiro.",
    "Ir e voltar pela mesma margem não é andar em círculos. Na segunda vez eu reparo em outras pedras.",
    "Escondo a cabeça quando alguém passa correndo. Não é medo. É que eu estava no meio de um raciocínio.",
    "Errei a mesma questão três vezes. Na quarta, quem desistiu foi ela.",
    "Se você está esperando ter vontade de revisar, eu já passei por aqui duas vezes.",
    "Dez questões hoje e dez amanhã parecem pouco. Daqui a um ano viram outra coisa, e não é sorte.",
    "Não tenho pressa de chegar à outra ponta. Lá eu só vou virar e voltar.",
]


def _quadro(cabeca, passo):
    linhas = [list(r) for r in CASCO]
    if cabeca:
        for i, r in enumerate(CABECA):
            for x, ch in enumerate(r):
                if ch != ".":
                    linhas[1 + i][x] = ch
        pe = PATAS[passo]
    else:
        linhas[3][11] = "O"                                     # só a pontinha do casco fechada
        pe = PATAS_DENTRO[0]
    return art.spr(["".join(r) for r in linhas] + [pe], PAL)


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        lt = time.localtime()
        # posição determinística pela hora: um vaivém de 24 min de relógio "rebatido" no ciclo da tartaruga
        fase = ((lt.tm_hour * 60 + lt.tm_min) % 24) / 24.0
        if fase < 0.5:
            self.x, self.dir = X_MIN + (X_MAX - X_MIN) * fase * 2, 1
        else:
            self.x, self.dir = X_MAX - (X_MAX - X_MIN) * (fase - 0.5) * 2, -1
        self.frase_i = lt.tm_hour % len(FRASES)
        self.recolhida = 0                                      # quadros restantes com a cabeça no casco
        self.virando = 0                                        # pausa ao chegar à ponta
        self.passo_t = 0
        self.lugares = [("tartaruga", self.x, ROTULO)]
        # sprites prontos: (dir, cabeça para fora?, passo)
        self.spr = {}
        for cab in (True, False):
            for p in (0, 1):
                s = _quadro(cab, p)
                self.spr[(1, cab, p)] = s
                self.spr[(-1, cab, p)] = pygame.transform.flip(s, True, False)
        self.sombra = pygame.Surface((16, 3), pygame.SRCALPHA)
        pygame.draw.ellipse(self.sombra, (0, 0, 10, 90), (0, 0, 16, 3))

    def update(self):
        mir = self.mirante
        d = mir.x - self.x
        if abs(mir.vx) > 0.6 and abs(d) < 28:                   # a Lume passou correndo: recolhe
            self.recolhida = 150
        elif self.recolhida:
            self.recolhida -= 1
        conversando = abs(d) < 12 and (mir.fala or mir.modal)
        if self.virando:
            self.virando -= 1
            if self.virando == 0:
                self.dir = -self.dir
        elif not self.recolhida and not conversando:
            self.x += VEL * self.dir
            self.passo_t += 1
            if (self.dir > 0 and self.x >= X_MAX) or (self.dir < 0 and self.x <= X_MIN):
                self.x = max(X_MIN, min(X_MAX, self.x))
                self.virando = 90
        # lugar móvel: troca a tupla na lista do Mirante
        tup = ("tartaruga", self.x, ROTULO)
        self.lugares[0] = tup
        lug = mir.lugares
        for i, l in enumerate(lug):
            if l[0] == "tartaruga":
                lug[i] = tup
                break

    def interagir(self, nome):
        self.mirante._falar([FRASES[self.frase_i % len(FRASES)]])
        self.frase_i += 1
        self.recolhida = 0

    def draw_frente(self, m, cam):
        # anda numa faixa um pouco à frente da trilha da Lume, para não sumir atrás dela
        x = int(self.x - cam)
        if x < -20 or x > m.get_width() + 20:
            return
        cab = not self.recolhida
        passo = (self.passo_t // 24) % 2 if cab and not self.virando else 0
        s = self.spr[(self.dir, cab, passo)]
        y = PE + 8 - s.get_height()
        m.blit(self.sombra, (x - 8, PE + 6))
        m.blit(s, (x - 8, y))
