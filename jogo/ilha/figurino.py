"""Figurino: a roupa do herói reage ao clima da fase (climas.py).

Quem monta (o Doutor, e quem usa o mesmo desenho de cavaleiro) troca de TRAJE inteiro, desenhado no próprio sprite
(trajes.py): capa de chuva amarela com capuz, parka, safári, havaiana, astronauta, escafandro, bombeiro, mágico,
quimono, pijama, mineiro, sobretudo e, no clima gótico, Robert Smith. Os outros personagens ainda não têm modelos
próprios: por enquanto só a cor da roupa muda com o clima (sem acessórios colados por cima).

Também aqui: cores trocadas na paleta (heroi.vestir: no gótico, pônei de crina preta e nuvem escura), a cor do
cachecol que voa (hk.Capa; some quando o traje já tem capa, capuz ou capacete) e a lanterna do mineiro, que acende
um facho para a frente no estilo do farol."""
import math

import pygame

from . import heroi, trajes

# clima → roupa (para quem não tem traje), nuvem e cores da paleta (valem para todos)
FIGURINO = {
    "chuva": dict(roupa="capa_chuva"), "tempestade": dict(roupa="capa_chuva"), "neve": dict(roupa="vermelho"),
    "aurora": dict(roupa="azul"), "noite": dict(roupa="roxo"), "floresta": dict(roupa="verde_folha"),
    "outono": dict(roupa="vinho"), "cerejeira": dict(roupa="rosa"), "deserto": dict(roupa="bege"),
    "mar": dict(roupa="turquesa"), "espaco": dict(roupa="branco"), "vulcao": dict(roupa="laranja"),
    "praia": dict(roupa="laranja"), "carnaval": dict(roupa="roxo"), "cristal": dict(roupa="roxo"),
    "frota": dict(roupa="dourado"), "samurai": dict(roupa="laca"), "neon": dict(roupa="amarelo_neon"),
    "colonia": dict(roupa="aco"), "runico": dict(roupa="oliva"), "reino": dict(roupa="prata"),
    "gotico": dict(roupa="luto", nuvem="chumbo",
                   cores={"h": (14, 12, 18), "j": (44, 40, 52), "d": (8, 6, 10), "F": (238, 234, 240),
                          "f": (198, 190, 206), "N": (8, 6, 12), "M": (200, 12, 36), "B": (26, 22, 30),
                          "b": (14, 12, 18), "m": (40, 36, 48), "l": (70, 64, 80), "z": (210, 206, 214)}),
}
# cachecol que voa atrás (hk.Capa): None = o traje não usa
CACHECOL_TRAJE = {"parka": (240, 240, 250), "sobretudo": (236, 140, 40), "cure": (18, 14, 22), "safari": None,
                  "guarda": None, "praia": None, "bombeiro": None, "magico": None, "quimono": None, "pijama": None,
                  "mineiro": None, "capa_chuva": None, "astronauta": None, "escafandro": None,
                  "frota": None, "samurai": None, "neon": None, "fuzileiro": None, "patrulheiro": None,
                  "paladino": (44, 72, 180)}                      # a capa azul do paladino voa atrás
CACHECOL_CLIMA = {"chuva": (248, 204, 40), "tempestade": (248, 204, 40), "neve": (240, 240, 250),
                  "aurora": (120, 230, 170), "outono": (236, 140, 40), "gotico": (18, 14, 22),
                  "samurai": (240, 236, 228), "neon": (255, 60, 180), "reino": (44, 72, 180), "frota": None,
                  "colonia": None, "runico": (112, 76, 42)}


def _monta():
    return heroi.PERSONAGENS[heroi.VISUAL["personagem"]]["tipo"] == "monta"


def traje(cid):
    """Nome do traje do clima para o personagem atual (só quem monta tem trajes por enquanto)."""
    return trajes.POR_CLIMA.get(cid) if _monta() else None


def visual(cid):
    f = FIGURINO.get(cid, {})
    v = dict(heroi.VISUAL)
    if not traje(cid) and f.get("roupa") in heroi.ROUPAS:
        v["roupa"] = f["roupa"]
    if f.get("nuvem") in heroi.NUVENS:
        v["nuvem"] = f["nuvem"]
    return v


def cores(cid):
    return FIGURINO.get(cid, {}).get("cores")


def cachecol(cid):
    """Cor do cachecol que voa (None = não desenhar)."""
    t = traje(cid)
    if t:
        return CACHECOL_TRAJE.get(t)
    return CACHECOL_CLIMA.get(cid, (214, 52, 66))


def desenhar(s, cid, spr, x, y, virado, t):
    """Efeitos de luz do traje por cima do herói já desenhado em (x, y): a lanterna do capacete de mineiro, o visor
    e os implantes do traje neon, a runa do patrulheiro e o brilho da armadura do paladino."""
    nome = traje(cid)
    if nome not in ("mineiro", "neon", "patrulheiro", "paladino", "fuzileiro"):
        return
    from .climas import _cone_girado, halo
    m = pygame.mask.from_surface(spr, 1)
    topo = next((yy for yy in range(m.get_size()[1]) if any(m.get_at((xx, yy)) for xx in range(m.get_size()[0]))), 0)
    if nome != "mineiro":
        add = pygame.BLEND_RGB_ADD
        frente = x + (24 if virado > 0 else spr.get_width() - 24)
        pisca = 0.75 + 0.25 * math.sin(t * 0.15)
        if nome in ("neon", "fuzileiro"):          # visor ciano / laranja brilhando
            cor = (20, 70, 80) if nome == "neon" else (80, 46, 10)
            s.blit(halo(6, tuple(int(v * pisca) for v in cor)), (frente - 6, y + topo + 3), special_flags=add)
        elif nome == "patrulheiro":                # runa do peito
            s.blit(halo(5, (int(80 * pisca), int(40 * pisca), 6)), (frente - 8, y + topo + 23), special_flags=add)
        else:                                      # paladino: um brilho dourado suave em volta
            r = 16
            s.blit(halo(r, (int(36 * pisca), int(30 * pisca), 10)), (frente - 4 - r, y + topo + 14 - r), special_flags=add)
        return
    lx = x + (24 if virado > 0 else spr.get_width() - 24)
    ly = y + topo + 2
    pisca = 0.85 + 0.15 * math.sin(t * 0.2)
    g, bx, by = _cone_girado(70, 0.22, (int(70 * pisca), int(66 * pisca), int(40 * pisca)), -90 * virado + 4 * virado)
    s.blit(g, (int(lx - bx), int(ly - by)), special_flags=pygame.BLEND_RGB_ADD)
    s.blit(halo(5, (120, 110, 60)), (lx - 5, ly - 5), special_flags=pygame.BLEND_RGB_ADD)
