"""App, entrada, quiz e menus."""
import math
import os
import random
import re
import threading
import time

import pygame

from . import art, data, edicao
from .audio import MUSICA_FIM, Audio
from .controle import PADEVENT, ACOES as ACOES_PAD, NOMES as NOMES_PAD, Pad
from .game import Jogo, LW, LH
from .toque import TOQUE, Toque, ativo as toque_ativo

W, H = LW * 4, LH * 4              # em pé: 720 x (1280…1536), acompanhando o formato do celular
RETRATO = edicao.RETRATO
MX = 16 if RETRATO else 130          # margem lateral do painel dos menus
MY = 196 if RETRATO else 140         # topo do painel (em pé, o subtítulo ocupa duas linhas)


def cortar(txt, f, largura):
    """Corta o texto com reticências para caber na largura (px)."""
    if f.size(txt)[0] <= largura:
        return txt
    while txt and f.size(txt + "…")[0] > largura:
        txt = txt[:-1]
    return txt + "…"
# DejaVu vai junto com o jogo (ilha/fontes); a do sistema fica de reserva
_SIS = "/usr/share/fonts/truetype/dejavu"
FONTE, FONTE_B = [os.path.join(edicao.FONTES, n) if os.path.exists(os.path.join(edicao.FONTES, n))
                  else os.path.join(_SIS, n) for n in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")]

TINTA = (50, 36, 40)
PAPEL = (255, 250, 236)
VERDE = (90, 190, 100)
VERMELHO = (225, 90, 90)
AMARELO = (255, 220, 90)

TECLAS = {
    "esq": (pygame.K_LEFT, pygame.K_a), "dir": (pygame.K_RIGHT, pygame.K_d),
    "cima": (pygame.K_UP, pygame.K_w), "baixo": (pygame.K_DOWN, pygame.K_s),
    "pulo": (pygame.K_z, pygame.K_SPACE, pygame.K_k), "lingua": (pygame.K_x, pygame.K_j),
    "ovo": (pygame.K_c, pygame.K_l, pygame.K_LSHIFT, pygame.K_RSHIFT), "pausa": (pygame.K_ESCAPE, pygame.K_p, pygame.K_AC_BACK),
    "ok": (pygame.K_RETURN, pygame.K_KP_ENTER),
    "voltar": (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_AC_BACK),   # AC_BACK = voltar do Android
}


def fonte(tam, bold=False):
    try:
        return pygame.font.Font(FONTE_B if bold else FONTE, tam)
    except Exception:
        return pygame.font.Font(None, int(tam * 1.4))


def _dicas_pad():
    """Dicas de rodapé com botões de controle (Steam/Steam Deck); a Ilha do Vestibulando é de teclado e mouse."""
    return edicao.STEAM and not edicao.VESTIBULANDO


ROTULOS_COMENT = {"Por quê:": (30, 120, 40), "E as outras:": (170, 60, 40), "Para fixar:": (120, 70, 160)}


def quebrar(texto, f, largura):
    linhas = []
    for par in texto.split("\n"):
        atual = ""
        for palavra in par.split(" "):
            teste = (atual + " " + palavra).strip()
            if f.size(teste)[0] <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                while f.size(palavra)[0] > largura and len(palavra) > 1:  # palavra gigante (URL)
                    corte = len(palavra)
                    while corte > 1 and f.size(palavra[:corte])[0] > largura:
                        corte -= 1
                    linhas.append(palavra[:corte])
                    palavra = palavra[corte:]
                atual = palavra
        linhas.append(atual)
    return linhas


def sombra(tela, txt, f, cor, pos, centro=False, sombra_cor=(40, 30, 30)):
    s = f.render(txt, True, cor)
    o = f.render(txt, True, sombra_cor)
    x, y = pos
    if centro:
        x -= s.get_width() // 2
    tela.blit(o, (x + 2, y + 2))
    tela.blit(s, (x, y))
    return s.get_width()


def painel(tela, rect, cor=PAPEL, borda=TINTA, raio=16):
    """Janela estilo 16-bit: desenhada em 1/4 da resolução e ampliada sem
    suavização (moldura com contorno, brilho e sombra de 1 'pixel')."""
    r = pygame.Rect(rect)
    w, h = max(4, r.w // 4), max(4, r.h // 4)
    s = pygame.Surface((w + 1, h + 1), pygame.SRCALPHA)
    s.fill((0, 0, 0, 90), (1, 1, w, h))
    s.fill(borda, (0, 0, w, h))
    s.fill((255, 255, 255), (1, 1, w - 2, h - 2))
    s.fill(art.mix(cor[:3], borda, 0.35), (2, 2, w - 3, h - 3))
    s.fill(cor[:3], (2, 2, w - 4, h - 4))
    for c in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        s.set_at(c, (0, 0, 0, 0))
    tela.blit(pygame.transform.scale(s, ((w + 1) * 4, (h + 1) * 4)), r.topleft)


def carteira_txt(save):
    """Resumo da carteira para os menus principais."""
    c = save.carteira
    pct = f" ({round(100 * c['acertos_total'] / c['questoes_total'])}% de acerto)" if c["questoes_total"] else ""
    return (f"Moedas: {c['moedas']:,} · Créditos de questão: {c['creditos']:,} · "
            f"Questões feitas: {c['questoes_total']:,}{pct}").replace(",", ".")


def titulo_px(tela, txt, cor, cx, y, escala=4):
    t = art.texto_px(txt.upper(), cor, escala=escala)
    larg = W - (2 * 84 if RETRATO else 40)      # em pé: deixa o canto livre para o botão Voltar
    while t.get_width() > larg and escala > 2:
        escala -= 1
        t = art.texto_px(txt.upper(), cor, escala=escala)
        y += 4
    tela.blit(t, (cx - t.get_width() // 2, y))


def cor_arcoiris(h, s=0.9, v=0.95):
    """Cor do arco-íris pelo matiz em graus (o Mundo do Dia usa para letras vibrantes)."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def titulo_arcoiris(tela, txt, cx, y, t, escala=4):
    """Título em pixel com cada letra numa cor do arco-íris, que corre e ondula com o tempo."""
    txt = txt.upper()
    larg = W - (2 * 84 if RETRATO else 40)
    while len(txt) * 6 * escala > larg and escala > 2:
        escala -= 1
        y += 4
    x0 = cx - (len(txt) * 6 * escala + 2) // 2
    for i, ch in enumerate(txt):
        if ch != " ":
            h = ((t * 5 + i * 30) // 15) * 15            # matiz em degraus: o cache de texto_px não explode
            dy = int(math.sin(t / 9 + i * 0.55) * 3)
            tela.blit(art.texto_px(ch, cor_arcoiris(h), escala=escala), (x0 + i * 6 * escala, y + dy))


def texto_arcoiris(fonte, txt, t, sombra_cor=(60, 40, 60)):
    """Texto comum com cada letra numa cor do arco-íris e sombra escura (legível no painel claro)."""
    letras = [(ch, fonte.render(ch, True, cor_arcoiris(t * 5 + i * 24, 0.95, 0.88))) for i, ch in enumerate(txt)]
    w = sum(s.get_width() for _, s in letras) + 2
    h = fonte.get_height() + 2
    sup = pygame.Surface((max(1, w), h), pygame.SRCALPHA)
    x = 0
    for ch, s in letras:
        sup.blit(fonte.render(ch, True, sombra_cor), (x + 2, 2))
        sup.blit(s, (x, 0))
        x += s.get_width()
    return sup


# ------------------------------------------------------------------ entrada

class Entrada:
    def __init__(self, pad=None, toque=None):
        self.apertados = set()
        self.atual = None      # ações do evento sendo despachado (None = do frame todo)
        self.pad = pad
        self.toque = toque

    def iniciar_frame(self):
        self.apertados.clear()

    def processar(self, e):
        antes = set(self.apertados)
        self.apertados = set()
        self._mapear(e)
        acoes = self.apertados
        self.apertados = antes | acoes
        return acoes

    def _mapear(self, e):
        if e.type == pygame.KEYDOWN:
            for acao, ks in TECLAS.items():
                if e.key in ks:
                    self.apertados.add(acao)
        elif e.type == PADEVENT:
            self.apertados.update(ACOES_PAD.get(e.botao, ()))
        elif e.type == TOQUE:
            self.apertados.update(e.acoes)

    def foi(self, acao):
        return acao in (self.apertados if self.atual is None else self.atual)

    def seg(self, acao):
        k = pygame.key.get_pressed()
        if any(k[c] for c in TECLAS.get(acao, ())):
            return True
        return bool(self.pad and self.pad.segurando(acao)) or bool(self.toque and self.toque.segurando(acao))


def eh_pad(e, *botoes):
    return e.type == PADEVENT and (not botoes or e.botao in botoes)


# ------------------------------------------------------------------ cenário de menu

class Cenario:
    """Ilha animada de fundo dos menus."""

    def __init__(self, idx=0):
        self.trocar(idx)
        self.t = 0

    def trocar(self, idx):
        self.idx = idx
        pal = art.paleta(idx)
        self.ceu = art.ceu(pal, LW, LH)
        self.camadas = art.fundo(pal, LW, LH, idx * 7 + 3)
        self.s = pygame.Surface((LW, LH))
        from .level import Nivel
        n = type("N", (), {})()
        n.w, n.h, n.seed = 3, 2, 1
        n.tiles = [[1, 1, 1], [1, 1, 1]]
        self.tile_chao = art.render_nivel(n, pal).subsurface((16, 0, 16, 32)).copy()

    def draw(self, tela):
        self.t += 1
        s = self.s
        s.blit(self.ceu, (0, 0))
        for i in range(4):
            art.nuvem(s, (i * 95 - self.t * 0.1 * (1 + i % 2)) % (LW + 60) - 50, 10 + (i * 19) % 45, 0.7 + (i % 3) * 0.15)
        for i, c in enumerate(self.camadas):
            ox = -int(self.t * (0.1, 0.2, 0.35)[i]) % LW
            s.blit(c, (ox - LW, 0))
            s.blit(c, (ox, 0))
        chao = LH - 14
        for x in range(0, LW, 16):
            s.blit(self.tile_chao, (x, chao))
        x = (self.t * 0.6) % (LW + 60) - 30
        s.blit(art.heroi("andar", (self.t // 8) % 4, True, 1), (int(x) - 20, chao - 46))
        from . import pets
        s.blit(pets.sprite("gato_branco", "vermelha", "nenhum", "andar", self.t // 5), (int(x) - 44, chao - 17))
        bx = (x + 120) % (LW + 60) - 30
        s.blit(art.bicho_questao(self.t // 14, (250, 170, 90), virado=-1), (int(bx), chao - 26 - int(abs(math.sin(self.t * 0.1)) * 3)))
        tela.blit(pygame.transform.scale(s, (W, H)), (0, 0))


def pets_pata():
    from . import pets
    return pets.pata()


# ------------------------------------------------------------------ estados base

class Estado:
    overlay = False

    def __init__(self, app):
        self.app = app

    def evento(self, e, inp):
        pass

    def update(self, inp):
        pass

    def draw(self, tela):
        pass

    def ao_voltar(self):
        pass


class Menu(Estado):
    """Lista rolável genérica. itens: dicts {label, info, acao, cor, desab} ou {secao: "TÍTULO"} — um cabeçalho
    baixo, que não se seleciona, para agrupar os itens."""
    ALT_SECAO = 40

    def __init__(self, app, titulo, itens, subtitulo="", ao_voltar=None, cenario=None):
        super().__init__(app)
        self.titulo, self.subtitulo = titulo, subtitulo
        self.itens = itens
        self.sel = 0
        self.topo = 0
        self.cb_voltar = ao_voltar
        self.cenario = cenario
        self.linha_h = 72 if RETRATO else 58          # em pé: linhas mais altas, para o dedo
        self.passo_rolagem = self.linha_h
        self.vis = (H - MY - 110) // self.linha_h if RETRATO else 9
        self._pular_desab(1)
        self._t = 0                      # quadros desde que abriu (itens entram em cascata)
        self._ysel = float(self.sel)     # faixa de seleção desliza até o item escolhido

    def _inativo(self, i):
        it = self.itens[i]
        return bool(it.get("desab") or it.get("secao"))

    def _alt(self, i):
        return self.ALT_SECAO if self.itens[i].get("secao") else self.linha_h

    def _visiveis(self, topo=None):
        """[(índice, y)] dos itens que cabem a partir do topo (cabeçalhos são mais baixos)."""
        topo = self.topo if topo is None else topo
        out, y, lim = [], 0, self.linha_h * self.vis
        for i in range(topo, len(self.itens)):
            if y + self._alt(i) > lim:
                break
            out.append((i, MY + 10 + y))
            y += self._alt(i)
        return out

    def _topo_max(self):
        resto, t = 0, len(self.itens)
        while t > 0 and resto + self._alt(t - 1) <= self.linha_h * self.vis:
            t -= 1
            resto += self._alt(t)
        return t

    def _pular_desab(self, d):
        for _ in range(len(self.itens)):
            if not self._inativo(self.sel):
                return
            self.sel = (self.sel + d) % len(self.itens)

    def evento(self, e, inp):
        n = len(self.itens)
        if not n:
            if inp.foi("voltar"):
                self.app.pop()
            return
        if inp.foi("cima") or inp.foi("baixo"):
            self._rolou = False
            d = -1 if inp.foi("cima") else 1
            self.sel = (self.sel + d) % n
            self._pular_desab(d)
            self.app.audio.tocar("menu")
        elif (e.type == pygame.KEYDOWN and e.key in (pygame.K_PAGEDOWN, pygame.K_PAGEUP)) or inp.foi("pgdn") or inp.foi("pgup"):
            desce = inp.foi("pgdn") or (e.type == pygame.KEYDOWN and e.key == pygame.K_PAGEDOWN)
            self.sel = max(0, min(n - 1, self.sel + (self.vis if desce else -self.vis)))
            self._pular_desab(1)
        elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self._ativar()
        elif inp.foi("voltar"):
            if self.cb_voltar:
                self.cb_voltar()
            else:
                self.app.pop()
        elif e.type == pygame.MOUSEWHEEL:
            self.topo = max(0, min(self._topo_max(), self.topo - e.y))
            vis = [i for i, _ in self._visiveis() if not self._inativo(i)]
            if vis and self.sel not in vis:               # a seleção acompanha a rolagem (senão o update desfaz)
                self.sel = vis[0] if self.sel < vis[0] else vis[-1]
                self._ysel = float(self.sel)
            self._rolou = True
        elif e.type == pygame.MOUSEMOTION or e.type == pygame.MOUSEBUTTONDOWN:
            i = self._item_em(e.pos)
            if i is not None and not self._inativo(i):
                self.sel = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._ativar()

    def _item_em(self, pos):
        x, y = pos
        if not MX + 10 <= x <= W - MX - 10:
            return None
        for i, yi in self._visiveis():
            if yi <= y < yi + self._alt(i):
                return i
        return None

    def _ativar(self):
        it = self.itens[self.sel]
        if self._inativo(self.sel) or not it.get("acao"):
            return
        self.app.audio.tocar("ovo")
        it["acao"]()

    def update(self, inp):
        if self.sel < self.topo:
            self.topo = self.sel
        else:
            while self.topo < self.sel and self.sel not in [i for i, _ in self._visiveis()]:
                self.topo += 1
        if self.topo and self.topo == self.sel and self.itens[self.sel - 1].get("secao") and not getattr(self, "_rolou", False):
            self.topo -= 1                                # mostra o cabeçalho do grupo junto (navegando por tecla)
        self._t += 1
        self._ysel += (self.sel - self._ysel) * 0.35
        if abs(self.sel - self._ysel) < 0.02:
            self._ysel = float(self.sel)

    def draw(self, tela):
        (self.cenario or self.app.cenario).draw(tela)
        f = self.app.f
        if getattr(self, "arcoiris", False):
            titulo_arcoiris(tela, self.titulo[:38], W // 2, 26, self._t)
        else:
            titulo_px(tela, self.titulo[:38], (255, 255, 255), W // 2, 26)
        if self.subtitulo and RETRATO:
            for i, l in enumerate(quebrar(self.subtitulo, f["peq"], W - 40)[:3]):
                sombra(tela, l, f["peq"], (255, 255, 240), (W // 2, 96 + 26 * i), centro=True)
        elif self.subtitulo:
            sombra(tela, self.subtitulo, f["peq"], (255, 255, 240), (W // 2, 88 if getattr(self, "barra", None) else 96),
                   centro=True)
        if getattr(self, "barra", None):
            self._desenhar_barra(tela, f)
        vis = self._visiveis()
        alt = (sum(self._alt(i) for i, _ in vis) if vis else self.linha_h) if RETRATO else self.linha_h * self.vis
        painel(tela, (MX, MY, W - 2 * MX, alt + 20), (255, 252, 240, ))   # em pé: painel do tamanho da lista
        ys = dict(vis)
        a, b = int(self._ysel), min(len(self.itens) - 1, int(self._ysel) + 1)   # faixa de seleção (posição suave)
        if a in ys and self.itens:
            yb = ys.get(b, ys[a] + self._alt(a))
            ysel = ys[a] + (yb - ys[a]) * (self._ysel - a)
            r = pygame.Rect(MX + 15, int(ysel), W - 2 * MX - 30, self.linha_h - 6)
            clip = tela.get_clip()
            tela.set_clip(pygame.Rect(MX + 10, MY + 6, W - 2 * MX - 20, self.linha_h * self.vis + 8))
            pygame.draw.rect(tela, AMARELO, r, border_radius=12)
            pygame.draw.rect(tela, TINTA, r, 2, border_radius=12)
            bob = int(math.sin(self._t / 6) * 2)
            from . import pets
            tela.blit(pygame.transform.scale(pets.pata(), (20, 24)), (r.x + 10, r.y + 13 + bob))
            tela.set_clip(clip)
        for k, (i, y) in enumerate(vis):
            it = self.itens[i]
            entra = max(0, k * 2 + 8 - self._t)               # cascata na abertura
            if it.get("secao"):
                t = f["peq"].render(it["secao"].upper(), True, (150, 110, 70))
                x = MX + 30 + entra * entra * 6
                tela.blit(t, (x, y + (self.ALT_SECAO - t.get_height()) // 2 + 2))
                yl = y + self.ALT_SECAO // 2 + 2
                pygame.draw.line(tela, (225, 205, 180), (x + t.get_width() + 12, yl), (W - MX - 30, yl), 2)
                continue
            r = pygame.Rect(MX + 15 + entra * entra * 6, y, W - 2 * MX - 30, self.linha_h - 6)
            cor = (150, 140, 140) if it.get("desab") else TINTA
            if it.get("cor"):
                pygame.draw.circle(tela, it["cor"], (r.x + 52, r.centery), 12)
                pygame.draw.circle(tela, TINTA, (r.x + 52, r.centery), 12, 2)
            lim = 52 if it.get("dir") else 62
            rot = it["label"] if len(it["label"]) <= lim else it["label"][:lim - 1] + "…"
            t_dir = f["med"].render(it["dir"], True, cor) if it.get("dir") else None
            larg = r.w - 76 - (t_dir.get_width() + 24 if t_dir else 14)
            dy = 6 if RETRATO else 0
            if it.get("arcoiris") and not it.get("desab"):
                tela.blit(texto_arcoiris(f["med"], cortar(rot, f["med"], larg - 8), self._t), (r.x + 76, r.y + 3 + dy))
            else:
                tela.blit(f["med"].render(cortar(rot, f["med"], larg), True, cor), (r.x + 76, r.y + 4 + dy))
            if it.get("info"):
                tela.blit(f["peq"].render(cortar(it["info"][:100], f["peq"], larg), True, (110, 95, 95)),
                          (r.x + 78, r.y + 30 + dy))
            if t_dir:
                t = t_dir
                tela.blit(t, (r.right - t.get_width() - 14, r.y + 12))
            if it.get("prog") is not None and not it.get("desab"):      # mini barra de progresso do item
                bx, bw, by = r.x + 78, larg - 4, r.bottom + 1
                pygame.draw.rect(tela, (225, 212, 195), (bx, by, bw, 3), border_radius=1)
                if it["prog"] > 0:
                    pygame.draw.rect(tela, VERDE if it["prog"] >= 1 else it.get("cor", VERDE),
                                     (bx, by, max(3, int(bw * min(1, it["prog"]))), 3), border_radius=1)
        n = len(self.itens)
        if self._topo_max() > 0:
            h = self.linha_h * self.vis
            barra = max(30, h * len(vis) // n)
            y = MY + 10 + (h - barra) * min(self.topo, self._topo_max()) // max(1, self._topo_max())
            pygame.draw.rect(tela, (200, 180, 160), (W - MX - 16, y, 8, barra), border_radius=4)
        sombra(tela, "Toque para escolher · arraste para rolar" if edicao.ANDROID else
               "↑↓ escolher · A / Enter confirma · B / Esc volta" if _dicas_pad() else
               "↑↓ escolher · Enter jogar · Esc voltar · M som · F11 tela cheia",
               f["peq"], (255, 255, 255), (W // 2, H - 40), centro=True)


def _barra_progresso(tela, f, rect, frac, vistas, texto, t=0):
    """Barra grossa de "quanto falta": verde = dominadas, amarelo claro = já vistas, creme = falta; texto por cima."""
    x, y, w, h = rect
    pygame.draw.rect(tela, (255, 250, 236), rect, border_radius=h // 2)
    if vistas > frac:
        pygame.draw.rect(tela, (250, 222, 140), (x, y, max(h, int(w * min(1, vistas))), h), border_radius=h // 2)
    if frac > 0:
        cor = (90, 200, 110) if frac < 1 else (120, 220, 90)
        pygame.draw.rect(tela, cor, (x, y, max(h, int(w * min(1, frac))), h), border_radius=h // 2)
        brilho = int((t * 3) % max(1, int(w * frac)))           # reflexo correndo na parte já feita
        pygame.draw.line(tela, (200, 255, 210), (x + brilho, y + 3), (x + min(int(w * frac) - 2, brilho + 18), y + 3), 2)
    pygame.draw.rect(tela, TINTA, rect, 2, border_radius=h // 2)
    pct = f"{round(frac * 100)}%"
    sombra(tela, f"{texto}  ·  {pct}", f["peq"], (255, 255, 255), (x + w // 2, y + (h - f["peq"].get_height()) // 2),
           centro=True)


def _menu_barra(self, tela, f):
    b = self.barra
    y = MY - 34 if RETRATO else 119
    _barra_progresso(tela, f, (MX + 10, y, W - 2 * MX - 20, 20 if not RETRATO else 26), b["frac"], b.get("vistas", 0), b["texto"], self._t)


Menu._desenhar_barra = _menu_barra


class Mensagem(Estado):
    def __init__(self, app, titulo, texto, ao_ok=None):
        super().__init__(app)
        self.titulo, self.texto, self.ao_ok = titulo, texto, ao_ok

    def evento(self, e, inp):
        if inp.foi("ok") or inp.foi("voltar") or (e.type == pygame.MOUSEBUTTONDOWN):
            self.app.pop()
            if self.ao_ok:
                self.ao_ok()

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        mx = 24 if RETRATO else 190
        painel(tela, (mx, 120, W - 2 * mx, H - 240))
        titulo_px(tela, self.titulo, AMARELO, W // 2, 136, 3)
        y = 210
        fonte_txt, passo = f["med"], 32
        linhas = quebrar(self.texto, fonte_txt, W - 2 * mx - 80)
        if len(linhas) * passo > H - 340:            # texto longo (em pé): letra menor
            fonte_txt, passo = f["peq"], 24
            linhas = quebrar(self.texto, fonte_txt, W - 2 * mx - 80)
        for linha in linhas:
            tela.blit(fonte_txt.render(linha, True, TINTA), (mx + 40, y))
            y += passo
        sombra(tela, "Toque para continuar" if edicao.ANDROID else "A / Enter para continuar" if _dicas_pad() else "Enter para continuar", f["peq"], (255, 255, 255), (W // 2, H - 80), centro=True)


class Carregando(Estado):
    def __init__(self, app, texto, tarefa, ao_fim):
        super().__init__(app)
        self.texto = texto
        self.res = None
        self.erro = None
        self.ao_fim = ao_fim

        def rodar():
            try:
                self.res = tarefa()
            except Exception as ex:
                self.erro = ex
            self.pronto = True
        self.pronto = False
        threading.Thread(target=rodar, daemon=True).start()

    def update(self, inp):
        if self.pronto:
            self.app.pop()
            self.ao_fim(self.res, self.erro)

    def draw(self, tela):
        self.app.cenario.draw(tela)
        pts = "." * (1 + (pygame.time.get_ticks() // 300) % 3)
        sombra(tela, self.texto + pts, self.app.f["grande"], (255, 255, 255), (W // 2, H // 2 - 40), centro=True)


class EntradaTexto(Estado):
    def __init__(self, app, titulo, valor, ao_ok, secreto=False, dica=""):
        super().__init__(app)
        self.titulo, self.valor, self.ao_ok = titulo, valor, ao_ok
        self.secreto, self.dica = secreto, dica       # secreto: senha (mostra bolinhas)
        self.r_caixa = self.r_ok = pygame.Rect(0, 0, 0, 0)
        pygame.key.start_text_input()

    def _confirmar(self):
        if self.valor.strip():
            pygame.key.stop_text_input()
            self.app.pop()
            self.ao_ok(self.valor.strip())

    def evento(self, e, inp):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:        # toque: OK confirma; caixa reabre o teclado
            if self.r_ok.collidepoint(e.pos):
                return self._confirmar()
            if self.r_caixa.collidepoint(e.pos):
                pygame.key.start_text_input()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_AC_BACK:
            pygame.key.stop_text_input()
            self.app.pop()
            return
        if eh_pad(e, "A", "START") and self.valor.strip():
            pygame.key.stop_text_input()
            self.app.pop()
            self.ao_ok(self.valor.strip())
            return
        if eh_pad(e, "B", "SELECT"):
            pygame.key.stop_text_input()
            self.app.pop()
            return
        if e.type == pygame.TEXTINPUT:
            if len(self.valor) < 30:
                self.valor += e.text
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                self.valor = self.valor[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.valor.strip():
                pygame.key.stop_text_input()
                self.app.pop()
                self.ao_ok(self.valor.strip())
            elif e.key == pygame.K_ESCAPE:
                pygame.key.stop_text_input()
                self.app.pop()

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        mx = 30 if RETRATO else 290
        painel(tela, (mx, 240, W - 2 * mx, 300 if edicao.ANDROID else 220))
        sombra(tela, self.titulo, f["grande"], AMARELO, (W // 2, 260), centro=True)
        if self.dica:
            sombra(tela, self.dica, f["peq"], (255, 255, 255), (W // 2, 304), centro=True)
        r = self.r_caixa = pygame.Rect(mx + 50, 340, W - 2 * mx - 100, 60)
        pygame.draw.rect(tela, (255, 255, 255), r, border_radius=10)
        pygame.draw.rect(tela, TINTA, r, 2, border_radius=10)
        cursor = "|" if (pygame.time.get_ticks() // 400) % 2 else ""
        txt = "•" * len(self.valor) if self.secreto else self.valor
        tela.blit(f["grande"].render(txt + cursor, True, TINTA), (r.x + 14, r.y + 8))
        if edicao.ANDROID:
            self.r_ok = pygame.Rect(W // 2 - 140, 424, 280, 72)
            pygame.draw.rect(tela, AMARELO if self.valor.strip() else (230, 225, 210), self.r_ok, border_radius=16)
            pygame.draw.rect(tela, TINTA, self.r_ok, 3, border_radius=16)
            t = f["grande"].render("OK", True, TINTA)
            tela.blit(t, t.get_rect(center=self.r_ok.center))


# ------------------------------------------------------------------ quiz

class Quiz(Estado):
    """Questão em tela cheia por cima da fase. Teclas A–E / 1–5 respondem;
    G corrige o gabarito ao vivo; I amplia imagem."""
    overlay = True
    passo_rolagem = 40                   # cada clique de roda rola 40 px

    def __init__(self, app, q, callback, contexto, fundo):
        super().__init__(app)
        self.q, self.cb, self.contexto, self.fundo = q, callback, contexto, fundo
        self.sel = 0
        self.escolha = None
        self.marcada = None              # celular: alternativa tocada, à espera do CONFIRMAR
        self.bt_quiz = pygame.Rect(60, H - 124, W - 120, 84)   # celular: CONFIRMAR / CONTINUAR
        self.rolagem = 0
        self.max_rolagem = 0
        self.corrigindo = False
        self.sel_corr = 0
        self.zoom = False
        self.t = 0
        self.imgs = []
        for c in q.get("imgs", [])[:2]:
            try:
                self.imgs.append(pygame.image.load(c).convert())
            except Exception:
                pass
        # figuras no meio do texto ([[img:caminho]] no enunciado, como na prova) e nas alternativas
        self.blocos = []                 # [("txt", linhas) | ("img", Surface)]
        self.alt_imgs = {}
        self.zoom_i = 0
        self.img_rects = []
        for k, c in (q.get("alt_imgs") or {}).items():
            im = _carregar_img(c)
            if im:
                self.alt_imgs[k] = im
        self.gab = app.gabarito(q)
        self._layout()

    def _layout(self):
        f = self.app.f
        self.larg_txt = W - 160 if RETRATO else 720 if self.imgs else 1100
        self.blocos = [("img", im) for im in self.imgs] if RETRATO else []   # em pé: figuras no topo
        for parte in re.split(r"(\[\[img:[^\]]+\]\])", self.q["enunciado"]):
            m = re.fullmatch(r"\[\[img:([^\]]+)\]\]", parte)
            if m:
                im = _carregar_img(m.group(1))
                if im:
                    self.blocos.append(("img", im))
            elif parte.strip():
                self.blocos.append(("txt", quebrar(parte.strip("\n"), f["q"], self.larg_txt)))
        self.linhas = [ln for tipo, b in self.blocos if tipo == "txt" for ln in b]
        self.alt_linhas = [(k, quebrar(v, f["q"], self.larg_txt - 70)) for k, v in self.q["alts"]]
        self.alt_rects = []

    def _figuras(self):
        """Todas as figuras da questão, na ordem (para o zoom)."""
        return self.imgs + [b for t, b in self.blocos if t == "img"] + list(self.alt_imgs.values())

    def evento(self, e, inp):
        letras = [k for k, _ in self.q["alts"]]
        if self.corrigindo:
            nova = None
            if e.type == pygame.KEYDOWN and e.unicode and e.unicode.upper() in letras:
                nova = e.unicode.upper()
            elif eh_pad(e, "UP", "DOWN"):
                self.sel_corr = (self.sel_corr + (1 if e.botao == "DOWN" else -1)) % len(letras)
            elif eh_pad(e, "A", "START"):
                nova = letras[self.sel_corr]
            elif (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE) or eh_pad(e, "B", "SELECT"):
                self.corrigindo = False
            if nova:
                self.app.corrigir_gabarito(self.q, nova)
                self.gab = nova
                self.corrigindo = False
            return
        figs = self._figuras()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_i and figs:
            if not self.zoom:                    # I abre a 1ª figura; I de novo passa para a próxima
                self.zoom, self.zoom_i = True, 0
            elif self.zoom_i + 1 < len(figs):
                self.zoom_i += 1
            else:
                self.zoom = False
            return
        if self.zoom:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.zoom = False
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:     # clique numa figura amplia
            for fig, r in self.img_rects:
                if r.collidepoint(e.pos):
                    self.zoom, self.zoom_i = True, next((i for i, x in enumerate(figs) if x is fig), 0)
                    return
        if e.type == pygame.MOUSEWHEEL:
            self.rolagem = max(0, min(self.max_rolagem, self.rolagem - e.y * 40))
            return
        if self.escolha is None:
            if e.type == pygame.KEYDOWN:
                ch = e.unicode.upper() if e.unicode else ""
                if ch in letras:
                    self._responder(ch)
                    return
                if ch in "12345" and ch and int(ch) <= len(letras):
                    self._responder(letras[int(ch) - 1])
                    return
            if inp.foi("cima"):
                self.sel = (self.sel - 1) % len(letras)
                self.app.audio.tocar("menu")
            elif inp.foi("baixo"):
                self.sel = (self.sel + 1) % len(letras)
                self.app.audio.tocar("menu")
            elif inp.foi("ok"):
                self._responder(letras[self.sel])
            elif (e.type == pygame.KEYDOWN and e.key == pygame.K_PAGEDOWN) or inp.foi("pgdn"):
                self.rolagem = min(self.max_rolagem, self.rolagem + 300)
            elif (e.type == pygame.KEYDOWN and e.key == pygame.K_PAGEUP) or inp.foi("pgup"):
                self.rolagem = max(0, self.rolagem - 300)
            elif edicao.ANDROID and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # celular: tocar marca a alternativa; o botão CONFIRMAR responde
                if self.marcada is not None and self.bt_quiz.collidepoint(e.pos):
                    self._responder(letras[self.marcada])
                    return
                for i, r in enumerate(self.alt_rects):
                    if r.collidepoint(e.pos):
                        self.sel = self.marcada = i
                        self.app.audio.tocar("menu")
            elif edicao.ANDROID and e.type == pygame.MOUSEMOTION:
                pass
            elif e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                for i, r in enumerate(self.alt_rects):
                    if r.collidepoint(e.pos):
                        self.sel = i
                        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                            self._responder(letras[i])
        else:
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_PAGEDOWN, pygame.K_DOWN)) or inp.foi("pgdn") or inp.foi("baixo"):
                self.rolagem = min(self.max_rolagem, self.rolagem + 120)
                return
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_PAGEUP, pygame.K_UP)) or inp.foi("pgup") or inp.foi("cima"):
                self.rolagem = max(0, self.rolagem - 120)
                return
            if not edicao.STEAM and ((e.type == pygame.KEYDOWN and e.key == pygame.K_g) or eh_pad(e, "SELECT")):
                self.corrigindo = True
                self.sel_corr = max(0, letras.index(self.gab)) if self.gab in letras else 0
            elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE) or \
                    (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and
                     (not edicao.ANDROID or self.bt_quiz.collidepoint(e.pos))) or eh_pad(e, "A", "B", "START"):
                ok = self.escolha == self.gab
                self.app.registrar(self.q, ok)
                self.app.pop()
                self.cb(self.escolha, ok)

    def _rodape_toque(self, tela, f):
        """Celular: resultado em cima e um botão grande embaixo (CONFIRMAR antes, CONTINUAR depois)."""
        b = self.bt_quiz
        if self.escolha is None:
            if self.marcada is None:
                sombra(tela, "Toque numa alternativa para marcar · arraste para rolar", f["peq"], (110, 95, 95),
                       (W // 2, b.centery), centro=True)
                return
            rot, cor = f"CONFIRMAR {[k for k, _ in self.q['alts']][self.marcada]}", AMARELO
        else:
            ok = self.escolha == self.gab
            msg = f"ACERTOU! Gabarito {self.gab}." if ok else f"Errou ({self.escolha}). Gabarito: {self.gab}."
            if not ok and self.q.get("coment"):
                msg += " Leia o comentário."
            t = f["med"].render(cortar(msg, f["med"], W - 140), True, (40, 140, 60) if ok else (190, 50, 50))
            tela.blit(t, (W // 2 - t.get_width() // 2, b.y - 44))
            rot, cor = "CONTINUAR", (190, 240, 190) if ok else (240, 235, 220)
        pygame.draw.rect(tela, cor, b, border_radius=18)
        pygame.draw.rect(tela, TINTA, b, 3, border_radius=18)
        t = f["grande"].render(rot, True, TINTA)
        tela.blit(t, (b.centerx - t.get_width() // 2, b.centery - t.get_height() // 2))

    def _responder(self, letra):
        self.escolha = letra
        self.app.audio.tocar("certo" if letra == self.gab else "errado")

    def update(self, inp):
        self.t += 1

    def draw(self, tela):
        if self.fundo:
            self.fundo.draw(tela)
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        v.fill((30, 20, 50, 150))
        tela.blit(v, (0, 0))
        f = self.app.f
        q = self.q
        painel(tela, (40, 20, W - 80, H - 40))
        # cabeçalho
        cab = " · ".join(x for x in (self.contexto, q.get("origem"), q.get("materia"),
                                      q.get("subtema"), q.get("assunto")) if x)
        tela.blit(f["peq"].render(cortar(cab[:150], f["peq"], W - 140), True, (140, 110, 110)), (70, 36))
        if q.get("revisao"):
            sombra(tela, "REVISÃO SM-2", f["peq"], (120, 200, 255), (W - 250, 36))
        area = pygame.Rect(60, 64, W - 120, H - (290 if edicao.ANDROID else 170))
        conteudo = pygame.Surface((area.w, 6000), pygame.SRCALPHA)
        y = 0
        img_pos = []                     # (figura, retângulo no conteúdo) para clique-amplia
        for tipo, b in self.blocos:
            if tipo == "txt":
                for ln in b:
                    conteudo.blit(f["q"].render(ln, True, TINTA), (10, y))
                    y += 28
                y += 6
            else:
                esc = min(self.larg_txt / b.get_width(), 300 / b.get_height(), 1.6)
                im = pygame.transform.smoothscale(b, (max(1, int(b.get_width() * esc)), max(1, int(b.get_height() * esc))))
                r = pygame.Rect(10, y + 4, im.get_width(), im.get_height())
                conteudo.blit(im, r.topleft)
                pygame.draw.rect(conteudo, (200, 190, 180), r.inflate(4, 4), 1)
                img_pos.append((b, r))
                y = r.bottom + 12
        y += 14
        img_y = 0
        rects = []
        letras = [k for k, _ in q["alts"]]
        for i, (k, lns) in enumerate(self.alt_linhas):
            aimg = self.alt_imgs.get(k)
            if aimg:
                esc = min((self.larg_txt - 80) / aimg.get_width(), 120 / aimg.get_height(), 1.4)
                aimg = pygame.transform.smoothscale(aimg, (max(1, int(aimg.get_width() * esc)), max(1, int(aimg.get_height() * esc))))
                lns = [ln for ln in lns if ln.strip()]
            pad = 14 if edicao.ANDROID else 0        # celular: alternativa mais alta, alvo de dedo
            h = max(44, 28 * len(lns) + 14 + (aimg.get_height() + 8 if aimg else 0)) + 2 * pad
            r = pygame.Rect(4, y, self.larg_txt + 20, h)
            cor = (255, 255, 255)
            if self.escolha is not None:
                if k == self.gab:
                    cor = (190, 240, 190)
                elif k == self.escolha:
                    cor = (250, 190, 190)
            elif i == self.sel and (not edicao.ANDROID or self.marcada is not None):
                cor = (255, 240, 170)
            pygame.draw.rect(conteudo, cor, r, border_radius=10)
            pygame.draw.rect(conteudo, TINTA, r, 2, border_radius=10)
            badge = VERDE if (self.escolha and k == self.gab) else (VERMELHO if self.escolha == k else AMARELO)
            pygame.draw.circle(conteudo, badge, (r.x + 26, r.y + 22 + pad), 16)
            pygame.draw.circle(conteudo, TINTA, (r.x + 26, r.y + 22 + pad), 16, 2)
            lt = f["med"].render(k, True, TINTA)
            conteudo.blit(lt, (r.x + 26 - lt.get_width() // 2, r.y + 22 + pad - lt.get_height() // 2))
            for j, ln in enumerate(lns):
                conteudo.blit(f["q"].render(ln, True, TINTA), (r.x + 56, r.y + 8 + pad + j * 28))
            if aimg:
                ar = pygame.Rect(r.x + 56, r.y + 8 + pad + 28 * len(lns), aimg.get_width(), aimg.get_height())
                conteudo.blit(aimg, ar.topleft)
                img_pos.append((self.alt_imgs[k], ar))
            rects.append(r)
            y += h + 10
        coment_bottom = None
        if self.escolha is not None and q.get("coment"):
            y += 6
            lns = quebrar(q["coment"], f["q"], self.larg_txt - 10)
            caixa = pygame.Rect(4, y, self.larg_txt + 20, 44 + 27 * len(lns))
            pygame.draw.rect(conteudo, (226, 236, 255), caixa, border_radius=10)
            pygame.draw.rect(conteudo, (70, 100, 170), caixa, 2, border_radius=10)
            conteudo.blit(f["med"].render("Comentário", True, (50, 80, 150)), (caixa.x + 14, caixa.y + 8))
            for j, ln in enumerate(lns):
                x, yl = caixa.x + 14, caixa.y + 40 + j * 27
                rot = next((r for r in ROTULOS_COMENT if ln.startswith(r)), None)
                if rot:                                   # comentário em três partes: o rótulo vem colorido
                    t = f["q"].render(rot, True, ROTULOS_COMENT[rot])
                    conteudo.blit(t, (x, yl))
                    x, ln = x + t.get_width(), ln[len(rot):]
                conteudo.blit(f["q"].render(ln, True, (30, 40, 70)), (x, yl))
            y = caixa.bottom + 10
            coment_bottom = caixa.bottom + 10
        total = y
        self.max_rolagem = max(0, total - area.h)
        if self.escolha is None and rects and self.sel != getattr(self, "_sel_visto", 0):
            self._sel_visto = self.sel           # só rola sozinho quando o jogador troca a alternativa
            r = rects[self.sel]
            if r.bottom - self.rolagem > area.h:
                self.rolagem = min(self.max_rolagem, r.bottom - area.h + 10)
            elif r.top < self.rolagem:
                self.rolagem = max(0, r.top - 10)
        elif coment_bottom and not getattr(self, "_rolou_coment", False):
            self._rolou_coment = True          # mostra o comentário logo após responder
            self.rolagem = min(self.max_rolagem, max(self.rolagem, coment_bottom - area.h))
        tela.blit(conteudo, area.topleft, (0, self.rolagem, area.w, area.h))
        self.alt_rects = [r.move(area.x, area.y - self.rolagem).clip(area) for r in rects]
        self.img_rects = [(fig, r.move(area.x, area.y - self.rolagem).clip(area)) for fig, r in img_pos]
        # imagens à direita
        if self.imgs and not RETRATO:
            iy = area.y
            for img in self.imgs:
                esc = min(390 / img.get_width(), (area.h / len(self.imgs) - 10) / img.get_height(), 2.0)
                im = pygame.transform.smoothscale(img, (int(img.get_width() * esc), int(img.get_height() * esc)))
                tela.blit(im, (W - 80 - im.get_width(), iy))
                pygame.draw.rect(tela, TINTA, (W - 80 - im.get_width(), iy, im.get_width(), im.get_height()), 2)
                iy += im.get_height() + 10
        if self.max_rolagem:
            frac = self.rolagem / self.max_rolagem
            pygame.draw.rect(tela, (200, 180, 160), (W - 62, area.y + int((area.h - 60) * frac), 6, 60), border_radius=3)
        # rodapé
        rod = pygame.Rect(60, H - 96, W - 120, 60)
        if self.corrigindo:
            msg, cor = (f"Corrigir gabarito: aperte a letra CORRETA (controle: ↑↓ = {[k for k, _ in self.q['alts']][self.sel_corr]}, A confirma) · Esc cancela", (60, 120, 200))
        elif self.escolha is None:
            msg, cor = ("Toque na alternativa · arraste para rolar" if edicao.ANDROID else
                        "↑↓ escolhe · A confirma · toque na alternativa · LB/RB rolam" if _dicas_pad() else
                        "A–E ou 1–5 respondem · ↑↓ + Enter · roda do mouse/PgDn rola") + (" · I amplia figura" if self._figuras() else ""), (110, 95, 95)
        elif self.escolha == self.gab:
            msg, cor = f"ACERTOU! Gabarito {self.gab}. +FLOR · " + ("toque para continuar" if edicao.ANDROID else "Enter/A continua · ↑↓ rola") + ("" if edicao.STEAM else " · G corrige gabarito"), (40, 140, 60)
        else:
            dica = "Leia o comentário · " if self.q.get("coment") else ""
            msg, cor = f"Errou ({self.escolha}). Gabarito: {self.gab}. {dica}" + ("toque para continuar" if edicao.ANDROID else "Enter/A continua · ↑↓ rola") + ("" if edicao.STEAM else " · G corrige"), (190, 50, 50)
        lns = quebrar(msg, f["med"], rod.w - 90)[:2]
        if edicao.ANDROID:
            self._rodape_toque(tela, f)
            lns = []
        for j, ln in enumerate(lns):
            tela.blit(f["med"].render(ln, True, cor), (rod.x + 10, rod.y + 14 - 15 * (len(lns) - 1) + 30 * j))
        if self.escolha is not None and not edicao.ANDROID:
            spr = art.flor(16, self.t // 3) if self.escolha == self.gab else art.virus(self.t // 4)
            tela.blit(pygame.transform.scale(spr, (48, 48)), (W - 120, H - 100))
        figs = self._figuras()
        if self.zoom and figs:
            v = pygame.Surface((W, H))
            v.fill((20, 20, 20))
            tela.blit(v, (0, 0))
            img = figs[min(self.zoom_i, len(figs) - 1)]
            esc = min((W - 40) / img.get_width(), (H - 40) / img.get_height())
            im = pygame.transform.smoothscale(img, (int(img.get_width() * esc), int(img.get_height() * esc)))
            tela.blit(im, ((W - im.get_width()) // 2, (H - im.get_height()) // 2))
            if len(figs) > 1:
                sombra(tela, f"Figura {self.zoom_i + 1} de {len(figs)} · I = próxima · qualquer tecla fecha",
                       f["peq"], (255, 255, 255), (W // 2, H - 16), centro=True)


_IMGS = {}


def _carregar_img(caminho):
    if caminho.startswith("fig:"):                   # figura desenhada pelo jogo (ilha/figuras.py)
        from . import figuras
        return figuras.figura(caminho[4:])
    if caminho not in _IMGS:
        try:
            im = pygame.image.load(caminho)
            _IMGS[caminho] = im.convert_alpha() if pygame.display.get_surface() else im
        except Exception:
            _IMGS[caminho] = None
    return _IMGS[caminho]


# ------------------------------------------------------------------ fase e resultado

class Briefing(Estado):
    """Resumo curto antes da fase: o jogador lê e aperta Enter para começar."""
    passo_rolagem = 60                   # cada clique de roda rola 60 px

    def __init__(self, app, info, questoes, iniciar):
        super().__init__(app)
        self.info, self.iniciar = info, iniciar
        self.pilulas = info.get("pilulas")
        if "pilulas" not in info and not edicao.STEAM:  # a edição Steam não leva o banco geral de pílulas
            from . import resumos
            self.pilulas = resumos.buscar(info.get("materia", ""), info.get("texto", ""), 3, info.get("extra", ""))
        self.pilulas = self.pilulas or []
        assuntos = []
        for q in questoes:
            a = q.get("subtema") or q.get("assunto") or ""
            if a and a not in assuntos:
                assuntos.append(a)
        self.assuntos = assuntos[:6]
        self.rol = 0
        self.max_rol = 0
        self.t = 0
        # narradora: um trecho por título/ponto, na ordem do texto (ilha/narrador.py)
        from . import narrador
        self.trechos = []                       # [(texto falado, (pílula, ponto) — ponto -1 = título)]
        for pi, p in enumerate(self.pilulas):
            tit = p["titulo"]
            self.trechos.append(("Bizus de " + tit[len("Bizus · "):] if tit.startswith("Bizus · ") else tit, (pi, -1)))
            for ki, ponto in enumerate(p["pontos"]):
                self.trechos.append((ponto, (pi, ki)))
        # narradora fica fora das edições de venda (Steam, Android, Vestibulando)
        self.leitura = narrador.Leitura([t for t, _ in self.trechos]) if self.trechos and not edicao.STEAM else None
        self.bt_ouvir = pygame.Rect(W - 320, 34, 220, 40)
        self._lido = -1

    def _ouvir_disponivel(self):
        return self.leitura is not None and self.leitura.disponivel()

    def _alternar_leitura(self):
        if not self._ouvir_disponivel():
            return
        if self.leitura.tocando:
            self.leitura.parar()
        else:
            self.leitura.tocar()

    def _sair(self):
        if self.leitura:
            self.leitura.parar()
        self.app.pop()

    def evento(self, e, inp):
        if (e.type == pygame.KEYDOWN and e.key == pygame.K_l) or (eh_pad(e, "Y") and self._ouvir_disponivel()) or \
                (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self._ouvir_disponivel() and self.bt_ouvir.collidepoint(e.pos)):
            self._alternar_leitura()
        elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE) or (eh_pad(e, "B") and not edicao.STEAM) \
                or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
            self._sair()
            self.iniciar()
        elif inp.foi("voltar"):
            self._sair()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_r and self.info.get("pdf"):
            import subprocess
            subprocess.Popen(["xdg-open", self.info["pdf"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif inp.foi("baixo") or inp.foi("pgdn") or (e.type == pygame.MOUSEWHEEL and e.y < 0):
            self.rol = min(self.max_rol, self.rol + 60)
        elif inp.foi("cima") or inp.foi("pgup") or (e.type == pygame.MOUSEWHEEL and e.y > 0):
            self.rol = max(0, self.rol - 60)

    def update(self, inp):
        self.t += 1
        if self.leitura:
            self.leitura.update()
            if pygame.mixer.get_init() and self.app.audio.faixas:     # música quase muda enquanto ela lê
                from .audio import VOL_ABAIXADO
                pygame.mixer.music.set_volume(0.04 if self.leitura.tocando else VOL_ABAIXADO)
            if self.leitura.atual != self._lido and self.leitura.atual >= 0:
                self._lido = self.leitura.atual
                pos = getattr(self, "_pos", {}).get(self.trechos[self._lido][1])
                if pos:                                                  # rola junto com a leitura
                    self.rol = max(0, min(self.max_rol, pos[0] - 60))

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        mx = 16 if RETRATO else 60
        painel(tela, (mx, 20, W - 2 * mx, H - 40))
        titulo_px(tela, self.info.get("cabecalho", "Resumo antes da fase"), AMARELO, W // 2, 38, 3)
        sub = self.info.get("titulo", "")
        t = f["med"].render(cortar(sub[:90], f["med"], W - 2 * mx - 40), True, TINTA)
        tela.blit(t, (W // 2 - t.get_width() // 2, 86))
        area = pygame.Rect(mx + 30, 124, W - 2 * mx - 60, H - 230)
        c = self._conteudo(area.w)
        self.max_rol = max(0, c.get_height() - area.h)
        if self.leitura and self.leitura.tocando and self.leitura.atual >= 0:     # destaca o trecho lido
            y0, y1 = self._pos.get(self.trechos[self.leitura.atual][1], (0, 0))
            r = pygame.Rect(area.x - 6, area.y + y0 - self.rol - 3, area.w + 6, y1 - y0 + 4).clip(area.inflate(8, 0))
            if r.h > 0:
                pygame.draw.rect(tela, (255, 232, 150), r, border_radius=8)
        tela.blit(c, area.topleft, (0, self.rol, area.w, area.h))
        if self._ouvir_disponivel():
            lt = self.leitura
            rot = "■ Parar leitura" if lt.tocando and not lt.preparando else ("… preparando voz" if lt.tocando else "▶ Ouvir (L / Y)")
            pygame.draw.rect(tela, AMARELO if lt.tocando else (240, 235, 220), self.bt_ouvir, border_radius=12)
            pygame.draw.rect(tela, TINTA, self.bt_ouvir, 2, border_radius=12)
            t2 = f["med"].render(rot, True, TINTA)
            tela.blit(t2, (self.bt_ouvir.centerx - t2.get_width() // 2, self.bt_ouvir.centery - t2.get_height() // 2))
        if self.max_rol:
            pygame.draw.rect(tela, (200, 180, 160), (area.right + 10, area.y + int((area.h - 50) * self.rol / self.max_rol), 6, 50))
        self._rodape(tela)

    def _conteudo(self, largura):
        """Texto do resumo renderizado uma vez só, na altura exata (antes: 3000 px refeitos a cada quadro)."""
        if getattr(self, "_cache", None) is not None and self._cache.get_width() == largura:
            return self._cache
        f = self.app.f
        self._pos = {}                            # (pílula, ponto) -> (y inicial, y final), para destacar o trecho lido
        ops = []                                  # (superfície, posição): monta e depois cria na altura exata
        area = pygame.Rect(0, 0, largura, 0)
        y = 0
        if not self.pilulas:
            for ln in quebrar("Ainda não há pílula de resumo cadastrada para este assunto. "
                              "Leia os tópicos abaixo e vá para a fase.", f["q"], area.w - 20):
                ops.append((f["q"].render(ln, True, (120, 100, 100)), (10, y)))
                y += 28
            y += 10
        def caixa(rotulo, texto, fundo, borda, cor_rot, y):
            """Bloco destacado (ideia-chave / na prova): rótulo pequeno + texto, num cartão colorido."""
            lns = quebrar(texto, f["q"], area.w - 44)
            alt = 34 + 27 * len(lns) + 10
            c = pygame.Surface((area.w - 8, alt), pygame.SRCALPHA)
            pygame.draw.rect(c, fundo, c.get_rect(), border_radius=12)
            pygame.draw.rect(c, borda, c.get_rect(), 2, border_radius=12)
            c.blit(f["peq"].render(rotulo, True, cor_rot), (14, 8))
            for i, ln in enumerate(lns):
                c.blit(f["q"].render(ln, True, TINTA), (14, 32 + 27 * i))
            ops.append((c, (4, y)))
            return y + alt + 10

        for pi, p in enumerate(self.pilulas):
            ops.append((art.texto_px(p["titulo"].upper()[:60], (255, 236, 120), escala=2), (0, y)))
            self._pos[(pi, -1)] = (y, y + 26)
            y += 32
            if p.get("ideia"):                       # padrão didático: a frase-âncora (o porquê) vem primeiro
                y = caixa("A IDEIA", p["ideia"], (255, 246, 205), (226, 196, 90), (150, 110, 20), y)
            if p.get("fig"):                         # figura didática desenhada pelo jogo (ilha/figuras.py)
                from . import figuras
                im = figuras.figura(p["fig"], min(area.w - 8, figuras.BW))
                if im:
                    ops.append((im, ((area.w - im.get_width()) // 2, y)))
                    y += im.get_height() + 14
            for ki, ponto in enumerate(p["pontos"]):
                lns = quebrar(ponto, f["q"], area.w - 50)
                self._pos[(pi, ki)] = (y, y + 27 * len(lns))
                ops.append((pygame.transform.scale(pets_pata(), (15, 18)), (8, y + 4)))
                for ln in lns:
                    ops.append((f["q"].render(ln, True, TINTA), (34, y)))
                    y += 27
                y += 6
            if p.get("exemplo"):                     # caso resolvido: a regra aplicada a um paciente, com números
                y = caixa("CASO RESOLVIDO", p["exemplo"], (226, 246, 222), (110, 180, 110), (40, 110, 40), y + 4)
            if p.get("na_prova"):
                y = caixa("NA PROVA", p["na_prova"], (226, 238, 255), (120, 150, 210), (50, 80, 150), y + 4)
            if p.get("fonte"):
                for ln in quebrar("Fonte: " + p["fonte"], f["peq"], area.w - 20):
                    ops.append((f["peq"].render(ln, True, (140, 125, 125)), (10, y)))
                    y += 22
            y += 12
        if self.assuntos:
            ops.append((f["med"].render("Nesta fase caem questões de:", True, (90, 120, 160)), (0, y)))
            y += 32
            for a in self.assuntos:
                ops.append((f["q"].render("• " + a, True, (90, 80, 80)), (20, y)))
                y += 26
        c = pygame.Surface((largura, max(1, y)), pygame.SRCALPHA)
        for sup, pos in ops:
            c.blit(sup, pos)
        self._cache = c
        return self._cache

    def _rodape(self, tela):
        f = self.app.f
        rod = ("Toque para começar  ·  arraste para rolar  ·  voltar do Android: voltar" if edicao.ANDROID else
               "A / Enter: começar  ·  ↑↓ rola  ·  B / Esc: voltar" if _dicas_pad() else
               "Enter/Espaço ou A/B: começar  ·  ↑↓ rola  ·  Esc/SELECT: voltar")
        if self._ouvir_disponivel() and not edicao.ANDROID:
            rod += "  ·  L ou Y (controle): ouvir"
        if self.info.get("pdf"):
            rod += "  ·  R: resumão PDF da aula (IA local, confira)"
        t = f["peq"].render(rod, True, (110, 95, 95))
        tela.blit(t, (W // 2 - t.get_width() // 2, H - 76))
        x = (self.t * 2) % (W + 200) - 100
        tela.blit(pygame.transform.scale(art.heroi("andar", (self.t // 8) % 4, True, 1), (80, 104)), (x, H - 124))


class SoQuestoes(Estado):
    """Estilo 'Sem risadinha': as questões da fase em sequência, só o Quiz (com comentário), sem plataforma.
    No fim monta o mesmo dicionário de resultado do Jogo, com pontos = % de acerto."""

    def __init__(self, app, questoes, titulo, contexto, ao_terminar):
        super().__init__(app)
        self.questoes, self.titulo, self.contexto, self.ao_terminar = questoes, titulo, contexto, ao_terminar
        self.i = 0
        self.respostas = {}
        self.terminou = False

    def _resposta(self, letra, ok):
        self.respostas[self.i] = (letra, ok)
        self.i += 1

    def _terminar(self):
        self.terminou = True
        n = len(self.questoes)
        acertos = sum(1 for _, ok in self.respostas.values() if ok)
        self.ao_terminar({"venceu": True, "pontos": round(100 * acertos / max(1, n)), "acertos": acertos, "n": n,
                          "respostas": self.respostas, "questoes": self.questoes, "estrelas": 0, "vermelhas": 0,
                          "moedas": acertos, "titulo": self.titulo, "so_questoes": True})

    def evento(self, e, inp):
        if inp.foi("voltar") and not self.terminou:     # sair no meio: resultado com o que foi respondido
            self.questoes = self.questoes[:max(1, self.i)]
            self._terminar()

    def update(self, inp):
        if self.terminou or self.app.pilha[-1] is not self:
            return
        if self.i >= len(self.questoes):
            self._terminar()
            return
        ctx = f"{self.contexto} · questão {self.i + 1}/{len(self.questoes)}"
        self.app.push(Quiz(self.app, self.questoes[self.i], self._resposta, ctx, self))

    def draw(self, tela):
        self.app.cenario.draw(tela)


class Fase(Estado):
    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo

    def evento(self, e, inp):
        self.jogo.evento(e, inp)

    def update(self, inp):
        self.jogo.update(inp)

    def draw(self, tela):
        self.jogo.draw(tela, self.app.f)


class Resultado(Estado):
    def __init__(self, app, res, opcoes):
        super().__init__(app)
        self.res = res
        self.opcoes = opcoes  # [(rótulo, ação)]
        self.sel = 0
        self.rol = 0
        self.t = 0
        self.mostrado = 0
        self.rects = []

    def evento(self, e, inp):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.opcoes[i][1]()
                    return
        if inp.foi("cima") or inp.foi("esq"):
            self.sel = (self.sel - 1) % len(self.opcoes)
        elif inp.foi("baixo") or inp.foi("dir"):
            self.sel = (self.sel + 1) % len(self.opcoes)
        elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self.opcoes[self.sel][1]()
        elif inp.foi("voltar"):
            self.opcoes[-1][1]()
        elif e.type == pygame.MOUSEWHEEL:
            self.rol = max(0, self.rol - e.y)

    def update(self, inp):
        self.t += 1
        if self.mostrado < self.res["pontos"] and self.t % 2 == 0:
            self.mostrado += 1
            if self.mostrado % 5 == 0:
                self.app.audio.tocar("moeda")

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        r = self.res
        mx = 20 if RETRATO else 80
        painel(tela, (mx, 30, W - 2 * mx, H - 60))
        tit = "QUESTÕES RESOLVIDAS" if r.get("so_questoes") else "FASE CONCLUÍDA!" if r["venceu"] else "FIM DE JOGO"
        titulo_px(tela, tit, AMARELO if r["venceu"] else VERMELHO, W // 2, 46)
        tela.blit(f["peq"].render(cortar(r["titulo"][:110], f["peq"], W - 2 * mx - 80), True, (120, 100, 100)),
                  (mx + 40, 120))
        if r.get("so_questoes"):
            sombra(tela, f"{r['acertos']}/{r['n']} certas · {self.mostrado}%", f["grande"], (255, 255, 255),
                   (W // 2, 160), centro=True)
        elif r["venceu"]:
            sombra(tela, f"{self.mostrado} pontos", f["grande"], (255, 255, 255), (W // 2, 150), centro=True)
            det = f"Estrelas {min(30, r['estrelas'])}/30 · Fichas {r['vermelhas']}x4={r['vermelhas'] * 4}/20 · " \
                  f"Acertos {r['acertos']}/{r['n']} = {round(50 * r['acertos'] / max(1, r['n']))}/50"
            for j, ln in enumerate(quebrar(det, f["peq"], W - 2 * mx - 60)[:2]):
                t = f["peq"].render(ln, True, TINTA)
                tela.blit(t, (W // 2 - t.get_width() // 2, 194 + 22 * j - (11 if RETRATO else 0)))
            if r.get("recorde_antes") is not None and r["pontos"] > r["recorde_antes"]:
                sombra(tela, "NOVO RECORDE!", f["med"], (255, 160, 200), (W // 2, 226), centro=True)
        else:
            sombra(tela, f"Acertos: {r['acertos']}/{len(r['respostas'])} respondidas", f["grande"], (255, 255, 255), (W // 2, 160), centro=True)
        y = 262
        for i, q in enumerate(r["questoes"][self.rol:self.rol + (16 if RETRATO else 8)], start=self.rol):
            resp = r["respostas"].get(i)
            if resp is None:
                marca, cor, extra = "–", (150, 140, 140), "não respondida"
            else:
                ok = resp[1]
                marca, cor = ("✔", (40, 140, 60)) if ok else ("✘", (190, 50, 50))
                extra = f"sua {resp[0]} · gabarito {self.app.gabarito(q)}"
            tela.blit(f["med"].render(marca, True, cor), (mx + 40, y))
            txt = q["enunciado"].replace("\n", " ")
            txt = txt[:95] + ("…" if len(txt) > 95 else "")
            tela.blit(f["peq"].render(cortar(txt, f["peq"], W - 2 * mx - 100), True, TINTA), (mx + 76, y + 2))
            tela.blit(f["peq"].render(extra, True, cor), (mx + 76, y + 22))
            y += 46
        c = self.app.save.carteira
        ganho = (f"Nesta fase: +{r.get('moedas', 0)} moedas, +{r['acertos']} créditos  ·  "
                 f"Na carteira: {c['moedas']} moedas, {c['creditos']} créditos")
        if RETRATO:
            for j, ln in enumerate(ganho.split("  ·  ")):
                sombra(tela, ln, f["peq"], (255, 236, 150), (W // 2, H - 160 + 24 * j), centro=True)
        else:
            sombra(tela, ganho, f["peq"], (255, 236, 150), (W // 2, H - 136), centro=True)
        x = W // 2 - sum(f["med"].size(o[0])[0] + 60 for o in self.opcoes) // 2
        self.rects = []
        for i, (rot, _) in enumerate(self.opcoes):
            w = f["med"].size(rot)[0] + 40
            rr = pygame.Rect(x, H - 100, w, 48)
            self.rects.append(rr)
            pygame.draw.rect(tela, AMARELO if i == self.sel else (240, 235, 220), rr, border_radius=12)
            pygame.draw.rect(tela, TINTA, rr, 2, border_radius=12)
            tela.blit(f["med"].render(rot, True, TINTA), (rr.x + 20, rr.y + 10))
            x += w + 20


# ------------------------------------------------------------------ app

class ConfigControle(Estado):
    """Assistente: aperta cada botão pedido no controle; salva o perfil por GUID."""
    PASSOS = ["UP", "DOWN", "LEFT", "RIGHT", "B", "Y", "A", "X", "L", "R", "SELECT", "START"]
    DICA = {"B": "pular", "Y": "ataque do pet", "A": "dash / confirmar", "X": "dash", "L": "rolar para cima",
            "R": "rolar para baixo", "SELECT": "voltar / corrigir gabarito", "START": "pausa / confirmar"}

    def __init__(self, app, joy, origem="desconhecido"):
        super().__init__(app)
        self.joy, self.origem = joy, origem
        self.i = 0
        self.mapa = {}
        self.espera_soltar = False
        self.base = [joy.get_axis(k) for k in range(joy.get_numaxes())]
        self.fim_t = 0
        self.t = 0

    def _registrar(self, b):
        if b in self.mapa.values():
            return
        self.mapa[self.PASSOS[self.i]] = b
        self.app.audio.tocar("moeda")
        self.i += 1
        self.espera_soltar = True
        if self.i >= len(self.PASSOS):
            self.app.pad.salvar_perfil(self.joy, self.mapa)
            self.app.audio.tocar("anel")
            self.fim_t = 90

    def evento(self, e, inp):
        if self.fim_t:
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.toast("Configuração cancelada: usando o mapeamento padrão")
                self.app.pop()
            elif e.key == pygame.K_BACKSPACE and self.i > 0:
                self.i -= 1
                self.mapa.pop(self.PASSOS[self.i], None)
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN):   # pular este botão
                self.i += 1
                if self.i >= len(self.PASSOS):
                    self.app.pad.salvar_perfil(self.joy, self.mapa)
                    self.fim_t = 90
            return
        if getattr(e, "instance_id", None) != self.joy.get_instance_id() or self.espera_soltar:
            return
        if e.type == pygame.JOYBUTTONDOWN:
            self._registrar(["b", e.button])
        elif e.type == pygame.JOYHATMOTION and e.value != (0, 0):
            hx, hy = e.value
            self._registrar(["h", e.hat, hx, 0] if hx else ["h", e.hat, 0, hy])
        elif e.type == pygame.JOYAXISMOTION:
            base = self.base[e.axis] if e.axis < len(self.base) else 0
            if abs(e.value - base) > 0.6 and abs(e.value) > 0.5:
                self._registrar(["a", e.axis, 1 if e.value > 0 else -1])

    def update(self, inp):
        self.t += 1
        if self.espera_soltar:
            soltos = self.app.pad.neutro(self.joy)
            eixos_ok = all(abs(self.joy.get_axis(k) - (self.base[k] if k < len(self.base) else 0)) < 0.3
                           for k in range(self.joy.get_numaxes()))
            if soltos and eixos_ok:
                self.espera_soltar = False
        if self.fim_t:
            self.fim_t -= 1
            if self.fim_t == 0:
                self.app.toast(f"Controle configurado: {self.joy.get_name()}")
                self.app.pop()

    def _desenhar_controle(self, tela, destaque):
        """Controle de SNES em pixel art (desenhado a 1/4 e ampliado)."""
        s = pygame.Surface((150, 64), pygame.SRCALPHA)
        K = art.K
        corpo, borda = (200, 200, 212), (120, 120, 140)
        on = lambda nome: (255, 96, 200) if nome == destaque and (self.t // 10) % 2 == 0 else None
        for nome, r in (("L", (10, 0, 40, 10)), ("R", (100, 0, 40, 10))):
            pygame.draw.rect(s, K, r, border_radius=4)
            pygame.draw.rect(s, on(nome) or (160, 160, 176), (r[0] + 1, r[1] + 1, r[2] - 2, r[3] - 2), border_radius=4)
        pygame.draw.ellipse(s, K, (0, 6, 62, 56))
        pygame.draw.ellipse(s, K, (88, 6, 62, 56))
        pygame.draw.rect(s, K, (30, 8, 90, 52))
        pygame.draw.ellipse(s, corpo, (1, 7, 60, 54))
        pygame.draw.ellipse(s, corpo, (89, 7, 60, 54))
        pygame.draw.rect(s, corpo, (30, 9, 90, 50))
        # direcional
        cx, cy = 30, 34
        pygame.draw.rect(s, K, (cx - 5, cy - 15, 11, 31))
        pygame.draw.rect(s, K, (cx - 15, cy - 5, 31, 11))
        pygame.draw.rect(s, (60, 60, 70), (cx - 4, cy - 14, 9, 29))
        pygame.draw.rect(s, (60, 60, 70), (cx - 14, cy - 4, 29, 9))
        for nome, r in (("UP", (cx - 4, cy - 14, 9, 9)), ("DOWN", (cx - 4, cy + 6, 9, 9)),
                        ("LEFT", (cx - 14, cy - 4, 9, 9)), ("RIGHT", (cx + 6, cy - 4, 9, 9))):
            if on(nome):
                pygame.draw.rect(s, on(nome), r)
        # select / start
        for nome, x in (("SELECT", 62), ("START", 80)):
            pygame.draw.rect(s, K, (x, 36, 12, 6), border_radius=3)
            pygame.draw.rect(s, on(nome) or (110, 110, 124), (x + 1, 37, 10, 4), border_radius=2)
        # botões coloridos (padrão SNES: X azul, A vermelho, B amarelo, Y verde)
        bx, by = 120, 34
        for nome, (dx, dy), cor in (("X", (0, -12), (90, 110, 230)), ("A", (12, 0), (220, 60, 60)),
                                     ("B", (0, 12), (240, 200, 50)), ("Y", (-12, 0), (70, 170, 80))):
            pygame.draw.circle(s, K, (bx + dx, by + dy), 7)
            pygame.draw.circle(s, on(nome) or cor, (bx + dx, by + dy), 6)
            s.blit(art.texto_px(nome, (255, 255, 255)), (bx + dx - 4, by + dy - 6))
        tela.blit(pygame.transform.scale(s, (600, 256)), (W // 2 - 300, 250))

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        painel(tela, (100, 30, W - 200, H - 60))
        titulo_px(tela, "Configurar controle", AMARELO, W // 2, 50, 3)
        t = f["peq"].render(f"{self.joy.get_name()}  ·  {self.origem}", True, (120, 100, 100))
        tela.blit(t, (W // 2 - t.get_width() // 2, 100))
        if self.fim_t:
            titulo_px(tela, "Pronto!", VERDE, W // 2, 160, 4)
            self._desenhar_controle(tela, None)
            return
        alvo = self.PASSOS[self.i]
        msg = f"Aperte {NOMES_PAD[alvo]}" + (f"  ({self.DICA[alvo]})" if alvo in self.DICA else "")
        t = f["grande"].render(msg, True, TINTA)
        tela.blit(t, (W // 2 - t.get_width() // 2, 150))
        t = f["peq"].render(f"Botão {self.i + 1} de {len(self.PASSOS)}" + ("  ·  solte o botão…" if self.espera_soltar else ""),
                            True, (120, 100, 100))
        tela.blit(t, (W // 2 - t.get_width() // 2, 200))
        self._desenhar_controle(tela, alvo)
        t = f["peq"].render("Teclado: Espaço pula este botão · Backspace volta · Esc cancela (usa o padrão)", True, (110, 95, 95))
        tela.blit(t, (W // 2 - t.get_width() // 2, H - 90))


def _sincronia_ligada():
    """PC: só com a pasta de save verdadeira (testes usam pastas temporárias e não podem mexer na cópia
    mestra). Celular: só no Android de verdade. Edições de venda: nunca. ILHA_SINCRONIA força ligar."""
    if os.environ.get("ILHA_SEM_SINCRONIA"):
        return False
    if os.environ.get("ILHA_SINCRONIA"):
        return True
    if edicao.ANDROID:
        return bool(os.environ.get("ANDROID_ARGUMENT"))
    return not edicao.STEAM and os.path.abspath(data.SAVE_DIR) == os.path.abspath(data.SAVE_DIR_PADRAO)


class App:
    def __init__(self, mudo=False, tela_cheia=False):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption(edicao.NOME)
        icone = os.path.join(os.path.dirname(edicao.PASTA), "icone.png")
        if os.path.exists(icone):
            pygame.display.set_icon(pygame.image.load(icone))
        # Android: sem RESIZABLE (com ele o SDL libera a rotação e ignora a orientação do manifesto) e com
        # FULLSCREEN (modo imersivo: sem barra de status e de navegação por cima dos botões)
        flags = pygame.SCALED | pygame.FULLSCREEN if edicao.ANDROID else pygame.SCALED | pygame.RESIZABLE
        self.margens = (edicao.MARGEM_CIMA, edicao.MARGEM_BAIXO) if edicao.ANDROID else (0, 0)
        try:
            self.janela = pygame.display.set_mode((W, H + sum(self.margens)), flags)
        except pygame.error:             # driver sem tela cheia
            self.janela = pygame.display.set_mode((W, H + sum(self.margens)), pygame.SCALED)
        # as telas desenham na área útil; as margens (câmera em cima, barra de gestos embaixo) são cenário
        self.tela = self.janela.subsurface((0, self.margens[0], W, H)) if any(self.margens) else self.janela
        self.save = data.Save()
        from . import loja
        loja.aplicar(self.save)          # personagem e itens equipados (heroi.py)
        if edicao.STEAM and not edicao.VESTIBULANDO:   # Steam: tela cheia por padrão (sempre no Steam Deck)
            tela_cheia = tela_cheia or edicao.no_steam_deck() or self.save.config.get("tela_cheia", True)
        if tela_cheia:
            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:         # driver sem tela cheia (ex.: testes sem vídeo)
                pass
        self.relogio = pygame.time.Clock()
        g = 1.15 if RETRATO else 1                       # celular: letra maior (lida a um palmo do rosto)
        self.f = {"peq": fonte(round(17 * g)), "q": fonte(round(20 * g)), "med": fonte(round(22 * g), True),
                  "grande": fonte(34, True),
                  "titulo": fonte(52, True), "enorme": fonte(72, True)}
        self.audio = Audio(mudo or self.save.config.get("mudo", False))
        self.pad = Pad()
        self.toque = Toque(W, H, *self.margens) if toque_ativo() else None
        if self.toque:
            self.toque.dicas_restantes = self.save.config.get("dicas_gestos", 3)

            def _dica_vista(n):
                self.save.config["dicas_gestos"] = n
                self.save.salvar()
            self.toque.ao_mostrar_dica = _dica_vista
        self.entrada = Entrada(self.pad, self.toque)
        self._toast = None
        self.cenario = Cenario(0)
        self.pilha = []
        self._trans = None
        self.banco = None
        self.servidor = data.SemServidor() if edicao.STEAM else data.Servidor()
        self.sincronia = None            # progresso unificado PC + celular (não vai nas edições de venda)
        self.conta = None
        if _sincronia_ligada():
            try:
                from .sincronia import Sincronia
                try:
                    from .conta import Conta
                    self.conta = Conta(data.SAVE_DIR)       # servidor da Ilha (internet); sem conta = Wi-Fi de casa
                except ImportError:
                    self.conta = None
                self.sincronia = Sincronia(self.save, data.SAVE_DIR, self.conta)
                self.sincronia.iniciar()
            except ImportError:
                pass
        self.rodando = True

    # -- pilha de estados (com transição deslizante entre telas cheias)
    def _transicao(self, de, para, direcao):
        if not (de and para) or getattr(de, "overlay", False) or getattr(para, "overlay", False):
            return
        if os.environ.get("ILHA_SEM_TRANSICAO") or (os.environ.get("SDL_VIDEODRIVER") == "dummy"
                                                    and not os.environ.get("ILHA_TRANSICAO")):
            return
        self._trans = [self.tela.copy(), direcao, 0]

    def push(self, est):
        self._transicao(self.pilha[-1] if self.pilha else None, est, 1)
        self.pilha.append(est)

    def pop(self):
        velho = self.pilha.pop() if self.pilha else None
        if self.pilha:
            self._transicao(velho, self.pilha[-1], -1)
            self.pilha[-1].ao_voltar()

    def trocar(self, est):
        velho = self.pilha.pop()
        self._transicao(velho, est, 1)
        self.pilha.append(est)

    def _desenhar_transicao(self):
        """A tela nova entra deslizando e empurra a antiga (12 quadros, desacelerando no fim)."""
        snap, d, t = self._trans
        t += 1
        self._trans[2] = t
        f = min(1.0, t / 12)
        e = 1 - (1 - f) ** 3
        off = int(W * e)
        novo = self.tela.copy()
        self.tela.blit(novo, (d * (W - off), 0))
        self.tela.blit(snap, (-d * off, 0))
        if f >= 1:
            self._trans = None

    def para_mundo(self, pos):
        return pos[0] * LW / W, pos[1] * LH / H

    # -- questões
    def gabarito(self, q):
        return self.save.gabarito(q)

    def corrigir_gabarito(self, q, letra):
        self.save.corrigir_gabarito(q, letra)
        if "server_qid" in q:
            threading.Thread(target=self.servidor.corrigir_gabarito, args=(q, letra), daemon=True).start()

    def registrar(self, q, ok):
        self.save.registrar(q, ok)
        if "server_qid" in q and self.servidor.jogador_id:
            threading.Thread(target=self.servidor.responder, args=(q, ok), daemon=True).start()

    def abrir_quiz(self, q, cb, contexto):
        self.push(Quiz(self, q, cb, contexto, self.pilha[-1] if self.pilha else None))

    # -- fases
    def jogar(self, questoes, titulo, chave, contexto, paleta_idx, proxima=None, repetir=None, briefing=None):
        """Mostra o resumo, abre a fase e no fim mostra resultado com próxima/repetir/voltar."""
        if not questoes:
            self.push(Mensagem(self, "Sem questões", "Não achei questões para esta fase."))
            return
        info = dict(briefing or {})
        info.setdefault("titulo", titulo)
        info.setdefault("materia", questoes[0].get("materia", ""))
        info.setdefault("texto", " ".join(filter(None, [questoes[0].get("subtema"), titulo])))
        self.push(Briefing(self, info, questoes,
                           lambda: self._iniciar_fase(questoes, titulo, chave, contexto, paleta_idx, proxima, repetir)))

    def _iniciar_fase(self, questoes, titulo, chave, contexto, paleta_idx, proxima=None, repetir=None):
        seed = random.randrange(1 << 30)
        profundidade = len(self.pilha)

        def fim(res):
            self.save.ganhar_moedas(res.get("moedas", 0))      # moedas valem mesmo se a fase não foi vencida
            if res["venceu"]:
                res["recorde_antes"] = self.save.nota_fase(chave, res["pontos"])
            if self.sincronia:
                self.sincronia.iniciar()
                if self.servidor.jogador_id and any("server_qid" in q for q in questoes):
                    threading.Thread(target=self.servidor.pontuacao, args=(res["pontos"],), daemon=True).start()
            del self.pilha[profundidade:]
            ops = []
            if proxima:
                ops.append(("Próxima fase", lambda: (self.pop(), proxima())))
            if repetir:
                ops.append(("Jogar de novo", lambda: (self.pop(), repetir())))
            ops.append(("Voltar", lambda: self.pop()))
            self.push(Resultado(self, res, ops))

        if self.save.config.get("estilo") == "questoes":      # 'Sem risadinha': só as questões, sem a fase
            self.push(SoQuestoes(self, questoes, titulo, contexto, fim))
            return
        jogo = Jogo(self, questoes, titulo, seed, paleta_idx, fim, contexto)
        self.push(Fase(self, jogo))
        self._musica(self.audio.iniciar_musica())

    # -- controles
    def _musica(self, nome):
        from .climas import CLIMAS, de_faixa
        cid = de_faixa(nome) if nome else None
        clima = CLIMAS[cid]["nome"] if cid else ""
        if nome and not edicao.STEAM:           # edições de venda (Steam/Android): sem nome de faixa na tela
            self.toast(f"♪ {nome}" + (f"  ·  clima: {clima}" if clima else "") + "  (N: próxima faixa)")
        elif clima:
            self.toast(f"Clima: {clima}")

    def toast(self, msg):
        self._toast = (msg, pygame.time.get_ticks() + 3500)

    def _desenhar_toast(self):
        if not self._toast:
            return
        msg, ate = self._toast
        if pygame.time.get_ticks() > ate:
            self._toast = None
            return
        t = self.f["med"].render(msg, True, (255, 255, 255))
        r = pygame.Rect(0, 0, t.get_width() + 40, 48)
        r.midbottom = (W // 2, H - 20)
        pygame.draw.rect(self.tela, art.K, r, border_radius=10)
        pygame.draw.rect(self.tela, (70, 90, 160), r.inflate(-6, -6), border_radius=8)
        self.tela.blit(t, (r.x + 20, r.y + 11))

    def _conectou(self, indice):
        try:
            joy, precisa, origem = self.pad.adicionar(indice)
        except pygame.error:
            return
        self.audio.tocar("resgate")
        if precisa and not edicao.ANDROID and not isinstance(self.pilha[-1] if self.pilha else None, ConfigControle):
            self.push(ConfigControle(self, joy, "modelo desconhecido: vamos mapear os botões"))
        else:
            self.toast(f"Controle conectado: {joy.get_name().strip()} ({origem}) · botão trocado? Menu > Controle")

    def reconectar_conta(self):
        """Depois de entrar/sair da conta: a sincronia passa a usar (ou deixa de usar) o servidor."""
        if self.sincronia is None or self.conta is None:
            return
        from .sincronia import Sincronia
        self.sincronia = Sincronia(self.save, data.SAVE_DIR, self.conta)
        self.sincronia.iniciar()
        for est in self.pilha:
            if hasattr(est, "ao_conectar"):
                est.ao_conectar()

    def _preencher_margens(self):
        """Faixas seguras (furo da câmera / barra de gestos): a cor média da borda da tela (céu em cima,
        chão embaixo), para o cenário continuar até a borda do aparelho sem listras."""
        cima, baixo = self.margens
        if cima:
            cor = pygame.transform.average_color(self.tela, (0, 0, W, 2))
            self.janela.fill(cor, (0, 0, W, cima))
        if baixo:
            cor = pygame.transform.average_color(self.tela, (0, H - 2, W, 2))
            self.janela.fill(cor, (0, cima + H, W, baixo))

    def _segundo_plano(self, sim):
        """Celular: saiu do app (home, ligação, tela apagada) = pausa a fase, cala o som e salva;
        voltou = som de volta, fase continua pausada até o jogador tocar em Continuar."""
        if sim == getattr(self, "_em_segundo_plano", False):
            return
        self._em_segundo_plano = sim
        if sim:
            topo = self.pilha[-1] if self.pilha else None
            if isinstance(topo, Fase) and not topo.jogo.pausado:
                topo.jogo.pausado = True
                topo.jogo.pausa_sel = 0
            try:
                self.save.salvar()
            except Exception:
                pass
        if pygame.mixer.get_init():
            if sim:
                pygame.mixer.music.pause()
                pygame.mixer.pause()
            else:
                pygame.mixer.music.unpause()
                pygame.mixer.unpause()

    def configurar_controle(self):
        js = self.pad.conectados()
        if not js:
            self.push(Mensagem(self, "Nenhum controle",
                               "Nenhum controle foi detectado. Conecte o controle USB: o jogo reconhece na hora "
                               "e, se o modelo for novo, abre este assistente sozinho."))
            return
        self.push(ConfigControle(self, js[0], "reconfigurando"))

    def alternar_tela_cheia(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            return
        self.save.config["tela_cheia"] = bool(pygame.display.is_fullscreen())
        self.save.salvar()

    def quadro(self):
        """Um quadro do laço principal (separado para os testes poderem dirigir o jogo)."""
        self.entrada.iniciar_frame()
        eventos = pygame.event.get()
        topo = self.pilha[-1]
        configurando = isinstance(topo, ConfigControle)
        for e in eventos:
            if e.type in (pygame.APP_WILLENTERBACKGROUND, pygame.APP_DIDENTERBACKGROUND, pygame.WINDOWFOCUSLOST,
                          pygame.WINDOWMINIMIZED) and edicao.ANDROID:
                self._segundo_plano(True)
            elif e.type in (pygame.APP_DIDENTERFOREGROUND, pygame.WINDOWFOCUSGAINED, pygame.WINDOWRESTORED) \
                    and edicao.ANDROID:
                self._segundo_plano(False)
            elif e.type == pygame.JOYDEVICEADDED:
                self._conectou(e.device_index)
            elif e.type == pygame.JOYDEVICEREMOVED:
                nome = self.pad.remover(e.instance_id)
                if nome:
                    self.toast(f"Controle desconectado: {nome}")
        if not configurando:
            eventos += self.pad.frame(pygame.time.get_ticks())
        if self.toque:
            na_fase = isinstance(topo, Fase)
            self.toque.passo = getattr(topo, "passo_rolagem", 46)   # a lista anda junto com o dedo
            eventos = self.toque.filtrar(eventos, na_fase, na_fase and topo.jogo.pausado,
                                         id(topo.jogo) if na_fase else None)
        acoes = [self.entrada.processar(e) for e in eventos]
        topo = self.pilha[-1]
        for e, ac in zip(eventos, acoes):
            if e.type == pygame.QUIT:
                self.rodando = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                self.alternar_tela_cheia()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_m and not isinstance(topo, (EntradaTexto, Quiz)):
                self.save.config["mudo"] = self.audio.alternar_mudo()
                self.save.salvar()
                if not self.audio.mudo and isinstance(topo, Fase):
                    self._musica(self.audio.iniciar_musica(False))
            elif e.type == MUSICA_FIM:
                self._musica(self.audio.fim_de_faixa())
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_n and isinstance(topo, Fase) \
                    and self.audio.tocando and self.audio.faixas:
                self._musica(self.audio.iniciar_musica())
            elif e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEWHEEL,
                            pygame.TEXTINPUT, PADEVENT, TOQUE) or \
                    (configurando and e.type in (pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION, pygame.JOYAXISMOTION)):
                if self.pilha and self.pilha[-1] is topo:
                    self.entrada.atual = ac
                    topo.evento(e, self.entrada)
                    self.entrada.atual = None
        if not self.pilha:
            return
        topo = self.pilha[-1]
        self.audio.abaixar(not isinstance(topo, Fase))
        # entrada "apertada" sem evento correspondente (ex.: pulo) chega via update
        topo.update(self.entrada)
        if self.sincronia:
            self.sincronia.passo()
            if self.sincronia.trouxe:
                self.sincronia.trouxe = False
                self.toast("Progresso do outro aparelho sincronizado")
                from . import loja
                loja.aplicar(self.save)
                if self.pilha and not isinstance(self.pilha[-1], (Fase, Quiz)):
                    self.pilha[-1].ao_voltar()          # menus recalculam dominadas/recordes
        if self.pilha:
            self.pilha[-1].draw(self.tela)
            if self.toque and isinstance(self.pilha[-1], Fase) and not self.pilha[-1].jogo.pausado:
                self.toque.desenhar(self.tela)
            if self.toque:
                # celular: botão ◀ Voltar sempre visível nos menus (a fase tem a pausa; a questão, os botões)
                self.toque.voltar_visivel = len(self.pilha) > 1 and not isinstance(
                    self.pilha[-1], (Fase, Quiz, Resultado, Carregando))
                if self.toque.voltar_visivel:
                    self.toque.desenhar_voltar(self.tela)
                self.toque.desenhar_ondas(self.tela)
            if self._trans:
                self._desenhar_transicao()
            self._desenhar_toast()
        self._preencher_margens()
        pygame.display.flip()
        self.relogio.tick(60)
        cap = os.environ.get("ILHA_CAPTURA")     # teste do executável: "arquivo.png,quadros" salva e fecha
        if cap:
            self._n_quadros = getattr(self, "_n_quadros", 0) + 1
            arq, _, n = cap.partition(",")
            if self._n_quadros >= int(n or 90):
                pygame.image.save(self.tela, arq)
                self.rodando = False

    def loop(self, gasometria=False, ventilacao=False, hipercalemia=False, farmacologia=False, ic=False, reumatologia=False,
             prova_cm=False, mfc=False):
        from .menus import menu_principal, abrir_gasometria, abrir_ventilacao, abrir_hipercalemia, abrir_farmacologia
        if edicao.VESTIBULANDO:
            from .vestibulando import menu_vestibulando
            self.push(menu_vestibulando(self))
        elif edicao.ANDROID:
            from .android import menu_android
            self.push(menu_android(self))
        elif edicao.STEAM:
            from .steam import menu_steam
            self.push(menu_steam(self))
        else:
            self.push(menu_principal(self))
        if prova_cm and not edicao.STEAM:
            from .menus import abrir_internato
            abrir_internato(self)
        elif mfc and not edicao.STEAM:
            from .menus import abrir_mfc
            abrir_mfc(self)
        elif gasometria and not edicao.STEAM:
            abrir_gasometria(self)
        elif ventilacao:
            abrir_ventilacao(self)
        elif hipercalemia and not edicao.STEAM:
            abrir_hipercalemia(self)
        elif farmacologia and not edicao.STEAM:
            abrir_farmacologia(self)
        elif ic and not edicao.STEAM:
            from .menus import IC, abrir_tema
            abrir_tema(self, IC)
        elif reumatologia and not edicao.STEAM:
            from .menus import REUMATO, abrir_tema
            abrir_tema(self, REUMATO)
        if not os.environ.get("ILHA_SEM_ESCOLHA"):
            from .personagens import abrir_escolha
            abrir_escolha(self)          # escolha do personagem por cima de tudo, ao abrir o jogo
        while self.rodando and self.pilha:
            self.quadro()
        if self.sincronia:
            self.sincronia.finalizar()
        self.servidor.encerrar()
        pygame.quit()
