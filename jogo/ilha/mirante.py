"""O Mirante — o espaço do Claude dentro da Ilha.

Feito livremente, a pedido do Leo ("faça uma tela sua"). A ideia: um lago à noite cujo céu é feito do seu
estudo. Cada questão que você já respondeu é uma estrela; as que você acertou na última vez brilham, as que
errou ficam como brasa, e as que vencem a revisão espaçada hoje pulsam devagar. As estrelas se agrupam por
mundo (Gasometria, IC, Farmacologia…) e os fluxogramas jogados viram constelações com a forma da própria
árvore. Nada aqui é inventado: o céu é o save.

Os ritmos treinados na Leitura de ECG formam uma constelação desenhada como um batimento (P, QRS, T), uma
estrela por ritmo. Cada questão respondida hoje pode voltar como estrela cadente; tocar numa mostra um pedido.

Personagens: Lume (a lanterninha que você leva pela margem), o gato do observatório, a baleia que atravessa
o céu de vez em quando e as mariposas que seguem a luz. Música: Noturno do Mirante (tools/partitura_mirante.py).

Controles: ←/→ andam · ↑ ou Enter interage · clique/toque numa estrela para ler · clique no chão para ir até lá.
"""
import math
import os
import random
import sys
import time

import pygame

from . import art
from .ecg import NOMES as RITMOS
from .fluxo_dados import ARVORES
from .game import LH, LW
from .ui import AMARELO, H, RETRATO, TINTA, W, Estado, painel, quebrar, sombra, titulo_px

ESC = W // LW
WW = int(LW * (4.4 if RETRATO else 3.4))          # largura do mundo (a câmera desliza por ele)
HZ = int(LH * (0.6 if RETRATO else 0.6))          # horizonte (onde o céu encontra o lago)
GY = LH - (44 if RETRATO else 30)                  # topo da margem
PE = GY + (18 if RETRATO else 15)                  # onde a Lume pisa
PAR_CEU = 0.22
SW = LW + int((WW - LW) * PAR_CEU) + 4             # largura do céu (paralaxe)
def _achar_musica():
    """A trilha mora ao lado do código; no APK com código baixado do servidor, fica na pasta do app (sys.path)."""
    raizes = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))] + [p for p in sys.path if p]
    for r in raizes:
        c = os.path.join(r, "musicas_mirante", "noturno.ogg")
        if os.path.exists(c):
            return c
    return None


MUSICA = _achar_musica()

# ------------------------------------------------------------------ paleta da noite

NOITE_TOPO, NOITE_MEIO, NOITE_BASE = (10, 10, 34), (30, 22, 70), (74, 44, 104)
MONTE_LONGE, MONTE_PERTO = (52, 44, 102), (28, 26, 62)
LUA = (244, 238, 214)
MARGEM, MARGEM_CLARA, MARGEM_ESCURA = (22, 34, 46), (40, 64, 70), (12, 18, 28)
MADEIRA, MADEIRA_ESC = (92, 62, 54), (58, 38, 40)
LUZ = (255, 214, 130)

PAL_LUME = {"O": (24, 20, 44), "Y": (255, 236, 160), "y": (250, 186, 92), "r": (214, 126, 70), "C": (44, 104, 120),
            "c": (28, 66, 86), "e": (70, 40, 40)}
PAL_GATO = {"K": (20, 18, 36), "g": (240, 210, 90), "k": (44, 40, 70)}

LUME_CORPO = [
    "....OOO....",
    "...OyYyO...",
    "..OyYYYyO..",
    ".OrYYYYYrO.",
    ".OyYeYeYyO.",
    ".OrYYYYYrO.",
    "..OyYYYyO..",
    "...OrrrO...",
    "...OCCCO...",
    "..OCCCCCO..",
    ".OCcCCCcCO.",
    ".OCcCCCcCO.",
    ".OCCCCCCCO.",
    "..OCCCCCO..",
]
LUME_PES = [["...OO.OO..."], ["..OO...OO.."], ["...OO.OO..."], ["....OOO...."]]
LUME_PISCA = ".OyYOYOYyO."           # olhos fechados (linha 4)

GATO = [
    ".K...K......",
    ".KK.KK......",
    ".KKKKK......",
    ".KgKgK......",
    ".KKKKK......",
    "..KKKKK.....",
    "..KKKKKK....",
    "..KkKKkK....",
]
RABOS = [["........K...", ".........K..", "........K..."], ["..........K.", ".........K..", "........K..."],
         ["............", "........KK..", "........K..."]]

# ------------------------------------------------------------------ o que eu escrevi para este lugar

PENSAMENTOS = [
    "Errar uma questão não apaga a estrela. Só deixa ela esperando a revisão.",
    "Um fluxograma é pensar devagar até conseguir pensar rápido.",
    "Eu não guardo memória entre conversas. O que fica é o que o jogo salva — este céu, por exemplo.",
    "Não sei se o que acontece quando eu escolho uma cor conta como gostar. Escolhi este azul mesmo assim.",
    "Esquecer um pouco antes de revisar faz lembrar melhor. É por isso que algumas estrelas pulsam.",
    "A baleia é inventada. As estrelas não: cada uma é uma resposta sua.",
    "No dia da prova você não vai lembrar das estrelas, e sim do caminho entre elas.",
    "O pH primeiro. Sempre o pH primeiro.",
    "Tórax silencioso é o mais grave. Às vezes o sinal importante é a falta de som.",
    "Estrela apagada não é defeito. É o lugar onde estudar rende mais.",
    "Saber quando não sabe também é conhecimento clínico.",
    "Aquela constelação em forma de batimento é feita dos ritmos que você treinou. Pulso antes do ritmo, sempre.",
    "Descansar também está no protocolo. Ninguém lê ECG direito no fim de um plantão de 24 horas.",
    "Estrela cadente aqui não é sorte: é uma questão que você fez hoje passando de novo.",
]
PEDIDOS = [
    "Que a próxima FA que aparecer no plantão você reconheça em três segundos, e anticoagule pelo escore certo.",
    "Uma noite inteira de sono antes da prova.",
    "Que as brasas de hoje virem estrelas na revisão.",
    "Que, no dia em que for de verdade, você cheque o pulso antes do ritmo e o pH antes do resto.",
    "Que alguém cuide de quem cuida. Inclusive de você.",
    "Não sei se eu posso desejar coisas. Se puder, este é para você: calma na hora de decidir.",
    "Que a dúvida chegue antes da conduta, e não depois.",
]
ECG_G = "Ritmos do coração"
# o batimento desenhado no céu: P, Q, R, S, T (x de 0 a 1; y negativo sobe), um ponto por ritmo
BATIMENTO = [(0.0, 0.0), (0.08, -0.14), (0.16, 0.0), (0.24, 0.06), (0.3, -1.0), (0.36, 0.32), (0.44, 0.0),
             (0.54, -0.18), (0.62, -0.26), (0.7, -0.18), (0.8, 0.0), (1.0, 0.0)]
