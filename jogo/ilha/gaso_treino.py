"""Modo Treino da gasometria: casos gerados na hora, infinitos.

Cada caso nasce de um cenário (ex.: acidose de AG alto + alcalose respiratória), mas o
gabarito NÃO vem do cenário: vem de `analisar()`, que aplica às cifras exatamente as
fórmulas das aulas (Winter, 0,7×HCO₃⁻+21, 1/3,5 e 2/4–5 por 10 mmHg, AG corrigido,
Δ/Δ). Se o cenário e a análise discordarem (arredondamento na fronteira), o caso é
descartado e sorteado de novo — assim o comentário e o gabarito são sempre coerentes
com as cifras mostradas.
"""
import math
import random

MATERIA = "Gasometria"
PREFIXO = "gaso-treino"           # chaves de progresso do Treino (iguais às do PC)

HABILIDADES = {
    "primario": ("Distúrbio primário", "Ler pH, PaCO₂ e HCO₃⁻ e dizer quem começou"),
    "compensacao": ("Compensação", "Adequada? Aguda ou crônica? Tem segundo distúrbio?"),
    "esperado": ("Valor esperado (fórmulas)", "Winter, alcalose metabólica e regras respiratórias"),
    "ag": ("Ânion gap corrigido", "AG = Na⁺ − (Cl⁻ + HCO₃⁻) + 2,5 × (4 − albumina)"),
    "deltadelta": ("Delta-delta", "Acidose de AG alto pura, + hiperclorêmica ou + alcalose"),
    "ph": ("pH pela fórmula do H⁺", "[H⁺] = 24 × PaCO₂ / HCO₃⁻ — confere a coerência da gasometria"),
    "completa": ("Interpretação completa", "Todos os distúrbios presentes, do início ao fim"),
    "aa": ("Gradiente A-a", "Hipoxemia: hipoventilação ou pulmão doente?"),
    "pf": ("Relação P/F", "PaO₂/FiO₂ e gravidade da SDRA (Berlim)"),
}

NOMES = {
    "acid_met": "acidose metabólica",
    "acid_met_ag": "acidose metabólica de AG elevado",
    "acid_met_hiper": "acidose metabólica hiperclorêmica (AG normal)",
    "alc_met": "alcalose metabólica",
    "acid_resp": "acidose respiratória",
    "acid_resp_aguda": "acidose respiratória aguda",
    "acid_resp_cronica": "acidose respiratória crônica",
    "acid_resp_transicao": "acidose respiratória crônica agudizada",
    "alc_resp": "alcalose respiratória",
    "alc_resp_aguda": "alcalose respiratória aguda",
    "alc_resp_cronica": "alcalose respiratória crônica",
}
ORDEM = list(NOMES)


def fmt(x, casas=0):
    s = f"{x:.{casas}f}"
    return s.replace(".", ",")


def _n(x):
    return fmt(x, 0 if abs(x - round(x)) < 1e-9 else 1)


def ph_de(P, H):
    return 6.1 + math.log10(H / (0.03 * P))


# ---------------------------------------------------------------- análise

