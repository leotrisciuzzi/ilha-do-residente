"""Bonecos articulados: o motor dos inimigos com partes móveis (desenhos em bonecos.py).

Em vez de 2 a 4 quadros prontos, cada inimigo é montado a cada quadro com peças que se mexem sozinhas:
  Mola ....... número que persegue um alvo com inércia (corpo que amassa ao cair, antena que balança, olhar)
  Corrente ... pontos ligados com física de Verlet, presos numa âncora (flagelo, cauda, tentáculo, fio, verme)
  perna() .... duas hastes com joelho resolvido por cinemática inversa (o pé fica no chão enquanto o corpo anda)
  Passada .... fase do passo medida pela distância andada (o pé não escorrega) e altura do pé no ar
  Olhos ...... olham para o jogador, piscam em tempos aleatórios e franzem a sobrancelha quando bravos

O desenho acontece numa tela pequena (o "quadro" do modelo) com o boneco virado à direita; no fim ganha contorno
de 1 px, pisca de branco quando apanha, vira, amplia (monstros grandes) e é colado alinhado pelos pés.
Coordenadas: x à direita, y para baixo, origem (OX, OY) = centro-baixo da hitbox (ou o centro, para quem voa)."""
import math
import random

import pygame

K = (28, 20, 36)
_esferas = {}


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def claro(c, t=0.45):
    return mix(c, (255, 255, 255), t)


def escuro(c, t=0.4):
    return mix(c, K, t)


# ===================================================================== física das peças

class Mola:
    """Valor com inércia: v persegue o alvo como uma mola amortecida (k = dureza, am = quanto conserva)."""
    __slots__ = ("v", "vel", "k", "am")

    def __init__(self, v=0.0, k=0.18, am=0.72):
        self.v, self.vel, self.k, self.am = v, 0.0, k, am

    def passo(self, alvo):
        self.vel = (self.vel + (alvo - self.v) * self.k) * self.am
        self.v += self.vel
        return self.v

    def chute(self, dv):
        self.vel += dv


class Corrente:
    """n pontos a `seg` px um do outro, o primeiro preso na âncora. Integração de Verlet + restrição de distância.
    `rigidez` puxa cada elo para a direção do anterior (0 = corda mole, 1 = haste quase reta)."""

    def __init__(self, n, seg, x=0.0, y=0.0, grav=0.12, arrasto=0.86, rigidez=0.0, direcao=(-1, 0)):
        self.seg, self.grav, self.arrasto, self.rigidez = seg, grav, arrasto, rigidez
        self.dir = direcao
        self.p = [[x + direcao[0] * seg * i, y + direcao[1] * seg * i] for i in range(n)]
        self.ant = [list(q) for q in self.p]

    def reposicionar(self, x, y):
        dx, dy = x - self.p[0][0], y - self.p[0][1]
        for q, a in zip(self.p, self.ant):
            q[0] += dx
            q[1] += dy
            a[0] += dx
            a[1] += dy

    def passo(self, ax, ay, direcao=None, forca=(0.0, 0.0), onda=None):
        """ax, ay = âncora; direcao = para onde a corrente "quer" sair (vetor unitário); onda = (amp, fase, comp)."""
        if direcao is not None:
            self.dir = direcao
        if abs(ax - self.p[0][0]) + abs(ay - self.p[0][1]) > 60:   # teleporte (respawn, sumiço): sem chicote
            self.reposicionar(ax, ay)
        p, a = self.p, self.ant
        p[0][0], p[0][1] = ax, ay
        for i in range(1, len(p)):
            q, qa = p[i], a[i]
            vx, vy = (q[0] - qa[0]) * self.arrasto, (q[1] - qa[1]) * self.arrasto
            qa[0], qa[1] = q[0], q[1]
            q[0] += vx + forca[0]
            q[1] += vy + self.grav + forca[1]
            if onda:
                amp, fase, comp = onda
                k = amp * math.sin(fase - i * comp) * (i / len(p))
                q[0] += -self.dir[1] * k
                q[1] += self.dir[0] * k
        for _ in range(2):
            for i in range(1, len(p)):
                q, ant = p[i], p[i - 1]
                if self.rigidez:
                    if i >= 2:
                        d0x, d0y = ant[0] - p[i - 2][0], ant[1] - p[i - 2][1]
                        n0 = math.hypot(d0x, d0y) or 1
                        alvo = (ant[0] + d0x / n0 * self.seg, ant[1] + d0y / n0 * self.seg)
                    else:
                        alvo = (ant[0] + self.dir[0] * self.seg, ant[1] + self.dir[1] * self.seg)
                    q[0] += (alvo[0] - q[0]) * self.rigidez
                    q[1] += (alvo[1] - q[1]) * self.rigidez
                dx, dy = q[0] - ant[0], q[1] - ant[1]
                d = math.hypot(dx, dy) or 0.001
                f = (d - self.seg) / d
                q[0] -= dx * f
                q[1] -= dy * f
        p[0][0], p[0][1] = ax, ay


