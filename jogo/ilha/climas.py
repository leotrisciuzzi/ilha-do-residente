"""Climas das fases: cada música do rodízio leva a um clima (céu, tom do cenário, astros, partículas e luz).

A fase pergunta ao áudio qual faixa está tocando (Audio.atual) e troca de clima com um véu curto quando a faixa
muda (fim da faixa, tecla N). Sem música (mudo, ou sem arquivos), o clima é sorteado pela semente da fase.

Desenho em pixel art na resolução lógica do mundo (LW×LH), em duas camadas:
- fundo: céu em faixas pontilhadas (o mesmo traço de art.ceu), estrelas, nebulosa, aurora, sol/lua/planeta e fachos de
  luz no estilo do farol do Mirante (cones pré-renderizados somados com BLEND_RGB_ADD);
- frente: partículas (chuva, neve, folhas, pétalas, bolhas, brasas, vaga-lumes, areia, confete, brilhos), raios da
  tempestade, fogos, e um halo de luz em volta do herói nos climas escuros.
O cenário (morros e mapa) é tingido UMA vez, na troca, por multiplicação (BLEND_RGB_MULT) em cópias; o herói e os
bichos ficam com a cor original, para continuarem legíveis. Por quadro só há blits e retângulos pequenos, e nada usa
NumPy (roda no Android)."""
import math
import random

import pygame

from . import art

ADD = pygame.BLEND_RGB_ADD
MULT = pygame.BLEND_RGB_MULT

# --------------------------------------------------------------------- os climas

CLIMAS = {
    "sol": dict(nome="Dia de sol", ceu=None, tom=None, astro="sol", nuvens=True,
                part=[("semente", 14)]),
    "chuva": dict(nome="Chuva", ceu=((84, 98, 128), (150, 162, 184)), tom=(150, 160, 186), nuvens=True,
                  part=[("chuva", 110)], neblina=(60, 70, 90)),
    "tempestade": dict(nome="Tempestade", ceu=((22, 24, 44), (68, 70, 96)), tom=(92, 98, 132), nuvens=True, silhueta="farol",
                       part=[("chuva_forte", 170)], raios=True, vento=-1.6, luz=(70, 70, 90)),
    "neve": dict(nome="Neve", ceu=((160, 182, 218), (226, 236, 250)), tom=(206, 220, 246), nuvens=True, silhueta="pinheiros",
                 part=[("neve", 110)]),
    "aurora": dict(nome="Aurora boreal", ceu=((6, 10, 32), (28, 52, 84)), tom=(108, 130, 176), nuvens=False, silhueta="montanhas",
                   estrelas=90, aurora=True, part=[("neve", 35)], luz=(60, 80, 70)),
    "noite": dict(nome="Noite de vaga-lumes", ceu=((12, 16, 46), (62, 58, 112)), tom=(104, 110, 172), nuvens=False, silhueta="vila",
                  estrelas=70, astro="lua", part=[("vagalume", 22)], luz=(70, 66, 40)),
    "floresta": dict(nome="Floresta encantada", ceu=((96, 150, 126), (196, 224, 168)), tom=(164, 212, 156), silhueta="arvores",
                     nuvens=True, fachos="raios", cor_facho=(110, 120, 60), part=[("esporo", 26)]),
    "outono": dict(nome="Outono", ceu=((226, 150, 106), (252, 214, 160)), tom=(246, 190, 150), nuvens=True, silhueta="outono",
                   astro="sol_baixo", part=[("folha", 50)], vento=0.5),
    "cerejeira": dict(nome="Cerejeiras", ceu=((248, 190, 210), (255, 236, 226)), tom=(255, 216, 228), nuvens=True, silhueta="torii",
                      astro="sol", part=[("petala", 60), ("vapor", 10)], vento=0.35),
    "deserto": dict(nome="Deserto", ceu=((232, 168, 84), (255, 230, 168)), tom=(255, 222, 168), nuvens=False, silhueta="piramides",
                    astro="sol_grande", part=[("areia", 70)], vento=2.2, neblina=(120, 90, 40)),
    "mar": dict(nome="Fundo do mar", ceu=((8, 44, 86), (30, 120, 150)), tom=(110, 190, 212), nuvens=False, silhueta="algas",
                fachos="raios", cor_facho=(40, 90, 100), part=[("bolha", 34), ("peixe", 6)], luz=(30, 70, 80)),
    "espaco": dict(nome="Espaço", ceu=((4, 2, 16), (30, 12, 50)), tom=(150, 128, 200), nuvens=False,
                   estrelas=160, nebulosa=True, astro="planeta", cadentes=True, part=[("poeira", 20)],
                   luz=(60, 50, 90)),
    "vulcao": dict(nome="Vulcão", ceu=((36, 8, 12), (150, 48, 28)), tom=(232, 140, 118), nuvens=False, silhueta="vulcao",
                   part=[("brasa", 55), ("cinza", 30)], brilho_chao=(90, 30, 0), luz=(90, 40, 10)),
    "praia": dict(nome="Pôr do sol na praia", ceu=((246, 112, 112), (255, 214, 140)), tom=(255, 200, 176), silhueta="coqueiros",
                  nuvens=True, astro="sol_poente", part=[("gaivota", 4), ("semente", 6)]),
    "carnaval": dict(nome="Parque à noite", ceu=((36, 16, 66), (118, 48, 118)), tom=(188, 158, 222), nuvens=False, silhueta="roda",
                     estrelas=50, fachos="holofotes", fogos=True, part=[("confete", 55)], luz=(80, 50, 80)),
    # The Cure: preto e branco com vermelho, lua enorme, catedral com facho girando, lampiões, corvos e rosas
    "gotico": dict(nome="Noite gótica", ceu=((3, 2, 6), (32, 24, 40)), tom=(58, 54, 70), nuvens=False,
                   astro="lua_grande", silhueta="catedral", part=[("petala_rosa", 26), ("corvo", 4), ("cinza", 12)],
                   neblina=(40, 32, 48), luz=(70, 60, 80), pb=True),
    "cristal": dict(nome="Caverna de cristal", ceu=((18, 8, 38), (70, 38, 110)), tom=(150, 128, 212), nuvens=False, silhueta="colunas",
                    part=[("brilho", 30), ("poeira", 24)], luz=(70, 50, 100), cristais=True),
    # --- climas temáticos (trilhas originais "32 bits" em tools/partituras.py)
    # ficção científica de TV dos anos 70: céu pintado de magenta e laranja, rochas de isopor, planeta verde,
    # nave da frota cruzando o céu e o brilho dourado do teletransporte
    "frota": dict(nome="Planeta da Frota (anos 70)", ceu=((58, 14, 82), (238, 112, 92)), tom=(236, 174, 214),
                  nuvens=False, estrelas=55, astro="planeta_verde", silhueta="rochas_alien",
                  part=[("tele", 20)], extra="nave", luz=(60, 40, 70)),
    # Japão feudal: sol vermelho no crepúsculo, castelo de telhados curvos, monte nevado, pinheiros e bambus
    "samurai": dict(nome="Japão feudal", ceu=((142, 36, 50), (252, 184, 124)), tom=(244, 186, 168), nuvens=True,
                    astro="sol_vermelho", silhueta="castelo_jp", part=[("folha_bordo", 42)], vento=0.7,
                    neblina=(70, 36, 40)),
    # cyberpunk: megacidade de noite, letreiros de neon, chuva colorida, carros voadores e um peixe holográfico
    "neon": dict(nome="Megacidade neon", ceu=((8, 4, 24), (92, 22, 88)), tom=(150, 112, 206), nuvens=False,
                 silhueta="megacidade", part=[("chuva_neon", 95), ("carro", 6)], vento=-0.5,
                 fachos="holofotes", cor_holofotes=[(80, 20, 70), (10, 70, 90), (70, 60, 10)], extra="holograma",
                 neblina=(46, 8, 58), luz=(80, 30, 90)),
    # colônia de fronteira: poeira laranja, dois sóis, base de colonos com farol piscando, cristais azuis e a
    # colmeia alienígena com o tapete roxo; nave de desembarque passando
    "colonia": dict(nome="Colônia de fronteira", ceu=((86, 32, 22), (228, 142, 82)), tom=(238, 172, 134), nuvens=False,
                    astro="sois_duplos", silhueta="colonia", part=[("areia", 46), ("esporo_roxo", 14)], vento=1.3,
                    neblina=(90, 48, 26), extra="nave_drop"),
    # masmorra rúnica: fortaleza de pedra e ferro, runas acesas, portal girando, lava no chão e brasas
    "runico": dict(nome="Fortaleza rúnica", ceu=((14, 10, 8), (72, 48, 30)), tom=(152, 120, 94), nuvens=False,
                   silhueta="fortaleza", part=[("brasa", 40), ("cinza", 22)], brilho_chao=(80, 30, 0),
                   luz=(80, 50, 22), extra="portal"),
    # reino de fantasia: tarde dourada, castelo de torres azuis com bandeiras, moinho girando, faíscas de magia
    "reino": dict(nome="Reino de fantasia", ceu=((70, 112, 192), (252, 216, 160)), tom=(252, 228, 194), nuvens=True,
                  astro="sol_baixo", silhueta="castelo_reino", fachos="raios", cor_facho=(90, 80, 40),
                  part=[("faisca", 24), ("folha", 8)], vento=0.3, extra="moinho"),
}

# título da faixa (Audio.nome sem o autor) → clima
FAIXA_CLIMA = {
    "Ilha Ensolarada": "sol", "Pradarias": "sol", "Campo dos Sonhos": "sol", "Tema da Vila": "sol",
    "Aventura Chiptune 1": "sol", "Aventura Chiptune 2": "sol", "Hino à Alegria": "sol",
    "Chuva Azul": "chuva", "Lo-fi Tranquilo": "chuva",
    "Olho da Tempestade": "tempestade", "Ação Chiptune 1": "tempestade", "Ação Chiptune 2": "tempestade",
    "Neve Caindo": "neve", "Für Elise": "neve",
    "Vila do Gelo": "aurora", "Cânone em Ré": "aurora",
    "Noites na Pradaria": "noite", "Canção de Ninar Feliz": "noite",
    "A Floresta": "floresta", "Minueto em Sol": "floresta",
    "Noite de Outono": "gotico", "A Velha Taverna": "outono",       # Noite de Outono é gothic doom metal
    "Vila das Termas": "cerejeira",
    "Caravana": "deserto",
    "Vila Submersa": "mar",
    "Templo Galáctico": "espaco",
    "Fase do Fogo": "vulcao", "Castelo da Prova": "vulcao",
    "Praia": "praia", "Tiki Encantado": "praia", "Bossa 8-bit": "praia",
    "Parque de Diversões": "carnaval", "Corrida do Residente": "carnaval",
    "Caverna de Cristal": "cristal", "Caverna do Plantão": "cristal",
    "Fronteira Final": "frota", "Caminho do Samurai": "samurai", "Neon da Megacidade": "neon",
    "Colônia Fronteiriça": "colonia", "Portal Rúnico": "runico", "Reino em Guerra": "reino",
}
# faixas curtas tocam mais de uma vez seguida, para o clima não trocar depressa demais
VOLTAS = {"Parque de Diversões": 2, "Canção de Ninar Feliz": 1, "Aventura Chiptune 1": 1, "Olho da Tempestade": 1,
          "Caverna de Cristal": 1, "Neve Caindo": 1, "Reino em Guerra": 1}


