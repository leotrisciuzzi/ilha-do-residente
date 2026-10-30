"""Leitura de ECG: uma tira de DII longo (ilha/ecg.py) por vez, quatro ritmos para escolher e a explicação com as
medidas do próprio traçado (quadradinhos do RR, PR, largura do QRS).

O sorteio pesa mais os ritmos em que você erra; acertos e erros ficam em save.d["ecg"] = {ritmo: [acertos, erros]}.
Em cima, a tira inteira (10 s); embaixo, a lupa (toque na tira de cima para levar a lupa até ali, ◀ ▶ para andar)."""
import random

import pygame

from . import ecg
from .ui import AMARELO, H, RETRATO, TINTA, W, Estado, cortar, painel, quebrar, titulo_px

MOEDAS = 2
LUPA_S = 3800                     # ms de tira mostrados na lupa

# ritmos com que cada um se confunde (os distratores saem daqui primeiro)
PARECIDOS = {
    "sinusal": ["bav1", "tsv", "flutter", "fa"],
    "bav1": ["sinusal", "mobitz1", "mobitz2", "bavt"],
    "mobitz1": ["mobitz2", "bav1", "bavt", "fa"],
    "mobitz2": ["mobitz1", "bavt", "bav1", "sinusal"],
    "bavt": ["mobitz2", "mobitz1", "bav1", "sinusal"],
    "fa": ["flutter", "sinusal", "tsv", "mobitz1"],
    "flutter": ["fa", "tsv", "sinusal", "tv"],
    "tsv": ["tv", "flutter", "sinusal", "fa"],
    "tv": ["tsv", "torsades", "fv", "flutter"],
    "torsades": ["tv", "fv", "assistolia", "tsv"],
    "fv": ["torsades", "assistolia", "tv", "fa"],
    "assistolia": ["fv", "bavt", "torsades", "mobitz2"],
}