class Passada:
    """Ciclo de passos pela distância percorrida: dois (ou mais) pés defasados; parado, os pés voltam ao lugar."""

    def __init__(self, passo_px=7.0):
        self.fase = random.uniform(0, math.tau)
        self.passo_px = passo_px
        self.amp = Mola(0.0, 0.25, 0.6)

    def andar(self, dx, no_chao=True):
        if no_chao:
            self.fase += abs(dx) / self.passo_px * math.pi
        self.amp.passo(1.0 if abs(dx) > 0.05 and no_chao else 0.0)

    def pe(self, i, n=2, comp=4.0, alt=2.5):
        """(deslocamento x, altura) do pé i; a fase dos pés se alterna."""
        f = self.fase + i * math.tau / n
        a = self.amp.v
        return math.cos(f) * comp * a, max(0.0, math.sin(f)) * alt * a


class Olhos:
    """Pupilas que seguem um alvo, pálpebra que pisca, sobrancelha de raiva."""

    def __init__(self):
        self.ox, self.oy = Mola(0, 0.3, 0.55), Mola(0, 0.3, 0.55)
        self.piscar = random.randint(60, 200)
        self.fecha = 0

    def passo(self, dx, dy):
        n = math.hypot(dx, dy) or 1
        self.ox.passo(dx / n)
        self.oy.passo(dy / n * 0.8)
        self.piscar -= 1
        if self.piscar <= 0:
            self.fecha = 7
            self.piscar = random.randint(90, 260) if random.random() > 0.2 else 12   # às vezes pisca duas vezes
        self.fecha = max(0, self.fecha - 1)

    @property
    def fechado(self):
        return 2 <= self.fecha <= 5


# ===================================================================== desenho das peças