def titulo(nome):
    """'Kistol - Neve Caindo' → 'Neve Caindo'."""
    return nome.split(" - ", 1)[1] if nome and " - " in nome else (nome or "")


def de_faixa(nome):
    """Clima da faixa. No Android as faixas viram 'faixa07 - chuva' (sem o nome da obra): o título já é o clima."""
    t = titulo(nome)
    return FAIXA_CLIMA.get(t) or (t if t in CLIMAS else None)


# --------------------------------------------------------------------- peças pré-renderizadas (cache do módulo)

_cache = {}


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def halo(r, cor):
    """Brilho redondo para somar (fundo preto)."""
    ch = ("halo", r, cor)
    if ch not in _cache:
        s = pygame.Surface((2 * r + 1, 2 * r + 1))
        for y in range(2 * r + 1):
            for x in range(2 * r + 1):
                d = math.hypot(x - r, y - r) / (r + 0.5)
                if d < 1:
                    k = (1 - d) ** 1.8
                    s.set_at((x, y), tuple(int(c * k) for c in cor))
        _cache[ch] = s
    return _cache[ch]


def _ceu(topo, base, lw, lh):
    ch = ("ceu", topo, base, lw, lh)
    if ch not in _cache:
        _cache[ch] = art.ceu({"ceu_topo": topo, "ceu_base": base}, lw, lh)
    return _cache[ch]


def _estrelas(n, lw, lh, seed):
    ch = ("estrelas", n, lw, lh, seed)
    if ch not in _cache:
        rng = random.Random(seed)
        s = pygame.Surface((lw, lh))
        pts = []
        for _ in range(n):
            x, y = rng.randrange(lw), int(lh * 0.75 * rng.random() ** 1.3)
            b = rng.choice((90, 130, 170, 220))
            cor = _mix((b, b, b), rng.choice([(255, 220, 180), (180, 200, 255), (255, 255, 255)]), 0.3)
            s.set_at((x, y), cor)
            if b > 200 and rng.random() < 0.4:
                pts.append((x, y))
        _cache[ch] = (s, pts)
    return _cache[ch]


def _nebulosa(lw, lh, seed):
    ch = ("nebulosa", lw, lh, seed)
    if ch not in _cache:
        rng = random.Random(seed + 7)
        s = pygame.Surface((lw, lh))
        for _ in range(26):
            r = rng.randint(10, 30)
            cor = rng.choice([(26, 8, 40), (10, 16, 44), (34, 10, 30), (8, 26, 36)])
            x = int(lw * (0.2 + 0.6 * rng.random()) + rng.gauss(0, lw * 0.08))
            y = int(lh * (0.15 + 0.3 * rng.random()))
            s.blit(halo(r, cor), (x - r, y - r), special_flags=ADD)
        _cache[ch] = s
    return _cache[ch]


def _aurora(lw, lh, seed, cor_baixo, cor_cima):
    """Uma cortina larga (2×LW) que rola: colunas verticais com degradê, base ondulando."""
    ch = ("aurora", lw, lh, seed, cor_baixo)
    if ch not in _cache:
        rng = random.Random(seed)
        w, h = lw * 2, int(lh * 0.55)
        s = pygame.Surface((w, h))
        f1, f2, p1, p2 = rng.uniform(1.5, 2.5), rng.uniform(4, 6), rng.uniform(0, 6), rng.uniform(0, 6)
        for x in range(w):
            u = x / w * 2 * math.pi
            base = h * (0.62 + 0.16 * math.sin(f1 * u + p1) + 0.07 * math.sin(f2 * u + p2))
            alto = h * (0.30 + 0.18 * (0.5 + 0.5 * math.sin(3 * u + p2)))
            forca = 0.55 + 0.45 * math.sin(7 * u + p1) ** 2
            for i in range(int(alto)):
                y = int(base - i)
                if 0 <= y < h:
                    t = i / alto
                    k = forca * (1 - t) ** 1.2 * (0.6 if x % 2 else 1.0)
                    c = _mix(cor_baixo, cor_cima, t)
                    s.set_at((x, y), tuple(int(v * k) for v in c))
        _cache[ch] = s
    return _cache[ch]


def _cone(comp, abre, cor):
    """Facho no estilo do farol: aponta para cima a partir de (meio, baixo), abre com a distância, fundo preto."""
    ch = ("cone", comp, abre, cor)
    if ch not in _cache:
        meia_max = int(1 + abre * comp)
        s = pygame.Surface((2 * meia_max + 3, comp))
        cx = meia_max + 1
        for i in range(comp):
            u = i / comp
            meia = 1 + abre * i
            k = (1 - u) ** 1.3
            y = comp - 1 - i
            for dx in range(-int(meia), int(meia) + 1):
                borda = 1 - (abs(dx) / (meia + 1)) ** 2
                c = tuple(int(v * k * borda) for v in cor)
                if c[0] or c[1] or c[2]:
                    s.set_at((cx + dx, y), c)
        _cache[ch] = s
    return _cache[ch]


def _cone_girado(comp, abre, cor, ang):
    ang = int(round(ang / 4.0)) * 4                 # 4° por passo: poucas superfícies em cache
    ch = ("cone_g", comp, abre, cor, ang)
    if ch not in _cache:
        base = _cone(comp, abre, cor)
        g = pygame.transform.rotate(base, ang)
        # ponto de origem (base do cone) depois da rotação, para posicionar o facho pela base
        r = math.radians(ang)
        ox, oy = 0, base.get_height() / 2           # do centro até a base, antes de girar
        bx = ox * math.cos(r) + oy * math.sin(r)
        by = -ox * math.sin(r) + oy * math.cos(r)
        _cache[ch] = (g, g.get_width() / 2 + bx, g.get_height() / 2 + by)
    return _cache[ch]


def _faixa_luz(w, h, cor, incl):
    """Raio de luz vindo de cima, inclinado (floresta, fundo do mar): some para baixo."""
    ch = ("faixa", w, h, cor, incl)
    if ch not in _cache:
        s = pygame.Surface((w + int(abs(incl) * h) + 2, h))
        for y in range(h):
            k = (1 - y / h) ** 1.5
            x0 = int(incl * y) if incl > 0 else int(abs(incl) * (h - y))
            for x in range(w):
                borda = 1 - (abs(x - w / 2) / (w / 2 + 1)) ** 2
                c = tuple(int(v * k * borda) for v in cor)
                if c[0] or c[1] or c[2]:
                    s.set_at((x0 + x, y), c)
        _cache[ch] = s
    return _cache[ch]


