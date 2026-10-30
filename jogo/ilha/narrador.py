"""Narradora do resumo antes da fase: voz feminina calma lendo trecho a trecho, junto com o texto.

A voz é neural (Microsoft Edge TTS, via pacote edge-tts): o áudio de cada trecho é gerado uma vez,
guardado em cache (MP3, nome = hash do texto + voz) e depois toca sem internet. Pré-gerar tudo:
`venv/bin/python tools/narrar.py`. Sem edge-tts e sem cache (edições de venda), o botão não aparece.

Trocar a voz: VOZ / VELOCIDADE / TOM abaixo (amostras: tools/narrar.py --amostras)."""
import asyncio
import hashlib
import os
import re
import threading

import pygame

VOZ = "pt-BR-FranciscaNeural"
VELOCIDADE = "-12%"       # mais devagar que o normal: leitura de livro
TOM = "-4Hz"              # um pouco mais grave

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBUTIDA = os.path.join(_RAIZ, "narracao")          # áudios que vão junto com o jogo (se houver)


def _pasta_cache():
    from . import data
    return os.path.join(data.SAVE_DIR, "narracao")


try:
    import edge_tts
except ImportError:            # edições de venda: só tocam o que já vier gerado
    edge_tts = None

# --- texto escrito → texto falado -------------------------------------------------------------
_TROCAS = [
    (r"\b(\d+)/(\d+) h\b", r"de \2 em \2 horas"), (r"\be/ou\b", "e ou"), (r"\b1/3\b", "um terço"),
    (r"\b2/3\b", "dois terços"), (r"\b(\d+)/(\d+)\b", r"\1 por \2"),
    (r"<", " menor que "), (r">", " maior que "), (r"↑", " aumento de "), (r"↓", " queda de "), (r"~", " cerca de "),
    (r"\s\+\s", " mais "), (r"\+(?=[\s,;.]|$)", " positivo"),
    (r"≥", " maior ou igual a "), (r"≤", " menor ou igual a "), (r"→", ", "), (r"×", " vezes "),
    (r"±", " mais ou menos "), (r"(?<=\d)\s*–\s*(?=\d)", " a "), (r"\s–\s", ", "), (r"—", ", "),
    (r"\bmg/dL\b", " miligramas por decilitro"), (r"\bmEq/L\b", " miliequivalentes por litro"),
    (r"\bmL/kg\b", " mililitros por quilo"), (r"\bU/kg/h\b", " unidade por quilo por hora"),
    (r"\bmg/kg\b", " miligramas por quilo"), (r"\bUI/kg\b", " unidades por quilo"),
    (r"\bmL/min\b", " mililitros por minuto"), (r"\bng/mL\b", " nanogramas por mililitro"),
    (r"\bmmHg\b", " milímetros de mercúrio"), (r"\bcmH2O\b", " centímetros de água"),
    (r"\bmcg\b", " microgramas"), (r"\bmg\b", " miligramas"), (r"\bUI\b", " unidades"), (r"\bmL\b", " mililitros"),
    (r"\bL/min\b", " litros por minuto"), (r"/h\b", " por hora"), (r"/dia\b", " por dia"),
    (r"(?<=\d)\s*h\b", " horas"), (r"\b(\d+)/(\d+) h\b", r"\1 em \2 horas"),
    (r"\b1ª", "primeira"), (r"\b2ª", "segunda"), (r"\b3ª", "terceira"), (r"\b4ª", "quarta"),
    (r"\b1º", "primeiro"), (r"\b2º", "segundo"), (r"\b3º", "terceiro"),
    (r"\bvs\.?\b", "versus"), (r"\bex\.:", "por exemplo,"), (r"\(", ", "), (r"\)", ", "),
    (r"\s*/\s*", " ou "), (r"\s{2,}", " "), (r"\s+,", ","), (r",\s*,", ","),
]


def falado(texto):
    t = texto
    for rx, rep in _TROCAS:
        t = re.sub(rx, rep, t)
    return t.strip(" ,")


def _nome(texto):
    h = hashlib.sha1(f"{VOZ}|{VELOCIDADE}|{TOM}|{falado(texto)}".encode()).hexdigest()[:20]
    return h + ".mp3"


def arquivo(texto):
    """Caminho do áudio já gerado (embutido ou em cache) ou None."""
    n = _nome(texto)
    for pasta in (EMBUTIDA, _pasta_cache()):
        c = os.path.join(pasta, n)
        if os.path.exists(c) and os.path.getsize(c) > 0:
            return c
    return None


def pode_gerar():
    return edge_tts is not None


async def _gerar_um(texto, destino):
    tmp = destino + ".tmp"
    await edge_tts.Communicate(falado(texto), VOZ, rate=VELOCIDADE, pitch=TOM).save(tmp)
    os.replace(tmp, destino)


def gerar(texto):
    """Gera (bloqueante) e devolve o caminho; None se não der (sem edge-tts ou sem internet)."""
    c = arquivo(texto)
    if c or not pode_gerar():
        return c
    os.makedirs(_pasta_cache(), exist_ok=True)
    destino = os.path.join(_pasta_cache(), _nome(texto))
    try:
        asyncio.run(_gerar_um(texto, destino))
        return destino
    except Exception:
        return None


class Leitura:
    """Lê uma lista de trechos em sequência num canal próprio do mixer. `atual` = índice do trecho
    que está tocando (o Briefing destaca e rola até ele). Gera em segundo plano o que faltar."""

    def __init__(self, trechos):
        self.trechos = trechos
        self.caminhos = [arquivo(t) for t in trechos]
        self.atual = -1
        self.tocando = False
        self.preparando = False
        self.erro = False
        self._canal = None
        self._fio = None

    def disponivel(self):
        return pode_gerar() or all(self.caminhos)

    def _gerar_faltantes(self):
        for i, t in enumerate(self.trechos):
            if not self.tocando:
                return
            if not self.caminhos[i]:
                self.caminhos[i] = gerar(t)
                if not self.caminhos[i]:
                    self.erro = True
                    return

    def tocar(self, inicio=0):
        if not pygame.mixer.get_init():
            return
        self.tocando, self.erro, self.atual = True, False, inicio - 1
        if not all(self.caminhos) and (self._fio is None or not self._fio.is_alive()):
            self._fio = threading.Thread(target=self._gerar_faltantes, daemon=True)
            self._fio.start()
        self._proximo()

    def parar(self):
        self.tocando = False
        self.preparando = False
        if self._canal:
            self._canal.stop()

    def _proximo(self):
        nxt = self.atual + 1
        if nxt >= len(self.trechos):
            self.tocando = False
            self.atual = -1
            return
        c = self.caminhos[nxt]
        if not c:                      # ainda gerando: espera o update seguinte
            self.preparando = not self.erro
            if self.erro:
                self.tocando = False
            return
        self.preparando = False
        self.atual = nxt
        try:
            som = pygame.mixer.Sound(c)
            self._canal = som.play()
            if self._canal:
                self._canal.set_volume(1.0)
        except pygame.error:
            self._canal = None            # áudio corrompido: o update pula para o próximo

    def update(self):
        if not self.tocando:
            return
        if self.preparando or self._canal is None or not self._canal.get_busy():
            self._proximo()
