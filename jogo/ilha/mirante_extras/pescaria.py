"""A pescaria — um deque pequeno com uma vara encostada.

Os peixes deste lago são as questões que você errou e ainda não acertou de novo. Lançar a linha abre uma vista
do lago: a boia (luminosa, porque é noite) fica boiando de 2 a 6 segundos, dá umas beliscadas e, de repente,
afunda com um "plop". Há uns 0,8 s para puxar (Enter, ↑ ou clique). Se pegar, sai da água a questão de erro mais
antigo ainda não corrigida — enunciado, alternativas com a certa destacada e o comentário, quando houver. Cada
peixe seguinte é o próximo erro mais antigo. Nada é registrado no save: é só para relembrar.

Sem banco carregado, ou sem erros pendentes, o lago devolve uma bota velha."""
import math
import random
import re
import time

import pygame

from . import Base
from .. import art
from ..mirante import GY, HZ, LUZ, MADEIRA, MADEIRA_ESC, MARGEM_ESCURA, NOITE_BASE, NOITE_MEIO, NOITE_TOPO, WW
from ..ui import AMARELO, H, RETRATO, TINTA, W, painel, quebrar, sombra

FRACAO = 0.381
PAPEL = (255, 250, 236)
ROTULOS_COMENT = {"Por quê:": (30, 120, 40), "E as outras:": (170, 60, 40), "Para fixar:": (120, 70, 160)}

PAL = {"O": (16, 18, 40), "b": (88, 136, 200), "f": (58, 92, 168), "l": (196, 214, 236), "w": (250, 250, 255),
       "K": (12, 12, 24), "m": (104, 72, 52), "h": (146, 110, 80), "s": (60, 44, 40), "a": (150, 200, 255)}
PEIXE = [
    "......OOOO......",
    "....OOffffOO..OO",
    "..OObbbbbbbbOOfO",
    ".ObwKbbbbbbbbbfO",
    "Obbbbbbbbbbbbbf.",
    ".Olllllllbbbbbf.",
    "..OOllllllbbOOfO",
    "....OOOOOOOO..OO",
]
BOTA = [
    "..OOOOOO.....",
    "..OmmmmO.....",
    "..OmhmmO.....",
    "..OmhmmO..a..",
    "..OmmmmO.....",
    "..OmmmmmOO...",
    ".OmmmmmmmmOO.",
    ".OmhmmmmmmmmO",
    ".OmmmmmmmmmmO",
    ".OssssssssssO",
    "..OOOOOOOOOO.",
]

BOTAS_SEM_BANCO = [
    "Uma bota velha, cheia de água. O banco de questões não está carregado agora, então o lago só tem botas.",
]
BOTAS_SEM_ERROS = [
    "Uma bota velha, número 42, sem o par. Não há questão errada esperando para ser acertada de novo, "
    "e os peixes deste lago são feitos só disso.",
    "Outra bota. Talvez seja o par da primeira. Enquanto nenhum erro ficar pendente, é o que este lago tem.",
    "Uma bota com um girino morando dentro. Ele parece satisfeito. Peixe mesmo, só quando houver um erro "
    "ainda não corrigido.",
]

# tempos em quadros (60 por segundo)
T_LANCE = 36
JANELA = 48                                              # ~0,8 s para puxar depois do plop
T_SALTO = 54


