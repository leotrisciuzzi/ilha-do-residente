"""Os inimigos como bonecos articulados (motor em rig.py). Cada um tem várias partes que se mexem sozinhas:

    bacilo ........ corpo que ondula em 4 gomos, 2 flagelos que chicoteiam, pili, cílios que andam
    vírus ......... cápsula que gira, 8 espículas com mola (vibram ao cair), olhos que seguem
    aedes ......... asas batendo, abdome listrado que balança, 6 patas penduradas com física, probóscide
    estafilococo .. 5 cocos que chacoalham com atraso, 2 pernas com joelho, passada que não escorrega
    estreptococo .. corrente de cocos arrastada pela cabeça (vira e o corpo dá a volta), perninhas por coco
    fago .......... cápsula, colar, bainha que encolhe ao agachar, 6 patas aranha com IK, fibras da cauda
    ameba ......... pseudópodes que estendem e puxam, núcleo que balança dentro, vacúolos
    caixa ......... tampa com dobradiça que abre ao atirar, olhos espiando, pés que batem
    comprimido .... duas metades girando pelo chão percorrido, rosto que fica de pé, estica ao quicar
    cândida ....... caule de 3 gomos que balança, mandíbula que abre antes do esporo, brotos
    carrapato ..... 8 patas que se debatem, escudo, hipostômio
    morcego ....... asas com braço, cotovelo e dedos, orelhas com mola; dormindo, embrulhado de cabeça para baixo
    lombriga ...... verme de 7 gomos com física, cabeça que ergue, boca que abre
    bicho-questão . pelo que balança, olho único que segue, chifres com mola, placa da questão em pêndulo
    mosca, cuspidor, chifrudo, louva-a-deus, colosso, glóbulo, tatu, musgo, feiticeiro e água-viva (monstros.py)

Os comportamentos continuam em game.py, inimigos.py e monstros.py; aqui só o corpo."""
import math
import random

import pygame

from .rig import (K, Corrente, Modelo, Mola, Passada, bola, claro, corda, escuro, esfera, girar, haste, mix, olho,
                  perna)

# paletas (as mesmas dos desenhos antigos)
BAC = ((255, 214, 226), (244, 150, 180), (204, 96, 140))
BAC_BRAVO = ((255, 176, 168), (236, 84, 84), (176, 40, 56))
OURO = (250, 200, 60)
CASCA, CASCA2, CASCA_LUZ = (46, 40, 60), (30, 26, 42), (78, 70, 98)
OSSO, OSSO2 = (228, 220, 204), (164, 156, 150)
OLHO_M, OLHO_MIOLO, INFEC = (255, 140, 40), (255, 236, 170), (236, 110, 36)
KM = (14, 10, 22)

_asas = {}


