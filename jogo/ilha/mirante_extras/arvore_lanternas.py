"""A árvore das lanternas — um calendário pendurado nos galhos.

Uma árvore de copa escura na margem do lago. Cada dia dos últimos 30 em que alguma questão foi respondida
acende uma lanterna de papel num fio. A posição de cada lanterna depende só da data (o mesmo dia fica sempre
no mesmo galho); as antigas vão ficando tênues, e a de hoje, se houver, brilha mais e balança mais na brisa.

Ao interagir, abre um calendário dos 30 dias com o número de questões de cada dia, o total do mês e a maior
sequência de dias seguidos. Limite honesto dos dados: o save guarda só a ÚLTIMA vez que cada questão foi
respondida ("ult"), então uma questão refeita conta apenas no dia mais recente.
"""
import math
import time
from datetime import date, datetime, timedelta

import pygame

from . import Base
from ..mirante import GY, PE, WW
from ..ui import RETRATO, TINTA, W, H, painel, sombra

DIAS = 30
DIAS_SEM = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

# cores quentes das lanternas: âmbar, rosa, laranja, coral, dourado, pêssego
CORES = [(255, 178, 74), (255, 126, 156), (255, 138, 58), (248, 104, 86), (255, 212, 112), (255, 160, 120)]

COPA, COPA_SOMBRA, COPA_ARO = (16, 22, 42), (10, 14, 30), (38, 50, 86)
TRONCO, TRONCO_ESC = (34, 26, 38), (20, 16, 26)
FIO = (64, 54, 70)


def _h(s):
    """Hash estável (não depende do PYTHONHASHSEED)."""
    v = 2166136261
    for ch in s.encode():
        v = ((v ^ ch) * 16777619) & 0xFFFFFFFF
    return v


def _mul(cor, k):
    return tuple(max(0, min(255, int(c * k))) for c in cor)


def _brilho(raio, cor, forca):
    """Halo radial pequeno (para somar com BLEND_RGB_ADD)."""
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1))
    for r in range(raio, 0, -1):
        k = forca * (1 - r / (raio + 1)) ** 1.6
        pygame.draw.circle(s, _mul(cor, k), (raio, raio), r)
    return s


def _contar_dias(save_d):
    """{date: nº de questões cuja última resposta caiu nesse dia}, só nos últimos DIAS dias."""
    hoje = date.today()
    inicio = hoje - timedelta(days=DIAS - 1)
    cont = {}
    for st in (save_d.get("q") or {}).values():
        try:
            ult = float(st.get("ult") or 0)
            if ult <= 0:
                continue
            if ult > 1e11:                      # por garantia, caso algum registro venha em milissegundos
                ult /= 1000.0
            d = datetime.fromtimestamp(ult).date()
        except (TypeError, ValueError, OSError, OverflowError, AttributeError):
            continue
        if inicio <= d <= hoje:
            cont[d] = cont.get(d, 0) + 1
    return cont


