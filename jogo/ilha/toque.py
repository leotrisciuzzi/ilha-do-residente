"""Controles de toque (Android), no molde do Super Mario Run: sem controle desenhado na tela.

Na fase o Doutor corre sozinho. Toque em qualquer lugar = pula (segurar = pula mais alto e, no ar,
plana). Deslizar o dedo: ← → vira/volta a correr · ↓ para (no ar: pisão; segurando: abaixa) ·
↑ ataque do pet (bote do gato; sem pet, golpe de bastão) · na diagonal ataca para esse lado ·
→ de novo no sentido em que já corre: dash. Só a pausa (II, no canto) é um botão. Vários dedos
ao mesmo tempo funcionam (segurar o pulo com um e deslizar com outro).
Fora da fase: arrastar o dedo rola a lista (vira MOUSEWHEEL) e um toque curto vira clique.
Os eventos de mouse que o SDL sintetiza a partir do toque são descartados — este módulo
gera os seus, já nas coordenadas lógicas da tela (W x H, com as faixas pretas descontadas)."""
import math
import os

import pygame

TOQUE = pygame.event.custom_type()       # Event(TOQUE, acoes={...}[, angulo=rad]) = ações recém-disparadas

RAIO_PAUSA = 40                          # único botão (II), no canto superior direito
VOLTAR = (46, 46, 36)                    # botão ◀ dos menus (centro x, centro y, raio)
ESPERA_PULO = 5        # quadros (~80 ms) sem deslizar até o toque virar pulo segurado
INICIO_DESLIZE = 16    # px andados dentro da espera: é deslize, não pulo
DESLIZE = 48           # px para reconhecer a direção do deslize
TOQUE_CURTO = 40       # deslocamento máximo (px) para valer como toque (menus); dedo treme mais que mouse
PASSO_ROLAGEM = 46     # px de arrasto por "clique" da roda
DICA_QUADROS = 300
PULO_MINIMO = 8       # quadros de pulo "segurado" garantidos num toque rápido (pulo útil, não um pulinho)     # dica dos gestos no começo de cada fase


def ativo():
    return bool(os.environ.get("ANDROID_ARGUMENT") or os.environ.get("ILHA_TOQUE"))


class Dedo:
    __slots__ = ("x0", "y0", "x", "y", "t", "estado")

    def __init__(self, x, y):
        self.x0 = self.x = x
        self.y0 = self.y = y
        self.t = 0
        self.estado = "novo"      # novo -> pulo | deslize -> (abaixa | feito)


