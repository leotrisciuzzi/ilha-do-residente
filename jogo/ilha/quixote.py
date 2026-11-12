"""Elenco da tela conceito de La Mancha (Dom Quixote): quem aparece no lugar do gato e dos inimigos (figurino.ELENCO).

Só muda o desenho: a hitbox, a física e o comportamento continuam os do inimigo original, então o nível joga igual.
Cada inimigo vira uma figura do livro de Cervantes (domínio público), em Traço Ilha (poucas partes, contorno escuro):
  moinho     — bicho-questão, com a placa da questão: "aqueles que ali vês são gigantes" (cap. 8)
  gigante    — o chefe: o moinho que o cavaleiro enxerga, com braços (Briareu) e faixa vermelha
  ovelha     — os germes rasteiros: os rebanhos que ele toma por exércitos (cap. 18)
  carneiro   — quem tem espinho (não se pisa): chifres e espigões na lã
  clavilenho — quem voa: o cavalo de madeira com a cavilha na testa e as pás girando (2ª parte, cap. 41)
  odre       — caixas e comprimidos: os odres de vinho que ele esfaqueia na estalagem (cap. 35)
  pastor     — quem cospe de longe: pastor com a funda; o cuspe vira pedra
  cavaleiro  — os monstros fortes: o Cavaleiro dos Espelhos (2ª parte, cap. 14)
  encantador — o feiticeiro: Frestón, o sábio encantador que o Quixote culpa por tudo
Sancho Pança, montado no burro Ruço, fica no lugar do pet (Pet.forma = "sancho"); no fundo, o moinho-gigante e Dulcineia
ficam no lugar do Oni e do Daidara (quixote.Dupla).

Tudo é pré-desenhado e guardado no cache por (forma, tamanho, quadro); por quadro só há blits. Nada usa NumPy."""
import math

import pygame

from . import art
from .rig import contorno

K = (28, 20, 28)
SRC = pygame.SRCALPHA
_cache = {}

# classe do inimigo → forma (quem tem espinho vira carneiro, seja qual for a classe)
FORMA = {"BichoQuestao": "moinho", "Gigante": "gigante",
         "Bacilo": "ovelha", "Estafilococo": "ovelha", "Estreptococo": "ovelha", "Ameba": "ovelha",
         "Globulo": "ovelha", "Carrapato": "ovelha", "Tatu": "ovelha",
         "Virus": "carneiro", "Fago": "carneiro", "Candida": "carneiro",
         "Aedes": "clavilenho", "Morcego": "clavilenho", "Mosca": "clavilenho", "AguaViva": "clavilenho",
         "Caixa": "odre", "Comprimido": "odre", "Lombriga": "odre", "Musgo": "odre",
         "Cuspidor": "pastor", "Chifrudo": "cavaleiro", "Louva": "cavaleiro", "Colosso": "cavaleiro",
         "Feiticeiro": "encantador"}
PEDRAS = ("Cuspe", "Seringa", "Esporo")      # projéteis: as pedradas que o Quixote leva no livro
VOAM = ("clavilenho", "encantador")


def forma_de(e):
    """Forma do inimigo, ou None para quem fica como está (ondas, orbes de magia)."""
    nome = type(e).__name__
    if nome in PEDRAS:
        return "pedra"
    if nome in FORMA and FORMA[nome] in ("moinho", "gigante"):
        return FORMA[nome]
    if getattr(e, "espinhento", False):
        return "carneiro"
    if nome in FORMA:
        return FORMA[nome]
    return "moinho" if getattr(e, "boneco", None) is not None else None


# --------------------------------------------------------------------- utilidades

