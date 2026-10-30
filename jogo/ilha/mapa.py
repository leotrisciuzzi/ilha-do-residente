"""Mapa de Estudos: a tela de seleção de fases no estilo do Super Mario Bros. Wonder, com o Doutor recortado em papel
(como no Paper Mario) andando pelo caminho.

Duas camadas, o mesmo motor:
  - Mapa-múndi: uma ilha por especialidade (reino), com o castelo pintado pelo progresso, a bandeira quando tudo foi
    concluído e a estrela dourada quando tudo foi dominado.
  - Mapa do reino: uma ilha por trilha (tema do cronograma, mundo a fundo, fluxogramas, prova por prevalência) e
    uma fase em cada pedestal do caminho. O pedestal muda de cor com o estado (cinza, bronze, azul, ouro), o
    reloginho laranja diz "pede revisão" e o alfinete vermelho, "a aula já passou na agenda".

O visual (a 'beleza e a iluminação' do Wonder) sai de camadas baratas, quase tudo pré-renderizado:
ilhas com penhasco extrudado, borda iluminada e sombra suave na água, árvores com volume, caminho de terra; mar com
ondas e brilhos; luz quente do sol, raios de luz, sombras de nuvens passando, vinheta, partículas de luz e o
desfoque de miniatura (tilt-shift) em cima e embaixo. O herói é o sprite 2D com borda branca de papel, sombra no
chão e o giro de papel ao mudar de lado."""
import datetime as dt
import math
import random
import time

import pygame

from . import art, edicao, jornada
from .ui import (AMARELO, H, RETRATO, TINTA, W, Estado, Menu, Mensagem, Carregando, cortar, fonte, quebrar)

SS = 2                              # supersampling da arte cacheada (bordas suaves)
PAISAGEM = not RETRATO
ESP = 150 if RETRATO else 136        # distância entre fases no caminho
POR_LINHA = 3                        # fases por fileira dentro da ilha (o caminho serpenteia)
R_NO = 78                            # raio de terra em volta de cada fase
VAO = 120                            # mar entre uma ilha e a próxima
PROF = 30                            # altura do penhasco
VEL = 7.5                            # px por quadro do herói
TOPO_HUD = 150 if RETRATO else 96
BASE_HUD = 262 if RETRATO else 196

ESTILO = {
    "prado":     dict(topo=(118, 200, 92), luz=(178, 234, 128), lado=(170, 118, 76), fundo=(104, 70, 52),
                      estrada=(246, 226, 168), borda=(196, 156, 104), arv=[(64, 168, 84), (92, 190, 86), (52, 150, 96)],
                      tipo="redonda", mar=((18, 84, 168), (58, 186, 222))),
    "cerejeira": dict(topo=(140, 208, 112), luz=(196, 240, 150), lado=(176, 120, 96), fundo=(110, 70, 70),
                      estrada=(250, 230, 200), borda=(206, 160, 140), arv=[(255, 168, 204), (255, 196, 222), (240, 140, 186)],
                      tipo="redonda", mar=((40, 80, 170), (96, 180, 230))),
    "praia":     dict(topo=(242, 222, 160), luz=(255, 244, 200), lado=(200, 160, 110), fundo=(140, 104, 74),
                      estrada=(255, 250, 236), borda=(220, 190, 140), arv=[(70, 180, 90), (96, 200, 100)],
                      tipo="palmeira", mar=((10, 110, 170), (40, 210, 210))),
    "outono":    dict(topo=(196, 178, 88), luz=(236, 214, 130), lado=(160, 104, 70), fundo=(98, 62, 48),
                      estrada=(246, 222, 170), borda=(190, 140, 90), arv=[(236, 120, 50), (220, 80, 50), (250, 170, 60)],
                      tipo="redonda", mar=((28, 76, 150), (72, 160, 200))),
    "neve":      dict(topo=(236, 244, 255), luz=(255, 255, 255), lado=(140, 156, 190), fundo=(86, 96, 130),
                      estrada=(200, 214, 240), borda=(160, 176, 214), arv=[(50, 120, 96), (64, 140, 110)],
                      tipo="pinheiro", mar=((20, 54, 120), (70, 130, 200))),
    "cristal":   dict(topo=(160, 130, 220), luz=(206, 186, 255), lado=(110, 80, 160), fundo=(64, 44, 104),
                      estrada=(236, 222, 255), borda=(170, 140, 220), arv=[(120, 240, 255), (255, 140, 230), (180, 255, 200)],
                      tipo="cristal", mar=((40, 30, 110), (100, 90, 210))),
    "selva":     dict(topo=(64, 164, 84), luz=(120, 212, 110), lado=(140, 96, 64), fundo=(80, 56, 40),
                      estrada=(226, 206, 150), borda=(170, 136, 90), arv=[(40, 130, 70), (60, 160, 70), (30, 110, 80)],
                      tipo="selva", mar=((10, 90, 110), (40, 170, 160))),
    "deserto":   dict(topo=(232, 192, 122), luz=(252, 222, 160), lado=(200, 130, 80), fundo=(140, 80, 52),
                      estrada=(252, 236, 200), borda=(206, 160, 110), arv=[(90, 170, 90), (110, 190, 100)],
                      tipo="cacto", mar=((20, 100, 170), (70, 190, 210))),
}
MAR_MUNDI = ((14, 70, 150), (52, 176, 220))

# estado → cores do pedestal (topo, lado)
PEDESTAL = {0: ((210, 216, 230), (138, 148, 176)), 1: ((255, 186, 108), (196, 118, 58)),
            2: ((112, 172, 255), (54, 96, 196)), 3: ((255, 214, 84), (204, 146, 36))}
