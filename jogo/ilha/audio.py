"""Efeitos sintetizados com numpy. Música de fundo: as faixas 16-bit em
musicas/ (OGG gerados por tools/compor.py a partir de tools/partituras.py), uma
por fase em rodízio embaralhado; sem arquivos, cai no loop sintetizado. Na edição pessoal
entram também as faixas que houver em musicas_pessoais/ (hoje vazia
), uma a cada 4 de musicas/."""
import glob
import os
import random
import re

import pygame

try:
    import numpy as np
except ImportError:          # Android: sem NumPy, os efeitos vêm prontos em efeitos/*.wav
    np = None

SR = 44100
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MUSICAS = os.path.join(_RAIZ, "musicas")
PASTA_PESSOAIS = os.path.join(_RAIZ, "musicas_pessoais")
PASTA_EFEITOS = os.path.join(_RAIZ, "efeitos")      # gerados por tools/exportar_efeitos.py
MUSICA_FIM = pygame.event.custom_type()
VOL_MUSICA, VOL_ABAIXADO = 0.45, 0.15


def _env(n, a=0.005, r=0.08):
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] = np.linspace(1, 0, nr)
    return e


def _tom(freq, dur, onda="quad", vol=0.3, glide=None):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = np.full(n, float(freq)) if glide is None else np.linspace(freq, glide, n)
    fase = 2 * np.pi * np.cumsum(f) / SR
    if onda == "quad":
        w = np.sign(np.sin(fase)) * 0.6
    elif onda == "tri":
        w = 2 / np.pi * np.arcsin(np.sin(fase))
    elif onda == "ruido":
        w = np.random.uniform(-1, 1, n)
    else:
        w = np.sin(fase)
    return w * _env(n, r=min(0.08, dur / 2)) * vol


def _seq(notas, onda="quad", vol=0.3):
    return np.concatenate([_tom(f, d, onda, vol) if f else np.zeros(int(SR * d)) for f, d in notas])


def _snd(arr):
    a = np.clip(arr, -1, 1)
    a = (a * 32000).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([a, a]) if _canais == 2 else a)


_canais = 1


def nota(n):  # n semitons a partir de A4
    return 440.0 * 2 ** (n / 12)


