"""Protagonista: o Doutor (cabelo cacheado, óculos redondos, jaleco, gravata e cachecol
arco-íris) montado num pônei branco de crina rosa e lilás, no traço dos 16 bits.
Desenho original, pixel a pixel em ASCII. Toque anime/Disney (2026-11-09): olhos grandes com
reflexo (E) e brilho (J), bochechas, sombra dura do lado direito (luz de cima à esquerda), caras
exageradas na dor (">_<", "X_X", boca escancarada) e squash & stretch do grupo montaria + cavaleiro
(`esq` em _pose) no pulo, queda, abaixar e pouso — tamanho do sprite, mão e hitbox não mudam.

Partes: pônei sem pernas (com variantes de boca aberta, piscada e susto), sela, o Doutor
sentado (o cachecol ondula) e, no lugar das patas, uma nuvem dourada que estica, achata e
pulsa conforme o estado.

Personagens e itens (loja.py vende, o save guarda): PERSONAGENS (todos sentados na montaria como o
Doutor; tipo "pe" = cabeça e corpo próprios, desenhados sentados no pônei), NUVENS (paleta + efeito), BASTOES (desenhados por código) e ROUPAS
(cor da camisa/pijama). equipar() escolhe o visual do jogo; heroi(..., visual=) desenha outro
(prévia da loja) sem mexer no equipado."""
import math

import pygame

PAL = {
    "K": (20, 16, 28),
    "G": (60, 196, 60), "L": (128, 236, 96), "H": (206, 255, 160), "g": (26, 128, 44),
    "W": (255, 255, 255), "w": (200, 208, 222), "E": (255, 255, 255),
    "R": (232, 48, 52), "P": (255, 140, 120), "r": (150, 20, 36),
    "O": (248, 132, 16), "Y": (255, 208, 80), "o": (172, 70, 16),
    # pônei: branco com sombra azulada, crina rosa/lilás, focinho rosado, cascos
    "s": (150, 160, 188), "m": (250, 160, 206), "l": (196, 156, 244), "z": (246, 214, 224), "q": (112, 100, 128),
    # Doutor
    "h": (128, 78, 42), "j": (186, 124, 66), "d": (78, 44, 26),
    "F": (252, 210, 172), "f": (222, 152, 112), "N": (150, 104, 54), "M": (170, 56, 72), "J": (76, 138, 104),
    "U": (176, 148, 226), "p": (98, 80, 92), "B": (126, 74, 40), "b": (80, 44, 24),
    # arco-íris (cachecol e gravata), uma cor por linha
    "a": (240, 70, 80), "c": (255, 150, 60), "e": (255, 226, 80), "i": (110, 210, 110),
    "n": (90, 160, 250), "v": (170, 110, 230),
}

# pônei inteiro sem as pernas (cabeça, pescoço com crina, corpo, cauda), virado à direita.
# Toque anime: olho grande (5×5) com dois reflexos e cílio, topete caindo na testa, bochecha rosada,
# sorriso em U, cauda erguida e ondulada; luz de cima à esquerda (sombra w/s embaixo e no peito).
PONEI = """
....................KK.........
...................KzWK........
.................KKmlmmKK......
...............KKmmlmlmWWK.....
..............KmmlmlmKKKKWK....
.............KmmlmmWKEEKKWWK...
.............KmlmmlWKEKKKWWWK..
............KmmlmmWWKqKEKWWWWK.
............KmlmlWWWWKKKWWzzzzK
...........KmmlmWWWWWWWWmzzzKzK
...KK......KmlmmwWWWWKWWWKzzzzK
..KmlK..KKKKKmlmwwWWWwKKKwzzzK.
.KmlmlKWWWWWWmlWwwWWWK..KKKKK..
KmlmlKWWWWWWWWmWwwWWWK.........
KmlmlKWWWWWWWWWWwwWWWWK........
KmllmKWWWWWWWWWWWwWWWWWK.......
.KmlmKwWWWWWWWWWWWWWWWWWK......
.KmlKwwWWWWWWWWWWWWWWWWWK......
.KmlKwwwWWWWWWWWWWWWWWWwK......
..KmKswwwWWWWWWWWWWWWWwwK......
..KlKsswwwwwwwwwwwwwwwwsK......
...K.KKKKKKKKKKKKKKKKKKK.......
""".split()


def _troca(rows, mudancas):
    """mudancas: {linha: texto completo}"""
    out = list(rows)
    for k, t in mudancas.items():
        out[k] = t
    return out


def _olho(rows, *linhas, x0=20, y0=4):
    """Troca o bloco do olho da montaria (5 colunas a partir de x0, a partir da linha y0) pelas linhas dadas."""
    out = [list(r) for r in rows]
    for k, t in zip(range(y0, y0 + len(linhas)), linhas):
        out[k][x0:x0 + 5] = t
    return ["".join(r) for r in out]


# boca aberta com a língua de fora (golpe/mirar): queixo cai e a língua pende
PONEI_BOCA = _troca(PONEI, {
    10: "...KK......KmlmmwWWWWWWWzKKKKKK",
    11: "..KmlK..KKKKKmlmwwWWWKKKKMMMMMK",
    12: ".KmlmlKWWWWWWmlWwwWWWKKzzzMMPK.",
    13: "KmlmlKWWWWWWWWmWwwWWWK.KKKKKKK.",
})
PONEI_PISCA = _olho(PONEI, "mWWWW", "WWWWW", "WKKKW", "KWWWK", "WWWWW")     # olho fechado feliz (arco)
# dor: olho apertado ">" e boca aberta no berro
PONEI_SUSTO = _troca(_olho(PONEI, "mWWWW", "KKWWW", "WKKWW", "KKWWW", "WWWWW"), {
    10: "...KK......KmlmmwWWWWWWWzKKKKKK",
    11: "..KmlK..KKKKKmlmwwWWWKKKKMMMMKK",
    12: ".KmlmlKWWWWWWmlWwwWWWK..KzzzzK.",
    13: "KmlmlKWWWWWWWWmWwwWWWK...KKKK..",
})
SELA = """
.KKKKKKK.
KRPRRRRRK
KRRRRRRRK
KWWWWWWWK
.KrrrrrK.
""".split()
# o Doutor sentado; linhas 15-20 do cachecol trocam a cada quadro. Rosto anime: óculos redondos grandes
# (armação N) com olhos de 3×3 (branco E atrás, íris verde J com pupila K e reflexo E em cima), cachos com
# luz j em cima à esquerda e sombra d à direita, bochechas P.
DOUTOR = """
...KKK..KKK.....
..KjjhKKjjhK....
.KjhhhhhhhhhhK..
KjhhhhjhhhhhhhK.
KhhhhhhhhhhdhdK.
KhhhhdhhFFFFhdK.
KhhhhhhFFFFFFK..
.KhhhfFNNNFNNNK.
.KhhffNEEJNEEJNf
.KhhffNEJKFEJKNf
.KhhffNEJJFEJJNf
..KhfFFNNNFNNNK.
..KhfFPFFFMMPK..
...KffffFFFFK...
....KKKKKKKK....
.aaaKWWUUaUWWK..
bbbbKWWUUbUWWWK.
cccKWWWWUcUWWWK.
.ddKWWWWWdWWwFFK
..eKWWWWWWWWwFFK
...KwWWWWWWWwKK.
...KwwwwwwwwwK..
...KpppppppppK..
....KKKKKpppK...
.........KppK...
.........KppK...
........KBBBBK..
........KKKKKK..
""".split()
DOUTOR = [l.replace("b", "c").replace("d", "i") if 15 <= k <= 19 else l for k, l in enumerate(DOUTOR)]
# cachecol: 2 quadros de ondulação (só as colunas à esquerda do jaleco)
CACHECOL = [
    ["..aaa", "aaccc", "ccee.", ".eei.", "..in.", "...v."],
    [".aaa.", "accc.", "cceee", ".eii.", "..nn.", "..v.."],
]
# dor: os óculos pulam para a testa, olhos ">_<" bem visíveis e boca de berro em trapézio (lábio M, fundo r);
# a linha 12 mantém "KMK": trajes.py procura por ela para escolher a cara de susto dos desenhos inteiros
DOUTOR_SUSTO_ROSTO = {5: "KhhhhdhNNNFNNNK.", 6: "KhhhhhhNFNFNFNK.", 7: ".KhhhfFFFFFFFFK.",
                      8: ".KhhffFKFFFFFKFf", 9: ".KhhffFFKFFFKFFf", 10: ".KhhffFKFFFFFKFf",
                      11: "..KhfFPFFKKKPFK.", 12: "..KhfFFFKMKFFK..", 13: "...KfffKrrrrK..."}
LARG, ALT = 34, 44
OX, OY = 2, 14           # canto do pônei no canvas (sem balanço)
_cache = {}
_spr = {}


def _s(rows, pal=None):
    chave = (id(rows), id(pal))
    if chave not in _spr:
        p = pal or PAL
        w = max(len(r) for r in rows)
        s = pygame.Surface((w, len(rows)), pygame.SRCALPHA)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in p:
                    s.set_at((x, y), p[ch])
        _spr[chave] = s
    return _spr[chave]


TRAJE = [None]           # traje do clima no Doutor montado (trajes.py); None = jaleco de sempre


def trajar(nome=None):
    TRAJE[0] = nome


_pal_traje = {}


