"""Os gigantes do fundo da fase, dois personagens que reagem às respostas, ao herói e um ao outro:

    Oni ........ ogro do folclore japonês (pele vermelha, chifres, bastão): gargalha e aponta quando o jogador erra;
                 emburra quando ele acerta; dá um risinho quando o herói se machuca; leva um susto quando o
                 gigante da fase cai. À toa: coça a cabeça, bate o bastão no ombro, boceja, espia o Daidara.
    Daidara .... Daidarabotchi, o gigante bondoso do folclore japonês que ergueu montanhas: pele de musgo, franja
                 de musgo que escorre, pinheirinhos e cogumelos na cabeça, capa de palha e cabaça. Comemora no
                 acerto, fica triste no erro, faz careta de dó quando o herói se machuca, dança quando o gigante da
                 fase cai. À toa: um passarinho pousa no pinheiro e canta, acena para o herói, cantarola.

Vistas (turnaround, como nas folhas de modelo): cada gigante tem um GIRO contínuo de −1 (perfil olhando para a
esquerda) a 0 (frente) a 1 (perfil para a direita). O desenho gira em torno da linha de centro do rosto: os traços
deslizam para o lado do giro, o olho do lado de lá estreita e some no perfil, o nariz sai da silhueta, a orelha de
lá some e a de cá vai para trás; coque, chifres e gola acompanham.

Animação (princípios do desenho animado):
  continuação ... o corpo gira atrasado em relação à cabeça (giro_corpo segue giro com mola mais mole);
  antecipação ... antes de cada reação a cabeça encolhe por alguns quadros (squash) e depois estica;
  respiração .... ombros sobem e descem devagar; piscada simples ou dupla em tempos aleatórios.

Traço Ilha: cor chapada, sombra dura do lado direito, contorno escuro da própria cor (o do Oni treme quando ri).
Desenho a cada quadro numa tela pequena, colado com o tom do clima e um véu de distância."""
import math
import random

import pygame

W, H = 112, 114                                        # 10 px de folga em cima: pinheiros e passarinho
PELE_ONI = ((222, 84, 66), (174, 52, 54), (244, 128, 100))
PELE_DAI = ((128, 178, 108), (92, 138, 86), (172, 210, 142))
FOCINHO_DAI = (196, 222, 160)
CONT_ONI, CONT_DAI = (60, 16, 24), (30, 50, 34)
CHIFRE, CHIFRE_S = (242, 228, 192), (200, 180, 146)
CABELO, CABELO_L = (34, 26, 40), (70, 58, 84)
QUIMONO, QUIMONO_S, GOLA = (64, 76, 146), (44, 52, 108), (244, 240, 228)
PALHA, PALHA_S, PALHA_L = (214, 182, 112), (170, 136, 78), (236, 212, 150)
QUIMONO_DAI = (86, 150, 156)
FERRO, FERRO_L = (74, 66, 80), (118, 110, 126)
BOCA, LINGUA, DENTE = (110, 20, 34), (240, 110, 130), (252, 250, 240)
PINHO, PINHO_S, MUSGO, MUSGO_S = (52, 120, 84), (30, 84, 64), (84, 138, 74), (58, 104, 58)
COGU, COGU_P = (226, 90, 80), (252, 240, 230)
CABACA, CABACA_S = (232, 176, 80), (186, 128, 50)
PASSARO, PASSARO_B = (250, 210, 90), (240, 140, 60)
LAGRIMA, SUOR = (150, 210, 250), (190, 230, 255)


def _mola(v, alvo, k=0.12):
    return v + (alvo - v) * k