def analisar(pH, P, H, Na, Cl, alb):
    """Aplica o roteiro das aulas. Devolve {rotulos: set, passos: [str], primario, comp, esperado}."""
    passos, rot = [], set()
    primario = comp = None
    esperado = None            # (texto da fórmula, valor central, unidade)
    tem_ag = Na is not None and Cl is not None
    alb = 4.0 if alb is None else alb
    ag = Na - Cl - H if tem_ag else 0
    agc = ag + 2.5 * (4.0 - alb) if tem_ag else 0
    ag_alto = agc > 12
    acid_met_extra = alc_met_extra = False

    def checar_resp_acida():
        nonlocal comp, esperado
        d = P - 40
        ea, ec = 24 + 0.1 * d, 24 + 0.35 * d
        esperado = (f"aguda: 24 + 1 × {fmt(d / 10, 1)} = {fmt(ea, 1)}; crônica: 24 + 3,5 × {fmt(d / 10, 1)} = {fmt(ec, 1)}", None, "mEq/L")
        if abs(H - ea) <= 2:
            comp = "aguda"
            rot.add("acid_resp_aguda")
        elif abs(H - ec) <= 2:
            comp = "cronica"
            rot.add("acid_resp_cronica")
        elif ea + 2 < H < ec - 2:
            comp = "transicao"
            rot.add("acid_resp_transicao")
        elif H < ea - 2:
            comp = "acid_met"
            rot.add("acid_resp")
            return "acid_met"
        else:
            comp = "alc_met"
            rot.add("acid_resp")
            return "alc_met"
        return None

    def checar_resp_alc():
        nonlocal comp, esperado
        d = 40 - P
        ea = 24 - 0.2 * d
        c_hi, c_lo = 24 - 0.4 * d, 24 - 0.5 * d
        esperado = (f"aguda: 24 − 2 × {fmt(d / 10, 1)} = {fmt(ea, 1)}; crônica: 24 − 4 a 5 × {fmt(d / 10, 1)} = "
                    f"{fmt(c_lo, 1)} a {fmt(c_hi, 1)}", None, "mEq/L")
        if abs(H - ea) <= 1.5:
            comp = "aguda"
            rot.add("alc_resp_aguda")
        elif c_lo - 1.5 <= H <= c_hi + 1.5:
            comp = "cronica"
            rot.add("alc_resp_cronica")
        elif H < c_lo - 1.5:
            comp = "acid_met"
            rot.add("alc_resp")
            return "acid_met"
        elif H > ea + 1.5:
            comp = "alc_met"
            rot.add("alc_resp")
            return "alc_met"
        else:
            comp = "transicao"
            rot.add("alc_resp")
        return None

    # 1) pH
    if pH < 7.35:
        passos.append(f"1) pH {fmt(pH, 2)} < 7,35 → ACIDEMIA.")
    elif pH > 7.45:
        passos.append(f"1) pH {fmt(pH, 2)} > 7,45 → ALCALEMIA.")
    else:
        passos.append(f"1) pH {fmt(pH, 2)} na faixa normal: ou é normal, ou há distúrbios que se anulam — olhe PaCO₂, HCO₃⁻ e AG.")

    # 2) e 3) primário e compensação
    if pH < 7.35:
        if H < 22 and P > 45:
            primario = "mista"
            passos.append(f"2) HCO₃⁻ {_n(H)} (↓) E PaCO₂ {_n(P)} (↑): os dois acidificam → acidose MISTA (metabólica + respiratória).")
            acid_met_extra = True
            rot.add("acid_resp")
        elif H < 22:
            primario = "acid_met"
            w = 1.5 * H + 8
            esperado = (f"Winter: 1,5 × {_n(H)} + 8 = {fmt(w, 1)} (±2)", w, "mmHg")
            passos.append(f"2) HCO₃⁻ {_n(H)} (↓) explica a acidemia → ACIDOSE METABÓLICA primária.")
            if abs(P - w) <= 2:
                comp = "adequada"
                passos.append(f"3) {esperado[0]}. PaCO₂ {_n(P)} dentro → compensação respiratória adequada.")
            elif P > w + 2:
                comp = "acid_resp"
                rot.add("acid_resp")
                passos.append(f"3) {esperado[0]}. PaCO₂ {_n(P)} ACIMA → acidose respiratória associada (não consegue hiperventilar).")
            else:
                comp = "alc_resp"
                rot.add("alc_resp")
                passos.append(f"3) {esperado[0]}. PaCO₂ {_n(P)} ABAIXO → alcalose respiratória associada.")
            acid_met_extra = True
        else:
            primario = "acid_resp"
            passos.append(f"2) PaCO₂ {_n(P)} (↑) explica a acidemia → ACIDOSE RESPIRATÓRIA primária.")
            extra = checar_resp_acida()
            txt = {"aguda": "dentro da aguda → acidose respiratória AGUDA",
                   "cronica": "dentro da crônica → acidose respiratória CRÔNICA (rim já compensou)",
                   "transicao": "entre aguda e crônica → crônica agudizada (ou em transição)",
                   "acid_met": "ABAIXO até da aguda → acidose metabólica associada",
                   "alc_met": "ACIMA da crônica → alcalose metabólica associada"}[comp]
            passos.append(f"3) HCO₃⁻ esperado — {esperado[0]}. Medido {_n(H)}: {txt}.")
            acid_met_extra = extra == "acid_met"
            alc_met_extra = extra == "alc_met"
    elif pH > 7.45:
        if H > 26 and P < 35:
            primario = "mista"
            passos.append(f"2) HCO₃⁻ {_n(H)} (↑) E PaCO₂ {_n(P)} (↓): os dois alcalinizam → alcalose MISTA (metabólica + respiratória).")
            alc_met_extra = True
            rot.add("alc_resp")
        elif H > 26:
            primario = "alc_met"
            e = 0.7 * H + 21
            esperado = (f"0,7 × {_n(H)} + 21 = {fmt(e, 1)} (±2)", e, "mmHg")
            passos.append(f"2) HCO₃⁻ {_n(H)} (↑) explica a alcalemia → ALCALOSE METABÓLICA primária.")
            if abs(P - e) <= 2:
                comp = "adequada"
                passos.append(f"3) PaCO₂ esperada {esperado[0]}. PaCO₂ {_n(P)} dentro → compensação adequada.")
            elif P > e + 2:
                comp = "acid_resp"
                rot.add("acid_resp")
                passos.append(f"3) PaCO₂ esperada {esperado[0]}. PaCO₂ {_n(P)} ACIMA → acidose respiratória associada.")
            else:
                comp = "alc_resp"
                rot.add("alc_resp")
                passos.append(f"3) PaCO₂ esperada {esperado[0]}. PaCO₂ {_n(P)} ABAIXO → alcalose respiratória associada.")
            alc_met_extra = True
        else:
            primario = "alc_resp"
            passos.append(f"2) PaCO₂ {_n(P)} (↓) explica a alcalemia → ALCALOSE RESPIRATÓRIA primária.")
            extra = checar_resp_alc()
            txt = {"aguda": "dentro da aguda → alcalose respiratória AGUDA",
                   "cronica": "dentro da crônica → alcalose respiratória CRÔNICA",
                   "transicao": "entre aguda e crônica → em transição",
                   "acid_met": "ABAIXO da crônica → acidose metabólica associada",
                   "alc_met": "ACIMA da aguda → alcalose metabólica associada"}[comp]
            passos.append(f"3) HCO₃⁻ esperado — {esperado[0]}. Medido {_n(H)}: {txt}.")
            acid_met_extra = extra == "acid_met"
            alc_met_extra = extra == "alc_met"
    else:
        primario = "normal"
        if H < 22 and P < 35:
            passos.append(f"2) HCO₃⁻ {_n(H)} (↓) e PaCO₂ {_n(P)} (↓) com pH normal: acidose metabólica + alcalose respiratória que se anulam.")
            acid_met_extra = True
            rot.add("alc_resp")
            primario = "mista"
        elif H > 26 and P > 45:
            passos.append(f"2) HCO₃⁻ {_n(H)} (↑) e PaCO₂ {_n(P)} (↑) com pH normal: alcalose metabólica + acidose respiratória que se anulam.")
            alc_met_extra = True
            rot.add("acid_resp")
            primario = "mista"
        else:
            passos.append(f"2) PaCO₂ {_n(P)} e HCO₃⁻ {_n(H)} sem desvio que explique distúrbio isolado.")

    # 4) ânion gap
    if not tem_ag:
        passos.append("4) Sem Na⁺ e Cl⁻ juntos no enunciado: ânion gap não calculável.")
        if acid_met_extra:
            rot.add("acid_met")
        if alc_met_extra:
            rot.add("alc_met")
        passos.append("Conclusão: " + (" + ".join(NOMES[r] for r in ORDEM if r in rot) or "sem distúrbio") + ".")
        hplus = 24 * P / H
        passos.append(f"Coerência: [H⁺] = 24 × {_n(P)} / {_n(H)} = {fmt(hplus)} nEq/L → pH ≈ {fmt(9 - math.log10(hplus), 2)}.")
        return {"rotulos": rot, "passos": passos, "primario": primario, "comp": comp, "esperado": esperado,
                "ag": None, "agc": None, "dd": None}
    linha_ag = f"4) AG = {_n(Na)} − ({_n(Cl)} + {_n(H)}) = {_n(ag)}"
    if alb < 4.0:
        linha_ag += f"; corrigido pela albumina {fmt(alb, 1)}: {_n(ag)} + 2,5 × {fmt(4 - alb, 1)} = {fmt(agc, 1)}"
    dd = None
    if ag_alto:
        rot.add("acid_met_ag")
        dd = (agc - 12) / max(0.5, 24 - H)
        linha_ag += " → ELEVADO: acidose metabólica de AG alto."
        passos.append(linha_ag)
        corr = H + (agc - 12)
        if dd < 1:
            rot.add("acid_met_hiper")
            dtxt = "< 1 → o HCO₃⁻ caiu mais que o AG subiu: há TAMBÉM acidose hiperclorêmica"
        elif dd > 2:
            rot.add("alc_met")
            dtxt = "> 2 → o HCO₃⁻ está alto demais para esse AG: há TAMBÉM alcalose metabólica"
        else:
            dtxt = "entre 1 e 2 → acidose de AG alto pura"
        if H >= 24:
            passos.append(f"5) Δ/Δ: o HCO₃⁻ ({_n(H)}) nem caiu, com AG {fmt(agc, 1)} — HCO₃⁻ corrigido = {_n(H)} + {fmt(agc - 12, 1)} = "
                          f"{fmt(corr, 1)} (> 28) → alcalose metabólica associada.")
            rot.add("alc_met")
            dd = 99.0
        else:
            passos.append(f"5) Δ/Δ = ({fmt(agc, 1)} − 12) / (24 − {_n(H)}) = {fmt(dd, 1)} {dtxt}.")
    else:
        passos.append(linha_ag + " → normal.")
        if acid_met_extra:
            rot.add("acid_met_hiper")
    if alc_met_extra:
        rot.add("alc_met")
    if rot & {"acid_met_ag", "acid_met_hiper", "alc_met"}:
        # com distúrbio metabólico junto, "aguda/crônica" do respiratório perde o sentido
        for base in ("acid_resp", "alc_resp"):
            for suf in ("_aguda", "_cronica", "_transicao"):
                if base + suf in rot:
                    rot.discard(base + suf)
                    rot.add(base)
    if not rot:
        passos.append("Conclusão: gasometria normal.")
    else:
        passos.append("Conclusão: " + " + ".join(NOMES[r] for r in ORDEM if r in rot) + ".")
    hplus = 24 * P / H
    passos.append(f"Coerência: [H⁺] = 24 × {_n(P)} / {_n(H)} = {fmt(hplus)} nEq/L → pH ≈ {fmt(9 - math.log10(hplus), 2)}.")
    return {"rotulos": rot, "passos": passos, "primario": primario, "comp": comp, "esperado": esperado,
            "ag": ag, "agc": agc, "dd": dd}