def _doutor(quadro, susto=False, pal=None, chapeu=False):
    traje = TRAJE[0]
    chave = ("doutor", quadro % 2, susto, id(pal), chapeu, traje)
    if chave not in _spr:
        rows = [list(l) for l in DOUTOR]
        for k, faixa in enumerate(CACHECOL[quadro % 2]):
            for x, ch in enumerate(faixa):
                if x < 4 and rows[15 + k][x] not in "KW":
                    rows[15 + k][x] = ch
        if susto:
            for k, t in DOUTOR_SUSTO_ROSTO.items():
                rows[k] = list(t)
        if chapeu and not traje:
            for k, t in CHAPEU.items():
                rows[k] = list(t)
        rows = ["".join(r) for r in rows]
        if traje:
            from . import trajes
            rows, _ = trajes.aplicar(rows, traje)
            ch_p = (id(pal), traje)
            if ch_p not in _pal_traje:
                pt = dict(pal or PAL)
                pt.update(trajes.cores(traje))
                _pal_traje[ch_p] = (pt, pal)
            pal = _pal_traje[ch_p][0]
        _linhas_vivas.append(rows)                   # _s indexa por id(): a lista precisa continuar viva
        _spr[chave] = _s(rows, pal)
    return _spr[chave]


_linhas_vivas = []

# ------------------------------------------------------------------ Doutora
# Doutora de pé: rabo de cavalo cheio com laço, franja com luz j, olhos anime 2×3 (reflexo E em cima, brilho J
# embaixo), bochechas P, jaleco aberto sobre o pijama cirúrgico (U/u, cor da roupa) com sombra w do lado direito,
# estetoscópio, mão da frente estendida (segura o bastão) e tamancos.
DOUTORA = """
......KKKKKKK.......
....KKhjjjhhhKK.....
...KhhjjhhhhhhhK....
..KhhjhhhhhhhhhhK...
.KKhhhhhhhhhhhhhK...
KaaKhhhhhhhhFFFhK...
KhhKhhhhhhhFFFFFK...
KhjKhhhhhffFFFFFFK..
KhhKhhhhffFENFFENK..
KhjKhhhhffFNNFFNNF..
KhhKhhhhffFJNFFJNK..
.KhKKhhhfFPFFFFPK...
.KhhKhhhKfFFFMMFK...
..KK.KhhKKffffFK....
......KKKKKKKKK.....
.....KWWwuUUuwWWK...
....KWWWwUUUUwWWwK..
....KWWWWwUUwWWWwKK.
....KWWWWWwwWWWWwWFK
....KWWWWWWwWWWWwWFK
....KWWWWWWsWWWWwKK.
....KWWWWWWsWWWWwK..
....KwWWWWWWWWWwK...
....KwwwwwwwwwwwK...
.....KUUUUUUUUUK....
.....KUUUuKUUUuK....
.....KUUUuKUUUuK....
.....KUUUuKUUUuK....
.....KBBBBKBBBBBK...
.....KKKKKKKKKKKK...
""".split()
CORPO_EM_PE = DOUTORA[15:]
CABECAS = {"doutora": DOUTORA[:15]}
CORPOS = {}             # corpo próprio (estudantes.py); padrão: jaleco + pijama
# caras: dor = olhos ">_<" e boca escancarada; piscada = traço no meio do olho
CARAS = {"doutora": {"susto": {8: "KhhKhhhhffFNFFFNFK..", 9: "KhjKhhhhffFFNFFFNF..", 10: "KhhKhhhhffFNFFFNFK..",
                               12: ".KhhKhhhKfFFKMMKK...", 13: "..KK.KhhKKffKKKK...."},
                     "pisca": {8: "KhhKhhhhffFFFFFFFK..", 9: "KhjKhhhhffFNNFFNNF..", 10: "KhhKhhhhffFFFFFFFK.."}}}
PAL_DOUTORA = {"h": (58, 36, 52), "j": (110, 70, 96), "F": (232, 178, 138), "f": (196, 132, 96),
               "M": (196, 70, 90), "P": (246, 140, 130), "a": (240, 70, 110), "B": (60, 64, 84), "N": (40, 26, 36),
               "J": (120, 86, 130)}

def _olhos(cab, pos, cor="N", alt=3):
    """Olhos anime nas cabeças de pé: em cada (linha, coluna) do canto superior esquerdo desenha um olho de 2 colunas
    por `alt` linhas (reflexo E em cima à esquerda, íris `cor`, brilho J embaixo). Devolve (cabeça, caras) com a
    piscada (traço no meio) e o susto/dor (olhos ">" apertados e boca escancarada, 1 linha a mais)."""
    if alt == 3:
        normal, pisca, susto = ["E" + cor, cor * 2, "J" + cor], ["FF", cor * 2, "FF"], [cor + "F", "F" + cor, cor + "F"]
    else:
        normal, pisca, susto = ["E" + cor, cor * 2], ["FF", cor * 2], [cor + "F", "F" + cor]

    def pinta(base, olho):
        rows = [list(l.ljust(20, ".")) for l in base]
        for y, x in pos:
            for k, par in enumerate(olho):
                rows[y + k][x], rows[y + k][x + 1] = par
        return ["".join(r) for r in rows]

    cab = pinta(cab, normal)
    linhas = {pos[0][0] + k for k in range(alt)}
    caras = {"pisca": {k: l for k, l in enumerate(pinta(cab, pisca)) if k in linhas}}
    dor = [list(l) for l in pinta(cab, susto)]
    y = next(k for k, l in enumerate(cab) if "MM" in l)          # boca: abre (K dos lados e embaixo)
    i = cab[y].index("MM")
    j = i + len(cab[y][i:]) - len(cab[y][i:].lstrip("M"))
    for x in (i - 1, j):
        if dor[y][x] not in ".K":
            dor[y][x] = "K"
    for x in range(i - 1, j + 1):
        if dor[y + 1][x] in "FfdhwW":
            dor[y + 1][x] = "K"
    caras["susto"] = {k: "".join(dor[k]) for k in sorted(linhas | {y, y + 1})}
    return cab, caras


# Cirurgião: touca cirúrgica estampada (C/c), máscara abaixada no queixo (w), barba curta
CABECAS["cirurgiao"] = """
.....KKKKKKKKK......
....KCCcCCCcCCK.....
...KCcCCCcCCCcCK....
..KCCCCcCCCCcCCCK...
..KCcCCCCCcCCCcCK...
..KKKKKKKKKKKKKKK...
..KhKFFFFFFFFFFFK...
..KhFFFFFFFFFFFFFK..
..KFFfFFFFFFFFFFFK..
..KFFfFFFFFFFFFFFF..
..KhFfFPFFFFFFFPFK..
..KhhFFFFFFFMMFFK...
...KhhhhhhhhhhhK....
...KwwwwwwwwwwwK....
....KKKKKKKKKKK.....
""".split()
CABECAS["cirurgiao"], CARAS["cirurgiao"] = _olhos(CABECAS["cirurgiao"], [(7, 8), (7, 13)])
PAL_CIRURGIAO = {"h": (36, 24, 24), "F": (142, 92, 62), "f": (108, 66, 44), "M": (90, 40, 40), "N": (28, 20, 24),
                 "J": (96, 70, 60), "P": (190, 110, 90),
                 "C": (90, 150, 230), "c": (40, 90, 170), "w": (190, 226, 240), "B": (40, 44, 60)}
# Professor: careca, cabelo e barba brancos (W/w), óculos de meia-lua (N)
CABECAS["professor"] = """
......KKKKKKK.......
.....KFFFFFFFK......
....KFFFFFFFFFK.....
...KFFfFFFFFFFFK....
..KwWFFFFFFFFFFK....
..KWWFFFFFFFFFFFK...
..KWwFFFFFFFFFFFK...
..KWWFFfKNNNKFNNNK..
..KWwFFfFEJKFFEJKFF.
..KWWFFFFJKKFFJKKK..
..KWwWFFFFFFFFFFFK..
...KWWWWWWMMWWWWK...
...KWWWWWWWWWWWK....
....KWWWWWWWWWK.....
.....KKKKKKKKK......
""".split()
CARAS["professor"] = {"susto": {8: "..KWwFFfFEEEFFEEEFF.", 9: "..KWWFFFFEKEFFEKEK..", 11: "...KWWWWWKMMKWWWK...",
                                12: "...KWWWWWKKKKWWK...."},
                      "pisca": {8: "..KWwFFfFFFFFFFFFFF.", 9: "..KWWFFFFKKKFFKKKK.."}}
PAL_PROFESSOR = {"F": (248, 206, 176), "f": (214, 160, 128), "W": (246, 246, 250), "w": (190, 194, 210),
                 "N": (120, 120, 140), "M": (190, 90, 100), "B": (90, 54, 34), "J": (96, 118, 150)}
# Doutora Cachos: cabelo black power (h/j), pele negra
CABECAS["cachos"] = """
...KKKKKKKKKK.......
.KKhjhhjhhjhhKK.....
KhjhhjhhjhhjhhjK....
KhhjhhjhhjhhjhhhK...
KhjhhjhhhhjhhhjhK...
KhhjhhhhhFFFFFhhK...
KjhhhhhhFFFFFFFhK...
KhhjhhhfFFFFFFFFK...
KhjhhhffFFFFFFFFFK..
KhhjhhffFFFFFFFFFK..
.KhhjhhfPFFFFFFPK...
.KjhhhhhfFFFMMFK....
..KhjhhhKffffFK.....
...KKhhKKKKKKK......
.....KKK............
""".split()
CABECAS["cachos"], CARAS["cachos"] = _olhos(CABECAS["cachos"], [(7, 9), (7, 13)])
PAL_CACHOS = {"h": (40, 26, 28), "j": (84, 56, 60), "F": (150, 98, 70), "f": (116, 72, 50), "N": (30, 20, 22),
              "J": (92, 62, 66), "M": (170, 60, 80), "P": (196, 110, 100), "B": (120, 60, 80)}