def esfera(rx, ry, cor, luz=True):
    """Elipse sombreada (luz de cima à esquerda) pronta para colar; rx, ry em px inteiros. Fica em cache."""
    rx, ry = max(1, int(round(rx))), max(1, int(round(ry)))
    ch = (rx, ry, tuple(cor), luz)
    s = _esferas.get(ch)
    if s is None:
        if len(_esferas) > 2500:
            _esferas.clear()
        w, h = 2 * rx + 1, 2 * ry + 1
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        sombra, meio, clara = escuro(cor, 0.32), cor[:3], claro(cor, 0.4)
        pygame.draw.ellipse(s, sombra, (0, 0, w, h))
        if luz and rx >= 2 and ry >= 2:
            pygame.draw.ellipse(s, meio, (0, 0, w - max(1, rx // 3), h - max(1, ry // 3)))
            if rx >= 3 and ry >= 3:
                pygame.draw.ellipse(s, clara, (max(1, rx // 3), max(1, ry // 4), max(2, rx // 2), max(2, ry // 2)))
                s.set_at((max(1, rx // 2), max(1, ry // 3)), (255, 255, 255))
        else:
            pygame.draw.ellipse(s, meio, (0, 0, w, h - 1))
        if len(cor) == 4:
            s.set_alpha(cor[3])
        _esferas[ch] = s
    return s


def bola(c, x, y, rx, ry=None, cor=(200, 200, 200), luz=True):
    s = esfera(rx, ry if ry is not None else rx, cor, luz)
    c.blit(s, (int(round(x - s.get_width() / 2)), int(round(y - s.get_height() / 2))))


def haste(c, p0, p1, larg, cor):
    """Segmento grosso de pontas redondas (osso, perna, braço, tentáculo)."""
    p0, p1 = (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1])))
    if larg <= 1:
        pygame.draw.line(c, cor, p0, p1)
        return
    pygame.draw.line(c, cor, p0, p1, larg)
    r = larg // 2
    if r:
        pygame.draw.circle(c, cor, p0, r)
        pygame.draw.circle(c, cor, p1, r)


def ik(quadril, pe, l1, l2, dobra=1):
    """Joelho de uma perna de duas hastes (l1 coxa, l2 canela). dobra = +1 joelho para a frente (direita)."""
    dx, dy = pe[0] - quadril[0], pe[1] - quadril[1]
    d = math.hypot(dx, dy) or 0.001
    d2 = min(d, l1 + l2 - 0.01)
    a = (l1 * l1 - l2 * l2 + d2 * d2) / (2 * d2)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    mx, my = quadril[0] + dx / d * a, quadril[1] + dy / d * a
    return mx + dobra * (-dy / d) * h * -1, my + dobra * (dx / d) * h * -1


def perna(c, quadril, pe, l1, l2, larg, cor, dobra=1, pata=None):
    j = ik(quadril, pe, l1, l2, dobra)
    haste(c, quadril, j, larg, cor)
    haste(c, j, pe, max(1, larg - 1), cor)
    if pata:
        pw = pata
        pygame.draw.line(c, cor, (int(pe[0] - pw // 2), int(pe[1])), (int(pe[0] + pw - pw // 2), int(pe[1])), max(1, larg - 1))
    return j


def corda(c, pts, cor, larg=1, afina=False):
    """Desenha uma Corrente (ou lista de pontos) como linha; afina = fica mais fina na ponta."""
    for i in range(len(pts) - 1):
        lg = larg
        if afina and larg > 1:
            lg = max(1, int(round(larg * (1 - i / len(pts)))))
        haste(c, pts[i], pts[i + 1], lg, cor)


def olho(c, x, y, r, olhos, cor_iris=(30, 24, 40), branco=(250, 250, 244), bravo=False, lado=1, fechado=None):
    """Olho de desenho animado: branco, pupila que segue o alvo, pálpebra; r = raio (1 a 4)."""
    x, y = int(round(x)), int(round(y))
    fch = olhos.fechado if fechado is None else fechado
    if fch:
        pygame.draw.line(c, K, (x - r, y), (x + r, y))
        return
    if r <= 1:
        c.fill(cor_iris, (x, y, 1, 2))
        return
    pygame.draw.ellipse(c, branco, (x - r, y - r - 1, 2 * r + 1, 2 * r + 2))
    px = x + int(round(olhos.ox.v * (r - 1)))
    py = y + int(round(olhos.oy.v * (r - 1)))
    pr = max(1, r // 2)
    if pr == 1:
        c.fill(cor_iris, (px, py - 1, 1, 2))
        c.fill(cor_iris, (px + (1 if olhos.ox.v >= 0 else -1), py - 1, 1, 2))
    else:
        pygame.draw.circle(c, cor_iris, (px, py), pr)
        c.set_at((px - 1, py - 1), (255, 255, 255))
    if bravo:
        pygame.draw.line(c, K, (x - r - 1, y - r - 2 + (1 if lado > 0 else 0)), (x + r, y - r + (0 if lado > 0 else -1)), 1)


def girar(c, surf, pivo_local, pos, graus):
    """Cola `surf` girada em torno do ponto `pivo_local` (coord. dentro de surf), com o pivô em `pos` no quadro."""
    w, h = surf.get_size()
    rot = pygame.transform.rotate(surf, graus)
    cx, cy = w / 2, h / 2
    vx, vy = pivo_local[0] - cx, pivo_local[1] - cy
    a = math.radians(-graus)
    rx, ry = vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)
    rw, rh = rot.get_size()
    c.blit(rot, (int(round(pos[0] - rx - rw / 2)), int(round(pos[1] - ry - rh / 2))))


def contorno(s, cor=K):
    """Contorno de 1 px em volta de tudo que não é transparente (na mesma superfície, sem aumentar)."""
    m = pygame.mask.from_surface(s, 8)
    sil = m.to_surface(setcolor=cor, unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out.blit(sil, (dx, dy))
    out.blit(s, (0, 0))
    return out


# ===================================================================== o boneco

class Modelo:
    """Base de todo boneco. Subclasses definem W, H, OX, OY e `pinta(c, e)`; opcionalmente `anima(e, g)`.
    `voa` = a origem é o centro da hitbox (quem voa) em vez do centro-baixo."""
    W, H, OX, OY = 32, 32, 16, 28
    voa = False
    com_contorno = True
    cor_contorno = K

    def __init__(self):
        self.t = random.randrange(1000)
        self.c = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.olhos = Olhos()
        self.sq = Mola(1.0, 0.22, 0.68)              # amassa e estica (1 = normal; < 1 achatado)
        self.inclina = Mola(0.0, 0.15, 0.7)          # inclinação do corpo pela velocidade
        self.vy_ant = 0.0
        self.chao_ant = True
        self.virado = 1
        self.mundo = (0.0, 0.0)                      # origem do modelo no mundo (para as correntes)
        self.escala = 1.0
        self.brilhos = []                            # [(x, y, r)] dos olhos que brilham (monstros)

    # --- coordenadas: correntes vivem no mundo; o desenho, no quadro do modelo virado à direita
    def origem_mundo(self, e):
        return (e.x + e.w / 2, e.y + (e.h / 2 if self.voa else e.h))

    def para_mundo(self, lx, ly):
        """Ponto do quadro (relativo à origem, virado à direita) → mundo."""
        ox, oy = self.mundo
        return ox + (lx - self.OX) * self.virado * self.escala, oy + (ly - self.OY) * self.escala

    def para_quadro(self, wx, wy):
        ox, oy = self.mundo
        return self.OX + (wx - ox) * self.virado / self.escala, self.OY + (wy - oy) / self.escala

    def pontos(self, corrente):
        return [self.para_quadro(x, y) for x, y in corrente.p]

    # --- passo (chamado pelo Jogo depois do update do inimigo)
    def passo(self, e, g):
        self.t += 1
        self.virado = 1 if getattr(e, "virado", 1) >= 0 else -1
        self.escala = getattr(e, "escala", 1) or 1
        self.mundo = self.origem_mundo(e)
        vy = getattr(e, "vy", 0.0)
        chao = getattr(e, "no_chao", True)
        if chao and not self.chao_ant and self.vy_ant > 1.5:          # aterrissou: amassa
            self.sq.chute(-min(0.5, self.vy_ant * 0.09))
        if not chao and self.chao_ant and vy < -1:                    # pulou: estica
            self.sq.chute(0.25)
        self.sq.passo(1.0 + (max(-0.15, min(0.18, -vy * 0.03)) if not chao else 0.0))
        self.inclina.passo(max(-1.0, min(1.0, getattr(e, "vx", 0.0) * self.virado)))
        p = g.p
        ex, ey = self.para_mundo(*self.olho_base())
        self.olhos.passo((p.x + p.w / 2 - ex) * self.virado, (p.y + p.h * 0.4 - ey))
        self.anima(e, g)                                              # (vê o estado anterior em chao_ant/vy_ant)
        self.vy_ant, self.chao_ant = vy, chao

    def olho_base(self):
        return self.OX, self.OY - 8

    def anima(self, e, g):
        pass

    def pinta(self, c, e):
        raise NotImplementedError

    # --- desenho
    def quadro(self, e, branco=False):
        c = self.c
        c.fill((0, 0, 0, 0))
        self.brilhos = []
        self.pinta(c, e)
        s = contorno(c, self.cor_contorno) if self.com_contorno else c
        if branco:
            s = s.copy() if s is c else s
            s.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        ox = self.OX
        if self.virado < 0:
            s = pygame.transform.flip(s, True, False)
            ox = self.W - self.OX
        oy = self.OY
        br = self.brilhos
        if self.virado < 0:
            br = [(self.W - x, y, r) for x, y, r in br]
        if self.escala != 1:
            s = pygame.transform.scale_by(s, self.escala)
            ox, oy = ox * self.escala, oy * self.escala
            br = [(x * self.escala, y * self.escala, r * self.escala) for x, y, r in br]
        return s, ox, oy, br

    def draw(self, tela, cam, e, branco=False, dx=0, dy=0):
        """Cola o boneco no mundo; devolve (x, y da superfície na tela, brilhos já na tela)."""
        if self.t == 0 or self.mundo == (0.0, 0.0):
            self.mundo = self.origem_mundo(e)
        s, ox, oy, br = self.quadro(e, branco)
        wx, wy = self.origem_mundo(e)
        x, y = int(round(wx - ox - cam[0])) + dx, int(round(wy - oy - cam[1])) + dy
        tela.blit(s, (x, y))
        return x, y, [(x + bx, y + by, r) for bx, by, r in br]
