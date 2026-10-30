"""A Carta Celeste — um cavalete na margem com o mapa do céu inteiro.

No mundo é só um cavalete de madeira com um mapinha azul preso nele (umas estrelas piscando no papel). Ao
interagir, a carta toma a tela: todas as constelações do céu do jogador redesenhadas em alta resolução sobre um
papel azul-escuro antigo, com moldura de régua, graticulado curvo, cartela de título, legenda e rosa dos ventos.

Nada é inventado: as posições vêm do próprio céu do Mirante (self.mirante.estrelas/centros/linhas). Como no céu
os grupos se sobrepõem, a carta afasta os grupos uns dos outros (relaxação simples, uma vez ao abrir), mantendo a
forma interna de cada constelação e a ordem aproximada no céu, para que cada nome caiba embaixo do seu desenho.

Estrelas: claras = acertou na última vez; brasa = errou na última vez; anel = a revisão vence hoje; círculo vazio
= ritmo de ECG ainda não visto. ←/→ destacam um grupo por vez (rodapé com acertos, erros e quantas vencem hoje);
Enter/Esc fecham; clique num grupo destaca, clique no papel vazio fecha.
"""
import math
import random
import time

import pygame

from . import Base
from .. import art
from ..mirante import LW, PE, WW, MADEIRA, MADEIRA_ESC
from ..ui import H, RETRATO, W, cortar, fonte, quebrar

# tintas da carta
PAPEL_A, PAPEL_B = (16, 24, 52), (28, 40, 78)
OURO = (198, 168, 104)
OURO_ESC = (120, 98, 62)
TINTA_CLARA = (232, 222, 190)
TINTA_FLUXO = (130, 196, 186)
GRADE = (60, 78, 128)
ESTRELA = (252, 246, 222)
BRASA = (238, 112, 58)
ANEL = (150, 182, 255)
APAGADA = (96, 104, 150)

# o cavalete no mundo (o mapinha é desenhado em ASCII, as pernas com linhas)
QUADRO = [
    "gggggggggggggggg",
    "gBBBBBBBBBBBBBBg",
    "gBBwBBBBBBBbBBBg",
    "gBBBlBBBBBwBBBBg",
    "gBbBBwlllBBBBBBg",
    "gBBBBBBBBlBoBBBg",
    "gBBoBBBBBBwBBBBg",
    "gBBBBBBbBBBBBBwg",
    "gBwBBBBBBBBBBBBg",
    "gggggggggggggggg",
]
PAL_QUADRO = {"g": (150, 124, 76), "B": (24, 34, 72), "b": (40, 54, 100), "w": (230, 232, 250),
              "o": (226, 120, 70), "l": (86, 106, 168)}
PISCAM = [(3, 2), (10, 3), (5, 4), (10, 6), (14, 7), (2, 8)]      # pixels-estrela do mapinha (no QUADRO)


def _plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def _pct(c, e):
    return f"{round(100 * c / (c + e))}%" if c + e else "—"


