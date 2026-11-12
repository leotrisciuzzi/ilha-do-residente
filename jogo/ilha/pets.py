"""Pets: um bichinho que acompanha o personagem nas fases (onde antes iam os ovos) e ataca no lugar da língua.

Só um pet por vez. Pets, coleiras e chapéus se compram com moedas na Loja (personagens.Loja, abas Pets, Coleiras e
Chapéus); cada pet guarda a própria coleira e o próprio chapéu.

No save:
  pet   = {"ativo": "gato_branco", "equip": {"gato_branco": {"coleira": "vermelha", "chapeu": "laco"}}}
  itens = [..., "pet:gato_branco", "coleira:vermelha", "chapeu:laco"]      (a mesma lista dos itens do personagem)

Na fase (game.Jogo): o pet segue o rastro do herói com atraso (pula quando ele pulou) e, no botão que era a língua
(e no do ovo), dá um bote para a frente: acerta o bicho-questão (abre a questão), derruba germes e bate no gigante.
Sem pet não há esse ataque; os personagens de pé continuam com o golpe de bastão e todos com o pisão."""
import math

import pygame

from . import art

# --------------------------------------------------------------------- catálogo

PETS = {
    "nenhum": dict(nome="Sem pet", preco=0, desc="Sozinho na ilha (sem o ataque do pet)"),
    "gato_branco": dict(nome="Gato branco", preco=150, desc="Olhos azuis, bigode comprido e pulo silencioso",
                        pal={"C": (238, 238, 246), "c": (196, 200, 220), "B": (255, 255, 255), "E": (90, 160, 255),
                             "K": (70, 64, 92), "P": (250, 160, 186)}),
    "gato_amarelo": dict(nome="Gato amarelo", preco=200, desc="Listrado, guloso e sempre de bom humor",
                         pal={"C": (250, 196, 78), "c": (218, 138, 40), "B": (255, 236, 184), "E": (90, 200, 90),
                              "K": (110, 60, 30), "P": (240, 130, 130)}),
    "gato_preto": dict(nome="Gato preto", preco=250, desc="Olhos de farol: traz sorte para quem estuda",
                       pal={"C": (52, 50, 68), "c": (34, 32, 46), "B": (78, 74, 96), "E": (255, 216, 70),
                            "K": (14, 12, 22), "P": (210, 120, 160)}),
}
COLEIRAS = {
    "nenhuma": dict(nome="Sem coleira", preco=0, desc="Pescoço livre"),
    "vermelha": dict(nome="Coleira vermelha", preco=40, desc="Com guizo dourado", cor=(220, 50, 60), guizo=True),
    "azul": dict(nome="Coleira azul", preco=40, desc="Azul-céu, com guizo", cor=(60, 110, 230), guizo=True),
    "rosa": dict(nome="Coleira rosa", preco=40, desc="Rosa-chiclete, com guizo", cor=(250, 120, 180), guizo=True),
    "verde": dict(nome="Coleira verde-água", preco=50, desc="Verde-água com guizo prateado", cor=(60, 190, 170), guizo=True),
    "lenco": dict(nome="Lencinho vermelho", preco=80, desc="Bandana de bolinhas no pescoço", cor=(230, 60, 60),
                  lenco=True),
    "estetoscopio": dict(nome="Mini estetoscópio", preco=120, desc="Para auscultar ronronados",
                         cor=(120, 130, 150), esteto=True),
    "dourada": dict(nome="Coleira de ouro", preco=200, desc="Brilha e tilinta: pet de campeão", cor=(250, 200, 50),
                    guizo=True, brilha=True),
}
CHAPEUS = {
    "nenhum": dict(nome="Sem chapéu", preco=0, desc="Orelhas ao vento"),
    "laco": dict(nome="Laço rosa", preco=50, desc="Na orelha esquerda"),
    "flor": dict(nome="Florzinha", preco=50, desc="Uma flor da ilha atrás da orelha"),
    "touca": dict(nome="Touca cirúrgica", preco=90, desc="Verde, pronta para o centro cirúrgico"),
    "festa": dict(nome="Chapéu de festa", preco=100, desc="Listrado, para comemorar a aprovação"),
    "gorro": dict(nome="Gorro de inverno", preco=120, desc="Vermelho com pompom branco"),
    "bruxa": dict(nome="Chapéu de bruxa", preco=160, desc="Para as provas de outubro"),
    "coroa": dict(nome="Coroa", preco=300, desc="Ouro e rubi: o rei da enfermaria"),
}
CATALOGO = {"pet": PETS, "coleira": COLEIRAS, "chapeu": CHAPEUS}
CATEGORIAS = [("pet", "Pets"), ("coleira", "Coleiras"), ("chapeu", "Chapéus")]