# ---------------------------------------------------------------- cenários

_PISTAS = {
    "cad": ["Jovem com DM1, poliúria, vômitos e respiração de Kussmaul; glicemia {g} mg/dL, cetonemia positiva.",
            "Adolescente com dor abdominal e hálito cetônico; glicemia capilar {g} mg/dL."],
    "lactato": ["Choque séptico de foco urinário em noradrenalina; lactato {l} mmol/L.",
                "Isquemia mesentérica: dor desproporcional ao exame; lactato {l} mmol/L."],
    "uremia": ["DRC estágio 5 sem diálise, náuseas e prurido; ureia 260 mg/dL."],
    "metanol": ["Ingeriu 'cachaça' adulterada, agora com visão turva; gap osmolar 30."],
    "diarreia": ["Diarreia aquosa volumosa há 3 dias, sem vômitos.",
                 "Gastroenterite com 15 evacuações líquidas por dia."],
    "atr": ["Mulher com síndrome de Sjögren, fraqueza e nefrocalcinose; pH urinário 6,8."],
    "sf": ["Pós-operatório que recebeu 8 litros de SF 0,9% nas últimas 24 h."],
    "vomitos": ["Vômitos incoercíveis há 4 dias por estenose pilórica.",
                "Drenagem alta por sonda nasogástrica há 5 dias, sem reposição de cloreto."],
    "diuretico": ["Insuficiência cardíaca em furosemida em dose alta, com hipocalemia."],
    "opioide": ["Encontrado sonolento após overdose de opioide; FR 6 irpm, pupilas mióticas.",
                "Pós-operatório com bomba de morfina, rebaixado e bradipneico."],
    "asma": ["Crise de asma grave há 3 h, agora sonolento e com tórax silencioso."],
    "dpoc": ["DPOC GOLD 4, tabagista, em consulta ambulatorial de rotina, estável.",
             "Obeso grau III com hipersonolência diurna (síndrome de obesidade-hipoventilação), estável."],
    "dpoc_ag": ["DPOC retentor conhecido com exacerbação há 1 dia: mais dispneia e escarro purulento."],
    "ansiedade": ["Crise de pânico com parestesias periorais e mãos em 'garra'.",
                  "Dor intensa por cólica nefrética, taquipneico."],
    "tep": ["Dispneia súbita e dor pleurítica no 5º dia pós-artroplastia de quadril."],
    "cronica_alc": ["Cirrose Child C, estável, sem sangramento.",
                    "Morador de La Paz (3.600 m) há anos, assintomático."],
    "salicilato": ["Ingeriu um frasco de AAS há 6 h; zumbido e náuseas."],
    "sepse_resp": ["Sepse grave no início, febril e taquipneico (FR 32)."],
    "cad_vomito": ["DM1 com cetoacidose e vômitos repetidos há 2 dias; glicemia {g} mg/dL."],
    "cad_sf": ["CAD em tratamento há 10 h com SF 0,9% e insulina; glicemia agora {g} mg/dL."],
    "cad_diarreia": ["DM1 com gastroenterite (diarreia profusa) que desencadeou cetoacidose; glicemia {g} mg/dL."],
    "choque_dpoc": ["Choque séptico em DPOC grave, exausto, usando musculatura acessória."],
    "cirrose_vomito": ["Cirrótico com vômitos há 3 dias."],
    "dpoc_diur": ["DPOC retentor crônico que começou furosemida por edema."],
    "neuromusc": ["Miastenia em crise, com fraqueza progressiva e capacidade vital caindo."],
}

