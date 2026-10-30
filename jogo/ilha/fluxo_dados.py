"""Fluxogramas de gasometria e distúrbios hidroeletrolíticos: as árvores de decisão e os geradores de casos.

Cada árvore é um grafo de nós. Um nó de decisão tem uma pergunta, opções (rótulo do ramo + regra) e uma função
`decide(caso)` que diz qual ramo os NÚMEROS do caso mandam seguir; `explica(caso)` mostra a regra aplicada a esses
números. Folhas são diagnósticos. Alguns ramos CONVERGEM no mesmo nó seguinte e só deixam um "achado" anotado
(ex.: compensação inadequada = distúrbio respiratório associado), que entra no diagnóstico final.

Os geradores sorteiam um caso coerente para uma folha-alvo (pH calculado por Henderson-Hasselbalch a partir de
HCO₃⁻ e PaCO₂, ânion gap a partir de Na⁺, Cl⁻ e HCO₃⁻ etc.). O teste confere que percorrer a árvore com as
regras leva exatamente à folha-alvo, para todos os alvos e muitas sementes.

Regras: Berend et al. NEJM 2014 (roteiro ácido-base, Winter, compensações, Δ/Δ); Kraut e Madias 2010 (ânion gap,
gap osmolar, AG urinário, ATR); Spasovski et al. 2014 (diretriz europeia de hiponatremia); Adrogué e Madias NEJM
2000 (hipernatremia); Palmer e Clegg 2016/2017 (hipo e hipercalemia); UK Kidney Association 2023 (hipercalemia)."""
import math

# ------------------------------------------------------------------ estrutura


class No:
    def __init__(self, id, rotulo, pergunta, opcoes, decide, explica):
        self.id, self.rotulo, self.pergunta = id, rotulo, pergunta
        self.opcoes = opcoes            # [(rótulo do ramo, regra, destino, achado ou None)]
        self.decide, self.explica = decide, explica
        self.folha = False


class Folha:
    def __init__(self, id, rotulo, diagnostico, ensina):
        self.id, self.rotulo, self.diagnostico, self.ensina = id, rotulo, diagnostico, ensina
        self.folha = True


class Arvore:
    def __init__(self, id, nome, descricao, raiz, nos, gerar, alvos, contas, grupo="eletrolitos"):
        self.id, self.nome, self.descricao, self.raiz = id, nome, descricao, raiz
        self.grupo = grupo              # seção do menu: "eletrolitos" ou "asma"
        self.nos = {n.id: n for n in nos}
        self.gerar = gerar              # gerar(rng, alvo) -> caso
        self.alvos = alvos              # ids das folhas que o gerador sabe produzir
        self.contas = contas            # contas(caso) -> [(nome, valor)] mostradas no nível 1

    def percorrer(self, caso):
        """[(id do nó, índice da opção certa)] até a folha, e a folha."""
        caminho, no = [], self.nos[self.raiz]
        while not no.folha:
            i = no.decide(caso)
            caminho.append((no.id, i))
            no = self.nos[no.opcoes[i][2]]
            if len(caminho) > 20:
                raise RuntimeError("ciclo na árvore " + self.id)
        return caminho, no

    def achados(self, caminho):
        out = []
        for nid, i in caminho:
            a = self.nos[nid].opcoes[i][3]
            if a:
                out.append(a)
        return out


def f1(x):
    return f"{x:.1f}".replace(".", ",")


def f2(x):
    return f"{x:.2f}".replace(".", ",")


def fi(x):
    """Inteiro arredondado para cima no meio (12,5 → 13), como se faz à mão — round() do Python iria para o par."""
    return f"{math.floor(x + 0.5)}"


def ph_de(h, p):
    return 6.1 + math.log10(h / (0.03 * p))


# ================================================================== 1. ÁCIDO-BASE

def _ag(c):
    return c["na"] - c["cl"] - c["hco3"]


def _agc(c):
    return _ag(c) + 2.5 * (4.0 - c["alb"])


def _dd(c):
    return (_agc(c) - 12) / max(0.5, 24 - c["hco3"])


def _gap_osm(c):
    return c["osm"] - (2 * c["na"] + c["glic"] / 18 + c["ureia"] / 6)


def _agu(c):
    return c["na_u"] + c["k_u"] - c["cl_u"]


def _winter(c):
    return 1.5 * c["hco3"] + 8


def _comp_alc(c):
    return 0.7 * c["hco3"] + 21


def _resp_acid_esp(c):
    d = (c["pco2"] - 40) / 10
    return 24 + 1 * d, 24 + 3.5 * d


def _resp_alc_esp(c):
    d = (40 - c["pco2"]) / 10
    return 24 - 2 * d, 24 - 4.5 * d


def _ab_decide_raiz(c):
    return 0 if c["ph"] < 7.35 else 1 if c["ph"] > 7.45 else 2


def _ab_prim_acid(c):
    if c["hco3"] < 22 and c["pco2"] > 45:
        return 2
    return 0 if c["hco3"] < 22 else 1


def _ab_prim_alc(c):
    if c["hco3"] > 26 and c["pco2"] < 35:
        return 2
    return 0 if c["hco3"] > 26 else 1


def _ab_winter(c):
    e = _winter(c)
    return 1 if c["pco2"] > e + 2 else 2 if c["pco2"] < e - 2 else 0


def _ab_comp_alc(c):
    e = _comp_alc(c)
    return 1 if c["pco2"] > e + 2 else 2 if c["pco2"] < e - 2 else 0


def _ab_resp_acid(c):
    ea, ec = _resp_acid_esp(c)
    if c["hco3"] > ec + 2:
        return 2
    return 0 if abs(c["hco3"] - ea) <= abs(c["hco3"] - ec) else 1


def _ab_resp_alc(c):
    ea, ec = _resp_alc_esp(c)
    return 0 if abs(c["hco3"] - ea) <= abs(c["hco3"] - ec) else 1


def _ab_causa(c):
    if c["lact"] > 4:
        return 0
    if c["cet"]:
        return 1
    if _gap_osm(c) > 10:
        return 2
    return 3


def _ex_raiz(c):
    return f"pH {f2(c['ph'])}: abaixo de 7,35 é acidemia, acima de 7,45 é alcalemia; entre os dois, normal."


def _ex_prim_acid(c):
    return (f"HCO₃⁻ {fi(c['hco3'])} (baixo se < 22) e PaCO₂ {fi(c['pco2'])} (alta se > 45). Quem puxa o pH para baixo é o "
            "primário; se os dois puxam, é misto.")


def _ex_prim_alc(c):
    return (f"HCO₃⁻ {fi(c['hco3'])} (alto se > 26) e PaCO₂ {fi(c['pco2'])} (baixa se < 35). Quem puxa o pH para cima é o "
            "primário; se os dois puxam, é misto.")


def _ex_winter(c):
    e = _winter(c)
    return (f"Winter: PaCO₂ esperada = 1,5 × {fi(c['hco3'])} + 8 = {f1(e)} (faixa {f1(e - 2)} a {f1(e + 2)}). "
            f"A PaCO₂ medida é {fi(c['pco2'])}.")


def _ex_comp_alc(c):
    e = _comp_alc(c)
    return (f"PaCO₂ esperada = 0,7 × {fi(c['hco3'])} + 21 = {f1(e)} (faixa {f1(e - 2)} a {f1(e + 2)}). "
            f"A PaCO₂ medida é {fi(c['pco2'])}.")


def _ex_ag(c):
    return (f"AG = {fi(c['na'])} − ({fi(c['cl'])} + {fi(c['hco3'])}) = {fi(_ag(c))}; corrigido pela albumina "
            f"{f1(c['alb'])}: {fi(_ag(c))} + 2,5 × (4 − {f1(c['alb'])}) = {fi(_agc(c))}. Acima de 12 é alto.")


def _ex_dd(c):
    return (f"Δ/Δ = (AG corrigido − 12) / (24 − HCO₃⁻) = ({fi(_agc(c))} − 12) / (24 − {fi(c['hco3'])}) = {f1(_dd(c))}. "
            "Abaixo de 1: há também acidose de AG normal; de 1 a 2: pura; acima de 2: há alcalose metabólica junto.")


def _ex_causa(c):
    return (f"Lactato {f1(c['lact'])} (alto se > 4) · cetonas {'presentes' if c['cet'] else 'ausentes'} · gap osmolar "
            f"{fi(_gap_osm(c))} (alto se > 10) · ureia {fi(c['ureia'])}.")


def _ex_agu(c):
    return (f"AG urinário = Na⁺u + K⁺u − Cl⁻u = {fi(c['na_u'])} + {fi(c['k_u'])} − {fi(c['cl_u'])} = {fi(_agu(c))}. "
            "Negativo: o rim excreta amônio bem, a perda é intestinal. Positivo: o rim não acidifica, é ATR.")


def _ex_k_atr(c):
    return f"K⁺ {f1(c['k'])}: alto (> 5) aponta ATR tipo 4 (falta de aldosterona); baixo aponta ATR 1 ou 2."


def _ex_ph_u(c):
    return f"pH urinário {f1(c['ph_u'])}: acima de 5,5 em plena acidemia = rim distal não acidifica (tipo 1); até 5,5 = tipo 2."


def _ex_resp_acid(c):
    ea, ec = _resp_acid_esp(c)
    return (f"PaCO₂ {fi(c['pco2'])}: HCO₃⁻ esperado agudo = 24 + 1 por 10 = {f1(ea)}; crônico = 24 + 3,5 por 10 = {f1(ec)}. "
            f"Medido: {fi(c['hco3'])}. Mais perto do agudo = aguda; mais perto do crônico = crônica; mais de 2 acima do "
            "crônico = alcalose metabólica associada.")


def _ex_resp_alc(c):
    ea, ec = _resp_alc_esp(c)
    return (f"PaCO₂ {fi(c['pco2'])}: HCO₃⁻ esperado agudo = 24 − 2 por 10 = {f1(ea)}; crônico = 24 − 4,5 por 10 = {f1(ec)}. "
            f"Medido: {fi(c['hco3'])}. O mais próximo dos dois indica a fase.")


def _ex_cl_u(c):
    return f"Cl⁻ urinário {fi(c['cl_u'])}: abaixo de 20 = responde a soro (o rim está segurando cloro e volume)."


def _ex_pa(c):
    return f"PA {fi(c['pa'])} mmHg de sistólica: hipertensão com alcalose e hipocalemia aponta excesso de mineralocorticoide."


def _ex_normal(c):
    return (f"HCO₃⁻ {fi(c['hco3'])} (normal 22–26) e PaCO₂ {fi(c['pco2'])} (normal 35–45). pH normal com valores "
            "alterados = dois distúrbios que se anulam.")


