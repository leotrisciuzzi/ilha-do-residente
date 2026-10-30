"""Monstros inspirados no bestiário do Hollow Knight (arte em arte_monstros.py), com o mesmo princípio de lá:
cada um tem um comportamento legível — percebe o jogador, ANUNCIA o ataque (olhos acendem, corpo treme, som) e só
então ataca, ficando vulnerável depois. Todos têm vida (vários golpes), piscam em branco e recuam ao apanhar.

    mosca       Mosca necrófaga ....... voa parada; ao ver o jogador grita e persegue (Vengefly)
    cuspidor    Cuspidor .............. mantém distância no ar e cospe ácido, 1 ou 3 bolas (Aspid)
    chifrudo    Necrosado chifrudo .... abaixa o chifre e dispara até bater na parede; fica tonto (Husk Hornhead)
    louva       Louva-a-deus febril ... agacha, salta sobre o jogador e corta ao cair; recua (Mantis Youth)
    colosso     Colosso necrosado ..... grande e lento; ergue a maça e cria ondas de choque no chão (False Knight)
    globulo     Glóbulo quicante ...... ricocheteia pelo ar sem parar (Gruzzer)
    tatu        Tatuzinho blindado .... vira bola blindada e rola contra o jogador (Baldur)
    musgo       Musgo espreitador ..... finge ser moita; acorda com espinhos e pula (Mosskin)
    feiticeiro  Feiticeiro da febre ... some e reaparece perto; conjura orbes que perseguem (Soul Twister)
    aguaviva    Água-viva tóxica ...... flutua até você; ao morrer incha e explode (Ooma)

ADAPTÁVEIS: tudo lê g.ameaca (0,6 a 1,6), que sobe quando o jogador derrota bichos sem apanhar e cai quando ele se
machuca; vale para velocidade, tempo de aviso e intervalo entre ataques, e fica guardada no save entre as fases.
Às vezes um monstro nasce GRANDE (mais vida, 1,5× o tamanho, mais moedas) — mais vezes quanto maior a ameaça."""
import math
import random

import pygame

from . import arte_monstros as A
from . import bonecos as B
from .climas import halo
from .game import Ent, GRAV, MAXQUEDA, TILE, Item

ADD = pygame.BLEND_RGB_ADD


def _ameaca(g):
    return getattr(g, "ameaca", 1.0)