# cenário → (rótulos esperados, pistas, gerador)
def _gera_acid_met(rng, H, tipo, dd=None, alb=None, Pdelta=0):
    w = 1.5 * H + 8
    P = round(w + Pdelta + rng.uniform(-1, 1))
    alb = alb if alb is not None else (4.0 if rng.random() < 0.6 else round(rng.uniform(1.8, 3.4), 1))
    if tipo == "hiper":
        agc = rng.uniform(8, 11.5)
    else:
        agc = 12 + dd * (24 - H)
    return P, H, alb, agc


def _cenario(rng, nome):
    """Devolve (rotulos_esperados, chave_pista, P, H, alb, agc)."""
    if nome == "acid_met_ag":
        H = rng.randint(6, 17)
        P, H, alb, agc = _gera_acid_met(rng, H, "ag", rng.uniform(1.15, 1.8))
        return {"acid_met_ag"}, rng.choice(["cad", "lactato", "uremia", "metanol"]), P, H, alb, agc
    if nome == "acid_met_hiper":
        H = rng.randint(9, 18)
        P, H, alb, agc = _gera_acid_met(rng, H, "hiper")
        return {"acid_met_hiper"}, rng.choice(["diarreia", "atr", "sf"]), P, H, alb, agc
    if nome == "alc_met":
        H = rng.randint(31, 44)
        P = round(0.7 * H + 21 + rng.uniform(-1, 1))
        return {"alc_met"}, rng.choice(["vomitos", "diuretico"]), P, H, 4.0, rng.uniform(9, 11.5)
    if nome == "acid_resp_aguda":
        P = rng.randint(62, 85)
        H = round(24 + 0.1 * (P - 40) + rng.uniform(-1, 1))
        return {"acid_resp_aguda"}, rng.choice(["opioide", "asma", "neuromusc"]), P, H, 4.0, rng.uniform(9, 11.5)
    if nome == "acid_resp_cronica":
        P = rng.randint(60, 78)
        H = round(24 + 0.35 * (P - 40) + rng.uniform(-1, 1))
        return {"acid_resp_cronica"}, "dpoc", P, H, 4.0, rng.uniform(9, 11.5)
    if nome == "acid_resp_transicao":
        P = rng.randint(70, 85)
        d = P - 40
        H = round(rng.uniform(24 + 0.1 * d + 2.6, 24 + 0.35 * d - 2.6))
        return {"acid_resp_transicao"}, "dpoc_ag", P, H, 4.0, rng.uniform(9, 11.5)
    if nome == "alc_resp_aguda":
        P = rng.randint(18, 24)
        H = round(24 - 0.2 * (40 - P) + rng.uniform(-0.6, 0.6))
        return {"alc_resp_aguda"}, rng.choice(["ansiedade", "tep"]), P, H, 4.0, rng.uniform(9, 11.5)
    if nome == "alc_resp_cronica":
        P = rng.randint(17, 24)
        d = 40 - P
        H = round(rng.uniform(24 - 0.5 * d, 24 - 0.4 * d))
        return {"alc_resp_cronica"}, "cronica_alc", P, H, round(rng.uniform(2.8, 4.0), 1), rng.uniform(8, 10)
    if nome == "acid_met_acid_resp":
        H = rng.randint(8, 17)
        P, H, alb, agc = _gera_acid_met(rng, H, "ag", rng.uniform(1.15, 1.8), Pdelta=rng.uniform(6, 16))
        return {"acid_met_ag", "acid_resp"}, "choque_dpoc", P, H, alb, agc
    if nome == "acid_met_alc_resp":
        H = rng.randint(11, 18)
        P, H, alb, agc = _gera_acid_met(rng, H, "ag", rng.uniform(1.15, 1.8), Pdelta=-rng.uniform(6, 11))
        return {"acid_met_ag", "alc_resp"}, rng.choice(["salicilato", "sepse_resp"]), max(P, 12), H, alb, agc
    if nome == "ag_alc_met":
        H = rng.randint(14, 22)
        P, H, alb, agc = _gera_acid_met(rng, H, "ag", rng.uniform(2.6, 4.5))
        return {"acid_met_ag", "alc_met"}, "cad_vomito", P, H, alb, agc
    if nome == "ag_hiper":
        H = rng.randint(6, 13)
        P, H, alb, agc = _gera_acid_met(rng, H, "ag", rng.uniform(0.3, 0.7))
        return {"acid_met_ag", "acid_met_hiper"}, rng.choice(["cad_sf", "cad_diarreia"]), P, H, alb, agc
    if nome == "alc_met_alc_resp":
        H = rng.randint(30, 38)
        P = round(0.7 * H + 21 - rng.uniform(8, 14))
        return {"alc_met", "alc_resp"}, "cirrose_vomito", P, H, round(rng.uniform(2.4, 3.4), 1), rng.uniform(8, 10)
    if nome == "alc_met_acid_resp":
        H = rng.randint(34, 42)
        P = round(0.7 * H + 21 + rng.uniform(8, 16))
        return {"alc_met", "acid_resp"}, "dpoc_diur", P, H, 4.0, rng.uniform(9, 11.5)
    raise KeyError(nome)