AB_NOS = [
    No("ph", "pH", "Olhe o pH. O sangue está ácido, alcalino ou normal?",
       [("Acidemia", "pH < 7,35", "prim_acid", None), ("Alcalemia", "pH > 7,45", "prim_alc", None),
        ("pH normal", "7,35 a 7,45", "normais", None)], _ab_decide_raiz, _ex_raiz),
    No("prim_acid", "Primário", "Acidemia. Quem explica o pH baixo?",
       [("Metabólica", "HCO₃⁻ < 22", "winter", None), ("Respiratória", "PaCO₂ > 45", "resp_acid", None),
        ("Mista", "os dois", "f_acid_mista", None)], _ab_prim_acid, _ex_prim_acid),
    No("winter", "Compensação", "Acidose metabólica. A PaCO₂ compensou como esperado (Winter)?",
       [("Adequada", "dentro de ±2", "ag", None),
        ("PaCO₂ acima", "> esperado + 2", "ag", "acidose respiratória associada"),
        ("PaCO₂ abaixo", "< esperado − 2", "ag", "alcalose respiratória associada")], _ab_winter, _ex_winter),
    No("ag", "Ânion gap", "Calcule o ânion gap (corrigido pela albumina). Ele está alto ou normal?",
       [("AG alto", "corrigido > 12", "dd", None), ("AG normal", "corrigido ≤ 12", "agu", None)],
       lambda c: 0 if _agc(c) > 12 else 1, _ex_ag),
    No("dd", "Delta-delta", "AG alto. O delta-delta esconde outro distúrbio metabólico?",
       [("Δ/Δ < 1", "também AG normal", "causa", "acidose de AG normal associada"),
        ("Δ/Δ 1 a 2", "AG alto pura", "causa", None),
        ("Δ/Δ > 2", "alcalose junto", "causa", "alcalose metabólica associada")],
       lambda c: 0 if _dd(c) < 1 else 2 if _dd(c) > 2 else 1, _ex_dd),
    No("causa", "Qual ácido?", "Qual ácido entrou? Olhe lactato, cetonas, gap osmolar e ureia.",
       [("Lática", "lactato > 4", "f_latica", None), ("Cetoacidose", "cetonas +", "f_ceto", None),
        ("Álcool tóxico", "gap osmolar > 10", "f_alcool", None), ("Urêmica", "ureia muito alta", "f_uremia", None)],
       _ab_causa, _ex_causa),
    No("agu", "AG urinário", "AG normal (hiperclorêmica). Rim ou intestino? Calcule o AG urinário.",
       [("Negativo", "Na⁺u + K⁺u < Cl⁻u", "f_diarreia", None), ("Positivo", "Na⁺u + K⁺u > Cl⁻u", "k_atr", None)],
       lambda c: 0 if _agu(c) < 0 else 1, _ex_agu),
    No("k_atr", "Potássio", "É acidose tubular renal. O potássio está alto ou baixo?",
       [("K⁺ alto", "> 5", "f_atr4", None), ("K⁺ baixo", "< 3,5", "ph_u", None)],
       lambda c: 0 if c["k"] > 5 else 1, _ex_k_atr),
    No("ph_u", "pH urinário", "ATR com potássio baixo. O rim consegue acidificar a urina?",
       [("pH u > 5,5", "não acidifica", "f_atr1", None), ("pH u ≤ 5,5", "acidifica", "f_atr2", None)],
       lambda c: 0 if c["ph_u"] > 5.5 else 1, _ex_ph_u),
    No("resp_acid", "Aguda ou crônica?", "Acidose respiratória. O HCO₃⁻ subiu como na aguda ou na crônica?",
       [("Aguda", "+1 por 10", "f_racid_aguda", None), ("Crônica", "+3,5 por 10", "f_racid_cronica", None),
        ("HCO₃⁻ alto demais", "> crônico + 2", "f_racid_alc", None)], _ab_resp_acid, _ex_resp_acid),
    No("prim_alc", "Primário", "Alcalemia. Quem explica o pH alto?",
       [("Metabólica", "HCO₃⁻ > 26", "comp_alc", None), ("Respiratória", "PaCO₂ < 35", "resp_alc", None),
        ("Mista", "os dois", "f_alc_mista", None)], _ab_prim_alc, _ex_prim_alc),
    No("comp_alc", "Compensação", "Alcalose metabólica. A PaCO₂ subiu como esperado?",
       [("Adequada", "dentro de ±2", "cl_u", None),
        ("PaCO₂ acima", "> esperado + 2", "cl_u", "acidose respiratória associada"),
        ("PaCO₂ abaixo", "< esperado − 2", "cl_u", "alcalose respiratória associada")], _ab_comp_alc, _ex_comp_alc),
    No("cl_u", "Cl⁻ urinário", "Alcalose metabólica. Responde a soro? Olhe o cloro urinário.",
       [("Cl⁻u < 20", "responde a soro", "f_salina", None), ("Cl⁻u ≥ 20", "resistente", "pa", None)],
       lambda c: 0 if c["cl_u"] < 20 else 1, _ex_cl_u),
    No("pa", "Pressão", "Cloro urinário alto. O paciente está hipertenso?",
       [("Hipertenso", "PAS ≥ 150", "f_mineral", None), ("Normotenso", "PAS < 150", "f_diuretico", None)],
       lambda c: 0 if c["pa"] >= 150 else 1, _ex_pa),
    No("resp_alc", "Aguda ou crônica?", "Alcalose respiratória. O HCO₃⁻ caiu como na aguda ou na crônica?",
       [("Aguda", "−2 por 10", "f_ralc_aguda", None), ("Crônica", "−4,5 por 10", "f_ralc_cronica", None)],
       _ab_resp_alc, _ex_resp_alc),
    No("normais", "Valores normais?", "pH normal. HCO₃⁻ e PaCO₂ também estão normais?",
       [("Normais", "HCO₃⁻ 22–26 e PaCO₂ 35–45", "f_normal", None), ("Alterados", "fora da faixa", "f_misto_normal", None)],
       lambda c: 0 if 22 <= c["hco3"] <= 26 and 35 <= c["pco2"] <= 45 else 1, _ex_normal),
    Folha("f_acid_mista", "Acidose mista", "Acidose mista: metabólica e respiratória ao mesmo tempo",
          "HCO₃⁻ baixo e PaCO₂ alta puxam o pH para o mesmo lado: é o pH mais baixo que existe (ex.: parada cardíaca)."),
    Folha("f_latica", "Acidose lática", "Acidose metabólica de AG alto por lactato",
          "Tipo A é hipoperfusão (choque, isquemia); tipo B é sem hipóxia (metformina, fígado, linezolida). Trate a causa."),
    Folha("f_ceto", "Cetoacidose", "Acidose metabólica de AG alto por cetoácidos",
          "Diabética, alcoólica ou de jejum. Na CAD: volume, potássio (insulina só com K⁺ > 3,5) e insulina."),
    Folha("f_alcool", "Álcool tóxico", "Acidose de AG alto com gap osmolar alto: metanol ou etilenoglicol",
          "Antídoto fomepizol (ou etanol) e hemodiálise nos graves. Metanol cega; etilenoglicol dá oxalato e lesão renal."),
    Folha("f_uremia", "Urêmica", "Acidose de AG alto da insuficiência renal avançada",
          "O rim não excreta ácidos fixos (sulfato, fosfato). Bicarbonato oral e diálise conforme o caso."),
    Folha("f_diarreia", "Diarreia", "Acidose hiperclorêmica por perda intestinal de bicarbonato",
          "AG urinário negativo: o rim está excretando amônio direitinho. Reponha volume, potássio e bicarbonato se preciso."),
    Folha("f_atr4", "ATR tipo 4", "Acidose tubular tipo 4: hipoaldosteronismo (com hipercalemia)",
          "Nefropatia diabética, IECA/BRA, espironolactona, heparina, trimetoprim. Trate a causa e o potássio."),
    Folha("f_atr1", "ATR tipo 1", "Acidose tubular distal (tipo 1): o coletor não secreta H⁺",
          "Urina com pH > 5,5 em acidemia, hipocalemia, nefrocalcinose. Sjögren, lúpus, anfotericina. Citrato de potássio."),
    Folha("f_atr2", "ATR tipo 2", "Acidose tubular proximal (tipo 2): perda de bicarbonato no túbulo proximal",
          "Muitas vezes Fanconi (glicosúria com glicemia normal): mieloma, tenofovir, ifosfamida. Álcali em dose alta + K⁺."),
    Folha("f_racid_aguda", "Resp. aguda", "Acidose respiratória aguda",
          "Hipoventilação súbita (opioide, sedativo, crise grave): o rim ainda não compensou. Trate a ventilação."),
    Folha("f_racid_cronica", "Resp. crônica", "Acidose respiratória crônica compensada",
          "Retentor crônico (DPOC, obesidade-hipoventilação). Não 'normalizar' a PaCO₂ no ventilador: alcalose pós-hipercápnica."),
    Folha("f_racid_alc", "Resp. + alcalose met.", "Acidose respiratória com alcalose metabólica associada",
          "HCO₃⁻ alto demais até para a crônica: vômito, diurético ou corticoide no retentor de CO₂."),
    Folha("f_alc_mista", "Alcalose mista", "Alcalose mista: metabólica e respiratória",
          "Os dois puxam o pH para cima (ex.: vômitos com hiperventilação por dor ou sepse). Risco de arritmia."),
    Folha("f_salina", "Responde a soro", "Alcalose metabólica responsiva a cloreto (soro)",
          "Vômitos, sonda gástrica, diurético usado antes. Trate com SF 0,9% e reponha potássio."),
    Folha("f_mineral", "Mineralocorticoide", "Alcalose metabólica com hipertensão: excesso de mineralocorticoide",
          "Hiperaldosteronismo primário (renina baixa), Cushing, Liddle, alcaçuz. Dose aldosterona e renina."),
    Folha("f_diuretico", "Diurético/Bartter", "Alcalose metabólica resistente sem hipertensão",
          "Diurético em uso, Bartter (como alça) ou Gitelman (como tiazídico: magnésio baixo e cálcio urinário baixo)."),
    Folha("f_ralc_aguda", "Resp. aguda", "Alcalose respiratória aguda",
          "Hiperventilação recente: ansiedade, dor, febre, hipoxemia, TEP. Parestesias pela queda do cálcio ionizado."),
    Folha("f_ralc_cronica", "Resp. crônica", "Alcalose respiratória crônica compensada",
          "Gestação, altitude, cirrose, doença pulmonar intersticial: o rim já baixou o HCO₃⁻."),
    Folha("f_normal", "Normal", "Gasometria normal",
          "pH, HCO₃⁻ e PaCO₂ dentro da faixa. Confira oxigenação e o contexto clínico."),
    Folha("f_misto_normal", "Misto, pH normal", "Distúrbio misto com pH normal (dois distúrbios opostos)",
          "Valores muito alterados e pH normal: a compensação nunca leva o pH exatamente ao normal. Ache os dois."),
]


def _ab_contas(c):
    """Contas do nível 1: só a fórmula de compensação que vale para o distúrbio primário deste caso."""
    out = [("AG", fi(_ag(c))), ("AG corrigido", fi(_agc(c)))]
    raiz = _ab_decide_raiz(c)
    prim = _ab_prim_acid(c) if raiz == 0 else _ab_prim_alc(c) if raiz == 1 else None
    if raiz == 0 and prim == 0:
        out += [("PaCO₂ esperada (Winter)", f"{f1(_winter(c) - 2)} a {f1(_winter(c) + 2)}")]
        if _agc(c) > 12:
            out += [("Δ/Δ", f1(_dd(c)))]
    elif raiz == 0 and prim == 1:
        ea, ec = _resp_acid_esp(c)
        out += [("HCO₃⁻ esperado aguda / crônica", f"{f1(ea)} / {f1(ec)}")]
    elif raiz == 1 and prim == 0:
        out += [("PaCO₂ esperada", f"{f1(_comp_alc(c) - 2)} a {f1(_comp_alc(c) + 2)}")]
    elif raiz == 1 and prim == 1:
        ea, ec = _resp_alc_esp(c)
        out += [("HCO₃⁻ esperado aguda / crônica", f"{f1(ea)} / {f1(ec)}")]
    out += [("Gap osmolar", fi(_gap_osm(c))), ("AG urinário", fi(_agu(c)))]
    return out


def _base(rng):
    return {"na": rng.randint(136, 142), "alb": 4.0, "lact": round(rng.uniform(0.8, 1.6), 1), "cet": False,
            "glic": rng.randint(85, 120), "ureia": rng.randint(25, 45), "k": round(rng.uniform(3.7, 4.6), 1),
            "na_u": rng.randint(40, 70), "k_u": rng.randint(25, 40), "cl_u": rng.randint(50, 80), "ph_u": 5.8,
            "pa": rng.randint(110, 135), "osm": 0}


def _fechar(c):
    c["ph"] = round(ph_de(c["hco3"], c["pco2"]), 2)
    c["osm"] = c["osm"] or round(2 * c["na"] + c["glic"] / 18 + c["ureia"] / 6 + 4)
    return c


def _gerar_ab(rng, alvo):
    for _ in range(400):
        c = _base(rng)
        texto = ""
        if alvo in ("f_latica", "f_ceto", "f_alcool", "f_uremia", "f_diarreia", "f_atr4", "f_atr1", "f_atr2"):
            h = rng.randint(8, 17)
            comp = rng.choice([0, 0, 0, 1, 2])
            e = _winter({"hco3": h})
            p = round(e + (rng.uniform(-1.2, 1.2) if comp == 0 else rng.uniform(5, 9) if comp == 1 else -rng.uniform(5, 8)))
            if p < 12 or p > 44:
                continue
            c.update(hco3=h, pco2=p)
            if rng.random() < 0.3:
                c["alb"] = round(rng.uniform(2.0, 3.0), 1)
            if alvo in ("f_latica", "f_ceto", "f_alcool", "f_uremia"):
                r = rng.choice([rng.uniform(1.15, 1.8), rng.uniform(0.3, 0.7), rng.uniform(2.4, 3.2)])
                agc = 12 + r * (24 - h)
                if agc < 17 or agc > 40:
                    continue
                ag = agc - 2.5 * (4 - c["alb"])
                c["cl"] = round(c["na"] - h - ag)
                if alvo == "f_latica":
                    c["lact"] = round(rng.uniform(5.5, 12), 1)
                    texto = rng.choice(["Homem de 67 anos em choque séptico de foco abdominal.",
                                        "Mulher de 55 anos com isquemia mesentérica e hipotensão.",
                                        "Diabético em metformina com lesão renal aguda e choque."])
                elif alvo == "f_ceto":
                    c.update(cet=True, glic=rng.randint(350, 650))
                    texto = rng.choice(["Jovem com DM1, poliúria, vômitos e hálito cetônico.",
                                        "Etilista em jejum há 3 dias, vômitos, glicemia pouco alterada."])
                    if "Etilista" in texto:
                        c["glic"] = rng.randint(90, 180)
                elif alvo == "f_alcool":
                    c["osm"] = round(2 * c["na"] + c["glic"] / 18 + c["ureia"] / 6 + rng.randint(22, 45))
                    texto = rng.choice(["Homem que bebeu cachaça adulterada e agora vê 'tempestade de neve'.",
                                        "Paciente que ingeriu anticongelante de radiador; cristais na urina."])
                else:
                    c.update(ureia=rng.randint(190, 320))
                    texto = "Renal crônico sem diálise, náuseas e prurido, creatinina 9."
            else:
                agc = rng.uniform(8, 11)
                ag = agc - 2.5 * (4 - c["alb"])
                c["cl"] = round(c["na"] - h - ag)
                if alvo == "f_diarreia":
                    c.update(na_u=rng.randint(15, 30), k_u=rng.randint(10, 20), cl_u=rng.randint(60, 90),
                             k=round(rng.uniform(2.6, 3.3), 1))
                    texto = "Mulher com diarreia aquosa há 5 dias."
                else:
                    c.update(na_u=rng.randint(40, 70), k_u=rng.randint(25, 45))
                    c["cl_u"] = c["na_u"] + c["k_u"] - rng.randint(8, 25)
                    if alvo == "f_atr4":
                        c["k"] = round(rng.uniform(5.6, 6.3), 1)
                        texto = "Diabético de longa data em uso de IECA, sem diarreia."
                    elif alvo == "f_atr1":
                        c.update(k=round(rng.uniform(2.6, 3.2), 1), ph_u=round(rng.uniform(6.1, 6.9), 1))
                        texto = "Mulher com síndrome de Sjögren e cálculos renais de repetição."
                    else:
                        c.update(k=round(rng.uniform(2.7, 3.3), 1), ph_u=round(rng.uniform(5.0, 5.4), 1))
                        texto = "Paciente em tenofovir com glicosúria e glicemia normal."
        elif alvo == "f_acid_mista":
            h, p = rng.randint(12, 19), rng.randint(50, 68)
            c.update(hco3=h, pco2=p)
            c["cl"] = round(c["na"] - h - rng.uniform(16, 24))
            c["lact"] = round(rng.uniform(6, 11), 1)
            texto = "Paciente após parada cardiorrespiratória revertida, ainda hipoventilando."
        elif alvo in ("f_racid_aguda", "f_racid_cronica", "f_racid_alc"):
            p = rng.randint(85, 100) if alvo == "f_racid_alc" else rng.randint(56, 80)
            ea, ec = _resp_acid_esp({"pco2": p})
            h = (ea + rng.uniform(-0.4, 0.4) if alvo == "f_racid_aguda" else ec + rng.uniform(-0.6, 0.6)
                 if alvo == "f_racid_cronica" else ec + rng.uniform(2.6, 3.4))
            h = round(h)
            if h < 22 and alvo != "f_racid_aguda":
                continue
            c.update(hco3=h, pco2=p)
            c["cl"] = round(c["na"] - h - rng.uniform(9, 11))
            texto = {"f_racid_aguda": "Jovem sonolento após overdose de opioide.",
                     "f_racid_cronica": "DPOC grave em casa, estável, sem queixa nova.",
                     "f_racid_alc": "DPOC retentor em uso de furosemida e com vômitos."}[alvo]
        elif alvo in ("f_salina", "f_mineral", "f_diuretico"):
            h = rng.randint(30, 40)
            comp = rng.choice([0, 0, 0, 1, 2])
            e = _comp_alc({"hco3": h})
            p = round(e + (rng.uniform(-1.2, 1.2) if comp == 0 else rng.uniform(4, 7) if comp == 1 else -rng.uniform(4, 6)))
            if p < 35:
                continue
            c.update(hco3=h, pco2=p, k=round(rng.uniform(2.5, 3.3), 1))
            c["cl"] = round(c["na"] - h - rng.uniform(9, 12))
            if alvo == "f_salina":
                c.update(cl_u=rng.randint(5, 15), na_u=rng.randint(10, 60))
                texto = "Mulher com vômitos incoercíveis há 4 dias."
            elif alvo == "f_mineral":
                c.update(cl_u=rng.randint(40, 80), pa=rng.randint(160, 200))
                texto = "Hipertenso resistente a três drogas, com câimbras."
            else:
                c.update(cl_u=rng.randint(40, 90), pa=rng.randint(95, 125))
                texto = rng.choice(["Jovem normotensa com câimbras e magnésio baixo.", "Idoso em uso de hidroclorotiazida."])
        elif alvo in ("f_ralc_aguda", "f_ralc_cronica"):
            p = rng.randint(20, 28)
            ea, ec = _resp_alc_esp({"pco2": p})
            h = round(ea + rng.uniform(-0.4, 0.4) if alvo == "f_ralc_aguda" else ec + rng.uniform(-0.5, 0.5))
            c.update(hco3=h, pco2=p)
            c["cl"] = round(c["na"] - h - rng.uniform(8, 11))
            texto = {"f_ralc_aguda": "Jovem em crise de pânico, com parestesias nas mãos.",
                     "f_ralc_cronica": "Gestante de 32 semanas, assintomática."}[alvo]
        elif alvo == "f_alc_mista":
            h, p = rng.randint(30, 36), rng.randint(26, 33)
            c.update(hco3=h, pco2=p)
            c["cl"] = round(c["na"] - h - rng.uniform(9, 12))
            texto = "Paciente com vômitos importantes e dor intensa, taquipneico."
        elif alvo == "f_normal":
            c.update(hco3=rng.randint(23, 25), pco2=rng.randint(37, 43))
            c["cl"] = round(c["na"] - c["hco3"] - rng.uniform(8, 11))
            texto = "Exame pré-operatório de rotina."
        elif alvo == "f_misto_normal":
            h, p = rng.randint(13, 16), rng.randint(23, 27)
            c.update(hco3=h, pco2=p)
            c["cl"] = round(c["na"] - h - rng.uniform(18, 24))
            texto = "Intoxicação por salicilato com várias horas de evolução."
        _fechar(c)
        if abs(c["ph"] - 7.35) < 0.015 or abs(c["ph"] - 7.45) < 0.015:
            continue
        c["texto"] = texto
        c["mostrar"] = _ab_mostrar(c)
        if ARVORES_PRONTAS and ACIDO_BASE.percorrer(c)[1].id == alvo:
            return c
        if not ARVORES_PRONTAS:
            return c
    raise RuntimeError(f"não consegui gerar {alvo}")


