"""Barquinho de papel — soltar o erro depois de entendê-lo.

Numa pedra na beira d'água há uma pilha de folhas. Ao interagir, a Lume dobra um barquinho que leva escrita a
questão errada mais recente do save (enunciado curto e a resposta certa). Depois que você lê, o barco vai para
a água, balança com as ondas e deriva devagar até o horizonte, diminuindo até sumir (~40 s). Se não houver erro
recente com enunciado conhecido, o barco leva a despedida de um erro antigo, já corrigido. Até 3 barcos na água.
"""
import math
import random
import re

import pygame

from . import Base
from .. import art
from ..mirante import GY, HZ, LW, WW

VIDA = 2400                      # quadros até sumir (~40 s a 60 qps)
MAX_BARCOS = 3

PAL = {"W": (226, 230, 246), "w": (168, 176, 214), "s": (110, 116, 168), "L": (255, 226, 170)}
# o barco em quatro tamanhos (de perto a longe); o último é só um pontinho claro
FORMAS = [
    ["....W....",
     "...WWw...",
     "..WWWww..",
     "LWWWWWWwW",
     ".swwwwws.",
     "..sssss.."],
    ["...W...",
     "..WWw..",
     "LWWWWwW",
     ".swwws."],
    ["..W..",
     "LWWwW",
     ".sws."],
    ["WWw"],
]

PEDRA = [
    "....aWWWWWa.....",
    "...aWwWWWWWa....",
    "..aWWWWwWWWWa...",
    "..bbbbbbbbbbbb..",
    ".bpppppppppppppb",
    "bppPPPPPPPPPpppb",
    "bpPPPPPPPPPPPPpb",
    ".bpppppppppppbb.",
    "..bbbbbbbbbbb...",
]
PAL_PEDRA = {"W": (210, 214, 236), "w": (160, 166, 206), "a": (122, 126, 170), "b": (16, 22, 36),
             "p": (52, 60, 86), "P": (72, 80, 112)}

DESPEDIDAS = [
    "Não sobrou erro recente para dobrar. Este barco leva um erro sem nome, de algum dia que já passou. Ele ensinou o que tinha para ensinar e pode ir.",
    "As folhas estão em branco: nenhum erro esperando. O barco vai assim mesmo, leve, só para lembrar que errar fez parte do caminho.",
]