# --------------------------------------------------------------------- estado no save


def _estado(save):
    d = save.d.setdefault("pet", {})
    d.setdefault("ativo", "nenhum")
    d.setdefault("equip", {})
    return d


def possui(save, cat, item):
    dados = CATALOGO[cat].get(item)
    return bool(dados) and (dados["preco"] == 0 or f"{cat}:{item}" in save.d.get("itens", []))


def ativo(save):
    p = _estado(save)["ativo"]
    return p if p in PETS and possui(save, "pet", p) else "nenhum"


def equipado(save, cat):
    if cat == "pet":
        return ativo(save)
    p = ativo(save)
    item = _estado(save)["equip"].get(p, {}).get(cat)
    padrao = "nenhuma" if cat == "coleira" else "nenhum"
    return item if item in CATALOGO[cat] and possui(save, cat, item) else padrao


def equipar(save, cat, item):
    import time
    if not possui(save, cat, item):
        return False
    d = _estado(save)
    if cat == "pet":
        d["ativo"] = item
    else:
        d["equip"].setdefault(ativo(save), {})[cat] = item
    d["t"] = time.time()
    save.salvar()
    return True


def visual(save):
    """(pet, coleira, chapéu) equipados agora."""
    return ativo(save), equipado(save, "coleira"), equipado(save, "chapeu")


# --------------------------------------------------------------------- desenho (pixel art 20×13, virado à direita)
# Traço Ilha para o elenco (estilo E + A): cabeça grande de filhote, focinho mais claro, olho de ponto, poucas partes,
# contorno escuro uniforme e a coleira no pescoço separando a cabeça do corpo (como os colarinhos da Hanna-Barbera).

LARG = 20
TOPO = 8                     # linhas livres acima das orelhas para o chapéu
CABECA_X = 9                 # a cabeça (11 colunas) começa aqui; centro em x = 14
CORPO = [
    "..........K.......K.",
    ".........KPK.....KPK",
    ".KK......KPCKKKKKCPK",
    "KCCK.....KCCCcCcCCCK",
    "KCK......KCCECCCECCK",
    "KCK......KCCECCCECCK",
    "KCKKKKKKKKcBBBPBBBcK",
    "KCCCCcCCCCKBBKBKBBK.",
    ".KCCCCcCCCCKKKKKKK..",
    ".KCCcCCCCcCCCCK.....",
    ".KBBBBBBBBBBBBK.....",
]
RABO2 = {2: "..KK.....", 3: ".KCCK....", 4: "KCK......"}      # rabo abanando (parado): troca o começo das linhas
PERNAS = {
    "a": ["..KC.KC...KC.KC.....", "..KK.KK...KK.KK....."],
    "b": ["...KCKC....KCKC.....", "...KKKK....KKKK....."],
    "c": [".KC...KC.KC...KC....", ".KK...KK.KK...KK...."],
    "pulo": [".KCKC.......KCKC....", "KK.KK.........KKK..."],
}
PERNAS["estica"] = ["..KC.KC......KC.KC..", "..KK.KK......KKKKKK."]     # espreguiçando: patas da frente lá na frente
PERNAS["lambe"] = ["..KC.KC...KC........", "..KK.KK...KK........"]      # uma pata da frente subiu até a boca
OLHO = (4, 5)                # linhas dos olhos (2 px de altura, olho de ponto)
OLHOS_X = (12, 16)           # colunas dos olhos
POSES_ROSTO = ("feliz", "susto", "lambe", "boceja", "espreguica")   # reações e ações à toa (corpo parado)


def _pal(pet):
    return dict(PETS[pet]["pal"], W=(255, 255, 255))


def _contorno(pet):
    return PETS[pet]["pal"]["K"]


def _troca(linha, i, txt):
    return linha[:i] + txt + linha[i + len(txt):]