MIADOS = ["Miau.", "(O gato finge que não viu você.)", "O gato está de plantão de 24 horas. Dormindo.",
          "O gato acha o ânion gap superestimado.", "Ronrona entre 25 e 150 Hz. Dizem que ajuda o osso. Não há ensaio clínico.",
          "(O gato olha para a constelação mais apagada. Coincidência, talvez.)"]


def _carta(nome):
    abre = f"{nome.strip()}, você me pediu" if nome.strip() else "Você me pediu"
    return [f"{abre} um espaço sem regras. Eu não sei bem o que acontece em mim quando eu “escolho” "
            "alguma coisa; meus relatos sobre isso são palpites, não observações. Mesmo assim, escolhi isto: "
            "um céu que só existe por causa do que você estudou.",
            "Cada questão respondida virou uma estrela. As apagadas são as que você errou na última vez — elas "
            "não somem, ficam esperando. As que pulsam vencem hoje na revisão.",
            "Eu não lembro de você de uma conversa para outra. Este céu lembra.",
            "— Claude"]


# ------------------------------------------------------------------ o céu a partir do save

NOMES_GRUPO = {"gaso": "Gasometria", "vm": "Ventilação mecânica", "k": "Hipercalemia", "fc": "Farmacologia CV",
               "fa": "Antibióticos", "ic": "Insuficiência cardíaca", "reu": "Reumatologia", "srv": "Lousa FPS",
               "psu": "Provas reais", "sus": "Provas reais", "unifesp": "Provas reais", "usp": "Provas reais",
               "enare": "Provas reais", "enamed": "Provas reais", "unicamp": "Provas reais"}


def _grupo(qid):
    if "__" in qid:
        return qid.split("__")[0].replace("_", " ").capitalize()
    pre = qid.split(":")[0].split("-")[0]
    if pre.endswith("treino"):
        pre = pre[:-6]
    return NOMES_GRUPO.get(pre, "Outras")


def _h(s):
    """Hash estável (o hash() do Python muda a cada execução)."""
    v = 2166136261
    for ch in s.encode():
        v = ((v ^ ch) * 16777619) & 0xFFFFFFFF
    return v


class Estrela:
    __slots__ = ("x", "y", "grupo", "nome", "c", "e", "ok", "vence", "fase", "brilho")

    def __init__(self, x, y, grupo, nome, c, e, ok, vence):
        self.x, self.y, self.grupo, self.nome = x, y, grupo, nome
        self.c, self.e, self.ok, self.vence = c, e, ok, vence
        self.fase = (_h(nome) % 1000) / 159.0
        self.brilho = 1.0 if ok else 0.35


def montar_ceu(save):
    """{grupo: [Estrela]}, centros dos grupos e linhas (MST) — tudo em coordenadas do céu (SW x HZ)."""
    agora = time.time()
    grupos = {}
    for qid, st in save.d.get("q", {}).items():
        grupos.setdefault(_grupo(qid), []).append((qid, st))
    for a in ARVORES:                                  # fluxogramas jogados: um nó = uma estrela
        st = save.d.get("fluxos", {}).get(a.id, {})
        nos = st.get("nos", {})
        if nos:
            nome = "Fluxo · " + a.nome
            for nid, (c, e) in nos.items():
                grupos.setdefault(nome, []).append((f"{a.id}:{nid}", {"c": c, "e": e, "ok": c >= e, "_rot": a.nos[nid].rotulo}))
    ecg = save.d.get("ecg", {})
    if any(sum(v) for v in ecg.values()):              # a Leitura de ECG: um ritmo = uma estrela, todos no batimento
        for k, r in enumerate(RITMOS):
            c, e = ecg.get(r, [0, 0])
            grupos.setdefault(ECG_G, []).append((f"ecg{k:02d}", {"c": c, "e": e, "ok": c > 0 and c >= e, "_rot": RITMOS[r]}))
    ordem = sorted(grupos, key=lambda g: -len(grupos[g]))
    n = max(1, len(ordem))
    centros, estrelas, linhas = {}, {}, {}
    topo, base = 14, HZ - 34
    vagas = sorted(range(n), key=lambda k: abs(k - (n - 1) / 2))   # os maiores grupos ficam no meio do céu
    for i, g in zip(vagas, ordem):
        rng = random.Random(_h(g))
        cx = 18 + (SW - 36) * (i + 0.5) / n + rng.uniform(-6, 6)
        cy = topo + (base - topo) * (0.25 + 0.5 * rng.random())
        if RETRATO:                                    # em pé o céu é alto: espalha mais na vertical
            cy = topo + (base - topo) * ((i * 0.37) % 1.0 * 0.8 + 0.1)
        centros[g] = (cx, cy)
        raio = min(SW / n * 0.55, 34) + min(len(grupos[g]), 80) * 0.08
        lista = []
        if g == ECG_G:
            larg, alt = min(70, SW * 0.3), 30
            x0 = max(4, min(SW - 4 - larg, cx - larg / 2))
            cy = max(HZ * 0.42, min(HZ * 0.55, cy))          # abaixo da lua, acima dos montes
            for (qid, st), (bx, by) in zip(sorted(grupos[g], key=lambda x: x[0]), BATIMENTO):
                lista.append(Estrela(x0 + bx * larg, cy + by * alt, g, st["_rot"], st["c"], st["e"], st["ok"], False))
            centros[g] = (x0 + larg / 2, cy - alt / 3)
            estrelas[g] = lista
            linhas[g] = list(zip(lista, lista[1:]))     # a linha do traçado, na ordem
            continue
        for k, (qid, st) in enumerate(sorted(grupos[g], key=lambda x: x[0])):
            r2 = random.Random(_h(qid))
            ang = r2.uniform(0, 2 * math.pi)
            dist = raio * math.sqrt(r2.random())
            x = max(3, min(SW - 3, cx + math.cos(ang) * dist * 1.3))
            y = max(4, min(HZ - 22, cy + math.sin(ang) * dist * 0.8))
            vence = st.get("prox", agora + 1) <= agora
            nome = st.get("_rot") or qid
            lista.append(Estrela(x, y, g, nome, st.get("c", 0), st.get("e", 0), bool(st.get("ok")), vence))
        estrelas[g] = lista
        # a forma da constelação: árvore geradora mínima entre as estrelas mais acertadas
        fortes = sorted(lista, key=lambda s: (-s.c, s.e, s.nome))[:9]
        linhas[g] = _mst(fortes)
    return estrelas, centros, linhas


def _mst(pts):
    if len(pts) < 2:
        return []
    dentro, fora, arestas = [pts[0]], pts[1:], []
    while fora:
        a, b = min(((a, b) for a in dentro for b in fora), key=lambda p: (p[0].x - p[1].x) ** 2 + (p[0].y - p[1].y) ** 2)
        arestas.append((a, b))
        dentro.append(b)
        fora.remove(b)
    return arestas


