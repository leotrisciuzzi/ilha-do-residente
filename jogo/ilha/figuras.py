"""Figuras didáticas desenhadas pelo próprio jogo (sem arquivos de imagem).

Cada pílula de aula pode ter "fig": "<nome>"; o Briefing chama figura(nome, largura)
e mostra a figura logo depois da ideia-chave. Nas questões, "[[img:fig:<nome>]]" no
enunciado também funciona (ui._carregar_img reconhece o prefixo "fig:").

Tudo é desenhado numa tela-base de 900 px de largura e reduzido se a área for menor.
"""
import math
import os

import pygame

from . import edicao

BW = 900                                   # largura-base de desenho
PAPEL = (255, 252, 242)
TINTA = (50, 36, 40)
CINZA = (150, 140, 140)
CLARO = (232, 226, 214)
AZUL = (55, 105, 200)
VERMELHO = (205, 65, 65)
VERDE = (50, 145, 80)
LARANJA = (225, 135, 35)
ROXO = (130, 80, 180)
AMARELO = (250, 225, 120)

_FONTES = {}
_CACHE = {}


def _fonte(tam, bold=False):
    if (tam, bold) not in _FONTES:
        nome = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        for base in (edicao.FONTES, "/usr/share/fonts/truetype/dejavu"):
            c = os.path.join(base, nome)
            if os.path.exists(c):
                _FONTES[(tam, bold)] = pygame.font.Font(c, tam)
                break
        else:
            _FONTES[(tam, bold)] = pygame.font.Font(None, int(tam * 1.4))
    return _FONTES[(tam, bold)]


def _quebrar(texto, f, largura):
    out = []
    for par in texto.split("\n"):
        atual = ""
        for p in par.split(" "):
            t = (atual + " " + p).strip()
            if f.size(t)[0] <= largura or not atual:
                atual = t
            else:
                out.append(atual)
                atual = p
        out.append(atual)
    return out


# ------------------------------------------------------------------ kit de desenho

