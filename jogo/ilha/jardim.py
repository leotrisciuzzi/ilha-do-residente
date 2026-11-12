"""Elenco da tela conceito O Jardim das Delícias (Hieronymus Bosch, c. 1490-1510; domínio público): figurino.ELENCO.

Como em quixote.py e grito.py, só muda o desenho: hitbox, física e comportamento continuam os do inimigo original.
Cada inimigo vira uma criatura do tríptico, sem nenhuma figura humana nua:
  coruja   — bicho-questão: a coruja que espia da fonte, com a placa da questão
  principe — o chefe: o Príncipe do Inferno, azul, cabeça de pássaro, panela na cabeça, sentado no trono alto
  morango  — os germes rasteiros: o morango gigante do painel central, agora de perninhas
  cardo    — quem tem espinho (não se pisa): os frutos cheios de pontas do jardim
  pintassilgo — quem voa: os pássaros enormes que pousam entre as pessoas
  mexilhao — caixas e comprimidos: a concha que abre e fecha, com dentes por dentro
  gaita    — quem cospe de longe: a gaita de foles do Inferno; o cuspe vira nota musical
  orelhas  — os monstros fortes: as duas orelhas com a faca no meio, agora andando
  lanterna — o feiticeiro: o encapuzado de lanterna do painel do Inferno
O peixe de pernas (o bicho que sai da água no Paraíso) fica no lugar do pet; no fundo, a Fonte da Vida torce pelo
jogador e o Homem-Árvore olha para trás e zomba do erro, no lugar do Oni e do Daidara."""
import math

import pygame

from .quixote import Dupla as _Dupla, _anda, _barra, _colar, _par, _sprite

K = (24, 18, 34)
ROSA, ROSA2, ROSA3 = (240, 156, 176), (198, 104, 142), (252, 208, 214)
AZUL, AZUL2, AZUL3 = (72, 116, 196), (42, 68, 138), (150, 190, 232)
VERDE, VERDE2 = (112, 170, 96), (66, 118, 80)
VERMELHO, VERMELHO2 = (216, 52, 62), (150, 30, 54)
OURO, OURO2 = (248, 204, 92), (190, 136, 50)
OSSO, OSSO2 = (240, 230, 208), (190, 174, 158)
MADEIRA, MADEIRA2 = (136, 94, 62), (88, 58, 48)
FOGO = (244, 130, 48)

FORMA = {"BichoQuestao": "coruja", "Gigante": "principe",
         "Bacilo": "morango", "Estafilococo": "morango", "Estreptococo": "morango", "Ameba": "morango",
         "Globulo": "morango", "Carrapato": "morango", "Tatu": "morango",
         "Virus": "cardo", "Fago": "cardo", "Candida": "cardo",
         "Aedes": "pintassilgo", "Morcego": "pintassilgo", "Mosca": "pintassilgo", "AguaViva": "pintassilgo",
         "Caixa": "mexilhao", "Comprimido": "mexilhao", "Lombriga": "mexilhao", "Musgo": "mexilhao",
         "Cuspidor": "gaita", "Chifrudo": "orelhas", "Louva": "orelhas", "Colosso": "orelhas",
         "Feiticeiro": "lanterna"}
NOTAS = ("Cuspe", "Seringa", "Esporo")        # projéteis: as notas da partitura do painel do Inferno
BRAVOS = ("mira", "grito", "ergue", "prestes", "incha")
_CACHE = {}


def forma_de(e):
    """Forma do inimigo, ou None para quem fica como está (ondas, orbes)."""
    nome = type(e).__name__
    if nome in NOTAS:
        return "nota"
    if nome in ("BichoQuestao", "Gigante"):
        return FORMA[nome]
    if getattr(e, "espinhento", False):
        return "cardo"
    if nome in FORMA:
        return FORMA[nome]
    return "coruja" if getattr(e, "boneco", None) is not None else None


def _bravo(e):
    return bool(getattr(e, "bravo", 0)) or getattr(e, "estado", "") in BRAVOS


