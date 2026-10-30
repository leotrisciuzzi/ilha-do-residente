"""Estado de jogo: plataforma com o Doutor montado no pônei branco + bichos-questão."""
import math
import random

import pygame

from . import art, bonecos, climas, edicao, figurino, heroi, hk, pets
from .controle import PADEVENT
from .level import (Nivel, TILE, H, VAZIO, CHAO, PLAT, ESPINHO, BLOCO_OVO,
                    TRONCO, BLOCO_USADO)

LW, LH = (180, edicao.ALTURA_MUNDO) if edicao.RETRATO else (320, 180)   # resolução lógica do mundo (escalada 4x, pixel art)
GRAV, MAXQUEDA = 0.32, 6.5
PULO, ACC, ACC_AR, ATRITO, VMAX = -5.9, 0.3, 0.22, 0.38, 2.1     # aceleração e freio mais secos (resposta rápida)
FLUTTER_FORCA, FLUTTER_MAX = 0.5, 52


def rect_hit(a, b):
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


def pe(s, spr, e, cam, dy=0):
    """Desenha o sprite alinhado pelos pés (centro-baixo) da hitbox."""
    s.blit(spr, (int(e.x + e.w / 2 - spr.get_width() / 2 - cam[0]),
                 int(e.y + e.h - spr.get_height() - cam[1] + dy)))


def centro(s, spr, e, cam, dy=0):
    s.blit(spr, (int(e.x + e.w / 2 - spr.get_width() / 2 - cam[0]),
                 int(e.y + e.h / 2 - spr.get_height() / 2 - cam[1] + dy)))