class Monstro(Ent):
    vida = 2
    moedas = 1
    voa = False
    pode_grande = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.grande = None
        self.branco = 0
        self.invul = 0
        self.atordoa = 0
        self.alerta = 0.0
        self.estado = "inicio"
        self.timer = 0
        self.cd = random.randint(20, 60)
        self.escala = 1
        self.vida_max = self.vida

    # -- ciclo comum
    def _nascer(self, g):
        am = _ameaca(g)
        self.grande = self.pode_grande and random.random() < 0.10 * am
        if self.grande:
            cx, base = self.cx, self.y + self.h
            self.w, self.h = int(self.w * 1.5), int(self.h * 1.5)
            self.x, self.y = cx - self.w / 2, base - self.h
            self.vida += 2 + (2 if am > 1.2 else 0)
            self.moedas *= 3
            self.escala = 1.5
        self.vida_max = self.vida
        self.estado = self.estado_inicial

    estado_inicial = "anda"

    def update(self, g):
        if self.grande is None:
            self._nascer(g)
        self.t += 1
        self.branco = max(0, self.branco - 1)
        self.invul = max(0, self.invul - 1)
        if self.atordoa:                                     # recuo do golpe
            self.atordoa -= 1
            self.vx *= 0.85
            if not self.voa:
                self.vy = min(self.vy + GRAV, MAXQUEDA)
            else:
                self.vy *= 0.85
            self.fisica(g.nivel)
            return
        self.agir(g)
        if self.t % 23 == 0 and random.random() < 0.5:     # esporos laranja da infecção
            g.efeito(self.cx + random.uniform(-self.w / 2, self.w / 2), self.y + random.uniform(0, self.h),
                     "ponto", A.INFEC, random.uniform(-0.1, 0.1), -0.25, 28)

    def agir(self, g):
        pass

    def ao_acertar(self, g, como):
        if self.invul:
            return True
        self.vida -= 2 if como == "pisao" else 1
        self.branco, self.invul = 8, 10
        if self.vida <= 0:
            return False
        lado = 1 if self.cx > g.p.cx else -1
        self.vx = lado * (1.0 if self.grande or self.vida_max >= 8 else 2.2)
        if self.voa:
            self.vy = -1.2
        self.atordoa = 4 if self.vida_max >= 8 else 10
        self.apanhou(g)
        g.audio.tocar("acerto_inimigo")
        return True

    def apanhou(self, g):
        pass

    def ao_morrer(self, g):
        for k in range(self.moedas):
            m = Item(self.cx + random.uniform(-4, 4), self.y + self.h, "moeda")
            m.solta, m.vy, m.vx = True, -random.uniform(2.5, 4.5), random.uniform(-1.2, 1.2)
            g.itens.append(m)
        if self.vida_max >= 6:
            g.shake = max(g.shake, 14)
            g.parada = max(g.parada, 8)
            for _ in range(3):
                g.particulas_burst(self.cx, self.y + self.h / 2, A.INFEC, 14, 3.5)

    # -- utilidades
    def dist(self, g):
        p = g.p
        return math.hypot(p.cx - self.cx, (p.y + p.h / 2) - (self.y + self.h / 2))

    def lado_jogador(self, g):
        return 1 if g.p.cx > self.cx else -1

    def arte(self):
        """(chave do cache, superfície, olhos) virada à direita."""
        raise NotImplementedError

    def draw(self, s, cam):
        tremor = random.randint(-1, 1) if self.estado in ("mira", "ergue", "grito", "incha", "acorda", "prestes") else 0
        if self.boneco is not None:                         # boneco articulado (bonecos.py)
            x, y, ol = self.boneco.draw(s, cam, self, self.branco > 4, tremor)
        else:
            chave, spr, olhos = self.arte()
            t, ol = A.versao(chave, spr, olhos, self.virado, self.escala, self.branco > 4)
            x = int(self.x + self.w / 2 - t.get_width() / 2 - cam[0]) + tremor
            y = int(self.y + self.h - t.get_height() - cam[1])
            if self.voa:
                y = int(self.y + self.h / 2 - t.get_height() / 2 - cam[1])
            s.blit(t, (x, y))
            ol = [(x + ox, y + oy, r) for ox, oy, r in ol]
        k = 0.45 + 0.55 * self.alerta
        for ox, oy, r in ol:
            r = int(r + 1)
            s.blit(halo(r, (int(120 * k), int(60 * k), int(14 * k))), (int(ox) - r, int(oy) - r),
                   special_flags=ADD)
        if self.vida_max >= 6 and self.vida < self.vida_max:      # barra de vida dos grandes
            w = int(self.w)
            bx, by = int(self.x - cam[0]), int(self.y - cam[1]) - 6
            s.fill((20, 14, 30), (bx, by, w, 3))
            s.fill(A.INFEC, (bx, by, int(w * self.vida / self.vida_max), 3))

    # física de quem anda
    def _cair_e_andar(self, g, vel, beira=True):
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if vel is not None:
            self.vx = vel
        bx, _ = self.fisica(g.nivel)
        if bx or (beira and self.no_chao and self.beira(g.nivel) and abs(self.vx) > 0):
            self.vx = -self.vx
            return True
        return False


# =====================================================================================================================

