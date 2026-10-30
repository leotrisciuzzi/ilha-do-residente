"""A fogueira do Mirante: um foguinho de toras cruzadas na margem, com faíscas, fumaça tênue e o reflexo no lago.

Sentar ao fogo abre "A semana à beira do fogo": um gráfico de barras à mão (estilo caderno, em pixel) com as
questões respondidas em cada um dos últimos 7 dias, o % de acerto da semana, o mundo mais jogado e a sequência
do Mundo do Dia. Os números vêm do save: cada questão conta no dia da sua ÚLTIMA resposta (save.d["q"][*]["ult"]),
e o acerto é o da última resposta ("ok"). Não há histórico completo no save, então é isso que dá para afirmar.

Desempenho: chamas (4 quadros), toras, halo no chão e reflexo (4 quadros) são pré-renderizados; por quadro só há
blits e uma dúzia de partículas. O conteúdo do modal é montado uma vez, ao sentar."""
import datetime as dt
import math
import random

import pygame

from . import Base
from ..mirante import ESC, GY, HZ, LW, MADEIRA, MADEIRA_ESC, PE, WW, _grupo
from ..ui import H, RETRATO, TINTA, W, painel, quebrar

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
DIAS_CURTO = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
FOGO = [(150, 40, 40), (214, 84, 42), (246, 146, 52), (255, 210, 104), (255, 246, 206)]
PEDRA, PEDRA_CLARA = (54, 58, 82), (84, 88, 116)


def _chamas(k, larg=9, alt=13):
    """Um quadro da chama: forma afunilada que oscila; cor pela distância ao eixo e pela altura."""
    rng = random.Random(40 + k)
    s = pygame.Surface((larg, alt), pygame.SRCALPHA)
    cx = (larg - 1) / 2
    for y in range(alt):
        t = y / (alt - 1)                                   # 0 no topo, 1 na base
        meia = (larg / 2) * (t ** 0.75) + 0.3
        off = math.sin(y * 0.8 + k * 1.57) * (1 - t) * 1.6
        for x in range(larg):
            d = abs(x - (cx + off)) / meia
            if d >= 1 or (t < 0.25 and rng.random() < 0.35):
                continue
            if d < 0.3 and t > 0.5:
                c = FOGO[4]
            elif d < 0.55 and t > 0.3:
                c = FOGO[3]
            elif d < 0.8:
                c = FOGO[2]
            else:
                c = FOGO[1]
            s.set_at((x, y), c)
    # uma língua solta acima, que muda a cada quadro
    lx = int(cx + (k % 3 - 1) * 2)
    s.set_at((lx, 0), FOGO[1])
    return s


def _toras():
    """Toras cruzadas, brasas e o anel de pedras (22×9)."""
    s = pygame.Surface((22, 9), pygame.SRCALPHA)
    for i, x in enumerate((1, 4, 8, 13, 17, 20)):           # pedras de trás
        pygame.draw.ellipse(s, PEDRA, (x - 1, 1 + (i % 2), 4, 3))
    pygame.draw.line(s, MADEIRA_ESC, (3, 7), (17, 2), 3)    # tora 1
    pygame.draw.line(s, MADEIRA, (3, 6), (17, 1), 1)
    pygame.draw.line(s, MADEIRA_ESC, (4, 2), (18, 7), 3)    # tora 2, cruzando
    pygame.draw.line(s, MADEIRA, (4, 1), (18, 6), 1)
    for x, y in ((3, 7), (18, 7)):                          # pontas cortadas
        s.set_at((x, y), (150, 110, 80))
    for x, c in ((8, FOGO[1]), (10, FOGO[2]), (11, FOGO[3]), (13, FOGO[1]), (9, FOGO[0]), (12, FOGO[2])):
        s.set_at((x, 6), c)
    for i, x in enumerate((0, 5, 10, 15, 19)):              # pedras da frente
        pygame.draw.ellipse(s, PEDRA_CLARA if i % 2 else PEDRA, (x, 6, 4, 3))
    return s


