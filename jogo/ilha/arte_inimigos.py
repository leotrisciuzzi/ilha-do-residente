"""Pixel art dos inimigos novos (estilo 16 bits, contorno escuro, sombreado). Tudo original.

Os redondos (estafilococo, estreptococo, ameba, comprimido) são esferas sombreadas desenhadas por código
(luz de cima à esquerda, brilho, contorno); os outros, pixel a pixel em ASCII. Comportamento em inimigos.py."""
import math

import pygame

from .art import K, PAL, mix, spr

_cache = {}


def _flip(s, virado):
    return pygame.transform.flip(s, True, False) if virado < 0 else s


def _tons(base):
    return {1: mix(base, (255, 255, 255), 0.55), 2: base, 3: mix(base, K, 0.35), 4: mix(base, K, 0.6)}


def bolhas(w, h, bolas, brilho=True):
    """bolas: [(x, y, r, cor_base)], de trás para a frente. Cada pixel pertence à bola mais da frente;
    contorno onde o vizinho é vazio ou é outra bola mais de trás (separa os cocos)."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    dono = {}
    for py in range(h):
        for px in range(w):
            for i in range(len(bolas) - 1, -1, -1):
                bx, by, r, _ = bolas[i]
                if (px + 0.5 - bx) ** 2 + (py + 0.5 - by) ** 2 <= r * r:
                    dono[(px, py)] = i
                    break
    for (px, py), i in dono.items():
        bx, by, r, cor = bolas[i]
        viz = [dono.get((px + a, py + b)) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if None in viz or any(v is not None and v < i and
                              (px + 0.5 - bx) ** 2 + (py + 0.5 - by) ** 2 > (r - 1.2) ** 2 for v in viz):
            s.set_at((px, py), K)
            continue
        d = ((px + 0.5 - bx) * 0.55 + (py + 0.5 - by)) / r
        t = _tons(cor)
        s.set_at((px, py), t[1] if d < -0.5 else t[3] if d > 0.42 else t[2])
    if brilho:
        for bx, by, r, cor in bolas:
            if r >= 2.6:
                p = (int(bx - r * 0.42), int(by - r * 0.5))
                if dono.get(p) is not None and bolas[dono[p]][:2] == (bx, by):
                    s.set_at(p, (255, 255, 255))
    return s


def _pinta(s, rows, x, y, pal=None):
    p = dict(PAL)
    if pal:
        p.update(pal)
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in p and ch != ".":
                xx, yy = x + dx, y + dy
                if 0 <= xx < s.get_width() and 0 <= yy < s.get_height():
                    s.set_at((xx, yy), p[ch])


OLHOS = ["KK.KK", "EK.EK", "EK.EK"]          # dois olhos olhando para a frente (direita)
OLHOS_BRAVO = ["K...K", ".K.K.", "EK.EK", "EK.EK"]
PES = [["KooK..KooK", "KKKK..KKKK"], [".KooK.KooK", ".KKKK.KKKK"]]


# ------------------------------------------------------------------ 1. estafilococo (cacho dourado)
def estafilococo(frame, virado=1):
    chave = ("estafilo", frame % 2, virado)
    if chave not in _cache:
        ouro, ouro2 = (250, 200, 60), (236, 176, 44)
        s = bolhas(18, 17, [(5.0, 5.5, 3.6, ouro2), (11.5, 4.5, 3.9, ouro2), (14.0, 9.5, 3.4, ouro),
                            (3.8, 10.5, 3.2, ouro), (9.0, 10.0, 4.6, ouro)])
        _pinta(s, OLHOS, 8, 7)
        _pinta(s, ["KK"], 9, 12)
        _pinta(s, PES[frame % 2], 4, 15)
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 2. estreptococo (corrente de cocos)
def estreptococo(frame, virado=1, bravo=False):
    chave = ("estrepto", frame % 4, virado, bravo)
    if chave not in _cache:
        base = (230, 70, 70) if bravo else (120, 200, 120)
        segs = []
        for i in range(5):                        # cauda à esquerda, cabeça à direita
            y = 7.5 + 1.4 * math.sin(frame * math.pi / 2 + i * 1.1)
            r = 4.6 if i == 4 else 3.4
            segs.append((4.0 + i * 6.6, y, r, base if i == 4 else mix(base, (255, 255, 255), 0.12 * (i % 2))))
        s = bolhas(38, 15, segs)
        hx, hy = segs[-1][0], segs[-1][1]
        _pinta(s, OLHOS_BRAVO if bravo else OLHOS, int(hx) - 1, int(hy) - (4 if bravo else 3))
        _pinta(s, ["KRRK"] if bravo else ["KK"], int(hx) - (1 if bravo else 0), int(hy) + 2)
        for i in range(4):                        # perninhas
            x = int(segs[i][0])
            _pinta(s, ["K.K"] if (frame + i) % 2 else [".K."], x - 1, int(segs[i][1]) + 3)
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 3. bacteriófago
FAGO = """
.....KKKK.....
....KCCCCK....
...KCNCCCcK...
..KCNEKCEKcK..
..KCCEKCEKcK..
..KCCCCCCCcK..
...KcCCCCcK...
....KccccK....
.....KKKK.....
.....KwwK.....
....KKKKKK....
.....KddK.....
.....KwwK.....
.....KddK.....
....KKKKKK....
""".split()
FAGO_PERNAS = [["...KK.KK.KK...", "..K..K..K..K..", ".K...K..K...K.", "K....K..K....K"],
               ["..K..K..K..K..", ".K...K..K...K.", ".K...K..K...K.", ".KK..KK.KK..KK"]]
_FAGO_PAL = {"C": (170, 220, 250), "c": (96, 150, 210), "N": (230, 248, 255)}


def fago(frame, virado=1, agachado=False):
    chave = ("fago", agachado, virado)
    if chave not in _cache:
        s = pygame.Surface((14, 19), pygame.SRCALPHA)
        corpo = FAGO if not agachado else FAGO[:11] + FAGO[13:]
        _pinta(s, corpo, 0, 0, _FAGO_PAL)
        _pinta(s, FAGO_PERNAS[1 if agachado else 0], 0, len(corpo))
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 4. ameba
def ameba(frame, virado=1, pequena=False):
    chave = ("ameba", frame % 4, virado, pequena)
    if chave not in _cache:
        k = 0.62 if pequena else 1.0
        verde = (150, 220, 160)
        a = frame * math.pi / 2
        bolas = [(4 + 2 * math.sin(a), 8.5, 3.4, verde), (13 + 1.5 * math.cos(a), 8.0, 3.6, verde),
                 (9, 6.5 + 0.6 * math.sin(a), 5.2, verde), (2.5 + 1.2 * math.cos(a), 10.0, 2.2, verde),
                 (15.5 - 1.2 * math.sin(a), 10.2, 2.2, verde)]
        w, h = 19, 13
        if pequena:
            bolas = [(x * k + 0.5, y * k, r * k + 0.25, c) for x, y, r, c in bolas]
            w, h = 13, 9
        s = bolhas(w, h, bolas)
        cx, cy = (6, 4) if pequena else (8, 5)
        if not pequena:
            _pinta(s, ["..vv", ".vVV", "..vv"], cx - 6, cy + 1, {"v": (90, 150, 110), "V": (60, 110, 80)})
        _pinta(s, ["EK.EK"] if pequena else OLHOS, cx, cy - (0 if pequena else 1))
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 5. caixa de perfurocortantes + seringa
CAIXA = """
..KKKKKKKKKK..
.KRRRRRRRRRRK.
KKKKKKKKKKKKKK
KyKDDDDDDDDKyK
KYKDEKDDEKDKYK
KYKDEKDDEKDKYK
KYKKKKKKKKKKYK
KYYYYYYYYYYYYK
KYYYYYKKYYYYYK
KYYYYKKKKYYYYK
KYYYKKYYKKYYYK
KYYYKKYYKKYYYK
KYYKKKKKKKKYYK
KyYKKKYYKKKYyK
KyKKKKKKKKKKyK
.KKKKKKKKKKKK.
""".split()
SERINGA = """
K..KKKKKKKKKK....
KKKKCCCCRRRRKKKK.
KwwKCCCCRRRRKwwwK
KKKKCCCCRRRRKKKK.
K..KKKKKKKKKK....
""".split()


def caixa(frame, virado=1):
    chave = ("caixa", frame % 2)
    if chave not in _cache:
        rows = list(CAIXA)
        if frame % 2:                              # pisca
            rows[4] = rows[5] = "KYKDDDDDDDDKYK"
            rows[5] = "KYKDKKDDKKDKYK"
        _cache[chave] = spr(rows)
    return _cache[chave]


def seringa(virado=1):
    chave = ("seringa", virado)
    if chave not in _cache:
        s = spr(SERINGA, {"C": (210, 236, 255), "R": (236, 70, 80), "w": (200, 208, 222)})
        agulha = pygame.Surface((22, 5), pygame.SRCALPHA)
        agulha.blit(s, (0, 0))
        agulha.fill((150, 156, 178), (17, 2, 5, 1))
        _cache[chave] = _flip(agulha, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 6. comprimido (cápsula que rola)
def comprimido(frame, virado=1):
    chave = ("comp", frame % 4, virado)
    if chave not in _cache:
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        base = pygame.Surface((16, 9), pygame.SRCALPHA)
        rows = ["..KKKKKKKKKKKK..",
                ".KWWWWWKRRRRRRK.",
                "KWEWWWWKRlRRRRrK",
                "KWWWEKWKRRRRRRrK",
                "KWWWEKWKRRRRRRrK",
                "KWWWWWWKRRRRRRrK",
                "KwWWWWWKrRRRRrrK",
                ".KwwwwwKrrrrrrK.",
                "..KKKKKKKKKKKK.."]
        _pinta(base, rows, 0, 0, {"l": (255, 190, 190), "w": (200, 200, 214)})
        ang = [0, -30, -60, -90][frame % 4] if frame % 8 < 4 else [180, 150, 120, 90][frame % 4]
        rot = pygame.transform.rotate(base, ang)
        s.blit(rot, rot.get_rect(center=(8, 8)))
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 7. cândida (fungo que sai do chão)
CANDIDA = """
....KKK..KKK....
...KQQQKKQQQK...
..KQWQQQQWQQQK..
..KQQKKKKKKQqK..
.KQQKRRRRRRKqqK.
.KQQKEKEKEKKqqK.
.KQQKKKKKKKKqqK.
..KQQKEKEKEKqK..
..KQQKRRRRRKqK..
...KQQKKKKKqK...
....KKQQQqKK....
......KGGK......
......KgGK......
.....KGgGK......
.....KGGgK......
......KgGK......
......KGgK......
......KGGK......
""".split()
CANDIDA_FECHADA = CANDIDA[:3] + ["..KQQQQQQQQQqK..", ".KQQQKKKKKQQqqK.", ".KQQQKEKEKKQqqK.",
                                 ".KQQQKKKKKKQqqK.", "..KQQQQQQQQQqK..", "..KQQQQQQQQqqK.."] + CANDIDA[9:]
_CAND_PAL = {"Q": (252, 236, 210), "q": (214, 180, 150), "W": (255, 255, 255)}


def candida(frame):
    chave = ("candida", frame % 2)
    if chave not in _cache:
        _cache[chave] = spr(CANDIDA if frame % 2 else CANDIDA_FECHADA, _CAND_PAL)
    return _cache[chave]


def esporo(frame):
    chave = ("esporo", frame % 2)
    if chave not in _cache:
        s = bolhas(7, 7, [(3.5, 3.5, 3.0, (240, 200, 240) if frame % 2 else (220, 170, 230))])
        _cache[chave] = s
    return _cache[chave]


# ------------------------------------------------------------------ 8. carrapato
CARRAPATO = """
.....K..K.....
......KKKK....
.K...KtTTtK...K
..K.KTTTTTTK.K.
...KTuTTTTTtK..
KKKTuuTTTTTttKKK
...KTTTEKTEKtK..
KKKTTTTTTTTttKKK
...KtTTTTTTtK...
..K.KttTTttK.K..
.K...KKttKK...K.
......KKKK......
""".split()


def carrapato(frame):
    chave = ("carrapato", frame % 2)
    if chave not in _cache:
        rows = list(CARRAPATO)
        if frame % 2:
            rows[2], rows[10] = "..K..KtTTtK..K.", "..K..KKttKK..K.."
        _cache[chave] = spr(rows, {"T": (150, 92, 60), "t": (100, 56, 36), "u": (196, 140, 96)})
    return _cache[chave]


# ------------------------------------------------------------------ 9. morcego da raiva
MORCEGO_ASA = """
K..................K
KK......K..K......KK
KDK.....KKKK.....KDK
KDDK...KDDDDK...KDDK
KDDDKKKDRDDRDKKKDDDK
KDdDDDDDDDDDDDDDdDDK
.KdKdDDDWKKWDDDdKdK.
..K.KdKDDWWDDKdK.K..
.....K.KDDDDK.K.....
........KKKK........
""".split()
MORCEGO_CIMA = """
...K..........K...
..KDK...KK...KDK..
.KDdDK.KDDK.KDdDK.
.KDddDKDRRDKDddDK.
..KDddDDDDDDddDK..
...KKdDDWWDDdKK...
.....KdDDDDdK.....
......KKDDKK......
........KK........
""".split()
MORCEGO_DORME = """
...K..K...
...KKKK...
..KDDDDK..
.KdDDDDdK.
.KddDDddK.
.KdDKKDdK.
.KdDDDDdK.
..KdDDdK..
...KDDK...
....KK....
""".split()
_MORC_PAL = {"D": (110, 96, 140), "d": (70, 58, 96), "R": (255, 80, 80), "W": (255, 255, 255)}


def morcego(frame, virado=1, dormindo=False):
    chave = ("morcego", frame % 2, virado, dormindo)
    if chave not in _cache:
        rows = MORCEGO_DORME if dormindo else (MORCEGO_ASA if frame % 2 == 0 else MORCEGO_CIMA)
        s = spr(rows, _MORC_PAL)
        if dormindo:
            s = pygame.transform.flip(s, False, True)  # de cabeça para baixo
        _cache[chave] = _flip(s, virado)
    return _cache[chave]


# ------------------------------------------------------------------ 10. lombriga + montinho de terra
LOMBRIGA = [
    """
