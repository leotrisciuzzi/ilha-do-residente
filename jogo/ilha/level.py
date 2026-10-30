"""Gerador procedural de fases em blocos (chunks), sempre jogável:
saltos ≤ 4 tiles de vão e ≤ 2 tiles de subida."""
import random

TILE = 16
H = 24
VAZIO, CHAO, PLAT, ESPINHO, BLOCO_OVO, TRONCO, BLOCO_USADO = 0, 1, 2, 3, 4, 5, 6


class Nivel:
    def __init__(self, seed, n_questoes=5, dificuldade=1.0, comprimento=None, castelo=False):
        self.seed = seed
        self.rng = rng = random.Random(seed)
        self.h = H
        self.w = comprimento or (120 + n_questoes * 26)
        self.tiles = [[VAZIO] * self.w for _ in range(H)]
        self.spawns = []        # (tipo, x_px, y_px, extra)
        self.castelo = castelo
        self.dif = dificuldade
        self.elenco = self._sortear_elenco()
        self._gerar(n_questoes)

    def _col(self, x, altura):
        for y in range(H - altura, H):
            self.tiles[y][x] = CHAO

    def solo_y(self, altura):
        return (H - altura) * TILE

    def add(self, tipo, tx, ty_px, extra=None):
        self.spawns.append((tipo, tx * TILE + TILE // 2, ty_px, extra))

    def _gerar(self, n_q):
        rng = self.rng
        h = 5
        x = 0
        # área inicial plana
        for _ in range(14):
            self._col(x, h)
            x += 1
        self.inicio = (4 * TILE, self.solo_y(h))
        fim = self.w - 22
        meio_x = fim // 2
        meio_feito = False
        # posições das questões espalhadas ao longo da fase
        alvos_q = [int(18 + (fim - 30) * (i + 0.5) / n_q) for i in range(n_q)]
        qi = 0
        vermelhas = sorted(rng.sample(range(20, fim - 10), 5))
        vi = 0
        while x < fim:
            tipo = rng.choices(
                ["plano", "vao", "degrau", "plataformas", "espinhos", "tronco", "bloco", "ondas"],
                [3, 2 * self.dif, 2, 2, 1 * self.dif, 1.2, 1, 1.5])[0]
            ini = x
            if tipo == "plano":
                n = rng.randint(5, 10)
                for _ in range(n):
                    self._col(x, h)
                    x += 1
                if rng.random() < 0.7:
                    self._inimigo(ini + n // 2, h)
                if rng.random() < 0.5:
                    self._arco_moedas(ini + 1, n - 2, self.solo_y(h) - 40)
            elif tipo == "vao":
                n = rng.randint(2, 4 if self.dif >= 1 else 3)
                x += n
                for k in range(n):
                    self.add("moeda", ini + k, self.solo_y(h) - 56)
                for _ in range(2):
                    self._col(x, h)
                    x += 1
            elif tipo == "degrau":
                h = max(2, min(9, h + rng.choice((-2, -1, 1, 2))))
                for _ in range(rng.randint(4, 7)):
                    self._col(x, h)
                    x += 1
                if rng.random() < 0.4:
                    self._inimigo(x - 2, h)
            elif tipo == "plataformas":
                n = rng.randint(8, 12)
                for _ in range(n):
                    self._col(x, h)
                    x += 1
                py = H - h - 4
                px = ini + 2
                for k in range(4):
                    if 0 <= py < H:
                        self.tiles[py][px + k] = PLAT
                self.add("moeda", px + 1, py * TILE - 12)
                self.add("moeda", px + 2, py * TILE - 12)
                if rng.random() < 0.6 and py - 3 > 2:
                    for k in range(3):
                        self.tiles[py - 3][px + 4 + k] = PLAT
                    self.add("estrela", px + 5, (py - 3) * TILE - 14)
            elif tipo == "espinhos":
                n = rng.randint(6, 9)
                for _ in range(n):
                    self._col(x, h)
                    x += 1
                for k in range(2):
                    self.tiles[H - h - 1][ini + 2 + k] = ESPINHO
            elif tipo == "tronco":
                n = rng.randint(7, 10)
                for _ in range(n):
                    self._col(x, h)
                    x += 1
                alt = rng.randint(1, 2)
                for k in range(alt):
                    for dx in (0, 1):
                        self.tiles[H - h - 1 - k][ini + 3 + dx] = TRONCO
                self.add("moeda", ini + 3, self.solo_y(h + alt) - 14)
            elif tipo == "bloco":
                n = rng.randint(6, 8)
                for _ in range(n):
                    self._col(x, h)
                    x += 1
                self.tiles[H - h - 4][ini + 3] = BLOCO_OVO
            elif tipo == "ondas":
                for _ in range(rng.randint(2, 3)):
                    h2 = max(2, min(9, h + rng.choice((-1, 1))))
                    for _ in range(3):
                        self._col(x, h2)
                        x += 1
                    h = h2
                if rng.random() < 0.6:
                    voador = [t for t in ("aedes", "morcego", "carrapato", "mosca", "cuspidor", "globulo", "aguaviva",
                                          "feiticeiro") if t in self.elenco]
                    t = rng.choice(voador) if voador else "aedes"
                    self.add(t, x - 3, self.solo_y(h) - (50 if t == "aedes" else 0))
            # questões, fichas vermelhas e anel do meio caem no chunk que cobre a posição
            while qi < n_q and alvos_q[qi] < x:
                cx, hh = self._chao_perto(min(max(alvos_q[qi], ini), x - 1))
                self.add("bicho_q", cx, self.solo_y(hh), qi)
                qi += 1
            while vi < 5 and vermelhas[vi] < x:
                cx = min(max(vermelhas[vi], ini), x - 1)
                _, hh = self._chao_perto(cx)
                alto = rng.choice((40, 56, 72))
                self.add("vermelha", cx, self.solo_y(hh) - alto)
                vi += 1
            if not meio_feito and x >= meio_x:
                hh = self._altura_em(x - 1)
                for _ in range(4):
                    self._col(x, hh)
                    x += 1
                self.meio = ((x - 2) * TILE, self.solo_y(hh))
                self.add("anel_meio", x - 2, self.solo_y(hh))
                meio_feito = True
                h = hh
        # final: arena do gigante + anel de chegada
        for _ in range(self.w - x):
            self._col(x, h)
            x += 1
        self.add("gigante", self.w - 14, self.solo_y(h))
        self.fim = ((self.w - 5) * TILE, self.solo_y(h))
        self.add("anel_fim", self.w - 5, self.solo_y(h))
        if not meio_feito:
            self.meio = self.inicio

    def _altura_em(self, x):
        for y in range(H):
            if self.tiles[y][x] == CHAO:
                return H - y
        return 0

    def _chao_perto(self, x):
        for d in range(0, 12):
            for c in (x - d, x + d):
                if 0 <= c < self.w and self._altura_em(c) and self.tiles[H - self._altura_em(c) - 1][c] == VAZIO:
                    return c, self._altura_em(c)
        return x, 5

    # elenco: cada fase tem um andarilho básico + 3 ou 4 especiais (peso = frequência na fase)
    ANDARILHOS = ["bacilo", "estafilococo"]
    ESPECIAIS = {"virus": 0.8, "aedes": 0.8, "estreptococo": 0.6, "fago": 0.7, "ameba": 0.7, "caixa": 0.4,
                 "comprimido": 0.6, "candida": 0.5, "carrapato": 0.5, "morcego": 0.6, "lombriga": 0.6,
                 # monstros (monstros.py), inspirados no Hollow Knight
                 "mosca": 1.1, "cuspidor": 1.0, "chifrudo": 1.1, "louva": 1.0, "colosso": 0.5, "globulo": 0.9,
                 "tatu": 1.0, "musgo": 0.9, "feiticeiro": 0.8, "aguaviva": 0.8}
    DIFICEIS = {"virus", "caixa", "candida", "estreptococo", "colosso", "feiticeiro", "cuspidor"}     # mais raros nas fases fáceis

    def _sortear_elenco(self):
        rng = self.rng
        tipos = list(self.ESPECIAIS)
        pesos = [self.ESPECIAIS[t] * (self.dif if t in self.DIFICEIS else 1.0) for t in tipos]
        esc = []
        while len(esc) < rng.choice((4, 5)) and tipos:
            i = rng.choices(range(len(tipos)), pesos)[0]
            esc.append(tipos.pop(i))
            pesos.pop(i)
        return {rng.choice(self.ANDARILHOS): 2.0, **{t: 1.0 for t in esc}}

    def _inimigo(self, tx, h):
        tipos = list(self.elenco)
        tipo = self.rng.choices(tipos, [self.elenco[t] for t in tipos])[0]
        y = self.solo_y(h) - (50 if tipo == "aedes" else 0)
        self.add(tipo, tx, y)

    def _arco_moedas(self, tx, n, y):
        for k in range(max(0, n)):
            off = int(((k - (n - 1) / 2) ** 2) * 2)
            self.add("moeda", tx + k, y + off)

    def solido(self, tx, ty):
        if tx < 0 or tx >= self.w:
            return True
        if ty < 0 or ty >= H:
            return False
        return self.tiles[ty][tx] in (CHAO, TRONCO, BLOCO_OVO, BLOCO_USADO)

    def tile(self, tx, ty):
        if 0 <= tx < self.w and 0 <= ty < H:
            return self.tiles[ty][tx]
        return VAZIO