# ---- elenco novo (2026-10-16): cabeças 20×15 no mesmo molde, sobre o corpo comum de jaleco
# Doutor Ruivo: cabelo curto ruivo e sardas (S)
CABECAS["ruivo"] = """
......KKKKKKK.......
....KKhhjhhhhKK.....
...KhhjhhhhjhhhK....
..KhhhhhjhhhhhhhK...
..KhhhhhhhhhFFFFK...
..KhhhhhhhFFFFFFFK..
..KhhhhhFFFFFFFFFK..
..KhhhhfFFFFFFFFFK..
..KhhhfFFFFFSFFFFF..
..KhhhfFFFFFFFFFFK..
..KhhhfFSFFFSFFFSK..
...KhhfFFFFFMMFFK...
...KKhKfFFFFFFFK....
.....KKKfffffKK.....
.......KKKKKKK......
""".split()
CABECAS["ruivo"], CARAS["ruivo"] = _olhos(CABECAS["ruivo"], [(7, 9), (7, 14)])
PAL_RUIVO = {"h": (200, 90, 40), "j": (240, 146, 76), "F": (250, 214, 184), "f": (222, 162, 124), "S": (196, 118, 78),
             "M": (190, 80, 80), "N": (40, 30, 30), "J": (70, 130, 160)}
# Doutora Tranças: tranças longas atrás com miçangas douradas (a)
CABECAS["trancas"] = """
.......KKKKKK.......
.....KKhjhjhhKK.....
....KhjhjhjhjhhK....
...KhjhjhjhjhjhhK...
..KhjhjhjhjhhhhhK...
.KhjhjhjhhhhFFFhK...
KhjhjhjhhhhFFFFFK...
KjhjhjhhhffFFFFFFK..
KhjhjhhhffFFFFFFFK..
KjhjhKhhffFFFFFFFF..
KhjhjKhhffFFFFFFFK..
KjhjhKKhfFPFFFFPK...
KaKaKKhhKfFFFMMFK...
KKKKK.KhKKffffFK....
......KKKKKKKKK.....
""".split()
CABECAS["trancas"], CARAS["trancas"] = _olhos(CABECAS["trancas"], [(8, 11), (8, 15)])
PAL_TRANCAS = {"h": (30, 20, 24), "j": (74, 50, 54), "F": (122, 80, 56), "f": (94, 60, 42), "a": (240, 192, 64),
               "P": (160, 92, 82), "M": (150, 58, 70), "N": (24, 16, 20), "J": (88, 56, 50)}
# Doutora Grisalha: coque branco no alto e óculos (N = armação)
CABECAS["grisalha"] = """
......KKKK..........
.....KwWWwK.........
.....KWwWWK.........
....KKKKKKKKK.......
...KWwWWwWWWwK......
..KwWWWWWWWWWWK.....
..KWWwWWWWWFFFFK....
..KWWWWWWFFFFFFFK...
..KwWWWWfKNNNKNNNK..
..KWWWWffNEJKNEJKN..
..KwWWWffNJKKNJKKN..
..KWWWWfFFPFFFFPK...
...KwWWKfFFFMMFK....
....KKWKKfffffK.....
......KKKKKKKK......
""".split()
CARAS["grisalha"] = {"susto": {9: "..KWWWWffNEEENEEEN..", 10: "..KwWWWffNEKENEKEN..", 12: "...KwWWKfFFKMMKK....",
                               13: "....KKWKKffKKKK....."},
                     "pisca": {9: "..KWWWWffNFFFNFFFN..", 10: "..KwWWWffNKKKNKKKN.."}}
PAL_GRISALHA = {"W": (230, 230, 236), "w": (178, 178, 192), "F": (246, 206, 182), "f": (212, 160, 132),
                "N": (110, 80, 140), "P": (240, 150, 150), "M": (180, 80, 100), "J": (118, 96, 140)}
# Doutor Dread: dreadlocks com faixa verde (a) e barba curta (d)
CABECAS["dread"] = """
......KKKKKKKK......
....KKhjhjhjhjKK....
...KjhjhjhjhjhjhK...
..KaaaaaaaaaaaaaaK..
..KhjhjhjhhhFFFFFK..
.KhjhjhjhhFFFFFFFFK.
.KjhjhjhhFFFFFFFFFK.
.KhjhjhhfFFFFFFFFFF.
.KjhjhjhfFFFFFFFFFK.
.KhjhjhhfFFFFFFFFK..
.KjhKhjhfdddFFFddK..
.KhjKhjhKddMMMMddK..
..KKKhjKKddddddK....
.....KKK.KKKKKK.....
....................
""".split()
CABECAS["dread"], CARAS["dread"] = _olhos(CABECAS["dread"], [(6, 11), (6, 15)])
PAL_DREAD = {"h": (34, 24, 20), "j": (96, 66, 42), "a": (60, 170, 90), "F": (132, 88, 62), "f": (102, 66, 46),
             "d": (40, 28, 24), "M": (150, 64, 64), "N": (20, 14, 12), "J": (84, 56, 44)}
# Doutora do Lenço: hijab azul (L/l) emoldurando o rosto
CABECAS["hijab"] = """
.......KKKKKK.......
.....KKLLLLLLKK.....
....KLLLlLLLLLLK....
...KLLLLLLLlLLLLK...
..KLLLlLLLLLLLLLK...
..KLLLLLLKKKKKKLK...
.KLLLLLLKFFFFFFKLK..
.KLLlLLKFFFFFFFFKK..
.KLLLLLKFFFFFFFFFK..
.KLLLLLKFPFFFFFPFK..
.KLLLlLLKFFFMMFFK...
.KLLLLLLLKffffKLK...
..KLLLlLLLKKKKLLK...
...KKLLLLLLLLLLK....
.....KKKKKKKKKK.....
""".split()
CABECAS["hijab"], CARAS["hijab"] = _olhos(CABECAS["hijab"], [(7, 9), (7, 13)], alt=2)
PAL_HIJAB = {"L": (60, 110, 190), "l": (40, 78, 150), "F": (214, 166, 126), "f": (180, 132, 98), "P": (232, 142, 132),
             "M": (176, 72, 84), "N": (34, 24, 26), "J": (96, 66, 60)}
# Doutor Intensivista: careca com brilho (E) e barba cheia (d)
CABECAS["careca"] = """
......KKKKKKK.......
.....KFFFFEFFK......
....KFFFFFEEFFK.....
...KFFFFFFFFFFFK....
..KFFFFFFFFFFFFFK...
..KfFFFFFFFFFFFFFK..
..KffFFFFFKKFFFKKK..
..KffFFFFFFFFFFFFK..
..KffFFFFFFFFFFFFF..
..KfdFFFFFFFFFFFFK..
..KfddddFFFFFFFddK..
...KdddddddMMMdddK..
...KKddddddddddK....
.....KKddddddKK.....
.......KKKKKK.......
""".split()
CABECAS["careca"], CARAS["careca"] = _olhos(CABECAS["careca"], [(7, 10), (7, 15)])
PAL_CARECA = {"F": (204, 142, 102), "f": (164, 106, 72), "E": (242, 196, 156), "d": (62, 46, 38), "M": (150, 70, 70),
              "N": (30, 22, 20), "J": (104, 74, 58)}


def _em_pe(pid, pal, cara=""):
    """Personagem de pé: cabeça própria sobre o corpo comum (jaleco + pijama na cor da roupa)."""
    chave = ("em_pe", pid, cara, id(pal))
    if chave not in _spr:
        cab = [l.ljust(20, ".") for l in CABECAS[pid]]
        for k, t in CARAS.get(pid, {}).get(cara, {}).items():
            cab[k] = t.ljust(20, ".")
        rows = cab + CORPOS.get(pid, CORPO_EM_PE)
        _linhas_vivas.append(rows)
        _spr[chave] = _s(rows, pal)
    return _spr[chave]


def _pernas_sentado(corpo):
    """Tronco do corpo de pé (até a barra do jaleco) + colo e perna pendurada do lado do pônei, nas cores da calça
    e do sapato desse corpo."""
    k = next(i for i in range(3, len(corpo)) if corpo[i].startswith(".....K"))     # 1ª linha da calça
    calca = max(set(corpo[k].strip(".K")), key=corpo[k].count)
    tom = next((c for c in corpo[k + 1].strip(".K") if c != calca), calca)
    sola = corpo[-2].strip(".").replace("K", "")
    sapato = (sola[:4] or "BBBB").ljust(4, sola[:1] or "B")
    P, p = calca, tom
    return corpo[:6] + corpo[7:k] + [            # sentado o tronco encurta uma linha
        "....K" + P * 12 + "K..",
        "....KKKKKKKK" + P * 3 + p + "K...",
        "...........K" + P * 2 + p + "K....",
        "...........K" + P * 2 + p + "K....",
        "..........K" + sapato + sapato[-1] + "K...",
        "..........KKKKKKK...",
    ]


def _sentado(pid, pal, cara=""):
    """Personagem que era de pé, agora sentado no pônei: mesma cabeça, tronco do corpo próprio, pernas de montaria."""
    chave = ("sentado", pid, cara, id(pal))
    if chave not in _spr:
        cab = [l.ljust(20, ".") for l in CABECAS[pid]]
        for k, t in CARAS.get(pid, {}).get(cara, {}).items():
            cab[k] = t.ljust(20, ".")
        rows = cab + _pernas_sentado(CORPOS.get(pid, CORPO_EM_PE))
        _linhas_vivas.append(rows)
        _spr[chave] = _s(rows, pal)
    return _spr[chave]


def _doutora(pal, cara=""):
    return _em_pe("doutora", pal, cara)


