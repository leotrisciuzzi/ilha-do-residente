"""Cenários de fundo no traço de desenho animado (guia em assets/estilo/GUIA_DE_ESTILO.md): cor chapada, sombra dura
de um lado, contorno escuro da própria cor, formas que escorrem, riscos curtos de textura e pontinhos de brilho.

Cenários originais, cada um em três camadas com paralaxe (longe, meio, perto), como art.fundo:
  bosque     — árvores-gota (copa em tiras) e o Posto de Saúde-Cogumelo
  confeitado — morros de glacê e o Hospital Confeitado (andares de bolo, torres-cápsula)
  cosmo      — fitas lilás com borda ciano, pingos, brotos e planetas-bolha
  brasas     — céu em redemoinho, rochedos riscados e uma fileira de chamas
  gelo       — montanhas facetadas com capa de neve, morros de neve e pinheiros chapados
  mar        — água em faixas onduladas, areia com manchas, algas e rochas de coral
  grito      — fiorde preto-azulado em linhas que serpenteiam, barquinhos e a ponte de O Grito (Munch)
  lamancha   — planície dourada, aldeia branca, oliveiras e moinhos (as pás são desenhadas por quadro: ancoras())
  jardim     — O Jardim das Delícias (Bosch): montes azuis, torres rosas, morangos e pássaros enormes; extras por painel
  arraial    — o Bosque das Gotas em noite de festa: varais de bandeirinhas, barracas-cogumelo, fogueira e lanternas
O cenário segue o clima (CENA_DO_CLIMA); climas.Controle pede as camadas por camadas(...) quando troca o clima.
As camadas emendam na horizontal (tudo que passa da borda é desenhado de novo do outro lado)."""
import math
import random

import pygame

from .art import mix

SRC = pygame.SRCALPHA

CENA_DO_CLIMA = {
    "neve": "gelo", "aurora": "gelo",
    "reino": "confeitado", "cerejeira": "confeitado", "praia": "confeitado", "carnaval": "confeitado",
    "espaco": "cosmo", "cristal": "cosmo", "frota": "cosmo", "neon": "cosmo", "mar": "mar",
    "vulcao": "brasas", "colonia": "brasas", "runico": "brasas", "lamancha": "lamancha", "grito": "grito", "arraial": "arraial", "jardim": "jardim",
}
# quanto o tom do clima tinge as camadas: o bosque serve a qualquer clima e é tingido inteiro; os outros já foram
# pintados nas cores do clima deles e só pegam um pouco do tom
FORCA_TOM = {"bosque": 1.0, "confeitado": 0.4, "cosmo": 0.3, "brasas": 0.3, "gelo": 0.35, "mar": 0.3,
             "enfermaria": 0.12, "lamancha": 0.3, "grito": 0.2, "arraial": 0.4, "jardim": 0.0}
# mundos que se passam dentro do hospital (prefixo da chave da fase): o cenário é a enfermaria, seja qual for o clima
INTERIOR = {"cpn": "enfermaria", "crn": "enfermaria", "cgr": "enfermaria", "cvb": "enfermaria", "vm": "enfermaria"}


def interior_da_chave(chave):
    """'cpn-treino:x' / 'vm:3' → 'enfermaria'; mundos ao ar livre → None."""
    pref = (chave or "").split(":")[0].split("-")[0]
    return INTERIOR.get(pref)

BRILHO = (248, 240, 176)
_cache = {}


def cena_do_clima(cid):
    return CENA_DO_CLIMA.get(cid, "bosque")


# ------------------------------------------------------------------ pintura

def _escuro(cor, k=0.72, puxa=(40, 16, 40)):
    """Contorno: a própria cor bem escurecida, puxada para o roxo/marrom (nunca cinza)."""
    return mix(cor, puxa, k)


def _menos(m, outra, off=(0, 0)):
    r = m.copy()
    r.erase(outra, off)
    return r


def _miolo(m, n=1):
    """A silhueta sem as n camadas de pixels da borda."""
    e = m
    for _ in range(n):
        for o in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            e = e.overlap_mask(m, o)
    return e


def _por(s, m, cor):
    """Pinta os pixels marcados na máscara."""
    m.to_surface(s, setcolor=cor, unsetcolor=None)


def _pintar(forma, base, sombra=None, luz=None, contorno=None, desloc=(3, 2), luz_desloc=(2, 2), riscos=None,
            rng=None, n_riscos=0):
    """Pinta uma silhueta (Surface com alfa) no estilo: base chapada, sombra dura embaixo à direita (a silhueta
    deslocada), faixa de luz em cima à esquerda, riscos de textura e contorno de 1 px."""
    m = pygame.mask.from_surface(forma)
    w, h = forma.get_size()
    s = pygame.Surface((w, h), SRC)
    sombra = sombra or mix(base, (60, 20, 70), 0.3)
    _por(s, m, sombra)
    acesa = m.overlap_mask(m, (-desloc[0], -desloc[1]))           # acesa se o pixel embaixo à direita ainda é forma
    _por(s, acesa, base)
    if luz:
        borda_luz = _menos(acesa, m.overlap_mask(m, luz_desloc))   # perto da borda de cima/esquerda
        _por(s, borda_luz, luz)
    if riscos and n_riscos:
        _riscos(s, _miolo(m, 2), riscos, n_riscos, rng or random.Random(w * 31 + h), cor=mix(base, sombra, 0.75))
    _por(s, _menos(m, _miolo(m)), contorno or _escuro(base))
    return s


