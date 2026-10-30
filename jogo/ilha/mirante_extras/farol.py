"""O farol — um farolzinho sobre pedras na ponta esquerda da margem.

O facho gira devagar e varre o céu e o lago. A força e a velocidade dele vêm do save: quantas questões estão
vencidas para revisão agora (prox <= agora). Nenhuma vencida = facho calmo e fraco; muitas = facho mais forte e
mais rápido, como um aviso. A lâmpada pisca em código Morse a palavra CALMA, num ritmo lento o bastante para
ser lido. O faroleiro, ao lado da porta, conta as vencidas por mundo/matéria e lembra por que revisar no dia
certo importa.

Tudo pré-renderizado no __init__ (pedras, torre, faroleiro, cones do facho e reflexos); por quadro só há blits."""
import math
import time

import pygame

from . import Base
from ..mirante import GY, HZ, LUZ, MARGEM, MARGEM_CLARA, MARGEM_ESCURA, PE, WW, _grupo
from .. import art

X = WW * 0.028
LAMP_Y = GY - 34                     # altura da lâmpada no mundo
ALCANCE = 150                        # comprimento máximo do facho (px do mundo)
N_CONES = 16                         # quantos comprimentos pré-renderizados

# Morse de CALMA: C -.-.  A .-  L .-..  M --  A .-
MORSE = {"C": "-.-.", "A": ".-", "L": ".-..", "M": "--"}
UNIDADE = 10                         # quadros por unidade (~0,17 s a 60 fps)

# nomes dos mundos que o Mirante ainda não conhece
NOMES_EXTRA = {"uas": "Asma", "udp": "DPOC", "uvm": "VM", "utr": "Transfusão",
               "urm": "Reumato", "dia": "Tema do dia"}

PAL_FAROLEIRO = {"O": (20, 18, 36), "b": (40, 52, 86), "B": (58, 74, 116), "p": (226, 184, 150),
                 "w": (210, 214, 230), "y": (255, 214, 130)}
FAROLEIRO = [
    ".OOO..",
    "ObbbO.",
    ".OpO..",
    ".wpw..",
    "OBBBOy",
    "OBBBO.",
    ".BbB..",
    ".O.O..",
]


def _sequencia(palavra):
    """Lista de booleanos (uma entrada por unidade): aceso/apagado."""
    seq = []
    for i, letra in enumerate(palavra):
        for j, s in enumerate(MORSE[letra]):
            seq += [True] * (1 if s == "." else 3)
            if j < len(MORSE[letra]) - 1:
                seq += [False]                      # entre sinais
        seq += [False] * (3 if i < len(palavra) - 1 else 7)   # entre letras / fim da palavra
    return seq


def _cone(f, brilho):
    """Facho apontando para a direita, comprimento f*ALCANCE, levemente para cima. Fundo preto (para ADD)."""
    L = max(2, int(ALCANCE * f))
    sobe = 0.3                                     # inclinação: sobe 3 px a cada 10
    alt = int(L * sobe) + 30
    s = pygame.Surface((L, alt))
    s.fill((0, 0, 0))
    y0 = alt - 15                                  # a lâmpada fica em (0, y0)
    for x in range(L):
        u = x / L
        meia = 1 + u * (4 + 7 * f)                 # o cone abre com a distância
        cy = y0 - x * sobe
        k = brilho * (1 - u) ** 1.4 * (0.55 + 0.45 * f)
        for dy in range(-int(meia), int(meia) + 1):
            borda = 1 - (abs(dy) / (meia + 1)) ** 2
            c = (int(120 * k * borda), int(108 * k * borda), int(66 * k * borda))
            if c[0] > 0:
                s.set_at((x, int(cy + dy)), c)
    return s, y0


