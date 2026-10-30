"""A coruja da árvore seca — uma pérola de prova por visita.

Numa árvore baixa e sem folhas, à beira do lago, mora uma coruja. A cabeça gira para acompanhar a Lume (os olhos
mudam conforme o lado em que ela está, olham para baixo quando ela chega perto e para a lua quando ela vai longe),
pisca devagar e, de vez em quando, eriça as penas.

Interagir: a coruja recita UMA pérola "na prova" tirada das próprias pílulas dos mundos do jogo (título da pílula,
a pérola e a fonte). Nada é inventado aqui: o texto vem do conteúdo já revisado de cada mundo. A ordem do dia é
embaralhada pela data (determinística) e não repete na mesma sessão do app.
"""
import datetime
import importlib
import math
import random

import pygame

from . import Base
from ..mirante import PE, WW
from ..ui import H, RETRATO, TINTA, W, painel, quebrar

# mundos de onde vêm as pérolas (módulo, lista) — dia_temas usa TEMAS com "materia" em cada tema
_FONTES = ("internato_asma", "internato_dpoc", "internato_vm", "internato_transf", "internato_reum", "reumatologia", "gasometria",
           "ventilacao", "hipercalemia", "insuf_cardiaca", "farmaco_cardio", "farmaco_atb", "dia_temas")

_PEROLAS = None                                  # cache do processo (importar os mundos uma vez só)
_SESSAO = {"dia": None, "i": 0}                  # posição na ordem do dia; vive enquanto o app estiver aberto


def _coletar():
    global _PEROLAS
    if _PEROLAS is not None:
        return _PEROLAS
    out = []
    for nome in _FONTES:
        try:
            mod = importlib.import_module(f"ilha.{nome}")
            lista = getattr(mod, "MODULOS", None) or getattr(mod, "TEMAS", None) or []
            materia = getattr(mod, "MATERIA", "")
            for tema in lista:
                if not isinstance(tema, dict):
                    continue
                cab = f"{tema.get('materia') or materia} · {tema.get('titulo', '')}".strip(" ·")
                for p in tema.get("aula", []) or []:
                    if isinstance(p, dict) and p.get("na_prova"):
                        out.append({"titulo": str(p.get("titulo", "")), "perola": str(p["na_prova"]),
                                    "fonte": str(p.get("fonte", "") or ""), "cab": cab})
        except Exception:
            continue
    _PEROLAS = out
    return out


def _proxima():
    """Próxima pérola da ordem do dia (embaralhada pela data; recomeça só depois de passar por todas)."""
    perolas = _coletar()
    if not perolas:
        return None, False
    hoje = datetime.date.today().toordinal()
    if _SESSAO["dia"] != hoje:
        _SESSAO["dia"], _SESSAO["i"] = hoje, 0
    ordem = list(range(len(perolas)))
    random.Random(hoje * 7919).shuffle(ordem)
    i = _SESSAO["i"]
    _SESSAO["i"] += 1
    return perolas[ordem[i % len(ordem)]], i >= len(ordem) and i % len(ordem) == 0


# ------------------------------------------------------------------ paleta e sprites (desenhados uma vez)

CASCA, CASCA_LUZ, CASCA_ESC = (44, 40, 66), (78, 72, 108), (24, 22, 40)
CONT = (16, 14, 30)                      # contorno
PENA, PENA_ESC, PENA_CLARA = (98, 86, 118), (66, 56, 86), (150, 138, 158)
DISCO = (128, 116, 140)                  # disco facial
OLHO, PUPILA, BICO = (255, 206, 110), (22, 16, 28), (206, 160, 92)