def _ab_mostrar(c):
    out = [("pH", f2(c["ph"])), ("PaCO₂", f"{fi(c['pco2'])} mmHg"), ("HCO₃⁻", f"{fi(c['hco3'])} mEq/L"),
           ("Na⁺", fi(c["na"])), ("Cl⁻", fi(c["cl"])), ("K⁺", f1(c["k"])), ("Albumina", f"{f1(c['alb'])} g/dL"),
           ("Lactato", f"{f1(c['lact'])} mmol/L"), ("Glicemia", fi(c["glic"])), ("Ureia", fi(c["ureia"])),
           ("Osm medida", fi(c["osm"])), ("Cetonas", "+++" if c["cet"] else "negativas"),
           ("Na⁺ / K⁺ / Cl⁻ urinários", f"{fi(c['na_u'])} / {fi(c['k_u'])} / {fi(c['cl_u'])}"),
           ("pH urinário", f1(c["ph_u"])), ("PA sistólica", f"{fi(c['pa'])} mmHg")]
    return out


ARVORES_PRONTAS = False
ACIDO_BASE = Arvore(
    "acidobase", "Ácido-base completo", "pH → primário → compensação → ânion gap → delta-delta → causa", "ph", AB_NOS,
    _gerar_ab, [n.id for n in AB_NOS if n.folha], _ab_contas)

# ================================================================== 2. HIPONATREMIA

HN_NOS = [
    No("osm", "Osm sérica", "Hiponatremia. Qual a osmolalidade sérica medida?",
       [("Hipertônica", "> 295", "f_hn_hiper", None), ("Isotônica", "275 a 295", "f_hn_iso", None),
        ("Hipotônica", "< 275", "osm_u", None)],
       lambda c: 0 if c["osm"] > 295 else 1 if c["osm"] >= 275 else 2,
       lambda c: f"Osm medida {fi(c['osm'])} mOsm/kg: acima de 295 tem soluto puxando água (glicose); "
                 "275–295 é falsa (pseudo); abaixo de 275 é hiponatremia verdadeira."),
    No("osm_u", "Osm urinária", "Hiponatremia hipotônica. O rim está diluindo a urina ao máximo?",
       [("Osm u ≤ 100", "diluição máxima", "f_hn_agua", None), ("Osm u > 100", "ADH agindo", "vol", None)],
       lambda c: 0 if c["osm_u"] <= 100 else 1,
       lambda c: f"Osm urinária {fi(c['osm_u'])}: até 100 = o rim está diluindo bem, o problema é água demais entrando."),
    No("vol", "Volemia", "O ADH está agindo. Como está o volume do paciente (exame físico)?",
       [("Hipovolêmico", "desidratado", "na_u_hipo", None), ("Euvolêmico", "sem edema nem desidratação", "eu", None),
        ("Hipervolêmico", "edema, ascite", "na_u_hiper", None)],
       lambda c: {"hipo": 0, "eu": 1, "hiper": 2}[c["vol"]],
       lambda c: f"Exame: {c['vol_txt']}."),
    No("na_u_hipo", "Na⁺ urinário", "Hipovolêmico. A perda de sódio é pelo rim ou fora dele?",
       [("Na⁺u ≤ 30", "rim segurando", "f_hn_extra", None), ("Na⁺u > 30", "rim perdendo", "f_hn_renal", None)],
       lambda c: 0 if c["na_u"] <= 30 else 1,
       lambda c: f"Na⁺ urinário {fi(c['na_u'])}: até 30 o rim está poupando sódio (perda extrarrenal); acima, o rim perde."),
    No("eu", "Excluir causas", "Euvolêmico. Antes de chamar de SIADH, olhe TSH e cortisol.",
       [("TSH alto", "hipotireoidismo", "f_hn_tireo", None), ("Cortisol baixo", "insuficiência adrenal", "f_hn_adrenal", None),
        ("Ambos normais", "SIADH", "f_hn_siadh", None)],
       lambda c: 0 if c["tsh"] > 10 else 1 if c["cortisol"] < 5 else 2,
       lambda c: f"TSH {f1(c['tsh'])} (alto se > 10) e cortisol {f1(c['cortisol'])} µg/dL (baixo se < 5)."),
    No("na_u_hiper", "Na⁺ urinário", "Hipervolêmico. O rim está retendo sódio ou não consegue excretar?",
       [("Na⁺u < 20", "retenção ávida", "f_hn_edema", None), ("Na⁺u ≥ 20", "rim doente", "f_hn_rim", None)],
       lambda c: 0 if c["na_u"] < 20 else 1,
       lambda c: f"Na⁺ urinário {fi(c['na_u'])}: abaixo de 20 o rim retém (IC, cirrose, nefrótica); acima, doença renal."),
    Folha("f_hn_hiper", "Hipertônica", "Hiponatremia hipertônica (translocacional): hiperglicemia ou manitol",
          "A glicose puxa água para fora das células. Corrija: Na⁺ sobe ~1,6–2,4 a cada 100 mg/dL de glicose acima de 100."),
    Folha("f_hn_iso", "Pseudo", "Pseudo-hiponatremia (isotônica): triglicerídeos ou proteínas muito altos",
          "Erro do método de dosagem. Não trate; dose o sódio por eletrodo direto (gasometria)."),
    Folha("f_hn_agua", "Excesso de água", "Polidipsia primária ou potomania (dieta pobre em soluto)",
          "Urina diluída ao máximo. Restringir água; cuidado com a correção rápida demais quando a ingestão para."),
    Folha("f_hn_extra", "Perda extrarrenal", "Hiponatremia hipovolêmica por perda extrarrenal (vômito, diarreia, suor)",
          "Repor volume com SF 0,9%. Ao restaurar o volume, o ADH desliga e o sódio sobe rápido: vigiar a correção."),
    Folha("f_hn_renal", "Perda renal", "Hiponatremia hipovolêmica por perda renal: diurético tiazídico ou insuficiência adrenal",
          "Suspender o tiazídico; pensar em Addison (com potássio alto) e em perda cerebral de sal."),
    Folha("f_hn_tireo", "Hipotireoidismo", "Hiponatremia por hipotireoidismo",
          "Excluir sempre antes do SIADH. Trata-se com levotiroxina."),
    Folha("f_hn_adrenal", "Insuf. adrenal", "Hiponatremia por insuficiência adrenal (falta de cortisol)",
          "Sem cortisol, o ADH fica alto. Hidrocortisona corrige; a primária também tem potássio alto."),
    Folha("f_hn_siadh", "SIADH", "Síndrome da secreção inapropriada de ADH",
          "Euvolêmico, urina concentrada e Na⁺u > 30. Causas: pulmão, SNC, drogas (ISRS, carbamazepina), câncer. Restringir água."),
    Folha("f_hn_edema", "IC/cirrose/nefrótica", "Hiponatremia hipervolêmica: insuficiência cardíaca, cirrose ou síndrome nefrótica",
          "O volume efetivo é baixo e o rim retém água e sal. Restrição hídrica, diurético e tratar a doença de base."),
    Folha("f_hn_rim", "Doença renal", "Hiponatremia hipervolêmica por doença renal (aguda ou crônica)",
          "O rim não excreta água livre. Restrição hídrica, diurético e diálise se necessário."),
]

_VOL = {"hipo": ["mucosas secas, PA 92/60, FC 112, turgor diminuído", "hipotensão postural e veias jugulares colabadas"],
        "eu": ["sem edema e sem sinais de desidratação", "exame de volume normal, PA 124/78"],
        "hiper": ["edema de membros inferiores, ascite e turgência jugular", "anasarca e estertores em bases"]}


def _hn_contas(c):
    return [("Osm sérica", fi(c["osm"])), ("Osm urinária", fi(c["osm_u"])), ("Na⁺ urinário", fi(c["na_u"])),
            ("Na⁺ corrigido p/ glicose", f1(c["na"] + 2.4 * max(0, c["glic"] - 100) / 100))]


def _gerar_hn(rng, alvo):
    c = {"na": rng.randint(116, 131), "glic": rng.randint(85, 120), "osm_u": rng.randint(250, 600),
         "na_u": rng.randint(40, 80), "tsh": round(rng.uniform(0.8, 3.5), 1), "cortisol": round(rng.uniform(10, 20), 1),
         "vol": "eu", "tg": rng.randint(90, 180)}
    c["osm"] = round(2 * c["na"] + c["glic"] / 18 + 5)
    texto = "Paciente com náuseas e confusão leve."
    if alvo == "f_hn_hiper":
        c.update(glic=rng.randint(700, 1100))
        c["osm"] = rng.randint(300, 320)
        texto = "Diabético descompensado, muito sede e poliúria."
    elif alvo == "f_hn_iso":
        c["osm"] = rng.randint(282, 292)
        c["tg"] = rng.randint(2500, 4000)
        texto = "Paciente com pancreatite e soro lipêmico, assintomático."
    else:
        c["osm"] = min(c["osm"], rng.randint(240, 268))
        if alvo == "f_hn_agua":
            c["osm_u"] = rng.randint(50, 95)
            texto = rng.choice(["Paciente psiquiátrico que bebe muitos litros de água por dia.",
                                "Homem que vive de cerveja e quase não come (potomania)."])
        else:
            c["osm_u"] = rng.randint(250, 650)
            if alvo in ("f_hn_extra", "f_hn_renal"):
                c["vol"] = "hipo"
                c["na_u"] = rng.randint(5, 25) if alvo == "f_hn_extra" else rng.randint(45, 90)
                texto = ("Idosa com diarreia há 6 dias." if alvo == "f_hn_extra" else
                         rng.choice(["Idosa em uso de hidroclorotiazida, tonta.", "Mulher com astenia, hiperpigmentação e K⁺ alto."]))
            elif alvo in ("f_hn_tireo", "f_hn_adrenal", "f_hn_siadh"):
                c["vol"] = "eu"
                c["na_u"] = rng.randint(40, 90)
                if alvo == "f_hn_tireo":
                    c["tsh"] = round(rng.uniform(25, 80), 1)
                    texto = "Mulher com ganho de peso, frio e pele seca."
                elif alvo == "f_hn_adrenal":
                    c["cortisol"] = round(rng.uniform(1.0, 3.5), 1)
                    texto = "Paciente que parou corticoide de uso crônico há 2 semanas."
                else:
                    texto = rng.choice(["Tabagista com massa pulmonar central.", "Idosa que iniciou sertralina há 3 semanas.",
                                        "Paciente com meningite em tratamento."])
            else:
                c["vol"] = "hiper"
                c["na_u"] = rng.randint(5, 15) if alvo == "f_hn_edema" else rng.randint(30, 70)
                texto = (rng.choice(["Cirrótico com ascite volumosa.", "Insuficiência cardíaca descompensada."])
                         if alvo == "f_hn_edema" else "Renal crônico estágio 5 com edema.")
    c["vol_txt"] = rng.choice(_VOL[c["vol"]])
    c["texto"] = texto
    c["mostrar"] = [("Na⁺", f"{fi(c['na'])} mEq/L"), ("Osm sérica medida", f"{fi(c['osm'])} mOsm/kg"),
                    ("Glicemia", fi(c["glic"])), ("Triglicerídeos", fi(c["tg"])),
                    ("Osm urinária", fi(c["osm_u"])), ("Na⁺ urinário", fi(c["na_u"])), ("Exame de volume", c["vol_txt"]),
                    ("TSH", f1(c["tsh"])), ("Cortisol (8 h)", f"{f1(c['cortisol'])} µg/dL")]
    return c


HIPONATREMIA = Arvore("hiponatremia", "Hiponatremia", "Osmolalidade → osm urinária → volemia → Na⁺ urinário",
                      "osm", HN_NOS, _gerar_hn, [n.id for n in HN_NOS if n.folha], _hn_contas)

# ================================================================== 3. HIPERNATREMIA

HR_NOS = [
    No("osm_u", "Osm urinária", "Hipernatremia. O rim está concentrando a urina?",
       [("Osm u > 600", "concentra", "f_hr_extra", None), ("300 a 600", "parcial", "f_hr_osmotica", None),
        ("Osm u < 300", "urina diluída", "ddavp", None)],
       lambda c: 0 if c["osm_u"] > 600 else 1 if c["osm_u"] >= 300 else 2,
       lambda c: f"Osm urinária {fi(c['osm_u'])}: acima de 600 o rim concentra bem (a água sumiu por fora); "
                 "abaixo de 300 o rim não concentra (diabetes insípido)."),
    No("ddavp", "Desmopressina", "Urina diluída com sódio alto: diabetes insípido. A osm urinária sobe com desmopressina?",
       [("Sobe > 50%", "faltava ADH", "f_hr_central", None), ("Não sobe", "rim não responde", "f_hr_nefro", None)],
       lambda c: 0 if c["osm_u_ddavp"] > 1.5 * c["osm_u"] else 1,
       lambda c: f"Osm urinária foi de {fi(c['osm_u'])} para {fi(c['osm_u_ddavp'])} após desmopressina "
                 f"({fi(100 * (c['osm_u_ddavp'] / c['osm_u'] - 1))}%). Subir mais de 50% = central."),
    Folha("f_hr_extra", "Perda extrarrenal", "Hipernatremia por perda de água extrarrenal ou falta de acesso à água",
          "Idoso acamado, febre, diarreia, queimadura. O rim concentra bem. Repor água livre devagar (≤ 10 mEq/L em 24 h)."),
    Folha("f_hr_osmotica", "Diurese osmótica", "Diurese osmótica (glicose, ureia, manitol) ou diabetes insípido parcial",
          "Urina nem diluída nem concentrada: soluto arrastando água. Trate a glicose ou a causa."),
    Folha("f_hr_central", "DI central", "Diabetes insípido central (falta de ADH)",
          "Pós-neurocirurgia, trauma de crânio, tumor. Trata-se com desmopressina."),
    Folha("f_hr_nefro", "DI nefrogênico", "Diabetes insípido nefrogênico (rim não responde ao ADH)",
          "Lítio, hipercalcemia, hipocalemia. Suspender a causa, tiazídico e dieta pobre em sódio."),
]


def _gerar_hr(rng, alvo):
    c = {"na": rng.randint(150, 166), "osm_u": 0, "osm_u_ddavp": 0, "glic": rng.randint(90, 140)}
    if alvo == "f_hr_extra":
        c["osm_u"] = rng.randint(650, 950)
        texto = rng.choice(["Idosa acamada com demência e febre há 3 dias.", "Criança com diarreia intensa sem acesso a água."])
    elif alvo == "f_hr_osmotica":
        c["osm_u"] = rng.randint(320, 560)
        c["glic"] = rng.randint(500, 900)
        texto = "Diabético com hiperglicemia grave e poliúria."
    else:
        c["osm_u"] = rng.randint(90, 250)
        if alvo == "f_hr_central":
            c["osm_u_ddavp"] = round(c["osm_u"] * rng.uniform(1.8, 3.0))
            texto = "Paciente no 2º dia após cirurgia de hipófise, urinando 6 litros por dia."
        else:
            c["osm_u_ddavp"] = round(c["osm_u"] * rng.uniform(1.0, 1.15))
            texto = "Paciente bipolar em uso de lítio há 10 anos, com poliúria."
    c["texto"] = texto
    c["mostrar"] = [("Na⁺", f"{fi(c['na'])} mEq/L"), ("Glicemia", fi(c["glic"])), ("Osm urinária", fi(c["osm_u"])),
                    ("Osm urinária após desmopressina", fi(c["osm_u_ddavp"]) if c["osm_u_ddavp"] else "não feito")]
    return c