# o que fecha o diagnóstico no papel (CRITERIO), o que fazer (CONDUTA) e de onde veio (FONTE)
AHA = "AHA 2025 (Suporte Avançado de Vida no adulto)"
BRADI = "ACC/AHA/HRS 2018 (bradicardia e distúrbios de condução) e AHA 2025"
CRITERIO = {
    "sinusal": "Toda P é seguida de QRS; P positiva em DII; PR de 120 a 200 ms (3 a 5 quadradinhos) e fixo; QRS estreito "
               "(< 120 ms); RR regular. FC < 60 = bradicardia sinusal; > 100 = taquicardia sinusal.",
    "bav1": "Toda P conduz, mas o PR passa de 200 ms (mais de 5 quadradinhos) e é sempre o mesmo.",
    "mobitz1": "O PR alonga a cada batimento até uma P ficar sem QRS; o PR logo depois do bloqueio é o mais curto. "
               "Os RR encurtam antes da pausa e a pausa é menor que dois PP.",
    "mobitz2": "PR fixo (antes e depois da pausa) e, de repente, uma P não conduz. A pausa vale exatamente dois PP. "
               "QRS largo reforça bloqueio no His-Purkinje.",
    "bavt": "Dissociação AV: P regulares (PP fixo) e QRS regulares (RR fixo), mais P que QRS e PR que muda o tempo todo. "
            "Escape juncional = QRS estreito, 40–60 bpm; ventricular = QRS largo, 20–40 bpm.",
    "fa": "RR irregularmente irregular, sem onda P, linha de base com ondas f finas. FC: QRS em 10 s × 6.",
    "flutter": "Ondas F em dente de serra a ~300/min (1 a cada 5 quadradinhos), negativas em DII, DIII e aVF no flutter "
               "típico; o QRS sai a cada 2, 3 ou 4 ondas F. FC de 150 cravada = flutter 2:1 até prova em contrário.",
    "tsv": "Taquicardia de QRS estreito (< 120 ms), regular, em geral 150–250 bpm, sem P visível antes do QRS "
           "(a P retrógrada fica escondida no QRS ou logo depois dele).",
    "tv": "Taquicardia regular de QRS largo (≥ 120 ms) e monomórfico. Taquicardia de QRS largo é TV até prova em "
          "contrário, principalmente com cardiopatia estrutural.",
    "torsades": "TV polimórfica cujos QRS giram em torno da linha de base (amplitude cresce e diminui), disparada sobre um "
                "QT longo, muitas vezes depois de uma pausa (sequência curto-longo-curto).",
    "fv": "Ondulações caóticas, sem QRS, sem ritmo e sem linha de base. Paciente sem pulso.",
    "assistolia": "Linha praticamente reta, sem QRS. Antes de chamar de assistolia: protocolo da linha reta (cabos "
                  "conectados, ganho aumentado, outra derivação), para não deixar de chocar uma FV fina.",
}
CONDUTA = {
    "sinusal": "Ritmo normal. Bradi ou taquicardia sinusal se tratam pela causa (dor, febre, hipovolemia, drogas, "
               "hipotireoidismo…), não com antiarrítmico.",
    "bav1": "Não precisa de tratamento nem de marca-passo. Revise drogas que freiam o nó AV (betabloqueador, "
            "verapamil/diltiazem, digoxina). Marca-passo só se PR muito longo (> 300 ms) der sintomas.",
    "mobitz1": "Bloqueio no nó AV, em geral benigno (tônus vagal, atletas, sono, IAM inferior, drogas). Assintomático: "
               "observar e retirar drogas. Sintomático: atropina 1 mg IV (repete a cada 3–5 min, até 3 mg).",
    "mobitz2": "Bloqueio infranodal com risco de virar BAVT ou assistolia: marca-passo definitivo indicado mesmo sem "
               "sintomas (se não houver causa reversível). Instável: atropina pode ser tentada, mas costuma falhar → "
               "marca-passo transcutâneo ou adrenalina/dopamina em infusão até o transvenoso.",
    "bavt": "Instável: atropina 1 mg IV pode falhar (sobretudo com QRS largo) → marca-passo transcutâneo ou adrenalina/"
            "dopamina em infusão, depois transvenoso. Afastar causa reversível (IAM inferior, hipercalemia, drogas, "
            "Lyme); sem ela, marca-passo definitivo, mesmo sem sintomas.",
    "fa": "Instável (hipotensão, choque, congestão, isquemia) → cardioversão elétrica sincronizada já, começando com "
          "≥ 200 J. Estável: controle de FC com betabloqueador ou diltiazem/verapamil (estes não se FE ≤ 40% ou IC "
          "descompensada); amiodarona no doente grave. Anticoagulação pelo CHA₂DS₂-VA; FA > 24 h: 3 semanas de "
          "anticoagulação (ou ECO transesofágico) antes de cardioverter. Pré-excitação (WPW): nada que freia o nó AV.",
    "flutter": "Mesma lógica da FA: instável → cardioversão sincronizada (200 J iniciais); estável → controle de FC e "
               "anticoagulação pelo mesmo escore. Flutter típico recorrente: ablação do istmo cavotricuspídeo.",
    "tsv": "Estável: manobra vagal (Valsalva modificada: soprar e logo deitar com as pernas elevadas) → adenosina "
           "6 mg IV em bolus rápido com flush, 12 mg se não reverter → diltiazem/verapamil ou betabloqueador. "
           "Instável: cardioversão sincronizada (~100 J).",
    "tv": "Sem pulso: protocolo de FV/TV (desfibrilação). Com pulso e instável: cardioversão sincronizada (~100 J). "
          "Estável: amiodarona (150 mg IV em 10 min) ou procainamida; cardioversão se não reverter. Nunca "
          "verapamil/diltiazem em taquicardia de QRS largo; adenosina só se for regular e monomórfica.",
    "torsades": "Sulfato de magnésio 1–2 g IV (é com QT longo que o magnésio funciona). Instável ou sem pulso: "
                "desfibrilação (não sincronizada). Corrija K⁺ e Mg²⁺, suspenda drogas que alargam o QT; recorrente "
                "com bradicardia: aumentar a FC (marca-passo ou isoproterenol).",
    "fv": "Ritmo chocável: desfibrilação imediata e RCP por 2 min entre os choques. Adrenalina 1 mg a cada 3–5 min "
          "depois que os primeiros choques falharem; FV refratária: amiodarona 300 mg (depois 150 mg) ou lidocaína. "
          "Magnésio de rotina não.",
    "assistolia": "Não chocável: RCP de qualidade e adrenalina 1 mg o quanto antes, repetindo a cada 3–5 min. Procure "
                  "e trate os 5 H e 5 T. Marca-passo não ajuda na parada estabelecida.",
}
FONTE = {r: AHA for r in CRITERIO}
FONTE.update({"bav1": BRADI, "mobitz1": BRADI, "mobitz2": BRADI, "bavt": BRADI,
              "fa": "ESC 2024 (fibrilação atrial) e AHA 2025", "flutter": "ESC 2024 (fibrilação atrial) e AHA 2025",
              "tsv": "ESC 2019 (taquicardia supraventricular) e AHA 2025", "sinusal": "AHA 2025"})