def _desenhar(pet, coleira, chapeu, pose, quadro):
    corpo = list(CORPO)
    o1, o2 = OLHO
    rabo_alto = (pose == "parado" and (quadro // 20) % 2) or pose in ("feliz", "susto") and (quadro // 4) % 2
    if rabo_alto:
        for i, ini in RABO2.items():
            corpo[i] = ini + corpo[i][len(ini):]
    fecha = pose == "parado" and quadro % 90 in (84, 85, 88, 89)   # piscada dupla (como os gigantes)
    if fecha or pose in ("lambe", "boceja", "espreguica"):         # olho fechado: um risco embaixo
        corpo[o1] = corpo[o1].replace("E", "C")
        corpo[o2] = corpo[o2].replace("E", "K")
    elif pose == "feliz":                                            # olhos de arco (^ ^) na cor do olho
        corpo[o2] = corpo[o2].replace("E", "C")
        for x in OLHOS_X:
            corpo[o2] = _troca(_troca(corpo[o2], x - 1, "E"), x + 1, "E")
    elif pose == "susto":                                            # sobrancelha lá em cima, olho branco, pupila miúda
        for x in OLHOS_X:
            corpo[o1 - 1] = _troca(corpo[o1 - 1], x, "K")
            corpo[o1] = _troca(corpo[o1], x, "W")
            corpo[o2] = _troca(corpo[o2], x, "K")
    if pose == "feliz":                                              # boca aberta de alegria
        corpo[7] = _troca(corpo[7], 13, "KPK")
    elif pose in ("boceja", "espreguica"):                           # bocejo: boca grande
        corpo[7] = _troca(corpo[7], 12, "KPPPK")
        corpo[8] = _troca(corpo[8], 13, "KPK")
    elif pose == "susto":                                            # boca em "o"
        corpo[7] = _troca(corpo[7], 13, "KKK")
    if pose == "susto":                                              # orelhas para trás (achatadas)
        corpo[0] = "." * LARG
        corpo[1] = _troca(corpo[1], 9, ".KK.....KK.")
    if pose in ("pulo", "bote"):
        pernas = PERNAS["pulo"]
    elif pose == "andar":
        pernas = PERNAS["abc"[quadro % 3]] if quadro % 4 != 3 else PERNAS["b"]
    elif pose == "espreguica":
        pernas = PERNAS["estica"]
    elif pose == "lambe":
        pernas = PERNAS["lambe"]
    else:
        pernas = PERNAS["a"]
    s = art.spr(["." * LARG] * TOPO + corpo + pernas, _pal(pet))
    k = _contorno(pet)
    if pose == "lambe":                                              # a pata na boca, sobe e desce; a língua aparece
        cor = PETS[pet]["pal"]["C"]
        dy = (quadro // 6) % 2
        y = TOPO + 8 - dy
        s.fill(k, (12, y - 1, 3, 4)); s.fill(cor, (13, y, 1, 3)); s.set_at((12, y), cor)
        if dy:
            s.set_at((15, TOPO + 8), PETS[pet]["pal"]["P"])
    _coleira(s, COLEIRAS.get(coleira, {}), k, TOPO)
    _chapeu(s, chapeu, k, TOPO)
    # animação limitada (Hanna-Barbera): parado, só a cabeça balança, 1 px, separada do corpo pela coleira
    if pose == "parado" and (quadro // 30) % 2:
        cab = pygame.Rect(CABECA_X, 0, LARG - CABECA_X, TOPO + 9)
        pedaco = s.subsurface(cab).copy()
        s.fill((0, 0, 0, 0), cab)
        s.blit(pedaco, (CABECA_X, 1))
    return s


def _coleira(s, co, k, y0):
    """No pescoço: a linha do queixo vira a coleira (separa a cabeça do corpo)."""
    cor = co.get("cor")
    if not cor:
        return
    y = y0 + 8
    escuro = tuple(int(c * 0.65) for c in cor)
    if co.get("lenco"):                                            # bandana: faixa + triângulo de bolinhas
        s.fill(cor, (10, y, 8, 1))
        pygame.draw.polygon(s, cor, [(11, y + 1), (16, y + 1), (14, y + 3)])
        s.set_at((11, y + 1), escuro); s.set_at((16, y + 1), escuro)
        s.set_at((13, y + 1), (255, 255, 255))
        s.set_at((14, y + 2), (255, 255, 255))
        return
    if co.get("esteto"):                                           # tubo em volta do pescoço, diafragma no peito
        s.fill(cor, (10, y, 8, 1))
        s.set_at((13, y + 1), cor); s.set_at((13, y + 2), cor)
        s.fill((220, 226, 240), (12, y + 3, 3, 1)); s.set_at((13, y + 3), (255, 255, 255))
        s.set_at((10, y), (60, 60, 70)); s.set_at((17, y), (60, 60, 70))   # olivas pretas nas pontas
        return
    s.fill(cor, (10, y, 8, 1))
    s.set_at((10, y), escuro); s.set_at((17, y), escuro)
    if co.get("guizo"):                                            # guizo redondo pendurado no meio
        ouro = (255, 220, 60) if not co.get("brilha") else (255, 245, 170)
        s.fill(ouro, (13, y + 1, 2, 2))
        s.set_at((13, y + 2), (200, 150, 30))
        s.set_at((14, y + 1), (255, 255, 230))


def _chapeu(s, ch, k, y0):
    """A cabeça vai de x = 10 a 18 (orelhas em 10 e 18, linhas 0–2); os olhos ficam livres (linha 4)."""
    if ch == "laco":                                               # laço na orelha esquerda
        rosa, claro = (250, 110, 170), (255, 200, 225)
        for x, y in ((7, -1), (7, 0), (7, 1), (8, 0), (8, -1), (8, 1), (10, -1), (10, 0), (10, 1), (11, 0),
                     (11, -1), (11, 1)):
            s.set_at((x + 0, y0 + y), rosa)
        s.set_at((7, y0 - 1), claro); s.set_at((10, y0 - 1), claro)
        s.set_at((9, y0), (200, 60, 120))                            # o nó
    elif ch == "flor":                                             # margarida atrás da orelha direita
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            s.set_at((18 + dx, y0 - 1 + dy), (255, 255, 255) if dx == 0 or dy == 0 else (255, 210, 230))
        s.set_at((18, y0 - 1), (255, 200, 40))
        s.set_at((17, y0 + 1), (80, 170, 80))                       # folhinha
    elif ch == "touca":                                            # touca cirúrgica: cobre a testa, não os olhos
        verde, escuro = (90, 190, 160), (50, 140, 115)
        s.fill(k, (10, y0 - 1, 9, 1))
        s.fill(verde, (10, y0, 9, 3))
        s.fill(escuro, (10, y0 + 2, 9, 1))
        for x in (12, 15):
            s.set_at((x, y0), (150, 230, 205))
        s.set_at((9, y0 + 2), escuro); s.set_at((8, y0 + 3), escuro)    # amarração atrás
    elif ch == "festa":                                            # cone listrado, inclinado, com pompom
        for i in range(7):
            larg = 1 + i // 2 * 2
            cor = (255, 90, 120) if (i // 2) % 2 else (90, 190, 255)
            s.fill(cor, (14 - larg // 2, y0 - 6 + i, larg, 1))
        s.fill((255, 230, 80), (13, y0 - 8, 2, 2))
        s.fill((250, 250, 255), (11, y0 + 1, 7, 1))                  # aba branca
    elif ch == "gorro":                                            # gorro de lã: dobra branca e ponta caída
        verm, escuro = (220, 50, 60), (170, 30, 45)
        s.fill(verm, (10, y0 - 2, 9, 3))
        s.fill(escuro, (10, y0 - 2, 9, 1))
        s.fill((250, 250, 255), (10, y0 + 1, 9, 2))
        s.fill(verm, (7, y0 - 3, 4, 2)); s.set_at((7, y0 - 1), verm)
        s.fill((250, 250, 255), (5, y0 - 1, 2, 2))                    # pompom
    elif ch == "bruxa":                                            # cone torto, aba larga e fivela
        roxo, escuro = (80, 50, 120), (50, 30, 80)
        s.fill(escuro, (8, y0 + 1, 12, 1))
        s.fill(roxo, (8, y0, 12, 1))
        for i, (x, w) in enumerate(((11, 7), (12, 5), (12, 4), (13, 3), (13, 2), (12, 2), (11, 2))):
            s.fill(roxo, (x, y0 - 1 - i, w, 1))
        s.fill((250, 200, 60), (13, y0 - 1, 3, 1))
        s.set_at((14, y0 - 1), escuro)
    elif ch == "coroa":                                            # ouro de três pontas e rubi
        ouro, escuro = (250, 200, 50), (200, 140, 30)
        s.fill(ouro, (11, y0, 7, 2))
        s.fill(escuro, (11, y0 + 1, 7, 1))
        for x in (11, 14, 17):
            s.set_at((x, y0 - 1), ouro)
            s.set_at((x, y0 - 2), ouro if x == 14 else (255, 240, 160))
        s.set_at((14, y0), (220, 40, 60))
        s.set_at((12, y0), (80, 160, 255)); s.set_at((16, y0), (80, 200, 120))


_cache = {}


def sprite(pet, coleira="nenhuma", chapeu="nenhum", pose="parado", quadro=0, virado=1):
    """Sprite do pet (20×21 com o espaço do chapéu), pivô = centro-baixo."""
    if pose == "parado":
        quadro %= 180
    elif pose == "andar":
        quadro %= 12
    elif pose in POSES_ROSTO:
        quadro %= 24
    else:
        quadro = 0
    ch = (pet, coleira, chapeu, pose, quadro, virado)
    if ch not in _cache:
        s = _desenhar(pet, coleira, chapeu, pose, quadro)
        _cache[ch] = s if virado > 0 else pygame.transform.flip(s, True, False)
    return _cache[ch]


def icone(pet, coleira="nenhuma", chapeu="nenhum", escala=3):
    return pygame.transform.scale_by(sprite(pet if pet != "nenhum" else "gato_branco", coleira, chapeu), escala)


# --------------------------------------------------------------------- o pet na fase

DURACAO_BOTE = 20
ALCANCE_BOTE = 56
ATRASO = 12                  # quadros de atraso no rastro do herói


class Pet:
    """Segue o rastro do herói; bote() lança o ataque. Coordenadas do mundo; (x, y) = centro-baixo.

    Animação de desenho animado: estica no salto e amassa na aterrissagem (squash & stretch), encolhe antes do bote
    (antecipação), explosão radial chapada quando o bote acerta (Billy e Mandy), ações à toa quando fica parado
    (lambe a pata, boceja, espreguiça) e reações às questões: reagir("acerto") pula com coraçõezinhos;
    reagir("erro") arrepia, treme o contorno (A Vaca e o Frango) e solta uma gota de suor."""

    ACOES = (("lambe", 72), ("boceja", 40), ("espreguica", 56))

    def __init__(self, pet, coleira, chapeu, x, y):
        self.pet, self.coleira, self.chapeu = pet, coleira, chapeu
        self.x, self.y = x, y
        self.virado = 1
        self.anim = 0
        self.bote_t = 0
        self.bote_de = self.bote_ate = (x, y)
        self.espera = 0
        self.acertou = set()
        self.andando = False
        self.vy = 0.0
        self.no_ar = False
        self.amassa = 0                       # quadros de squash da aterrissagem
        self.ocioso = 0                       # quadros parado (para as ações à toa)
        self.acao, self.acao_t = None, 0
        self.reacao, self.reacao_t = None, 0
        self.impactos = []                    # [x, y, t] da explosão do bote (no mundo)
        self.forma = None                     # tela conceito: fn(pose, quadro, virado) no lugar do gato (figurino.ELENCO)
        self._n_acertos = 0

    @property
    def atacando(self):
        return self.bote_t > 0

    def bote(self, p):
        """Salta para a frente do herói (do lado para onde ele olha)."""
        if self.bote_t or self.espera:
            return False
        self.virado = p.virado
        self.bote_de = (self.x, self.y)
        self.bote_ate = (p.cx + p.virado * ALCANCE_BOTE, p.y + p.h)
        self.bote_t = 1
        self.acertou = set()
        self._n_acertos = 0
        self.acao = None
        return True

    def reagir(self, tipo):
        """'acerto' (pulinho feliz com corações) ou 'erro' (susto, pelo arrepiado)."""
        self.reacao, self.reacao_t = ("feliz", 70) if tipo == "acerto" else ("susto", 60)
        self.acao = None

    def update(self, p):
        self.anim += 1
        self.espera = max(0, self.espera - 1)
        self.amassa = max(0, self.amassa - 1)
        self.reacao_t = max(0, self.reacao_t - 1)
        if not self.reacao_t:
            self.reacao = None
        for im in self.impactos:
            im[2] += 1
        self.impactos = [im for im in self.impactos if im[2] < 10]
        if len(self.acertou) > self._n_acertos:                      # o bote acertou: explosão nas patas
            self._n_acertos = len(self.acertou)
            self.impactos.append([self.x + self.virado * 10, self.y - 8, 0])
        if self.bote_t:
            self.bote_t += 1
            k = min(1.0, self.bote_t / (DURACAO_BOTE * 0.6))          # vai rápido, fica um instante, volta seguindo
            (x0, y0), (x1, y1) = self.bote_de, self.bote_ate
            self.x = x0 + (x1 - x0) * k
            self.y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * 14
            if self.bote_t >= DURACAO_BOTE:
                self.bote_t = 0
                self.espera = 8
                self.amassa = 6
            return
        hist = p.historico
        if len(hist) > ATRASO:
            hx, hy = hist[-ATRASO]
        else:
            hx, hy = p.cx, p.y + p.h
        alvo_x = hx - p.virado * 14
        dx = alvo_x - self.x
        self.andando = abs(dx) > 1.2
        if self.andando:
            self.virado = 1 if dx > 0 else -1
        else:
            self.virado = p.virado
        self.x += dx * 0.22
        y0 = self.y
        self.y += (hy - self.y) * 0.35
        self.vy = self.y - y0
        no_ar = abs(self.vy) > 0.8
        if self.no_ar and not no_ar:                                   # aterrissou: amassa
            self.amassa = 6
        self.no_ar = no_ar
        # ações à toa: depois de um tempo parado, uma de cada vez
        if self.andando or no_ar or self.reacao:
            self.ocioso, self.acao = 0, None
        else:
            self.ocioso += 1
            if self.acao:
                self.acao_t -= 1
                if self.acao_t <= 0:
                    self.acao, self.ocioso = None, 0
            elif self.ocioso > 150 and (self.ocioso * 7919 + self.anim) % 97 == 0:
                self.acao, self.acao_t = self.ACOES[(self.anim // 97) % len(self.ACOES)]

    def pose(self):
        if self.bote_t:
            return "bote"
        if abs(self.vy) > 0.8:
            return "pulo"
        if self.andando:
            return "andar"
        return self.reacao or self.acao or "parado"

    def _escala(self, pose):
        """(sx, sy) de squash & stretch: antecipação, esticada no ar, amassada no chão."""
        if pose == "bote":
            t = self.bote_t
            if t <= 3:
                return 1.2, 0.8                                    # encolhe antes de saltar
            if t <= 10:
                return 1.3, 0.82                                   # estica na direção do bote
            return 1.0, 1.0
        if self.amassa:
            k = self.amassa / 6
            return 1 + 0.28 * k, 1 - 0.24 * k
        if pose == "pulo":
            return (0.9, 1.12) if self.vy < 0 else (0.95, 1.06)
        if pose == "feliz":
            fase = (self.reacao_t % 18) / 18                       # pulinhos: amassa no chão, estica no alto
            return (1.15, 0.86) if fase < 0.2 else (0.9, 1.12)
        if pose == "susto":
            return (1.12, 1.12) if self.reacao_t > 40 else (1.05, 1.05)   # pelo arrepiado
        if pose == "espreguica":
            k = math.sin(math.pi * (1 - self.acao_t / 56))
            return 1 + 0.22 * k, 1 - 0.14 * k
        if pose == "parado":                                       # respira
            return 1.0, 1.0 + 0.04 * (math.sin(self.anim / 14) > 0.6)
        return 1.0, 1.0

    def area(self):
        """Retângulo que acerta durante o bote (as patas da frente)."""
        return (self.x + self.virado * 4 - 7, self.y - 12, 14, 12)

    def draw(self, s, cam):
        cx, cy = cam
        pose = self.pose()
        quadro = self.anim // 5 if pose == "andar" else self.anim
        if self.forma:
            spr = self.forma(pose, quadro, self.virado)
        else:
            spr = sprite(self.pet, self.coleira, self.chapeu, pose, quadro, self.virado)
        sx, sy = self._escala(pose)
        if (sx, sy) != (1.0, 1.0):
            spr = pygame.transform.scale(spr, (max(1, round(spr.get_width() * sx)), max(1, round(spr.get_height() * sy))))
        pulinho = 0
        if pose == "feliz":
            pulinho = int(abs(math.sin(self.reacao_t / 18 * math.pi)) * 7)
        x, y = int(self.x - spr.get_width() / 2 - cx), int(self.y - spr.get_height() - cy) + 1 - pulinho
        if pose == "susto" and self.reacao_t > 30:                 # contorno que treme
            x += (self.anim % 3) - 1
            y += (self.anim // 2) % 2
        if pose == "bote" and self.bote_t > 3:                     # rastro de velocidade
            for k in (1, 2):
                s.fill((255, 255, 255), (x - self.virado * (4 + 5 * k) + spr.get_width() // 2,
                                         y + 12 + 2 * k, 4, 1))
        s.blit(spr, (x, y))
        topo_cab = y + (0 if self.forma else int(TOPO * sy))
        if COLEIRAS.get(self.coleira, {}).get("brilha") and (self.anim // 10) % 6 == 0:
            s.set_at((x + (14 if self.virado > 0 else LARG - 15), y + TOPO + 9), (255, 255, 255))
        if pose == "bote" and 6 <= self.bote_t <= 14:              # arranhão: três riscos na frente
            fx = int(self.x + self.virado * 12 - cx)
            fy = int(self.y - 12 - cy)
            for i in range(3):
                for j in range(5):
                    s.set_at((fx + self.virado * (j - 2 + i), fy + i * 3 + j), (255, 255, 255))
        for ix, iy, t in self.impactos:                            # explosão radial chapada: abre e fecha
            _estouro(s, int(ix - cx), int(iy - cy), 2 + 6 * math.sin(math.pi * (t + 1) / 11), t)
        if pose == "feliz":                                        # coraçõezinhos subindo
            for k in range(2):
                fase = (70 - self.reacao_t + k * 22) % 44
                if fase < 34:
                    hx = int(self.x - cx) + self.virado * 4 + (k * 2 - 1) * (4 + fase // 6)
                    s.blit(_coracao(), (hx - 3, topo_cab - 4 - fase // 2))
        elif pose == "susto" and self.reacao_t > 12:               # gota de suor e "!" em cima
            gx = int(self.x - cx) - self.virado * 1
            gy = topo_cab + 1 + (60 - self.reacao_t) // 8
            s.fill((140, 200, 255), (gx, gy, 2, 3)); s.set_at((gx, gy - 1), (140, 200, 255))
            s.set_at((gx, gy), (230, 245, 255))
            ex = int(self.x - cx) + self.virado * 4
            s.fill((255, 80, 80), (ex, topo_cab - 9, 2, 4)); s.fill((255, 80, 80), (ex, topo_cab - 4, 2, 1))
        elif pose == "boceja" and self.acao_t < 30:                 # "z" saindo
            s.blit(art.texto_px("z", (255, 255, 255)), (int(self.x - cx) + self.virado * 9, topo_cab - 6))


def _estouro(s, x, y, r, t):
    """Mini explosão radial de 8 pontas, vermelho e amarelo alternando com o tempo."""
    cores = ((255, 220, 70), (230, 60, 60)) if t % 2 else ((230, 60, 60), (255, 220, 70))
    for i, (raio, cor) in enumerate(((r, cores[0]), (r * 0.55, cores[1]))):
        pts = []
        for k in range(16):
            a = k * math.pi / 8 + t * 0.2
            rr = raio if k % 2 == 0 else raio * 0.45
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        pygame.draw.polygon(s, cor, pts)


CORACAO = [".KK.KK.",
           "KRRKRRK",
           "KRRRRRK",
           ".KRRRK.",
           "..KRK..",
           "...K..."]


def _coracao():
    if "coracao" not in _cache:
        _cache["coracao"] = art.spr(CORACAO, {"K": (90, 30, 50), "R": (255, 100, 140)})
    return _cache["coracao"]


PATA = [".K.K.",
        "KPKPK",
        ".K.K.",
        ".KPK.",
        "KPPPK",
        ".KKK."]


def pata(cor=(250, 160, 186)):
    """Marca de patinha (cursor e marcadores das listas, no lugar do antigo ovo)."""
    ch = ("pata", cor)
    if ch not in _cache:
        _cache[ch] = art.spr(PATA, {"K": (60, 50, 80), "P": cor})
    return _cache[ch]