HIPERNATREMIA = Arvore("hipernatremia", "Hipernatremia", "Osm urinária → resposta à desmopressina", "osm_u", HR_NOS,
                       _gerar_hr, [n.id for n in HR_NOS if n.folha],
                       lambda c: [("Osm urinária", fi(c["osm_u"]))] +
                                 ([("Aumento com desmopressina", f"{fi(100 * (c['osm_u_ddavp'] / c['osm_u'] - 1))}%")]
                                  if c["osm_u_ddavp"] else []))

# ================================================================== 4. HIPOCALEMIA

HK_NOS = [
    No("redist", "Redistribuição?", "Hipocalemia. Há algo empurrando o potássio para dentro das células?",
       [("Sim", "insulina, β2, alcalose aguda", "f_hk_redist", None), ("Não", "perda real", "k_u", None)],
       lambda c: 0 if c["redist"] else 1,
       lambda c: "Insulina, salbutamol, tireotoxicose e alcalose aguda deslocam K⁺ para dentro sem perda real." +
                 (f" Aqui: {c['redist']}." if c["redist"] else " Aqui não há nada disso.")),
    No("k_u", "K⁺ urinário", "Perda real. O rim está perdendo potássio?",
       [("K⁺u < 20", "rim poupando", "hk_extra_ab", None), ("K⁺u ≥ 20", "rim perdendo", "hk_renal_ab", None)],
       lambda c: 0 if c["k_u"] < 20 else 1,
       lambda c: f"K⁺ urinário {fi(c['k_u'])} mEq/L: abaixo de 20 o rim está poupando (perda fora do rim)."),
    No("hk_extra_ab", "Ácido-base", "Perda extrarrenal. Como está o bicarbonato?",
       [("Acidose", "HCO₃⁻ < 22", "f_hk_diarreia", None), ("Normal", "HCO₃⁻ 22–26", "f_hk_ingesta", None)],
       lambda c: 0 if c["hco3"] < 22 else 1,
       lambda c: f"HCO₃⁻ {fi(c['hco3'])}: diarreia perde bicarbonato junto com potássio."),
    No("hk_renal_ab", "Ácido-base", "Perda renal. Acidose ou alcalose metabólica?",
       [("Acidose", "HCO₃⁻ < 22", "f_hk_atr", None), ("Alcalose", "HCO₃⁻ > 26", "hk_pa", None)],
       lambda c: 0 if c["hco3"] < 22 else 1,
       lambda c: f"HCO₃⁻ {fi(c['hco3'])}: com acidose, pense em ATR ou cetoacidose; com alcalose, siga pela pressão."),
    No("hk_pa", "Pressão", "Perda renal com alcalose. O paciente está hipertenso?",
       [("Hipertenso", "PAS ≥ 150", "hk_renina", None), ("Normotenso", "PAS < 150", "hk_cl_u", None)],
       lambda c: 0 if c["pa"] >= 150 else 1,
       lambda c: f"PA sistólica {fi(c['pa'])}: hipertensão sugere excesso de mineralocorticoide."),
    No("hk_renina", "Renina/aldosterona", "Hipertensão com hipocalemia. O que dizem renina e aldosterona?",
       [("Aldo alta, renina baixa", "primário", "f_hk_primario", None),
        ("As duas altas", "secundário", "f_hk_secundario", None),
        ("As duas baixas", "outro mineralocorticoide", "f_hk_pseudo", None)],
       lambda c: {"prim": 0, "sec": 1, "baixas": 2}[c["ren"]],
       lambda c: f"Aldosterona {c['aldo_txt']} e renina {c['renina_txt']}."),
    No("hk_cl_u", "Cl⁻ urinário", "Normotenso com alcalose. Olhe o cloro urinário.",
       [("Cl⁻u < 20", "vômito", "f_hk_vomito", None), ("Cl⁻u ≥ 20", "diurético/Bartter", "f_hk_diuretico", None)],
       lambda c: 0 if c["cl_u"] < 20 else 1,
       lambda c: f"Cl⁻ urinário {fi(c['cl_u'])}: abaixo de 20 = vômito ou sonda; acima = diurético, Bartter ou Gitelman."),
    Folha("f_hk_redist", "Redistribuição", "Hipocalemia por redistribuição (sem perda corporal)",
          "Trate a causa; reponha com cautela, porque o K⁺ volta das células (rebote, sobretudo na paralisia tireotóxica)."),
    Folha("f_hk_diarreia", "Diarreia", "Hipocalemia por perda intestinal (diarreia, laxativos)",
          "K⁺ urinário baixo com acidose metabólica. Repor potássio e volume."),
    Folha("f_hk_ingesta", "Baixa ingesta", "Hipocalemia por baixa ingestão ou perda cutânea",
          "Desnutrição, alcoolismo, sudorese intensa. Repor potássio e magnésio."),
    Folha("f_hk_atr", "ATR / CAD", "Hipocalemia renal com acidose: ATR tipo 1 ou 2, ou cetoacidose tratada",
          "Calcule AG e AG urinário. ATR distal: citrato de potássio."),
    Folha("f_hk_primario", "Hiperaldo primário", "Hiperaldosteronismo primário (adenoma ou hiperplasia)",
          "Relação aldosterona/renina alta. Espironolactona ou cirurgia se adenoma unilateral."),
    Folha("f_hk_secundario", "Hiperaldo secundário", "Hiperaldosteronismo secundário (estenose de artéria renal, tumor de renina)",
          "Renina alta puxa a aldosterona. Investigue a artéria renal."),
    Folha("f_hk_pseudo", "Outro mineralocorticoide", "Excesso de outro mineralocorticoide: Cushing, Liddle ou alcaçuz",
          "Renina e aldosterona baixas. Liddle responde a amilorida."),
    Folha("f_hk_vomito", "Vômito", "Hipocalemia por vômitos (perda renal de K⁺ pela bicarbonatúria)",
          "Cloro urinário baixo. SF 0,9% com KCl corrige volume, cloro e potássio."),
    Folha("f_hk_diuretico", "Diurético/Bartter", "Diurético, Bartter ou Gitelman",
          "Cloro urinário alto, normotenso. Gitelman: magnésio baixo e calciúria baixa (como tiazídico)."),
]


def _gerar_hk(rng, alvo):
    c = {"k": round(rng.uniform(2.3, 3.3), 1), "redist": "", "k_u": rng.randint(30, 70), "hco3": rng.randint(23, 25),
         "pa": rng.randint(110, 135), "ren": "prim", "cl_u": rng.randint(40, 90)}
    textos = {
        "f_hk_redist": rng.choice(["Asmático após várias nebulizações com salbutamol.",
                                   "Paciente com cetoacidose em infusão de insulina.",
                                   "Homem jovem com tireotoxicose e fraqueza súbita após refeição rica em carboidrato."]),
        "f_hk_diarreia": "Paciente com diarreia crônica e abuso de laxativos.",
        "f_hk_ingesta": "Etilista desnutrido que quase não come.",
        "f_hk_atr": "Mulher com Sjögren e nefrocalcinose.",
        "f_hk_primario": "Hipertenso resistente de 45 anos.", "f_hk_secundario": "Hipertensão grave e sopro abdominal.",
        "f_hk_pseudo": rng.choice(["Paciente que consome muito alcaçuz.", "Jovem com hipertensão e história familiar (Liddle)."]),
        "f_hk_vomito": "Gestante com hiperêmese gravídica.", "f_hk_diuretico": "Idosa em uso de furosemida."}
    if alvo == "f_hk_redist":
        c["redist"] = ("nebulização repetida com salbutamol" if "salbutamol" in textos[alvo] else
                       "infusão de insulina" if "insulina" in textos[alvo] else "tireotoxicose com refeição rica em carboidrato")
    elif alvo in ("f_hk_diarreia", "f_hk_ingesta"):
        c["k_u"] = rng.randint(5, 15)
        c["hco3"] = rng.randint(13, 18) if alvo == "f_hk_diarreia" else rng.randint(23, 26)
    else:
        c["k_u"] = rng.randint(30, 80)
        if alvo == "f_hk_atr":
            c["hco3"] = rng.randint(12, 18)
        else:
            c["hco3"] = rng.randint(29, 38)
            if alvo in ("f_hk_primario", "f_hk_secundario", "f_hk_pseudo"):
                c["pa"] = rng.randint(160, 210)
                c["ren"] = {"f_hk_primario": "prim", "f_hk_secundario": "sec", "f_hk_pseudo": "baixas"}[alvo]
            else:
                c["cl_u"] = rng.randint(5, 15) if alvo == "f_hk_vomito" else rng.randint(40, 100)
    c["aldo_txt"] = {"prim": "alta", "sec": "alta", "baixas": "baixa"}[c["ren"]]
    c["renina_txt"] = {"prim": "suprimida", "sec": "alta", "baixas": "baixa"}[c["ren"]]
    c["texto"] = textos[alvo]
    c["mostrar"] = [("K⁺", f"{f1(c['k'])} mEq/L"), ("HCO₃⁻", f"{fi(c['hco3'])} mEq/L"), ("K⁺ urinário", fi(c["k_u"])),
                    ("Cl⁻ urinário", fi(c["cl_u"])), ("PA sistólica", f"{fi(c['pa'])} mmHg")]
    if c["pa"] >= 150:
        c["mostrar"] += [("Aldosterona", c["aldo_txt"]), ("Renina", c["renina_txt"])]
    return c


HIPOCALEMIA = Arvore("hipocalemia", "Hipocalemia", "Redistribuição → K⁺ urinário → ácido-base → pressão → renina",
                     "redist", HK_NOS, _gerar_hk, [n.id for n in HK_NOS if n.folha],
                     lambda c: [("K⁺ urinário", fi(c["k_u"])), ("HCO₃⁻", fi(c["hco3"]))])

# ================================================================== 5. HIPERCALEMIA

HP_NOS = [
    No("pseudo", "É real?", "Hipercalemia. Pode ser pseudo-hipercalemia (erro de coleta)?",
       [("Pode ser pseudo", "hemólise, plaquetas/leucócitos muito altos", "f_hp_pseudo", None),
        ("É real", "coleta boa", "grav", None)],
       lambda c: 0 if c["pseudo"] else 1,
       lambda c: "Hemólise na amostra, trombocitose ou leucocitose extremas e ECG normal sugerem pseudo." +
                 (f" Aqui: {c['pseudo']}." if c["pseudo"] else " Aqui a coleta foi adequada.")),
    No("grav", "Gravidade", "É real. É grave (ECG alterado ou K⁺ ≥ 6,5)?",
       [("Grave", "ECG alterado ou ≥ 6,5", "causa", "grave: cálcio IV + insulina-glicose + remover"),
        ("Não grave", "ECG normal e < 6,5", "causa", "sem cálcio: redistribuir e remover")],
       lambda c: 0 if c["ecg_alt"] or c["k"] >= 6.5 else 1,
       lambda c: f"K⁺ {f1(c['k'])} e ECG {'com ' + c['ecg'] if c['ecg_alt'] else 'normal'}: grave se ECG alterado ou K⁺ ≥ 6,5."),
    No("causa", "Por quê?", "Qual o mecanismo da hipercalemia?",
       [("Lise celular", "CK/ácido úrico altos", "f_hp_lise", None), ("Saiu da célula", "CAD, acidose", "f_hp_redist", None),
        ("Rim não excreta", "TFG < 20", "f_hp_rim", None), ("Droga", "bloqueia aldosterona", "f_hp_droga", None)],
       lambda c: {"lise": 0, "redist": 1, "rim": 2, "droga": 3}[c["mec"]],
       lambda c: f"Pistas: {c['pistas']}."),
    Folha("f_hp_pseudo", "Pseudo", "Provável pseudo-hipercalemia: repita a dosagem no plasma ou na gasometria",
          "Se o ECG estiver alterado, trate como verdadeira enquanto confirma."),
    Folha("f_hp_lise", "Lise celular", "Hipercalemia por lise celular (rabdomiólise, lise tumoral)",
          "Subida rápida e perigosa, ainda mais com lesão renal. Pense cedo em diálise."),
    Folha("f_hp_redist", "Redistribuição", "Hipercalemia por saída de K⁺ das células (falta de insulina, acidose)",
          "Na CAD, o K⁺ total está baixo: com a insulina ele despenca. Repor quando cair abaixo de 5."),
    Folha("f_hp_rim", "Excreção", "Hipercalemia por excreção renal reduzida (doença renal avançada ou lesão aguda)",
          "Remover: diurético se ainda urina, quelante, diálise nos graves."),
    Folha("f_hp_droga", "Droga", "Hipercalemia por droga que reduz a aldosterona ou bloqueia o ENaC",
          "IECA, BRA, espironolactona, AINE, trimetoprim, heparina. Ajuste e use quelante para manter o que protege."),
]


def _gerar_hp(rng, alvo):
    c = {"k": round(rng.uniform(5.7, 7.4), 1), "pseudo": "", "ecg_alt": False, "ecg": "", "mec": "rim", "pistas": ""}
    if alvo == "f_hp_pseudo":
        c["pseudo"] = rng.choice(["amostra hemolisada, coleta difícil com garrote longo", "plaquetas de 1.300.000/mm³"])
        c["k"] = round(rng.uniform(5.7, 6.8), 1)
        texto = "Paciente assintomático em exame de rotina, ECG normal."
    else:
        if rng.random() < 0.5:
            c["ecg_alt"] = True
            c["ecg"] = rng.choice(["ondas T apiculadas", "QRS alargado", "PR longo e P achatada"])
        c["mec"] = {"f_hp_lise": "lise", "f_hp_redist": "redist", "f_hp_rim": "rim", "f_hp_droga": "droga"}[alvo]
        c["pistas"] = {"lise": "CK 48.000, urina escura após esforço extremo",
                       "redist": "glicemia 540, pH 7,08, cetonas +++",
                       "rim": "creatinina 7,8, TFG 8 mL/min, sem diálise",
                       "droga": "TFG 55, uso de enalapril e espironolactona, iniciou ibuprofeno"}[c["mec"]]
        texto = {"lise": "Maratonista com dor muscular intensa.", "redist": "Jovem com DM1 e vômitos.",
                 "rim": "Renal crônico que faltou à consulta.", "droga": "Cardiopata em tratamento otimizado."}[c["mec"]]
    c["texto"] = texto
    c["mostrar"] = [("K⁺", f"{f1(c['k'])} mEq/L"), ("ECG", c["ecg"] if c["ecg_alt"] else "normal"),
                    ("Coleta", c["pseudo"] or "adequada"), ("Outros achados", c["pistas"] or "—")]
    return c


HIPERCALEMIA = Arvore("hipercalemia", "Hipercalemia", "É real? → gravidade → mecanismo", "pseudo", HP_NOS, _gerar_hp,
                      [n.id for n in HP_NOS if n.folha], lambda c: [("K⁺", f1(c["k"]))])

