"""Trajes do Doutor (o personagem montado, heroi.DOUTOR 16×28) para cada clima, desenhados no próprio sprite.

Cada traje parte do desenho do Doutor e troca o que precisa: o cabelo vira capuz, capacete ou fica sob um chapéu
(linhas do topo redesenhadas pixel a pixel), o jaleco e a camisa ganham outro tecido e outra cor, o cachecol de
arco-íris some ou muda, os sapatos viram galochas ou botas, e detalhes (botões, faixas refletivas, flores, estrelas,
listras) são pintados por cima. Assim o boneco continua o mesmo — só troca de roupa.

Letras novas (fora de heroi.PAL), definidas em CORES de cada traje: A/D/S tecido principal (meio, sombra, luz),
C/I detalhe, T/Q segundo tecido, X olho borrado, Z bota, V vidro, k contorno suave."""

# chave do clima → traje
POR_CLIMA = {"chuva": "capa_chuva", "tempestade": "capa_chuva", "neve": "parka", "aurora": "parka",
             "deserto": "safari", "floresta": "guarda", "praia": "praia", "espaco": "astronauta", "mar": "escafandro",
             "vulcao": "bombeiro", "carnaval": "magico", "cerejeira": "quimono", "noite": "pijama",
             "cristal": "mineiro", "outono": "sobretudo", "gotico": "cure",
             "frota": "frota", "samurai": "samurai", "neon": "neon", "colonia": "fuzileiro", "runico": "patrulheiro",
             "reino": "paladino"}

CABELO = set("hjd")
JALECO = set("Ww")
CAMISA = set("U")
CACHECOL = set("aceinv")
CALCA = set("p")
SAPATO = set("B")