def _limpo(txt, n):
    """Uma linha só, cortada numa palavra, com reticências se precisar."""
    txt = re.sub(r"\s+", " ", str(txt or "")).strip()
    if len(txt) <= n:
        return txt
    corte = txt[:n].rsplit(" ", 1)[0].rstrip(",;:.")
    return corte + "…"


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x0 = WW * 0.064
        self.lugares = [("barco_papel", self.x0, "dobrar um barquinho de papel")]
        self.pedra = art.spr(PEDRA, PAL_PEDRA)
        self.formas = [art.spr(f, PAL) for f in FORMAS]
        self.reflexos = []
        for s in self.formas:                                  # reflexo: de cabeça para baixo e escuro
            r = pygame.transform.flip(s, False, True)
            r.fill((90, 96, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
            r.set_alpha(70)
            self.reflexos.append(r)
        self.barcos = []          # [idade, deriva_x, fase]
        self.pendente = False     # barco dobrado, esperando a fala terminar para ir à água
        self.enviadas = set()
        self.desp_i = 0
        self.rng = random.Random()

    # ------------------------------------------------------------- o que vai escrito
    def _escrito(self):
        app = self.mirante.app
        q = app.save.d.get("q", {}) or {}
        banco = getattr(app, "banco", None)
        por_id = getattr(banco, "por_id", {}) if banco is not None else {}
        erradas = sorted(((st.get("ult", 0), qid) for qid, st in q.items()
                          if isinstance(st, dict) and not st.get("ok") and st.get("e", 0) and qid in por_id),
                         reverse=True)
        livres = [qid for _, qid in erradas if qid not in self.enviadas]
        if livres:
            qid = livres[0]
            self.enviadas.add(qid)
            qq = por_id[qid]
            try:
                letra = app.save.gabarito(qq)
            except Exception:
                letra = qq.get("gab", "")
            texto = ""
            for alt in qq.get("alts", ()) or ():
                try:
                    k, v = alt[0], alt[1]
                except Exception:
                    continue
                if k == letra:
                    texto = v
            tema = qq.get("subtema") or qq.get("materia") or ""
            p1 = "Você dobra uma folha em barquinho. Nela vai escrita a última questão que você errou"
            p1 += f", de {_limpo(tema, 50)}." if tema else "."
            p2 = f"“{_limpo(qq.get('enunciado', ''), 170)}”"
            resp = f"{letra}) {_limpo(texto, 110)}" if texto else (f"letra {letra}" if letra else "")
            p3 = (f"Embaixo, a resposta certa: {resp}." if resp else "Embaixo, um espaço para a resposta certa.")
            p3 += " Leia com calma até entender por que é essa."
            return [p1, p2, p3, "Pronto. Agora pode soltar o barco: o que ele tinha para ensinar ficou com você."]
        # sem erro recente: a despedida de um erro antigo, de preferência um que já virou acerto
        corrigidos = [(st.get("ult", 0), qid, st) for qid, st in q.items()
                      if isinstance(st, dict) and st.get("ok") and st.get("e", 0)]
        if corrigidos:
            _, qid, st = sorted(corrigidos)[self.desp_i % len(corrigidos)]
            self.desp_i += 1
            e = st.get("e", 0)
            vezes = f"{e} vez" if e == 1 else f"{e} vezes"
            if qid in por_id:
                trecho = _limpo(por_id[qid].get("enunciado", ""), 120)
                return [f"Este barco leva um erro antigo: “{trecho}”",
                        f"Você errou essa questão {vezes} e acertou na última. Ele pode ir; ficou o que ele ensinou."]
            return [f"Este barco leva um erro antigo, de uma questão que você errou {vezes} e depois acertou.",
                    "O enunciado ficou para trás. Ele pode ir; ficou o que ele ensinou."]
        frase = DESPEDIDAS[self.desp_i % len(DESPEDIDAS)]
        self.desp_i += 1
        return [frase]

    # ------------------------------------------------------------- ganchos
    def interagir(self, nome):
        if self.pendente:
            return
        if len(self.barcos) >= MAX_BARCOS:
            self.mirante._falar(["Já há três barquinhos na água. Espere um deles chegar ao horizonte antes de dobrar outro."])
            return
        self.mirante._falar(self._escrito())
        self.pendente = True

    def update(self):
        if self.pendente and not self.mirante.fala and not self.mirante.modal:
            self.pendente = False
            self.barcos.append([0, self.rng.uniform(-14, 22), self.rng.uniform(0, 6.28)])
        for b in self.barcos:
            b[0] += 1
        if self.barcos and self.barcos[0][0] >= VIDA:
            self.barcos = [b for b in self.barcos if b[0] < VIDA]

    def draw_lago(self, m, cam):
        t = self.mirante.t
        y_ini, y_fim = GY - 4, HZ + 1.5
        for idade, deriva, fase in self.barcos:
            p = idade / VIDA
            prof = 1 - (1 - p) ** 1.6                        # rápido perto, lento perto do horizonte
            y = y_ini + (y_fim - y_ini) * prof
            # parallax: quanto mais longe, menos o barco acompanha a câmera
            x = self.x0 + deriva * prof + math.sin(p * 9 + fase) * 3 - cam * (1 - 0.7 * prof)
            if not -12 < x < LW + 12:
                continue
            perto = 1 - prof
            y += math.sin(t * 0.06 + fase) * 0.7 * perto       # balança nas ondas
            x += math.sin(t * 0.023 + fase * 2) * 0.5 * perto
            i = 0 if prof < 0.18 else 1 if prof < 0.45 else 2 if prof < 0.78 else 3
            s, r = self.formas[i], self.reflexos[i]
            a = 255 if p < 0.82 else max(0, int(255 * (1 - p) / 0.18))
            bx, by = int(x - s.get_width() / 2), int(y - s.get_height())
            if r.get_height() > 1:
                r.set_alpha(int(70 * a / 255))
                m.blit(r, (bx + int(math.sin(t * 0.09 + fase)), by + s.get_height()))
            if a > 20 and i < 3:                                # o papel pega um pouco da luz
                m.blit(self.mirante.halo[3], (x - 3, by + s.get_height() / 2 - 3),
                       special_flags=pygame.BLEND_RGB_ADD)
            s.set_alpha(a)
            m.blit(s, (bx, by))
            s.set_alpha(255)

    def draw_margem(self, m, cam):
        x = self.x0 - cam
        if not -20 < x < LW + 20:
            return
        m.blit(self.pedra, (int(x - 8), GY - 6))
        if self.pendente:                                       # barquinho dobrado, pousado na pedra
            s = self.formas[1]
            m.blit(s, (int(x - 2), GY - 6 - s.get_height() + 1))
