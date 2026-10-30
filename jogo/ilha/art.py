"""Pixel art estilo 16-bit (SNES/GBC): sprites desenhados pixel a pixel em
ASCII, paleta limitada, contorno escuro e sombreado. Tudo original.

O mundo é desenhado em 320x180 e ampliado 4x sem suavização."""
import colorsys
import math
import random

import pygame

from . import heroi as _heroi

TILE = 16
K = (28, 20, 36)          # contorno
_cache = {}


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ sprites ASCII

PAL = {
    "K": K,
    # verdes (bichos, flores) e itens
    "G": (96, 200, 72), "g": (40, 128, 56), "L": (184, 240, 120),
    "W": (248, 248, 232), "w": (176, 176, 184),
    "R": (232, 64, 72), "r": (144, 32, 56),
    "O": (248, 144, 40), "o": (184, 80, 24), "q": (120, 48, 24),
    "E": (255, 255, 255),
    # bebê
    "B": (72, 152, 248), "b": (40, 80, 184), "S": (252, 208, 168), "s": (216, 144, 112),
    "+": (248, 120, 152),
    # itens
    "Y": (255, 216, 48), "y": (208, 136, 16), "l": (255, 248, 168),
    "V": (152, 96, 216), "v": (96, 56, 152), "N": (200, 160, 248),
    "P": (248, 152, 184), "p": (200, 88, 128), "Q": (255, 208, 224),
    "D": (64, 64, 80), "d": (120, 120, 140),
    "C": (160, 216, 255), "c": (88, 152, 216),
    "T": (176, 112, 64), "t": (120, 72, 40), "u": (216, 160, 104),
}