class Toque:
    def __init__(self, W, H, margem_cima=0, margem_baixo=0):
        self.W, self.H = W, H
        self.oy = margem_cima                     # a área útil começa abaixo da margem segura de cima
        self.H_janela = H + margem_cima + margem_baixo
        self.pausa = (W - 44, 44, RAIO_PAUSA)
        self.dedos = {}            # id -> Dedo (na fase)
        self.gestos = {}           # id -> [x0, y0, x, y, acumulado_y, moveu] (menus)
        self.sentido = 1           # corrida automática: 1 direita, -1 esquerda
        self.parado = False
        self.fase = None           # id do jogo atual: fase nova = volta a correr para a direita
        self.dica = 0
        self.rastros = []          # (x, y, ângulo, quadros restantes, rótulo) — retorno visual do gesto
        self.pausa_apertada = 0
        self.pulo_min = 0
        self.voltar_visivel = False
        self.mouse_sdl = False
        self.passo = PASSO_ROLAGEM   # px de arrasto por clique de roda; o App ajusta à tela (lista anda com o dedo)
        self.inercia = 0.0           # px/quadro que a lista ainda anda depois de soltar o dedo
        self.inercia_acc = 0.0
        self.quadro = 0
        self.ondas = []              # [x, y, idade]: ondinha que nasce onde o dedo tocou (menus)
        self.dicas_restantes = 3     # o App lê/grava no save
        self.ao_mostrar_dica = None       # o SDL está gerando mouse a partir do toque (usado nos menus)  # o App liga nas telas que têm para onde voltar
        self._fontes = {}

    # -- coordenadas
    def logico(self, e):
        ww, wh = pygame.display.get_window_size()
        s = min(ww / self.W, wh / self.H_janela) or 1
        ox, oy = (ww - self.W * s) / 2, (wh - self.H_janela * s) / 2
        return (e.x * ww - ox) / s, (e.y * wh - oy) / s - self.oy

    def segurando(self, acao):
        if acao == "pulo":
            return self.pulo_min > 0 or any(d.estado == "pulo" for d in self.dedos.values())
        if acao == "baixo":
            return any(d.estado == "abaixa" for d in self.dedos.values())
        if acao in ("dir", "esq") and self.fase is not None and not self.parado:
            return self.sentido == (1 if acao == "dir" else -1)
        return False

    def nova_fase(self, ident):
        if ident != self.fase:
            self.fase = ident
            self.sentido, self.parado = 1, False
            if self.dicas_restantes > 0:            # só nas primeiras fases
                self.dicas_restantes -= 1
                self.dica = DICA_QUADROS
                if self.ao_mostrar_dica:
                    self.ao_mostrar_dica(self.dicas_restantes)
            self.dedos.clear()
            self.rastros.clear()
            self.pulo_min = 0

    # -- filtro de eventos (chamado uma vez por quadro, mesmo sem eventos)
    def filtrar(self, eventos, na_fase, pausado=False, fase=None):
        out = []
        if na_fase:
            self.nova_fase(fase)
        menus = not na_fase or pausado
        self.quadro += 1
        for e in eventos:
            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL) \
                    and getattr(e, "touch", False):
                # "mouse" que o SDL gera do toque: já vem na coordenada exata da tela desenhada (ele mesmo
                # desconta faixas pretas, barra de navegação e recorte). Nos menus é a fonte do toque.
                if not self.mouse_sdl:
                    self.mouse_sdl = True
                    self.gestos.clear()                     # descarta o gesto já começado pelo dedo
                if menus and e.type != pygame.MOUSEWHEEL:
                    tipo = {pygame.MOUSEBUTTONDOWN: pygame.FINGERDOWN, pygame.MOUSEBUTTONUP: pygame.FINGERUP,
                            pygame.MOUSEMOTION: pygame.FINGERMOTION}[e.type]
                    if tipo == pygame.FINGERDOWN or "mouse" in self.gestos:
                        ev = pygame.event.Event(tipo, finger_id="mouse")
                        out += self._gesto(ev, e.pos[0], e.pos[1] - self.oy)
                continue
            if e.type not in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
                out.append(e)
                continue
            x, y = self.logico(e)
            if na_fase and not pausado:
                out += self._fase(e, x, y)
            else:
                self.dedos.clear()
                if not self.mouse_sdl:                      # sem o mouse do SDL: calcula pelo dedo
                    out += self._gesto(e, x, y)
        if na_fase and not pausado:
            out += self._tempo()
            self.inercia = 0.0
        else:
            self.dedos.clear()
            out += self._inercia()
        if not na_fase:
            self.fase = None
        return out

    def _evento(self, *acoes, **extra):
        return pygame.event.Event(TOQUE, acoes=set(acoes), **extra)

    def _fase(self, e, x, y):
        if e.type == pygame.FINGERDOWN:
            cx, cy, r = self.pausa
            if math.hypot(x - cx, y - cy) <= r * 1.3:
                self.pausa_apertada = 8
                return [self._evento("pausa")]
            self.dedos[e.finger_id] = Dedo(x, y)
            return []
        d = self.dedos.get(e.finger_id)
        if d is None:
            return []
        d.x, d.y = x, y
        out = []
        if d.estado == "novo" and math.hypot(x - d.x0, y - d.y0) >= INICIO_DESLIZE:
            d.estado = "deslize"
        if d.estado == "deslize" and math.hypot(x - d.x0, y - d.y0) >= DESLIZE:
            out += self._deslize(d)
        if e.type == pygame.FINGERUP:
            del self.dedos[e.finger_id]
            if d.estado == "novo":          # toque rápido: pulo baixo (soltou antes da espera)
                self.pulo_min = PULO_MINIMO
                out.append(self._evento("pulo", "ok"))
        return out

    def _tempo(self):
        """Toque parado por ESPERA_PULO quadros vira pulo segurado (quanto mais segura, mais alto)."""
        out = []
        for d in self.dedos.values():
            d.t += 1
            if d.estado == "novo" and d.t >= ESPERA_PULO:
                d.estado = "pulo"
                out.append(self._evento("pulo", "ok"))
        self.dica = max(0, self.dica - 1)
        self.pulo_min = max(0, self.pulo_min - 1)
        self.pausa_apertada = max(0, self.pausa_apertada - 1)
        for r in self.rastros:
            r[3] -= 1
        self.rastros = [r for r in self.rastros if r[3] > 0]
        return out

    def _deslize(self, d):
        dx, dy = d.x - d.x0, d.y - d.y0
        ang = math.atan2(dy, dx)
        graus = math.degrees(ang)                  # 0 = direita, 90 = baixo, -90 = cima
        d.estado = "feito"
        if abs(graus) <= 25 or abs(graus) >= 155:  # horizontal: vira e volta a correr; no mesmo sentido: dash
            novo = 1 if dx > 0 else -1
            if novo == self.sentido and not self.parado:
                rot, ev = "DASH", [self._evento("dash")]
            else:
                rot, ev = "", []
            self.sentido = novo
            self.parado = False
        elif 65 <= graus <= 115:                   # para baixo: para (no ar: pisão); segurando: abaixa
            self.parado = True
            d.estado = "abaixa"
            rot, ev = "", [self._evento("baixo")]
        elif -115 <= graus <= -65:                 # para cima: ataque (bote do pet)
            rot, ev = "ATAQUE", [self._evento("lingua")]
        else:                                      # diagonal: ataque virado para esse lado
            rot, ev = "ATAQUE", [self._evento("arremesso", angulo=ang)]
        self.rastros.append([d.x0, d.y0, ang, 18, rot])
        return ev

    def _gesto(self, e, x, y):
        out = []
        g = self.gestos.get(e.finger_id)
        if e.type == pygame.FINGERDOWN:
            self.inercia = 0.0                          # dedo na tela segura a lista
            self.ondas.append([x, y, 0])                # resposta visual imediata ao toque
            self.gestos[e.finger_id] = [x, y, x, y, 0.0, False, [(self.quadro, y)]]
            out.append(pygame.event.Event(pygame.MOUSEMOTION, pos=(int(x), int(y)), rel=(0, 0), buttons=(0, 0, 0),
                                          touch=False))
        elif e.type == pygame.FINGERMOTION and g:
            g[4] += y - g[3]
            g[2], g[3] = x, y
            g[6] = [h for h in g[6] if self.quadro - h[0] <= 4] + [(self.quadro, y)]
            if math.hypot(x - g[0], y - g[1]) > TOQUE_CURTO:
                if not g[5]:
                    g[4] = y - g[1]                     # o deslocamento até aqui também rola
                g[5] = True
            if g[5]:
                g[4] = self._rodar(g[4], out)
        elif e.type == pygame.FINGERUP and g:
            del self.gestos[e.finger_id]
            if g[5]:                                    # soltou arrastando: a lista continua (inércia)
                (q0, y0), (q1, y1) = g[6][0], g[6][-1]
                v = (y1 - y0) / max(1, q1 - q0)
                if abs(v) > 4:
                    self.inercia = max(-70.0, min(70.0, v))
                    self.inercia_acc = g[4]
            if not g[5] and self.voltar_visivel and math.hypot(g[0] - VOLTAR[0], g[1] - VOLTAR[1]) <= VOLTAR[2] * 1.4:
                out.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_AC_BACK, mod=0, unicode="", scancode=0))
            elif not g[5]:
                p = (int(x), int(y))
                out.append(pygame.event.Event(pygame.MOUSEMOTION, pos=p, rel=(0, 0), buttons=(0, 0, 0), touch=False))
                out.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=p, button=1, touch=False))
                out.append(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=p, button=1, touch=False))
        return out

    def _rodar(self, acc, out):
        """Converte px arrastados em cliques de roda: a lista anda junto com o dedo (passo = altura da linha)."""
        while abs(acc) >= self.passo:
            d = 1 if acc > 0 else -1                    # arrastar para baixo = rolar para cima
            acc -= d * self.passo
            out.append(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=d, flipped=False,
                                          precise_x=0.0, precise_y=float(d), touch=False))
        return acc

    def _inercia(self):
        out = []
        if abs(self.inercia) > 1.5:
            self.inercia_acc = self._rodar(self.inercia_acc + self.inercia, out)
            self.inercia *= 0.9
        else:
            self.inercia = 0.0
        return out

    # -- desenho
    def _fonte(self, tam):
        if tam not in self._fontes:
            from .ui import fonte
            self._fontes[tam] = fonte(tam, True)
        return self._fontes[tam]

    def desenhar(self, tela):
        # pausa: o único botão desenhado
        cx, cy, r = self.pausa
        s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 130 if self.pausa_apertada else 70), (r + 2, r + 2), r)
        pygame.draw.circle(s, (50, 36, 40, 150), (r + 2, r + 2), r, 3)
        for bx in (-9, 5):
            pygame.draw.rect(s, (50, 36, 40, 200), (r + 2 + bx, r - 10, 6, 24))
        tela.blit(s, (cx - r - 2, cy - r - 2))
        # retorno visual dos deslizes: seta que some
        for x, y, ang, q, rot in self.rastros:
            a = int(200 * q / 18)
            camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            ex, ey = x + math.cos(ang) * 90, y + math.sin(ang) * 90
            pygame.draw.line(camada, (255, 255, 255, a), (x, y), (ex, ey), 10)
            for lado in (2.5, -2.5):
                pygame.draw.line(camada, (255, 255, 255, a), (ex, ey),
                                 (ex - math.cos(ang + lado) * -28, ey - math.sin(ang + lado) * -28), 10)
            tela.blit(camada, (0, 0))
            if rot:
                t = self._fonte(22).render(rot, True, (255, 255, 255))
                t.set_alpha(a)
                tela.blit(t, (ex - t.get_width() // 2, ey - 40))
        # dica dos gestos no começo da fase
        if self.dica:
            a = min(255, self.dica * 4)
            linhas = ("O Doutor corre sozinho",
                      "TOQUE: pula · segure: mais alto e plana",
                      "DESLIZE  ← →  vira  ·  ↓  para / pisão",
                      "↑  ataque do pet  ·  → de novo: dash")
            f = self._fonte(24)
            caixa = pygame.Surface((self.W, 16 + 36 * len(linhas)), pygame.SRCALPHA)
            caixa.fill((30, 20, 24, int(150 * a / 255)))
            for i, l in enumerate(linhas):
                t = f.render(l, True, (255, 255, 255))
                caixa.blit(t, (self.W // 2 - t.get_width() // 2, 10 + i * 36))
            caixa.set_alpha(a)
            tela.blit(caixa, (0, self.H - caixa.get_height() - 30))

    def desenhar_voltar(self, tela):
        cx, cy, r = VOLTAR
        s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 252, 240, 235), (r + 2, r + 2), r)
        pygame.draw.circle(s, (50, 36, 40), (r + 2, r + 2), r, 3)
        pygame.draw.polygon(s, (50, 36, 40), [(r - 12, r + 2), (r + 10, r - 13), (r + 10, r + 17)])
        tela.blit(s, (cx - r - 2, cy - r - 2))

    def desenhar_ondas(self, tela):
        """Onda que se expande e some onde o dedo tocou (como o 'ripple' dos apps de celular)."""
        vivas = []
        for o in self.ondas:
            o[2] += 1
            if o[2] > 16:
                continue
            vivas.append(o)
            k = o[2] / 16
            r = int(14 + 46 * k)
            s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, int(110 * (1 - k))), (r + 2, r + 2), r)
            pygame.draw.circle(s, (255, 236, 150, int(200 * (1 - k))), (r + 2, r + 2), r, 3)
            tela.blit(s, (o[0] - r - 2, o[1] - r - 2))
        self.ondas = vivas