class Mosca(Monstro):
    Boneco = B.Mosca
    w, h = 14, 13
    voa = True
    vida = 2
    estado_inicial = "vaga"

    def __init__(self, x, y):
        super().__init__(x, y)
        self.casa = (self.x, self.y)

    def agir(self, g):
        am = _ameaca(g)
        d = self.dist(g)
        if self.estado == "vaga":
            self.alerta = max(0, self.alerta - 0.05)
            hx, hy = self.casa
            self.vx = math.cos(self.t * 0.03) * 0.5
            self.vy = (hy + math.sin(self.t * 0.05) * 10 - self.y) * 0.05
            if d < 110:
                self.estado, self.timer = "grito", int(20 / am)
                g.audio.tocar("grito")
        elif self.estado == "grito":
            self.alerta = 1.0
            self.vx = self.vy = 0
            self.timer -= 1
            if self.timer <= 0:
                self.estado = "caca"
        else:
            p = g.p
            ax = math.copysign(0.09 * am, p.cx - self.cx)
            ay = math.copysign(0.07 * am, (p.y + 6) - self.y)
            self.vx = max(-1.6 * am, min(1.6 * am, self.vx + ax))
            self.vy = max(-1.3 * am, min(1.3 * am, self.vy + ay)) + math.sin(self.t * 0.3) * 0.15
            if d > 240:
                self.estado, self.casa = "vaga", (self.x, self.y)
        self.virado = 1 if (self.vx if abs(self.vx) > 0.1 else self.lado_jogador(g)) > 0 else -1
        bx, teto = self.fisica(g.nivel)
        if bx:
            self.vx = -self.vx * 0.5

    def arte(self):
        s, o = A.mosca(self.t // 3, self.estado != "vaga")
        return ("mosca", self.t // 3 % 2, self.estado != "vaga"), s, o


class Cuspe(Ent):
    """Bola de ácido do cuspidor: cai um pouco e some ao bater."""
    w, h = 6, 6

    def __init__(self, x, y, vx, vy):
        super().__init__(x, y)
        self.x, self.y, self.vx, self.vy = x - 3, y - 3, vx, vy
        self.vida_t = 160

    def update(self, g):
        self.t += 1
        self.vida_t -= 1
        self.vy += 0.04
        bx, teto = self.fisica(g.nivel, plataformas=False)
        if bx or teto or self.no_chao or self.vida_t <= 0:
            self.vivo = False
            g.particulas_burst(self.cx, self.y + 3, A.INFEC, 5, 1.2)

    def draw(self, s, cam):
        spr, _ = A.cuspe(self.t // 4)
        x, y = int(self.x - 1 - cam[0]), int(self.y - 1 - cam[1])
        s.blit(halo(5, (90, 40, 8)), (x - 1, y - 1), special_flags=ADD)
        s.blit(spr, (x, y))


class Cuspidor(Monstro):
    Boneco = B.Cuspidor
    w, h = 16, 16
    voa = True
    vida = 3
    moedas = 2
    estado_inicial = "paira"

    def agir(self, g):
        am = _ameaca(g)
        p = g.p
        lado = -1 if p.cx > self.cx else 1
        alvo_x, alvo_y = p.cx + lado * 72, p.y - 46
        d = self.dist(g)
        self.virado = self.lado_jogador(g)
        if self.estado == "paira":
            self.alerta = max(0.3, self.alerta - 0.03)
            self.vx = max(-1.0, min(1.0, self.vx + math.copysign(0.05, alvo_x - self.cx)))
            self.vy = max(-0.9, min(0.9, self.vy + math.copysign(0.05, alvo_y - self.y))) + math.sin(self.t * 0.12) * 0.1
            self.cd -= am
            if self.cd <= 0 and d < 170:
                self.estado, self.timer = "incha", int(26 / am)
                self.vx = self.vy = 0
        elif self.estado == "incha":
            self.alerta = 1.0
            self.vx *= 0.8
            self.vy *= 0.8
            self.timer -= 1
            if self.timer <= 0:
                n = 3 if (self.grande or am > 1.25) else 1
                ox, oy = self.cx + self.virado * 8, self.y + self.h / 2 + 2
                ang = math.atan2((p.y + p.h / 2) - oy, p.cx - ox)
                for k in range(n):
                    a = ang + (k - (n - 1) / 2) * 0.32
                    v = 2.1 + 0.3 * am
                    g.novos.append(Cuspe(ox, oy, math.cos(a) * v, math.sin(a) * v))
                g.audio.tocar("cuspe")
                self.estado, self.cd = "paira", 110 + random.randint(0, 40)
                self.vx = -self.virado * 1.2                    # coice
        self.fisica(g.nivel)

    def arte(self):
        inch = 0.0
        if self.estado == "incha":
            inch = min(1.0, 1 - self.timer / 26)
        s, o = A.cuspidor(self.t // 5, inch)
        return ("cusp", self.t // 5 % 6, round(inch, 1)), s, o


class Chifrudo(Monstro):
    Boneco = B.Chifrudo
    w, h = 16, 24
    vida = 3
    moedas = 2

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.4

    def agir(self, g):
        am = _ameaca(g)
        p = g.p
        if self.estado == "anda":
            self.alerta = max(0, self.alerta - 0.05)
            vira = self._cair_e_andar(g, math.copysign(0.4, self.vx or -1))
            self.virado = 1 if self.vx > 0 else -1
            mesma_altura = abs((p.y + p.h) - (self.y + self.h)) < 30
            if self.cd > 0:
                self.cd -= 1
            elif mesma_altura and abs(p.cx - self.cx) < 130 and self.no_chao:
                self.virado = self.lado_jogador(g)
                self.estado, self.timer = "mira", int(30 / am)
                g.audio.tocar("grito")
        elif self.estado == "mira":
            self.alerta = 1.0
            self.vx = 0
            self.virado = self.lado_jogador(g)
            self.vy = min(self.vy + GRAV, MAXQUEDA)
            self.fisica(g.nivel)
            if self.t % 4 == 0:
                g.part.append([self.cx - self.virado * 6, self.y + self.h, -self.virado * 0.8, -0.6, 12, (180, 160, 140)])
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "corre", 80
        elif self.estado == "corre":
            bateu = self._cair_e_andar(g, self.virado * 3.0 * am, beira=True)
            self.timer -= 1
            if self.t % 3 == 0:
                g.part.append([self.cx - self.virado * 8, self.y + self.h - 2, -self.virado, -0.3, 10, (200, 180, 160)])
            if bateu or self.timer <= 0:
                if bateu:
                    g.shake = max(g.shake, 6)
                    g.audio.tocar("pisao")
                self.estado, self.timer = "atordoado", 46
                self.vx = 0
        elif self.estado == "atordoado":
            self.alerta = 0.2
            self.vx = 0
            self._cair_e_andar(g, 0)
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.cd = "anda", int(60 / am)
                self.vx = 0.4 * self.virado

    def arte(self):
        pose = {"mira": "mira", "corre": "corre", "atordoado": "atordoado"}.get(self.estado, "anda")
        q = self.t // (3 if pose == "corre" else 7)
        s, o = A.chifrudo(q, pose)
        return ("chifrudo", q % 4, pose), s, o


class Louva(Monstro):
    Boneco = B.Louva
    w, h = 14, 24
    vida = 3
    moedas = 2
    estado_inicial = "guarda"

    def agir(self, g):
        am = _ameaca(g)
        p = g.p
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if self.estado == "guarda":
            self.alerta = max(0.2, self.alerta - 0.04)
            self.virado = self.lado_jogador(g)
            self.vx *= 0.8
            self.fisica(g.nivel)
            self.cd = max(0, self.cd - am)
            if self.cd <= 0 and self.dist(g) < 100 and self.no_chao:
                self.estado, self.timer = "mira", int(18 / am)
                g.audio.tocar("grito")
        elif self.estado == "mira":
            self.alerta = 1.0
            self.vx = 0
            self.fisica(g.nivel)
            self.timer -= 1
            if self.timer <= 0:
                self.estado = "salto"
                self.vy = -5.2
                self.vx = max(-3.0, min(3.0, (p.cx - self.cx) / 26)) * am
                g.audio.tocar("pulo")
        elif self.estado == "salto":
            self.fisica(g.nivel)
            if self.no_chao:
                self.estado, self.timer = "corte", 14
                self.vx = 0
                g.audio.tocar("arremesso")
                for k in range(6):
                    a = -1.2 + k * 0.48
                    g.efeito(self.cx + self.virado * 10 + math.cos(a) * 9 * self.virado, self.y + 6 + math.sin(a) * 9,
                             "ponto", (255, 255, 255), 0, 0, 10)
        elif self.estado == "corte":
            self.fisica(g.nivel)
            self.timer -= 1
            if self.timer <= 0:
                self.estado = "recua"
                self.vy, self.vx = -3.2, -self.virado * 1.6
        else:                                                   # recua
            self.fisica(g.nivel)
            if self.no_chao:
                self.estado, self.cd = "guarda", 70

    def arte(self):
        pose = {"mira": "mira", "salto": "salto", "corte": "corte", "recua": "salto"}.get(self.estado, "guarda")
        s, o = A.louva(self.t // 12, pose)
        return ("louva", self.t // 12 % 2, pose), s, o


class Onda(Ent):
    """Onda de choque da maça: corre pelo chão; só pulando por cima. Golpes não a destroem."""
    w, h = 10, 10
    espinhento = True

    def __init__(self, x, y, lado):
        super().__init__(x, y)
        self.vx = lado * 2.7
        self.vida_t = 50

    def ao_acertar(self, g, como):
        return True

    def update(self, g):
        self.t += 1
        self.vida_t -= 1
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        bx, _ = self.fisica(g.nivel)
        if bx or self.vida_t <= 0 or (self.no_chao and self.beira(g.nivel)):
            self.vivo = False
        if self.t % 2 == 0:
            g.part.append([self.cx, self.y + self.h, -self.vx * 0.2, -1.2, 10, (255, 200, 140)])

    def draw(self, s, cam):
        x, y = int(self.x - cam[0]), int(self.y + self.h - cam[1])
        k = self.vida_t / 50
        for i in range(4):
            alt = int((10 - i * 2) * (0.6 + 0.4 * k))
            xx = x + (i * 3 if self.vx < 0 else self.w - i * 3)
            pygame.draw.line(s, (255, 236, 200), (xx, y), (xx, y - alt), 2)
        s.blit(halo(8, (90, 50, 20)), (x - 3, y - 14), special_flags=ADD)


class Colosso(Monstro):
    Boneco = B.Colosso
    w, h = 32, 44
    vida = 10
    moedas = 8
    pode_grande = True

    def agir(self, g):
        am = _ameaca(g)
        raiva = 1.4 if self.vida * 2 <= self.vida_max else 1.0
        d = abs(g.p.cx - self.cx)
        if self.estado == "anda":
            self.alerta = 0.5 if d < 170 else 0.2
            vel = 0.0
            if d < 170:
                self.virado = self.lado_jogador(g)
                vel = self.virado * 0.38 * am * raiva
            self._cair_e_andar(g, vel)
            if self.t % 26 == 0 and abs(vel) > 0:
                g.shake = max(g.shake, 2)
            self.cd = max(0, self.cd - 1)
            if self.cd <= 0 and d < 60 + self.w / 2 and self.no_chao:
                self.estado, self.timer = "ergue", int(36 / (am * raiva))
                self.timer0 = self.timer
                g.audio.tocar("grito")
        elif self.estado == "ergue":
            self.alerta = 1.0
            self._cair_e_andar(g, 0)
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "golpe", 50
                g.shake, g.parada = 16, 4
                g.audio.tocar("pisao")
                chao = self.y + self.h
                mx = self.cx + self.virado * self.w * 0.7
                for lado in (-1, 1):
                    g.novos.append(Onda(mx + lado * 6, chao, lado))
                g.particulas_burst(mx, chao, (220, 200, 170), 16, 3)
                if raiva > 1:                                    # com raiva, duas ondas seguidas
                    self.segunda = 18
        elif self.estado == "golpe":
            self.alerta = 0.3
            self._cair_e_andar(g, 0)
            self.timer -= 1
            seg = getattr(self, "segunda", 0)
            if seg:
                self.segunda = seg - 1
                if self.segunda == 0:
                    chao = self.y + self.h
                    for lado in (-1, 1):
                        g.novos.append(Onda(self.cx + lado * self.w * 0.6, chao, lado))
                    g.shake = 10
                    g.audio.tocar("pisao")
            if self.timer <= 0:
                self.estado, self.cd = "anda", int(50 / am)

    def apanhou(self, g):
        self.vx *= 0.3

    def arte(self):
        pose = self.estado if self.estado in ("ergue", "golpe") else "anda"
        er = 0.0
        if pose == "ergue":
            er = round(min(1.0, 1 - self.timer / max(1, getattr(self, "timer0", 36))), 1)
        q = self.t // 10
        s, o = A.colosso(q, pose, er)
        return ("colosso", q % 4, pose, er), s, o


class Globulo(Monstro):
    Boneco = B.Globulo
    w, h = 13, 13
    voa = True
    vida = 2
    estado_inicial = "quica"

    def agir(self, g):
        am = _ameaca(g)
        if not (self.vx and self.vy):
            self.vx, self.vy = random.choice((-1, 1)) * 0.9, random.choice((-1, 1)) * 0.9
        v = 0.9 * am
        self.vx, self.vy = math.copysign(v, self.vx), math.copysign(v, self.vy)
        vy0 = self.vy
        bx, teto = self.fisica(g.nivel, plataformas=False)
        if bx:
            self.vx = -self.vx
        if teto or self.no_chao:
            self.vy = -vy0
        self.virado = 1 if self.vx > 0 else -1
        self.alerta = 0.7

    def arte(self):
        s, o = A.globulo(self.t // 3)
        return ("globulo", self.t // 3 % 8), s, o


class Tatu(Monstro):
    Boneco = B.Tatu
    w, h = 18, 15
    vida = 3
    moedas = 2

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.3

    def ao_acertar(self, g, como):
        if self.estado == "rola" and como != "pisao":        # blindado: só o pisão fura a bola
            g.audio.tocar("quica")
            self.branco = 3
            return True
        return super().ao_acertar(g, como)

    def agir(self, g):
        am = _ameaca(g)
        if self.estado == "anda":
            self.alerta = 0.3
            self._cair_e_andar(g, math.copysign(0.3, self.vx or -1))
            self.virado = 1 if self.vx > 0 else -1
            self.cd = max(0, self.cd - 1)
            if self.cd <= 0 and self.dist(g) < 80:
                self.estado, self.timer = "enrola", 14
        elif self.estado == "enrola":
            self.alerta = 1.0
            self._cair_e_andar(g, 0)
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "rola", 110
                self.virado = self.lado_jogador(g)
                self.vx = self.virado * 2.6 * am
        elif self.estado == "rola":
            if self._cair_e_andar(g, None, beira=False):
                g.audio.tocar("quica")
            self.virado = 1 if self.vx > 0 else -1
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "desenrola", 20
        else:
            self._cair_e_andar(g, 0)
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.cd = "anda", 70

    def arte(self):
        bola = self.estado in ("rola", "enrola")
        q = self.t // (2 if bola else 8)
        s, o = A.tatu(q, bola)
        return ("tatu", q % 6, bola), s, o


class Musgo(Monstro):
    Boneco = B.Musgo
    w, h = 18, 14
    vida = 2
    moedas = 2
    estado_inicial = "disfarce"

    def atingivel(self):
        return self.estado != "disfarce"

    def agir(self, g):
        am = _ameaca(g)
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if self.estado == "disfarce":
            self.alerta = 0
            self.fisica(g.nivel)
            if self.dist(g) < 50:
                self.estado, self.timer = "acorda", int(16 / am)
                g.audio.tocar("grito")
        elif self.estado == "acorda":
            self.alerta = 1 - self.timer / 16
            self.fisica(g.nivel)
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.cd = "caca", 0
        else:
            self.alerta = 1.0
            self.virado = self.lado_jogador(g)
            self.fisica(g.nivel)
            if self.no_chao:
                self.vx *= 0.7
                self.cd -= am
                if self.cd <= 0:
                    self.vy, self.vx = -3.6, self.virado * 1.7 * am
                    self.cd = 46

    def arte(self):
        ac = 0.0 if self.estado == "disfarce" else (self.alerta if self.estado == "acorda" else 1.0)
        s, o = A.musgo(self.t // 10, ac)
        return ("musgo", self.t // 10 % 2, round(ac, 1)), s, o


class Orbe(Ent):
    """Orbe do feiticeiro: persegue devagar, atravessa paredes, some com o tempo ou com um golpe."""
    w, h = 8, 8

    def __init__(self, x, y, ang, vel):
        super().__init__(x, y)
        self.x, self.y = x - 4, y - 4
        self.ang, self.vel = ang, vel
        self.vida_t = 210

    def update(self, g):
        self.t += 1
        self.vida_t -= 1
        alvo = math.atan2((g.p.y + g.p.h / 2) - self.y, g.p.cx - self.cx)
        dif = (alvo - self.ang + math.pi) % math.tau - math.pi
        self.ang += max(-0.035, min(0.035, dif))
        self.x += math.cos(self.ang) * self.vel
        self.y += math.sin(self.ang) * self.vel
        if self.vida_t <= 0:
            self.vivo = False
            g.particulas_burst(self.cx, self.y + 4, (255, 170, 80), 6, 1.2)
        if self.t % 3 == 0:
            g.efeito(self.cx, self.y + 4, "ponto", (255, 170, 80), 0, 0, 12)

    def draw(self, s, cam):
        spr, _ = A.orbe(self.t // 4)
        x, y = int(self.x - 2 - cam[0]), int(self.y - 2 - cam[1])
        s.blit(halo(9, (110, 60, 20)), (x - 3, y - 3), special_flags=ADD)
        s.blit(spr, (x, y))


class Feiticeiro(Monstro):
    Boneco = B.Feiticeiro
    w, h = 14, 24
    voa = True
    vida = 3
    moedas = 3
    estado_inicial = "visivel"

    def atingivel(self):
        return self.estado not in ("some", "fora")

    def apanhou(self, g):
        self.estado, self.timer = "some", 16                  # apanhou: desaparece e reaparece em outro lugar

    def _lugar_livre(self, g, x, y):
        nv = g.nivel
        for ty in range(int(y // TILE), int((y + self.h) // TILE) + 1):
            for tx in range(int(x // TILE), int((x + self.w) // TILE) + 1):
                if nv.solido(tx, ty):
                    return False
        return True

    def agir(self, g):
        am = _ameaca(g)
        self.virado = self.lado_jogador(g)
        self.vx = self.vy = 0
        if self.estado == "visivel":
            self.alerta = 0.5
            self.y += math.sin(self.t * 0.08) * 0.3
            self.cd -= am
            if self.cd <= 0 and self.dist(g) < 190:
                self.estado, self.timer = "conjura", int(30 / am)
                g.audio.tocar("grito")
        elif self.estado == "conjura":
            self.alerta = 1.0
            self.timer -= 1
            if self.timer % 4 == 0:
                g.efeito(self.cx + self.virado * 8 + random.uniform(-6, 6), self.y + 12 + random.uniform(-6, 6),
                         "brilho", (255, 170, 80), 0, -0.2, 12)
            if self.timer <= 0:
                ox, oy = self.cx + self.virado * 8, self.y + 12
                ang = math.atan2((g.p.y + g.p.h / 2) - oy, g.p.cx - ox)
                n = 2 if self.grande else 1
                for k in range(n):
                    g.novos.append(Orbe(ox, oy, ang + (k - (n - 1) / 2) * 0.6, 1.1 + 0.25 * am))
                g.audio.tocar("abre_q")
                self.estado, self.timer = "espera", 60
        elif self.estado == "espera":
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "some", 18
        elif self.estado == "some":
            self.timer -= 1
            if self.timer <= 0:
                self.estado, self.timer = "fora", 30
        elif self.estado == "fora":
            self.timer -= 1
            if self.timer <= 0:
                p = g.p
                for _ in range(12):
                    nx = p.cx + random.choice((-1, 1)) * random.uniform(60, 100)
                    ny = p.y - random.uniform(10, 40)
                    if self._lugar_livre(g, nx - self.w / 2, ny):
                        self.x, self.y = nx - self.w / 2, ny
                        break
                self.estado, self.timer, self.cd = "aparece", 18, 90
                g.particulas_burst(self.cx, self.y + 12, (120, 80, 160), 10, 1.5)
        elif self.estado == "aparece":
            self.timer -= 1
            if self.timer <= 0:
                self.estado = "visivel"

    def draw(self, s, cam):
        if self.estado == "fora":
            return
        if self.estado in ("some", "aparece"):
            k = self.timer / 18 if self.estado == "some" else 1 - self.timer / 18
            if (self.t // 2) % 2 and k < 0.6:
                return
        super().draw(s, cam)

    def arte(self):
        c = self.estado == "conjura"
        s, o = A.feiticeiro(self.t // 6, c)
        return ("feit", self.t // 6 % 9, c), s, o


class AguaViva(Monstro):
    Boneco = B.AguaViva
    w, h = 16, 16
    voa = True
    vida = 2
    moedas = 2
    estado_inicial = "deriva"

    def atingivel(self):
        return self.estado == "deriva"

    def ao_acertar(self, g, como):
        if self.estado != "deriva":
            return True
        r = super().ao_acertar(g, como)
        if not r:                                              # "morreu": incha e explode daqui a pouco
            self.estado, self.timer = "prestes", 40
            self.vida = 0
            g.audio.tocar("grito")
            return True
        return r

    def agir(self, g):
        am = _ameaca(g)
        if self.estado == "deriva":
            self.alerta = 0.5
            p = g.p
            self.vx = math.copysign(min(0.3 * am, abs(p.cx - self.cx) * 0.02), p.cx - self.cx)
            self.vy = math.copysign(min(0.25 * am, abs((p.y - 10) - self.y) * 0.02), (p.y - 10) - self.y)
            self.vy += math.sin(self.t * 0.06) * 0.25
            self.x += self.vx
            self.y += self.vy
            self.virado = 1
        else:
            self.alerta = 1.0
            self.timer -= 1
            if self.timer <= 0:
                self.vivo = False
                g.shake, g.parada = 10, 4
                g.audio.tocar("pisao")
                for _ in range(2):
                    g.particulas_burst(self.cx, self.y + self.h / 2, (255, 140, 60), 16, 3.2)
                if self.dist(g) < 30:
                    g.ferir(origem=self.cx)
                self.ao_morrer(g)

    def arte(self):
        pr = 0.0 if self.estado == "deriva" else round(1 - self.timer / 40, 1)
        s, o = A.aguaviva(self.t // 4, pr)
        return ("agua", self.t // 4 % 12, pr), s, o


# nome no gerador de fases → (classe, altura acima do chão onde nasce)
TIPOS = {
    "mosca": (Mosca, 46), "cuspidor": (Cuspidor, 56), "chifrudo": (Chifrudo, 0), "louva": (Louva, 0),
    "colosso": (Colosso, 0), "globulo": (Globulo, 40), "tatu": (Tatu, 0), "musgo": (Musgo, 0),
    "feiticeiro": (Feiticeiro, 30), "aguaviva": (AguaViva, 44),
}