def _sequencias(cont, hoje):
    """(maior sequência de dias seguidos na janela, sequência atual terminando hoje ou ontem)."""
    maior = atual = 0
    for i in range(DIAS - 1, -1, -1):
        d = hoje - timedelta(days=i)
        atual = atual + 1 if cont.get(d) else 0
        maior = max(maior, atual)
    corrente = 0
    d = hoje if cont.get(hoje) else hoje - timedelta(days=1)
    while cont.get(d) and (hoje - d).days < DIAS:
        corrente += 1
        d -= timedelta(days=1)
    return maior, corrente


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x0 = WW * 0.611
        self.lugares = [("arvore_lanternas", self.x0, "ver as lanternas do mês")]
        self.hoje = date.today()
        try:
            self.cont = _contar_dias(mirante.app.save.d)
        except Exception:
            self.cont = {}
        self.maior, self.corrente = _sequencias(self.cont, self.hoje)
        self._arvore()
        self._lanternas()
        self.modal_sup = None

    # ------------------------------------------------------------- arte no mundo (pré-renderizada)
    def _arvore(self):
        """Copa escura de silhueta irregular, aro de luar no alto, tronco com raízes. ~38×36 px."""
        w, h = 40, 37
        self.cx, self.base = 20, h - 1              # centro e chão dentro da superfície
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        # tronco e galhos
        pygame.draw.polygon(s, TRONCO, [(18, h - 1), (23, h - 1), (22, 20), (19, 20)])
        pygame.draw.line(s, TRONCO_ESC, (18, h - 1), (19, 21))
        for p in [(14, h - 1), (26, h - 1)]:        # raízes
            pygame.draw.line(s, TRONCO, (20, h - 4), p)
        pygame.draw.line(s, TRONCO, (20, 22), (8, 17))
        pygame.draw.line(s, TRONCO, (21, 21), (33, 16))
        pygame.draw.line(s, TRONCO, (20, 21), (5, 20))
        pygame.draw.line(s, TRONCO, (21, 21), (36, 19))
        # copa: bolhas sobrepostas, sombra embaixo
        bolhas = [(20, 11, 10), (11, 13, 8), (29, 13, 8), (15, 6, 7), (26, 6, 7), (6, 16, 5), (34, 16, 5), (20, 4, 6)]
        for x, y, r in bolhas:
            pygame.draw.circle(s, COPA_SOMBRA, (x, y + 1), r)
        for x, y, r in bolhas:
            pygame.draw.circle(s, COPA, (x, y), r - 1)
        # recorte irregular da borda e aro de luar (a lua fica à direita, no alto)
        for x in range(w):
            for y in range(h - 14):
                if s.get_at((x, y)).a == 0:
                    continue
                viz = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                borda = any(not (0 <= a < w and 0 <= b < h) or s.get_at((a, b)).a == 0 for a, b in viz)
                if borda and _h(f"{x},{y}") % 5 == 0:
                    s.set_at((x, y), (0, 0, 0, 0))
                elif borda and (y < 9 or x > 26) and (x + y) % 2 == 0 and y < 15:
                    s.set_at((x, y), COPA_ARO)
        self.arvore = s
        # pontos de pendurar: dentro da metade de baixo da copa, espaçados (determinísticos)
        cand = [(x, y) for y in range(8, 22) for x in range(3, w - 3)
                if s.get_at((x, y)).a and s.get_at((x, y))[:3] in (COPA, COPA_SOMBRA, TRONCO)]
        cand.sort(key=lambda p: _h(f"anc{p}"))
        ancoras = []
        for p in cand:
            if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= 14 for q in ancoras):
                ancoras.append(p)
            if len(ancoras) >= DIAS + 6:
                break
        ancoras.sort(key=lambda p: (p[1], p[0]))
        self.ancoras = ancoras
        # poça de luz quente no chão (escala com o número de lanternas)
        n = len(self.cont)
        self.poca = None
        if n:
            k = 0.18 + 0.4 * min(1.0, n / 12)
            p = pygame.Surface((44, 8))
            for i in range(4, 0, -1):
                pygame.draw.ellipse(p, _mul((255, 170, 90), k * (1 - i / 5)), (22 - i * 5, 4 - i, i * 10, i * 2))
            self.poca = p

    def _lanternas(self):
        """Uma lanterna por dia com estudo: posição pela data, brilho pela idade."""
        livres = list(range(len(self.ancoras)))
        self.lant = []
        for d in sorted(self.cont, reverse=True):          # hoje primeiro: escolhe galho antes
            if not livres:
                break
            chave = d.isoformat()
            i = livres.pop(_h(chave) % len(livres))
            ax, ay = self.ancoras[i]
            idade = (self.hoje - d).days
            e_hoje = idade == 0
            cor = CORES[_h("c" + chave) % len(CORES)]
            k = 1.0 if e_hoje else max(0.38, 0.92 - 0.018 * idade)
            fio = 3 + _h("f" + chave) % 4
            if e_hoje:
                linhas = [".ddd.", "cCYCc", "cCYCc", "cCYCc", ".cCc.", "..d.."]
            else:
                linhas = [".d.", "cCc", "cCc", ".d."]
            pal = {"d": _mul((70, 44, 40), max(k, 0.6)), "c": _mul(cor, 0.72 * k), "C": _mul(cor, k),
                   "Y": _mul((255, 246, 200), k)}
            sp = pygame.Surface((len(linhas[0]), len(linhas)), pygame.SRCALPHA)
            for y, ln in enumerate(linhas):
                for x, ch in enumerate(ln):
                    if ch in pal:
                        sp.set_at((x, y), pal[ch])
            glow = _brilho(7 if e_hoje else 4, cor, (0.75 if e_hoje else 0.5) * k)
            self.lant.append({"ax": ax, "ay": ay, "fio": fio, "sp": sp, "glow": glow, "hoje": e_hoje,
                              "fase": (_h("p" + chave) % 628) / 100.0, "amp": 1.7 if e_hoje else 0.6 + 0.3 * k})
        self.lant.sort(key=lambda L: L["hoje"])          # a de hoje por cima

    # ------------------------------------------------------------- desenho no mundo
    def draw_margem(self, m, cam):
        sx = self.x0 - cam
        if not -30 < sx < m.get_width() + 30:
            return
        ox, oy = int(sx) - self.cx, PE - self.base
        if self.poca:
            m.blit(self.poca, (int(sx) - 22, PE - 4), special_flags=pygame.BLEND_RGB_ADD)
        m.blit(self.arvore, (ox, oy))
        t = self.mirante.t
        rajada = 0.7 + 0.3 * math.sin(t * 0.006)
        for L in self.lant:
            ax, ay = ox + L["ax"], oy + L["ay"]
            dx = math.sin(t * 0.03 + L["fase"]) * L["amp"] * rajada
            if L["hoje"]:
                dx += math.sin(t * 0.071 + 1.3) * 0.5
            sp = L["sp"]
            lx, ly = ax + dx, ay + L["fio"]
            pygame.draw.line(m, FIO, (ax, ay), (round(lx), ly))
            g = L["glow"]
            pulso = 0 if not L["hoje"] else int(math.sin(t * 0.05) > 0.3)
            m.blit(g, (round(lx) - g.get_width() // 2, ly + sp.get_height() // 2 - g.get_height() // 2 - pulso),
                   special_flags=pygame.BLEND_RGB_ADD)
            m.blit(sp, (round(lx) - sp.get_width() // 2, ly))

    # ------------------------------------------------------------- interação
    def interagir(self, nome):
        try:
            self._montar_modal()
        except Exception:
            self.modal_sup = None
        if self.modal_sup is None:
            return
        self.mirante.abrir_modal(self)

    def evento_modal(self, e, inp):
        if inp.foi("voltar") or inp.foi("ok") or e.type == pygame.MOUSEBUTTONDOWN:
            return False
        return True

    def _lanterna_hd(self, cor, acesa, tam):
        """Lanterna de papel em alta resolução (tam = altura do corpo)."""
        lw, lh = int(tam * 0.82), tam
        s = pygame.Surface((lw + 4, lh + 16), pygame.SRCALPHA)
        cx = (lw + 4) // 2
        pygame.draw.line(s, (120, 100, 110) if acesa else (70, 70, 96), (cx, 0), (cx, 6), 2)
        corpo = pygame.Rect(2, 8, lw, lh - 4)
        if acesa:
            pygame.draw.ellipse(s, _mul(cor, 0.72), corpo)
            pygame.draw.ellipse(s, cor, corpo.inflate(-lw // 3, -4))
            pygame.draw.ellipse(s, (255, 244, 205), corpo.inflate(-lw * 2 // 3, -lh // 3))
            nerv = _mul(cor, 0.55)
        else:
            pygame.draw.ellipse(s, (44, 46, 76), corpo)
            pygame.draw.ellipse(s, (70, 72, 108), corpo, 2)
            nerv = (60, 62, 96)
        for f in (0.3, 0.5, 0.7):                       # nervuras do papel
            y = corpo.y + int(corpo.h * f)
            meia = int(lw / 2 * math.sqrt(max(0.0, 1 - ((f - 0.5) * 2) ** 2)) * 0.9)
            pygame.draw.line(s, nerv, (cx - meia, y), (cx + meia - 1, y))
        tampa = (90, 56, 48) if acesa else (52, 50, 74)
        pygame.draw.rect(s, tampa, (cx - lw // 4, 6, lw // 2, 4), border_radius=1)
        pygame.draw.rect(s, tampa, (cx - lw // 4, corpo.bottom - 2, lw // 2, 4), border_radius=1)
        if acesa:
            pygame.draw.line(s, tampa, (cx, corpo.bottom + 2), (cx, corpo.bottom + 7), 2)
        return s

    def _montar_modal(self):
        f = self.mirante.app.f
        mx = 16 if RETRATO else 70
        alto = min(H - 120, 1000) if RETRATO else H - 40
        r = pygame.Rect(mx, (H - alto) // 2, W - 2 * mx, alto)
        sup = pygame.Surface((W, H), pygame.SRCALPHA)
        sup.fill((4, 4, 16, 200))
        painel(sup, r, cor=(24, 22, 52), borda=(8, 6, 20), raio=16)
        y = r.y + 22
        sombra(sup, "As lanternas do mês", f["grande"], (255, 222, 150), (W // 2, y), centro=True, sombra_cor=(8, 6, 20))
        y += 50
        sombra(sup, "Uma lanterna para cada dia dos últimos 30 em que você respondeu questões.", f["peq"],
               (196, 196, 234), (W // 2, y), centro=True, sombra_cor=(8, 6, 20))
        y += 36
        cols = 5 if RETRATO else 6
        linhas = DIAS // cols
        gx0, gw = r.x + 24, r.w - 48
        rodape = 150 if RETRATO else 112
        gh = r.bottom - rodape - y
        cw, ch = gw / cols, gh / linhas
        empilhado = RETRATO
        tam = int(min(ch * (0.5 if empilhado else 0.62), cw * 0.5, 54))
        self.hd_hoje = None
        for i in range(DIAS):
            d = self.hoje - timedelta(days=DIAS - 1 - i)
            n = self.cont.get(d, 0)
            c = pygame.Rect(int(gx0 + (i % cols) * cw) + 4, int(y + (i // cols) * ch) + 4, int(cw) - 8, int(ch) - 8)
            e_hoje = d == self.hoje
            fundo = (40, 34, 66) if n else (30, 30, 56)
            pygame.draw.rect(sup, fundo, c, border_radius=8)
            if e_hoje:
                pygame.draw.rect(sup, (255, 210, 130), c, 2, border_radius=8)
            cor = CORES[_h("c" + d.isoformat()) % len(CORES)]
            lan = self._lanterna_hd(cor, n > 0, tam)
            if empilhado:
                lp = (c.centerx - lan.get_width() // 2, c.y + 6)
            else:
                lp = (c.x + 10, c.centery - lan.get_height() // 2)
            if n:
                gl = _brilho(int(tam * 0.9), cor, 0.55 if e_hoje else 0.35)
                gp = (lp[0] + lan.get_width() // 2 - gl.get_width() // 2, lp[1] + 8 + tam // 2 - gl.get_height() // 2)
                area = sup.subsurface(c)
                area.blit(gl, (gp[0] - c.x, gp[1] - c.y), special_flags=pygame.BLEND_RGB_ADD)
                if e_hoje:
                    self.hd_hoje = (gl, gp, c.copy())
            sup.blit(lan, lp)
            rot = "hoje" if e_hoje else f"{DIAS_SEM[d.weekday()]} {d.day:02d}/{d.month:02d}"
            qtxt = f"{n} {'questão' if n == 1 else 'questões'}" if n else "apagada"
            corq = (255, 226, 160) if n else (110, 110, 150)
            if empilhado:
                ty = lp[1] + lan.get_height() + 2
                for txt, fo, co in ((rot, f["peq"], (200, 200, 236)), (qtxt, f["peq"], corq)):
                    im = fo.render(txt, True, co)
                    sup.blit(im, (c.centerx - im.get_width() // 2, ty))
                    ty += 22
            else:
                tx = lp[0] + lan.get_width() + 12
                sup.blit(f["peq"].render(rot, True, (200, 200, 236)), (tx, c.centery - 24))
                sup.blit((f["med"] if n else f["peq"]).render(qtxt, True, corq), (tx, c.centery + 2))
        # rodapé: totais e sequências
        dias_n = len(self.cont)
        total = sum(self.cont.values())
        yb = r.bottom - rodape + 10
        if dias_n:
            linha1 = (f"{dias_n} de 30 dias acesos · {total} {'questão' if total == 1 else 'questões'} no mês · "
                      f"maior sequência: {self.maior} {'dia' if self.maior == 1 else 'dias'} seguidos")
            if self.corrente:
                linha1 += f" · sequência atual: {self.corrente}"
        else:
            linha1 = "Nenhuma lanterna acesa nos últimos 30 dias. Um dia com pelo menos uma questão acende uma."
        nota = ("Cada questão conta no dia da última vez em que foi respondida; uma questão refeita depois "
                "aparece só no dia mais recente.")
        from ..ui import quebrar
        for ln in quebrar(linha1, f["med"], r.w - 60):
            sombra(sup, ln, f["med"], (255, 232, 180), (W // 2, yb), centro=True, sombra_cor=(8, 6, 20))
            yb += 30
        yb += 4
        for ln in quebrar(nota, f["peq"], r.w - 60):
            sombra(sup, ln, f["peq"], (160, 160, 206), (W // 2, yb), centro=True, sombra_cor=(8, 6, 20))
            yb += 22
        dica = "toque para fechar" if RETRATO else "Enter, Esc ou clique para fechar"
        sombra(sup, dica, f["peq"], (130, 130, 176), (W // 2, r.bottom - 30), centro=True, sombra_cor=(8, 6, 20))
        self.modal_sup = sup

    def draw_modal(self, tela):
        if self.modal_sup is None:
            return
        tela.blit(self.modal_sup, (0, 0))
        if self.hd_hoje:                                 # a lanterna de hoje respira devagar
            gl, gp, c = self.hd_hoje
            k = 0.5 + 0.5 * math.sin(self.mirante.t * 0.05)
            if k > 0.05:
                g2 = gl.copy() if not hasattr(self, "_g2") else self._g2
                self._g2 = g2
                g2.fill((0, 0, 0))
                g2.blit(gl, (0, 0))
                g2.fill(_mul((255, 255, 255), 0.45 * k), special_flags=pygame.BLEND_RGB_MULT)
                tela.subsurface(c).blit(g2, (gp[0] - c.x, gp[1] - c.y), special_flags=pygame.BLEND_RGB_ADD)