def _aa_disco(raio, cor_cima, cor_baixo, contorno):
    """Corpo da boia em alta resolução: desenhado 4× maior e reduzido (bordas suaves)."""
    k = 4
    d = (raio * 2 + 2) * k
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    pygame.draw.circle(s, contorno, (c, c), raio * k + k)
    pygame.draw.circle(s, cor_baixo, (c, c), raio * k - k)
    meia = pygame.Surface((d, d // 2), pygame.SRCALPHA)
    pygame.draw.circle(meia, cor_cima, (c, c), raio * k - k)
    s.blit(meia, (0, 0))
    pygame.draw.line(s, contorno, (c - raio * k, c), (c + raio * k, c), k)
    pygame.draw.circle(s, (255, 255, 255, 150), (c - raio * k // 3, c - raio * k // 2), raio * k // 4)
    return pygame.transform.smoothscale(s, (d // k, d // k))


def _brilho_hr(raio, cor, forca):
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1))
    for r in range(raio, 0, -1):
        f = (1 - r / raio) ** 2 * forca
        pygame.draw.circle(s, tuple(min(255, int(c * f)) for c in cor), (raio, raio), r)
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.lugares = [("pescaria", WW * FRACAO, "pescar no deque")]
        self.ativo = False
        self.estado = None
        self.vez = 0                                     # quantos peixes já saíram nesta visita
        self.bota_i = 0
        self.vista = None                                # superfícies do modal: feitas na primeira pescaria
        self.plop = None
        self.ultimo_ok = -99

    # ------------------------------------------------------------------ mundo (baixa resolução)
    def draw_lago(self, m, cam):
        px = WW * FRACAO - cam
        if not -20 < px < m.get_width() + 20:
            return
        t = self.mirante.t
        for k in range(1, 9):                            # reflexo da lanterninha na água
            if (k * 7 + t // 7) % 3:
                dx = math.sin(k * 1.3 + t * 0.08)
                m.fill((60, 46, 22), (px + 7 + dx - 1, GY - 9 + k * 1.1 - 9, 2 + (k > 4), 1),
                       special_flags=pygame.BLEND_RGB_ADD)

    def draw_margem(self, m, cam):
        px = WW * FRACAO - cam
        if not -20 < px < m.get_width() + 20:
            return
        t = self.mirante.t
        topo = GY - 9
        # deque: tablado curto entrando no lago, com dois esteios
        pygame.draw.polygon(m, MADEIRA_ESC, [(px - 9, GY + 3), (px + 7, GY + 3), (px + 5, topo), (px - 6, topo)])
        for k in range(5):
            f = k / 5
            y = GY + 2 - (GY + 2 - topo) * f
            pygame.draw.line(m, MADEIRA, (px - 9 + 3 * f, y), (px + 7 - 2 * f, y))
        for lx in (px - 6, px + 4):
            pygame.draw.line(m, MADEIRA_ESC, (lx, topo - 1), (lx, topo + 5))
        # estaca com lanterninha
        sx = px + 9
        pygame.draw.line(m, MADEIRA_ESC, (sx, GY + 6), (sx, GY - 9))
        pygame.draw.rect(m, (40, 34, 50), (sx - 1, GY - 13, 3, 4))
        luz = (255, 220, 140) if (t // 50) % 9 else (240, 190, 110)
        m.fill(luz, (sx, GY - 12, 1, 2))
        m.blit(self.mirante.halo[9], (sx - 9, GY - 20), special_flags=pygame.BLEND_RGB_ADD)
        # a vara, encostada na estaca: cabo de cortiça, molinete e a linha pendurada com a boia
        base, ponta = (px + 14, GY + 9), (px - 3, GY - 27)
        pygame.draw.line(m, (66, 60, 84), base, ponta)
        pygame.draw.line(m, (170, 128, 88), base, (base[0] - 2, base[1] - 4))
        m.set_at((base[0] - 1, base[1] - 6), (150, 160, 180))
        bal = math.sin(t * 0.04) * 0.8
        fio_y = ponta[1] + 10
        for y in range(ponta[1] + 1, fio_y):
            m.set_at((int(ponta[0] + bal * (y - ponta[1]) / 10), y), (120, 130, 160))
        bx = int(ponta[0] + bal)
        m.set_at((bx, fio_y), (220, 70, 70))
        m.set_at((bx, fio_y + 1), (235, 235, 240))
        # baldinho
        pygame.draw.rect(m, (70, 84, 100), (px - 14, GY + 5, 4, 4))
        pygame.draw.line(m, (110, 126, 140), (px - 14, GY + 5), (px - 11, GY + 5))
        m.set_at((px - 15, GY + 9), MARGEM_ESCURA)

    # ------------------------------------------------------------------ interação
    def interagir(self, nome):
        if self.vista is None:
            self._preparar()
        self.ativo = True
        self.mirante.abrir_modal(self)
        self._lancar()

    def _questoes(self):
        """Erros pendentes (última resposta errada) que existem no banco, do mais antigo para o mais novo."""
        app = self.mirante.app
        banco = getattr(app, "banco", None)
        if banco is None:
            return None
        q = (app.save.d.get("q") or {}) if isinstance(app.save.d, dict) else {}
        pend = []
        for qid, st in q.items():
            if isinstance(st, dict) and st.get("e", 0) and not st.get("ok") and qid in banco.por_id:
                pend.append((st.get("ult", 0) or 0, qid, st))
        pend.sort(key=lambda p: (p[0], p[1]))
        return [(banco.por_id[qid], st) for _, qid, st in pend]

    def _lancar(self):
        self.estado, self.f = "lance", 0
        rng = random.Random()
        self.alvo = (W * rng.uniform(0.5, 0.74 if not RETRATO else 0.78),
                     self.hy + (H - self.hy) * rng.uniform(0.24, 0.42))
        self.espera = rng.randint(120, 360)
        self.beliscos = sorted(rng.sample(range(40, max(41, self.espera - 30)), rng.randint(0, 2)))
        self.ondas = []
        self.afunda = 0.0
        self.msg = None
        self.rolagem = 0
        self._som("pulo")

    def _puxar(self):
        if self.estado == "espera":
            self.estado, self.f = "fugiu", 0
            self.msg = ["Puxou cedo: a boia ainda nem tinha afundado.", "O peixe se assustou com a linha."]
            self._som("quica")
        elif self.estado == "fisga":
            lista = self._questoes()
            if lista:
                q, st = lista[self.vez % len(lista)]
                self.vez += 1
                self.peixe = (q, st, len(lista))
                self.carta = self._montar_carta(q, st)
                self.bota = None
            else:
                self.peixe = None
                frases = BOTAS_SEM_BANCO if lista is None else BOTAS_SEM_ERROS
                self.bota = frases[self.bota_i % len(frases)]
                self.bota_i += 1
            self.estado, self.f = "salto", 0
            self._som("moeda")

    def evento_modal(self, e, inp):
        if inp.foi("voltar"):
            self.ativo = False
            return False
        clique = e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1
        ok = inp.foi("ok") or inp.foi("pulo") or clique
        if self.estado == "carta":
            if e.type == pygame.MOUSEWHEEL:
                self._rolar(-e.y * 60)
            elif e.type == pygame.MOUSEMOTION and e.buttons[0]:
                self._rolar(-e.rel[1])
            elif inp.foi("baixo") or inp.foi("cima"):
                self._rolar(90 if inp.foi("baixo") else -90)
            elif clique:
                if self.bt_sair.collidepoint(e.pos):
                    self.ativo = False
                    return False
                if self.bt_mais.collidepoint(e.pos):
                    self._lancar()
            elif ok:
                self._lancar()
            return True
        if not (ok or inp.foi("cima")):
            return True
        if self.mirante.t - self.ultimo_ok < 8:          # toque que vira clique + ação: conta uma vez só
            return True
        self.ultimo_ok = self.mirante.t
        if self.estado in ("espera", "fisga"):
            self._puxar()
        elif self.estado in ("fugiu", "bota"):
            self._lancar()
        elif self.estado == "salto":
            self.estado = "carta" if self.peixe else "bota"
        return True

    def _rolar(self, d):
        self.rolagem = max(0, min(self.max_rol, self.rolagem + d))

    def update(self):
        if not self.ativo:
            return
        if self.mirante.modal is not self:
            self.ativo = False
            return
        self.f += 1
        t = self.mirante.t
        if self.estado == "lance" and self.f >= T_LANCE:
            self.estado, self.f = "espera", 0
            self.ondas.append([0, 1.0])
            self._som("quica")
        elif self.estado == "espera":
            if self.f in self.beliscos:
                self.ondas.append([0, 0.5])
            if self.f >= self.espera:
                self.estado, self.f = "fisga", 0
                self.ondas += [[0, 1.4], [-6, 1.0]]
                self._plop()
        elif self.estado == "fisga" and self.f >= JANELA:
            self.estado, self.f = "fugiu", 0
            self.msg = ["O peixe fugiu.", "Ele beliscou, mas a linha demorou a subir."]
        elif self.estado == "salto" and self.f >= T_SALTO:
            self.estado = "carta" if self.peixe else "bota"
        elif self.estado == "espera" and t % 100 == 0:
            self.ondas.append([0, 0.45])
        # boia: quanto está afundada (px)
        if self.estado == "fisga":
            alvo = self.alt_boia + 6
        elif self.estado == "espera" and any(0 <= self.f - b < 10 for b in self.beliscos):
            alvo = 5
        elif self.estado in ("salto", "carta", "bota"):
            alvo = self.alt_boia + 6
        else:
            alvo = 0
        self.afunda += (alvo - self.afunda) * (0.45 if alvo > self.afunda else 0.12)
        for o in self.ondas:
            o[0] += 1
        self.ondas = [o for o in self.ondas if o[0] < 70]

    # ------------------------------------------------------------------ som
    def _som(self, nome):
        try:
            self.mirante.app.audio.tocar(nome)
        except Exception:
            pass

    def _plop(self):
        au = self.mirante.app.audio
        if not (au.ok and not au.mudo):
            return
        try:
            if self.plop is None:
                import numpy as np
                freq, _, canais = pygame.mixer.get_init()
                n = int(freq * 0.16)
                tt = np.arange(n) / freq
                f0 = 900 * np.exp(-tt * 22) + 140                    # bolha: o tom cai depressa
                fase = 2 * np.pi * np.cumsum(f0) / freq
                env = np.minimum(1, tt * 400) * np.exp(-tt * 28)
                ruido = np.random.default_rng(3).normal(0, 1, n) * np.exp(-tt * 90) * 0.25
                onda = (np.sin(fase) * env + ruido) * 0.12 * 32767
                onda = onda.astype(np.int16)
                arr = np.repeat(onda[:, None], canais, axis=1) if canais > 1 else onda
                self.plop = pygame.sndarray.make_sound(np.ascontiguousarray(arr))
            self.plop.play()
        except Exception:
            self.plop = False if self.plop is None else self.plop

    # ------------------------------------------------------------------ modal (alta resolução)
    def _preparar(self):
        """Vista do lago em pixel art (¼ da tela, ampliada), boia em alta resolução e sprites."""
        lw, lh = W // 4, H // 4
        hy = int(lh * (0.36 if RETRATO else 0.42))
        self.hy = hy * 4
        s = pygame.Surface((lw, lh))
        for y in range(hy):
            f = y / max(1, hy - 1)
            a, b, k = (NOITE_TOPO, NOITE_MEIO, f / 0.6) if f < 0.6 else (NOITE_MEIO, NOITE_BASE, (f - 0.6) / 0.4)
            s.fill(art.mix(a, b, k), (0, y, lw, 1))
        rng = random.Random(38)
        for _ in range(lw * hy // 40):
            x, y = rng.randrange(lw), rng.randrange(int(hy * 0.85))
            v = rng.randint(60, 200)
            s.set_at((x, y), (v, v, min(255, v + 40)))
        lx, ly = int(lw * 0.8), int(hy * 0.3)
        lua = _brilho_hr(16, (120, 116, 90), 0.5)
        s.blit(lua, (lx - 16, ly - 16), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(s, (244, 238, 214), (lx, ly), 6)
        pygame.draw.circle(s, (0, 0, 0), (lx + 3, ly - 2), 5)
        pygame.draw.circle(s, art.mix(NOITE_TOPO, NOITE_MEIO, 0.4), (lx + 3, ly - 2), 5)
        for cor, alt, sem in (((52, 44, 102), 0.22, 2), ((28, 26, 62), 0.12, 7)):   # montes
            fases = [random.Random(sem + i).uniform(0, 6.3) for i in range(3)]
            pts = [(0, hy)]
            for x in range(lw + 1):
                h = math.sin(x * 0.03 + fases[0]) * 0.5 + math.sin(x * 0.08 + fases[1]) * 0.3 + math.sin(x * 0.2 + fases[2]) * 0.2
                pts.append((x, hy - hy * alt * (0.6 + 0.4 * h)))
            pts.append((lw, hy))
            pygame.draw.polygon(s, cor, pts)
        for y in range(hy, lh):                          # água: escurece para perto
            f = (y - hy) / max(1, lh - hy)
            s.fill(art.mix((34, 34, 84), (8, 12, 30), f ** 0.7), (0, y, lw, 1))
            if y % 2 == 0:
                for x in range((y // 2) % 3, lw, 3 + int(f * 4)):
                    if rng.random() < 0.35:
                        s.set_at((x, y), art.mix((54, 56, 120), (16, 20, 48), f))
        pygame.draw.line(s, (90, 80, 150), (0, hy), (lw, hy))
        for y in range(hy + 1, lh, 2):                   # coluna da lua na água
            f = (y - hy) / (lh - hy)
            meia = 1 + f * 5 + rng.random() * 2
            if rng.random() < 0.8:
                s.fill(art.mix((200, 196, 170), (40, 44, 90), 0.35 + f * 0.6), (lx - meia + rng.randint(-1, 1), y, meia * 2, 1))
        # primeiro plano: tábuas do deque, estaca com lanterna e juncos
        dy, dx = int(lh * 0.86), int(lw * (0.34 if RETRATO else 0.3))
        pygame.draw.polygon(s, MADEIRA_ESC, [(0, dy - 2), (dx, dy), (dx + 4, lh), (0, lh)])
        for k, y in enumerate(range(dy, lh, 4)):
            pygame.draw.line(s, MADEIRA, (0, y), (dx + 1 + (y - dy) // 4, y + 1))
            s.set_at(((k * 13) % max(1, dx), y + 1), MADEIRA_ESC)
        pygame.draw.rect(s, MADEIRA_ESC, (dx - 3, dy - 22, 3, 24))
        pygame.draw.rect(s, (40, 34, 50), (dx - 4, dy - 27, 5, 6))
        s.fill((255, 220, 140), (dx - 3, dy - 25, 3, 3))
        s.blit(_brilho_hr(22, LUZ, 0.5), (dx - 24, dy - 46), special_flags=pygame.BLEND_RGB_ADD)
        for k in range(18):
            x = lw - 2 - rng.randrange(int(lw * 0.22))
            h = rng.randint(8, 22)
            pygame.draw.line(s, (10, 16, 26), (x, lh), (x + rng.randint(-2, 2), lh - h))
        self.vista = pygame.transform.scale(s, (W, H))
        # boia luminosa
        self.r_boia = 11 if not RETRATO else 13
        self.disco = _aa_disco(self.r_boia, (226, 64, 60), (240, 240, 236), (24, 20, 40))
        self.alt_boia = self.r_boia * 2 + 16
        b = pygame.Surface((self.disco.get_width(), self.alt_boia + 6), pygame.SRCALPHA)
        cx = b.get_width() // 2
        pygame.draw.line(b, (30, 26, 44), (cx, 2), (cx, 18), 3)
        pygame.draw.circle(b, (255, 236, 160), (cx, 3), 3)
        b.blit(self.disco, (0, 14))
        self.boia = b
        refl = pygame.transform.flip(b, False, True)
        refl.fill((150, 150, 210, 70), special_flags=pygame.BLEND_RGBA_MULT)
        self.reflexo = refl
        self.brilho_boia = _brilho_hr(26, LUZ, 0.45)
        self.peixe_spr = pygame.transform.scale_by(art.spr(PEIXE, PAL), 6)
        self.bota_spr = pygame.transform.scale_by(art.spr(BOTA, PAL), 6)
        self.max_rol = 0

    def _ponta(self):
        base = (W * (0.07 if RETRATO else 0.1), H * 1.01)
        ponta = [W * (0.36 if RETRATO else 0.33), H * (0.42 if RETRATO else 0.36)]
        if self.estado == "fisga":
            ponta[1] += 22 * min(1, self.f / 6) + math.sin(self.f * 1.7) * 4
        elif self.estado == "salto":
            ponta[1] -= 26 * max(0, 1 - self.f / 20)
        return base, ponta

    def _pos_boia(self):
        _, ponta = self._ponta()
        if self.estado == "lance":
            k = min(1, self.f / T_LANCE)
            x = ponta[0] + (self.alvo[0] - ponta[0]) * k
            y = ponta[1] + (self.alvo[1] - ponta[1]) * k - H * 0.16 * math.sin(math.pi * k)
            return x, y, False
        bob = math.sin(self.mirante.t * 0.07) * 2.2 if self.estado in ("espera", "fugiu") else 0
        return self.alvo[0], self.alvo[1] + bob, True

    def draw_modal(self, tela):
        if self.vista is None:
            return
        f = self.mirante.app.f
        t = self.mirante.t
        tela.blit(self.vista, (0, 0))
        rng = random.Random(t // 10)                      # cintilado na água
        for _ in range(14):
            y = rng.randrange(self.hy + 6, H - 20)
            x = rng.randrange(W)
            k = (y - self.hy) / (H - self.hy)
            tela.fill((24, 26, 50), (x, y, 8 + int(k * 26), 2), special_flags=pygame.BLEND_RGB_ADD)
        if self.estado in ("carta", "bota"):
            self._draw_vara(tela)
            véu = pygame.Surface((W, H), pygame.SRCALPHA)
            véu.fill((6, 8, 24, 150))
            tela.blit(véu, (0, 0))
            if self.estado == "carta":
                self._draw_carta(tela)
            else:
                self._draw_bota(tela)
            return
        bx, by, na_agua = self._pos_boia()
        wy = self.alvo[1]
        for idade, forca in self.ondas:                   # anéis na água
            raio = 8 + idade * 1.4 * (1 + forca * 0.4)
            a = max(0.0, 1 - idade / 70) * min(1.0, forca)
            if a <= 0:
                continue
            cor = tuple(int(c * a) for c in (110, 120, 190))
            r = pygame.Rect(0, 0, raio * 2, raio * 0.5)
            r.center = (bx, wy + 2)
            pygame.draw.ellipse(tela, cor, r, 2)
            tela.fill(cor, r, special_flags=pygame.BLEND_RGB_ADD) if False else None
        self._draw_vara(tela, (bx, by - self.alt_boia // 2 - 4 + self.afunda if na_agua else by))
        if self.estado != "salto":
            self._draw_boia(tela, bx, by, na_agua)
        if self.estado == "fisga":
            pulo = abs(math.sin(self.f * 0.35)) * 10
            sombra(tela, "!", f["titulo"], AMARELO, (bx, wy - self.alt_boia - 70 - pulo), centro=True, sombra_cor=(20, 14, 30))
        if self.estado == "salto":
            self._draw_salto(tela, bx, wy)
        # textos
        if self.estado == "fugiu" and self.msg:
            self._caixa(tela, self.msg, "Enter ou clique para lançar de novo · Esc guarda a vara")
        else:
            dica = {"lance": "lançando a linha…", "espera": "espere a boia afundar e puxe: Enter, ↑ ou clique",
                    "fisga": "agora!", "salto": ""}.get(self.estado, "")
            if dica:
                sombra(tela, dica, f["med"], (230, 230, 255), (W // 2, H - 64), centro=True, sombra_cor=(10, 10, 30))
            sombra(tela, "Esc guarda a vara", f["peq"], (160, 160, 200), (W // 2, H - 30), centro=True, sombra_cor=(10, 10, 30))

    def _draw_vara(self, tela, boia=None):
        base, ponta = self._ponta()
        meio = ((base[0] + ponta[0]) / 2 + 6, (base[1] + ponta[1]) / 2 + (6 if self.estado == "fisga" else 0))
        pygame.draw.lines(tela, (24, 20, 36), False, [base, meio, ponta], 9)
        pygame.draw.lines(tela, (86, 76, 108), False, [base, meio, ponta], 5)
        pygame.draw.aaline(tela, (140, 130, 170), (meio[0] - 2, meio[1]), (ponta[0] - 1, ponta[1]))
        cabo = (base[0] + (meio[0] - base[0]) * 0.35, base[1] + (meio[1] - base[1]) * 0.35)
        pygame.draw.line(tela, (176, 132, 90), base, cabo, 11)
        pygame.draw.circle(tela, (150, 160, 184), (int(cabo[0] + 14), int(cabo[1] + 6)), 10)
        pygame.draw.circle(tela, (40, 40, 60), (int(cabo[0] + 14), int(cabo[1] + 6)), 10, 2)
        if boia is None:
            return
        # linha com barriga (Bézier quadrática), mais esticada quando o peixe puxa
        tensa = self.estado in ("fisga", "lance")
        cx = (ponta[0] + boia[0]) / 2
        cy = max(ponta[1], boia[1]) + (4 if tensa else 34)
        pts = []
        for i in range(17):
            k = i / 16
            pts.append(((1 - k) ** 2 * ponta[0] + 2 * (1 - k) * k * cx + k * k * boia[0],
                        (1 - k) ** 2 * ponta[1] + 2 * (1 - k) * k * cy + k * k * boia[1]))
        pygame.draw.aalines(tela, (186, 196, 230), False, pts)

    def _draw_boia(self, tela, bx, by, na_agua):
        b = self.boia
        x0 = int(bx - b.get_width() / 2)
        topo = int(by - self.alt_boia // 2 - 4 + self.afunda)    # centro do disco na linha d'água
        if not na_agua:
            tela.blit(b, (x0, int(by - b.get_height() / 2)))
            tela.blit(self.brilho_boia, (bx - 26, by - b.get_height() / 2 - 23), special_flags=pygame.BLEND_RGB_ADD)
            return
        wy = int(self.alvo[1] + (by - self.alvo[1]))
        vis = wy - topo
        if vis > 0:
            tela.blit(b, (x0, topo), (0, 0, b.get_width(), min(vis, b.get_height())))
            rf = self.reflexo
            tela.blit(rf, (x0, wy + 1), (0, rf.get_height() - vis, rf.get_width(), min(vis, rf.get_height())))
            if vis > 6:
                tela.blit(self.brilho_boia, (bx - 26, topo - 23), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.line(tela, (130, 140, 200), (bx - self.r_boia - 4, wy), (bx + self.r_boia + 4, wy), 2)

    def _draw_salto(self, tela, bx, wy):
        k = min(1, self.f / T_SALTO)
        spr = self.peixe_spr if self.peixe else self.bota_spr
        dest = (W * 0.5, H * 0.3)
        x = bx + (dest[0] - bx) * k
        y = wy + (dest[1] - wy) * k - H * 0.18 * math.sin(math.pi * k)
        giro = math.sin(self.f * 0.4) * 18 * (1 - k)
        s = pygame.transform.rotate(spr, giro)
        tela.blit(s, (x - s.get_width() / 2, y - s.get_height() / 2))
        rng = random.Random(7)
        for i in range(10):                               # respingos
            a = rng.uniform(0.3, 2.8)
            d = self.f * rng.uniform(2.0, 4.5)
            gx = bx + math.cos(a) * d
            gy = wy - math.sin(a) * d + 0.09 * self.f ** 2
            if gy < wy + 4:
                pygame.draw.circle(tela, (170, 190, 240), (int(gx), int(gy)), 3)

    def _caixa(self, tela, linhas, rodape):
        f = self.mirante.app.f
        larg = min(W - 40, max(f["med"].size(l)[0] for l in linhas + [rodape]) + 60)
        r = pygame.Rect(0, 0, larg, 40 + 32 * len(linhas) + 30)
        r.midtop = (W // 2, 40 if not RETRATO else 90)
        painel(tela, r)
        for i, ln in enumerate(linhas):
            tela.blit(f["med"].render(ln, True, TINTA), (r.centerx - f["med"].size(ln)[0] // 2, r.y + 20 + 32 * i))
        tela.blit(f["peq"].render(rodape, True, (120, 100, 100)), (r.centerx - f["peq"].size(rodape)[0] // 2, r.bottom - 38))

    # ------------------------------------------------------------------ a carta (a questão pescada)
    def _area_carta(self):
        if RETRATO:
            return pygame.Rect(16, 70, W - 32, H - 140)
        larg = min(W - 120, 1080)
        return pygame.Rect((W - larg) // 2, 28, larg, H - 56)

    def _montar_carta(self, q, st):
        """Pré-renderiza o conteúdo rolável: enunciado, alternativas (a certa em verde) e comentário."""
        f = self.mirante.app.f
        r = self._area_carta()
        larg = r.w - 60
        tw = larg - 20
        blocos = []                                       # (altura, função de desenho)
        y = 0
        partes = []
        mat = " · ".join(x for x in (q.get("materia"), q.get("subtema")) if x)
        if mat:
            partes.append(("rot", mat))
        enun = re.sub(r"\[\[img:[^\]]+\]\]", "[figura da prova, não mostrada aqui]", q.get("enunciado", "") or "")
        surf_h = 20
        linhas_en = quebrar(enun.strip(), f["q"], tw)
        try:
            certa = self.mirante.app.save.gabarito(q)
        except Exception:
            certa = q.get("gab")
        alts = []
        for letra, txt in q.get("alts") or []:
            lns = quebrar(str(txt), f["q"], tw - 70)
            alts.append((letra, lns, letra == certa))
        coment = q.get("coment") or ""
        lns_c = quebrar(coment, f["q"], tw - 20) if coment else []
        # altura total
        alt = (30 if mat else 0) + 27 * len(linhas_en) + 16
        alt += sum(max(40, 18 + 27 * len(l)) + 10 for _, l, _ in alts)
        if lns_c:
            alt += 10 + 50 + 27 * len(lns_c)
        alt += surf_h
        s = pygame.Surface((larg, alt))
        s.fill(PAPEL)
        y = 4
        if mat:
            s.blit(f["peq"].render(mat[:120], True, (130, 100, 90)), (6, y))
            y += 30
        for ln in linhas_en:
            s.blit(f["q"].render(ln, True, TINTA), (6, y))
            y += 27
        y += 12
        for letra, lns, ok in alts:
            h = max(40, 18 + 27 * len(lns))
            caixa = pygame.Rect(2, y, larg - 8, h)
            pygame.draw.rect(s, (214, 242, 214) if ok else (246, 238, 222), caixa, border_radius=10)
            pygame.draw.rect(s, (60, 150, 70) if ok else (206, 192, 170), caixa, 3 if ok else 2, border_radius=10)
            bola = (caixa.x + 26, caixa.y + 20)
            pygame.draw.circle(s, (60, 150, 70) if ok else (226, 214, 196), bola, 15)
            lt = f["med"].render(str(letra), True, (255, 255, 255) if ok else TINTA)
            s.blit(lt, (bola[0] - lt.get_width() // 2, bola[1] - lt.get_height() // 2))
            for j, ln in enumerate(lns):
                s.blit(f["q"].render(ln, True, (20, 70, 30) if ok else TINTA), (caixa.x + 56, caixa.y + 9 + 27 * j))
            if ok:
                tag = f["peq"].render("✓ certa", True, (40, 120, 50))
                s.blit(tag, (caixa.right - tag.get_width() - 12, caixa.bottom - tag.get_height() - 4))
            y += h + 10
        if lns_c:
            y += 6
            caixa = pygame.Rect(2, y, larg - 8, 44 + 27 * len(lns_c))
            pygame.draw.rect(s, (226, 236, 255), caixa, border_radius=10)
            pygame.draw.rect(s, (70, 100, 170), caixa, 2, border_radius=10)
            s.blit(f["med"].render("Comentário", True, (50, 80, 150)), (caixa.x + 14, caixa.y + 8))
            for j, ln in enumerate(lns_c):
                x, yl = caixa.x + 14, caixa.y + 40 + 27 * j
                rot = next((k for k in ROTULOS_COMENT if ln.startswith(k)), None)
                if rot:
                    tr = f["q"].render(rot, True, ROTULOS_COMENT[rot])
                    s.blit(tr, (x, yl))
                    x, ln = x + tr.get_width(), ln[len(rot):]
                s.blit(f["q"].render(ln, True, (30, 40, 70)), (x, yl))
        return s

    def _draw_carta(self, tela):
        f = self.mirante.app.f
        q, st, total = self.peixe
        r = self._area_carta()
        painel(tela, r)
        icone = pygame.transform.scale_by(self.peixe_spr, 0.5)
        tela.blit(icone, (r.x + 24, r.y + 22))
        tela.blit(f["med"].render("Fisgou uma questão que você errou", True, (40, 60, 120)), (r.x + 80, r.y + 16))
        try:
            quando = time.strftime("%d/%m/%Y", time.localtime(float(st.get("ult") or 0)))
        except Exception:
            quando = "?"
        e, c = int(st.get("e", 0) or 0), int(st.get("c", 0) or 0)
        n = self.vez % total or total
        sub = (f"última resposta errada em {quando} · {e} erro{'s' if e != 1 else ''}, "
               f"{c} acerto{'s' if c != 1 else ''} · peixe {n} de {total}")
        tela.blit(f["peq"].render(sub, True, (120, 100, 100)), (r.x + 80, r.y + 46))
        # área rolável
        vis = pygame.Rect(r.x + 30, r.y + 80, r.w - 60, r.h - 80 - 70)
        self.max_rol = max(0, self.carta.get_height() - vis.h)
        self.rolagem = min(self.rolagem, self.max_rol)
        tela.blit(self.carta, vis.topleft, (0, self.rolagem, vis.w, vis.h))
        if self.max_rol:
            trilho = pygame.Rect(r.right - 22, vis.y, 6, vis.h)
            pygame.draw.rect(tela, (226, 214, 196), trilho, border_radius=3)
            alt = max(30, vis.h * vis.h // self.carta.get_height())
            yb = vis.y + (vis.h - alt) * self.rolagem // self.max_rol
            pygame.draw.rect(tela, (150, 120, 100), (trilho.x, yb, 6, alt), border_radius=3)
            if self.rolagem < self.max_rol:
                tela.blit(f["peq"].render("▼ role para ver mais (↓ / roda do mouse)", True, (150, 120, 100)),
                          (vis.x, vis.bottom + 4))
        # botões
        self._botoes(tela, r, "Só leitura: nada é registrado no save.")

    def _botoes(self, tela, r, nota):
        f = self.mirante.app.f
        y = r.bottom - 52
        self.bt_mais = pygame.Rect(0, 0, 250, 38)
        self.bt_sair = pygame.Rect(0, 0, 230, 38)
        self.bt_sair.bottomright = (r.right - 28, r.bottom - 18)
        self.bt_mais.bottomright = (self.bt_sair.x - 14, r.bottom - 18)
        for bt, txt, cor in ((self.bt_mais, "Enter · lançar de novo", (70, 110, 180)),
                             (self.bt_sair, "Esc · guardar a vara", (130, 110, 110))):
            pygame.draw.rect(tela, cor, bt, border_radius=10)
            tt = f["peq"].render(txt, True, (255, 255, 255))
            tela.blit(tt, (bt.centerx - tt.get_width() // 2, bt.centery - tt.get_height() // 2))
        if not RETRATO:
            tela.blit(f["peq"].render(nota, True, (140, 120, 110)), (r.x + 30, y + 14))
        else:
            tela.blit(f["peq"].render(nota, True, (140, 120, 110)), (r.x + 30, self.bt_mais.y - 30))

    def _draw_bota(self, tela):
        f = self.mirante.app.f
        lns = quebrar(self.bota, f["med"], min(W - 120, 760) - 260 if not RETRATO else W - 100)
        larg = min(W - 40, 860)
        alt = max(250, 120 + 32 * len(lns)) + 70 + (140 if RETRATO else 0)
        r = pygame.Rect(0, 0, larg, alt)
        r.center = (W // 2, H // 2)
        painel(tela, r)
        bx = r.x + 40
        by = r.y + 40
        if RETRATO:
            bx, by = r.centerx - self.bota_spr.get_width() // 2, r.y + 30
        tela.blit(self.bota_spr, (bx, by + math.sin(self.mirante.t * 0.05) * 3))
        if (self.mirante.t // 20) % 4 == 0:               # pinga
            pygame.draw.circle(tela, (120, 170, 230), (bx + 60, by + 80 + (self.mirante.t % 20) * 2), 4)
        tx = r.x + 160 if not RETRATO else r.x + 40
        ty = r.y + 40 if not RETRATO else by + self.bota_spr.get_height() + 30
        tela.blit(f["med"].render("Uma bota velha", True, (40, 60, 120)), (tx, ty))
        for i, ln in enumerate(lns):
            tela.blit(f["med"].render(ln, True, TINTA), (tx, ty + 44 + 32 * i))
        self._botoes(tela, r, "")