def _riscos(s, dentro, tipo, n, rng, cor):
    """Riscos curtos de textura, só dentro da máscara: 'casca' (verticais), 'sorriso' (︶) e 'barra' (//)."""
    w, h = s.get_size()
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        if tipo == "casca":
            pts = [(x, y + k) for k in range(rng.randint(2, 5))]
            if rng.random() < 0.4:
                pts.append((x + rng.choice((-1, 1)), y + len(pts)))
        elif tipo == "sorriso":
            L = rng.randint(3, 6)
            pts = [(x + k, y + (1 if 0 < k < L - 1 else 0)) for k in range(L)]
        else:
            pts = [(x + k // 2, y - k) for k in range(rng.randint(2, 4))]
        if all(0 <= px < w and 0 <= py < h and dentro.get_at((px, py)) for px, py in pts):
            for p in pts:
                s.set_at(p, cor)


def _emendar(dst, peca, x, y, largura):
    """Desenha a peça e a cópia do outro lado, para a camada emendar na rolagem."""
    for dx in (-largura, 0, largura):
        if -peca.get_width() < x + dx < largura:
            dst.blit(peca, (x + dx, y))


def _pontos_brilho(s, rng, n, y0, y1, cor=BRILHO):
    w = s.get_width()
    for _ in range(n):
        x, y = rng.randrange(w), rng.randint(int(y0), int(y1))
        r = rng.choice((1, 1, 1, 2, 2, 3))
        if r == 1:
            s.fill(cor, (x, y, 1, 1))
        else:
            pygame.draw.circle(s, cor, (x, y), r)
            if r == 3:
                pygame.draw.circle(s, mix(cor, (255, 255, 255), 0.6), (x - 1, y - 1), 1)


def _forma_vazia(w, h):
    return pygame.Surface((max(1, int(w)), max(1, int(h))), SRC)


# ------------------------------------------------------------------ peças comuns

def nuvem(w, rng, cor=(250, 250, 252), sombra=(222, 222, 242), contorno=(122, 140, 184)):
    """Nuvem de topo recortado e base reta, sombra lilás embaixo."""
    h = int(w * 0.48)
    f = _forma_vazia(w, h)
    base_y = h - 3
    n = max(3, w // 10)
    for i in range(n):
        cx = 4 + (w - 8) * i / (n - 1)
        meio = 1 - abs(i / (n - 1) - 0.5) * 2
        r = int(h * (0.22 + 0.28 * meio) * rng.uniform(0.85, 1.1))
        pygame.draw.circle(f, (255, 255, 255), (int(cx), base_y - r + 2), r)
    pygame.draw.rect(f, (255, 255, 255), (3, base_y - h // 5, w - 6, h // 5))
    pygame.draw.ellipse(f, (255, 255, 255), (0, base_y - h // 4, w, h // 4 + 3))
    return _pintar(f, cor, sombra, None, contorno, desloc=(0, max(2, h // 6)), riscos="sorriso", rng=rng,
                   n_riscos=w // 6)


def folhas_pontudas(n, rng, cor=(40, 104, 56), sombra=(16, 64, 40), contorno=(10, 34, 20)):
    """Tufo de folhas compridas e pontudas (base dos troncos e beira dos morros)."""
    w, h = 6 + n * 4, 16
    f = _forma_vazia(w, h)
    for i in range(n):
        x = 3 + i * 4 + rng.randint(-1, 1)
        alt = rng.randint(8, 15)
        inc = rng.uniform(-3, 3)
        pygame.draw.polygon(f, (255, 255, 255), [(x - 2, h), (x + inc - 1, h - alt * 0.6), (x + inc, h - alt),
                                                 (x + inc + 1, h - alt * 0.6), (x + 2, h)])
    return _pintar(f, cor, sombra, None, contorno, desloc=(1, 0))


def arvore_gota(alt, rng, pal):
    """Árvore-gota: copa redonda que escorre em tiras de comprimentos diferentes (uma camada escura atrás, mais
    comprida), tronco riscado com nó em amêndoa e raízes abertas."""
    cw = int(alt * rng.uniform(0.5, 0.62))
    w = cw + 10
    s = _forma_vazia(w, alt)
    copa_h = int(alt * rng.uniform(0.56, 0.64))
    cx = w // 2
    # tronco (atrás da copa)
    tw = max(4, cw // 4)
    topo_t = copa_h - 10
    t = _forma_vazia(w, alt)
    pygame.draw.polygon(t, (255, 255, 255), [(cx - tw // 2, topo_t), (cx + tw // 2, topo_t), (cx + tw // 2 + 1, alt - 5),
                                             (cx + tw + 2, alt), (cx - tw - 2, alt), (cx - tw // 2 - 1, alt - 5)])
    tronco = _pintar(t, pal["casca"], pal["casca_s"], None, pal["contorno"], desloc=(max(2, tw // 3), 0),
                     riscos="casca", rng=rng, n_riscos=tw * 3)
    m = pygame.mask.from_surface(t)
    for y in range(topo_t, topo_t + 8):                       # sombra da copa no alto do tronco, borda ondulada
        for x in range(w):
            if m.get_at((x, y)) and y < topo_t + 5 + 2 * math.sin(x * 0.9):
                tronco.set_at((x, y), pal["casca_s"])
    if alt > 40 and rng.random() < 0.7:                       # nó em amêndoa
        ny = rng.randint(copa_h + 1, max(copa_h + 2, alt - 9))
        nx = cx + rng.randint(-1, 1)
        pygame.draw.ellipse(tronco, pal["contorno"], (nx - 2, ny - 3, 4, 7))
        pygame.draw.ellipse(tronco, pal["casca_s"], (nx - 1, ny - 2, 2, 5))
    s.blit(tronco, (0, 0))
    # copa: cúpula + tiras que escorrem; atrás, uma camada escura de tiras mais compridas
    def silhueta(encolhe, extra):
        f = _forma_vazia(w, alt)
        x0, x1 = 5 + encolhe, 5 + cw - encolhe
        pygame.draw.ellipse(f, (255, 255, 255), (x0, 0, x1 - x0, int(copa_h * 0.7)))
        pygame.draw.rect(f, (255, 255, 255), (x0, int(copa_h * 0.3), x1 - x0, int(copa_h * 0.3)))
        tiras, x = [], x0
        while x < x1 - 1:
            lw = min(rng.randint(3, 5), x1 - x)
            fundo = min(alt - 8, int(copa_h * rng.uniform(0.78, 1.12)) + extra)
            pygame.draw.rect(f, (255, 255, 255), (x, int(copa_h * 0.5), lw, fundo - int(copa_h * 0.5)))
            pygame.draw.ellipse(f, (255, 255, 255), (x, fundo - 2, lw, 4))
            tiras.append((x, lw, fundo))
            x += lw
        return f, tiras
    f, tiras = silhueta(2, 7)
    s.blit(_pintar(f, pal["copa_f"], mix(pal["copa_f"], (0, 0, 0), 0.3), None, pal["contorno"], desloc=(2, 0),
                   riscos="casca", rng=rng, n_riscos=cw), (0, 0))
    f, tiras = silhueta(0, 0)
    frente = _pintar(f, pal["copa"], pal["copa_s"], pal["copa_l"], pal["contorno"],
                     desloc=(max(3, cw // 5), 2), luz_desloc=(max(3, cw // 7), 3), riscos="casca", rng=rng,
                     n_riscos=cw * 2)
    mf = pygame.mask.from_surface(f)
    for x, lw, fundo in tiras[1:]:                           # risco entre uma tira e outra (separa as tiras)
        topo = int(copa_h * rng.uniform(0.55, 0.75))
        for y in range(topo, fundo - 1):
            if mf.get_at((x, y)) and mf.get_at((x - 1, y)):
                frente.set_at((x, y), mix(pal["copa_s"], pal["contorno"], 0.45))
    s.blit(frente, (0, 0))
    if rng.random() < 0.35:                                   # frutinhas
        for _ in range(rng.randint(2, 4)):
            fx, fy = rng.randint(8, w - 8), rng.randint(int(copa_h * 0.3), int(copa_h * 0.7))
            if frente.get_at((fx, fy)).a:
                pygame.draw.circle(s, pal["fruta"], (fx, fy), 1)
                s.set_at((fx, fy + 1), _escuro(pal["fruta"]))
    return s


COPAS = [
    dict(copa=(88, 184, 64), copa_l=(136, 204, 96), copa_s=(56, 152, 64), copa_f=(0, 96, 48), fruta=(216, 64, 48)),
    dict(copa=(64, 176, 160), copa_l=(120, 210, 196), copa_s=(40, 136, 136), copa_f=(16, 80, 96), fruta=(248, 200, 72)),
    dict(copa=(232, 140, 176), copa_l=(248, 190, 214), copa_s=(196, 98, 150), copa_f=(128, 52, 104), fruta=(255, 240, 176)),
    dict(copa=(216, 168, 56), copa_l=(240, 208, 104), copa_s=(184, 120, 40), copa_f=(120, 64, 24), fruta=(216, 64, 48)),
]


def _pal_bosque(rng):
    p = dict(rng.choice(COPAS))
    p.update(casca=(168, 144, 64), casca_s=(96, 80, 32), contorno=(30, 34, 16))
    return p


def posto_cogumelo(rng):
    """Posto de Saúde-Cogumelo: caule de casa com janela redonda e porta, chapéu que pinga com a cruz vermelha e
    uma chaminé soltando fumaça."""
    w, h = 64, 66
    s = _forma_vazia(w, h)
    contorno = (48, 20, 30)
    f = _forma_vazia(w, h)
    pygame.draw.polygon(f, (255, 255, 255), [(18, 30), (46, 30), (49, h - 3), (15, h - 3)])
    pygame.draw.ellipse(f, (255, 255, 255), (12, h - 8, 40, 8))
    caule = _pintar(f, (248, 232, 200), (214, 182, 150), (255, 248, 230), contorno, desloc=(7, 0), riscos="casca",
                    rng=rng, n_riscos=20)
    s.blit(caule, (0, 0))
    pygame.draw.circle(s, contorno, (25, 42), 5)                        # janela redonda
    pygame.draw.circle(s, (72, 168, 208), (25, 42), 4)
    pygame.draw.line(s, contorno, (25, 38), (25, 46))
    pygame.draw.line(s, contorno, (21, 42), (29, 42))
    s.set_at((23, 40), (200, 236, 250))
    pygame.draw.rect(s, contorno, (34, h - 22, 11, 18), border_top_left_radius=5, border_top_right_radius=5)
    pygame.draw.rect(s, (150, 72, 52), (35, h - 21, 9, 17), border_top_left_radius=4, border_top_right_radius=4)
    s.fill((248, 200, 72), (42, h - 12, 1, 2))
    s.fill(contorno, (8, h - 4, 48, 1))
    # chaminé + fumaça
    pygame.draw.rect(s, contorno, (43, 3, 7, 12))
    pygame.draw.rect(s, (200, 120, 96), (44, 4, 5, 10))
    for i, (fx, fy, r) in enumerate(((48, 1, 2), (52, -3, 3))):
        if fy - r >= 0:
            pygame.draw.circle(s, (240, 240, 248), (fx, fy), r)
    # chapéu
    c = _forma_vazia(w, h)
    pygame.draw.ellipse(c, (255, 255, 255), (2, 4, w - 4, 34))
    pygame.draw.rect(c, (255, 255, 255), (2, 20, w - 4, 10))
    x = 3
    while x < w - 5:
        lw = rng.randint(3, 6)
        pygame.draw.circle(c, (255, 255, 255), (x + lw // 2, 30 + rng.randint(0, 4)), lw // 2 + 1)
        x += lw
    chapeu = _pintar(c, (232, 72, 80), (176, 40, 64), (250, 136, 128), contorno, desloc=(8, 3), luz_desloc=(5, 3),
                     riscos="sorriso", rng=rng, n_riscos=18)
    s.blit(chapeu, (0, 0))
    pygame.draw.circle(s, contorno, (w // 2, 19), 8)                    # selo com a cruz
    pygame.draw.circle(s, (250, 250, 246), (w // 2, 19), 7)
    s.fill((224, 48, 56), (w // 2 - 1, 14, 3, 11))
    s.fill((224, 48, 56), (w // 2 - 5, 18, 11, 3))
    for bx, by in ((12, 14), (50, 24), (16, 26)):                      # bolinhas claras do chapéu
        pygame.draw.circle(s, (250, 196, 190), (bx, by), 2)
    return s


def _manchas(s, rng, n, cor, clara, escura):
    """Chão de desenho: manchas elípticas chapadas (mais claras e mais escuras) e tiques de grama 'ıı', só por dentro
    do que já está pintado com a cor-base (não invade sombra nem contorno)."""
    w, h = s.get_size()
    for _ in range(n):
        ew, eh = rng.randint(8, 22), rng.randint(2, 5)
        x, y = rng.randrange(w - ew), rng.randrange(h - eh)
        tom = clara if rng.random() < 0.55 else escura
        e = pygame.Surface((ew, eh), SRC)
        pygame.draw.ellipse(e, (255, 255, 255), (0, 0, ew, eh))
        me = pygame.mask.from_surface(e)
        for yy in range(eh):
            for xx in range(ew):
                if me.get_at((xx, yy)) and s.get_at((x + xx, y + yy))[:3] == cor:
                    s.set_at((x + xx, y + yy), tom)
    for _ in range(n):
        x, y = rng.randrange(1, w - 3), rng.randrange(2, h)
        if all(s.get_at((x + k, y - j))[:3] == cor for k in (0, 2) for j in (0, 1)):
            for k in (0, 2):
                s.set_at((x + k, y), escura)
                s.set_at((x + k, y - 1), escura)


def _morros(largura, altura, rng, base_y, amp, cor, sombra, luz, contorno, riscos="sorriso", ondas=(2, 3, 5),
            tufos=None, manchas=0):
    """Faixa de morros que vai até o fim da tela; o perfil é periódico na largura (emenda na rolagem)."""
    M = 8                                                             # margem: sem contorno na borda da camada
    f = _forma_vazia(largura + 2 * M, altura + M)
    fases = [rng.uniform(0, 6.28) for _ in ondas]
    amps = [amp * k for k in (1.0, 0.5, 0.25)][:len(ondas)]
    pts = [(0, altura + M)]
    perfil = []
    for x in range(-M, largura + M + 1):
        y = base_y - sum(a * (0.5 + 0.5 * math.sin(2 * math.pi * n * x / largura + fz))
                         for a, n, fz in zip(amps, ondas, fases))
        if 0 <= x <= largura:
            perfil.append(int(y))
        pts.append((x + M, y))
    pts.append((largura + 2 * M, altura + M))
    pygame.draw.polygon(f, (255, 255, 255), pts)
    s = _pintar(f, cor, sombra, luz, contorno, desloc=(6, 5), luz_desloc=(3, 3), riscos=riscos, rng=rng,
                n_riscos=largura // 3).subsurface((M, 0, largura, altura)).copy()
    if manchas:
        _manchas(s, rng, manchas, tuple(cor), mix(cor, luz or (255, 255, 255), 0.45), mix(cor, sombra, 0.6))
    if tufos:
        x = rng.randint(0, 20)
        while x < largura:
            t = folhas_pontudas(rng.randint(2, 4), rng, *tufos)
            _emendar(s, t, x - t.get_width() // 2, perfil[min(largura, max(0, x))] - t.get_height() + 4, largura)
            x += rng.randint(18, 46)
    return s, perfil


def _banco_nuvens(s, rng, y, largura, escala=1.0, **cores):
    x = rng.randint(-30, 0)
    while x < largura:
        n = nuvem(int(rng.randint(30, 56) * escala), rng, **cores)
        _emendar(s, n, x, int(y - n.get_height() + rng.randint(-6, 6)), largura)
        x += int(n.get_width() * rng.uniform(0.55, 0.85))


# ------------------------------------------------------------------ cenários

def _bosque(L, H, rng):
    pal = _pal_bosque(rng)
    c0 = _forma_vazia(L, H)
    _banco_nuvens(c0, rng, H * 0.62, L, 0.9)
    longe, perfil = _morros(L, H, rng, H * 0.7, 26, (170, 214, 190), (140, 186, 176), None, (110, 150, 150),
                            riscos=None)
    x = rng.randint(0, 20)
    while x < L:                                                      # arvorezinhas distantes, chapadas
        a = rng.randint(12, 18)
        y = perfil[min(L, x)]
        pygame.draw.ellipse(longe, (120, 176, 150), (x - a // 3, y - a, a * 2 // 3, a))
        longe.fill((120, 176, 150), (x - 2, y - a // 2, a // 3 + 3, a // 2))
        x += rng.randint(14, 34)
    c0.blit(longe, (0, 0))
    # meio: morros verdes + árvores médias + o posto de saúde
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.8, 22, (120, 188, 100), (82, 150, 92), (164, 214, 126), (36, 70, 40),
                           tufos=((60, 128, 64), (32, 88, 52), (16, 48, 28)), manchas=26)
    posto_x = rng.randint(L // 5, L // 2)
    x = rng.randint(0, 30)
    while x < L:
        if abs(x - posto_x) > 46:
            a = rng.randint(34, 52)
            arv = (arvore_bolota if rng.random() < 0.45 else arvore_gota)(a, rng, pal)
            _emendar(c1, arv, x - arv.get_width() // 2, perfil[min(L, x)] - a + 4, L)
        x += rng.randint(40, 80)
    posto = posto_cogumelo(rng)
    _emendar(c1, posto, posto_x - posto.get_width() // 2, perfil[posto_x] - posto.get_height() + 6, L)
    c1.blit(meio, (0, 0))
    # perto: árvores grandes e morro escuro com folhas pontudas
    c2 = _forma_vazia(L, H)
    perto, perfil = _morros(L, H, rng, H * 0.95, 14, (64, 120, 72), (40, 88, 60), (92, 150, 90), (16, 40, 28),
                            tufos=((40, 104, 56), (16, 64, 40), (10, 34, 20)), manchas=30)
    x = rng.randint(10, 40)
    while x < L:
        a = rng.randint(64, 88)
        arv = (arvore_bolota if rng.random() < 0.4 else arvore_gota)(a, rng, pal)
        _emendar(c2, arv, x - arv.get_width() // 2, perfil[min(L, x)] - a + 6, L)
        x += rng.randint(90, 150)
    c2.blit(perto, (0, 0))
    return [c0, c1, c2]


def hospital_confeitado(rng):
    """Hospital Confeitado: três andares de bolo com glacê pingando e morangos, torres-cápsula de remédio com telhado
    em cone e bandeirola, domo lilás com a cruz e uma porta em arco."""
    w, h = 132, 112
    s = _forma_vazia(w, h)
    cont = (88, 28, 24)
    def andar(x, y, lw, lh, massa, glace):
        f = _forma_vazia(w, h)
        pygame.draw.rect(f, (255, 255, 255), (x, y, lw, lh))
        s.blit(_pintar(f, massa, mix(massa, (200, 110, 70), 0.45), mix(massa, (255, 255, 255), 0.5), cont,
                       desloc=(lw // 3, 0), luz_desloc=(3, 0), riscos="sorriso", rng=rng, n_riscos=lw // 4), (0, 0))
        g = _forma_vazia(w, h)
        pygame.draw.rect(g, (255, 255, 255), (x - 1, y - 2, lw + 2, 5))
        k = x
        while k < x + lw - 2:                                            # pingos do glacê
            pl = rng.choice((2, 3, 3, 4, 6))
            pygame.draw.rect(g, (255, 255, 255), (k + 1, y + 2, 2, pl))
            pygame.draw.circle(g, (255, 255, 255), (k + 2, y + 2 + pl), 1)
            k += rng.randint(4, 7)
        s.blit(_pintar(g, glace, mix(glace, (150, 50, 90), 0.3), mix(glace, (255, 255, 255), 0.5), cont,
                       desloc=(lw // 3, 0), luz_desloc=(0, 1)), (0, 0))
        k = x + 3
        while k < x + lw - 2:                                            # morangos na borda
            pygame.draw.circle(s, cont, (k, y - 3), 2)
            s.set_at((k, y - 3), (232, 56, 64))
            s.set_at((k - 1, y - 3), (232, 56, 64))
            s.set_at((k, y - 5), (112, 192, 96))
            k += rng.randint(9, 14)
    def torre(x, y, alt, rw):
        f = _forma_vazia(w, h)
        pygame.draw.rect(f, (255, 255, 255), (x, y, rw, alt), border_radius=rw // 2)
        t = _pintar(f, (250, 246, 236), (214, 196, 196), None, cont, desloc=(rw // 3, 0))
        cor = _pintar(f, (232, 72, 72), (176, 40, 56), (248, 140, 128), cont, desloc=(rw // 3, 0), luz_desloc=(2, 0))
        s.blit(t, (0, 0))
        s.blit(cor.subsurface((0, 0, w, y + alt // 2)), (0, 0))         # cápsula: metade de cima colorida
        s.fill(cont, (x + 1, y + alt // 2, rw - 2, 1))
        for jy in range(y + 6, y + alt - 4, 9):                          # janelinhas
            pygame.draw.rect(s, cont, (x + rw // 2 - 2, jy, 4, 5))
            s.fill((72, 168, 208), (x + rw // 2 - 1, jy + 1, 2, 3))
        tet = _forma_vazia(w, h)
        pygame.draw.polygon(tet, (255, 255, 255), [(x - 2, y + 3), (x + rw // 2, y - 15), (x + rw + 1, y + 3)])
        s.blit(_pintar(tet, (240, 144, 32), (190, 92, 30), (252, 196, 96), cont, desloc=(rw // 3, 0)), (0, 0))
        pygame.draw.line(s, cont, (x + rw // 2, y - 15), (x + rw // 2, y - 23))
        pygame.draw.polygon(s, (232, 72, 64), [(x + rw // 2 + 1, y - 23), (x + rw // 2 + 9, y - 21),
                                               (x + rw // 2 + 6, y - 19), (x + rw // 2 + 10, y - 17),
                                               (x + rw // 2 + 1, y - 17)])
    base = h - 4
    torre(4, 40, 66, 14)
    torre(w - 18, 40, 66, 14)
    torre(30, 22, 40, 11)
    torre(w - 41, 22, 40, 11)
    andar(12, base - 26, w - 24, 26, (248, 236, 176), (240, 144, 144))
    andar(26, base - 48, w - 52, 22, (248, 210, 160), (250, 246, 236))
    andar(40, base - 66, w - 80, 18, (248, 236, 176), (196, 140, 210))
    d = _forma_vazia(w, h)                                               # domo com a cruz
    pygame.draw.ellipse(d, (255, 255, 255), (w // 2 - 19, base - 90, 38, 48))
    d.fill((0, 0, 0, 0), (0, base - 66, w, h))                          # só a metade de cima: o domo assenta no andar
    s.blit(_pintar(d, (184, 128, 184), (136, 88, 150), (220, 180, 222), cont, desloc=(8, 2), luz_desloc=(4, 3),
                   riscos="sorriso", rng=rng, n_riscos=6), (0, 0))
    pygame.draw.circle(s, cont, (w // 2, base - 76), 7)
    pygame.draw.circle(s, (250, 250, 246), (w // 2, base - 76), 6)
    s.fill((224, 48, 56), (w // 2 - 1, base - 81, 3, 11))
    s.fill((224, 48, 56), (w // 2 - 5, base - 77, 11, 3))
    pygame.draw.circle(s, cont, (w // 2, base - 92), 3)                 # cereja no topo
    pygame.draw.circle(s, (232, 56, 64), (w // 2, base - 92), 2)
    pygame.draw.rect(s, cont, (w // 2 - 9, base - 20, 18, 20), border_top_left_radius=9, border_top_right_radius=9)
    pygame.draw.rect(s, (110, 44, 44), (w // 2 - 8, base - 19, 16, 19), border_top_left_radius=8, border_top_right_radius=8)
    for k in range(-5, 6, 4):
        s.fill((80, 28, 28), (w // 2 + k, base - 15, 1, 15))
    return s


def _confeitado(L, H, rng):
    c0 = _forma_vazia(L, H)
    _banco_nuvens(c0, rng, H * 0.58, L, 0.9, cor=(255, 246, 250), sombra=(240, 214, 232), contorno=(176, 140, 184))
    longe, _ = _morros(L, H, rng, H * 0.72, 22, (250, 210, 222), (230, 180, 206), None, (196, 150, 180), riscos=None)
    c0.blit(longe, (0, 0))
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.84, 16, (248, 220, 160), (226, 170, 120), (252, 240, 196), (120, 64, 40), manchas=22)
    hx = rng.randint(L // 4, L // 2)
    hosp = hospital_confeitado(rng)
    _emendar(c1, hosp, hx - hosp.get_width() // 2, perfil[hx] - hosp.get_height() + 6, L)
    c1.blit(meio, (0, 0))
    _pontos_brilho(c1, rng, 26, H * 0.15, H * 0.6)
    pal = _pal_bosque(rng)
    pal.update(COPAS[2])
    pal.update(casca=(250, 240, 220), casca_s=(214, 176, 168), contorno=(110, 40, 70))
    c2 = _forma_vazia(L, H)
    perto, perfil = _morros(L, H, rng, H * 0.95, 12, (240, 150, 170), (200, 106, 140), (252, 196, 210), (110, 40, 70),
                            tufos=((150, 210, 120), (104, 168, 96), (40, 80, 50)), manchas=26)
    x = rng.randint(10, 40)
    while x < L:
        a = rng.randint(56, 76)
        arv = arvore_gota(a, rng, pal)
        _emendar(c2, arv, x - arv.get_width() // 2, perfil[min(L, x)] - a + 6, L)
        x += rng.randint(100, 160)
    c2.blit(perto, (0, 0))
    return [c0, c1, c2]


def _fita(L, H, rng, y0, grossura, amp, pingos=True):
    """Fita de nuvem mágica (periódica na largura): corpo lilás, borda de cima ciano, barriga rosa, marcas ︶ e
    pingos pendurados. Sem contorno escuro: a borda é a faixa de cor."""
    f = _forma_vazia(L, H)
    fz = [rng.uniform(0, 6.28) for _ in range(3)]
    def y_de(x):
        return (y0 + amp * math.sin(2 * math.pi * x / L + fz[0]) + amp * 0.4 * math.sin(2 * math.pi * 3 * x / L + fz[1]))
    fz.append(rng.uniform(0, 6.28))
    def r_de(x):                                                         # grossura que varia e some nos vãos
        corte = math.sin(2 * math.pi * 2 * x / L + fz[3])
        if corte < -0.75:
            return 0
        fino = min(1.0, (corte + 0.75) * 3)
        return grossura * fino * (0.55 + 0.6 * (0.5 + 0.5 * math.sin(2 * math.pi * 3 * x / L + fz[2])))
    for x in range(0, L, 2):
        for dx in (-L, 0, L):
            pygame.draw.circle(f, (255, 255, 255), (x + dx, int(y_de(x))), int(r_de(x)))
    for _ in range(L // 9):                                              # carocinhos de cima (topo fofo)
        x = rng.randrange(L)
        r = int(r_de(x) * rng.uniform(0.5, 0.85))
        if r < 3:
            continue
        for dx in (-L, 0, L):
            pygame.draw.circle(f, (255, 255, 255), (x + dx, int(y_de(x) - r_de(x) * 0.55)), r)
    m = pygame.mask.from_surface(f)
    s = _forma_vazia(L, H)
    _por(s, m, (96, 112, 184))
    def faixa(desl, cor):
        _por(s, _menos(m, m.overlap_mask(m, desl)), cor)
    faixa((0, -6), (168, 112, 176))                                      # barriga rosa
    faixa((0, -2), (208, 152, 192))
    faixa((0, 5), (16, 160, 184))                                        # borda de cima ciano
    faixa((0, 2), (64, 196, 236))
    _riscos(s, _miolo(m, 4), "sorriso", L // 2, rng, (176, 128, 196))
    _riscos(s, _miolo(m, 3), "sorriso", L // 4, rng, (224, 176, 212))
    if pingos:
        for _ in range(L // 16):
            x = rng.randrange(L)
            fundo = None
            for y in range(H - 1, 0, -1):
                if m.get_at((x, y)):
                    fundo = y
                    break
            if fundo is None or fundo > H - 14:
                continue
            pl = rng.randint(4, 11)
            for dx in (-L, 0, L):
                s.fill((16, 160, 184), (x + dx - 1, fundo - 1, 3, pl))
                s.fill((64, 196, 236), (x + dx, fundo - 1, 1, pl - 1))
                s.fill((16, 160, 184), (x + dx, fundo - 1 + pl, 1, 1))
    return s


def _broto(rng):
    """Brotinho verde de folhas finas (como um pinheiro de três galhos)."""
    s = _forma_vazia(11, 18)
    cor, esc = (128, 184, 120), (64, 120, 80)
    pygame.draw.line(s, esc, (5, 17), (6, 3))
    pygame.draw.line(s, cor, (4, 17), (5, 3))
    for k, y in enumerate((5, 8, 11)):
        lw = 2 + k
        pygame.draw.line(s, cor, (5, y), (5 - lw, y + 2))
        pygame.draw.line(s, cor, (6, y), (6 + lw, y + 2))
    s.set_at((5, 2), cor)
    return s


def _cosmo(L, H, rng):
    c0 = _forma_vazia(L, H)
    for _ in range(L // 24):                                             # respingos escuros
        x, y = rng.randrange(L), rng.randint(int(H * 0.2), H)
        for _ in range(14):
            px, py = x + int(rng.gauss(0, 7)), y + int(rng.gauss(0, 5))
            if 0 <= py < H:
                c0.set_at((px % L, py), (40, 10, 36))
    for _ in range(3):                                                   # planetas-bolha, com bolhinhas em volta
        x, y, r = rng.randrange(L), rng.randint(int(H * 0.08), int(H * 0.45)), rng.randint(8, 16)
        for dx in (-L, 0, L):
            pygame.draw.circle(c0, (112, 72, 152), (x + dx, y), r)
            pygame.draw.circle(c0, (136, 92, 170), (x + dx - r // 3, y - r // 3), r // 3)
        for _ in range(7):
            bx, by = x + rng.randint(-r * 2, r * 2), y + rng.randint(-r * 2, r * 2)
            pygame.draw.circle(c0, (100, 64, 140), (bx % L, by), rng.randint(1, 4))
    c0.blit(_fita(L, H, rng, H * 0.42, 8, 10, pingos=False), (0, 0))
    _pontos_brilho(c0, rng, 16, 0, H * 0.8)
    c1 = _forma_vazia(L, H)
    c1.blit(_fita(L, H, rng, H * 0.6, 13, 14), (0, 0))
    _pontos_brilho(c1, rng, 18, H * 0.2, H * 0.7)
    c2 = _forma_vazia(L, H)
    fita = _fita(L, int(H * 1.6), rng, H * 0.98, 20, 8, pingos=False)
    m = pygame.mask.from_surface(fita)
    x = rng.randint(0, 30)
    while x < L:
        for y in range(H):
            if m.get_at((x, y)):
                b = _broto(rng)
                _emendar(c2, b, x - 5, y - b.get_height() + 4, L)
                break
        x += rng.randint(40, 90)
    c2.blit(fita, (0, 0))
    return [c0, c1, c2]


def chama(w, h, rng, inclina):
    """Chama em três camadas (vermelho, laranja, amarelo): base larga, corpo em S e ponta que curva para um lado;
    às vezes solta uma gotinha de fogo acima da ponta. A superfície tem o dobro da largura (a ponta sai do eixo)."""
    W = w * 2
    s = _forma_vazia(W, h)
    onda = rng.uniform(0.6, 1.4)
    for k, cor in ((1.0, (206, 36, 30)), (0.74, (234, 116, 34)), (0.46, (244, 214, 44))):
        hk = h * k
        pts_e, pts_d = [], []
        for i in range(17):
            t = i / 16
            meia = w / 2 * k * (1 - t) ** 0.6 * (0.85 + 0.35 * math.sin(t * math.pi * 0.9))
            meio = W / 2 + inclina * w * 0.45 * t ** 2.2 + w * 0.12 * k * math.sin(t * math.pi * 1.6 * onda)
            y = h - t * hk
            pts_e.append((meio - meia * (1.1 - 0.2 * t), y))
            pts_d.append((meio + meia * (0.9 + 0.2 * t), y))
        pygame.draw.polygon(s, cor, pts_e + pts_d[::-1])
    if rng.random() < 0.4 and h > 26:                                   # gotinha de fogo solta
        gx = int(W / 2 + inclina * w * 0.6)
        gy = int(h * 0.08) + 2
        pygame.draw.circle(s, (206, 36, 30), (gx, gy + 2), 2)
        pygame.draw.polygon(s, (206, 36, 30), [(gx - 2, gy + 2), (gx + inclina * 2, gy - 3), (gx + 2, gy + 2)])
    return s


def _brasas(L, H, rng):
    c0 = _forma_vazia(L, H)
    for i, cor in enumerate(((80, 10, 52), (112, 18, 44), (150, 34, 42))):   # céu em redemoinho: faixas curvas
        r = int(H * (1.3 - i * 0.22))
        cx = rng.randrange(L)
        for dx in (-L, 0, L):
            pygame.draw.circle(c0, cor, (cx + dx, int(H * 1.25)), r, max(6, H // 14))
    longe, _ = _morros(L, H, rng, H * 0.74, 30, (120, 20, 26), (92, 14, 24), None, (60, 8, 20), riscos="barra",
                       ondas=(3, 5, 9))
    c0.blit(longe, (0, 0))
    _pontos_brilho(c0, rng, 10, 0, H * 0.4, cor=(200, 170, 220))
    c1 = _forma_vazia(L, H)
    M = 16
    f = _forma_vazia(L + 2 * M, H + M)
    x = rng.randint(-10, 10) + M
    while x < L + 20 + M:                                                # rochedos: bolotas empilhadas
        bw, bh = rng.randint(30, 60), rng.randint(24, 46)
        for dx in (-L, 0, L):
            pygame.draw.ellipse(f, (255, 255, 255), (x + dx - bw // 2, int(H * 0.86) - bh, bw, bh * 2))
            pygame.draw.ellipse(f, (255, 255, 255), (x + dx - bw // 4, int(H * 0.86) - bh - 8, bw // 2, bh))
        x += rng.randint(26, 46)
    pygame.draw.rect(f, (255, 255, 255), (0, int(H * 0.86), L + 2 * M, H))
    c1.blit(_pintar(f, (124, 20, 22), (76, 14, 20), (168, 48, 56), (40, 8, 16), desloc=(10, 6), luz_desloc=(4, 3),
                    riscos="barra", rng=rng, n_riscos=L), (-M, 0))
    c2 = _forma_vazia(L, H)
    base = int(H * 0.93)
    x = rng.randint(-6, 6)
    while x < L + 10:
        cw, ch = rng.randint(14, 26), rng.randint(22, 46)
        ch_s = chama(cw, ch, rng, rng.choice((-1, 1)) * rng.uniform(0.5, 1.2))
        _emendar(c2, ch_s, x - cw, base - ch + 4, L)
        x += rng.randint(9, 17)
    c2.fill((206, 36, 30), (0, base, L, H - base))
    x = rng.randint(-6, 6)
    while x < L + 10:                                                    # segunda fileira, baixa, na frente
        cw, ch = rng.randint(10, 18), rng.randint(10, 18)
        ch_s = chama(cw, ch, rng, rng.choice((-1, 1)) * rng.uniform(0.3, 0.9))
        _emendar(c2, ch_s, x - cw, H - ch + 2, L)
        x += rng.randint(7, 12)
    return [c0, c1, c2]


def arvore_bolota(alt, rng, pal):
    """Árvore de bolotas (tipo brócolis): copa de bolas sobrepostas, sombra dura embaixo à direita, bolotas mais
    claras por cima com a linha na própria cor; tronco com nó."""
    cw = int(alt * rng.uniform(0.62, 0.78))
    w = cw + 8
    s = _forma_vazia(w, alt)
    cx = w // 2
    copa_h = int(alt * rng.uniform(0.55, 0.65))
    tw = max(4, cw // 5)
    t = _forma_vazia(w, alt)
    pygame.draw.polygon(t, (255, 255, 255), [(cx - tw // 2, copa_h - 8), (cx + tw // 2, copa_h - 8), (cx + tw // 2, alt - 4),
                                             (cx + tw, alt), (cx - tw, alt), (cx - tw // 2, alt - 4)])
    s.blit(_pintar(t, pal["casca"], pal["casca_s"], None, pal["contorno"], desloc=(max(2, tw // 3), 0),
                   riscos="casca", rng=rng, n_riscos=tw * 2), (0, 0))
    if alt > 40:
        ny = rng.randint(copa_h + 2, max(copa_h + 3, alt - 8))
        pygame.draw.ellipse(s, pal["contorno"], (cx - 2, ny - 3, 4, 6))
        pygame.draw.ellipse(s, pal["casca_s"], (cx - 1, ny - 2, 2, 4))
    f = _forma_vazia(w, alt)
    bolas = []
    for _ in range(7):
        r = int(cw * rng.uniform(0.18, 0.28))
        bx = rng.randint(4 + r, w - 4 - r)
        by = rng.randint(r + 1, max(r + 2, copa_h - r))
        bolas.append((bx, by, r))
    bolas.append((cx, int(copa_h * 0.55), int(cw * 0.32)))
    for bx, by, r in bolas:
        pygame.draw.circle(f, (255, 255, 255), (bx, by), r)
    s.blit(_pintar(f, pal["copa"], pal["copa_s"], None, pal["contorno"], desloc=(max(3, cw // 6), max(3, cw // 7)),
                   riscos="sorriso", rng=rng, n_riscos=cw // 2), (0, 0))
    for bx, by, r in sorted(bolas, key=lambda b: b[1])[:4]:              # bolotas claras de cima
        rr = max(2, r // 2)
        x, y = bx - r // 4, by - r // 3
        pygame.draw.circle(s, mix(pal["copa_l"], pal["copa_s"], 0.35), (x, y), rr)
        pygame.draw.circle(s, pal["copa_l"], (x, y), rr - 1)
    return s


def pinheiro(alt, rng, neve=False, cor=(44, 120, 88), sombra=(26, 84, 70), contorno=(14, 40, 40)):
    """Pinheiro chapado: andares de triângulos empilhados, metade direita na sombra, pontinha de neve opcional."""
    w = int(alt * 0.62) | 1
    f = _forma_vazia(w, alt)
    n = 3 if alt < 30 else 4
    tronco = max(3, alt // 9)
    for i in range(n):
        topo = int((alt - tronco) * i / (n + 0.6))
        base = int((alt - tronco) * (i + 1.5) / (n + 0.6))
        meia = int(w / 2 * (0.45 + 0.55 * (i + 1) / n))
        pygame.draw.polygon(f, (255, 255, 255), [(w // 2, topo), (w // 2 + meia, base), (w // 2 - meia, base)])
    s = _pintar(f, cor, sombra, mix(cor, (255, 255, 255), 0.25), contorno, desloc=(w // 4, 0), luz_desloc=(1, 2))
    s.fill(contorno, (w // 2 - 1, alt - tronco - 1, 3, tronco + 1))
    s.fill((120, 80, 50), (w // 2, alt - tronco - 1, 1, tronco))
    if neve:                                                            # chapeuzinho de neve na ponta de cada andar
        for i in range(n):
            topo = int((alt - tronco) * i / (n + 0.6))
            meia = int(w / 2 * (0.45 + 0.55 * (i + 1) / n))
            k = max(2, meia // 2)
            pygame.draw.polygon(s, (246, 250, 255), [(w // 2, topo + 1), (w // 2 + k, topo + k + 1),
                                                     (w // 2, topo + k - 1), (w // 2 - k, topo + k + 1)])
    return s


def montanha_facetada(w, h, rng, claro=(206, 230, 250), escuro=(126, 160, 222), meio=(166, 196, 238),
                      contorno=(46, 66, 130), neve=(250, 252, 255)):
    """Montanha de gelo/cristal facetada: polígonos chapados, lado da luz e lado da sombra, faces internas e capa
    de neve no pico."""
    s = _forma_vazia(w, h)
    px = int(w * rng.uniform(0.38, 0.62))
    pico = (px, 1)
    def encosta(x0):                                                    # lado torto: ombros no caminho
        pts = []
        for i in range(1, 4):
            t = i / 4
            pts.append((int(px + (x0 - px) * t + rng.randint(-3, 3)), int(1 + (h - 1) * t + rng.randint(-4, 2))))
        return pts
    le, ld = encosta(0), encosta(w - 1)
    crista = [pico] + [(px + rng.randint(-4, 4), int(h * t)) for t in (0.35, 0.7)] + [(px + rng.randint(-6, 6), h)]
    pygame.draw.polygon(s, claro, [pico] + le + [(0, h)] + crista[::-1])
    pygame.draw.polygon(s, escuro, crista + [(w - 1, h)] + ld[::-1])
    for lado, pts in ((-1, le), (1, ld)):                                # faces internas: do ombro até o pé
        for (ox, oy) in pts[:2]:
            pe = (ox + lado * rng.randint(4, 12), h)
            meio_pe = ((ox + crista[2][0]) // 2, h)
            pygame.draw.polygon(s, meio if lado < 0 else mix(escuro, contorno, 0.22), [(ox, oy), pe, meio_pe])
    capa = int(h * rng.uniform(0.24, 0.34))
    m0 = pygame.mask.from_surface(s)
    for y in range(capa + 3):                                           # capa de neve com borda em dentes
        for x in range(w):
            if m0.get_at((x, y)) and y < capa + (2 if (x // 3) % 2 else -1):
                s.set_at((x, y), neve if x < crista[0][0] + 1 else mix(neve, escuro, 0.3))
    m = pygame.mask.from_surface(s)
    _por(s, _menos(m, _miolo(m)), contorno)
    pygame.draw.lines(s, mix(escuro, contorno, 0.5), False, crista)
    return s


def _gelo(L, H, rng):
    c0 = _forma_vazia(L, H)
    _banco_nuvens(c0, rng, H * 0.5, L, 0.8)
    x = rng.randint(-20, 0)
    while x < L:
        mw, mh = rng.randint(60, 110), rng.randint(56, 96)
        m = montanha_facetada(mw, mh, rng)
        _emendar(c0, m, x, int(H * 0.78) - mh, L)
        x += int(mw * rng.uniform(0.45, 0.75))
    c0.fill((210, 226, 250), (0, int(H * 0.78), L, H))
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.82, 20, (242, 248, 255), (196, 208, 244), None, (110, 128, 196),
                           manchas=24)
    x = rng.randint(0, 20)
    while x < L:
        a = rng.randint(18, 34)
        p = pinheiro(a, rng, neve=True)
        _emendar(c1, p, x - p.get_width() // 2, perfil[min(L, x)] - a + 3, L)
        x += rng.randint(10, 40)
    c1.blit(meio, (0, 0))
    c2 = _forma_vazia(L, H)
    perto, perfil = _morros(L, H, rng, H * 0.95, 12, (226, 236, 252), (176, 190, 236), None, (90, 104, 170),
                            manchas=26)
    x = rng.randint(10, 40)
    while x < L:
        a = rng.randint(46, 70)
        p = pinheiro(a, rng, neve=True)
        _emendar(c2, p, x - p.get_width() // 2, perfil[min(L, x)] - a + 5, L)
        x += rng.randint(50, 110)
    c2.blit(perto, (0, 0))
    return [c0, c1, c2]


def _faixas_agua(s, rng, y0, y1, cores):
    """Água de desenho: faixas horizontais onduladas chapadas (periódicas na largura)."""
    L, H = s.get_size()
    n = len(cores)
    for i, cor in enumerate(cores):
        topo = y0 + (y1 - y0) * i / n
        fz, amp, k = rng.uniform(0, 6.28), rng.uniform(1.5, 3.5), rng.choice((2, 3, 4))
        pts = [(0, H)] + [(x, topo + amp * math.sin(2 * math.pi * k * x / L + fz)) for x in range(0, L + 1, 2)] + [(L, H)]
        pygame.draw.polygon(s, cor, pts)


def alga(alt, rng, cor=(70, 168, 112), sombra=(40, 120, 90), contorno=(16, 60, 56)):
    """Alga: fita que ondula de baixo para cima, com folhinhas."""
    w = 12
    f = _forma_vazia(w, alt)
    fz = rng.uniform(0, 6.28)
    for y in range(alt):
        t = 1 - y / alt
        x = w / 2 + 3 * math.sin(y * 0.25 + fz) * t
        pygame.draw.circle(f, (255, 255, 255), (int(x), y), 2 if t < 0.85 else 1)
    return _pintar(f, cor, sombra, None, contorno, desloc=(1, 0))


def _mar(L, H, rng):
    c0 = _forma_vazia(L, H)
    _faixas_agua(c0, rng, H * 0.42, H * 0.86, [(26, 96, 132), (20, 110, 146), (30, 126, 156), (40, 140, 160)])
    for _ in range(18):                                                  # bolhas
        x, y, r = rng.randrange(L), rng.randint(int(H * 0.1), int(H * 0.7)), rng.choice((1, 2, 2, 3))
        pygame.draw.circle(c0, (150, 220, 236), (x, y), r, 1)
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.84, 14, (214, 200, 150), (176, 158, 120), (236, 224, 180), (92, 80, 64),
                           manchas=24)
    x = rng.randint(0, 20)
    while x < L:
        a = rng.randint(18, 40)
        g = alga(a, rng)
        _emendar(c1, g, x - 6, perfil[min(L, x)] - a + 3, L)
        x += rng.randint(8, 30)
    c1.blit(meio, (0, 0))
    c2 = _forma_vazia(L, H)
    M = 12
    f = _forma_vazia(L + 2 * M, H + M)
    x = rng.randint(0, 20) + M
    while x < L + M + 20:                                                # rochas de coral
        bw, bh = rng.randint(26, 50), rng.randint(14, 30)
        for dx in (-L, 0, L):
            pygame.draw.ellipse(f, (255, 255, 255), (x + dx - bw // 2, int(H * 0.92) - bh, bw, bh * 2))
        x += rng.randint(40, 80)
    pygame.draw.rect(f, (255, 255, 255), (0, int(H * 0.95), L + 2 * M, H))
    rocha = _pintar(f, (92, 112, 150), (62, 76, 116), (128, 150, 186), (30, 36, 64), desloc=(8, 5), luz_desloc=(3, 3),
                    riscos="sorriso", rng=rng, n_riscos=L // 2)
    mr = pygame.mask.from_surface(f)
    for _ in range(L // 6):                                              # bolotas de coral rosa por cima
        cx = rng.randrange(M, L + M)
        for y in range(H):
            if mr.get_at((cx, y)):
                r = rng.randint(2, 4)
                pygame.draw.circle(rocha, (120, 40, 70), (cx, y), r + 1)
                pygame.draw.circle(rocha, rng.choice(((240, 120, 150), (250, 170, 90))), (cx, y), r)
                rocha.set_at((cx - 1, y - 1), (255, 220, 230))
                break
    c2.blit(rocha, (-M, 0))
    return [c0, c1, c2]


# ------------------------------------------------------------------ interior (Traço Ilha: Laboratório de Dexter)

FAMILIAS = [(58, 150, 160), (70, 120, 200), (90, 176, 140), (150, 120, 196)]   # petróleo, azul, menta, lilás


def _tons(base):
    """Uma família de cor só (Dexter: um tom por ambiente): 6 valores do quase branco ao quase preto."""
    return [mix(base, (250, 252, 255), 0.82), mix(base, (250, 252, 255), 0.55), mix(base, (250, 252, 255), 0.22),
            base, mix(base, (10, 14, 30), 0.38), mix(base, (10, 14, 30), 0.7)]


def _leito(t, w=58):
    """Leito hospitalar visto de lado: cabeceira, colchão, travesseiro, grade e rodinhas (geometria dura)."""
    s = _forma_vazia(w, 34)
    s.fill(t[4], (2, 4, 4, 24))                                            # cabeceira
    s.fill(t[3], (3, 5, 2, 22))
    s.fill(t[4], (w - 6, 12, 4, 16))                                       # pés
    s.fill(t[0], (5, 13, w - 10, 6))                                       # colchão
    s.fill(t[1], (5, 17, w - 10, 2))
    s.fill(t[0], (7, 9, 12, 5))                                            # travesseiro
    s.fill(t[2], (7, 13, 12, 1))
    s.fill(t[4], (5, 19, w - 10, 3))                                       # estrado
    for x in range(12, w - 12, 6):                                         # grade lateral
        s.fill(t[3], (x, 8, 1, 6))
    s.fill(t[3], (10, 8, w - 22, 1))
    for x in (8, w - 10):                                                  # rodinhas
        s.fill(t[5], (x, 22, 2, 8))
        pygame.draw.circle(s, t[5], (x + 1, 31), 2)
    return s


def _monitor(t):
    s = _forma_vazia(18, 44)
    s.fill(t[4], (8, 14, 2, 28))                                           # haste
    s.fill(t[5], (3, 40, 12, 3))
    s.fill(t[5], (0, 0, 18, 14))                                           # tela com o traçado
    s.fill(t[4], (1, 1, 16, 12))
    pts = [(2, 8), (5, 8), (6, 4), (7, 11), (8, 8), (11, 8), (12, 6), (13, 8), (16, 8)]
    pygame.draw.lines(s, t[0], False, pts)
    return s


def _soro(t):
    s = _forma_vazia(14, 56)
    s.fill(t[4], (6, 4, 2, 50))
    s.fill(t[4], (2, 4, 10, 2))
    s.fill(t[0], (2, 7, 5, 9))                                             # bolsa
    s.fill(t[2], (2, 13, 5, 3))
    pygame.draw.line(s, t[2], (4, 16), (9, 40))                            # equipo
    s.fill(t[5], (1, 53, 12, 2))
    return s


def _cortina(t, w, h):
    s = _forma_vazia(w, h)
    s.fill(t[4], (0, 0, w, 2))                                             # trilho
    for x in range(0, w, 6):                                               # pregas: faixas claro/escuro
        s.fill(t[2], (x, 2, 3, h - 2))
        s.fill(t[1], (x + 3, 2, 3, h - 2))
    return s


def _janela(t, w, h):
    s = _forma_vazia(w, h)
    s.fill(t[4], (0, 0, w, h))
    s.fill(t[0], (2, 2, w - 4, h - 4))
    s.fill(t[1], (2, h // 2, w - 4, h // 2 - 2))                           # o lado de fora, em 2 faixas
    s.fill(t[4], (w // 2 - 1, 0, 2, h))
    s.fill(t[4], (0, h // 2 - 1, w, 2))
    return s


def _enfermaria(L, H, rng):
    t = _tons(rng.choice(FAMILIAS))
    # 0: parede (cobre o céu), rodameio, janelas, quadro de avisos e relógio
    c0 = pygame.Surface((L, H), SRC)
    c0.fill(t[0])
    c0.fill(t[1], (0, int(H * 0.55), L, H))                               # barrado de azulejo
    for x in range(0, L, 10):
        c0.fill(t[2], (x, int(H * 0.55), 1, H))
    for y in range(int(H * 0.55), H, 10):
        c0.fill(t[2], (0, y, L, 1))
    c0.fill(t[3], (0, int(H * 0.55) - 3, L, 3))                           # rodameio
    x = rng.randint(10, 30)
    janelas = []
    while x < L - 40:
        _emendar(c0, _janela(t, 36, 30), x, int(H * 0.18), L)
        janelas.append(x)
        x += rng.randint(80, 120)
    rx = rng.randrange(L)
    pygame.draw.circle(c0, t[4], (rx, int(H * 0.12)), 7)
    pygame.draw.circle(c0, t[0], (rx, int(H * 0.12)), 5)
    pygame.draw.line(c0, t[5], (rx, int(H * 0.12)), (rx, int(H * 0.12) - 4))
    pygame.draw.line(c0, t[5], (rx, int(H * 0.12)), (rx + 3, int(H * 0.12)))
    qx = (janelas[0] + 42) % L if janelas else (rx + L // 2) % L         # quadro no vão entre janelas
    c0.fill(t[3], (qx, int(H * 0.22), 26, 18))
    c0.fill(t[1], (qx + 2, int(H * 0.22) + 2, 22, 14))
    for k in range(3):
        c0.fill(t[3], (qx + 4, int(H * 0.22) + 5 + k * 4, 14 - k * 3, 1))
    pygame.draw.line(c0, t[4], (qx + 21, int(H * 0.22) + 4), (qx + 21, int(H * 0.22) + 9), 2)   # cruz do hospital
    pygame.draw.line(c0, t[4], (qx + 19, int(H * 0.22) + 6), (qx + 23, int(H * 0.22) + 6), 2)
    # 1: leitos com cortina, monitor e soro, sobre o piso quadriculado em perspectiva
    c1 = _forma_vazia(L, H)
    piso = int(H * 0.8)
    c1.fill(t[2], (0, piso, L, H - piso))
    for k in range(0, L + 40, 14):                                         # linhas de fuga do piso
        pygame.draw.line(c1, t[3], (k, piso), (k + (k - L / 2) * 0.6, H))
    for y in (piso + 6, piso + 15, piso + 27):
        c1.fill(t[3], (0, y, L, 1))
    x = rng.randint(0, 20)
    while x < L:
        _emendar(c1, _cortina(t, 30, int(H * 0.42)), x - 6, piso - int(H * 0.42) - 6, L)
        _emendar(c1, _leito(t), x + 20, piso - 32, L)
        _emendar(c1, _monitor(t), x + 82, piso - 44, L)
        _emendar(c1, _soro(t), x + 12, piso - 56, L)
        x += rng.randint(120, 150)
    # 2: perto, escuro: carrinho, cilindro de oxigênio e cadeira
    c2 = _forma_vazia(L, H)
    x = rng.randint(20, 60)
    while x < L:
        k = rng.randrange(3)
        if k == 0:                                                         # carrinho de curativo
            p = _forma_vazia(30, 30)
            p.fill(t[5], (0, 6, 30, 3))
            p.fill(t[5], (0, 16, 30, 3))
            p.fill(t[5], (2, 6, 2, 20))
            p.fill(t[5], (26, 6, 2, 20))
            pygame.draw.circle(p, t[5], (3, 27), 3)
            pygame.draw.circle(p, t[5], (27, 27), 3)
        elif k == 1:                                                       # cilindro de oxigênio
            p = _forma_vazia(12, 40)
            pygame.draw.rect(p, t[5], (1, 6, 10, 34), border_radius=4)
            p.fill(t[4], (4, 0, 4, 7))
            p.fill(t[3], (3, 12, 2, 20))
        else:                                                              # cadeira
            p = _forma_vazia(20, 32)
            p.fill(t[5], (2, 0, 3, 32))
            p.fill(t[5], (2, 14, 16, 3))
            p.fill(t[5], (15, 14, 3, 18))
        _emendar(c2, p, x, H - p.get_height() - 2, L)
        x += rng.randint(70, 130)
    return [c0, c1, c2]


# ------------------------------------------------------------------ La Mancha

_ANCORAS = {}                                     # id(camada) → [(x, y, raio)] dos cubos das pás


def ancoras(camada):
    return _ANCORAS.get(id(camada), ())


def _torre_moinho(alt):
    """Moinho manchego: torre caiada, chapéu cônico escuro e uma portinha; devolve (superfície, x e y do cubo)."""
    w = alt
    f = _forma_vazia(w, alt)
    cx = w // 2
    topo, bw, tw = int(alt * 0.26), int(alt * 0.27), int(alt * 0.19)
    pygame.draw.polygon(f, (255, 255, 255), [(cx - tw, topo), (cx + tw, topo), (cx + bw, alt), (cx - bw, alt)])
    s = _pintar(f, (248, 240, 222), (208, 188, 172), None, (92, 62, 60), desloc=(max(2, alt // 9), 0))
    pygame.draw.polygon(s, (92, 62, 60), [(cx - tw - 3, topo + 1), (cx, 1), (cx + tw + 3, topo + 1)])
    pygame.draw.polygon(s, (132, 88, 66), [(cx - tw - 1, topo), (cx, 3), (cx + tw + 1, topo)])
    pw = max(2, alt // 12)
    s.fill((92, 62, 60), (cx - pw, alt - alt // 5, pw * 2, alt // 5))
    s.fill((92, 62, 60), (cx - 1, int(alt * 0.5), 3, 4))
    return s, cx, topo + alt // 8


def _oliveira(alt, rng):
    w = int(alt * 1.1)
    f = _forma_vazia(w, alt)
    for _ in range(5):
        r = rng.randint(alt // 5, alt // 3)
        pygame.draw.circle(f, (255, 255, 255), (rng.randint(r, max(r + 1, w - r)), rng.randint(r, alt * 2 // 3)), r)
    s = _pintar(f, (132, 148, 92), (92, 112, 78), (168, 180, 116), (44, 56, 40), desloc=(3, 2))
    s.fill((72, 52, 40), (w // 2 - 1, alt * 2 // 3, 3, alt - alt * 2 // 3))
    return s


def _aldeia(rng):
    """Casinhas caiadas de telha vermelha e a torre da igreja."""
    s = _forma_vazia(70, 34)
    s.fill((248, 240, 222), (48, 6, 10, 28))
    pygame.draw.polygon(s, (170, 84, 60), [(46, 6), (53, 0), (60, 6)])
    s.fill((96, 70, 66), (51, 11, 3, 5))
    for x in range(0, 60, 11):
        h = rng.randint(10, 16)
        s.fill((248, 240, 222), (x, 34 - h, 10, h))
        s.fill((212, 196, 180), (x + 7, 34 - h, 3, h))
        pygame.draw.polygon(s, (188, 92, 62), [(x - 1, 34 - h), (x + 5, 34 - h - 5), (x + 11, 34 - h)])
        s.fill((96, 70, 66), (x + 3, 34 - h + 3, 2, 3))
    return s


def _lamancha(L, H, rng):
    c0 = _forma_vazia(L, H)
    longe, perfil = _morros(L, H, rng, H * 0.68, 16, (224, 200, 152), (198, 170, 134), None, (160, 130, 110), riscos=None)
    x = rng.randint(10, 40)
    while x < L:                                                       # moinhozinhos em fila no alto da serra
        m, _, _ = _torre_moinho(rng.randint(14, 18))
        _emendar(c0, m, x - m.get_width() // 2, perfil[min(L, x)] - m.get_height() + 3, L)
        x += rng.randint(50, 110)
    c0.blit(longe, (0, 0))
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.8, 18, (232, 192, 96), (198, 148, 74), (248, 222, 138), (104, 70, 42),
                           riscos="sorriso", manchas=26)
    al = _aldeia(rng)
    ax = rng.randint(L // 2, L * 3 // 4)
    _emendar(c1, al, ax - 35, perfil[ax] - 30, L)
    pos = []
    x = rng.randint(10, 40)
    while x < L:                                                       # moinhos médios; as pás giram por quadro
        if abs(x - ax) > 56:
            alt = rng.randint(34, 42)
            m, hx, hy = _torre_moinho(alt)
            ox, oy = x - m.get_width() // 2, perfil[min(L, x)] - alt + 4
            _emendar(c1, m, ox, oy, L)
            pos.append(((ox + hx) % L, oy + hy, int(alt * 0.46)))
        x += rng.randint(70, 130)
    x = rng.randint(0, 30)
    while x < L:
        o = _oliveira(rng.randint(14, 20), rng)
        _emendar(c1, o, x, perfil[min(L, x)] - o.get_height() + 3, L)
        x += rng.randint(30, 70)
    c1.blit(meio, (0, 0))
    _ANCORAS[id(c1)] = pos
    c2 = _forma_vazia(L, H)
    perto, perfil = _morros(L, H, rng, H * 0.95, 12, (176, 126, 66), (130, 88, 54), (206, 160, 90), (64, 40, 30),
                            tufos=((150, 132, 62), (110, 92, 48), (60, 46, 26)), manchas=24)
    x = rng.randint(10, 50)
    while x < L:
        o = _oliveira(rng.randint(30, 42), rng)
        _emendar(c2, o, x, perfil[min(L, x)] - o.get_height() + 4, L)
        x += rng.randint(110, 190)
    c2.blit(perto, (0, 0))
    return [c0, c1, c2]


# ------------------------------------------------------------------ O Grito

def _faixas_tortas(s, L, H, y0, cores, passo=5, amp=4.0, ondas=(2, 5), fase=0.0):
    """Faixas de cor que serpenteiam até o fim da tela; emendam na largura. O perfil de cima fica em y0."""
    for x in range(L):
        fx = 2 * math.pi * x / L
        topo = y0 + amp * math.sin(fx * ondas[0] + fase) + amp * 0.5 * math.sin(fx * ondas[1] - fase)
        y, i = topo, 0
        while y < H:
            alt = passo + 2 * math.sin(fx * ondas[1] + i * 1.7 + fase)
            s.fill(cores[i % len(cores)], (x, int(y), 1, int(alt) + 2))
            y += max(2, alt)
            i += 1


def _barquinho(s, x, y, L):
    b = _forma_vazia(16, 8)
    pygame.draw.polygon(b, (22, 20, 34), [(0, 4), (15, 4), (12, 7), (3, 7)])
    b.fill((22, 20, 34), (7, 0, 1, 5))
    pygame.draw.polygon(b, (214, 170, 110), [(8, 0), (13, 3), (8, 3)])
    _emendar(s, b, x, y, L)


def _grito(L, H, rng):
    c0 = _forma_vazia(L, H)                            # a outra margem, escura, com a igrejinha
    _faixas_tortas(c0, L, H, H * 0.58, [(44, 60, 66), (32, 46, 58), (58, 70, 62), (38, 40, 62)], passo=6, amp=7, ondas=(1, 3),
                   fase=rng.uniform(0, 6))
    cx = rng.randint(L // 4, L * 3 // 4)
    y = int(H * 0.58) - 2
    c0.fill((30, 28, 44), (cx, y - 12, 5, 16))
    pygame.draw.polygon(c0, (30, 28, 44), [(cx - 1, y - 12), (cx + 2, y - 20), (cx + 6, y - 12)])
    c1 = _forma_vazia(L, H)                            # o fiorde: azul quase preto em redemoinho
    _faixas_tortas(c1, L, H, H * 0.68, [(30, 44, 88), (20, 30, 64), (44, 64, 110), (24, 36, 74), (72, 84, 120), (20, 30, 64)],
                   passo=4, amp=5, ondas=(2, 7), fase=rng.uniform(0, 6))
    for k in range(3):
        _barquinho(c1, rng.randint(0, L), int(H * (0.72 + 0.05 * k)), L)
    c2 = _forma_vazia(L, H)                            # a ponte: tábuas ocre e o guarda-corpo torto
    yp = int(H * 0.86)
    _faixas_tortas(c2, L, H, yp, [(156, 94, 56), (118, 66, 48), (186, 124, 70), (132, 78, 50)], passo=3, amp=1.5, ondas=(1, 4), fase=rng.uniform(0, 6))
    corrimao = yp - int(H * 0.09)
    for x in range(L):                                 # dois varões
        o = 1.5 * math.sin(2 * math.pi * x / L * 3)
        c2.fill((70, 40, 36), (x, int(corrimao + o), 1, 3))
        c2.fill((132, 82, 52), (x, int(corrimao + o), 1, 1))
        c2.fill((70, 40, 36), (x, int(corrimao + o + (yp - corrimao) * 0.5), 1, 2))
    for x in range(8, L, 34):                          # postes inclinados: é o que dá a pressa da diagonal do quadro
        pygame.draw.line(c2, (54, 30, 32), (x + 8, corrimao - 1), (x, yp + 2), 3)
        pygame.draw.line(c2, (120, 74, 50), (x + 9, corrimao), (x + 1, yp + 1))
    return [c0, c1, c2]


BANDEIRINHAS = ((232, 72, 80), (248, 200, 72), (72, 168, 208), (120, 200, 110), (214, 120, 200), (250, 246, 232))


def lanterna(rng, cor):
    """Lanterna de papel: bola mole em gomos, tampinhas escuras e um fiozinho embaixo."""
    w, h = 11, 15
    f = _forma_vazia(w, h)
    pygame.draw.ellipse(f, (255, 255, 255), (0, 2, w, h - 5))
    s = _pintar(f, cor, mix(cor, (120, 30, 70), 0.4), mix(cor, (255, 250, 210), 0.55), _escuro(cor, 0.5), desloc=(3, 1))
    pygame.draw.line(s, mix(cor, (120, 30, 70), 0.3), (w // 2, 4), (w // 2, h - 5))
    s.fill((60, 34, 44), (3, 1, w - 6, 2))
    s.fill((60, 34, 44), (3, h - 4, w - 6, 2))
    s.fill(mix(cor, (60, 34, 44), 0.3), (w // 2, h - 2, 1, 2))
    return s


def varal(dst, a, b, L, rng, queda=8, lanternas=True):
    """Varal de bandeirinhas entre os pontos a e b: fio que cede no meio, bandeirinhas moles (ponta torta) e, às vezes,
    uma lanterna pendurada. Os x podem passar de L: a peça emenda na rolagem."""
    x0, x1 = a[0], b[0]
    y0 = min(a[1], b[1]) - 2
    w, h = max(2, x1 - x0 + 8), abs(a[1] - b[1]) + queda + 28
    p = _forma_vazia(w, h)
    def fio(x):
        u = (x - x0) / max(1, x1 - x0)
        return a[1] + (b[1] - a[1]) * u + queda * 4 * u * (1 - u) - y0
    for x in range(x0, x1 + 1):
        p.set_at((x - x0, int(fio(x))), (70, 44, 54))
    k = rng.randrange(6)
    x = x0 + 4
    while x < x1 - 5:
        cor = BANDEIRINHAS[k % 6]
        y = fio(x + 2)
        ponta = (x - x0 + 2 + rng.choice((-1, 0, 1)), int(y) + 7)
        f = _forma_vazia(w, h)
        pygame.draw.polygon(f, (255, 255, 255), [(x - x0 - 1, int(fio(x))), (x - x0 + 5, int(fio(x + 5))), ponta])
        p.blit(_pintar(f, cor, mix(cor, (90, 30, 90), 0.3), None, _escuro(cor, 0.55), desloc=(1, 1)), (0, 0))
        k += 1
        x += 8
    if lanternas:
        for u in (0.3, 0.7):
            lx = int(x0 + (x1 - x0) * u)
            if rng.random() < 0.7:
                p.blit(lanterna(rng, rng.choice(((250, 150, 70), (248, 196, 84), (240, 100, 110)))), (lx - x0 - 5, int(fio(lx))))
    _emendar(dst, p, x0, y0, L)


def barraca_cogumelo(rng, cor):
    """Barraca do arraial, parente do Posto-Cogumelo: balcão em caule creme, chapéu de cogumelo que pinga, com gomos e
    bolinhas, e potes no balcão."""
    w, h = 52, 44
    s = _forma_vazia(w, h)
    contorno = _escuro(cor, 0.4)
    f = _forma_vazia(w, h)
    pygame.draw.rect(f, (255, 255, 255), (8, 20, w - 16, h - 22), border_radius=3)
    s.blit(_pintar(f, (248, 232, 200), (214, 182, 150), (255, 248, 230), (48, 20, 30), desloc=(5, 0), riscos="casca", rng=rng, n_riscos=12), (0, 0))
    s.fill((96, 52, 58), (12, 21, w - 24, 11))                           # o vão escuro da barraca, com luz quente
    s.fill((150, 84, 62), (12, 21, w - 24, 2))
    s.fill((168, 112, 64), (9, 31, w - 18, 3))                           # o balcão
    s.fill((48, 20, 30), (9, 34, w - 18, 1))
    for k, px in enumerate(range(15, w - 15, 7)):                        # potes e milho no balcão
        c = ((248, 200, 72), (232, 120, 72), (150, 200, 110), (240, 150, 170))[k % 4]
        pygame.draw.rect(s, (48, 20, 30), (px - 1, 25, 6, 7), border_radius=2)
        pygame.draw.rect(s, c, (px, 26, 4, 5), border_radius=1)
        s.set_at((px, 26), mix(c, (255, 255, 255), 0.6))
    c = _forma_vazia(w, h)
    pygame.draw.ellipse(c, (255, 255, 255), (1, 0, w - 2, 28))
    pygame.draw.rect(c, (255, 255, 255), (1, 12, w - 2, 9))
    x = 2
    while x < w - 4:
        lw = rng.randint(3, 6)
        pygame.draw.circle(c, (255, 255, 255), (x + lw // 2, 21 + rng.randint(0, 3)), lw // 2 + 1)
        x += lw
    s.blit(_pintar(c, cor, mix(cor, (90, 24, 70), 0.35), mix(cor, (255, 244, 220), 0.45), contorno, desloc=(7, 3), luz_desloc=(4, 2),
                   riscos="sorriso", rng=rng, n_riscos=10), (0, 0))
    for bx, by, r in ((12, 12, 2), (24, 7, 2), (37, 13, 3), (21, 17, 1), (44, 17, 1)):
        pygame.draw.circle(s, mix(cor, (255, 250, 236), 0.65), (bx, by), r)
    return s


def fogueira(rng):
    """Fogueira: as chamas em três camadas (as mesmas do Vale das Brasas) sobre lenha cruzada e riscada."""
    w, h = 36, 40
    s = _forma_vazia(w, h)
    for inclina, ox, a in ((-1, 2, 24), (1, 14, 26), (1, 8, 34)):
        ch = chama(10, a, rng, inclina)
        s.blit(ch, (ox, h - 8 - a))
    lenha = _forma_vazia(w, h)
    pygame.draw.line(lenha, (255, 255, 255), (4, h - 2), (31, h - 9), 5)
    pygame.draw.line(lenha, (255, 255, 255), (4, h - 9), (31, h - 2), 5)
    s.blit(_pintar(lenha, (150, 92, 56), (96, 56, 44), (190, 132, 78), (48, 22, 28), desloc=(1, 2), riscos="casca", rng=rng, n_riscos=8), (0, 0))
    return s


def _arraial(L, H, rng):
    pal = _pal_bosque(rng)
    c0 = _forma_vazia(L, H)
    _banco_nuvens(c0, rng, H * 0.6, L, 0.85, cor=(252, 220, 214), sombra=(214, 170, 200), contorno=(150, 112, 164))
    longe, perfil = _morros(L, H, rng, H * 0.7, 24, (168, 158, 196), (138, 126, 178), None, (104, 92, 146), riscos=None)
    x = rng.randint(0, 20)
    while x < L:                                                      # arvorezinhas distantes, chapadas
        a = rng.randint(12, 18)
        y = perfil[min(L, x)]
        pygame.draw.ellipse(longe, (130, 120, 170), (x - a // 3, y - a, a * 2 // 3, a))
        longe.fill((130, 120, 170), (x - 2, y - a // 2, a // 3 + 3, a // 2))
        x += rng.randint(14, 34)
    c0.blit(longe, (0, 0))
    # meio: morros, árvores, o Posto-Cogumelo de sempre, as barracas e varais de árvore em árvore
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.8, 20, (116, 172, 104), (80, 134, 96), (162, 202, 124), (36, 66, 48),
                           tufos=((60, 118, 70), (32, 84, 58), (16, 46, 32)), manchas=26)
    posto_x = rng.randint(L // 6, L // 3)
    barracas = [posto_x + 74, posto_x + 74 + 66, posto_x + L // 2 + 30]
    copas = []
    x = rng.randint(0, 30)
    while x < L:
        if abs(x - posto_x) > 46 and all(abs(x - b) > 40 for b in barracas):
            a = rng.randint(36, 52)
            arv = (arvore_bolota if rng.random() < 0.45 else arvore_gota)(a, rng, pal)
            _emendar(c1, arv, x - arv.get_width() // 2, perfil[min(L, x)] - a + 4, L)
            copas.append((x, perfil[min(L, x)] - a - 14))
        x += rng.randint(38, 70)
    # os varais ficam altos, de mastro em mastro, e deixam vãos: atrás do herói o fundo tem de continuar calmo.
    # Vêm antes do Posto e das barracas, para não passar na frente da cruz
    n = max(3, L // 100)
    mastros = [(k * L // n, perfil[k * L // n] - 62 + rng.randint(-4, 4)) for k in range(n)]
    for mx, my in mastros:
        pe = perfil[mx] + 2
        c1.fill((70, 44, 54), (mx - 1, my, 3, pe - my))
        c1.fill((190, 140, 92), (mx, my, 1, pe - my))
    for k in range(n):
        if k % 3 != 2:                                                # um vão a cada três
            a, b = mastros[k], mastros[(k + 1) % n]
            varal(c1, a, (b[0] + (L if k == n - 1 else 0), b[1]), L, rng, queda=10, lanternas=False)
    posto = posto_cogumelo(rng)
    _emendar(c1, posto, posto_x - posto.get_width() // 2, perfil[posto_x] - posto.get_height() + 6, L)
    for k, b in enumerate(barracas):
        peca = barraca_cogumelo(rng, ((232, 86, 88), (88, 150, 214), (244, 176, 66))[k % 3])
        bx = b % L
        _emendar(c1, peca, bx - peca.get_width() // 2, perfil[bx] - peca.get_height() + 6, L)
    c1.blit(meio, (0, 0))
    # perto: árvores grandes, a fogueira e o varal comprido, com lanternas
    c2 = _forma_vazia(L, H)
    perto, perfil = _morros(L, H, rng, H * 0.95, 12, (66, 112, 78), (42, 82, 66), (96, 144, 96), (16, 38, 32),
                            tufos=((40, 98, 62), (16, 60, 46), (10, 32, 24)), manchas=30)
    fx = rng.randint(L // 2, L * 3 // 4)
    copas = []
    x = rng.randint(10, 40)
    while x < L:
        if abs(x - fx) > 54:
            a = rng.randint(66, 88)
            arv = (arvore_bolota if rng.random() < 0.4 else arvore_gota)(a, rng, pal)
            _emendar(c2, arv, x - arv.get_width() // 2, perfil[min(L, x)] - a + 6, L)
            copas.append((x, perfil[min(L, x)] - a + 4))
        x += rng.randint(90, 140)
    fg = fogueira(rng)
    _emendar(c2, fg, fx - fg.get_width() // 2, perfil[fx] - fg.get_height() + 4, L)
    for tx, ty in copas:                                              # lanternas penduradas nas copas, sem varal na frente
        for dx in (-13, 15):
            fio = rng.randint(6, 12)
            lx = (tx + dx) % L
            c2.fill((70, 44, 54), (lx, ty + 8, 1, fio))
            _emendar(c2, lanterna(rng, rng.choice(((250, 150, 70), (248, 196, 84), (240, 100, 110)))), lx - 5, ty + 8 + fio, L)
    c2.blit(perto, (0, 0))
    _pontos_brilho(c2, rng, 14, H * 0.3, H * 0.75, cor=(255, 226, 150))
    return [c0, c1, c2]


# ------------------------------------------------------------------ O Jardim das Delícias (Bosch)

_EXTRAS = {}                                      # id(camada) → (peças do Paraíso, peças do Inferno): climas.Controle cruza por painel


def extras(camada):
    return _EXTRAS.get(id(camada), (None, None))


def torre_fantastica(alt, rng, cor=(240, 156, 176), sombra=(190, 96, 140), luz=(252, 212, 216), globo=(72, 116, 196)):
    """As torres do Jardim: gomos moles empilhados, gargalo fino, globo no alto e chifres que brotam dos lados."""
    w = int(alt * 0.62)
    f = _forma_vazia(w, alt)
    cx = w // 2
    pygame.draw.ellipse(f, (255, 255, 255), (cx - w * 0.42, alt * 0.56, w * 0.84, alt * 0.44))
    pygame.draw.ellipse(f, (255, 255, 255), (cx - w * 0.3, alt * 0.36, w * 0.6, alt * 0.32))
    pygame.draw.polygon(f, (255, 255, 255), [(cx - 3, alt * 0.14), (cx + 3, alt * 0.14), (cx + w * 0.14, alt * 0.44), (cx - w * 0.14, alt * 0.44)])
    for lado in (-1, 1):                          # os chifres finos, um pouco tortos
        pygame.draw.lines(f, (255, 255, 255), False, [(cx + lado * w * 0.24, alt * 0.5), (cx + lado * w * 0.42, alt * 0.38),
                                                      (cx + lado * w * 0.42, alt * rng.uniform(0.2, 0.28))], 2)
    s = _pintar(f, cor, sombra, luz, _escuro(cor, 0.55), desloc=(max(3, w // 6), 1), luz_desloc=(2, 1), riscos="sorriso", rng=rng, n_riscos=8)
    r = max(3, alt // 12)
    pygame.draw.circle(s, _escuro(globo, 0.6), (cx, r + 1), r)
    pygame.draw.circle(s, globo, (cx - 1, r), r - 1)
    s.set_at((cx - 2, r - 2), (230, 240, 250))
    for fy in (0.72, 0.84):                       # as bocas escuras das conchas
        pygame.draw.ellipse(s, _escuro(sombra, 0.55), (cx - 4 + int(fy * 9) % 5, alt * fy, 8, 5))
    return s


def morango_grande(alt, rng):
    """O morango enorme do painel central: maior que quem passa."""
    w = int(alt * 0.86)
    f = _forma_vazia(w, alt)
    pygame.draw.ellipse(f, (255, 255, 255), (0, alt * 0.12, w, alt * 0.56))
    pygame.draw.polygon(f, (255, 255, 255), [(1, alt * 0.42), (w - 1, alt * 0.42), (w // 2, alt - 1)])
    s = _pintar(f, (222, 56, 66), (152, 32, 62), (248, 120, 110), (92, 20, 44), desloc=(max(3, w // 6), 2))
    for _ in range(max(8, alt // 2)):
        x, y = rng.randint(4, w - 5), rng.randint(int(alt * 0.22), int(alt * 0.72))
        if s.get_at((x, y))[3] and s.get_at((x, y))[:3] != (92, 20, 44):
            s.set_at((x, y), (250, 214, 110))
    for k in range(5):
        a = -math.pi * k / 4
        pygame.draw.line(s, (72, 130, 76), (w // 2, int(alt * 0.14)), (w // 2 + math.cos(a) * w * 0.28, alt * 0.14 + math.sin(a) * alt * 0.12), 2)
    return s


def passaro_grande(alt, rng, cor=(248, 206, 70), asa=(150, 104, 60), peito=(238, 226, 190), mascara=(216, 52, 62)):
    """Os pássaros enormes que pousam no Jardim, parados, de perfil, com o olho redondo."""
    w = int(alt * 0.92)
    f = _forma_vazia(w, alt)
    pygame.draw.ellipse(f, (255, 255, 255), (w * 0.16, alt * 0.3, w * 0.62, alt * 0.48))
    pygame.draw.circle(f, (255, 255, 255), (int(w * 0.72), int(alt * 0.28)), max(4, int(alt * 0.17)))
    pygame.draw.polygon(f, (255, 255, 255), [(w * 0.28, alt * 0.56), (0, alt * 0.74), (w * 0.08, alt * 0.8), (w * 0.34, alt * 0.72)])
    s = _pintar(f, peito, mix(peito, (120, 70, 90), 0.35), None, _escuro(asa, 0.5), desloc=(2, 3))
    a = _forma_vazia(w, alt)
    pygame.draw.ellipse(a, (255, 255, 255), (w * 0.14, alt * 0.38, w * 0.5, alt * 0.26))
    s.blit(_pintar(a, asa, _escuro(asa, 0.7), cor, _escuro(asa, 0.45), desloc=(2, 2), riscos="sorriso", rng=rng, n_riscos=5), (0, 0))
    hx, hy, r = int(w * 0.72), int(alt * 0.28), max(4, int(alt * 0.17))
    pygame.draw.ellipse(s, mascara, (hx - r // 2, hy - r + 1, r + r // 2, r))
    pygame.draw.circle(s, (250, 246, 226), (hx + 1, hy - 1), max(2, r // 3))
    s.set_at((hx + 1, hy - 1), (24, 18, 34))
    pygame.draw.polygon(s, (214, 180, 120), [(hx + r - 1, hy - 1), (w - 1, hy + 2), (hx + r - 1, hy + 3)])
    for dx in (0.4, 0.54):                        # patas finas
        s.fill(_escuro(asa, 0.5), (int(w * dx), int(alt * 0.76), 2, alt - int(alt * 0.76)))
        s.fill(_escuro(asa, 0.5), (int(w * dx) - 2, alt - 2, 6, 2))
    return s


def bolha_vidro(r):
    """As bolhas de vidro do Jardim: quase só o contorno e o reflexo; dá para ver o fundo através."""
    s = pygame.Surface((r * 2 + 2, r * 2 + 2), SRC)
    pygame.draw.circle(s, (190, 226, 232, 70), (r + 1, r + 1), r)
    pygame.draw.circle(s, (112, 164, 186, 220), (r + 1, r + 1), r, 1)
    pygame.draw.arc(s, (250, 252, 252, 240), (4, 4, r * 2 - 6, r * 2 - 6), 1.5, 2.9, 2)
    return s


def arbusto_frutas(w, rng):
    """Moita de bolotas com frutas azuis e vermelhas enormes."""
    h = int(w * 0.62)
    f = _forma_vazia(w, h)
    x = 3
    while x < w - 4:
        r = rng.randint(max(4, w // 8), max(6, w // 5))
        pygame.draw.circle(f, (255, 255, 255), (x + r // 2, h - r - rng.randint(0, h // 4)), r)
        x += r
    f.fill((255, 255, 255), (2, h - h // 3, w - 4, h // 3))
    s = _pintar(f, (92, 152, 88), (54, 104, 78), (150, 196, 112), (28, 66, 56), desloc=(3, 3), riscos="sorriso", rng=rng, n_riscos=6)
    for _ in range(max(3, w // 12)):
        cor = rng.choice(((216, 52, 62), (72, 116, 196), (246, 170, 190)))
        fx, fy = rng.randint(4, w - 5), rng.randint(3, h - 4)
        if s.get_at((fx, fy))[3]:
            pygame.draw.circle(s, _escuro(cor, 0.5), (fx, fy), 3)
            pygame.draw.circle(s, cor, (fx, fy), 2)
    return s


def girafa(alt, rng):
    """A girafa pálida do Paraíso, de pescoço comprido."""
    w = int(alt * 0.7)
    f = _forma_vazia(w, alt)
    pygame.draw.ellipse(f, (255, 255, 255), (w * 0.08, alt * 0.48, w * 0.56, alt * 0.26))
    pygame.draw.polygon(f, (255, 255, 255), [(w * 0.46, alt * 0.56), (w * 0.62, alt * 0.56), (w * 0.86, alt * 0.12), (w * 0.76, alt * 0.08)])
    pygame.draw.ellipse(f, (255, 255, 255), (w * 0.72, 0, w * 0.28, alt * 0.14))
    for dx in (0.14, 0.26, 0.46, 0.56):
        f.fill((255, 255, 255), (int(w * dx), int(alt * 0.66), 3, alt - int(alt * 0.66)))
    s = _pintar(f, (246, 226, 206), (214, 170, 170), None, (136, 96, 116), desloc=(2, 2))
    for _ in range(14):
        x, y = rng.randint(4, w - 3), rng.randint(int(alt * 0.1), int(alt * 0.7))
        if s.get_at((x, y))[:3] == (246, 226, 206):
            pygame.draw.circle(s, (206, 150, 120), (x, y), 1)
    s.set_at((int(w * 0.88), int(alt * 0.05)), (24, 18, 34))
    return s


def elefante(alt, rng):
    """O elefante branco do Paraíso."""
    w = int(alt * 1.3)
    f = _forma_vazia(w, alt)
    pygame.draw.ellipse(f, (255, 255, 255), (0, alt * 0.12, w * 0.76, alt * 0.66))
    pygame.draw.circle(f, (255, 255, 255), (int(w * 0.78), int(alt * 0.34)), int(alt * 0.24))
    pygame.draw.lines(f, (255, 255, 255), False, [(w * 0.92, alt * 0.38), (w * 0.97, alt * 0.66), (w * 0.88, alt * 0.92)], 4)
    for dx in (0.1, 0.26, 0.48, 0.62):
        f.fill((255, 255, 255), (int(w * dx), int(alt * 0.6), max(4, w // 10), alt - int(alt * 0.6)))
    s = _pintar(f, (242, 240, 232), (196, 192, 208), None, (116, 110, 140), desloc=(3, 3))
    pygame.draw.ellipse(s, (206, 200, 214), (w * 0.62, alt * 0.2, w * 0.14, alt * 0.3))
    s.set_at((int(w * 0.84), int(alt * 0.3)), (24, 18, 34))
    s.fill((252, 250, 236), (int(w * 0.84), int(alt * 0.5), 2, 4))
    return s


def faca_gigante(alt, rng):
    w = int(alt * 0.24)
    f = _forma_vazia(w, alt)
    pygame.draw.polygon(f, (255, 255, 255), [(1, alt * 0.62), (w - 2, alt * 0.62), (w - 2, alt * 0.1), (w // 2, 0)])
    s = _pintar(f, (176, 184, 200), (98, 100, 124), (232, 236, 244), (34, 30, 44), desloc=(max(2, w // 3), 0))
    s.fill((96, 62, 48), (0, int(alt * 0.62), w, alt - int(alt * 0.62)))
    s.fill((48, 26, 30), (0, int(alt * 0.62), w, 2))
    return s


def harpa_gigante(alt, rng):
    """A harpa do Inferno, tão grande quanto uma casa."""
    w = int(alt * 0.72)
    s = _forma_vazia(w, alt)
    for k in range(1, 8):
        x = int(w * 0.14 + k * w * 0.09)
        pygame.draw.line(s, (232, 214, 150), (x, int(alt * (0.2 + k * 0.05))), (x, alt - 6))
    f = _forma_vazia(w, alt)
    pygame.draw.lines(f, (255, 255, 255), False, [(w * 0.12, alt - 2), (w * 0.08, alt * 0.3), (w * 0.3, alt * 0.06), (w * 0.62, alt * 0.2), (w * 0.94, alt * 0.56)], 6)
    pygame.draw.line(f, (255, 255, 255), (w * 0.12, alt - 3), (w * 0.94, alt - 3), 6)
    pygame.draw.line(f, (255, 255, 255), (w * 0.92, alt * 0.56), (w * 0.92, alt - 3), 5)
    s.blit(_pintar(f, (150, 92, 54), (88, 48, 44), (206, 148, 84), (36, 20, 28), desloc=(2, 2)), (0, 0))
    return s


def alaude_gigante(alt, rng):
    w = int(alt * 0.56)
    f = _forma_vazia(w, alt)
    pygame.draw.ellipse(f, (255, 255, 255), (0, alt * 0.42, w, alt * 0.58))
    pygame.draw.polygon(f, (255, 255, 255), [(w * 0.42, 0), (w * 0.6, 0), (w * 0.62, alt * 0.5), (w * 0.38, alt * 0.5)])
    s = _pintar(f, (190, 126, 64), (112, 66, 52), (232, 180, 110), (40, 22, 30), desloc=(max(3, w // 6), 2))
    pygame.draw.circle(s, (46, 26, 32), (w // 2, int(alt * 0.68)), max(3, w // 6))
    for dx in (-2, 0, 2):
        pygame.draw.line(s, (240, 226, 180), (w // 2 + dx, 3), (w // 2 + dx, int(alt * 0.9)))
    return s


def _jardim(L, H, rng):
    c0 = _forma_vazia(L, H)                            # o azul de longe de Bosch: montes e torres que somem no ar
    longe, perfil = _morros(L, H, rng, H * 0.66, 24, (150, 190, 214), (126, 170, 204), None, (106, 150, 188), riscos=None)
    x = rng.randint(0, 30)
    while x < L:
        t = torre_fantastica(rng.randint(30, 46), rng, (170, 196, 222), (138, 170, 208), (206, 222, 236), (120, 158, 204))
        _emendar(c0, t, x, perfil[min(L, x)] - t.get_height() + 6, L)
        x += rng.randint(70, 120)
    c0.blit(longe, (0, 0))
    # meio: o prado verde-claro, a lagoa, as torres rosas e azuis, os morangos e os pássaros
    c1 = _forma_vazia(L, H)
    meio, perfil = _morros(L, H, rng, H * 0.78, 16, (152, 196, 108), (112, 160, 98), (192, 222, 130), (62, 104, 76),
                           tufos=((86, 142, 88), (54, 104, 78), (28, 66, 56)), manchas=30)
    pecas = []
    x = rng.randint(10, 40)
    k = 0
    while x < L - 30:
        tipo = ("torre", "morango", "passaro", "torre_az", "bolha", "morango", "passaro2")[k % 7]
        pecas.append((tipo, x))
        x += rng.randint(52, 88)
        k += 1
    for tipo, x in pecas:
        y = perfil[min(L, x)]
        if tipo == "torre":
            p = torre_fantastica(rng.randint(66, 84), rng)
        elif tipo == "torre_az":
            p = torre_fantastica(rng.randint(58, 74), rng, (116, 156, 216), (72, 104, 176), (178, 208, 240), (240, 156, 176))
        elif tipo == "morango":
            p = morango_grande(rng.randint(30, 40), rng)
        elif tipo == "passaro":
            p = passaro_grande(rng.randint(40, 50), rng)
        elif tipo == "passaro2":                       # o martim-pescador, azul e laranja
            p = passaro_grande(rng.randint(36, 46), rng, (120, 190, 230), (54, 104, 176), (244, 170, 100), (54, 104, 176))
        else:
            p = bolha_vidro(rng.randint(14, 20))
            _emendar(c1, p, x, y - p.get_height() - 4, L)
            continue
        _emendar(c1, p, x, y - p.get_height() + 6, L)
    c1.blit(meio, (0, 0))
    # perto: a margem escura, com as moitas e as frutas enormes
    c2 = _forma_vazia(L, H)
    perto, perfil2 = _morros(L, H, rng, H * 0.94, 10, (84, 140, 90), (54, 104, 78), (122, 172, 104), (26, 60, 50),
                             tufos=((60, 118, 76), (32, 84, 62), (16, 46, 38)), manchas=26)
    x = rng.randint(0, 30)
    while x < L:
        a = arbusto_frutas(rng.randint(38, 58), rng)
        _emendar(c2, a, x, perfil2[min(L, x)] - a.get_height() + 5, L)
        x += rng.randint(64, 118)
    c2.blit(perto, (0, 0))

    # o que só existe no Paraíso (bichos soltos) e o que só existe no Inferno (instrumentos, faca, chamas)
    pa1 = _forma_vazia(L, H)
    x = rng.randint(30, 80)
    for peca in (girafa(58, rng), elefante(38, rng), girafa(50, rng)):
        _emendar(pa1, peca, x, perfil[min(L - 1, x)] - peca.get_height() + 5, L)
        x = (x + L // 3) % L
    inf1 = _forma_vazia(L, H)
    x = rng.randint(10, 60)
    for peca in (harpa_gigante(78, rng), faca_gigante(72, rng), alaude_gigante(66, rng), faca_gigante(58, rng)):
        _emendar(inf1, peca, x, perfil[min(L - 1, x)] - peca.get_height() + 6, L)
        x = (x + L // 4) % L
    inf2 = _forma_vazia(L, H)
    x = rng.randint(0, 20)
    while x < L:
        ch = chama(rng.randint(8, 14), rng.randint(22, 36), rng, rng.choice((-1, 1)))
        _emendar(inf2, ch, x, perfil2[min(L - 1, x)] - ch.get_height() + 5, L)
        x += rng.randint(34, 70)
    _EXTRAS[id(c1)] = (pa1, inf1)
    _EXTRAS[id(c2)] = (None, inf2)
    return [c0, c1, c2]


CENAS = {"bosque": _bosque, "confeitado": _confeitado, "cosmo": _cosmo, "brasas": _brasas, "gelo": _gelo,
         "mar": _mar, "enfermaria": _enfermaria, "lamancha": _lamancha, "grito": _grito, "arraial": _arraial, "jardim": _jardim}


def camadas(cena, largura, altura, seed):
    """As três camadas do cenário (cacheadas por cena, tamanho e semente)."""
    chave = (cena, largura, altura, seed)
    if chave not in _cache:
        if len(_cache) > 12:
            _cache.clear()
            _ANCORAS.clear()
            _EXTRAS.clear()
        _cache[chave] = CENAS[cena](largura, altura, random.Random(seed * 7919 + len(cena)))
    return _cache[chave]


def ceu(largura, altura, cima=(104, 200, 240), baixo=(176, 228, 246)):
    """Céu de desenho: cor chapada em três faixas de borda reta (sem degradê)."""
    s = pygame.Surface((largura, altura))
    s.fill(cima)
    s.fill(mix(cima, baixo, 0.5), (0, int(altura * 0.55), largura, altura))
    s.fill(baixo, (0, int(altura * 0.75), largura, altura))
    return s


_nuvens = {}


def nuvem_ceu(s, x, y, escala=1.0):
    """Nuvem solta do céu (no lugar de art.nuvem)."""
    k = int(escala * 10)
    if k not in _nuvens:
        _nuvens[k] = nuvem(max(24, int(48 * escala)), random.Random(k))
    s.blit(_nuvens[k], (int(x), int(y)))


# ------------------------------------------------------------------ impacto (Traço Ilha: Billy e Mandy)

_explosoes = {}


def explosao(w, h, cores=((214, 40, 52), (244, 104, 96)), miolo=(255, 250, 236), centro=None, n=26, seed=0):
    """Fundo de impacto: fatias chapadas alternando duas cores a partir do centro e um miolo claro recortado em
    pontas (explosão radial dos cartões de 'estoque' de Billy e Mandy). Na resolução da tela; fica em cache."""
    cx, cy = centro or (w // 2, h // 2)
    ch = (w, h, cores, miolo, int(cx), int(cy), n, seed)
    s = _explosoes.get(ch)
    if s is None:
        if len(_explosoes) > 12:
            _explosoes.clear()
        rng = random.Random(seed)
        s = pygame.Surface((w, h))
        s.fill(cores[0])
        R = math.hypot(max(cx, w - cx), max(cy, h - cy)) + 10
        a = rng.uniform(0, 6.28)
        for k in range(n):
            larg = math.tau / n * rng.uniform(0.35, 0.6)
            pygame.draw.polygon(s, cores[1], [(cx, cy), (cx + math.cos(a) * R, cy + math.sin(a) * R),
                                              (cx + math.cos(a + larg) * R, cy + math.sin(a + larg) * R)])
            a += math.tau / n
        r0 = min(w, h) * 0.22
        pts = []
        for k in range(36):                                                # miolo em pontas irregulares
            ang = math.tau * k / 36
            r = r0 * (1.0 if k % 2 else rng.uniform(1.35, 1.9))
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.8))
        pygame.draw.polygon(s, miolo, pts)
        _explosoes[ch] = s
    return s
