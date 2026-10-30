"""Inimigos novos, no estilo dos clássicos de plataforma (desenhos em arte_inimigos.py).

Ganchos que o Jogo usa (game.Ent): `atingivel()` (falso = não colide com nada: fungo escondido, caixa),
`ao_acertar(g, como)` (True = já tratou, não morre: estreptococo que fica bravo; a ameba se divide e morre),
`comestivel` (língua/bastão engole e vira ovo) e `espinhento` (pisar machuca; só o ovo derrota)."""
import math
import random

from . import arte_inimigos as A
from . import bonecos as B
from .game import Ent, GRAV, MAXQUEDA, centro, pe


def _andar(e, g, vel, beira=True):
    e.vy = min(e.vy + GRAV, MAXQUEDA)
    e.vx = math.copysign(vel, e.vx or -1)
    bx, _ = e.fisica(g.nivel)
    if bx or (beira and e.no_chao and e.beira(g.nivel)):
        e.vx = -e.vx
    e.virado = 1 if e.vx > 0 else -1


class Estafilococo(Ent):
    """Cacho dourado que anda e vira na beira."""
    Boneco = B.Estafilococo
    w, h = 14, 13
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.45

    def update(self, g):
        self.t += 1
        _andar(self, g, 0.45)

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Estreptococo(Ent):
    """Corrente de cocos: a 1ª pisada deixa bravo (vermelho e rápido); a 2ª derrota."""
    Boneco = B.Estreptococo
    w, h = 32, 11

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.4
        self.bravo = False
        self.calma = 0

    def ao_acertar(self, g, como):
        if como == "pisao" and not self.bravo:
            self.bravo = True
            self.calma = 30
            g.texto(self.cx, self.y - 6, "!!", (255, 120, 120))
            g.audio.tocar("pisao")
            return True
        return False

    def atingivel(self):
        return self.calma == 0

    def update(self, g):
        self.t += 1
        self.calma = max(0, self.calma - 1)
        if self.bravo:                       # persegue o jogador
            self.vx = math.copysign(1.1, g.p.cx - self.cx)
        _andar(self, g, 1.1 if self.bravo else 0.4)

    def draw(self, s, cam):
        if self.calma and self.calma % 4 < 2:
            return
        self.boneco.draw(s, cam, self)


