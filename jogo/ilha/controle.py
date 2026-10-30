"""Controles (SNES USB e afins): detecção ao conectar, mapeamento automático
pelo banco do SDL quando ele conhece o modelo, assistente "aperte o botão"
para os desconhecidos, perfis salvos por GUID.

Os botões lógicos seguem o controle de SNES. A ligação com o SDL é
posicional (B = botão de baixo, A = direita, Y = esquerda, X = cima), então
um controle de Xbox/PlayStation também cai no lugar certo."""
import json
import os

import pygame

from . import data

PADEVENT = pygame.event.custom_type()
LOGICOS = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "X", "Y", "L", "R", "SELECT", "START"]
NOMES = {"UP": "CIMA", "DOWN": "BAIXO", "LEFT": "ESQUERDA", "RIGHT": "DIREITA", "A": "A", "B": "B",
         "X": "X", "Y": "Y", "L": "L", "R": "R", "SELECT": "SELECT", "START": "START"}
# Esquema do jogo: B pula; Y ataca (bote do pet: ação "lingua"); A e X dão dash (ação "ovo": os nomes ficaram antigos).
ACOES = {"UP": ["cima"], "DOWN": ["baixo"], "LEFT": ["esq"], "RIGHT": ["dir"],
         "B": ["pulo", "voltar"], "Y": ["lingua"], "A": ["ovo", "ok"], "X": ["ovo"],
         "START": ["pausa", "ok"], "SELECT": ["voltar", "corrigir"], "L": ["pgup"], "R": ["pgdn"]}
# Perfil genérico dos clones USB de SNES mais comuns (DragonRise 0079:0011 e parecidos)
PADRAO = {"X": ["b", 0], "A": ["b", 1], "B": ["b", 2], "Y": ["b", 3], "L": ["b", 4], "R": ["b", 5],
          "SELECT": ["b", 8], "START": ["b", 9], "UP": ["a", 1, -1], "DOWN": ["a", 1, 1],
          "LEFT": ["a", 0, -1], "RIGHT": ["a", 0, 1]}
# Clones de SNES com layout já conhecido (vendor:product) -> funcionam sem assistente
CONHECIDOS = {"081f:e401": ("clone USB de SNES", PADRAO), "0079:0011": ("clone USB de SNES", PADRAO)}
ARQ = os.path.join(data.SAVE_DIR, "controles.json")


def vid_pid(guid):
    """GUID do SDL (Linux): bytes 4-5 = vendor, 8-9 = product, little-endian."""
    try:
        v = guid[10:12] + guid[8:10]
        p = guid[18:20] + guid[16:18]
        return f"{v}:{p}".lower()
    except Exception:
        return ""
REPETIR = {"UP", "DOWN", "LEFT", "RIGHT"}


def _sdl_para_binding(s):
    s = s.strip()
    if not s:
        return None
    sinal = 0
    if s[0] in "+-":
        sinal = -1 if s[0] == "-" else 1
        s = s[1:]
    s = s.rstrip("~")
    try:
        if s.startswith("b"):
            return ["b", int(s[1:])]
        if s.startswith("h"):
            hat, mask = s[1:].split(".")
            mask = int(mask)
            dx = 1 if mask & 2 else (-1 if mask & 8 else 0)
            dy = 1 if mask & 1 else (-1 if mask & 4 else 0)
            return ["h", int(hat), dx, dy]
        if s.startswith("a"):
            return ["a", int(s[1:]), sinal or 1]
    except ValueError:
        return None
    return None


def perfil_do_sdl(indice):
    """Converte o mapeamento do SDL GameController (se existir) para o perfil SNES."""
    try:
        from pygame._sdl2 import controller as ctl
        ctl.init()
        if not ctl.is_controller(indice):
            return None
        m = ctl.Controller(indice).get_mapping()
    except Exception:
        return None
    pos = {"a": "B", "b": "A", "x": "Y", "y": "X", "leftshoulder": "L", "rightshoulder": "R",
           "back": "SELECT", "start": "START", "dpup": "UP", "dpdown": "DOWN", "dpleft": "LEFT", "dpright": "RIGHT"}
    try:
        from . import edicao
        rotulo = edicao.STEAM            # edição Steam: nome lógico = letra impressa no controle (Xbox/Deck)
    except ImportError:
        rotulo = False
    if rotulo:
        pos.update({"a": "A", "b": "B", "x": "X", "y": "Y"})
    perfil = {}
    for k, logico in pos.items():
        if k in m:
            b = _sdl_para_binding(m[k])
            if b:
                perfil[logico] = b
    for eixo, (neg, posi) in (("leftx", ("LEFT", "RIGHT")), ("lefty", ("UP", "DOWN"))):
        if eixo in m:
            b = _sdl_para_binding(m[eixo])
            if b and b[0] == "a":
                # direcional digital já mapeado: o analógico entra como alternativa ("UP~")
                for lg, sinal in ((neg, -1), (posi, 1)):
                    perfil[lg if lg not in perfil else lg + "~"] = ["a", b[1], sinal]
    essenciais = {"A", "B", "START", "UP", "DOWN", "LEFT", "RIGHT"}
    return perfil if essenciais <= set(perfil) else None


