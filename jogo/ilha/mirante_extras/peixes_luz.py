"""Peixes de luz — peixinhos bioluminescentes sob a superfície do lago do Mirante.

Há um peixe para cada mundo (grupo de questões) que você já jogou: os ids do save são agrupados pelo prefixo
(antes do primeiro "-", ":" ou "__"), os mais jogados primeiro; no mínimo 2 e no máximo 14 peixes. A cor de cada
um sai do nome do grupo (sempre a mesma), num leque frio de ciano, azul e violeta.

Eles vivem no mundo, não na tela: nadam devagar entre o horizonte e a margem, somem quando a câmera passa e
estão lá quando ela volta. Os mais distantes (perto do horizonte) parecem menores e mais apagados. Se a Lume
para perto da margem, os que estão por ali chegam devagar, curiosos com a luz. De vez em quando, raramente,
um deles salta: um arco curto acima da água, umas gotinhas, e anéis que se abrem na superfície.
"""
import colorsys
import math
import random
import re
import zlib

import pygame

from . import Base
from ..mirante import GY, HZ, LW, WW

TOPO, FUNDO = HZ + 3, GY - 3          # faixa onde os peixes nadam
ALT = FUNDO - TOPO


def _grupos(save_d):
    """Grupos distintos de questões jogadas, do mais jogado ao menos jogado."""
    cont = {}
    try:
        for k in (save_d.get("q") or {}):
            g = re.split(r"[-:]|__", str(k), maxsplit=1)[0].strip().lower() or "?"
            cont[g] = cont.get(g, 0) + 1
    except Exception:
        pass
    gs = sorted(cont, key=lambda g: (-cont[g], g))[:14]
    for extra in ("lume", "lua"):                       # mínimo de dois peixes, mesmo com save vazio
        if len(gs) >= 2:
            break
        gs.append(extra)
    return gs


def _cor(grupo):
    """Cor determinística pelo nome do grupo: matiz entre ciano e violeta, com leve variação de brilho."""
    h = zlib.crc32(grupo.encode("utf-8"))
    matiz = (170 + (h % 1000) / 1000 * 120) / 360           # 170°–290°
    sat = 0.45 + ((h >> 10) % 100) / 100 * 0.3
    return tuple(int(v * 255) for v in colorsys.hsv_to_rgb(matiz, sat, 1.0))


def _brilho(raio, cor, forca):
    s = pygame.Surface((raio * 2 + 1, raio * 2 + 1))
    for r in range(raio, 0, -1):
        k = (1 - r / raio) ** 2 * forca
        pygame.draw.circle(s, tuple(min(255, int(c * k)) for c in cor), (raio, raio), r)
    return s


# corpinhos (olhando para a direita): tamanhos 3, 4 e 5; dois quadros de cauda
FORMAS = {
    3: (["b..", "bBb", "..."], ["...", "bBb", "b.."]),
    4: (["b.b.", ".bBb", "b.b."], ["..b.", "bbBb", "..b."]),
    5: (["b.bb.", ".bbBH", "b.bb."], ["..bb.", "bbbBH", "..bb."]),
}


def _sprite(linhas, cor):
    pal = {"b": tuple(int(c * 0.7) for c in cor), "B": tuple(min(255, int(c * 0.9 + 30)) for c in cor),
           "H": tuple(min(255, int(c * 0.6 + 120)) for c in cor)}
    s = pygame.Surface((len(linhas[0]), len(linhas)))
    s.fill((0, 0, 0))
    for y, ln in enumerate(linhas):
        for x, ch in enumerate(ln):
            if ch in pal:
                s.set_at((x, y), pal[ch])
    return s                                             # desenhado com BLEND_RGB_ADD: o preto não soma nada