def _halo_chao(larg, alt, forca):
    """Elipse quente no chão (aditiva)."""
    s = pygame.Surface((larg, alt))
    cx, cy = larg / 2, alt / 2
    for y in range(alt):
        for x in range(larg):
            d = ((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2
            if d < 1:
                k = (1 - d) ** 1.6 * forca
                s.set_at((x, y), (int(110 * k), int(58 * k), int(22 * k)))
    return s


def _reflexo(k, alt):
    """Rastro quebrado da chama na água, do pé da margem para o horizonte (aditivo)."""
    rng = random.Random(90 + k)
    s = pygame.Surface((11, alt))
    for r in range(alt):                                    # r = 0 junto à margem
        f = (1 - r / alt) ** 1.4
        if rng.random() < 0.3 + 0.4 * (r / alt):
            continue
        meia = 1 + (alt - r) * 0.08 + rng.random()
        dx = math.sin(r * 0.9 + k * 1.6) * 1.2
        c = (int(170 * f), int(82 * f), int(30 * f))
        s.fill(c, (5 + dx - meia, alt - 1 - r, meia * 2, 1))
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x0 = WW * 0.464
        self.lugares = [("fogueira", self.x0, "sentar ao fogo")]
        self.fx = self.x0 + 9                               # a fogueira fica à direita de onde a Lume para
        self.quadros = [_chamas(k) for k in range(4)]
        self.base = _toras()
        self.halos = [_halo_chao(58, 14, f) for f in (0.8, 0.95, 1.1)]
        self.alt_ref = max(4, int((GY - HZ) * 0.7))
        self.reflexos = [_reflexo(k, self.alt_ref) for k in range(4)]
        self.fumaca = []
        for a in (46, 34, 22, 12):                          # bolinhas de fumaça, da mais densa à mais rala
            b = pygame.Surface((3, 3), pygame.SRCALPHA)
            b.fill((120, 118, 150, a), (0, 1, 3, 1))
            b.fill((120, 118, 150, a), (1, 0, 1, 3))
            self.fumaca.append(b)
        self.faiscas = []                                   # [x, y, vx, vy, vida] (mundo)
        self.nuvem = []                                     # [x, y, vida]
        self.rng = random.Random(7)
        self.conteudo = None
        self.veu = None

    # --------------------------------------------------------- mundo
    def update(self):
        t = self.mirante.t
        perto = abs(self.fx - self.mirante.cam - LW / 2) < LW
        if perto and t % 5 == 0 and len(self.faiscas) < 10:
            self.faiscas.append([self.fx + self.rng.uniform(-2, 2), PE - 8, self.rng.uniform(-0.15, 0.15),
                                 -self.rng.uniform(0.35, 0.7), self.rng.randint(25, 55)])
        if perto and t % 14 == 0 and len(self.nuvem) < 8:
            self.nuvem.append([self.fx + self.rng.uniform(-1, 1), PE - 15, 0])
        for f in self.faiscas:
            f[0] += f[2] + math.sin((t + f[4]) * 0.2) * 0.12
            f[1] += f[3]
            f[3] *= 0.985
            f[4] -= 1
        self.faiscas = [f for f in self.faiscas if f[4] > 0]
        for n in self.nuvem:
            n[0] += 0.08 + math.sin((t + n[1]) * 0.05) * 0.1
            n[1] -= 0.18
            n[2] += 1
        self.nuvem = [n for n in self.nuvem if n[2] < 110]

    def _tremor(self):
        t = self.mirante.t
        return (t // 6 + (t // 17) * 3) % 4

    def draw_lago(self, m, cam):
        x = self.fx - cam
        if -12 < x < LW + 12:
            m.blit(self.reflexos[(self.mirante.t // 8) % 4], (x - 5, GY - self.alt_ref),
                   special_flags=pygame.BLEND_RGB_ADD)

    def draw_margem(self, m, cam):
        x = self.fx - cam
        if not -40 < x < LW + 40:
            return
        q = self._tremor()
        m.blit(self.halos[q % 3], (x - 29, PE - 9), special_flags=pygame.BLEND_RGB_ADD)
        # toquinho para sentar, do lado esquerdo
        sx = self.x0 - 12 - cam
        pygame.draw.rect(m, MADEIRA_ESC, (sx - 4, PE - 4, 9, 4))
        pygame.draw.line(m, MADEIRA, (sx - 4, PE - 4), (sx + 4, PE - 4))
        pygame.draw.ellipse(m, (150, 110, 80), (sx + 3, PE - 4, 3, 4))
        m.blit(self.base, (x - 11, PE - 8))
        m.blit(self.quadros[q], (x - 4, PE - 17))
        m.blit(self.mirante.halo[9], (x - 9, PE - 19), special_flags=pygame.BLEND_RGB_ADD)
        if q % 2:
            m.blit(self.mirante.halo[14], (x - 14, PE - 24), special_flags=pygame.BLEND_RGB_ADD)

    def draw_frente(self, m, cam):
        x0 = self.fx - cam
        if not -40 < x0 < LW + 40:
            return
        for n in self.nuvem:
            i = min(3, n[2] // 28)
            m.blit(self.fumaca[i], (n[0] - cam - 1, n[1] - 1))
        for f in self.faiscas:
            c = FOGO[3] if f[4] > 30 else FOGO[2] if f[4] > 12 else FOGO[1]
            m.fill(c, (int(f[0] - cam), int(f[1]), 1, 1))

    # --------------------------------------------------------- dados da semana
    def _semana(self):
        app = self.mirante.app
        save = app.save
        qs = save.d.get("q", {}) or {}
        hoje = dt.date.today()
        dias = [hoje - dt.timedelta(days=6 - i) for i in range(7)]
        idx = {d: i for i, d in enumerate(dias)}
        n = [0] * 7
        certas = total = 0
        grupos = {}
        banco = getattr(app, "banco", None)
        temas = {}
        try:                                                # nome dos mundos pelo prefixo (Asma, DPOC, …)
            from .. import menus
            for tm in list(menus.TEMAS) + list(getattr(menus, "FARMACOS", [])) + list(getattr(menus, "INTERNATO_CM2", [])):
                temas[tm.pref] = tm.nome
        except Exception:
            pass
        for qid, st in qs.items():
            try:
                d = dt.date.fromtimestamp(float(st.get("ult", 0)))
            except Exception:
                continue
            if d not in idx:
                continue
            n[idx[d]] += 1
            total += 1
            certas += 1 if st.get("ok") else 0
            g = _grupo(qid)
            if g == "Outras":
                pre = qid.split(":")[0].split("-")[0]
                g = temas.get(pre[:-6] if pre.endswith("treino") else pre, g)
            if g in ("Provas reais", "Outras") and banco is not None:
                try:
                    g = banco.por_id[qid].get("materia") or g
                except Exception:
                    pass
            grupos[g] = grupos.get(g, 0) + 1
        seq = feitos = None
        try:
            from .. import dia
            seq = dia.sequencia(save)
            feitos = dia.n_feitos(save, hoje)
        except Exception:
            pass
        return dias, n, total, certas, grupos, seq, feitos

    def _frase(self, dias, n):
        ativos = sum(1 for v in n if v)
        if not ativos:
            return "Nenhuma questão respondida nos últimos 7 dias; o fogo fica aceso do mesmo jeito."
        forte = max(range(7), key=lambda i: (n[i], i))
        nome = "hoje" if forte == 6 else DIAS[dias[forte].weekday()]
        s = "dia" if ativos == 1 else "dias"
        q = "questão" if n[forte] == 1 else "questões"
        if ativos == 1:
            return f"Semana com 1 dia de estudo: {nome}, com {n[forte]} {q}."
        return f"Semana com {ativos} {s} de estudo; o dia mais forte foi {nome}, com {n[forte]} {q}."

    # --------------------------------------------------------- o modal (montado uma vez)
    def interagir(self, nome):
        self._montar()
        self.mirante.abrir_modal(self)

    def _grafico(self, cw, ch, dias, n):
        """Barras à mão: desenhadas em 1/3 da resolução e ampliadas sem suavização (pixel de caderno)."""
        f = self.mirante.app.f
        P = 3
        lw, lh = cw // P, ch // P
        s = pygame.Surface((lw, lh), pygame.SRCALPHA)
        rng = random.Random(3)
        base = lh - 12
        topo = 10
        esq = 4
        passo = (lw - esq - 2) / 7
        maior = max(n) or 1
        lapis = (70, 60, 90)
        # eixo levemente torto, como feito a lápis
        for x in range(esq, lw - 1):
            s.set_at((x, base + (1 if rng.random() < 0.12 else 0)), lapis)
        for i, v in enumerate(n):
            bx = int(esq + passo * i + passo * 0.2)
            bw = max(3, int(passo * 0.6))
            alt = 0 if not v else max(2, int((base - topo) * v / maior))
            if alt:
                cor = (232, 132, 60) if i == 6 else (120, 110, 190)
                escura = (170, 80, 40) if i == 6 else (70, 64, 140)
                r = pygame.Rect(bx, base - alt, bw, alt)
                s.fill(cor, r)
                s.set_clip(r)
                for k in range(-alt, bw, 3):                 # hachura diagonal
                    pygame.draw.line(s, escura, (bx + k, base - 1), (bx + k + alt, base - alt - 1))
                s.set_clip(None)
                s.fill(cor, (bx, base - alt, bw, 1))
                for y in range(base - alt, base):            # contorno tremido
                    s.set_at((bx - (1 if rng.random() < 0.15 else 0), y), lapis)
                    s.set_at((bx + bw - (0 if rng.random() < 0.85 else 1), y), lapis)
                pygame.draw.line(s, lapis, (bx, base - alt), (bx + bw, base - alt - (1 if rng.random() < 0.3 else 0)))
            else:
                s.fill((180, 170, 160), (bx + bw // 2 - 1, base - 1, 2, 1))
        out = pygame.transform.scale(s, (lw * P, lh * P))
        for i, (d, v) in enumerate(zip(dias, n)):
            cx = int((esq + passo * i + passo * 0.2 + max(3, int(passo * 0.6)) / 2) * P)
            rot = "hoje" if i == 6 else DIAS_CURTO[d.weekday()]
            t = f["peq"].render(rot, True, (170, 80, 40) if i == 6 else TINTA)
            out.blit(t, (cx - t.get_width() // 2, (base + 3) * P))
            alt = 0 if not v else max(2, int((base - topo) * v / maior))
            t = f["peq"].render(str(v), True, TINTA if v else (160, 150, 140))
            out.blit(t, (cx - t.get_width() // 2, (base - alt) * P - t.get_height() - 2))
        return out

    def _montar(self):
        f = self.mirante.app.f
        dias, n, total, certas, grupos, seq, feitos = self._semana()
        pw, ph = (W - 40, min(H - 120, 1040)) if RETRATO else (min(W - 120, 1060), min(H - 60, 640))
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        painel(s, (0, 0, pw - 4, ph - 4))
        # pautas de caderno e margem vermelha
        for y in range(96, ph - 20, 30):
            pygame.draw.line(s, (214, 224, 236), (14, y), (pw - 22, y))
        pygame.draw.line(s, (236, 170, 170), (54, 14), (54, ph - 22), 2)
        tit = f["med"].render("A semana à beira do fogo", True, (120, 60, 40))
        s.blit(tit, (74, 30))
        sub = f["peq"].render(f"{dias[0].strftime('%d/%m')} a {dias[-1].strftime('%d/%m')} · questões por dia",
                              True, (110, 100, 110))
        s.blit(sub, (74, 62))
        # textos da direita (ou de baixo, em pé)
        pct = f"{round(100 * certas / total)}%" if total else "—"
        linhas = [("Questões na semana", f"{total}")]
        linhas.append(("Acerto da semana", pct + (f" ({certas} de {total})" if total else "")))
        if grupos:
            g, v = max(grupos.items(), key=lambda kv: kv[1])
            linhas.append(("Mais jogado", f"{g} ({v})"))
        else:
            linhas.append(("Mais jogado", "nenhum mundo nesta semana"))
        if seq is None:
            linhas.append(("Mundo do Dia", "sem dados"))
        else:
            dd = "dia" if seq == 1 else "dias"
            txt = f"sequência de {seq} {dd}" if seq else "nenhuma sequência ativa"
            linhas.append(("Mundo do Dia", f"{txt}; hoje, {feitos} de 5 passos feitos"))
        if RETRATO:
            gx, gy, gw, gh = 70, 100, pw - 100, 420
            tx, ty, tw = 74, gy + gh + 30, pw - 110
        else:
            gx, gy, gw, gh = 70, 100, int(pw * 0.55), ph - 260
            tx, ty, tw = gx + gw + 30, 120, pw - (gx + gw + 30) - 30
        s.blit(self._grafico(gw, gh, dias, n), (gx, gy))
        y = ty
        for rot, val in linhas:
            s.blit(f["peq"].render(rot, True, (120, 110, 130)), (tx, y))
            y += 24
            for ln in quebrar(val, f["med"], tw):
                s.blit(f["med"].render(ln, True, TINTA), (tx, y))
                y += 30
            y += 14
        # frase final e rodapé
        y = max(y, gy + gh) + (10 if RETRATO else 16)
        for ln in quebrar(self._frase(dias, n), f["q"], pw - 120):
            s.blit(f["q"].render(ln, True, (60, 50, 70)), (74, y))
            y += 30
        nota = "Cada questão conta no dia da sua última resposta; o acerto também é o da última resposta."
        for ln in quebrar(nota, f["peq"], pw - 120):
            s.blit(f["peq"].render(ln, True, (140, 130, 140)), (74, y + 4))
            y += 24
        dica = ("toque para levantar" if RETRATO else "Enter ou Esc para levantar")
        t = f["peq"].render(dica, True, (150, 110, 80))
        s.blit(t, (pw - t.get_width() - 34, ph - 42))
        self.conteudo = s
        self.veu = pygame.Surface((W, H), pygame.SRCALPHA)
        self.veu.fill((6, 6, 20, 150))

    def evento_modal(self, e, inp):
        if inp.foi("ok") or inp.foi("voltar") or e.type == pygame.MOUSEBUTTONDOWN:
            return False
        return True

    def draw_modal(self, tela):
        if self.conteudo is None:
            return
        tela.blit(self.veu, (0, 0))
        r = self.conteudo.get_rect(center=(W // 2, H // 2))
        tela.blit(self.conteudo, r)
        # uma chaminha viva no canto do caderno (o quadro atual da fogueira, ampliado)
        q = self.quadros[self._tremor()]
        tela.blit(pygame.transform.scale(q, (q.get_width() * ESC, q.get_height() * ESC)),
                  (r.right - 46 - q.get_width() * ESC, r.y + 22))