def eh_sensor(nome):
    """O SDL do Android expõe o acelerômetro (e às vezes o giroscópio) como joystick: não é controle."""
    n = (nome or "").lower()
    return any(k in n for k in ("accelerometer", "acelerômetro", "gyro", "sensor"))


class Pad:
    def __init__(self):
        self.perfis = {}
        try:
            self.perfis = json.load(open(ARQ, encoding="utf-8"))
        except Exception:
            pass
        self.disp = {}       # instance_id -> {joy, map, prev, rep}

    def salvar_perfil(self, joy, mapa):
        # remapear não apaga o analógico alternativo ("UP~"), se ele não colidir com o novo mapa
        for d in self.disp.values():
            if d["joy"].get_guid() == joy.get_guid():
                for lg, b in d["map"].items():
                    if lg.endswith("~") and b not in mapa.values():
                        mapa.setdefault(lg, b)
        self.perfis[joy.get_guid()] = {"nome": joy.get_name(), "map": mapa}
        os.makedirs(os.path.dirname(ARQ), exist_ok=True)
        with open(ARQ, "w", encoding="utf-8") as f:
            json.dump(self.perfis, f, ensure_ascii=False, indent=1)
        for d in self.disp.values():
            if d["joy"].get_guid() == joy.get_guid():
                d["map"] = mapa

    def adicionar(self, indice):
        """Abre o controle; devolve (joystick, precisa_configurar, origem do mapa)."""
        joy = pygame.joystick.Joystick(indice)
        if eh_sensor(joy.get_name()):
            raise pygame.error("sensor do celular, não é controle")
        guid = joy.get_guid()
        if guid in self.perfis:
            mapa, precisa, origem = self.perfis[guid]["map"], False, "perfil salvo"
        elif vid_pid(guid) in CONHECIDOS:
            nome, m = CONHECIDOS[vid_pid(guid)]
            mapa, precisa, origem = dict(m), False, nome
        else:
            sdl = perfil_do_sdl(indice)
            if sdl:
                mapa, precisa, origem = sdl, False, "reconhecido automaticamente"
            else:
                mapa, precisa, origem = dict(PADRAO), True, "desconhecido"
        self.disp[joy.get_instance_id()] = {"joy": joy, "map": mapa, "prev": set(), "rep": {}}
        return joy, precisa, origem

    def remover(self, instance_id):
        d = self.disp.pop(instance_id, None)
        return d["joy"].get_name() if d else None

    def conectados(self):
        return [d["joy"] for d in self.disp.values()]

    @staticmethod
    def _ativo(joy, b):
        try:
            if b[0] == "b":
                return b[1] < joy.get_numbuttons() and joy.get_button(b[1])
            if b[0] == "a":
                return b[1] < joy.get_numaxes() and joy.get_axis(b[1]) * b[2] > 0.5
            if b[0] == "h":
                if b[1] >= joy.get_numhats():
                    return False
                hx, hy = joy.get_hat(b[1])
                return (b[2] and hx == b[2]) or (b[3] and hy == b[3])
        except pygame.error:
            return False
        return False

    def _estado(self, d):
        return {lg.rstrip("~") for lg, b in d["map"].items() if b and self._ativo(d["joy"], b)}

    def frame(self, agora_ms):
        """Eventos PADEVENT para botões recém-apertados (+ auto-repetição no direcional)."""
        evs = []
        for d in self.disp.values():
            atual = self._estado(d)
            for lg in atual - d["prev"]:
                evs.append(pygame.event.Event(PADEVENT, botao=lg))
                d["rep"][lg] = agora_ms + 380
            for lg in atual & d["prev"]:
                if lg in REPETIR and agora_ms >= d["rep"].get(lg, 1 << 62):
                    evs.append(pygame.event.Event(PADEVENT, botao=lg))
                    d["rep"][lg] = agora_ms + 90
            d["prev"] = atual
        return evs

    def segurando(self, acao):
        for d in self.disp.values():
            for lg in d["prev"]:
                if acao in ACOES.get(lg, ()):
                    return True
        return False

    def neutro(self, joy):
        try:
            if any(joy.get_button(i) for i in range(joy.get_numbuttons())):
                return False
            if any(joy.get_hat(i) != (0, 0) for i in range(joy.get_numhats())):
                return False
        except pygame.error:
            return True
        return True
