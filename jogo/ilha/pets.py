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


# --------------------------------------------------------------------- desenho (pixel art 17×12, virado à direita)

TOPO = 6                     # linhas livres acima da cabeça para o chapéu
CORPO = [
    "...........K...K.",
    "..........KPK.KPK",
    "..........KCCKCCK",
    ".KK.......KCCCCCK",
    "KCK.......KEcCcEK",
    "KCK.......KCCPCCK",
    ".KCKKKKKKKKBCCCBK",
    "..KCCcCCcCCCKKKK.",
    "..KCCCcCCCcCCK...",
    "..KBBBBBBBBBBK...",
]
CORPO_RABO2 = ["...K.......K...K.", "..KCK.....KPK.KPK", "..KCK.....KCCKCCK", "..KCK.....KCCCCCK",
               "...KCK....KEcCcEK", "....K.....KCCPCCK"]          # rabo para cima (parado, abanando)
PERNAS = {
    "a": ["...KC.KC..KC.KC..", "...KK.KK..KK.KK.."],
    "b": ["....KCKC...KCKC..", "....KKKK...KKKK.."],
    "c": ["..KC...KC.KC...KC", "..KK...KK.KK...KK"],
    "pulo": [".KC.........KC...", "KK...........KK.."],
}
PISCA = "KCCcCcCK"                                            # linha dos olhos fechados (substitui KEcCcEK)


def _pal(pet):
    return dict(PETS[pet]["pal"], W=(255, 255, 255))


def _desenhar(pet, coleira, chapeu, pose, quadro):
    corpo = list(CORPO)
    if pose == "parado" and (quadro // 20) % 2:
        corpo[:6] = CORPO_RABO2
    if pose == "parado" and quadro % 90 > 84:
        corpo[4] = corpo[4].replace("KEcCcEK", "K" + PISCA[1:7])
    if pose in ("pulo", "bote"):
        pernas = PERNAS["pulo"]
    elif pose == "andar":
        pernas = PERNAS["abc"[quadro % 3]] if quadro % 4 != 3 else PERNAS["b"]
    else:
        pernas = PERNAS["a"]
    linhas = ["." * 17] * TOPO + corpo + pernas
    s = art.spr(linhas, _pal(pet))
    y0 = TOPO
    co = COLEIRAS.get(coleira, {})
    if co.get("cor"):
        if co.get("lenco"):
            pygame.draw.polygon(s, co["cor"], [(10, y0 + 6), (14, y0 + 6), (12, y0 + 9)])
            s.set_at((12, y0 + 7), (255, 255, 255))
        elif co.get("esteto"):
            s.fill(co["cor"], (10, y0 + 6, 5, 1))
            s.set_at((10, y0 + 7), co["cor"])
            s.set_at((10, y0 + 8), (220, 224, 236))
        else:
            s.fill(co["cor"], (10, y0 + 6, 5, 1))
            if co.get("guizo"):
                s.set_at((12, y0 + 7), (255, 220, 60))
    ch = chapeu
    if ch == "laco":
        for x, y in ((9, 0), (10, 1), (11, 0), (9, 2), (11, 2), (10, 1)):
            s.set_at((x, y0 + y - 1), (250, 110, 170))
        s.set_at((10, y0), (255, 200, 225))
    elif ch == "flor":
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            s.set_at((16 + dx if 16 + dx < 17 else 16, y0 + 1 + dy), (255, 255, 255))
        s.set_at((16, y0 + 1), (255, 210, 60))
    elif ch == "touca":
        s.fill((70, 180, 150), (10, y0 - 1, 7, 3))
        s.fill((50, 150, 120), (10, y0 + 1, 7, 1))
        s.set_at((11, y0 - 1), (140, 230, 200))
    elif ch == "festa":
        for i in range(6):
            larg = 1 + i // 2
            cor = (255, 90, 120) if i % 2 else (90, 190, 255)
            s.fill(cor, (13 - larg // 2, y0 - 5 + i, larg, 1))
        s.set_at((13, y0 - 6), (255, 230, 80))
    elif ch == "gorro":
        s.fill((220, 50, 60), (10, y0 - 2, 7, 3))
        s.fill((250, 250, 255), (10, y0 + 1, 7, 1))
        s.fill((220, 50, 60), (8, y0 - 3, 4, 2))
        s.set_at((7, y0 - 3), (250, 250, 255))
    elif ch == "bruxa":
        s.fill((60, 40, 90), (9, y0, 9 if 9 + 9 <= 17 else 8, 1))
        for i in range(5):
            s.fill((60, 40, 90), (12 + i // 3, y0 - 1 - i, 3 - i // 2, 1))
        s.set_at((13, y0 - 1), (250, 200, 60))
    elif ch == "coroa":
        s.fill((250, 200, 50), (10, y0 - 1, 7, 2))
        for x in (10, 13, 16):
            s.set_at((x, y0 - 2), (250, 200, 50))
        s.set_at((13, y0 - 1), (220, 40, 60))
    return s


_cache = {}


def sprite(pet, coleira="nenhuma", chapeu="nenhum", pose="parado", quadro=0, virado=1):
    """Sprite do pet (17×18 com o espaço do chapéu), pivô = centro-baixo."""
    if pose == "parado":
        quadro %= 180
    elif pose == "andar":
        quadro %= 12
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
    """Segue o rastro do herói; bote() lança o ataque. Coordenadas do mundo; (x, y) = centro-baixo."""

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
        return True

    def update(self, p):
        self.anim += 1
        self.espera = max(0, self.espera - 1)
        if self.bote_t:
            self.bote_t += 1
            k = min(1.0, self.bote_t / (DURACAO_BOTE * 0.6))          # vai rápido, fica um instante, volta seguindo
            (x0, y0), (x1, y1) = self.bote_de, self.bote_ate
            self.x = x0 + (x1 - x0) * k
            self.y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * 14
            if self.bote_t >= DURACAO_BOTE:
                self.bote_t = 0
                self.espera = 8
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

    def pose(self):
        if self.bote_t:
            return "bote"
        if abs(self.vy) > 0.8:
            return "pulo"
        return "andar" if self.andando else "parado"

    def area(self):
        """Retângulo que acerta durante o bote (as patas da frente)."""
        return (self.x + self.virado * 4 - 7, self.y - 12, 14, 12)

    def draw(self, s, cam):
        cx, cy = cam
        pose = self.pose()
        spr = sprite(self.pet, self.coleira, self.chapeu, pose, self.anim // 5 if pose == "andar" else self.anim,
                     self.virado)
        x, y = int(self.x - spr.get_width() / 2 - cx), int(self.y - spr.get_height() - cy) + 1
        if pose == "bote" and self.bote_t > 3:                    # rastro de velocidade
            for k in (1, 2):
                s.fill((255, 255, 255), (x - self.virado * (4 + 5 * k) + spr.get_width() // 2,
                                         y + 10 + 2 * k, 4, 1))
        s.blit(spr, (x, y))
        if COLEIRAS.get(self.coleira, {}).get("brilha") and (self.anim // 10) % 6 == 0:
            s.set_at((x + (12 if self.virado > 0 else 4), y + TOPO + 6), (255, 255, 255))
        if pose == "bote" and 6 <= self.bote_t <= 14:              # arranhão: três riscos na frente
            fx = int(self.x + self.virado * 12 - cx)
            fy = int(self.y - 12 - cy)
            for i in range(3):
                for j in range(5):
                    s.set_at((fx + self.virado * (j - 2 + i), fy + i * 3 + j), (255, 255, 255))


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