COR_ESTADO = {0: (150, 156, 176), 1: (236, 150, 60), 2: (70, 130, 240), 3: (230, 170, 20)}


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _blur(s, k=6):
    """Desfoque barato: reduz e amplia com suavização (k = fator)."""
    w, h = s.get_size()
    p = pygame.transform.smoothscale(s, (max(1, w // k), max(1, h // k)))
    return pygame.transform.smoothscale(p, (w, h))


def _pl(p, l):
    """(progresso, lateral) → (x, y) do mapa: em paisagem o caminho anda para a direita, em pé anda para cima."""
    return (p, l) if PAISAGEM else (l, -p)


def _suave(pts, passo=6):
    """Catmull-Rom pelos pontos, amostrado a cada ~passo px."""
    if len(pts) < 2:
        return list(pts)
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(2, int(math.dist(p1, p2) / passo))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


# ------------------------------------------------------------------ layout

class No:
    def __init__(self, x, y, ilha, k, dado):
        self.x, self.y, self.ilha, self.k, self.dado = x, y, ilha, k, dado


class Ilha:
    def __init__(self, nos, raio, bioma, rotulo, seed, sub=""):
        self.nos, self.raio, self.bioma, self.rotulo, self.seed, self.sub = nos, raio, bioma, rotulo, seed, sub
        self.surf, self.pos = None, (0, 0)

    @property
    def centro(self):
        return (sum(n.x for n in self.nos) / len(self.nos), sum(n.y for n in self.nos) / len(self.nos))


def layout_reino(reino):
    """Uma ilha por trilha; dentro dela as fases serpenteiam em fileiras de POR_LINHA."""
    ilhas, nos = [], []
    p = 0.0
    rng = random.Random(reino.nome)
    for ti, t in enumerate(reino.trilhas):
        n = len(t.fases)
        linhas = math.ceil(n / POR_LINHA)
        meio = math.sin(ti * 1.7) * (40 if RETRATO else 34)
        p0 = p + R_NO
        pts = []
        for k in range(n):
            r, j = divmod(k, POR_LINHA)
            if r % 2:
                j = POR_LINHA - 1 - j
            cheia = min(POR_LINHA, n - r * POR_LINHA) if n > 1 else 1
            if n <= POR_LINHA:
                jj = j - (cheia - 1) / 2
            else:
                jj = j - (POR_LINHA - 1) / 2
            lat = meio + jj * ESP + rng.uniform(-12, 12)
            prog = p0 + r * ESP * 0.92 + rng.uniform(-10, 10) + (abs(jj) * 14 if n > 1 else 0)
            pts.append(_pl(prog, lat))
        il = Ilha([], R_NO, reino.bioma, t.nome, hash((reino.nome, t.id)) & 0xFFFF, t.sub)
        for k, xy in enumerate(pts):
            no = No(xy[0], xy[1], len(ilhas), k, t.fases[k])
            il.nos.append(no)
            nos.append(no)
        ilhas.append(il)
        p = p0 + (linhas - 1) * ESP * 0.92 + R_NO + VAO
    return ilhas, nos


def layout_mundi(reinos):
    """Mapa-múndi: uma ilha por reino, em fileiras de 2 que serpenteiam."""
    ilhas, nos = [], []
    passo_l = 300 if RETRATO else 270
    passo_p = 330 if RETRATO else 300
    rng = random.Random(7)
    for i, r in enumerate(reinos):
        lin, j = divmod(i, 2)
        if lin % 2:
            j = 1 - j
        lat = (j - 0.5) * passo_l + rng.uniform(-24, 24)
        prog = 150 + lin * passo_p + j * 60 + rng.uniform(-20, 20)
        x, y = _pl(prog, lat)
        il = Ilha([], 128, r.bioma, r.nome, hash(r.nome) & 0xFFFF)
        no = No(x, y, i, 0, r)
        il.nos.append(no)
        ilhas.append(il)
        nos.append(no)
    return ilhas, nos


# ------------------------------------------------------------------ arte das ilhas (cacheada)

def _arvore(s, x, y, est, rng, esc):
    """Árvore/enfeite com volume: sombra de contato, base escura, luz no alto à esquerda."""
    tipo = est["tipo"]
    cor = rng.choice(est["arv"])
    escura, clara = _mix(cor, (20, 30, 40), 0.35), _mix(cor, (255, 255, 240), 0.35)
    sh = pygame.Surface((int(60 * esc), int(24 * esc)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    s.blit(sh, (x - sh.get_width() // 2 + int(6 * esc), y - sh.get_height() // 2))
    if tipo in ("redonda", "selva"):
        r = int((22 if tipo == "redonda" else 27) * esc * rng.uniform(0.85, 1.2))
        pygame.draw.rect(s, (110, 74, 50), (x - int(4 * esc), y - int(18 * esc), int(8 * esc), int(18 * esc)),
                         border_radius=int(3 * esc))
        cy = y - int(18 * esc) - r + int(6 * esc)
        pygame.draw.circle(s, escura, (x, cy), r)
        pygame.draw.circle(s, cor, (x - int(r * 0.12), cy - int(r * 0.12)), int(r * 0.86))
        pygame.draw.circle(s, clara, (x - int(r * 0.32), cy - int(r * 0.34)), int(r * 0.42))
        pygame.draw.circle(s, _mix(clara, (255, 255, 255), 0.5), (x - int(r * 0.42), cy - int(r * 0.46)), int(r * 0.16))
        if tipo == "selva":
            for a in (-0.9, 0.9):
                pygame.draw.ellipse(s, escura, (x + int(a * r) - int(10 * esc), cy + int(r * 0.2), int(20 * esc), int(12 * esc)))
    elif tipo == "pinheiro":
        h = int(58 * esc * rng.uniform(0.8, 1.2))
        pygame.draw.rect(s, (100, 70, 50), (x - int(3 * esc), y - int(10 * esc), int(6 * esc), int(10 * esc)))
        for k in range(3):
            w = int((30 - k * 7) * esc)
            yb = y - int(8 * esc) - k * h // 4
            pygame.draw.polygon(s, escura, [(x - w, yb), (x + w, yb), (x, yb - h // 2)])
            pygame.draw.polygon(s, cor, [(x - w + int(3 * esc), yb - int(2 * esc)), (x, yb - h // 2), (x, yb - int(2 * esc))])
            pygame.draw.polygon(s, (250, 252, 255), [(x - w // 3, yb - h // 3), (x + w // 3, yb - h // 3), (x, yb - h // 2)])
    elif tipo == "palmeira":
        h = int(52 * esc * rng.uniform(0.85, 1.15))
        curva = rng.choice((-1, 1)) * int(10 * esc)
        pts = [(x + int(curva * (k / 6) ** 2), y - h * k // 6) for k in range(7)]
        pygame.draw.lines(s, (150, 104, 64), False, pts, int(7 * esc))
        tx, ty = pts[-1]
        for a in range(6):
            ang = a * math.pi / 3 + 0.3
            ex, ey = tx + math.cos(ang) * 26 * esc, ty + math.sin(ang) * 14 * esc + 6 * esc
            pygame.draw.polygon(s, cor if a % 2 else escura,
                                [(tx, ty), (ex, ey), (tx + math.cos(ang + 0.35) * 14 * esc, ty + math.sin(ang + 0.35) * 8 * esc)])
        pygame.draw.circle(s, (120, 80, 40), (tx, ty + int(3 * esc)), int(4 * esc))
    elif tipo == "cacto":
        h = int(40 * esc * rng.uniform(0.8, 1.2))
        w = int(12 * esc)
        pygame.draw.rect(s, escura, (x - w // 2, y - h, w, h), border_radius=w // 2)
        pygame.draw.rect(s, cor, (x - w // 2 + int(2 * esc), y - h + int(2 * esc), w // 2, h - int(6 * esc)), border_radius=w // 3)
        for lado in (-1, 1):
            ay = y - h // 2 - rng.randint(0, h // 4)
            pygame.draw.rect(s, escura, (x + lado * w // 2 - (w if lado < 0 else 0), ay, w, int(6 * esc)))
            pygame.draw.rect(s, escura, (x + lado * (w // 2 + w // 2) - w // 2, ay - h // 3, int(9 * esc), h // 3 + int(4 * esc)),
                             border_radius=int(4 * esc))
    elif tipo == "cristal":
        h = int(44 * esc * rng.uniform(0.8, 1.3))
        for dx, hh in ((-10, 0.7), (0, 1.0), (11, 0.6)):
            cx, ch = x + int(dx * esc), int(h * hh)
            w = int(9 * esc)
            pygame.draw.polygon(s, escura, [(cx - w, y), (cx + w, y), (cx + w, y - ch + w), (cx, y - ch), (cx - w, y - ch + w)])
            pygame.draw.polygon(s, clara, [(cx - w, y), (cx, y), (cx, y - ch), (cx - w, y - ch + w)])
            pygame.draw.line(s, (255, 255, 255), (cx - w // 2, y - ch + w + int(3 * esc)), (cx - w // 2, y - int(8 * esc)), max(1, int(2 * esc)))


def _arbusto(s, x, y, est, rng, esc):
    cor = _mix(est["topo"], (30, 80, 40), 0.25)
    for dx, r in ((-9, 9), (0, 12), (10, 8)):
        pygame.draw.circle(s, _mix(cor, (0, 0, 0), 0.25), (x + int(dx * esc), y - int(r * 0.6 * esc)), int(r * esc))
    for dx, r in ((-9, 7), (0, 10), (10, 6)):
        pygame.draw.circle(s, cor, (x + int((dx - 2) * esc), y - int((r * 0.6 + 2) * esc)), int(r * esc))
    if rng.random() < 0.5:
        for _ in range(3):
            pygame.draw.circle(s, rng.choice([(255, 90, 110), (255, 230, 90), (255, 255, 255)]),
                               (x + rng.randint(-12, 12) * esc // 1, y - rng.randint(6, 16) * esc // 1), int(2.5 * esc))


def render_ilha(il, est, rotulo_fonte=None, plaqueta=True):
    """Desenha a ilha (sombra, espuma, penhasco, topo iluminado, caminho, enfeites e placa) em cache 1×."""
    rng = random.Random(il.seed)
    xs = [n.x for n in il.nos]
    ys = [n.y for n in il.nos]
    pad = il.raio + 50
    x0, y0 = min(xs) - pad, min(ys) - pad
    w, h = int(max(xs) - x0 + pad + 30), int(max(ys) - y0 + pad + PROF + 40)
    S = SS
    loc = [((n.x - x0) * S, (n.y - y0) * S) for n in il.nos]
    via = _suave(loc, 8 * S) if len(loc) > 1 else loc
    blobs = [(x, y, il.raio * S * rng.uniform(0.92, 1.08)) for x, y in loc]
    for i in range(0, len(via), 6):
        x, y = via[i]
        blobs.append((x, y, il.raio * S * rng.uniform(0.8, 0.95)))
    for x, y in list(loc):                                  # calombos na borda: contorno orgânico
        for _ in range(3):
            a = rng.uniform(0, math.tau)
            d = il.raio * S * rng.uniform(0.45, 0.75)
            blobs.append((x + math.cos(a) * d, y + math.sin(a) * d * 0.8, il.raio * S * rng.uniform(0.45, 0.7)))

    def forma(surf, cor, dx=0, dy=0, dr=0.0):
        for x, y, r in blobs:
            if r + dr > 2:
                pygame.draw.circle(surf, cor, (int(x + dx), int(y + dy)), int(r + dr))

    big = pygame.Surface((w * S, h * S), pygame.SRCALPHA)
    # sombra na água (projetada para baixo e à direita, bem difusa)
    sh = pygame.Surface((w * S, h * S), pygame.SRCALPHA)
    forma(sh, (0, 20, 50, 90), 16 * S, (PROF + 26) * S, 6 * S)
    big.blit(_blur(sh, 10), (0, 0))
    # espuma no pé do penhasco
    sp = pygame.Surface((w * S, h * S), pygame.SRCALPHA)
    forma(sp, (255, 255, 255, 120), 0, PROF * S, 9 * S)
    big.blit(_blur(sp, 4), (0, 0))
    # penhasco: camadas do escuro (embaixo) ao claro (em cima), com estrias
    for k in range(PROF, -1, -2):
        t = k / PROF
        forma(big, _mix(est["lado"], est["fundo"], t), 0, k * S)
        if k % 10 == 0 and 0 < k < PROF:
            forma(big, _mix(est["lado"], est["fundo"], t + 0.12), 0, k * S, -2 * S)
    # topo: borda de luz em cima, corpo, centro mais claro (volume de platô)
    forma(big, est["luz"], 0, -5 * S)
    forma(big, est["topo"])
    meio = pygame.Surface((w * S, h * S), pygame.SRCALPHA)
    forma(meio, (*_mix(est["topo"], est["luz"], 0.45), 255), -6 * S, -6 * S, -24 * S)
    big.blit(_blur(meio, 8), (0, 0))
    mask = pygame.mask.from_surface(meio, 60)
    # textura: tufos de grama/manchas
    for _ in range(int(len(il.nos) * 26)):
        x, y = rng.randrange(w * S), rng.randrange(h * S)
        if mask.get_at((x, y)):
            c = _mix(est["topo"], (0, 40, 0) if rng.random() < 0.6 else (255, 255, 220), rng.uniform(0.08, 0.18))
            pygame.draw.ellipse(big, c, (x, y, rng.randint(6, 14) * S // 2, rng.randint(3, 6) * S // 2))
    # caminho de terra: borda, leito e pontilhado
    if len(via) > 1:
        for x, y in via:
            pygame.draw.circle(big, est["borda"], (int(x), int(y + 2 * S)), 17 * S)
        for x, y in via:
            pygame.draw.circle(big, est["estrada"], (int(x), int(y)), 14 * S)
        for i in range(0, len(via), 5):
            x, y = via[i]
            pygame.draw.circle(big, _mix(est["estrada"], (255, 255, 255), 0.5), (int(x - 3 * S), int(y - 3 * S)), 3 * S)
    # enfeites longe do caminho e das fases, do fundo para a frente
    livres = []
    tentativas = int(len(il.nos) * 30 + 30)
    for _ in range(tentativas):
        x, y = rng.randrange(w * S), rng.randrange(h * S)
        if not mask.get_at((x, y)):
            continue
        if min((math.dist((x, y), p) for p in via[::3]), default=999) < 44 * S:
            continue
        if any(math.dist((x, y), p) < 34 * S for p in livres):
            continue
        livres.append((x, y))
    livres.sort(key=lambda p: p[1])
    for x, y in livres:
        if rng.random() < 0.62:
            _arvore(big, int(x), int(y), est, rng, S * rng.uniform(0.85, 1.15))
        else:
            _arbusto(big, int(x), int(y), est, rng, S)
    il.surf = pygame.transform.smoothscale(big, (w, h))
    il.pos = (x0, y0)
    if plaqueta and il.rotulo and rotulo_fonte:
        _placa(il, rotulo_fonte)


def _placa(il, f):
    """Placa de madeira com o nome da ilha, fincada antes da primeira fase."""
    txt = cortar(il.rotulo, f, 260)
    t = f.render(txt, True, (60, 36, 20))
    tw, th = t.get_width() + 22, t.get_height() + 10
    s = pygame.Surface((tw + 8, th + 34), pygame.SRCALPHA)
    pygame.draw.rect(s, (110, 70, 40), (tw // 2 - 3, th - 4, 7, 34))
    pygame.draw.rect(s, (90, 56, 30), (2, 4, tw, th), border_radius=7)
    pygame.draw.rect(s, (226, 176, 112), (0, 0, tw, th), border_radius=7)
    pygame.draw.rect(s, (246, 206, 146), (3, 3, tw - 6, th // 2 - 2), border_radius=5)
    s.blit(t, (11, 5))
    n0 = il.nos[0]
    dx = -tw // 2 - 4
    x = int(n0.x - il.pos[0] + dx)
    y = int(n0.y - il.pos[1] - 62 - th)
    x = max(0, min(il.surf.get_width() - s.get_width(), x))
    y = max(0, y)
    il.surf.blit(s, (x, y))


# ------------------------------------------------------------------ pedestais, ícones e herói de papel

_CACHE = {}


def _pedestal(nivel, raio=30):
    k = ("ped", nivel, raio)
    if k in _CACHE:
        return _CACHE[k]
    topo, lado = PEDESTAL[nivel]
    S = SS
    rx, ry, alt = raio * S, int(raio * 0.52 * S), 12 * S
    s = pygame.Surface((rx * 2 + 8 * S, ry * 2 + alt + 10 * S), pygame.SRCALPHA)
    cx, cy = s.get_width() // 2, ry + 2 * S
    pygame.draw.ellipse(s, (0, 0, 0, 60), (cx - rx - 2 * S, cy + alt - ry + 4 * S, rx * 2 + 8 * S, ry * 2 + 4 * S))
    pygame.draw.ellipse(s, _mix(lado, (0, 0, 0), 0.3), (cx - rx, cy + alt - ry, rx * 2, ry * 2))
    pygame.draw.rect(s, lado, (cx - rx, cy, rx * 2, alt))
    pygame.draw.rect(s, _mix(lado, (255, 255, 255), 0.25), (cx - rx + 3 * S, cy + 2 * S, rx // 2, alt - 2 * S))
    pygame.draw.ellipse(s, _mix(topo, (0, 0, 0), 0.12), (cx - rx, cy - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(s, topo, (cx - rx + 3 * S, cy - ry + 2 * S, rx * 2 - 6 * S, ry * 2 - 6 * S))
    pygame.draw.ellipse(s, _mix(topo, (255, 255, 255), 0.55), (cx - rx * 0.6, cy - ry * 0.75, rx * 0.8, ry * 0.6))
    out = pygame.transform.smoothscale(s, (s.get_width() // S, s.get_height() // S))
    _CACHE[k] = out
    return out


def _brilho(raio, cor):
    """Halo aditivo (a luz que as fases emitem)."""
    k = ("glow", raio, cor)
    if k in _CACHE:
        return _CACHE[k]
    n = 24
    s = pygame.Surface((n * 2, n * 2), pygame.SRCALPHA)
    for i in range(n, 0, -1):
        a = (1 - i / n) ** 2
        pygame.draw.circle(s, (int(cor[0] * a), int(cor[1] * a), int(cor[2] * a)), (n, n), i)
    out = pygame.transform.smoothscale(s, (raio * 2, raio * 2))
    _CACHE[k] = out
    return out


def _icone(tipo, nivel):
    """Emblema 2D (recortado em papel) que fica em pé no pedestal."""
    k = ("ico", tipo, nivel)
    if k in _CACHE:
        return _CACHE[k]
    S = 3
    s = pygame.Surface((40 * S, 44 * S), pygame.SRCALPHA)
    c = s.get_width() // 2
    apag = nivel == 0
    if tipo == "castelo":
        pedra, telhado = ((200, 200, 214), (120, 120, 150)) if apag else ((236, 230, 220), (220, 70, 70))
        if nivel == 3:
            telhado = (250, 200, 40)
        pygame.draw.rect(s, _mix(pedra, (0, 0, 0), 0.25), (c - 15 * S, 16 * S, 30 * S, 26 * S))
        pygame.draw.rect(s, pedra, (c - 15 * S, 16 * S, 26 * S, 24 * S))
        for dx in (-17, 9):
            pygame.draw.rect(s, pedra, (c + dx * S, 10 * S, 9 * S, 30 * S))
            pygame.draw.polygon(s, telhado, [(c + (dx - 2) * S, 11 * S), (c + (dx + 11) * S, 11 * S), (c + (dx + 4.5) * S, 0)])
        pygame.draw.rect(s, (80, 50, 40), (c - 5 * S, 28 * S, 10 * S, 14 * S), border_radius=5 * S)
        for dx in (-13, 11):
            pygame.draw.rect(s, (90, 120, 200), (c + dx * S, 18 * S, 3 * S, 4 * S))
    elif tipo == "aula":
        capa = (150, 160, 190) if apag else (70, 120, 220)
        pygame.draw.polygon(s, capa, [(c - 17 * S, 14 * S), (c, 18 * S), (c + 17 * S, 14 * S), (c + 17 * S, 38 * S),
                                      (c, 42 * S), (c - 17 * S, 38 * S)])
        pygame.draw.polygon(s, (255, 255, 250), [(c - 15 * S, 12 * S), (c - 1 * S, 16 * S), (c - 1 * S, 38 * S), (c - 15 * S, 34 * S)])
        pygame.draw.polygon(s, (240, 240, 232), [(c + 15 * S, 12 * S), (c + 1 * S, 16 * S), (c + 1 * S, 38 * S), (c + 15 * S, 34 * S)])
        for i in range(4):
            y = 19 + i * 4
            pygame.draw.line(s, (170, 170, 190), (c - 12 * S, (y - 1) * S), (c - 4 * S, (y + 1) * S), S)
            pygame.draw.line(s, (170, 170, 190), (c + 4 * S, (y + 1) * S), (c + 12 * S, (y - 1) * S), S)
    elif tipo == "treino":
        cor = (150, 150, 170) if apag else (90, 200, 110)
        pygame.draw.rect(s, (90, 90, 100), (c - 14 * S, 25 * S, 28 * S, 5 * S), border_radius=2 * S)
        for dx in (-18, 10):
            pygame.draw.rect(s, cor, (c + dx * S, 16 * S, 8 * S, 22 * S), border_radius=3 * S)
            pygame.draw.rect(s, _mix(cor, (255, 255, 255), 0.4), (c + (dx + 1) * S, 18 * S, 3 * S, 16 * S), border_radius=S)
    elif tipo == "fluxo":
        cor = (150, 150, 170) if apag else (90, 200, 220)
        pygame.draw.line(s, TINTA, (c, 14 * S), (c - 12 * S, 30 * S), 2 * S)
        pygame.draw.line(s, TINTA, (c, 14 * S), (c + 12 * S, 30 * S), 2 * S)
        for x, y in ((c, 12), (c - 12, 32), (c + 12, 32)):
            pygame.draw.rect(s, TINTA, (x - 8 * S, (y - 6) * S, 16 * S, 12 * S), border_radius=3 * S)
            pygame.draw.rect(s, cor, (x - 7 * S, (y - 5) * S, 14 * S, 10 * S), border_radius=3 * S)
    elif tipo == "ecg":
        cor = (170, 150, 160) if apag else (236, 70, 90)
        pygame.draw.circle(s, cor, (c - 7 * S, 20 * S), 9 * S)
        pygame.draw.circle(s, cor, (c + 7 * S, 20 * S), 9 * S)
        pygame.draw.polygon(s, cor, [(c - 16 * S, 22 * S), (c + 16 * S, 22 * S), (c, 40 * S)])
        pts = [(-14, 24), (-6, 24), (-3, 16), (1, 32), (4, 22), (14, 22)]
        pygame.draw.lines(s, (255, 255, 255), False, [(c + x * S, y * S) for x, y in pts], 2 * S)
    else:                                                # bloco "?" (módulo / questões de prova)
        cor = (180, 180, 196) if apag else ((250, 200, 60) if tipo == "fase" else (240, 140, 90))
        pygame.draw.rect(s, _mix(cor, (60, 30, 0), 0.4), (c - 15 * S, 12 * S, 30 * S, 30 * S), border_radius=5 * S)
        pygame.draw.rect(s, cor, (c - 15 * S, 12 * S, 28 * S, 28 * S), border_radius=5 * S)
        pygame.draw.rect(s, _mix(cor, (255, 255, 255), 0.5), (c - 13 * S, 14 * S, 24 * S, 4 * S), border_radius=2 * S)
        for x, y in ((-12, 15), (9, 15), (-12, 36), (9, 36)):
            pygame.draw.circle(s, _mix(cor, (60, 30, 0), 0.45), (c + x * S, y * S), S)
        f = fonte(26 * S // 2, True)
        t = f.render("?" if tipo == "fase" else "✓" if False else "Q", True, (255, 255, 255))
        o = f.render("?" if tipo == "fase" else "Q", True, _mix(cor, (60, 30, 0), 0.5))
        s.blit(o, (c - t.get_width() // 2 + S, 26 * S - t.get_height() // 2 + S))
        s.blit(t, (c - t.get_width() // 2 - S, 26 * S - t.get_height() // 2))
    out = _papel(pygame.transform.smoothscale(s, (40, 44)), 2)
    _CACHE[k] = out
    return out


def _papel(spr, borda=3):
    """Recorte de papel: silhueta branca em volta do desenho (como os personagens do Paper Mario)."""
    w, h = spr.get_size()
    m = pygame.mask.from_surface(spr, 40)
    sil = m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((w + borda * 2 + 2, h + borda * 2 + 2), pygame.SRCALPHA)
    esc = m.to_surface(setcolor=(40, 30, 40, 70), unsetcolor=(0, 0, 0, 0))
    for dx in range(-borda, borda + 1):
        for dy in range(-borda, borda + 1):
            if dx * dx + dy * dy <= borda * borda + 1:
                out.blit(esc, (borda + dx + 1, borda + dy + 2))
    for dx in range(-borda, borda + 1):
        for dy in range(-borda, borda + 1):
            if dx * dx + dy * dy <= borda * borda + 1:
                out.blit(sil, (borda + dx, borda + dy))
    out.blit(spr, (borda, borda))
    return out


def _selo(tipo):
    """Selos que flutuam sobre a fase: concluída (✔ azul), dominada (★), revisão (relógio), atrasada (!)."""
    k = ("selo", tipo)
    if k in _CACHE:
        return _CACHE[k]
    S = 3
    s = pygame.Surface((22 * S, 22 * S), pygame.SRCALPHA)
    c = 11 * S
    if tipo == "ok":
        pygame.draw.circle(s, (40, 90, 200), (c, c), 10 * S)
        pygame.draw.circle(s, (90, 150, 255), (c - S, c - S), 8 * S)
        pygame.draw.lines(s, (255, 255, 255), False, [(c - 5 * S, c), (c - S, c + 4 * S), (c + 5 * S, c - 4 * S)], 3 * S)
    elif tipo == "estrela":
        pts = [(c + math.cos(-math.pi / 2 + i * math.pi / 5) * (10 if i % 2 == 0 else 4.4) * S,
                c + math.sin(-math.pi / 2 + i * math.pi / 5) * (10 if i % 2 == 0 else 4.4) * S + S) for i in range(10)]
        pygame.draw.polygon(s, (200, 130, 10), [(x + S, y + S) for x, y in pts])
        pygame.draw.polygon(s, (255, 214, 50), pts)
        pygame.draw.circle(s, (255, 250, 200), (c - 2 * S, c - 2 * S), 2 * S)
    elif tipo == "revisar":
        pygame.draw.circle(s, (210, 110, 20), (c, c), 10 * S)
        pygame.draw.circle(s, (255, 170, 60), (c, c), 8 * S)
        pygame.draw.circle(s, (255, 250, 236), (c, c), 6 * S)
        pygame.draw.line(s, TINTA, (c, c), (c, c - 4 * S), 2 * S)
        pygame.draw.line(s, TINTA, (c, c), (c + 3 * S, c + S), 2 * S)
    elif tipo == "atrasada":
        pygame.draw.line(s, (90, 70, 70), (c - 3 * S, c + 9 * S), (c - 3 * S, c - 8 * S), 2 * S)
        pygame.draw.polygon(s, (230, 60, 60), [(c - 2 * S, c - 9 * S), (c + 9 * S, c - 5 * S), (c - 2 * S, c - S)])
    elif tipo == "marca":
        pygame.draw.circle(s, (120, 90, 200), (c, c), 10 * S)
        pygame.draw.line(s, (255, 255, 255), (c - 5 * S, c + 5 * S), (c + 4 * S, c - 4 * S), 3 * S)
        pygame.draw.polygon(s, (255, 220, 120), [(c - 6 * S, c + 6 * S), (c - 5 * S, c + 2 * S), (c - 2 * S, c + 5 * S)])
    out = pygame.transform.smoothscale(s, (22, 22))
    _CACHE[k] = out
    return out


class HeroiPapel:
    """O Doutor (e o pet) em 2D sobre o mapa: sprite ampliado com borda branca, sombra no chão, quique ao andar e
    o giro de papel (a largura passa por zero) ao virar."""

    ESC = 2

    def __init__(self, app):
        self.app = app
        self.x = self.y = 0.0
        self.virado = 1
        self._giro = 1.0                     # -1…1: escala horizontal do giro
        self.andando = False
        self.t = 0
        self._cache = {}
        self.rastro = []
        try:
            from . import pets
            self.pet = pets.visual(app.save)
        except Exception:
            self.pet = ("nenhum",) * 3

    def _spr(self, estado, quadro):
        k = (estado, quadro)
        if k not in self._cache:
            base = art.heroi(estado, quadro, True, 1)
            base = pygame.transform.scale(base, (base.get_width() * self.ESC, base.get_height() * self.ESC))
            self._cache[k] = _papel(base, 3)
        return self._cache[k]

    def _spr_pet(self, quadro, andando):
        k = ("pet", quadro, andando)
        if k not in self._cache:
            from . import pets
            p, col, cha = self.pet
            base = pets.sprite(p, col, cha, "andar" if andando else "parado", quadro)
            base = pygame.transform.scale(base, (base.get_width() * self.ESC, base.get_height() * self.ESC))
            self._cache[k] = _papel(base, 2)
        return self._cache[k]

    def virar(self, dx):
        if abs(dx) > 0.5:
            self.virado = 1 if dx > 0 else -1

    def update(self):
        self.t += 1
        self._giro += (self.virado - self._giro) * 0.22
        self.rastro.append((self.x, self.y))
        if len(self.rastro) > 14:
            self.rastro.pop(0)

    def draw(self, tela, cx, cy):
        quadro = (self.t // 6) % 4 if self.andando else 0
        spr = self._spr("andar" if self.andando else "parado", quadro)
        sx = abs(self._giro)
        w = max(2, int(spr.get_width() * sx))
        img = pygame.transform.flip(spr, self._giro < 0, False)
        if w != spr.get_width():
            img = pygame.transform.scale(img, (w, spr.get_height()))
        bob = -abs(math.sin(self.t * 0.35)) * 6 if self.andando else math.sin(self.t * 0.06) * 1.5
        sh = _sombra_eli(46, 14)
        if self.pet[0] != "nenhum" and self.rastro:
            px, py = self.rastro[0]
            ps = self._spr_pet((self.t // 4) % 12 if self.andando else self.t % 180, self.andando)
            ps = pygame.transform.flip(ps, self.virado < 0, False)
            ex, ey = int(px - self.x + cx - self.virado * 34), int(py - self.y + cy)
            tela.blit(_sombra_eli(30, 10), (ex - 15, ey - 5))
            tela.blit(ps, (ex - ps.get_width() // 2, ey - ps.get_height() + 4))
        tela.blit(sh, (cx - sh.get_width() // 2, cy - sh.get_height() // 2))
        if self.andando:                      # leve inclinação de papel ao andar
            img = pygame.transform.rotate(img, math.sin(self.t * 0.35) * 3)
        tela.blit(img, (cx - img.get_width() // 2, cy - img.get_height() + 8 + bob))


def _sombra_eli(w, h):
    k = ("sombra", w, h)
    if k not in _CACHE:
        s = pygame.Surface((w * 4, h * 4), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 20, 30, 110), s.get_rect().inflate(-8, -8))
        _CACHE[k] = _blur(s, 3) if False else pygame.transform.smoothscale(s, (w, h))
    return _CACHE[k]


# ------------------------------------------------------------------ luz e atmosfera (tela inteira, cacheadas)

class Atmosfera:
    def __init__(self, mar, seed=3):
        self.t = 0
        self.mar = self._gradiente(mar)
        self.ondas = self._ondas(mar)
        self.sol = self._radial((255, 196, 120), (0.12, -0.05), 0.95, aditivo=True)
        self.vinheta = self._vinheta()
        self.raios = self._raios()
        self.nuvem = self._nuvem()
        rng = random.Random(seed)
        self.particulas = [[rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.2, 0.7), rng.uniform(0, 6.28),
                            rng.choice((3, 4, 5))] for _ in range(34)]

    def _gradiente(self, mar):
        s = pygame.Surface((1, 64))
        for y in range(64):
            t = y / 63
            s.set_at((0, y), _mix(mar[1], mar[0], 0.25 + 0.75 * t))
        return pygame.transform.smoothscale(s, (W, H))

    def _ondas(self, mar):
        T = 256
        s = pygame.Surface((T, T), pygame.SRCALPHA)
        rng = random.Random(11)
        for _ in range(9):
            x, y = rng.randrange(T), rng.randrange(T)
            w = rng.randint(50, 110)
            k = rng.uniform(0.10, 0.18)
            for dx in (-T, 0, T):
                for dy in (-T, 0, T):
                    pygame.draw.arc(s, (int(255 * k), int(255 * k), int(255 * k), 255), (x + dx, y + dy, w, w // 4),
                                    0.4, 2.7, 3)
        return _blur(s, 2)

    def _radial(self, cor, centro, alcance, aditivo):
        n = 48
        hh = int(n * H / W)
        s = pygame.Surface((n, hh))
        cx, cy = centro[0] * n, centro[1] * hh
        for y in range(hh):
            for x in range(n):
                d = math.hypot(x - cx, (y - cy) * 1.2) / (n * alcance)
                a = max(0.0, 1 - d) ** 2
                s.set_at((x, y), (int(cor[0] * a * 0.42), int(cor[1] * a * 0.42), int(cor[2] * a * 0.42)))
        return pygame.transform.smoothscale(s, (W, H))

    def _vinheta(self):
        n = 48
        hh = int(n * H / W)
        s = pygame.Surface((n, hh))
        for y in range(hh):
            for x in range(n):
                d = math.hypot((x / n - 0.5) * 1.1, (y / hh - 0.5)) / 0.72
                v = int(255 * (1 - 0.42 * max(0.0, d - 0.35) ** 1.5))
                v = max(120, min(255, v))
                s.set_at((x, y), (v, v, min(255, v + 6)))
        return pygame.transform.smoothscale(s, (W, H))

    def _raios(self):
        """Fachos de luz diagonais, já multiplicados pela intensidade (a soma aditiva ignora o canal alfa)."""
        s = pygame.Surface((W // 4, H // 4))
        rng = random.Random(5)
        for i in range(4):
            x = rng.randint(-W // 16, W // 8) + i * W // 14
            larg = rng.randint(W // 50, W // 24)
            k = rng.uniform(0.07, 0.13)
            pts = [(x, -10), (x + larg, -10), (x + larg + H // 3, H // 4 + 10), (x + H // 3, H // 4 + 10)]
            pygame.draw.polygon(s, (int(255 * k), int(236 * k), int(190 * k)), pts)
        fade = pygame.Surface((W // 4, H // 4))               # somem para baixo
        for y in range(H // 4):
            v = int(255 * max(0.0, 1 - y / (H // 4)) ** 1.4)
            pygame.draw.line(fade, (v, v, v), (0, y), (W // 4, y))
        s.blit(fade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        return pygame.transform.smoothscale(_blur(s, 3), (W, H))

    def _nuvem(self):
        """Sombra de nuvem para multiplicar: branco (não muda nada) com uma mancha azulada e difusa no meio."""
        m = pygame.Surface((160, 100), pygame.SRCALPHA)
        for x, y, r in ((50, 50, 30), (80, 44, 36), (112, 54, 28), (70, 62, 28)):
            pygame.draw.circle(m, (255, 255, 255, 255), (x, y), r)
        m = pygame.transform.smoothscale(_blur(m, 5), (480, 300))
        cor = pygame.Surface((480, 300), pygame.SRCALPHA)
        cor.fill((204, 212, 232, 255))
        cor.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        out = pygame.Surface((480, 300))
        out.fill((255, 255, 255))
        out.blit(cor, (0, 0))
        return out

    def fundo(self, tela, cam):
        tela.blit(self.mar, (0, 0))
        T = self.ondas.get_width()
        ox = -int(cam[0] * 0.92 + self.t * 0.25) % T
        oy = -int(cam[1] * 0.92 + math.sin(self.t * 0.01) * 10) % T
        for x in range(ox - T, W, T):
            for y in range(oy - T, H, T):
                tela.blit(self.ondas, (x, y), special_flags=pygame.BLEND_RGB_ADD)
        # brilhos no mar (ficam presos ao mapa, piscando)
        bx, by = int(cam[0] // 90), int(cam[1] // 90)
        for gx in range(bx - 1, bx + W // 90 + 2):
            for gy in range(by - 1, by + H // 90 + 2):
                h = (gx * 73856093 ^ gy * 19349663) & 0xFFFF
                if h % 5:
                    continue
                fase = (self.t * 0.05 + h) % 6.28
                a = max(0.0, math.sin(fase)) ** 6
                if a < 0.05:
                    continue
                x = gx * 90 + h % 70 - cam[0]
                y = gy * 90 + (h >> 7) % 70 - cam[1]
                r = int(2 + 5 * a)
                pygame.draw.line(tela, (255, 255, 255), (x - r, y), (x + r, y), 2)
                pygame.draw.line(tela, (255, 255, 255), (x, y - r), (x, y + r), 2)

    def frente(self, tela, cam):
        self.t += 1
        # sombras de nuvens atravessando o mapa
        for i in range(3):
            x = ((self.t * (0.35 + i * 0.1) + i * 700 - cam[0] * 0.5) % (W + 900)) - 480
            y = ((i * 380 + 140 - cam[1] * 0.5) % (H + 400)) - 300
            tela.blit(self.nuvem, (int(x), int(y)), special_flags=pygame.BLEND_RGB_MULT)
        tela.blit(self.sol, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        tela.blit(self.raios, (int(math.sin(self.t * 0.004) * 30), 0), special_flags=pygame.BLEND_RGB_ADD)
        for p in self.particulas:            # ciscos de luz subindo
            p[1] -= p[2]
            p[0] += math.sin(self.t * 0.02 + p[3]) * 0.4
            if p[1] < -10:
                p[1] = H + 10
                p[0] = random.uniform(0, W)
            g = _brilho(p[4] * 3, (150, 130, 90))
            tela.blit(g, (int(p[0]) - g.get_width() // 2, int(p[1]) - g.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        _tilt_shift(tela)
        tela.blit(self.vinheta, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


def _tilt_shift(tela):
    """Desfoque de miniatura: faixas de cima e de baixo cada vez mais borradas (a 'maquete' do Wonder)."""
    faixa = int(H * (0.13 if RETRATO else 0.17))
    for topo in (True, False):
        y0 = 0 if topo else H - faixa
        sub = tela.subsurface((0, y0, W, faixa)).copy()
        bl = _blur(sub, 7)
        passos = 4
        for i in range(passos):
            h = faixa // passos
            yy = i * h if topo else (passos - 1 - i) * h
            a = int(255 * (1 - i / passos) ** 1.3)
            pedaco = bl.subsurface((0, yy, W, h)).copy()
            pedaco.set_alpha(a)
            tela.blit(pedaco, (0, y0 + yy))


# ------------------------------------------------------------------ a cena

def _txt(tela, f, txt, cor, pos, contorno=(40, 30, 40), centro=False, esp=2):
    t = f.render(txt, True, cor)
    o = f.render(txt, True, contorno)
    x, y = pos
    if centro:
        x -= t.get_width() // 2
    for dx in range(-esp, esp + 1):
        for dy in range(-esp, esp + 1):
            if dx or dy:
                tela.blit(o, (x + dx, y + dy))
    tela.blit(t, (x, y))
    return t.get_width()


def _cartao(tela, r, cor=(255, 252, 244), alfa=236, raio=18):
    r = pygame.Rect(r)
    s = pygame.Surface((r.w + 12, r.h + 14), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 20, 40, 60), (6, 9, r.w, r.h), border_radius=raio)
    pygame.draw.rect(s, (*cor, alfa), (0, 0, r.w, r.h), border_radius=raio)
    pygame.draw.rect(s, (255, 255, 255, 255), (0, 0, r.w, r.h), 3, border_radius=raio)
    tela.blit(s, r.topleft)


class CenaMapa(Estado):
    """Base: ilhas, caminho, nós, herói, câmera, luz e HUD. As filhas dizem o que é cada nó."""

    def __init__(self, app, ilhas, nos, mar, sel=0):
        super().__init__(app)
        self.ilhas, self.nos = ilhas, nos
        self.atm = Atmosfera(mar)
        f_placa = fonte(17, True)
        for il in ilhas:
            render_ilha(il, ESTILO[il.bioma], f_placa, plaqueta=self.plaquetas())
        self._pontes = self._fazer_pontes()
        self.sel = max(0, min(sel, len(nos) - 1))
        self.alvo = self.sel
        self.heroi = HeroiPapel(app)
        self.heroi.x, self.heroi.y = self.pos_heroi(nos[self.sel])
        self.cam = [self.heroi.x - W / 2, self.heroi.y - self._cy()]
        self.t = 0
        self._rota = []
        self._estados = {}
        self.festa = []
        self.botoes = {}
        self.recalcular()

    # -- para as filhas
    def pos_heroi(self, no):
        return no.x, no.y

    def plaquetas(self):
        return True

    def estado_no(self, no):
        return {"nivel": 0}

    def tipo_icone(self, no):
        return "fase"

    def ativar(self, no):
        pass

    def desenhar_hud(self, tela):
        pass

    # -- dados
    def recalcular(self):
        antes = dict(self._estados)
        self._estados = {id(n): self.estado_no(n) for n in self.nos}
        for n in self.nos:
            a, d = antes.get(id(n)), self._estados[id(n)]
            if a and d["nivel"] > a["nivel"]:
                self._comemorar(n, d["nivel"])

    def _comemorar(self, no, nivel):
        rng = random.Random()
        for _ in range(46):
            ang = rng.uniform(0, math.tau)
            v = rng.uniform(2, 7)
            self.festa.append([no.x, no.y - 30, math.cos(ang) * v, math.sin(ang) * v - 5, rng.randint(40, 70),
                               rng.choice([(255, 90, 110), (255, 214, 60), (90, 170, 255), (120, 230, 120), (255, 255, 255)])])
        self.app.audio.tocar("estrela")
        self.app.toast({3: "★ Dominada!", 2: "✔ Concluída!", 1: "Começou!"}[nivel])

    def _fazer_pontes(self):
        """Ligações entre ilhas: caminho de tábuas sobre o mar, da última fase de uma à primeira da próxima."""
        out = []
        for a, b in zip(self.ilhas, self.ilhas[1:]):
            p, q = a.nos[-1], b.nos[0]
            out.append(((p.x, p.y), (q.x, q.y)))
        return out

    def _cy(self):
        return TOPO_HUD + (H - TOPO_HUD - BASE_HUD) * 0.55

    # -- movimento
    def _ir_para(self, alvo):
        alvo = max(0, min(len(self.nos) - 1, alvo))
        if alvo == self.sel and not self._rota:
            return
        passo = 1 if alvo > self.sel else -1
        self._rota = list(range(self.sel + passo, alvo + passo, passo))
        self.alvo = alvo

    def _direcao(self, dx, dy):
        """Seta: vai para o vizinho do caminho (anterior ou seguinte) que fica mais na direção apertada."""
        if self._rota:
            return
        melhor, mv = None, 0.25
        for j in (self.sel - 1, self.sel + 1):
            if 0 <= j < len(self.nos):
                n0, n1 = self.nos[self.sel], self.nos[j]
                vx, vy = n1.x - n0.x, n1.y - n0.y
                d = math.hypot(vx, vy) or 1
                v = (vx * dx + vy * dy) / d
                if v > mv:
                    melhor, mv = j, v
        if melhor is None:                       # nenhum vizinho naquela direção: segue a ordem do caminho
            adiante = (dx > 0 or dy > 0) if PAISAGEM else (dx > 0 or dy < 0)
            melhor = self.sel + (1 if adiante else -1)
        self._ir_para(melhor)

    def _pular_ilha(self, d):
        il = self.nos[self.sel].ilha + d
        if 0 <= il < len(self.ilhas):
            alvo = self.nos.index(self.ilhas[il].nos[0])
            self._teleporte(alvo)

    def _teleporte(self, alvo):
        self._rota = []
        self.sel = self.alvo = max(0, min(len(self.nos) - 1, alvo))
        self.heroi.x, self.heroi.y = self.pos_heroi(self.nos[self.sel])
        self.heroi.rastro.clear()

    def evento(self, e, inp):
        if inp.foi("voltar"):
            self.app.pop()
            return
        if inp.foi("ok") or inp.foi("pulo"):
            if not self._rota:
                self.ativar(self.nos[self.sel])
            return
        for acao, (dx, dy) in (("esq", (-1, 0)), ("dir", (1, 0)), ("cima", (0, -1)), ("baixo", (0, 1))):
            if inp.foi(acao):
                self._direcao(dx, dy)
                return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_PAGEDOWN:
                self._pular_ilha(1)
            elif e.key == pygame.K_PAGEUP:
                self._pular_ilha(-1)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for nome, r in self.botoes.items():
                if r.collidepoint(e.pos):
                    self.botao(nome)
                    return
            mx, my = e.pos[0] + self.cam[0], e.pos[1] + self.cam[1]
            perto = min(range(len(self.nos)), key=lambda i: math.dist((mx, my), (self.nos[i].x, self.nos[i].y - 10)))
            if math.dist((mx, my), (self.nos[perto].x, self.nos[perto].y - 10)) < 56:
                if perto == self.sel and not self._rota:
                    self.ativar(self.nos[perto])
                else:
                    self._ir_para(perto)
        elif e.type == pygame.MOUSEWHEEL:
            self._direcao(0, -e.y) if not PAISAGEM else self._direcao(-e.y, 0)

    def botao(self, nome):
        pass

    def update(self, inp):
        self.t += 1
        h = self.heroi
        if self._rota:
            nx, ny = self.pos_heroi(self.nos[self._rota[0]])
            dx, dy = nx - h.x, ny - h.y
            d = math.hypot(dx, dy)
            vel = VEL * (2.2 if len(self._rota) > 2 else 1)
            h.virar(dx)
            if d <= vel:
                h.x, h.y = nx, ny
                self.sel = self._rota.pop(0)
                if not self._rota:
                    self.app.audio.tocar("menu")
            else:
                h.x += dx / d * vel
                h.y += dy / d * vel
            h.andando = True
        else:
            h.andando = False
            for acao, (dx, dy) in (("esq", (-1, 0)), ("dir", (1, 0)), ("cima", (0, -1)), ("baixo", (0, 1))):
                if inp.seg(acao) and self.t % 2 == 0:
                    self._direcao(dx, dy)
                    break
        h.update()
        # na lateral, a câmera puxa para o meio da ilha (em pé, a ilha inteira cabe na largura da tela)
        cx, cy = self.ilhas[self.nos[self.sel].ilha].centro
        if PAISAGEM:
            alvo_x, alvo_y = h.x - W / 2, 0.45 * h.y + 0.55 * cy - self._cy()
        else:
            alvo_x, alvo_y = 0.3 * h.x + 0.7 * cx - W / 2, h.y - self._cy()
        self.cam[0] += (alvo_x - self.cam[0]) * 0.12
        self.cam[1] += (alvo_y - self.cam[1]) * 0.12
        for p in self.festa:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[4] -= 1
        self.festa = [p for p in self.festa if p[4] > 0]

    def ao_voltar(self):
        self.heroi.pet = getattr(self.heroi, "pet", ("nenhum",) * 3)
        self.recalcular()

    # -- desenho
    def draw(self, tela):
        cam = (int(self.cam[0]), int(self.cam[1]))
        self.atm.fundo(tela, cam)
        tela_r = pygame.Rect(cam[0] - 40, cam[1] - 40, W + 80, H + 80)
        for a, b in self._pontes:
            self._ponte(tela, a, b, cam)
        for il in self.ilhas:
            r = pygame.Rect(il.pos, il.surf.get_size())
            if r.colliderect(tela_r):
                tela.blit(il.surf, (il.pos[0] - cam[0], il.pos[1] - cam[1]))
        vis = [n for n in self.nos if tela_r.collidepoint(n.x, n.y)]
        for n in vis:
            self._halo(tela, n, cam)
        hx, hy = self.heroi.x, self.heroi.y
        atras = [n for n in vis if n.y <= hy]
        frente = [n for n in vis if n.y > hy]
        for n in sorted(atras, key=lambda n: n.y):
            self._no(tela, n, cam)
        self.heroi.draw(tela, int(hx - cam[0]), int(hy - cam[1]))
        for n in sorted(frente, key=lambda n: n.y):
            self._no(tela, n, cam)
        for p in self.festa:
            pygame.draw.rect(tela, p[5], (int(p[0] - cam[0]), int(p[1] - cam[1]), 6, 4))
        self._rotulo_sel(tela, cam)
        self.atm.frente(tela, cam)
        self.botoes = {}
        self.desenhar_hud(tela)

    def _ponte(self, tela, a, b, cam):
        ax, ay = a[0] - cam[0], a[1] - cam[1]
        bx, by = b[0] - cam[0], b[1] - cam[1]
        if max(ax, bx) < -50 or min(ax, bx) > W + 50 or max(ay, by) < -50 or min(ay, by) > H + 50:
            return
        d = math.hypot(bx - ax, by - ay) or 1
        n = int(d / 16)
        ux, uy = (bx - ax) / d, (by - ay) / d
        px, py = -uy, ux
        for k in range(n + 1):
            t = k / max(1, n)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t + math.sin(t * math.pi) * 10
            c = (180, 128, 80) if k % 2 else (196, 144, 92)
            pts = [(x - px * 15 - ux * 6, y - py * 15 - uy * 6 + 8), (x + px * 15 - ux * 6, y + py * 15 - uy * 6 + 8),
                   (x + px * 15 + ux * 6, y + py * 15 + uy * 6 + 8), (x - px * 15 + ux * 6, y - py * 15 + uy * 6 + 8)]
            pygame.draw.polygon(tela, (0, 30, 60), [(p[0] + 5, p[1] + 10) for p in pts])
            pygame.draw.polygon(tela, c, pts)
            pygame.draw.polygon(tela, (120, 80, 50), pts, 1)

    def _halo(self, tela, n, cam):
        e = self._estados.get(id(n), {})
        cor = {3: (255, 200, 80), 2: (120, 170, 255), 1: (255, 160, 90)}.get(e.get("nivel", 0))
        sel = n is self.nos[self.sel]
        if sel:
            r = int(56 + 6 * math.sin(self.t * 0.12))
            g = _brilho(r, (120, 110, 70))
            tela.blit(g, (int(n.x - cam[0] - r), int(n.y - cam[1] - r + 4)), special_flags=pygame.BLEND_RGB_ADD)
        elif cor:
            g = _brilho(40, tuple(c // 3 for c in cor))
            tela.blit(g, (int(n.x - cam[0] - 44), int(n.y - cam[1] - 40)), special_flags=pygame.BLEND_RGB_ADD)

    def _no(self, tela, n, cam):
        e = self._estados.get(id(n), {"nivel": 0})
        x, y = n.x - cam[0], n.y - cam[1]
        grande = self.tipo_icone(n) == "castelo"
        ped = _pedestal(e["nivel"], 38 if grande else 30)
        tela.blit(ped, (int(x - ped.get_width() // 2), int(y - ped.get_height() // 2 + 4)))
        ico = _icone(self.tipo_icone(n), e["nivel"])
        if grande:
            ico = pygame.transform.smoothscale(ico, (int(ico.get_width() * 1.5), int(ico.get_height() * 1.5)))
        sel = n is self.nos[self.sel]
        bob = math.sin(self.t * 0.1 + n.k) * 3 if sel else 0
        if not (sel and (self.heroi.x, self.heroi.y) == self.pos_heroi(n)) or grande:
            tela.blit(ico, (int(x - ico.get_width() // 2), int(y - ico.get_height() + 2 + bob)))
        topo = y - ico.get_height() - 4
        selos = []
        if e["nivel"] == 3:
            selos.append("estrela")
        elif e["nivel"] == 2:
            selos.append("ok")
        if e.get("revisar"):
            selos.append("revisar")
        if e.get("atrasada"):
            selos.append("atrasada")
        if e.get("marcada") and e["nivel"] == 2 and not e.get("feitas"):
            selos[0:1] = ["marca"]
        for i, s in enumerate(selos):
            img = _selo(s)
            if s == "estrela":
                gx = abs(math.cos(self.t * 0.05 + n.k))
                img = pygame.transform.smoothscale(img, (max(2, int(22 * gx)), 22))
            sx = x + 16 + i * 18 - img.get_width() // 2
            sy = topo + 8 + math.sin(self.t * 0.08 + i + n.k) * 2
            tela.blit(img, (int(sx), int(sy)))
        if e.get("pct") is not None and grande:
            self._anel(tela, x, y - 6, e["pct"])

    def _anel(self, tela, x, y, pct):
        r = 44
        rect = pygame.Rect(int(x - r), int(y - r * 0.55), r * 2, int(r * 1.1))
        pygame.draw.ellipse(tela, (40, 40, 60), rect, 5)
        if pct > 0:
            pygame.draw.arc(tela, (120, 230, 120) if pct < 1 else (255, 214, 60), rect, math.pi / 2 - pct * math.tau,
                            math.pi / 2, 5)

    def _rotulo_sel(self, tela, cam):
        n = self.nos[self.sel]
        nome = self.nome_no(n)
        f = self.app.f["med"]
        txt = cortar(nome, f, 380)
        t = f.render(txt, True, TINTA)
        x = int(n.x - cam[0])
        y = int(n.y - cam[1] - 150)
        r = pygame.Rect(0, 0, t.get_width() + 28, t.get_height() + 14)
        r.midbottom = (x, y + 10)
        r.x = max(8, min(W - r.w - 8, r.x))
        _cartao(tela, r, alfa=246, raio=14)
        pygame.draw.polygon(tela, (255, 255, 255), [(x - 9, r.bottom), (x + 9, r.bottom), (x, r.bottom + 10)])
        tela.blit(t, (r.x + 14, r.y + 7))

    def nome_no(self, n):
        return ""

    def _botao(self, tela, nome, r, txt, cor=(255, 255, 255)):
        r = pygame.Rect(r)
        _cartao(tela, r, cor=cor, alfa=240, raio=14)
        f = self.app.f["peq"]
        t = f.render(txt, True, TINTA)
        tela.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))
        self.botoes[nome] = r


def _ha(ts):
    if not ts:
        return "nunca"
    d = (dt.date.today() - dt.date.fromtimestamp(ts)).days
    return "hoje" if d == 0 else "ontem" if d == 1 else f"há {d} dias"


def _contadores(tela, f, res, x, y, direita=False):
    itens = [("ok", f"{res['concl']}/{res['n']}"), ("estrela", str(res["dom"]))]
    if res["revisar"]:
        itens.append(("revisar", str(res["revisar"])))
    if res["atrasadas"]:
        itens.append(("atrasada", str(res["atrasadas"])))
    larg = sum(28 + f.size(t)[0] + 14 for _, t in itens)
    if direita:
        x -= larg
    for s, t in itens:
        tela.blit(pygame.transform.smoothscale(_selo(s), (26, 26)), (x, y + 2))
        x += 30
        x += _txt(tela, f, t, (255, 255, 255), (x, y)) + 14
    return larg


# ------------------------------------------------------------------ mapa-múndi

class MapaMundi(CenaMapa):
    def __init__(self, app, reinos, sel=0):
        self.reinos = reinos
        self.res = {}
        ilhas, nos = layout_mundi(reinos)
        if sel is None:
            sel = self._recomendado(app, reinos)
        super().__init__(app, ilhas, nos, MAR_MUNDI, sel)

    @staticmethod
    def _recomendado(app, reinos):
        hoje = dt.date.today()
        for i, r in enumerate(reinos):                 # o reino da aula de hoje (ou da próxima) no cronograma
            if any(f.data and f.data >= hoje for f in r.fases) and any(f.data and f.data <= hoje + dt.timedelta(days=7)
                                                                    for f in r.fases):
                return i
        for i, r in enumerate(reinos):
            if jornada.resumo(app.save, r.fases)["concl"] < len(r.fases):
                return i
        return 0

    def plaquetas(self):
        return False

    def pos_heroi(self, no):
        return no.x - 62, no.y + 26              # ao lado do castelo, sem cobri-lo

    def estado_no(self, no):
        r = no.dado
        res = jornada.resumo(self.app.save, r.fases)
        self.res[r.nome] = res
        n = max(1, res["n"])
        nivel = 3 if res["dom"] == res["n"] else 2 if res["concl"] == res["n"] else 1 if res["comecou"] else 0
        return {"nivel": nivel, "revisar": res["revisar"], "atrasada": res["atrasadas"] > 0, "pct": res["concl"] / n}

    def tipo_icone(self, no):
        return "castelo"

    def nome_no(self, n):
        return n.dado.nome

    def ativar(self, no):
        self.app.audio.tocar("ovo")
        self.app.push(MapaReino(self.app, no.dado))

    def draw(self, tela):
        super().draw(tela)

    def _no(self, tela, n, cam):
        super()._no(tela, n, cam)
        if n is not self.nos[self.sel]:              # nome de cada reino numa plaquinha (orientação no mapa)
            f = self.app.f["peq"]
            x, y = n.x - cam[0], n.y - cam[1] + 34
            t = f.render(n.dado.nome, True, TINTA)
            r = pygame.Rect(0, 0, t.get_width() + 16, t.get_height() + 6)
            r.midtop = (int(x), int(y))
            _cartao(tela, r, alfa=220, raio=10)
            tela.blit(t, (r.x + 8, r.y + 3))

    def desenhar_hud(self, tela):
        f, fm = self.app.f["peq"], self.app.f["med"]
        todas = [fz for r in self.reinos for fz in r.fases]
        res = jornada.resumo(self.app.save, todas) if self.t % 30 == 1 or not hasattr(self, "_res_tot") else self._res_tot
        self._res_tot = res
        _txt(tela, self.app.f["titulo"] if not RETRATO else self.app.f["grande"], "Mapa de Estudos", (255, 255, 255),
             (24, 14), esp=3)
        if RETRATO:
            _contadores(tela, fm, res, 24, 74)
        else:
            _contadores(tela, fm, res, W - 24, 28, direita=True)
        r = self.nos[self.sel].dado
        rs = self.res.get(r.nome) or jornada.resumo(self.app.save, r.fases)
        card = pygame.Rect(16, H - BASE_HUD + 8, W - 32, BASE_HUD - 54)
        _cartao(tela, card)
        tela.blit(self.app.f["grande"].render(r.nome, True, TINTA), (card.x + 20, card.y + 10))
        pct = rs["concl"] / max(1, rs["n"])
        _barra(tela, (card.x + 20, card.y + 56, card.w - 40 if RETRATO else 420, 16), rs["concl"], rs["dom"], rs["n"])
        linha = (f"{round(100 * pct)}% concluído · {rs['dom']} dominadas · {len(r.trilhas)} ilhas · "
                 f"última vez: {_ha(rs['ult'])}")
        y = card.y + 80
        for l in quebrar(linha, f, card.w - 40)[:2]:
            tela.blit(f.render(l, True, (90, 80, 90)), (card.x + 20, y))
            y += 22
        extra = []
        if rs["revisar"]:
            extra.append(f"{rs['revisar']} {'fase pede' if rs['revisar'] == 1 else 'fases pedem'} revisão")
        if rs["atrasadas"]:
            extra.append(f"{rs['atrasadas']} aulas da agenda já passaram sem ser feitas aqui")
        if extra:
            tela.blit(f.render(cortar(" · ".join(extra), f, card.w - 40), True, (200, 90, 60)), (card.x + 20, y))
        if not RETRATO:
            ilhas = ", ".join(t.nome for t in r.trilhas[:4]) + ("…" if len(r.trilhas) > 4 else "")
            tela.blit(f.render(cortar(ilhas, f, card.w - 500), True, (110, 100, 110)), (card.x + 470, card.y + 54))
        bw = 150 if RETRATO else 132
        self._botao(tela, "entrar", (card.right - bw - 16, card.y + 12, bw, 40), "▶ Entrar", (255, 226, 120))
        self._botao(tela, "diario", (W - 16 - bw * 2 - 10 if RETRATO else W - 300, 70 if not RETRATO else 118, bw, 38),
                    "Diário", (220, 240, 255))
        self._botao(tela, "lista", (W - 16 - bw, 70 if not RETRATO else 118, bw, 38), "Lista", (220, 255, 220))
        self._botao(tela, "voltar", (W - 16 - bw * 3 - 20 if RETRATO else W - 450, 70 if not RETRATO else 118, bw, 38),
                    "◀ Voltar")
        _dica(tela, f, "Setas andam · Enter entra no reino · R diário · Tab lista · Esc volta")

    def evento(self, e, inp):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
            self.botao("diario")
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            self.botao("lista")
            return
        super().evento(e, inp)

    def botao(self, nome):
        if nome == "entrar":
            self.ativar(self.nos[self.sel])
        elif nome == "voltar":
            self.app.pop()
        elif nome == "diario":
            abrir_diario(self.app, self.reinos, self)
        elif nome == "lista":
            menu = Menu(self.app, "Reinos", [], "Toque num reino para ir até ele no mapa")
            for i, r in enumerate(self.reinos):
                rs = jornada.resumo(self.app.save, r.fases)
                marca = "★ " if rs["dom"] == rs["n"] else "✔ " if rs["concl"] == rs["n"] else ""
                menu.itens.append({"label": marca + r.nome, "cor": COR_ESTADO[3 if marca == "★ " else 2 if marca else
                                                                            1 if rs["comecou"] else 0],
                                   "info": f"{rs['concl']}/{rs['n']} concluídas · {rs['dom']} dominadas · "
                                           f"{rs['revisar']} pedem revisão · última vez: {_ha(rs['ult'])}",
                                   "acao": (lambda i=i: (self.app.pop(), self._teleporte(i)))})
            menu.sel = self.sel
            self.app.push(menu)


def _barra(tela, r, concl, dom, n):
    x, y, w, h = r
    pygame.draw.rect(tela, (225, 220, 214), (x, y, w, h), border_radius=h // 2)
    if n:
        wc = int(w * concl / n)
        wd = int(w * dom / n)
        if wc:
            pygame.draw.rect(tela, (90, 150, 250), (x, y, max(h, wc), h), border_radius=h // 2)
        if wd:
            pygame.draw.rect(tela, (250, 200, 50), (x, y, max(h, wd), h), border_radius=h // 2)
    pygame.draw.rect(tela, (120, 110, 120), (x, y, w, h), 2, border_radius=h // 2)


def _dica(tela, f, txt):
    if edicao.ANDROID:
        txt = "Toque numa fase para andar até ela · toque de novo para jogar"
    _txt(tela, f, txt, (255, 255, 255), (W // 2, H - 34), centro=True, esp=1)


# ------------------------------------------------------------------ mapa do reino

class MapaReino(CenaMapa):
    def __init__(self, app, reino, sel=None):
        self.reino = reino
        ilhas, nos = layout_reino(reino)
        if sel is None:
            sel = jornada.proxima(app.save, [n.dado for n in nos])
        est = ESTILO[reino.bioma]
        super().__init__(app, ilhas, nos, est["mar"], sel)
        self._res = jornada.resumo(app.save, reino.fases)

    def estado_no(self, no):
        return jornada.estado(self.app.save, no.dado)

    def recalcular(self):
        super().recalcular()
        self._res = jornada.resumo(self.app.save, self.reino.fases)
        self._prox = jornada.proxima(self.app.save, [n.dado for n in self.nos])

    def tipo_icone(self, no):
        f = no.dado
        return {"castelo": "castelo", "treino": "treino", "fluxo": "fluxo", "ecg": "ecg", "aula": "aula",
                "prova": "prova"}.get(f.icone, "fase")

    def nome_no(self, n):
        return n.dado.nome

    def ativar(self, no):
        self.app.audio.tocar("ovo")
        no.dado.jogar(self.app)

    def _no(self, tela, n, cam):
        super()._no(tela, n, cam)
        if getattr(self, "_prox", None) is not None and n is self.nos[self._prox] and n is not self.nos[self.sel]:
            x, y = n.x - cam[0], n.y - cam[1] - 70 + math.sin(self.t * 0.15) * 6       # seta da próxima recomendada
            pygame.draw.polygon(tela, TINTA, [(x - 13, y - 4), (x + 13, y - 4), (x, y + 13)])
            pygame.draw.polygon(tela, (255, 226, 80), [(x - 9, y - 2), (x + 9, y - 2), (x, y + 9)])

    def desenhar_hud(self, tela):
        f, fm = self.app.f["peq"], self.app.f["med"]
        _txt(tela, self.app.f["titulo"] if not RETRATO else self.app.f["grande"], self.reino.nome, (255, 255, 255),
             (24, 14), esp=3)
        if RETRATO:
            _contadores(tela, fm, self._res, 24, 74)
        else:
            _contadores(tela, fm, self._res, W - 24, 28, direita=True)
        n = self.nos[self.sel]
        fz = n.dado
        trilha = self.reino.trilhas[n.ilha]
        e = self._estados[id(n)]
        card = pygame.Rect(16, H - BASE_HUD + 8, W - 32, BASE_HUD - 54)
        _cartao(tela, card)
        larg = card.w - 40 - (0 if RETRATO else 180)
        tela.blit(f.render(cortar(f"{trilha.nome} · {trilha.sub}", f, larg - (170 if RETRATO else 0)), True,
                           (130, 110, 120)), (card.x + 20, card.y + 10))
        y = card.y + 34
        for l in quebrar(fz.nome, fm, larg)[:2]:
            tela.blit(fm.render(l, True, TINTA), (card.x + 20, y))
            y += 28
        chip = jornada.ROTULO[e["nivel"]] + (" (marcada por você)" if e.get("marcada") else "")
        t = f.render(chip, True, (255, 255, 255))
        cr = pygame.Rect(card.x + 20, y + 4, t.get_width() + 20, t.get_height() + 6)
        pygame.draw.rect(tela, COR_ESTADO[e["nivel"]], cr, border_radius=cr.h // 2)
        tela.blit(t, (cr.x + 10, cr.y + 3))
        det = self._detalhe(fz, e)
        if RETRATO:
            y = cr.bottom + 6
            for l in quebrar(det, f, larg)[:2]:
                tela.blit(f.render(l, True, (90, 80, 90)), (card.x + 20, y))
                y += 22
        else:
            x = cr.right + 12
            tela.blit(f.render(cortar(det, f, card.x + 20 + larg - x), True, (90, 80, 90)), (x, cr.y + 3))
            y = cr.bottom + 6
        avisos = []
        if e.get("revisar"):
            avisos.append(f"{e['revisar']} {'questão pede' if e['revisar'] == 1 else 'questões pedem'} revisão "
                          "(erro ou intervalo vencido)")
        if e.get("atrasada"):
            avisos.append(f"aula de {fz.data:%d/%m} na agenda, ainda não feita aqui")
        for l in quebrar(" · ".join(avisos), f, larg)[:2] if avisos else []:
            tela.blit(f.render(l, True, (200, 90, 60)), (card.x + 20, y))
            y += 22
        bw = 150 if RETRATO else 132
        self._botao(tela, "jogar", (card.right - bw - 16, card.y + 12, bw, 40), "▶ Jogar", (255, 226, 120))
        if not RETRATO:
            self._botao(tela, "marcar", (card.right - bw - 16, card.y + 58, bw, 36),
                        "Desmarcar" if e.get("marcada") else "✎ Estudei", (236, 226, 255))
        topo_b = 118 if RETRATO else 70
        self._botao(tela, "lista", (W - 16 - bw, topo_b, bw, 38), "Lista", (220, 255, 220))
        self._botao(tela, "voltar", (W - 26 - bw * 2, topo_b, bw, 38), "◀ Mapa")
        if RETRATO:
            self._botao(tela, "marcar", (W - 36 - bw * 3, topo_b, bw, 38),
                        "Desmarcar" if e.get("marcada") else "✎ Estudei", (236, 226, 255))
        _dica(tela, f, "Setas andam · Enter joga · E marca 'estudei fora do jogo' · Tab lista · PgUp/PgDn ilha · Esc mapa")

    @staticmethod
    def _detalhe(fz, e):
        if fz.tipo == "questoes":
            return f"{e['feitas']}/{e['total']} respondidas · {e['dom']} certas na última vez · última vez: {_ha(e['ult'])}"
        if fz.tipo == "aula":
            return f"Aula de {fz.data:%d/%m/%Y} · fase do cronograma" + (" · feita" if e["feitas"] else "")
        if fz.tipo == "treino":
            return f"{e['feitas']}/{e['total']} habilidades treinadas · {e['dom']} com 80% de acerto"
        if fz.tipo == "fluxo":
            return f"Nível {max(1, e['feitas'])}/4 do fluxograma"
        if fz.tipo == "ecg":
            return f"{e['feitas']}/{e['total']} ritmos vistos · {e['dom']} com 80% de acerto"
        return ""

    def evento(self, e, inp):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_e:
            self.botao("marcar")
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            self.botao("lista")
            return
        super().evento(e, inp)

    def botao(self, nome):
        if nome == "jogar":
            self.ativar(self.nos[self.sel])
        elif nome == "voltar":
            self.app.pop()
        elif nome == "marcar":
            fz = self.nos[self.sel].dado
            on = jornada.alternar_marca(self.app.save, fz)
            self.app.toast("✎ Marcada como estudada" if on else "Marca retirada")
            self.recalcular()
        elif nome == "lista":
            abrir_lista(self.app, self)


# ------------------------------------------------------------------ lista (o "L" do Wonder) e diário

_MARCA = {0: "○ ", 1: "◐ ", 2: "✔ ", 3: "★ "}


def abrir_lista(app, cena):
    reino = cena.reino
    menu = Menu(app, reino.nome, [], "")

    def montar():
        res = jornada.resumo(app.save, reino.fases)
        menu.subtitulo = (f"{res['concl']}/{res['n']} concluídas · {res['dom']} dominadas · {res['revisar']} pedem "
                          f"revisão · {res['atrasadas']} aulas passadas sem fazer")
        menu.itens = []
        i = 0
        for t in reino.trilhas:
            menu.itens.append({"secao": t.nome[:40], "label": ""})
            if t.tipo == "agenda":
                passadas = [f for f in t.fases if f.data and f.data < dt.date.today()
                            and jornada.estado(app.save, f)["nivel"] < 2]
                if passadas:
                    menu.itens.append({"label": f"✎ Já assisti às {len(passadas)} aulas passadas desta ilha",
                                       "cor": (200, 180, 255), "info": "Marca como estudadas fora do jogo (dá para desmarcar uma a uma)",
                                       "acao": (lambda ps=passadas: _marcar_todas(app, ps, montar))})
            for f in t.fases:
                e = jornada.estado(app.save, f)
                extra = (" ⟳" if e["revisar"] else "") + (" !" if e["atrasada"] else "")
                info = MapaReino._detalhe(f, e)
                menu.itens.append({"label": _MARCA[e["nivel"]] + f.nome + extra, "info": info,
                                   "cor": COR_ESTADO[e["nivel"]],
                                   "acao": (lambda i=i: (app.pop(), cena._teleporte(i)))})
                i += 1
        menu._pular_desab(1)

    menu.ao_voltar = montar
    montar()
    alvo = cena.sel
    k = -1
    for j, it in enumerate(menu.itens):
        if it.get("acao") and not it.get("secao") and not it["label"].startswith("✎ Já"):
            k += 1
            if k == alvo:
                menu.sel = j
                break
    app.push(menu)


def _marcar_todas(app, fases, depois):
    for f in fases:
        if not jornada.marcada(app.save, f):
            jornada.alternar_marca(app.save, f)
    app.toast(f"✎ {len(fases)} aulas marcadas como estudadas")
    depois()


def abrir_diario(app, reinos, mundi):
    dias = jornada.diario(app.save, reinos)
    hoje = dt.date.today()
    nomes = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    itens = []
    for d, linhas in dias:
        q = sum(x[3] for x in linhas)
        c = sum(x[4] for x in linhas)
        rot = "Hoje" if d == hoje else "Ontem" if (hoje - d).days == 1 else f"{nomes[d.weekday()]} {d:%d/%m}"
        itens.append({"secao": f"{rot} · {q} questões · {round(100 * c / max(1, q))}% certas", "label": ""})
        for r, t, f, n, ok in linhas:
            ri = reinos.index(r)
            itens.append({"label": f.nome, "cor": COR_ESTADO[jornada.estado(app.save, f)["nivel"]],
                          "info": f"{r.nome} · {t.nome} · {n} respondidas, {ok} certas",
                          "acao": (lambda ri=ri, f=f: _ir_fase(app, mundi, reinos[ri], f))})
    if not itens:
        app.push(Mensagem(app, "Diário de estudo", "Nada respondido nos últimos 14 dias."))
        return
    app.push(Menu(app, "Diário de estudo", itens, "O que você estudou nos últimos 14 dias (pela última resposta de cada questão)"))


def _ir_fase(app, mundi, reino, fase):
    app.pop()
    mundi._teleporte(mundi.reinos.index(reino))
    k = [f.id for f in reino.fases].index(fase.id)
    app.push(MapaReino(app, reino, sel=k))


# ------------------------------------------------------------------ entrada

def abrir(app, temas=None):
    """temas: no Android, os pacotes do menu (sem cronograma nem prova por prevalência, que ficam só no PC)."""
    def tarefa():
        if edicao.ANDROID:
            return jornada.catalogo(com_agenda=False, temas=temas, com_clinica=False)
        return jornada.catalogo()

    def pronto(reinos, erro):
        if erro or not reinos:
            app.push(Mensagem(app, "Mapa indisponível", f"Não consegui montar o mapa. {erro or ''}"))
            return
        app.push(MapaMundi(app, reinos, sel=None))

    app.push(Carregando(app, "Desenhando o mapa", tarefa, pronto))