class Peixe:
    def __init__(self, grupo, rng):
        self.cor = _cor(grupo)
        self.x = rng.uniform(10, WW - 10)
        self.y = rng.uniform(TOPO + 2, FUNDO - 2)
        self.ax, self.ay = self.x, self.y                # alvo atual
        self.vx = self.vy = 0.0
        self.dir = 1
        self.fase = rng.uniform(0, 6.28)
        self.vel = rng.uniform(0.12, 0.2)
        self.espera = rng.randint(0, 200)
        self.rastro = []                                 # últimas posições (x, y)
        self.salto = None                                # [x0, y0, x1, quadro, duração, altura]
        # sprites prontos: {tamanho: [[quadro0, quadro1] direita, [..] esquerda]}
        self.spr = {}
        for n, (a, b) in FORMAS.items():
            d = [_sprite(a, self.cor), _sprite(b, self.cor)]
            self.spr[n] = [d, [pygame.transform.flip(s, True, False) for s in d]]
        self.halo = [_brilho(5, self.cor, f) for f in (0.5, 0.7, 0.95)]
        self.rastro_cor = [tuple(int(c * k) for c in self.cor) for k in (0.08, 0.14, 0.22, 0.3, 0.4)]


class Extra(Base):
    lugares = ()

    def __init__(self, mirante):
        super().__init__(mirante)
        rng = random.Random(77)
        try:
            d = mirante.app.save.d
        except Exception:
            d = {}
        self.peixes = [Peixe(g, rng) for g in _grupos(d)]
        self.rng = random.Random()
        self.salto_t = self.rng.randint(600, 1400)
        self.aneis = []                                  # [x, y, raio, vida]
        self.gotas = []                                  # [x, y, vx, vy, vida]

    # ------------------------------------------------------------ simulação
    def _novo_alvo(self, p, lume):
        perto = lume is not None and abs(p.x - lume) < 120
        if perto:                                        # curiosidade: chega devagar perto da margem, diante da Lume
            p.ax = lume + math.sin(p.fase * 3.7) * 14
            p.ay = FUNDO - 1 - abs(math.cos(p.fase * 2.3)) * 6
            p.espera = self.rng.randint(40, 120)
        else:
            p.ax = max(8, min(WW - 8, p.x + self.rng.uniform(-70, 70)))
            p.ay = self.rng.uniform(TOPO + 1, FUNDO - 1)
            p.espera = self.rng.randint(60, 260)

    def update(self):
        mir = self.mirante
        t = mir.t
        lume = mir.x if getattr(mir, "modo", "andar") != "luneta" else None
        for p in self.peixes:
            if p.salto:
                self._update_salto(p)
                continue
            dx, dy = p.ax - p.x, p.ay - p.y
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                p.espera -= 1
                if p.espera <= 0:
                    self._novo_alvo(p, lume)
            elif lume is not None and abs(p.x - lume) < 120 and abs(p.ax - lume) > 30:
                self._novo_alvo(p, lume)                 # a Lume chegou: muda de ideia
            v = p.vel * (0.6 if dist < 8 else 1.0)
            if dist > 0.01:
                p.vx += (dx / dist * v - p.vx) * 0.04
                p.vy += (dy / dist * v * 0.5 - p.vy) * 0.04
            else:
                p.vx *= 0.9
                p.vy *= 0.9
            p.x += p.vx + math.sin(t * 0.05 + p.fase) * 0.03
            p.y = max(TOPO, min(FUNDO, p.y + p.vy + math.sin(t * 0.031 + p.fase) * 0.02))
            if abs(p.vx) > 0.03:
                p.dir = 1 if p.vx > 0 else -1
            if t % 4 == 0:
                p.rastro.append((p.x, p.y))
                if len(p.rastro) > 5:
                    p.rastro.pop(0)
        # salto raro de um peixe que esteja à vista
        self.salto_t -= 1
        if self.salto_t <= 0:
            cam = mir.cam
            vis = [p for p in self.peixes if not p.salto and 20 < p.x - cam < LW - 20]
            if vis:
                self._saltar(self.rng.choice(vis))
                self.salto_t = self.rng.randint(1500, 3200)
            else:
                self.salto_t = self.rng.randint(200, 500)
        for a in self.aneis:
            a[2] += 0.12
            a[3] -= 1
        self.aneis = [a for a in self.aneis if a[3] > 0]
        for g in self.gotas:
            g[0] += g[2]
            g[1] += g[3]
            g[3] += 0.06
            g[4] -= 1
        self.gotas = [g for g in self.gotas if g[4] > 0 and g[1] < g[5]]

    def _saltar(self, p):
        prof = (p.y - TOPO) / max(1, ALT)               # 0 = longe (horizonte), 1 = perto (margem)
        altura = 7 + 10 * prof
        x1 = p.x + p.dir * (8 + 8 * prof)
        p.salto = [p.x, p.y, x1, 0, int(44 + 16 * prof), altura]
        p.rastro.clear()
        self._respingo(p.x, p.y, prof, 3)

    def _respingo(self, x, y, prof, n):
        self.aneis.append([x, y, 1.0, 60])
        self.aneis.append([x, y, 0.2, 75])
        for _ in range(n):
            self.gotas.append([x, y - 1, self.rng.uniform(-0.35, 0.35), self.rng.uniform(-0.9, -0.5) * (0.7 + prof * 0.5),
                               40, y + 1])

    def _update_salto(self, p):
        x0, y0, x1, k, dur, alt = p.salto
        k += 1
        f = k / dur
        p.x = x0 + (x1 - x0) * f
        p.y = y0 - math.sin(math.pi * f) * alt
        p.salto[3] = k
        if k % 6 == 0 and 0.15 < f < 0.85:               # pinguinhos caindo do corpo
            self.gotas.append([p.x, p.y, self.rng.uniform(-0.15, 0.15), 0.1, 30, y0 + 1])
        if k >= dur:
            p.x, p.y, p.salto = x1, y0, None
            p.ax, p.ay, p.vx, p.vy, p.espera = x1, y0, 0.0, 0.0, 60
            self._respingo(x1, y0, (y0 - TOPO) / max(1, ALT), 4)

    # ------------------------------------------------------------ desenho
    def draw_lago(self, m, cam):
        t = self.mirante.t
        add = pygame.BLEND_RGB_ADD
        for a in self.aneis:                             # anéis de ondulação (achatados pela perspectiva)
            x = a[0] - cam
            if not -30 < x < LW + 30:
                continue
            prof = (a[1] - TOPO) / max(1, ALT)
            r = a[2] * (0.7 + prof * 0.6)
            w, h = max(2, int(r * 2)), max(1, int(r * (0.25 + prof * 0.15)))
            nv = max(1, min(6, int(a[3] / 75 * 6 + 0.5)))      # brilho em 6 degraus (cache pequeno)
            chave = (w, h + 1, nv)
            anel = _ANEL.get(chave)
            if anel is None:
                anel = pygame.Surface((w, h + 1))
                anel.fill((0, 0, 0))
                pygame.draw.ellipse(anel, (11 * nv, 15 * nv, 22 * nv), (0, 0, w, h + 1), 1)
                if len(_ANEL) < 600:
                    _ANEL[chave] = anel
            m.blit(anel, (int(x) - w // 2, int(a[1]) - h // 2), special_flags=add)  # somada: o reflexo continua
        for p in self.peixes:
            x = p.x - cam
            if not -12 < x < LW + 12:
                continue
            prof = (p.y - TOPO) / max(1, ALT) if not p.salto else (p.salto[1] - TOPO) / max(1, ALT)
            n = 3 if prof < 0.3 else (4 if prof < 0.65 else 5)
            fora = p.salto is not None
            pulso = math.sin(t * 0.045 + p.fase)
            nivel = 2 if fora else (1 if pulso > -0.2 else 0)
            if prof < 0.3 and not fora:
                nivel = max(0, nivel - 1)
            for i, (rx, ry) in enumerate(p.rastro):      # rastro curto que se apaga
                c = p.rastro_cor[i + 5 - len(p.rastro)]
                m.fill(c, (int(rx - cam), int(ry), 1, 1), special_flags=add)
            h = p.halo[nivel]
            m.blit(h, (int(x) - 5, int(p.y) - 5), special_flags=add)
            quadro = (t // (6 if not fora else 3) + int(p.fase * 10)) % 2
            spr = p.spr[n][0 if p.dir > 0 else 1][quadro]
            m.blit(spr, (int(x) - n // 2, int(p.y) - 1), special_flags=add)
            if fora:                                     # fora da água: o corpo aparece inteiro, mais claro
                m.blit(spr, (int(x) - n // 2, int(p.y) - 1), special_flags=add)
        for g in self.gotas:
            x = g[0] - cam
            if 0 <= x < LW:
                k = min(1.0, g[4] / 20)
                m.fill((int(150 * k), int(185 * k), int(230 * k)), (int(x), int(g[1]), 1, 1), special_flags=add)


_ANEL = {}