class Ent:
    w, h = 12, 12
    comestivel = False
    espinhento = False
    boneco = None              # modelo articulado (bonecos.py); o Jogo chama boneco.passo depois do update
    Boneco = None              # fábrica do boneco: classe de bonecos.py (ou função que recebe o inimigo)

    def __init__(self, x, y):
        self.x, self.y = x - self.w / 2, y - self.h
        self.vx = self.vy = 0.0
        self.vivo = True
        self.t = random.randrange(100)
        self.no_chao = False
        self.virado = -1
        if self.Boneco is not None:
            self.boneco = self.Boneco()

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    @property
    def cx(self):
        return self.x + self.w / 2

    def fisica(self, nivel, plataformas=True):
        """Colisão AABB com tiles, eixo a eixo. Retorna (bateu_x, bateu_teto)."""
        bateu_x = bateu_teto = False
        self.x += self.vx
        x0, x1 = int(self.x // TILE), int((self.x + self.w - 0.01) // TILE)
        y0, y1 = int(self.y // TILE), int((self.y + self.h - 0.01) // TILE)
        for ty in range(y0, y1 + 1):
            for tx in (x0, x1):
                if nivel.solido(tx, ty):
                    if self.vx > 0:
                        self.x = tx * TILE - self.w
                    elif self.vx < 0:
                        self.x = (tx + 1) * TILE
                    bateu_x = True
                    break
        pe_antes = self.y + self.h
        self.y += self.vy
        x0, x1 = int(self.x // TILE), int((self.x + self.w - 0.01) // TILE)
        self.no_chao = False
        if self.vy >= 0:
            ty = int((self.y + self.h) // TILE)
            for tx in range(x0, x1 + 1):
                t = nivel.tile(tx, ty)
                if nivel.solido(tx, ty) or (plataformas and t == PLAT and pe_antes <= ty * TILE + 1):
                    self.y = ty * TILE - self.h
                    self.vy = 0
                    self.no_chao = True
                    break
        else:
            ty = int(self.y // TILE)
            for tx in range(x0, x1 + 1):
                if nivel.solido(tx, ty):
                    self.y = (ty + 1) * TILE
                    self.vy = 0
                    bateu_teto = (tx, ty)
                    break
        return bateu_x, bateu_teto

    def atingivel(self):
        """False = não colide com nada agora (fungo escondido, caixa de seringas)."""
        return True

    def ao_acertar(self, g, como):
        """True = o inimigo tratou o golpe e não morre (ex.: estreptococo fica bravo)."""
        return False

    def beira(self, nivel):
        """True se o próximo passo cai num buraco (andarilhos viram)."""
        frente = self.x + (self.w + 1 if self.vx > 0 else -1)
        ty = int((self.y + self.h + 2) // TILE)
        tx = int(frente // TILE)
        return not (nivel.solido(tx, ty) or nivel.tile(tx, ty) == PLAT)

    def update(self, g):
        pass

    def draw(self, s, cam):
        pass


# ------------------------------------------------------------------ inimigos

class Bacilo(Ent):
    w, h = 14, 9
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.boneco = bonecos.Bacilo()

    def update(self, g):
        self.t += 1
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        bx, _ = self.fisica(g.nivel)
        if bx or (self.no_chao and self.beira(g.nivel)):
            self.vx = -self.vx
        self.virado = 1 if self.vx > 0 else -1

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Virus(Bacilo):
    w, h = 12, 12
    comestivel = False
    espinhento = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.35
        self.boneco = bonecos.Virus()

    def update(self, g):
        super().update(g)
        if self.no_chao and self.t % 90 == 0:
            self.vy = -4

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Aedes(Ent):
    w, h = 14, 8
    comestivel = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.ox, self.oy = self.x, self.y
        self.boneco = bonecos.Aedes()

    def update(self, g):
        self.t += 1
        nx = self.ox + math.sin(self.t * 0.02) * 40
        self.virado = 1 if nx > self.x else -1
        self.x = nx
        self.y = self.oy + math.sin(self.t * 0.07) * 10

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class BichoQuestao(Ent):
    """O bicho-questão: carrega uma questão. Bote do pet, golpe de bastão ou pisão
    abrem o quiz. Certo = vira flor. Errado = ele te acerta (o Doutor cai)."""
    w, h = 18, 15

    def __init__(self, x, y, idx, cor, revisao=False):
        super().__init__(x, y)
        self.idx, self.cor, self.revisao = idx, cor, revisao
        self.ox = self.x
        self.usado = False
        self.boneco = bonecos.BichoQuestao(cor, revisao)

    def update(self, g):
        self.t += 1
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        if self.no_chao and self.t % 70 == 0:
            self.vy = -3
            self.vx = random.choice((-0.6, 0.6))
            if abs(self.x + self.vx * 10 - self.ox) > 24:
                self.vx = -self.vx
        if self.no_chao and self.vy == 0:
            self.vx *= 0.8
        self.fisica(g.nivel)
        if self.no_chao and self.beira(g.nivel):
            self.vx = 0
        self.virado = 1 if g.p.cx > self.cx else -1

    def draw(self, s, cam):
        self.boneco.draw(s, cam, self)


class Gigante(BichoQuestao):
    """Guardião do anel final — uma questão por acerto (bote do pet, bastão ou pisão)."""
    w, h = 36, 30
    escala = 2                 # o mesmo boneco do bicho-questão, em dobro

    def __init__(self, x, y, idxs, cor):
        super().__init__(x, y, None, cor)
        self.fila = list(idxs)
        self.invuln = 0
        self.bravo = 0
        self.vx = -0.6

    def update(self, g):
        self.t += 1
        self.invuln = max(0, self.invuln - 1)
        self.bravo = max(0, self.bravo - 1)
        self.vy = min(self.vy + GRAV, MAXQUEDA)
        vel = 1.2 if self.bravo else 0.6
        self.vx = math.copysign(vel, self.vx)
        bx, _ = self.fisica(g.nivel)
        if bx or abs(self.x - self.ox) > 70 or (self.no_chao and self.beira(g.nivel)):
            self.vx = -self.vx
            self.x += self.vx * 2
        if self.no_chao and self.t % 120 == 0:
            self.vy = -4.5
        self.virado = 1 if g.p.cx > self.cx else -1

    def draw(self, s, cam):
        if self.invuln and self.invuln % 6 < 3:
            return
        self.boneco.draw(s, cam, self)


# ------------------------------------------------------------------ itens

class Item(Ent):
    w, h = 8, 11

    def __init__(self, x, y, tipo):
        super().__init__(x, y)
        self.tipo = tipo
        self.solta = False             # moeda que pulou do bloco: cai com gravidade

    def update(self, g):
        self.t += 1
        if self.solta:
            self.vy = min(self.vy + GRAV, MAXQUEDA)
            self.fisica(g.nivel)

    def draw(self, s, cam):
        if self.tipo == "moeda":
            pe(s, art.moeda(self.t // 8), self, cam)
        elif self.tipo == "vermelha":
            pe(s, art.moeda(self.t // 8, True), self, cam)
        elif self.tipo == "estrela":
            pe(s, art.estrela(self.t // 10), self, cam, int(math.sin(self.t * 0.1) * 2))


# ------------------------------------------------------------------ jogador

class Heroi(Ent):
    w, h = 14, 26

    def __init__(self, x, y):
        super().__init__(x, y)
        self.virado = 1
        self.flutter = 0
        self.flutter_gasto = 0
        self.coyote = 0
        self.buffer_pulo = 0
        self.pound = 0
        self.lingua_t = 0              # quadro do golpe de bastão (o nome ficou da antiga língua)
        self.dash_t = self.dash_espera = 0
        self.dash_no_ar = False
        self.parede = self.parede_t = self.trava = 0
        self.foco = 0
        self.invuln = 0
        self.bebe = True
        self.anim = 0
        self.historico = []
        self.abaixado = False
        self.t_pulo = self.t_pouso = self.t_abaixo = 99   # quadros desde o pulo / o pouso / abaixar

    def estado(self):
        if self.pound:
            return "pound"
        if self.dash_t:
            return "flutter"
        if self.lingua_t:
            return "lingua"
        if not self.no_chao:
            if self.flutter:
                return "flutter"
            if self.t_pulo < 6 and self.vy < 0:
                return "decolar"
            return "pular" if self.vy < 0 else "cair"
        if self.abaixado:
            return "abaixar"
        if self.t_pouso < 6:
            return "pousar"
        if abs(self.vx) > 0.3:
            return "andar"
        return "parado"

    def quadro(self, est):
        """Contador que o sprite usa em cada estado."""
        if est == "andar":
            return self.anim // 6
        if est == "decolar":
            return self.t_pulo
        if est == "pousar":
            return self.t_pouso
        if est == "abaixar":
            return self.t_abaixo
        return self.anim // 3


ALCANCE_GOLPE = 30
PEGADA_GOLPE = 30     # no golpe, segura o bastão perto da ponta de baixo (linha 30 de 34), como um porrete


def _ang_golpe(t):
    """Ângulo do bastão (graus a partir da vertical, positivo = para a frente) no quadro t do golpe
    (1..22, o mesmo tempo da língua): ergue por trás da cabeça, desce com força até apontar para o
    chão à frente, segura e volta."""
    if t <= 4:
        return -45 * t / 4
    if t <= 9:
        f = (t - 4) / 5
        return -45 + 180 * f * f               # acelera na descida, como uma pancada
    if t <= 14:
        return 135
    return 135 * (1 - (t - 14) / 8)


class _Inimigos(dict):
    """Tipos de inimigo de inimigos.py, carregados na primeira consulta (inimigos.py importa este módulo)."""

    def _carregar(self):
        if not dict.__len__(self):
            from .inimigos import TIPOS
            self.update(TIPOS)

    def __contains__(self, k):
        self._carregar()
        return dict.__contains__(self, k)

    def __getitem__(self, k):
        self._carregar()
        return dict.__getitem__(self, k)


INIMIGOS = _Inimigos()


class Jogo:
    """Uma fase. `questoes` alimenta bichos + gigante; `ao_terminar(res)`
    é chamado no fim (vitória ou game over)."""

    def __init__(self, app, questoes, titulo, seed, paleta_idx=0, ao_terminar=None,
                 contexto="", vidas=3, dificuldade=1.0):
        self.app, self.audio = app, app.audio
        self.questoes = questoes
        self.titulo, self.contexto = titulo, contexto
        self.ao_terminar = ao_terminar
        n = len(questoes)
        n_gig = 0 if n < 3 else (2 if n < 8 else 3)
        self.idx_bichos = list(range(n - n_gig))
        self.idx_gigante = list(range(n - n_gig, n))
        self.nivel = Nivel(seed, max(1, len(self.idx_bichos)), dificuldade)
        self.pal = art.paleta(paleta_idx)
        self.mapa_base = self.mapa = art.render_nivel(self.nivel, self.pal)
        self.ceu = art.ceu(self.pal, LW, LH)
        self.camadas = art.fundo(self.pal, LW, LH, seed)
        self.clima = climas.Controle(self, seed)       # céu, cenário tingido e partículas da música que toca
        rng = random.Random(seed)
        self.nuvens = [(rng.uniform(0, LW * 2), rng.uniform(10, 120), rng.uniform(0.6, 1.3)) for _ in range(7)]
        self.mundo = pygame.Surface((LW, LH))
        self.respostas = {}    # idx -> (escolha, acertou)
        self.estrelas = 10.0
        self.moedas = 0
        self.vermelhas = 0
        self.flores = 0
        self.vidas = vidas
        self.ents, self.itens, self.part, self.textos = [], [], [], []
        self.fx = []                     # efeitos que flutuam: [x, y, vx, vy, vida, vida0, forma, cor, grav]
        self.novos = []        # entidades criadas durante a fase (seringas, esporos, amebinhas)
        self.bolha = None
        self.shake = 0
        self.tempo = 0
        self.gigante = None
        self.vitoria = 0
        self.morte = 0
        self.pausado = False
        self.pausa_sel = 0
        self.quiz_alvo = None
        self.cor_bicho = art.hsv(0.13 + paleta_idx * 0.137 + 0.5, 0.45, 0.95)
        self._spawn()
        self.p = Heroi(*self.nivel.inicio)
        self.pet = self._novo_pet()
        self.capa = hk.Capa(self.p.cx, self.p.y)
        self.parada = 0                    # quadros congelados no impacto (hit-stop)
        save = getattr(app, "save", None)
        self.ameaca = save.d.get("ameaca", 1.0) if save else 1.0     # monstros adaptáveis (monstros.py)
        self.alma = 0
        self.rastro_dash = []
        self.sombra = None
        self.checkpoint = self.nivel.inicio
        self.cam = [0.0, float(LH)]
        self._centralizar_camera(True)

    def _spawn(self):
        bichos = iter(self.idx_bichos)
        for tipo, x, y, extra in self.nivel.spawns:
            if tipo in ("moeda", "vermelha", "estrela"):
                self.itens.append(Item(x, y, tipo))
            elif tipo == "bacilo":
                self.ents.append(Bacilo(x, y))
            elif tipo == "virus":
                self.ents.append(Virus(x, y))
            elif tipo == "aedes":
                self.ents.append(Aedes(x, y))
            elif tipo in INIMIGOS:
                cls, alt = INIMIGOS[tipo]
                self.ents.append(cls(x, y - alt))
            elif tipo == "bicho_q":
                i = next(bichos, None)
                if i is not None:
                    self.ents.append(BichoQuestao(x, y, i, self.cor_bicho,
                                                  self.questoes[i].get("revisao", False)))
            elif tipo == "gigante" and self.idx_gigante:
                self.gigante = Gigante(x, y, self.idx_gigante, self.cor_bicho)
                self.ents.append(self.gigante)
            elif tipo == "anel_meio":
                self.anel_meio = [x, y, True]
            elif tipo == "anel_fim":
                self.anel_fim = [x, y]

    # ------------------------------------------------------------ helpers

    def texto(self, x, y, msg, cor=(255, 255, 255)):
        self.textos.append([x, y, msg, cor, 50])

    def particulas_burst(self, x, y, cor, n=8, vel=2.0):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.5, vel)
            self.part.append([x, y, math.cos(a) * v, math.sin(a) * v - 1, random.randint(18, 32), cor])

    def efeito(self, x, y, forma, cor, vx=0.0, vy=0.0, vida=30, grav=0.0):
        if len(self.fx) < 160:
            self.fx.append([x, y, vx, vy, vida, vida, forma, cor, grav])

    def brilho(self, x, y, cor=(255, 240, 150), n=6):
        """Estrelinhas em cruz que se espalham ao coletar algo."""
        for i in range(n):
            a = i / n * math.tau + random.uniform(-0.3, 0.3)
            v = random.uniform(0.8, 1.6)
            self.efeito(x, y, "brilho", cor, math.cos(a) * v, math.sin(a) * v - 0.4, random.randint(16, 24))

    def confete(self, n=6):
        cores = ((255, 80, 90), (255, 200, 60), (90, 200, 120), (80, 160, 255), (220, 110, 240), (255, 255, 255))
        for _ in range(n):
            self.efeito(self.cam[0] + random.uniform(0, LW), self.cam[1] - 4, "confete", random.choice(cores),
                        random.uniform(-0.5, 0.5), random.uniform(0.4, 1.0), random.randint(90, 150), 0.012)

    def _rastro_heroi(self, p):
        """A nuvem equipada solta faíscas da cor dela quando o pônei corre ou voa."""
        rapido = abs(p.vx) > 1.1 or p.flutter
        if not rapido or self.tempo % (2 if p.flutter else 3):
            return
        forma, cores = heroi.rastro()
        self.efeito(p.cx - p.virado * random.uniform(8, 14), p.y + p.h - random.uniform(1, 6), forma,
                    random.choice(cores), -p.virado * random.uniform(0.1, 0.5), random.uniform(-0.5, -0.1),
                    random.randint(18, 28) if forma != "ponto" else random.randint(12, 18))

    def _soneca(self, p):
        """Parado muito tempo: o Doutor cochila (zZz subindo)."""
        if p.estado() == "parado" and not p.vx:
            p.t_parado = getattr(p, "t_parado", 0) + 1
        else:
            p.t_parado = 0
        if p.t_parado > 300 and p.t_parado % 50 == 0:
            self.efeito(p.cx + 6 * p.virado, p.y - 4, "z", (230, 236, 255), 0.25 * p.virado, -0.35, 70)

    def _baforada(self, p, n):
        """Fiapos da nuvem que escapam pelos lados ao pular e ao pousar."""
        for _ in range(n):
            lado = random.choice((-1, 1))
            self.part.append([p.cx + lado * random.uniform(6, 14), p.y + p.h - random.uniform(0, 4),
                              lado * random.uniform(0.6, 1.8), random.uniform(-0.9, -0.2), random.randint(10, 18),
                              random.choice(((255, 240, 170), (255, 214, 96), (255, 255, 230)))])

    def _traco(self, s, p, cam):
        """Traço de movimento atrás da nuvem quando o pônei anda (mais longo quanto mais rápido)."""
        v = abs(p.vx)
        if v < 1.0 or not p.no_chao and not p.flutter:
            return
        cx, cy = cam
        tras = -1 if p.vx > 0 else 1
        base = p.x + p.w / 2 + tras * 15 - cx
        chao = p.y + p.h - cy
        for i, dy in enumerate((-13, -8, -3)):
            comp = int(v * (6 + 3 * ((p.anim // 2 + i * 2) % 3)))
            x0 = base + tras * (1 + 4 * ((p.anim // 2 + i) % 2))
            x1 = x0 + tras * comp
            a, b = sorted((int(x0), int(x1)))
            y = int(chao + dy)
            s.fill((214, 120, 30), (a, y + 1, b - a + 1, 1))         # sombra embaixo do traço
            s.fill((255, 250, 214), (a, y, b - a + 1, 1))
            m = (b - a) // 2                                       # trecho mais forte junto da nuvem
            s.fill((255, 255, 255), (b - m if tras < 0 else a, y, m + 1, 1))

    def abrir_bloco(self, tx, ty):
        self.nivel.tiles[ty][tx] = BLOCO_USADO
        art._bloco_ovo(self.mapa, tx * TILE, ty * TILE, True)
        if self.mapa is not self.mapa_base:
            art._bloco_ovo(self.mapa_base, tx * TILE, ty * TILE, True)
        for k in range(3):                       # o bloco solta três moedas
            m = Item(tx * TILE + 8, ty * TILE, "moeda")
            m.solta, m.vy, m.vx = True, -3.5 - k * 0.6, (k - 1) * 0.7
            self.itens.append(m)
        self.audio.tocar("moeda")

    def ganhar_estrela(self):
        self.estrelas = min(30, self.estrelas + 1)
        self.audio.tocar("estrela")

    def _novo_pet(self):
        """O pet equipado na loja, ao lado do herói (None = sem pet)."""
        pet, coleira, chapeu = pets.visual(self.app.save) if getattr(self.app, "save", None) else ("nenhum",) * 3
        if pet == "nenhum":
            return None
        return pets.Pet(pet, coleira, chapeu, self.p.cx - 14, self.p.y + self.p.h)

    # ------------------------------------------------------------ quiz

    def abrir_quiz(self, bicho):
        if self.quiz_alvo is not None:
            return
        if isinstance(bicho, Gigante):
            if bicho.invuln or not bicho.fila:
                return
            idx = bicho.fila[0]
        else:
            if bicho.usado:
                return
            bicho.usado = True
            idx = bicho.idx
        self.quiz_alvo = bicho
        self.audio.tocar("abre_q")
        q = self.questoes[idx]
        rotulo = "GIGANTE" if isinstance(bicho, Gigante) else f"Bicho {idx + 1}/{len(self.questoes)}"
        self.app.abrir_quiz(q, lambda escolha, ok: self._resultado_quiz(idx, escolha, ok),
                            f"{self.contexto} · {rotulo}")

    def _resultado_quiz(self, idx, escolha, ok):
        bicho = self.quiz_alvo
        self.quiz_alvo = None
        self.respostas[idx] = (escolha, ok)
        if ok:
            self.flores += 1
            self.estrelas = min(30, self.estrelas + 3)
            self.particulas_burst(bicho.cx, bicho.y, (255, 255, 255), 16, 3)
            self.particulas_burst(bicho.cx, bicho.y, (255, 220, 80), 10, 2.5)
            self.texto(bicho.cx, bicho.y - 10, "+FLOR!", (255, 240, 120))
            self.ganhar_estrela()
            self.alma = min(hk.ALMA_MAX, self.alma + hk.ALMA_QUESTAO)
        else:
            self.texto(bicho.cx, bicho.y - 10, "ERROU!", (255, 120, 120))
            self.ferir(forcado=True, origem=bicho.cx)
        if isinstance(bicho, Gigante):
            bicho.fila.pop(0)
            bicho.invuln = 90
            bicho.bravo = 0 if ok else 240
            if not bicho.fila:
                bicho.vivo = False
                self.shake = 20
                self.audio.tocar("pisao")
                for _ in range(4):
                    self.particulas_burst(bicho.cx, bicho.y + 20, (255, 200, 220), 14, 3.5)
                self.texto(bicho.cx, bicho.y, "GIGANTE VENCIDO!", (255, 255, 160))
        else:
            bicho.vivo = False

    # ------------------------------------------------------------ dano

    def ferir(self, forcado=False, origem=None):
        p = self.p
        if p.invuln and not forcado:
            return
        p.invuln = 120
        lado = 1 if origem is None or p.cx > origem else -1
        p.vx, p.vy = 2.6 * lado, -3.5
        p.pound = p.dash_t = p.foco = 0
        self.shake = 8
        self.parada = 6
        self.ameaca = max(0.6, self.ameaca - 0.12)
        if p.bebe:
            p.bebe = False
            self.bolha = {"x": p.cx, "y": p.y - 10, "vx": -0.4 * lado, "t": 0}
            self.audio.tocar("bebe")
            self.estrelas = max(self.estrelas, 10)
        else:
            self.audio.tocar("dano")

    def morrer(self, motivo):
        if self.morte:
            return
        self.log_mortes = getattr(self, "log_mortes", []) + [(motivo, int(self.p.x))]
        if self.moedas > 0:                  # as moedas ficam com a sombra, no último chão firme
            hx, hy = self.p.historico[0] if self.p.historico else (self.p.cx, self.p.y + self.p.h)
            if motivo != "Caiu no buraco":
                hx, hy = self.p.cx, self.p.y + self.p.h
            self.sombra = hk.Sombra(hx, min(hy, H * TILE - 20), self.moedas)
            self.moedas = 0
        self.morte = 100
        self.motivo_morte = motivo
        self.audio.tocar("morte")

    def _respawn(self):
        self.vidas -= 1
        if self.vidas < 0:
            self._terminar(False)
            return
        x, y = self.checkpoint
        self.p = Heroi(x, y)
        self.p.invuln = 90
        self.pet = self._novo_pet()
        self.capa = hk.Capa(self.p.cx, self.p.y)
        self.bolha = None
        self.estrelas = 10.0
        self._centralizar_camera(True)

    def _terminar(self, venceu):
        n = len(self.questoes)
        acertos = sum(1 for e, ok in self.respostas.values() if ok)
        pontos = 0
        if venceu:
            pontos = int(min(30, self.estrelas)) + self.vermelhas * 4 + round(50 * acertos / max(1, n))
        res = {"venceu": venceu, "pontos": pontos, "acertos": acertos, "n": n,
               "respostas": self.respostas, "questoes": self.questoes,
               "estrelas": int(self.estrelas), "vermelhas": self.vermelhas,
               "moedas": self.moedas, "titulo": self.titulo}
        self.audio.parar_musica()
        save = getattr(self.app, "save", None)
        if save:                                  # a ameaça segue para a próxima fase, puxada de volta para o meio
            save.d["ameaca"] = round(0.8 * self.ameaca + 0.2, 3)
        if self.ao_terminar:
            self.ao_terminar(res)

    # ------------------------------------------------------------ loop

    def evento(self, e, inp):
        if self.pausado:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:     # toque/clique nas opções da pausa
                wy = e.pos[1] * LH / self.app.tela.get_height()
                y0, passo = self._pausa_layout()
                if y0 - 6 <= wy < y0 + passo:
                    self.pausado = False
                elif y0 + passo <= wy < y0 + 2 * passo + 6:
                    self.pausado = False
                    self._terminar(False)
                return
            if e.type == pygame.KEYDOWN or e.type == PADEVENT:
                if inp.foi("cima"):
                    self.pausa_sel = (self.pausa_sel - 1) % 2
                elif inp.foi("baixo"):
                    self.pausa_sel = (self.pausa_sel + 1) % 2
                elif inp.foi("ok") or inp.foi("pulo"):
                    if self.pausa_sel == 0:
                        self.pausado = False
                    else:
                        self.pausado = False
                        self._terminar(False)
                elif inp.foi("pausa"):
                    self.pausado = False
            return
        if inp.foi("pausa"):
            self.pausado = True
            self.pausa_sel = 0
            return
        if getattr(e, "angulo", None) is not None and not self.morte and not self.vitoria:
            p = self.p                                     # deslize na diagonal (toque): ataca para esse lado
            p.virado = 1 if math.cos(e.angulo) >= 0 else -1
            self._atacar()
            return
        if getattr(e, "acoes", None) and "dash" in e.acoes and not self.morte and not self.vitoria:
            self._dash(0)                                  # deslize na direção em que já corre (toque)
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3) and not self.morte and not self.vitoria:
            wx = self.app.para_mundo(e.pos)[0] + self.cam[0]
            lado = 1 if wx > self.p.cx else -1
            if e.button == 1:
                self.p.virado = lado
                self._atacar()
            else:
                self._dash(lado)

    @staticmethod
    def _pausa_layout():
        """(y da 1ª opção, altura de cada opção) do menu de pausa, em px do mundo."""
        return (LH // 2 - 10, 30) if edicao.RETRATO else (90, 16)

    def _atacar(self):
        """O botão que era a língua: com pet, o bote do pet; sem pet, o golpe de bastão de quem fica de pé."""
        p = self.p
        if p.pound:
            return
        if self.pet:
            if self.pet.bote(p):
                self.audio.tocar("miau")
            return
        if heroi.golpeia() and not p.lingua_t:
            p.lingua_t = 1
            self.audio.tocar("lingua")

    def _dash(self, dir_):
        """Dash do Hollow Knight: rápido e reto; um por pulo (recarrega no chão ou na parede)."""
        p = self.p
        if p.dash_t or p.dash_espera or p.pound or p.foco or (p.dash_no_ar and not p.no_chao):
            return
        if p.parede:
            p.virado = -p.parede
        elif dir_:
            p.virado = dir_
        p.dash_t, p.dash_espera = hk.DASH_QUADROS, hk.DASH_ESPERA
        p.dash_no_ar = not p.no_chao
        p.parede = p.parede_t = 0
        self.audio.tocar("arremesso")
        for _ in range(6):
            self.part.append([p.cx - p.virado * 6, p.y + p.h - random.uniform(2, 20), -p.virado * random.uniform(0.5, 1.6),
                              random.uniform(-0.3, 0.3), random.randint(8, 14), (60, 50, 90)])

    def _foco(self, p, inp, dir_):
        if (inp.seg("baixo") and p.no_chao and not dir_ and abs(p.vx) < 0.5 and self.alma >= hk.ALMA_FOCO
                and not p.lingua_t and not p.dash_t):
            p.foco += 1
            if p.foco % 3 == 0:
                hk.particulas_foco(self, p)
            if p.foco >= hk.FOCO_QUADROS:
                p.foco = 0
                self.alma -= hk.ALMA_FOCO
                self.vidas += 1
                self.audio.tocar("resgate")
                self.particulas_burst(p.cx, p.y + p.h / 2, (230, 236, 255), 16, 2.5)
                self.texto(p.cx, p.y - 16, "+1 VIDA", (220, 230, 255))
                self.parada = 5
        else:
            p.foco = 0

    def update(self, inp):
        if self.pausado:
            return
        if self.parada:                     # hit-stop: o mundo para por alguns quadros no impacto
            self.parada -= 1
            return
        self.tempo += 1
        if self.vitoria:
            self.vitoria += 1
            self.p.vx = 1.2
            self.p.vy = min(self.p.vy + GRAV, MAXQUEDA)
            self.p.fisica(self.nivel)
            if self.vitoria < 120 and self.vitoria % 3 == 0:
                self.confete(4)
            if self.vitoria % 25 == 5:
                self.brilho(self.p.cx, self.p.y - 6, (255, 236, 140), 8)
            if self.vitoria == 150:
                self._terminar(True)
            self._mover_particulas()
            return
        if self.morte:
            self.morte -= 1
            if self.morte > 60:
                self.p.y -= 1.5
            else:
                self.p.y += 3
            if self.morte == 0:
                self._respawn()
            return
        self._jogador(inp)
        cam = self.cam
        for e in self.ents:
            if -64 < e.x - cam[0] < LW + 64:
                e.update(self)
                if e.boneco is not None:
                    e.boneco.passo(e, self)
            if e.y > H * TILE + 64:
                e.vivo = False
        if self.novos:
            self.ents += self.novos
            self.novos = []
        for it in self.itens:
            it.update(self)
        if self.pet:
            self.pet.update(self.p)
        if self.sombra:
            self.sombra.update(self)
            if not self.sombra.vivo:
                self.sombra = None
        p = self.p
        alt = 31 if heroi.PERSONAGENS[heroi.VISUAL["personagem"]]["tipo"] == "pe" else 33
        cor = figurino.cachecol(self.clima.atual.id)
        self.capa.visivel = cor is not None
        if cor and cor != self.capa.cor:
            self.capa.cor, self.capa.escura = cor, tuple(int(c * 0.62) for c in cor)
        self.capa.update(p.cx - p.virado * 3, p.y + p.h - alt, p.vx, p.vy, self.tempo)
        for r in self.rastro_dash:
            r[6] -= 1
        self.rastro_dash = [r for r in self.rastro_dash if r[6] > 0]
        self._colisoes()
        self._bolha()
        self.ents = [e for e in self.ents if e.vivo]
        self.itens = [i for i in self.itens if i.vivo]
        self._mover_particulas()
        self._centralizar_camera()

    def _jogador(self, inp):
        p = self.p
        p.anim += 1
        p.invuln = max(0, p.invuln - 1)
        dir_ = (1 if inp.seg("dir") else 0) - (1 if inp.seg("esq") else 0)
        p.t_pulo, p.t_pouso, p.t_abaixo = p.t_pulo + 1, p.t_pouso + 1, p.t_abaixo + 1
        self._rastro_heroi(p)
        self._soneca(p)
        abaixa = inp.seg("baixo") and p.no_chao and not p.lingua_t and not p.pound
        if abaixa and not p.abaixado:
            p.t_abaixo = 0
            self.particulas_burst(p.cx, p.y + p.h - 2, (255, 236, 150), 4, 1.2)
        p.abaixado = abaixa
        # ataque: bote do pet (ou golpe de bastão); dash no botão do antigo ovo
        if inp.foi("lingua"):
            self._atacar()
        if inp.foi("ovo") or inp.foi("dash"):
            self._dash(dir_)
        # foco: ↓ parado no chão gasta alma e devolve uma vida (Hollow Knight)
        self._foco(p, inp, dir_)
        # pisão
        if inp.foi("baixo") and not p.no_chao and not p.pound and not p.lingua_t and not p.dash_t:
            p.pound = 1
        p.trava = max(0, p.trava - 1)
        p.dash_espera = max(0, p.dash_espera - 1)
        if p.dash_t:                                       # dash: reto, sem gravidade, deixando sombras
            p.dash_t -= 1
            p.vx, p.vy = p.virado * hk.DASH_VEL, 0
            if p.dash_t % 2 == 0:
                self.rastro_dash.append([p.x, p.y, p.virado, p.estado(), p.quadro(p.estado()), p.bebe, 12])
            if not p.dash_t:
                p.vx = p.virado * VMAX
        elif p.pound:
            p.pound += 1
            if p.pound < 12:
                p.vx = p.vy = 0
            else:
                p.vy = 8
        else:
            if p.trava:                                    # logo depois do pulo de parede o controle volta aos poucos
                dir_ = 0
            if dir_ and not p.lingua_t and not p.abaixado and not p.foco:
                if p.no_chao and p.vx * dir_ < 0:          # virada seca no chão (responde na hora)
                    p.vx *= 0.35
                p.vx += dir_ * (ACC if p.no_chao else ACC_AR)
                p.virado = dir_
            else:
                if p.no_chao:
                    p.vx -= math.copysign(min(abs(p.vx), ATRITO), p.vx)
            vmax = VMAX
            p.vx = max(-vmax - (1.2 if p.trava else 0), min(vmax + (1.2 if p.trava else 0), p.vx))
            # pulo com coyote time e buffer; pulo de parede quando está agarrado nela
            p.coyote = 7 if p.no_chao else max(0, p.coyote - 1)
            p.buffer_pulo = 8 if inp.foi("pulo") else max(0, p.buffer_pulo - 1)
            if p.buffer_pulo and p.parede_t and not p.coyote:
                lado = -p.parede
                p.vy = PULO * 0.95
                p.vx = lado * 3.0
                p.virado = lado
                p.trava = 10
                p.parede = p.parede_t = 0
                p.buffer_pulo = 0
                p.flutter_gasto = 0
                p.dash_no_ar = False
                p.t_pulo = 0
                self.audio.tocar("pulo")
                for _ in range(5):
                    self.part.append([p.cx - lado * 7, p.y + p.h - random.uniform(4, 18), lado * random.uniform(0.3, 1.2),
                                      random.uniform(-0.6, 0.3), random.randint(10, 16), (236, 226, 210)])
            elif p.buffer_pulo and p.coyote:
                p.vy = PULO
                p.coyote = p.buffer_pulo = 0
                p.flutter_gasto = 0
                p.t_pulo = 0
                self.audio.tocar("pulo")
                self._baforada(p, 6)
            if not inp.seg("pulo") and p.vy < -2 and not p.flutter:
                p.vy *= 0.6
            # flutter: segurar pulo caindo
            p.flutter = 0
            if inp.seg("pulo") and not p.no_chao and p.vy > -0.5 and p.flutter_gasto < FLUTTER_MAX and not p.parede:
                p.flutter = 1
                p.flutter_gasto += 1
                p.vy = max(p.vy - FLUTTER_FORCA - GRAV, -1.0)
                if p.flutter_gasto % 12 == 1:
                    self.audio.tocar("flutter")
            g = GRAV * (0.55 if inp.seg("pulo") and abs(p.vy) < 1.1 and not p.no_chao else 1)   # ápice mais leve
            p.vy = min(p.vy + g, MAXQUEDA)
            if p.parede and p.vy > 1.3:                   # deslizando na parede
                p.vy = 1.3
                if self.tempo % 4 == 0:
                    self.part.append([p.cx + p.parede * 7, p.y + p.h - 4, 0, -0.4, 10, (236, 226, 210)])
        estava_no_chao = p.no_chao
        pound_antes = p.pound
        bx, teto = p.fisica(self.nivel)
        # agarrado na parede: no ar, caindo e empurrando contra ela
        empurra = (1 if inp.seg("dir") else 0) - (1 if inp.seg("esq") else 0)
        if bx and not p.no_chao and empurra and not p.pound and not p.dash_t and p.vy > -0.5:
            p.parede, p.parede_t = empurra, 6
            p.dash_no_ar = False
        else:
            p.parede = 0
            p.parede_t = max(0, p.parede_t - 1)
        if bx and p.dash_t:
            p.dash_t = 0
        if p.no_chao and not estava_no_chao:
            p.t_pouso = 0
            p.dash_no_ar = False
            if not p.pound:
                self._baforada(p, 5)
        if teto and self.nivel.tile(*teto) == BLOCO_OVO:
            self.abrir_bloco(*teto)
        if p.no_chao:
            p.flutter_gasto = 0
            if p.pound:
                p.pound = 0
                self.shake = 10
                self.parada = 3
                self.audio.tocar("pisao")
                self.particulas_burst(p.cx, p.y + p.h, (200, 170, 130), 10)
                for e in self.ents:
                    if abs(e.cx - p.cx) < 40 and abs((e.y + e.h) - (p.y + p.h)) < 12:
                        self._acertar(e, "pisao")
        # golpe de bastão
        if p.lingua_t:
            p.lingua_t += 1
            if p.lingua_t >= 22:
                p.lingua_t = 0
        # espinho / buraco
        cx = int(p.cx // TILE)
        if self.nivel.tile(cx, int((p.y + p.h - 2) // TILE)) == ESPINHO:
            if pound_antes:                                # pogo: o pisão quica no espinho sem ferir
                p.vy, p.pound = -6.2, 0
                p.dash_no_ar = False
                self.parada, self.shake = 3, 4
                self.audio.tocar("quica")
                self.particulas_burst(p.cx, p.y + p.h, (255, 255, 255), 6)
            else:
                self.ferir(origem=p.cx - p.virado)
                p.vy = -5
        if p.y > H * TILE + 20:
            self.morrer("Caiu no buraco")
        p.historico.append((p.cx, p.y + p.h))
        if len(p.historico) > 80:
            p.historico.pop(0)
        # anéis
        if self.anel_meio[2] and abs(p.cx - self.anel_meio[0]) < 12 and p.y + p.h > self.anel_meio[1] - 60:
            self.anel_meio[2] = False
            self.checkpoint = (self.anel_meio[0], self.anel_meio[1])
            self.estrelas = min(30, self.estrelas + 10)
            self.audio.tocar("anel")
            self.texto(p.cx, p.y - 20, "+10 ESTRELAS", (255, 230, 120))
        if (not self.gigante or not self.gigante.vivo) and p.cx > self.anel_fim[0] - 6 and p.bebe:
            self.vitoria = 1
            self.audio.parar_musica()
            self.audio.tocar("fim")
            for _ in range(5):
                self.particulas_burst(self.anel_fim[0], self.anel_fim[1] - 30, (255, 150, 200), 12, 3)

    def _areas_golpe(self):
        """Três pontos ao longo do bastão girando (meio, quase ponta, ponta do arco)."""
        p = self.p
        (hx, hy), _ = self._mao_mundo()
        a = math.radians(_ang_golpe(p.lingua_t)) * p.virado
        return [(hx + r * math.sin(a), hy - r * math.cos(a)) for r in (10, 20, ALCANCE_GOLPE)]

    def _mao_mundo(self):
        p = self.p
        (mx, my), bast = heroi.mao(virado=p.virado)
        return (p.x + p.w / 2 - heroi.LARG / 2 + mx, p.y + p.h - heroi.ALT + my), bast

    def _desenhar_golpe(self, s, cam):
        """Bastão girando em volta da mão + rastro do arco."""
        p = self.p
        (hx, hy), bast = self._mao_mundo()
        hx, hy = hx - cam[0], hy - cam[1]
        a = _ang_golpe(p.lingua_t)
        if 5 < p.lingua_t <= 14:                 # rastro: do recuo até o ângulo atual
            for k in range(0, 9):
                ak = math.radians(a - k * 16) * p.virado
                if a - k * 16 < -45:
                    break
                for r, cor in ((ALCANCE_GOLPE, (255, 255, 255)), (ALCANCE_GOLPE - 4, (190, 230, 255))):
                    x, y = int(hx + r * math.sin(ak)), int(hy - r * math.cos(ak))
                    s.fill(cor, (x - 1, y - 1, 3 - k // 4, 3 - k // 4))
        if bast:
            img = pygame.transform.rotate(bast, -a * p.virado)
            off = pygame.math.Vector2(0, (bast.get_height() / 2 - PEGADA_GOLPE)).rotate(a * p.virado)
            c = (hx + off.x, hy + off.y)
            s.blit(img, img.get_rect(center=(int(c[0]), int(c[1]))))

    def _golpear(self, areas, como, ja=None):
        """Bastão ou bote do pet: abre o bicho-questão, derruba o germe (que vira moeda) e pega itens no caminho."""
        for e in self.ents:
            if not e.atingivel() or not any(rect_hit(tr, e.rect) for tr in areas):
                continue
            if ja is not None:
                if id(e) in ja:
                    continue
                ja.add(id(e))
            if isinstance(e, BichoQuestao):
                self.abrir_quiz(e)
                return
            if e.comestivel:
                e.vivo = False
                self.audio.tocar("acerto_inimigo")
                self.alma = min(hk.ALMA_MAX, self.alma + hk.ALMA_GOLPE)
                self.parada, self.shake = max(self.parada, 3), max(self.shake, 4)
                self.particulas_burst(e.cx, e.y + e.h / 2, (255, 255, 255), 10)
                self.particulas_burst(e.cx, e.y + e.h / 2, (255, 150, 60), 6, 2.6)
                m = Item(e.cx, e.y + e.h, "moeda")
                m.solta, m.vy = True, -3
                self.itens.append(m)
            else:
                self._acertar(e, "golpe")
            return
        for it in self.itens:
            if any(rect_hit(tr, it.rect) for tr in areas):
                self._pegar(it)

    def _acertar(self, e, como):
        if isinstance(e, BichoQuestao):
            self.abrir_quiz(e)
            return
        self.alma = min(hk.ALMA_MAX, self.alma + hk.ALMA_GOLPE)
        self.parada, self.shake = max(self.parada, 3), max(self.shake, 4)
        if e.ao_acertar(self, como):
            if not hasattr(e, "branco"):          # os monstros piscam em branco por conta própria
                e.pisca = 10
            return
        e.vivo = False
        self.ameaca = min(1.6, self.ameaca + 0.04)
        if hasattr(e, "ao_morrer"):
            e.ao_morrer(self)
        self.audio.tocar("acerto_inimigo")
        self.particulas_burst(e.cx, e.y + e.h / 2, (255, 255, 255), 8)
        self.particulas_burst(e.cx, e.y + e.h / 2, (255, 150, 60), 6, 2.6)      # respingo laranja, como no Hollow Knight
        self.estrelas = min(30, self.estrelas + 0)
        if random.random() < 0.3:
            self.itens.append(Item(e.cx, e.y + e.h, "estrela"))

    def _colisoes(self):
        p = self.p
        pr = p.rect
        # golpe de bastão (personagens de pé, sem pet)
        if p.lingua_t and heroi.golpeia() and 5 <= p.lingua_t <= 14:
            areas = [(x - 5, y - 5, 10, 10) for x, y in self._areas_golpe()]
            self._golpear(areas, "golpe")
        # bote do pet: as patas da frente acertam o primeiro bicho no caminho
        pet = self.pet
        if pet and pet.atacando and 4 <= pet.bote_t <= 14:
            self._golpear([pet.area()], "gato", pet.acertou)
        # inimigos
        for e in self.ents:
            if not e.atingivel() or not rect_hit(pr, e.rect):
                continue
            pisando = p.vy > 0 and (p.y + p.h) - e.y < 10
            if isinstance(e, BichoQuestao):
                if pisando or p.pound:
                    p.vy = -4.5
                    self.abrir_quiz(e)
                else:  # empurra de leve, sem dano: tocar no bicho não é errar
                    lado = -1 if p.cx < e.cx else 1
                    p.vx = 1.5 * lado
                    p.x += 2 * lado
                continue
            if p.pound:                                  # pogo: o pisão quica no inimigo (até no espinhento)
                if not e.espinhento:
                    self._acertar(e, "pisao")
                else:
                    self.parada, self.shake = 3, 4
                    self.audio.tocar("quica")
                p.pound, p.vy, p.dash_no_ar = 0, -5.6, False
            elif pisando and not e.espinhento:
                p.vy = -4.5
                p.dash_no_ar = False
                self._acertar(e, "pisao")
            elif not p.invuln:
                self.ferir(origem=e.cx)
        # itens
        for it in self.itens:
            if rect_hit(pr, it.rect):
                self._pegar(it)

    def _pegar(self, it):
        if not it.vivo:
            return
        it.vivo = False
        self.brilho(it.cx, it.y + 4, {"vermelha": (255, 150, 160), "estrela": (255, 250, 190)}.get(it.tipo, (255, 226, 110)),
                    8 if it.tipo != "moeda" else 5)
        if it.tipo == "moeda":
            self.moedas += 1
            self.audio.tocar("moeda")
            if self.moedas % 100 == 0:
                self.vidas += 1
                self.texto(it.cx, it.y, "1UP", (120, 255, 120))
        elif it.tipo == "vermelha":
            self.vermelhas += 1
            self.moedas += 1
            self.audio.tocar("vermelha")
            self.texto(it.cx, it.y, f"{self.vermelhas}/5", (255, 140, 150))
        elif it.tipo == "estrela":
            self.estrelas = min(30, self.estrelas + 1)
            self.audio.tocar("estrela")

    def _bolha(self):
        p = self.p
        if p.bebe:
            if self.estrelas < 10 and self.tempo % 60 == 0:
                self.estrelas += 1
            return
        b = self.bolha
        b["t"] += 1
        b["x"] += b["vx"] + math.sin(b["t"] * 0.05) * 0.3
        b["y"] += math.sin(b["t"] * 0.08) * 0.6 - 0.05
        b["y"] = max(self.cam[1] + 24, min(self.cam[1] + LH - 60, b["y"]))
        b["x"] = max(self.cam[0] + 20, min(self.cam[0] + LW - 20, b["x"]))
        if b["t"] % 40 == 0:
            self.estrelas -= 1
            if b["t"] % 90 == 0:
                self.audio.tocar("bebe")
        if self.estrelas <= 0:
            self.estrelas = 0
            nome = heroi.artigo_nome()
            self.morrer(f"{nome[0].upper()}{nome[1:]} foi levad{nome[0]} pela supervisão!")
            return
        if rect_hit(p.rect, (b["x"] - 12, b["y"] - 12, 24, 24)) and b["t"] > 30:
            p.bebe = True
            self.bolha = None
            self.audio.tocar("resgate")
            self.texto(p.cx, p.y - 20, "RESGATADO!", (180, 230, 255))

    def _mover_particulas(self):
        for f in self.fx:
            f[0] += f[2]
            f[1] += f[3]
            f[3] += f[8]
            f[2] *= 0.97
            if f[6] == "confete":
                f[2] += math.sin((self.tempo + f[5]) * 0.12) * 0.04
            f[4] -= 1
        self.fx = [f for f in self.fx if f[4] > 0]
        for pt in self.part:
            pt[0] += pt[2]
            pt[1] += pt[3]
            pt[3] += 0.1
            pt[4] -= 1
        self.part = [pt for pt in self.part if pt[4] > 0]
        for t in self.textos:
            t[1] -= 0.6
            t[4] -= 1
        self.textos = [t for t in self.textos if t[4] > 0]
        self.shake = max(0, self.shake - 1)

    def _centralizar_camera(self, instant=False):
        p = self.p
        alvo_x = p.cx - LW / 2 + p.virado * (LW * 0.22 if edicao.RETRATO else 28)   # em pé: mostra o caminho à frente
        alvo_y = p.y - LH * 0.55
        alvo_x = max(0, min(self.nivel.w * TILE - LW, alvo_x))
        alvo_y = max(0, min(H * TILE - LH, alvo_y))
        k = 1 if instant else 0.1
        self.cam[0] += (alvo_x - self.cam[0]) * k
        self.cam[1] += (alvo_y - self.cam[1]) * (1 if instant else 0.08)

    # ------------------------------------------------------------ desenho

    def draw(self, tela, fonte):
        s = self.mundo
        cx, cy = int(self.cam[0]), int(self.cam[1])
        if self.shake:
            cx += random.randint(-1, 1)
            cy += random.randint(-1, 1)
        self.clima.passo(cx)
        if self.clima.draw_ceu(s, cx):
            for nx, ny, esc in self.nuvens:
                x = (nx - cx * 0.1 - self.tempo * 0.05 * esc) % (LW + 60) - 50
                art.nuvem(s, x, ny * 0.5, esc * 0.8)
        for i, cam in enumerate(self.clima.atual.camadas):
            fator = (0.15, 0.3, 0.5)[i]
            ox = -int(cx * fator) % LW
            oy = int((H * TILE - LH - cy) * fator * 0.4)
            s.blit(cam, (ox - LW, oy))
            s.blit(cam, (ox, oy))
        self.clima.draw_meio(s, cx)
        s.blit(self.mapa, (-cx, -cy))
        cam = (cx, cy)
        if self.anel_meio[2]:
            s.blit(art.anel(self.tempo, True), (self.anel_meio[0] - 16 - cx, self.anel_meio[1] - 50 - cy))
        s.blit(art.anel(self.tempo), (self.anel_fim[0] - 16 - cx, self.anel_fim[1] - 50 - cy))
        for it in self.itens:
            if -20 < it.x - cx < LW + 20:
                it.draw(s, cam)
        for e in self.ents:
            if -64 < e.x - cx < LW + 64:
                pisca = getattr(e, "pisca", 0)
                if pisca:
                    e.pisca = pisca - 1
                if pisca % 4 < 2:
                    e.draw(s, cam)
        if self.sombra:
            self.sombra.draw(s, cam)
        self.clima.pos_mundo(s)                           # gótico: preto e branco (o herói vem depois, no figurino)
        frente = self.pet and self.pet.atacando           # no bote o pet passa na frente do herói
        if self.pet and not self.morte and not frente:
            self.pet.draw(s, cam)
        self._draw_heroi(s, cam)
        if frente and not self.morte:
            self.pet.draw(s, cam)
        if self.bolha:
            s.blit(art.bebe_bolha(self.bolha["t"]), (int(self.bolha["x"] - 13 - cx), int(self.bolha["y"] - 13 - cy)))
        for x, y, vx, vy, vida, cor in self.part:
            if vida > 8:
                s.fill(cor, (int(x - cx), int(y - cy), 2, 2))
            else:
                s.set_at((int(x - cx), int(y - cy)), cor)
        self._draw_fx(s, cx, cy)
        self.clima.draw_frente(s, cx, cy)
        for x, y, msg, cor, vida in self.textos:
            t = art.texto_px(msg, cor)
            s.blit(t, (int(x - cx - t.get_width() / 2), int(y - cy)))
        self._hud(s)
        tela.blit(pygame.transform.scale(s, tela.get_size()), (0, 0))

    def _draw_fx(self, s, cx, cy):
        for x, y, vx, vy, vida, vida0, forma, cor, _ in self.fx:
            x, y = int(x - cx), int(y - cy)
            if not (-6 < x < LW + 6 and -6 < y < LH + 6):
                continue
            k = vida / vida0
            if forma == "ponto":
                s.fill(cor, (x, y, 2 if k > 0.5 else 1, 2 if k > 0.5 else 1))
            elif forma == "brilho":
                r = 2 if k > 0.6 else 1
                s.fill(cor, (x - r, y, 2 * r + 1, 1))
                s.fill(cor, (x, y - r, 1, 2 * r + 1))
                if k > 0.6:
                    s.set_at((x, y), (255, 255, 255))
            elif forma == "coracao":
                if k > 0.4:
                    s.fill(cor, (x - 2, y - 1, 2, 2))
                    s.fill(cor, (x + 1, y - 1, 2, 2))
                    s.fill(cor, (x - 1, y, 3, 2))
                    s.set_at((x, y + 2), cor)
                else:
                    s.fill(cor, (x, y, 2, 2))
            elif forma == "floco":
                s.set_at((x, y), cor)
                if k > 0.5:
                    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                        s.set_at((x + dx, y + dy), cor)
            elif forma == "confete":
                fase = (vida // 6) % 3
                s.fill(cor, (x, y, (3, 2, 1)[fase], 2))
            elif forma == "z":
                s.blit(art.texto_px("z" if k > 0.5 else "Z", cor), (x, y))

    def _draw_heroi(self, s, cam):
        p = self.p
        cx, cy = cam
        for x, y, vir, est, q, bebe, vida in self.rastro_dash:        # sombras do dash
            spr = art.heroi(est, q, bebe, vir)
            sil = hk.silhueta(spr, (70, 56, 120), int(150 * vida / 12))
            s.blit(sil, (int(x + p.w / 2 - spr.get_width() / 2 - cx), int(y + p.h - spr.get_height() - cy)))
        if not self.morte and p.bebe and not (p.invuln and p.invuln % 6 < 3) and getattr(self.capa, "visivel", True):
            self.capa.draw(s, cam)
        if p.foco:                                         # foco: anel de luz que fecha sobre o herói
            k = p.foco / hk.FOCO_QUADROS
            c = (int(p.cx - cx), int(p.y + p.h / 2 - cy))
            r = int(26 - 16 * k)
            s.blit(climas.halo(18, (int(40 + 60 * k),) * 2 + (int(70 + 60 * k),)), (c[0] - 18, c[1] - 18),
                   special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(s, (240, 244, 255), c, r, 1)
            pygame.draw.circle(s, (180, 196, 255), c, r + 3, 1)
        if not (p.invuln and p.invuln % 6 < 3 and not self.morte):
            est = p.estado()
            if p.invuln > 96 and not self.morte:
                est = "dor"
            frame = p.quadro(est)
            self._traco(s, p, cam)
            cid = self.clima.atual.id                      # a roupa reage ao clima (figurino.py)
            heroi.vestir(figurino.cores(cid))
            heroi.trajar(figurino.traje(cid))
            spr = heroi.heroi(est, frame, p.bebe, p.virado, visual=figurino.visual(cid))
            heroi.vestir(None)
            heroi.trajar(None)
            sx = int(p.x + p.w / 2 - spr.get_width() / 2 - cam[0])
            sy = int(p.y + p.h - spr.get_height() - cam[1])
            s.blit(spr, (sx, sy))
            if p.bebe:
                figurino.desenhar(s, cid, spr, sx, sy, p.virado, self.tempo)
        if p.lingua_t and heroi.golpeia():
            self._desenhar_golpe(s, cam)

    def _hud(self, s):
        tx = art.texto_px
        hk.vaso_alma(s, 10, 23, self.alma, self.tempo, self.p.foco)
        s.blit(art.estrela(0), (3, 3))
        s.blit(tx(f"{int(self.estrelas):02d}", (255, 236, 120)), (15, 2))
        cab = pygame.transform.scale(art.cabeca_icone(), (15, 10))
        s.blit(cab, (36, 5))
        s.blit(tx(f"x{max(0, self.vidas)}"), (53, 2))
        s.blit(art.moeda(0), (71, 2))
        s.blit(tx(f"{self.moedas}", (255, 220, 96)), (80, 2))
        n = len(self.questoes)
        x0 = LW - 3 - n * 13
        for i in range(n):
            f = art.flor()
            r = self.respostas.get(i)
            if r is None:
                f = f.copy()
                f.set_alpha(60)
            elif not r[1]:
                f = f.copy()
                f.fill((255, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(f, (x0 + i * 13, 2))
        for i in range(5):
            m = art.moeda(0, True)
            if i >= self.vermelhas:
                m = m.copy()
                m.set_alpha(60)
            s.blit(m, (LW - 3 - 5 * 10 + i * 10, 16))
        W2 = LW // 2
        if not self.p.bebe and self.bolha and not self.pausado:
            t = tx(str(int(self.estrelas)), (255, 72, 72), escala=3)
            s.blit(t, (W2 - t.get_width() // 2, 18))
            t = tx(f"RESGATE {heroi.artigo_nome().upper()}!", (255, 255, 255))
            s.blit(t, (W2 - t.get_width() // 2, 56))
        if self.gigante and self.gigante.vivo and abs(self.gigante.cx - self.p.cx) < 220:
            t = tx(f"GIGANTE: {len(self.gigante.fila)} QUESTÕES", (255, 150, 150))
            s.blit(t, (W2 - t.get_width() // 2, 30))
        if self.morte:
            t = tx(getattr(self, "motivo_morte", ""), (255, 200, 200))
            s.blit(t, (W2 - t.get_width() // 2, LH // 2 - 10))
        if self.vitoria:
            t = tx("FASE CONCLUÍDA!", (255, 236, 120), escala=2)
            s.blit(t, (W2 - t.get_width() // 2, LH // 2 - 30))
        if self.pausado:
            v = pygame.Surface((LW, LH), pygame.SRCALPHA)
            v.fill((16, 16, 40, 170))
            s.blit(v, (0, 0))
            y0, passo = self._pausa_layout()
            t = tx("PAUSA", escala=2)
            s.blit(t, (W2 - t.get_width() // 2, y0 - 40))
            for i, op in enumerate(("CONTINUAR", "SAIR DA FASE")):
                cor = (255, 228, 96) if i == self.pausa_sel else (220, 220, 220)
                if edicao.RETRATO:            # celular: botões largos para o dedo
                    r = pygame.Rect(16, y0 + i * passo, LW - 32, passo - 6)
                    pygame.draw.rect(s, (60, 50, 90), r, border_radius=4)
                    pygame.draw.rect(s, cor, r, 1, border_radius=4)
                    t = tx(op, cor)
                    s.blit(t, (W2 - t.get_width() // 2, r.centery - t.get_height() // 2))
                else:
                    t = tx((">" if i == self.pausa_sel else " ") + op, cor)
                    s.blit(t, (W2 - 40, y0 + i * passo))
        else:
            t = tx(self.titulo.upper()[:min(52, (LW - 6) // 6)], (255, 255, 255))
            s.blit(t, (3, LH - 13))