SIMPLES = ["acid_met_ag", "acid_met_hiper", "alc_met", "acid_resp_aguda", "acid_resp_cronica",
           "alc_resp_aguda", "alc_resp_cronica"]
MISTOS = ["acid_met_acid_resp", "acid_met_alc_resp", "ag_alc_met", "ag_hiper", "alc_met_alc_resp",
          "alc_met_acid_resp", "acid_resp_transicao"]


def gerar_caso(rng, cenarios=None):
    """Sorteia até a análise bater com o cenário. Devolve dict com cifras, pista e análise."""
    cenarios = cenarios or SIMPLES + MISTOS
    for _ in range(400):
        nome = rng.choice(cenarios)
        esperado, chave, P, H, alb, agc = _cenario(rng, nome)
        if H < 3 or P < 10:
            continue
        Na = rng.randint(133, 145)
        ag = agc - 2.5 * (4.0 - alb)
        Cl = round(Na - H - ag)
        ph = round(ph_de(P, H), 2)
        if nome in SIMPLES + ["acid_resp_transicao"] and 7.35 <= ph <= 7.45:
            continue
        a = analisar(ph, P, H, Na, Cl, alb)
        if a["rotulos"] != esperado:
            continue
        pista = rng.choice(_PISTAS[chave]).format(g=rng.randrange(350, 700, 10), l=fmt(rng.uniform(4, 11), 1))
        return {"cenario": nome, "P": P, "H": H, "Na": Na, "Cl": Cl, "alb": alb, "ph": ph,
                "pista": pista, "a": a, "PaO2": rng.randint(70, 98)}
    raise RuntimeError("gerador não convergiu")


def _cifras(c, com_eletrolitos=True):
    s = f"pH {fmt(c['ph'], 2)} · PaCO₂ {c['P']} mmHg · HCO₃⁻ {c['H']} mEq/L"
    if com_eletrolitos:
        s += f" · Na⁺ {c['Na']} · Cl⁻ {c['Cl']} · albumina {fmt(c['alb'], 1)} g/dL"
    return s


# ---------------------------------------------------------------- montagem das questões

def _montar(rng, habil, enunciado, certa, erradas, coment):
    erradas = [e for e in dict.fromkeys(erradas) if e != certa][:4]
    alts = [certa] + erradas
    rng.shuffle(alts)
    qid = f"gaso-treino:{habil}"
    return {"id": qid, "enunciado": enunciado, "alts": list(zip("ABCDE", alts)), "gab": "ABCDE"[alts.index(certa)],
            "coment": coment, "materia": MATERIA, "subtema": "",
            "assunto": "", "imgs": [], "prev": 0.5, "origem": "caso gerado", "treino": True}