class Fago(Ent):
    """Bacteriófago: agacha e salta na direção do jogador."""
    Boneco = B.Fago
    w, h = 12, 18
    comestivel = True

    def update(self, g):
        self.t += 1
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if self.no_chao:
            self.vx *= 0.7
            if self.t % 80 == 0 and abs(g.p.cx - self.cx) < 200:
                self.vy = -5.2
                self.vx = math.copysign(1.3, g.p.cx - self.cx)
        bx, _ = self.fisica(g.nivel)
        if bx:
            self.vx = -self.vx
        self.virado = 1 if g.p.cx > self.cx else -1

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Ameba(Ent):
    """Gelatinosa e lenta; pisão ou ovo divide em duas amebinhas."""
    Boneco = None
    comestivel = True

    def __init__(self, x, y, pequena=False, vx=-0.3):
        self.pequena = pequena
        self.w, self.h = (10, 7) if pequena else (16, 11)
        super().__init__(x, y)
        self.boneco = B.Ameba(pequena)
        self.vx = vx

    def ao_acertar(self, g, como):
        if not self.pequena:
            for lado in (-1, 1):
                a = Ameba(self.cx, self.y + self.h, True, 0.5 * lado)
                a.vy = -3
                g.novos.append(a)
        return False

    def update(self, g):
        self.t += 1
        _andar(self, g, 0.5 if self.pequena else 0.3)

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Seringa(Ent):
    """Disparada pela caixa: voa reto; pisar ou acertar com ovo derruba."""
    w, h = 18, 5

    def __init__(self, x, y, lado):
        super().__init__(x, y)
        self.vx = 2.0 * lado
        self.virado = lado

    def update(self, g):
        self.t += 1
        self.x += self.vx
        tx, ty = int((self.x + (self.w if self.vx > 0 else 0)) // 16), int((self.y + 2) // 16)
        if self.t > 420 or g.nivel.solido(tx, ty):
            self.vivo = False

    def draw(self, s, cam):
        centro(s, A.seringa(self.virado), self, cam)


class Caixa(Ent):
    """Caixa de perfurocortantes: não machuca, mas dispara seringas para o lado do jogador."""
    Boneco = B.Caixa
    w, h = 14, 16

    def atingivel(self):
        return False

    def update(self, g):
        self.t += 1
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        self.fisica(g.nivel)
        d = g.p.cx - self.cx
        if self.t % 150 == 0 and 30 < abs(d) < 260:
            lado = 1 if d > 0 else -1
            g.novos.append(Seringa(self.cx + lado * 12, self.y + 9, lado))
            g.audio.tocar("arremesso")

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Comprimido(Ent):
    """Cápsula que rola rápido e quica nas paredes (cai dos buracos)."""
    Boneco = B.Comprimido
    w, h = 13, 9
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -1.5

    def update(self, g):
        self.t += 1
        _andar(self, g, 1.5, beira=False)

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Esporo(Ent):
    w, h = 6, 6
    espinhento = True

    def __init__(self, x, y, vx):
        super().__init__(x, y)
        self.vx, self.vy = vx, -3.2

    def update(self, g):
        self.t += 1
        self.vy = min(self.vy + 0.16, 4)
        self.x += self.vx
        self.y += self.vy
        if g.nivel.solido(int(self.cx // 16), int((self.y + self.h) // 16)) or self.t > 300:
            self.vivo = False

    def draw(self, s, cam):
        centro(s, A.esporo(self.t // 6), self, cam)


class Candida(Ent):
    """Fungo que sai do chão de tempos em tempos e solta um esporo; tem dentes: só o ovo derrota.
    Não sai se o jogador estiver em cima (como as plantas carnívoras)."""
    Boneco = B.Candida
    w, h = 12, 16
    espinhento = True
    CICLO = 200

    def __init__(self, x, y):
        super().__init__(x, y)
        self.base_y = self.y
        self.fora = 0.0                      # 0 = escondido, 1 = todo para fora

    def atingivel(self):
        return self.fora > 0.5

    def update(self, g):
        self.t += 1
        f = self.t % self.CICLO
        perto = abs(g.p.cx - self.cx) < 18
        if f < 90:
            alvo = 0.0 if (perto and self.fora == 0) else 1.0
        else:
            alvo = 0.0
        self.fora = max(0.0, min(1.0, self.fora + (0.06 if alvo > self.fora else -0.06)))
        self.y = self.base_y + (1 - self.fora) * (self.h + 2)
        if f == 50 and self.fora >= 1:
            g.novos.append(Esporo(self.cx, self.base_y + 2, math.copysign(1.0, g.p.cx - self.cx)))

    def draw(self, s, cam):
        if self.fora <= 0:
            return
        b = self.boneco                      # só a parte que já saiu do chão aparece
        sp, ox, oy, _ = b.quadro(self)
        vis = max(1, min(sp.get_height(), int(oy * self.fora) + 1))
        x = int(self.cx - ox - cam[0])
        y = int(self.base_y + self.h - vis - cam[1])
        s.blit(sp.subsurface((0, 0, sp.get_width(), vis)), (x, y))


class Carrapato(Ent):
    """Pendurado num fio no alto; desce quando o jogador passa embaixo e sobe devagar."""
    Boneco = B.Carrapato
    w, h = 12, 11
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.chao = self.y
        self.topo = self.y - 78
        self.y = self.topo
        self.estado = "espera"
        self.espera = 0

    def update(self, g):
        self.t += 1
        if self.estado == "espera" and abs(g.p.cx - self.cx) < 36 and g.p.y > self.y:
            self.estado = "desce"
        elif self.estado == "desce":
            self.y = min(self.chao - 6, self.y + 2.2)
            if self.y >= self.chao - 6:
                self.estado, self.espera = "embaixo", 50
        elif self.estado == "embaixo":
            self.espera -= 1
            if self.espera <= 0:
                self.estado = "sobe"
        elif self.estado == "sobe":
            self.y = max(self.topo, self.y - 0.6)
            if self.y <= self.topo:
                self.estado = "espera"

    def draw(self, s, cam):
        x = int(self.cx - cam[0])
        y1 = int(self.y - cam[1])
        if y1 > 0:
            s.fill((230, 230, 240), (x, 0, 1, y1))
        self.boneco.draw(s, cam, self)


class Morcego(Ent):
    """Dorme pendurado; quando o jogador chega perto, dá um rasante e segue voando."""
    Boneco = B.Morcego
    w, h = 16, 9
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.estado = "dorme"
        self.base = self.y

    def update(self, g):
        self.t += 1
        if self.estado == "dorme":
            if abs(g.p.cx - self.cx) < 80:
                self.estado = "rasante"
                self.vx = math.copysign(1.7, g.p.cx - self.cx)
                self.vy = 2.6
                g.audio.tocar("flutter")
        else:
            self.vy -= 0.07
            if self.vy < -1.2:
                self.vy = -1.2
            if self.y < self.base - 40:
                self.vy = 0.6
            self.x += self.vx
            self.y += self.vy + math.sin(self.t * 0.2) * 0.4
            self.virado = 1 if self.vx > 0 else -1

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Lombriga(Ent):
    """Escondida num montinho: treme, salta para fora e persegue o jogador."""
    Boneco = B.Lombriga
    w, h = 14, 9
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.monte = (self.cx, self.y + self.h)
        self.estado = "escondida"
        self.treme = 0

    def atingivel(self):
        return self.estado == "fora"

    def update(self, g):
        self.t += 1
        if self.estado == "escondida":
            if abs(g.p.cx - self.cx) < 90:
                self.estado, self.treme = "treme", 40
            return
        if self.estado == "treme":
            self.treme -= 1
            if self.treme <= 0:
                self.estado = "fora"
                self.vy = -5
                self.vx = math.copysign(1.0, g.p.cx - self.cx)
            return
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if self.no_chao:
            self.vx += 0.05 * (1 if g.p.cx > self.cx else -1)
            self.vx = max(-1.0, min(1.0, self.vx))
        bx, _ = self.fisica(g.nivel)
        if bx:
            self.vx = -self.vx
        self.virado = 1 if self.vx > 0 else -1

    def draw(self, s, cam):
        mx, my = self.monte
        m = A.montinho(self.estado == "fora", self.treme)
        s.blit(m, (int(mx - 9 - cam[0]), int(my - 6 - cam[1])))
        if self.estado == "fora":
            self.boneco.draw(s, cam, self)


# nome no gerador de fases → (classe, altura acima do chão onde nasce); os monstros (monstros.py) entram no fim
TIPOS = {
    "estafilococo": (Estafilococo, 0), "estreptococo": (Estreptococo, 0), "fago": (Fago, 0),
    "ameba": (Ameba, 0), "caixa": (Caixa, 0), "comprimido": (Comprimido, 0), "candida": (Candida, 0),
    "carrapato": (Carrapato, 0), "morcego": (Morcego, 70), "lombriga": (Lombriga, 0),
}

from .monstros import TIPOS as _MONSTROS  # noqa: E402  (bestiário inspirado no Hollow Knight)

TIPOS.update(_MONSTROS)