# capivara (montaria do Doutor do Interior), no mesmo canvas do pônei
CAPI = """
...............................
...............................
...............................
...................KK..KK......
..................KtuKKtuK.....
.................KTTTTTTTTK....
................KTTTTTKKKTTK...
...............KTTTTTKEEKKTTK..
...............KTTTTTKEKKKTTTK.
...............KTTTTTKtKEKTTTTK
...............KTTTTTTKKKTTnnnK
..............KTTTTTTTTTTPnnKnK
.....KKKKKKKKKTTTTTTTTTTTTnnnnK
...KKTTTTTTTTTTTTTTTTTTTTKKKKK.
..KTTuTTTTTTTTTTTTTTTTTTK......
.KTTuTTTTTTTTTTTTTTTTTTTK......
.KTTTTTTTTTTTTTTTTTTTTTTTK.....
KTTTTTTTTTTTTTTTTTTTTTTTTK.....
KtTTTTTTTTTTTTTTTTTTTTTTtK.....
KttTTTTTTTTTTTTTTTTTTTTttK.....
.KttttttttttttttttttttttK......
..KKKKKKKKKKKKKKKKKKKKKK.......
""".split()
CAPI_BOCA = _troca(CAPI, {12: ".....KKKKKKKKKTTTTTTTTTTTTKKKKK", 13: "...KKTTTTTTTTTTTTTTTTTTTTKMMMK."})
CAPI_PISCA = _olho(CAPI, "TTTTT", "TTTTT", "TKKKT", "KTTTK", "TTTTT", x0=21, y0=6)       # olho fechado feliz
CAPI_SUSTO = _olho(CAPI_BOCA, "TTTTT", "KKTTT", "TKKTT", "KKTTT", "TTTTT", x0=21, y0=6)  # olho apertado, boca aberta
PAL_CAPI = {"T": (156, 106, 66), "t": (110, 72, 44), "u": (190, 140, 96), "n": (92, 62, 42), "M": (200, 80, 90),
            "P": (214, 122, 96)}
def _chifre(rows):
    """Chifre dourado na testa do pônei (colunas livres acima da cabeça)."""
    out = [list(r.ljust(31, ".")) for r in rows]
    for y, x, ch in ((0, 26, "K"), (0, 27, "K"), (1, 25, "K"), (1, 26, "Y"), (1, 27, "K"), (2, 25, "K"), (2, 26, "Y"),
                     (2, 27, "y"), (2, 28, "K"), (3, 26, "Y"), (3, 27, "K")):
        if out[y][x] in ".K":
            out[y][x] = ch
    return ["".join(r) for r in out]


UNI, UNI_BOCA, UNI_PISCA, UNI_SUSTO = (_chifre(r) for r in (PONEI, PONEI_BOCA, PONEI_PISCA, PONEI_SUSTO))
PAL_UNI = {"m": (176, 120, 255), "l": (96, 214, 240), "z": (255, 226, 240), "Y": (255, 214, 80), "y": (214, 150, 40)}

MONTARIAS = {"ponei": {id(PONEI): PONEI, id(PONEI_BOCA): PONEI_BOCA, id(PONEI_PISCA): PONEI_PISCA, id(PONEI_SUSTO): PONEI_SUSTO},
             "capivara": {id(PONEI): CAPI, id(PONEI_BOCA): CAPI_BOCA, id(PONEI_PISCA): CAPI_PISCA, id(PONEI_SUSTO): CAPI_SUSTO},
             "unicornio": {id(PONEI): UNI, id(PONEI_BOCA): UNI_BOCA, id(PONEI_PISCA): UNI_PISCA, id(PONEI_SUSTO): UNI_SUSTO}}


def _rocinante(rows):
    """Rocinante: o pônei em pele e osso (costelas à mostra e barriga funda)."""
    r = [list(l.ljust(31, ".")) for l in rows]
    for y in range(14, 19):
        for x in (10, 12, 14, 16, 18):
            if r[y][x] in "Ww":
                r[y][x] = "s"
    for x in range(9, 19):                        # barriga funda
        r[19][x], r[20][x], r[21][x] = "K", ".", "."
    return ["".join(l) for l in r]


MONTARIAS["rocinante"] = {id(x): _rocinante(x) for x in (PONEI, PONEI_BOCA, PONEI_PISCA, PONEI_SUSTO)}
PAL_MONTARIA = {"unicornio": PAL_UNI,
                "rocinante": {"W": (208, 184, 144), "w": (166, 140, 106), "s": (112, 90, 70), "m": (84, 64, 50),
                              "l": (58, 44, 36), "z": (228, 208, 176), "q": (70, 56, 48)}}
MONTARIAS["pesadelo"] = MONTARIAS["ponei"]         # o mesmo pônei, nas cores do quadro de Munch
PAL_MONTARIA["pesadelo"] = {"W": (58, 66, 104), "w": (36, 42, 74), "s": (22, 24, 48), "m": (232, 104, 44),
                            "l": (176, 36, 44), "z": (92, 96, 130), "q": (20, 20, 40)}
MONTARIAS["bosch"] = MONTARIAS["unicornio"]         # o unicórnio branco de Bosch, de chifre comprido e sem arco-íris
PAL_MONTARIA["bosch"] = {"W": (246, 240, 226), "w": (216, 206, 196), "s": (160, 146, 150), "m": (216, 196, 170), "l": (178, 156, 140),
                         "z": (255, 252, 240), "Y": (240, 226, 196), "y": (176, 156, 140)}
MONTARIA_TRAJE = {"quixote": "rocinante", "grito": "pesadelo", "caminhante": "bosch"}   # o traje leva a própria montaria
CHAPEU = {0: "....KKKKKKKK....", 1: "...KYYRRRRYYK...", 2: "KYYYYYYYYYYYYYYK"}
PAL_INTERIOR = {"h": (44, 32, 30), "j": (80, 60, 52), "d": (30, 20, 18), "F": (206, 146, 104), "f": (166, 106, 74),
                "Y": (240, 206, 120), "R": (200, 60, 60)}
_PAL_CAPI_CACHE = {}


_PAL_MONT_CACHE = {}


def _pal_montaria(nome, pal):
    """Paleta de uma montaria com cores próprias (unicórnio); None = a paleta padrão do pônei."""
    if nome not in PAL_MONTARIA:
        return None
    if (nome, id(pal)) not in _PAL_MONT_CACHE:
        p = dict(PAL)
        p.update(PAL_MONTARIA[nome])
        _PAL_MONT_CACHE[(nome, id(pal))] = p
    return _PAL_MONT_CACHE[(nome, id(pal))]


def _pal_capi(pal):
    if id(pal) not in _PAL_CAPI_CACHE:
        p = dict(pal)
        p.update(PAL_CAPI)
        _PAL_CAPI_CACHE[id(pal)] = p
    return _PAL_CAPI_CACHE[id(pal)]


# ------------------------------------------------------------------ catálogo (loja.py vende)
def _mix(c, alvo, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c, alvo))


def _tons(base):
    """4 tons de nuvem (brilho, base, sombra, fundo) a partir de uma cor."""
    return {"1": _mix(base, (255, 255, 255), 0.75), "2": base, "3": _mix(base, (0, 0, 0), 0.22),
            "4": _mix(base, (0, 0, 0), 0.45)}