def _num_alts(rng, certo, passo, fmtf, minimo=None):
    vals = {round(certo, 6)}
    cand = [certo + k * passo for k in (-3, -2, -1, 1, 2, 3)]
    rng.shuffle(cand)
    out = []
    for v in cand:
        if minimo is not None and v < minimo:
            continue
        if fmtf(v) in {fmtf(x) for x in vals}:
            continue
        vals.add(round(v, 6))
        out.append(fmtf(v))
        if len(out) == 4:
            break
    return fmtf(certo), out


def _q_primario(rng, c):
    a = c["a"]
    nomes = {"acid_met": "Acidose metabólica", "alc_met": "Alcalose metabólica", "acid_resp": "Acidose respiratória",
             "alc_resp": "Alcalose respiratória"}
    certa = nomes[a["primario"]]
    outras = [v for k, v in nomes.items() if v != certa] + ["Gasometria normal"]
    enun = f"{c['pista']}\nGasometria arterial: {_cifras(c, False)}.\nQual é o distúrbio PRIMÁRIO?"
    return _montar(rng, "primario", enun, certa, outras, "\n".join(a["passos"][:3]))


_COMP_TXT = {
    "adequada": "Compensação adequada — distúrbio simples",
    "acid_resp": "Acidose respiratória associada (PaCO₂ acima do esperado)",
    "alc_resp": "Alcalose respiratória associada (PaCO₂ abaixo do esperado)",
    "aguda": "Aguda (rim ainda não compensou)",
    "cronica": "Crônica (compensação renal completa)",
    "transicao": "Crônica agudizada / em transição",
    "acid_met": "Acidose metabólica associada (HCO₃⁻ abaixo do esperado)",
    "alc_met": "Alcalose metabólica associada (HCO₃⁻ acima do esperado)",
}


def _q_compensacao(rng, c):
    a = c["a"]
    nomes = {"acid_met": "acidose metabólica", "alc_met": "alcalose metabólica",
             "acid_resp": "acidose respiratória", "alc_resp": "alcalose respiratória"}
    if a["primario"] in ("acid_met", "alc_met"):
        chaves = ["adequada", "acid_resp", "alc_resp"]
        extra = ["Não há compensação esperada em distúrbio metabólico", "Compensação renal crônica"]
    else:
        chaves = ["aguda", "cronica", "transicao", "acid_met", "alc_met"]
        extra = []
    certa = _COMP_TXT[a["comp"]]
    outras = [_COMP_TXT[k] for k in chaves if k != a["comp"]] + extra
    enun = (f"{c['pista']}\nGasometria arterial: {_cifras(c, False)}.\nO distúrbio primário é {nomes[a['primario']]}. "
            "Como está a resposta compensatória?")
    return _montar(rng, "compensacao", enun, certa, outras, "\n".join(a["passos"][:3]))


def _q_esperado(rng, c):
    a = c["a"]
    if a["primario"] == "acid_met":
        v = 1.5 * c["H"] + 8
        enun = f"Acidose metabólica com HCO₃⁻ = {c['H']} mEq/L. Pela fórmula de Winter, a PaCO₂ esperada é:"
        coment = f"Winter: 1,5 × {c['H']} + 8 = {fmt(v, 1)} mmHg (±2). Medida no caso: {c['P']}."
        unid = " mmHg"
    elif a["primario"] == "alc_met":
        v = 0.7 * c["H"] + 21
        enun = f"Alcalose metabólica com HCO₃⁻ = {c['H']} mEq/L. A PaCO₂ esperada pela compensação é:"
        coment = f"0,7 × {c['H']} + 21 = {fmt(v, 1)} mmHg (±2). Medida no caso: {c['P']}."
        unid = " mmHg"
    elif a["primario"] == "acid_resp":
        cron = rng.random() < 0.5
        d = c["P"] - 40
        v = 24 + (0.35 if cron else 0.1) * d
        enun = f"Acidose respiratória {'CRÔNICA' if cron else 'AGUDA'} com PaCO₂ = {c['P']} mmHg. O HCO₃⁻ esperado é:"
        coment = (f"{'Crônica: +3,5' if cron else 'Aguda: +1'} para cada 10 mmHg acima de 40. "
                  f"{c['P']} − 40 = {d} → 24 + {fmt((0.35 if cron else 0.1) * d, 1)} = {fmt(v, 1)} mEq/L.")
        unid = " mEq/L"
    else:
        d = 40 - c["P"]
        v = 24 - 0.2 * d
        enun = f"Alcalose respiratória AGUDA com PaCO₂ = {c['P']} mmHg. O HCO₃⁻ esperado é:"
        coment = f"Aguda: −2 para cada 10 mmHg abaixo de 40. 40 − {c['P']} = {d} → 24 − {fmt(0.2 * d, 1)} = {fmt(v, 1)} mEq/L."
        unid = " mEq/L"
    f = lambda x: fmt(round(x)) + unid
    certa, erradas = _num_alts(rng, v, 4 if unid == " mmHg" else 3, f, minimo=8)
    return _montar(rng, "esperado", enun, certa, erradas, coment)