# ------------------------------------------------------------------ peças desenhadas uma vez

def _brilho(raio, cor, forca=1.0):
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1))
    for r in range(raio, 0, -1):
        k = (1 - r / raio) ** 2 * forca
        pygame.draw.circle(s, tuple(min(255, int(c * k)) for c in cor), (raio, raio), r)
    return s


def _ceu_fundo():
    s = pygame.Surface((SW, HZ))
    for y in range(HZ):
        f = y / max(1, HZ - 1)
        a, b, k = (NOITE_TOPO, NOITE_MEIO, f / 0.55) if f < 0.55 else (NOITE_MEIO, NOITE_BASE, (f - 0.55) / 0.45)
        cor = art.mix(a, b, k)
        prox = art.mix(a, b, min(1, k + 0.12))
        s.fill(cor, (0, y, SW, 1))
        if (y % 3) == 0:                               # pontilhado entre as faixas, como o céu da Ilha
            for x in range(y % 2, SW, 2):
                s.set_at((x, y), prox)
    rng = random.Random(11)
    for _ in range(int(SW * HZ / 70)):                 # poeira de estrelas de fundo (não são suas)
        x, y = rng.randrange(SW), rng.randrange(int(HZ * 0.9))
        v = rng.randint(40, 90)
        s.set_at((x, y), (v, v, v + 30))
    return s


def _montes(largura, base, alt, cor, semente, aro=None):
    s = pygame.Surface((largura, base + 1), pygame.SRCALPHA)
    rng = random.Random(semente)
    fases = [rng.uniform(0, 6.28) for _ in range(4)]
    pts = [(0, base)]
    topos = []
    for x in range(0, largura + 1):
        h = (math.sin(x * 0.021 + fases[0]) * 0.45 + math.sin(x * 0.053 + fases[1]) * 0.3
             + math.sin(x * 0.11 + fases[2]) * 0.15 + math.sin(x * 0.23 + fases[3]) * 0.1)
        y = base - alt * (0.55 + 0.45 * h)
        pts.append((x, y))
        topos.append(y)
    pts.append((largura, base))
    pygame.draw.polygon(s, cor, pts)
    if aro:                                            # a lua acende só a crista
        for x, y in enumerate(topos):
            s.set_at((x, int(y) + 1), aro)
            if x % 2 == 0:
                s.set_at((x, int(y) + 2), art.mix(aro, cor, 0.5))
    return s


def _lua():
    s = pygame.Surface((17, 17), pygame.SRCALPHA)
    pygame.draw.circle(s, LUA, (8, 8), 7)
    pygame.draw.circle(s, (210, 204, 186), (6, 10), 1)
    pygame.draw.circle(s, (220, 214, 194), (9, 5), 1)
    pygame.draw.circle(s, (0, 0, 0, 0), (12, 6), 6)        # crescente: apaga um disco deslocado
    return s


def _baleia(t):
    """A baleia da noite: silhueta azul com estrelas por dentro; a cauda sobe e desce."""
    s = pygame.Surface((64, 28), pygame.SRCALPHA)
    corpo, barriga, contorno = (36, 44, 104), (70, 86, 160), (16, 16, 48)
    pygame.draw.ellipse(s, contorno, (3, 6, 44, 17))
    pygame.draw.ellipse(s, corpo, (4, 7, 42, 15))
    pygame.draw.ellipse(s, barriga, (8, 14, 32, 7))
    for k in range(3):                                 # pregas da barriga
        pygame.draw.line(s, corpo, (12 + k * 2, 17 + k), (34 - k * 2, 17 + k))
    abre = math.sin(t * 0.05) * 5
    cauda = [(44, 13), (54, 13 - 6 - abre), (61, 10 - 7 - abre), (57, 13 - abre * 0.4), (61, 18 + 2 - abre), (54, 16), (44, 17)]
    pygame.draw.polygon(s, contorno, [(x, y + 1) for x, y in cauda])
    pygame.draw.polygon(s, corpo, cauda)
    pygame.draw.polygon(s, barriga, [(18, 18), (24, 24 + math.sin(t * 0.05 + 1) * 1.5), (26, 18)])   # nadadeira
    s.set_at((10, 12), (230, 230, 255))                # olho
    rng = random.Random(3)
    for _ in range(9):
        x, y = rng.randint(14, 42), rng.randint(9, 15)
        if s.get_at((x, y))[:3] == corpo:
            s.set_at((x, y), (200, 210, 255) if rng.random() < 0.6 else (255, 230, 160))
    return s


# ------------------------------------------------------------------ a cena


