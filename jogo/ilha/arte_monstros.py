"""Pixel art dos monstros (monstros.py), no clima do Hollow Knight: carapaças escuras, máscaras cor de osso e olhos
laranja de infecção que brilham. Tudo desenhado por código (formas + contorno de 1 px pela máscara), em quadros
pré-calculados e guardados em cache; a versão grande é a mesma arte ampliada em pixels inteiros.

Cada função devolve (superfície, [(x, y, raio) dos olhos]) com a criatura virada à direita; os olhos recebem um
brilho somado na hora de desenhar."""
import math

import pygame

K = (14, 10, 22)
CASCA, CASCA2, CASCA_LUZ = (46, 40, 60), (30, 26, 42), (78, 70, 98)
OSSO, OSSO2 = (228, 220, 204), (164, 156, 150)
OLHO, OLHO_MIOLO = (255, 140, 40), (255, 236, 170)
INFEC = (236, 110, 36)
ASA = (150, 170, 210, 150)

_cache = {}


def _contorno(s):
    """Contorno escuro de 1 px em volta de tudo que não é transparente."""
    m = pygame.mask.from_surface(s, 1)
    sil = m.to_surface(setcolor=K, unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((s.get_width() + 2, s.get_height() + 2), pygame.SRCALPHA)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(sil, (dx, dy))
    out.blit(s, (1, 1))
    return out


def _pronto(chave, w, h, fn, contorno=True):
    if chave not in _cache:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        olhos = fn(s) or []
        if contorno:
            s = _contorno(s)
            olhos = [(x + 1, y + 1, r) for x, y, r in olhos]
        _cache[chave] = (s, olhos)
    return _cache[chave]


def versao(chave, s, olhos, virado, escala, branco):
    """Vira, amplia (grandes) e pinta de branco (quadros do golpe) uma arte pronta."""
    ch = ("v", chave, virado, escala, branco)
    if ch not in _cache:
        if len(_cache) > 1500:
            _cache.clear()
        t = s
        if escala != 1:
            t = pygame.transform.scale_by(t, escala)
        if branco:
            t = t.copy()
            t.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        ol = [(x * escala, y * escala, r * escala) for x, y, r in olhos]
        if virado < 0:
            t = pygame.transform.flip(t, True, False)
            ol = [(t.get_width() - x, y, r) for x, y, r in ol]
        _cache[ch] = (t, ol)
    return _cache[ch]


def _elipse(s, cor, r):
    pygame.draw.ellipse(s, cor, pygame.Rect(r))


def _olho(s, x, y, grande=False, aceso=1.0):
    c = tuple(int(v * (0.55 + 0.45 * aceso)) for v in OLHO)
    if grande:
        s.fill(c, (x, y, 2, 2))
        s.set_at((x, y), OLHO_MIOLO)
    else:
        s.set_at((x, y), c)


def _mascara(s, cx, cy, w, h, olhos_x, aceso, chifres=0):
    """Máscara de osso com dois olhos escavados (o rosto dos bichos do Hollow Knight)."""
    _elipse(s, OSSO, (cx - w // 2, cy - h // 2, w, h))
    pygame.draw.line(s, OSSO2, (cx - w // 2 + 1, cy + h // 2 - 1), (cx + w // 2 - 1, cy + h // 2 - 1))
    if chifres:
        pygame.draw.line(s, OSSO, (cx - w // 2 + 1, cy - h // 2 + 1), (cx - w // 2 - 1, cy - h // 2 - chifres), 2)
        pygame.draw.line(s, OSSO, (cx + w // 2 - 1, cy - h // 2 + 1), (cx + w // 2 + 1, cy - h // 2 - chifres), 2)
    out = []
    for ox in olhos_x:
        s.fill(K, (cx + ox, cy - 1, 2, 3))
        _olho(s, cx + ox, cy, True, aceso)
        out.append((cx + ox + 1, cy + 1, 3))
    return out


# --------------------------------------------------------------------- 1. mosca necrófaga (voa e persegue)

def mosca(q, alerta=False):
    def fn(s):
        asa = q % 2
        cor_asa = ASA
        if asa:
            _elipse(s, cor_asa, (2, 0, 9, 6))
            _elipse(s, cor_asa, (8, 1, 7, 5))
        else:
            _elipse(s, cor_asa, (1, 5, 9, 4))
            _elipse(s, cor_asa, (8, 6, 7, 4))
        _elipse(s, CASCA, (3, 4, 13, 11))
        _elipse(s, CASCA_LUZ, (5, 5, 5, 3))
        for i in range(3):
            s.set_at((6 + 3 * i, 15), CASCA2)
            s.set_at((6 + 3 * i, 16 - (q + i) % 2), CASCA2)
        boca = 2 if alerta else 0
        if boca:
            s.fill(INFEC, (13, 10, 3, 2))
        return _mascara(s, 12, 8, 7, 6, (-2, 1), 1.0 if alerta else 0.6)
    return _pronto(("mosca", q % 2, alerta), 18, 18, fn)


# --------------------------------------------------------------------- 2. cuspidor (mantém distância e cospe ácido)

def cuspidor(q, inchado=0.0):
    def fn(s):
        cx, cy = 10, 9
        r = 7 + int(inchado * 2)
        for i in range(4):                                    # perninhas penduradas, balançando
            a = 0.6 + i * 0.5 + math.sin(q * 0.8 + i) * 0.25
            x0 = cx - 4 + i * 3
            pygame.draw.line(s, CASCA2, (x0, cy + 4), (x0 + int(math.cos(a) * 3), cy + 9 + i % 2), 1)
        _elipse(s, CASCA, (cx - r, cy - r + 1, 2 * r, 2 * r - 2))
        for k in range(5):                                    # espinhos nas costas
            a = math.pi * (1.1 + 0.2 * k)
            pygame.draw.line(s, CASCA2, (cx + int(math.cos(a) * (r - 1)), cy + int(math.sin(a) * (r - 1))),
                             (cx + int(math.cos(a) * (r + 3)), cy + int(math.sin(a) * (r + 3))), 2)
        _elipse(s, CASCA_LUZ, (cx - 4, cy - r + 3, 5, 3))
        if inchado > 0.3:
            pygame.draw.circle(s, INFEC, (cx + r - 2, cy + 2), 2 + int(inchado * 2))
            s.set_at((cx + r - 2, cy + 2), OLHO_MIOLO)
        out = []
        for ox in (1, 4):
            s.fill(K, (cx + ox, cy - 3, 2, 2))
            _olho(s, cx + ox, cy - 3, True, 0.6 + inchado * 0.4)
            out.append((cx + ox + 1, cy - 2, 3))
        return out
    return _pronto(("cusp", q % 6, round(inchado, 1)), 24, 22, fn)


# --------------------------------------------------------------------- 3. necrosado chifrudo (avança de cabeça)

def chifrudo(q, pose="anda"):
    def fn(s):
        abaixa = 4 if pose in ("mira", "corre") else 0
        passo = q % 4
        # pernas
        for i, lado in enumerate((-1, 1)):
            off = (passo if i == 0 else (passo + 2) % 4) - 1.5
            if pose == "atordoado":
                off = 0
            x = 9 + lado * 3 + int(off)
            pygame.draw.line(s, CASCA2, (9 + lado * 2, 20), (x, 25), 2)
        # corpo (casca de inseto zumbi)
        _elipse(s, CASCA, (2, 9 + abaixa // 2, 15, 13))
        _elipse(s, CASCA_LUZ, (4, 10 + abaixa // 2, 6, 4))
        pygame.draw.line(s, CASCA2, (3, 16 + abaixa // 2), (15, 16 + abaixa // 2))
        # bracinhos
        pygame.draw.line(s, CASCA2, (13, 15), (17, 17 + (passo % 2)), 1)
        # cabeça com chifre
        hx, hy = 13 + abaixa // 2, 7 + abaixa
        olhos = _mascara(s, hx, hy, 8, 7, (-2, 1), 1.0 if pose in ("mira", "corre") else 0.55, chifres=3)
        pygame.draw.polygon(s, OSSO, [(hx + 3, hy - 2), (hx + 9, hy - 3 + abaixa // 2), (hx + 3, hy + 1)])
        if pose == "atordoado":
            for k in range(3):
                s.set_at((hx - 2 + k * 3, hy - 6 - (q + k) % 2), (255, 236, 120))
        return olhos
    return _pronto(("chifrudo", q % 4, pose), 26, 28, fn)


# --------------------------------------------------------------------- 4. louva-a-deus febril (salta e corta)

def louva(q, pose="guarda"):
    def fn(s):
        agach = 4 if pose == "mira" else 0
        no_ar = pose == "salto"
        # pernas finas
        if no_ar:
            pygame.draw.line(s, CASCA2, (8, 19), (4, 24), 1)
            pygame.draw.line(s, CASCA2, (10, 19), (13, 25), 1)
        else:
            pygame.draw.line(s, CASCA2, (7, 18 + agach // 2), (4, 26), 1)
            pygame.draw.line(s, CASCA2, (11, 18 + agach // 2), (14, 26), 1)
        # tórax esguio
        _elipse(s, CASCA, (5, 9 + agach, 9, 12))
        pygame.draw.line(s, CASCA_LUZ, (7, 11 + agach), (7, 17 + agach))
        # foices
        lam = (240, 240, 250)
        if pose == "corte":
            pygame.draw.arc(s, lam, (10, 2 + agach, 14, 16), -1.2, 1.2, 2)
            pygame.draw.line(s, OSSO, (12, 12 + agach), (20, 6 + agach), 2)
        else:
            sobe = 1 if q % 2 else 0
            pygame.draw.line(s, CASCA2, (12, 12 + agach), (16, 8 + agach - sobe), 2)
            pygame.draw.line(s, OSSO, (16, 8 + agach - sobe), (15, 14 + agach - sobe), 2)
        # cabeça triangular com olhos
        hx, hy = 10, 6 + agach
        pygame.draw.polygon(s, OSSO, [(hx - 4, hy - 3), (hx + 5, hy - 3), (hx + 1, hy + 4)])
        pygame.draw.line(s, OSSO, (hx - 3, hy - 3), (hx - 6, hy - 8), 1)
        pygame.draw.line(s, OSSO, (hx + 4, hy - 3), (hx + 6, hy - 8), 1)
        out = []
        for ox in (-2, 2):
            s.fill(K, (hx + ox, hy - 2, 2, 2))
            _olho(s, hx + ox, hy - 2, True, 1.0 if pose in ("mira", "corte") else 0.6)
            out.append((hx + ox + 1, hy - 1, 3))
        return out
    return _pronto(("louva", q % 2, pose), 26, 28, fn)


# --------------------------------------------------------------------- 5. colosso necrosado (grande, maça e onda)

def colosso(q, pose="anda", ergue=0.0):
    def fn(s):
        passo = q % 4
        # pernas grossas
        for i, lado in enumerate((-1, 1)):
            off = 0 if pose != "anda" else ((passo if i == 0 else (passo + 2) % 4) - 1.5) * 1.5
            pygame.draw.line(s, CASCA2, (20 + lado * 6, 36), (20 + lado * 7 + int(off), 46), 5)
            s.fill(CASCA2, (20 + lado * 7 + int(off) - 3, 45, 7, 3))
        # corpo blindado
        _elipse(s, CASCA, (5, 12, 32, 30))
        _elipse(s, CASCA_LUZ, (9, 15, 12, 7))
        for y in (24, 30):
            pygame.draw.arc(s, CASCA2, (6, y - 8, 30, 14), 3.6, 5.8, 1)
        # infecção escorrendo pelas frestas
        for k, (x, y) in enumerate(((12, 28), (27, 33), (19, 36))):
            pygame.draw.circle(s, INFEC, (x, y), 2)
            s.set_at((x, y + 3 + (q + k) % 3), INFEC)
        # braço com a maça (ergue de 0 a 1)
        a = math.radians(-20 - 150 * ergue) if pose in ("ergue", "golpe") else math.radians(20)
        if pose == "golpe":
            a = math.radians(60)
        ox, oy = 30, 22
        mx, my = ox + int(math.cos(a) * 14), oy + int(math.sin(a) * 14)
        pygame.draw.line(s, CASCA2, (ox, oy), (mx, my), 4)
        pygame.draw.circle(s, OSSO2, (mx, my), 6)
        pygame.draw.circle(s, OSSO, (mx - 1, my - 1), 4)
        for k in range(6):
            b = k * math.pi / 3
            s.set_at((mx + int(math.cos(b) * 7), my + int(math.sin(b) * 7)), OSSO2)
        # elmo
        olhos = _mascara(s, 22, 9, 15, 13, (-4, 2), 1.0 if pose in ("ergue", "golpe") else 0.7, chifres=5)
        pygame.draw.line(s, OSSO2, (22, 3), (22, 15))
        return [(x, y, 5) for x, y, _ in olhos]
    return _pronto(("colosso", q % 4, pose, round(ergue, 1)), 52, 50, fn)


# --------------------------------------------------------------------- 6. glóbulo quicante (ricocheteia no ar)

def globulo(q):
    def fn(s):
        p = 1 if q % 4 < 2 else 0
        _elipse(s, (120, 40, 50), (2 - p, 2 + p, 13 + 2 * p, 13 - 2 * p))
        _elipse(s, (170, 60, 64), (4, 4, 6, 4))
        for k in range(4):
            a = q * 0.4 + k * math.pi / 2
            s.set_at((8 + int(math.cos(a) * 6), 8 + int(math.sin(a) * 6)), INFEC)
        s.fill(K, (8, 6, 3, 3))
        _olho(s, 9, 7, True, 1.0)
        return [(10, 8, 3)]
    return _pronto(("globulo", q % 8), 17, 17, fn)


# --------------------------------------------------------------------- 7. tatuzinho blindado (vira bola e rola)

def tatu(q, bola=False):
    def fn(s):
        if bola:
            a = q * 0.6
            pygame.draw.circle(s, CASCA, (9, 9), 8)
            for k in range(3):
                b = a + k * 2.1
                pygame.draw.line(s, CASCA_LUZ, (9, 9), (9 + int(math.cos(b) * 7), 9 + int(math.sin(b) * 7)), 1)
            pygame.draw.circle(s, CASCA2, (9, 9), 8, 1)
            return []
        passo = q % 2
        for i in range(3):
            s.set_at((5 + 4 * i + passo, 15), CASCA2)
            s.set_at((5 + 4 * i + passo, 16), CASCA2)
        _elipse(s, CASCA, (1, 5, 18, 11))
        for x in (6, 10, 14):
            pygame.draw.line(s, CASCA_LUZ, (x, 6), (x - 1, 14))
        s.fill(OSSO, (16, 9, 4, 4))
        s.fill(K, (17, 10, 2, 2))
        _olho(s, 18, 10, False, 0.8)
        return [(18, 11, 2)]
    return _pronto(("tatu", q % 6, bola), 21, 18, fn)


# --------------------------------------------------------------------- 8. musgo espreitador (finge ser moita)

def musgo(q, acordado=0.0):
    def fn(s):
        sobe = int(acordado * 7)
        verde, verde2 = (70, 120, 70), (44, 84, 54)
        for k in range(7):                                    # folhas
            x = 2 + k * 3
            pygame.draw.polygon(s, verde if k % 2 else verde2,
                                [(x, 16), (x + 2, 6 - sobe + (k % 3) * 2 + (q + k) % 2 * int(acordado)), (x + 4, 16)])
        if acordado > 0.2:
            _elipse(s, CASCA, (6, 10 - sobe, 12, 10))
            for k in range(5):                                # espinhos
                pygame.draw.line(s, OSSO, (7 + k * 2, 11 - sobe), (6 + k * 2 + k % 2 * 2, 6 - sobe), 1)
            s.fill(K, (13, 13 - sobe, 2, 2))
            _olho(s, 13, 13 - sobe, True, acordado)
            s.fill(K, (9, 13 - sobe, 2, 2))
            _olho(s, 9, 13 - sobe, True, acordado)
            return [(14, 14 - sobe, 3), (10, 14 - sobe, 3)]
        s.set_at((12, 11), (90, 60, 50))                      # um piscar escondido entre as folhas
        return []
    return _pronto(("musgo", q % 2, round(acordado, 1)), 24, 24, fn)


# --------------------------------------------------------------------- 9. feiticeiro da febre (teleporta e conjura)

def feiticeiro(q, conjura=False):
    def fn(s):
        bob = int(math.sin(q * 0.7) * 1)
        manto = (54, 34, 74)
        pygame.draw.polygon(s, manto, [(10, 6 + bob), (2, 26), (18, 26)])
        for k in range(4):                                    # barra do manto esfarrapada
            s.fill((0, 0, 0, 0), (3 + k * 4 + q % 2, 25, 2, 2))
        pygame.draw.line(s, (90, 60, 120), (10, 8 + bob), (6, 24))
        olhos = _mascara(s, 10, 6 + bob, 9, 9, (-3, 1), 1.0 if conjura else 0.7, chifres=2)
        if conjura:
            pygame.draw.circle(s, (255, 170, 80), (17, 14 + bob), 3)
            s.set_at((17, 14 + bob), OLHO_MIOLO)
        return olhos
    return _pronto(("feit", q % 9, conjura), 22, 28, fn)


# --------------------------------------------------------------------- 10. água-viva tóxica (flutua; explode)

def aguaviva(q, prestes=0.0):
    def fn(s):
        cor = tuple(int(a + (b - a) * prestes) for a, b in zip((150, 120, 210), (255, 120, 60)))
        pul = 1 if q % 6 < 3 else 0
        _elipse(s, cor + (190,), (2, 1 + pul, 16, 11 - pul))
        _elipse(s, (230, 220, 255, 200), (5, 3 + pul, 5, 3))
        for k in range(5):
            x = 4 + k * 3
            for y in range(12, 22):
                xx = x + int(math.sin(y * 0.6 + q * 0.5 + k) * 1.4)
                s.set_at((xx, y), cor + (150,))
        pygame.draw.circle(s, (255, 200, 120), (10, 7), 2)
        return [(10, 7, 4)]
    return _pronto(("agua", q % 12, round(prestes, 1)), 20, 23, fn, contorno=False)


# --------------------------------------------------------------------- projéteis

def cuspe(q):
    def fn(s):
        pygame.draw.circle(s, INFEC, (4, 4), 3)
        s.set_at((3, 3), OLHO_MIOLO)
        s.set_at((4 - (q % 2), 7), INFEC)
        return [(5, 5, 3)]
    return _pronto(("cuspe", q % 2), 9, 9, fn)


def orbe(q):
    def fn(s):
        r = 4 + q % 2
        pygame.draw.circle(s, (255, 150, 60), (6, 6), r)
        pygame.draw.circle(s, OLHO_MIOLO, (6, 6), 2)
        return [(7, 7, 6)]
    return _pronto(("orbe", q % 2), 13, 13, fn, contorno=False)