PERSONAGENS = {
    "doutor": dict(nome="Doutor", artigo="o", preco=0, tipo="monta", montaria="ponei", pal={},
                   desc="Montado no pônei branco de crina rosa, sobre a nuvem dourada",
                   padrao={"nuvem": "dourada", "bastao": "nenhum", "roupa": "lilas"}),
    "doutora": dict(nome="Doutora", artigo="a", preco=0, tipo="pe", pal=PAL_DOUTORA,
                    desc="Montada no pônei, na nuvem lilás, com o bastão de Esculápio na mão",
                    padrao={"nuvem": "lilas", "bastao": "esculapio", "roupa": "verde_agua"}),
    "cirurgiao": dict(nome="Cirurgião", artigo="o", preco=150, tipo="pe", pal=PAL_CIRURGIAO,
                      desc="Touca do centro cirúrgico, máscara no queixo e um bisturi gigante",
                      padrao={"nuvem": "celeste", "bastao": "bisturi", "roupa": "azul"}),
    "professor": dict(nome="Professor", artigo="o", preco=200, tipo="pe", pal=PAL_PROFESSOR,
                      desc="Barba branca, óculos de meia-lua e a bengala de quem já viu de tudo",
                      padrao={"nuvem": "branca", "bastao": "bengala", "roupa": "vinho"}),
    "cachos": dict(nome="Doutora Cachos", artigo="a", preco=250, tipo="pe", pal=PAL_CACHOS,
                   desc="Black power, pijama rosa e o bastão de Esculápio",
                   padrao={"nuvem": "pessego", "bastao": "esculapio", "roupa": "rosa"}),
    "interior": dict(nome="Doutor do Interior", artigo="o", preco=300, tipo="monta", montaria="capivara",
                     pal=PAL_INTERIOR, chapeu=True,
                     desc="Chapéu de palha, montado numa capivara, atende da roça à capital",
                     padrao={"nuvem": "dourada", "bastao": "bengala", "roupa": "verde_agua"}),
    "ruivo": dict(nome="Doutor Ruivo", artigo="o", preco=180, tipo="pe", pal=PAL_RUIVO,
                  desc="Cabelo cor de fogo e sardas, o termômetro sempre à mão",
                  padrao={"nuvem": "menta", "bastao": "termometro", "roupa": "laranja"}),
    "trancas": dict(nome="Doutora Tranças", artigo="a", preco=220, tipo="pe", pal=PAL_TRANCAS,
                    desc="Tranças longas com miçangas douradas e o estetoscópio no pescoço",
                    padrao={"nuvem": "aurora", "bastao": "estetoscopio", "roupa": "turquesa"}),
    "dread": dict(nome="Doutor Dread", artigo="o", preco=240, tipo="pe", pal=PAL_DREAD,
                  desc="Dreadlocks, faixa verde e o martelo de reflexo de quem examina tudo",
                  padrao={"nuvem": "floresta", "bastao": "martelo", "roupa": "verde_folha"}),
    "hijab": dict(nome="Doutora do Lenço", artigo="a", preco=260, tipo="pe", pal=PAL_HIJAB,
                  desc="Lenço azul-profundo e a lanterna clínica pronta para o exame",
                  padrao={"nuvem": "oceano", "bastao": "lanterna", "roupa": "branco"}),
    "careca": dict(nome="Doutor Intensivista", artigo="o", preco=320, tipo="pe", pal=PAL_CARECA,
                   desc="Careca brilhante, barba cheia e a seringa de quem não dorme na UTI",
                   padrao={"nuvem": "tempestade", "bastao": "seringa", "roupa": "cinza"}),
    "grisalha": dict(nome="Doutora Grisalha", artigo="a", preco=400, tipo="pe", pal=PAL_GRISALHA,
                     desc="Coque branco e óculos lilás: a chefe da clínica que viu de tudo",
                     padrao={"nuvem": "neve", "bastao": "bengala", "roupa": "roxo"}),
    "unicornio": dict(nome="Doutor do Unicórnio", artigo="o", preco=650, tipo="monta", montaria="unicornio", pal={},
                      desc="Montado num unicórnio de chifre dourado e crina colorida",
                      padrao={"nuvem": "coracoes", "bastao": "estrela", "roupa": "rosa"}),
}
# item: nome, preço em moedas (0 = já vem com o jogo), descrição, dados de desenho
NUVENS = {
    "dourada": dict(nome="Nuvem dourada", preco=0, desc="A clássica, que brilha como ouro",
                    tons={"1": (255, 250, 214), "2": (255, 226, 112), "3": (250, 184, 52), "4": (214, 120, 30)}),
    "lilas": dict(nome="Nuvem lilás", preco=0, desc="A nuvem da Doutora", tons=_tons((214, 176, 250))),
    "algodao": dict(nome="Algodão-doce", preco=90, desc="Rosa e fofinha", tons=_tons((255, 182, 214))),
    "menta": dict(nome="Nuvem de menta", preco=90, desc="Fresca como o plantão da madrugada", tons=_tons((140, 228, 196))),
    "fogo": dict(nome="Nuvem de fogo", preco=250, desc="Para quem chega voando no plantão",
                 tons={"1": (255, 246, 190), "2": (255, 178, 60), "3": (236, 104, 34), "4": (168, 40, 24)}, efeito="fogo"),
    "tempestade": dict(nome="Nuvem de tempestade", preco=300, desc="Cinza-chumbo, solta faíscas",
                       tons=_tons((128, 134, 160)), efeito="raios"),
    "celeste": dict(nome="Nuvem celeste", preco=90, desc="Azul-claro de céu limpo (vem com o Cirurgião)",
                    tons=_tons((150, 206, 250))),
    "branca": dict(nome="Nuvem branca", preco=60, desc="Nuvem de verdade (vem com o Professor)", tons=_tons((236, 238, 246))),
    "pessego": dict(nome="Nuvem pêssego", preco=90, desc="Laranja-rosado de fim de tarde (vem com a Doutora Cachos)",
                    tons=_tons((255, 196, 150))),
    "estrelada": dict(nome="Céu estrelado", preco=450, desc="A noite inteira dentro da nuvem",
                      tons=_tons((72, 86, 186)), efeito="estrelas"),
    "arcoiris": dict(nome="Nuvem arco-íris", preco=800, desc="Todas as cores, do vermelho ao violeta",
                     tons=_tons((255, 226, 112)), efeito="arcoiris"),
    "neve": dict(nome="Nuvem de neve", preco=200, desc="Flocos brilhando (vem com a Doutora Grisalha)",
                 tons=_tons((226, 240, 255)), efeito="neve"),
    "aurora": dict(nome="Aurora boreal", preco=380, desc="Verde e violeta dançando (vem com a Doutora Tranças)",
                   tons=_tons((120, 220, 180)), efeito="aurora"),
    "coracoes": dict(nome="Nuvem de corações", preco=420, desc="Cor-de-rosa salpicada de corações",
                     tons=_tons((255, 170, 210)), efeito="coracoes"),
    "oceano": dict(nome="Nuvem oceano", preco=260, desc="Azul do mar com espuma (vem com a Doutora do Lenço)",
                   tons=_tons((80, 150, 230)), efeito="oceano"),
    "floresta": dict(nome="Nuvem floresta", preco=160, desc="Verde-mata (vem com o Doutor Dread)", tons=_tons((96, 180, 110))),
    "lavanda": dict(nome="Nuvem lavanda", preco=110, desc="Lilás bem clarinho", tons=_tons((200, 186, 240))),
    "chumbo": dict(nome="Nuvem noturna", preco=140, desc="Azul-marinho do plantão da madrugada", tons=_tons((70, 84, 130))),
}
BASTOES = {
    "nenhum": dict(nome="Sem bastão", preco=0, desc="Mãos livres"),
    "esculapio": dict(nome="Bastão de Esculápio", preco=0, desc="O símbolo da medicina: bastão de madeira com uma serpente"),
    "bisturi": dict(nome="Bisturi gigante", preco=150, desc="Lâmina 22, cabo de aço (vem com o Cirurgião)"),
    "bengala": dict(nome="Bengala", preco=100, desc="Madeira com cabo curvo (vem com o Professor e o Doutor do Interior)"),
    "termometro": dict(nome="Termômetro gigante", preco=120, desc="Mercúrio subindo: febre de estudar"),
    "magico": dict(nome="Bastão mágico", preco=220, desc="Vermelho com pontas douradas"),
    "cristal": dict(nome="Cajado de cristal", preco=350, desc="Ponta de diamante azul"),
    "luz": dict(nome="Bastão de luz", preco=500, desc="Lâmina verde brilhante"),
    "estrela": dict(nome="Cetro da estrela", preco=700, desc="Ouro maciço com uma estrela na ponta"),
    "estetoscopio": dict(nome="Estetoscópio", preco=140, desc="Campânula prateada e tubo azul (vem com a Doutora Tranças)"),
    "seringa": dict(nome="Seringa gigante", preco=160, desc="Êmbolo cheio de coragem (vem com o Intensivista)"),
    "martelo": dict(nome="Martelo de reflexo", preco=150, desc="Cabeça vermelha triangular (vem com o Doutor Dread)"),
    "lanterna": dict(nome="Lanterna clínica", preco=130, desc="Luz para as pupilas (vem com a Doutora do Lenço)"),
}
ROUPAS = {
    "lilas": dict(nome="Camisa lilás", preco=0, desc="A camisa do Doutor", cor=(176, 148, 226)),
    "verde_agua": dict(nome="Pijama verde-água", preco=0, desc="O pijama cirúrgico da Doutora", cor=(64, 186, 176)),
    "azul": dict(nome="Pijama azul-cirúrgico", preco=60, desc="Direto do centro cirúrgico", cor=(70, 120, 220)),
    "vinho": dict(nome="Pijama vinho", preco=60, desc="Elegante no plantão", cor=(150, 40, 70)),
    "rosa": dict(nome="Pijama rosa", preco=60, desc="Outubro Rosa o ano todo", cor=(240, 120, 170)),
    "preto": dict(nome="Pijama preto", preco=120, desc="Modo noturno", cor=(50, 48, 62)),
    "laranja": dict(nome="Pijama laranja", preco=120, desc="Visível de longe no pronto-socorro", cor=(250, 140, 40)),
    "turquesa": dict(nome="Pijama turquesa", preco=80, desc="Turquesa de praia", cor=(40, 190, 200)),
    "verde_folha": dict(nome="Pijama verde-folha", preco=80, desc="Verde de mata", cor=(80, 170, 70)),
    "branco": dict(nome="Pijama branco", preco=90, desc="Branco de consultório", cor=(236, 236, 242)),
    "cinza": dict(nome="Pijama cinza", preco=80, desc="Cinza de UTI", cor=(120, 124, 140)),
    "roxo": dict(nome="Pijama roxo", preco=100, desc="Roxo de chefe", cor=(120, 70, 170)),
    "vermelho": dict(nome="Pijama vermelho", preco=110, desc="Vermelho de emergência", cor=(214, 50, 56)),
}
# roupas que só o clima veste (figurino.py): fora da loja
ROUPAS["capa_chuva"] = dict(nome="Capa de chuva", preco=0, desc="Amarela, para a chuva", cor=(248, 204, 40), oculta=True)
ROUPAS["bege"] = dict(nome="Roupa de explorador", preco=0, desc="Cáqui do deserto", cor=(206, 178, 126), oculta=True)
ROUPAS["luto"] = dict(nome="Preto gótico", preco=0, desc="Preto total", cor=(26, 22, 30), oculta=True)
ROUPAS["dourado"] = dict(nome="Túnica da frota", preco=0, desc="Veludo dourado dos anos 70", cor=(228, 184, 56), oculta=True)
ROUPAS["laca"] = dict(nome="Laca vermelha", preco=0, desc="Armadura de samurai", cor=(178, 30, 38), oculta=True)
ROUPAS["amarelo_neon"] = dict(nome="Jaqueta neon", preco=0, desc="Amarelo de megacidade", cor=(250, 210, 40), oculta=True)
ROUPAS["aco"] = dict(nome="Azul-aço", preco=0, desc="Armadura de colono", cor=(74, 104, 164), oculta=True)
ROUPAS["oliva"] = dict(nome="Verde-oliva", preco=0, desc="Armadura de patrulha", cor=(98, 102, 62), oculta=True)
ROUPAS["prata"] = dict(nome="Prata", preco=0, desc="Armadura de paladino", cor=(198, 202, 216), oculta=True)
BASTOES["lanca"] = dict(nome="Lança", preco=0, desc="Lança de cavaleiro andante", oculta=True)
NUVENS["poeira"] = dict(nome="Nuvem de poeira", preco=0, desc="A poeira da estrada de La Mancha", tons=_tons((222, 186, 128)),
                        oculta=True)