ARVORES = [ACIDO_BASE, HIPONATREMIA, HIPERNATREMIA, HIPOCALEMIA, HIPERCALEMIA]
POR_ID = {a.id: a for a in ARVORES}
ARVORES_PRONTAS = True


def novo_caso(arvore, rng):
    """Sorteia uma folha-alvo e gera um caso que leva até ela."""
    alvo = rng.choice(arvore.alvos)
    c = arvore.gerar(rng, alvo)
    c["_alvo"] = alvo
    return c


# ================================================================== contas por nó (nível 2+: o jogador calcula)
# calc(caso) -> (pergunta, valor certo, [(valor errado, que erro é)], fórmula com os números, casas decimais)

def _c_ag(c):
    certo = _agc(c)
    err = [(_ag(c), "esqueceu de corrigir pela albumina"), (c["na"] - c["cl"], "esqueceu de subtrair o HCO₃⁻"),
           (_ag(c) - 2.5 * (4 - c["alb"]), "corrigiu com o sinal trocado"), (certo + 6, "errou a conta")]
    form = (f"{fi(c['na'])} − ({fi(c['cl'])} + {fi(c['hco3'])}) + 2,5 × (4 − {f1(c['alb'])}) = {fi(certo)}")
    return "Quanto dá o ânion gap CORRIGIDO pela albumina?", certo, err, form, 0


def _c_winter(c):
    e = _winter(c)
    err = [(1.5 * c["hco3"], "esqueceu o + 8"), (_comp_alc(c), "usou a fórmula da alcalose"),
           (c["hco3"] + 15, "usou o atalho HCO₃⁻ + 15 da alcalose"), (e + 8, "errou a conta")]
    return "Qual a PaCO₂ esperada (fórmula de Winter)?", e, err, f"1,5 × {fi(c['hco3'])} + 8 = {f1(e)}", 1


def _c_comp_alc(c):
    e = _comp_alc(c)
    err = [(_winter(c), "usou Winter, que é da acidose"), (40 + c["hco3"], "somou o HCO₃⁻ inteiro"),
           (0.7 * c["hco3"], "esqueceu o + 21"), (e - 7, "errou a conta")]
    return "Qual a PaCO₂ esperada na alcalose metabólica?", e, err, f"0,7 × {fi(c['hco3'])} + 21 = {f1(e)}", 1


def _c_dd(c):
    d = _dd(c)
    den = max(0.5, 24 - c["hco3"])
    err = [((_ag(c) - 12) / den, "usou o AG sem corrigir"), (den / max(0.5, _agc(c) - 12), "inverteu a fração"),
           (_agc(c) / den, "esqueceu de tirar o 12 do AG"), (d + 1.2, "errou a conta")]
    return "Quanto dá o delta-delta (Δ/Δ)?", d, err, f"({fi(_agc(c))} − 12) / (24 − {fi(c['hco3'])}) = {f1(d)}", 1


def _c_agu(c):
    v = _agu(c)
    err = [(c["na_u"] - c["cl_u"], "esqueceu o K⁺ urinário"), (-v, "trocou o sinal"),
           (c["na_u"] + c["k_u"] + c["cl_u"], "somou o cloro em vez de subtrair"), (v + 15, "errou a conta")]
    return "Quanto dá o ânion gap urinário?", v, err, f"{fi(c['na_u'])} + {fi(c['k_u'])} − {fi(c['cl_u'])} = {fi(v)}", 0


def _c_gap(c):
    calc = 2 * c["na"] + c["glic"] / 18 + c["ureia"] / 6
    v = c["osm"] - calc
    err = [(c["osm"] - 2 * c["na"], "esqueceu glicose e ureia"), (c["osm"] - (2 * c["na"] + c["glic"] / 18), "esqueceu a ureia"),
           (c["osm"] - (c["na"] + c["glic"] / 18 + c["ureia"] / 6), "não multiplicou o sódio por 2"), (v + 12, "errou a conta")]
    form = f"{fi(c['osm'])} − (2 × {fi(c['na'])} + {fi(c['glic'])}/18 + {fi(c['ureia'])}/6) = {fi(v)}"
    return "Quanto dá o gap osmolar?", v, err, form, 0


def _c_resp_acid(c):
    ea, ec = _resp_acid_esp(c)
    err = [(ea, "esse é o esperado na AGUDA"), (24 + 2 * (c["pco2"] - 40) / 10, "usou 2 por 10"),
           (24 + 5 * (c["pco2"] - 40) / 10, "usou 5 por 10"), (ec + 4, "errou a conta")]
    return ("Se fosse CRÔNICA, qual seria o HCO₃⁻ esperado?", ec, err,
            f"24 + 3,5 × ({fi(c['pco2'])} − 40)/10 = {f1(ec)}", 1)


def _c_resp_alc(c):
    ea, ec = _resp_alc_esp(c)
    err = [(ea, "esse é o esperado na AGUDA"), (24 - 3.5 * (40 - c["pco2"]) / 10, "usou 3,5 por 10"),
           (24 - 1 * (40 - c["pco2"]) / 10, "usou 1 por 10"), (ec - 4, "errou a conta")]
    return ("Se fosse CRÔNICA, qual seria o HCO₃⁻ esperado?", ec, err,
            f"24 − 4,5 × (40 − {fi(c['pco2'])})/10 = {f1(ec)}", 1)


def _c_ddavp(c):
    v = 100 * (c["osm_u_ddavp"] / c["osm_u"] - 1)
    err = [(c["osm_u_ddavp"] - c["osm_u"], "deu a diferença em mOsm, não em %"),
           (100 * c["osm_u"] / c["osm_u_ddavp"], "inverteu a fração"), (v + 40, "errou a conta"), (v - 30, "errou a conta")]
    return ("Quanto (%) a osm urinária subiu com a desmopressina?", v, err,
            f"({fi(c['osm_u_ddavp'])} / {fi(c['osm_u'])} − 1) × 100 = {fi(v)}%", 0)


for _a, _nid, _f in [(ACIDO_BASE, "ag", _c_ag), (ACIDO_BASE, "winter", _c_winter), (ACIDO_BASE, "comp_alc", _c_comp_alc),
                     (ACIDO_BASE, "dd", _c_dd), (ACIDO_BASE, "agu", _c_agu), (ACIDO_BASE, "causa", _c_gap),
                     (ACIDO_BASE, "resp_acid", _c_resp_acid), (ACIDO_BASE, "resp_alc", _c_resp_alc),
                     (HIPERNATREMIA, "ddavp", _c_ddavp)]:
    _a.nos[_nid].calc = _f
for _a in ARVORES:
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None


def opcoes_calc(no, caso, rng):
    """(pergunta, [textos], índice certo, fórmula, {texto errado: que erro é}) — valores distintos após formatar."""
    r = no.calc(caso)
    if r is None:                       # a conta não se aplica a este caso (ex.: sem antibiótico em uso)
        return None
    pergunta, certo, erros, formula, casas = r
    fmt = (lambda v: f"{v:.{casas}f}".replace(".", ",")) if casas else (lambda v: f"{round(v)}")
    vistos, alts, motivo = {fmt(certo)}, [fmt(certo)], {}
    for v, por in erros:
        t = fmt(v)
        if t not in vistos:
            vistos.add(t)
            alts.append(t)
            motivo[t] = por
        if len(alts) == 4:
            break
    passo = 1 if casas else 4
    k = 2
    while len(alts) < 4:
        t = fmt(certo + passo * k * (1 if k % 2 else -1))
        k += 1
        if t not in vistos:
            vistos.add(t)
            alts.append(t)
            motivo[t] = "errou a conta"
    certo_txt = alts[0]
    rng.shuffle(alts)
    return pergunta, alts, alts.index(certo_txt), formula, motivo


# ================================================================== 6. HIPOXEMIA (gradiente alvéolo-arterial)

def _pao2_alv(c):
    return c["fio2"] * (c["patm"] - 47) - c["pco2"] / 0.8


def _grad(c):
    return _pao2_alv(c) - c["pao2"]


def _grad_lim(c):
    return c["idade"] / 4 + 4


def _c_grad(c):
    v = _grad(c)
    err = [(c["fio2"] * (c["patm"] - 47) - c["pco2"] - c["pao2"], "esqueceu de dividir a PaCO₂ por 0,8"),
           (c["fio2"] * c["patm"] - c["pco2"] / 0.8 - c["pao2"], "esqueceu de tirar 47 (vapor d'água)"),
           (c["pao2"] - _pao2_alv(c), "inverteu a subtração"), (v + 15, "errou a conta")]
    form = (f"PAO₂ = {f2(c['fio2'])} × ({fi(c['patm'])} − 47) − {fi(c['pco2'])}/0,8 = {fi(_pao2_alv(c))}; "
            f"gradiente = {fi(_pao2_alv(c))} − {fi(c['pao2'])} = {fi(v)}")
    return "Quanto dá o gradiente alvéolo-arterial?", v, err, form, 0


HX_NOS = [
    No("aa", "Gradiente A-a", "Hipoxemia. O gradiente alvéolo-arterial está normal ou aumentado?",
       [("Normal", "≤ idade/4 + 4", "aa_normal", None), ("Aumentado", "> idade/4 + 4", "o2", None)],
       lambda c: 0 if _grad(c) <= _grad_lim(c) else 1,
       lambda c: (f"PAO₂ = FiO₂ × (Patm − 47) − PaCO₂/0,8 = {fi(_pao2_alv(c))}; gradiente = {fi(_pao2_alv(c))} − "
                  f"{fi(c['pao2'])} = {fi(_grad(c))}. Limite para {c['idade']} anos: {fi(_grad_lim(c))}.")),
    No("aa_normal", "Por que falta O₂?", "Gradiente normal: o pulmão troca bem. Por que falta oxigênio no alvéolo?",
       [("PaCO₂ alta", "hipoventilação", "f_hx_hipovent", None), ("PaCO₂ normal/baixa", "pouco O₂ no ar", "f_hx_altitude", None)],
       lambda c: 0 if c["pco2"] > 45 else 1,
       lambda c: f"PaCO₂ {fi(c['pco2'])}: acima de 45 o alvéolo tem pouco O₂ porque o ar não está sendo trocado."),
    No("o2", "Resposta ao O₂", "Gradiente aumentado: o problema é no pulmão. A PaO₂ sobe bem com oxigênio a 100%?",
       [("Sobe bem", "PaO₂ > 300 com O₂ 100%", "vq", None), ("Quase não sobe", "PaO₂ < 150 com O₂ 100%", "f_hx_shunt", None)],
       lambda c: 0 if c["pao2_100"] > 300 else 1,
       lambda c: f"Com O₂ a 100%, a PaO₂ foi a {fi(c['pao2_100'])}: o shunt não melhora, porque o sangue passa por alvéolo sem ar."),
    No("vq", "V/Q ou difusão?", "Melhora com O₂. É distúrbio ventilação-perfusão ou de difusão?",
       [("DLCO normal", "piora pouco no esforço", "f_hx_vq", None), ("DLCO baixa", "dessatura no esforço", "f_hx_difusao", None)],
       lambda c: 0 if c["dlco"] >= 70 else 1,
       lambda c: f"DLCO {fi(c['dlco'])}% do previsto: baixa aponta membrana espessada (difusão), que piora no exercício."),
    Folha("f_hx_hipovent", "Hipoventilação", "Hipoxemia por hipoventilação (gradiente normal, PaCO₂ alta)",
          "Opioide, sedativo, doença neuromuscular, obesidade-hipoventilação. Trate a ventilação, não só dê oxigênio."),
    Folha("f_hx_altitude", "Ar pobre em O₂", "Hipoxemia por baixa pressão de O₂ inspirado (altitude)",
          "O pulmão está bom; falta oxigênio no ar. Gradiente normal e PaCO₂ baixa pela hiperventilação."),
    Folha("f_hx_shunt", "Shunt", "Hipoxemia por shunt (SDRA, atelectasia, pneumonia extensa, malformação AV)",
          "O sangue passa por alvéolos sem ar: oxigênio a 100% quase não ajuda. PEEP e recrutamento abrem alvéolos."),
    Folha("f_hx_vq", "Distúrbio V/Q", "Hipoxemia por distúrbio ventilação-perfusão (o mecanismo mais comum)",
          "DPOC, asma, embolia, pneumonia. Melhora bem com oxigênio suplementar."),
    Folha("f_hx_difusao", "Difusão", "Hipoxemia por distúrbio de difusão (doença intersticial)",
          "Membrana espessada: piora no exercício, DLCO baixa. Fibrose pulmonar, pneumonite."),
]


def _gerar_hx(rng, alvo):
    c = {"idade": rng.randint(25, 75), "patm": 760, "fio2": 0.21, "pco2": rng.randint(34, 42), "pao2": 0,
         "pao2_100": 0, "dlco": rng.randint(80, 100), "exerc": "não dessatura"}
    for _ in range(200):
        if alvo == "f_hx_altitude":
            c["patm"] = rng.choice([500, 520, 540])
            c["pco2"] = rng.randint(26, 33)
            c["pao2"] = round(_pao2_alv(c) - rng.uniform(3, _grad_lim(c) - 3))
            texto = "Montanhista saudável a 3.800 metros de altitude."
        elif alvo == "f_hx_hipovent":
            c["pco2"] = rng.randint(62, 80)
            c["pao2"] = round(_pao2_alv(c) - rng.uniform(3, _grad_lim(c) - 3))
            texto = rng.choice(["Jovem sonolento após overdose de opioide, pulmões limpos.", "Paciente com miastenia em crise."])
        else:
            c["pao2"] = rng.randint(48, 62)
            if _grad(c) <= _grad_lim(c) + 6:
                continue
            if alvo == "f_hx_shunt":
                c["pao2_100"] = rng.randint(70, 140)
                texto = rng.choice(["Paciente com SDRA por pneumonia grave.", "Pós-operatório com atelectasia de lobo inteiro."])
            else:
                c["pao2_100"] = rng.randint(380, 560)
                if alvo == "f_hx_difusao":
                    c["dlco"], c["exerc"] = rng.randint(30, 55), "dessatura muito ao caminhar"
                    texto = "Paciente com fibrose pulmonar, estertores em velcro."
                else:
                    texto = rng.choice(["DPOC em exacerbação.", "Paciente com embolia pulmonar.", "Asmático em crise."])
        if c["pao2"] > 25:
            break
    c["texto"] = texto
    c["mostrar"] = [("Idade", f"{c['idade']} anos"), ("Pressão atmosférica", f"{fi(c['patm'])} mmHg"),
                    ("FiO₂", f2(c["fio2"])), ("PaO₂", f"{fi(c['pao2'])} mmHg"), ("PaCO₂", f"{fi(c['pco2'])} mmHg"),
                    ("PaO₂ com O₂ a 100%", fi(c["pao2_100"]) if c["pao2_100"] else "não feito"),
                    ("DLCO", f"{fi(c['dlco'])}% do previsto"), ("No exercício", c["exerc"])]
    return c


HIPOXEMIA = Arvore("hipoxemia", "Hipoxemia (gradiente A-a)", "Gradiente A-a → resposta ao O₂ → V/Q, difusão ou shunt",
                   "aa", HX_NOS, _gerar_hx, [n.id for n in HX_NOS if n.folha],
                   lambda c: [("PAO₂", fi(_pao2_alv(c))), ("Gradiente A-a", fi(_grad(c))),
                              ("Limite para a idade", fi(_grad_lim(c)))])

# ================================================================== 7. HIPERCALCEMIA