def _reflexo(f, brilho):
    """Rastro tracejado na água sob o facho (só para a direita; o esquerdo é espelhado)."""
    L = max(2, int(ALCANCE * 0.9 * f))
    s = pygame.Surface((L, 5))
    s.fill((0, 0, 0))
    for x in range(L):
        u = x / L
        if (x * 7 + int(u * 13)) % 5 == 0:
            continue
        k = brilho * (1 - u) ** 1.2 * f * 0.55
        c = (int(60 * k), int(54 * k), int(34 * k))
        s.set_at((x, 2 + (x // 6) % 2 - (x // 11) % 2), c)
    return s


def _torre():
    """Pedras + torre + lanterna (sem a luz da lâmpada). Retorna (surface, ponto da lâmpada dentro dela)."""
    w, h = 36, 50
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, base = w // 2, h - 8                       # base = GY no mundo
    # pedras
    for (px, py, rw, rh, cor) in [(-16, -3, 12, 9, MARGEM_ESCURA), (-6, -1, 14, 10, MARGEM), (5, -2, 12, 9, MARGEM_ESCURA),
                                  (-12, 3, 10, 7, MARGEM), (2, 4, 13, 6, MARGEM_ESCURA), (-3, -4, 9, 5, (34, 44, 62))]:
        pygame.draw.ellipse(s, cor, (cx + px, base + py, rw, rh))
    for (px, py) in [(-12, -2), (-3, -3), (8, -1), (-9, 4)]:
        pygame.draw.line(s, MARGEM_CLARA, (cx + px, base + py), (cx + px + 3, base + py))
    # torre: cônica, faixas claras/escuras
    topo, alto = base - 28, 28
    for y in range(topo, base):
        u = (y - topo) / alto
        meia = 2.5 + u * 3
        faixa = ((y - topo) // 5) % 2
        cor = (186, 182, 204) if faixa == 0 else (128, 62, 74)
        cor = art.mix(cor, (30, 30, 60), 0.25)
        pygame.draw.line(s, cor, (cx - meia, y), (cx + meia, y))
        s.set_at((int(cx + meia), y), art.mix(cor, (14, 14, 34), 0.45))       # sombra do lado direito
        s.set_at((int(cx - meia), y), art.mix(cor, (14, 14, 34), 0.25))
    pygame.draw.rect(s, (30, 26, 40), (cx - 1, base - 5, 3, 5))                # porta
    # varanda, lanterna e telhado
    pygame.draw.line(s, (40, 40, 66), (cx - 5, topo), (cx + 5, topo))
    pygame.draw.line(s, (70, 70, 100), (cx - 5, topo - 1), (cx + 5, topo - 1))
    pygame.draw.rect(s, (40, 40, 66), (cx - 3, topo - 6, 7, 5))
    pygame.draw.polygon(s, (60, 36, 46), [(cx - 4, topo - 6), (cx + 4, topo - 6), (cx, topo - 10)])
    s.set_at((cx, topo - 11), (90, 90, 120))
    return s, (cx, topo - 4), base


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.lugares = [("farol", X, "falar com o faroleiro")]
        self.venc = self._vencidas()
        n = sum(self.venc.values())
        self.n = n
        self.k = min(1.0, math.log1p(n) / math.log1p(150))       # 0 = calmo, 1 = muitas vencidas
        self.vel = 0.0035 + 0.0105 * self.k                      # rad/quadro: ~30 s a ~7 s por volta
        brilho = 0.35 + 0.75 * self.k
        self.cones = [_cone((i + 1) / N_CONES, brilho) for i in range(N_CONES)]
        self.cones_esq = [(pygame.transform.flip(c, True, False), y0) for c, y0 in self.cones]
        self.reflexos = [_reflexo((i + 1) / N_CONES, brilho) for i in range(N_CONES)]
        self.reflexos_esq = [pygame.transform.flip(r, True, False) for r in self.reflexos]
        self.torre, self.lamp, self.base = _torre()
        self.faroleiro = art.spr(FAROLEIRO, PAL_FAROLEIRO)
        self.morse = _sequencia("CALMA")
        self.ang = 1.3

    # ----------------------------------------------------------------- dados
    def _vencidas(self):
        agora = time.time()
        banco = getattr(self.mirante.app, "banco", None)
        por_id = getattr(banco, "por_id", None) or {}
        out = {}
        for qid, st in (self.mirante.app.save.d.get("q") or {}).items():
            try:
                if not isinstance(st, dict) or st.get("prox", agora + 1) > agora:
                    continue
            except TypeError:
                continue
            pre = qid.split(":")[0].split("-")[0]
            g = NOMES_EXTRA.get(pre) or _grupo(qid)
            if g in ("Provas reais", "Outras"):
                q = por_id.get(qid)
                mat = q.get("materia") if isinstance(q, dict) else None
                if mat:
                    g = str(mat).replace("_", " ").capitalize()
            out[g] = out.get(g, 0) + 1
        return out

    # ----------------------------------------------------------------- lógica
    def update(self):
        self.ang = (self.ang + self.vel) % (2 * math.pi)

    def _aceso(self):
        return self.morse[(self.mirante.t // UNIDADE) % len(self.morse)]

    # ----------------------------------------------------------------- desenho
    def draw_lago(self, m, cam):
        lx = X - cam
        if not -ALCANCE - 10 < lx < m.get_width() + ALCANCE + 10:
            return
        c = math.cos(self.ang)
        f = abs(c)
        i = min(N_CONES - 1, int(f * N_CONES))
        if i < 1:
            return
        ly = LAMP_Y
        if c > 0:
            cone, y0 = self.cones[i]
            m.blit(cone, (lx, ly - y0), special_flags=pygame.BLEND_RGB_ADD)
            m.blit(self.reflexos[i], (lx + 6, HZ + 3 + int(math.sin(self.mirante.t * 0.05))), special_flags=pygame.BLEND_RGB_ADD)
        else:
            cone, y0 = self.cones_esq[i]
            m.blit(cone, (lx - cone.get_width(), ly - y0), special_flags=pygame.BLEND_RGB_ADD)
            r = self.reflexos_esq[i]
            m.blit(r, (lx - 6 - r.get_width(), HZ + 3 + int(math.sin(self.mirante.t * 0.05))), special_flags=pygame.BLEND_RGB_ADD)

    def draw_margem(self, m, cam):
        lx = X - cam
        if not -30 < lx < m.get_width() + 30:
            return
        ox, oy = lx - self.lamp[0], GY - self.base
        m.blit(self.torre, (ox, oy))
        m.blit(self.faroleiro, (lx + 7, GY - 6))
        px, py = ox + self.lamp[0], oy + self.lamp[1]
        # a lanterna: aceso/apagado no Morse; o facho de frente dá um clarão
        frente = max(0.0, math.sin(self.ang)) ** 8
        if self._aceso():
            pygame.draw.rect(m, LUZ, (px - 2, py - 1, 5, 3))
            m.blit(self.mirante.halo[9], (px - 9 + 0.5, py - 9 + 0.5), special_flags=pygame.BLEND_RGB_ADD)
        else:
            pygame.draw.rect(m, (96, 76, 56), (px - 2, py - 1, 5, 3))
        if frente > 0.3:
            m.blit(self.mirante.halo[5 if frente < 0.8 else 9], (px - (5 if frente < 0.8 else 9) + 0.5, py - (5 if frente < 0.8 else 9) + 0.5),
                   special_flags=pygame.BLEND_RGB_ADD)
        for dx in (-3, -1, 1, 3):                                   # caixilhos da lanterna
            m.set_at((int(px + dx), int(py - 1)), (40, 40, 66))

    # ----------------------------------------------------------------- conversa
    def interagir(self, nome):
        n = self.n
        if n == 0:
            p1 = ("O faroleiro confere o caderno: nenhuma questão vencida para revisão agora. Por isso o facho gira "
                  "devagar e fraco. Não há o que avisar esta noite.")
            paginas = [p1]
        else:
            q = "questão vencida" if n == 1 else "questões vencidas"
            p1 = (f"O faroleiro confere o caderno: {n} {q} para revisão agora. Quanto mais vencidas, "
                  "mais forte e mais rápido o facho gira.")
            paginas = [p1]
            itens = sorted(self.venc.items(), key=lambda kv: (-kv[1], kv[0]))
            linhas, atual = [], ""
            for g, c in itens[:12]:
                pedaco = f"{g}: {c}"
                if atual and len(atual) + len(pedaco) + 3 > 190:
                    linhas.append(atual)
                    atual = pedaco
                else:
                    atual = f"{atual} · {pedaco}" if atual else pedaco
            if atual:
                resto = len(itens) - 12
                if resto > 0:
                    atual += f" · e mais {resto} {'assunto' if resto == 1 else 'assuntos'}"
                linhas.append(atual + ".")
            paginas += linhas[:3]
        paginas.append("Revisar no dia em que a questão vence, quando ela já começou a escapar, é o que segura a "
                       "memória: é a revisão espaçada. Antes disso rende pouco; muito depois, é quase reaprender.")
        paginas.append("A lâmpada pisca sempre a mesma palavra em Morse: -·-· ·- ·-·· -- ·-. CALMA. "
                       "Uma de cada vez.")
        self.mirante._falar(paginas)