def spr(rows, pal=None, extra=None):
    """Converte linhas ASCII em Surface ('.' = transparente)."""
    p = dict(PAL)
    if pal:
        p.update(pal)
    if extra:
        p.update(extra)
    w = max(len(r) for r in rows)
    s = pygame.Surface((w, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != "." and ch != " " and ch in p:
                s.set_at((x, y), p[ch])
    return s


def heroi(estado, frame, bebe=True, virado=1):
    """O Doutor montado no pônei branco (ver heroi.py)."""
    return _heroi.heroi(estado, frame, bebe, virado)


def cabeca_icone():
    return _heroi.cabeca()


def bebe_bolha(t):
    s = pygame.Surface((26, 26), pygame.SRCALPHA)
    pygame.draw.circle(s, (200, 232, 255, 70), (13, 13), 12)
    s.blit(_heroi.bebe_choro(), (5, 3 + (t // 20) % 2))
    pygame.draw.circle(s, (255, 255, 255, 230), (13, 13), 12, 1)
    for p in ((7, 6), (8, 6), (7, 7)):
        s.set_at(p, (255, 255, 255))
    return s


BACILO = """
....KKKKKKKKKKKK....
..KKQQQQPPPPPPPPKK..
.KQQQPPPPPPPPPKKPPK.
.KQPPPpPPPPPPKEEKPpK
KQPPPppPPPpPPKEKKPpK
KPPPPPPPPPppPKEKKPpK
KPPpPPPPPPPPPPKKPPpK
.KppPPPPPPPPPPPPPppK
.KjppppppppppppppjK.
..KKKKKKKKKKKKKKKK..
""".split()
_PILI = [{1: "K...", 2: ".KK.", 3: "...K"}, {1: "...K", 2: ".KK.", 3: "K..."}]
_BAC_PAL = {"Q": (255, 214, 226), "P": (244, 150, 180), "p": (204, 96, 140), "j": (140, 52, 96)}
_BAC_BRAVO = {"Q": (255, 176, 168), "P": (236, 84, 84), "p": (176, 40, 56), "j": (112, 20, 40)}


def bacilo(frame, cor=None, bravo=False, virado=1, questao=False):
    """Bacilo (bastonete) com pili/flagelo que ondula; 22x10."""
    chave = ("bac", frame % 2, bravo, virado)
    if chave not in _cache:
        linhas = ["  " + l for l in BACILO]
        for y, cauda in _PILI[frame % 2].items():     # flagelo na traseira
            y += 3
            linhas[y] = "".join(c if c != "." else linhas[y][i] for i, c in enumerate(cauda)) + linhas[y][4:]
        s = spr(linhas, _BAC_BRAVO if bravo else _BAC_PAL)
        _cache[chave] = pygame.transform.flip(s, True, False) if virado < 0 else s
    return _cache[chave]


AEDES = """
.......KKK.KKK.....
......KCCCKCCCK....
......KCcCKCcCK....
.......KCCKCCK.....
........KKKKKKKK...
...KKK.KDWDdDKEEK..
..KWDWKKdWdDKEEKKKK
.KDWDWDKDDDDKKKK...
KWDWDKKKKKKKK......
KDWDK..K.K.K.......
.KKK..W..W..W......
.....K..K...K......
....W...W....W.....
...K....K.....K....
""".split()
AEDES2 = ["", "", "", "",
          "........KKKKKKKK...",
          "...KKK.KDWDdDKEEK..",
          "..KWDWKKdWdDKEEKKKK",
          ".KDWDWDKDDDDKKKK...",
          "KWDWDKKCCCKCCCK....",
          "KDWDK.KCcCKCcCK....",
          ".KKK...KCCKCCKW....",
          "......K.KKKKK.K....",
          ".....W...W...W.....",
          "....K....K....K...."]
_AEDES_PAL = {"C": (214, 238, 255, 190), "c": (150, 196, 236, 190), "D": (52, 52, 72), "d": (92, 92, 120),
              "W": (240, 240, 250)}


def aedes(frame, virado=1):
    chave = ("aedes", frame % 2, virado)
    if chave not in _cache:
        s = spr(AEDES2 if frame % 2 else AEDES, _AEDES_PAL)
        _cache[chave] = pygame.transform.flip(s, True, False) if virado < 0 else s
    return _cache[chave]


VIRUS = """
.......OO.......
...O...KK...O...
...OK.KKKK.KO...
....KKVVVVKK....
.OK.KNNVVVVvK.KO
.OKKNNVVVVVVvKKO
...KNVVVVVVVvK..
..KVVEEVVVEEVvK.
OOKVVEKVVVEKVvKOO
..KVVVVVVVVVVvK.
..KvVVVKKKVVvjK.
...KvVVVVVVvjK..
.OKKvvVVVVvjKKO.
.OK.KjvvvvjjK.KO
....KKjjjjKK....
...OK.KKKK.KO...
...O...KK...O...
.......OO.......
""".split()
_VIRUS_PAL = {"N": (216, 184, 255), "V": (160, 104, 224), "v": (110, 64, 172), "j": (72, 36, 120),
              "O": (255, 176, 64)}


def virus(frame):
    chave = ("virus", frame % 2)
    if chave not in _cache:
        pal = dict(_VIRUS_PAL)
        if frame % 2:
            pal["O"] = (255, 232, 120)
        _cache[chave] = spr(VIRUS, pal)
    return _cache[chave]


BICHO = [
    "....K....K.....K....",
    "....K...KMK...KMK...",
    "...KMKKKMNMKKKMMK...",
    "..KMNMMMMMMMMMMMMK..",
    ".KMNMMMEEEEEMMMMMMK.",
    ".KMNMMEEEEEEEMMMMMK.",
    "KMNMMMEEEKKEEMMMMMMK",
    "KMMMMMEEEKKEEMMMMMMK",
    "KMMMMMMEEEEEMMMMMMmK",
    "KmMMMMMMMMMMMMMMMmmK",
    "KmMMMKEKEKEKEKMMMmmK",
    ".KmMMMKKKKKKKKMMmmK.",
    ".KmmMMMMMMMMMMMmmK..",
    "..KKmmmmmmmmmmmKK...",
    "...KKOOK...KOOKK....",
    "...KKKKK...KKKKK....",
]
BICHO2 = BICHO[:14] + ["....KOOK...KOOK.....", "....KKKK...KKKK....."]
BICHO_BRAVO_OLHO = ["KMNMMKKKKKKKMMMMMMK"]
PLACA_Q = [
    ".KKKKKKK.",
    "KYYYYYYYK",
    "KYYKKKYYK",
    "KYYYYKKYK",
    "KYYYKKYYK",
    "KYYYYYYYK",
    "KYYYKYYYK",
    ".KKKKKKK.",
    "....K....",
    "....K....",
]
PLACA_R = [
    ".KKKKKKK.",
    "KCCCCCCCK",
    "KCKKKKCCK",
    "KCKCCCKCK",
    "KCKKKKCCK",
    "KCKCCKCCK",
    "KCKCCCKCK",
    ".KKKKKKK.",
    "....K....",
    "....K....",
]


def bicho_questao(frame, cor, bravo=False, virado=1, gigante=False, revisao=False):
    """Bicho-questão (ciclope peludo) segurando a placa da questão."""
    chave = ("bq", frame % 2, tuple(cor), bravo, virado, gigante, revisao)
    if chave in _cache:
        return _cache[chave]
    if bravo:
        cor = (232, 72, 72)
    pal = {"M": cor, "m": mix(cor, K, 0.45), "N": mix(cor, (255, 255, 255), 0.45)}
    linhas = list(BICHO2 if frame % 2 else BICHO)
    if bravo:
        linhas[4] = ".KMNMMKKKKKKKMMMMMK."
    corpo = spr(linhas, pal)
    if virado < 0:
        corpo = pygame.transform.flip(corpo, True, False)
    s = pygame.Surface((22, 26), pygame.SRCALPHA)
    s.blit(corpo, (2, 10))
    placa = spr(PLACA_R if revisao else PLACA_Q)
    s.blit(placa, (0 if virado > 0 else 13, frame % 2))   # placa legível, do lado de trás
    if gigante:
        s = pygame.transform.scale(s, (44, 52))
    _cache[chave] = s
    return s


OVO = """
...KKKK...
..KWWWWK..
.KWEEWWwK.
.KWEWWbwK.
KWWWWWBbwK
KWbBWWWWwK
KWbbWWWWwK
KWWWWWBbwK
KwWWWWbbdK
.KwwWwwdK.
..KKKKKK..
""".split()


def ovo(cor_pinta=None):
    if "ovo" not in _cache:
        _cache["ovo"] = spr(OVO)
    return _cache["ovo"]


MOEDAS = [
    ["..KKKK..", ".KYYYYK.", "KYlYYYyK", "KYlYYYyK", "KYlYYYyK", "KYlYYYyK",
     "KYlYYYyK", "KYlYYYyK", "KYYYYYyK", ".KyyyyK.", "..KKKK.."],
    ["...KKK..", "..KYYYK.", "..KlYyK.", "..KlYyK.", "..KlYyK.", "..KlYyK.",
     "..KlYyK.", "..KlYyK.", "..KYYyK.", "..KyyyK.", "...KKK.."],
    ["...KK...", "...KK...", "...Ky...", "...Ky...", "...Ky...", "...Ky...",
     "...Ky...", "...Ky...", "...Ky...", "...KK...", "...KK..."],
    ["..KKK...", ".KYYYK..", ".KYlYK..", ".KYlYK..", ".KYlYK..", ".KYlYK..",
     ".KYlYK..", ".KYlYK..", ".KYYyK..", ".KyyyK..", "..KKK..."],
]
VERM = {"Y": (240, 64, 80), "y": (160, 24, 56), "l": (255, 176, 184)}


def moeda(frame, vermelha=False):
    chave = ("moeda", frame % 4, vermelha)
    if chave not in _cache:
        _cache[chave] = spr(MOEDAS[frame % 4], VERM if vermelha else None)
    return _cache[chave]


ESTRELA = [
    ".....K.....",
    "....KYK....",
    "....KlK....",
    "KKKKYlYKKKK",
    "KYYYlYYYYyK",
    ".KYYYYYYyK.",
    "..KYYKYYK..",
    "..KYyKyYK..",
    ".KYyK.KyYK.",
    ".KyK...KyK.",
    ".KK.....KK.",
]


def estrela(frame=0, tam=11):
    chave = ("estrela", frame % 2)
    if chave not in _cache:
        s = spr(ESTRELA)
        if frame % 2:
            s = spr(ESTRELA, {"Y": (255, 240, 120), "l": (255, 255, 255)})
        _cache[chave] = s
    return _cache[chave]


FLOR = [
    "...KK..KK...",
    "..KWWKKWWK..",
    "..KWWWWWWK..",
    "KKKWKKKKWKKK",
    "KWWKYYYYKWWK",
    "KWWKYKYKYWWK",
    ".KKKYYYYKKK.",
    "KWWKyYYyKWWK",
    "KWWWKKKKWWWK",
    ".KKWWWWWWKK.",
    "..KWWKKWWK..",
    "...KK..KK...",
]


def flor(tam=12, frame=0):
    chave = ("flor", frame % 2)
    if chave not in _cache:
        s = spr(FLOR)
        _cache[chave] = pygame.transform.rotate(s, 90) if frame % 2 else s
    return _cache[chave]


def anel(t, meio=False):
    s = pygame.Surface((32, 48), pygame.SRCALPHA)
    cores = ((255, 176, 48), (255, 240, 120)) if meio else ((248, 112, 168), (255, 240, 120))
    for i in range(12):
        a = i * math.pi / 6 + t * 0.04
        x, y = int(16 + math.cos(a) * 12), int(24 + math.sin(a) * 20)
        pygame.draw.rect(s, K, (x - 2, y - 2, 5, 5))
        pygame.draw.rect(s, cores[i % 2], (x - 1, y - 1, 3, 3))
        s.set_at((x - 1, y - 1), (255, 255, 255))
    return s


# ------------------------------------------------------------------ fonte bitmap

_GLIFOS = {
    "A": ".###." "#...#" "#...#" "#####" "#...#" "#...#" "#...#", "B": "####.#...##...#####.#...##...#####.",
    "C": ".###.#...##....#....#....#...#.###.", "D": "####.#...##...##...##...##...#####.",
    "E": "######....#....####.#....#....#####", "F": "######....#....####.#....#....#....",
    "G": ".###.#...##....#.####...##...#.####", "H": "#...##...##...#######...##...##...#",
    "I": ".###...#....#....#....#....#...###.", "J": "..###...#....#....#.#..#.#..#..##..",
    "K": "#...##..#.#.#..##...#.#..#..#.#...#", "L": "#....#....#....#....#....#....#####",
    "M": "#...###.###.#.##.#.##...##...##...#", "N": "#...###..##.#.##..###...##...##...#",
    "O": ".###.#...##...##...##...##...#.###.", "P": "####.#...##...#####.#....#....#....",
    "Q": ".###.#...##...##...##.#.##..#..##.#", "R": "####.#...##...#####.#.#..#..#.#...#",
    "S": ".#####....#.....###.....#....#####.", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", "V": "#...##...##...##...##...#.#.#...#..",
    "W": "#...##...##...##.#.##.#.##.#.#.#.#.", "X": "#...##...#.#.#...#...#.#.#...##...#",
    "Y": "#...##...#.#.#...#....#....#....#..", "Z": "#####....#...#...#...#...#....#####",
    "0": ".###.#...##..###.#.###..##...#.###.", "1": "..#...##....#....#....#....#...###.",
    "2": ".###.#...#....#...#...#...#...#####", "3": "####.....#....#.###.....#....#####.",
    "4": "...#...##..#.#.#..#.#####...#....#.", "5": "######....####.....#....##...#.###.",
    "6": ".###.#....#....####.#...##...#.###.", "7": "#####....#...#...#...#....#....#...",
    "8": ".###.#...##...#.###.#...##...#.###.", "9": ".###.#...##...#.####....#....#.###.",
    "!": "..#....#....#....#....#.........#..", "?": ".###.#...#....#...#...#.........#..",
    ".": "................................#..", ",": "...........................#...#...",
    ":": ".......#....................#......", "+": ".......#....#..#####..#....#.......",
    "-": "...............#####...............", "/": "....#...#....#...#....#...#....#...",
    "x": "..........#...#.#.#...#...#.#.#...#", "(": "...#...#...#....#....#.....#.....#.",
    ")": ".#.....#.....#....#....#...#...#...", "'": "..#....#...........................",
    "%": "##..###.#....#...#...#....#.###..##", " ": "." * 35, "*": "..#..#.#.#.###.#.#.#..#............",
    "=": "..........#####.....#####..........", "·": ".................#.................",
    "—": "...............#####...............", "–": "...............#####...............",
    "|": "..#....#....#....#....#....#....#..", ";": ".......#...................#...#...",
    "#": ".#.#.#####.#.#..#.#.#####.#.#......", "_": "..............................#####",
}
_ACENTOS = {"Á": ("A", "´"), "À": ("A", "`"), "Â": ("A", "^"), "Ã": ("A", "~"), "É": ("E", "´"),
            "Ê": ("E", "^"), "Í": ("I", "´"), "Ó": ("O", "´"), "Ô": ("O", "^"), "Õ": ("O", "~"),
            "Ú": ("U", "´"), "Ü": ("U", "¨"), "Ç": ("C", "¸")}
_MARCAS = {"´": [(3, 0), (2, 1)], "`": [(1, 0), (2, 1)], "^": [(2, 0), (1, 1), (3, 1)],
           "~": [(1, 0), (2, 0), (3, 1), (4, 1)][:2] + [(0, 1), (3, 1)], "¨": [(1, 1), (3, 1)],
           "¸": [(2, 9), (1, 10)]}


def _glifo(ch):
    """Glifo 5x7 com 2 linhas livres em cima (acentos) e 2 embaixo (cedilha)."""
    ch = ch.upper()
    base, marca = _ACENTOS.get(ch, (ch, None))
    bits = _GLIFOS.get(base, _GLIFOS[" "])
    pts = [(i % 5, 2 + i // 5) for i, b in enumerate(bits) if b == "#"]
    if marca:
        pts += _MARCAS[marca]
    return pts


def texto_px(txt, cor=(255, 255, 255), contorno=K, escala=1):
    """Renderiza texto na fonte bitmap 5x7 com contorno de 1px."""
    chave = ("txt", txt, cor, contorno, escala)
    if chave in _cache:
        return _cache[chave]
    w = len(txt) * 6 + 2
    s = pygame.Surface((w, 13), pygame.SRCALPHA)
    pts = []
    for i, ch in enumerate(txt):
        pts += [(1 + i * 6 + x, 1 + y) for x, y in _glifo(ch)]
    if contorno:
        for x, y in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    s.set_at((x + dx, y + dy), contorno)
    for x, y in pts:
        s.set_at((x, y), cor)
    if escala != 1:
        s = pygame.transform.scale(s, (w * escala, 13 * escala))
    if len(_cache) > 4000:
        _cache.clear()
    _cache[chave] = s
    return s


# ------------------------------------------------------------------ cenário

# ------------------------------------------------------------------ cenário algodão-doce
# Estética de livro de colorir: tons pastel, textura de giz de cera em riscos
# diagonais, nuvens fofas, morros altos com "cobertura" escorrendo e chão em bolotas.

TEMAS = [
    # nome, topo do chão (cobertura), terra, morros (longe, meio, perto), céu (cima, baixo)
    {"nome": "morango", "cob": (255, 196, 222), "terra": (250, 178, 150),
     "longe": (236, 214, 250), "meio": (255, 176, 206), "perto": (150, 96, 150),
     "ceu": ((150, 200, 250), (255, 214, 232)), "acento": (255, 120, 170)},
    {"nome": "baunilha", "cob": (255, 236, 160), "terra": (248, 168, 104),
     "longe": (206, 236, 250), "meio": (170, 226, 170), "perto": (70, 110, 110),
     "ceu": ((120, 190, 250), (232, 246, 255)), "acento": (250, 190, 70)},
    {"nome": "menta", "cob": (196, 246, 220), "terra": (236, 186, 164),
     "longe": (226, 220, 255), "meio": (150, 222, 210), "perto": (96, 104, 160),
     "ceu": ((170, 214, 255), (220, 255, 240)), "acento": (80, 210, 170)},
    {"nome": "uva", "cob": (226, 206, 255), "terra": (240, 170, 170),
     "longe": (255, 220, 236), "meio": (196, 170, 246), "perto": (110, 84, 140),
     "ceu": ((180, 170, 250), (255, 222, 240)), "acento": (170, 120, 250)},
    {"nome": "pêssego", "cob": (255, 214, 176), "terra": (240, 150, 110),
     "longe": (255, 232, 214), "meio": (255, 190, 150), "perto": (130, 86, 110),
     "ceu": ((140, 206, 246), (255, 230, 200)), "acento": (255, 150, 90)},
    {"nome": "chiclete", "cob": (190, 226, 255), "terra": (246, 176, 196),
     "longe": (226, 246, 255), "meio": (250, 180, 230), "perto": (90, 110, 170),
     "ceu": ((160, 196, 255), (250, 226, 255)), "acento": (90, 170, 255)},
]


def paleta(indice):
    """Uma paleta pastel por ilha/matéria (sabor de algodão-doce)."""
    t = TEMAS[indice % len(TEMAS)]
    cob, terra = t["cob"], t["terra"]
    return {
        "tema": t["nome"],
        "ceu_topo": t["ceu"][0], "ceu_base": t["ceu"][1],
        "morro_longe": t["longe"], "morro_meio": t["meio"], "morro_perto": t["perto"],
        "terra": terra, "terra_esc": mix(terra, (120, 50, 70), 0.35), "terra_clara": mix(terra, (255, 245, 220), 0.45),
        "grama": cob, "grama_esc": mix(cob, (190, 90, 120), 0.35), "grama_clara": mix(cob, (255, 255, 255), 0.6),
        "contorno": mix(terra, (60, 20, 50), 0.7),
        "acento": t["acento"],
    }


def _riscos(s, dentro, cor, n, rng, comp=(3, 6)):
    """Textura de giz de cera: n riscos curtos subindo para a direita (2 px para cima a
    cada 1 para o lado), só onde dentro(x, y) é verdade."""
    w, h = s.get_size()
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        for k in range(rng.randint(*comp)):
            xx, yy = x + k // 2, y - k
            if 0 <= xx < w and 0 <= yy < h and dentro(xx, yy):
                s.set_at((xx, yy), cor)


def ceu(pal, largura, altura):
    """Céu pastel em faixas pontilhadas + riscos horizontais de giz."""
    s = pygame.Surface((largura, altura))
    n = 8
    cores = [mix(pal["ceu_topo"], pal["ceu_base"], (i / (n - 1)) ** 0.8) for i in range(n)]
    banda = altura / n
    for y in range(altura):
        i = min(n - 1, int(y / banda))
        frac = (y - i * banda) / banda
        s.fill(cores[i], (0, y, largura, 1))
        if frac > 0.6 and i + 1 < n:
            for x in range((y % 2), largura, 2):
                s.set_at((x, y), cores[i + 1])
    rng = random.Random(7)
    for _ in range(170):                 # riscos longos quase horizontais
        x, y = rng.randrange(largura), rng.randrange(altura)
        i = min(n - 1, int(y / banda))
        cor = mix(cores[i], (255, 255, 255), 0.22)
        L = rng.randint(6, 16)
        for k in range(L):
            s.set_at(((x + k) % largura, max(0, y - k // 6)), cor)
    return s


def _fofo(mascara, bolas, cor):
    for bx, by, r in bolas:
        pygame.draw.circle(mascara, cor, (int(bx), int(by)), int(r))


def _pintar_fofo(largura, altura, bolas, claro, medio, sombra, borda, rng, riscos=260):
    """Volume fofo (nuvem, algodão): silhueta de bolas, sombra embaixo-direita,
    brilho em cima-esquerda, contorno suave e riscos de giz."""
    m = pygame.Surface((largura, altura), pygame.SRCALPHA)
    _fofo(m, bolas, (255, 255, 255))
    alfa = pygame.mask.from_surface(m)
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    _fofo(s, bolas, sombra)
    _fofo(s, [(bx - r * 0.18, by - r * 0.22, r * 0.86) for bx, by, r in bolas], medio)
    _fofo(s, [(bx - r * 0.35, by - r * 0.4, r * 0.5) for bx, by, r in bolas], claro)
    # aparar o que vazou da silhueta
    for y in range(altura):
        for x in range(largura):
            if not alfa.get_at((x, y)):
                s.set_at((x, y), (0, 0, 0, 0))
    _riscos(s, lambda x, y: alfa.get_at((x, y)), mix(medio, sombra, 0.35), riscos, rng, comp=(2, 4))
    _riscos(s, lambda x, y: alfa.get_at((x, y)), mix(claro, (255, 255, 255), 0.5), riscos // 2, rng, comp=(2, 4))
    for y in range(altura):
        for x in range(largura):
            if alfa.get_at((x, y)) and (x == 0 or y == 0 or x == largura - 1 or y == altura - 1 or
                                       not alfa.get_at((x - 1, y)) or not alfa.get_at((x + 1, y)) or
                                       not alfa.get_at((x, y - 1)) or not alfa.get_at((x, y + 1))):
                s.set_at((x, y), borda)
    return s


def nuvem(s, x, y, escala=1.0, cor=(255, 255, 255)):
    chave = ("nuvem", int(escala * 10))
    if chave not in _cache:
        e = escala
        w, h = int(56 * e), int(30 * e)
        rng = random.Random(int(e * 100))
        bolas = [(12 * e, 20 * e, 9 * e), (24 * e, 13 * e, 12 * e), (37 * e, 15 * e, 10 * e), (46 * e, 21 * e, 7 * e),
                 (28 * e, 21 * e, 9 * e)]
        _cache[chave] = _pintar_fofo(w, h, bolas, (255, 255, 255), (246, 246, 255), (206, 210, 246),
                                     (176, 176, 226), rng, riscos=int(40 * e))
    s.blit(_cache[chave], (int(x), int(y)))


def _morro(cor_corpo, cor_cob, w, h, rng, riscos, borda_k, calda, fase):
    """Um morro alto e arredondado, desenhado sozinho: corpo, sombra curva à direita,
    cobertura de calda escorrendo com brilho, riscos de giz e contorno."""
    H = h * 2 + 40
    m = pygame.Surface((w, H), pygame.SRCALPHA)
    pygame.draw.ellipse(m, (255, 255, 255), (0, 0, w, H))
    alfa = pygame.mask.from_surface(m)
    s = pygame.Surface((w, H), pygame.SRCALPHA)
    corpo_cl = mix(cor_corpo, (255, 255, 255), 0.18)
    corpo_es = mix(cor_corpo, (40, 20, 50), 0.22)
    cob, cob_cl, cob_es = cor_cob, mix(cor_cob, (255, 255, 255), 0.45), mix(cor_cob, (120, 60, 90), 0.25)
    ex, ey, ea, eb = w * 0.38, h * 0.75, w * 0.5, h * 0.85
    prof = int(h * rng.uniform(*calda)) if calda else -1
    for x in range(w):
        gota = int(3 * math.sin((x + fase) * 0.45) + 2 * math.sin((x + fase) * 0.17))
        lim = prof + gota
        for y in range(min(H, h + 40)):
            if not alfa.get_at((x, y)):
                continue
            sombra = ((x - ex) / ea) ** 2 + ((y - ey) / eb) ** 2 > 1
            if calda and y < lim:
                c = cob_es if sombra else cob
                if not sombra and y < prof // 2 and w * 0.15 < x < w * 0.4 and (x + y) % 3 == 0:
                    c = cob_cl
            elif calda and y == lim:
                c = mix(cob_es, cor_corpo, 0.5)
            else:
                c = corpo_es if sombra else cor_corpo
            s.set_at((x, y), c)
    dentro = lambda x, y: alfa.get_at((x, y)) and y < h + 40 and (not calda or y > prof + 3)
    k = 0.35 if sum(cor_corpo) < 450 else 0.6        # em morro escuro o giz fica discreto
    _riscos(s, dentro, mix(cor_corpo, corpo_cl, k), riscos, rng, comp=(2, 4))
    _riscos(s, dentro, mix(cor_corpo, corpo_es, k), riscos, rng, comp=(2, 4))
    borda = mix(cor_corpo, (40, 20, 50), borda_k)
    for y in range(min(H, h + 40)):
        for x in range(w):
            if alfa.get_at((x, y)) and (y == 0 or x == 0 or x == w - 1 or not alfa.get_at((x, y - 1)) or
                                       not alfa.get_at((x - 1, y)) or not alfa.get_at((x + 1, y))):
                s.set_at((x, y), borda)
    return s


def _camada_morros(pal, cor_corpo, cor_cob, largura, altura, rng, morros, riscos=900, borda_k=0.45,
                   escorrer=True, calda=(0.28, 0.4)):
    """Empilha morros (cx, base, w, h) de trás para a frente, repetindo nas bordas para
    a camada emendar na rolagem."""
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    por_morro = max(20, riscos * 60 // (largura * max(1, len(morros))) * 10)
    for cx, base, w, h in morros:
        m = _morro(cor_corpo, cor_cob, w, h, rng, por_morro, borda_k, calda if escorrer else None, cx)
        for dx in (-largura, 0, largura):
            s.blit(m, (cx - w // 2 + dx, base - h))
    return s


def _arvore_algodao(s, x, y, cor, rng, escala=1.0):
    """Árvore de algodão-doce: palito e bola fofa listrada de giz."""
    r = int(rng.randint(6, 9) * escala)
    pau, pau_e = (250, 240, 220), (200, 180, 160)
    s.fill(pau_e, (x - 1, y - r - 1, 3, r + 2))
    s.fill(pau, (x, y - r - 1, 1, r + 2))
    bolas = [(r + 2, r + 3, r), (r // 2 + 2, r + 5, r * 0.7), (r * 1.5 + 2, r + 5, r * 0.7)]
    w, h = int(r * 2 + 6), int(r * 2 + 8)
    bola = _pintar_fofo(w, h, bolas, mix(cor, (255, 255, 255), 0.6), cor, mix(cor, (150, 70, 120), 0.3),
                        mix(cor, (90, 40, 80), 0.5), rng, riscos=r * 6)
    s.blit(bola, (x - w // 2, y - r - h + 3))


def fundo(pal, largura, altura, seed=0):
    """Três camadas: banco de nuvens fofas, morros altos pastel com cobertura, e morros
    próximos mais escuros com árvores de algodão-doce."""
    rng = random.Random(seed)
    camadas = []
    # ---- 0: banco de nuvens + morros bem claros
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    bolas = []
    x = -10
    while x < largura + 20:
        r = rng.randint(14, 26)
        bolas.append((x, altura * 0.52 + rng.randint(-14, 10), r))
        x += rng.randint(14, 26)
    bolas += [(bx, by + 18, r + 6) for bx, by, r in bolas]
    banco = _pintar_fofo(largura, altura, bolas, (255, 255, 255), mix(pal["ceu_base"], (255, 255, 255), 0.55),
                         mix(pal["ceu_topo"], (255, 255, 255), 0.35), mix(pal["ceu_topo"], (90, 90, 160), 0.25), rng, 500)
    s.blit(banco, (0, 0))
    morros = []
    x = rng.randint(-20, 10)
    while x < largura + 30:
        morros.append((x, int(altura * 0.72), rng.randint(40, 64), rng.randint(40, 62)))
        x += rng.randint(34, 56)
    s.blit(_camada_morros(pal, pal["morro_longe"], mix(pal["morro_longe"], (255, 255, 255), 0.5), largura, altura,
                          rng, morros, riscos=500, borda_k=0.25), (0, 0))
    camadas.append(s)
    # ---- 1: morros altos tipo ovo, pastel, com calda
    morros = []
    x = rng.randint(-20, 0)
    while x < largura + 30:
        morros.append((x, int(altura * 0.86), rng.randint(46, 76), rng.randint(62, 96)))
        x += rng.randint(40, 70)
    cob = mix(pal["grama"], (255, 255, 255), 0.25)
    camadas.append(_camada_morros(pal, pal["morro_meio"], cob, largura, altura, rng, morros, riscos=800, borda_k=0.4))
    # ---- 2: morros próximos mais escuros (contraste com o jogo) + árvores de algodão
    s = pygame.Surface((largura, altura), pygame.SRCALPHA)
    morros = []
    x = rng.randint(-20, 0)
    while x < largura + 30:
        morros.append((x, int(altura * 0.98), rng.randint(70, 110), rng.randint(46, 70)))
        x += rng.randint(56, 90)
    perto = _camada_morros(pal, pal["morro_perto"], pal["grama"], largura, altura, rng, morros, riscos=1400, borda_k=0.5,
                           calda=(0.16, 0.24))
    topo = []
    for xx in range(largura):
        yy = 0
        while yy < altura - 1 and perto.get_at((xx, yy)).a == 0:
            yy += 1
        topo.append(yy)
    sabores = [(255, 170, 210), (170, 210, 255), (200, 170, 250), (255, 220, 150), (170, 240, 210)]
    x = rng.randint(6, 30)
    while x < largura - 8:
        _arvore_algodao(s, x, topo[x] + 4, rng.choice(sabores), rng, rng.choice((0.9, 1.1, 1.3)))
        x += rng.randint(30, 70)
    s.blit(perto, (0, 0))
    camadas.append(s)
    return camadas


# ------------------------------------------------------------------ tiles

def _tile_terra(pal, variante, prof):
    """Terra pastel com padrão de anéis e riscos de giz."""
    chave = ("terra", tuple(pal["terra"]), variante, prof)
    if chave in _cache:
        return _cache[chave]
    base = mix(pal["terra"], pal["terra_esc"], min(0.45, prof * 0.12))
    anel = mix(base, pal["terra_esc"], 0.55)
    luz = mix(base, pal["terra_clara"], 0.5)
    s = pygame.Surface((TILE, TILE))
    s.fill(base)
    rng = random.Random(variante * 97 + prof * 13 + 5)
    for _ in range(2):
        cx, cy, r = rng.randrange(2, 14), rng.randrange(2, 14), rng.choice((2, 2, 3))
        pygame.draw.circle(s, anel, (cx, cy), r, 1)
        s.set_at((cx - 1, cy - 1), luz)
    for _ in range(5):
        x, y = rng.randrange(16), rng.randrange(16)
        for k in range(3):
            if 0 <= x + k // 2 < 16 and 0 <= y - k < 16:
                s.set_at((x + k // 2, y - k), luz if k % 2 else mix(base, anel, 0.4))
    _cache[chave] = s
    return s


_PERFIL_GRAMA = [5, 6, 6, 5, 4, 4, 5, 6, 6, 5, 5, 4, 4, 5, 6, 5]


def render_nivel(nivel, pal):
    """Pré-renderiza o mapa de tiles numa superfície só."""
    W, H = nivel.w, nivel.h
    s = pygame.Surface((W * TILE, H * TILE), pygame.SRCALPHA)
    g = nivel.tiles
    solido = lambda x, y: 0 <= x < W and 0 <= y < H and g[y][x] in (1, 5)
    for y in range(H):
        for x in range(W):
            t = g[y][x]
            px, py = x * TILE, y * TILE
            if t == 1:
                prof = 0
                while prof < 4 and y - prof - 1 >= 0 and g[y - prof - 1][x] == 1:
                    prof += 1
                s.blit(_tile_terra(pal, ((x * 73856093) ^ (y * 19349663)) % 9, prof), (px, py))
                if not solido(x - 1, y):
                    s.fill(pal["contorno"], (px, py, 1, TILE))
                    s.fill(pal["terra_clara"], (px + 1, py, 1, TILE))
                if not solido(x + 1, y):
                    s.fill(pal["contorno"], (px + TILE - 1, py, 1, TILE))
                    s.fill(pal["terra_esc"], (px + TILE - 2, py, 1, TILE))
                if not solido(x, y - 1):
                    _grama(s, px, py, pal, solido(x - 1, y), solido(x + 1, y), (x * 31) % 5 == 0)
            elif t == 5:
                _tronco(s, px, py, not solido(x, y - 1))
            elif t == 2:
                _plataforma(s, px, py, g[y][x - 1] == 2 if x > 0 else False, g[y][x + 1] == 2 if x + 1 < W else False)
            elif t == 3:
                _espinho(s, px, py)
            elif t in (4, 6):
                _bloco_ovo(s, px, py, t == 6)
    _decorar(s, nivel, pal)
    return s


def _decorar(s, nivel, pal):
    """Enfeites sobre o chão (atrás dos personagens): moitas, flores altas sorridentes,
    tufos, pedras, cogumelos, cercas e a placa do hospital no início."""
    W, H, g = nivel.w, nivel.h, nivel.tiles
    rng = random.Random(getattr(nivel, "seed", 0) * 7 + 3)
    topo = []
    for x in range(W):
        yy = None
        for y in range(1, H):
            if g[y][x] == 1 and g[y - 1][x] == 0:
                yy = y
                break
        topo.append(yy)
    ini = int(getattr(nivel, "inicio", (64, 0))[0] // TILE)
    if 0 <= ini - 2 < W and topo[ini - 2] is not None:
        _placa_hospital(s, (ini - 2) * TILE + 2, topo[ini - 2] * TILE + 3)
    x = ini + 2
    while x < W - 4:
        y = topo[x]
        if y is None:
            x += 1
            continue
        plano = all(topo[x + k] == y for k in range(3) if x + k < W)
        base = y * TILE + 4
        px = x * TILE
        r = rng.random()
        if r < 0.20 and plano:
            _moita(s, px, base, rng.randint(2, 3), pal)
            x += 4
        elif r < 0.38:
            _flor_alta(s, px + rng.randint(2, 8), base, rng)
            x += 2
        elif r < 0.50 and plano:
            _cerca(s, px, base, rng.randint(2, 3))
            x += 4
        elif r < 0.60:
            _cogumelo(s, px + rng.randint(2, 8), base, rng)
            x += 2
        elif r < 0.70:
            _pedra(s, px + rng.randint(0, 6), base, pal)
            x += 2
        elif r < 0.88:
            _tufo(s, px + rng.randint(0, 10), base, pal)
            x += 1
        else:
            x += 1


def _contornar(c):
    """Contorno K de 1 px em volta do que estiver opaco na surface c."""
    w, h = c.get_size()
    out = c.copy()
    for y in range(h):
        for x in range(w):
            if c.get_at((x, y)).a:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and c.get_at((xx, yy)).a and c.get_at((xx, yy))[:3] != K:
                    out.set_at((x, y), K)
                    break
    return out


def _moita(s, px, base, n, pal):
    """Moita de algodão: bolas fofas na cor da cobertura, com olhinhos."""
    chave = ("moita", n, tuple(pal["grama"]))
    if chave not in _cache:
        w = n * 16
        rng = random.Random(n)
        bolas = [(5 + i * (w - 10) / max(1, n * 2 - 2), 12 - (3 if i % 2 else 0), 6 if i % 2 else 5) for i in range(n * 2 - 1)]
        c = _pintar_fofo(w + 2, 18, bolas, pal["grama_clara"], pal["grama"], pal["grama_esc"], pal["contorno"], rng, riscos=n * 25)
        mx = w // 2
        c.fill(pal["contorno"], (mx - 3, 9, 1, 3)); c.fill(pal["contorno"], (mx + 2, 9, 1, 3))
        _cache[chave] = c
    c = _cache[chave]
    s.blit(c, (px, base - c.get_height() + 1))


def _flor_alta(s, x, base, rng):
    cores = [((248, 88, 96), (255, 170, 170)), ((255, 210, 60), (255, 244, 170)), ((120, 150, 255), (200, 214, 255)),
             ((250, 140, 220), (255, 200, 240))]
    pet, luz = rng.choice(cores)
    h = rng.randint(9, 14)
    caule = (60, 150, 60)
    s.fill(K, (x, base - h, 3, h)); s.fill(caule, (x + 1, base - h, 1, h))
    s.fill(K, (x + 2, base - h // 2 - 1, 4, 3)); s.fill((100, 200, 80), (x + 3, base - h // 2, 2, 1))
    cy = base - h - 3
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
        pygame.draw.circle(s, K, (x + 1 + dx, cy + dy), 2)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
        pygame.draw.circle(s, pet, (x + 1 + dx, cy + dy), 1)
    s.fill(K, (x - 1, cy - 2, 5, 5))
    s.fill((255, 236, 120), (x, cy - 1, 3, 3))
    s.set_at((x, cy - 1), K); s.set_at((x + 2, cy - 1), K)       # carinha sorridente
    s.set_at((x + 1, cy + 1), (200, 60, 60))
    s.set_at((x - 2, cy - 3), luz)


def _cerca(s, px, base, n):
    mad, luz, som = (236, 220, 190), (255, 250, 236), (176, 150, 120)
    w = n * 16
    for yy in (base - 9, base - 5):
        s.fill(K, (px, yy - 1, w, 4)); s.fill(mad, (px, yy, w, 2)); s.fill(luz, (px, yy, w, 1))
    for i in range(n * 2 + 1):
        x = px + i * 8 - (1 if i == n * 2 else 0)
        s.fill(K, (x - 1, base - 13, 5, 13)); s.fill(mad, (x, base - 12, 3, 12))
        s.fill(luz, (x, base - 12, 1, 12)); s.fill(som, (x + 2, base - 12, 1, 12))
        s.set_at((x - 1, base - 13), (0, 0, 0, 0)); s.set_at((x + 3, base - 13), (0, 0, 0, 0))


def _cogumelo(s, x, base, rng):
    chapeu = rng.choice([((232, 64, 72), (255, 150, 140)), ((90, 170, 255), (180, 220, 255)), ((255, 170, 50), (255, 220, 140))])
    s.fill(K, (x - 2, base - 6, 6, 6)); s.fill((248, 240, 220), (x - 1, base - 6, 4, 6))
    s.set_at((x, base - 4), K); s.set_at((x + 1, base - 4), K)
    pygame.draw.ellipse(s, K, (x - 5, base - 12, 12, 8))
    pygame.draw.ellipse(s, chapeu[0], (x - 4, base - 11, 10, 6))
    s.fill((255, 255, 255), (x - 2, base - 10, 2, 2)); s.fill((255, 255, 255), (x + 3, base - 9, 1, 1))
    s.set_at((x - 3, base - 9), chapeu[1])


def _pedra(s, x, base, pal):
    """Bala de goma listrada no chão."""
    cor = pal["acento"]
    pygame.draw.ellipse(s, pal["contorno"], (x, base - 7, 11, 8))
    pygame.draw.ellipse(s, cor, (x + 1, base - 6, 9, 6))
    for k in range(1, 9, 3):
        s.fill(mix(cor, (255, 255, 255), 0.6), (x + 1 + k, base - 6, 1, 6))
    s.set_at((x + 3, base - 5), (255, 255, 255))


def _tufo(s, x, base, pal):
    """Tulipa rosa de três pétalas pontudas."""
    caule, ce = (110, 190, 110), (60, 130, 80)
    h = 7 + (x * 7) % 4
    s.fill(ce, (x + 2, base - h, 1, h))
    s.set_at((x + 3, base - h + 3), caule); s.set_at((x + 4, base - h + 2), caule)
    pet, pc, pe = (246, 140, 176), (255, 200, 220), (180, 70, 120)
    y = base - h - 5
    for dx, alto in ((0, 4), (2, 5), (4, 4)):
        for k in range(alto):
            s.set_at((x + dx, y + 5 - k), pet if k < alto - 1 else pe)
            s.set_at((x + dx + 1, y + 5 - k), pc if k > 1 else pet)
    s.fill(pe, (x, y + 5, 6, 1))


def _placa_hospital(s, x, base):
    """Placa de madeira com a cruz vermelha: o ponto de partida é o hospital."""
    s.fill(K, (x + 5, base - 12, 4, 12)); s.fill((176, 112, 64), (x + 6, base - 12, 2, 12))
    s.fill(K, (x - 1, base - 24, 16, 13)); s.fill((250, 248, 240), (x, base - 23, 14, 11))
    s.fill((214, 214, 228), (x, base - 13, 14, 1))
    from . import edicao
    if edicao.VESTIBULANDO:          # na Ilha do Vestibulando a partida é a escola: lousa verde com "1+1"
        s.fill((40, 110, 70), (x, base - 23, 14, 10))
        giz = (240, 244, 236)
        s.fill(giz, (x + 2, base - 20, 1, 4)); s.fill(giz, (x + 4, base - 19, 3, 1)); s.fill(giz, (x + 5, base - 20, 1, 3))
        s.fill(giz, (x + 8, base - 20, 1, 4)); s.fill(giz, (x + 10, base - 19, 2, 1)); s.fill(giz, (x + 10, base - 17, 2, 1))
        return
    s.fill((228, 52, 64), (x + 5, base - 22, 4, 9)); s.fill((228, 52, 64), (x + 2, base - 19, 10, 3))


def _grama(s, px, py, pal, viz_esq, viz_dir, flor_):
    """Cobertura fofa em bolotas na borda do chão, saindo 3 px
    acima do tile, com sombra embaixo, brilho em cima e contorno suave."""
    chave = ("cob", tuple(pal["grama"]), viz_esq, viz_dir, px // TILE % 3)
    if chave not in _cache:
        g, ge, gc, bo = pal["grama"], pal["grama_esc"], pal["grama_clara"], pal["contorno"]
        c = pygame.Surface((TILE + 2, 15), pygame.SRCALPHA)
        rng = random.Random(px // TILE % 3 + 1)
        bolas = []
        x = 1 + rng.randint(0, 2)
        while x < TILE + 1:
            bolas.append((x, rng.randint(5, 6), rng.choice((4, 5))))
            x += rng.randint(5, 7)
        if not viz_esq:
            bolas.append((2, 7, 3))
        if not viz_dir:
            bolas.append((TILE - 1, 7, 3))
        m = pygame.Surface(c.get_size(), pygame.SRCALPHA)
        for bx, by, r in bolas:
            pygame.draw.circle(m, (255, 255, 255), (bx, by), r)
        m.fill((255, 255, 255), (1 if not viz_esq else 0, 7, TILE + (0 if viz_dir else -1) + (1 if viz_esq else 0), 4))
        alfa = pygame.mask.from_surface(m)
        for bx, by, r in bolas:
            pygame.draw.circle(c, ge, (bx, by), r)
        for bx, by, r in bolas:
            pygame.draw.circle(c, g, (bx - 1, by - 1), max(1, r - 1))
            c.set_at((bx - 1, by - r + 1), gc)
            c.set_at((bx - 2, by - r + 2), gc)
        c.fill(ge, (0, 9, TILE + 2, 2))
        for y in range(c.get_height()):
            for x in range(c.get_width()):
                if not alfa.get_at((x, y)):
                    c.set_at((x, y), (0, 0, 0, 0))
                elif (y == 0 or not alfa.get_at((x, y - 1)) or (x > 0 and not alfa.get_at((x - 1, y)) and not viz_esq)
                      or (x + 1 < c.get_width() and not alfa.get_at((x + 1, y)) and not viz_dir)):
                    c.set_at((x, y), bo)
                elif y >= 10 and not alfa.get_at((x, min(c.get_height() - 1, y + 1))):
                    c.set_at((x, y), mix(ge, bo, 0.4))
        _cache[chave] = c
    c = _cache[chave]
    s.blit(c, (px - 1, py - 5))


def _tronco(s, px, py, topo):
    T, t, u = PAL["T"], PAL["t"], PAL["u"]
    s.fill(T, (px, py, TILE, TILE))
    for gx in (4, 9, 13):
        s.fill(t, (px + gx, py, 1, TILE))
    s.fill(u, (px + 2, py, 1, TILE))
    s.fill(K, (px, py, 1, TILE))
    s.fill(K, (px + TILE - 1, py, 1, TILE))
    if topo:
        pygame.draw.ellipse(s, K, (px, py - 3, TILE, 7))
        pygame.draw.ellipse(s, u, (px + 1, py - 2, TILE - 2, 5))
        pygame.draw.ellipse(s, T, (px + 5, py - 1, 6, 3))


def _plataforma(s, px, py, esq, dir_):
    """Ponte de tábuas: madeira com veio, pregos e pontas arredondadas."""
    mad, luz, som, veio = (214, 146, 78), (246, 196, 120), (150, 92, 46), (176, 112, 58)
    s.fill(K, (px, py, TILE, 9))
    s.fill(mad, (px, py + 1, TILE, 6))
    s.fill(luz, (px, py + 1, TILE, 1))
    s.fill(som, (px, py + 6, TILE, 1))
    s.fill(veio, (px + 2, py + 3, 5, 1)); s.fill(veio, (px + 9, py + 4, 4, 1))
    s.fill(K, (px + 7, py + 1, 1, 6))          # junta entre tábuas
    for nx in (2, 12):
        s.set_at((px + nx, py + 2), (90, 80, 90)); s.set_at((px + nx, py + 5), (90, 80, 90))
    if not esq:
        s.fill((0, 0, 0, 0), (px, py, 2, 9)); s.set_at((px + 2, py), (0, 0, 0, 0)); s.set_at((px + 2, py + 8), (0, 0, 0, 0))
        s.fill(K, (px + 1, py + 1, 1, 7)); s.fill(K, (px + 2, py, 1, 1))
        s.set_at((px + 2, py + 1), K); s.set_at((px + 2, py + 7), K)
    if not dir_:
        s.fill((0, 0, 0, 0), (px + TILE - 2, py, 2, 9)); s.set_at((px + TILE - 3, py), (0, 0, 0, 0)); s.set_at((px + TILE - 3, py + 8), (0, 0, 0, 0))
        s.fill(K, (px + TILE - 2, py + 1, 1, 7))
        s.set_at((px + TILE - 3, py + 1), K); s.set_at((px + TILE - 3, py + 7), K)


def _espinho(s, px, py):
    for k in range(2):
        x0 = px + k * 8
        for i in range(8):
            h = 9 - abs(i - 3.5) * 2.2
            for yy in range(int(h)):
                y = py + TILE - 1 - yy
                c = (232, 232, 240) if i < 4 else (160, 160, 184)
                if yy == int(h) - 1 or i in (0, 7):
                    c = K
                s.set_at((x0 + i, y), c)


def _bloco_ovo(s, px, py, usado):
    cor, luz, som = ((200, 184, 160), (232, 220, 200), (150, 132, 112)) if usado else \
        ((248, 200, 48), (255, 240, 160), (200, 128, 24))
    s.fill(K, (px, py, TILE, TILE))
    s.fill(cor, (px + 1, py + 1, TILE - 2, TILE - 2))
    s.fill(luz, (px + 1, py + 1, TILE - 2, 1))
    s.fill(luz, (px + 1, py + 1, 1, TILE - 2))
    s.fill(som, (px + 1, py + TILE - 2, TILE - 2, 1))
    s.fill(som, (px + TILE - 2, py + 1, 1, TILE - 2))
    for c in ((2, 2), (13, 2), (2, 13), (13, 13)):
        s.set_at((px + c[0], py + c[1]), som)
    if not usado:                                   # bloco de moedas (era o bloco do ovo)
        s.blit(moeda(0), (px + 4, py + 3))