def _arvore():
    """Árvore seca baixa (44×60), tronco torto, galhos nus; a luz da lua bate do lado direito."""
    s = pygame.Surface((44, 60), pygame.SRCALPHA)
    base, topo = 59, 20
    for y in range(base, topo, -1):                     # tronco (afunila e entorta um pouco)
        f = (base - y) / (base - topo)
        cx = 21 + math.sin(f * 2.4) * 2.4
        meia = 3.4 - 2.0 * f
        x0, x1 = int(cx - meia), int(cx + meia)
        s.fill(CASCA, (x0, y, x1 - x0 + 1, 1))
        s.set_at((x1, y), CASCA_LUZ)
        s.set_at((x0, y), CASCA_ESC)
    for dx, l in ((-1, 5), (1, 7)):                     # raízes
        for k in range(l):
            s.set_at((21 + dx * (3 + k), base - (1 if k < 2 else 0)), CASCA if k < l - 1 else CASCA_ESC)

    def galho(x, y, ang, comp, esp):
        for k in range(int(comp)):
            px, py = x + math.cos(ang) * k, y + math.sin(ang) * k
            s.fill(CASCA, (int(px), int(py), esp, 1))
            s.set_at((int(px), int(py) - 1), CASCA_LUZ if math.cos(ang) > -0.3 else CASCA_ESC)
        return x + math.cos(ang) * comp, y + math.sin(ang) * comp

    galho(22, 26, -0.06, 19, 2)                         # galho da coruja (direita, quase horizontal)
    galho(36, 25, -1.0, 6, 1)
    ex, ey = galho(20, 24, -2.25, 13, 2)                # galhos de cima e da esquerda
    galho(ex, ey, -2.9, 6, 1)
    galho(ex, ey, -1.7, 6, 1)
    dx_, dy_ = galho(22, 21, -1.25, 12, 1)
    galho(dx_, dy_, -0.6, 5, 1)
    galho(dx_, dy_, -2.0, 4, 1)
    galho(19, 40, -2.7, 10, 1)
    s.set_at((21, 46), CASCA_ESC)                       # nó no tronco
    s.set_at((22, 47), CASCA_ESC)
    return s


def _corpo(eriçada):
    """Corpo da coruja (13×11): ovo de penas, asas escuras, peito claro com pintas e garras."""
    w, h = 13, 11
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    meia_max = 5.5 if eriçada else 4.5
    for y in range(h - 1):
        f = y / (h - 2)
        meia = meia_max * (0.75 + 0.25 * math.sin(math.pi * min(1, f * 1.15)))
        x0, x1 = round(6 - meia), round(6 + meia)
        s.fill(PENA, (x0, y, x1 - x0 + 1, 1))
        s.set_at((x0, y), CONT)
        s.set_at((x1, y), CONT)
        if y > 0:                                       # asas
            s.set_at((x0 + 1, y), PENA_ESC)
            s.set_at((x1 - 1, y), PENA_ESC)
        if eriçada and y % 2 == 0:                      # penas arrepiadas na borda
            s.set_at((max(0, x0 - 1), y), CONT)
            s.set_at((min(w - 1, x1 + 1), y), CONT)
    for y in range(1, h - 2):                           # peito claro com pintas esparsas
        for x in range(4, 9):
            s.set_at((x, y), PENA_ESC if (x * 3 + y * 5) % 7 == 0 else PENA_CLARA)
    s.fill(CONT, (3, h - 2, 7, 1))
    for x in (4, 5, 7, 8):                              # garras no galho
        s.set_at((x, h - 1), BICO)
    return s


_CABECA = [".O.......O.",
           ".OBOOOOOBO.",
           "OBBBBBBBBBO",
           "OBBBBBBBBBO",
           "OBBBBBBBBBO",
           "OBBBBBBBBBO",
           ".OBBBBBBBO.",
           "..OOOOOOO.."]


def _cabeca(lado, olhar, palpebra):
    """Cabeça 11×8. lado ∈ {-1,0,1}: o rosto desliza 2 px (a cabeça girando) e aparece a nuca do outro lado;
    olhar = (dx, dy) da pupila dentro do olho 2×2; palpebra 0 aberto, 1 meio fechado, 2 fechado."""
    s = pygame.Surface((11, 8), pygame.SRCALPHA)
    cores = {"O": CONT, "B": PENA}
    for y, ln in enumerate(_CABECA):
        for x, ch in enumerate(ln):
            if ch in cores:
                s.set_at((x, y), cores[ch])
    for x0 in (1, 9):                                   # tufos giram junto
        x = max(0, min(10, x0 + lado))
        s.set_at((x0, 0), (0, 0, 0, 0))
        s.set_at((x, 0), CONT)
    d = 2 * lado

    def pinta(x, y, cor):
        if 1 <= x <= 9 and s.get_at((x, y))[:3] == PENA:
            s.set_at((x, y), cor)

    for y in range(2, 7):                               # disco facial (cantos arredondados)
        for x in range(2 + d, 9 + d):
            if (y in (2, 6)) and x in (2 + d, 8 + d):
                continue
            pinta(x, y, DISCO)
    for ox in (3 + d, 6 + d):
        for yy in (3, 4):
            for xx in (ox, ox + 1):
                if palpebra == 2:
                    pinta(xx, yy, CONT if yy == 4 else PENA_ESC)
                elif palpebra == 1 and yy == 3:
                    pinta(xx, yy, PENA_ESC)
                else:
                    pinta(xx, yy, OLHO)
        if palpebra < 2:
            dx, dy = olhar
            dy = 1 if palpebra == 1 else dy
            if 1 <= ox + dx <= 9:
                s.set_at((ox + dx, 3 + dy), PUPILA)
    for yy in (4, 5):
        if 1 <= 5 + d <= 9:
            s.set_at((5 + d, yy), BICO)
    return s


