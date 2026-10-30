"""Caixinha de música — um toco na margem com uma caixinha em cima.

Interagir abre a tampa: uma estrelinha sobe de dentro e gira, notinhas sobem pelo ar, e a caixinha toca a
"Valsinha do Toco" (composição do Claude, tools/partitura_caixinha.py -> musicas_mirante/caixinha.ogg) num
canal próprio do mixer, com a trilha do Mirante abaixada enquanto ela toca. Interagir de novo fecha e para;
se a valsa acabar sozinha, a tampa fecha e a trilha volta ao volume de antes. Sem áudio, só a animação.
"""
import math
import os
import sys

import pygame

from . import Base
from ..mirante import GY, MADEIRA, MADEIRA_ESC, MARGEM_ESCURA, WW

NOME_PECA = "Valsinha do Toco"
VOL_CAIXINHA = 0.45          # a caixinha em si (a trilha do Mirante toca a 0,4)
VOL_TRILHA_BAIXA = 0.08      # a trilha enquanto a caixinha toca

CAIXA, CAIXA_ESC, CAIXA_CLARA = (78, 58, 118), (48, 36, 80), (112, 90, 160)
OURO, VELUDO = (210, 170, 96), (120, 40, 70)
NOTA_COR = (220, 206, 255)


def _achar_ogg():
    """Como a trilha do Mirante: ao lado do código ou na pasta do app (sys.path)."""
    raizes = [os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))] + [p for p in sys.path if p]
    for r in raizes:
        c = os.path.join(r, "musicas_mirante", "caixinha.ogg")
        if os.path.exists(c):
            return c
    return None


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.cx = WW * 0.505
        self.lugares = [("caixinha", self.cx, "abrir ou fechar a caixinha")]
        self.aberta = False
        self.a = 0.0                    # abertura da tampa (0 fechada, 1 aberta)
        self.som = None
        self.canal = None
        self.vol_antes = None           # volume da trilha antes de abaixar
        self.notas = []                 # [x, y, vida, fase] em coordenadas do mundo
        self.vezes = 0
        self.base_y = GY + 6            # o toco fica um pouco atrás de onde a Lume pisa
        # o Mirante só sai por _sair(); embrulho na instância para a valsa não seguir tocando lá fora
        sair = mirante._sair

        def _sair_com_caixinha():
            try:
                self._parar()
            except Exception:
                pass
            sair()
        mirante._sair = _sair_com_caixinha

    # ------------------------------------------------------------ som
    def _com_audio(self):
        au = self.mirante.app.audio
        return au.ok and not au.mudo

    def _tocar(self):
        if not self._com_audio():
            return False
        try:
            if self.som is None:
                ogg = _achar_ogg()
                if not ogg:
                    return False
                self.som = pygame.mixer.Sound(ogg)
                self.som.set_volume(VOL_CAIXINHA)
            self.canal = self.som.play(fade_ms=300)
            if self.canal is None:
                return False
            if self.vol_antes is None:
                self.vol_antes = pygame.mixer.music.get_volume()
            pygame.mixer.music.set_volume(min(self.vol_antes, VOL_TRILHA_BAIXA))
            return True
        except pygame.error:
            self.canal = None
            return False

    def _parar(self):
        if self.canal is not None:
            try:
                if self.canal.get_sound() is self.som:
                    self.canal.fadeout(400)
            except pygame.error:
                pass
            self.canal = None
        if self.vol_antes is not None:
            try:
                pygame.mixer.music.set_volume(self.vol_antes)
            except pygame.error:
                pass
            self.vol_antes = None

    # ------------------------------------------------------------ ganchos
    def interagir(self, nome):
        if self.aberta:
            self.aberta = False
            self._parar()
            return
        self.aberta = True
        self.vezes += 1
        if self._tocar():
            if self.vezes == 1:
                self.mirante._falar([f"“{NOME_PECA}”. Uma valsa curta que eu compus para esta caixinha: "
                                     "Sol maior, três tempos, um pouco mais de um minuto.",
                                     "Interaja de novo para fechar a tampa."])
            else:
                self.mirante._falar([f"A caixinha toca a “{NOME_PECA}”."])
        else:
            self.mirante._falar([f"A caixinha abre e toca a “{NOME_PECA}” tão baixinho que só a estrelinha ouve."])

    def update(self):
        alvo = 1.0 if self.aberta else 0.0
        self.a += (alvo - self.a) * 0.08
        if abs(alvo - self.a) < 0.01:
            self.a = alvo
        # a valsa acabou sozinha (ou o som foi desligado no meio): fecha e devolve a trilha
        if self.canal is not None:
            try:
                acabou = not self.canal.get_busy() or self.canal.get_sound() is not self.som
            except pygame.error:
                acabou = True
            if acabou or not self._com_audio():
                self._parar()
                self.aberta = False
        t = self.mirante.t
        if self.aberta and self.a > 0.6 and t % 34 == 0 and len(self.notas) < 6:
            self.notas.append([self.cx + (t // 34 % 3 - 1) * 3, self.base_y - 22, 0, t * 0.37])
        for n in self.notas:
            n[1] -= 0.18
            n[2] += 1
        self.notas = [n for n in self.notas if n[2] < 150]

    def draw_margem(self, m, cam):
        x = round(self.cx - cam)
        if not -30 < x < m.get_width() + 30:
            return
        t, a, y0 = self.mirante.t, self.a, self.base_y
        # toco: casca, raízes e o topo cortado com anéis
        pygame.draw.rect(m, MADEIRA_ESC, (x - 6, y0 - 9, 12, 10))
        pygame.draw.line(m, MADEIRA, (x - 3, y0 - 8), (x - 3, y0))
        pygame.draw.line(m, MADEIRA, (x + 2, y0 - 7), (x + 2, y0 - 1))
        for dx in (-8, -7, 6, 7):
            m.set_at((x + dx, y0), MADEIRA_ESC)
        pygame.draw.ellipse(m, MADEIRA, (x - 6, y0 - 11, 12, 4))
        pygame.draw.ellipse(m, MADEIRA_ESC, (x - 3, y0 - 10, 6, 2), 1)
        pygame.draw.line(m, MARGEM_ESCURA, (x - 7, y0 + 1), (x + 6, y0 + 1))
        # brilho quente de dentro da caixinha
        if a > 0.5:
            m.blit(self.mirante.halo[9], (x - 9, y0 - 26), special_flags=pygame.BLEND_RGB_ADD)
        # corpo da caixinha
        topo = y0 - 16
        pygame.draw.rect(m, CAIXA, (x - 5, topo, 10, 6))
        pygame.draw.rect(m, CAIXA_ESC, (x - 5, topo + 4, 10, 2))
        pygame.draw.line(m, OURO, (x - 5, topo + 1), (x + 4, topo + 1))
        m.set_at((x, topo + 3), OURO)                                   # fechadura
        # manivela do lado direito (gira enquanto toca)
        ang = t * 0.15 if self.aberta else 0.0
        pygame.draw.line(m, OURO, (x + 5, topo + 3), (x + 6, topo + 3))
        m.set_at((x + 7 + round(math.cos(ang)), topo + 3 + round(math.sin(ang))), OURO)
        # interior (veludo) aparece quando a tampa sobe
        if a > 0.15:
            pygame.draw.rect(m, VELUDO, (x - 4, topo - 1, 8, 1))
        # estrelinha que sobe e gira
        if a > 0.3:
            sy = topo - 1 - round(5 * a)
            pygame.draw.line(m, OURO, (x, sy + 1), (x, topo - 1))         # o pino que gira
            larg = abs(math.cos(t * 0.11)) if self.aberta else 1.0
            braco = round(2 * larg)
            frente = math.cos(t * 0.11) > 0
            cor = (255, 240, 190) if frente else (200, 176, 230)
            m.blit(self.mirante.halo[4], (x - 4, sy - 4), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.line(m, cor, (x - braco, sy), (x + braco, sy))
            pygame.draw.line(m, cor, (x, sy - 2), (x, sy + 2))
            if braco >= 1:
                m.set_at((x - braco + (1 if braco > 1 else 0), sy - 1), cor)
                m.set_at((x + braco - (1 if braco > 1 else 0), sy + 1), cor)
        # tampa: dobradiça atrás; fechada é uma placa, aberta fica de pé com o espelhinho
        alt = 2 + round(7 * a)
        if a < 0.15:
            pygame.draw.rect(m, CAIXA_CLARA, (x - 5, topo - 2, 10, 2))
            pygame.draw.line(m, OURO, (x - 5, topo - 1), (x + 4, topo - 1))
        else:
            recuo = round(2 * a)
            pygame.draw.polygon(m, CAIXA_CLARA, [(x - 5, topo - 1), (x + 4, topo - 1),
                                                 (x + 4 - recuo, topo - alt), (x - 5 + recuo, topo - alt)])
            pygame.draw.rect(m, (150, 170, 210), (x - 3 + recuo // 2, topo - alt + 2, 6 - recuo, max(1, alt - 4)))
            pygame.draw.line(m, OURO, (x - 5 + recuo, topo - alt), (x + 4 - recuo, topo - alt))
        # notinhas subindo
        for nx, ny, vida, f in self.notas:
            px = round(nx - cam + math.sin(vida * 0.06 + f) * 3)
            py = round(ny)
            k = min(1.0, vida / 15) * max(0.0, 1 - vida / 150)
            cor = tuple(int(c * k) for c in NOTA_COR)
            ad = pygame.BLEND_RGB_ADD
            m.fill(cor, (px, py, 2, 1), special_flags=ad)
            m.fill(cor, (px + 1, py - 3, 1, 3), special_flags=ad)
            m.fill(cor, (px + 2, py - 3, 1, 1), special_flags=ad)
