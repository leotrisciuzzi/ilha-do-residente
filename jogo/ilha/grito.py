"""Elenco da tela conceito de O Grito (Edvard Munch, 1893; obra em domínio público): figurino.ELENCO.

Como em quixote.py, só muda o desenho: hitbox, física e comportamento continuam os do inimigo original.
Cada inimigo vira uma figura da obra de Munch, em cores doentes e sem contorno de desenho animado alegre:
  fantasma  — bicho-questão: um rosto que grita, com a placa da questão
  mascara   — o chefe: o grito enorme, de capuz, com faixa vermelha e braços
  passante  — os germes rasteiros: a multidão pálida de chapéu de "Ansiedade" (1894)
  angustia  — quem tem espinho (não se pisa): o redemoinho preto do fiorde, cheio de pontas
  vampiro   — quem voa: a mulher de cabelo vermelho de "Vampiro" (1895)
  relogio   — caixas e comprimidos: o relógio sem ponteiros de "Entre o Relógio e a Cama" (1940-43)
  fumante   — quem cospe de longe: "Autorretrato com Cigarro" (1895); o cuspe vira fumaça
  esqueleto — os monstros fortes: "Autorretrato com Braço de Esqueleto" (1895)
  morte     — o feiticeiro: a Morte encapuzada, que atravessa a obra dele
Os dois homens de cartola da ponte ficam no lugar do pet; no fundo, o Sol (mural de 1911, Universidade de Oslo) torce
pelo jogador e a Caveira zomba do erro, no lugar do Oni e do Daidara."""
import math

import pygame

from .quixote import Dupla as _Dupla, _anda, _barra, _colar, _par, _sprite

K = (18, 16, 30)
PALIDO, PALIDO2 = (228, 214, 150), (178, 164, 116)
ESCURO, ESCURO2, CLARO = (42, 44, 72), (24, 24, 44), (84, 80, 110)
SANGUE, FOGO, OURO = (176, 36, 44), (232, 104, 44), (248, 196, 84)
OSSO, OSSO2 = (236, 228, 200), (176, 166, 144)
SRC = pygame.SRCALPHA

FORMA = {"BichoQuestao": "fantasma", "Gigante": "mascara",
         "Bacilo": "passante", "Estafilococo": "passante", "Estreptococo": "passante", "Ameba": "passante",
         "Globulo": "passante", "Carrapato": "passante", "Tatu": "passante",
         "Virus": "angustia", "Fago": "angustia", "Candida": "angustia",
         "Aedes": "vampiro", "Morcego": "vampiro", "Mosca": "vampiro", "AguaViva": "vampiro",
         "Caixa": "relogio", "Comprimido": "relogio", "Lombriga": "relogio", "Musgo": "relogio",
         "Cuspidor": "fumante", "Chifrudo": "esqueleto", "Louva": "esqueleto", "Colosso": "esqueleto",
         "Feiticeiro": "morte"}
FUMACAS = ("Cuspe", "Seringa", "Esporo")      # projéteis: a fumaça do cigarro


def forma_de(e):
    """Forma do inimigo, ou None para quem fica como está (ondas, orbes)."""
    nome = type(e).__name__
    if nome in FUMACAS:
        return "fumaca"
    if nome in ("BichoQuestao", "Gigante"):
        return FORMA[nome]
    if getattr(e, "espinhento", False):
        return "angustia"
    if nome in FORMA:
        return FORMA[nome]
    return "fantasma" if getattr(e, "boneco", None) is not None else None


# --------------------------------------------------------------------- peças do rosto