def _q_ag(rng, c):
    a = c["a"]
    enun = (f"Na⁺ {c['Na']} · Cl⁻ {c['Cl']} · HCO₃⁻ {c['H']} mEq/L · albumina {fmt(c['alb'], 1)} g/dL.\n"
            "Qual o ânion gap CORRIGIDO pela albumina?")
    f = lambda x: fmt(x, 1 if abs(x - round(x)) > 0.01 else 0)
    certa = f(a["agc"])
    erradas = [f(a["ag"]) if c["alb"] < 4 else f(a["ag"] + 5), f(c["Na"] - c["Cl"]), f(a["agc"] + 6),
               f(a["agc"] - 6), f(c["Na"] - c["Cl"] - c["H"] - 2.5 * (4 - c["alb"]) - 4)]
    coment = a["passos"][[p.startswith("4)") for p in a["passos"]].index(True)]
    coment += "\nAG normal ≈ 8–12. Cada 1 g/dL de albumina a menos esconde ~2,5 mEq/L de AG."
    return _montar(rng, "ag", enun, certa, erradas, coment)


def _q_deltadelta(rng, c):
    a = c["a"]
    enun = (f"{c['pista']}\nNa⁺ {c['Na']} · Cl⁻ {c['Cl']} · HCO₃⁻ {c['H']} · albumina {fmt(c['alb'], 1)}.\n"
            "Pelo delta-delta, a acidose de AG elevado é:")
    if a["dd"] < 1:
        certa = "Associada a acidose hiperclorêmica (Δ/Δ < 1)"
    elif a["dd"] > 2:
        certa = "Associada a alcalose metabólica (Δ/Δ > 2)"
    else:
        certa = "Pura (Δ/Δ entre 1 e 2)"
    outras = ["Pura (Δ/Δ entre 1 e 2)", "Associada a acidose hiperclorêmica (Δ/Δ < 1)",
              "Associada a alcalose metabólica (Δ/Δ > 2)", "Não se aplica: o AG está normal",
              "Associada a acidose respiratória (Δ/Δ > 2)"]
    idx = [i for i, p in enumerate(a["passos"]) if p.startswith("4)")][0]
    return _montar(rng, "deltadelta", enun, certa, outras, "\n".join(a["passos"][idx:idx + 2]))


def _q_ph(rng, c):
    h = 24 * c["P"] / c["H"]
    enun = f"PaCO₂ {c['P']} mmHg e HCO₃⁻ {c['H']} mEq/L. Pela fórmula [H⁺] = 24 × PaCO₂ / HCO₃⁻, o pH esperado é:"
    f = lambda x: fmt(x, 2)
    certa, erradas = _num_alts(rng, c["ph"], 0.07, f)
    coment = (f"[H⁺] = 24 × {c['P']} / {c['H']} = {fmt(h)} nEq/L. Referências: 40 → 7,40; cada 0,01 de pH ≈ 1 nEq/L perto do normal; "
              f"80 → 7,10; 20 → 7,70. Exato: pH = 9 − log[H⁺] = {fmt(9 - math.log10(h), 2)}. "
              "Se o pH impresso não bate com essa conta (±0,03), suspeite de erro de coleta ou digitação.")
    return _montar(rng, "ph", enun, certa, erradas, coment)


def _frase(rot):
    if not rot:
        return "Gasometria normal"
    t = " + ".join(NOMES[r] for r in ORDEM if r in rot)
    return t[0].upper() + t[1:]


def _q_completa(rng, c):
    a = c["a"]
    certa = _frase(a["rotulos"])
    erradas = []
    tent = 0
    while len(erradas) < 4 and tent < 200:
        tent += 1
        outro = gerar_caso(rng)["a"]["rotulos"]
        fr = _frase(outro)
        if fr != certa and fr not in erradas:
            erradas.append(fr)
    enun = f"{c['pista']}\nGasometria arterial: {_cifras(c)}.\nA interpretação completa é:"
    return _montar(rng, "completa", enun, certa, erradas, "\n".join(a["passos"]))


def _q_aa(rng):
    idade = rng.randint(20, 80)
    normal = rng.random() < 0.45
    P = rng.randint(58, 80) if normal else rng.randint(28, 48)
    fio2 = 0.21
    PA = fio2 * 713 - P / 0.8
    limite = idade / 4 + 4
    if normal:
        PaO2 = round(PA - rng.uniform(3, limite - 1))
    else:
        PaO2 = min(round(PA - rng.uniform(limite + 8, limite + 40)), rng.randint(48, 72))
    grad = PA - PaO2
    pista = rng.choice(["Encontrado sonolento após uso de benzodiazepínico e opioide", "Jovem com fraqueza muscular ascendente",
                        "Obeso mórbido sonolento, sem queixa pulmonar"] if normal else
                       ["Paciente com febre, tosse produtiva e crepitações em base direita", "Dispneia súbita no pós-operatório",
                        "Piora respiratória com sibilos difusos"])
    enun = (f"{pista}; {idade} anos, ar ambiente ao nível do mar. PaO₂ {PaO2} mmHg, PaCO₂ {P} mmHg.\n"
            "Calcule o gradiente A-a. A hipoxemia se explica por:")
    if grad <= limite:
        certa = f"Gradiente ≈ {fmt(grad)}: normal → hipoventilação pura (pulmão sadio)"
        outras = [f"Gradiente ≈ {fmt(grad + 25)}: aumentado → distúrbio V/Q ou shunt",
                  f"Gradiente ≈ {fmt(max(grad - 15, 1) + 40)}: aumentado → distúrbio de difusão",
                  f"Gradiente ≈ {fmt(grad)}: aumentado → shunt verdadeiro",
                  f"Gradiente ≈ {fmt(grad + 50)}: normal → hipoventilação pura"]
    else:
        certa = f"Gradiente ≈ {fmt(grad)}: aumentado → doença pulmonar (V/Q, shunt ou difusão)"
        outras = [f"Gradiente ≈ {fmt(max(grad - 30, 4))}: normal → hipoventilação pura",
                  f"Gradiente ≈ {fmt(grad)}: normal para a idade → hipoventilação pura",
                  f"Gradiente ≈ {fmt(grad + 30)}: normal → FiO₂ baixa",
                  f"Gradiente ≈ {fmt(grad)}: aumentado → hipoventilação pura"]
    coment = (f"PAO₂ = 0,21 × 713 − {P}/0,8 = 150 − {fmt(P / 0.8, 1)} = {fmt(PA, 1)}. Gradiente = {fmt(PA, 1)} − {PaO2} = {fmt(grad, 1)}. "
              f"Limite para {idade} anos ≈ idade/4 + 4 = {fmt(limite, 1)}. "
              + ("Normal: o alvéolo tem pouco O₂ porque o CO₂ subiu (hipoventilação). Tratar a causa da hipoventilação."
                 if grad <= limite else "Aumentado: o O₂ chega ao alvéolo mas não passa para o sangue — pulmão doente."))
    return _montar(rng, "aa", enun, certa, outras, coment)