def _curva(c, cor, p0, p1, p2, larg):
    """Braço de macarrão: curva de Bézier quadrática grossa; devolve a ponta (onde vai a mão)."""
    pts = []
    for i in range(9):
        t = i / 8
        a, b, d = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        pts.append((a * p0[0] + b * p1[0] + d * p2[0], a * p0[1] + b * p1[1] + d * p2[1]))
    for i in range(8):
        pygame.draw.line(c, cor, pts[i], pts[i + 1], larg)
        pygame.draw.circle(c, cor, (int(pts[i + 1][0]), int(pts[i + 1][1])), larg // 2)
    return pts[-1]


def _simbolo(s, qual, x, y, r, cor):
    """Estrelinha de 5 pontas ou nota musical, com contorno escuro."""
    escuro = tuple(v // 3 for v in cor)
    if qual == "★":
        pts = [(x + math.cos(-math.pi / 2 + k * math.pi / 5) * (r if k % 2 == 0 else r * 0.45),
                y + math.sin(-math.pi / 2 + k * math.pi / 5) * (r if k % 2 == 0 else r * 0.45)) for k in range(10)]
        pygame.draw.polygon(s, cor, pts)
        pygame.draw.polygon(s, escuro, pts, 1)
    else:
        pygame.draw.ellipse(s, escuro, (x - r // 2 - 1, y + r // 2 - 1, r + 2, int(r * 0.8) + 2))
        pygame.draw.ellipse(s, cor, (x - r // 2, y + r // 2, r, int(r * 0.8)))
        pygame.draw.line(s, cor, (x + r // 2 - 1, y + r // 2 + 1), (x + r // 2 - 1, y - r), max(1, r // 4))
        pygame.draw.line(s, cor, (x + r // 2 - 1, y - r), (x + r, y - r // 2), max(1, r // 4))


class Gigante:
    """Base: reação (com antecipação), ação à toa, giro com continuação, respiração, piscar, textos que sobem."""
    CONT = CONT_ONI
    ACOES = ()                                                  # ações à toa deste gigante

    def __init__(self, seed=0):
        self.rng = random.Random(seed)
        self.t = 0
        self.giro = self.giro_corpo = 0.0
        self.alvo_giro = 0.0
        self.reacao, self.resta = None, 0
        self.acao, self.acao_t = None, 0                         # ação à toa e quanto falta
        self.prox_acao = self.rng.randint(240, 480)
        self.squash = 0                                         # antecipação: quadros de cabeça encolhida
        self.piscar, self.prox_pisca, self.piscadas = 0, self.rng.randint(80, 200), 0
        self.textos = []                                        # [texto, x, y, vida, cor]
        self.c = pygame.Surface((W, H), pygame.SRCALPHA)
        self.f = None

    def reagir(self, nome, para_lado, quadros=120):
        """Reação a um acontecimento; para_lado = −1/1 (onde está o outro gigante)."""
        self.reacao, self.resta = nome, quadros
        self.acao = None
        self.squash = 6
        vira = {"ri": 0.78, "comemora": 0.78, "emburra": 0.78, "triste": 0.45, "risinho": 0.6, "ai": 0.0,
                "danca": 0.3, "choque": 0.5, "espia": 0.7}
        self.alvo_giro = vira.get(nome, 0.4) * para_lado

    def passo(self, olhar_heroi=0.0):
        self.t += 1
        if self.resta:
            self.resta -= 1
            if not self.resta:
                self.reacao = None
        self.squash = max(0, self.squash - 1)
        if not self.reacao:
            self.alvo_giro = max(-0.35, min(0.35, olhar_heroi * 0.35))
            if self.acao:
                self.acao_t -= 1
                if self.acao_t <= 0:
                    self.acao = None
            else:
                self.prox_acao -= 1
                if self.prox_acao <= 0 and self.ACOES:
                    self.acao = self.rng.choice(self.ACOES)
                    self.acao_t = 150
                    self.prox_acao = self.rng.randint(420, 840)
        if self.reacao == "danca":
            self.alvo_giro = 0.45 * math.sin(self.t * 0.18)
        self.giro = _mola(self.giro, self.alvo_giro, 0.14)
        self.giro_corpo = _mola(self.giro_corpo, self.giro, 0.06)       # o corpo vem atrás da cabeça
        self.prox_pisca -= 1
        if self.prox_pisca <= 0:
            self.piscar = 7
            self.piscadas = 1 if self.rng.random() < 0.25 else 0       # às vezes pisca duas vezes
            self.prox_pisca = self.rng.randint(120, 260)
        if self.piscar == 1 and self.piscadas:
            self.piscadas, self.piscar = 0, 12
        self.piscar = max(0, self.piscar - 1)
        for tx in self.textos:
            tx[2] -= 0.45
            tx[3] -= 1
        self.textos = [tx for tx in self.textos if tx[3] > 0]

    def _fechado(self):
        return 0 < self.piscar <= 7                             # na piscada dupla, 12…8 é o olho aberto no meio

    def _resp(self):
        return math.sin(self.t * 0.05) * 1.2                   # respiração: ombros sobem e descem

    def _cabeca_y(self):
        """Antecipação: a cabeça afunda 2 px nos primeiros quadros da reação."""
        return 2 if self.squash else 0

    def _texto(self, txt, x, y, vida, cor):
        self.textos.append([txt, x, y, vida, cor])

    # ------------------------------------------------------------------ peças comuns a todos os giros
    def _rosto(self, c, hx, hy, pele, olhos, boca, sobrancelha, cor_sob, larg_sob=3):
        """Desenha olhos, sobrancelhas, nariz e boca girados: tudo desliza com a linha de centro."""
        g = self.giro
        lado = 1 if g >= 0 else -1
        ag = abs(g)
        hw = 20 * (1 - 0.12 * ag)
        fx = hx + g * hw * 0.62                                  # linha de centro do rosto
        d = 9 * (1 - 0.45 * ag)
        perto_x, longe_x = fx - lado * d * (1 - 0.3 * ag), fx + lado * d
        cont = self.CONT
        for k, (x, escala) in enumerate(((perto_x, 1.0), (longe_x, 1 - 0.7 * ag))):
            if escala < 0.4:                                     # perfil: o olho de lá some
                continue
            x, y = int(round(x)), int(round(hy - 1))
            rx = max(1, int(round(5 * escala)))
            if olhos == "riso":
                pygame.draw.arc(c, cont, (x - rx, y - 3, 2 * rx, 8), math.radians(20), math.radians(160), 2)
            elif olhos == "triste":
                pygame.draw.arc(c, cont, (x - rx, y - 1, 2 * rx, 7), math.radians(200), math.radians(340), 2)
            elif olhos == "aperta":                              # careta: olhos apertados ><
                lx = 1 if k == 0 else -1
                pygame.draw.line(c, cont, (x - rx, y - 3 * lx * lado), (x + rx, y), 2)
                pygame.draw.line(c, cont, (x - rx, y + 3 * lx * lado), (x + rx, y), 2)
            elif olhos == "fechado" or self._fechado():
                c.fill(cont, (x - rx, y, 2 * rx, 2))
            elif olhos == "arregalado":                          # susto: olho grande, pupila pequena
                pygame.draw.ellipse(c, (252, 250, 244), (x - rx - 1, y - 7, 2 * rx + 3, 13))
                c.fill(cont, (x + int(round(g * 2)), y, 1, 1))
            else:
                pygame.draw.ellipse(c, (252, 250, 244), (x - rx, y - 5, 2 * rx + 1, 10))
                px = x + int(round(g * 2))
                pygame.draw.circle(c, cont, (px, y + 1), 2 if escala > 0.6 else 1)
                c.set_at((px - 1, y), (255, 255, 255))
            if sobrancelha:                                      # ângulo da sobrancelha diz o humor
                # ponta de dentro baixa = bravo; ponta de dentro alta = triste (o olho de cá fica do lado oposto ao giro)
                inc = {"brava": 3, "triste": -3, "alta": 0}.get(sobrancelha, 0) * (1 if k == 0 else -1) * lado
                if escala < 0.6:
                    inc *= 0.5
                yy = y - 8 - (3 if sobrancelha in ("alta", "susto") else 0) - (3 if sobrancelha == "susto" else 0)
                pygame.draw.line(c, cor_sob, (x - rx - 1, yy - inc), (x + rx + 1, yy + inc), larg_sob)
        return fx, hw, lado, ag

    def _boca(self, c, fx, hy, g, ag, boca):
        cont = self.CONT
        mx, my = fx + g * 3, hy + 13
        mw = 10 * (1 - 0.35 * ag)
        if boca == "riso":
            abre = 9 + int(3 * abs(math.sin(self.t * 0.75)))
            pygame.draw.ellipse(c, BOCA, (int(mx - mw - 2), int(my - 3), int(2 * mw + 4), abre))
            pygame.draw.ellipse(c, LINGUA, (int(mx - mw * 0.5), int(my + abre - 7), int(mw), 5))
        elif boca == "risinho":
            pygame.draw.ellipse(c, BOCA, (int(mx - mw * 0.7), int(my - 2), int(1.4 * mw), 5 + int(abs(math.sin(self.t)))))
        elif boca == "sorriso":
            pygame.draw.arc(c, cont, (int(mx - mw), int(my - 7), int(2 * mw), 10), math.radians(200), math.radians(340), 2)
        elif boca == "comemora":
            pygame.draw.ellipse(c, BOCA, (int(mx - mw), int(my - 4), int(2 * mw), 9))
            pygame.draw.rect(c, DENTE, (int(mx - mw + 2), int(my - 4), int(2 * mw - 4), 3))
        elif boca == "triste":
            pygame.draw.arc(c, cont, (int(mx - mw * 0.8), int(my - 1), int(1.6 * mw), 8), math.radians(20), math.radians(160), 2)
        elif boca == "bico":
            c.fill(cont, (int(mx - mw * 0.5), int(my - 1), int(mw), 2))
        elif boca == "o":                                        # susto / bocejo
            r = 4 if self.reacao == "choque" else 3 + int(2 * abs(math.sin(self.t * 0.08)))
            pygame.draw.ellipse(c, BOCA, (int(mx - r), int(my - r), 2 * r, 2 * r + 2))
        elif boca == "ondulada":                                 # careta de dó
            for i in range(int(2 * mw)):
                c.set_at((int(mx - mw + i), int(my + 2 * math.sin(i * 0.9))), cont)
        elif boca == "sorrisao":                                 # sorriso aberto em D, simpático
            pygame.draw.ellipse(c, BOCA, (int(mx - mw * 0.75), int(my - 6), int(1.5 * mw), 10))
            pygame.draw.rect(c, FOCINHO_DAI, (int(mx - mw * 0.8), int(my - 7), int(1.6 * mw) + 1, 5))
            pygame.draw.ellipse(c, LINGUA, (int(mx - mw * 0.35), int(my), int(0.7 * mw), 3))
            c.fill(DENTE, (int(mx - 3), int(my - 2), 2, 2))
            c.fill(DENTE, (int(mx + 1), int(my - 2), 2, 2))
        elif boca == "canta":
            r = 2 + int(abs(math.sin(self.t * 0.2)) * 2)
            pygame.draw.ellipse(c, BOCA, (int(mx - 3), int(my - 2), 6, r + 2))

    def _nariz(self, c, hx, hy, fx, hw, g, ag, cor, largo=10, alto=7):
        nx = hx + g * (hw + 3) if ag > 0.6 else fx + g * 3      # de lado, o nariz sai da silhueta
        pygame.draw.ellipse(c, cor, (int(nx - largo / 2), int(hy + 3), largo, alto))
        c.fill(self.CONT, (int(nx - 2 + g * 2), int(hy + 3 + alto - 1), 2, 1))

    def _orelhas(self, c, hx, hy, pele, hw):
        """Na frente, duas; girando, a de lá some e a de cá vai para trás da cabeça."""
        g, ag = self.giro, abs(self.giro)
        lado = 1 if g >= 0 else -1
        if ag < 0.3:
            pygame.draw.ellipse(c, pele[1], (int(hx - hw - 5), int(hy - 4), 7, 10))
        pygame.draw.ellipse(c, pele[1], (int(hx - lado * hw * (1 - ag * 0.9) - 3 - (2 if lado > 0 else 0)), int(hy - 4),
                                         7, 10))
        if ag < 0.3:
            pygame.draw.ellipse(c, pele[1], (int(hx + hw - 2), int(hy - 4), 7, 10))

    def _contorno(self, treme=False):
        c = self.c
        m = pygame.mask.from_surface(c)
        borda = m.to_surface(setcolor=self.CONT, unsetcolor=(0, 0, 0, 0))
        out = pygame.Surface((W + 4, H + 4), pygame.SRCALPHA)
        tr = (lambda: self.rng.randint(-1, 1)) if treme and self.t % 3 == 0 else (lambda: 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            out.blit(borda, (2 + dx + tr(), 2 + dy + tr()))
        out.blit(c, (2, 2))
        return out

    def draw(self, s, x, y, tom=None, escala=1, nevoa=None):
        """Cola o gigante com o meio da base em (x, y)."""
        c = self.c
        c.fill((0, 0, 0, 0))
        self.pinta(c)
        out = self._contorno(treme=self.reacao in ("ri", "choque"))
        if tom:
            out.fill(tom, special_flags=pygame.BLEND_RGB_MULT)
        if nevoa:
            cor, k = nevoa
            veu = pygame.Surface(out.get_size(), pygame.SRCALPHA)
            veu.fill(cor + (int(255 * k),))
            veu.blit(out, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            out.blit(veu, (0, 0))
        e = escala
        if e != 1:
            out = pygame.transform.scale(out, (int(out.get_width() * e), int(out.get_height() * e)))
        s.blit(out, (int(x - (W / 2 + 2) * e), int(y - (H + 2) * e)))
        if self.textos:
            if self.f is None:
                self.f = pygame.font.Font(None, int(14 * e))
            for txt, tx, ty, vida, cor in self.textos:
                px, py = int(x + (tx - W / 2) * e), int(y + (ty - H) * e)
                if txt in ("★", "♪"):                            # a fonte padrão não tem esses: desenhados à mão
                    _simbolo(s, txt, px, py, int(5 * e), cor)
                    continue
                t = self.f.render(txt, True, cor)
                t.set_alpha(min(255, vida * 9))
                s.blit(t, (px, py))


class Oni(Gigante):
    CONT = CONT_ONI
    ACOES = ("coca", "ombro", "boceja")

    def passo(self, olhar_heroi=0.0):
        super().passo(olhar_heroi)
        r = self.reacao
        if r == "ri" and self.resta % 16 == 0:
            self._texto("HA", W * 0.5 + self.giro * 20 + self.rng.uniform(-6, 6), H * 0.24, 40, (255, 236, 200))
        elif r == "risinho" and self.resta % 14 == 0:
            self._texto("he", W * 0.5 + self.giro * 20, H * 0.26, 30, (255, 236, 200))
        elif r == "emburra" and self.resta % 30 == 0:
            self._texto("hmpf", W * 0.5 - self.giro * 14, H * 0.2, 36, (230, 230, 240))
        elif r == "choque" and self.resta == 58:
            self._texto("!?", W * 0.5 + self.giro * 16, H * 0.22, 50, (255, 255, 255))
        if self.acao == "boceja" and self.acao_t == 60:
            self._texto("uaaah", W * 0.5, H * 0.18, 50, (230, 230, 240))

    def pinta(self, c):
        g, ag = self.giro, abs(self.giro)
        gc = self.giro_corpo
        lado = 1 if g >= 0 else -1
        r, acao = self.reacao, self.acao
        rindo = r == "ri"
        chac = int(round(math.sin(self.t * 1.3))) if rindo else 0
        # corpo: quimono; a gola cruzada segue o giro do corpo (que vem atrás da cabeça)
        oy = 64 + chac + self._resp() + (-3 if r == "choque" else 0)
        pygame.draw.ellipse(c, QUIMONO_S, (12, oy, 88, 90))
        pygame.draw.ellipse(c, QUIMONO, (12, oy, 74, 86))
        for k in range(10):
            x, y = 20 + (k * 23) % 66, oy + 10 + (k * 7) % 22
            c.fill((92, 108, 182), (x, y, 3, 1))
            c.fill((92, 108, 182), (x + 1, y - 1, 1, 3))
        gx = 56 + gc * 14
        pygame.draw.polygon(c, GOLA, [(gx - 10, oy + 2), (gx, oy + 24), (gx + 10, oy + 2), (gx + 6, oy + 2), (gx, oy + 16),
                                      (gx - 6, oy + 2)])
        pygame.draw.polygon(c, PELE_ONI[1], [(gx - 6, oy + 2), (gx, oy + 16), (gx + 6, oy + 2)])
        # bastão no ombro: bate no ombro (ação "ombro"), balança rindo, cai no susto
        bx = 80 - gc * 8
        ang = -58
        if rindo:
            ang += 6 * math.sin(self.t * 0.6)
        elif acao == "ombro":
            ang += 10 * max(0.0, math.sin(self.t * 0.25))
        elif r == "choque":
            ang += 20
        a = math.radians(ang)
        x1, y1 = bx + math.cos(a) * 44, oy + 24 + math.sin(a) * 44
        pygame.draw.line(c, FERRO, (bx, oy + 24), (x1, y1), 7)
        pygame.draw.line(c, FERRO_L, (bx - 2, oy + 23), (x1 - 2, y1 - 1), 2)
        for k in range(2, 6):
            px, py = bx + math.cos(a) * k * 8, oy + 24 + math.sin(a) * k * 8
            c.fill(FERRO_L, (int(px) + 3, int(py) - 1, 2, 2))
        pygame.draw.ellipse(c, PELE_ONI[0], (bx - 8, oy + 16, 14, 12))
        # cabeça
        inc = -3 if rindo else (2 if r == "emburra" else (-4 if r == "choque" else 0))
        if acao == "boceja" and 30 < self.acao_t < 110:
            inc = -4
        bob = (2 * math.sin(self.t * 0.75) if rindo else 0.8 * math.sin(self.t * 0.04)) + chac + self._cabeca_y()
        if r == "risinho":
            bob += math.sin(self.t * 0.9)
        hx, hy = 56, 44 + inc + bob
        hw = 20 * (1 - 0.12 * ag)
        mao_coca = None
        if acao == "coca":                                       # coça o topo da cabeça: braço atrás, mão por cima
            mexe = 2 * math.sin(self.t * 0.9)
            mao_coca = _curva(c, PELE_ONI[1], (30, oy + 14), (14, oy - 24), (hx - 12 + mexe, hy - 24), 6)
        if ag > 0.3:                                             # chifre de lá, atrás da cabeça
            self._chifre(c, hx + lado * 12 - g * 4, hy, lado, atras=True)
        for k in range(11):                                      # juba (vai para trás do giro); arrepia no susto
            a2 = math.pi * (0.95 + 1.1 * k / 10)
            rr = 23 + (k % 2) * 3 + (3 if r == "choque" else 0)
            pygame.draw.circle(c, CABELO, (int(hx - g * 5 + math.cos(a2) * rr), int(hy - 2 + math.sin(a2) * rr * 0.9)), 6)
        tx = hx - g * 7                                          # coque
        pygame.draw.ellipse(c, CABELO, (tx - 9, hy - 33, 18, 12))
        pygame.draw.ellipse(c, CABELO_L, (tx - 5, hy - 32, 6, 3))
        c.fill((220, 60, 60), (tx - 6, hy - 23, 12, 2))
        if ag > 0.3:                                             # chifre de cá, na frente
            self._chifre(c, hx - lado * 12 - g * 4, hy, -lado, atras=False)
        else:
            for ld in (-1, 1):
                self._chifre(c, hx + ld * 12 - g * 4, hy, ld, atras=False)
        pygame.draw.rect(c, PELE_ONI[1], (int(hx - hw), hy - 18, int(2 * hw), 38), border_radius=13)
        pygame.draw.rect(c, PELE_ONI[0], (int(hx - hw), hy - 18, int(2 * hw * 0.82), 34), border_radius=13)
        pygame.draw.ellipse(c, PELE_ONI[2], (int(hx - hw + 5), hy - 14, 10, 6))
        self._orelhas(c, hx, hy, PELE_ONI, hw)
        bocejo = acao == "boceja" and 30 < self.acao_t < 110
        if rindo or r == "risinho":
            olhos, boca, sob = "riso", ("riso" if rindo else "risinho"), "alta"
        elif r == "emburra":
            olhos, boca, sob = ("fechado" if self.t % 40 < 20 else "aberto"), "bico", "brava"
        elif r == "choque":
            olhos, boca, sob = "arregalado", "o", "susto"
        elif bocejo:
            olhos, boca, sob = "fechado", "o", "alta"
        elif acao == "coca":
            olhos, boca, sob = "fechado", "sorriso", "alta"
        else:
            olhos, boca, sob = "aberto", "sorriso", "brava"
        fx, hw, lado, ag = self._rosto(c, hx, hy, PELE_ONI, olhos, boca, sob, CABELO)
        self._nariz(c, hx, hy, fx, hw, g, ag, PELE_ONI[1])
        self._boca(c, fx, hy, g, ag, boca)
        for ld in (-1, 1):                                       # bigode de fios
            pygame.draw.line(c, CABELO, (fx + ld * 4, hy + 11), (fx + ld * 13 * (1 - 0.3 * ag), hy + 16), 2)
        if boca == "sorriso":                                    # presas
            for ld in (-1, 1):
                x = int(fx + g * 3 + ld * 6 * (1 - 0.35 * ag))
                pygame.draw.polygon(c, DENTE, [(x - 1, hy + 12), (x, hy + 9), (x + 1, hy + 12)])
        if r == "choque":                                        # gota de suor
            pygame.draw.ellipse(c, SUOR, (int(hx + hw - 2), int(hy - 14 + (self.t % 30) * 0.3), 4, 6))
        # braços
        if rindo:                                                # aponta para o outro gigante, rindo
            ombro = (56 + lado * 22, oy + 14)
            mao = _curva(c, PELE_ONI[0], ombro, (ombro[0] + lado * 18, oy - 4), (ombro[0] + lado * 36, oy + 2), 6)
            pygame.draw.circle(c, PELE_ONI[0], (int(mao[0]), int(mao[1])), 5)
            pygame.draw.line(c, PELE_ONI[0], mao, (mao[0] + lado * 9, mao[1] - 2), 3)       # dedo apontando
        elif r == "risinho":                                     # mão na boca, segurando o riso
            ombro = (40, oy + 14)
            mao = _curva(c, PELE_ONI[0], ombro, (34, oy - 4), (fx - 2, hy + 14), 6)
            pygame.draw.circle(c, PELE_ONI[0], (int(mao[0]), int(mao[1])), 5)
        elif mao_coca:                                           # a mão coçando, por cima do cabelo
            pygame.draw.circle(c, PELE_ONI[0], (int(mao_coca[0]), int(mao_coca[1])), 5)
            for k in range(3):
                c.fill(PELE_ONI[1], (int(mao_coca[0]) - 3 + k * 3, int(mao_coca[1]) + 3, 1, 2))
        elif bocejo:                                             # mão na frente do bocejo
            ombro = (38, oy + 14)
            mao = _curva(c, PELE_ONI[0], ombro, (30, oy), (fx - 4, hy + 16), 6)
            pygame.draw.circle(c, PELE_ONI[0], (int(mao[0]), int(mao[1])), 5)

    def _chifre(self, c, bx, hy, lado, atras):
        pts = [(bx - 3, hy - 15), (bx + lado * 7, hy - 30), (bx + 3 * lado + 3, hy - 14)]
        pygame.draw.polygon(c, CHIFRE_S if atras else CHIFRE, pts)
        if not atras:
            pygame.draw.polygon(c, CHIFRE_S, [pts[1], pts[2], (bx + lado, hy - 16)])


class Daidara(Gigante):
    CONT = CONT_DAI
    ACOES = ("passaro", "acena", "cantarola")

    def passo(self, olhar_heroi=0.0):
        super().passo(olhar_heroi)
        r = self.reacao
        if r == "comemora" and self.resta % 14 == 0:
            self._texto("★", W * 0.5 + self.rng.uniform(-30, 30), H * 0.3, 34, (255, 230, 110))
        if r == "comemora" and self.resta == 118:
            self._texto("ISSO!", W * 0.5 + self.giro * 16, H * 0.27, 60, (255, 255, 230))
        if r == "triste" and self.resta == 118:
            self._texto("ahh…", W * 0.5 + self.giro * 16, H * 0.27, 60, (200, 220, 250))
        if r == "ai" and self.resta == 58:
            self._texto("ai!", W * 0.5, H * 0.26, 44, (255, 220, 220))
        if r == "danca" and self.resta % 20 == 0:
            self._texto("♪", W * 0.5 + self.rng.uniform(-34, 34), H * 0.28, 40, (255, 250, 200))
        if self.acao == "cantarola" and self.acao_t % 30 == 0:
            self._texto("♪", W * 0.5 + 18 + self.rng.uniform(-6, 6), H * 0.3, 40, (240, 250, 230))
        if self.acao == "passaro" and 50 < self.acao_t < 100 and self.acao_t % 25 == 0:
            self._texto("piu", W * 0.5 - 8, H * 0.02, 30, (255, 250, 220))

    def _passaro(self, c, hx, hy, g):
        """O passarinho: chega voando de fora, pousa no pinheiro do meio, canta e vai embora."""
        t = 150 - self.acao_t
        pouso = (hx - g * 6, hy - 37)
        if t < 40:                                               # chegando
            u = t / 40
            x, y = W + 10 + (pouso[0] - W - 10) * u, 0 + (pouso[1] - 0) * u - 10 * math.sin(u * math.pi)
            asa = int(t / 3) % 2
        elif t < 110:                                            # pousado, pulinhos
            x, y = pouso[0], pouso[1] - (2 if (t // 12) % 2 else 0)
            asa = 0
        else:                                                    # indo embora
            u = (t - 110) / 40
            x, y = pouso[0] - u * 80, pouso[1] - u * 40
            asa = int(t / 3) % 2
        x, y = int(x), int(y)
        pygame.draw.ellipse(c, PASSARO, (x - 3, y - 3, 7, 5))
        c.fill(PASSARO_B, (x + 3 if t < 110 else x - 4, y - 2, 2, 1))           # bico
        c.set_at((x + 1 if t < 110 else x - 2, y - 2), CONT_DAI)                # olho
        pygame.draw.line(c, PASSARO, (x - 1, y - 1), (x - 3, y - 4 - 2 * asa))   # asa

    def pinta(self, c):
        g, ag = self.giro, abs(self.giro)
        gc = self.giro_corpo
        lado = 1 if g >= 0 else -1
        r, acao = self.reacao, self.acao
        festa = r == "comemora"
        triste = r == "triste"
        danca = r == "danca"
        pulo = -abs(math.sin(self.t * 0.35)) * 4 if (festa or danca) else 0
        balanco = 3 * math.sin(self.t * 0.18) if danca else 0
        oy = 64 + pulo + (3 if triste else 0) + self._resp()
        # capa de palha (mino) com franjas, gola de quimono por baixo e a cabaça na alça
        pygame.draw.ellipse(c, PALHA_S, (10 + balanco, oy, 92, 92))
        pygame.draw.ellipse(c, PALHA, (10 + balanco, oy, 78, 88))
        for x in range(16, 96, 4):
            pygame.draw.line(c, PALHA_S if x % 8 else PALHA_L, (x + balanco, oy + 14), (x + 1 + balanco, oy + 60), 1)
        for x in range(14, 98, 6):                               # bainha desfiada da capa
            pygame.draw.line(c, PALHA_S, (x + balanco, oy + 12), (x + 2 + balanco, oy + 16), 1)
        gx = 56 + gc * 14 + balanco
        pygame.draw.polygon(c, QUIMONO_DAI, [(gx - 11, oy + 2), (gx, oy + 18), (gx + 11, oy + 2)])
        pygame.draw.polygon(c, PELE_DAI[1], [(gx - 6, oy + 2), (gx, oy + 11), (gx + 6, oy + 2)])
        alca_x = 30 + gc * 6 + balanco
        pygame.draw.line(c, (150, 80, 50), (alca_x, oy + 6), (alca_x + 6, oy + 30), 2)
        cx, cy = int(alca_x + 6), int(oy + 34 + math.sin(self.t * 0.06) * 1.5)   # cabaça balançando
        pygame.draw.circle(c, CABACA, (cx, cy - 6), 4)
        pygame.draw.circle(c, CABACA, (cx, cy + 2), 6)
        pygame.draw.circle(c, CABACA_S, (cx + 2, cy + 3), 3)
        c.fill((150, 80, 50), (cx - 2, cy - 4, 5, 1))
        # cabeça: redonda, bochechuda, com focinho claro
        bob = (pulo * 0.6) if (festa or danca) else 0.6 * math.sin(self.t * 0.035)
        bob += self._cabeca_y()
        if acao == "cantarola":
            bob += math.sin(self.t * 0.1)
        hx, hy = 56 + balanco, 44 + bob + (5 if triste else 0) + (2 if r == "ai" else 0)
        hw = 20 * (1 - 0.12 * ag)
        pygame.draw.ellipse(c, PELE_DAI[1], (int(hx - hw - 1), hy - 20, int(2 * hw + 2), 42))
        pygame.draw.ellipse(c, PELE_DAI[0], (int(hx - hw - 1), hy - 20, int(2 * hw * 0.84), 38))
        pygame.draw.ellipse(c, PELE_DAI[2], (int(hx - hw + 4), hy - 15, 10, 6))
        self._orelhas(c, hx, hy, PELE_DAI, hw)
        fx = hx + g * hw * 0.62
        pygame.draw.ellipse(c, FOCINHO_DAI, (int(fx - 13 * (1 - 0.3 * ag)), int(hy + 2), int(26 * (1 - 0.3 * ag)), 16))
        # franja de musgo que escorre (Hora de Aventura), vai para trás do giro
        for i in range(9):
            x = int(hx - hw + 4 + i * (2 * hw - 8) / 8 - g * 4)
            comp = 5 + (i * 7) % 5
            pygame.draw.rect(c, MUSGO_S, (x - 2, hy - 20, 5, comp + 2))
            pygame.draw.rect(c, MUSGO, (x - 2, hy - 21, 4, comp), border_radius=2)
        # pinheirinhos e cogumelos na cabeça
        for k, (dx, alt) in enumerate(((-11, 12), (0, 17), (11, 11))):
            px = int(hx + dx - g * 6)
            base = hy - 19 + abs(dx) // 4
            pygame.draw.polygon(c, PINHO_S if k == 1 else PINHO, [(px, base - alt), (px + 5, base), (px - 5, base)])
            pygame.draw.polygon(c, PINHO, [(px, base - alt + 3), (px + 4, base - alt // 2), (px - 4, base - alt // 2)])
        for dx in (-17, 16):
            px = int(hx + dx - g * 6)
            c.fill(COGU_P, (px - 1, hy - 21, 2, 4))
            pygame.draw.ellipse(c, COGU, (px - 4, hy - 25, 8, 5))
            c.set_at((px - 1, hy - 24), COGU_P)
        if acao == "passaro":
            self._passaro(c, hx, hy, g)
        if festa or danca:
            olhos, boca, sob = "riso", "comemora", "alta"
        elif triste:
            olhos, boca, sob = "triste", "triste", "triste"
        elif r == "ai":
            olhos, boca, sob = "aperta", "ondulada", "triste"
        elif acao == "cantarola":
            olhos, boca, sob = "riso", "canta", "alta"
        else:
            olhos, boca, sob = "aberto", "sorrisao", "alta"
        fx, hw, lado, ag = self._rosto(c, hx, hy, PELE_DAI, olhos, boca, sob, MUSGO_S, 3)
        self._nariz(c, hx, hy, fx, hw, g, ag, PELE_DAI[1], 12, 8)            # nariz de batata
        self._boca(c, fx, hy, g, ag, boca)
        for ld in (-1, 1):                                       # bochechas rosadas
            pygame.draw.ellipse(c, (232, 150, 140), (int(fx + ld * 13 * (1 - 0.4 * ag) - 3), int(hy + 5), 7, 4))
        pygame.draw.ellipse(c, MUSGO, (int(fx - 9 * (1 - 0.3 * ag)), int(hy + 17), int(18 * (1 - 0.3 * ag)), 7))  # barba
        if triste and self.t % 50 < 40:                          # lágrima escorrendo
            ly = hy + 2 + (self.t % 50) * 0.35
            pygame.draw.ellipse(c, LAGRIMA, (int(fx - lado * 7 - 2), int(ly), 3, 5))
        # braços
        if festa:                                                # punho erguido para o lado do Oni
            ombro = (56 + lado * 22, oy + 12)
            sobe = 6 * math.sin(self.t * 0.35)
            mao = _curva(c, PELE_DAI[0], ombro, (ombro[0] + lado * 14, oy - 6), (ombro[0] + lado * 16, oy - 26 + sobe), 7)
            pygame.draw.circle(c, PELE_DAI[0], (int(mao[0]), int(mao[1])), 6)
            pygame.draw.circle(c, PELE_DAI[1], (int(mao[0]) + 2, int(mao[1]) + 2), 3)
        elif danca:                                              # os dois braços para cima, balançando
            for ld in (-1, 1):
                ombro = (56 + ld * 22 + balanco, oy + 12)
                onda = 5 * math.sin(self.t * 0.18 + ld)
                mao = _curva(c, PELE_DAI[0], ombro, (ombro[0] + ld * 12, oy - 4), (ombro[0] + ld * 8 + onda, oy - 28), 7)
                pygame.draw.circle(c, PELE_DAI[0], (int(mao[0]), int(mao[1])), 6)
        elif acao == "acena":                                    # acena para o herói
            ombro = (78, oy + 12)
            aceno = 8 * math.sin(self.t * 0.3)
            mao = _curva(c, PELE_DAI[0], ombro, (92, oy - 4), (90 + aceno, oy - 26), 7)
            pygame.draw.circle(c, PELE_DAI[0], (int(mao[0]), int(mao[1])), 6)
            for k in range(3):                                   # dedinhos abertos
                pygame.draw.line(c, PELE_DAI[0], mao, (mao[0] - 4 + k * 4, mao[1] - 7), 2)
        elif r == "ai":                                          # mãos no rosto, de dó
            for ld in (-1, 1):
                ombro = (56 + ld * 22, oy + 12)
                mao = _curva(c, PELE_DAI[0], ombro, (ombro[0] + ld * 4, oy - 2), (fx + ld * 15, hy + 8), 7)
                pygame.draw.circle(c, PELE_DAI[0], (int(mao[0]), int(mao[1])), 6)


class Dupla:
    """O par do fundo: o Daidara à esquerda, o Oni à direita; reagem às respostas olhando um para o outro."""

    def __init__(self, seed=0):
        self.bom = Daidara(seed)
        self.oni = Oni(seed + 1)
        self.prox_espiada = random.Random(seed).randint(600, 1200)

    def erro(self):
        self.oni.reagir("ri", -1)                 # vira para o Daidara (à esquerda) e aponta rindo
        self.bom.reagir("triste", 1)              # olha para o Oni, cabisbaixo

    def acerto(self):
        self.bom.reagir("comemora", 1)            # vira para o Oni e comemora
        self.oni.reagir("emburra", -1)            # o Oni vira e fica emburrado

    def dano(self):
        """O herói se machucou: o Oni dá um risinho, o Daidara faz careta de dó."""
        if self.oni.reacao in ("ri", "emburra") or self.bom.reacao in ("comemora", "triste"):
            return                                # não atropela a reação a uma resposta
        self.oni.reagir("risinho", -1, 60)
        self.bom.reagir("ai", 1, 60)

    def chefe_vencido(self):
        """O gigante da fase caiu: o Daidara dança, o Oni leva um susto."""
        self.bom.reagir("danca", 1, 180)
        self.oni.reagir("choque", -1, 90)

    def passo(self, heroi_x, largura):
        """heroi_x na tela; cada um olha para o herói quando não está reagindo; de vez em quando se espiam."""
        self.prox_espiada -= 1
        if self.prox_espiada <= 0:
            self.prox_espiada = self.bom.rng.randint(900, 1600)
            if not self.oni.reacao and not self.bom.reacao:
                self.oni.reagir("espia", -1, 50)
                self.bom.reagir("espia", 1, 50)
        self.bom.passo((heroi_x - largura * 0.24) / (largura * 0.5))
        self.oni.passo((heroi_x - largura * 0.78) / (largura * 0.5))

    def draw(self, s, largura, y, tom=None, escala=1, nevoa=None):
        self.bom.draw(s, largura * 0.24, y, tom, escala, nevoa)
        self.oni.draw(s, largura * 0.78, y, tom, escala, nevoa)


def folha(saida, escala=3):
    """Folha de vistas (turnaround) dos dois gigantes: giro −1, −0,5, 0, 0,5, 1, as reações e as ações à toa."""
    giros = (-1.0, -0.5, 0.0, 0.5, 1.0)
    linhas = [("Oni", Oni, None, None), ("Oni · ri", Oni, "ri", None), ("Oni · emburra", Oni, "emburra", None),
              ("Oni · risinho", Oni, "risinho", None), ("Oni · susto", Oni, "choque", None),
              ("Oni · coça", Oni, None, "coca"), ("Oni · boceja", Oni, None, "boceja"),
              ("Daidara", Daidara, None, None), ("Daidara · comemora", Daidara, "comemora", None),
              ("Daidara · triste", Daidara, "triste", None), ("Daidara · ai", Daidara, "ai", None),
              ("Daidara · dança", Daidara, "danca", None), ("Daidara · acena", Daidara, None, "acena"),
              ("Daidara · passarinho", Daidara, None, "passaro")]
    cw, ch = (W + 4) * escala, (H + 4) * escala
    tela = pygame.Surface((len(giros) * cw + 230, len(linhas) * (ch + 6) + 40))
    tela.fill((168, 214, 250))
    f = pygame.font.Font(None, 28)
    for i, g in enumerate(giros):
        tela.blit(f.render(f"giro {g:+.1f}", True, (30, 20, 30)), (230 + i * cw + cw // 2 - 40, 8))
    for j, (nome, cls, reacao, acao) in enumerate(linhas):
        tela.blit(f.render(nome, True, (30, 20, 30)), (10, 40 + j * (ch + 6) + ch // 2))
        for i, g in enumerate(giros):
            gg = cls(3)
            gg.t = 20
            if reacao:
                gg.reacao, gg.resta = reacao, 60
            if acao:
                gg.acao, gg.acao_t = acao, 80
            gg.giro = gg.giro_corpo = g
            gg.piscar = 0
            gg.prox_pisca = 999
            sup = pygame.Surface((W + 4, H + 4), pygame.SRCALPHA)
            gg.draw(sup, (W + 4) / 2, H + 2)
            tela.blit(pygame.transform.scale(sup, (cw, ch)), (230 + i * cw, 40 + j * (ch + 6)))
    pygame.image.save(tela, saida)