def _perninhas(c, cx, y, h, q, cor=K, d=3, pe=None):
    """Perna fina de bicho de Bosch, em curva, com o pezinho para a frente."""
    for lado in (-1, 1):
        fx = cx + lado * d + lado * q * 2
        pygame.draw.lines(c, cor, False, [(cx + lado * d, y), (cx + lado * d + lado, (y + h) // 2), (fx, h - 2)], 2)
        c.fill(pe or cor, (fx - 1, h - 2, 4, 2))


# --------------------------------------------------------------------- a coruja da fonte (bicho-questão)

def _coruja(c, w, h, q, bravo):
    cx = w // 2
    _perninhas(c, cx, h - 7, h, 0, OURO2, 4, OURO2)
    pena, pena2 = (136, 96, 66), (92, 62, 54)
    pygame.draw.ellipse(c, pena2, (cx - w * 0.42, h * 0.12, w * 0.84, h * 0.78))
    pygame.draw.ellipse(c, pena, (cx - w * 0.42, h * 0.1, w * 0.74, h * 0.74))
    pygame.draw.ellipse(c, (224, 200, 158), (cx - w * 0.22, h * 0.44, w * 0.44, h * 0.42))
    for k in range(3):                                 # peito em escamas
        for j in range(3 - k % 2):
            c.set_at((int(cx - w * 0.14 + j * w * 0.14 + (k % 2) * w * 0.07), int(h * (0.54 + k * 0.1))), pena2)
    for lado in (-1, 1):                               # tufos, asa que abana
        pygame.draw.polygon(c, pena2, [(cx + lado * w * 0.14, h * 0.16), (cx + lado * w * 0.4, 0), (cx + lado * w * 0.36, h * 0.24)])
        pygame.draw.ellipse(c, pena2, (cx + (w * 0.26 if lado > 0 else -w * 0.42), h * (0.4 - 0.03 * q), w * 0.16, h * 0.34))
    r = max(3, int(w * 0.17))
    y = int(h * 0.32)
    fecha = q == 3 and not bravo
    for lado in (-1, 1):                               # o olho enorme e fixo que encara do quadro
        ex = cx + lado * (r + 1)
        pygame.draw.circle(c, (250, 234, 180), (ex, y), r)
        if fecha:
            c.fill(K, (ex - r + 1, y, r * 2 - 2, 1))
        else:
            pygame.draw.circle(c, VERMELHO if bravo else K, (ex, y), max(1, r // 2))
            c.set_at((ex - 1, y - 1), (255, 255, 255))
    pygame.draw.polygon(c, OURO, [(cx - 2, y + 2), (cx + 2, y + 2), (cx, y + 6)])
    if bravo:
        for lado in (-1, 1):
            pygame.draw.line(c, K, (cx + lado * (2 * r + 1), y - r - 1), (cx + lado, y - r + 2), 2)


def desenhar_coruja(s, cam, e):
    w, h = _par(max(e.w * 1.5, 24)), _par(max(e.h * 2.1, 28))
    bravo = _bravo(e)
    q = (getattr(e, "t", 0) // 12) % 8
    q = q if q < 4 else 0
    chave = ("j_coruja", w, h, q, bravo)
    spr = _sprite(chave, w, h, lambda c: _coruja(c, w, h, q, bravo), K)
    x, y = _colar(s, cam, e, spr, chave, dy=-int(abs(math.sin(e.t * 0.1)) * 2))
    virado = getattr(e, "virado", 1) or 1
    placa = getattr(getattr(e, "boneco", None), "placa", None)
    if placa is not None:                              # a placa da questão, sempre legível
        s.blit(placa, (x + w // 2 - (w // 2 + 3) * virado - placa.get_width() // 2, y + int(math.sin(e.t * 0.1) * 1.5)))


# --------------------------------------------------------------------- o Príncipe do Inferno (chefe)

def _principe(c, w, h, q, bravo):
    cx = w // 2
    az, az2 = (66, 112, 190), (38, 62, 130)
    for lado in (-1, 1):                               # o trono alto, de pernas compridas
        pygame.draw.line(c, MADEIRA2, (cx + lado * int(w * 0.22), int(h * 0.62)), (cx + lado * int(w * 0.34), h - 1), 3)
    c.fill(MADEIRA, (cx - int(w * 0.34), int(h * 0.6), int(w * 0.68), max(3, h // 14)))
    c.fill(MADEIRA2, (cx - int(w * 0.34), int(h * 0.64), int(w * 0.68), 2))
    pygame.draw.ellipse(c, az2, (cx - int(w * 0.32), int(h * 0.26), int(w * 0.64), int(h * 0.4)))     # a barriga azul
    pygame.draw.ellipse(c, az, (cx - int(w * 0.32), int(h * 0.25), int(w * 0.54), int(h * 0.36)))
    pygame.draw.ellipse(c, AZUL3, (cx - int(w * 0.2), int(h * 0.34), int(w * 0.26), int(h * 0.2)))
    for lado in (-1, 1):                               # pés de ave, pendurados, com a panelinha em cada um
        fx = cx + lado * int(w * 0.16)
        pygame.draw.line(c, az2, (fx, int(h * 0.62)), (fx, int(h * 0.76)), 2)
        pygame.draw.ellipse(c, (70, 62, 74), (fx - 6, int(h * 0.74), 12, 8))
    a = (math.sin(q * math.pi / 2)) * h * 0.04         # braços que levam tudo à boca
    for lado in (-1, 1):
        pygame.draw.line(c, az2, (cx + lado * int(w * 0.28), int(h * 0.36)), (cx + lado * int(w * 0.42), int(h * 0.26 + lado * a)), 4)
        pygame.draw.circle(c, az, (cx + lado * int(w * 0.42), int(h * 0.26 + lado * a)), 3)
    r = max(8, int(w * 0.24))
    fy = int(h * 0.2)
    pygame.draw.circle(c, az, (cx, fy), r)
    pygame.draw.circle(c, az2, (cx + r // 3, fy + r // 3), r * 2 // 3)
    pygame.draw.circle(c, az, (cx - 1, fy - 1), r * 3 // 4)
    abre = 5 + (q % 2) * 3 + (3 if bravo else 0)        # o bico: abre e fecha, mastigando
    pygame.draw.polygon(c, OURO, [(cx - 2, fy - 2), (cx + r + 9, fy + 1), (cx + 2, fy + 3)])
    pygame.draw.polygon(c, OURO2, [(cx - 2, fy + 3), (cx + r + 6, fy + 2 + abre), (cx + 2, fy + 6)])
    for lado in (-1, 1):
        pygame.draw.circle(c, (250, 236, 180), (cx + lado * r // 2 - 2, fy - r // 4), 3)
        pygame.draw.circle(c, VERMELHO if bravo else K, (cx + lado * r // 2 - 1, fy - r // 4), 1)
    pygame.draw.polygon(c, (86, 76, 80), [(cx - r, fy - r + 3), (cx + r, fy - r + 3), (cx + r - 3, fy - r - 6), (cx - r + 3, fy - r - 6)])   # a panela
    c.fill((122, 110, 112), (cx - r + 3, fy - r - 6, r * 2 - 6, 2))
    pygame.draw.line(c, (86, 76, 80), (cx + r - 3, fy - r - 4), (cx + r + 5, fy - r - 8), 2)


def desenhar_principe(s, cam, e):
    if getattr(e, "invuln", 0) and e.invuln % 6 < 3:
        return
    w, h = _par(max(e.w * 1.5, 40)), _par(max(e.h * 1.5, 54))
    bravo = _bravo(e)
    q = (e.t // 9) % 4
    chave = ("j_principe", w, h, q, bravo)
    spr = _sprite(chave, w, h, lambda c: _principe(c, w, h, q, bravo), K)
    x, y = _colar(s, cam, e, spr, chave)
    virado = getattr(e, "virado", 1) or 1
    placa = getattr(getattr(e, "boneco", None), "placa", None)
    if placa is not None:
        s.blit(placa, (x + w // 2 - (w // 2 + 3) * virado - placa.get_width() // 2, y + int(math.sin(e.t * 0.1) * 1.5)))


# --------------------------------------------------------------------- o morango gigante

def _morango(c, w, h, q, seed, bravo):
    cx = w // 2
    _perninhas(c, cx, h - 6, h, q, VERDE2, 3)
    corpo = (VERMELHO, (230, 76, 66), (204, 44, 76))[seed % 3]
    pts = [(cx, h - 3), (cx - w * 0.42, h * 0.48), (cx - w * 0.36, h * 0.2), (cx + w * 0.36, h * 0.2), (cx + w * 0.42, h * 0.48)]
    pygame.draw.polygon(c, VERMELHO2, pts)
    pygame.draw.polygon(c, corpo, [(cx - 1, h - 5), (cx - w * 0.42, h * 0.46), (cx - w * 0.36, h * 0.2), (cx + w * 0.24, h * 0.2), (cx + w * 0.2, h * 0.5)])
    pygame.draw.ellipse(c, corpo, (cx - w * 0.42, h * 0.16, w * 0.84, h * 0.46))
    pygame.draw.ellipse(c, VERMELHO2, (cx + w * 0.14, h * 0.26, w * 0.26, h * 0.34))
    pygame.draw.ellipse(c, corpo, (cx + w * 0.1, h * 0.22, w * 0.26, h * 0.34))
    for k, (fx, fy) in enumerate(((-0.26, 0.56), (0.0, 0.66), (0.22, 0.6), (-0.1, 0.8), (0.32, 0.36), (-0.34, 0.36))):   # as sementes
        c.set_at((int(cx + w * fx), int(h * fy)), OURO)
    for k in range(5):                                 # o cabo de folhas
        a = -math.pi * k / 4
        pygame.draw.line(c, VERDE, (cx, int(h * 0.18)), (cx + math.cos(a) * w * 0.32, h * 0.18 + math.sin(a) * h * 0.14), 2)
    for lado in (-1, 1):
        c.fill(K, (cx + lado * max(2, w // 7) - 1, int(h * 0.38), 2, 2))
    if bravo:
        pygame.draw.line(c, K, (cx - w // 4, int(h * 0.28)), (cx - 1, int(h * 0.34)))
        pygame.draw.line(c, K, (cx + w // 4, int(h * 0.28)), (cx + 1, int(h * 0.34)))
    c.fill(K, (cx - 1, int(h * 0.5), 3, 1))


def desenhar_morango(s, cam, e):
    w, h = _par(max(e.w * 1.4, 16)), _par(max(e.h * 2.0, 20))
    q = ((e.t // 6) % 3 - 1) if _anda(e) else 0
    seed = sum(map(ord, type(e).__name__))
    bravo = _bravo(e)
    chave = ("j_morango", w, h, q, seed % 3, bravo)
    spr = _sprite(chave, w, h, lambda c: _morango(c, w, h, q, seed, bravo), K)
    _colar(s, cam, e, spr, chave, dy=-int(abs(math.sin(e.t * 0.25)) * 2) if _anda(e) else 0)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o fruto de pontas

def _cardo(c, w, h, q):
    cx, cy = w // 2, h // 2 + 1
    r = min(w, h) * 0.3
    for k in range(11):                                # as pontas giram devagar: é o aviso de que não se pisa
        a = k * 2 * math.pi / 11 + q * 0.28
        cor = ROSA3 if k % 2 else AZUL3
        ax, ay = cx + math.cos(a) * r * 1.65, cy + math.sin(a) * r * 1.65
        pygame.draw.polygon(c, cor, [(cx + math.cos(a - 0.24) * r, cy + math.sin(a - 0.24) * r), (ax, ay),
                                     (cx + math.cos(a + 0.24) * r, cy + math.sin(a + 0.24) * r)])
    pygame.draw.circle(c, ROSA2, (cx, cy), int(r))
    pygame.draw.circle(c, ROSA, (cx - 1, cy - 1), int(r * 0.78))
    for k in range(5):                                 # a casca em gomos
        a = k * 2 * math.pi / 5
        c.set_at((int(cx + math.cos(a) * r * 0.55), int(cy + math.sin(a) * r * 0.55)), ROSA2)
    for lado in (-1, 1):
        c.fill(K, (cx + lado * max(2, int(r * 0.4)) - 1, cy - 2, 2, 3))
    c.fill(K, (cx - 2, cy + max(2, int(r * 0.4)), 4, 1))


def desenhar_cardo(s, cam, e):
    w = h = _par(max(e.w, e.h) * 2.0)
    q = (e.t // 5) % 6
    chave = ("j_cardo", w, q)
    spr = _sprite(chave, w, h, lambda c: _cardo(c, w, h, q), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o pássaro enorme

def _pintassilgo(c, w, h, q):
    cx, cy = int(w * 0.52), int(h * 0.56)
    asa = (-0.42, -0.08, 0.3, -0.08)[q]
    amarelo, amarelo2 = (248, 206, 70), (196, 140, 40)
    pygame.draw.polygon(c, K, [(cx - w * 0.3, cy), (cx - w * 0.5, cy + h * 0.1), (cx - w * 0.5, cy + h * 0.32), (cx - w * 0.22, cy + h * 0.16)])
    pygame.draw.polygon(c, amarelo2, [(cx - 4, cy - 2), (cx - w * 0.3, cy + h * asa), (cx - w * 0.12, cy + h * asa * 0.2 + 3), (cx + 4, cy + 2)])
    pygame.draw.ellipse(c, (232, 214, 182), (cx - w * 0.3, cy - h * 0.18, w * 0.62, h * 0.4))
    pygame.draw.ellipse(c, (186, 148, 112), (cx - w * 0.3, cy - h * 0.12, w * 0.46, h * 0.26))
    pygame.draw.polygon(c, amarelo, [(cx - 3, cy - 3), (cx + w * 0.12, cy + h * asa), (cx + w * 0.26, cy + h * asa * 0.3 + 3), (cx + 6, cy + 3)])
    pygame.draw.polygon(c, K, [(cx + w * 0.12, cy + h * asa), (cx + w * 0.26, cy + h * asa * 0.3 + 3), (cx + w * 0.2, cy + h * asa * 0.7 + 2)])
    r = max(4, int(h * 0.2))
    hx, hy = cx + int(w * 0.28), cy - int(h * 0.2)
    pygame.draw.circle(c, (246, 240, 226), (hx, hy), r)
    pygame.draw.ellipse(c, VERMELHO, (hx - r // 2, hy - r + 1, r + r // 2, r + 1))   # a máscara vermelha do pintassilgo
    c.fill(K, (hx - r + 1, hy - r // 2, max(2, r // 2), r))
    c.fill(K, (hx + 1, hy - 1, 2, 2))
    pygame.draw.polygon(c, (232, 196, 170), [(hx + r - 1, hy - 1), (hx + r + 4, hy + 1), (hx + r - 1, hy + 2)])


def desenhar_pintassilgo(s, cam, e):
    w, h = _par(max(e.w * 2.1, 28)), _par(max(e.h * 2.3, 22))
    q = (e.t // 5) % 4
    chave = ("j_pintassilgo", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _pintassilgo(c, w, h, q), K)
    _colar(s, cam, e, spr, chave, voa=True)
    _barra(s, cam, e)


# --------------------------------------------------------------------- a concha de dentes

def _mexilhao(c, w, h, q):
    cx = w // 2
    abre = (0, 2, 5, 2)[q] * max(1, h // 18)
    base = h - 5
    cima, baixo = (58, 74, 118), (40, 50, 88)
    _perninhas(c, cx, base, h, 0, K, w // 4)
    pygame.draw.ellipse(c, K, (cx - w * 0.42, base - h * 0.4 - abre, w * 0.84, h * 0.32 + abre))   # o escuro de dentro
    pygame.draw.ellipse(c, VERMELHO2, (cx - w * 0.3, base - h * 0.3 - abre, w * 0.6, h * 0.22 + abre))
    if abre > 2:                                       # os dentes e os olhinhos que moram lá dentro
        for k in range(-2, 3):
            c.fill(OSSO, (cx + k * max(2, w // 8) - 1, base - int(h * 0.12) - 1, 2, 3))
        for lado in (-1, 1):
            c.fill(OURO, (cx + lado * max(2, w // 7) - 1, base - int(h * 0.3) - abre // 2, 2, 2))
    pygame.draw.ellipse(c, baixo, (cx - w * 0.46, base - h * 0.24, w * 0.92, h * 0.28))
    pts = [(cx - w * 0.46, base - h * 0.2 - abre), (cx - w * 0.22, base - h * 0.6 - abre), (cx + w * 0.26, base - h * 0.62 - abre), (cx + w * 0.46, base - h * 0.2 - abre)]
    pygame.draw.polygon(c, cima, pts)
    pygame.draw.polygon(c, (92, 112, 160), pts[:2] + [(cx - w * 0.06, base - h * 0.5 - abre), (cx - w * 0.26, base - h * 0.2 - abre)])
    for k in range(3):                                 # as linhas de crescimento da concha
        pygame.draw.line(c, (32, 40, 74), (cx - w * 0.3 + k * w * 0.24, base - h * 0.24 - abre), (cx - w * 0.16 + k * w * 0.2, base - h * 0.54 - abre))


def desenhar_mexilhao(s, cam, e):
    w, h = _par(max(e.w * 1.5, 20)), _par(max(e.h * 1.7, 20))
    fase = getattr(e, "t", 0) // 10
    q = (fase % 8) if fase % 8 < 4 else 0
    chave = ("j_mexilhao", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _mexilhao(c, w, h, q), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- a gaita de foles que cospe notas

def _gaita(c, w, h, q, mira):
    cx = w // 2 - 2
    _perninhas(c, cx, int(h * 0.72), h, 0, K, 4)
    sopro = (3 if mira else q) + 1                     # o fole enche antes de cuspir
    bag, bag2 = (214, 104, 124), (150, 62, 96)
    pygame.draw.ellipse(c, bag2, (cx - w * 0.34 - sopro, h * 0.3 - sopro // 2, w * 0.68 + sopro * 2, h * 0.46 + sopro))
    pygame.draw.ellipse(c, bag, (cx - w * 0.34 - sopro, h * 0.28 - sopro // 2, w * 0.56 + sopro, h * 0.4 + sopro))
    c.set_at((cx - int(w * 0.14), int(h * 0.38)), ROSA3)
    c.set_at((cx - int(w * 0.1), int(h * 0.36)), ROSA3)
    for x0, comp in ((-0.14, 0.34), (0.02, 0.28)):     # os bordões apontados para cima
        pygame.draw.line(c, MADEIRA2, (cx + w * x0, h * 0.32), (cx + w * x0 - 2, h * (0.32 - comp)), 2)
        c.fill(OURO, (int(cx + w * x0 - 3), int(h * (0.32 - comp)) - 1, 3, 2))
    bx = cx + int(w * 0.32)                            # a boca: o cano pelo qual saem as notas
    pygame.draw.line(c, MADEIRA, (cx + int(w * 0.2), int(h * 0.5)), (bx + 5, int(h * 0.44)), 4)
    c.fill(OURO2, (bx + 4, int(h * 0.38), 3, 7))
    for lado in (-1, 1):
        ex = cx - int(w * 0.04) + lado * max(2, w // 8)
        pygame.draw.circle(c, (250, 236, 200), (ex, int(h * 0.48)), 2)
        c.set_at((ex + 1, int(h * 0.48)), K)


def desenhar_gaita(s, cam, e):
    w, h = _par(max(e.w * 1.8, 26)), _par(max(e.h * 1.5, 28))
    q = (e.t // 12) % 2
    mira = getattr(e, "estado", "") == "mira"
    chave = ("j_gaita", w, h, q, mira)
    spr = _sprite(chave, w, h, lambda c: _gaita(c, w, h, q, mira), K)
    x, y = _colar(s, cam, e, spr, chave)
    if mira:                                           # treme e solta uma notinha de aviso
        f = e.t % 24
        virado = getattr(e, "virado", 1) or 1
        nota(s, x + (w + 2 if virado > 0 else -2), y + 8 - f // 3)
    _barra(s, cam, e)


# --------------------------------------------------------------------- as orelhas com a faca

def _orelha(c, ox, y0, alt, larg, lado):
    """Uma orelha de verdade, de perfil: hélice larga em cima, lóbulo fino embaixo, a dobra em C e o canal escuro."""
    pele, pele2, dobra = (244, 196, 170), (206, 140, 128), (168, 92, 96)
    pygame.draw.ellipse(c, pele2, (ox - larg // 2, y0, larg, int(alt * 0.74)))
    pygame.draw.ellipse(c, pele2, (ox - larg // 4 + lado, y0 + int(alt * 0.6), larg // 2, int(alt * 0.4)))     # lóbulo
    pygame.draw.ellipse(c, pele, (ox - larg // 2 + (1 if lado > 0 else 0), y0, larg - 1, int(alt * 0.7)))
    pygame.draw.ellipse(c, pele, (ox - larg // 4 + lado, y0 + int(alt * 0.6), larg // 2 - 1, int(alt * 0.36)))
    ax, ay, aw, ah = ox - larg // 2 + 3, y0 + 3, larg - 6, int(alt * 0.56)
    if lado > 0:                                       # a dobra da hélice abre para o lado de fora
        pygame.draw.arc(c, dobra, (ax, ay, aw, ah), -1.2, 2.6, 2)
    else:
        pygame.draw.arc(c, dobra, (ax, ay, aw, ah), 0.5, 4.3, 2)
    pygame.draw.ellipse(c, dobra, (ox - 2 - lado * (larg // 8), y0 + int(alt * 0.34), 4, int(alt * 0.16)))     # o canal


def _orelhas(c, w, h, q, bravo):
    cx = w // 2
    _perninhas(c, cx, int(h * 0.82), h, q, K, max(3, w // 6))
    fy = int(h * (0.0 if bravo else 0.08))             # bravo, a faca sobe
    lam = max(3, w // 8)
    for lado in (-1, 1):                               # as duas orelhas, altas, encostadas na lâmina
        _orelha(c, cx + lado * int(w * 0.28), int(h * 0.2), int(h * 0.62), int(w * 0.38), lado)
    pygame.draw.polygon(c, (222, 228, 238), [(cx - lam, h * 0.78), (cx + lam, h * 0.78), (cx + lam, fy + h * 0.12), (cx - lam + 1, fy)])
    pygame.draw.polygon(c, (156, 164, 184), [(cx + 1, h * 0.78), (cx + lam, h * 0.78), (cx + lam, fy + h * 0.12), (cx + 1, fy + h * 0.07)])
    c.fill(MADEIRA2, (cx - lam - 1, int(h * 0.76), lam * 2 + 2, max(3, h // 10)))
    ey = int(h * 0.42)                                 # os olhinhos na lâmina: é a faca que anda
    for lado in (-1, 1):
        c.fill(K, (cx + lado * max(1, lam // 2) - 1, ey, 2, 3))
    if bravo:
        pygame.draw.line(c, K, (cx - lam, ey - 3), (cx - 1, ey - 1))
        pygame.draw.line(c, K, (cx + lam, ey - 3), (cx + 1, ey - 1))
        c.fill(VERMELHO, (cx - 1, int(h * 0.56), 3, int(h * 0.1)))


def desenhar_orelhas(s, cam, e):
    w, h = _par(max(e.w * 1.7, 28)), _par(max(e.h * 1.5, 32))
    q = ((e.t // 7) % 3 - 1) if _anda(e) else 0
    bravo = _bravo(e)
    chave = ("j_orelhas", w, h, q, bravo)
    spr = _sprite(chave, w, h, lambda c: _orelhas(c, w, h, q, bravo), K)
    _colar(s, cam, e, spr, chave, dy=-int(abs(math.sin(e.t * 0.2)) * 2) if _anda(e) else 0)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o encapuzado da lanterna

def _lanterna(c, w, h, q):
    cx = w // 2 - 1
    manto, manto2 = (58, 48, 78), (34, 28, 54)
    pygame.draw.polygon(c, manto, [(cx - 5, h * 0.3), (cx + 6, h * 0.3), (cx + w * 0.26, h - 2), (cx - w * 0.3, h - 2)])
    pygame.draw.polygon(c, manto2, [(cx + 1, h * 0.3), (cx + 6, h * 0.3), (cx + w * 0.26, h - 2), (cx + 1, h - 2)])
    r = max(5, int(h * 0.15))
    yc = int(h * 0.22)
    pygame.draw.ellipse(c, manto2, (cx - r - 2, yc - r - 3, r * 2 + 4, r * 2 + 6))
    pygame.draw.circle(c, K, (cx, yc), r)
    for lado in (-1, 1):
        c.fill(OURO, (cx + lado * (r // 2) - 1, yc - 1, 2, 2))
    lx, ly = cx + int(w * 0.3), int(h * 0.4)           # a lanterna na ponta da vara
    pygame.draw.line(c, MADEIRA, (cx + 3, int(h * 0.58)), (lx, ly - 3), 2)
    c.fill(K, (lx - 4, ly - 3, 9, 11))
    c.fill(OURO if q else FOGO, (lx - 3, ly - 2, 7, 9))
    c.fill((255, 246, 200), (lx - 1, ly, 3, 4))
    c.fill(MADEIRA2, (lx - 4, ly - 5, 9, 2))


def desenhar_lanterna(s, cam, e):
    w, h = _par(max(e.w * 1.9, 28)), _par(max(e.h * 1.5, 34))
    q = (e.t // 8) % 2
    chave = ("j_lanterna", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _lanterna(c, w, h, q), K)
    x, y = _colar(s, cam, e, spr, chave, dy=int(math.sin(e.t * 0.05) * 2))
    _barra(s, cam, e)


# --------------------------------------------------------------------- a nota musical (projétil)

def nota(s, x, y):
    pygame.draw.ellipse(s, K, (x - 3, y, 6, 5))
    pygame.draw.line(s, K, (x + 2, y + 2), (x + 2, y - 6), 2)
    pygame.draw.line(s, K, (x + 2, y - 6), (x + 5, y - 4), 2)
    pygame.draw.ellipse(s, OSSO, (x - 2, y + 1, 4, 3))


def desenhar_nota(s, cam, e):
    nota(s, int(e.x + e.w / 2 - cam[0]), int(e.y + e.h / 2 - cam[1]))


_DESENHOS = {"coruja": desenhar_coruja, "principe": desenhar_principe, "morango": desenhar_morango, "cardo": desenhar_cardo,
             "pintassilgo": desenhar_pintassilgo, "mexilhao": desenhar_mexilhao, "gaita": desenhar_gaita,
             "orelhas": desenhar_orelhas, "lanterna": desenhar_lanterna, "nota": desenhar_nota}


def desenhar(s, cam, e):
    """Desenha o inimigo como criatura de Bosch. False = esse aí fica com o desenho de sempre."""
    forma = forma_de(e)
    if forma is None:
        return False
    _DESENHOS[forma](s, cam, e)
    return True


# --------------------------------------------------------------------- os gigantes do fundo: a Fonte e o Homem-Árvore

GW, GH = 96, 108


def _fonte(c, humor, fecha):
    """A Fonte da Vida do Paraíso: cúpula rosa em gomos, agulha com o globo azul, chifres com botões, gola de contas e a
    bacia que transborda. Comemora jorrando alto; no erro, chora pelas bicas."""
    cx = GW // 2
    pygame.draw.polygon(c, ROSA2, [(cx - 12, 70), (cx + 12, 70), (cx + 22, GH), (cx - 22, GH)])         # o pé
    pygame.draw.polygon(c, ROSA, [(cx - 12, 70), (cx + 2, 70), (cx + 4, GH), (cx - 22, GH)])
    pygame.draw.ellipse(c, ROSA2, (cx - 40, 66, 80, 20))                                               # a bacia
    pygame.draw.ellipse(c, ROSA3, (cx - 40, 63, 80, 18))
    pygame.draw.ellipse(c, AZUL, (cx - 34, 66, 68, 11))
    pygame.draw.ellipse(c, AZUL3, (cx - 30, 67, 44, 6))
    alto = humor == "ri"
    for lado in (-1, 1):                               # as bicas: no acerto sobem, no erro só pingam
        pts = [(cx + lado * (26 + u * 22), (54 - 40 * u + 58 * u * u) if alto else 56 + 18 * u * u) for u in (k / 8 for k in range(9))]
        pygame.draw.lines(c, AZUL3, False, pts, 3 if humor != "triste" else 1)
        pygame.draw.lines(c, (236, 248, 252), False, pts, 1)
    for lado in (-1, 1):                               # os chifres finos que brotam da cúpula, com botão na ponta
        pts = [(cx + lado * 24, 40), (cx + lado * 38, 32), (cx + lado * 40, 14)]
        pygame.draw.lines(c, ROSA2, False, pts, 4)
        pygame.draw.lines(c, ROSA, False, pts, 2)
        pygame.draw.circle(c, ROSA2, (cx + lado * 40, 12), 5)
        pygame.draw.circle(c, ROSA3, (cx + lado * 40 - 1, 11), 3)
    pygame.draw.polygon(c, ROSA2, [(cx - 5, 18), (cx + 5, 18), (cx + 2, 8), (cx - 2, 8)])              # a agulha
    pygame.draw.circle(c, AZUL2, (cx, 7), 7)
    pygame.draw.circle(c, AZUL, (cx - 1, 6), 5)
    c.set_at((cx - 3, 4), (232, 244, 252))
    pygame.draw.ellipse(c, ROSA2, (cx - 29, 14, 58, 52))                                               # a cúpula
    pygame.draw.ellipse(c, ROSA, (cx - 29, 14, 52, 48))
    for dx, l in ((-20, 6), (20, 6)):                  # os gomos da pedra rosa
        pygame.draw.arc(c, ROSA2, (cx + dx - l - 8, 16, 2 * (l + 8), 46), 1.2 if dx > 0 else -0.3, 2.0 if dx > 0 else 0.5 + 1.2, 1)
    pygame.draw.ellipse(c, ROSA3, (cx - 21, 19, 13, 7))
    ey = 36
    for lado in (-1, 1):
        ex = cx + lado * 11
        if fecha or humor == "ri":                     # olhos apertados de alegria (ou a piscada)
            pygame.draw.arc(c, K, (ex - 6, ey - 5, 12, 10), 0.2, 2.9, 3)
        else:
            pygame.draw.ellipse(c, (255, 252, 244), (ex - 6, ey - 7, 12, 14))
            pygame.draw.ellipse(c, K, (ex - 3 - lado, ey - 4, 6, 9))
            c.set_at((ex - 2 - lado, ey - 3), (255, 255, 255))
            pygame.draw.line(c, K, (ex - 5, ey - 7), (ex - 7 * lado * 0 + 5, ey - 8))
        if humor == "triste":
            pygame.draw.line(c, K, (cx + lado * 5, ey - 10), (cx + lado * 16, ey - 7), 2)
    for lado in (-1, 1):
        pygame.draw.ellipse(c, ROSA2, (cx + lado * 20 - 5, 45, 10, 5))
    if humor == "ri":
        pygame.draw.ellipse(c, K, (cx - 11, 45, 22, 15))
        pygame.draw.ellipse(c, VERMELHO2, (cx - 9, 46, 18, 13))
        c.fill(OSSO, (cx - 7, 46, 14, 3))
    elif humor == "triste":
        pygame.draw.arc(c, K, (cx - 8, 49, 16, 10), 0.4, 2.7, 3)
        pygame.draw.circle(c, AZUL3, (cx + 15, 47), 2)
        c.fill(AZUL3, (cx + 15, 49, 1, 4))
    else:
        pygame.draw.arc(c, K, (cx - 10, 42, 20, 12), 3.5, 5.9, 3)
    for k in range(-5, 6):                             # a gola de contas
        pygame.draw.circle(c, OURO if k % 2 else AZUL, (cx + k * 5, 62 - abs(k) // 2), 2)


def _homem_arvore(c, q, humor):
    """O Homem-Árvore do Inferno: os galhos secos subindo dos ombros de casca de ovo quebrada, o fogo aceso dentro do peito,
    o rosto comprido e pálido olhando de lado, por cima do ombro, e o disco rosa com a gaita enorme na cabeça."""
    cx = GW // 2
    for lado in (-1, 1):                               # os galhos: é por eles que se lê "árvore"
        pts = [(cx + lado * 34, 74), (cx + lado * 42, 50), (cx + lado * 40, 26), (cx + lado * 45, 10)]
        pygame.draw.lines(c, MADEIRA2, False, pts, 7)
        pygame.draw.lines(c, MADEIRA, False, pts, 3)
        pygame.draw.lines(c, MADEIRA2, False, [(cx + lado * 42, 44), (cx + lado * 47, 36), (cx + lado * 47, 26)], 4)
        pygame.draw.line(c, MADEIRA2, (cx + lado * 40, 26), (cx + lado * 34, 14), 3)
    pygame.draw.ellipse(c, OSSO2, (cx - 41, 54, 82, 70))                                               # a casca do ovo
    pygame.draw.ellipse(c, OSSO, (cx - 41, 52, 72, 64))
    pygame.draw.polygon(c, K, [(cx - 22, 72), (cx - 12, 66), (cx - 4, 72), (cx + 8, 64), (cx + 20, 72), (cx + 26, 88), (cx + 12, 84), (cx + 2, 92), (cx - 12, 84), (cx - 24, 88)])
    pygame.draw.polygon(c, FOGO, [(cx - 16, 86), (cx - 10, 72 - q % 2), (cx - 3, 80), (cx + 5, 70 + q % 2), (cx + 13, 82), (cx + 19, 86), (cx + 2, 90)])
    pygame.draw.polygon(c, OURO, [(cx - 7, 86), (cx - 3, 80), (cx + 2, 76 + q % 3), (cx + 7, 86)])
    pygame.draw.polygon(c, MADEIRA2, [(cx - 16, 92), (cx + 18, 92), (cx + 22, 100), (cx - 20, 100)])   # a mesa da taberna, lá dentro
    pygame.draw.ellipse(c, OSSO2, (cx - 26, 18, 52, 50))                                               # o rosto comprido
    pygame.draw.ellipse(c, OSSO, (cx - 26, 17, 46, 47))
    pygame.draw.ellipse(c, OSSO2, (cx + 2, 40, 16, 16))                                                # a bochecha funda
    pygame.draw.ellipse(c, OSSO, (cx + 1, 38, 12, 14))
    ey = 37
    for ex in (cx - 17, cx + 3):                       # olha para trás, por cima do ombro: íris no canto do olho
        if humor == "ri":
            pygame.draw.arc(c, K, (ex - 6, ey - 5, 12, 10), 0.2, 2.9, 3)
        else:
            pygame.draw.ellipse(c, (252, 248, 236), (ex - 6, ey - 5, 12, 10))
            pygame.draw.circle(c, K, (ex - 3, ey), 3)
            c.set_at((ex - 4, ey - 1), (255, 255, 255))
        pygame.draw.line(c, K, (ex - 7, ey - 8), (ex + 6, ey - 6 if humor != "triste" else ey - 10), 2)
    pygame.draw.lines(c, OSSO2, False, [(cx - 7, ey - 2), (cx - 11, ey + 11), (cx - 5, ey + 12)], 2)   # o nariz fino
    if humor == "ri":                                  # a gargalhada torta
        pygame.draw.ellipse(c, K, (cx - 21, 52, 28, 14))
        pygame.draw.ellipse(c, VERMELHO2, (cx - 19, 54, 24, 10))
        for k in range(4):
            c.fill(OSSO, (cx - 17 + k * 6, 54, 4, 3))
    elif humor == "triste":
        pygame.draw.arc(c, K, (cx - 18, 55, 22, 10), 0.4, 2.7, 3)
    else:                                              # o meio sorriso cansado, puxado para um lado só
        pygame.draw.lines(c, K, False, [(cx - 18, 55), (cx - 8, 57), (cx + 2, 55), (cx + 8, 50)], 3)
    pygame.draw.ellipse(c, ROSA2, (cx - 40, 13, 80, 15))                                               # o disco rosa
    pygame.draw.ellipse(c, ROSA, (cx - 40, 11, 76, 13))
    sopro = q % 3                                      # a gaita de foles, que enche e esvazia sozinha
    pygame.draw.line(c, MADEIRA2, (cx + 3, 5), (cx + 16, 0), 3)
    pygame.draw.ellipse(c, VERMELHO2, (cx - 18 - sopro, 2 - sopro // 2, 30 + sopro * 2, 13 + sopro))
    pygame.draw.ellipse(c, (222, 104, 126), (cx - 18 - sopro, 2 - sopro // 2, 26 + sopro, 10 + sopro))
    c.fill(ROSA3, (cx - 12, 4, 5, 1))


class Dupla(_Dupla):
    """A mesma dupla de quixote.Dupla, com outros desenhos."""
    pinta_esq = staticmethod(_fonte)
    pinta_dir = staticmethod(_homem_arvore)


# --------------------------------------------------------------------- o peixe de pernas (no lugar do pet)

def _peixe(c, w, h, pose, q, fecha, quadro):
    pulo = 3 if pose in ("pulo", "bote") else 0
    b = h - 5 - pulo
    if pose == "bote":
        q = 0
    corpo, corpo2, barriga = (96, 164, 170), (58, 112, 136), (226, 224, 192)
    for lado, dq in ((-1, q), (1, -q)):                # as duas pernas de gente que saíram da água
        x = 12 + lado * 3
        fx = x + dq * 2
        pygame.draw.line(c, (216, 170, 136), (x, b), (fx, h - 2 - pulo), 2)
        c.fill((216, 170, 136), (fx, h - 2 - pulo, 3, 2))
    arrepia = pose == "susto"
    pygame.draw.polygon(c, corpo2, [(5, b - 7), (0, b - 13 - q), (0, b - 1 + q)])   # a cauda abana
    pygame.draw.ellipse(c, corpo2, (3, b - 13, 21, 14))
    pygame.draw.ellipse(c, corpo, (3, b - 14, 19, 12))
    pygame.draw.ellipse(c, barriga, (8, b - 7, 13, 6))
    for k in range(3):                                 # as escamas
        pygame.draw.arc(c, corpo2, (8 + k * 4, b - 13, 5, 4), 3.2, 6.2)
    if arrepia:
        for k in range(4):
            pygame.draw.line(c, corpo2, (7 + k * 4, b - 14), (6 + k * 4, b - 18))
    else:                                              # a barbatana de cima
        pygame.draw.polygon(c, corpo2, [(10, b - 13), (14, b - 18), (17, b - 13)])
    ex, ey = 18, b - 10
    if fecha or pose in ("feliz", "boceja", "espreguica"):
        c.fill(K, (ex - 1, ey, 3, 1))
    elif arrepia:
        pygame.draw.circle(c, (255, 255, 255), (ex, ey), 3)
        c.set_at((ex, ey), K)
    else:
        pygame.draw.circle(c, (255, 255, 255), (ex, ey), 2)
        c.fill(K, (ex, ey - 1, 2, 2))
    if pose in ("feliz", "boceja", "espreguica") or arrepia:
        c.fill(VERMELHO2, (20, b - 6, 4, 3))
    elif pose == "lambe":
        c.fill(VERMELHO, (20, b - 5, 4, 1))
    else:
        c.fill(K, (21, b - 5, 3, 1))
    if pose == "bote":
        pygame.draw.line(c, (255, 255, 255), (w - 4, b - 11), (w - 1, b - 13))
        pygame.draw.line(c, (255, 255, 255), (w - 4, b - 6), (w - 1, b - 4))


def peixe(pose="parado", quadro=0, virado=1):
    """O bicho que sai da água no painel do Paraíso (pivô centro-baixo; poses do pet)."""
    if pose == "parado":
        quadro %= 180
    elif pose == "andar":
        quadro %= 12
    elif pose in ("feliz", "susto", "lambe", "boceja", "espreguica"):
        quadro %= 24
    else:
        quadro = 0
    ch = (pose, quadro, virado < 0)
    if ch not in _CACHE:
        q = (quadro % 3) - 1 if pose == "andar" else 0
        fecha = pose == "parado" and quadro % 90 in (84, 85, 88, 89)
        pulinho = pose == "feliz" and quadro % 8 < 4
        spr = _sprite(("j_peixe", pose, quadro), 28, 24,
                      lambda c: _peixe(c, 28, 24 - (2 if pulinho else 0), pose, q, fecha, quadro), K)
        _CACHE[ch] = pygame.transform.flip(spr, True, False) if virado < 0 else spr
    return _CACHE[ch]


pet = peixe