HC_NOS = [
    No("pth", "PTH", "Hipercalcemia confirmada. O PTH está alto (ou normal, o que já é inadequado) ou suprimido?",
       [("PTH alto/normal", "não suprimido", "calciuria", None), ("PTH suprimido", "< 20 pg/mL", "pthrp", None)],
       lambda c: 0 if c["pth"] >= 20 else 1,
       lambda c: f"PTH {fi(c['pth'])} pg/mL: com cálcio alto, o PTH deveria estar suprimido. Normal ou alto = a paratireoide é a culpada."),
    No("calciuria", "Calciúria", "PTH não suprimido. O cálcio urinário está baixo?",
       [("Ca urinário baixo", "fração < 0,01", "f_hc_hhf", None), ("Ca urinário normal/alto", "fração > 0,02", "f_hc_hpp", None)],
       lambda c: 0 if c["fe_ca"] < 0.01 else 1,
       lambda c: f"Fração de excreção de cálcio {c['fe_ca']:.3f}".replace(".", ",") +
                 ": abaixo de 0,01 sugere hipercalcemia hipocalciúrica familiar, que não se opera."),
    No("pthrp", "PTHrP", "PTH suprimido: o cálcio vem de fora da paratireoide. O PTHrP está alto?",
       [("PTHrP alto", "tumor produz", "f_hc_pthrp", None), ("PTHrP normal", "outra via", "vitd", None)],
       lambda c: 0 if c["pthrp"] else 1,
       lambda c: "PTHrP " + ("alto: o tumor produz um peptídeo que imita o PTH." if c["pthrp"] else "normal.")),
    No("vitd", "Vitamina D", "PTH e PTHrP baixos. Olhe as duas formas de vitamina D.",
       [("1,25-OH alta", "granuloma/linfoma", "f_hc_granuloma", None), ("25-OH alta", "intoxicação", "f_hc_vitd", None),
        ("Ambas normais", "osso liberando", "f_hc_osteolise", None)],
       lambda c: 0 if c["calcitriol"] else 1 if c["vit25"] > 150 else 2,
       lambda c: f"25-OH-vitamina D {fi(c['vit25'])} ng/mL (alta se > 150) e 1,25-OH {'alta' if c['calcitriol'] else 'normal'}."),
    Folha("f_hc_hpp", "Hiperparatireoidismo 1º", "Hiperparatireoidismo primário (adenoma de paratireoide)",
          "A causa mais comum no ambulatório. Cálculos, osteoporose, sintomas leves. Cirurgia se critérios."),
    Folha("f_hc_hhf", "Hipocalciúrica familiar", "Hipercalcemia hipocalciúrica familiar (mutação do sensor de cálcio)",
          "PTH normal ou pouco alto com cálcio urinário muito baixo. Benigna: não operar."),
    Folha("f_hc_pthrp", "PTHrP (câncer)", "Hipercalcemia humoral da malignidade (PTHrP)",
          "A causa mais comum no hospital: carcinoma escamoso, mama, rim. Hidratação, bisfosfonato ou denosumabe."),
    Folha("f_hc_granuloma", "Calcitriol", "Excesso de calcitriol: granulomas (sarcoidose, tuberculose) ou linfoma",
          "O granuloma produz 1,25-OH-vitamina D. Corticoide reduz essa produção."),
    Folha("f_hc_vitd", "Intox. vitamina D", "Intoxicação por vitamina D (suplemento em dose excessiva)",
          "Suspender o suplemento, hidratar; corticoide se grave."),
    Folha("f_hc_osteolise", "Osso", "Liberação óssea: metástases líticas, mieloma, imobilização ou tireotoxicose",
          "Peça eletroforese de proteínas (mieloma), cintilografia ou TC. Bisfosfonato reduz a reabsorção."),
]


def _gerar_hc(rng, alvo):
    c = {"ca": round(rng.uniform(11.2, 14.5), 1), "pth": rng.randint(5, 15), "fe_ca": round(rng.uniform(0.02, 0.04), 3),
         "pthrp": False, "vit25": rng.randint(25, 60), "calcitriol": False}
    texto = {"f_hc_hpp": "Mulher de 58 anos com cálculos renais e osteoporose.",
             "f_hc_hhf": "Jovem assintomático; o pai também tem cálcio alto há anos.",
             "f_hc_pthrp": "Tabagista com carcinoma escamoso de pulmão e confusão.",
             "f_hc_granuloma": "Paciente com adenopatia hilar bilateral e lesões de pele.",
             "f_hc_vitd": "Mulher que toma vitamina D em dose altíssima por conta própria.",
             "f_hc_osteolise": rng.choice(["Idoso com dor lombar, anemia e insuficiência renal.", "Mulher com câncer de mama e metástases ósseas."])}[alvo]
    if alvo in ("f_hc_hpp", "f_hc_hhf"):
        c["pth"] = rng.randint(55, 140) if alvo == "f_hc_hpp" else rng.randint(30, 70)
        c["fe_ca"] = round(rng.uniform(0.002, 0.008), 3) if alvo == "f_hc_hhf" else round(rng.uniform(0.022, 0.045), 3)
        if alvo == "f_hc_hhf":
            c["ca"] = round(rng.uniform(10.6, 11.4), 1)
    elif alvo == "f_hc_pthrp":
        c["pthrp"] = True
    elif alvo == "f_hc_granuloma":
        c["calcitriol"] = True
    elif alvo == "f_hc_vitd":
        c["vit25"] = rng.randint(180, 400)
    c["texto"] = texto
    c["mostrar"] = [("Cálcio (corrigido)", f"{f1(c['ca'])} mg/dL"), ("PTH", f"{fi(c['pth'])} pg/mL"),
                    ("Fração de excreção de Ca", f"{c['fe_ca']:.3f}".replace(".", ",")),
                    ("PTHrP", "alto" if c["pthrp"] else "normal" if c["pth"] < 20 else "não dosado"),
                    ("25-OH-vitamina D", f"{fi(c['vit25'])} ng/mL"), ("1,25-OH-vitamina D", "alta" if c["calcitriol"] else "normal")]
    return c


HIPERCALCEMIA = Arvore("hipercalcemia", "Hipercalcemia", "PTH → calciúria → PTHrP → vitamina D", "pth", HC_NOS,
                       _gerar_hc, [n.id for n in HC_NOS if n.folha], lambda c: [("PTH", fi(c["pth"]))])

# ================================================================== 8. HIPOCALCEMIA

def _ca_corr(c):
    return c["ca"] + 0.8 * (4 - c["alb"])


def _c_ca_corr(c):
    v = _ca_corr(c)
    err = [(c["ca"], "não corrigiu"), (c["ca"] - 0.8 * (4 - c["alb"]), "corrigiu com o sinal trocado"),
           (c["ca"] + 2.5 * (4 - c["alb"]), "usou o fator 2,5 do ânion gap"), (v + 1.2, "errou a conta")]
    return ("Quanto dá o cálcio corrigido pela albumina?", v, err,
            f"{f1(c['ca'])} + 0,8 × (4 − {f1(c['alb'])}) = {f1(v)}", 1)


HO_NOS = [
    No("corr", "Cálcio corrigido", "Cálcio total baixo. Corrigido pela albumina, ele continua baixo?",
       [("Normal", "corrigido ≥ 8,5", "f_ho_pseudo", None), ("Baixo", "corrigido < 8,5", "mg", None)],
       lambda c: 0 if _ca_corr(c) >= 8.5 else 1,
       lambda c: f"Cálcio corrigido = {f1(c['ca'])} + 0,8 × (4 − {f1(c['alb'])}) = {f1(_ca_corr(c))}."),
    No("mg", "Magnésio", "Hipocalcemia verdadeira. Antes de tudo, o magnésio está baixo?",
       [("Mg baixo", "< 1,2 mg/dL", "f_ho_mg", None), ("Mg normal", "≥ 1,7", "pth", None)],
       lambda c: 0 if c["mg"] < 1.2 else 1,
       lambda c: f"Magnésio {f1(c['mg'])}: sem magnésio, a paratireoide não secreta PTH e o cálcio não sobe."),
    No("pth", "PTH", "Magnésio normal. O PTH está baixo (inadequado) ou alto (reagindo)?",
       [("PTH baixo", "glândula falhou", "f_ho_hipopara", None), ("PTH alto", "glândula reage", "fosforo", None)],
       lambda c: 0 if c["pth"] < 20 else 1,
       lambda c: f"PTH {fi(c['pth'])} pg/mL: com cálcio baixo, o PTH deveria subir. Baixo = hipoparatireoidismo."),
    No("fosforo", "Fósforo", "PTH alto: a glândula reage. Como está o fósforo?",
       [("Fósforo alto", "> 4,5", "renal_ho", None), ("Fósforo baixo", "< 2,5", "f_ho_vitd", None)],
       lambda c: 0 if c["p"] > 4.5 else 1,
       lambda c: f"Fósforo {f1(c['p'])}: o PTH deveria jogar fósforo na urina; alto = rim falhando ou resistência ao PTH."),
    No("renal_ho", "Função renal", "PTH e fósforo altos. Como está a função renal?",
       [("TFG baixa", "< 30", "f_ho_drc", None), ("TFG normal", "≥ 60", "f_ho_pseudohipo", None)],
       lambda c: 0 if c["tfg"] < 30 else 1,
       lambda c: f"TFG {fi(c['tfg'])} mL/min: a doença renal retém fósforo e não ativa a vitamina D."),
    Folha("f_ho_pseudo", "Albumina baixa", "Pseudo-hipocalcemia: só a albumina está baixa (cálcio iônico normal)",
          "Corrija o cálcio ou dose o cálcio iônico. Não reponha cálcio."),
    Folha("f_ho_mg", "Hipomagnesemia", "Hipocalcemia por hipomagnesemia (álcool, diarreia, IBP, diurético)",
          "Reponha o magnésio primeiro: o cálcio só corrige depois."),
    Folha("f_ho_hipopara", "Hipoparatireoidismo", "Hipoparatireoidismo (pós-tireoidectomia, autoimune, infiltração)",
          "Fósforo alto e PTH baixo. Cálcio e calcitriol."),
    Folha("f_ho_vitd", "Falta de vitamina D", "Deficiência de vitamina D (fósforo baixo, PTH reagindo)",
          "Pouco sol, má absorção, doença hepática. Reponha vitamina D e cálcio."),
    Folha("f_ho_drc", "Doença renal", "Hipocalcemia da doença renal crônica (fósforo alto, calcitriol baixo)",
          "Quelante de fósforo, calcitriol, controle do hiperparatireoidismo secundário."),
    Folha("f_ho_pseudohipo", "Resistência ao PTH", "Pseudo-hipoparatireoidismo (resistência ao PTH)",
          "PTH alto com fósforo alto e rim normal; pode ter baixa estatura e metacarpos curtos."),
]


def _gerar_ho(rng, alvo):
    c = {"ca": round(rng.uniform(6.8, 7.9), 1), "alb": 4.0, "mg": round(rng.uniform(1.8, 2.3), 1),
         "pth": rng.randint(70, 160), "p": round(rng.uniform(2.6, 4.2), 1), "tfg": rng.randint(70, 110)}
    texto = {"f_ho_pseudo": "Cirrótico internado com ascite, assintomático.", "f_ho_mg": "Etilista com diarreia e tremores.",
             "f_ho_hipopara": "Mulher com parestesias 2 dias após tireoidectomia total.",
             "f_ho_vitd": "Idosa acamada, sem sol, com dores ósseas.", "f_ho_drc": "Renal crônico em tratamento conservador.",
             "f_ho_pseudohipo": "Adolescente com baixa estatura e quarto metacarpo curto."}[alvo]
    if alvo == "f_ho_pseudo":
        c["alb"] = round(rng.uniform(1.8, 2.4), 1)
        c["ca"] = round(rng.uniform(7.4, 8.0), 1)
        if _ca_corr(c) < 8.6:
            c["ca"] = round(8.7 - 0.8 * (4 - c["alb"]) + 0.1, 1)
    else:
        if rng.random() < 0.3:
            c["alb"] = round(rng.uniform(3.4, 3.8), 1)
        if alvo == "f_ho_mg":
            c["mg"] = round(rng.uniform(0.6, 1.0), 1)
        elif alvo == "f_ho_hipopara":
            c.update(pth=rng.randint(3, 12), p=round(rng.uniform(5.0, 6.5), 1))
        elif alvo == "f_ho_vitd":
            c["p"] = round(rng.uniform(1.6, 2.3), 1)
        else:
            c["p"] = round(rng.uniform(5.2, 7.5), 1)
            c["tfg"] = rng.randint(8, 22) if alvo == "f_ho_drc" else rng.randint(75, 110)
    c["texto"] = texto
    c["mostrar"] = [("Cálcio total", f"{f1(c['ca'])} mg/dL"), ("Albumina", f"{f1(c['alb'])} g/dL"),
                    ("Magnésio", f"{f1(c['mg'])} mg/dL"), ("PTH", f"{fi(c['pth'])} pg/mL"), ("Fósforo", f"{f1(c['p'])} mg/dL"),
                    ("TFG", f"{fi(c['tfg'])} mL/min")]
    return c


HIPOCALCEMIA = Arvore("hipocalcemia", "Hipocalcemia", "Cálcio corrigido → magnésio → PTH → fósforo → rim", "corr", HO_NOS,
                      _gerar_ho, [n.id for n in HO_NOS if n.folha], lambda c: [("Cálcio corrigido", f1(_ca_corr(c)))])

# ================================================================== 9. LESÃO RENAL AGUDA

def _fena(c):
    return 100 * (c["na_u"] * c["cr"]) / (c["na"] * c["cr_u"])


def _feur(c):
    return 100 * (c["ur_u"] * c["cr"]) / (c["ur"] * c["cr_u"])


def _c_fena(c):
    v = _fena(c)
    err = [(100 * c["na_u"] / c["na"], "esqueceu as creatininas"), (100 * (c["na"] * c["cr_u"]) / (c["na_u"] * c["cr"]), "inverteu a fração"),
           (c["na_u"] * c["cr"] / (c["na"] * c["cr_u"]), "esqueceu de multiplicar por 100"), (v + 1.5, "errou a conta")]
    return ("Quanto dá a fração de excreção de sódio (FENa)?", v, err,
            f"100 × ({fi(c['na_u'])} × {f1(c['cr'])}) / ({fi(c['na'])} × {fi(c['cr_u'])}) = {f1(v)}%", 1)


def _c_feur(c):
    v = _feur(c)
    err = [(100 * c["ur_u"] / c["ur"], "esqueceu as creatininas"), (_fena(c), "calculou a FENa, que o diurético falseia"),
           (v + 18, "errou a conta"), (v - 15, "errou a conta")]
    return ("Quanto dá a fração de excreção de ureia (FEureia)?", v, err,
            f"100 × ({fi(c['ur_u'])} × {f1(c['cr'])}) / ({fi(c['ur'])} × {fi(c['cr_u'])}) = {fi(v)}%", 0)