def _brilho_alfa(raio, cor, forca):
    """Brilho redondo com alfa (para pousar sobre camadas transparentes)."""
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1), pygame.SRCALPHA)
    for r in range(raio, 0, -1):
        k = (1 - r / raio) ** 1.8 * forca
        pygame.draw.circle(s, (*cor, min(255, int(255 * k))), (raio, raio), r)
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.wx = WW * 0.726
        self.lugares = [("carta_celeste", self.wx, "abrir a carta celeste")]
        self.spr = self._cavalete()
        self.carta = None                     # montada ao abrir (o céu pode ter mudado)
        self.sel = -1                         # -1 = visão geral; senão índice em self.ordem
        self._g_ok = _brilho_alfa(7, (200, 210, 255), 0.55)       # brilhos das estrelas (a legenda também usa)
        self._g_ok_forte = _brilho_alfa(11, (255, 236, 190), 0.5)
        self._g_brasa = _brilho_alfa(7, (255, 110, 50), 0.6)

    # ------------------------------------------------------------------ no mundo
    def _cavalete(self):
        s = pygame.Surface((18, 28), pygame.SRCALPHA)
        pygame.draw.line(s, MADEIRA_ESC, (9, 3), (11, 27))                    # perna de trás
        pygame.draw.line(s, MADEIRA, (6, 11), (2, 27))                        # pernas da frente
        pygame.draw.line(s, MADEIRA, (12, 11), (16, 27))
        pygame.draw.line(s, MADEIRA_ESC, (4, 21), (14, 21))                   # travessa
        pygame.draw.rect(s, MADEIRA_ESC, (8, 0, 3, 2))                        # cabeça
        s.blit(art.spr(QUADRO, PAL_QUADRO), (1, 1))
        pygame.draw.rect(s, MADEIRA, (1, 11, 16, 1))                          # aparador
        pygame.draw.rect(s, MADEIRA_ESC, (1, 12, 16, 1))
        return s

    def draw_margem(self, m, cam):
        x = int(self.wx - cam) - 9
        if x < -20 or x > LW + 4:
            return
        y = PE - 27
        m.blit(self.spr, (x, y))
        t = self.mirante.t
        for k, (px, py) in enumerate(PISCAM):                                 # o mapinha cintila
            v = 0.5 + 0.5 * math.sin(t * 0.05 + k * 1.7)
            if k in (3, 5):
                continue
            c = int(150 + 105 * v)
            m.set_at((x + 1 + px, y + 1 + py), (c, c, min(255, c + 20)))

    # ------------------------------------------------------------------ abrir
    def interagir(self, nome):
        self.sel = -1
        self.carta = self._montar()
        self.mirante.abrir_modal(self)
        self._som("menu")

    def _som(self, nome):
        try:
            au = self.mirante.app.audio
            if au.ok and not au.mudo:
                au.tocar(nome)
        except Exception:
            pass

    # ------------------------------------------------------------------ montagem (uma vez por abertura)
    def _montar(self):
        mir = self.mirante
        c = {}
        c["f_tit"] = fonte(30 if not RETRATO else 26, True)
        c["f_sub"] = fonte(15)
        c["f_sub"].set_italic(True)
        c["f_nome"] = fonte(15, True)
        c["f_nome"].set_italic(True)
        c["f_info"] = fonte(13)
        c["f_leg"] = fonte(13)
        c["f_rod"] = fonte(17)
        c["f_rod_b"] = fonte(21, True)
        # moldura, área do mapa e rodapé
        rod_h = 112 if not RETRATO else 190
        topo = 22 if not RETRATO else 70
        c["moldura"] = moldura = pygame.Rect(22 if not RETRATO else 12, topo, W - (44 if not RETRATO else 24), H - topo - rod_h - 14)
        c["rodape"] = pygame.Rect(moldura.x, moldura.bottom + 10, moldura.w, H - moldura.bottom - 22)
        interno = moldura.inflate(-36, -36)
        c["interno"] = interno
        c["cartela_h"] = 64
        c["obst_h"] = 92 if not RETRATO else 96                    # faixa de baixo: legenda e rosa
        area = pygame.Rect(interno.x + 10, interno.y + c["cartela_h"] + 8, interno.w - 20,
                           interno.h - c["cartela_h"] - 8 - c["obst_h"])
        c["area"] = area
        c["fundo"] = self._fundo(c)
        # grupos
        grupos = [g for g in mir.estrelas if mir.estrelas[g]]
        c["grupos"] = {}
        if grupos:
            self._projetar(c, grupos)
        ordem = sorted(c["grupos"], key=lambda g: c["grupos"][g]["pos"][0])
        c["ordem"] = ordem
        clara = c["fundo"].copy()
        escura = c["fundo"].copy()
        for g in ordem:
            G = c["grupos"][g]
            clara.blit(G["camada"], G["rect"])
        if ordem:
            for g in ordem:
                G = c["grupos"][g]
                fraca = G["camada"].copy()                 # cópia: set_alpha(None) apagaria o alfa por pixel
                fraca.set_alpha(70)
                escura.blit(fraca, G["rect"])
        else:
            self._vazio(clara, c)
        c["clara"], c["escura"] = clara, escura
        c["rod_cache"] = {}
        return c

    def _fundo(self, c):
        """Papel azul-escuro manchado, graticulado curvo, moldura de régua, cantos, cartela, legenda e rosa."""
        s = pygame.Surface((W, H))
        s.fill((6, 8, 20))
        mol = c["moldura"]
        rng = random.Random(7261)
        # papel: manchas em baixa resolução, depois suavizadas
        pw, ph = max(8, mol.w // 16), max(8, mol.h // 16)
        baixo = pygame.Surface((pw, ph))
        for y in range(ph):
            for x in range(pw):
                dx, dy = (x - pw / 2) / (pw / 2), (y - ph / 2) / (ph / 2)
                vinheta = max(0.0, 1 - 0.45 * (dx * dx + dy * dy))
                k = vinheta * (0.75 + 0.25 * rng.random())
                baixo.set_at((x, y), tuple(int(a + (b - a) * k) for a, b in zip(PAPEL_A, PAPEL_B)))
        papel = pygame.transform.smoothscale(baixo, mol.size)
        for _ in range(mol.w * mol.h // 900):                                  # fibras e pontinhos do papel
            x, y = rng.randrange(mol.w), rng.randrange(mol.h)
            v = rng.choice((-8, -5, 6, 9))
            cor = papel.get_at((x, y))
            papel.set_at((x, y), tuple(max(0, min(255, cor[i] + v)) for i in range(3)))
        for _ in range(5):                                                     # manchas de tempo
            r = rng.randint(30, 90)
            mancha = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(mancha, (0, 0, 10, 26), mancha.get_rect())
            papel.blit(mancha, (rng.randrange(mol.w) - r, rng.randrange(mol.h) - r))
        s.blit(papel, mol)
        # via láctea: uma faixa leve atravessando a carta
        faixa = pygame.Surface(mol.size, pygame.SRCALPHA)
        for i in range(60):
            f = i / 59
            x = mol.w * (0.05 + 0.9 * f)
            y = mol.h * (0.78 - 0.5 * f) + math.sin(f * 7) * 12
            r = int(mol.h * 0.09 * (0.6 + 0.4 * math.sin(f * 3.1)))
            pygame.draw.circle(faixa, (120, 140, 210, 7), (x, y), max(6, r))
        s.blit(faixa, mol)
        # graticulado: meridianos em leque e paralelos curvos
        it = c["interno"]
        grade = pygame.Surface(mol.size, pygame.SRCALPHA)
        cx = it.centerx - mol.x
        n_mer = 12 if not RETRATO else 7
        for k in range(n_mer + 1):
            xb = (it.x - mol.x) + it.w * k / n_mer
            xt = cx + (xb - cx) * 0.86
            pygame.draw.line(grade, (*GRADE, 70), (xt, it.y - mol.y), (xb, it.bottom - mol.y))
        n_par = 6 if not RETRATO else 10
        for k in range(1, n_par):
            y0 = (it.y - mol.y) + it.h * k / n_par
            pts = []
            for j in range(41):
                fx = j / 40
                x = (it.x - mol.x) + it.w * fx
                pts.append((x, y0 - 18 * (1 - (2 * fx - 1) ** 2)))
            pygame.draw.lines(grade, (*GRADE, 60), False, pts)
        s.blit(grade, mol)
        # poeira de estrelinhas de fundo (não são do save: só textura, bem apagadas)
        for _ in range(mol.w * mol.h // 2600):
            x, y = rng.randrange(it.x, it.right), rng.randrange(it.y, it.bottom)
            v = rng.randint(50, 90)
            s.set_at((x, y), (v, v + 6, v + 30))
        # moldura de régua: linha grossa, faixa com segmentos alternados, linha fina
        pygame.draw.rect(s, OURO, mol, 3)
        faixa_r = mol.inflate(-12, -12)
        pygame.draw.rect(s, OURO_ESC, faixa_r, 1)
        pygame.draw.rect(s, OURO, it.inflate(4, 4), 1)
        passo = 24
        for x in range(faixa_r.x + 8, faixa_r.right - 8, passo):
            if (x // passo) % 2 == 0:
                pygame.draw.rect(s, OURO_ESC, (x, faixa_r.y + 2, passo // 2, 5))
                pygame.draw.rect(s, OURO_ESC, (x, faixa_r.bottom - 7, passo // 2, 5))
        for y in range(faixa_r.y + 8, faixa_r.bottom - 8, passo):
            if (y // passo) % 2 == 0:
                pygame.draw.rect(s, OURO_ESC, (faixa_r.x + 2, y, 5, passo // 2))
                pygame.draw.rect(s, OURO_ESC, (faixa_r.right - 7, y, 5, passo // 2))
        for px, py in (mol.topleft, (mol.right - 1, mol.y), (mol.x, mol.bottom - 1), (mol.right - 1, mol.bottom - 1)):
            self._losango(s, px + (12 if px == mol.x else -12), py + (12 if py == mol.y else -12), 9)
        self._cartela(s, c)
        self._legenda(s, c)
        r = 34 if not RETRATO else 32
        self._rosa(s, it.right - r - 14, it.bottom - r - 12, r, c)
        return s

    def _losango(self, s, x, y, r):
        pygame.draw.polygon(s, (16, 22, 46), [(x, y - r), (x + r, y), (x, y + r), (x - r, y)])
        pygame.draw.polygon(s, OURO, [(x, y - r), (x + r, y), (x, y + r), (x - r, y)], 1)
        pygame.draw.circle(s, OURO, (x, y), 2)

    def _cartela(self, s, c):
        it = c["interno"]
        tit = c["f_tit"].render("CARTA CELESTE DO MIRANTE", True, OURO)
        meses = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
                 "outubro", "novembro", "dezembro")
        lt = time.localtime()
        sub = c["f_sub"].render(f"o céu do seu estudo, levantado em {lt.tm_mday} de {meses[lt.tm_mon - 1]} de {lt.tm_year}",
                                True, TINTA_CLARA)
        larg = max(tit.get_width(), sub.get_width()) + 70
        r = pygame.Rect(0, 0, min(larg, it.w - 20), c["cartela_h"] - 4)
        r.midtop = (it.centerx, it.y + 2)
        pygame.draw.rect(s, (14, 20, 44), r, border_radius=6)
        pygame.draw.rect(s, OURO, r, 2, border_radius=6)
        pygame.draw.rect(s, OURO_ESC, r.inflate(-8, -8), 1, border_radius=4)
        for lado in (-1, 1):                                                  # volutas simples
            x = r.centerx + lado * (r.w // 2 + 10)
            pygame.draw.circle(s, OURO, (x, r.centery), 6, 1)
            pygame.draw.line(s, OURO_ESC, (x + lado * 8, r.centery), (x + lado * 40, r.centery))
        s.blit(tit, tit.get_rect(midtop=(r.centerx, r.y + 7)))
        s.blit(sub, sub.get_rect(midbottom=(r.centerx, r.bottom - 7)))

    def _legenda(self, s, c):
        it = c["interno"]
        f = c["f_leg"]
        itens = [("ok", "acertou na última vez"), ("brasa", "errou na última vez"),
                 ("anel", "revisão vence hoje"), ("fluxo", "fluxograma jogado")]
        larg = max(f.size(t)[0] for _, t in itens) + 44
        r = pygame.Rect(it.x + 8, it.bottom - 8 - (len(itens) * 18 + 30), larg, len(itens) * 18 + 30)
        pygame.draw.rect(s, (12, 18, 40), r, border_radius=4)
        pygame.draw.rect(s, OURO_ESC, r, 1, border_radius=4)
        s.blit(f.render("LEGENDA", True, OURO), (r.x + 10, r.y + 6))
        for i, (k, txt) in enumerate(itens):
            y = r.y + 30 + 18 * i
            x = r.x + 18
            if k == "ok":
                s.blit(self._g_ok, (x - self._g_ok.get_width() // 2, y - self._g_ok.get_height() // 2))
                pygame.draw.circle(s, ESTRELA, (x, y), 2)
            elif k == "brasa":
                s.blit(self._g_brasa, (x - self._g_brasa.get_width() // 2, y - self._g_brasa.get_height() // 2))
                pygame.draw.circle(s, BRASA, (x, y), 2)
            elif k == "anel":
                pygame.draw.circle(s, ESTRELA, (x, y), 2)
                pygame.draw.circle(s, ANEL, (x, y), 6, 1)
            else:
                pygame.draw.line(s, TINTA_FLUXO, (x - 7, y), (x + 7, y), 2)
            s.blit(f.render(txt, True, TINTA_CLARA), (x + 14, y - 8))

    def _rosa(self, s, cx, cy, r, c):
        """Rosa dos ventos de oito pontas, com o N em cima."""
        pygame.draw.circle(s, OURO_ESC, (cx, cy), r + 3, 1)
        pygame.draw.circle(s, OURO_ESC, (cx, cy), int(r * 0.45), 1)
        for k in range(8):
            a = -math.pi / 2 + k * math.pi / 4
            comp = r if k % 2 == 0 else r * 0.58
            ld = r * 0.13
            ponta = (cx + math.cos(a) * comp, cy + math.sin(a) * comp)
            e = (cx + math.cos(a - math.pi / 2) * ld, cy + math.sin(a - math.pi / 2) * ld)
            d = (cx + math.cos(a + math.pi / 2) * ld, cy + math.sin(a + math.pi / 2) * ld)
            pygame.draw.polygon(s, OURO if k % 2 == 0 else OURO_ESC, [ponta, e, (cx, cy)])
            pygame.draw.polygon(s, (60, 50, 34) if k % 2 == 0 else (40, 36, 30), [ponta, d, (cx, cy)])
        pygame.draw.circle(s, OURO, (cx, cy), 2)
        n = c["f_info"].render("N", True, OURO)
        s.blit(n, n.get_rect(midbottom=(cx, cy - r - 4)))

    # ------------------------------------------------------------------ projeção das constelações
    def _projetar(self, c, grupos):
        mir = self.mirante
        area = c["area"]
        todas = [s for g in grupos for s in mir.estrelas[g]]
        x0, x1 = min(s.x for s in todas), max(s.x for s in todas)
        y0, y1 = min(s.y for s in todas), max(s.y for s in todas)
        sx, sy = max(x1 - x0, 20), max(y1 - y0, 10)
        kx = area.w / sx
        ky = min(area.h / sy, kx * 3.2)
        k_in = max(2.4, min(4.5, kx * 1.25))          # escala interna (forma de cada constelação)
        ox = area.x + (area.w - sx * kx) / 2
        oy = area.y + (area.h - sy * ky) / 2
        info = {}
        for g in grupos:
            lista = mir.estrelas[g]
            mx = sum(s.x for s in lista) / len(lista)
            my = sum(s.y for s in lista) / len(lista)
            rel = [((s.x - mx) * k_in, (s.y - my) * k_in * 1.55) for s in lista]
            bx0 = min(p[0] for p in rel) - 10
            bx1 = max(p[0] for p in rel) + 10
            by0 = min(p[1] for p in rel) - 10
            by1 = max(p[1] for p in rel) + 10
            fluxo = g.startswith("Fluxo · ")
            nome = g[len("Fluxo · "):] if fluxo else g
            nome = cortar(nome, c["f_nome"], 170)
            vistas = [s for s in lista if s.c + s.e]
            ac, er = sum(s.c for s in lista), sum(s.e for s in lista)
            info_txt = f"{_plural(len(vistas), 'estrela', 'estrelas')} · {_pct(ac, er)}"
            lw = max(c["f_nome"].size(nome)[0], c["f_info"].size(info_txt)[0]) + 6
            lh = 34
            larg = max(bx1 - bx0, lw)
            alt = (by1 - by0) + lh
            info[g] = {"lista": lista, "rel": rel, "bbox": (bx0, bx1, by0, by1), "nome": nome, "info": info_txt,
                       "fluxo": fluxo, "lw": lw, "lh": lh, "w": larg, "h": alt,
                       "orig": [ox + (mx - x0) * kx, oy + (my - y0) * ky], "ac": ac, "er": er}
            # pos = centro do desenho das estrelas; a pegada inclui o rótulo embaixo
            info[g]["pos"] = list(info[g]["orig"])
        self._relaxar(info, area)
        for g, G in info.items():
            self._camada(g, G, c)
        c["grupos"] = info

    def _pegada(self, G):
        """Retângulo (x0, y0, x1, y1) ocupado pelo grupo: estrelas + rótulo."""
        bx0, bx1, by0, by1 = G["bbox"]
        px, py = G["pos"]
        meia = G["w"] / 2
        cx = px + (bx0 + bx1) / 2
        return cx - meia, py + by0, cx + meia, py + by1 + G["lh"]

    def _relaxar(self, info, area):
        """Afasta grupos sobrepostos (eixo de menor penetração) e puxa de leve de volta ao lugar no céu."""
        gs = sorted(info, key=lambda g: -len(info[g]["lista"]))
        for passo in range(260):
            mexeu = False
            peg = {g: self._pegada(info[g]) for g in gs}
            for i, a in enumerate(gs):
                A = peg[a]
                for b in gs[i + 1:]:
                    B = peg[b]
                    px = min(A[2], B[2]) - max(A[0], B[0]) + 6
                    py = min(A[3], B[3]) - max(A[1], B[1]) + 6
                    if px <= 0 or py <= 0:
                        continue
                    mexeu = True
                    pa, pb = info[a]["pos"], info[b]["pos"]
                    if px < py * 1.6:                                            # empurra na horizontal
                        d = 1 if (A[0] + A[2]) <= (B[0] + B[2]) else -1
                        pa[0] -= d * px * 0.5
                        pb[0] += d * px * 0.5
                    else:
                        d = 1 if (A[1] + A[3]) <= (B[1] + B[3]) else -1
                        if (A[1] + A[3]) == (B[1] + B[3]):
                            d = 1 if a < b else -1
                        pa[1] -= d * py * 0.5
                        pb[1] += d * py * 0.5
                    A = self._pegada(info[a])
                    peg[a], peg[b] = A, self._pegada(info[b])
            for g in gs:                                                         # mola de volta + caber na área
                G = info[g]
                G["pos"][0] += (G["orig"][0] - G["pos"][0]) * 0.015
                G["pos"][1] += (G["orig"][1] - G["pos"][1]) * 0.015
                x0, y0, x1, y1 = self._pegada(G)
                if x0 < area.x:
                    G["pos"][0] += area.x - x0
                elif x1 > area.right:
                    G["pos"][0] -= x1 - area.right
                x0, y0, x1, y1 = self._pegada(G)
                if y0 < area.y:
                    G["pos"][1] += area.y - y0
                elif y1 > area.bottom:
                    G["pos"][1] -= y1 - area.bottom
            if not mexeu and passo > 10:
                break

    def _camada(self, g, G, c):
        """Desenha um grupo (linhas, estrelas, rótulo) numa camada transparente própria."""
        x0, y0, x1, y1 = self._pegada(G)
        x0, y0 = int(x0) - 4, int(y0) - 4
        rect = pygame.Rect(x0, y0, int(x1 - x0) + 8, int(y1 - y0) + 8)
        cam = pygame.Surface(rect.size, pygame.SRCALPHA)
        px, py = G["pos"]
        pts = {id(s): (px + dx - x0, py + dy - y0) for s, (dx, dy) in zip(G["lista"], G["rel"])}
        G["pts_tela"] = {k: (v[0] + x0, v[1] + y0) for k, v in pts.items()}
        cor_linha = (120, 190, 180, 150) if G["fluxo"] else (150, 170, 230, 140)
        for a, b in self.mirante.linhas.get(g, ()):
            if id(a) in pts and id(b) in pts:
                ca = cor_linha if (a.ok and b.ok) else (cor_linha[0] // 2 + 40, cor_linha[1] // 2, cor_linha[2] // 2 + 30, 110)
                pygame.draw.line(cam, ca, pts[id(a)], pts[id(b)], 1)
        for s in G["lista"]:                                                     # brilhos primeiro
            x, y = pts[id(s)]
            if s.ok:
                gl = self._g_ok_forte if s.c >= 3 else self._g_ok
                cam.blit(gl, (x - gl.get_width() // 2, y - gl.get_height() // 2))
            elif s.c + s.e:
                cam.blit(self._g_brasa, (x - 7, y - 7))
        for s in G["lista"]:
            x, y = pts[id(s)]
            if s.ok:
                r = 1.5 + min(s.c, 4) * 0.45
                pygame.draw.circle(cam, ESTRELA, (x, y), r)
                if s.c >= 3:                                                     # muito acertada: cruz fina
                    pygame.draw.line(cam, (255, 246, 220, 170), (x - 6, y), (x + 6, y))
                    pygame.draw.line(cam, (255, 246, 220, 170), (x, y - 6), (x, y + 6))
            elif s.c + s.e == 0:
                pygame.draw.circle(cam, APAGADA, (x, y), 3, 1)
            else:
                pygame.draw.circle(cam, BRASA, (x, y), 2)
                cam.set_at((int(x), int(y)), (255, 200, 140))
            if s.vence:
                pygame.draw.circle(cam, ANEL, (x, y), 6, 1)
        # rótulo embaixo do desenho
        bx0, bx1, by0, by1 = G["bbox"]
        cx = px + (bx0 + bx1) / 2 - x0
        ly = py + by1 - y0
        cor_nome = TINTA_FLUXO if G["fluxo"] else TINTA_CLARA
        tn = c["f_nome"].render(G["nome"], True, cor_nome)
        ti = c["f_info"].render(G["info"], True, (170, 176, 210))
        cam.blit(tn, tn.get_rect(midtop=(cx, ly)))
        cam.blit(ti, ti.get_rect(midtop=(cx, ly + 17)))
        G["rect"] = rect
        G["camada"] = cam
        G["estrelas_rect"] = pygame.Rect(int(px + bx0), int(py + by0), int(bx1 - bx0), int(by1 - by0))

    def _vazio(self, s, c):
        area = c["area"]
        f = c["f_rod"]
        linhas = ["Esta carta ainda está em branco."]
        linhas += quebrar("Cada questão que você responder vira uma estrela neste papel, no canto do céu do "
                          "mundo de onde ela veio. Não há pressa: o mapa espera.", f, min(620, area.w - 40))
        y = area.centery - 14 * len(linhas)
        for i, ln in enumerate(linhas):
            t = (c["f_rod_b"] if i == 0 else c["f_sub"]).render(ln, True, OURO if i == 0 else TINTA_CLARA)
            s.blit(t, t.get_rect(midtop=(area.centerx, y)))
            y += 34 if i == 0 else 24

    # ------------------------------------------------------------------ modal
    def evento_modal(self, e, inp):
        c = self.carta
        if c is None or inp.foi("voltar") or inp.foi("ok"):
            return False
        n = len(c["ordem"])
        if inp.foi("esq") or inp.foi("cima"):
            if n:
                self.sel = (self.sel + 1) % (n + 1) - 1 if False else (n - 1 if self.sel < 0 else self.sel - 1)
                self._som("menu")
            return True
        if inp.foi("dir") or inp.foi("baixo"):
            if n:
                self.sel = 0 if self.sel < 0 else (self.sel + 1 if self.sel + 1 < n else -1)
                self._som("menu")
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            pos = e.pos
            rod = c["rodape"]
            if rod.collidepoint(pos):                                         # setas do rodapé
                if n:
                    if pos[0] < rod.x + rod.w * 0.25:
                        self.sel = n - 1 if self.sel < 0 else self.sel - 1
                    elif pos[0] > rod.right - rod.w * 0.25:
                        self.sel = 0 if self.sel < 0 else (self.sel + 1 if self.sel + 1 < n else -1)
                    else:
                        return False
                    self._som("menu")
                    return True
                return False
            for i, g in enumerate(c["ordem"]):
                if c["grupos"][g]["rect"].collidepoint(pos):
                    self.sel = -1 if self.sel == i else i
                    self._som("menu")
                    return True
            return False
        return True

    def draw_modal(self, tela):
        c = self.carta
        if c is None:
            return
        if self.sel < 0 or not c["ordem"]:
            tela.blit(c["clara"], (0, 0))
        else:
            self.sel = min(self.sel, len(c["ordem"]) - 1)
            g = c["ordem"][self.sel]
            G = c["grupos"][g]
            tela.blit(c["escura"], (0, 0))
            er = G["estrelas_rect"].inflate(18, 12)
            pygame.draw.ellipse(tela, OURO_ESC, er, 1)                          # o grupo cercado a lápis
            tela.blit(G["camada"], G["rect"])
            t = self.mirante.t
            fase = (t % 90) / 90
            for s in G["lista"]:                                               # anéis das que vencem pulsam
                if s.vence:
                    x, y = G["pts_tela"][id(s)]
                    r = 6 + int(5 * fase)
                    v = int(255 * (1 - fase))
                    pygame.draw.circle(tela, (v * 150 // 255, v * 182 // 255, v), (x, y), r, 1)
        self._rodape(tela, c)

    def _rodape(self, tela, c):
        chave = self.sel
        if chave not in c["rod_cache"]:
            c["rod_cache"][chave] = self._montar_rodape(c)
        tela.blit(c["rod_cache"][chave], c["rodape"])

    def _montar_rodape(self, c):
        r = c["rodape"]
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (14, 20, 44), s.get_rect(), border_radius=8)
        pygame.draw.rect(s, OURO_ESC, s.get_rect(), 2, border_radius=8)
        fb, f, fp = c["f_rod_b"], c["f_rod"], c["f_info"]
        n = len(c["ordem"])
        larg = r.w - (150 if not RETRATO else 60)
        x = 24 if not RETRATO else 18
        if not n:
            l1 = "Céu vazio por enquanto"
            l2 = ["Responda uma questão em qualquer mundo e volte aqui: a primeira estrela já entra na carta."]
        elif self.sel < 0:
            todas = [st for G in c["grupos"].values() for st in G["lista"]]
            vistas = sum(1 for st in todas if st.c + st.e)
            ac, er = sum(st.c for st in todas), sum(st.e for st in todas)
            claras = sum(1 for st in todas if st.ok)
            vencem = sum(1 for st in todas if st.vence)
            l1 = f"A carta inteira: {_plural(vistas, 'estrela', 'estrelas')} em {_plural(n, 'constelação', 'constelações')}"
            l2 = [f"{_plural(ac, 'acerto', 'acertos')} e {_plural(er, 'erro', 'erros')} ao todo ({_pct(ac, er)} de acerto) · "
                  f"{claras} claras, {vistas - claras} em brasa · "
                  + (f"{_plural(vencem, 'vence', 'vencem')} hoje" if vencem else "nenhuma revisão vence hoje")]
        else:
            g = c["ordem"][self.sel]
            G = c["grupos"][g]
            lista = G["lista"]
            vistas = [st for st in lista if st.c + st.e]
            claras = sum(1 for st in lista if st.ok)
            vencem = sum(1 for st in lista if st.vence)
            l1 = cortar(g, fb, larg)
            partes = [f"Acertos: {G['ac']} · Erros: {G['er']} · {_pct(G['ac'], G['er'])} de acerto",
                      f"{_plural(len(vistas), 'estrela', 'estrelas')}: {claras} clara{'s' if claras != 1 else ''}, "
                      f"{len(vistas) - claras} em brasa"]
            if g.startswith("Fluxo · "):
                partes.append("cada estrela é uma caixa do fluxograma")
            else:
                partes.append(f"vence{'m' if vencem != 1 else ''} hoje: {vencem}")
            l2 = [" · ".join(partes)]
        y = 12
        s.blit(fb.render(l1, True, OURO), (x, y))
        y += 32
        for bloco in l2:
            for ln in quebrar(bloco, f, larg):
                s.blit(f.render(ln, True, TINTA_CLARA), (x, y))
                y += 24
        if n:
            idx = "visão geral" if self.sel < 0 else f"{self.sel + 1} de {n}"
            dica = ("toque nas pontas para trocar · no meio para fechar" if RETRATO else
                    "←/→ constelação · clique num grupo · Enter/Esc fecha")
            t1 = fp.render(idx, True, (170, 176, 210))
            t2 = fp.render(dica, True, (130, 136, 170))
            s.blit(t1, t1.get_rect(topright=(r.w - 16, 14)))
            s.blit(t2, t2.get_rect(bottomright=(r.w - 16, r.h - 10)))
            for lado, seta in ((-1, "◀"), (1, "▶")):
                ts = fb.render(seta, True, OURO_ESC)
                if RETRATO:
                    s.blit(ts, ts.get_rect(midbottom=((12 + ts.get_width() // 2) if lado < 0 else r.w - 12 - ts.get_width() // 2,
                                                       r.h - 30)))
        else:
            t2 = fp.render("Enter/Esc fecha", True, (130, 136, 170))
            s.blit(t2, t2.get_rect(bottomright=(r.w - 16, r.h - 10)))
        return s