.........KKKK...
........KPPPPK..
.......KPEKPEKK.
.......KPEKPEKPK
..KKK..KPPPPPPPK
.KPpPK..KpPRRPK.
KPpKpPK.KpPPpK..
KpK.KpPKpPpPK...
.K...KpPpPpK....
......KKKKK.....
""".split(),
    """
.........KKKK...
........KPPPPK..
.......KPEKPEKK.
.......KPEKPEKPK
.......KPPPPPPPK
..KKKKKKpPRRPK..
.KPpPpPpPPPpK...
KPpKKKKKKKKK....
KpK.............
.K..............
""".split()]
MONTINHO = """
.....KKKKKK.....
...KKuTuTTuKK...
..KTuTTKTTKTTK..
.KTTTTEKTTEKTTK.
KTtTTTTTTTTTTtTK
KttttttttttttttK
""".split()
MONTINHO_VAZIO = """
.....KKKKKK.....
...KKuTuTTuKK...
..KTuKKKKKKTTK..
.KTTKDDDDDDKTTK.
KTtTTKKKKKKTTtTK
KttttttttttttttK
""".split()
_LOMB_PAL = {"P": (250, 168, 180), "p": (210, 110, 130), "R": (190, 50, 80)}


def lombriga(frame, virado=1):
    chave = ("lombriga", frame % 2, virado)
    if chave not in _cache:
        _cache[chave] = _flip(spr(LOMBRIGA[frame % 2], _LOMB_PAL), virado)
    return _cache[chave]


def montinho(vazio=False, tremendo=0):
    chave = ("montinho", vazio, tremendo % 2)
    if chave not in _cache:
        s = pygame.Surface((18, 6), pygame.SRCALPHA)
        s.blit(spr(MONTINHO_VAZIO if vazio else MONTINHO), (1 + (tremendo % 2), 0))
        _cache[chave] = s
    return _cache[chave]