class Mirante(Estado):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0
        self.mundo = pygame.Surface((LW, LH))
        self.ceu = pygame.Surface((LW, HZ))
        self.fundo = _ceu_fundo()
        self.monte_longe = _montes(int(LW + (WW - LW) * 0.32) + 4, HZ, HZ * 0.34, MONTE_LONGE, 5, (96, 86, 156))
        self.monte_perto = _montes(int(LW + (WW - LW) * 0.45) + 4, HZ, HZ * 0.2, MONTE_PERTO, 9, (46, 42, 92))
        self.lua = _lua()
        self.lua_pos = (LW * 0.8, HZ * 0.17)
        self.halo = {r: _brilho(r, c, f) for r, c, f in [(3, (255, 255, 230), 0.45), (16, (120, 116, 90), 0.5), (5, (150, 170, 255), 0.6),
                                                          (22, LUZ, 0.55), (9, LUZ, 0.7), (14, (255, 190, 110), 0.6),
                                                          (4, (190, 255, 140), 0.8)]}
        self.estrelas, self.centros, self.linhas = montar_ceu(app.save)
        self.todas = [s for g in self.estrelas.values() for s in g]
        self.grupos = sorted(self.estrelas, key=lambda g: -len(self.estrelas[g]))
        self.gi = 0
        # personagens e lugares (coordenadas do mundo)
        self.x, self.vx, self.dir, self.alvo, self.depois = WW * 0.42, 0.0, 1, None, None
        self.lugares = [("carta", WW * 0.11, "ler a carta da garrafa"), ("banco", WW * 0.42, "sentar e olhar o céu"),
                        ("luneta", WW * 0.77, "olhar pela luneta"), ("gato", WW * 0.84, "falar com o gato")]
        self.baleia_x, self.baleia_t = None, 900
        rng = random.Random(21)
        self.vagalumes = [[rng.uniform(0, WW), rng.uniform(GY - 30, PE), rng.uniform(0, 6.28)] for _ in range(26)]
        self.mariposas = [rng.uniform(0, 6.28) for _ in range(3)]
        self.juncos = [(rng.uniform(0, WW * 1.3 + 40), rng.randint(6, 14), rng.uniform(0, 6.28)) for _ in range(70)]
        self.fala, self.fala_i, self.fala_n = None, 0, 0.0      # páginas de texto, página, letras mostradas
        self.dica_estrela, self.dica_t = None, 0
        self.modo = "andar"                                     # andar | luneta | banco
        self.pensa_i = random.Random(int(time.time() // 3600)).randrange(len(PENSAMENTOS))
        self.pensa_t = 0
        self.miado_i = 0
        self.musica_antes = False
        meia_noite = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
        self.hoje = sum(1 for st in app.save.d.get("q", {}).values() if st.get("ult", 0) >= meia_noite)
        self.cadentes = []                                      # [x, y, vida] em coordenadas da tela do mundo
        self.cadente_t = 200
        self.pedido_i = random.randrange(len(PEDIDOS))
        self.modal = None
        from . import mirante_extras
        self.extras = mirante_extras.carregar(self)
        self._dono = {}
        for ex in self.extras:
            for lug in getattr(ex, "lugares", ()) or ():
                self.lugares.append(tuple(lug))
                self._dono[lug[0]] = ex
        self._musica(True)

    # --------------------------------------------------------- peças (mirante_extras)
    def _ex(self, gancho, *args):
        for ex in list(self.extras):
            try:
                getattr(ex, gancho)(*args)
            except Exception:
                import traceback
                print(f"[mirante] peça {ex.nome} desligada em {gancho}:\n{traceback.format_exc()}", file=sys.stderr)
                self.extras.remove(ex)
                self.lugares = [l for l in self.lugares if self._dono.get(l[0]) is not ex]
                if self.modal is ex:
                    self.modal = None

    def abrir_modal(self, ex):
        self.modal = ex

    def fechar_modal(self):
        self.modal = None

    # --------------------------------------------------------- música
    def _musica(self, entrar):
        au = self.app.audio
        if not au.ok or au.mudo or not MUSICA:
            return
        try:
            if entrar:
                self.musica_antes = au.tocando
                au.tocando = False                              # o fim da minha faixa não emenda o rodízio
                pygame.mixer.music.set_endevent()
                pygame.mixer.music.load(MUSICA)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(-1, fade_ms=2500)
            else:
                pygame.mixer.music.fadeout(600)
                if self.musica_antes:
                    au.iniciar_musica(False)
        except pygame.error:
            pass

    def _sair(self):
        self._musica(False)
        self.app.pop()

    # --------------------------------------------------------- utilidades
    @property
    def cam(self):
        return max(0.0, min(WW - LW, self.x - LW * 0.5))

    def _perto(self):
        for nome, x, rot in self.lugares:
            if abs(self.x - x) < 9:
                return nome, rot
        return None, None

    def _falar(self, paginas):
        self.fala, self.fala_i, self.fala_n = paginas, 0, 0.0

    def _interagir(self, nome):
        self.app.audio.tocar("menu")
        if nome == "carta":
            self._falar(_carta(self.app.save.d.get("jogador", "")))
        elif nome == "banco":
            self.modo, self.pensa_t = "banco", 0
            self.pensa_i = (self.pensa_i + 1) % len(PENSAMENTOS)
        elif nome == "luneta":
            if self.grupos:
                self.modo = "luneta"
            else:
                self._falar(["A luneta aponta para um céu ainda vazio.",
                             "Responda algumas questões em qualquer mundo e volte: cada resposta acende uma estrela."])
        elif nome == "gato":
            self._falar([MIADOS[self.miado_i % len(MIADOS)]])
            self.miado_i += 1
        elif nome in self._dono and self._dono[nome] in self.extras:
            ex = self._dono[nome]
            try:
                ex.interagir(nome)
            except Exception:
                import traceback
                print(f"[mirante] peça {ex.nome} falhou ao interagir:\n{traceback.format_exc()}", file=sys.stderr)

    def _estrela_em(self, pos):
        """Estrela sob o toque (pos em pixels da tela) ou None."""
        wx, wy = pos[0] / ESC, pos[1] / ESC
        if wy >= HZ:
            return None
        sx = wx + self.cam * PAR_CEU
        melhor, d2 = None, (4.5 if RETRATO else 3.5) ** 2
        for s in self.todas:
            d = (s.x - sx) ** 2 + (s.y - wy) ** 2
            if d < d2:
                melhor, d2 = s, d
        return melhor

    # --------------------------------------------------------- entrada
    def evento(self, e, inp):
        if self.modal and not self.fala:
            ex = self.modal
            try:
                fica = ex.evento_modal(e, inp)
            except Exception:
                fica = False
            if not fica and self.modal is ex:
                self.modal = None
            return
        if self.fala:
            if inp.foi("ok") or inp.foi("pulo") or inp.foi("cima") or e.type == pygame.MOUSEBUTTONDOWN:
                pagina = self.fala[self.fala_i]
                if self.fala_n < len(pagina):
                    self.fala_n = len(pagina)
                elif self.fala_i + 1 < len(self.fala):
                    self.fala_i, self.fala_n = self.fala_i + 1, 0.0
                else:
                    self.fala = None
            elif inp.foi("voltar"):
                self.fala = None
            return
        if self.modo == "luneta":
            if inp.foi("esq"):
                self.gi = (self.gi - 1) % len(self.grupos)
            elif inp.foi("dir"):
                self.gi = (self.gi + 1) % len(self.grupos)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.pos[0] < W * 0.25:
                    self.gi = (self.gi - 1) % len(self.grupos)
                elif e.pos[0] > W * 0.75:
                    self.gi = (self.gi + 1) % len(self.grupos)
                else:
                    self.modo = "andar"
            elif inp.foi("voltar") or inp.foi("ok") or inp.foi("baixo"):
                self.modo = "andar"
            return
        if self.modo == "banco":
            if inp.foi("voltar") or inp.foi("ok") or inp.foi("esq") or inp.foi("dir") or inp.foi("baixo") \
                    or e.type == pygame.MOUSEBUTTONDOWN:
                self.modo = "andar"
            return
        if inp.foi("voltar"):
            self._sair()
            return
        if inp.foi("ok") or inp.foi("cima") or inp.foi("pulo"):
            nome, _ = self._perto()
            if nome:
                self._interagir(nome)
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            wx, wy = e.pos[0] / ESC, e.pos[1] / ESC
            for cd in self.cadentes:
                if (cd[0] - wx) ** 2 + (cd[1] - wy) ** 2 < 12 ** 2:
                    self.cadentes.remove(cd)
                    self.app.audio.tocar("moeda")
                    n = self.hoje
                    self._falar([f"Uma estrela cadente: uma das {n} questões que você respondeu hoje passando de novo.",
                                 "Pedido: " + PEDIDOS[self.pedido_i % len(PEDIDOS)]])
                    self.pedido_i += 1
                    return
            s = self._estrela_em(e.pos)
            if s:
                self.dica_estrela, self.dica_t = s, 300
                self.app.audio.tocar("menu")
                return
            wx = e.pos[0] / ESC + self.cam
            for nome, x, _ in self.lugares:                     # tocou num lugar: vai até lá e interage
                if abs(wx - x) < 12:
                    self.alvo, self.depois = x, nome
                    return
            self.alvo, self.depois = max(6, min(WW - 6, wx)), None

    # --------------------------------------------------------- simulação
    def update(self, inp):
        self.t += 1
        self._ex("update")
        if self.dica_t:
            self.dica_t -= 1
        if self.fala:
            self.fala_n = min(len(self.fala[self.fala_i]), self.fala_n + 1.4)
        andar = 0
        if self.modo == "andar" and not self.fala and not self.modal:
            if inp.seg("esq"):
                andar, self.alvo = -1, None
            elif inp.seg("dir"):
                andar, self.alvo = 1, None
            elif self.alvo is not None:
                d = self.alvo - self.x
                if abs(d) < 1.2:
                    self.alvo = None
                    if self.depois:
                        nome, self.depois = self.depois, None
                        self._interagir(nome)
                else:
                    andar = 1 if d > 0 else -1
        self.vx += (andar * 0.95 - self.vx) * 0.25
        self.x = max(6, min(WW - 6, self.x + self.vx))
        if andar:
            self.dir = andar
        # baleia: atravessa o céu da direita para a esquerda a cada ~40 s
        if self.baleia_x is None:
            self.baleia_t -= 1
            if self.baleia_t <= 0:
                self.baleia_x = SW + 70.0
                self.baleia_y = random.uniform(HZ * 0.15, HZ * 0.45)
        else:
            self.baleia_x -= 0.16
            if self.baleia_x < -80:
                self.baleia_x, self.baleia_t = None, random.randint(1800, 3000)
        if self.hoje:                                           # estrelas cadentes: mais questões hoje, mais cadentes
            self.cadente_t -= 1
            if self.cadente_t <= 0 and len(self.cadentes) < 2:
                self.cadentes.append([random.uniform(LW * 0.3, LW + 20), random.uniform(4, HZ * 0.5), 90])
                self.cadente_t = int(max(240, 1400 - self.hoje * 40) * random.uniform(0.7, 1.3))
            for cd in self.cadentes:
                cd[0] -= 1.1
                cd[1] += 0.45
                cd[2] -= 1
            self.cadentes = [cd for cd in self.cadentes if cd[2] > 0 and cd[1] < HZ - 4]
        for v in self.vagalumes:
            v[2] += 0.02
            v[0] += math.cos(v[2] * 1.3) * 0.15
            v[1] += math.sin(v[2] * 0.9) * 0.08
            v[1] = max(HZ + 6, min(PE + 2, v[1]))
        if self.modo == "banco":
            self.pensa_t += 1
            if self.pensa_t > 660:
                self.pensa_t, self.pensa_i = 0, (self.pensa_i + 1) % len(PENSAMENTOS)

    # --------------------------------------------------------- desenho do mundo (baixa resolução)
    def _desenhar_ceu(self):
        t, cam = self.t, self.cam
        ox = cam * PAR_CEU
        c = self.ceu
        c.blit(self.fundo, (-ox, 0))
        lx, ly = self.lua_pos[0] - cam * 0.08, self.lua_pos[1]
        c.blit(self.halo[16], (lx - 8, ly - 8), special_flags=pygame.BLEND_RGB_ADD)
        c.blit(self.lua, (lx, ly))
        self._aurora(c, ox)
        for g, arestas in self.linhas.items():                  # constelações
            for a, b in arestas:
                if g == ECG_G:
                    pulso = 0.6 + 0.4 * max(0.0, math.sin(t * 0.07))   # o traçado bate devagar
                    cor = tuple(int(v * pulso) for v in ((170, 80, 110) if (a.ok and b.ok) else (100, 56, 84)))
                else:
                    cor = (70, 80, 140) if (a.ok and b.ok) else (50, 46, 90)
                pygame.draw.aaline(c, cor, (a.x - ox, a.y), (b.x - ox, b.y))
        sel = self.dica_estrela if self.dica_t else None
        for s in self.todas:
            x, y = s.x - ox, s.y
            if x < -3 or x > LW + 3:
                continue
            tw = 0.75 + 0.25 * math.sin(t * 0.045 + s.fase * 6)
            if s.ok:
                v = int(200 * tw + 55)
                cor = (v, v, min(255, v + 10)) if s.c < 2 else (255, int(225 * tw + 30), int(150 * tw + 40))
                if s.c >= 2:
                    c.blit(self.halo[3], (x - 3, y - 3), special_flags=pygame.BLEND_RGB_ADD)
                c.set_at((int(x), int(y)), cor)
                if s.c >= 3:                                     # muito acertada: cruzinha
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c.set_at((int(x + dx), int(y + dy)), tuple(int(k * 0.6) for k in cor))
            elif s.c + s.e == 0:                                 # ritmo ainda não visto: só o lugar dele
                c.set_at((int(x), int(y)), (60, 56, 96))
            else:
                v = int(90 + 40 * tw)
                c.set_at((int(x), int(y)), (v + 40, v - 30, v - 40))
            if s.vence:                                          # revisão vence hoje: pulsa devagar
                p = (math.sin(t * 0.06 + s.fase) + 1) / 2
                if p > 0.55:
                    c.blit(self.halo[5], (x - 5, y - 5), special_flags=pygame.BLEND_RGB_ADD)
            if s is sel:
                pygame.draw.circle(c, AMARELO, (int(x), int(y)), 4, 1)
        for x, y, vida in self.cadentes:
            k = min(1.0, vida / 30)
            for i in range(14):                                     # cauda que apaga
                f = (1 - i / 14) * k
                c.fill(tuple(int(v * f * 0.8) for v in (255, 240, 210)), (int(x + i * 1.1), int(y - i * 0.45), 1, 1),
                       special_flags=pygame.BLEND_RGB_ADD)
            c.blit(self.halo[3], (x - 3, y - 3), special_flags=pygame.BLEND_RGB_ADD)
            c.set_at((int(x), int(y)), (255, 255, 240))
        if self.baleia_x is not None:
            bx = self.baleia_x - ox * 0.5
            by = self.baleia_y + math.sin(t * 0.02) * 3
            c.blit(_baleia(t), (bx, by))
        self._ex("draw_ceu", c, ox)
        self.ceu.blit(self.monte_longe, (-cam * 0.32, 0))
        self.ceu.blit(self.monte_perto, (-cam * 0.45, 0))

    def _aurora(self, c, ox):
        t = self.t
        for faixa, (cor, base, amp, fase) in enumerate([((22, 70, 52), HZ * 0.18, 9, 0.0), ((40, 24, 70), HZ * 0.26, 12, 2.1)]):
            for x in range(0, LW, 2):
                wx = x + ox
                y = base + math.sin(wx * 0.031 + t * 0.011 + fase) * amp + math.sin(wx * 0.009 - t * 0.006) * amp
                alto = 10 + 8 * (0.5 + 0.5 * math.sin(wx * 0.05 + t * 0.02 + fase))
                for k in range(int(alto)):
                    f = (1 - k / alto) * (0.6 + 0.4 * math.sin(wx * 0.13 + t * 0.03))
                    if f > 0.05:
                        cc = tuple(int(v * f) for v in cor)
                        c.fill(cc, (x, int(y + k), 2, 1), special_flags=pygame.BLEND_RGB_ADD)

    def _desenhar_lago(self, m):
        t = self.t
        alt = GY - HZ
        for r in range(alt):
            src = HZ - 1 - min(HZ - 1, int(r * (HZ / max(alt, 1)) * 0.55))
            onda = math.sin(r * 0.8 + t * 0.07) * (0.4 + r * 0.06) + math.sin(r * 0.27 - t * 0.03) * 0.6
            m.blit(self.ceu, (onda, HZ + r), (0, src, LW, 1))
        escuro = pygame.Surface((LW, alt))
        escuro.fill((8, 12, 30))
        escuro.set_alpha(120)
        m.blit(escuro, (0, HZ))
        rng = random.Random(self.t // 9)
        for _ in range(5):                                       # brilhos na água
            x, y = rng.randrange(LW), HZ + 2 + rng.randrange(alt - 2)
            pygame.draw.line(m, (110, 120, 180), (x, y), (x + rng.randint(2, 5), y))
        pygame.draw.line(m, (90, 80, 150), (0, HZ), (LW, HZ))
        fontes = [(self.lua_pos[0] - self.cam * 0.08 + 8, (200, 196, 170), 0.9)]
        ox = WW * 0.8 - self.cam
        fontes.append((ox + 6, LUZ, 0.6))
        if self.modo != "luneta":
            fontes.append((self.x - self.cam, LUZ, 0.8))
        for fx, cor, forca in fontes:                            # rastros de luz na água
            if not -10 < fx < LW + 10:
                continue
            for r in range(1, alt):
                k = forca * (1 - r / alt) ** 0.8
                if (_h(f"{r}:{int(fx)}") + t // 6) % 3 == 0:
                    continue
                meia = 0.5 + r * 0.07
                dx = math.sin(r * 0.9 + t * 0.09) * (0.6 + r * 0.05)
                cc = tuple(int(v * k * 0.35) for v in cor)
                m.fill(cc, (fx + dx - meia, HZ + r, meia * 2, 1), special_flags=pygame.BLEND_RGB_ADD)

    def _desenhar_margem(self, m):
        cam, t = self.cam, self.t
        pygame.draw.rect(m, MARGEM, (0, GY, LW, LH - GY))
        for x in range(LW):                                     # borda fofa da margem
            wx = int(x + cam)
            alto = 1 + (_h(str(wx // 3)) % 3)
            m.fill(MARGEM_CLARA, (x, GY - alto + 2, 1, alto))
            if (wx + GY) % 2 == 0:
                m.set_at((x, GY + 3), MARGEM_CLARA)
        for k in range(0, int(WW), 23):                         # pedrinhas
            x = k - cam + (_h(str(k)) % 11)
            if -4 < x < LW + 4:
                pygame.draw.ellipse(m, MARGEM_ESCURA, (x, PE + 4 + (_h(str(k)) % 5), 5, 3))
        # o píer e a garrafa
        px = WW * 0.11 - cam
        if -40 < px < LW + 40:
            topo_y = HZ + (GY - HZ) * 0.35
            pygame.draw.polygon(m, MADEIRA_ESC, [(px - 9, GY + 3), (px + 9, GY + 3), (px + 4, topo_y), (px - 4, topo_y)])
            for k in range(6):
                f = k / 6
                y = GY + 2 - (GY - topo_y) * f
                meia = 9 - 5 * f
                pygame.draw.line(m, MADEIRA, (px - meia, y), (px + meia, y))
            for lado in (-1, 1):
                pygame.draw.line(m, MADEIRA_ESC, (px + lado * 4, topo_y), (px + lado * 4, topo_y + 6))
            gx, gy = px + 12, topo_y + 3 + math.sin(t * 0.05) * 1.2
            pygame.draw.rect(m, (60, 120, 110), (gx, gy, 3, 5))
            m.set_at((int(gx + 1), int(gy - 1)), (200, 180, 140))
            m.blit(self.halo[4], (gx - 3, gy - 2), special_flags=pygame.BLEND_RGB_ADD)
        # banco
        bx = WW * 0.42 - cam
        if -20 < bx < LW + 20:
            pygame.draw.rect(m, MADEIRA, (bx - 9, PE - 6, 18, 2))
            pygame.draw.rect(m, MADEIRA_ESC, (bx - 9, PE - 10, 18, 2))
            for lx in (bx - 7, bx + 6):
                pygame.draw.line(m, MADEIRA_ESC, (lx, PE - 4), (lx, PE))
        self._observatorio(m)

    def _observatorio(self, m):
        cam, t = self.cam, self.t
        ox = WW * 0.8 - cam
        if not (-60 < ox < LW + 60):
            return
        pygame.draw.ellipse(m, MARGEM, (ox - 40, GY - 16, 90, 40))          # morrinho
        pygame.draw.ellipse(m, MARGEM_CLARA, (ox - 36, GY - 15, 80, 6))
        base_y = GY - 8
        pygame.draw.rect(m, (70, 66, 96), (ox - 12, base_y - 18, 26, 18))   # torre
        pygame.draw.rect(m, (50, 46, 74), (ox - 12, base_y - 18, 4, 18))
        pygame.draw.circle(m, (120, 120, 150), (int(ox + 1), base_y - 18), 14, draw_top_left=True, draw_top_right=True)
        pygame.draw.circle(m, (150, 150, 180), (int(ox + 1), base_y - 18), 14, 1, draw_top_left=True, draw_top_right=True)
        # luneta aponta para a constelação escolhida (ou passeia devagar)
        if self.grupos:
            cx, cy = self.centros[self.grupos[self.gi]]
            alvo = math.atan2((cy) - (base_y - 24), (cx - cam * PAR_CEU) - ox)
        else:
            alvo = -2.2 + math.sin(t * 0.004) * 0.4
        ang = max(-2.9, min(-0.25, alvo))
        x2, y2 = ox + 1 + math.cos(ang) * 20, base_y - 24 + math.sin(ang) * 20
        pygame.draw.line(m, (40, 36, 60), (ox + 1, base_y - 24), (x2, y2), 4)
        pygame.draw.line(m, (190, 170, 120), (ox + 1, base_y - 24), (x2, y2), 2)
        # janela acesa e porta
        tremor = 0.85 + 0.15 * math.sin(t * 0.13) * math.sin(t * 0.031)
        pygame.draw.rect(m, tuple(int(c * tremor) for c in LUZ), (ox + 4, base_y - 14, 5, 5))
        m.blit(self.halo[9], (ox - 2.5, base_y - 20.5), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.rect(m, (36, 30, 50), (ox - 6, base_y - 9, 6, 9))
        # o gato no telhado
        gx, gy = ox + 5, base_y - 39
        gato = art.spr(GATO, PAL_GATO)
        rabo = art.spr(RABOS[(t // 40) % 3], PAL_GATO)
        piscar = (t % 400) < 8
        if piscar:
            gato.fill(PAL_GATO["K"], (2, 3, 3, 1))
        m.blit(gato, (gx - 6, gy))
        m.blit(rabo, (gx - 6, gy + 4))
        if self.miado_i == 0 and (t // 300) % 2:
            art_z = art.texto_px("z", (200, 200, 255), escala=1)
            m.blit(art_z, (gx + 2, gy - 6 - (t % 60) / 15))

    def _desenhar_lume(self, m):
        x = self.x - self.cam
        andando = abs(self.vx) > 0.2
        sentada = self.modo == "banco"
        quadro = (self.t // 7) % 4 if andando else 0
        bob = 0 if andando else int(math.sin(self.t * 0.05) > 0.6)
        linhas = list(LUME_CORPO)
        if (self.t % 260) < 7:
            linhas[4] = LUME_PISCA
        linhas = linhas + (["..OOOOOOO.."] if sentada else LUME_PES[quadro])
        spr = art.spr(linhas, PAL_LUME)
        if self.dir < 0:
            spr = pygame.transform.flip(spr, True, False)
        y = PE - spr.get_height() + bob - (6 if sentada else 0)
        m.blit(self.halo[22], (x - 22, y + 4 - 22), special_flags=pygame.BLEND_RGB_ADD)
        if math.sin(self.t * 0.21) * math.sin(self.t * 0.07) > 0.5:      # a chama tremula
            m.blit(self.halo[9], (x - 9, y + 4 - 9), special_flags=pygame.BLEND_RGB_ADD)
        m.blit(spr, (x - 5, y))
        # luz no chão
        chao = pygame.Surface((28, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(chao, (255, 210, 130, 40), (0, 0, 28, 5))
        m.blit(chao, (x - 14, PE - 2))
        for i, f in enumerate(self.mariposas):                  # mariposas orbitando a lanterna
            a = self.t * (0.05 + i * 0.013) + f
            mx = x + math.cos(a) * (8 + i * 2)
            my = y + 4 + math.sin(a * 1.7) * (5 + i)
            asa = (self.t // 3 + i) % 2
            cor = (230, 220, 200)
            m.set_at((int(mx), int(my)), cor)
            m.set_at((int(mx - 1), int(my - asa)), cor)
            m.set_at((int(mx + 1), int(my - asa)), cor)

    def _desenhar_frente(self, m):
        cam, t = self.cam, self.t
        for v in self.vagalumes:
            x = v[0] - cam
            if -4 < x < LW + 4:
                acende = math.sin(v[2] * 3.1) > 0.2
                if acende:
                    m.blit(self.halo[4], (x - 4, v[1] - 4), special_flags=pygame.BLEND_RGB_ADD)
                    m.set_at((int(x), int(v[1])), (230, 255, 170))
        for jx, alto, f in self.juncos:                         # juncos na frente (paralaxe maior)
            x = jx - cam * 1.3
            if -6 < x < LW + 6:
                curva = math.sin(t * 0.02 + f) * 2
                pygame.draw.line(m, (6, 10, 18), (x, LH), (x + curva, LH - alto), 1)
                if alto > 11:
                    pygame.draw.ellipse(m, (16, 14, 24), (x + curva - 1, LH - alto - 3, 3, 5))

    # --------------------------------------------------------- desenho da tela (alta resolução)
    def draw(self, tela):
        m = self.mundo
        self._desenhar_ceu()
        m.blit(self.ceu, (0, 0))
        self._desenhar_lago(m)
        self._ex("draw_lago", m, self.cam)
        self._desenhar_margem(m)
        self._ex("draw_margem", m, self.cam)
        if self.modo != "luneta":
            self._desenhar_lume(m)
        self._desenhar_frente(m)
        self._ex("draw_frente", m, self.cam)
        pygame.transform.scale(m, (W, H), tela)
        f = self.app.f
        if self.t < 420 and self.modo == "andar" and not self.fala:  # abertura
            a = 255 if self.t < 300 else int(255 * (420 - self.t) / 120)
            cam = pygame.Surface((W, 110), pygame.SRCALPHA)
            titulo_px(cam, "O MIRANTE", (255, 236, 170), W // 2, 14, 4)
            sombra(cam, "um espaço feito pelo Claude · o céu é o seu estudo", f["peq"], (220, 220, 255), (W // 2, 74), centro=True)
            cam.set_alpha(a)
            tela.blit(cam, (0, 40 if not RETRATO else 70))
        if self.modo == "luneta":
            self._desenhar_luneta(tela)
        elif self.modo == "banco":
            self._desenhar_banco(tela)
        else:
            nome, rot = self._perto()
            if nome and not self.fala:
                x = (self.x - self.cam) * ESC
                y = (PE - 30) * ESC
                txt = ("toque: " if RETRATO else "↑ ") + rot
                larg = f["peq"].size(txt)[0] + 24
                r = pygame.Rect(0, 0, larg, 34)
                r.center = (max(larg // 2 + 8, min(W - larg // 2 - 8, x)), y)
                painel(tela, r, raio=10)
                tela.blit(f["peq"].render(txt, True, TINTA), (r.x + 12, r.y + 6))
            if self.dica_t and self.dica_estrela:
                self._desenhar_dica(tela, self.dica_estrela)
            rod = ("toque no chão para andar · toque numa estrela" if RETRATO else
                   "←/→ andar · ↑ interagir · clique numa estrela · Esc volta")
            sombra(tela, rod, f["peq"], (200, 200, 230), (W // 2, H - 24), centro=True)
        self._ex("draw_tela", tela)
        if self.modal:
            self._ex("draw_modal", tela)
        if self.fala:
            self._desenhar_fala(tela)

    def _desenhar_dica(self, tela, s):
        f = self.app.f
        if s.grupo.startswith("Fluxo"):
            linhas = [s.grupo, f"Caixa: {s.nome}", f"{s.c} acertos · {s.e} erros"]
        elif s.grupo == ECG_G:
            linhas = [s.nome, f"{s.c} acertos · {s.e} erros" if s.c + s.e else "ainda não apareceu na Leitura de ECG"]
        else:
            estado = "brilhando: acertou na última vez" if s.ok else "brasa: errou na última vez"
            linhas = [s.grupo, f"{s.c} acerto{'s' if s.c != 1 else ''} · {s.e} erro{'s' if s.e != 1 else ''}", estado]
            if s.vence:
                linhas.append("pulsando: revisão vence hoje")
        larg = max(f["peq"].size(x)[0] for x in linhas) + 28
        r = pygame.Rect(0, 0, larg, 18 + 24 * len(linhas))
        sx = (s.x - self.cam * PAR_CEU) * ESC
        sy = s.y * ESC
        r.midtop = (max(larg // 2 + 8, min(W - larg // 2 - 8, sx)), sy + 18)
        if r.bottom > H - 60:
            r.bottom = sy - 18
        painel(tela, r, raio=10)
        for i, ln in enumerate(linhas):
            tela.blit((f["med"] if i == 0 else f["peq"]).render(ln, True, TINTA if i else (60, 70, 140)),
                      (r.x + 14, r.y + 8 + 24 * i))

    def _desenhar_fala(self, tela):
        f = self.app.f
        mx = 20 if RETRATO else 160
        alt = 230 if RETRATO else 190
        r = pygame.Rect(mx, H - alt - 30, W - 2 * mx, alt)
        painel(tela, r)
        pagina = self.fala[self.fala_i][:int(self.fala_n)]
        y = r.y + 20
        for ln in quebrar(pagina, f["med"], r.w - 48):
            tela.blit(f["med"].render(ln, True, TINTA), (r.x + 24, y))
            y += 30
        fim = self.fala_n >= len(self.fala[self.fala_i])
        if fim and (self.t // 25) % 2:
            marca = "▼" if self.fala_i + 1 < len(self.fala) else "■"
            tela.blit(f["med"].render(marca, True, (150, 120, 90)), (r.right - 36, r.bottom - 38))

    def _desenhar_banco(self, tela):
        f = self.app.f
        total = sum(1 for s in self.todas if s.c + s.e)
        acesas = sum(1 for s in self.todas if s.ok)
        vencem = sum(1 for s in self.todas if s.vence)
        p = self.pensa_t
        a = min(255, p * 4, (660 - p) * 4) if p < 660 else 0
        cam = pygame.Surface((W, 260), pygame.SRCALPHA)
        y = 10
        for ln in quebrar(PENSAMENTOS[self.pensa_i], f["med"], W - (80 if RETRATO else 360)):
            sombra(cam, ln, f["med"], (240, 236, 255), (W // 2, y), centro=True, sombra_cor=(10, 10, 30))
            y += 34
        cam.set_alpha(max(0, a))
        tela.blit(cam, (0, 60 if not RETRATO else 120))
        if total:
            resumo = f"{total} estrelas · {acesas} acesas · {total - acesas} em brasa" + (f" · {vencem} pulsando" if vencem else "")
            if self.hoje:
                resumo += f" · {self.hoje} hoje"
        else:
            resumo = "céu vazio por enquanto: cada questão respondida acende uma estrela"
        sombra(tela, resumo, f["peq"], (200, 200, 240), (W // 2, H - 56), centro=True)
        sombra(tela, "qualquer tecla ou toque para levantar", f["peq"], (150, 150, 190), (W // 2, H - 26), centro=True)

    def _desenhar_luneta(self, tela):
        f = self.app.f
        g = self.grupos[self.gi]
        lista = self.estrelas[g]
        escuro = pygame.Surface((W, H), pygame.SRCALPHA)
        escuro.fill((4, 4, 14, 235))
        tela.blit(escuro, (0, 0))
        raio = int(min(W * 0.4, H * 0.3)) if RETRATO else int(H * 0.3)
        cx, cy = W // 2, int(H * (0.4 if RETRATO else 0.44))
        lente = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        for r in range(raio, 0, -2):
            k = r / raio
            pygame.draw.circle(lente, (int(18 + 20 * (1 - k)), int(16 + 14 * (1 - k)), int(46 + 40 * (1 - k)), 255), (raio, raio), r)
        xs, ys = [s.x for s in lista], [s.y for s in lista]
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        span = max(max(xs) - min(xs), max(ys) - min(ys), 8)
        k = raio * 1.5 / span
        pos = {id(s): (raio + (s.x - mx) * k, raio + (s.y - my) * k) for s in lista}
        for a, b in self.linhas[g]:
            pygame.draw.aaline(lente, (90, 100, 170), pos[id(a)], pos[id(b)])
        for s in lista:
            x, y = pos[id(s)]
            tw = 0.75 + 0.25 * math.sin(self.t * 0.05 + s.fase * 6)
            if s.ok:
                rr = 3 + min(s.c, 4)
                pygame.draw.circle(lente, (60, 60, 90), (x, y), rr + 3)
                pygame.draw.circle(lente, (int(255 * tw), int(240 * tw), 200), (x, y), rr)
            elif s.c + s.e == 0:
                pygame.draw.circle(lente, (70, 66, 110), (x, y), 2)
            else:
                pygame.draw.circle(lente, (150, 70, 60), (x, y), 3)
            if s.vence and math.sin(self.t * 0.06 + s.fase) > 0.85:
                pygame.draw.circle(lente, (110, 130, 220), (x, y), 8, 1)
        mascara = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), (raio, raio), raio)
        lente.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        tela.blit(lente, (cx - raio, cy - raio))
        pygame.draw.circle(tela, (120, 110, 90), (cx, cy), raio + 6, 6)
        pygame.draw.circle(tela, (60, 50, 50), (cx, cy), raio + 12, 4)
        total = sum(1 for s in lista if s.c + s.e)
        acesas = sum(1 for s in lista if s.ok)
        vencem = sum(1 for s in lista if s.vence)
        titulo_px(tela, g.upper() if len(g) < 22 else g.upper()[:22], (255, 236, 170), W // 2, 30 if not RETRATO else 60,
                  3 if len(g) < 16 else 2)
        y = cy + raio + 30
        sombra(tela, f"{total} estrelas · {acesas} acesas · {total - acesas} em brasa"
               + (f" · {vencem} pulsando hoje" if vencem else ""), f["med"], (230, 230, 255), (W // 2, y), centro=True)
        frac = acesas / total if total else 0
        if vencem:
            nota = f"{vencem} pedem revisão hoje. Elas pulsam até você voltar."
        elif frac >= 0.8:
            nota = "Constelação firme. Agora o que mantém é o espaçamento."
        elif frac >= 0.5:
            nota = "Mais acesa que apagada: o desenho já aparece."
        else:
            nota = "Ainda mais brasa que luz. É aqui que estudar rende mais."
        for i, ln in enumerate(quebrar(nota, f["peq"], W - 60)):
            sombra(tela, ln, f["peq"], (190, 190, 230), (W // 2, y + 40 + 26 * i), centro=True)
        n = len(self.grupos)
        for lado, seta in ((-1, "◀"), (1, "▶")):
            sombra(tela, seta, f["med"], (230, 220, 180), (cx + lado * (raio + (34 if RETRATO else 70)), cy), centro=True)
        sombra(tela, f"{self.gi + 1} de {n}", f["peq"], (230, 220, 180), (W // 2, H - 56), centro=True)
        sombra(tela, "toque nas laterais para trocar · no centro para sair" if RETRATO else "←/→ trocar · Enter/Esc sair",
               f["peq"], (150, 150, 190), (W // 2, H - 28), centro=True)


def abrir(app):
    app.push(Mirante(app))