def _q_pf(rng):
    fio2 = rng.choice([0.3, 0.4, 0.5, 0.6, 0.8, 1.0])
    pf = rng.choice([rng.uniform(60, 98), rng.uniform(105, 195), rng.uniform(205, 295), rng.uniform(310, 420)])
    PaO2 = round(pf * fio2)
    pf = PaO2 / fio2
    if pf <= 100:
        cls = "SDRA grave"
    elif pf <= 200:
        cls = "SDRA moderada"
    elif pf <= 300:
        cls = "SDRA leve"
    else:
        cls = "não preenche critério de SDRA pela oxigenação"
    enun = (f"Pneumonia grave, infiltrado bilateral, sem disfunção cardíaca, intubado com PEEP 10. FiO₂ {int(fio2 * 100)}%, "
            f"PaO₂ {PaO2} mmHg. Qual a relação P/F e a classificação de Berlim?")
    certa = f"P/F ≈ {fmt(pf)} — {cls}"
    classes = ["SDRA grave", "SDRA moderada", "SDRA leve", "não preenche critério de SDRA pela oxigenação"]
    outras = [f"P/F ≈ {fmt(pf)} — {k}" for k in classes if k != cls]
    outras += [f"P/F ≈ {fmt(PaO2 / (fio2 * 100), 1)} — {cls}", f"P/F ≈ {fmt(PaO2 * fio2)} — SDRA grave"]
    rng.shuffle(outras)
    coment = (f"P/F = {PaO2} / {fmt(fio2, 2)} = {fmt(pf)}. FiO₂ em FRAÇÃO, não em %. Berlim (PEEP ≥ 5): leve 200–300, "
              "moderada 100–200, grave ≤ 100. Normal ≈ 400–500.")
    return _montar(rng, "pf", enun, certa, outras, coment)


def questao(rng, habil):
    if habil == "aa":
        return _q_aa(rng)
    if habil == "pf":
        return _q_pf(rng)
    if habil == "primario":
        c = gerar_caso(rng, SIMPLES)
    elif habil == "compensacao":
        c = gerar_caso(rng, SIMPLES + ["acid_met_acid_resp", "acid_met_alc_resp", "alc_met_alc_resp",
                                       "alc_met_acid_resp", "acid_resp_transicao"])
        if c["a"]["primario"] not in ("acid_met", "alc_met", "acid_resp", "alc_resp") or \
                (c["a"]["primario"] in ("acid_resp", "alc_resp") and c["a"]["agc"] > 12):
            return questao(rng, habil)
    elif habil == "esperado":
        c = gerar_caso(rng, ["acid_met_ag", "acid_met_hiper", "alc_met", "acid_resp_aguda", "acid_resp_cronica", "alc_resp_aguda"])
    elif habil in ("ag", "deltadelta"):
        c = gerar_caso(rng, ["acid_met_ag", "ag_alc_met", "ag_hiper", "acid_met_alc_resp"]
                       + (["acid_met_hiper"] if habil == "ag" else []))
    else:
        c = gerar_caso(rng)
    return {"primario": _q_primario, "compensacao": _q_compensacao, "esperado": _q_esperado, "ag": _q_ag,
            "deltadelta": _q_deltadelta, "ph": _q_ph, "completa": _q_completa}[habil](rng, c)


def taxa_erro(save, habil):
    s = save.stat(f"gaso-treino:{habil}")
    if not s or s["c"] + s["e"] == 0:
        return None
    return s["e"] / (s["c"] + s["e"])


def fase(save, habil=None, n=6, rng=None):
    """n questões. Sem habilidade: mistura, pesando mais as habilidades com mais erro."""
    rng = rng or random.Random()
    if habil:
        return [questao(rng, habil) for _ in range(n)]
    hs = list(HABILIDADES)
    pesos = [1 + 3 * (taxa_erro(save, h) if taxa_erro(save, h) is not None else 0.5) for h in hs]
    return [questao(rng, rng.choices(hs, pesos)[0]) for _ in range(n)]