TRAJES = {
    "capa_chuva": dict(
        cores={"A": (250, 206, 40), "D": (206, 150, 18), "S": (255, 238, 150), "Z": (60, 140, 76), "C": (30, 26, 36)},
        cabelo="capuz", jaleco="A", camisa="A", cachecol=None, sapato="Z",
        pontos=[(15, 8, "C"), (17, 8, "C"), (19, 8, "C"), (16, 5, "S"), (17, 5, "S"), (18, 5, "S")],
        topo=["....KKKKKKK.....", "...KASSSSAAK....", "..KASAAAAAAAKK.."]),
    "parka": dict(
        cores={"A": (200, 40, 52), "D": (140, 24, 36), "S": (236, 90, 96), "C": (244, 242, 236), "I": (196, 190, 184),
               "Z": (90, 60, 40)},
        cabelo="pelo", jaleco="A", camisa="D", cachecol="manter", sapato="Z",
        listras=[17, 19, 21], topo=["...KKKKKKKK.....", "..KCICCICCCK....", ".KCCICCCCCICK..."]),
    "safari": dict(
        cores={"A": (200, 172, 116), "D": (150, 122, 76), "S": (226, 204, 156), "T": (120, 92, 56), "Z": (96, 66, 40),
               "C": (90, 60, 34)},
        cabelo="chapeu", jaleco="A", camisa="S", cachecol=None, sapato="Z",
        pontos=[(17, 6, "D"), (17, 7, "D"), (17, 11, "D"), (17, 12, "D")],
        topo=["....KKKKKKK.....", "...KSSAAAAAK....", "KKKKTTTTTTTTKKKK", "KAAAAAAAAAAAAAAK"]),
    "guarda": dict(
        cores={"A": (82, 120, 70), "D": (54, 86, 48), "S": (120, 160, 96), "T": (110, 84, 52), "Z": (70, 50, 34),
               "C": (230, 200, 90)},
        cabelo="chapeu", jaleco="A", camisa="S", cachecol=None, sapato="Z",
        pontos=[(16, 11, "C"), (17, 6, "D"), (17, 7, "D")],
        topo=["....KKKKKKK.....", "...KSSAAAAAK....", "KKKKTTTTTTTTKKKK", "KAAAAAAAAAAAAAAK"]),
    "praia": dict(
        cores={"A": (250, 130, 50), "D": (210, 90, 30), "S": (255, 200, 120), "C": (255, 255, 255), "I": (60, 200, 210),
               "T": (236, 200, 104), "Q": (196, 150, 70), "Z": (236, 200, 104), "X": (16, 14, 22)},
        cabelo="palha", jaleco="A", camisa="A", cachecol=None, sapato="Z", oculos=True,
        pontos=[(16, 6, "C"), (18, 9, "I"), (16, 11, "C"), (19, 7, "I"), (17, 12, "C"), (20, 10, "C")],
        topo=["....KKKKKKKK....", "...KTTTTTTTTK...", ".KKQQQQQQQQQQKK.", "KTTTTTTTTTTTTTTK"]),
    "astronauta": dict(
        cores={"A": (236, 238, 244), "D": (176, 182, 200), "S": (255, 255, 255), "C": (230, 70, 60), "I": (70, 120, 220),
               "V": (120, 180, 230), "Z": (176, 182, 200)},
        cabelo="capacete", jaleco="A", camisa="A", cachecol=None, sapato="Z",
        pontos=[(16, 7, "C"), (16, 8, "I"), (17, 7, "I"), (17, 8, "C"), (19, 9, "D"), (19, 10, "D")]),
    "escafandro": dict(
        cores={"A": (40, 70, 110), "D": (24, 44, 74), "S": (70, 110, 150), "C": (210, 140, 60), "I": (150, 90, 30),
               "V": (120, 200, 210), "Z": (24, 44, 74)},
        cabelo="cobre", jaleco="A", camisa="A", cachecol=None, sapato="Z",
        pontos=[(16, 8, "C"), (16, 9, "C"), (16, 10, "C")]),
    "bombeiro": dict(
        cores={"A": (150, 112, 60), "D": (110, 80, 40), "S": (186, 148, 90), "C": (250, 236, 90), "I": (200, 40, 40),
               "T": (150, 20, 24), "Z": (30, 26, 34)},
        cabelo="chapeu", jaleco="A", camisa="A", cachecol=None, sapato="Z", listras_cor="C", listras=[18, 20],
        topo=["....KKKKKKK.....", "...KIIIIIIIK....", ".KKITTTTTTTIKK..", "KIIIIIIIIIIIIIIK"]),
    "magico": dict(
        cores={"A": (30, 26, 40), "D": (16, 12, 24), "S": (60, 54, 74), "C": (255, 255, 255), "I": (200, 24, 44),
               "T": (16, 12, 24), "Q": (200, 24, 44)},
        cabelo="cartola", jaleco="A", camisa="C", cachecol="capa", sapato="B",
        pontos=[(15, 9, "I"), (15, 10, "I")],
        topo=["....KKKKKKK.....", "....KTTTTTK.....", "....KQQQQQK.....", "..KKTTTTTTTKK..."]),
    "quimono": dict(
        cores={"A": (246, 150, 186), "D": (210, 100, 146), "S": (255, 206, 222), "C": (120, 40, 90), "I": (255, 255, 255),
               "T": (250, 200, 70)},
        cabelo="flor", jaleco="A", camisa="S", cachecol=None, sapato="B", faixa=(19, "C"),
        pontos=[(16, 4, "I"), (17, 12, "I"), (21, 6, "I")]),
    "pijama": dict(
        cores={"A": (90, 110, 200), "D": (60, 76, 150), "S": (140, 160, 236), "C": (255, 240, 150), "I": (240, 240, 250),
               "T": (90, 110, 200), "Q": (60, 76, 150)},
        cabelo="touca", jaleco="A", camisa="S", cachecol=None, sapato="B",
        pontos=[(16, 6, "C"), (18, 11, "C"), (20, 7, "C"), (17, 9, "I")],
        topo=["..I.............", ".KIK............", "..KTTTKKKK......", "..KTQTTTTTTKK..."]),
    "mineiro": dict(
        cores={"A": (70, 90, 150), "D": (46, 60, 110), "S": (110, 130, 190), "C": (250, 210, 60), "I": (180, 140, 30),
               "T": (250, 210, 60), "Q": (255, 255, 220), "Z": (70, 50, 34)},
        cabelo="chapeu", jaleco="A", camisa="S", cachecol=None, sapato="Z",
        topo=["....KKKKKKK.....", "...KTTTTTTQK....", "..KTTTTTTTQQK...", ".KIIIIIIIIIIIK.."]),
    "sobretudo": dict(
        cores={"A": (140, 96, 60), "D": (100, 66, 40), "S": (176, 130, 86), "C": (236, 140, 40), "I": (200, 100, 30),
               "T": (120, 40, 60), "Q": (90, 28, 44)},
        cabelo="boina", jaleco="A", camisa="S", cachecol="laranja", sapato="B",
        topo=["................", "...KKKKKKKK.....", "..KTTTTTTTTKK...", ".KTQTTTTTTTTTK.."]),
    # The Cure (Robert Smith): cabelo armado e espetado, pele de giz, olho borrado, batom vermelho, sobretudo preto
    "cure": dict(
        cores={"A": (24, 20, 30), "D": (12, 10, 16), "S": (46, 40, 56), "C": (236, 232, 240), "I": (190, 14, 36),
               "X": (40, 34, 48), "h": (10, 8, 14), "j": (40, 36, 48), "d": (4, 4, 8), "F": (238, 234, 240),
               "f": (196, 190, 206), "M": (210, 14, 40), "N": (8, 6, 12)},
        cabelo="manter", jaleco="A", camisa="C", cachecol="preto", sapato="B", olho_borrado=True, batom=True,
        topo=["K.KK.KK.KK.K....", ".KhjKhhKjhKhK...", "KhhhhjhhhhhhhKK.", "hhjhhhhhhhjhhhhK"]),
    # --- trajes dos climas temáticos
    # túnica de veludo dourado da frota (anos 70): gola preta, insígnia, calça e botas pretas, costeletas
    "frota": dict(
        cores={"A": (228, 184, 56), "D": (172, 132, 28), "S": (250, 220, 112), "C": (22, 20, 28), "I": (236, 236, 246),
               "Z": (22, 20, 28), "p": (28, 26, 34), "E": (236, 236, 246)},
        cabelo="manter", jaleco="A", camisa="C", cachecol=None, sapato="Z", gola="C",
        pontos=[(17, 11, "I"), (18, 11, "I"), (17, 12, "I")], rosto=[(7, 5, "h"), (8, 5, "h"), (9, 5, "h")]),
    # samurai: armadura laqueada de vermelho com cordões, elmo de ferro com crescente dourado, hakama escura
    "samurai": dict(
        cores={"A": (178, 30, 38), "D": (112, 16, 26), "S": (222, 72, 66), "T": (66, 62, 78), "Q": (130, 124, 144),
               "C": (242, 192, 64), "I": (236, 230, 220), "Z": (206, 176, 116), "p": (40, 40, 70)},
        cabelo="kabuto", jaleco="A", camisa="T", cachecol=None, sapato="Z", listras=[16, 18, 20], listras_cor="T",
        pontos=[(17, 9, "C"), (19, 9, "C"), (21, 9, "C")],
        topo=["..CC.......CC...", "...CCC...CCC....", "..KKQQQCCQQQKK..", "KCQQQQQQQQQQQQCK"]),
    # cyberpunk: jaqueta amarela e preta de gola alta, visor ciano, cabelo neon e implantes que brilham
    "neon": dict(
        cores={"A": (250, 210, 40), "D": (190, 148, 18), "S": (255, 240, 140), "C": (20, 18, 28), "I": (60, 240, 255),
               "X": (60, 240, 255), "Z": (236, 236, 244), "p": (30, 28, 40), "h": (236, 56, 168), "j": (255, 132, 210),
               "d": (140, 20, 108)},
        cabelo="manter", jaleco="A", camisa="C", cachecol=None, sapato="Z", oculos=True, gola="C",
        listras=[19], listras_cor="C", pontos=[(16, 11, "I"), (17, 11, "C"), (18, 11, "C")],
        rosto=[(11, 6, "I"), (12, 7, "I")]),
    # fuzileiro da colônia: armadura motorizada azul-aço, capacete-cúpula com visor laranja, faixa de alerta
    "fuzileiro": dict(
        cores={"A": (74, 104, 164), "D": (42, 62, 112), "S": (136, 164, 214), "V": (252, 160, 44), "C": (240, 200, 60),
               "T": (40, 44, 60), "Z": (40, 50, 82), "p": (52, 72, 122)},
        cabelo="capacete", visor_cheio=True, jaleco="A", camisa="T", cachecol=None, sapato="Z", listras=[18], listras_cor="D",
        pontos=[(16, 6, "C"), (16, 7, "T"), (16, 8, "C"), (20, 10, "C"), (20, 11, "T")]),
    # patrulheiro da masmorra: armadura verde-oliva, bandoleira de couro, runa acesa no peito, cabelo raspado
    "patrulheiro": dict(
        cores={"A": (98, 102, 62), "D": (64, 66, 40), "S": (134, 138, 86), "T": (112, 76, 42), "C": (250, 140, 40),
               "Z": (42, 32, 26), "p": (72, 58, 42), "h": (42, 32, 26), "j": (72, 56, 42), "d": (26, 18, 14)},
        cabelo="manter", jaleco="A", camisa="T", cachecol=None, sapato="Z",
        pontos=[(16, 6, "T"), (17, 7, "T"), (18, 8, "T"), (19, 9, "T"), (20, 10, "T"), (21, 11, "T"),
                (17, 11, "C"), (18, 11, "C"), (18, 12, "C")]),
    # paladino do reino: armadura de prata com friso dourado, sobreveste azul, capa azul voando, cabelo louro
    "paladino": dict(
        cores={"A": (198, 202, 216), "D": (132, 138, 158), "S": (244, 246, 252), "T": (44, 72, 172), "C": (242, 198, 72),
               "Z": (132, 138, 158), "p": (132, 138, 158), "h": (204, 162, 72), "j": (242, 208, 112), "d": (142, 102, 42)},
        cabelo="manter", jaleco="A", camisa="T", cachecol=None, sapato="Z", faixa=(20, "C"),
        pontos=[(16, 8, "C"), (17, 8, "C"), (17, 7, "C"), (17, 9, "C"), (18, 8, "C")]),
}