NUVENS["rosada"] = dict(nome="Nuvem rosada", preco=0, desc="O céu do Jardim das Delícias", oculta=True,
                        tons={"1": (255, 240, 240), "2": (248, 200, 212), "3": (214, 140, 176), "4": (140, 104, 170)})
BASTOES["bordao"] = dict(nome="Bordão", preco=0, desc="O bordão de quem caminha", oculta=True)
NUVENS["redemoinho"] = dict(nome="Redemoinho", preco=0, desc="As linhas do céu de O Grito", oculta=True,
                            tons={"1": (250, 204, 92), "2": (238, 120, 48), "3": (190, 52, 44), "4": (84, 32, 62)})
CATALOGO = {"nuvem": NUVENS, "bastao": BASTOES, "roupa": ROUPAS, "personagem": PERSONAGENS}
ITENS_VISUAIS = ("nuvem", "bastao", "roupa")

PADRAO = "doutor"        # personagem inicial (estudantes.ativar() troca o elenco na Ilha do Vestibulando)
VISUAL = {"personagem": "doutor", **PERSONAGENS["doutor"]["padrao"]}


def visual_valido(v):
    """Completa/corrige um visual vindo do save (item desconhecido → padrão do personagem)."""
    p = v.get("personagem") if v.get("personagem") in PERSONAGENS else PADRAO
    out = {"personagem": p}
    for cat in ITENS_VISUAIS:
        out[cat] = v.get(cat) if v.get(cat) in CATALOGO[cat] else PERSONAGENS[p]["padrao"][cat]
    return out


def artigo_nome(v=None):
    """'o Doutor' / 'a Doutora' (textos do jogo que falam do personagem)."""
    p = PERSONAGENS[(v or VISUAL)["personagem"]]
    return f"{p['artigo']} {p['nome']}"


def equipar(v):
    VISUAL.clear()
    VISUAL.update(visual_valido(v))


_pals = {}


FIGURINO = {}        # cores trocadas pelo clima (figurino.py): ex. cabelo preto e pele pálida no clima gótico


def vestir(cores=None):
    """Troca (ou limpa) as cores do figurino; vale para os próximos desenhos do herói."""
    if cores != FIGURINO:
        FIGURINO.clear()
        FIGURINO.update(cores or {})


def _paleta(v):
    chave = (v["personagem"], v["roupa"], tuple(sorted(FIGURINO.items())))
    if chave not in _pals:
        p = dict(PAL)
        dados = PERSONAGENS[v["personagem"]]
        p.update(dados.get("pal", {}))
        cor = ROUPAS[v["roupa"]]["cor"]
        p["U"], p["u"] = cor, _mix(cor, (0, 0, 0), 0.3)
        if dados["tipo"] == "monta":
            p["p"] = _mix(cor, (0, 0, 0), 0.5)          # calça no tom escuro da roupa
        p.update(FIGURINO)
        _pals[chave] = p
    return _pals[chave]


# bastões: grade de 8 colunas desenhada por código (centro entre as colunas 3 e 4)
PAL_BASTAO = {"K": PAL["K"], "B": (170, 110, 60), "b": (112, 68, 34), "i": (110, 210, 110), "g": (40, 130, 60),
              "R": (226, 46, 52), "r": (150, 20, 36), "Y": (255, 214, 80), "y": (200, 140, 30), "W": (255, 255, 255),
              "w": (200, 208, 222), "C": (176, 232, 255), "c": (100, 170, 236), "s": (150, 156, 178), "q": (90, 94, 118),
              "G": (120, 255, 150), "E": (255, 255, 230), "n": (70, 120, 220), "N": (40, 80, 170)}
ALT_BASTAO = 34