def _par(v):
    """Tamanhos em passos de 2 px: poucas entradas no cache."""
    return max(6, int(v) // 2 * 2)


def _sprite(chave, w, h, pinta, cor=K):
    if chave not in _cache:
        c = pygame.Surface((w, h), SRC)
        pinta(c)
        _cache[chave] = contorno(c, cor)
    return _cache[chave]


def _versao(spr, chave, virado, branco):
    ch = ("v", chave, virado < 0, branco)
    if ch not in _cache:
        s = pygame.transform.flip(spr, True, False) if virado < 0 else spr
        if branco:
            s = s.copy()
            s.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        _cache[ch] = s
    return _cache[ch]


def _colar(s, cam, e, spr, chave, voa=False, dy=0):
    """Cola centrado na hitbox: no chão pelos pés, no ar pelo centro. Devolve o canto da superfície na tela."""
    virado = getattr(e, "virado", 1) or 1
    branco = getattr(e, "branco", 0) > 4
    t = _versao(spr, chave, virado, branco)
    tremor = 0
    if getattr(e, "estado", "") in ("mira", "ergue", "grito", "incha", "acorda", "prestes"):
        tremor = (getattr(e, "t", 0) % 3) - 1
    x = int(e.x + e.w / 2 - t.get_width() / 2 - cam[0]) + tremor
    base = e.y + e.h / 2 + t.get_height() / 2 if voa else e.y + e.h
    y = int(base - t.get_height() - cam[1]) + dy
    s.blit(t, (x, y))
    return x, y


def _barra(s, cam, e):
    """Barra de vida dos inimigos grandes (a mesma de monstros.Monstro)."""
    vmax = getattr(e, "vida_max", 0)
    if vmax >= 6 and e.vida < vmax:
        bx, by = int(e.x - cam[0]), int(e.y - cam[1]) - 6
        s.fill((20, 14, 30), (bx, by, int(e.w), 3))
        s.fill((226, 60, 60), (bx, by, int(e.w * e.vida / vmax), 3))


def _anda(e):
    return abs(getattr(e, "vx", 0)) > 0.05


# --------------------------------------------------------------------- moinho e gigante

MADEIRA, LONA = (112, 74, 44), (246, 234, 206)
TELHADOS = ((172, 78, 54), (98, 110, 138), (120, 128, 76), (140, 92, 150), (196, 140, 54))


def pas(c, x, y, r, ang, lona=LONA, madeira=MADEIRA, larg=0.3):
    """As quatro pás, de frente: varão de madeira e vela de treliça de um lado só. Serve ao sprite e ao cenário."""
    for k in range(4):
        a = ang + k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca
        w = max(2.0, r * larg)
        ini = r * 0.22
        pts = [(x + ca * ini, y + sa * ini), (x + ca * r, y + sa * r),
               (x + ca * r + nx * w, y + sa * r + ny * w), (x + ca * ini + nx * w, y + sa * ini + ny * w)]
        pygame.draw.polygon(c, lona, pts)
        if r >= 10:                                    # treliça: dois riscos atravessando a vela
            for f in (0.5, 0.75):
                pygame.draw.line(c, madeira, (x + ca * r * f, y + sa * r * f),
                                 (x + ca * r * f + nx * w, y + sa * r * f + ny * w))
        pygame.draw.line(c, madeira, (x, y), (x + ca * r, y + sa * r))
    pygame.draw.circle(c, madeira, (int(x), int(y)), max(1, int(r * 0.12)))


R_CUBO, R_PA, Y_OLHO = 0.33, 0.31, 0.76          # as pás giram acima do rosto, sem cobrir os olhos


def _desenha_moinho(c, h, telhado, quadro, chefe, bravo):
    w = c.get_width()
    cx = w // 2
    topo, base = int(h * 0.3), h - 1
    tw, bw = max(3, int(h * 0.18)), max(4, int(h * 0.27))
    parede = (70, 62, 72) if chefe else (246, 238, 218)
    sombra = (44, 38, 48) if chefe else (206, 186, 168)
    pygame.draw.polygon(c, parede, [(cx - tw, topo), (cx + tw, topo), (cx + bw, base), (cx - bw, base)])
    pygame.draw.polygon(c, sombra, [(cx + tw // 3, topo), (cx + tw, topo), (cx + bw, base), (cx + bw // 3, base)])
    pygame.draw.polygon(c, telhado, [(cx - tw - 2, topo), (cx, int(h * 0.04)), (cx + tw + 2, topo)])
    pas(c, cx + 1, int(h * R_CUBO), h * R_PA, quadro * math.pi / 12)
    # rosto: brancos dos olhos no sprite; as pupilas vão por quadro (seguem o herói)
    ey, er = int(h * Y_OLHO), max(1, int(h * 0.055))
    for lado in (-1, 1):
        ex = cx + lado * max(2, int(h * 0.1))
        pygame.draw.circle(c, (255, 255, 255), (ex, ey), er)
        ang = 2 if bravo or chefe else 1
        pygame.draw.line(c, K, (ex - lado * (er + 1), ey - er - ang), (ex + lado * (er + 1), ey - er), 1)
    my = int(h * 0.88)
    c.fill(K, (cx - max(1, int(h * 0.07)), my, max(2, int(h * 0.14)), max(1, int(h * 0.03))))
    if chefe:                                          # dentes, faixa vermelha na testa e braços (Briareu)
        for k in range(-1, 2):
            c.set_at((cx + k * 2, my), (255, 255, 255))
        c.fill((220, 40, 48), (cx - tw, int(h * 0.64), tw * 2, max(1, int(h * 0.03))))


def desenhar_moinho(s, cam, e, chefe=False):
    if chefe and getattr(e, "invuln", 0) and e.invuln % 6 < 3:
        return
    h = _par(max(e.h * 2.4, 24))
    r = int(h * R_PA)
    w = 2 * r + 10
    bravo = bool(getattr(e, "bravo", 0))
    if chefe:
        telhado = (34, 28, 40)
    elif bravo:
        telhado = (226, 66, 66)
    else:
        telhado = getattr(e, "cor", None) or TELHADOS[sum(map(ord, type(e).__name__)) % len(TELHADOS)]
    vel = 0.5 if bravo else 0.3 if _anda(e) else 0.14
    quadro = int(getattr(e, "t", 0) * vel) % 6
    chave = ("moinho", h, tuple(telhado), quadro, chefe, bravo)
    spr = _sprite(chave, w, h, lambda c: _desenha_moinho(c, h, telhado, quadro, chefe, bravo))
    pulo = int(abs(math.sin(getattr(e, "t", 0) * 0.22)) * 2) if _anda(e) and getattr(e, "no_chao", True) else 0
    x, y = _colar(s, cam, e, spr, chave, dy=-pulo)
    virado = getattr(e, "virado", 1) or 1
    # pés (fora do sprite, para trocar a passada sem multiplicar o cache)
    pe = max(2, h // 12)
    passo = int(math.sin(getattr(e, "t", 0) * 0.3) * pe) if _anda(e) else 0
    cx = x + w // 2
    for lado in (-1, 1):
        s.fill(K, (cx + lado * int(h * 0.14) - pe + lado * passo, y + h - 1 + pulo, pe * 2, 2))
    # pupilas e pálpebra: olham para o herói
    olhos = getattr(getattr(e, "boneco", None), "olhos", None)
    ox = int(round(olhos.ox.v)) if olhos else 0
    oy = int(round(olhos.oy.v)) if olhos and h >= 40 else 0
    fechado = bool(olhos and olhos.fechado)
    ey, er = int(h * Y_OLHO), max(1, int(h * 0.055))
    pup = (230, 40, 48) if chefe else K
    for lado in (-1, 1):
        ex = cx + lado * max(2, int(h * 0.1))
        if fechado:
            s.fill(K, (ex - er, y + ey, er * 2 + 1, 1))
        else:
            d = max(1, er // 2 + 1)
            s.fill(pup, (ex + ox * (er // 2) * virado - d // 2, y + ey + oy - d // 2, d, d))
    if chefe:                                          # braços que batem no ar
        a = math.sin(getattr(e, "t", 0) * 0.12) * 5
        for lado in (-1, 1):
            ax, ay = cx + lado * int(h * 0.2), y + int(h * 0.62)
            bx, by = ax + lado * int(h * 0.24), ay - int(h * 0.1) + int(a * lado)
            pygame.draw.line(s, K, (ax, ay), (bx, by), 5)
            pygame.draw.line(s, (112, 100, 110), (ax, ay), (bx, by), 3)
            pygame.draw.circle(s, K, (bx, by), 5)
            pygame.draw.circle(s, (140, 126, 134), (bx, by), 4)
    placa = getattr(getattr(e, "boneco", None), "placa", None)
    if placa is not None:                              # a placa da questão, sempre legível
        s.blit(placa, (cx - (r + 3) * virado - placa.get_width() // 2, y + h // 3 + int(math.sin(e.t * 0.1) * 1.5)))


# --------------------------------------------------------------------- ovelha e carneiro

def _desenha_ovelha(c, w, h, passo, carneiro):
    la, la2 = ((150, 140, 134), (112, 102, 104)) if carneiro else ((250, 246, 232), (214, 204, 196))
    cara = (74, 58, 62) if carneiro else (46, 38, 44)
    perna = h - max(2, h // 5)
    for k, px in enumerate((w * 0.24, w * 0.36, w * 0.6, w * 0.72)):   # pernas alternadas
        alt = 1 if (k + passo) % 2 else 0
        c.fill(cara, (int(px), perna - 1, max(1, w // 12), h - perna + 1 - alt))
    rx, ry = w * 0.32, (h - 3) * 0.32
    cy = (h - 3) * 0.5
    for k in range(5):                                 # lã: cinco bolotas
        a = k * math.pi * 2 / 5
        pygame.draw.circle(c, la2, (int(w * 0.42 + math.cos(a) * rx * 0.7 + 1), int(cy + math.sin(a) * ry * 0.7 + 1)),
                           max(2, int(ry * 0.8)))
    for k in range(5):
        a = k * math.pi * 2 / 5
        pygame.draw.circle(c, la, (int(w * 0.42 + math.cos(a) * rx * 0.7), int(cy + math.sin(a) * ry * 0.7)),
                           max(2, int(ry * 0.72)))
    fx, fy = int(w * 0.8), int(cy)
    fr = max(2, int(h * 0.2))
    pygame.draw.ellipse(c, cara, (fx - fr, fy - fr, fr * 2, int(fr * 2.2)))
    c.fill(cara, (fx - fr - 1, fy - fr, max(1, fr // 2), max(1, fr // 2)))     # orelha
    c.set_at((fx, fy - 1), (255, 255, 255))
    if carneiro:                                       # chifres enrolados e espigões: não dá para pisar
        chifre = (236, 214, 150)
        pygame.draw.arc(c, chifre, (fx - fr - 2, fy - fr - 3, fr * 2 + 2, fr * 2 + 2), 0.3, 3.4, 2)
        for k in range(4):
            px = int(w * (0.18 + k * 0.17))
            pygame.draw.polygon(c, chifre, [(px - 2, int(cy - ry)), (px, max(0, int(cy - ry - 4))), (px + 2, int(cy - ry))])


def desenhar_ovelha(s, cam, e, carneiro=False):
    w, h = _par(max(e.w * 1.8, 22)), _par(max(e.h * 1.9, 18))
    if carneiro:
        h += 4
    passo = (e.t // 6) % 2 if _anda(e) else 0
    chave = ("ovelha", w, h, passo, carneiro)
    spr = _sprite(chave, w, h, lambda c: _desenha_ovelha(c, w, h, passo, carneiro))
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- Clavilenho, o cavalo de madeira que voa

def _desenha_clavilenho(c, w, h, quadro):
    mad, mad2, crina = (168, 116, 66), (120, 78, 44), (70, 46, 34)
    my = int(h * 0.62)
    c.fill(mad2, (int(w * 0.22), my + int(h * 0.1), max(2, w // 10), int(h * 0.26)))      # pernas de pau
    c.fill(mad2, (int(w * 0.62), my + int(h * 0.1), max(2, w // 10), int(h * 0.26)))
    c.fill(mad, (int(w * 0.14), my - int(h * 0.14), int(w * 0.62), int(h * 0.28)))        # corpo: uma tábua
    c.fill(mad2, (int(w * 0.14), my + int(h * 0.08), int(w * 0.62), max(1, h // 14)))
    pygame.draw.polygon(c, mad, [(int(w * 0.62), my), (int(w * 0.8), int(h * 0.3)), (int(w * 0.98), int(h * 0.36)),
                                 (int(w * 0.92), int(h * 0.5)), (int(w * 0.76), my)])     # pescoço e cabeça
    c.fill(crina, (int(w * 0.66), int(h * 0.34), 2, int(h * 0.2)))
    c.set_at((int(w * 0.84), int(h * 0.38)), K)
    c.fill((236, 196, 90), (int(w * 0.86), int(h * 0.27), 2, 2))                          # a cavilha na testa
    c.fill(crina, (0, my - int(h * 0.1), int(w * 0.16), 2))                               # rabo
    pas(c, w * 0.44, h * 0.28, min(w * 0.3, h * 0.28), quadro * math.pi / 8, larg=0.34)   # as pás fazem voar


def desenhar_clavilenho(s, cam, e):
    w, h = _par(max(e.w * 1.8, 24)), _par(max(e.h * 2.2, 22))
    quadro = (getattr(e, "t", 0) // 2) % 4
    chave = ("clavilenho", w, h, quadro)
    spr = _sprite(chave, w, h, lambda c: _desenha_clavilenho(c, w, h, quadro))
    _colar(s, cam, e, spr, chave, voa=True)
    _barra(s, cam, e)


# --------------------------------------------------------------------- odre de vinho

def _desenha_odre(c, w, h, q):
    couro, couro2, tinto = (124, 44, 52), (86, 26, 40), (164, 30, 60)
    sx = 1 + (0.06 if q else -0.04)
    bw, bh = int(w * 0.8 * sx), int(h * 0.74 / sx)
    x0, y0 = (w - bw) // 2, h - bh
    pygame.draw.ellipse(c, couro, (x0, y0, bw, bh))
    pygame.draw.ellipse(c, couro2, (x0 + bw // 2, y0 + bh // 3, bw // 2, bh * 2 // 3))
    c.fill((186, 96, 90), (x0 + bw // 4, y0 + bh // 6, max(1, bw // 5), 1))              # brilho do couro
    c.fill(couro2, (w // 2 - 2, 2, 4, y0 + 1))                                          # gargalo amarrado
    c.fill((226, 200, 140), (w // 2 - 3, 3, 6, 2))
    ey = y0 + bh // 3
    for lado in (-1, 1):                               # cara emburrada, como o gigante que ele vê no odre
        ex = w // 2 + lado * max(2, w // 7)
        c.fill((255, 255, 255), (ex - 1, ey, 2, 2))
        c.set_at((ex, ey + 1), K)
        pygame.draw.line(c, K, (ex - lado * 2, ey - 2), (ex + lado * 1, ey - 1))
    c.fill(K, (w // 2 - 2, ey + 4, 4, 1))
    if q:                                              # o vinho vazando pelo furo
        c.fill(tinto, (x0 + 1, y0 + bh * 2 // 3, 2, 3))


def desenhar_odre(s, cam, e):
    w, h = _par(max(e.w * 1.4, 16)), _par(max(e.h * 1.5, 18))
    q = (getattr(e, "t", 0) // 12) % 2
    chave = ("odre", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _desenha_odre(c, w, h, q))
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- figuras de pé

def _pernas(c, cx, y, h, passo, cor, bota):
    for lado in (-1, 1):
        d = lado * passo
        c.fill(cor, (cx + lado * 2 - 1 + d, y, 3, h - y - 2))
        c.fill(bota, (cx + lado * 2 - 1 + d, h - 2, 4, 2))


def _desenha_pastor(c, w, h, q, mira):
    cx = w // 2 - 2
    _pernas(c, cx, int(h * 0.7), h, 0, (100, 76, 54), (60, 42, 32))
    c.fill((150, 112, 72), (cx - 5, int(h * 0.36), 10, int(h * 0.36)))                 # gibão de pele
    c.fill((222, 204, 170), (cx - 5, int(h * 0.36), 10, 2))
    c.fill((96, 66, 44), (cx - 5, int(h * 0.56), 10, 1))
    pygame.draw.circle(c, (236, 190, 150), (cx + 1, int(h * 0.24)), max(3, int(h * 0.13)))
    c.fill((70, 48, 34), (cx - 3, int(h * 0.3), 8, 2))                                 # barba
    c.set_at((cx + 3, int(h * 0.22)), K)
    c.fill((120, 92, 56), (cx - 6, int(h * 0.1), 14, 2))                               # chapéu de aba
    c.fill((120, 92, 56), (cx - 3, int(h * 0.03), 8, int(h * 0.09)))
    a = q * math.pi / 2 + (0.6 if mira else 0)                                         # a funda girando
    mx, my = cx + 6, int(h * 0.3)
    fx, fy = mx + math.cos(a) * 6, my - 3 + math.sin(a) * 4
    pygame.draw.line(c, (70, 54, 44), (mx, my + 4), (fx, fy))
    c.fill((120, 118, 124), (int(fx) - 1, int(fy) - 1, 3, 3))
    c.fill((236, 190, 150), (mx - 1, my + 3, 3, 3))


def _desenha_cavaleiro(c, w, h, q, branco_olho):
    aco, aco2, espelho = (170, 180, 198), (108, 118, 142), (206, 238, 252)
    cx = w // 2 - 1
    _pernas(c, cx, int(h * 0.68), h, q, aco2, (70, 76, 96))
    c.fill(aco, (cx - int(w * 0.2), int(h * 0.3), int(w * 0.4), int(h * 0.4)))          # peitoral
    c.fill(aco2, (cx + int(w * 0.04), int(h * 0.3), int(w * 0.16), int(h * 0.4)))
    pygame.draw.circle(c, (120, 150, 190), (cx, int(h * 0.48)), max(2, int(w * 0.12)))  # os espelhos da armadura
    pygame.draw.circle(c, espelho, (cx - 1, int(h * 0.47)), max(1, int(w * 0.07)))
    pygame.draw.circle(c, aco, (cx + 1, int(h * 0.18)), max(3, int(h * 0.15)))          # elmo fechado
    c.fill(K, (cx - 1, int(h * 0.16), int(h * 0.15) + 1, 2))                            # viseira
    c.set_at((cx + int(h * 0.08), int(h * 0.165)), (255, 90, 70) if branco_olho else (255, 255, 255))
    for k in range(4):                                 # penacho
        c.fill((70, 110, 190), (cx - 3 - k, int(h * 0.02) + k, 3, 2))
    ex = cx + int(w * 0.24)                            # espada
    pygame.draw.line(c, espelho, (ex, int(h * 0.52)), (ex + int(w * 0.18), int(h * 0.1) + q), 2)
    c.fill((236, 196, 90), (ex - 2, int(h * 0.5), 5, 2))
    r = max(3, int(h * 0.16))                          # escudo com a lua (o Cavaleiro da Branca Lua é o mesmo)
    pygame.draw.circle(c, (56, 72, 130), (cx - int(w * 0.24), int(h * 0.48)), r)
    pygame.draw.circle(c, (240, 240, 250), (cx - int(w * 0.24), int(h * 0.48)), max(1, r // 2))
    pygame.draw.circle(c, (56, 72, 130), (cx - int(w * 0.24) + 1, int(h * 0.48) - 1), max(1, r // 2))


def _desenha_encantador(c, w, h, q):
    manto, manto2, ouro = (54, 42, 96), (34, 26, 66), (246, 206, 90)
    cx = w // 2 - 1
    pygame.draw.polygon(c, manto, [(cx - 3, int(h * 0.36)), (cx + 4, int(h * 0.36)), (cx + int(w * 0.28), h - 2),
                                   (cx - int(w * 0.28), h - 2)])
    pygame.draw.polygon(c, manto2, [(cx + 1, int(h * 0.36)), (cx + 4, int(h * 0.36)), (cx + int(w * 0.28), h - 2),
                                    (cx + 3, h - 2)])
    for fx, fy in ((-0.1, 0.62), (0.08, 0.8), (-0.16, 0.86)):
        c.set_at((cx + int(w * fx), int(h * fy)), ouro)
    pygame.draw.circle(c, (236, 196, 160), (cx, int(h * 0.3)), max(3, int(h * 0.1)))
    pygame.draw.polygon(c, (240, 240, 244), [(cx - 3, int(h * 0.33)), (cx + 4, int(h * 0.33)), (cx + 1, int(h * 0.56))])  # barba
    c.set_at((cx + 2, int(h * 0.28)), K)
    pygame.draw.polygon(c, manto, [(cx - int(w * 0.24), int(h * 0.24)), (cx + 2, 0), (cx + int(w * 0.24), int(h * 0.24))])  # chapéu
    c.fill(ouro, (cx - int(w * 0.24), int(h * 0.23), int(w * 0.5), 2))
    ex = cx + int(w * 0.3)                             # cajado com a faísca do encanto
    c.fill((120, 84, 50), (ex, int(h * 0.2), 2, int(h * 0.76)))
    r = 2 if q else 3
    pygame.draw.circle(c, ouro, (ex + 1, int(h * 0.17)), r)
    c.set_at((ex + 1, int(h * 0.17)), (255, 255, 255))


def desenhar_pastor(s, cam, e):
    w, h = _par(max(e.w * 1.9, 24)), _par(max(e.h * 1.5, 26))
    q = (e.t // 5) % 4
    mira = getattr(e, "estado", "") == "mira"
    chave = ("pastor", w, h, q, mira)
    spr = _sprite(chave, w, h, lambda c: _desenha_pastor(c, w, h, q, mira))
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


def desenhar_cavaleiro(s, cam, e):
    w, h = _par(max(e.w * 1.6, 26)), _par(max(e.h * 1.25, 30))
    q = ((e.t // 7) % 3 - 1) if _anda(e) else 0
    bravo = getattr(e, "estado", "") in ("mira", "grito", "ergue", "prestes", "incha")
    chave = ("cavaleiro", w, h, q, bravo)
    spr = _sprite(chave, w, h, lambda c: _desenha_cavaleiro(c, w, h, q, bravo))
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


def desenhar_encantador(s, cam, e):
    w, h = _par(max(e.w * 1.8, 26)), _par(max(e.h * 1.3, 32))
    q = (e.t // 10) % 2
    chave = ("encantador", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _desenha_encantador(c, w, h, q))
    _colar(s, cam, e, spr, chave, dy=int(math.sin(e.t * 0.06) * 2))
    _barra(s, cam, e)


def desenhar_pedra(s, cam, e):
    x, y = int(e.x + e.w / 2 - cam[0]), int(e.y + e.h / 2 - cam[1])
    pygame.draw.circle(s, K, (x, y), 4)
    pygame.draw.circle(s, (150, 144, 140), (x, y), 3)
    s.fill((206, 200, 192), (x - 1, y - 2, 2, 1))


_DESENHOS = {"moinho": desenhar_moinho, "gigante": lambda s, cam, e: desenhar_moinho(s, cam, e, True),
             "ovelha": desenhar_ovelha, "carneiro": lambda s, cam, e: desenhar_ovelha(s, cam, e, True),
             "clavilenho": desenhar_clavilenho, "odre": desenhar_odre, "pastor": desenhar_pastor,
             "cavaleiro": desenhar_cavaleiro, "encantador": desenhar_encantador, "pedra": desenhar_pedra}


def desenhar(s, cam, e):
    """Desenha o inimigo com a forma de La Mancha. False = esse aí fica com o desenho de sempre."""
    forma = forma_de(e)
    if forma is None:
        return False
    _DESENHOS[forma](s, cam, e)
    return True


# --------------------------------------------------------------------- os gigantes do fundo em La Mancha
# No lugar do Oni e do Daidara (mesma interface de gigantes.Dupla): o moinho-gigante zomba do erro, e Dulcineia del
# Toboso, a dama que o cavaleiro imagina, torce pelo jogador. Quadros pré-desenhados, escolhidos por humor e pás.

GW, GH = 96, 108


def _gigante_moinho(c, q, humor):
    cx, chao = GW // 2, GH
    parede, sombra, teto = (236, 226, 204), (190, 170, 158), (116, 78, 62)
    # o rosto fica alto na torre: os morros cobrem a parte de baixo
    pygame.draw.polygon(c, parede, [(cx - 24, 28), (cx + 24, 28), (cx + 36, chao), (cx - 36, chao)])
    pygame.draw.polygon(c, sombra, [(cx + 8, 28), (cx + 24, 28), (cx + 36, chao), (cx + 16, chao)])
    pygame.draw.polygon(c, teto, [(cx - 30, 29), (cx, 2), (cx + 30, 29)])
    pas(c, cx, 22, 21, q * math.pi / 12, larg=0.3)
    ey = 54
    for lado in (-1, 1):
        ex = cx + lado * 12
        if humor == "ri":                              # olhos fechados de gargalhada
            pygame.draw.arc(c, K, (ex - 6, ey - 4, 12, 10), 0.2, 2.9, 2)
        else:
            pygame.draw.circle(c, (255, 255, 255), (ex, ey), 6)
            pygame.draw.circle(c, K, (ex - lado * 1, ey + 1), 3)
        cai = 4 if humor != "triste" else -4           # sobrancelha de raiva; emburrado, ela cai para fora
        pygame.draw.line(c, K, (ex + lado * 8, ey - 8 - cai), (ex - lado * 6, ey - 8 + cai // 2), 3)
    if humor == "ri":
        pygame.draw.ellipse(c, K, (cx - 13, 64, 26, 20))
        c.fill((255, 255, 255), (cx - 9, 65, 18, 4))
        pygame.draw.ellipse(c, (190, 60, 70), (cx - 7, 75, 14, 7))
    elif humor == "triste":
        pygame.draw.arc(c, K, (cx - 10, 68, 20, 14), 0.3, 2.8, 3)
    else:
        c.fill(K, (cx - 10, 70, 20, 3))


def _dulcineia(c, humor, fecha):
    cx = GW // 2
    cabelo, pele, pele2 = (34, 24, 30), (246, 208, 172), (222, 168, 134)
    vestido, renda = (176, 40, 64), (248, 240, 226)
    pygame.draw.polygon(c, vestido, [(cx - 16, 70), (cx + 16, 70), (cx + 40, GH), (cx - 40, GH)])
    pygame.draw.polygon(c, renda, [(cx - 12, 70), (cx + 12, 70), (cx, 92)])
    pygame.draw.circle(c, cabelo, (cx, 8), 10)                                       # coque
    pygame.draw.ellipse(c, cabelo, (cx - 32, 10, 64, 68))
    pygame.draw.ellipse(c, pele, (cx - 25, 20, 50, 54))
    pygame.draw.polygon(c, cabelo, [(cx - 25, 34), (cx - 22, 16), (cx + 22, 16), (cx + 25, 34), (cx, 22)])  # risca no meio
    pygame.draw.ellipse(c, pele2, (cx + 8, 26, 17, 46))                              # sombra dura de um lado
    pygame.draw.ellipse(c, pele, (cx + 2, 24, 18, 48))
    for dx, cor in ((0, (214, 34, 58)), (5, (236, 70, 84)), (-5, (190, 24, 50))):     # a rosa no cabelo
        pygame.draw.circle(c, cor, (cx - 25 + dx, 22 + abs(dx) // 2), 6)
    pygame.draw.circle(c, (150, 16, 40), (cx - 25, 22), 2)
    ey = 46
    for lado in (-1, 1):
        ex = cx + lado * 11
        if fecha or humor == "ri":                     # de alegria, olhos em arco
            pygame.draw.arc(c, K, (ex - 5, ey - 3, 10, 8), 0.2, 2.9, 2)
        else:
            pygame.draw.circle(c, (255, 255, 255), (ex, ey), 5)
            pygame.draw.circle(c, K, (ex, ey), 3)
            c.set_at((ex - 1, ey - 1), (255, 255, 255))
        cai = 3 if humor == "triste" else 0
        pygame.draw.line(c, cabelo, (ex - 6, ey - 8 - (cai if lado > 0 else -cai)), (ex + 6, ey - 8 + (cai if lado > 0 else -cai)), 2)
        pygame.draw.circle(c, (244, 150, 140), (ex + lado * 3, ey + 11), 4)
    if humor == "ri":
        pygame.draw.ellipse(c, (170, 30, 60), (cx - 9, 58, 18, 11))
        c.fill((255, 255, 255), (cx - 6, 58, 12, 3))
    elif humor == "triste":
        pygame.draw.arc(c, (170, 30, 60), (cx - 6, 61, 12, 9), 0.4, 2.7, 2)
        c.fill((140, 200, 255), (cx + 12, 54, 2, 5))                                  # lágrima
    else:
        pygame.draw.arc(c, (170, 30, 60), (cx - 9, 52, 18, 13), 3.4, 6.0, 2)


class Dupla:
    """Mesmos métodos de gigantes.Dupla: acerto, erro, dano, chefe_vencido, passo, draw. Outro tema herda e troca os
    dois desenhos (pinta_esq = quem torce, pinta_dir = quem zomba)."""
    pinta_esq = staticmethod(_dulcineia)
    pinta_dir = staticmethod(_gigante_moinho)

    def __init__(self):
        self.t = 0
        self.humor_m, self.humor_d, self.timer = "neutro", "neutro", 0

    def _reage(self, moinho, dama, quadros=120):
        self.humor_m, self.humor_d, self.timer = moinho, dama, quadros

    def acerto(self):
        self._reage("triste", "ri")

    def erro(self):
        self._reage("ri", "triste")

    def dano(self):
        if not self.timer:                             # não atropela a reação a uma resposta
            self._reage("ri", "triste", 60)

    def chefe_vencido(self):
        self._reage("triste", "ri", 240)

    def passo(self, heroi_x=0, largura=0):
        self.t += 1
        if self.timer:
            self.timer -= 1
            if not self.timer:
                self.humor_m = self.humor_d = "neutro"

    def _quadro(self, chave, pinta, tom, nevoa, e):
        ch = ("dupla", type(self).__module__, chave, tom, nevoa, e)
        if ch not in _cache:
            c = pygame.Surface((GW, GH), SRC)
            pinta(c)
            out = contorno(c)
            if tom:
                out.fill(tom, special_flags=pygame.BLEND_RGB_MULT)
            if nevoa:                                  # a mesma névoa de distância dos gigantes
                cor, k = nevoa
                veu = pygame.Surface(out.get_size(), SRC)
                veu.fill(tuple(cor) + (int(255 * k),))
                veu.blit(out, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                out.blit(veu, (0, 0))
            if e != 1:
                out = pygame.transform.scale(out, (int(GW * e), int(GH * e)))
            _cache[ch] = out
        return _cache[ch]

    def draw(self, s, largura, y, tom=None, escala=1, nevoa=None):
        y -= 17 if escala > 1 else 30                  # a base foi medida para o Oni: sobe para o rosto sair dos morros
        escala *= 0.78                                 # bem menores que o Oni: não cobrem o HUD nem a aldeia
        hm, hd = self.humor_m, self.humor_d
        vel = 0.6 if hm == "ri" else 0.05 if hm == "triste" else 0.2       # zombando, as pás disparam
        q = int(self.t * vel) % 6
        fecha = self.t % 170 in (0, 1, 2, 3, 4, 8, 9, 10)
        dm = self._quadro(("m", q, hm), lambda c: self.pinta_dir(c, q, hm), tom, nevoa, escala)
        dd = self._quadro(("d", hd, fecha), lambda c: self.pinta_esq(c, hd, fecha), tom, nevoa, escala)
        pm = int(abs(math.sin(self.t * 0.3)) * 3 * escala) if hm == "ri" else 0
        pd = int(abs(math.sin(self.t * 0.25)) * 4 * escala) if hd == "ri" else int(math.sin(self.t * 0.03) * 1.5)
        s.blit(dd, (int(largura * 0.24 - GW * escala / 2), int(y - GH * escala) - pd))
        s.blit(dm, (int(largura * 0.78 - GW * escala / 2), int(y - GH * escala) - pm))


# --------------------------------------------------------------------- Sancho Pança no burro Ruço (no lugar do pet)
# C/c pelo do burro, b focinho; Y/y chapéu de palha, F/f pele, P bochecha, h barba, R colete, U camisa, p calção

_PAL_SANCHO = {"K": K, "C": (150, 146, 152), "c": (108, 104, 114), "b": (222, 214, 204), "Y": (240, 206, 110),
               "y": (196, 150, 70), "F": (242, 196, 152), "f": (214, 158, 118), "P": (236, 130, 110), "h": (56, 40, 40),
               "R": (176, 58, 50), "r": (124, 36, 40), "U": (236, 228, 204), "u": (196, 186, 170), "p": (92, 70, 60),
               "W": (255, 255, 255), "V": (120, 70, 40), "M": (140, 40, 50)}
_BURRO = [
    ".................K..K...",
    "................KcKKcK..",
    "................KCKKCK..",
    "...............KCCCCCCK.",
    "..............KCCCKCCCK.",
    "..............KCCCCCbbbK",
    ".KK.KKKKKKKKKKKCCCbbbbbK",
    "KcKKCCCCCCCCCCCCCCKKKKK.",
    "KKKCCCCCCCCCCCCCCCK.....",
    ".KcCCCCCCCCCCCCCCcK.....",
    ".KccCCCCCCCCCCCCccK.....",
    "..KKKKKKKKKKKKKKKK......",
]
_PERNAS_B = {"a": ["..KcK.KcK....KcK.KcK....", "..KKK.KKK....KKK.KKK...."],
             "b": ["...KcKcK......KcKcK.....", "...KKKKK......KKKKK....."],
             "c": [".KcK...KcK..KcK...KcK...", ".KKK...KKK..KKK...KKK..."],
             "pulo": [".KcKcK.........KcKcK....", "KKK.KKK.........KKKK...."]}
_CHAPEU_S = ["....KKKKKK....", "...KYYYYYYK...", ".KKyyyyyyyyKK.", "KYYYYYYYYYYYYK"]
_ROSTOS = {
    "parado": [".KKFFFFFFFFKK.", "..KFFKFFFKFFK.", "..KFPPFFFPPFK.", "..KhFFFKKFFhK.", "..KhhhFFFhhhK.", "...KhhhhhhhK.."],
    "fecha": [".KKFFFFFFFFKK.", "..KFKKFFKKFFK.", "..KFPPFFFPPFK.", "..KhFFFKKFFhK.", "..KhhhFFFhhhK.", "...KhhhhhhhK.."],
    "feliz": [".KKFFFFFFFFKK.", "..KFKFKFKFKFK.", "..KFPPFFFPPFK.", "..KhFMMMMFFhK.", "..KhhMMMMhhhK.", "...KhhhhhhhK.."],
    "susto": [".KKFFKFFFKFKK.", "..KFWKFFWKFFK.", "..KFFFFFFFFFK.", "..KhFFKKKFFhK.", "..KhhFKMKFhhK.", "...KhhhhhhhK.."],
    "boceja": [".KKFFFFFFFFKK.", "..KFKKFFKKFFK.", "..KFPPFFFPPFK.", "..KhFMMMMFFhK.", "..KhFMMMMFFhK.", "...KhhMMhhhK.."],
}
_CORPO_S = ["..KRRRhhhRRRK.", ".KRUUURRRUURRK", ".KRUUUUUUUURRK", "KFKuUUUUUUUuKF", "KKKuuuuuuuuuKK", ".KpKKKKKKKKpK."]


def _sancho(pose, quadro):
    rosto = {"feliz": "feliz", "susto": "susto", "boceja": "boceja", "espreguica": "boceja", "lambe": "fecha"}.get(pose)
    if rosto is None:
        rosto = "fecha" if pose == "parado" and quadro % 90 in (84, 85, 88, 89) else "parado"
    linhas = _CHAPEU_S + _ROSTOS[rosto] + _CORPO_S
    alt = 10 + len(_BURRO) + 2                         # o Sancho (16 linhas) afunda até o lombo do burro
    s = pygame.Surface((24, alt), SRC)
    pernas = {"pulo": "pulo", "bote": "pulo"}.get(pose)
    if pernas is None:
        pernas = "abc"[quadro % 3] if pose == "andar" else "a"
    corpo_burro = art.spr(_BURRO + _PERNAS_B[pernas], _PAL_SANCHO)
    s.blit(corpo_burro, (0, alt - corpo_burro.get_height()))
    if pose in ("feliz",) and quadro % 8 < 4:          # chapéu para o alto na alegria
        linhas = ["." * 14] + linhas[:-1]
    dy = 1 if (pose == "andar" and quadro % 3 == 1) else 0
    s.blit(art.spr(linhas, _PAL_SANCHO), (2, dy))
    if pose == "lambe":                                # a bota de vinho na boca (no lugar da lambida)
        s.fill(_PAL_SANCHO["V"], (13, 9 + (quadro // 6) % 2, 5, 3))
        s.fill(K, (15, 8 + (quadro // 6) % 2, 2, 1))
    elif pose == "bote":                               # o punho na frente: agora o Sancho é quem bate
        s.fill(K, (15, 11, 6, 4))
        s.fill(_PAL_SANCHO["F"], (16, 12, 4, 2))
    return s


def sancho(pose="parado", quadro=0, virado=1):
    """Sancho no Ruço (pivô centro-baixo). As poses são as mesmas do pet (pets.Pet.pose)."""
    if pose == "parado":
        quadro %= 180
    elif pose == "andar":
        quadro %= 12
    elif pose in ("feliz", "susto", "lambe", "boceja", "espreguica"):
        quadro %= 24
    else:
        quadro = 0
    ch = ("sancho", pose, quadro, virado < 0)
    if ch not in _cache:
        s = _sancho(pose, quadro)
        _cache[ch] = pygame.transform.flip(s, True, False) if virado < 0 else s
    return _cache[ch]


pet = sancho