def _brilho_olho():
    s = pygame.Surface((5, 5))
    for y in range(5):
        for x in range(5):
            d = math.hypot(x - 2, y - 2)
            k = max(0.0, 1 - d / 2.6) * 0.35
            s.set_at((x, y), (int(255 * k), int(190 * k), int(100 * k)))
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.wx = WW * 0.271
        self.lugares = [("coruja", self.wx, "ouvir a coruja")]
        self.arvore = _arvore()
        self.corpos = {False: _corpo(False), True: _corpo(True)}
        self.cabecas = {}
        for lado in (-1, 0, 1):
            for dx in (0, 1):
                for dy in (0, 1):
                    for p in (0, 1, 2):
                        self.cabecas[(lado, dx, dy, p)] = _cabeca(lado, (dx, dy), p)
        self.brilho = _brilho_olho()
        self.rng = random.Random()
        self.lado, self.lado_t = 0, 0                 # giro atual e quanto tempo falta para poder girar de novo
        self.pisca_em, self.pisca = self.rng.randint(200, 420), -1
        self.eriça_em, self.eriça = self.rng.randint(600, 1400), -1
        self.perola, self.letras, self.volta = None, 0.0, False
        self.icone = None
        _coletar()

    # --------------------------------------------------------- vida própria
    def update(self):
        t = self.mirante.t
        dx = self.mirante.x - self.wx
        alvo = 0 if abs(dx) < 8 else (1 if dx > 0 else -1)
        if alvo != self.lado:                          # gira um passo de cada vez (esq → frente → dir)
            if self.lado_t <= 0:
                self.lado += 1 if alvo > self.lado else -1
                self.lado_t = 7
        self.lado_t -= 1
        if self.pisca >= 0:
            self.pisca += 1
            if self.pisca > 34:
                self.pisca, self.pisca_em = -1, t + self.rng.randint(240, 520)
        elif t >= self.pisca_em:
            self.pisca = 0
        if self.eriça >= 0:
            self.eriça += 1
            if self.eriça > 50:
                self.eriça, self.eriça_em = -1, t + self.rng.randint(900, 1800)
        elif t >= self.eriça_em:
            self.eriça = 0
        if self.mirante.modal is self and self.perola:
            self.letras = min(len(self.perola["perola"]), self.letras + 1.6)

    def _olhar(self):
        dx = self.mirante.x - self.wx
        if abs(dx) < 8:
            return (0 if dx < 0 else 1), 1             # Lume embaixo: olha para baixo
        if dx > 150:
            return 1, 0                                # longe à direita: olha para a lua
        return (1 if dx > 0 else 0), (1 if abs(dx) < 40 else 0)

    def draw_margem(self, m, cam):
        x = int(self.wx - cam)
        if not -30 < x < m.get_width() + 30:
            return
        m.fill((10, 14, 24), (x - 13, PE - 1, 28, 2))                  # sombra no chão
        m.blit(self.arvore, (x - 21, PE - 59))
        bx, by = x + 9, PE - 33                                        # onde a coruja pousa (sobre o galho)
        eriçada = 0 <= self.eriça < 50
        tremor = 1 if eriçada and self.eriça % 6 < 3 else 0
        corpo = self.corpos[eriçada]
        m.blit(corpo, (bx - corpo.get_width() // 2 + tremor, by - corpo.get_height() + 1))
        p = 0
        if self.pisca >= 0:
            p = 1 if self.pisca < 6 or self.pisca > 28 else 2
        dx, dy = self._olhar()
        cab = self.cabecas[(self.lado, dx, dy, p)]
        hy = by - corpo.get_height() - 6 - (1 if eriçada else 0)
        m.blit(cab, (bx - 5 + tremor, hy))
        if p == 0:                                                     # olhos acesos (a luz quente da peça)
            for ox in (3 + 2 * self.lado, 6 + 2 * self.lado):
                m.blit(self.brilho, (bx - 5 + tremor + ox - 1.5, hy + 3 - 1.5), special_flags=pygame.BLEND_RGB_ADD)

    # --------------------------------------------------------- a pérola
    def interagir(self, nome):
        self.perola, self.volta = _proxima()
        if not self.perola:
            self.mirante._falar(["Hu-hu.", "A coruja hoje só olha. Não encontrei pílulas para ela recitar."])
            return
        self.letras = 0.0
        self.mirante.abrir_modal(self)

    def evento_modal(self, e, inp):
        if inp.foi("voltar"):
            return False
        if inp.foi("ok") or inp.foi("cima") or e.type == pygame.MOUSEBUTTONDOWN:
            if self.perola and self.letras < len(self.perola["perola"]):
                self.letras = len(self.perola["perola"])
                return True
            return False
        return True

    def _icone(self):
        if self.icone is None:
            s = pygame.Surface((13, 19), pygame.SRCALPHA)
            corpo = self.corpos[False]
            s.blit(corpo, (0, 8))
            s.blit(self.cabecas[(0, 1, 1, 0)], (1, 1))
            self.icone = pygame.transform.scale(s, (13 * 5, 19 * 5))
        return self.icone

    def draw_modal(self, tela):
        if not self.perola:
            return
        f = self.mirante.app.f
        mx = 24 if RETRATO else 150
        r = pygame.Rect(mx, 0, W - 2 * mx, 0)
        tx = r.x + 30 + (0 if RETRATO else 90)
        larg = r.right - 30 - tx
        cab = quebrar(self.perola["cab"], f["peq"], larg)
        tit = quebrar(self.perola["titulo"], f["med"], larg)
        per = quebrar(self.perola["perola"], f["med"], larg)
        fon = quebrar(("Fonte: " + self.perola["fonte"]) if self.perola["fonte"] else "", f["peq"], larg)
        alt = 24 + 32 + 26 * len(cab) + 32 * len(tit) + 12 + 30 * len(per) + 12 + 24 * len(fon) + 44
        if RETRATO:
            alt += 100
        r.h = alt
        r.centery = H // 2
        painel(tela, r)
        y = r.y + 22
        if RETRATO:
            ic = self._icone()
            tela.blit(ic, (r.centerx - ic.get_width() // 2, y))
            y += ic.get_height() + 6
        else:
            tela.blit(self._icone(), (r.x + 24, r.y + 26))
        fala = "Hu-hu. Hoje já disse todas; recomeço a lista." if self.volta else "Hu-hu."
        tela.blit(f["q"].render(fala, True, (150, 110, 70)), (tx, y))
        y += 32
        for ln in cab:
            tela.blit(f["peq"].render(ln, True, (130, 110, 120)), (tx, y))
            y += 26
        for ln in tit:
            tela.blit(f["med"].render(ln, True, (60, 70, 140)), (tx, y))
            y += 32
        y += 12
        resta = int(self.letras)
        for ln in per:                                   # a pérola aparece letra a letra
            if resta <= 0:
                break
            parte = ln[:resta]
            tela.blit(f["med"].render(parte, True, TINTA), (tx, y))
            resta -= len(ln) + 1
            y += 30
        if self.letras >= len(self.perola["perola"]):
            y = r.y + alt - 44 - 24 * len(fon)
            for ln in fon:
                tela.blit(f["peq"].render(ln, True, (120, 100, 100)), (tx, y))
                y += 24
            dica = "toque para fechar" if RETRATO else "Enter ou Esc fecha"
            d = f["peq"].render(dica, True, (150, 130, 130))
            tela.blit(d, (r.right - d.get_width() - 24, r.bottom - 36))