class Tela:
    def __init__(self, h, titulo=None):
        self.s = pygame.Surface((BW, h), pygame.SRCALPHA)
        pygame.draw.rect(self.s, PAPEL, self.s.get_rect(), border_radius=14)
        pygame.draw.rect(self.s, (210, 196, 170), self.s.get_rect(), 2, border_radius=14)
        if titulo:
            self.txt(titulo, BW // 2, 12, TINTA, 19, "tm", True, larg=BW - 40)

    def txt(self, s, x, y, cor=TINTA, tam=16, anc="tl", bold=False, larg=None, fundo=None):
        """Texto (com quebra se larg) ancorado: t/m/b (vertical) + l/m/r (horizontal)."""
        f = _fonte(tam, bold)
        lns = _quebrar(s, f, larg) if larg else [s]
        sup = [f.render(ln, True, cor) for ln in lns]
        w = max(i.get_width() for i in sup)
        h = sum(i.get_height() for i in sup)
        x0 = x - (w // 2 if anc[1] == "m" else w if anc[1] == "r" else 0)
        y0 = y - (h // 2 if anc[0] == "m" else h if anc[0] == "b" else 0)
        if fundo:
            pygame.draw.rect(self.s, fundo, (x0 - 4, y0 - 2, w + 8, h + 4), border_radius=5)
        for i in sup:
            xi = x0 + ((w - i.get_width()) // 2 if anc[1] == "m" else (w - i.get_width()) if anc[1] == "r" else 0)
            self.s.blit(i, (xi, y0))
            y0 += i.get_height()
        return pygame.Rect(x0, y0 - h, w, h)

    def linha(self, a, b, cor=TINTA, w=2):
        pygame.draw.line(self.s, cor, a, b, w)

    def tracejada(self, a, b, cor=CINZA, w=1, passo=8):
        d = math.dist(a, b)
        n = max(1, int(d // passo))
        for i in range(0, n, 2):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            q = (a[0] + (b[0] - a[0]) * min(n, i + 1) / n, a[1] + (b[1] - a[1]) * min(n, i + 1) / n)
            pygame.draw.line(self.s, cor, p, q, w)

    def seta(self, a, b, cor=TINTA, w=3, ponta=11, dupla=False):
        pygame.draw.line(self.s, cor, a, b, w)
        for (p, q) in ([(a, b), (b, a)] if dupla else [(a, b)]):
            ang = math.atan2(q[1] - p[1], q[0] - p[0])
            pts = [q, (q[0] - ponta * math.cos(ang - 0.45), q[1] - ponta * math.sin(ang - 0.45)),
                   (q[0] - ponta * math.cos(ang + 0.45), q[1] - ponta * math.sin(ang + 0.45))]
            pygame.draw.polygon(self.s, cor, pts)

    def caixa(self, r, texto, fundo=(255, 246, 205), borda=(200, 170, 80), cor=TINTA, tam=16, bold=False):
        r = pygame.Rect(r)
        pygame.draw.rect(self.s, fundo, r, border_radius=10)
        pygame.draw.rect(self.s, borda, r, 2, border_radius=10)
        self.txt(texto, r.centerx, r.centery, cor, tam, "mm", bold, larg=r.w - 14)
        return r

    def curva(self, pts, cor, w=3):
        if len(pts) > 1:
            pygame.draw.lines(self.s, cor, False, pts, w)

    def ret(self, r, cor, borda=None, raio=0):
        pygame.draw.rect(self.s, cor, r, border_radius=raio)
        if borda:
            pygame.draw.rect(self.s, borda, r, 2, border_radius=raio)


class Eixos:
    """Plano cartesiano dentro de um retângulo da Tela."""

    def __init__(self, t, r, xr, yr, xlab="", ylab="", xt=(), yt=(), fx=str, fy=str):
        self.t, self.r, self.xr, self.yr = t, pygame.Rect(r), xr, yr
        r = self.r
        for v in yt:
            y = self.py(v)
            t.linha((r.x, y), (r.right, y), (236, 230, 218), 1)
            t.txt(fy(v), r.x - 8, y, CINZA, 14, "mr")
        for v in xt:
            x = self.px(v)
            t.linha((x, r.bottom), (x, r.bottom + 5), CINZA, 1)
            t.txt(fx(v), x, r.bottom + 8, CINZA, 14, "tm")
        t.linha((r.x, r.y), (r.x, r.bottom), TINTA, 2)
        t.linha((r.x, r.bottom), (r.right, r.bottom), TINTA, 2)
        if xlab:
            t.txt(xlab, r.centerx, r.bottom + 30, TINTA, 15, "tm", True)
        if ylab:
            sup = _fonte(15, True).render(ylab, True, TINTA)
            sup = pygame.transform.rotate(sup, 90)
            t.s.blit(sup, (r.x - 62 - sup.get_width() // 2, r.centery - sup.get_height() // 2))

    def px(self, x):
        return self.r.x + (x - self.xr[0]) / (self.xr[1] - self.xr[0]) * self.r.w

    def py(self, y):
        return self.r.bottom - (y - self.yr[0]) / (self.yr[1] - self.yr[0]) * self.r.h

    def p(self, x, y):
        return (self.px(x), self.py(y))

    def func(self, f, x0, x1, n=120):
        return [self.p(x0 + (x1 - x0) * i / n, f(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]

    def faixa_y(self, y0, y1, cor):
        r = pygame.Rect(self.r.x + 1, self.py(y1), self.r.w - 1, self.py(y0) - self.py(y1))
        sup = pygame.Surface(r.size, pygame.SRCALPHA)
        sup.fill(cor)
        self.t.s.blit(sup, r.topleft)

    def faixa_x(self, x0, x1, cor):
        r = pygame.Rect(self.px(x0), self.r.y, self.px(x1) - self.px(x0), self.r.h - 1)
        sup = pygame.Surface(r.size, pygame.SRCALPHA)
        sup.fill(cor)
        self.t.s.blit(sup, r.topleft)

    def ponto(self, x, y, cor=TINTA, rot="", dx=10, dy=-10, anc="bl", guias=True):
        p = self.p(x, y)
        if guias:
            self.t.tracejada((p[0], self.r.bottom), p)
            self.t.tracejada((self.r.x, p[1]), p)
        pygame.draw.circle(self.t.s, cor, p, 7)
        pygame.draw.circle(self.t.s, PAPEL, p, 3)
        if rot:
            self.t.txt(rot, p[0] + dx, p[1] + dy, cor, 15, anc, True, fundo=PAPEL)
        return p


def _v(x):
    """Número com vírgula decimal."""
    return (f"{x:g}").replace(".", ",")


# ------------------------------------------------------------------ química

def ph_h():
    t = Tela(400, "pH × concentração de H⁺: a escala é logarítmica")
    e = Eixos(t, (110, 60, 560, 270), (6.8, 7.8), (0, 170), "pH", "H⁺ (nmol/L)",
              xt=(6.8, 7.0, 7.2, 7.4, 7.6, 7.8), yt=(0, 40, 80, 120, 160), fx=_v)
    e.faixa_x(7.35, 7.45, (90, 190, 100, 50))
    t.curva(e.func(lambda ph: 10 ** (9 - ph), 6.8, 7.8), AZUL, 4)
    e.ponto(7.4, 40, VERDE, "7,40 → 40 nmol/L", -12, -12, "br")
    e.ponto(7.1, 79.4, VERMELHO, "7,10 → 80 (o dobro)", 12, -8)
    e.ponto(7.7, 20, AZUL, "7,70 → 20 (a metade)", -12, -22, "br")
    t.txt("Cada 0,3 de pH = H⁺ × 2", 700, 90, TINTA, 17, "tm", True)
    t.txt("A faixa verde (7,35–7,45) é estreita no pH, mas o H⁺ varia de 35 a 45 nmol/L. "
          "Perto de 7,40, cada 0,01 de pH ≈ 1 nmol/L de H⁺ (base do atalho de Kassirer-Bleich).",
          700, 130, TINTA, 15, "tm", larg=270)
    return t.s


def tampao():
    t = Tela(400, "Curva de titulação do par bicarbonato/CO₂ (pKa 6,1)")
    e = Eixos(t, (110, 60, 440, 270), (0, 1), (4.1, 8.1), "fração na forma de base (HCO₃⁻)", "pH",
              xt=(0, 0.25, 0.5, 0.75, 1), yt=(4.1, 5.1, 6.1, 7.1, 8.1), fx=lambda v: f"{int(v * 100)}%", fy=_v)
    e.faixa_y(5.1, 7.1, (250, 225, 120, 90))
    t.curva(e.func(lambda x: 6.1 + math.log10(x / (1 - x)), 0.008, 0.992), AZUL, 4)
    e.ponto(0.5, 6.1, VERDE, "pH = pKa (metade/metade)", 12, 14, "tl")
    e.ponto(0.952, 7.4, VERMELHO, "sangue: pH 7,40 (20 : 1)", -12, -10, "br")
    t.txt("Zona de tampão", 735, 70, (150, 110, 20), 17, "tm", True)
    t.txt("Entre pKa − 1 e pKa + 1 (faixa amarela) a curva é quase plana: entra ácido ou base e o pH mexe pouco.",
          735, 98, TINTA, 15, "tm", larg=270)
    t.txt("A 7,40 o bicarbonato já está fora da zona plana — num sistema fechado seria um tampão fraco. "
          "Ele vale porque é aberto: pulmão tira CO₂ e rim repõe HCO₃⁻.", 735, 200, TINTA, 15, "tm", larg=270)
    return t.s


def bicarbonato():
    t = Tela(380, "O sistema aberto: pulmão controla o CO₂, rim controla o HCO₃⁻")
    y = 120
    t.caixa((40, y - 32, 190, 64), "CO₂ + H₂O", (220, 235, 255), AZUL, bold=True, tam=19)
    t.caixa((355, y - 32, 190, 64), "H₂CO₃", (240, 240, 240), CINZA, bold=True, tam=19)
    t.caixa((670, y - 32, 190, 64), "H⁺ + HCO₃⁻", (255, 236, 220), LARANJA, bold=True, tam=19)
    for x0, x1 in ((235, 350), (550, 665)):
        t.seta((x0, y - 8), (x1, y - 8), TINTA, 2)
        t.seta((x1, y + 8), (x0, y + 8), TINTA, 2)
    t.txt("anidrase carbônica", 292, y - 38, ROXO, 14, "bm", True)
    t.seta((135, y + 40), (135, 200), AZUL, 4)
    t.txt("PULMÃO: sopra CO₂ (minutos)", 135, 206, AZUL, 15, "tm", True)
    t.seta((765, 200), (765, y + 40), LARANJA, 4)
    t.txt("RIM: guarda e fabrica HCO₃⁻ (dias)", 740, 206, LARANJA, 15, "tm", True)
    # razão 20 : 1
    t.txt("pH = 6,1 + log ( HCO₃⁻ ÷ 0,03 × PaCO₂ ) = 6,1 + log (24 ÷ 1,2) = 6,1 + log 20 = 7,40",
          BW // 2, 256, TINTA, 16, "tm", True)
    x = 210
    for i in range(20):
        t.ret((x + i * 22, 300, 18, 34), (245, 170, 90), (200, 120, 40), 4)
    t.ret((x + 20 * 22 + 40, 300, 18, 34), (120, 160, 230), AZUL, 4)
    t.txt("HCO₃⁻ : 20", x - 10, 317, LARANJA, 16, "mr", True)
    t.txt("CO₂ dissolvido : 1", x + 20 * 22 + 70, 317, AZUL, 16, "ml", True)
    t.txt("O pH depende da RAZÃO, não de cada valor: dobrar os dois mantém 7,40.", BW // 2, 350, TINTA, 15, "tm")
    return t.s


# ------------------------------------------------------------------ fisiologia

def carga_acida():
    t = Tela(370, "Dois tipos de ácido, duas saídas")
    t.caixa((40, 130, 170, 70), "Metabolismo", (240, 240, 240), CINZA, bold=True, tam=18)
    t.caixa((360, 50, 220, 80), "CO₂ (ácido volátil)\n~15.000 mmol/dia", (220, 235, 255), AZUL, tam=16)
    t.caixa((360, 200, 220, 80), "Ácidos fixos\n~1 mEq/kg/dia (~70)", (255, 236, 220), LARANJA, tam=16)
    t.caixa((700, 50, 160, 80), "PULMÃO", (210, 230, 255), AZUL, AZUL, 20, True)
    t.caixa((700, 200, 160, 80), "RIM", (255, 228, 205), LARANJA, LARANJA, 20, True)
    t.seta((212, 150), (356, 92), AZUL, 12, 22)
    t.seta((212, 182), (356, 238), LARANJA, 4)
    t.seta((582, 90), (696, 90), AZUL, 12, 22)
    t.seta((582, 240), (696, 240), LARANJA, 4)
    t.txt("H₂SO₄ (aminoácidos com enxofre), fosfatos, ácidos orgânicos", 470, 288, TINTA, 14, "tm", larg=300)
    t.txt("Rim doente → ácido fixo acumula → acidose metabólica", 780, 292, VERMELHO, 14, "tm", True, larg=200)
    return t.s


def defesas():
    t = Tela(330, "Três linhas de defesa, três velocidades")
    x0, x1 = 210, 860
    marcas = [("segundos", 0), ("minutos", 0.25), ("horas", 0.5), ("1 dia", 0.72), ("3–5 dias", 0.95)]
    t.linha((x0, 260), (x1, 260), TINTA, 2)
    for rot, f in marcas:
        x = x0 + (x1 - x0) * f
        t.linha((x, 255), (x, 265), TINTA, 2)
        t.txt(rot, x, 270, TINTA, 14, "tm")
    linhas = [("Tampões", AZUL, 0.0, 0.03, "HCO₃⁻, Hb, proteínas, fosfato, osso"),
              ("Pulmão", VERDE, 0.2, 0.55, "muda a PaCO₂ (quimiorreceptores)"),
              ("Rim", LARANJA, 0.45, 0.95, "reabsorve e fabrica HCO₃⁻")]
    for i, (nome, cor, ini, cheio, obs) in enumerate(linhas):
        y = 55 + i * 64
        t.txt(nome, x0 - 16, y + 12, cor, 18, "mr", True)
        xa, xc = x0 + (x1 - x0) * ini, x0 + (x1 - x0) * cheio
        pygame.draw.polygon(t.s, cor, [(xa, y + 24), (xc, y), (x1, y), (x1, y + 24)])
        t.txt(obs, 24, y + 30, TINTA, 12, "tl", larg=170)
    t.txt("a rampa vai do início da ação até o efeito máximo", x1, 236, CINZA, 13, "br")
    return t.s


def ventilacao_co2():
    t = Tela(380, "PaCO₂ é inversamente proporcional à ventilação alveolar")
    e = Eixos(t, (110, 60, 480, 250), (1, 10), (0, 120), "ventilação alveolar (L/min)", "PaCO₂ (mmHg)",
              xt=(2, 4, 6, 8, 10), yt=(0, 20, 40, 60, 80, 100, 120))
    e.faixa_y(35, 45, (90, 190, 100, 50))
    t.curva(e.func(lambda va: 160 / va, 1.35, 10), AZUL, 4)
    e.ponto(4, 40, VERDE, "normal: 4 L → 40", 12, -6)
    e.ponto(2, 80, VERMELHO, "metade da ventilação → 80", 12, -6)
    e.ponto(8, 20, AZUL, "dobro → 20", 0, -14, "bm")
    t.txt("PaCO₂ ∝ produção de CO₂ ÷ ventilação alveolar", 740, 70, TINTA, 15, "tm", True, larg=260)
    t.txt("Ventilação alveolar = (volume corrente − espaço morto) × FR", 740, 130, TINTA, 15, "tm", larg=260)
    t.txt("Ex.: 500 − 150 = 350 mL × 12 = 4,2 L. Rápida e rasa: 200 − 150 = 50 mL × 40 = 2 L → PaCO₂ sobe "
          "mesmo com a ventilação-minuto parecida.", 740, 190, VERMELHO, 14, "tm", larg=260)
    return t.s


# ------------------------------------------------------------------ rim

def _celula(t, titulo_luz="LUZ TUBULAR", titulo_cel="CÉLULA", titulo_sg="SANGUE", h=330):
    t.ret((30, 50, 230, h - 70), (235, 245, 255), None, 10)
    t.ret((280, 50, 340, h - 70), (255, 238, 225), (215, 160, 120), 26)
    t.ret((640, 50, 230, h - 70), (255, 228, 228), None, 10)
    for x, s in ((145, titulo_luz), (450, titulo_cel), (755, titulo_sg)):
        t.txt(s, x, 58, CINZA, 14, "tm", True)


def rim_proximal():
    t = Tela(370, "Túbulo proximal: recuperar o HCO₃⁻ filtrado")
    _celula(t, "LUZ (filtrado)", "CÉLULA PROXIMAL")
    t.txt("HCO₃⁻ filtrado + H⁺", 145, 100, LARANJA, 16, "tm", True)
    t.seta((145, 125), (145, 150), TINTA, 2)
    t.txt("H₂CO₃", 145, 155, TINTA, 16, "tm", True)
    t.seta((145, 180), (145, 205), ROXO, 3)
    t.txt("AC", 172, 184, ROXO, 14, "tl", True)
    t.txt("CO₂ + H₂O", 145, 210, AZUL, 16, "tm", True)
    t.seta((215, 220), (330, 220), AZUL, 3)
    t.txt("CO₂ entra", 272, 226, AZUL, 13, "tm")
    t.txt("CO₂ + H₂O", 360, 210, AZUL, 16, "tl", True)
    t.seta((420, 200), (420, 160), ROXO, 3)
    t.txt("AC", 430, 172, ROXO, 14, "tl", True)
    t.txt("H⁺ + HCO₃⁻", 360, 128, TINTA, 16, "tl", True)
    t.seta((355, 138), (240, 112), VERMELHO, 3)
    t.txt("H⁺ sai (troca por Na⁺)", 290, 82, VERMELHO, 13, "tm", True)
    t.seta((490, 138), (700, 138), LARANJA, 5)
    t.txt("HCO₃⁻ volta ao sangue", 755, 150, LARANJA, 16, "tm", True)
    t.txt("80–90% dos ~4.500 mEq/dia filtrados", 755, 176, TINTA, 14, "tm", larg=210)
    pygame.draw.line(t.s, VERMELHO, (128, 182), (162, 204), 5)
    pygame.draw.line(t.s, VERMELHO, (162, 182), (128, 204), 5)
    t.txt("Acetazolamida bloqueia a AC (anidrase carbônica): o HCO₃⁻ fica na urina → acidose de AG normal.",
          BW // 2, 318, VERMELHO, 15, "tm", True, larg=800)
    return t.s


def rim_novo():
    t = Tela(370, "Gerar HCO₃⁻ novo: o H⁺ sai na urina preso a tampões")
    _celula(t, "LUZ (urina)", "CÉLULA TUBULAR", h=300)
    t.txt("CO₂ + H₂O → H⁺ + HCO₃⁻", 450, 160, TINTA, 16, "mm", True)
    t.seta((330, 150), (250, 110), VERMELHO, 3)
    t.seta((330, 172), (250, 220), VERMELHO, 3)
    t.txt("H⁺", 300, 108, VERMELHO, 15, "bm", True)
    t.txt("H⁺ + HPO₄²⁻ → H₂PO₄⁻", 145, 100, TINTA, 14, "tm", True)
    t.txt("acidez titulável ≈ 1/3", 145, 122, AZUL, 14, "tm", True)
    t.txt("NH₃ + H⁺ → NH₄⁺", 145, 205, TINTA, 15, "tm", True)
    t.txt("amônio ≈ 2/3", 145, 228, VERDE, 14, "tm", True)
    t.txt("(sobe muito na acidose crônica)", 145, 248, VERDE, 13, "tm")
    t.seta((560, 160), (690, 160), LARANJA, 5)
    t.txt("1 HCO₃⁻ NOVO", 755, 140, LARANJA, 17, "tm", True)
    t.txt("para cada H⁺ excretado", 755, 168, TINTA, 14, "tm")
    tot = 620
    t.ret((140, 306, tot // 3, 30), (120, 160, 230), AZUL, 6)
    t.ret((140 + tot // 3, 306, tot - tot // 3, 30), (130, 200, 140), VERDE, 6)
    t.txt("fosfato 1/3", 140 + tot // 6, 321, TINTA, 14, "mm", True)
    t.txt("amônio 2/3 — a via que cresce", 140 + tot // 3 + (tot - tot // 3) // 2, 321, TINTA, 14, "mm", True)
    t.txt("H⁺ livre na urina é ínfimo (pH urinário mínimo ≈ 4,5).", BW // 2, 342, CINZA, 13, "tm")
    return t.s


def aldosterona():
    t = Tela(380, "Ducto coletor: o que a aldosterona faz")
    t.ret((30, 50, 230, 260), (235, 245, 255), None, 10)
    t.txt("LUZ", 145, 58, CINZA, 14, "tm", True)
    t.txt("− − −", 145, 180, AZUL, 30, "mm", True)
    t.txt("luz negativa", 145, 206, AZUL, 14, "tm", True)
    t.ret((290, 60, 300, 115), (255, 238, 225), (215, 160, 120), 22)
    t.txt("célula PRINCIPAL", 440, 66, CINZA, 14, "tm", True)
    t.ret((290, 190, 300, 115), (240, 230, 255), (170, 140, 210), 22)
    t.txt("célula INTERCALADA A", 440, 196, CINZA, 14, "tm", True)
    t.seta((240, 96), (300, 96), VERDE, 4)
    t.txt("Na⁺ entra (ENaC)", 340, 96, VERDE, 14, "ml", True)
    t.seta((300, 140), (240, 140), LARANJA, 4)
    t.txt("K⁺ sai", 340, 140, LARANJA, 14, "ml", True)
    t.seta((300, 250), (240, 250), VERMELHO, 4)
    t.txt("H⁺ sai (bomba de H⁺)", 340, 250, VERMELHO, 14, "ml", True)
    t.caixa((630, 70, 240, 70), "ALDOSTERONA", (255, 246, 205), (200, 170, 80), tam=17, bold=True)
    t.seta((640, 120), (592, 110), (200, 170, 80), 3)
    t.seta((640, 125), (592, 240), (200, 170, 80), 3)
    t.caixa((620, 170, 260, 64), "EXCESSO: alcalose metabólica + hipocalemia", (255, 236, 220), LARANJA, tam=14)
    t.caixa((620, 245, 260, 64), "FALTA (ATR tipo 4): acidose + hipercalemia", (225, 235, 255), AZUL, tam=14)
    t.txt("Mais Na⁺ entrando deixa a luz mais negativa, o que puxa K⁺ e H⁺ para a urina.",
          BW // 2, 330, TINTA, 15, "tm", larg=820)
    return t.s


# ------------------------------------------------------------------ oxigênio

def _sat(p, p50=26.8, n=2.7):
    return 100 * p ** n / (p ** n + p50 ** n) if p > 0 else 0


def curva_o2():
    t = Tela(440, "Curva de dissociação da hemoglobina: o platô e a parte íngreme")
    e = Eixos(t, (110, 60, 470, 300), (0, 120), (0, 100), "PaO₂ (mmHg)", "Saturação (%)",
              xt=(0, 20, 40, 60, 80, 100, 120), yt=(0, 25, 50, 75, 90, 100))
    e.faixa_x(60, 120, (90, 190, 100, 45))
    e.faixa_x(0, 60, (225, 90, 90, 30))
    t.curva(e.func(_sat, 0, 120, 200), AZUL, 5)
    t.txt("PLATÔ", e.px(90), e.py(62), VERDE, 20, "mm", True)
    t.txt("a Hb já está quase cheia", e.px(90), e.py(53), VERDE, 13, "mm", True)
    t.txt("PARTE ÍNGREME", e.px(30), e.py(25), VERMELHO, 16, "mm", True)
    e.ponto(26.8, 50, ROXO, "P50 ≈ 27 → 50%", 10, 4, "tl")
    e.ponto(40, 75, LARANJA, "40 → 75% (venoso misto)", 10, 6, "tl")
    e.ponto(60, 90, VERMELHO, "60 → 90% (o joelho)", 12, 8, "tl")
    e.ponto(100, _sat(100), VERDE, "100 → 97%", -6, -12, "bm")
    t.txt("No platô (PaO₂ > 60), subir a PaO₂ de 60 para 100 ganha só ~7% de saturação: há reserva.",
          750, 70, TINTA, 15, "tm", larg=250)
    t.txt("Abaixo do joelho, pequenas quedas de PaO₂ derrubam a saturação. Por isso PaO₂ < 60 (Sat < 90%) "
          "define insuficiência respiratória.", 750, 170, VERMELHO, 15, "tm", larg=250)
    t.txt("Regra 40-50-60 / 75-80-90: PaO₂ 40 → 75%, 50 → 80%, 60 → 90%.", 750, 300, ROXO, 14, "tm", True, larg=250)
    return t.s


def curva_desvio():
    t = Tela(420, "Desvios da curva: quem ajuda a soltar e quem prende o O₂")
    e = Eixos(t, (110, 60, 470, 280), (0, 120), (0, 100), "PaO₂ (mmHg)", "Saturação (%)",
              xt=(0, 20, 40, 60, 80, 100, 120), yt=(0, 50, 100))
    t.tracejada(e.p(0, 50), e.p(120, 50), CINZA)
    t.curva(e.func(lambda p: _sat(p, 18), 0, 120, 200), VERMELHO, 4)
    t.curva(e.func(_sat, 0, 120, 200), TINTA, 4)
    t.curva(e.func(lambda p: _sat(p, 36), 0, 120, 200), AZUL, 4)
    for p50, cor in ((18, VERMELHO), (26.8, TINTA), (36, AZUL)):
        pygame.draw.circle(t.s, cor, e.p(p50, 50), 6)
    t.seta(e.p(27, 40), e.p(37, 40), AZUL, 3)
    t.seta(e.p(26, 60), e.p(17, 60), VERMELHO, 3)
    t.txt("P50 maior", e.px(40), e.py(36), AZUL, 13, "tl", True)
    t.txt("P50 menor", e.px(14), e.py(64), VERMELHO, 13, "br", True)
    t.caixa((610, 60, 270, 140), "DIREITA (solta O₂ no tecido): ↑ H⁺ (acidose), ↑ CO₂, febre, ↑ 2,3-DPG "
            "(anemia crônica, altitude)", (225, 235, 255), AZUL, tam=14)
    t.caixa((610, 215, 270, 140), "ESQUERDA (prende O₂): alcalose, hipotermia, sangue estocado, Hb fetal, "
            "monóxido de carbono, meta-Hb", (255, 228, 228), VERMELHO, tam=14)
    t.txt("Mnemônico: tecido que trabalha (quente, ácido, com CO₂) puxa a curva para a direita.",
          BW // 2, 392, TINTA, 14, "tm", True)
    return t.s


def conteudo_o2():
    t = Tela(380, "Conteúdo arterial de O₂: quem carrega é a hemoglobina")
    casos = [("Normal\nHb 15 · Sat 98% · PaO₂ 95", 15, 98, 95),
             ("Anemia\nHb 7,5 · Sat 98% · PaO₂ 95", 7.5, 98, 95),
             ("O₂ 100%\nHb 15 · Sat 100% · PaO₂ 500", 15, 100, 500)]
    base, esc, larg = 300, 10.5, 120
    for i, (rot, hb, sat, pao2) in enumerate(casos):
        x = 120 + i * 180
        lig, dis = 1.34 * hb * sat / 100, 0.003 * pao2
        h1, h2 = lig * esc, dis * esc
        t.ret((x, base - h1, larg, h1), (225, 110, 110), VERMELHO)
        t.ret((x, base - h1 - h2, larg, max(2, h2)), (120, 160, 230), AZUL)
        t.txt(f"{_v(round(lig + dis, 1))} mL/dL", x + larg // 2, base - h1 - h2 - 6, TINTA, 15, "bm", True)
        t.txt(rot, x + larg // 2, base + 8, TINTA, 13, "tm", larg=170)
    t.linha((90, base), (650, base), TINTA, 2)
    t.ret((690, 90, 22, 22), (225, 110, 110), VERMELHO)
    t.txt("ligado à Hb: 1,34 × Hb × Sat", 720, 101, TINTA, 14, "ml", larg=170)
    t.ret((690, 150, 22, 22), (120, 160, 230), AZUL)
    t.txt("dissolvido: 0,003 × PaO₂", 720, 161, TINTA, 14, "ml", larg=170)
    t.txt("Na anemia a PaO₂ e a saturação são normais, mas o conteúdo cai pela metade. "
          "O₂ a 100% quase não acrescenta (azul fininho).", 785, 200, VERMELHO, 14, "tm", larg=200)
    return t.s


# ------------------------------------------------------------------ trocas

def cascata_o2():
    t = Tela(380, "Do ar à artéria: equação do gás alveolar e gradiente A-a")
    e = Eixos(t, (110, 60, 470, 260), (0, 3), (0, 160), "", "PO₂ (mmHg)", yt=(0, 40, 80, 120, 160))
    degraus = [("ar inspirado", 150, "0,21 × (760 − 47) = 150"), ("alvéolo (PAO₂)", 100, "150 − PaCO₂/0,8 = 150 − 50"),
               ("artéria (PaO₂)", 90, "medida na gasometria")]
    for i, (rot, v, conta) in enumerate(degraus):
        x0, x1 = e.px(i + 0.12), e.px(i + 0.88)
        t.ret((x0, e.py(v), x1 - x0, e.py(0) - e.py(v)), (120, 160, 230) if i < 2 else (225, 110, 110), None, 6)
        t.txt(f"{v}", (x0 + x1) / 2, e.py(v) - 4, TINTA, 17, "bm", True)
        t.txt(rot, (x0 + x1) / 2, e.r.bottom + 8, TINTA, 14, "tm", True)
        t.txt(conta, (x0 + x1) / 2, e.r.bottom + 28, CINZA, 12, "tm", larg=150)
    xg = e.px(2.95)
    t.seta((xg, e.py(100)), (xg, e.py(90)), VERMELHO, 2, 7, True)
    t.txt("A-a = 10", xg + 6, e.py(95), VERMELHO, 14, "ml", True)
    t.txt("Gradiente A-a = PAO₂ − PaO₂", 760, 70, TINTA, 16, "tm", True, larg=230)
    t.txt("Normal 5–15 no jovem; limite estimado = idade/4 + 4.", 760, 120, TINTA, 15, "tm", larg=230)
    t.txt("PaO₂ baixa + gradiente normal = o O₂ não chegou ao alvéolo (hipoventilação, altitude). "
          "Gradiente alto = o pulmão não passa o O₂.", 760, 190, VERMELHO, 14, "tm", larg=230)
    return t.s


def hipoxemia():
    t = Tela(360, "Cinco causas de hipoxemia, separadas pelo gradiente A-a")
    t.caixa((340, 50, 220, 50), "HIPOXEMIA", (255, 246, 205), (200, 170, 80), tam=17, bold=True)
    t.caixa((70, 135, 270, 50), "Gradiente A-a NORMAL", (220, 240, 220), VERDE, tam=15, bold=True)
    t.caixa((510, 135, 270, 50), "Gradiente A-a ALTO", (255, 228, 228), VERMELHO, tam=15, bold=True)
    t.seta((400, 100), (220, 132), TINTA, 2)
    t.seta((500, 100), (640, 132), TINTA, 2)
    folhas = [(20, "FiO₂ baixa\n(altitude)", VERDE, "melhora com O₂"), (185, "Hipoventilação\n(PaCO₂ ↑)", VERDE, "melhora com O₂"),
              (400, "Distúrbio V/Q\n(asma, DPOC, TEP)", VERMELHO, "melhora com O₂"),
              (570, "Shunt\n(SDRA, atelectasia)", VERMELHO, "NÃO melhora com O₂ 100%"),
              (740, "Difusão\n(fibrose)", VERMELHO, "melhora com O₂")]
    for x, rot, cor, resp in folhas:
        w = 150
        pai = (205, 185) if cor == VERDE else (645, 185)
        t.seta(pai, (x + w // 2, 228), cor, 2)
        t.caixa((x, 230, w, 62), rot, PAPEL, cor, tam=13)
        t.txt(resp, x + w // 2, 300, VERMELHO if "NÃO" in resp else CINZA, 12, "tm", "NÃO" in resp, larg=w)
    t.txt("Hipoventilação é a única com PaCO₂ alta.", BW // 2, 336, TINTA, 14, "tm", True)
    return t.s


def pf():
    t = Tela(270, "Relação P/F (PaO₂ ÷ FiO₂) e a gravidade da SDRA (Berlim, PEEP ≥ 5)")
    x0, x1, y = 80, 820, 110
    esc = (x1 - x0) / 500
    faixas = [(0, 100, "GRAVE\n≤ 100", (225, 90, 90)), (100, 200, "MODERADA\n100–200", (240, 150, 90)),
              (200, 300, "LEVE\n200–300", (245, 205, 100)), (300, 400, "hipoxemia\nsem SDRA", (225, 225, 210)),
              (400, 500, "NORMAL\n400–500", (140, 200, 140))]
    for a, b, rot, cor in faixas:
        t.ret((x0 + a * esc, y, (b - a) * esc, 60), cor)
        t.txt(rot, x0 + (a + b) / 2 * esc, y + 30, TINTA, 14, "mm", True)
    for v in range(0, 501, 100):
        t.linha((x0 + v * esc, y + 60), (x0 + v * esc, y + 68), TINTA, 2)
        t.txt(str(v), x0 + v * esc, y + 72, TINTA, 14, "tm")
    px = x0 + 100 * esc
    t.seta((px, y - 30), (px, y - 4), TINTA, 3)
    t.txt("PaO₂ 80 ÷ FiO₂ 0,8 = 100", px, y - 34, TINTA, 14, "bm", True)
    t.txt("FiO₂ sempre em fração (ar ambiente = 0,21). Ar ambiente com PaO₂ 95 → 95 ÷ 0,21 ≈ 450.",
          BW // 2, 215, TINTA, 14, "tm", larg=820)
    return t.s


# ------------------------------------------------------------------ interpretação

def referencias():
    t = Tela(330, "Valores normais da gasometria arterial (e onde a venosa cai)")
    linhas = [("pH", 7.0, 7.8, 7.35, 7.45, -0.04, "7,35–7,45", _v),
              ("PaCO₂ (mmHg)", 10, 90, 35, 45, 5, "35–45", str),
              ("HCO₃⁻ (mEq/L)", 5, 45, 22, 26, 1, "22–26", str)]
    x0, x1 = 230, 760
    for i, (nome, a, b, n0, n1, dv, rot, fm) in enumerate(linhas):
        y = 80 + i * 75
        t.txt(nome, x0 - 16, y + 12, TINTA, 16, "mr", True)
        t.ret((x0, y + 4, x1 - x0, 16), CLARO, None, 8)
        px = lambda v: x0 + (v - a) / (b - a) * (x1 - x0)
        t.ret((px(n0), y, px(n1) - px(n0), 24), (110, 190, 120), VERDE, 6)
        t.txt(rot, (px(n0) + px(n1)) / 2, y + 28, VERDE, 14, "tm", True)
        t.txt(fm(a), x0, y + 28, CINZA, 13, "tl")
        t.txt(fm(b), x1, y + 28, CINZA, 13, "tr")
        if i < 2:
            mv = (n0 + n1) / 2 + dv
            t.seta(((px(n0) + px(n1)) / 2, y - 2), (px(mv), y - 2), ROXO, 2, 7)
            t.txt("venosa", px(mv) + (6 if dv > 0 else -6), y - 4, ROXO, 12, "bl" if dv > 0 else "br", True)
    t.txt("BE −2 a +2 · lactato < 2 mmol/L", 830, 90, TINTA, 14, "tm", larg=120)
    t.txt("Venosa: pH 0,03–0,05 menor, PCO₂ 4–6 maior. Serve para pH e HCO₃⁻; NÃO serve para oxigenação.",
          BW // 2, 290, ROXO, 14, "tm", True, larg=820)
    return t.s


def erros_coleta():
    t = Tela(300, "Erros de coleta deixam assinaturas previsíveis")
    cards = [("Bolha de ar", "a amostra se mistura com o ar", [("PaO₂", "→ 150", AZUL), ("PaCO₂", "↓", AZUL)]),
             ("Demora / leucocitose", "as células consomem O₂ na seringa", [("PaO₂", "↓ (falsa)", VERMELHO), ("SpO₂", "normal", VERDE)]),
             ("Heparina demais", "a amostra fica diluída", [("PCO₂", "↓", AZUL), ("HCO₃⁻", "↓", AZUL)])]
    for i, (tit, mec, efeitos) in enumerate(cards):
        x = 30 + i * 285
        t.ret((x, 55, 270, 225), (255, 246, 230), (210, 180, 140), 12)
        t.txt(tit, x + 135, 68, TINTA, 17, "tm", True)
        t.txt(mec, x + 135, 98, CINZA, 13, "tm", larg=240)
        for j, (par, ef, cor) in enumerate(efeitos):
            y = 160 + j * 50
            t.txt(par, x + 95, y, TINTA, 19, "mr", True)
            t.txt(ef, x + 110, y, cor, 19, "ml", True)
    return t.s


def roteiro():
    t = Tela(300, "O roteiro: sempre na mesma ordem")
    passos = [("1", "pH", "acidemia ou alcalemia?"), ("2", "Quem explica?", "HCO₃⁻ (metabólico) ou PaCO₂ (respiratório)"),
              ("3", "Compensação", "dentro do esperado? fora = 2º distúrbio"),
              ("4", "Ânion gap", "na acidose metabólica; corrigir pela albumina"),
              ("5", "Delta-delta", "se AG alto: há outro distúrbio escondido?"), ("6", "O₂ e clínica", "PaO₂, P/F, A-a, história")]
    for i, (n, tit, sub) in enumerate(passos):
        col, lin = i % 3, i // 3
        x, y = 40 + col * 285, 60 + lin * 115
        cor = (255, 246, 205) if i != 2 else (255, 228, 228)
        t.ret((x, y, 250, 95), cor, (200, 170, 80) if i != 2 else VERMELHO, 12)
        pygame.draw.circle(t.s, TINTA, (x + 24, y + 24), 16)
        t.txt(n, x + 24, y + 24, PAPEL, 17, "mm", True)
        t.txt(tit, x + 48, y + 14, TINTA, 17, "tl", True)
        t.txt(sub, x + 125, y + 46, TINTA, 13, "tm", larg=230)
        if col < 2:
            t.seta((x + 252, y + 47), (x + 282, y + 47), TINTA, 3, 9)
    t.seta((40 + 2 * 285 + 125, 157), (40 + 125, 172), CINZA, 2, 9)
    return t.s


def acidemia():
    t = Tela(300, "Acidemia é o pH; acidose é o processo que empurra")
    x0, x1, y = 90, 810, 150
    a, b = 6.9, 7.9
    px = lambda v: x0 + (v - a) / (b - a) * (x1 - x0)
    t.ret((px(a), y, px(7.35) - px(a), 40), (240, 150, 150))
    t.ret((px(7.35), y, px(7.45) - px(7.35), 40), (140, 200, 140))
    t.ret((px(7.45), y, px(b) - px(7.45), 40), (150, 180, 240))
    t.txt("ACIDEMIA (pH < 7,35)", (px(a) + px(7.35)) / 2, y + 20, TINTA, 15, "mm", True)
    t.txt("ALCALEMIA (pH > 7,45)", (px(7.45) + px(b)) / 2, y + 20, TINTA, 15, "mm", True)
    for v in (7.0, 7.2, 7.35, 7.45, 7.6, 7.8):
        t.txt(_v(v), px(v), y + 46, CINZA, 13, "tm")
    c = px(7.40)
    t.txt("normal", c, y - 4, VERDE, 13, "bm", True)
    t.seta((c - 10, 95), (c - 190, 95), VERMELHO, 6, 16)
    t.seta((c + 10, 95), (c + 190, 95), AZUL, 6, 16)
    t.txt("acidose metabólica (HCO₃⁻ 12) empurra para baixo", c - 205, 95, VERMELHO, 14, "mr", True, larg=200)
    t.txt("alcalose respiratória (PaCO₂ 20) empurra para cima", c + 205, 95, AZUL, 14, "ml", True, larg=200)
    t.txt("Os dois processos empurram com a mesma força: pH 7,40 com DOIS distúrbios. pH normal não exclui doença.",
          BW // 2, 240, TINTA, 15, "tm", True, larg=800)
    return t.s


def primario():
    t = Tela(330, "Quem explica o pH? (e a compensação anda no MESMO sentido)")
    x0, y0, cw, ch = 210, 70, 320, 95
    t.txt("METABÓLICO", x0 + cw // 2, y0 - 8, LARANJA, 16, "bm", True)
    t.txt("RESPIRATÓRIO", x0 + cw + cw // 2, y0 - 8, AZUL, 16, "bm", True)
    t.txt("ACIDEMIA\npH < 7,35", x0 - 16, y0 + ch // 2, VERMELHO, 16, "mr", True)
    t.txt("ALCALEMIA\npH > 7,45", x0 - 16, y0 + ch + ch // 2, AZUL, 16, "mr", True)
    cel = [("HCO₃⁻ ↓", "PaCO₂ ↓ compensa"), ("PaCO₂ ↑", "HCO₃⁻ ↑ compensa"),
           ("HCO₃⁻ ↑", "PaCO₂ ↑ compensa"), ("PaCO₂ ↓", "HCO₃⁻ ↓ compensa")]
    for i, (pri, comp) in enumerate(cel):
        c, l = i % 2, i // 2
        r = (x0 + c * cw, y0 + l * ch, cw, ch)
        t.ret(r, (255, 248, 232), (200, 180, 150))
        t.txt(pri, r[0] + cw // 2, r[1] + 30, TINTA, 22, "mm", True)
        t.txt(comp, r[0] + cw // 2, r[1] + 66, CINZA, 14, "mm", True)
    t.txt("HCO₃⁻ e PaCO₂ em sentidos OPOSTOS = distúrbio misto, sem precisar de fórmula "
          "(ex.: HCO₃⁻ ↓ com PaCO₂ ↑ = acidose metabólica + respiratória).", BW // 2, 275, VERMELHO, 15, "tm", True, larg=820)
    return t.s


def winter():
    t = Tela(400, "Acidose metabólica: a PaCO₂ esperada (Winter = 1,5 × HCO₃⁻ + 8 ± 2)")
    e = Eixos(t, (110, 60, 480, 270), (4, 24), (10, 50), "HCO₃⁻ (mEq/L)", "PaCO₂ (mmHg)",
              xt=(4, 8, 12, 16, 20, 24), yt=(10, 20, 30, 40, 50))
    banda = e.func(lambda h: 1.5 * h + 10, 4, 24) + e.func(lambda h: 1.5 * h + 6, 4, 24)[::-1]
    sup = pygame.Surface((BW, 400), pygame.SRCALPHA)
    pygame.draw.polygon(sup, (90, 190, 100, 70), banda)
    t.s.blit(sup, (0, 0))
    t.curva(e.func(lambda h: 1.5 * h + 8, 4, 24), VERDE, 3)
    t.txt("acidose respiratória associada", e.px(6), e.py(44), VERMELHO, 14, "tl", True)
    t.txt("alcalose respiratória associada", e.px(13), e.py(14), AZUL, 14, "tl", True)
    e.ponto(12, 26, VERDE, "esperado 26 ± 2", 12, 22, "tl", False)
    e.ponto(12, 36, VERMELHO, "medida 36 → retém CO₂", 12, -8, "bl", False)
    t.txt("Ex.: HCO₃⁻ 12 → 1,5 × 12 + 8 = 26 (24–28).", 740, 80, TINTA, 15, "tm", True, larg=260)
    t.txt("Acima da faixa: o pulmão não está compensando (fadiga, sedação) — acidose respiratória junto.",
          740, 140, VERMELHO, 14, "tm", larg=260)
    t.txt("Atalho: PaCO₂ esperada ≈ os dois dígitos finais do pH (pH 7,25 → 25).", 740, 240, ROXO, 14, "tm", larg=260)
    return t.s


def comp_respiratoria():
    t = Tela(420, "Distúrbio respiratório: HCO₃⁻ esperado, agudo × crônico")
    e = Eixos(t, (110, 60, 450, 290), (20, 80), (12, 40), "PaCO₂ (mmHg)", "HCO₃⁻ (mEq/L)",
              xt=(20, 30, 40, 50, 60, 70, 80), yt=(12, 16, 20, 24, 28, 32, 36, 40))
    t.curva(e.func(lambda p: 24 + (p - 40) * 0.1, 40, 80), LARANJA, 3)
    t.curva(e.func(lambda p: 24 + (p - 40) * 0.35, 40, 80), VERMELHO, 4)
    t.curva(e.func(lambda p: 24 - (40 - p) * 0.2, 20, 40), LARANJA, 3)
    t.curva(e.func(lambda p: 24 - (40 - p) * 0.45, 20, 40), AZUL, 4)
    pygame.draw.circle(t.s, TINTA, e.p(40, 24), 6)
    t.txt("aguda +1/10", e.px(80) - 4, e.py(28) + 4, LARANJA, 13, "tr", True)
    t.txt("crônica +3,5/10", e.px(74), e.py(36.5), VERMELHO, 13, "br", True)
    t.txt("aguda −2/10", e.px(21), e.py(20) - 4, LARANJA, 13, "bl", True)
    t.txt("crônica −4 a 5/10", e.px(21), e.py(15), AZUL, 13, "tl", True)
    e.ponto(60, 31, VERDE, "DPOC 60/31: crônica ok", -10, -10, "br", False)
    t.txt("Acidose respiratória", 750, 70, VERMELHO, 15, "tm", True, larg=270)
    t.txt("aguda: HCO₃⁻ +1 a cada 10 mmHg\ncrônica (3–5 dias): +3,5", 750, 98, TINTA, 14, "tm", larg=270)
    t.txt("Alcalose respiratória", 750, 190, AZUL, 15, "tm", True, larg=270)
    t.txt("aguda: HCO₃⁻ −2 a cada 10 mmHg\ncrônica: −4 a 5", 750, 218, TINTA, 14, "tm", larg=270)
    t.txt("Fora das linhas = 2º distúrbio metabólico.", 750, 300, ROXO, 14, "tm", True, larg=270)
    return t.s


# ------------------------------------------------------------------ ânion gap

def _gamble(t, x, base, esc, colunas, larg=90):
    """Colunas empilhadas [(valor, rótulo, cor)] de baixo para cima."""
    y = base
    for v, rot, cor in colunas:
        h = v * esc
        t.ret((x, y - h, larg, h), cor, TINTA)
        if rot:
            t.txt(rot, x + larg // 2, y - h / 2, TINTA, 13 if h > 30 else 11, "mm", True, larg=larg - 4)
        y -= h


def gamble_normal():
    t = Tela(400, "Ânion gap: os ânions que o laboratório não mede")
    base, esc = 360, 2.1
    _gamble(t, 220, base, esc, [(140, "Na⁺\n140", (245, 205, 120))], 140)
    _gamble(t, 380, base, esc, [(104, "Cl⁻\n104", (150, 200, 150)), (24, "HCO₃⁻ 24", (245, 170, 90)),
                                (12, "AG 12", (200, 180, 230))], 140)
    t.txt("CÁTIONS", 290, base + 6, TINTA, 14, "tm", True)
    t.txt("ÂNIONS", 450, base + 6, TINTA, 14, "tm", True)
    t.txt("AG = Na⁺ − (Cl⁻ + HCO₃⁻)\n= 140 − (104 + 24) = 12", 740, 80, TINTA, 16, "tm", True, larg=280)
    t.txt("O 'gap' é feito sobretudo de albumina (e fosfato, sulfato, ânions orgânicos).", 740, 150, TINTA, 14,
          "tm", larg=270)
    t.txt("Albumina baixa encolhe o gap: some 2,5 para cada 1 g/dL abaixo de 4.", 740, 220, VERMELHO, 14,
          "tm", True, larg=270)
    return t.s


def gamble_comparar():
    t = Tela(420, "Ácido com ânion novo (AG alto) × perda de HCO₃⁻ (AG normal)")
    base, esc = 350, 2.0
    cols = [("NORMAL", [(104, "Cl⁻ 104", (150, 200, 150)), (24, "HCO₃⁻ 24", (245, 170, 90)), (12, "AG 12", (200, 180, 230))]),
            ("AG ALTO", [(104, "Cl⁻ 104", (150, 200, 150)), (12, "HCO₃⁻ 12", (245, 170, 90)),
                         (24, "AG 24\nlactato, cetona", (190, 140, 225))]),
            ("AG NORMAL", [(116, "Cl⁻ 116", (110, 185, 110)), (12, "HCO₃⁻ 12", (245, 170, 90)), (12, "AG 12", (200, 180, 230))])]
    for i, (tit, c) in enumerate(cols):
        x = 70 + i * 270
        _gamble(t, x, base, esc, [(140, "Na⁺ 140", (245, 205, 120))], 80)
        _gamble(t, x + 90, base, esc, c, 110)
        t.txt(tit, x + 95, base + 8, TINTA, 15, "tm", True)
    t.txt("o ânion do ácido ocupa o lugar do HCO₃⁻", 70 + 270 + 95, base + 30, ROXO, 13, "tm", larg=250)
    t.txt("o Cl⁻ sobe no lugar do HCO₃⁻ (hiperclorêmica)", 70 + 540 + 95, base + 30, VERDE, 13, "tm", larg=250)
    return t.s


def delta_delta():
    t = Tela(330, "Delta-delta = (AG − 12) ÷ (24 − HCO₃⁻)")
    x0, x1, y = 80, 820, 120
    px = lambda v: x0 + v / 3 * (x1 - x0)
    zonas = [(0, 1, "< 1\n+ acidose de AG normal\n(diarreia, soro fisiológico)", (150, 200, 150)),
             (1, 2, "1 a 2\nacidose de AG alto pura", (220, 220, 210)),
             (2, 3, "> 2\n+ alcalose metabólica\n(vômitos)", (245, 170, 90))]
    for a, b, rot, cor in zonas:
        t.ret((px(a), y, px(b) - px(a), 90), cor, TINTA)
        t.txt(rot, (px(a) + px(b)) / 2, y + 45, TINTA, 14, "mm", True, larg=px(b) - px(a) - 10)
    for v in range(4):
        t.txt(str(v), px(v), y + 96, TINTA, 14, "tm", True)
    t.txt("O HCO₃⁻ caiu MAIS que o AG subiu", px(0.5), y - 10, VERDE, 13, "bm", True)
    t.txt("O HCO₃⁻ caiu MENOS que o AG subiu", px(2.5), y - 10, LARANJA, 13, "bm", True)
    t.txt("Ex.: CAD com vômitos: AG 27, HCO₃⁻ 18 → (27 − 12) ÷ (24 − 18) = 15 ÷ 6 = 2,5 → alcalose metabólica junto.",
          BW // 2, 260, TINTA, 15, "tm", True, larg=820)
    return t.s


def gap_osmolar():
    t = Tela(330, "Ânion gap × gap osmolar: onde estão os álcoois")
    x0, y0, cw, ch = 260, 80, 300, 90
    t.txt("Gap osmolar ALTO (> 10)", x0 + cw // 2, y0 - 8, ROXO, 15, "bm", True)
    t.txt("Gap osmolar normal", x0 + cw + cw // 2, y0 - 8, CINZA, 15, "bm", True)
    t.txt("AG ALTO", x0 - 16, y0 + ch // 2, VERMELHO, 16, "mr", True)
    t.txt("AG normal", x0 - 16, y0 + ch + ch // 2, CINZA, 16, "mr", True)
    cel = [("METANOL, ETILENOGLICOL", (255, 210, 210)), ("lactato, cetoacidose, uremia, salicilato", (255, 240, 225)),
           ("etanol, isopropanol (sem acidose importante)", (235, 225, 250)), ("—", (245, 245, 240))]
    for i, (s, cor) in enumerate(cel):
        c, l = i % 2, i // 2
        r = (x0 + c * cw, y0 + l * ch, cw, ch)
        t.ret(r, cor, (200, 180, 150))
        t.txt(s, r[0] + cw // 2, r[1] + ch // 2, TINTA, 15, "mm", i == 0, larg=cw - 20)
    t.txt("Osm calculada = 2 × Na⁺ + glicose/18 + ureia/6 · gap = medida − calculada",
          BW // 2, 275, TINTA, 15, "tm", True, larg=820)
    return t.s


def ag_urinario():
    t = Tela(400, "Ânion gap urinário = Na⁺ + K⁺ − Cl⁻ (o NH₄⁺ sai junto com o Cl⁻)")
    base, esc = 340, 1.4
    t.txt("DIARREIA: o rim excreta bem NH₄⁺", 230, 60, VERDE, 15, "tm", True)
    _gamble(t, 110, base, esc, [(80, "Na⁺ + K⁺\n80", (245, 205, 120)), (80, "NH₄⁺\n(não medido)", (215, 215, 215))], 110)
    _gamble(t, 240, base, esc, [(160, "Cl⁻ 160", (150, 200, 150))], 110)
    t.txt("80 − 160 = NEGATIVO", 230, base + 10, VERDE, 15, "tm", True)
    t.txt("ATR distal / tipo 4: pouco NH₄⁺", 670, 60, VERMELHO, 15, "tm", True)
    _gamble(t, 550, base, esc, [(90, "Na⁺ + K⁺\n90", (245, 205, 120)), (10, "", (215, 215, 215))], 110)
    _gamble(t, 680, base, esc, [(70, "Cl⁻ 70", (150, 200, 150))], 110)
    t.txt("90 − 70 = POSITIVO", 670, base + 10, VERMELHO, 15, "tm", True)
    t.txt("NEGativo = intestiNO (\"neGUTivo\")", 450, 100, ROXO, 15, "tm", True, larg=200)
    return t.s


def atr():
    t = Tela(470, "Onde falha cada acidose tubular renal")
    pygame.draw.circle(t.s, (240, 150, 150), (90, 130), 40)
    pygame.draw.circle(t.s, TINTA, (90, 130), 40, 2)
    t.txt("glomérulo", 90, 176, CINZA, 13, "tm")
    pts = [(130, 130), (250, 130), (290, 140), (310, 170), (310, 230), (350, 260), (390, 230), (390, 170),
           (420, 135), (560, 130), (620, 140), (640, 170), (640, 270)]
    pygame.draw.lines(t.s, (200, 170, 130), False, pts, 22)
    pygame.draw.lines(t.s, (255, 240, 220), False, pts, 14)
    t.caixa((140, 50, 210, 60), "TIPO 2 (proximal): perde HCO₃⁻", (255, 236, 220), LARANJA, tam=13, bold=True)
    t.seta((230, 110), (230, 122), LARANJA, 3)
    t.caixa((430, 46, 210, 64), "TIPO 1 (distal): não secreta H⁺", (255, 228, 228), VERMELHO, tam=13, bold=True)
    t.seta((530, 110), (530, 122), VERMELHO, 3)
    t.caixa((672, 200, 210, 64), "TIPO 4 (coletor): falta aldosterona", (225, 235, 255), AZUL, tam=13, bold=True)
    t.seta((670, 232), (654, 232), AZUL, 3)
    tab = [("tipo", "K⁺", "pH da urina", "pista"), ("1", "↓", "> 5,5", "cálculos, nefrocalcinose"),
           ("2", "↓", "< 5,5*", "Fanconi, mieloma, tenofovir"), ("4", "↑", "< 5,5", "diabetes, IECA, espironolactona")]
    _tabela(t, (150, 292), (60, 50, 140, 330), tab, 32)
    t.txt("* na tipo 2 o pH urinário só fica alto enquanto o HCO₃⁻ sérico está acima do limiar de reabsorção.",
          BW // 2, 432, CINZA, 12, "tm", larg=840)
    return t.s


def _tabela(t, origem, larguras, linhas, alt):
    x0, y = origem
    for i, ln in enumerate(linhas):
        x = x0
        for j, (cel, w) in enumerate(zip(ln, larguras)):
            cor = CINZA if i == 0 else (VERMELHO if cel == "↓" else AZUL if cel == "↑" else TINTA)
            t.txt(cel, x + 2, y + alt // 2, cor, 13, "ml", i == 0 or j < 2, larg=w)
            x += w + 6
        if i == 0:
            t.linha((x0, y + alt - 2), (x, y + alt - 2), CINZA, 1)
        y += alt


def alcalose():
    t = Tela(340, "Alcalose metabólica: o cloro urinário separa")
    t.caixa((330, 50, 240, 50), "ALCALOSE METABÓLICA", (255, 246, 205), (200, 170, 80), tam=15, bold=True)
    t.caixa((60, 140, 300, 56), "Cl⁻ urinário < 20 → RESPONDE A SORO", (220, 240, 220), VERDE, tam=14, bold=True)
    t.caixa((540, 140, 300, 56), "Cl⁻ urinário ≥ 20 → não responde", (255, 228, 228), VERMELHO, tam=14, bold=True)
    t.seta((400, 100), (210, 136), TINTA, 2)
    t.seta((500, 100), (690, 136), TINTA, 2)
    t.caixa((60, 225, 300, 80), "vômito, sonda nasogástrica, diurético usado antes (já suspenso)", PAPEL, VERDE, tam=13)
    t.seta((210, 196), (210, 222), VERDE, 2)
    t.caixa((470, 225, 200, 80), "COM hipertensão: hiperaldosteronismo, Cushing", PAPEL, VERMELHO, tam=13)
    t.caixa((680, 225, 200, 80), "SEM hipertensão: diurético em uso, Bartter, Gitelman", PAPEL, VERMELHO, tam=13)
    t.seta((640, 196), (570, 222), VERMELHO, 2)
    t.seta((740, 196), (780, 222), VERMELHO, 2)
    t.txt("Use o Cl⁻, não o Na⁺: no vômito o Na⁺ urinário sai arrastado pelo HCO₃⁻.", BW // 2, 318, ROXO, 14, "tm", True)
    return t.s


def asma_paco2():
    t = Tela(380, "Crise de asma: PaCO₂ 'normal' é sinal de cansaço")
    e = Eixos(t, (110, 60, 500, 250), (0, 10), (15, 70), "tempo de crise →", "PaCO₂ (mmHg)",
              xt=(), yt=(20, 30, 40, 50, 60, 70))
    e.faixa_y(35, 45, (90, 190, 100, 50))
    pts = [(0, 40), (1, 33), (2, 29), (3, 28), (4, 30), (5, 34), (6, 38), (7, 42), (8, 50), (9, 58), (10, 65)]
    import bisect
    xs = [p[0] for p in pts]

    def f(x):
        i = max(1, min(len(xs) - 1, bisect.bisect_left(xs, x)))
        (a, ya), (b, yb) = pts[i - 1], pts[i]
        u = (x - a) / (b - a)
        u = u * u * (3 - 2 * u)
        return ya + (yb - ya) * u
    t.curva(e.func(f, 0, 10, 200), AZUL, 4)
    e.ponto(2.5, f(2.5), AZUL, "início: hiperventila, PaCO₂ baixa (esperado)", -4, 14, "tl", False)
    e.ponto(7, 42, LARANJA, "volta ao 'normal' = FADIGA", -10, -10, "br", False)
    e.ponto(9.5, f(9.5), VERMELHO, "hipercapnia", -10, 0, "mr", False)
    t.txt("Asmático em crise deveria estar com PaCO₂ baixa. PaCO₂ de 40–45 após horas de crise = insuficiência "
          "respiratória iminente → suporte ventilatório.", 760, 80, VERMELHO, 15, "tm", True, larg=250)
    return t.s


def cad():
    t = Tela(340, "Cetoacidose: a ordem do tratamento (consenso 2024)")
    passos = [("1 · VOLUME", "cristaloide na 1ª hora", (220, 235, 255), AZUL),
              ("2 · POTÁSSIO", "K⁺ < 3,5: repor e ESPERAR a insulina\n3,5–5: repor junto\n> 5: não repor, dosar", (255, 236, 220), LARANJA),
              ("3 · INSULINA", "IV contínua só com K⁺ > 3,5", (240, 230, 255), ROXO),
              ("4 · GLICOSE", "glicemia < 250: soro glicosado e manter a insulina", (220, 240, 220), VERDE)]
    for i, (tit, sub, cor, borda) in enumerate(passos):
        x = 20 + i * 220
        t.ret((x, 60, 200, 170), cor, borda, 12)
        t.txt(tit, x + 100, 74, borda, 16, "tm", True)
        t.txt(sub, x + 100, 110, TINTA, 14, "tm", larg=184)
        if i < 3:
            t.seta((x + 202, 145), (x + 218, 145), TINTA, 3, 8)
    t.txt("Resolução: β-OHB < 0,6 mmol/L + pH venoso ≥ 7,3 ou HCO₃⁻ ≥ 18. Bicarbonato só se pH < 7,0.",
          BW // 2, 255, TINTA, 15, "tm", True, larg=840)
    t.txt("Diagnóstico: glicemia ≥ 200 (ou DM conhecido) + β-OHB ≥ 3 + pH < 7,3 ou HCO₃⁻ < 18.",
          BW // 2, 300, CINZA, 14, "tm", larg=840)
    return t.s


FIGURAS = {
    "ph_h": ph_h, "tampao": tampao, "bicarbonato": bicarbonato, "carga_acida": carga_acida, "defesas": defesas,
    "ventilacao_co2": ventilacao_co2, "rim_proximal": rim_proximal, "rim_novo": rim_novo, "aldosterona": aldosterona,
    "curva_o2": curva_o2, "curva_desvio": curva_desvio, "conteudo_o2": conteudo_o2, "cascata_o2": cascata_o2,
    "hipoxemia": hipoxemia, "pf": pf, "referencias": referencias, "erros_coleta": erros_coleta, "roteiro": roteiro,
    "acidemia": acidemia, "primario": primario, "winter": winter, "comp_respiratoria": comp_respiratoria,
    "gamble_normal": gamble_normal, "gamble_comparar": gamble_comparar, "delta_delta": delta_delta,
    "gap_osmolar": gap_osmolar, "ag_urinario": ag_urinario, "atr": atr, "alcalose": alcalose,
    "asma_paco2": asma_paco2, "cad": cad,
}


def figura(nome, largura=None):
    """Superfície da figura (cache por nome e largura); None se o nome não existe. Nome com ':' é figura paramétrica
    ("base:arg1:arg2…", argumentos em texto), usada pelos casos gerados do Treino."""
    from .figuras_vm import FIGURAS_VM, PARAMETRICAS
    FIGURAS.update(FIGURAS_VM)
    base, *args = nome.split(":")
    if nome not in FIGURAS and not (args and base in PARAMETRICAS):
        return None
    chave = (nome, largura)
    if chave not in _CACHE:
        if not pygame.font.get_init():
            pygame.font.init()
        s = PARAMETRICAS[base](*args) if args else FIGURAS[nome]()
        if largura and largura < BW:
            s = pygame.transform.smoothscale(s, (largura, round(s.get_height() * largura / BW)))
        _CACHE[chave] = s
    return _CACHE[chave]