def _troca(ch, mapa):
    return mapa.get(ch, ch)


def aplicar(linhas, nome):
    """Linhas do Doutor (16 colunas, já com o cachecol do quadro) → linhas com o traje (pode ter linhas a mais no
    topo, que sobem o desenho). Devolve (linhas, quantas linhas foram acrescentadas em cima)."""
    t = TRAJES[nome]
    rows = [list(l.ljust(16, ".")) for l in linhas]
    cab = t.get("cabelo")
    for y in range(15):                                   # cabeça
        for x in range(16):
            ch = rows[y][x]
            if ch in CABELO:
                if cab == "kabuto":                       # cabelo vira o ferro do elmo e o protetor de nuca
                    rows[y][x] = {"j": "Q", "h": "T", "d": "T"}[ch]
                elif cab in ("capuz", "pelo", "capacete", "cobre"):
                    luz, meio, sombra = {"capuz": "SAD", "pelo": "CCI", "capacete": "SAD", "cobre": "CIC"}[cab]
                    rows[y][x] = {"j": luz, "h": meio, "d": sombra}[ch]
    if cab in ("capuz", "pelo"):                          # o capuz abraça o rosto: aba na testa e lateral na bochecha
        aba, lado = ("A", "D") if cab == "capuz" else ("C", "I")
        for x in range(7, 14):
            if rows[5][x] in "Ff":
                rows[5][x] = aba
        for y in range(6, 14):
            for x in range(4, 8):
                if rows[y][x] == "f":
                    rows[y][x] = lado
        if cab == "capuz":                                # cordão do capuz
            rows[13][9] = rows[13][9] if rows[13][9] == "K" else "D"
            rows[14][9] = "D"
    if cab in ("capacete", "cobre"):                      # capacete-cúpula com visor (astronauta, escafandro)
        casca, luz, borda = ("A", "S", "D") if cab == "capacete" else ("C", "I", "I")
        for y in range(15):
            for x in range(16):
                d = ((x + 0.5 - 8) ** 2 + (y + 0.5 - 7.5) ** 2) ** 0.5
                viz = ((x + 0.5 - 10.5) / 4.6) ** 2 + ((y + 0.5 - 8.5) / 3.8) ** 2
                if d > 8.2:
                    rows[y][x] = "."
                elif d > 7.3:
                    rows[y][x] = "K"
                elif viz <= 1:
                    if rows[y][x] not in "FfNMK" or t.get("visor_cheio"):
                        rows[y][x] = "V"
                    if (x - y) in (2, 3) and viz < 0.7:
                        rows[y][x] = "S" if cab == "capacete" else "V"
                elif viz <= 1.45:
                    rows[y][x] = borda
                else:
                    rows[y][x] = luz if (x < 6 and y < 6) else casca
        if cab == "cobre":                                # parafusos do escafandro
            for y, x in ((3, 3), (12, 3), (2, 9), (13, 6)):
                rows[y][x] = "K"
    if t.get("oculos"):                                   # óculos escuros: lentes cheias
        for y in (7, 8, 9, 10):
            for x in range(6, 16):
                if rows[y][x] in "F" and (rows[y][x - 1] == "N" or rows[y][min(15, x + 1)] == "N"):
                    rows[y][x] = "X"
            for x in range(6, 16):
                if rows[y][x] == "N":
                    rows[y][x] = "X"
    if t.get("olho_borrado"):                             # delineador borrado em volta dos óculos
        for y in (7, 10, 11):
            for x in range(6, 15):
                if rows[y][x] in "F" and (rows[y - 1][x] == "N" or rows[min(13, y + 1)][x] == "N"):
                    rows[y][x] = "X"
    if t.get("batom"):                                    # batom vermelho borrado passando do lábio
        for x in range(9, 15):
            if rows[12][x] == "M":
                rows[12][x] = "I"
        if rows[12][13] in "F":
            rows[12][13] = "I"
        if rows[13][10] in "Ff":
            rows[13][10] = "I"
    for y in range(15, len(rows)):                        # corpo
        for x in range(16):
            ch = rows[y][x]
            if ch in JALECO:
                rows[y][x] = t["jaleco"] if ch == "W" else "D"
            elif ch in CAMISA:
                rows[y][x] = t["camisa"]
            elif ch in CACHECOL:
                cc = t.get("cachecol")
                if cc is None:
                    rows[y][x] = "."
                elif cc == "preto":
                    rows[y][x] = "D" if (x + y) % 3 else "I"
                elif cc == "capa":                        # capa de mágico: vermelha por fora
                    rows[y][x] = "I"
                elif cc == "laranja":
                    rows[y][x] = "C" if y % 2 else "I"
            elif ch in SAPATO and t.get("sapato") and t["sapato"] != "B":
                rows[y][x] = t["sapato"]
    for ly in t.get("listras", []):                       # costuras da parka / faixas refletivas
        if ly < len(rows):
            for x in range(16):
                if rows[ly][x] in "A":
                    rows[ly][x] = t.get("listras_cor", "D")
    if t.get("faixa"):                                    # obi do quimono
        ly, cor = t["faixa"]
        for x in range(16):
            if rows[ly][x] in "ASD":
                rows[ly][x] = cor
    if t.get("gola"):                                     # gola fechada no pescoço (frota, jaqueta neon)
        for x in range(16):
            if rows[15][x] in "ASD":
                rows[15][x] = t["gola"]
    for y, x, cor in t.get("rosto", []):                  # costeletas, implantes no rosto
        if rows[y][x] in "Ff":
            rows[y][x] = cor
    for y, x, cor in t.get("pontos", []):                 # botões, flores, estrelas, emblemas
        if y < len(rows) and rows[y][x] in "ASDCT":
            rows[y][x] = cor
    if cab == "flor":                                     # florzinha de cerejeira no cabelo
        for y, x in ((2, 4), (1, 4), (3, 4), (2, 3), (2, 5)):
            rows[y][x] = "A" if (y, x) != (2, 4) else "T"
    topo = t.get("topo", [])
    extra = 0
    if topo:
        # o topo redesenhado cobre as primeiras linhas da cabeça; o que passar de 3 linhas sobe o desenho
        extra = max(0, len(topo) - 3)
        novo = [list(l.ljust(16, ".")) for l in topo]
        if cab in ("chapeu", "palha", "cartola", "touca", "boina", "manter", "kabuto"):
            base = rows
            for i, l in enumerate(novo):
                y = i - extra
                if y < 0:
                    continue
                for x, ch in enumerate(l):
                    if ch != "." or cab not in ("manter",):
                        if ch != "." or y < 2:
                            base[y][x] = ch
            rows = [list(l) for l in novo[:extra]] + base
        else:
            for i, l in enumerate(novo):
                for x, ch in enumerate(l):
                    rows[i][x] = ch
    return ["".join(r) for r in rows], extra


def cores(nome):
    return TRAJES[nome]["cores"]