LR_NOS = [
    No("pos", "Obstrução?", "Lesão renal aguda. Primeiro: há obstrução (ultrassom com hidronefrose, bexigoma)?",
       [("Sim", "hidronefrose/bexigoma", "f_lr_pos", None), ("Não", "vias livres", "diur", None)],
       lambda c: 0 if c["obstr"] else 1,
       lambda c: "Ultrassom: " + ("hidronefrose bilateral." if c["obstr"] else "sem hidronefrose.") +
                 " Obstrução é a causa mais fácil de reverter e se exclui primeiro."),
    No("diur", "Diurético?", "Sem obstrução. O paciente recebeu diurético?",
       [("Sim", "use a FEureia", "feur", None), ("Não", "use a FENa", "fena", None)],
       lambda c: 0 if c["diuretico"] else 1,
       lambda c: "O diurético faz o rim perder sódio de propósito e falseia a FENa; aí se usa a FEureia."),
    No("fena", "FENa", "Calcule a FENa. O rim está poupando sódio?",
       [("FENa < 1%", "rim poupando", "f_lr_pre", None), ("FENa > 2%", "túbulo lesado", "sed", None)],
       lambda c: 0 if _fena(c) < 1 else 1,
       lambda c: f"FENa = 100 × (Na⁺u × Cr) / (Na⁺ × Cr u) = {f1(_fena(c))}%. Abaixo de 1% o túbulo funciona e segura sódio."),
    No("feur", "FEureia", "Com diurético, calcule a FEureia. O rim está poupando ureia?",
       [("FEureia < 35%", "pré-renal", "f_lr_pre", None), ("FEureia > 50%", "túbulo lesado", "sed", None)],
       lambda c: 0 if _feur(c) < 35 else 1,
       lambda c: f"FEureia = {fi(_feur(c))}%. Abaixo de 35% é pré-renal mesmo com diurético."),
    No("sed", "Sedimento", "Lesão do rim (intrínseca). O que o sedimento urinário mostra?",
       [("Cilindros granulosos", "barro marrom", "f_lr_nta", None), ("Hemácias dismórficas", "cilindros hemáticos", "f_lr_gn", None),
        ("Leucócitos, eosinófilos", "leucocitúria estéril", "f_lr_nia", None)],
       lambda c: {"nta": 0, "gn": 1, "nia": 2}[c["sed"]],
       lambda c: f"Sedimento: {c['sed_txt']}."),
    Folha("f_lr_pos", "Pós-renal", "Lesão renal aguda pós-renal (obstrução)",
          "Próstata, cálculo bilateral, tumor pélvico. Desobstrua (sonda vesical, nefrostomia)."),
    Folha("f_lr_pre", "Pré-renal", "Lesão renal aguda pré-renal (rim bom, pouco fluxo)",
          "Desidratação, sangramento, insuficiência cardíaca, cirrose, AINE/IECA. Corrija a perfusão."),
    Folha("f_lr_nta", "Necrose tubular", "Necrose tubular aguda (isquemia ou toxina)",
          "Choque prolongado, contraste, aminoglicosídeo, rabdomiólise. Suporte e evitar novas agressões."),
    Folha("f_lr_gn", "Glomerulonefrite", "Glomerulonefrite (síndrome nefrítica)",
          "Hematúria dismórfica, cilindros hemáticos, hipertensão, edema. Complemento, ANCA, anti-MBG e biópsia."),
    Folha("f_lr_nia", "Nefrite intersticial", "Nefrite intersticial aguda (geralmente por droga)",
          "Beta-lactâmico, IBP, AINE. Rash, febre, eosinofilia. Suspender a droga; corticoide em casos selecionados."),
]


def _gerar_lr(rng, alvo):
    c = {"na": rng.randint(134, 144), "cr": round(rng.uniform(2.6, 5.5), 1), "ur": rng.randint(110, 220),
         "obstr": False, "diuretico": False, "sed": "nta", "sed_txt": "sem alterações"}
    texto = {"f_lr_pos": "Idoso com prostatismo e anúria há 1 dia.", "f_lr_pre": rng.choice(["Idosa com diarreia e vômitos há 3 dias.", "Cirrótico com ascite em uso de furosemida."]),
             "f_lr_nta": "Paciente após choque séptico prolongado.", "f_lr_gn": "Jovem com urina escura e edema 2 semanas após faringite.",
             "f_lr_nia": "Paciente com rash e febre após começar oxacilina."}[alvo]
    for _ in range(200):
        c["diuretico"] = alvo in ("f_lr_pre", "f_lr_nta") and rng.random() < 0.45
        if "furosemida" in texto:
            c["diuretico"] = True
        c["cr_u"] = rng.randint(40, 160)
        if alvo == "f_lr_pos":
            c["obstr"] = True
            c["na_u"], c["ur_u"] = rng.randint(20, 60), rng.randint(200, 600)
        elif alvo == "f_lr_pre":
            if c["diuretico"]:
                c["na_u"] = rng.randint(40, 90)
                c["ur_u"] = round(0.25 * c["ur"] * c["cr_u"] / c["cr"] * rng.uniform(0.5, 1.0))
            else:
                c["na_u"] = rng.randint(5, 18)
                c["ur_u"] = round(0.3 * c["ur"] * c["cr_u"] / c["cr"])
        else:
            c["cr_u"] = rng.randint(15, 40)
            c["na_u"] = rng.randint(50, 90)
            c["ur_u"] = round(0.6 * c["ur"] * c["cr_u"] / c["cr"] * rng.uniform(0.95, 1.3))
            c["sed"] = {"f_lr_nta": "nta", "f_lr_gn": "gn", "f_lr_nia": "nia"}[alvo]
            c["sed_txt"] = {"nta": "cilindros granulosos pigmentados (barro marrom)",
                            "gn": "hemácias dismórficas e cilindros hemáticos",
                            "nia": "leucócitos, cilindros leucocitários, eosinófilos; urocultura negativa"}[c["sed"]]
        if alvo == "f_lr_pos":
            break
        f = _feur(c) if c["diuretico"] else _fena(c)
        if c["diuretico"] and (f < 32 or f > 52) or not c["diuretico"] and (f < 0.9 or f > 2.2):
            break
    c["texto"] = texto
    c["mostrar"] = [("Creatinina", f"{f1(c['cr'])} mg/dL"), ("Ureia", fi(c["ur"])), ("Na⁺", fi(c["na"])),
                    ("Na⁺ urinário", fi(c["na_u"])), ("Creatinina urinária", fi(c["cr_u"])), ("Ureia urinária", fi(c["ur_u"])),
                    ("Diurético", "sim, furosemida" if c["diuretico"] else "não"),
                    ("Ultrassom", "hidronefrose bilateral" if c["obstr"] else "sem hidronefrose"), ("Sedimento", c["sed_txt"])]
    return c


LRA = Arvore("lra", "Lesão renal aguda", "Obstrução → diurético → FENa/FEureia → sedimento", "pos", LR_NOS, _gerar_lr,
             [n.id for n in LR_NOS if n.folha], lambda c: [("FENa", f"{f1(_fena(c))}%"), ("FEureia", f"{fi(_feur(c))}%")])

# ================================================================== 10. ANEMIAS

def _mentzer(c):
    return c["vcm"] / c["hem"]


def _c_mentzer(c):
    v = _mentzer(c)
    err = [(c["hem"] / c["vcm"] * 10, "inverteu a fração"), (c["vcm"] / c["hb"], "usou a hemoglobina"),
           (v + 6, "errou a conta"), (v - 4, "errou a conta")]
    return ("Quanto dá o índice de Mentzer (VCM ÷ hemácias)?", v, err,
            f"{fi(c['vcm'])} ÷ {f1(c['hem'])} = {f1(v)}", 1)


AN_NOS = [
    No("vcm", "VCM", "Anemia. Comece pelo tamanho da hemácia (VCM).",
       [("Microcítica", "VCM < 80", "ferr", None), ("Normocítica", "80 a 100", "retic", None), ("Macrocítica", "VCM > 100", "b12", None)],
       lambda c: 0 if c["vcm"] < 80 else 2 if c["vcm"] > 100 else 1,
       lambda c: f"VCM {fi(c['vcm'])} fL."),
    No("ferr", "Ferritina", "Microcítica. O estoque de ferro (ferritina) está baixo?",
       [("Ferritina < 30", "estoque vazio", "f_an_ferro", None), ("Ferritina normal/alta", "estoque cheio", "mentzer", None)],
       lambda c: 0 if c["ferritina"] < 30 else 1,
       lambda c: f"Ferritina {fi(c['ferritina'])} ng/mL: abaixo de 30 fecha deficiência de ferro."),
    No("mentzer", "Mentzer", "Ferro guardado. É talassemia ou doença crônica? Calcule o índice de Mentzer.",
       [("Mentzer < 13", "muitas hemácias pequenas", "f_an_talass", None), ("Mentzer > 13", "poucas hemácias", "f_an_cronica", None)],
       lambda c: 0 if _mentzer(c) < 13 else 1,
       lambda c: f"Mentzer = VCM ÷ hemácias = {f1(_mentzer(c))}: abaixo de 13 sugere talassemia (medula produz muitas hemácias pequenas)."),
    No("retic", "Reticulócitos", "Normocítica. A medula está respondendo (reticulócitos)?",
       [("Reticulócitos altos", "> 2%", "hemolise", None), ("Reticulócitos baixos", "< 2%", "f_an_hipopro", None)],
       lambda c: 0 if c["retic"] > 2 else 1,
       lambda c: f"Reticulócitos {f1(c['retic'])}%: alto = sangue sendo perdido ou destruído; baixo = medula não produz."),
    No("hemolise", "Hemólise?", "Medula respondendo. Há sinais de hemólise (LDH e bilirrubina indireta altas, haptoglobina baixa)?",
       [("Sim", "LDH alta, haptoglobina baixa", "coombs", None), ("Não", "provável perda", "f_an_perda", None)],
       lambda c: 0 if c["hemol"] else 1,
       lambda c: f"LDH {fi(c['ldh'])}, haptoglobina {c['hapto']}: " + ("perfil de hemólise." if c["hemol"] else "sem hemólise.")),
    No("coombs", "Coombs", "Há hemólise. O Coombs direto é positivo?",
       [("Coombs +", "anticorpo", "f_an_ahai", None), ("Coombs −, esquizócitos", "quebra mecânica", "f_an_mat", None)],
       lambda c: 0 if c["coombs"] else 1,
       lambda c: "Coombs direto " + ("positivo: anticorpo na hemácia." if c["coombs"] else "negativo com esquizócitos no sangue periférico.")),
    No("b12", "B12 e folato", "Macrocítica. Dose B12 e folato.",
       [("B12 baixa", "< 200 pg/mL", "f_an_b12", None), ("Folato baixo", "< 4 ng/mL", "f_an_folato", None),
        ("Ambos normais", "outra causa", "f_an_macro_outra", None)],
       lambda c: 0 if c["b12"] < 200 else 1 if c["folato"] < 4 else 2,
       lambda c: f"B12 {fi(c['b12'])} pg/mL e folato {f1(c['folato'])} ng/mL."),
    Folha("f_an_ferro", "Ferropriva", "Anemia ferropriva",
          "Procure a perda: sangramento digestivo no homem e na mulher pós-menopausa, menstruação na jovem. Ferro oral ou venoso."),
    Folha("f_an_talass", "Talassemia menor", "Traço talassêmico (talassemia menor)",
          "Hemácias numerosas e pequenas, ferro normal. Eletroforese (HbA2 alta na beta). Não dar ferro."),
    Folha("f_an_cronica", "Doença crônica", "Anemia de doença crônica (inflamação)",
          "Ferritina normal ou alta, saturação baixa, PCR alta. Trate a doença de base."),
    Folha("f_an_hipopro", "Produção baixa", "Anemia hipoproliferativa: doença renal (EPO baixa), aplasia ou infiltração medular",
          "Reticulócitos baixos. Creatinina; se pancitopenia, mielograma."),
    Folha("f_an_perda", "Perda aguda", "Perda aguda de sangue (hemorragia)",
          "Reticulócitos altos sem hemólise. Ache e controle o sangramento."),
    Folha("f_an_ahai", "Autoimune", "Anemia hemolítica autoimune",
          "Coombs direto positivo, esferócitos. Lúpus, linfoma, drogas. Corticoide."),
    Folha("f_an_mat", "Microangiopática", "Anemia hemolítica microangiopática (PTT, SHU, CIVD, valva mecânica)",
          "Esquizócitos e plaquetas baixas. PTT: plasmaférese urgente."),
    Folha("f_an_b12", "Deficiência de B12", "Anemia megaloblástica por deficiência de B12",
          "Anemia perniciosa, gastrectomia, metformina, veganismo. Sintomas neurológicos. B12 IM."),
    Folha("f_an_folato", "Deficiência de folato", "Anemia megaloblástica por deficiência de folato",
          "Álcool, desnutrição, gestação, metotrexato. Ácido fólico (exclua B12 antes)."),
    Folha("f_an_macro_outra", "Macro sem carência", "Macrocitose sem carência: álcool, hepatopatia, hipotireoidismo, mielodisplasia ou drogas",
          "TSH, função hepática; se citopenias, mielograma."),
]


def _gerar_an(rng, alvo):
    c = {"hb": round(rng.uniform(7.2, 10.5), 1), "vcm": rng.randint(84, 96), "hem": round(rng.uniform(3.0, 3.8), 1),
         "ferritina": rng.randint(80, 300), "retic": round(rng.uniform(0.5, 1.5), 1), "hemol": False, "ldh": rng.randint(150, 230),
         "hapto": "normal", "coombs": False, "b12": rng.randint(350, 700), "folato": round(rng.uniform(6, 15), 1)}
    texto = {"f_an_ferro": "Mulher de 34 anos com menstruação abundante.", "f_an_talass": "Jovem assintomático de origem mediterrânea, exame de rotina.",
             "f_an_cronica": "Paciente com artrite reumatoide ativa.", "f_an_hipopro": "Renal crônico em tratamento conservador.",
             "f_an_perda": "Paciente com melena há 2 dias.", "f_an_ahai": "Mulher com lúpus, icterícia e cansaço.",
             "f_an_mat": "Paciente com febre, confusão, plaquetas baixas e esquizócitos.",
             "f_an_b12": "Idoso com parestesias e marcha instável.", "f_an_folato": "Etilista desnutrido.",
             "f_an_macro_outra": "Paciente com hipotireoidismo não tratado."}[alvo]
    if alvo in ("f_an_ferro", "f_an_talass", "f_an_cronica"):
        c["vcm"] = rng.randint(62, 76)
        if alvo == "f_an_ferro":
            c["ferritina"], c["hem"] = rng.randint(3, 20), round(rng.uniform(3.2, 4.0), 1)
        elif alvo == "f_an_talass":                       # VCM bem baixo com muitas hemácias
            c["vcm"] = rng.randint(60, 69)
            c["hem"], c["hb"], c["ferritina"] = round(rng.uniform(5.6, 6.5), 1), round(rng.uniform(10.2, 11.8), 1), rng.randint(60, 200)
        else:
            c["hem"], c["ferritina"] = round(rng.uniform(3.3, 4.2), 1), rng.randint(150, 600)
    elif alvo in ("f_an_hipopro", "f_an_perda", "f_an_ahai", "f_an_mat"):
        if alvo != "f_an_hipopro":
            c["retic"] = round(rng.uniform(4, 12), 1)
        if alvo in ("f_an_ahai", "f_an_mat"):
            c.update(hemol=True, ldh=rng.randint(600, 1500), hapto="indetectável", coombs=alvo == "f_an_ahai")
    else:
        c["vcm"] = rng.randint(106, 124)
        if alvo == "f_an_b12":
            c["b12"] = rng.randint(70, 160)
        elif alvo == "f_an_folato":
            c["folato"] = round(rng.uniform(1.2, 3.2), 1)
    c["texto"] = texto
    c["mostrar"] = [("Hemoglobina", f"{f1(c['hb'])} g/dL"), ("VCM", f"{fi(c['vcm'])} fL"), ("Hemácias", f"{f1(c['hem'])} milhões/µL"),
                    ("Ferritina", f"{fi(c['ferritina'])} ng/mL"), ("Reticulócitos", f"{f1(c['retic'])}%"), ("LDH", fi(c["ldh"])),
                    ("Haptoglobina", c["hapto"]), ("Coombs direto", "positivo" if c["coombs"] else "negativo"),
                    ("B12", f"{fi(c['b12'])} pg/mL"), ("Folato", f"{f1(c['folato'])} ng/mL")]
    return c