def _estado(save):
    return save.d.setdefault("ecg", {})


def _medidas(s):
    """Texto com o que se mede no papel deste traçado."""
    q = ecg.QD
    partes = []
    r = s["ritmo"]
    if r in ("fv", "assistolia"):
        return "Sem QRS para medir."
    if r == "torsades":
        return "Antes do disparo, QT longo (~560 ms, 14 quadradinhos); depois, QRS largos de amplitude que cresce e diminui."
    if s["regular"] and s["n_rr"]:
        partes.append(f"RR de {s['n_rr']} quadradinhos → FC = 1500 ÷ {s['n_rr']} ≈ {s['fc']} bpm")
    else:
        partes.append(f"{ecg.contar_qrs(s)} QRS em 10 s × 6 ≈ {s['fc']} bpm")
    if r == "mobitz1":
        partes.append("PR de " + " → ".join(f"{p // q}" for p in s["prs"]) + " quadradinhos e então a P bloqueada")
    elif r == "mobitz2":
        partes.append(f"PR fixo de {s['pr'] // q} quadradinhos ({s['pr']} ms), 1 P bloqueada a cada {s['bloqueio']}")
    elif r == "bavt":
        partes.append(f"P a cada {s['pp'] // q} quadradinhos ({round(60000 / s['pp'])}/min), sem relação com o QRS; "
                      f"escape {s['escape']}")
    elif r == "flutter":
        partes.append(f"condução {s['conducao']}:1")
    elif s.get("pr"):
        partes.append(f"PR de {s['pr'] // q} quadradinhos ({s['pr']} ms)")
    if s.get("qrs_ms"):
        partes.append(f"QRS de {s['qrs_ms'] // q} quadradinhos ({s['qrs_ms']} ms)")
    return "; ".join(partes) + "."