class Audio:
    def __init__(self, mudo=False):
        global _canais, SR
        self.ok = False
        self.mudo = mudo
        self.sons = {}
        self.musica = None
        self.faixas = self._rodizio()
        self.faixa_i = -1
        self.tocando = False
        self.atual = None                 # caminho da faixa tocando (a fase escolhe o clima por ela)
        self.abaixado = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SR, -16, 2, 1024)
            SR, _, _canais = pygame.mixer.get_init()
            self._gerar()
            self.ok = True
        except Exception:
            self.ok = False

    @staticmethod
    def _rodizio():
        """Ordem nova a cada sessão: as faixas CC0 novas (musicas/CREDITOS_CC0.txt) tocam antes das compostas antigas,
        e cada faixa pessoal entra só a cada 4 da lista principal."""
        def pasta(p):
            return glob.glob(os.path.join(p, "*.mp3")) + glob.glob(os.path.join(p, "*.ogg"))
        base = pasta(PASTA_MUSICAS)
        try:
            from . import edicao
            pessoais = [] if edicao.STEAM else pasta(PASTA_PESSOAIS)
        except ImportError:
            pessoais = []
        random.shuffle(base)
        random.shuffle(pessoais)
        try:
            creditos = open(os.path.join(PASTA_MUSICAS, "CREDITOS_CC0.txt"), encoding="utf-8").read()
        except OSError:
            creditos = ""
        base.sort(key=lambda f: os.path.splitext(os.path.basename(f))[0] + " —" not in creditos)
        if not base or not pessoais:
            return base + pessoais
        out = []
        for i, f in enumerate(base):
            out.append(f)
            if i % 4 == 3:
                out.append(pessoais[(i // 4) % len(pessoais)])
        return out

    def _gerar(self):
        if np is None:
            for arq in glob.glob(os.path.join(PASTA_EFEITOS, "*.wav")):
                self.sons[os.path.splitext(os.path.basename(arq))[0]] = pygame.mixer.Sound(arq)
            self.musica = None
            return
        s = self.sons
        s["pulo"] = _snd(_tom(300, 0.12, "quad", 0.18, glide=620))
        s["flutter"] = _snd(_seq([(500, 0.03), (560, 0.03)] * 3, "quad", 0.08))
        s["moeda"] = _snd(_seq([(nota(14), 0.05), (nota(19), 0.12)], "quad", 0.18))
        s["vermelha"] = _snd(_seq([(nota(14), 0.05), (nota(19), 0.05), (nota(26), 0.14)], "quad", 0.2))
        s["estrela"] = _snd(_seq([(nota(21), 0.04), (nota(26), 0.04), (nota(28), 0.08)], "tri", 0.3))
        s["lingua"] = _snd(_tom(700, 0.08, "sin", 0.25, glide=300))
        s["engolir"] = _snd(_seq([(260, 0.06), (180, 0.08)], "tri", 0.35))
        s["ovo"] = _snd(_seq([(nota(7), 0.04), (nota(12), 0.06)], "tri", 0.3))
        s["mirar"] = _snd(_tom(900, 0.03, "quad", 0.06))
        s["arremesso"] = _snd(_tom(500, 0.12, "sin", 0.3, glide=1100))
        s["quica"] = _snd(_tom(400, 0.04, "tri", 0.25))
        s["pisao"] = _snd(_tom(120, 0.18, "ruido", 0.25) + _tom(90, 0.18, "sin", 0.4))
        s["acerto_inimigo"] = _snd(_tom(800, 0.1, "quad", 0.15, glide=200))
        s["dano"] = _snd(_seq([(nota(0), 0.08), (nota(-5), 0.08), (nota(-9), 0.2)], "quad", 0.22))
        s["bebe"] = _snd(_seq([(nota(16), 0.1), (nota(12), 0.1)] * 2, "sin", 0.3))
        s["resgate"] = _snd(_seq([(nota(12), 0.06), (nota(16), 0.06), (nota(19), 0.06), (nota(24), 0.15)], "tri", 0.35))
        s["certo"] = _snd(_seq([(nota(12), 0.08), (nota(16), 0.08), (nota(19), 0.08), (nota(24), 0.25)], "quad", 0.18))
        s["errado"] = _snd(_seq([(nota(-2), 0.15), (nota(-8), 0.3)], "quad", 0.18))
        s["abre_q"] = _snd(_seq([(nota(19), 0.05), (nota(24), 0.05), (nota(31), 0.1)], "sin", 0.3))
        s["anel"] = _snd(_seq([(nota(12), 0.07), (nota(14), 0.07), (nota(16), 0.07), (nota(19), 0.07), (nota(24), 0.3)], "tri", 0.35))
        s["fim"] = _snd(_seq([(nota(12), 0.12), (nota(16), 0.12), (nota(19), 0.12), (nota(24), 0.12), (nota(19), 0.12), (nota(24), 0.5)], "quad", 0.18))
        s["morte"] = _snd(_seq([(nota(7), 0.12), (nota(3), 0.12), (nota(0), 0.12), (nota(-5), 0.4)], "tri", 0.3))
        s["menu"] = _snd(_tom(1200, 0.025, "quad", 0.08))
        s["grito"] = _snd(_tom(380, 0.16, "ruido", 0.12) * 0.6 + _tom(1150, 0.16, "quad", 0.07, glide=620))  # monstro avisa
        s["cuspe"] = _snd(_tom(260, 0.1, "ruido", 0.18) + _tom(180, 0.1, "sin", 0.2, glide=90))
        s["miau"] = _snd(np.concatenate([_tom(620, 0.07, "tri", 0.22, glide=900),        # bote do pet: "miau!" curto
                                         _tom(900, 0.12, "tri", 0.2, glide=520)]))
        self.musica = None if self.faixas else _snd(self._compor())

    def _compor(self):
        """Loop alegre em Fá maior: baixo em tercina + melodia de flauta."""
        bpm = 132
        b = 60 / bpm
        acordes = [(-4, 0, 3), (1, 5, 8), (-2, 1, 5), (3, 7, 10)] * 2   # F Bb Gm C
        mel = [12, 15, 17, 15, 12, None, 10, 12, 13, 17, 20, 17, 15, None, 13, 12,
               10, 13, 17, 13, 10, None, 8, 10, 15, 19, 22, 19, 17, 15, 14, 15]
        trilha = []
        baixo = []
        for i, ac in enumerate(acordes):
            for k in range(4):
                baixo.append(_tom(nota(ac[0] - 24 + (12 if k % 2 else 0)), b, "tri", 0.22))
            for k in range(4):
                n = mel[(i * 4 + k) % len(mel)]
                trilha.append(_tom(nota(n), b * 0.9, "sin", 0.12) + _tom(nota(n + 12), b * 0.9, "sin", 0.03)
                              if n is not None else np.zeros(int(SR * b * 0.9)))
                trilha.append(np.zeros(int(SR * b * 0.1)))
        m = np.concatenate(trilha)
        bx = np.concatenate(baixo)
        L = min(len(m), len(bx))
        return (m[:L] + bx[:L]) * 0.8

    def tocar(self, nome):
        if self.ok and not self.mudo and nome in self.sons:
            self.sons[nome].play()

    @staticmethod
    def nome(caminho):
        """'System Of A Down - Toxicity (Official HD Video) [id] [chiptune SNES].mp3' -> 'System Of A Down - Toxicity'"""
        n = os.path.splitext(os.path.basename(caminho))[0]
        n = re.sub(r"\s*\[[^\]]*\]", "", n)
        n = re.sub(r"\s*\((official|offical|2\d{3} remaster|remaster|hd|lyrics?)[^)]*\)", "", n, flags=re.I)
        return n.strip()

    def iniciar_musica(self, proxima=True):
        """Começa a música da fase; com faixas, avança no rodízio. Devolve o nome tocado (ou None)."""
        if not self.ok or self.mudo:
            return None
        if not self.faixas:
            if self.musica:
                self.musica.stop()
                self.musica.set_volume(0.35)
                self.musica.play(-1)
            return None
        if proxima or self.faixa_i < 0:
            self.faixa_i = (self.faixa_i + 1) % len(self.faixas)
        caminho = self.faixas[self.faixa_i]
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(VOL_ABAIXADO if self.abaixado else VOL_MUSICA)
            from .climas import VOLTAS, titulo
            pygame.mixer.music.play(VOLTAS.get(titulo(self.nome(caminho)), 0))   # faixa curta repete: o clima dura mais
            pygame.mixer.music.set_endevent(MUSICA_FIM)
            self.tocando = True
            self.atual = caminho
        except pygame.error:
            self.faixas.remove(caminho)
            return self.iniciar_musica(False) if self.faixas else None
        return self.nome(caminho)

    def fim_de_faixa(self):
        """Evento MUSICA_FIM: emenda a próxima faixa (ignora o fim causado por parar_musica)."""
        if self.tocando and not pygame.mixer.music.get_busy():
            return self.iniciar_musica()
        return None

    def abaixar(self, sim):
        """Volume menor enquanto a questão está aberta."""
        if sim != self.abaixado:
            self.abaixado = sim
            if self.ok and self.faixas:
                pygame.mixer.music.set_volume(VOL_ABAIXADO if sim else VOL_MUSICA)

    def parar_musica(self):
        self.tocando = False
        self.atual = None
        if self.ok:
            if self.musica:
                self.musica.stop()
            if self.faixas:
                pygame.mixer.music.stop()

    def alternar_mudo(self):
        self.mudo = not self.mudo
        if self.mudo:
            self.parar_musica()
            pygame.mixer.stop()
        return self.mudo