def _rosto_grito(c, cx, cy, r, mao=True, cor=PALIDO, sombra=PALIDO2, boca_alta=1.0):
    """Crânio pálido em pera, órbitas fundas, boca em O e, se couber, as mãos nas bochechas."""
    pygame.draw.ellipse(c, cor, (cx - r, cy - r * 1.2, r * 2, r * 2.5))
    pygame.draw.ellipse(c, sombra, (cx + r * 0.25, cy - r * 0.9, r * 0.75, r * 2.0))
    pygame.draw.ellipse(c, cor, (cx - r * 0.2, cy - r * 1.1, r * 0.9, r * 2.3))
    ox, orb = max(1, int(r * 0.42)), max(1, int(r * 0.28))
    for lado in (-1, 1):
        pygame.draw.circle(c, K, (int(cx + lado * ox), int(cy - r * 0.25)), orb)
    bw, bh = max(2, int(r * 0.55)), max(3, int(r * 0.85 * boca_alta))
    pygame.draw.ellipse(c, K, (cx - bw // 2, cy + r * 0.25, bw, bh))
    if mao:
        for lado in (-1, 1):
            hx = cx + lado * (r + max(1, r * 0.1))
            pygame.draw.line(c, cor, (hx, cy - r * 0.1), (hx - lado, cy + r * 0.9), max(2, int(r * 0.4)))


def _fantasma(c, w, h, q, bravo, chefe):
    cx = w // 2
    r = max(4, int(h * 0.2))
    cy = int(h * 0.3)
    manto, manto2 = (ESCURO, ESCURO2) if not bravo else (SANGUE, (110, 24, 40))
    ond = 2 if q % 2 else -2
    pts = [(cx - r * 0.8, cy + r), (cx + r * 0.8, cy + r), (cx + w * 0.34, h - 3)]
    n = 5
    for k in range(n + 1):                             # a barra ondula, como as linhas do quadro
        fx = 1 - k / n
        pts.append((cx - w * 0.34 + w * 0.68 * fx, h - 2 + (ond if k % 2 else -ond) * 0.7))
    pts.append((cx - w * 0.34, h - 3))
    pygame.draw.polygon(c, manto, pts)
    pygame.draw.polygon(c, manto2, [(cx + 1, cy + r), (cx + r * 0.8, cy + r), (cx + w * 0.34, h - 3), (cx + 1, h - 3)])
    pygame.draw.line(c, CLARO, (cx - r * 0.3, cy + r + 2), (cx - w * 0.2 + ond, h - 5))
    if chefe:                                          # capuz e faixa de sangue
        pygame.draw.ellipse(c, ESCURO2, (cx - r * 1.45, cy - r * 1.6, r * 2.9, r * 3.2))
    _rosto_grito(c, cx, cy, r, boca_alta=1.25 if bravo or chefe else 1.0)
    if chefe:
        c.fill(SANGUE, (cx - r, int(cy - r * 0.85), r * 2, max(2, r // 3)))


def desenhar_fantasma(s, cam, e, chefe=False):
    if chefe and getattr(e, "invuln", 0) and e.invuln % 6 < 3:
        return
    w, h = _par(max(e.w * 1.4, 22)), _par(max(e.h * 2.1, 26))
    bravo = bool(getattr(e, "bravo", 0))
    q = (getattr(e, "t", 0) // 8) % 2
    chave = ("g_fantasma", w, h, q, bravo, chefe)
    spr = _sprite(chave, w, h, lambda c: _fantasma(c, w, h, q, bravo, chefe), K)
    x, y = _colar(s, cam, e, spr, chave, dy=-int(abs(math.sin(e.t * 0.1)) * 2))
    virado = getattr(e, "virado", 1) or 1
    if chefe:                                          # braços compridos e tortos, batendo no ar
        cx = x + w // 2
        a = math.sin(e.t * 0.1) * 6
        for lado in (-1, 1):
            ax, ay = cx + lado * int(w * 0.24), y + int(h * 0.6)
            bx, by = ax + lado * int(w * 0.34), ay - int(h * 0.12) + int(a * lado)
            pygame.draw.line(s, K, (ax, ay), (bx, by), 5)
            pygame.draw.line(s, ESCURO, (ax, ay), (bx, by), 3)
            pygame.draw.circle(s, K, (bx, by), 4)
            pygame.draw.circle(s, PALIDO, (bx, by), 3)
    placa = getattr(getattr(e, "boneco", None), "placa", None)
    if placa is not None:                              # a placa da questão, sempre legível
        s.blit(placa, (x + w // 2 - (w // 2 + 3) * virado - placa.get_width() // 2, y + int(math.sin(e.t * 0.1) * 1.5)))


# --------------------------------------------------------------------- a multidão de "Ansiedade"

def _passante(c, w, h, q, seed):
    cx = w // 2
    casaco = (ESCURO, (58, 40, 62), (34, 50, 66))[seed % 3]
    y_perna = int(h * 0.76)
    for lado in (-1, 1):
        d = lado * q
        c.fill(ESCURO2, (cx + lado * 2 - 1 + d, y_perna, 2, h - y_perna))
    c.fill(casaco, (cx - max(3, w // 4), int(h * 0.42), max(6, w // 2), y_perna - int(h * 0.42)))
    r = max(3, int(h * 0.2))
    pygame.draw.ellipse(c, PALIDO, (cx - r, int(h * 0.1), r * 2, int(r * 2.2)))
    c.set_at((cx - r // 2, int(h * 0.1) + r), K)       # olhos de quem encara: dois pontos e nenhuma expressão
    c.set_at((cx + r // 2, int(h * 0.1) + r), K)
    c.fill(K, (cx - 1, int(h * 0.1) + int(r * 1.6), 2, 1))
    c.fill(K, (cx - r - 2, int(h * 0.12), r * 2 + 4, 2))        # chapéu de aba
    c.fill(K, (cx - r + 1, 0, r * 2 - 2, int(h * 0.12) + 1))


def desenhar_passante(s, cam, e):
    w, h = _par(max(e.w * 1.3, 14)), _par(max(e.h * 2.2, 22))
    q = ((e.t // 6) % 3 - 1) if _anda(e) else 0
    seed = sum(map(ord, type(e).__name__))
    chave = ("g_passante", w, h, q, seed % 3)
    spr = _sprite(chave, w, h, lambda c: _passante(c, w, h, q, seed), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o redemoinho com pontas

def _angustia(c, w, h, q):
    cx, cy = w // 2, h // 2 + 1
    r = min(w, h) * 0.34
    for k in range(9):                                 # pontas: é o aviso de que não se pisa
        a = k * 2 * math.pi / 9 + q * 0.35
        ax, ay = cx + math.cos(a) * r * 1.5, cy + math.sin(a) * r * 1.5
        pygame.draw.polygon(c, FOGO, [(cx + math.cos(a - 0.3) * r, cy + math.sin(a - 0.3) * r), (ax, ay),
                                      (cx + math.cos(a + 0.3) * r, cy + math.sin(a + 0.3) * r)])
    pygame.draw.circle(c, ESCURO2, (cx, cy), int(r))
    for k in range(28):                                # o traço em espiral do fiorde
        a = k * 0.5 + q * 0.7
        rr = r * k / 30
        c.set_at((int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr)), (92, 112, 150))
    for lado in (-1, 1):
        c.fill((250, 220, 110), (cx + lado * int(r * 0.4) - 1, cy - 1, 2, 2))


def desenhar_angustia(s, cam, e):
    w = h = _par(max(e.w, e.h) * 1.9)
    q = (e.t // 5) % 6
    chave = ("g_angustia", w, q)
    spr = _sprite(chave, w, h, lambda c: _angustia(c, w, h, q), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- Vampiro

def _vampiro(c, w, h, q):
    cx, cy = int(w * 0.56), int(h * 0.42)
    asa = (-0.34, 0.0, 0.34, 0.0)[q]
    capa = ESCURO2
    pygame.draw.polygon(c, capa, [(cx - 2, cy), (cx - w * 0.5, cy - h * asa), (cx - w * 0.3, cy + h * 0.42), (cx + 2, cy + h * 0.5)])
    pygame.draw.polygon(c, capa, [(cx + 2, cy), (cx + w * 0.42, cy - h * asa), (cx + w * 0.3, cy + h * 0.38), (cx, cy + h * 0.5)])
    r = max(3, int(h * 0.22))
    for k in range(5):                                 # o cabelo vermelho escorrendo, como no quadro
        x0 = cx - r + k * r // 2
        comp = h * (0.34 + 0.08 * ((k + q) % 3))
        pygame.draw.line(c, SANGUE, (x0, cy - r), (x0 - 2 - q, cy + comp), 2)
    pygame.draw.ellipse(c, PALIDO, (cx - r, cy - r, r * 2, int(r * 2.2)))
    pygame.draw.ellipse(c, (200, 48, 52), (cx - r - 1, cy - r - 1, r * 2 + 2, r))
    c.fill(K, (cx - r // 2 - 1, cy, 2, 2))
    c.fill(K, (cx + r // 2, cy, 2, 2))
    c.fill(SANGUE, (cx - 1, cy + r // 2 + 2, 3, 1))


def desenhar_vampiro(s, cam, e):
    w, h = _par(max(e.w * 1.9, 24)), _par(max(e.h * 2.3, 22))
    q = (e.t // 5) % 4
    chave = ("g_vampiro", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _vampiro(c, w, h, q), K)
    _colar(s, cam, e, spr, chave, voa=True)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o relógio sem ponteiros

def _relogio(c, w, h, q):
    mad, mad2 = (112, 60, 42), (74, 38, 34)
    cx = w // 2
    tw = max(4, int(w * 0.38))
    c.fill(mad, (cx - tw, 3, tw * 2, h - 5))
    c.fill(mad2, (cx + tw // 3, 3, tw - tw // 3, h - 5))
    pygame.draw.polygon(c, mad2, [(cx - tw - 1, 4), (cx, 0), (cx + tw + 1, 4)])
    r = max(3, int(tw * 0.78))
    fy = 4 + r + 1
    pygame.draw.circle(c, PALIDO, (cx, fy), r)
    pygame.draw.circle(c, K, (cx, fy), 1)              # o mostrador vazio: o relógio do quadro não tem ponteiros
    for k in range(4):
        a = k * math.pi / 2
        c.set_at((int(cx + math.cos(a) * (r - 1)), int(fy + math.sin(a) * (r - 1))), K)
    yb = fy + r + 2
    if yb + 6 < h:                                     # a portinha com o pêndulo
        c.fill(K, (cx - tw + 2, yb, tw * 2 - 4, h - yb - 4))
        px = cx + (-2 if q else 2)
        pygame.draw.line(c, OURO, (cx, yb), (px, h - 8))
        pygame.draw.circle(c, OURO, (px, h - 7), 2)
    for lado in (-1, 1):                               # pés
        c.fill(K, (cx + lado * (tw - 1) - 1, h - 2, 3, 2))


def desenhar_relogio(s, cam, e):
    w, h = _par(max(e.w * 1.2, 14)), _par(max(e.h * 2.0, 24))
    q = (getattr(e, "t", 0) // 14) % 2
    chave = ("g_relogio", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _relogio(c, w, h, q), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


# --------------------------------------------------------------------- o fumante e o esqueleto

def _pernas(c, cx, y, h, q, cor):
    for lado in (-1, 1):
        d = lado * q
        c.fill(cor, (cx + lado * 2 - 1 + d, y, 3, h - y))


def _fumante(c, w, h, q, mira):
    cx = w // 2 - 2
    _pernas(c, cx, int(h * 0.68), h, 0, ESCURO2)
    c.fill((46, 52, 84), (cx - 6, int(h * 0.3), 13, int(h * 0.4)))
    c.fill(PALIDO2, (cx - 1, int(h * 0.3), 3, int(h * 0.2)))
    r = max(3, int(h * 0.15))
    pygame.draw.ellipse(c, PALIDO, (cx - r + 1, int(h * 0.05), r * 2, int(r * 2.2)))
    c.fill(ESCURO2, (cx - r + 1, int(h * 0.05), r * 2, max(1, r // 2)))
    c.set_at((cx + r // 2 + 1, int(h * 0.05) + r), K)
    c.fill(PALIDO, (cx + 6, int(h * 0.42), 3, 3))      # a mão erguida com o cigarro
    c.fill((240, 240, 232), (cx + 8, int(h * 0.38), 1, 4))
    c.set_at((cx + 8, int(h * 0.37)), FOGO if q % 2 or mira else SANGUE)


def _esqueleto(c, w, h, q, bravo):
    cx = w // 2 - 1
    _pernas(c, cx, int(h * 0.7), h, q, ESCURO2)
    c.fill(ESCURO, (cx - int(w * 0.2), int(h * 0.28), int(w * 0.4), int(h * 0.44)))
    for k in range(4):                                 # as costelas à mostra
        yy = int(h * (0.33 + k * 0.07))
        c.fill(OSSO, (cx - int(w * 0.11), yy, int(w * 0.22), 1))
    r = max(4, int(h * 0.15))
    pygame.draw.circle(c, OSSO, (cx + 1, int(h * 0.15)), r)
    for lado in (-1, 1):
        c.fill(K, (cx + 1 + lado * max(1, r // 2) - 1, int(h * 0.12), max(2, r // 2), max(2, r // 2)))
    c.fill(K, (cx - 1, int(h * 0.22), 4, 1))
    ax, ay = cx + int(w * 0.2), int(h * 0.34)          # o braço de esqueleto, que no quadro corre na borda
    bx, by = ax + int(w * 0.2), ay + (int(h * 0.2) if not bravo else -int(h * 0.2))
    pygame.draw.line(c, OSSO, (ax, ay), (bx, by), 2)
    pygame.draw.circle(c, OSSO, (bx, by), 2)
    pygame.draw.line(c, OSSO2, (cx - int(w * 0.2), ay), (cx - int(w * 0.32), ay + int(h * 0.26)), 2)


def _morte(c, w, h, q):
    cx = w // 2 - 1
    pygame.draw.polygon(c, ESCURO2, [(cx - 5, int(h * 0.2)), (cx + 6, int(h * 0.2)), (cx + int(w * 0.28), h - 2), (cx - int(w * 0.28), h - 2)])
    pygame.draw.ellipse(c, ESCURO2, (cx - int(w * 0.24), 0, int(w * 0.5), int(h * 0.42)))
    r = max(5, int(h * 0.16))                          # a caveira, maior que o capuz deixaria: tem de se ler
    yc = int(h * 0.24)
    pygame.draw.circle(c, OSSO, (cx + 1, yc), r)
    for lado in (-1, 1):
        c.fill(K, (cx + 1 + lado * (r // 2) - 1, yc - 1, 2, 2))
    c.fill(K, (cx, yc + r // 2 + 1, 3, 1))
    ex = cx + int(w * 0.32)                            # a foice
    c.fill((116, 86, 60), (ex, int(h * 0.12), 2, int(h * 0.84)))
    pygame.draw.arc(c, (206, 210, 220), (ex - int(w * 0.34), int(h * 0.02), int(w * 0.4), int(h * 0.3)), 0.3, 2.4, 2)
    if q:
        c.set_at((ex - 6, int(h * 0.06)), (255, 255, 255))


def desenhar_fumante(s, cam, e):
    w, h = _par(max(e.w * 1.8, 24)), _par(max(e.h * 1.5, 26))
    q = (e.t // 12) % 2
    mira = getattr(e, "estado", "") == "mira"
    chave = ("g_fumante", w, h, q, mira)
    spr = _sprite(chave, w, h, lambda c: _fumante(c, w, h, q, mira), K)
    x, y = _colar(s, cam, e, spr, chave)
    virado = getattr(e, "virado", 1) or 1
    fx = x + (w // 2 + 6 if virado > 0 else w // 2 - 7)
    for k in range(3):                                 # a fumaça sobe em curva
        f = (e.t + k * 16) % 48
        pygame.draw.circle(s, (150, 146, 156), (fx + int(math.sin(f * 0.2) * 3), y + int(h * 0.36) - f // 3), 1 + f // 20)
    _barra(s, cam, e)


def desenhar_esqueleto(s, cam, e):
    w, h = _par(max(e.w * 1.6, 26)), _par(max(e.h * 1.3, 30))
    q = ((e.t // 7) % 3 - 1) if _anda(e) else 0
    bravo = getattr(e, "estado", "") in ("mira", "grito", "ergue", "prestes", "incha")
    chave = ("g_esqueleto", w, h, q, bravo)
    spr = _sprite(chave, w, h, lambda c: _esqueleto(c, w, h, q, bravo), K)
    _colar(s, cam, e, spr, chave)
    _barra(s, cam, e)


def desenhar_morte(s, cam, e):
    w, h = _par(max(e.w * 1.8, 26)), _par(max(e.h * 1.4, 34))
    q = (e.t // 10) % 2
    chave = ("g_morte", w, h, q)
    spr = _sprite(chave, w, h, lambda c: _morte(c, w, h, q), K)
    _colar(s, cam, e, spr, chave, dy=int(math.sin(e.t * 0.05) * 2))
    _barra(s, cam, e)


def desenhar_fumaca(s, cam, e):
    x, y = int(e.x + e.w / 2 - cam[0]), int(e.y + e.h / 2 - cam[1])
    pygame.draw.circle(s, K, (x, y), 4)
    pygame.draw.circle(s, (170, 166, 176), (x, y), 3)
    pygame.draw.circle(s, (222, 218, 224), (x - 1, y - 1), 1)


_DESENHOS = {"fantasma": desenhar_fantasma, "mascara": lambda s, cam, e: desenhar_fantasma(s, cam, e, True),
             "passante": desenhar_passante, "angustia": desenhar_angustia, "vampiro": desenhar_vampiro,
             "relogio": desenhar_relogio, "fumante": desenhar_fumante, "esqueleto": desenhar_esqueleto,
             "morte": desenhar_morte, "fumaca": desenhar_fumaca}


def desenhar(s, cam, e):
    """Desenha o inimigo como figura de Munch. False = esse aí fica com o desenho de sempre."""
    forma = forma_de(e)
    if forma is None:
        return False
    _DESENHOS[forma](s, cam, e)
    return True


# --------------------------------------------------------------------- os gigantes do fundo: o Sol e a Caveira

GW, GH = 96, 108


def _sol(c, humor, fecha):
    cx, cy = GW // 2, 52
    alcance = 50 if humor == "ri" else 34 if humor == "triste" else 44
    cores = ((248, 214, 96), (246, 246, 214), (120, 188, 150), (232, 120, 60))
    for k in range(24):                                # os raios retos e coloridos do mural de Oslo
        a = k * 2 * math.pi / 24
        fim = alcance * (1.0 if k % 2 == 0 else 0.76)
        pygame.draw.line(c, cores[k % 4], (cx + math.cos(a) * 18, cy + math.sin(a) * 18),
                         (cx + math.cos(a) * fim, cy + math.sin(a) * fim), 3)
    pygame.draw.circle(c, (252, 244, 196), (cx, cy), 21)
    pygame.draw.circle(c, (250, 220, 120), (cx + 3, cy + 3), 17)
    pygame.draw.circle(c, (252, 244, 196), (cx - 1, cy - 1), 15)
    for lado in (-1, 1):
        ex = cx + lado * 8
        if fecha or humor == "ri":
            pygame.draw.arc(c, K, (ex - 4, cy - 7, 8, 7), 0.2, 2.9, 2)
        else:
            pygame.draw.circle(c, K, (ex, cy - 3), 2)
    if humor == "ri":
        pygame.draw.ellipse(c, SANGUE, (cx - 7, cy + 3, 14, 9))
    elif humor == "triste":
        pygame.draw.arc(c, K, (cx - 6, cy + 5, 12, 8), 0.4, 2.7, 2)
    else:
        pygame.draw.arc(c, K, (cx - 7, cy + 1, 14, 9), 3.4, 6.0, 2)


def _caveira(c, q, humor):
    cx = GW // 2
    pygame.draw.polygon(c, ESCURO2, [(cx - 44, GH), (cx - 26, 56), (cx + 26, 56), (cx + 44, GH)])      # capa preta
    pygame.draw.ellipse(c, OSSO, (cx - 30, 4, 60, 58))
    pygame.draw.ellipse(c, OSSO2, (cx + 8, 12, 22, 44))
    pygame.draw.ellipse(c, OSSO, (cx + 4, 8, 22, 50))
    for lado in (-1, 1):
        ex = cx + lado * 13
        if humor == "ri":                              # gargalhada: as órbitas apertam
            pygame.draw.arc(c, K, (ex - 8, 22, 16, 14), 0.2, 2.9, 4)
        else:
            pygame.draw.circle(c, K, (ex, 30), 9)
            pygame.draw.circle(c, SANGUE, (ex + (q - 2) // 2, 31), 2)
    pygame.draw.polygon(c, K, [(cx, 40), (cx - 4, 49), (cx + 4, 49)])
    abre = 12 if humor == "ri" else 2 if humor == "triste" else 5     # o queixo desce na risada
    pygame.draw.ellipse(c, OSSO2, (cx - 20, 50, 40, 16 + abre))
    pygame.draw.ellipse(c, K, (cx - 16, 54, 32, 4 + abre))
    for k in range(-3, 4):
        c.fill(OSSO, (cx + k * 4 - 1, 53, 3, 3))


class Dupla(_Dupla):
    """A mesma dupla de quixote.Dupla, com outros desenhos."""
    pinta_esq = staticmethod(_sol)
    pinta_dir = staticmethod(_caveira)


# --------------------------------------------------------------------- os dois homens de cartola (no lugar do pet)

def _homem(c, x, base, q, chapeu_alto, cor=(26, 24, 40)):
    alt = 21
    c.fill(cor, (x - 3, base - alt + 7, 7, alt - 12))                 # sobretudo
    c.fill((14, 12, 24), (x + 1, base - alt + 7, 3, alt - 12))
    for lado in (-1, 1):
        d = lado * q
        c.fill(cor, (x + lado * 2 - 1 + d, base - 5, 2, 5))
    pygame.draw.circle(c, PALIDO2, (x, base - alt + 4), 3)
    c.set_at((x + 1, base - alt + 3), K)
    topo = base - alt - 1 - (4 if chapeu_alto else 0)                 # cartola: na alegria, sobe
    c.fill(cor, (x - 4, topo + 3, 9, 1))
    c.fill(cor, (x - 2, topo - 4, 5, 7))


def homens_de_cartola(pose="parado", quadro=0, virado=1):
    """Os dois vultos que seguem pela ponte, sem ligar para o grito (pivô centro-baixo; poses do pet)."""
    if pose == "parado":
        quadro = 0
    elif pose == "andar":
        quadro %= 12
    elif pose in ("feliz", "susto", "lambe", "boceja", "espreguica"):
        quadro %= 24
    else:
        quadro = 0
    ch = ("g_homens", pose, quadro, virado < 0)
    if ch not in _CACHE:
        q = (quadro % 3) - 1 if pose == "andar" else 0
        alto = pose == "feliz" and quadro % 8 < 4
        pulo = 2 if pose in ("pulo", "bote") else 0

        def pinta(c):
            _homem(c, 16, 28 - pulo, q, alto)
            _homem(c, 7, 28 - pulo, -q, alto, (34, 30, 52))
            if pose == "bote":                         # a bengala na frente: agora eles reagem
                pygame.draw.line(c, K, (18, 14), (25, 10), 2)
            elif pose == "lambe":                      # um acende o cigarro
                c.set_at((19, 8), FOGO)
            elif pose == "susto":
                c.fill(FOGO, (11, 0, 2, 3))
                c.set_at((11, 4), FOGO)

        spr = _sprite(("g_homens0", pose, quadro), 26, 30, pinta, (206, 124, 62))
        _CACHE[ch] = pygame.transform.flip(spr, True, False) if virado < 0 else spr
    return _CACHE[ch]


_CACHE = {}
pet = homens_de_cartola