ANEMIAS = Arvore("anemias", "Anemias", "VCM → ferritina e Mentzer → reticulócitos → hemólise → B12 e folato", "vcm", AN_NOS,
                 _gerar_an, [n.id for n in AN_NOS if n.folha], lambda c: [("Mentzer", f1(_mentzer(c)))])

for _a, _nid, _f in [(HIPOXEMIA, "aa", _c_grad), (HIPOCALCEMIA, "corr", _c_ca_corr), (LRA, "fena", _c_fena),
                     (LRA, "feur", _c_feur), (ANEMIAS, "mentzer", _c_mentzer)]:
    _a.nos[_nid].calc = _f
for _a in (HIPOXEMIA, HIPERCALCEMIA, HIPOCALCEMIA, LRA, ANEMIAS):
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None

ARVORES += [HIPOXEMIA, HIPERCALCEMIA, HIPOCALCEMIA, LRA, ANEMIAS]
POR_ID.update({a.id: a for a in ARVORES})

from .fluxo_asma import ASMA  # noqa: E402  (importa daqui No/Folha/Arvore, já definidos)

ARVORES += ASMA
POR_ID.update({a.id: a for a in ASMA})

from .fluxo_uti import UTI  # noqa: E402
from .fluxo_uti_treino import UTI_TREINO  # noqa: E402
from .fluxo_espiro import ESPIRO  # noqa: E402

ARVORES += UTI + UTI_TREINO + ESPIRO
POR_ID.update({a.id: a for a in UTI + UTI_TREINO + ESPIRO})







# ================================================================== mini-aulas: o porquê de cada passo
# Aparecem na 1ª vez que o jogador chega à caixa (níveis 1–2) e a qualquer momento no botão "?".

AULAS = {
    "acidobase": {
        "ph": "Comece SEMPRE pelo pH: ele diz para que lado o sangue foi. Só depois se procura quem o empurrou. "
              "Acidemia é pH abaixo de 7,35; alcalemia, acima de 7,45.",
        "prim_acid": "O distúrbio primário é o que explica a direção do pH. Na acidemia, HCO₃⁻ baixo aponta causa "
                     "metabólica e PaCO₂ alta aponta causa respiratória. Se os dois puxam para baixo, há dois distúrbios.",
        "winter": "Toda acidose metabólica faz o pulmão hiperventilar para baixar o CO₂. A fórmula de Winter prevê quanto: "
                  "1,5 × HCO₃⁻ + 8, com folga de 2. Fora da faixa existe um segundo distúrbio, respiratório.",
        "ag": "O ânion gap pergunta se entrou um ácido com ânion próprio (lactato, cetona). Ele é Na⁺ − (Cl⁻ + HCO₃⁻) e "
              "precisa ser corrigido pela albumina: some 2,5 para cada 1 g/dL abaixo de 4. Albumina baixa esconde AG alto.",
        "dd": "Numa acidose de AG alto pura, cada ácido que entra gasta um bicarbonato e sobe o gap em um. Se o bicarbonato "
              "caiu MAIS que o gap subiu, também se perdeu bicarbonato; se caiu MENOS, há alcalose junto.",
        "causa": "Com AG alto, falta saber qual ácido entrou. Olhe primeiro lactato e cetonas, os mais comuns. Se estão "
                 "normais, gap osmolar alto aponta álcool tóxico, e ureia muito alta aponta uremia.",
        "agu": "Na acidose de AG normal, o bicarbonato foi perdido pelo intestino ou pelo rim. O AG urinário estima o "
               "amônio na urina: negativo mostra o rim excretando ácido bem, logo a perda é intestinal.",
        "k_atr": "Se a culpa é do rim, o potássio separa os tipos de acidose tubular: alto aponta falta de aldosterona "
                 "(tipo 4); baixo aponta os tipos 1 e 2.",
        "ph_u": "Entre os tipos 1 e 2, pergunte se o rim consegue acidificar a urina. No tipo 1 o coletor não secreta "
                "hidrogênio, e a urina fica acima de 5,5 mesmo em plena acidemia.",
        "resp_acid": "Na acidose respiratória, o rim compensa guardando bicarbonato, mas leva dias. Por isso o HCO₃⁻ sobe "
                     "pouco na aguda (1 por 10 de PaCO₂) e muito mais na crônica (3,5 por 10).",
        "prim_alc": "Na alcalemia, HCO₃⁻ alto aponta causa metabólica e PaCO₂ baixa aponta causa respiratória. Se os dois "
                    "puxam para cima, são dois distúrbios ao mesmo tempo.",
        "comp_alc": "Na alcalose metabólica, o pulmão hipoventila para segurar CO₂: PaCO₂ esperada = 0,7 × HCO₃⁻ + 21, com "
                    "folga de 2. Ela raramente passa de 55, porque a hipoxemia freia a hipoventilação.",
        "cl_u": "Toda alcalose metabólica precisa de algo que a MANTENHA. Cloro urinário baixo mostra o rim segurando cloro "
                "e volume: a alcalose cede com soro. Cloro alto indica causa que o soro não resolve.",
        "pa": "Se o soro não resolve, a pressão separa as causas: hipertensão aponta excesso de mineralocorticoide; "
              "pressão normal aponta diurético, Bartter ou Gitelman.",
        "resp_alc": "Na alcalose respiratória, o rim compensa eliminando bicarbonato: na aguda o HCO₃⁻ cai 2 por 10 de "
                    "PaCO₂; na crônica, 4 a 5 por 10.",
        "normais": "pH normal não garante gasometria normal. Com HCO₃⁻ e PaCO₂ alterados e pH normal, são dois distúrbios "
                   "opostos se anulando — a compensação sozinha nunca normaliza o pH.",
    },
    "hiponatremia": {
        "osm": "Antes de tratar, confirme que a hiponatremia é hipotônica. Osmolalidade normal sugere erro de dosagem "
               "(pseudo); alta sugere glicose ou manitol puxando água para fora das células.",
        "osm_u": "A osmolalidade urinária mostra se o ADH está agindo. Urina diluída ao máximo (até 100) significa que o "
                 "problema é entrar água demais, e não ADH demais.",
        "vol": "Com o ADH agindo, o exame de volume organiza as causas em três grupos: desidratado, normal ou com edema. "
               "Cada grupo tem causas e tratamentos diferentes.",
        "na_u_hipo": "No desidratado, o sódio urinário diz por onde o sódio saiu: rim poupando (≤ 30) = perda fora do rim; "
                     "acima de 30, o próprio rim está perdendo (diurético, Addison).",
        "eu": "No euvolêmico, SIADH é diagnóstico de EXCLUSÃO. Antes, afaste hipotireoidismo e falta de cortisol, que "
              "também elevam o ADH.",
        "na_u_hiper": "Com edema, o sódio urinário separa quem retém sódio com avidez (insuficiência cardíaca, cirrose, "
                      "nefrótica) de quem tem o rim doente.",
    },
    "hipernatremia": {
        "osm_u": "Na hipernatremia, pergunte se o rim está concentrando a urina como deveria. Urina muito concentrada = rim "
                 "bom e água perdida por fora; urina diluída = diabetes insípido.",
        "ddavp": "A desmopressina separa os dois diabetes insípidos: se a urina concentra, faltava hormônio (central); se "
                 "não concentra, o rim não responde (nefrogênico).",
    },
    "hipocalemia": {
        "redist": "Primeiro veja se o potássio só ENTROU nas células, sem perda real (insulina, salbutamol, tireotoxicose). "
                  "Nesses casos a reposição precisa de cuidado por causa do rebote.",
        "k_u": "Havendo perda real, o potássio urinário diz quem perdeu: abaixo de 20 o rim está poupando, então a perda "
               "foi fora dele.",
        "hk_extra_ab": "Na perda extrarrenal, a diarreia leva bicarbonato junto e causa acidose; sem acidose, pense em "
                       "baixa ingestão ou suor.",
        "hk_renal_ab": "Na perda renal, o ácido-base divide o caminho: acidose sugere acidose tubular ou cetoacidose; "
                       "alcalose leva à pergunta da pressão.",
        "hk_pa": "Com alcalose e perda renal, hipertensão aponta excesso de mineralocorticoide; pressão normal aponta "
                 "vômito, diurético ou tubulopatia.",
        "hk_renina": "Renina e aldosterona localizam o excesso: aldosterona alta com renina baixa = primário; as duas altas "
                     "= secundário; as duas baixas = outro mineralocorticoide (Cushing, Liddle, alcaçuz).",
        "hk_cl_u": "No normotenso com alcalose, o cloro urinário separa o vômito (cloro baixo) do diurético e das "
                   "tubulopatias (cloro alto).",
    },
    "hipercalemia": {
        "pseudo": "Antes de tratar, pergunte se o potássio é real: hemólise na coleta e excesso de plaquetas ou leucócitos "
                  "soltam potássio no tubo.",
        "grav": "A gravidade decide se entra cálcio: eletrocardiograma alterado ou K⁺ de 6,5 ou mais pedem proteção do "
                "coração imediata, antes de baixar o potássio.",
        "causa": "Depois de proteger o coração, ache o mecanismo: o potássio saiu das células, entrou por lise, ou o rim "
                 "não excreta (sozinho ou por remédio).",
    },
    "hipoxemia": {
        "aa": "O gradiente A-a compara o O₂ que chega ao alvéolo (PAO₂) com o que chega ao sangue (PaO₂). Normal = o pulmão "
              "troca bem e falta O₂ no alvéolo; aumentado = o problema é a troca no pulmão.",
        "aa_normal": "Com gradiente normal, só há duas razões para o alvéolo ter pouco O₂: o ar tem pouco oxigênio "
                     "(altitude) ou o ar não está sendo renovado (hipoventilação, com PaCO₂ alta).",
        "o2": "Com gradiente aumentado, o oxigênio a 100% separa os mecanismos: no shunt o sangue passa por alvéolos sem ar "
              "e quase não melhora; no V/Q e na difusão melhora bem.",
        "vq": "Entre V/Q e difusão, a DLCO e o exercício decidem: membrana espessada (difusão) reduz a DLCO e dessatura no "
              "esforço, porque o sangue passa mais rápido.",
    },
    "hipercalcemia": {
        "pth": "O PTH é o primeiro exame: com cálcio alto ele DEVERIA estar suprimido. Se não está, a paratireoide é a "
               "culpada; se está, o cálcio vem de outra fonte.",
        "calciuria": "Com PTH não suprimido, o cálcio urinário separa o hiperparatireoidismo primário (calciúria normal ou "
                     "alta) da hipercalcemia hipocalciúrica familiar (calciúria muito baixa, não se opera).",
        "pthrp": "Com PTH suprimido, pense em câncer: muitos tumores produzem PTHrP, um peptídeo que imita o PTH.",
        "vitd": "Sem PTH nem PTHrP, olhe a vitamina D: 1,25 alta = granuloma ou linfoma produzindo; 25 alta = suplemento "
                "demais; as duas normais = osso sendo destruído (metástase, mieloma).",
    },
    "hipocalcemia": {
        "corr": "O cálcio total cai quando a albumina cai, sem mudar o cálcio que importa (iônico). Corrija: some 0,8 para "
                "cada 1 g/dL de albumina abaixo de 4.",
        "mg": "Antes de pensar em PTH, olhe o magnésio: sem magnésio a paratireoide não secreta PTH e o PTH não age. "
              "O cálcio só corrige depois de repor o magnésio.",
        "pth": "Com magnésio normal, o PTH diz se a glândula falhou (baixo, hipoparatireoidismo) ou está reagindo (alto, "
               "o problema está em outro lugar).",
        "fosforo": "Com PTH alto, o fósforo separa as causas: o PTH joga fósforo na urina, então fósforo baixo = falta de "
                   "vitamina D; fósforo alto = rim falhando ou resistência ao PTH.",
        "renal_ho": "Com PTH e fósforo altos, a função renal decide: doença renal crônica retém fósforo e não ativa a "
                    "vitamina D; rim normal sugere resistência ao PTH.",
    },
    "lra": {
        "pos": "Na lesão renal aguda, exclua obstrução PRIMEIRO: é a causa mais fácil de reverter e o ultrassom resolve "
               "em minutos.",
        "diur": "Antes de calcular a FENa, pergunte pelo diurético: ele faz o rim perder sódio de propósito e falseia a "
                "FENa. Nesse caso, use a FEureia.",
        "fena": "A FENa mostra se o túbulo funciona: rim bom com pouco fluxo segura sódio (FENa < 1%, pré-renal); túbulo "
                "lesado perde sódio (> 2%, intrínseca).",
        "feur": "Com diurético, a ureia substitui o sódio: FEureia abaixo de 35% indica pré-renal mesmo com furosemida.",
        "sed": "Na lesão intrínseca, o sedimento conta onde o rim foi atingido: túbulo (cilindros granulosos), glomérulo "
               "(hemácias dismórficas) ou interstício (leucócitos e eosinófilos).",
    },
    "anemias": {
        "vcm": "Toda anemia começa pelo tamanho da hemácia (VCM): pequena, normal ou grande. Cada tamanho tem uma lista "
               "curta de causas.",
        "ferr": "Na microcítica, a ferritina mede o estoque de ferro: abaixo de 30 é deficiência de ferro, a causa mais "
                "comum de anemia no mundo.",
        "mentzer": "Com ferro guardado, talassemia e doença crônica se parecem. O índice de Mentzer separa: na talassemia "
                   "a medula faz MUITAS hemácias pequenas (índice < 13).",
        "retic": "Na normocítica, os reticulócitos mostram se a medula responde: altos = sangue perdido ou destruído; "
                 "baixos = a medula não produz.",
        "hemolise": "Com medula respondendo, pergunte se há destruição: LDH e bilirrubina indireta altas com haptoglobina "
                    "baixa indicam hemólise; sem isso, pense em sangramento.",
        "coombs": "Na hemólise, o Coombs direto separa anticorpo (positivo, autoimune) de quebra mecânica (negativo com "
                  "esquizócitos: PTT, SHU, CIVD).",
        "b12": "Na macrocítica, dose B12 e folato: são as carências que dão anemia megaloblástica. Sem carência, pense em "
               "álcool, fígado, tireoide, mielodisplasia ou drogas.",
    },
}
for _a in ARVORES:
    for _nid, _txt in AULAS.get(_a.id, {}).items():
        _a.nos[_nid].aula = _txt
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "aula"):
            _n.aula = _n.pergunta


def laudo(arv, caminho, folha):
    """O diagnóstico do caso em uma frase, montado pelo caminho (como se escreve num laudo)."""
    if getattr(arv, "plano", False):    # checklist (FAST HUG): o laudo é o plano do dia, uma conduta por letra
        condutas = [arv.nos[nid].opcoes[i][3] for nid, i in caminho if arv.nos[nid].opcoes[i][3]]
        return "Plano do dia: " + "; ".join(condutas + [folha.diagnostico[0].lower() + folha.diagnostico[1:]]) + "."
    partes = []
    for nid, i in caminho:
        no = arv.nos[nid]
        if nid in ("winter", "comp_alc") and i == 0:
            partes.append("compensação respiratória adequada")
        if no.opcoes[i][3]:
            partes.append(no.opcoes[i][3])
    txt = folha.diagnostico
    if partes:
        txt += ", com " + (", ".join(partes[:-1]) + " e " + partes[-1] if len(partes) > 1 else partes[0])
    return txt + "."