def _asa(w, h, cor):
    ch = (w, h, cor)
    if ch not in _asas:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, cor, (0, 0, w, h))
        pygame.draw.ellipse(s, (255, 255, 255, min(255, cor[3] + 60)), (1, 1, w - 2, h - 2), 1)
        pygame.draw.line(s, (255, 255, 255, 120), (1, h // 2), (w - 2, h // 2))
        _asas[ch] = s
    return _asas[ch]


def _olho_mascara(m, c, x, y, aceso, grande=True):
    """Olho escavado na máscara de osso, com brilho laranja (monstros)."""
    x, y = int(round(x)), int(round(y))
    k = 0.55 + 0.45 * max(0.0, min(1.0, aceso))
    cor = tuple(int(v * k) for v in OLHO_M)
    c.fill(KM, (x, y - 1, 2, 3))
    if grande:
        c.fill(cor, (x, y, 2, 2))
        c.set_at((x, y), OLHO_MIOLO)
    else:
        c.set_at((x, y), cor)
    m.brilhos.append((x + 1, y + 1, 3))


def _mascara(m, c, cx, cy, w, h, olhos_x, aceso, chifres=0, ang_chifre=0.0):
    pygame.draw.ellipse(c, OSSO, (int(cx - w / 2), int(cy - h / 2), w, h))
    pygame.draw.line(c, OSSO2, (int(cx - w / 2 + 1), int(cy + h / 2 - 1)), (int(cx + w / 2 - 1), int(cy + h / 2 - 1)))
    if chifres:
        for lado in (-1, 1):
            bx, by = cx + lado * (w / 2 - 1), cy - h / 2 + 1
            a = math.radians(-90 + lado * 18 + ang_chifre * lado)
            haste(c, (bx, by), (bx + math.cos(a) * chifres, by + math.sin(a) * chifres), 2, OSSO)
    for ox in olhos_x:
        _olho_mascara(m, c, cx + ox, cy, aceso)


# =====================================================================================================================
#                                                      micróbios
# =====================================================================================================================

class Bacilo(Modelo):
    W, H, OX, OY = 40, 22, 20, 19

    def __init__(self, bravo=False):
        super().__init__()
        self.bravo = bravo
        self.flag = None
        self.passos = Passada(4.0)

    def olho_base(self):
        return self.OX + 5, self.OY - 6

    def anima(self, e, g):
        self.passos.andar(e.vx, e.no_chao)
        if self.flag is None:
            self.flag = [Corrente(7, 2.2, *self.para_mundo(self.OX - 8, self.OY - 4 - 2 * i), grav=0.02, arrasto=0.8,
                                  rigidez=0.35, direcao=(-self.virado, 0)) for i in range(2)]
        for i, f in enumerate(self.flag):
            ax, ay = self.para_mundo(self.OX - 8, self.OY - 3 - 3 * i)
            f.passo(ax, ay, (-self.virado, 0.15 * (1 - 2 * i)), onda=(1.1, self.t * 0.35 + i * 2, 0.9))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        claro_, meio, esc = BAC_BRAVO if self.bravo else BAC
        sq = self.sq.v
        for f in self.flag or ():
            corda(c, self.pontos(f), esc, 1)
        for i in range(5):                                      # cílios que "andam" por baixo
            dx, alt = self.passos.pe(i, 5, 1.6, 1.4)
            x = ox - 6 + i * 3
            haste(c, (x, oy - 3), (x + dx, oy - alt), 1, esc)
        ry = 4.0 / max(0.7, sq) ** 0.5
        for i in range(4):                                      # 4 gomos com onda peristáltica
            x = ox - 6 + i * 4.2
            y = oy - 6 + math.sin(self.t * 0.18 - i * 1.1) * 0.6
            bola(c, x, y, 4.6, ry + 0.4 * math.sin(self.t * 0.18 - i * 1.1), meio)
        for i in range(4):                                      # pili no dorso
            x = ox - 5 + i * 4
            a = math.sin(self.t * 0.2 + i) * 0.6
            haste(c, (x, oy - 10), (x + math.sin(a) * 2 - 1, oy - 12.5), 1, esc)
        bx = ox + 4
        olho(c, bx + 1, oy - 7, 2, self.olhos, bravo=self.bravo)
        olho(c, bx + 5, oy - 7, 2, self.olhos, bravo=self.bravo, lado=-1)
        boca = 1 + (1 if self.bravo else 0)
        c.fill(escuro(esc, 0.5), (bx + 2, oy - 4, 3, boca))


class Virus(Modelo):
    W, H, OX, OY = 34, 34, 17, 31

    def __init__(self):
        super().__init__()
        self.esp = [Mola(1.0, 0.25, 0.75) for _ in range(9)]
        self.giro = random.uniform(0, math.tau)

    def anima(self, e, g):
        if e.no_chao and not self.chao_ant:
            for m in self.esp:
                m.chute(random.uniform(-0.6, 0.6))
        for i, m in enumerate(self.esp):
            m.passo(1.0 + 0.12 * math.sin(self.t * 0.12 + i * 1.7))
        self.giro += 0.02 + abs(e.vx) * 0.05

    def olho_base(self):
        return self.OX, self.OY - 9

    def pinta(self, c, e):
        cx, cy = self.OX, self.OY - 9
        sq = self.sq.v
        rx, ry = 6.5 / sq ** 0.5, 6.5 * sq
        cy = self.OY - ry - 3
        for i, m in enumerate(self.esp):                        # espículas (proteína S) com mola
            a = self.giro + i * math.tau / len(self.esp)
            r0 = 5.5
            r1 = r0 + 3.6 * m.v
            p0 = (cx + math.cos(a) * r0 * rx / 6.5, cy + math.sin(a) * r0 * ry / 6.5)
            p1 = (cx + math.cos(a) * r1 * rx / 6.5, cy + math.sin(a) * r1 * ry / 6.5)
            haste(c, p0, p1, 1, (110, 64, 172))
            bola(c, p1[0], p1[1], 1, 1, (255, 176, 64) if (self.t // 12 + i) % 3 else (255, 232, 120), luz=False)
        bola(c, cx, cy, rx, ry, (160, 104, 224))
        for i in range(3):                                      # hexágonos da cápsula girando
            a = self.giro * 1.3 + i * 2.1
            px, py = cx + math.cos(a) * rx * 0.5, cy + math.sin(a) * ry * 0.5
            if math.sin(a) > -0.3:
                c.set_at((int(px), int(py)), (216, 184, 255))
        olho(c, cx - 1, cy - 1, 2, self.olhos, bravo=True)
        olho(c, cx + 3, cy - 1, 2, self.olhos, bravo=True, lado=-1)
        pygame.draw.line(c, (72, 36, 120), (int(cx), int(cy + 3)), (int(cx + 2), int(cy + 3)))
        for k in range(2):                                      # pezinhos
            fx = cx - 2 + k * 5
            haste(c, (fx, cy + ry - 1), (fx + (k * 2 - 1), self.OY - 1), 1, (110, 64, 172))


class Aedes(Modelo):
    W, H, OX, OY = 36, 30, 18, 14
    voa = True

    def __init__(self):
        super().__init__()
        self.patas = None
        self.abd = Mola(0, 0.12, 0.8)

    def olho_base(self):
        return self.OX + 6, self.OY - 1

    def anima(self, e, g):
        if self.patas is None:
            self.patas = [Corrente(3, 3.0, *self.para_mundo(self.OX - 1 + i * 2, self.OY + 2), grav=0.25, arrasto=0.8,
                                   direcao=(0, 1)) for i in range(6)]
        for i, p in enumerate(self.patas):
            ax, ay = self.para_mundo(self.OX - 2 + i * 1.6, self.OY + 2)
            p.passo(ax, ay, (0, 1), forca=(-0.05 * self.virado * (i % 3 - 1), 0))
        self.abd.passo(math.sin(self.t * 0.09) * 0.35 + self.inclina.v * 0.3)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        for p in self.patas or ():                              # patas listradas penduradas
            pts = self.pontos(p)
            corda(c, pts, (52, 52, 72))
            for q in pts[1:]:
                c.set_at((int(q[0]), int(q[1])), (240, 240, 250))
        a = self.abd.v                                          # abdome listrado num pivô
        for i in range(4):
            r = 3.2 - i * 0.45
            x = ox - 3 - i * 3.0 * math.cos(a)
            y = oy + 1 + i * 3.0 * math.sin(a) + i * 0.6
            bola(c, x, y, r, r * 0.8, (52, 52, 72) if i % 2 else (230, 230, 240), luz=i % 2 == 1)
        bola(c, ox + 1, oy, 3.6, 3.0, (52, 52, 72))
        for i in range(2):                                      # listras do tórax
            c.set_at((ox + i * 2, oy - 1), (240, 240, 250))
        bola(c, ox + 5, oy - 1, 2.2, 2.0, (92, 92, 120))
        haste(c, (ox + 6, oy), (ox + 11, oy + 4 + math.sin(self.t * 0.1)), 1, (40, 40, 56))   # probóscide
        olho(c, ox + 6, oy - 2, 1, self.olhos, cor_iris=(255, 60, 70))
        bate = math.sin(self.t * 1.9)                           # asas batendo (~ 18 batidas por segundo)
        asa = _asa(10, 4, (214, 238, 255, 150))
        for k, desloc in enumerate((-1.5, 1.0)):
            girar(c, asa, (0, 2), (ox + desloc, oy - 2), 30 + bate * 55 + k * 12)


class Estafilococo(Modelo):
    W, H, OX, OY = 30, 28, 15, 26
    BOLAS = [(-4.0, -12.5, 3.6), (2.5, -13.5, 3.9), (5.0, -8.5, 3.4), (-5.2, -7.5, 3.2), (0.0, -8.0, 4.6)]

    def __init__(self):
        super().__init__()
        self.passos = Passada(5.0)
        self.jig = [Mola(0, 0.2, 0.7) for _ in self.BOLAS]

    def olho_base(self):
        return self.OX + 1, self.OY - 9

    def anima(self, e, g):
        self.passos.andar(e.vx, e.no_chao)
        for i, m in enumerate(self.jig):
            m.passo(-self.inclina.v * (1.2 + (self.BOLAS[i][1] + 14) * -0.1) + math.sin(self.passos.fase + i) * 0.5)
        if e.no_chao and not self.chao_ant:
            for m in self.jig:
                m.chute(random.uniform(-1, 1))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        sq = self.sq.v
        cor_esc = (176, 120, 30)
        for i in range(2):                                      # 2 pernas com joelho e passada
            dx, alt = self.passos.pe(i, 2, 3.0, 2.2)
            quad = (ox - 2 + i * 4, oy - 5)
            pe_ = (ox - 3 + i * 5 + dx, oy - 1 - alt)
            perna(c, quad, pe_, 3, 3, 2, cor_esc, dobra=1, pata=3)
        for i, (bx, by, r) in enumerate(self.BOLAS):
            y = oy + (by + 2) * sq - 2
            bola(c, ox + bx + self.jig[i].v, y + math.sin(self.t * 0.1 + i) * 0.4, r, r * (0.92 + 0.08 * sq),
                 (236, 176, 44) if i < 2 else OURO)
        fy = oy - 8 * sq - 2
        olho(c, ox - 1 + self.jig[4].v, fy, 2, self.olhos)
        olho(c, ox + 3 + self.jig[4].v, fy, 2, self.olhos, lado=-1)
        c.fill((120, 70, 20), (int(ox + 1 + self.jig[4].v), int(fy + 3), 2, 1))


class Estreptococo(Modelo):
    W, H, OX, OY = 56, 24, 28, 21

    def __init__(self):
        super().__init__()
        self.corpo = None
        self.passos = Passada(4.0)
        self.bravo = False

    def olho_base(self):
        return self.OX + 13, self.OY - 7

    def anima(self, e, g):
        self.bravo = e.bravo
        self.passos.andar(e.vx, e.no_chao)
        cabeca = self.para_mundo(self.OX + 13, self.OY - 5)
        if self.corpo is None:
            self.corpo = Corrente(5, 6.4, *cabeca, grav=0.6, arrasto=0.7, direcao=(-self.virado, 0))
        self.corpo.passo(*cabeca)
        chao = e.y + e.h - 4.5
        for q in self.corpo.p[1:]:                              # os cocos ficam apoiados no chão
            if q[1] > chao:
                q[1] = chao

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        base = (230, 70, 70) if self.bravo else (120, 200, 120)
        pts = self.pontos(self.corpo) if self.corpo else [(ox + 13 - 6.4 * i, oy - 5) for i in range(5)]
        for i in range(len(pts) - 1, -1, -1):
            x, y = pts[i]
            fase = self.t * (0.3 if self.bravo else 0.16) - i * 1.1
            y += math.sin(fase) * 0.9
            for k in (0, 1):                                    # perninhas de cada coco
                dx, alt = self.passos.pe(k + i, 2, 1.6, 1.6)
                haste(c, (x - 1 + 2 * k, y + 2), (x - 1 + 2 * k + dx, oy - alt), 1, escuro(base, 0.5))
            r = 4.6 if i == 0 else 3.4 + 0.2 * math.sin(fase)
            bola(c, x, y, r, r, base if i % 2 == 0 else mix(base, (255, 255, 255), 0.15))
        hx, hy = pts[0][0], pts[0][1] + math.sin(self.t * 0.16) * 0.9
        olho(c, hx - 1, hy - 1, 2, self.olhos, bravo=self.bravo)
        olho(c, hx + 3, hy - 1, 2, self.olhos, bravo=self.bravo, lado=-1)
        if self.bravo:
            c.fill((190, 40, 50), (int(hx), int(hy + 2), 3, 2))
        else:
            c.fill((40, 90, 50), (int(hx + 1), int(hy + 2), 2, 1))


class Fago(Modelo):
    W, H, OX, OY = 34, 36, 17, 34

    def __init__(self):
        super().__init__()
        self.bainha = Mola(1.0, 0.25, 0.65)
        self.cabeca = Mola(0, 0.15, 0.7)

    def olho_base(self):
        return self.OX, self.OY - 25

    def anima(self, e, g):
        agachado = e.no_chao and e.t % 80 > 64
        self.bainha.passo(0.45 if agachado else (1.25 if not e.no_chao else 1.0))
        self.cabeca.passo(math.sin(self.t * 0.08) * 0.8)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        no_ar = not e.no_chao
        L = 9 * self.bainha.v
        base_y = oy - 7 if not no_ar else oy - 8
        topo = base_y - L
        for i, lado in enumerate((-1, -1, -1, 1, 1, 1)):        # 6 patas de aranha com joelho para cima
            k = i % 3
            quad = (ox + lado * 1.5, base_y)
            if no_ar:
                pe_ = (ox + lado * (6 + k * 2), base_y + 5 + k)
            else:
                pe_ = (ox + lado * (4 + k * 3.5), oy - 1)
            j = perna(c, quad, pe_, 5, 6, 1, (96, 150, 210), dobra=lado)
            c.set_at((int(j[0]), int(j[1])), (170, 220, 250))
        c.fill((96, 150, 210), (ox - 4, int(base_y), 9, 2))      # placa basal
        for y in range(int(topo), int(base_y)):                  # bainha listrada (encolhe ao agachar)
            c.fill((176, 176, 184) if (y - int(topo)) % 2 else (120, 120, 140), (ox - 1, y, 3, 1))
        c.fill((96, 150, 210), (ox - 3, int(topo) - 1, 7, 2))    # colar
        hx, hy = ox + self.cabeca.v, topo - 7
        pts = [(hx + 7 * math.cos(math.radians(a)), hy + 7 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        pygame.draw.polygon(c, (96, 150, 210), pts)
        pts2 = [(hx - 1 + 5.5 * math.cos(math.radians(a)), hy - 1 + 5.5 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        pygame.draw.polygon(c, (170, 220, 250), pts2)
        pygame.draw.line(c, (230, 248, 255), (int(hx - 4), int(hy - 3)), (int(hx - 2), int(hy - 5)))
        olho(c, hx - 1.5, hy, 2, self.olhos)
        olho(c, hx + 2.5, hy, 2, self.olhos, lado=-1)


class Ameba(Modelo):
    W, H, OX, OY = 32, 24, 16, 22

    def __init__(self, pequena=False):
        super().__init__()
        self.pequena = pequena
        self.nucleo = (Mola(0, 0.06, 0.85), Mola(0, 0.06, 0.85))
        self.k = 0.62 if pequena else 1.0

    def olho_base(self):
        return self.OX + 3, self.OY - 8 * self.k

    def anima(self, e, g):
        self.nucleo[0].passo(-self.inclina.v * 2 + math.sin(self.t * 0.05) * 1.5)
        self.nucleo[1].passo(math.cos(self.t * 0.04) * 1.0)

    def pinta(self, c, e):
        ox, oy, k = self.OX, self.OY, self.k
        verde = (150, 220, 160)
        t = self.t * 0.08
        sq = self.sq.v
        avanca = 0.5 + 0.5 * math.sin(t * 1.2)                  # pseudópode da frente estende e puxa
        bolas = [(-7 + 1.5 * math.sin(t), -3, 3.2), (7 + 3 * avanca, -3.5 + avanca * 0.5, 3.0 + avanca),
                 (0, -5.5 * sq, 5.4), (-9.5 + math.cos(t), -1.6, 2.2), (9.5 + 2 * avanca, -1.4, 2.0),
                 (3 * math.sin(t * 0.7), -9 * sq, 3.0)]
        for bx, by, r in bolas:
            bola(c, ox + bx * k, oy - 1 + by * k, r * k + 0.3, (r * k + 0.3) * (0.9 + 0.1 * sq), verde)
        if not self.pequena:
            bola(c, ox - 2 + self.nucleo[0].v, oy - 6 + self.nucleo[1].v, 2.3, 2.0, (70, 130, 90))
            for i in range(2):                                  # vacúolos
                a = t * 0.6 + i * 3
                c.set_at((int(ox + 4 * math.cos(a)), int(oy - 5 + 2 * math.sin(a))), (210, 250, 220))
        ey = oy - 1 - 7 * k * sq
        olho(c, ox + 2 * k, ey, 2 if not self.pequena else 1, self.olhos)
        olho(c, ox + 6 * k, ey, 2 if not self.pequena else 1, self.olhos, lado=-1)


class Caixa(Modelo):
    W, H, OX, OY = 28, 32, 14, 30

    def __init__(self):
        super().__init__()
        self.tampa = Mola(0, 0.25, 0.62)
        self.recuo = Mola(0, 0.3, 0.6)
        self.passos = Passada(3.0)

    def olho_base(self):
        return self.OX, self.OY - 12

    def anima(self, e, g):
        f = e.t % 150
        abre = 1.0 if f > 132 or f < 8 else 0.0
        self.tampa.passo(abre)
        if f == 0:
            self.recuo.chute(-2.0)
            self.sq.chute(-0.35)
        self.recuo.passo(0)
        self.passos.andar(0.3 if f > 120 else 0.0)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        sq = self.sq.v
        for i in range(2):                                      # pezinhos sapateando antes do tiro
            _, alt = self.passos.pe(i, 2, 0, 2)
            c.fill((40, 40, 50), (ox - 5 + i * 7, int(oy - 2 - alt), 4, 2))
        h = 13 * sq
        topo = oy - 2 - h
        x0 = ox - 7 + self.recuo.v
        r = pygame.Rect(int(x0), int(topo), 14, int(h))
        c.fill((255, 216, 48), r)
        c.fill((208, 136, 16), (r.x, r.y, 2, r.h))
        c.fill((255, 240, 150), (r.right - 3, r.y + 1, 1, r.h - 2))
        sx, sy = r.centerx, r.y + r.h * 0.62                    # símbolo de risco biológico simplificado
        for a in (90, 210, 330):
            b = math.radians(a + self.t * 0.5)
            pygame.draw.circle(c, K, (int(sx + math.cos(b) * 2.4), int(sy - math.sin(b) * 2.4)), 2, 1)
        c.set_at((int(sx), int(sy)), K)
        # olhos espiando pela fresta: aparecem mais quando a tampa abre
        ab = self.tampa.v
        ey = topo + 2 - ab * 2
        if ab > 0.15:
            c.fill((20, 18, 30), (r.x + 1, int(ey - 2), 12, 3))
        olho(c, r.x + 4, ey + 1, 2, self.olhos, bravo=ab > 0.5)
        olho(c, r.x + 9, ey + 1, 2, self.olhos, bravo=ab > 0.5, lado=-1)
        tampa = pygame.Surface((16, 4), pygame.SRCALPHA)        # tampa vermelha com dobradiça atrás
        tampa.fill((232, 64, 72))
        tampa.fill((144, 32, 56), (0, 3, 16, 1))
        tampa.fill((255, 140, 150), (1, 0, 13, 1))
        girar(c, tampa, (0, 3), (r.x - 1, topo + 0.5), ab * 55)
        if ab > 0.6:                                            # a seringa aparecendo
            c.fill((210, 236, 255), (r.right - 2, int(topo - 3), 4, 2))
            c.fill((150, 156, 178), (r.right + 2, int(topo - 2), 3, 1))


class Comprimido(Modelo):
    W, H, OX, OY = 26, 24, 13, 22

    def __init__(self):
        super().__init__()
        self.giro = 0.0
        self.vx_ant = 0.0

    def olho_base(self):
        return self.OX, self.OY - 6

    def anima(self, e, g):
        self.giro -= e.vx / 4.5 * 57.3 * self.virado
        if self.vx_ant * e.vx < 0:                              # bateu na parede: estica
            self.sq.chute(-0.4)
        self.vx_ant = e.vx

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        caps = pygame.Surface((16, 9), pygame.SRCALPHA)         # cápsula: metade branca, metade vermelha
        pygame.draw.rect(caps, (248, 248, 232), (0, 0, 10, 9), border_radius=4)
        pygame.draw.rect(caps, (232, 64, 72), (7, 0, 9, 9), border_radius=4)
        caps.fill((232, 64, 72), (7, 0, 3, 9))
        caps.fill((200, 200, 214), (1, 6, 6, 2))
        caps.fill((144, 32, 56), (8, 6, 7, 2))
        caps.fill(K, (7, 0, 1, 9))
        caps.fill((255, 255, 255), (2, 1, 3, 1))
        caps.fill((255, 170, 170), (10, 1, 3, 1))
        sq = self.sq.v
        if abs(sq - 1) > 0.03:
            caps = pygame.transform.scale(caps, (max(8, int(16 * (2 - sq))), max(5, int(9 * sq))))
        girar(c, caps, (caps.get_width() / 2, caps.get_height() / 2), (ox, oy - 6), self.giro)
        rapido = abs(e.vx) > 1.2                                # rosto fica de pé; olhos rodando quando rápido
        if rapido:
            a = self.t * 0.5
            self.olhos.ox.v, self.olhos.oy.v = math.cos(a), math.sin(a)
        olho(c, ox - 2, oy - 7, 2, self.olhos, fechado=False)
        olho(c, ox + 3, oy - 7, 2, self.olhos, fechado=False)
        if abs(e.vx) > 1:                                       # rastro de velocidade atrás
            for i in range(2):
                c.fill((255, 255, 255, 150), (ox - 13 + (self.t + i) % 2, oy - 8 + i * 4, 3, 1))


class Candida(Modelo):
    W, H, OX, OY = 30, 38, 15, 36

    def __init__(self):
        super().__init__()
        self.mand = Mola(0, 0.2, 0.65)

    def olho_base(self):
        return self.OX, self.OY - 24

    def anima(self, e, g):
        f = e.t % e.CICLO
        self.mand.passo(1.0 if 30 < f < 70 else 0.0)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        t = self.t * 0.07
        pts = []
        for i in range(4):                                      # caule em gomos (hifas) que balança
            sway = math.sin(t - i * 0.6) * (i * 0.9)
            pts.append((ox + sway, oy - 2 - i * 5))
        for i in range(len(pts) - 1):
            haste(c, pts[i], pts[i + 1], 4 - i // 2, (96, 200, 72) if i % 2 else (40, 128, 56))
        for i, lado in ((1, -1), (2, 1)):                       # brotos (blastoconídios)
            x, y = pts[i]
            bola(c, x + lado * 4, y - 1 + math.sin(t * 2 + i), 2.2, 2.0, (252, 236, 210))
        hx, hy = pts[-1][0], pts[-1][1] - 6
        ab = self.mand.v * 4                                    # cabeça com mandíbula que abre
        bola(c, hx, hy - ab * 0.5, 6.5, 5.0, (252, 236, 210))
        c.fill((214, 180, 150), (int(hx - 5), int(hy + 1 - ab * 0.5), 11, 1))
        if ab > 0.5:
            pygame.draw.ellipse(c, (120, 30, 50), (int(hx - 4), int(hy + 1 - ab * 0.4), 9, int(ab + 2)))
            for k in range(3):                                  # dentes
                c.fill((255, 255, 255), (int(hx - 3 + k * 3), int(hy + 1 - ab * 0.4), 1, 2))
        bola(c, hx, hy + 3 + ab * 0.6, 5.0, 2.4, (230, 210, 180))
        for k in range(5):                                      # pintas
            a = k * 1.3
            c.set_at((int(hx + math.cos(a) * 4), int(hy - 2 - ab * 0.5 + math.sin(a) * 2)), (214, 180, 150))
        olho(c, hx - 2.5, hy - 2 - ab * 0.5, 2, self.olhos, bravo=True)
        olho(c, hx + 2.5, hy - 2 - ab * 0.5, 2, self.olhos, bravo=True, lado=-1)


class Carrapato(Modelo):
    W, H, OX, OY = 34, 28, 17, 13
    voa = True

    def __init__(self):
        super().__init__()
        self.agita = Mola(0, 0.2, 0.7)

    def olho_base(self):
        return self.OX, self.OY + 2

    def anima(self, e, g):
        self.agita.passo(1.0 if e.estado in ("desce", "embaixo") else 0.25)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        cor_p = (100, 56, 36)
        for i in range(8):                                      # 8 patas que se debatem
            lado = -1 if i < 4 else 1
            k = i % 4
            quad = (ox + lado * 3, oy - 3 + k * 2.2)
            ang = math.radians(-50 + k * 32) + math.sin(self.t * 0.45 * self.agita.v + i * 1.3) * 0.45 * self.agita.v
            pe_ = (ox + lado * (7 + math.cos(ang) * 4), oy - 3 + k * 2.2 + math.sin(ang) * 5)
            perna(c, quad, pe_, 4, 4, 1, cor_p, dobra=-lado)
        resp = 1 + 0.05 * math.sin(self.t * 0.1)
        bola(c, ox, oy, 6.5 * resp, 7.0, (150, 92, 60))
        bola(c, ox, oy - 2, 4.5, 4.0, (196, 140, 96))             # escudo
        for k in range(3):
            c.set_at((ox - 3 + k * 3, oy + 3), (100, 56, 36))
        hy = oy + 6 + math.sin(self.t * 0.2) * 0.5               # capítulo (cabeça) de baixo
        bola(c, ox, hy, 3, 2.2, (120, 72, 40))
        haste(c, (ox - 1, hy + 1), (ox - 1, hy + 3), 1, (80, 40, 30))
        haste(c, (ox + 1, hy + 1), (ox + 1, hy + 3), 1, (80, 40, 30))
        olho(c, ox - 2, oy + 2, 1, self.olhos)
        olho(c, ox + 2, oy + 2, 1, self.olhos)


class Morcego(Modelo):
    W, H, OX, OY = 44, 30, 22, 14
    voa = True

    def __init__(self):
        super().__init__()
        self.orelha = Mola(0, 0.2, 0.6)

    def olho_base(self):
        return self.OX + 2, self.OY - 1

    def anima(self, e, g):
        self.orelha.passo(math.sin(self.t * 0.4) * 0.6 if e.estado != "dorme" else 0)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        D, d = (110, 96, 140), (70, 58, 96)
        if e.estado == "dorme":                                 # embrulhado nas asas, de cabeça para baixo
            resp = math.sin(self.t * 0.05)
            bola(c, ox, oy, 5, 6.5 + resp * 0.4, d)
            pygame.draw.line(c, D, (ox - 4, oy - 4), (ox + 4, oy + 4))
            pygame.draw.line(c, D, (ox + 4, oy - 4), (ox - 4, oy + 4))
            haste(c, (ox - 1, oy - 7), (ox - 1, oy - 9), 1, d)
            haste(c, (ox + 1, oy - 7), (ox + 1, oy - 9), 1, d)
            bola(c, ox, oy + 6, 3, 2.5, D)
            c.fill(K, (ox - 2, oy + 6, 1, 1))
            c.fill(K, (ox + 2, oy + 6, 1, 1))
            if (self.t // 40) % 3 == 0:                         # zzz
                c.set_at((ox + 6, oy - 2 - (self.t // 10) % 4), (200, 200, 240))
            return
        bate = math.sin(self.t * 0.42)
        for lado in (-1, 1):                                    # asa: ombro, cotovelo, pulso e 3 dedos
            omb = (ox + lado * 2, oy - 1)
            a = math.radians(-20 - bate * 50) if lado > 0 else math.radians(200 + bate * 50)
            cot = (omb[0] + math.cos(a) * 6, omb[1] + math.sin(a) * 6)
            b = a + lado * math.radians(25 + bate * 20)
            pul = (cot[0] + math.cos(b) * 6, cot[1] + math.sin(b) * 6)
            dedos = []
            for k in range(3):
                dd = b + lado * math.radians(-30 + k * 35 + bate * 10)
                dedos.append((pul[0] + math.cos(dd) * (7 - k), pul[1] + math.sin(dd) * (7 - k)))
            poly = [omb, cot, pul] + dedos + [(ox + lado * 1, oy + 3)]
            pygame.draw.polygon(c, d, [(int(x), int(y)) for x, y in poly])
            for q in dedos:
                haste(c, pul, q, 1, D)
            haste(c, omb, cot, 1, D)
            haste(c, cot, pul, 1, D)
        bola(c, ox, oy, 4, 4.5, D)
        bola(c, ox + 2, oy - 3, 3.2, 3.0, D)
        for lado in (-1, 1):                                    # orelhas com mola
            base = (ox + 2 + lado * 2, oy - 5)
            pt = (base[0] + lado * 1 + self.orelha.v, base[1] - 4)
            pygame.draw.polygon(c, D, [(int(base[0] - 1), int(base[1])), (int(pt[0]), int(pt[1])), (int(base[0] + 1), int(base[1]))])
        olho(c, ox + 1, oy - 3, 1, self.olhos, cor_iris=(255, 80, 80), branco=(255, 220, 220))
        olho(c, ox + 4, oy - 3, 1, self.olhos, cor_iris=(255, 80, 80), branco=(255, 220, 220))
        c.fill((255, 255, 255), (ox + 2, oy - 1, 1, 2))          # presinhas
        c.fill((255, 255, 255), (ox + 4, oy - 1, 1, 2))
        for lado in (-1, 1):
            haste(c, (ox + lado, oy + 4), (ox + lado * 2, oy + 7), 1, d)


class Lombriga(Modelo):
    W, H, OX, OY = 40, 26, 20, 23

    def __init__(self):
        super().__init__()
        self.corpo = None
        self.boca = Mola(0, 0.2, 0.6)

    def olho_base(self):
        return self.OX + 6, self.OY - 10

    def anima(self, e, g):
        ergue = 4 + 3 * abs(math.sin(self.t * 0.12))
        cabeca = self.para_mundo(self.OX + 6, self.OY - 3 - ergue)
        if self.corpo is None:
            self.corpo = Corrente(7, 2.6, *cabeca, grav=0.5, arrasto=0.75, rigidez=0.2, direcao=(-self.virado, 0.6))
        self.corpo.passo(*cabeca, direcao=(-self.virado, 0.7))
        chao = e.y + e.h - 2
        for q in self.corpo.p[2:]:
            q[1] = min(q[1], chao)
        self.boca.passo(1.0 if math.sin(self.t * 0.12) > 0.6 else 0.0)

    def pinta(self, c, e):
        P, p = (250, 168, 180), (210, 110, 130)
        pts = self.pontos(self.corpo) if self.corpo else [(self.OX + 6 - 2.6 * i, self.OY - 4) for i in range(7)]
        n = len(pts)
        for i in range(n - 1, -1, -1):
            r = 3.6 - i * 0.32 if i else 4.2
            bola(c, pts[i][0], pts[i][1], r, r * 0.95, P if i % 2 == 0 else p)
            if 0 < i < n - 1:
                c.set_at((int(pts[i][0]), int(pts[i][1] - r + 1)), (255, 220, 228))
        hx, hy = pts[0]
        ab = self.boca.v
        pygame.draw.ellipse(c, (190, 50, 80), (int(hx + 1), int(hy), 4, 2 + int(ab * 2)))
        olho(c, hx - 1, hy - 2, 2, self.olhos)
        olho(c, hx + 3, hy - 2, 2, self.olhos, lado=-1)


# =====================================================================================================================
#                                                 bicho-questão
# =====================================================================================================================

class BichoQuestao(Modelo):
    W, H, OX, OY = 34, 40, 17, 37

    def __init__(self, cor, revisao=False):
        super().__init__()
        from . import art
        self.cor = cor
        placa = art.spr(art.PLACA_R if revisao else art.PLACA_Q)
        self.placa = pygame.Surface((9, 16), pygame.SRCALPHA)  # placa no alto de um cabo
        self.placa.fill((120, 72, 40), (4, 8, 1, 8))
        self.placa.blit(placa, (0, 0))
        self.pend = Mola(0, 0.08, 0.92)                         # placa em pêndulo
        self.chifres = [Mola(0, 0.2, 0.75) for _ in range(2)]
        self.pelo = [Mola(0, 0.25, 0.7) for _ in range(9)]
        self.passos = Passada(4.0)
        self.bravo = False

    def olho_base(self):
        return self.OX + 1, self.OY - 10

    def anima(self, e, g):
        self.bravo = bool(getattr(e, "bravo", 0))
        self.passos.andar(e.vx, e.no_chao)
        self.pend.passo(-e.vx * self.virado * 0.5 - e.vy * 0.1)
        if not e.no_chao and self.chao_ant:
            self.pend.chute(0.5)
        for i, m in enumerate(self.chifres):
            m.passo(-self.inclina.v * 0.6 + (e.vy * 0.15 if not e.no_chao else 0))
            if e.no_chao and not self.chao_ant:
                m.chute(1.2 * (1 - 2 * i))
        for i, m in enumerate(self.pelo):
            m.passo(math.sin(self.t * 0.08 + i * 0.9) * 0.6 - self.inclina.v)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        cor = (232, 72, 72) if self.bravo else self.cor
        esc = escuro(cor, 0.45)
        sq = self.sq.v
        girar(c, self.placa, (4, 15), (ox - 8, oy - 9), 12 + self.pend.v * 25)  # placa atrás, legível
        for i in range(2):                                      # pés
            dx, alt = self.passos.pe(i, 2, 2.5, 2.0)
            c.fill((248, 144, 40), (int(ox - 5 + i * 7 + dx), int(oy - 3 - alt), 4, 3))
        rx, ry = 9.5 / sq ** 0.4, 7.0 * sq
        cy = oy - 3 - ry
        for i, m in enumerate(self.pelo):                       # tufos de pelo na borda que balançam
            a = math.pi * (0.9 + 1.2 * i / (len(self.pelo) - 1))
            bx, by = ox + math.cos(a) * rx, cy + math.sin(a) * ry
            tx, ty = bx + math.cos(a + m.v * 0.3) * 3, by + math.sin(a + m.v * 0.3) * 3
            pygame.draw.polygon(c, cor, [(int(bx - 1.5), int(by)), (int(tx), int(ty)), (int(bx + 1.5), int(by))])
        bola(c, ox, cy, rx, ry, cor)
        for i, lado in enumerate((-1, 1)):                      # chifrinhos com mola
            bx, by = ox + lado * 4, cy - ry + 1
            a = math.radians(-90 + lado * 20) + self.chifres[i].v * 0.25
            pt = (bx + math.cos(a) * 4, by + math.sin(a) * 4)
            haste(c, (bx, by), pt, 2, esc)
            bola(c, pt[0], pt[1], 1.4, 1.4, claro(cor, 0.4), luz=False)
        ex, ey = ox + 1, cy - 1.5                               # olho único (ciclope)
        olho(c, ex, ey, 4, self.olhos, cor_iris=(40, 30, 50), bravo=False)
        if self.bravo:
            pygame.draw.line(c, K, (int(ex - 5), int(ey - 6)), (int(ex + 4), int(ey - 3)), 2)
        my = cy + ry * 0.55                                     # boca com dentinhos
        c.fill(esc, (int(ox - 4), int(my), 9, 2))
        for k in range(4):
            c.set_at((int(ox - 3 + k * 2), int(my)), (255, 255, 255))


# =====================================================================================================================
#                                     monstros (contorno quase preto, máscara de osso, olhos que brilham)
# =====================================================================================================================

class _Monstro(Modelo):
    cor_contorno = KM

    def __init__(self):
        super().__init__()
        self.aceso = 0.6

    def anima(self, e, g):
        self.aceso = 0.55 + 0.45 * getattr(e, "alerta", 0.5)
        self.anima2(e, g)

    def anima2(self, e, g):
        pass


class Mosca(_Monstro):
    W, H, OX, OY = 30, 28, 15, 14
    voa = True

    def __init__(self):
        super().__init__()
        self.patas = None

    def anima2(self, e, g):
        if self.patas is None:
            self.patas = [Corrente(3, 2.4, *self.para_mundo(self.OX - 3 + 3 * i, self.OY + 4), grav=0.2, arrasto=0.8,
                                   direcao=(0, 1)) for i in range(3)]
        for i, p in enumerate(self.patas):
            p.passo(*self.para_mundo(self.OX - 3 + 3 * i, self.OY + 4), (0, 1),
                    onda=(0.4, self.t * 0.2 + i, 1.0))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        for p in self.patas or ():
            corda(c, self.pontos(p), CASCA2)
        bate = math.sin(self.t * (1.6 if e.estado != "vaga" else 1.1))
        asa = _asa(9, 5, (150, 170, 210, 150))
        girar(c, asa, (1, 2), (ox - 2, oy - 4), 140 - bate * 50)
        bola(c, ox - 1, oy, 6.5, 5.5, CASCA)
        bola(c, ox - 3, oy + 1, 3.0, 2.6, CASCA2)
        girar(c, asa, (1, 2), (ox + 1, oy - 4), 120 - bate * 50)
        hx, hy = ox + 4, oy - 2 + math.sin(self.t * 0.2) * 0.5
        alerta = e.estado != "vaga"
        if alerta:                                              # boca aberta, grito
            pygame.draw.ellipse(c, INFEC, (int(hx + 1), int(hy + 2), 3, 3 if (self.t // 4) % 2 else 2))
        _mascara(self, c, hx, hy, 7, 6, (-2, 1), self.aceso)


class Cuspidor(_Monstro):
    W, H, OX, OY = 36, 34, 18, 17
    voa = True

    def __init__(self):
        super().__init__()
        self.inch = Mola(0, 0.2, 0.65)
        self.patas = None

    def anima2(self, e, g):
        alvo = 0.0
        if e.estado == "incha":
            alvo = min(1.0, 1 - e.timer / 26)
        self.inch.passo(alvo)
        if self.patas is None:
            self.patas = [Corrente(3, 2.6, *self.para_mundo(self.OX - 4 + 3 * i, self.OY + 5), grav=0.18, arrasto=0.82,
                                   direcao=(0, 1)) for i in range(4)]
        for i, p in enumerate(self.patas):
            p.passo(*self.para_mundo(self.OX - 4 + 3 * i, self.OY + 5), (0, 1), onda=(0.5, self.t * 0.15 + i, 0.8))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        for p in self.patas or ():
            corda(c, self.pontos(p), CASCA2)
        inch = self.inch.v
        r = 7 + inch * 2.5
        bate = math.sin(self.t * 0.9)
        asa = _asa(8, 4, (150, 170, 210, 140))
        girar(c, asa, (1, 2), (ox - 3, oy - r + 2), 130 - bate * 45)
        for k in range(5):                                      # espinhos das costas, eriçam ao inchar
            a = math.pi * (1.05 + 0.2 * k)
            l = 3 + inch * 2 + math.sin(self.t * 0.1 + k) * 0.5
            p0 = (ox + math.cos(a) * (r - 1), oy + math.sin(a) * (r - 1))
            p1 = (ox + math.cos(a) * (r + l), oy + math.sin(a) * (r + l))
            haste(c, p0, p1, 2, CASCA2)
        bola(c, ox, oy, r, r - 1 - inch * 0.5, CASCA)
        girar(c, asa, (1, 2), (ox, oy - r + 2), 110 - bate * 45)
        if inch > 0.25:
            mx, my = ox + r - 2, oy + 2
            pygame.draw.circle(c, INFEC, (int(mx), int(my)), int(2 + inch * 2))
            c.set_at((int(mx), int(my)), OLHO_MIOLO)
            self.brilhos.append((int(mx), int(my), int(3 + inch * 2)))
        for dx in (1, 4):
            _olho_mascara(self, c, ox + dx, oy - 3, self.aceso)


class Chifrudo(_Monstro):
    W, H, OX, OY = 40, 38, 20, 36

    def __init__(self):
        super().__init__()
        self.passos = Passada(6.0)
        self.cab = Mola(0, 0.18, 0.65)

    def anima2(self, e, g):
        self.passos.andar(e.vx, e.no_chao)
        alvo = 1.0 if e.estado in ("mira", "corre") else 0.0
        self.cab.passo(alvo)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        ab = self.cab.v
        corre = e.estado == "corre"
        for i in range(2):                                      # pernas com joelho
            dx, alt = self.passos.pe(i, 2, 4.5 if corre else 3, 3.5 if corre else 2)
            perna(c, (ox - 1 + i * 2, oy - 11), (ox - 1 + i * 3 + dx, oy - 1 - alt), 6, 6, 2, CASCA2, dobra=1, pata=3)
        inc = ab * 0.35 + (0.1 if corre else 0)
        cx, cy = ox - 1 + ab * 1.5, oy - 17 + ab * 1.5 + math.sin(self.passos.fase * 2) * 0.6
        corpo = pygame.Surface((17, 15), pygame.SRCALPHA)
        bola(corpo, 8, 7, 8, 7, CASCA)
        pygame.draw.line(corpo, CASCA2, (1, 8), (15, 8))
        bola(corpo, 5, 4, 3, 2, CASCA_LUZ, luz=False)
        girar(c, corpo, (8, 7), (cx, cy), -math.degrees(inc))
        bal = math.sin(self.passos.fase) * 0.5                  # bracinho
        haste(c, (cx + 4, cy + 1), (cx + 7 + bal * 2, cy + 4 + bal), 1, CASCA2)
        hx, hy = cx + 5 + ab * 3, cy - 7 + ab * 5
        if e.estado == "atordoado":
            hx += math.sin(self.t * 0.3) * 1.2
        _mascara(self, c, hx, hy, 8, 7, (-2, 1), self.aceso, chifres=3)
        pygame.draw.polygon(c, OSSO, [(int(hx + 3), int(hy - 2)), (int(hx + 9 + ab), int(hy - 3 + ab * 2)), (int(hx + 3), int(hy + 1))])
        if e.estado == "atordoado":                             # estrelinhas girando
            for k in range(3):
                a = self.t * 0.15 + k * math.tau / 3
                c.set_at((int(hx + math.cos(a) * 5), int(hy - 7 + math.sin(a) * 1.5)), (255, 236, 120))


class Louva(_Monstro):
    W, H, OX, OY = 40, 40, 20, 38

    def __init__(self):
        super().__init__()
        self.braco = Mola(0, 0.25, 0.6)
        self.agach = Mola(0, 0.2, 0.65)
        self.antenas = None

    def anima2(self, e, g):
        alvo = {"guarda": -0.2 + math.sin(self.t * 0.08) * 0.15, "mira": -1.2, "salto": -0.6, "corte": 1.6,
                "recua": -0.4}.get(e.estado, 0)
        self.braco.passo(alvo)
        self.agach.passo(1.0 if e.estado == "mira" else 0.0)
        hx, hy = self.para_mundo(self.OX + 1, self.OY - 30)
        if self.antenas is None:
            self.antenas = [Corrente(4, 2.2, hx, hy, grav=0.0, arrasto=0.75, rigidez=0.5,
                                     direcao=(self.virado * 0.3 * s, -1)) for s in (-1, 1)]
        for k, s in enumerate((-1, 1)):
            self.antenas[k].passo(hx + s * 2 * self.virado, hy, (self.virado * (0.2 + 0.4 * s), -0.9))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        ag = self.agach.v * 4
        no_ar = not e.no_chao
        quad = (ox - 1, oy - 14 + ag)
        for i, (dx0, dx1) in enumerate(((-2, -6), (1, 5))):     # 2 pares de pernas finas
            pe_ = (ox + dx1, oy - 1) if not no_ar else (ox + dx1 * 0.6, oy - 4)
            perna(c, (quad[0] + dx0, quad[1]), pe_, 7, 7, 1, CASCA2, dobra=-1 if i == 0 else 1)
        if no_ar:                                               # asas abertas no salto
            asa = _asa(12, 5, (150, 170, 210, 140))
            girar(c, asa, (1, 2), (ox - 1, oy - 20), 150 + math.sin(self.t * 1.5) * 30)
        abd = pygame.Surface((7, 13), pygame.SRCALPHA)
        bola(abd, 3, 6, 3, 6, CASCA)
        girar(c, abd, (3, 1), (ox - 1, oy - 15 + ag), 25 + math.sin(self.t * 0.07) * 4)
        bola(c, ox + 1, oy - 20 + ag, 3, 6, CASCA)              # tórax esguio
        pygame.draw.line(c, CASCA_LUZ, (ox, int(oy - 24 + ag)), (ox, int(oy - 17 + ag)))
        for k, a_ in enumerate(self.antenas or ()):
            corda(c, self.pontos(a_), OSSO)
        hx, hy = ox + 2, oy - 29 + ag
        pygame.draw.polygon(c, OSSO, [(int(hx - 4), int(hy - 3)), (int(hx + 5), int(hy - 3)), (int(hx + 1), int(hy + 4))])
        for dx in (-2, 2):
            _olho_mascara(self, c, hx + dx, hy - 2, self.aceso)
        a = self.braco.v                                        # foice: braço + lâmina articulada
        omb = (ox + 3, oy - 23 + ag)
        cot = (omb[0] + math.cos(a) * 6, omb[1] + math.sin(a) * 6)
        lam_a = a + 2.4 if e.estado != "corte" else a + 1.2
        ponta = (cot[0] + math.cos(lam_a) * 7, cot[1] + math.sin(lam_a) * 7)
        haste(c, omb, cot, 2, CASCA2)
        haste(c, cot, ponta, 2, OSSO)
        c.set_at((int(ponta[0]), int(ponta[1])), (255, 255, 255))
        if e.estado == "corte":
            pygame.draw.arc(c, (240, 240, 250), (int(omb[0] - 4), int(omb[1] - 10), 18, 20), -1.3, 1.3, 1)


class Colosso(_Monstro):
    W, H, OX, OY = 70, 66, 35, 63

    def __init__(self):
        super().__init__()
        self.passos = Passada(9.0)
        self.maca = Mola(math.radians(20), 0.12, 0.7)
        self.respira = 0.0

    def anima2(self, e, g):
        self.passos.andar(e.vx, e.no_chao)
        if e.estado == "ergue":
            er = min(1.0, 1 - e.timer / max(1, getattr(e, "timer0", 36)))
            alvo = math.radians(-20 - 150 * er)
            self.maca.k = 0.12
        elif e.estado == "golpe":
            alvo = math.radians(65)
            self.maca.k = 0.5
        else:
            alvo = math.radians(20 + math.sin(self.passos.fase) * 10)
            self.maca.k = 0.12
        self.maca.passo(alvo)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        bob = abs(math.sin(self.passos.fase)) * 1.5 * self.passos.amp.v
        if e.estado == "golpe" and e.timer > 40:
            bob = -2 * (e.timer - 40) / 10
        for i in range(2):                                      # pernas grossas que pisam
            dx, alt = self.passos.pe(i, 2, 4, 3)
            perna(c, (ox - 5 + i * 10, oy - 17 + bob), (ox - 6 + i * 11 + dx, oy - 2 - alt), 8, 8, 5, CASCA2, dobra=1)
            c.fill(CASCA2, (int(ox - 10 + i * 11 + dx), int(oy - 3 - alt), 9, 3))
        cx, cy = ox - 1, oy - 30 + bob
        a2 = math.radians(160 + math.sin(self.passos.fase) * 15)   # braço de trás
        haste(c, (cx - 10, cy - 4), (cx - 10 + math.cos(a2) * 9, cy - 4 + math.sin(a2) * -9 + 12), 4, CASCA2)
        bola(c, cx, cy, 16, 15, CASCA)
        for k in range(3):                                      # placas da armadura que respiram
            y = cy - 6 + k * 6 + math.sin(self.t * 0.05 + k) * 0.4
            pygame.draw.arc(c, CASCA2, (int(cx - 14), int(y - 4), 28, 10), 3.5, 5.9, 1)
        bola(c, cx - 5, cy - 7, 6, 3.5, CASCA_LUZ, luz=False)
        for k, (dx, dy) in enumerate(((-6, 4), (7, 9), (0, 12))):   # infecção escorrendo
            pygame.draw.circle(c, INFEC, (int(cx + dx), int(cy + dy)), 2)
            gota = (self.t * 0.3 + k * 7) % 8
            c.set_at((int(cx + dx), int(cy + dy + 2 + gota)), INFEC)
            self.brilhos.append((int(cx + dx), int(cy + dy), 2))
        a = self.maca.v                                         # braço com maça
        omb = (cx + 9, cy - 6)
        mx, my = omb[0] + math.cos(a) * 15, omb[1] + math.sin(a) * 15
        haste(c, omb, (mx, my), 4, CASCA2)
        for k in range(6):
            b = k * math.pi / 3 + a
            haste(c, (mx, my), (mx + math.cos(b) * 7.5, my + math.sin(b) * 7.5), 1, OSSO2)
        bola(c, mx, my, 6, 6, OSSO)
        hx, hy = cx + 3, cy - 17 + (1 if e.estado == "ergue" else 0)   # elmo
        _mascara(self, c, hx, hy, 15, 13, (-4, 2), self.aceso, chifres=6, ang_chifre=math.sin(self.t * 0.05) * 4)
        pygame.draw.line(c, OSSO2, (int(hx), int(hy - 6)), (int(hx), int(hy + 6)))
        self.brilhos[-2:] = [(x, y, 5) for x, y, _ in self.brilhos[-2:]]


class Globulo(_Monstro):
    W, H, OX, OY = 26, 26, 13, 13
    voa = True

    def __init__(self):
        super().__init__()
        self.vant = (0, 0)
        self.sx, self.sy = Mola(1, 0.3, 0.6), Mola(1, 0.3, 0.6)

    def anima2(self, e, g):
        if self.vant[0] * e.vx < 0:
            self.sx.chute(-0.5)
        if self.vant[1] * e.vy < 0:
            self.sy.chute(-0.5)
        self.sx.passo(1)
        self.sy.passo(1)
        self.vant = (e.vx, e.vy)

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        rx = 6.5 * self.sx.v / max(0.6, self.sy.v) ** 0.3
        ry = 6.5 * self.sy.v / max(0.6, self.sx.v) ** 0.3
        for k in range(5):                                      # partículas de infecção em órbita
            a = self.t * 0.07 + k * math.tau / 5
            rr = 9 + math.sin(self.t * 0.1 + k) * 1.5
            c.set_at((int(ox + math.cos(a) * rr), int(oy + math.sin(a) * rr * 0.8)), INFEC)
        bola(c, ox, oy, rx, ry, (120, 40, 50))
        for k in range(3):                                      # membrana ondulando
            a = self.t * 0.12 + k * 2.1
            c.set_at((int(ox + math.cos(a) * (rx - 1)), int(oy + math.sin(a) * (ry - 1))), (170, 60, 64))
        ex = ox + 1 + self.olhos.ox.v * 1.5
        ey = oy - 1 + self.olhos.oy.v * 1.5
        c.fill(KM, (int(ex - 1), int(ey - 1), 4, 4))
        c.fill(OLHO_M, (int(ex), int(ey), 2, 2))
        c.set_at((int(ex), int(ey)), OLHO_MIOLO)
        self.brilhos.append((int(ex + 1), int(ey + 1), 3))


class Tatu(_Monstro):
    W, H, OX, OY = 32, 26, 16, 24

    def __init__(self):
        super().__init__()
        self.curl = Mola(0, 0.2, 0.65)
        self.giro = 0.0
        self.passos = Passada(3.0)
        self.antenas = None

    def anima2(self, e, g):
        bola_ = e.estado in ("rola", "enrola")
        self.curl.passo(1.0 if bola_ else 0.0)
        self.passos.andar(e.vx, e.no_chao)
        if e.estado == "rola":
            self.giro += e.vx * self.virado / 7.5
        else:                                                   # desenrola voltando à posição de casco
            self.giro = (self.giro + math.pi) % math.tau - math.pi
            self.giro *= 0.8
        hx, hy = self.para_mundo(self.OX + 9, self.OY - 6)
        if self.antenas is None:
            self.antenas = Corrente(4, 2.0, hx, hy, grav=0.05, arrasto=0.7, rigidez=0.45, direcao=(self.virado, -0.5))
        self.antenas.passo(hx, hy, (self.virado * 0.8, -0.6))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        cu = max(0.0, min(1.0, self.curl.v))
        if cu < 0.6:
            for i in range(7):                                  # 7 pares de patinhas
                dx, alt = self.passos.pe(i, 7, 1.2, 1.5)
                x = ox - 7 + i * 2.2
                haste(c, (x, oy - 3), (x + dx, oy - 1 - alt), 1, CASCA2)
            if self.antenas:
                corda(c, self.pontos(self.antenas), OSSO2)
        R = 8.0                                                 # placas num arco que fecha em bola
        cy = oy - 8
        n = 6
        for i in range(n):
            u = (i - (n - 1) / 2) / (n - 1)                     # -0.5 .. 0.5
            span = math.pi * (0.75 + 1.2 * cu)
            a = -math.pi / 2 + u * span + self.giro
            raio = R + (1 - cu) * 3
            px = ox + math.cos(a) * raio * (1 - cu * 0.15)
            py = cy + 2 * (1 - cu) + math.sin(a) * raio * (0.55 + 0.45 * cu) + (1 - cu) * 3
            bola(c, px, py, 3.6, 3.2 + cu, CASCA if i % 2 else CASCA_LUZ)
        if cu < 0.6:
            hx, hy = ox + 9, oy - 6
            bola(c, hx, hy, 2.6, 2.4, OSSO)
            _olho_mascara(self, c, hx + 0.5, hy - 0.5, self.aceso, grande=False)
        else:
            bola(c, ox, cy, 5, 5, CASCA2)


class Musgo(_Monstro):
    W, H, OX, OY = 32, 34, 16, 31

    def __init__(self):
        super().__init__()
        self.ac = Mola(0, 0.18, 0.65)
        self.folhas = [Mola(0, 0.15, 0.8) for _ in range(9)]

    def anima2(self, e, g):
        alvo = 0.0 if e.estado == "disfarce" else (e.alerta if e.estado == "acorda" else 1.0)
        self.ac.passo(alvo)
        for i, m in enumerate(self.folhas):
            m.passo(math.sin(self.t * 0.04 + i * 0.7) * (0.25 + 0.6 * self.ac.v) - self.inclina.v * 0.5)
        if e.estado == "acorda":
            for m in self.folhas:
                m.chute(random.uniform(-0.15, 0.15))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        ac = max(0.0, min(1.2, self.ac.v))
        sq = self.sq.v
        verde, verde2 = (70, 120, 70), (44, 84, 54)
        sobe = ac * 7 * sq
        if ac > 0.15:
            cx, cy = ox + 1, oy - 7 - sobe
            for k in range(6):                                  # espinhos que crescem
                a = math.pi * (1.1 + 0.16 * k)
                l = 2 + ac * 4
                haste(c, (cx + math.cos(a) * 5, cy + math.sin(a) * 4), (cx + math.cos(a) * (5 + l), cy + math.sin(a) * (4 + l)), 1, OSSO)
            bola(c, cx, cy, 6.5, 5.0 * sq, CASCA)
            for dx in (-3, 1):
                _olho_mascara(self, c, cx + dx, cy - 1, ac)
            if ac > 0.5:
                for k in range(2):                              # pezinhos
                    haste(c, (cx - 2 + k * 4, cy + 4), (cx - 3 + k * 6, oy - 1), 1, CASCA2)
        for i, m in enumerate(self.folhas):                     # folhas da moita: abrem quando acorda
            x = ox - 8 + i * 2
            lado = -1 if i < 4 else (1 if i > 4 else 0)
            alt = 9 + (i % 3) * 2 - abs(i - 4) * 0.5
            topo = (x + m.v * 4 + lado * ac * 4, oy - 2 - alt * (1 - ac * 0.35))
            pygame.draw.polygon(c, verde if i % 2 else verde2,
                                [(int(x - 2), oy - 1), (int(topo[0]), int(topo[1])), (int(x + 2), oy - 1)])
        if ac <= 0.15 and (self.t // 90) % 4 == 0:              # um piscar escondido entre as folhas
            c.set_at((ox + 1, oy - 7), (255, 140, 40))
            c.set_at((ox + 3, oy - 7), (255, 140, 40))


class Feiticeiro(_Monstro):
    W, H, OX, OY = 38, 42, 19, 18
    voa = True

    def __init__(self):
        super().__init__()
        self.barra = None
        self.maos = Mola(0, 0.12, 0.75)

    def anima2(self, e, g):
        self.maos.passo(1.0 if e.estado == "conjura" else 0.0)
        pts = [self.para_mundo(self.OX - 7 + i * 3.5, self.OY + 8) for i in range(5)]
        if self.barra is None:
            self.barra = [Corrente(3, 2.2, x, y, grav=0.12, arrasto=0.85, direcao=(0, 1)) for x, y in pts]
        for i, (x, y) in enumerate(pts):
            self.barra[i].passo(x, y, (0, 1), onda=(0.6, self.t * 0.12 + i * 0.8, 0.7))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        bob = math.sin(self.t * 0.08) * 1.2
        manto, manto2 = (54, 34, 74), (90, 60, 120)
        barra = [self.pontos(b) for b in self.barra] if self.barra else []
        base = [(ox - 8, oy + 8), (ox + 8, oy + 8)]
        for b in barra:                                         # barra esfarrapada (tecido com física)
            corda(c, b, manto, 2)
        pygame.draw.polygon(c, manto, [(ox, int(oy - 12 + bob)), base[0], base[1]])
        pygame.draw.line(c, manto2, (ox, int(oy - 10 + bob)), (ox - 4, oy + 7))
        m = self.maos.v                                         # mãos que flutuam e se juntam para conjurar
        for k, lado in enumerate((-1, 1)):
            a = self.t * 0.06 + k * math.pi
            hx = ox + lado * (8 - m * 2) + m * 6 + math.cos(a) * (1 - m) * 1.5
            hy = oy - 1 + math.sin(a) * 2 * (1 - m) + bob - m * 3
            bola(c, hx, hy, 2, 2, OSSO2)
        if m > 0.2:
            r = 1 + m * 3 + math.sin(self.t * 0.5) * 0.6
            pygame.draw.circle(c, (255, 170, 80), (int(ox + 7), int(oy - 4 + bob)), int(r))
            c.set_at((int(ox + 7), int(oy - 4 + bob)), OLHO_MIOLO)
            self.brilhos.append((int(ox + 7), int(oy - 4 + bob), int(3 + m * 4)))
            for k in range(3):                                  # runas orbitando
                a = self.t * 0.2 + k * math.tau / 3
                c.set_at((int(ox + 7 + math.cos(a) * 6), int(oy - 4 + bob + math.sin(a) * 6)), (200, 150, 255))
        _mascara(self, c, ox, oy - 12 + bob, 9, 9, (-3, 1), self.aceso, chifres=3, ang_chifre=math.sin(self.t * 0.05) * 6)


class AguaViva(_Monstro):
    W, H, OX, OY = 34, 42, 17, 13
    voa = True
    com_contorno = False

    def __init__(self):
        super().__init__()
        self.tent = None

    def anima2(self, e, g):
        pts = [self.para_mundo(self.OX - 6 + i * 3, self.OY + 4) for i in range(5)]
        if self.tent is None:
            self.tent = [Corrente(6, 3.0, x, y, grav=0.15, arrasto=0.88, direcao=(0, 1)) for x, y in pts]
        for i, (x, y) in enumerate(pts):
            self.tent[i].passo(x, y, (0, 1), onda=(0.7, self.t * 0.1 + i, 0.8))

    def pinta(self, c, e):
        ox, oy = self.OX, self.OY
        pr = 0.0 if e.estado == "deriva" else 1 - e.timer / 40
        cor = mix((150, 120, 210), (255, 120, 60), pr)
        pul = math.sin(self.t * 0.1)                            # sino pulsando
        rx, ry = 8 + pul * 0.8 + pr * 3, 6 - pul * 0.8 + pr * 3
        if pr:
            ox += random.randint(-1, 1) * (pr > 0.5)
        for t in self.tent or ():
            corda(c, self.pontos(t), escuro(cor, 0.15) + (220,), 1)
        for k in range(2):                                      # braços orais
            x = ox - 1 + k * 2
            pts = [(x + math.sin(self.t * 0.08 + j * 0.7 + k) * 1.5, oy + 3 + j * 2.5) for j in range(4)]
            corda(c, pts, claro(cor, 0.3) + (200,), 2)
        bola(c, ox, oy, rx, ry, cor + (190,))
        pygame.draw.ellipse(c, (230, 220, 255, 200), (int(ox - rx * 0.5), int(oy - ry * 0.6), int(rx * 0.6), int(ry * 0.5)))
        pygame.draw.circle(c, (255, 200, 120), (ox, int(oy)), 2)
        self.brilhos.append((ox, int(oy), 4))