class TreinoECG(Estado):
    def __init__(self, app):
        super().__init__(app)
        self.rng = random.Random()
        self.t = 0
        self.seq = 0
        self._novo()

    def _novo(self):
        st = _estado(self.app.save)
        ritmos = list(ecg.NOMES)
        pesos = []
        for r in ritmos:
            a, e = st.get(r, [0, 0])
            pesos.append(1 + 4 * (e + 1) / (a + e + 2) + (1.5 if a + e == 0 else 0))
        r = self.rng.choices(ritmos, pesos)[0]
        if r == getattr(self, "spec", {}).get("ritmo") and self.rng.random() < 0.7:
            r = self.rng.choices(ritmos, pesos)[0]               # evita repetir o mesmo ritmo seguido
        kw = {}
        if r == "flutter":
            kw["conducao"] = self.rng.choice([2, 2, 3, 4])
        elif r == "fv":
            kw["fv"] = self.rng.choice(["grossa", "grossa", "fina"])
        self.spec = ecg.montar(r, self.rng, **kw)
        dist = [x for x in PARECIDOS[r][:4]]
        self.rng.shuffle(dist)
        self.opcoes = dist[:3] + [r]
        self.rng.shuffle(self.opcoes)
        self.resposta = None
        self.t0 = 0.0
        self.rects = []
        self.r_prox = self.r_esq = self.r_dir = self.r_tira = pygame.Rect(0, 0, 0, 0)

    def _responder(self, i):
        if self.resposta is not None:
            return
        self.resposta = i
        r = self.spec["ritmo"]
        st = _estado(self.app.save)
        par = st.setdefault(r, [0, 0])
        save = self.app.save
        if self.opcoes[i] == r:
            par[0] += 1
            self.seq += 1
            save.d["carteira"]["moedas"] = save.d["carteira"].get("moedas", 0) + MOEDAS
            self.app.audio.tocar("moeda")
        else:
            par[1] += 1
            self.seq = 0
            self.app.audio.tocar("dano")
        save.salvar()

    def _andar(self, ms):
        self.t0 = max(0.0, min(ecg.DUR - LUPA_S, self.t0 + ms))

    # -- eventos
    def evento(self, e, inp):
        if inp.foi("voltar"):
            self.app.pop()
            return
        clique = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
        if clique and self.r_tira.collidepoint(e.pos):
            frac = (e.pos[0] - self.r_tira.x) / self.r_tira.w
            self.t0 = 0.0
            self._andar(frac * ecg.DUR - LUPA_S / 2)
        elif (clique and self.r_esq.collidepoint(e.pos)) or inp.foi("esq"):
            self._andar(-LUPA_S * 0.6)
        elif (clique and self.r_dir.collidepoint(e.pos)) or inp.foi("dir"):
            self._andar(LUPA_S * 0.6)
        elif e.type == pygame.MOUSEWHEEL:
            self._andar(-(e.x or e.y) * 400)
        elif self.resposta is not None:
            if (clique and self.r_prox.collidepoint(e.pos)) or inp.foi("ok"):
                self._novo()
        elif clique:
            for k, rr in enumerate(self.rects):
                if rr.collidepoint(e.pos):
                    self._responder(k)
        elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_4:
            self._responder(e.key - pygame.K_1)

    def update(self, inp):
        self.t += 1

    # -- desenho
    def _botao(self, tela, rr, txt, fundo, borda=TINTA, fonte=None):
        f = fonte or self.app.f["med"]
        pygame.draw.rect(tela, fundo, rr, border_radius=12)
        pygame.draw.rect(tela, borda, rr, 2, border_radius=12)
        t = f.render(cortar(txt, f, rr.w - 14), True, TINTA)
        tela.blit(t, t.get_rect(center=rr.center))

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        painel(tela, (12, 12, W - 24, H - 24))
        titulo_px(tela, "Leitura de ECG", AMARELO, W // 2, 24, 3)
        st = _estado(self.app.save)
        ac = sum(v[0] for v in st.values())
        tot = sum(v[0] + v[1] for v in st.values())
        cab = f"DII longo · 25 mm/s · 10 mm/mV  ·  {ac}/{tot} acertos" + (f"  ·  {self.seq} seguidos" if self.seq else "")
        t = f["peq"].render(cortar(cab, f["peq"], W - 60), True, (120, 100, 100))
        tela.blit(t, (W // 2 - t.get_width() // 2, 62))

        x, larg = 26, W - 52
        y = 90
        # tira inteira
        px_tira = larg / (ecg.DUR / ecg.QD)
        self.r_tira = pygame.Rect(x, y, larg, int(px_tira * 40))
        ecg.desenhar(tela, self.r_tira, self.spec, px_tira, rotulo="DII")
        jan = pygame.Rect(x + self.t0 / ecg.DUR * larg, y, LUPA_S / ecg.DUR * larg, self.r_tira.h)
        pygame.draw.rect(tela, (60, 110, 200), jan, 2)
        pygame.draw.rect(tela, (150, 130, 110), self.r_tira, 1)
        y = self.r_tira.bottom + 8
        # lupa
        px_lupa = larg / (LUPA_S / ecg.QD)
        alt_lupa = int(px_lupa * (36 if RETRATO else 26))
        lupa = pygame.Rect(x, y, larg, alt_lupa)
        ecg.desenhar(tela, lupa, self.spec, px_lupa, t0=self.t0, rotulo=f"lupa · {self.t0 / 1000:.1f}–{(self.t0 + LUPA_S) / 1000:.1f} s")
        pygame.draw.rect(tela, (150, 130, 110), lupa, 1)
        y = lupa.bottom + 8
        bw = 120
        self.r_esq = pygame.Rect(x, y, bw, 50)
        self.r_dir = pygame.Rect(x + larg - bw, y, bw, 50)
        self._botao(tela, self.r_esq, "◀", (226, 238, 255), (120, 150, 210))
        self._botao(tela, self.r_dir, "▶", (226, 238, 255), (120, 150, 210))
        dica = f["peq"].render(cortar("toque na tira de cima para mover a lupa", f["peq"], larg - 2 * bw - 20), True,
                               (120, 100, 100))
        tela.blit(dica, dica.get_rect(center=(W // 2, y + 25)))
        y += 62

        if self.resposta is None:
            t = f["med"].render("Qual é o ritmo?", True, TINTA)
            tela.blit(t, (x + 4, y))
            y += 36
        cols = 1 if RETRATO else 2
        alt = 58
        bl = (larg - 10 * (cols - 1)) // cols
        certo = self.opcoes.index(self.spec["ritmo"])
        self.rects = []
        mostrar = range(len(self.opcoes)) if self.resposta is None else sorted({certo, self.resposta})
        for n, k in enumerate(mostrar):                   # respondido: só a sua e a certa, para sobrar espaço
            rid = self.opcoes[k]
            c, l = n % cols, n // cols
            rr = pygame.Rect(x + c * (bl + 10), y + l * (alt + 8), bl, alt)
            fundo = (255, 252, 240)
            if self.resposta is not None:
                fundo = (190, 240, 190) if k == certo else (250, 190, 190) if k == self.resposta else (240, 236, 228)
            self._botao(tela, rr, f"{k + 1}. {ecg.NOMES[rid]}", fundo, fonte=f["q"])
            self.rects.append(rr)
        y += (-(-len(mostrar) // cols)) * (alt + 8) + 4

        if self.resposta is not None:
            ok = self.resposta == certo
            r = self.spec["ritmo"]
            cab = (f"Certo (+{MOEDAS} moedas)! " if ok else f"Era {ecg.NOMES[r]}. ")
            txt = (cab + CRITERIO[r] + "\n\nNeste traçado: " + _medidas(self.spec) + "\n\nConduta: " + CONDUTA[r]
                   + f"\n\nFonte: {FONTE[r]}.")
            sobra = H - 36 - 70 - y - 14
            for fonte in ((f["q"], f["peq"]) if RETRATO else (f["peq"],)):    # encolhe a letra antes de cortar
                lns = quebrar(txt, fonte, larg - 20)
                if len(lns) * (fonte.get_height() + 2) <= sobra:
                    break
            lns = lns[:max(1, sobra // (fonte.get_height() + 2))]
            caixa = pygame.Rect(x, y, larg, 14 + (fonte.get_height() + 2) * len(lns))
            pygame.draw.rect(tela, (226, 245, 226) if ok else (255, 236, 226), caixa, border_radius=12)
            pygame.draw.rect(tela, (120, 180, 120) if ok else (220, 140, 120), caixa, 2, border_radius=12)
            for k, ln in enumerate(lns):
                tela.blit(fonte.render(ln, True, TINTA), (x + 10, y + 7 + (fonte.get_height() + 2) * k))
            self.r_prox = pygame.Rect(x, min(caixa.bottom + 10, H - 36 - 60), larg, 60)
            self._botao(tela, self.r_prox, "Próximo traçado ▶", AMARELO)


def abrir(app):
    app.push(TreinoECG(app))