def _grade_bastao(tipo, h=ALT_BASTAO):
    import math as _m
    g = [["."] * 8 for _ in range(h)]

    def haste(c1, c2, y0=0, y1=h):
        for y in range(y0, y1):
            g[y][2], g[y][3], g[y][4], g[y][5] = "K", c1, c2, "K"

    def tampa(y, cor, cor2, larg=3):
        for x in range(4 - larg, 4 + larg):
            g[y][x] = cor if 0 < y < h - 1 else "K"
        g[y][4 - larg], g[y][3 + larg] = "K", "K"
        if cor2:
            g[y][4 - larg + 1] = cor2

    if tipo == "esculapio":
        haste("B", "b", 2, h)
        for x in (2, 3, 4, 5):
            g[1][x] = "K"
        g[2][3], g[2][4] = "B", "B"
        for y in range(7, h - 5):                       # serpente enrolada (hélice)
            fase = (y - 7) * 0.7
            x = 3.5 + 2.9 * _m.sin(fase)
            xi = int(round(x - 0.5))
            frente = _m.cos(fase) > 0
            for xx in (xi, xi + 1):
                if 0 <= xx < 8 and (frente or g[y][xx] == "."):
                    g[y][xx] = "i" if frente else "g"
        for y, linha in enumerate(("..KBbKK.", "..KBbKiK", "..KBbiKi", "..KBbiii", "..KBbKgK")):
            g[2 + y] = list(linha)                       # cabeça da serpente com olho, no alto
    elif tipo == "bisturi":
        haste("s", "q", 9, h)
        for y in range(11, h - 1, 3):
            g[y][3], g[y][4] = "q", "q"
        for y, linha in enumerate(("....K...", "...KWK..", "...KWwK.", "..KWWwK.", "..KWWwK.", "..KWWwK.",
                                   "..KWWwK.", "..KWwwK.", "..KKKKK.")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "bengala":
        haste("B", "b", 5, h)
        for y, linha in enumerate(("...KKKK.", "..KBBBBK", "..KBbKBK", "..KBbKBK", "..KBbKKK")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "magico":
        haste("R", "r")
        for y in (0, 1, 2, h - 3, h - 2, h - 1):
            tampa(y, "Y", "E" if y in (1, h - 2) else None, 3 if y in (1, h - 2) else 2)
    elif tipo == "termometro":
        haste("W", "w", 1, h - 4)
        for x in (3, 4):
            g[0][x] = "K"
        for y in range(int(h * 0.35), h - 4):
            g[y][3] = "R"
        for y in range(4, h - 6, 3):
            g[y][4] = "q"
        for y, linha in enumerate(("..KRRK..", ".KRRRRK.", ".KRERRK.", "..KKKK..")):
            g[h - 4 + y] = list(linha)
    elif tipo == "cristal":
        haste("c", "s", 7, h)
        for y, linha in enumerate(("...KK...", "..KCCK..", ".KCEcCK.", "KCECCcCK", ".KCCcCK.", "..KCcK..", "...KK...")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "luz":
        for y in range(1, h - 9):
            g[y][2], g[y][3], g[y][4], g[y][5] = "G", "E", "E", "G"
        g[0][3], g[0][4] = "G", "G"
        for y in range(h - 9, h):
            g[y][2], g[y][3], g[y][4], g[y][5] = "K", "s" if y % 3 else "q", "q", "K"
        tampa(h - 9, "s", None, 3)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "estrela":
        haste("Y", "y", 7, h)
        for y, linha in enumerate(("...KK...", "...KYK..", "KKKYYKKK", "KYYEYYYK", ".KYYYYK.", ".KYKKYK.", "KK....KK")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "estetoscopio":                       # tubo azul em Y com campânula prateada embaixo
        for y in range(4, h - 7):
            g[y][3], g[y][4] = ("n", "N") if y % 4 else ("N", "n")
            g[y][2], g[y][5] = "K", "K"
        for y, linha in enumerate(("KKK..KKK", "KsK..KsK", ".KnK.Kn.", "..KnKnK.")):
            g[y] = list(linha)
        for y, linha in enumerate(("..KnnK..", ".KsssK..", "KsWWssK.", "KsWsssK.", ".KsssK..", "..KKK...", "........")):
            g[h - 7 + y] = list(linha)
    elif tipo == "lanca":                           # lança de madeira, ponta de ferro e flâmula vermelha
        haste("B", "b", 6, h)
        for y, linha in enumerate(("...KK...", "..KWsK..", "..KWsK..", ".KWWssK.", "..KWsK..", "..KKKK..")):
            g[y] = list(linha)
        for y, (a, b) in enumerate((("K", "R"), ("R", "R"), ("R", "r"), (".", "r"))):
            g[7 + y][0], g[7 + y][1] = a, b
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "bordao":                          # o bordão de madeira do caminhante, com o nó no alto
        haste("B", "b", 2, h)
        for y, linha in enumerate(("..KKKK..", ".KBBBbK.", ".KBBbbK.", "..KKKK..")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "seringa":
        haste("C", "c", 7, h - 6)
        for y in range(9, h - 6, 3):
            g[y][4] = "q"
        for y, linha in enumerate(("..KKKK..", "..KssK..", "KKKKKKKK", "KsssssK.", "...KK...", "...Ks...", "...Ks...")):
            g[y] = list(linha)
        for y, linha in enumerate(("..KKKK..", "...KK...", "...KK...", "...Ks...", "...KK...", "...K....")):
            g[h - 6 + y] = list(linha)
    elif tipo == "martelo":
        haste("s", "q", 6, h)
        for y, linha in enumerate(("KKKKKKK.", "KRRRRRRK", ".KRRRRK.", "..KRRK..", "...KK...", "..KsqK..")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    elif tipo == "lanterna":
        haste("s", "q", 8, h)
        for y, linha in enumerate(("..KKKK..", ".KEEEEK.", ".KYEEYK.", ".KKKKKK.", "..KssK..", "..KsqK..", "..KqqK..",
                                   "..KsqK..")):
            g[y] = list(linha)
        g[h - 1][2:6] = list("KKKK")
    else:
        return None
    return ["".join(r) for r in g]


_bast = {}
GRADES_EXTRA = []        # desenhos de bastão de outras edições (estudantes.py): fn(tipo, h) → linhas ou None


def bastao(tipo):
    if tipo not in _bast:
        rows = next((r for f in GRADES_EXTRA if (r := f(tipo, ALT_BASTAO))), None) or _grade_bastao(tipo)
        _bast[tipo] = None
        if rows:
            s = pygame.Surface((8, len(rows)), pygame.SRCALPHA)
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch in PAL_BASTAO:
                        cor = PAL_BASTAO[ch]
                        s.set_at((x, y), (*cor, 150) if (tipo == "luz" and ch == "G") else cor)
            _bast[tipo] = s
    return _bast[tipo]


# ------------------------------------------------------------------ nuvem
# Nuvem dourada (no espírito da Kintoun) no lugar das patas: bolhas circulares com
# contorno, brilho em cima e sombra laranja embaixo, e um rabicho que fica para trás.
NUV = {"K": PAL["K"], "1": (255, 250, 214), "2": (255, 226, 112), "3": (250, 184, 52), "4": (214, 120, 30)}
NUV_DOR = {"K": PAL["K"], "1": (236, 236, 244), "2": (196, 200, 214), "3": (150, 156, 178), "4": (110, 114, 138)}
# (x, y, raio) com o fundo da nuvem em y=0; x no canvas, virado à direita.
# Ordem = de trás para a frente: o rabicho, a fileira de cima, a fileira da frente.
RABO = [(-0.6, -6.5, 1.3), (1.0, -5.2, 2.0), (3.6, -4.2, 2.8)]
BOLHAS = [(9.5, -6.2, 3.9), (15.2, -8.6, 4.4), (21.6, -9.2, 4.7), (27.6, -7.6, 4.1), (31.4, -5.2, 3.2),
          (6.5, -3.4, 3.3), (12.5, -3.6, 4.2), (18.5, -3.4, 4.5), (24.5, -3.5, 4.3), (29.5, -3.0, 3.3)]
FRENTE = len(RABO) + 5   # índice da primeira bolha da fileira da frente
CHAO = ALT - 1           # última linha da nuvem


def _cor_nuvem(estilo, ch, px, py):
    n = NUVENS.get(estilo, NUVENS["dourada"])
    if ch == "K":
        return PAL["K"]
    ef = n.get("efeito")
    if ef == "arcoiris":
        faixas = [(240, 70, 80), (255, 150, 60), (255, 226, 80), (110, 210, 110), (90, 160, 250), (170, 110, 230)]
        base = faixas[min(5, max(0, (py - 29) * 6 // 14))]
        return _tons(base)[ch]
    if ef == "estrelas" and ch in "23" and ((px * 73856093) ^ (py * 19349663)) % 11 == 0:
        return (255, 255, 220)
    if ef == "raios" and ch == "4" and (px * 5 + py * 3) % 7 == 0:
        return (255, 232, 90)
    if ef == "fogo" and ch == "1" and (px + py) % 5 == 0:
        return (255, 255, 240)
    if ef == "neve" and ch in "123" and ((px * 92821) ^ (py * 68917)) % 9 == 0:
        return (255, 255, 255)
    if ef == "aurora":
        faixas = [(90, 230, 170), (110, 200, 220), (150, 140, 240), (200, 120, 230)]
        base = faixas[min(3, max(0, (px + py // 2) * 4 // LARG))]
        return _tons(base)[ch]
    if ef == "oceano":
        if ch in "12" and (py + (px // 3) % 2) % 4 == 0:
            return (230, 246, 255)                    # espuma
        return n["tons"][ch]
    if ef == "coracoes" and ch in "23":
        coracao = {(0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)}
        if ((px // 5) + (py // 5)) % 2 == 0 and (px % 5, py % 5) in coracao:
            return (230, 50, 110)
    return n["tons"][ch]


def _nuvem(sx=1.0, sy=1.0, onda=0.0, amp=0.0, rabo=(0.0, 0.0), dor=False, cx0=18, estilo="dourada"):
    """Rasteriza a nuvem. sx/sy = esticar (âncora no fundo, centro x=cx0); onda/amp = bolhas
    pulsando fora de fase; rabo = deslocamento extra do rabicho (dx, dy)."""
    bs = []
    for k, (x, y, r) in enumerate(RABO):
        f = (k + 1) / len(RABO)
        f = 1 - f + 1 / len(RABO)                    # a ponta (k=0) é a que mais se mexe
        bs.append((cx0 + (x - cx0) * sx + rabo[0] * f, CHAO + y * sy + rabo[1] * f + amp * 4 * math.sin(onda * 1.3 + k), r))
    for i, (x, y, r) in enumerate(BOLHAS):
        r2 = r * (1 + amp * math.sin(onda + i * 1.7))
        bs.append((cx0 + (x - cx0) * sx, CHAO + y * sy, r2 * (sx + sy) / 2))
    cor = NUV_DOR
    s = pygame.Surface((LARG, ALT), pygame.SRCALPHA)
    dono = {}                                        # pixel -> (bolha da frente, posição vertical nela)
    for py in range(min(ALT, CHAO + 1)):
        for px in range(LARG):
            for i in range(len(bs) - 1, -1, -1):
                bx, by, r = bs[i]
                if (px + 0.5 - bx) ** 2 + (py + 0.5 - by) ** 2 <= r * r:
                    dono[(px, py)] = (i, (py + 0.5 - by) / r)
                    break
    for (px, py), (i, v) in dono.items():
        viz = [dono.get((px + a, py + b)) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if None in viz:
            ch = "K"
        elif i >= FRENTE and v < -0.25 and any(d[0] < FRENTE for d in viz):   # dobra: frente × fileira de cima
            ch = "3"
        elif (px, py + 2) not in dono:
            ch = "4"
        else:
            ch = "1" if v < -0.45 else "3" if v > 0.55 else "2"
        s.set_at((px, py), cor[ch] if dor else _cor_nuvem(estilo, ch, px, py))
    return s


_nuv = {}


def nuvem(chave, **kw):
    if chave not in _nuv:
        _nuv[chave] = _nuvem(**kw)
    return _nuv[chave]


def _pose(estado, frame):
    """Como a nuvem se deforma e quanto o pônei sobe/desce. `frame` = contador do estado."""
    p = {"bob": 0, "corpo": PONEI, "cach": frame // 4,
         "nuv": dict(sx=1.0, sy=1.0, onda=0.0, amp=0.0, rabo=(0.0, 0.0)), "voo": 0, "esq": 1.0}
    n = p["nuv"]
    if estado == "parado":
        f = frame % 40
        p["voo"] = -1 if 10 <= f < 30 else 0            # a nuvem flutua devagar
        n.update(onda=f * math.tau / 40, amp=0.05, rabo=(0, (f // 10) % 2))
        if f >= 37:
            p["corpo"] = PONEI_PISCA
        p["cach"] = f // 10
    elif estado == "andar":
        k = frame % 4
        p["bob"] = (-1, 0, -1, 0)[k]
        n.update(onda=k * math.tau / 4, amp=0.09, rabo=(-3 - k % 2, -1 + k % 2))
        p["cach"] = k // 2
    elif estado == "abaixar":                            # nuvem achata e o pônei afunda nela (squash)
        k = min(frame, 3)
        n.update(sx=1.0 + 0.06 * k, sy=1.0 - 0.1 * k, onda=frame * 0.4, amp=0.04, rabo=(1, 1))
        p["bob"] = k
        p["esq"] = 1.0 - 0.06 * k
        p["corpo"] = PONEI_PISCA if (frame // 12) % 5 == 4 else PONEI
    elif estado == "decolar":                            # impulso: espreme e depois estica
        sq = (0.7, 0.8, 1.25, 1.3, 1.2, 1.1)[min(frame, 5)]
        n.update(sx=2 - sq if sq > 1 else 1 + (1 - sq) * 0.8, sy=sq, amp=0.06, onda=frame, rabo=(0, 3 * (sq > 1)))
        p["bob"] = round((1 - sq) * 8) if sq < 1 else 0
        p["esq"] = 1 + (sq - 1) * 0.3
        p["cach"] = 1
    elif estado == "pular":                              # estica para cima
        n.update(sx=0.92, sy=1.15, onda=frame * 0.8, amp=0.07, rabo=(-1, 4))   # rabicho escorre para baixo
        p["esq"] = 1.08
        p["cach"] = 1
    elif estado == "cair":                               # achata um pouco, de barriga na nuvem
        n.update(sx=1.12, sy=0.88, onda=frame * 0.6, amp=0.08, rabo=(-1, -3))  # infla e o rabicho sobe
        p["esq"] = 0.95
        p["cach"] = 0
    elif estado == "pousar":                             # amortece a queda
        sq = (0.62, 0.7, 0.82, 0.94, 1.04, 1.0)[min(frame, 5)]
        n.update(sx=1 + (1 - sq) * 0.9, sy=sq, amp=0.05, onda=frame, rabo=(2, 0))
        p["bob"] = max(0, round((1 - sq) * 8))
        p["esq"] = 1 + (sq - 1) * 0.4
    elif estado == "flutter":
        k = frame % 2
        n.update(sx=(1.06, 0.94)[k], sy=(0.9, 1.1)[k], onda=k * 3, amp=0.12, rabo=(-2, 2 * k))
        p["corpo"] = PONEI_BOCA if k else PONEI
        p["esq"] = (0.96, 1.04)[k]
        p["cach"] = k
    elif estado == "pound":
        n.update(sx=0.86, sy=1.2, amp=0.1, onda=frame * 1.5, rabo=(3, -4))
        p["bob"] = -1
        p["esq"] = 1.06
        p["corpo"] = PONEI_PISCA
    elif estado in ("lingua", "mirar"):
        p["corpo"] = PONEI_BOCA
        n.update(onda=frame * 0.3, amp=0.04)
    elif estado == "dor":
        p["corpo"] = PONEI_SUSTO
        n.update(sx=1.0 + 0.05 * (frame % 2), onda=frame * 2, amp=0.12, rabo=(-2, 1))
    p["sy"] = n["sy"]
    return p


def _estica(dest, g, esq, anc):
    """Squash & stretch do grupo montaria + cavaleiro: estica (esq > 1) duplicando linhas inteiras, achata (esq < 1)
    tirando linhas — sempre as que têm menos contorno K por perto, para a gola, o pescoço e a sela não
    engrossarem nem sumirem (escalar por vizinho mais próximo duplicava a linha preta do colarinho).
    `anc` = linha que fica parada (a sela). Desenha o resultado em `dest`."""
    k_cor = PAL["K"]
    caixa = g.get_bounding_rect()
    n = round(ALT * esq) - ALT
    if n == 0 or not caixa.height:
        dest.blit(g, (0, 0))
        return
    y0, y1 = caixa.top, caixa.bottom - 1
    custo = {}
    for y in range(y0, y1 + 1):
        custo[y] = sum(1 for x in range(LARG) if g.get_at((x, y))[:3] == k_cor and g.get_at((x, y))[3])
    escolhidas = set()
    for k in range(abs(n)):
        alvo = y0 + (y1 - y0) * (k + 0.5) / abs(n)
        cand = [y for y in range(int(alvo) - 2, int(alvo) + 3) if y0 <= y <= y1 and y not in escolhidas]
        if cand:
            escolhidas.add(min(cand, key=lambda y: (custo[y], abs(y - alvo))))
    ordem = []
    for y in range(ALT):
        if y in escolhidas:
            if n > 0:
                ordem += [y, y]
            continue                                   # n < 0: a linha some
        ordem.append(y)
    pos_anc = next((i for i, y in enumerate(ordem) if y >= anc), len(ordem))
    topo = anc - pos_anc
    for i, y in enumerate(ordem):
        dest.blit(g, (0, topo + i), (0, y, LARG, 1))


MAO_MONTA = (OX + 1 + 13, OY - 11 + 18)            # onde a mão segura o bastão
SENTADO_DX = -2                                     # corpo de pé (20 colunas) é mais largo que o do Doutor
MAO_SENTADO = (OX + SENTADO_DX + 18, OY - 11 - 1 + 18)


def _mao_xy(pid):
    return MAO_MONTA if PERSONAGENS[pid]["tipo"] == "monta" else MAO_SENTADO


def heroi(estado, frame, bebe=True, virado=1, visual=None):
    """Sprite 34x44 virado à direita; pivô = centro-baixo. `bebe` = o Doutor montado.
    `visual` = outro visual (prévia da loja); padrão: o equipado."""
    v = visual_valido(visual) if visual else VISUAL
    pal = _paleta(v)
    p = _pose(estado, frame)
    n = p["nuv"]
    chave_n = (round(n["sx"], 2), round(n["sy"], 2), round(n["onda"] % 6.2832, 1), n["amp"],
               tuple(round(v_) for v_ in n["rabo"]), estado == "dor", v["nuvem"])
    # na tela conceito o herói escolhido continua golpeando: quem é de pé gira a lança em vez do bastão
    golpe = estado == "lingua" and (golpeia(v) or (TRAJE[0] in MONTARIA_TRAJE and golpeia()))
    esq = round(p["esq"], 2)
    chave = (id(p["corpo"]), p["bob"], p["voo"], p["cach"] % 2, bebe, virado, chave_n,
             v["personagem"], v["bastao"], v["roupa"], frame % 40 >= 37 and estado == "parado", golpe,
             tuple(sorted(FIGURINO.items())), TRAJE[0], esq)
    if chave in _cache:
        return _cache[chave]
    s = pygame.Surface((LARG, ALT), pygame.SRCALPHA)
    # o pônei sobe junto com o topo da nuvem quando ela estica (e desce quando achata)
    b = p["bob"] + p["voo"] - round((p["sy"] - 1) * 9)
    g = s                                          # montaria + cavaleiro: grupo que estica/achata (squash & stretch)
    if esq != 1.0:
        g = pygame.Surface((LARG, ALT), pygame.SRCALPHA)
    bast = bastao(v["bastao"]) if bebe and not golpe else None     # no golpe o jogo desenha o bastão girando
    mx, my = _mao_xy(v["personagem"])
    dados = PERSONAGENS[v["personagem"]]
    montaria = MONTARIA_TRAJE.get(TRAJE[0]) or dados.get("montaria", "ponei")   # quem era "de pé" monta o pônei, sentado como o Doutor
    capi = montaria == "capivara"
    corpo = MONTARIAS[montaria].get(id(p["corpo"]), p["corpo"])
    pal_m = _pal_capi(pal) if capi else _pal_montaria(montaria, pal)
    g.blit(_s(corpo, pal_m), (OX, OY + b))
    dy = 1 if capi else 0                           # a capivara é mais baixa
    g.blit(_s(SELA), (OX + 5, OY + 11 + b + dy))
    if bast:
        g.blit(bast, (mx - 4, my - 22 + b + dy))
    if bebe:
        if dados["tipo"] == "monta":
            dout = _doutor(p["cach"], estado == "dor", pal, dados.get("chapeu", False))
            g.blit(dout, (OX + 1, OY - 11 + b + dy - (dout.get_height() - 28)))     # traje com chapéu alto sobe
        else:
            cara = "susto" if estado == "dor" else "pisca" if (estado == "parado" and frame % 40 >= 37) else ""
            sent = _sentado(v["personagem"], pal, cara)
            g.blit(sent, (OX + SENTADO_DX, OY - 11 + b + dy - (sent.get_height() - 28)))
    if g is not s:                                  # estica/achata em torno da sela (o pé do pônei some na nuvem)
        _estica(s, g, esq, OY + 11 + b + dy)
    nv = nuvem(chave_n, sx=n["sx"], sy=n["sy"], onda=n["onda"], amp=n["amp"], rabo=n["rabo"], dor=estado == "dor",
               estilo=v["nuvem"])
    s.blit(nv, (0, p["voo"]))
    if virado < 0:
        s = pygame.transform.flip(s, True, False)
    _cache[chave] = s
    return s


_RASTRO = {"arcoiris": [(255, 80, 80), (255, 170, 60), (255, 236, 90), (110, 220, 110), (90, 160, 255), (170, 110, 240)],
           "fogo": [(255, 120, 30), (255, 200, 60), (255, 250, 200)],
           "tempestade": [(255, 250, 140), (200, 220, 255)],
           "neve": [(255, 255, 255), (220, 236, 255)],
           "aurora": [(90, 230, 170), (150, 140, 240), (110, 200, 220)],
           "oceano": [(230, 246, 255), (120, 190, 255)],
           "coracoes": [(255, 110, 170), (255, 190, 220)]}


def rastro(visual=None):
    """(forma, cores) das faíscas que a nuvem equipada solta ao correr. forma: ponto | brilho | coracao | floco."""
    v = visual_valido(visual) if visual else VISUAL
    n = NUVENS[v["nuvem"]]
    ef = n.get("efeito")
    forma = {"coracoes": "coracao", "neve": "floco", "arcoiris": "brilho", "tempestade": "brilho",
             "aurora": "brilho"}.get(ef, "ponto")
    return forma, _RASTRO.get(ef) or [n["tons"]["1"], n["tons"]["2"]]


def golpeia(visual=None):
    """Personagens de pé atacam com golpe de bastão (o do pônei usa a língua do pônei)."""
    return PERSONAGENS[(visual or VISUAL)["personagem"]].get("montaria") != "ponei"   # a capivara não tem língua


def mao(visual=None, virado=1):
    """Posição da mão (pivô do bastão) no sprite 34x44 já virado, e o bastão equipado (ou None)."""
    v = visual or VISUAL
    mx, my = _mao_xy(v["personagem"])
    return (mx if virado > 0 else LARG - 1 - mx, my), bastao(v["bastao"])


def cabeca(visual=None):
    v = visual_valido(visual) if visual else VISUAL
    dados = PERSONAGENS[v["personagem"]]
    chave = ("icone", v["personagem"])
    if chave not in _spr:
        if dados["tipo"] == "pe":
            _spr[chave] = _em_pe(v["personagem"], _paleta(v)).subsurface((0, 0, 20, 14)).copy()
        elif dados["montaria"] == "capivara":
            _spr[chave] = _s(CAPI, _pal_capi(_paleta(v))).subsurface((11, 3, 20, 13)).copy()
        else:
            _spr[chave] = _s(PONEI).subsurface((11, 0, 20, 13)).copy()
    return _spr[chave]


def bebe(visual=None):
    v = visual_valido(visual) if visual else VISUAL
    dados = PERSONAGENS[v["personagem"]]
    if dados["tipo"] == "pe":
        return _sentado(v["personagem"], _paleta(v))
    return _doutor(0, pal=_paleta(v), chapeu=dados.get("chapeu", False))


def bebe_choro(visual=None):
    """Cabeça e ombros do personagem assustado (vai dentro da bolha)."""
    v = visual_valido(visual) if visual else VISUAL
    dados = PERSONAGENS[v["personagem"]]
    chave = ("bolha", v["personagem"], v["roupa"])
    if chave not in _spr:
        if dados["tipo"] == "pe":
            _spr[chave] = _em_pe(v["personagem"], _paleta(v), "susto").subsurface((2, 0, 16, 18)).copy()
        else:
            _spr[chave] = _doutor(0, True, _paleta(v), dados.get("chapeu", False)).subsurface((0, 0, 16, 18)).copy()
    return _spr[chave]