def _sprite_astro(tipo):
    ch = ("astro", tipo)
    if ch in _cache:
        return _cache[ch]
    if tipo in ("sol", "sol_baixo", "sol_grande"):
        r = {"sol": 9, "sol_baixo": 11, "sol_grande": 15}[tipo]
        s = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 236, 160), (r, r), r)
        pygame.draw.circle(s, (255, 250, 214), (r - r // 4, r - r // 4), r // 2)
    elif tipo == "sol_poente":
        r = 22
        s = pygame.Surface((2 * r + 1, r + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 196, 110), (r, r), r)
        for i, y in enumerate(range(r // 2, r + 1, 4)):      # faixas recortadas do sol retrô
            s.fill((0, 0, 0, 0), (0, y, 2 * r + 1, 1 + i // 2))
        for y in range(0, r // 2):
            pygame.draw.line(s, (255, 236, 160), (r - int(math.sqrt(max(0, r * r - (r - y) ** 2))), y),
                             (r + int(math.sqrt(max(0, r * r - (r - y) ** 2))), y))
    elif tipo == "lua_grande":                              # lua cheia enorme, pálida, com crateras
        r = 17
        s = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (232, 230, 236), (r, r), r)
        pygame.draw.circle(s, (250, 250, 252), (r - 4, r - 4), r - 7)
        for cx_, cy_, rr in ((r + 5, r + 3, 4), (r - 6, r + 7, 3), (r + 2, r - 8, 2), (r + 9, r - 3, 2)):
            pygame.draw.circle(s, (200, 198, 206), (cx_, cy_), rr)
    elif tipo == "lua":
        r = 8
        s = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (240, 236, 210), (r, r), r)
        pygame.draw.circle(s, (0, 0, 0, 0), (r + 4, r - 2), r - 1)
        s.set_at((r - 4, r + 2), (200, 196, 176))
    elif tipo == "planeta_verde":                           # planeta pintado de cenário de TV, com lua pequena
        s = pygame.Surface((52, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, (70, 170, 140), (22, 22), 16)
        for y, c in ((12, (110, 210, 170)), (17, (50, 140, 120)), (24, (90, 196, 160)), (29, (40, 120, 110))):
            for x in range(6, 39):
                if (x - 22) ** 2 + (y - 22) ** 2 < 15 ** 2:
                    s.fill(c, (x, y, 1, 2))
        pygame.draw.circle(s, (170, 240, 210), (16, 16), 4)
        pygame.draw.circle(s, (250, 220, 190), (45, 7), 5)
        pygame.draw.circle(s, (210, 170, 150), (47, 9), 2)
    elif tipo == "sol_vermelho":                            # o disco vermelho do crepúsculo, sem brilho
        r = 19
        s = pygame.Surface((2 * r + 1, 2 * r + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (220, 40, 44), (r, r), r)
        pygame.draw.circle(s, (240, 70, 60), (r - 2, r - 2), r - 6)
    elif tipo == "sois_duplos":                             # dois sóis: um grande laranja e um pequeno branco
        s = pygame.Surface((46, 30), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 170, 80), (14, 15), 13)
        pygame.draw.circle(s, (255, 214, 140), (11, 12), 6)
        pygame.draw.circle(s, (255, 250, 236), (39, 7), 5)
    else:                                                   # planeta com anel
        s = pygame.Surface((44, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (150, 120, 200), (2, 9, 40, 9), 1)
        pygame.draw.circle(s, (200, 130, 110), (22, 13), 10)
        pygame.draw.circle(s, (230, 170, 140), (19, 10), 5)
        for y in (9, 14, 17):
            pygame.draw.line(s, (170, 104, 96), (14, y), (30, y))
        pygame.draw.arc(s, (190, 160, 236), (2, 9, 40, 9), math.pi, 2 * math.pi, 1)
    _cache[ch] = s
    return s


def _cristais(lw, lh, seed):
    """Cristais pendurados no alto da tela (estalactites roxas que brilham)."""
    ch = ("cristais", lw, lh, seed)
    if ch not in _cache:
        rng = random.Random(seed + 3)
        s = pygame.Surface((lw, lh // 4), pygame.SRCALPHA)
        x = rng.randint(0, 10)
        while x < lw:
            h = rng.randint(6, lh // 5)
            w = rng.randint(3, 6)
            cor = rng.choice([(150, 110, 230), (110, 160, 240), (200, 120, 220)])
            pygame.draw.polygon(s, cor, [(x, 0), (x + w, 0), (x + w // 2, h)])
            pygame.draw.line(s, _mix(cor, (255, 255, 255), 0.6), (x + 1, 0), (x + w // 2, h - 2))
            x += rng.randint(8, 22)
        _cache[ch] = s
    return _cache[ch]


# --------------------------------------------------------------------- silhuetas do horizonte

def _silhueta(tipo, lw, lh, cor, seed):
    """Paisagem distante de cada clima, desenhada atrás dos morros. Devolve (superfície, luzes), em que luzes são
    pontos (x, y, cor) que piscam por quadro (janelas, lâmpadas da roda-gigante, cratera, lanterna do farol)."""
    ch = ("silhueta", tipo, lw, lh, cor, seed)
    if ch in _cache:
        return _cache[ch]
    rng = random.Random(seed + 11)
    s = pygame.Surface((lw, lh), pygame.SRCALPHA)
    luzes = []
    chao = int(lh * 0.5)                                   # os morros cobrem daqui para baixo
    claro = _mix(cor, (255, 255, 255), 0.25)
    poly, line, circ = pygame.draw.polygon, pygame.draw.line, pygame.draw.circle

    def pinheiro(x, h, neve):
        for k in range(4):
            larg = int(h * (0.22 + 0.1 * k))
            topo = chao - h + int(h * 0.22 * k)
            poly(s, cor, [(x, topo), (x - larg // 2, topo + int(h * 0.35)), (x + larg // 2, topo + int(h * 0.35))])
            if neve:
                line(s, (236, 244, 255), (x - 1, topo + 2), (x - larg // 4, topo + int(h * 0.2)))
        s.fill(cor, (x - 1, chao - 4, 3, 6))

    if tipo == "farol":
        chao += int(lh * 0.16)                                  # o farol fica num rochedo mais baixo, inteiro na tela
        poly(s, cor, [(int(lw * 0.62), chao + 6), (int(lw * 0.7), chao - 26), (int(lw * 0.86), chao - 30),
                      (int(lw * 0.98), chao + 6)])
        x = int(lw * 0.8)
        poly(s, cor, [(x - 8, chao - 28), (x + 8, chao - 28), (x + 5, chao - 84), (x - 5, chao - 84)])
        for y in range(chao - 76, chao - 28, 12):
            s.fill(claro, (x - 6, y, 12, 4))
        s.fill(cor, (x - 7, chao - 96, 14, 12))
        s.fill(cor, (x - 4, chao - 103, 8, 7))
        luzes.append((x, chao - 90, (255, 230, 150)))
    elif tipo in ("pinheiros", "montanhas"):
        if tipo == "montanhas":
            for mx, mh in ((0.18, 0.38), (0.5, 0.48), (0.82, 0.34)):
                px, pt = int(lw * mx), chao - int(lh * mh)
                poly(s, cor, [(px - int(lw * 0.24), chao), (px, pt), (px + int(lw * 0.24), chao)])
                poly(s, (220, 232, 250), [(px, pt), (px - 9, pt + 12), (px - 3, pt + 9), (px + 2, pt + 13), (px + 9, pt + 11)])
        x = 6
        while x < lw - 6:
            pinheiro(x, rng.randint(40, 66), tipo == "pinheiros")
            x += rng.randint(14, 30)
    elif tipo == "vila":
        x = int(lw * 0.08)
        while x < lw * 0.92:
            w, h = rng.randint(16, 26), rng.randint(32, 48)
            s.fill(cor, (x, chao - h, w, h + 6))
            poly(s, cor, [(x - 2, chao - h), (x + w // 2, chao - h - 10), (x + w + 2, chao - h)])
            for j in range(rng.randint(1, 2)):
                wx, wy = x + 3 + j * 8, chao - h + 4
                if wx + 3 < x + w:
                    luzes.append((wx, wy, (255, 200, 110)))
            x += w + rng.randint(4, 18)
    elif tipo in ("arvores", "outono"):
        x = 4
        while x < lw - 4:
            h = rng.randint(50, 78)
            s.fill(cor, (x - 2, chao - h + 10, 5, h))
            copa = cor if tipo == "arvores" else rng.choice([(200, 110, 70), (220, 140, 70), (180, 90, 70)])
            copa = _mix(copa, cor, 0.5) if tipo == "outono" else copa
            for _ in range(5):
                circ(s, copa, (x + rng.randint(-9, 9), chao - h + rng.randint(-4, 10)), rng.randint(7, 12))
            x += rng.randint(18, 34)
    elif tipo == "torii":
        x = int(lw * 0.3)
        verm = _mix((200, 60, 70), cor, 0.35)
        s.fill(verm, (x - 18, chao - 56, 5, 62))
        s.fill(verm, (x + 13, chao - 56, 5, 62))
        s.fill(verm, (x - 26, chao - 62, 52, 5))
        s.fill(verm, (x - 21, chao - 50, 42, 4))
        for cx_ in (int(lw * 0.08), int(lw * 0.62), int(lw * 0.86)):
            s.fill(cor, (cx_ - 2, chao - 44, 5, 50))
            for _ in range(9):
                circ(s, _mix((255, 170, 200), cor, 0.3), (cx_ + rng.randint(-16, 16), chao - 50 + rng.randint(-10, 8)),
                     rng.randint(7, 12))
    elif tipo == "piramides":
        for px, ph in ((0.3, 0.3), (0.52, 0.22), (0.78, 0.36)):
            x, h = int(lw * px), int(lh * ph)
            poly(s, cor, [(x - h, chao), (x, chao - h), (x + h, chao)])
            poly(s, claro, [(x, chao - h), (x + h, chao), (x + h // 3, chao)])
    elif tipo == "algas":
        x = 3
        while x < lw:
            h = rng.randint(40, 92)
            f = rng.uniform(0.15, 0.3)
            for y in range(h):
                xx = x + int(3 * math.sin(y * f))
                s.fill(cor, (xx, chao + 6 - y, 2, 1))
            x += rng.randint(6, 16)
        for _ in range(6):
            circ(s, _mix((240, 120, 140), cor, 0.4), (rng.randrange(lw), chao + 2), rng.randint(4, 8))
    elif tipo == "vulcao":
        x = int(lw * 0.62)
        topo = chao - int(lh * 0.42)
        poly(s, cor, [(x - int(lw * 0.36), chao + 6), (x - 12, topo), (x + 12, topo), (x + int(lw * 0.36), chao + 6)])
        for k in range(3):
            xx = x - 6 + k * 6
            for y in range(topo, topo + 30 + k * 12):
                s.set_at((xx + int(2 * math.sin(y * 0.3 + k)), y), (255, 110 + k * 30, 40))
        luzes.append((x, topo, (255, 120, 40)))
    elif tipo == "coqueiros":
        for px, alt, d in ((0.06, 78, 1), (0.16, 62, 1), (0.88, 84, -1)):
            x0 = int(lw * px)
            pts = [(x0 + int(d * 8 * (i / 10) ** 2), chao + 6 - int(alt * i / 10)) for i in range(11)]
            pygame.draw.lines(s, cor, False, pts, 3)
            tx, ty = pts[-1]
            for a in (-2.6, -2.0, -1.2, -0.5, 0.1):
                ex, ey = tx + int(18 * math.cos(a)), ty + int(18 * math.sin(a)) + 6
                pygame.draw.lines(s, cor, False, [(tx, ty), ((tx + ex) // 2, min(ty, ey) - 3), (ex, ey)], 2)
    elif tipo == "roda":
        x, y, r = int(lw * 0.72), chao - 52, 40
        cor = claro = _mix(cor, (255, 220, 255), 0.35)
        circ(s, cor, (x, y), r, 2)
        for k in range(12):
            a = 2 * math.pi * k / 12
            ex, ey = x + int(r * math.cos(a)), y + int(r * math.sin(a))
            line(s, cor, (x, y), (ex, ey))
            luzes.append((ex, ey, rng.choice(_CONFETE)))
        poly(s, cor, [(x - 4, y), (x - 22, chao + 6), (x - 16, chao + 6)])
        poly(s, cor, [(x + 4, y), (x + 22, chao + 6), (x + 16, chao + 6)])
        tx = int(lw * 0.25)                                           # tenda listrada
        poly(s, cor, [(tx - 30, chao + 6), (tx, chao - 38), (tx + 30, chao + 6)])
        for k in range(-2, 3):
            line(s, claro, (tx, chao - 38), (tx + k * 12, chao + 6))
        luzes.append((tx, chao - 39, (255, 220, 120)))
    elif tipo == "catedral":                                  # catedral gótica, árvores mortas e cruzes
        x0 = int(lw * 0.56)
        s.fill(cor, (x0, chao - 46, 52, 52))
        poly(s, cor, [(x0 - 2, chao - 46), (x0 + 26, chao - 70), (x0 + 54, chao - 46)])
        for tx, th in ((x0 - 8, 92), (x0 + 52, 78)):                 # duas torres pontudas
            s.fill(cor, (tx, chao - th + 14, 12, th - 8))
            poly(s, cor, [(tx - 1, chao - th + 14), (tx + 6, chao - th - 10), (tx + 13, chao - th + 14)])
            line(s, cor, (tx + 6, chao - th - 10), (tx + 6, chao - th - 16))
            line(s, cor, (tx + 3, chao - th - 13), (tx + 9, chao - th - 13))
            for k in range(3):                                         # janelas em arco
                wy = chao - th + 22 + k * 16
                s.fill((0, 0, 0, 0), (tx + 4, wy, 4, 8))
        luzes.append((x0 - 2, chao - 78 + 4, (220, 210, 190)))         # sino da torre (facho)
        pygame.draw.circle(s, (0, 0, 0, 0), (x0 + 26, chao - 38), 7)    # rosácea (acesa em vermelho)
        luzes.append((x0 + 26, chao - 38, (200, 20, 40)))
        for k in range(4):                                             # vitrais estreitos
            s.fill((0, 0, 0, 0), (x0 + 8 + k * 12, chao - 24, 3, 10))
        for ax in (int(lw * 0.08), int(lw * 0.3), int(lw * 0.9)):      # árvores mortas
            line(s, cor, (ax, chao + 6), (ax, chao - 34), 3)
            for k in range(5):
                by_ = chao - 12 - k * 5
                d = 1 if k % 2 else -1
                ex = ax + d * (8 + k * 2)
                line(s, cor, (ax, by_), (ex, by_ - 6), 1)
                line(s, cor, (ex, by_ - 6), (ex + d * 3, by_ - 10), 1)
        for cx_ in (int(lw * 0.18), int(lw * 0.22), int(lw * 0.42)):   # cruzes do cemitério
            s.fill(cor, (cx_, chao - 10, 2, 16))
            s.fill(cor, (cx_ - 3, chao - 6, 8, 2))
    elif tipo == "colunas":
        x = 5
        while x < lw:
            w, h = rng.randint(12, 24), rng.randint(44, 100)
            c = rng.choice([(120, 90, 200), (90, 130, 210), (170, 100, 200)])
            c = _mix(c, cor, 0.35)
            poly(s, c, [(x, chao + 6), (x + w // 2, chao + 6 - h), (x + w, chao + 6)])
            line(s, _mix(c, (255, 255, 255), 0.5), (x + w // 2, chao + 6 - h), (x + w // 2 - 1, chao))
            if rng.random() < 0.5:
                luzes.append((x + w // 2, chao + 6 - h, (200, 170, 255)))
            x += w + rng.randint(4, 20)
    else:
        _silhueta_tema(tipo, s, luzes, lw, lh, chao - SOBE_TEMA, cor, claro, rng)
    _cache[ch] = (s, luzes)
    return _cache[ch]


# pontos fixos das peças animadas de cada silhueta (frações de LW, alturas a partir do chão do horizonte)
ANCORA = {"portal": (0.5, 30), "moinho": (0.17, 52)}
SOBE_TEMA = 24                    # as silhuetas temáticas ficam mais altas, para os morros não esconderem a base


def _silhueta_tema(tipo, s, luzes, lw, lh, chao, cor, claro, rng):
    """Silhuetas dos climas temáticos (frota, samurai, neon, colônia, rúnico, reino)."""
    poly, line, circ, ell = pygame.draw.polygon, pygame.draw.line, pygame.draw.circle, pygame.draw.ellipse
    escuro = _mix(cor, (0, 0, 0), 0.35)
    if tipo == "rochas_alien":                 # rochedos de isopor pintado: agulhas, mesas e um arco natural
        x = -4
        while x < lw:
            w, h = rng.randint(16, 34), rng.randint(18, 46)
            pts = [(x, chao + 6)]
            for k in range(1, 6):
                pts.append((x + w * k // 6 + rng.randint(-3, 3), chao + 6 - h + rng.randint(0, h // 2) * (k % 2)))
            pts.append((x + w, chao + 6))
            poly(s, cor, pts)
            line(s, claro, pts[1], pts[2])
            x += w - rng.randint(2, 8)
        for fx, h in ((0.12, 62), (0.84, 54)):                       # agulhas
            px = int(lw * fx)
            poly(s, escuro, [(px - 7, chao + 6), (px - 2, chao - h), (px + 1, chao - h - 6), (px + 4, chao - h + 4),
                             (px + 8, chao + 6)])
            line(s, claro, (px - 2, chao - h), (px - 5, chao))
        mx = int(lw * 0.42)                                          # mesa achatada
        poly(s, cor, [(mx - 30, chao + 6), (mx - 22, chao - 34), (mx + 22, chao - 36), (mx + 30, chao + 6)])
        s.fill(claro, (mx - 22, chao - 36, 44, 2))
        ax = int(lw * 0.66)                                          # arco natural
        poly(s, escuro, [(ax - 24, chao + 6), (ax - 20, chao - 40), (ax + 20, chao - 44), (ax + 24, chao + 6),
                         (ax + 12, chao + 6), (ax + 9, chao - 22), (ax - 9, chao - 22), (ax - 12, chao + 6)])
        ell(s, (0, 0, 0, 0), (ax - 10, chao - 30, 20, 16))
        for _ in range(5):                                           # cristais cor-de-rosa que brilham
            luzes.append((rng.randrange(lw), chao - rng.randint(2, 14), rng.choice([(255, 120, 200), (255, 200, 120)])))
    elif tipo == "castelo_jp":                 # monte nevado ao fundo, castelo de três telhados, pinheiros e bambus
        fx = int(lw * 0.22)
        longe = _mix(cor, (255, 220, 220), 0.35)
        poly(s, longe, [(fx - 70, chao + 6), (fx - 10, chao - 58), (fx + 10, chao - 58), (fx + 70, chao + 6)])
        poly(s, (250, 240, 244), [(fx - 10, chao - 58), (fx + 10, chao - 58), (fx + 20, chao - 46), (fx + 11, chao - 49),
                                  (fx + 4, chao - 43), (fx - 4, chao - 48), (fx - 12, chao - 44), (fx - 21, chao - 47)])
        cx = int(lw * 0.64)
        poly(s, claro, [(cx - 30, chao + 6), (cx - 24, chao - 16), (cx + 24, chao - 16), (cx + 30, chao + 6)])  # base de pedra
        for k in range(0, 34, 6):
            line(s, cor, (cx - 27 + k // 3, chao - 16 + k // 2 + 3), (cx + 27 - k // 3, chao - 16 + k // 2 + 3))
        y = chao - 16
        for k, (w, h) in enumerate(((40, 13), (30, 11), (20, 10))):
            s.fill(cor, (cx - w // 2, y - h, w, h))
            for jx in range(cx - w // 2 + 3, cx + w // 2 - 2, 6):                       # janelas acesas
                luzes.append((jx, y - h // 2, (255, 200, 120)))
            tw = w + 14                                                             # telhado com beirais virados
            poly(s, escuro, [(cx - tw // 2 - 3, y - h - 1), (cx - tw // 2 + 4, y - h - 6), (cx + tw // 2 - 4, y - h - 6),
                             (cx + tw // 2 + 3, y - h - 1), (cx + tw // 2 - 2, y - h + 1), (cx - tw // 2 + 2, y - h + 1)])
            y -= h + 5
        poly(s, escuro, [(cx - 6, y + 1), (cx, y - 6), (cx + 6, y + 1)])
        for gx in (cx - 5, cx + 5):                                                 # peixes dourados do telhado
            s.fill((240, 190, 70), (gx - 1, y - 2, 2, 2))
        for px_ in (int(lw * 0.42), int(lw * 0.86), int(lw * 0.95)):                 # pinheiros-guarda-chuva
            line(s, escuro, (px_, chao + 6), (px_ + 3, chao - 26), 3)
            for k, (ox, oy, w) in enumerate(((-6, -30, 22), (6, -36, 18), (-2, -42, 14))):
                ell(s, escuro, (px_ + ox - w // 2, chao + oy, w, 6))
        for bx in range(2, int(lw * 0.1), 4):                                       # bambuzal
            h = rng.randint(50, 80)
            line(s, escuro, (bx, chao + 6), (bx, chao - h), 2)
            for ny in range(chao - h + 6, chao, 9):
                s.fill(claro, (bx - 1, ny, 3, 1))
            line(s, escuro, (bx, chao - h + 4), (bx + 5, chao - h + 1))
    elif tipo == "megacidade":                 # torres com janelas, pirâmide-arcologia, letreiros de neon e antenas
        neons = [(255, 60, 180), (40, 240, 255), (255, 220, 60), (160, 90, 255)]
        fundo = _mix(cor, (40, 10, 70), 0.5)
        x = -2
        while x < lw:                                                               # fileira de trás
            w, h = rng.randint(10, 20), rng.randint(50, 86)
            s.fill(fundo, (x, chao + 6 - h, w, h))
            x += w + rng.randint(0, 3)
        pxm = int(lw * 0.55)
        poly(s, escuro, [(pxm - 34, chao + 6), (pxm - 4, chao - 84), (pxm + 4, chao - 84), (pxm + 34, chao + 6)])
        for k in range(8):
            yy = chao - 76 + k * 10
            meia = 4 + (yy - (chao - 84)) * 30 // 90
            s.fill(_mix(neons[1], escuro, 0.55), (pxm - meia, yy, 2 * meia, 1))
        luzes.append((pxm, chao - 86, (255, 40, 40)))
        x = 0
        while x < lw:                                                               # fileira da frente
            w, h = rng.randint(14, 26), rng.randint(30, 70)
            if abs(x + w / 2 - pxm) < 20:
                x += w
                continue
            s.fill(cor, (x, chao + 6 - h, w, h))
            for wy in range(chao + 8 - h, chao + 4, 4):
                for wx in range(x + 2, x + w - 1, 3):
                    if rng.random() < 0.35:
                        s.set_at((wx, wy), _mix(rng.choice([(255, 210, 140), (120, 230, 255), (255, 120, 200)]), cor, 0.4))
            if rng.random() < 0.55:                                                 # letreiro vertical
                c = rng.choice(neons)
                lx, ly, lh_ = x + rng.randint(1, max(1, w - 5)), chao + 6 - h + rng.randint(4, 12), rng.randint(10, 20)
                s.fill(_mix(c, (0, 0, 0), 0.6), (lx - 1, ly - 1, 6, lh_ + 2))
                s.fill(c, (lx, ly, 4, lh_))
                for k in range(ly + 1, ly + lh_ - 1, 3):
                    s.fill(_mix(c, (255, 255, 255), 0.6), (lx + 1, k, 2, 1))
                luzes.append((lx + 2, ly + lh_ // 2, c))
            elif rng.random() < 0.5:                                                # letreiro horizontal no topo
                c = rng.choice(neons)
                s.fill(c, (x + 1, chao + 3 - h, w - 2, 3))
                luzes.append((x + w // 2, chao + 4 - h, c))
            if rng.random() < 0.4:                                                  # antena com luz vermelha
                line(s, cor, (x + w // 2, chao + 6 - h), (x + w // 2, chao - h - 6))
                luzes.append((x + w // 2, chao - h - 6, (255, 40, 40)))
            x += w + rng.randint(1, 6)
    elif tipo == "colonia":                    # base de colonos à esquerda, cristais no meio, colmeia à direita
        bx = int(lw * 0.16)
        s.fill(cor, (bx - 22, chao - 22, 44, 28))                                    # centro de comando
        poly(s, cor, [(bx - 26, chao - 22), (bx - 16, chao - 32), (bx + 16, chao - 32), (bx + 26, chao - 22)])
        s.fill(escuro, (bx - 18, chao - 12, 36, 3))
        s.fill(cor, (bx + 8, chao - 50, 6, 20))                                      # torre e antena parabólica
        ell(s, claro, (bx + 2, chao - 58, 16, 8))
        line(s, cor, (bx + 10, chao - 58), (bx + 10, chao - 66))
        luzes.append((bx + 10, chao - 66, (255, 60, 50)))
        for k in range(4):
            luzes.append((bx - 18 + k * 12, chao - 23, (120, 255, 120) if k % 2 else (255, 220, 80)))
        for dx_ in (-44, 30, 44):                                                    # depósitos com listras
            x0 = bx + dx_
            poly(s, cor, [(x0 - 8, chao + 6), (x0 - 6, chao - 10), (x0 + 6, chao - 10), (x0 + 8, chao + 6)])
            for k in range(3):
                s.fill((230, 190, 60), (x0 - 6, chao - 8 + k * 4, 12, 1))
        ell(s, cor, (bx + 52, chao - 8, 22, 18))                                     # casamata
        s.fill(escuro, (bx + 56, chao - 3, 14, 2))
        for k in range(7):                                                           # cristais azuis
            cx_ = int(lw * 0.47) + k * 5 - 15
            h = rng.randint(8, 18)
            poly(s, (80, 170, 255), [(cx_ - 3, chao + 4), (cx_, chao + 4 - h), (cx_ + 3, chao + 4)])
            line(s, (200, 240, 255), (cx_, chao + 4 - h), (cx_ - 1, chao + 2))
            if k % 3 == 0:
                luzes.append((cx_, chao + 4 - h, (120, 200, 255)))
        hx = int(lw * 0.8)                                                           # tapete roxo da colmeia
        ell(s, (110, 40, 120, 255), (hx - 50, chao - 2, 100, 14))
        for k in range(5):
            mx = hx - 30 + k * 15
            h = rng.randint(16, 30)
            ell(s, _mix((120, 50, 110), cor, 0.4), (mx - 8, chao - h // 2, 16, h // 2 + 6))
            luzes.append((mx, chao - h // 4, (220, 80, 255)))
        for k, (ox, h, d) in enumerate(((-18, 54, 1), (2, 70, -1), (20, 46, 1))):    # espinhos curvos
            pts = [(hx + ox + int(d * 10 * (i / 10) ** 2), chao + 2 - int(h * i / 10)) for i in range(11)]
            for i in range(10):
                line(s, _mix((90, 40, 90), cor, 0.3), pts[i], pts[i + 1], max(1, 5 - i // 2))
            luzes.append((pts[6][0], pts[6][1], (230, 90, 255)))
    elif tipo == "fortaleza":                  # muralha ameada, torres com espetos, canos e o arco do portal
        s.fill(cor, (0, chao - 26, lw, 32))
        for x in range(0, lw, 8):                                                    # ameias
            s.fill(cor, (x, chao - 31, 5, 5))
        for y in range(chao - 22, chao + 6, 6):                                      # blocos
            for x in range((y // 6) % 2 * 6, lw, 12):
                s.fill(escuro, (x, y, 1, 5))
            s.fill(escuro, (0, y + 5, lw, 1))
        for tx in (int(lw * 0.1), int(lw * 0.32), int(lw * 0.72), int(lw * 0.92)):  # torres
            s.fill(cor, (tx - 9, chao - 64, 18, 40))
            for k in range(4):
                poly(s, escuro, [(tx - 9 + k * 5, chao - 64), (tx - 7 + k * 5, chao - 72), (tx - 5 + k * 5, chao - 64)])
            s.fill((0, 0, 0, 0), (tx - 2, chao - 54, 4, 8))
            luzes.append((tx, chao - 50, (255, 120, 30)))
        px_, alto = ANCORA["portal"]
        px_ = int(lw * px_)
        s.fill(cor, (px_ - 22, chao - 52, 44, 58))                                   # arco do portal
        poly(s, cor, [(px_ - 22, chao - 52), (px_, chao - 64), (px_ + 22, chao - 52)])
        ell(s, (0, 0, 0, 0), (px_ - 15, chao - alto - 16, 30, 34))
        s.fill((0, 0, 0, 0), (px_ - 15, chao - alto, 30, alto + 6))
        for k in range(7):                                                           # runas em volta do arco
            a = math.pi * (k / 6)
            rx, ry = px_ - int(19 * math.cos(a)), chao - alto - int(17 * math.sin(a)) + 2
            luzes.append((rx, ry, (255, 150, 40)))
        for cx_ in (int(lw * 0.2), int(lw * 0.82)):                                   # canos e correntes
            s.fill(escuro, (cx_, chao - 40, 3, 46))
            s.fill(escuro, (cx_ - 2, chao - 42, 7, 3))
    elif tipo == "castelo_reino":              # morros, castelo de torres azuis com bandeiras, moinho, bosque
        poly(s, _mix(cor, (255, 255, 255), 0.15), [(0, chao + 6), (int(lw * 0.08), chao - 28), (int(lw * 0.3), chao - 34),
                                                    (int(lw * 0.4), chao + 6)])
        mx, mh = ANCORA["moinho"]
        mx = int(lw * mx)
        poly(s, cor, [(mx - 6, chao - 24), (mx - 4, chao - mh), (mx + 4, chao - mh), (mx + 6, chao - 24)])
        poly(s, escuro, [(mx - 6, chao - mh), (mx, chao - mh - 7), (mx + 6, chao - mh)])
        cx = int(lw * 0.62)
        s.fill(cor, (cx - 30, chao - 26, 60, 32))                                    # muralha
        for x in range(cx - 30, cx + 30, 6):
            s.fill(cor, (x, chao - 30, 4, 4))
        s.fill(cor, (cx - 9, chao - 52, 18, 28))                                     # torre de menagem
        for k, (tx, th) in enumerate(((cx - 32, 46), (cx + 30, 46), (cx - 9, 52), (cx + 6, 62))):
            w = 10 if k < 2 else 8
            s.fill(cor, (tx - w // 2, chao - th, w, th))
            poly(s, (70, 90, 170), [(tx - w // 2 - 2, chao - th), (tx, chao - th - 14), (tx + w // 2 + 2, chao - th)])
            line(s, cor, (tx, chao - th - 14), (tx, chao - th - 20))
            poly(s, (220, 50, 50), [(tx, chao - th - 20), (tx + 6, chao - th - 18), (tx, chao - th - 16)])
            luzes.append((tx, chao - th + 6, (255, 210, 120)))
        poly(s, escuro, [(cx - 6, chao + 6), (cx - 6, chao - 8), (cx, chao - 13), (cx + 6, chao - 8), (cx + 6, chao + 6)])
        for k in range(6):                                                           # bosque redondo
            ax = int(lw * 0.82) + k * 9
            circ(s, _mix((60, 110, 60), cor, 0.5), (ax, chao - 6 - (k % 2) * 4), 9)
        for k in range(2):                                                           # casinhas de palha
            hx = int(lw * 0.3) + k * 18
            s.fill(claro, (hx, chao - 6, 12, 12))
            poly(s, (170, 130, 70), [(hx - 2, chao - 6), (hx + 6, chao - 13), (hx + 14, chao - 6)])
            luzes.append((hx + 4, chao - 2, (255, 200, 110)))


# --------------------------------------------------------------------- partículas

_COR = {"chuva": (170, 190, 230), "chuva_forte": (190, 205, 240), "neve": (250, 252, 255), "semente": (255, 255, 236),
        "areia": (236, 200, 140), "cinza": (110, 100, 104), "poeira": (190, 170, 240), "bolha": (190, 240, 255)}
_FOLHAS = [(214, 96, 40), (236, 150, 50), (180, 60, 40), (240, 190, 70)]
_PETALAS = [(255, 182, 206), (255, 214, 226), (246, 150, 186)]
_CONFETE = [(255, 90, 110), (255, 210, 70), (90, 200, 255), (130, 240, 140), (210, 120, 255)]
_BORDO = [(200, 30, 36), (230, 70, 40), (170, 20, 40), (250, 120, 60)]
_NEON = [(255, 70, 190), (60, 230, 255), (200, 110, 255), (255, 230, 90)]
_DERIVA = ("vagalume", "esporo", "poeira", "brilho", "tele", "esporo_roxo", "faisca")


class Particulas:
    def __init__(self, lw, lh, rng):
        self.lw, self.lh, self.rng = lw, lh, rng
        self.p = []                                         # [tipo, x, y, vx, vy, fase, cor]

    def nova(self, tipo, vento, topo=False):
        r, lw, lh = self.rng, self.lw, self.lh
        x, y = r.uniform(-20, lw + 20), (r.uniform(-20, 0) if topo else r.uniform(0, lh))
        cor = _COR.get(tipo)
        vx, vy = vento, 0.0
        if tipo == "chuva":
            vx, vy = vento - 0.6, r.uniform(4.5, 6)
        elif tipo == "chuva_forte":
            vx, vy = vento - 1.2, r.uniform(6, 8)
        elif tipo == "neve":
            vx, vy = vento * 0.4, r.uniform(0.25, 0.7)
        elif tipo in ("folha", "petala"):
            vx, vy = vento + r.uniform(-0.2, 0.4), r.uniform(0.35, 0.8)
            cor = r.choice(_FOLHAS if tipo == "folha" else _PETALAS)
        elif tipo == "confete":
            vx, vy, cor = r.uniform(-0.4, 0.4), r.uniform(0.5, 1.1), r.choice(_CONFETE)
        elif tipo == "semente":
            vx, vy = r.uniform(0.15, 0.45), r.uniform(-0.08, 0.12)
        elif tipo == "areia":
            vx, vy = vento * r.uniform(0.8, 1.6), r.uniform(-0.1, 0.25)
        elif tipo == "bolha":
            vx, vy = 0, -r.uniform(0.3, 0.8)
            if not topo:
                pass
            else:
                y = lh + r.uniform(0, 20)
        elif tipo == "brasa":
            vx, vy, cor = r.uniform(-0.2, 0.3), -r.uniform(0.4, 1.0), r.choice([(255, 200, 80), (255, 130, 40), (255, 90, 30)])
            if topo:
                y = lh + r.uniform(0, 10)
        elif tipo == "cinza":
            vx, vy = vento + r.uniform(0.1, 0.4), r.uniform(0.2, 0.5)
        elif tipo == "vapor":
            vx, vy = r.uniform(-0.1, 0.1), -r.uniform(0.15, 0.3)
            if topo:
                y = lh + r.uniform(0, 10)
        elif tipo in ("vagalume", "esporo", "poeira", "brilho"):
            vx, vy = r.uniform(-0.25, 0.25), r.uniform(-0.2, 0.15)
            if tipo == "vagalume":
                y = r.uniform(lh * 0.35, lh * 0.95)
        elif tipo == "peixe":
            vx, vy, cor = r.choice((-1, 1)) * r.uniform(0.3, 0.7), 0, r.choice([(255, 170, 90), (120, 220, 255), (255, 230, 120)])
            y = r.uniform(lh * 0.15, lh * 0.7)
        elif tipo == "petala_rosa":
            vx, vy = vento + r.uniform(-0.2, 0.3), r.uniform(0.3, 0.7)
            cor = r.choice([(150, 8, 28), (110, 0, 20), (190, 20, 40)])
        elif tipo == "corvo":
            vx, vy, cor = r.choice((-1, 1)) * r.uniform(0.5, 0.9), 0, (6, 4, 10)
            y = r.uniform(lh * 0.08, lh * 0.4)
        elif tipo == "gaivota":
            vx, vy, cor = r.uniform(0.25, 0.5), 0, (60, 40, 50)
            y, x = r.uniform(lh * 0.12, lh * 0.35), (-10 if topo else x)
        elif tipo == "folha_bordo":
            vx, vy, cor = vento + r.uniform(-0.2, 0.4), r.uniform(0.3, 0.7), r.choice(_BORDO)
        elif tipo == "chuva_neon":
            vx, vy = vento - 0.4, r.uniform(4.5, 6.5)
            cor = r.choice(_NEON) if r.random() < 0.3 else (120, 120, 170)
        elif tipo == "carro":                       # carro voador: faixa de altura do céu, farol e lanterna
            d = r.choice((-1, 1))
            vx, vy, cor = d * r.uniform(1.0, 2.2), 0, r.choice(_NEON)
            y, x = r.uniform(lh * 0.1, lh * 0.42), ((-10 if d > 0 else lw + 10) if topo else x)
        elif tipo in ("tele", "esporo_roxo", "faisca"):
            vx, vy = r.uniform(-0.15, 0.15), -r.uniform(0.05, 0.3)
            if tipo == "tele":
                y = r.uniform(lh * 0.4, lh * 0.95)
        self.p.append([tipo, x, y, vx, vy, r.uniform(0, 6.28), cor])

    def manter(self, alvo, vento, dx):
        """alvo = {tipo: quantidade}; dx = quanto a câmera andou (as partículas ficam presas ao mundo)."""
        lw, lh = self.lw, self.lh
        vivos = []
        cont = {}
        for q in self.p:
            tipo = q[0]
            par = 0.25 if tipo in ("gaivota", "semente", "corvo", "carro") else 0.8
            q[1] += q[3] - dx * par
            q[2] += q[4]
            q[5] += 0.05
            if tipo in ("neve", "folha", "petala", "petala_rosa", "confete", "bolha", "cinza", "folha_bordo"):
                q[1] += math.sin(q[5] * (1.5 if tipo != "neve" else 0.8)) * (0.35 if tipo != "bolha" else 0.25)
            elif tipo in _DERIVA:
                q[3] += self.rng.uniform(-0.03, 0.03)
                q[4] += self.rng.uniform(-0.03, 0.03)
                q[3], q[4] = max(-0.4, min(0.4, q[3])), max(-0.3, min(0.3, q[4]))
            if q[1] < -30:
                q[1] += lw + 50
            elif q[1] > lw + 30:
                q[1] -= lw + 50
            fora = q[2] > lh + 12 or q[2] < -40
            if tipo in _DERIVA:
                if q[2] < 0:
                    q[4] = abs(q[4])
                elif q[2] > lh:
                    q[4] = -abs(q[4])
                fora = False
            if fora or cont.get(tipo, 0) >= alvo.get(tipo, 0):
                continue
            cont[tipo] = cont.get(tipo, 0) + 1
            vivos.append(q)
        self.p = vivos
        for tipo, n in alvo.items():
            falta = n - cont.get(tipo, 0)
            for _ in range(min(falta, 6)):                  # entram aos poucos (sem "chuva de uma vez")
                self.nova(tipo, vento, topo=bool(self.p) or tipo in ("gaivota", "corvo", "carro"))

    def draw(self, s, t):
        fill, setp = s.fill, s.set_at
        for tipo, x, y, vx, vy, fase, cor in self.p:
            x, y = int(x), int(y)
            if tipo == "chuva":
                pygame.draw.line(s, cor, (x, y), (int(x + vx * 1.2), y + 4))
            elif tipo == "chuva_forte":
                pygame.draw.line(s, cor, (x, y), (int(x + vx * 1.2), y + 6))
            elif tipo == "neve":
                fill(cor, (x, y, 2 if fase % 1.7 > 0.85 else 1, 1 if fase % 1.7 > 0.85 else 2))
            elif tipo in ("folha", "petala"):
                f = int(fase * 2) % 4
                fill(cor, (x, y, (3, 2, 1, 2)[f], (1, 2, 3, 2)[f]) if tipo == "folha" else (x, y, 2 - f % 2, 1 + f % 2))
            elif tipo == "confete":
                f = int(fase * 3) % 3
                fill(cor, (x, y, (3, 2, 1)[f], 2))
            elif tipo == "semente":
                setp((x, y), cor)
                setp((x - 1, y - 1), (230, 230, 210))
                setp((x + 1, y - 1), (230, 230, 210))
            elif tipo == "areia":
                fill(cor, (x, y, 2, 1))
            elif tipo == "bolha":
                r = 1 + int(fase * 7) % 2
                pygame.draw.circle(s, cor, (x, y), r + 1, 1)
                setp((x - 1, y - 1), (255, 255, 255))
            elif tipo == "brasa":
                s.blit(halo(3, (90, 40, 10)), (x - 3, y - 3), special_flags=ADD)
                fill(cor if math.sin(fase * 9) > -0.6 else (200, 80, 30), (x, y, 1, 1 + (fase % 2 > 1)))
            elif tipo == "cinza":
                setp((x, y), cor)
            elif tipo == "vapor":
                s.blit(halo(6, (26, 22, 24)), (x - 6, y - 6), special_flags=ADD)
            elif tipo == "vagalume":
                b = 0.5 + 0.5 * math.sin(fase * 3)
                if b > 0.25:
                    s.blit(halo(7, (int(150 * b), int(170 * b), int(40 * b))), (x - 7, y - 7), special_flags=ADD)
                    fill((255, 255, 170), (x, y, 2, 2) if b > 0.7 else (x, y, 1, 1))
            elif tipo == "esporo":
                s.blit(halo(3, (50, 60, 26)), (x - 3, y - 3), special_flags=ADD)
                setp((x, y), (240, 255, 200))
            elif tipo == "poeira":
                if math.sin(fase * 2) > -0.3:
                    setp((x, y), cor)
            elif tipo == "brilho":
                b = math.sin(fase * 2.4)
                if b > 0.3:
                    c = (230, 210, 255)
                    r = 2 if b > 0.8 else 1
                    fill(c, (x - r, y, 2 * r + 1, 1))
                    fill(c, (x, y - r, 1, 2 * r + 1))
                    s.blit(halo(4, (60, 40, 90)), (x - 4, y - 4), special_flags=ADD)
            elif tipo == "peixe":
                d = 1 if vx > 0 else -1
                fill(cor, (x - 2, y, 4, 2))
                setp((x - 3 * d, y - 1), cor)
                setp((x - 3 * d, y + 2), cor)
                setp((x + d, y), (30, 30, 50))
            elif tipo == "petala_rosa":
                f = int(fase * 2) % 3
                fill(cor, (x, y, 2 if f else 1, 1 if f == 2 else 2))
                setp((x + 1, y), (60, 0, 10))
            elif tipo == "corvo":                                    # corvo batendo as asas
                a = int(fase * 3) % 3
                fill(cor, (x - 2, y, 5, 2))
                setp((x + 3 * (1 if vx > 0 else -1), y), cor)
                for k in (1, 2, 3):
                    dy = (-k, 0, k)[a] // 2
                    setp((x - 2 - k, y + dy), cor)
                    setp((x + 2 + k, y + dy), cor)
            elif tipo == "folha_bordo":                              # folha de bordo vermelha girando
                f = int(fase * 2) % 4
                fill(cor, (x, y, (3, 2, 1, 2)[f], (1, 2, 3, 2)[f]))
                setp((x + 1, y + 1), _mix(cor, (60, 0, 0), 0.5))
            elif tipo == "chuva_neon":
                pygame.draw.line(s, cor, (x, y), (int(x + vx * 1.2), y + 5))
            elif tipo == "carro":
                d = 1 if vx > 0 else -1
                fill((30, 24, 44), (x - 3, y, 7, 2))
                fill((50, 44, 70), (x - 1, y - 1, 3, 1))
                setp((x + 3 * d, y), (255, 255, 220))
                setp((x - 3 * d, y + 1), cor)
                s.blit(halo(4, _q(tuple(v * 0.4 for v in cor))), (x - 3 * d - 4, y - 3), special_flags=ADD)
                for k in range(1, 6):                                # rastro de luz do motor
                    b = 1 - k / 6
                    setp((x - (3 + k) * d, y + 1), tuple(int(v * b * 0.8) for v in cor))
            elif tipo == "tele":                                     # cintilação dourada do teletransporte
                b = math.sin(fase * 3.1)
                if b > 0.2:
                    c = (255, 230, 150)
                    fill(c, (x, y - 1, 1, 3))
                    if b > 0.8:
                        fill(c, (x - 1, y, 3, 1))
                    s.blit(halo(3, (70, 60, 30)), (x - 3, y - 3), special_flags=ADD)
            elif tipo == "esporo_roxo":
                s.blit(halo(3, (50, 16, 60)), (x - 3, y - 3), special_flags=ADD)
                setp((x, y), (230, 150, 255))
            elif tipo == "faisca":                                   # faíscas de magia dourada subindo
                b = math.sin(fase * 2.2)
                if b > -0.2:
                    s.blit(halo(4, (70, 56, 20)), (x - 4, y - 4), special_flags=ADD)
                    setp((x, y), (255, 240, 180))
            elif tipo == "gaivota":
                a = int(fase * 4) % 2
                setp((x, y), cor)
                setp((x - 1, y - a), cor)
                setp((x - 2, y - 1 + a), cor)
                setp((x + 1, y - a), cor)
                setp((x + 2, y - 1 + a), cor)


# --------------------------------------------------------------------- o controle da fase

class Clima:
    """Um clima pronto para desenhar: céu, cenário tingido e as peças do fundo."""

    def __init__(self, cid, lw, lh, camadas, mapa, seed):
        self.id, self.cfg = cid, CLIMAS[cid]
        cfg = self.cfg
        self.lw, self.lh = lw, lh
        self.ceu = _ceu(*cfg["ceu"], lw, lh) if cfg["ceu"] else None
        tom = cfg.get("tom")
        if tom:
            self.camadas = []
            for c in camadas:
                c = c.copy()
                c.fill(tom, special_flags=MULT)
                self.camadas.append(c)
            self.mapa = mapa.copy()
            claro = 0.12 if cfg.get("pb") else 0.45                                # no gótico o chão também escurece
            self.mapa.fill(_mix(tom, (255, 255, 255), claro), special_flags=MULT)   # mapa mais claro que o fundo
        else:
            self.camadas, self.mapa = camadas, mapa
        self.estrelas = _estrelas(cfg["estrelas"], lw, lh, seed) if cfg.get("estrelas") else None
        self.nebulosa = _nebulosa(lw, lh, seed) if cfg.get("nebulosa") else None
        self.auroras = [_aurora(lw, lh, seed, (30, 150, 90), (60, 30, 110)),
                        _aurora(lw, lh, seed + 1, (20, 110, 120), (80, 30, 90))] if cfg.get("aurora") else []
        self.astro = _sprite_astro(cfg["astro"]) if cfg.get("astro") else None
        self.cristais = _cristais(lw, lh, seed) if cfg.get("cristais") else None
        self.neblina = None
        if cfg.get("neblina"):
            n = pygame.Surface((lw, lh))
            for y in range(lh):
                k = max(0.0, 1 - abs(y - lh * 0.62) / (lh * 0.3))
                n.fill(tuple(int(v * k) for v in cfg["neblina"]), (0, y, lw, 1))
            self.neblina = n
        self.brilho_chao = None
        if cfg.get("brilho_chao"):
            b = pygame.Surface((lw, lh // 2))
            for y in range(lh // 2):
                k = (y / (lh // 2)) ** 2
                b.fill(tuple(int(v * k) for v in cfg["brilho_chao"]), (0, y, lw, 1))
            self.brilho_chao = b
        self.silhueta = None
        if cfg.get("silhueta"):
            base = cfg["ceu"][1] if cfg["ceu"] else (200, 200, 230)
            self.silhueta = _silhueta(cfg["silhueta"], lw, lh, _mix(base, (20, 10, 40), 0.45), seed)
        self.part = dict(cfg.get("part", []))
        self.vento = cfg.get("vento", 0.0)


class Controle:
    """Dono do clima de uma fase (um por Jogo)."""

    VEU = 24                                               # quadros do véu de cada lado da troca

    def __init__(self, jogo, seed):
        self.j = jogo
        from .game import LW, LH
        self.lw, self.lh = LW, LH
        self.seed = seed
        self.rng = random.Random(seed)
        self.sorteado = self.rng.choice(sorted(CLIMAS))
        self.atual = None
        self.alvo = None
        self.veu = 0                                       # >0: escurecendo para trocar; <0: clareando
        self.t = 0
        self.part = Particulas(LW, LH, self.rng)
        self.ult_cx = None
        self.flash = 0
        self.raio = None
        self.prox_raio = 120
        self.fogos = []
        self.prox_fogo = 60
        self.cadente = None
        self._decidir(imediato=True)

    # -- qual clima
    def _desejado(self):
        au = self.j.app.audio
        cid = de_faixa(au.nome(au.atual)) if getattr(au, "atual", None) and au.tocando else None
        return cid or (self.atual.id if self.atual else self.sorteado)

    def _decidir(self, imediato=False):
        cid = self._desejado()
        if self.atual is None or imediato:
            self._ativar(cid)
        elif cid != self.atual.id and cid != self.alvo:
            self.alvo = cid
            self.veu = max(self.veu, 1)

    def _ativar(self, cid):
        j = self.j
        self.atual = Clima(cid, self.lw, self.lh, j.camadas, j.mapa_base, self.seed)
        j.mapa = self.atual.mapa
        self.alvo = None

    @property
    def nome(self):
        return self.atual.cfg["nome"]

    # -- por quadro
    def passo(self, cx):
        self.t += 1
        if self.t == 2:                                    # a música começa logo depois de a fase ser criada
            self._decidir(imediato=True)
        elif self.t % 30 == 0:
            self._decidir()
        if self.veu > 0:
            self.veu += 1
            if self.veu >= self.VEU:
                self._ativar(self.alvo or self.atual.id)
                self.part.p = []
                self.veu = -self.VEU
        elif self.veu < 0:
            self.veu += 1
        dx = 0 if self.ult_cx is None else cx - self.ult_cx
        self.ult_cx = cx
        if abs(dx) > 40:                                   # câmera pulou (checkpoint): não arrasta as partículas
            dx = 0
        c = self.atual.cfg
        self.part.manter(self.atual.part, self.atual.vento, dx)
        if c.get("raios"):
            self.prox_raio -= 1
            if self.prox_raio <= 0:
                self._novo_raio()
                self.prox_raio = self.rng.randint(150, 420)
        if self.flash:
            self.flash -= 1
        if self.raio:
            self.raio[1] -= 1
            if self.raio[1] <= 0:
                self.raio = None
        if c.get("fogos"):
            self.prox_fogo -= 1
            if self.prox_fogo <= 0:
                self._novo_fogo()
                self.prox_fogo = self.rng.randint(50, 140)
            for f in self.fogos:
                f[0] += f[2]
                f[1] += f[3]
                f[3] += 0.02
                f[4] -= 1
            self.fogos = [f for f in self.fogos if f[4] > 0]
        if c.get("cadentes"):
            if self.cadente:
                self.cadente[0] += 3.2
                self.cadente[1] += 1.4
                self.cadente[2] -= 1
                if self.cadente[2] <= 0:
                    self.cadente = None
            elif self.rng.random() < 0.006:
                self.cadente = [self.rng.uniform(0, self.lw * 0.6), self.rng.uniform(4, self.lh * 0.3), 28]

    def _novo_raio(self):
        r = self.rng
        x = r.uniform(self.lw * 0.1, self.lw * 0.9)
        pts, y = [(x, 0)], 0
        fim = r.uniform(self.lh * 0.45, self.lh * 0.8)
        while y < fim:
            y += r.uniform(6, 14)
            x += r.uniform(-9, 9)
            pts.append((x, y))
        self.raio = [pts, 8]
        self.flash = 10

    def _novo_fogo(self):
        r = self.rng
        x, y = r.uniform(self.lw * 0.1, self.lw * 0.9), r.uniform(self.lh * 0.12, self.lh * 0.4)
        cor = r.choice(_CONFETE)
        n = r.randint(14, 22)
        for i in range(n):
            a = 2 * math.pi * i / n
            v = r.uniform(0.7, 1.1)
            self.fogos.append([x, y, math.cos(a) * v, math.sin(a) * v, r.randint(34, 50), cor])

    # -- desenho
    def draw_ceu(self, s, cx):
        a, c, lw, lh, t = self.atual, self.atual.cfg, self.lw, self.lh, self.t
        s.blit(a.ceu or self.j.ceu, (0, 0))
        if a.nebulosa:
            s.blit(a.nebulosa, (-(cx // 40) % lw - lw, 0), special_flags=ADD)
            s.blit(a.nebulosa, (-(cx // 40) % lw, 0), special_flags=ADD)
        if a.estrelas:
            fundo, piscam = a.estrelas
            s.blit(fundo, (0, 0), special_flags=ADD)
            for i, (x, y) in enumerate(piscam):
                if math.sin(t * 0.05 + i * 1.7) > 0.4:
                    s.fill((255, 255, 255), (x - 1, y, 3, 1))
                    s.fill((255, 255, 255), (x, y - 1, 1, 3))
        for i, au in enumerate(a.auroras):
            ox = -int(t * (0.12 + 0.08 * i) + cx * 0.03) % au.get_width()
            y = int(lh * (0.02 + 0.06 * i))
            s.blit(au, (ox, y), special_flags=ADD)
            s.blit(au, (ox - au.get_width(), y), special_flags=ADD)
        if self.cadente:
            x, y, v = self.cadente
            for k in range(10):
                b = int(255 * (1 - k / 10) * v / 28)
                s.set_at((int(x - k * 1.6), int(y - k * 0.7)), (b, b, b))
        if a.astro:
            tipo = c["astro"]
            pos = {"planeta_verde": (0.7, 0.1), "sol_vermelho": (0.36, 0.2), "sois_duplos": (0.62, 0.12),
                   "sol": (0.78, 0.14), "sol_baixo": (0.72, 0.34), "sol_grande": (0.7, 0.18), "lua": (0.8, 0.12),
                   "lua_grande": (0.24, 0.1),
                   "planeta": (0.74, 0.16), "sol_poente": (0.5, 0.2)}[tipo]
            x = int(lw * pos[0] - cx * 0.02) % (lw + 60) - 30
            y = int(lh * pos[1])
            w, h = a.astro.get_size()
            cor_halo = {"lua": (40, 40, 50), "planeta": (40, 26, 50), "lua_grande": (70, 66, 80), "planeta_verde": (20, 50, 40),
                        "sol_vermelho": (90, 20, 10), "sois_duplos": (110, 70, 30)}.get(tipo, (90, 70, 30))
            if tipo == "lua_grande":                         # raios de luar descendo, girando devagar (cones do farol)
                for i in range(3):
                    ang = 180 + 26 * math.sin(t * 0.004 + i * 2.1) + (i - 1) * 24
                    g, bx, by = _cone_girado(int(lh * 0.95), 0.07, (56, 54, 64), ang)
                    s.blit(g, (int(x + w / 2 - bx), int(y + h / 2 - by)), special_flags=ADD)
            r = max(w, h)
            s.blit(halo(r, cor_halo), (x + w // 2 - r, y + h // 2 - r), special_flags=ADD)
            s.blit(a.astro, (x, y))
        if c.get("fachos") == "raios":
            cor = c["cor_facho"]
            for i in range(4):
                b = 0.55 + 0.45 * math.sin(t * 0.013 + i * 1.9)
                cor_i = tuple(int(v * (0.5 + 0.5 * b)) for v in cor)
                faixa = _faixa_luz(10 + 4 * (i % 2), int(lh * 0.85), _q(cor_i), 0.35)
                x = int(lw * (0.1 + 0.25 * i) - cx * 0.12) % (lw + 80) - 60
                s.blit(faixa, (x, 0), special_flags=ADD)
        self._rosas = []
        if a.silhueta:
            sil, luzes = a.silhueta
            ox = -int(cx * 0.06) % lw
            if c["silhueta"] == "catedral":
                self._rosas = [(luzes[1][0] + dx, luzes[1][1]) for dx in (ox - lw, ox)]
            for dx in (ox - lw, ox):
                s.blit(sil, (dx, 0))
                if c.get("extra") in ("portal", "moinho"):
                    self._peca_animada(s, c["extra"], dx)
                for i, (x, y, cor) in enumerate(luzes):
                    b = 0.55 + 0.45 * math.sin(t * (0.04 if c["silhueta"] != "roda" else 0.12) + i * 2.3)
                    r = 9 if c["silhueta"] in ("vulcao", "farol", "catedral") else 4
                    s.blit(halo(r, _q(tuple(v * 0.5 * b for v in cor))), (x + dx - r, y - r), special_flags=ADD)
                    s.set_at((x + dx, y), cor)
                    if c["silhueta"] == "farol" or (c["silhueta"] == "catedral" and i == 0):
                        self._facho_farol(s, x + dx, y)
        if c.get("extra") in ("nave", "nave_drop", "holograma"):
            self._ceu_animado(s, c["extra"], cx)
        return c.get("nuvens", True)

    # -- peças animadas dos climas temáticos
    def _peca_animada(self, s, tipo, dx):
        t, lw, chao = self.t, self.lw, int(self.lh * 0.5) - SOBE_TEMA
        fx, alto = ANCORA[tipo]
        x = int(lw * fx) + dx
        if x < -40 or x > lw + 40:
            return
        if tipo == "portal":                       # portal rúnico: espiral girando dentro do arco
            y = chao - alto + 4
            s.blit(halo(16, (40, 20, 8)), (x - 16, y - 16), special_flags=ADD)
            for k in range(36):
                a = k * 0.55 + t * 0.06
                rr = 1 + k * 0.38
                px, py = x + int(rr * math.cos(a)), y + int(rr * math.sin(a) * 1.15)
                b = 1 - k / 40
                s.set_at((px, py), (int(200 * b) + 40, int(110 * b) + 20, int(40 * b)))
                a2 = a + math.pi
                s.set_at((x + int(rr * math.cos(a2)), y + int(rr * math.sin(a2) * 1.15)), (int(120 * b), int(60 * b), int(150 * b)))
        else:                                      # moinho: quatro pás girando
            y = chao - alto - 2
            a0 = t * 0.03
            for k in range(4):
                a = a0 + k * math.pi / 2
                ex, ey = x + int(18 * math.cos(a)), y + int(18 * math.sin(a))
                pygame.draw.line(s, (90, 64, 40), (x, y), (ex, ey), 1)
                nx, ny = -math.sin(a), math.cos(a)
                pts = [(x + int(6 * math.cos(a)), y + int(6 * math.sin(a))), (ex, ey),
                       (ex + int(4 * nx), ey + int(4 * ny)), (x + int(6 * math.cos(a) + 4 * nx), y + int(6 * math.sin(a) + 4 * ny))]
                pygame.draw.polygon(s, (236, 220, 190), pts)
                pygame.draw.polygon(s, (120, 90, 60), pts, 1)
            s.fill((60, 40, 30), (x - 1, y - 1, 3, 3))

    def _ceu_animado(self, s, tipo, cx):
        t, lw, lh = self.t, self.lw, self.lh
        if tipo == "holograma":                    # peixe holográfico enorme nadando sobre a cidade
            per = 900
            u = (t % per) / per
            x = int(-60 + (lw + 120) * u)
            y = int(lh * 0.2 + 8 * math.sin(t * 0.02))
            if math.sin(t * 0.7) > -0.85:          # falha de sinal de vez em quando
                s.blit(_holo_peixe(int(t * 0.15) % 2), (x - 30, y - 12), special_flags=ADD)
            return
        ev = getattr(self, "_ev", None)
        if ev is None or ev[0] != tipo:
            self._ev = ev = [tipo, None, self.rng.randint(120, 300)]
        if ev[1] is None:
            ev[2] -= 1
            if ev[2] <= 0:
                d = self.rng.choice((-1, 1))
                ev[1] = [(-50 if d > 0 else lw + 50), self.rng.uniform(lh * 0.1, lh * 0.3), d, 0]
            return
        x, y, d, k = ev[1]
        vel = 0.45 if tipo == "nave" else 0.9
        ev[1][0] += vel * d
        ev[1][3] += 1
        sd = 1 if d > 0 else -1
        spr = _nave(tipo, sd)
        w, h = spr.get_size()
        if tipo == "nave" and k > 60 and lw * 0.45 < x < lw * 0.55 and self.rng.random() < 0.02:
            ev[1][2] = sd * 12                     # dobra espacial: estica e some
        if abs(ev[1][2]) > 1:
            for i in range(1, 9):
                s.blit(spr, (int(x - sd * i * 7 - w / 2), int(y - h / 2)), special_flags=ADD)
        s.blit(spr, (int(x - w / 2), int(y - h / 2)))
        luz = (255, 90, 60) if t % 40 < 20 else (90, 160, 255)
        s.blit(halo(4, _q(tuple(v * 0.5 for v in luz))), (int(x - sd * w / 2) - 4, int(y) - 4), special_flags=ADD)
        if x < -80 or x > lw + 80:
            ev[1], ev[2] = None, self.rng.randint(500, 1100)

    def _facho_farol(self, s, x, y):
        """O facho do farol varre o céu da tempestade (o mesmo cone do farol do Mirante, girando)."""
        ang = 80 * math.sin(self.t * 0.018)
        g, bx, by = _cone_girado(int(self.lw * 0.55), 0.09, (120, 108, 66), ang)
        s.blit(g, (int(x - bx), int(y - by)), special_flags=ADD)

    def draw_meio(self, s, cx):
        """Depois dos morros e antes do mapa: holofotes do parque nascendo de trás do terreno; lampiões góticos."""
        c, t, lw, lh = self.atual.cfg, self.t, self.lw, self.lh
        if c.get("pb"):
            passo = 150
            base = int(lh * 0.8)
            for k in range(-1, lw // passo + 2):
                wx = k * passo - (int(cx * 0.5) % passo) + 60
                chama = 0.75 + 0.25 * math.sin(t * 0.31 + k * 1.7) * math.sin(t * 0.13 + k)   # gás tremendo
                s.fill((8, 6, 12), (wx, base - 46, 2, 46))
                s.fill((8, 6, 12), (wx - 4, base - 50, 10, 5))
                s.fill((8, 6, 12), (wx + 2, base - 46, 6, 1))
                cor = _q(tuple(v * chama for v in (60, 56, 48)))
                g, bx, by = _cone_girado(48, 0.32, cor, 180)
                s.blit(g, (int(wx + 1 - bx), int(base - 46 - by)), special_flags=ADD)
                s.blit(halo(10, _q(tuple(v * chama for v in (120, 110, 90)))), (wx - 9, base - 57), special_flags=ADD)
                s.fill((250, 240, 220), (wx - 1, base - 48, 4, 3))
        if c.get("fachos") == "holofotes":
            for i, cor in enumerate(c.get("cor_holofotes") or [(70, 40, 90), (40, 70, 90), (90, 70, 30)]):
                ang = 32 * math.sin(t * 0.012 + i * 2.1)
                g, bx, by = _cone_girado(int(lh * 0.9), 0.16, cor, ang)
                x0 = int(lw * (0.2 + 0.3 * i) - cx * 0.1) % (lw + 60) - 30
                s.blit(g, (int(x0 - bx), int(lh - by)), special_flags=ADD)
        a = self.atual
        if a.cristais:
            s.blit(a.cristais, (-(cx // 6) % lw - lw, 0))
            s.blit(a.cristais, (-(cx // 6) % lw, 0))

    def pos_mundo(self, s):
        """Clima gótico: o mundo vira preto e branco de alto contraste; só o vermelho volta (rosácea, rosas, batom)."""
        if not self.atual.cfg.get("pb"):
            return
        s.blit(pygame.transform.grayscale(s), (0, 0))
        s.fill((206, 196, 214), special_flags=MULT)
        p, j = self.j.p, self.j                            # canhão de luz de palco caindo sobre o herói
        hx, hy = int(p.cx - j.cam[0]), int(p.y + p.h - j.cam[1])
        b = 0.85 + 0.15 * math.sin(self.t * 0.07)
        comp = max(24, (hy + 8) // 8 * 8)                  # comprimento em passos de 8: poucos cones no cache
        g, bx, by = _cone_girado(comp, 0.2, _q((int(118 * b), int(112 * b), int(126 * b))), 180)
        s.blit(g, (int(hx - bx), int(hy + 4 - comp - by)), special_flags=ADD)
        ch = ("poca", self.lh)
        if ch not in _cache:
            _cache[ch] = pygame.transform.smoothscale(halo(14, (90, 86, 96)), (44, 8))
        s.blit(_cache[ch], (hx - 22, hy - 4), special_flags=ADD)
        for x, y in getattr(self, "_rosas", ()):
            b = 0.7 + 0.3 * math.sin(self.t * 0.05)
            s.blit(halo(11, _q((int(150 * b), 8, 24))), (x - 11, y - 11), special_flags=ADD)
            pygame.draw.circle(s, (200, 20, 44), (x, y), 5)
            pygame.draw.circle(s, (250, 120, 120), (x, y), 2)
            for k in range(4):
                a = k * math.pi / 4
                pygame.draw.line(s, (70, 0, 12), (x - int(math.cos(a) * 5), y - int(math.sin(a) * 5)),
                                 (x + int(math.cos(a) * 5), y + int(math.sin(a) * 5)))

    def _vinheta(self):
        ch = ("vinheta", self.lw, self.lh)
        if ch not in _cache:
            v = pygame.Surface((self.lw, self.lh))
            v.fill((255, 255, 255))
            for i in range(26):
                k = 255 - int(150 * (1 - i / 26) ** 2)
                pygame.draw.rect(v, (k, k, k), (i * 2, int(i * 1.4), self.lw - i * 4, self.lh - int(i * 2.8)), 2)
            _cache[ch] = pygame.transform.smoothscale(pygame.transform.smoothscale(v, (self.lw // 4, self.lh // 4)),
                                                      (self.lw, self.lh))
        return _cache[ch]

    def draw_frente(self, s, cx, cy):
        a, c, t = self.atual, self.atual.cfg, self.t
        if a.brilho_chao:
            s.blit(a.brilho_chao, (0, self.lh - a.brilho_chao.get_height()), special_flags=ADD)
        if a.neblina:
            s.blit(a.neblina, (0, 0), special_flags=ADD)
        if c.get("luz"):                                   # o herói carrega um pouco de luz nos climas escuros
            p = self.j.p
            r = 22
            s.blit(halo(r, c["luz"]), (int(p.x + p.w / 2 - cx - r), int(p.y + p.h / 2 - cy - r)), special_flags=ADD)
        self.part.draw(s, t)
        for x, y, vx, vy, vida, cor in self.fogos:
            k = vida / 50
            s.blit(halo(3, tuple(int(v * 0.35 * k) for v in cor)), (int(x) - 3, int(y) - 3), special_flags=ADD)
            s.set_at((int(x), int(y)), cor if vida > 12 else (255, 255, 255))
        if self.raio:
            pts, v = self.raio
            pygame.draw.lines(s, (200, 200, 255), False, pts, 2)
            pygame.draw.lines(s, (255, 255, 255), False, pts, 1)
        if self.flash:
            k = int(9 * self.flash)
            s.fill((k, k, k + 6), special_flags=ADD)
        if c.get("pb"):
            s.blit(self._vinheta(), (0, 0), special_flags=MULT)
        if self.veu:                                       # véu da troca de clima
            k = abs(self.veu) / self.VEU
            v = int(255 * (1 - 0.85 * k))
            s.fill((v, v, v), special_flags=MULT)


def _nave(tipo, d):
    """Nave da frota (disco, pescoço, casco e duas naceles) ou nave de desembarque da colônia, virada para d."""
    ch = ("nave", tipo, d)
    if ch not in _cache:
        if tipo == "nave":
            s = pygame.Surface((34, 14), pygame.SRCALPHA)
            casco, sombra, luz = (214, 216, 226), (150, 154, 170), (255, 255, 255)
            pygame.draw.ellipse(s, casco, (16, 0, 18, 6))                  # disco
            pygame.draw.line(s, luz, (19, 1), (31, 1))
            pygame.draw.line(s, sombra, (20, 6), (16, 8), 2)               # pescoço
            pygame.draw.ellipse(s, casco, (8, 7, 12, 4))                   # casco secundário
            for ny in (3, 12):                                             # naceles com a frente vermelha
                pygame.draw.line(s, sombra, (8, 9), (6, ny), 1)
                s.fill(casco, (0, ny - 1, 13, 2))
                s.fill((255, 80, 60), (12, ny - 1, 2, 2))
                s.fill((110, 170, 255), (0, ny - 1, 2, 2))
            s.set_at((25, 3), (90, 200, 255))
        else:
            s = pygame.Surface((26, 12), pygame.SRCALPHA)
            casco, sombra = (150, 140, 128), (96, 88, 82)
            pygame.draw.polygon(s, casco, [(4, 4), (22, 3), (26, 6), (22, 8), (4, 8)])
            s.fill(sombra, (6, 8, 14, 2))
            s.fill(sombra, (2, 2, 6, 3))
            s.fill(sombra, (2, 8, 6, 3))
            s.fill((255, 160, 60), (0, 3, 2, 2))
            s.fill((255, 160, 60), (0, 9, 2, 2))
            s.fill((120, 200, 255), (20, 4, 3, 2))
        if d < 0:
            s = pygame.transform.flip(s, True, False)
        _cache[ch] = s
    return _cache[ch]


def _holo_peixe(q):
    """Carpa holográfica (para somar): ciano e magenta com linhas de varredura."""
    ch = ("holo", q)
    if ch not in _cache:
        s = pygame.Surface((60, 24))
        cor, borda = (20, 90, 110), (90, 30, 100)
        pygame.draw.ellipse(s, cor, (16, 6, 30, 12))
        pygame.draw.ellipse(s, borda, (16, 6, 30, 12), 1)
        cauda = [(18, 12), (4, 3 + q * 2), (8, 12), (4, 21 - q * 2)]
        pygame.draw.polygon(s, cor, cauda)
        pygame.draw.polygon(s, borda, cauda, 1)
        pygame.draw.polygon(s, borda, [(28, 7), (34, 1), (38, 7)])
        pygame.draw.polygon(s, borda, [(30, 17), (34, 22), (37, 17)])
        s.fill((140, 220, 240), (40, 10, 2, 2))
        for y in range(0, 24, 2):                                          # linhas de varredura
            s.fill((0, 0, 0), (0, y, 60, 1))
        _cache[ch] = s
    return _cache[ch]


def _q(cor):
    """Arredonda a cor em passos de 8: o brilho pulsando reaproveita superfícies do cache."""
    return tuple(int(v) // 8 * 8 for v in cor)
