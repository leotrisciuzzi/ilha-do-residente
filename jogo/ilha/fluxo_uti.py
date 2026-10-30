"""Fluxogramas da UTI: o checklist FAST HUG (Vincent, Crit Care Med 2005) e a extensão FAST HUGS BID (Vincent 2009).

Duas árvores, no mesmo molde das de gasometria (fluxo_dados): cada letra do mnemônico é uma caixa com regra
aplicada aos números do paciente. Os ramos de cada letra CONVERGEM na letra seguinte e só deixam a conduta
anotada como "achado" — no fim, o laudo é o plano do dia inteiro numa frase.

  1. FAST HUG ............. Feeding, Analgesia, Sedation, Thromboprophylaxis, Head of bed, Ulcer, Glucose
  2. FAST HUGS BID ........ Spontaneous breathing trial, Bowel, Indwelling catheters, De-escalation

Fontes das regras: ESPEN 2023 (nutrição na UTI: enteral em 48 h, adiar no choque não controlado, parenteral em
3–7 dias se a enteral é contraindicada, resíduo > 500 mL/6 h); PADIS 2018 e atualização SCCM 2025 (dor antes
de sedar, BPS > 5, sedação leve RASS −2 a 0, dexmedetomidina preferida ao propofol); ACCP/ASH (HBPM; HNF se
ClCr < 30; compressão pneumática se contraindicação); SCCM/ASHP 2024 (profilaxia de úlcera só com coagulopatia,
choque ou hepatopatia crônica; suspender quando o fator some); SCCM 2024 (insulina se glicemia ≥ 180
persistente, sem alvo intensivo); ATS/ACCP 2017 e Tobin 1991 (TRE, índice f/VT > 105); Surviving Sepsis
2021 (descalonar pela cultura, procalcitonina para suspender)."""
from .fluxo_dados import Arvore, Folha, No, f1, f2, fi

VINCENT = "Vincent · FAST HUG"

# ================================================================== 1. FAST HUG (a visita do leito)

_BPS_FACE = {1: "relaxada", 2: "sobrancelha franzida", 3: "olhos cerrados", 4: "careta"}
_BPS_MMSS = {1: "parados", 2: "pouco fletidos", 3: "fletidos, dedos também", 4: "retraídos"}
_BPS_VM = {1: "tolera", 2: "tosse, mas tolera", 3: "briga com o ventilador", 4: "impossível ventilar"}
_RASS = {3: "muito agitado", 2: "agitado", 1: "inquieto", 0: "alerta e calmo", -1: "sonolento", -2: "sedação leve",
         -3: "sedação moderada", -4: "sedação profunda", -5: "não desperta"}


def _instavel(c):
    return c["lac1"] > c["lac0"] or c["nora1"] > c["nora0"]


def _bps(c):
    return c["face"] + c["mmss"] + c["vm"]


def _alvo_rass(c):
    return (-5, -4) if c["profunda"] else (-2, 0)


def _clcr(c):
    v = (140 - c["idade"]) * c["peso"] / (72 * c["cr"])
    return v * 0.85 if c["mulher"] else v


def _coagulo(c):
    return c["plaq"] < 50 or c["inr"] > 1.5


def _fator_up(c):
    return _coagulo(c) or c["nora1"] > 0 or c["hepato"]


def _c_bps(c):
    n = _bps(c)
    err = [(n - 3, "contou cada item de 0 a 3 (no BPS o mínimo de cada um é 1)"),
           (c["face"] + c["mmss"], "esqueceu a adaptação ao ventilador"),
           (max(c["face"], c["mmss"], c["vm"]) * 3, "multiplicou o pior item por 3")]
    form = f"face {c['face']} + membros superiores {c['mmss']} + ventilador {c['vm']} = {n} (vai de 3 a 12)"
    return "Quanto soma a Behavioral Pain Scale (BPS)?", n, err, form, 0


def _c_clcr(c):
    v = _clcr(c)
    bruto = (140 - c["idade"]) * c["peso"] / (72 * c["cr"])
    err = [((140 - c["idade"]) * c["peso"] / 72, "não dividiu pela creatinina"),
           ((140 + c["idade"]) * c["peso"] / (72 * c["cr"]) * (0.85 if c["mulher"] else 1), "somou a idade em vez de subtrair")]
    err.insert(0, (bruto, "esqueceu o × 0,85 da mulher") if c["mulher"] else
               (bruto * 0.85, "aplicou o × 0,85 (é só para mulher)"))
    form = (f"(140 − {c['idade']}) × {c['peso']} ÷ (72 × {f1(c['cr'])})"
            + (" × 0,85" if c["mulher"] else "") + f" = {fi(v)} mL/min")
    return "Qual o clearance de creatinina (Cockcroft-Gault), em mL/min?", v, err, form, 0


def _dieta(c):
    if c["tgi"]:
        return 2
    if _instavel(c):
        return 1
    return 3 if (c["grv"] or 0) > 500 else 0


def _sed(c):
    if c["rass"] >= 1:
        return 2
    return 1 if c["rass"] < _alvo_rass(c)[0] else 0


def _trombo(c):
    if c["sangra"] or c["plaq"] < 50:
        return 0
    return 1 if _clcr(c) < 30 else 2


def _cab(c):
    if c["coluna"]:
        return 2
    return 0 if c["cab"] >= 30 else 1


def _up(c):
    if _fator_up(c):
        return 0
    return 2 if c["ibp"] else 1


def _glic(c):
    if min(c["g0"], c["g1"]) < 70:
        return 2
    return 1 if c["g0"] >= 180 and c["g1"] >= 180 else 0


FH_NOS = [
    No("dieta", "F · Dieta", "F de Feeding: como fica a dieta deste paciente hoje?",
       [("Enteral", "estável, TGI ok", "dor", "enteral precoce (24–48 h)"),
        ("Adiar", "choque piorando", "dor", "enteral adiada até controlar o choque"),
        ("Parenteral", "TGI contraindicado", "dor", "parenteral em 3–7 dias (TGI contraindicado)"),
        ("Procinético", "resíduo > 500 mL", "dor", "procinético (resíduo > 500 mL)")],
       _dieta,
       lambda c: (f"Noradrenalina {f2(c['nora0'])} → {f2(c['nora1'])} mcg/kg/min, lactato {f1(c['lac0'])} → {f1(c['lac1'])} em 6 h"
                  + (f"; TGI: {c['tgi']}." if c["tgi"] else
                     ". Choque piorando: sem enteral até estabilizar." if _instavel(c) else
                     f"; resíduo gástrico {c['grv']} mL/6 h." if c["grv"] else ". Estável, intestino funcionando."))),
    No("dor", "A · Analgesia", "A de Analgesia: intubado, não fala. Ele tem dor? (Behavioral Pain Scale)",
       [("Sem dor", "BPS ≤ 5", "sed", "analgesia mantida"),
        ("Com dor", "BPS > 5", "sed", "opioide para a dor (BPS > 5)")],
       lambda c: 0 if _bps(c) <= 5 else 1,
       lambda c: (f"BPS = face {c['face']} + membros {c['mmss']} + ventilador {c['vm']} = {_bps(c)}. "
                  + ("Acima de 5 é dor: analgesia primeiro (analgossedação)." if _bps(c) > 5 else "Até 5 não indica dor relevante."))),
    No("sed", "S · Sedação", "S de Sedation: o RASS está no alvo para este paciente?",
       [("No alvo", "RASS no alvo", "trombo", "sedação no alvo"),
        ("Sedado demais", "abaixo do alvo", "trombo", "reduzir a sedação e despertar diário"),
        ("Agitado", "RASS ≥ +1", "trombo", "agitação: buscar dor e delirium (CAM-ICU)")],
       _sed,
       lambda c: (f"RASS {c['rass']:+d} ({_RASS[c['rass']]}). "
                  + (f"Há indicação de sedação profunda ({c['profunda']}): alvo −4 a −5." if c["profunda"] else
                     "Sem indicação de sedação profunda: alvo −2 a 0.")).replace("+0", "0")),
    No("trombo", "T · TEV", "T de Thromboprophylaxis: qual profilaxia de TEV?",
       [("Contraindicação", "sangra / plaq < 50", "cab",
         "compressão pneumática (anticoagulante contraindicado)"),
        ("ClCr < 30", "a HBPM acumula", "cab", "HNF 5.000 UI SC 8/8–12/12 h (ClCr < 30)"),
        ("ClCr ≥ 30", "enoxaparina", "cab", "enoxaparina 40 mg SC 1×/dia")],
       _trombo,
       lambda c: (f"Sangramento: {c['sangra'] or 'não'}; plaquetas {c['plaq']} mil; ClCr {fi(_clcr(c))} mL/min. "
                  + ("Contraindicação ao anticoagulante: proteção mecânica." if _trombo(c) == 0 else
                     "Rim abaixo de 30: a enoxaparina acumula, use heparina não fracionada." if _trombo(c) == 1 else
                     "Sem contraindicação e rim acima de 30: HBPM."))),
    No("cab", "H · Cabeceira", "H de Head of bed: e a cabeceira?",
       [("Já a 30–45°", "manter", "up", "cabeceira a 30–45°"),
        ("Elevar", "abaixo de 30°", "up", "elevar a cabeceira a 30–45°"),
        ("Proclive", "coluna instável", "up", "proclive (coluna instável)")],
       _cab,
       lambda c: f"Cabeceira a {c['cab']}°; coluna {'instável' if c['coluna'] else 'sem restrição'}."),
    No("up", "U · Úlcera", "U de Ulcer: profilaxia de úlcera de estresse? (fator = coagulopatia, choque ou hepatopatia crônica)",
       [("Com fator", "coagulopatia/choque", "glic",
         "IBP em dose baixa (fator de risco)"),
        ("Sem fator", "não iniciar", "glic", "sem profilaxia de úlcera"),
        ("Suspender IBP", "sem fator, em uso", "glic", "suspender o IBP (sem fator de risco)")],
       _up,
       lambda c: (f"Plaquetas {c['plaq']} mil, INR {f1(c['inr'])}, noradrenalina {f2(c['nora1'])}, hepatopatia crônica: "
                  f"{'sim' if c['hepato'] else 'não'}. "
                  + ("Há fator de risco: profilaxia indicada." if _fator_up(c) else
                     "Nenhum fator: o IBP só traz risco (pneumonia, C. difficile)."))),
    No("glic", "G · Glicemia", "G de Glucose: as duas últimas glicemias pedem o quê?",
       [("Manter", "< 180 ou isolada", "f_fh_alvo", None),
        ("Insulina IV", "≥ 180 duas vezes", "f_fh_insulina", None),
        ("Hipoglicemia", "< 70", "f_fh_hipo", None)],
       _glic,
       lambda c: (f"Glicemias {c['g0']} → {c['g1']} mg/dL{', com insulina' if c['insulina'] else ''}. "
                  + ("Abaixo de 70 é hipoglicemia, a mais perigosa." if _glic(c) == 2 else
                     "Duas acima de 180: hiperglicemia persistente." if _glic(c) == 1 else
                     "Uma medida isolada alta não basta; e não se persegue 80–110."))),
    Folha("f_fh_alvo", "Glicemia ok", "Glicemia sem hiperglicemia persistente: manter (alvo 140–180)",
          "NICE-SUGAR: alvo intensivo (80–110) aumentou mortalidade por hipoglicemia. Glicemia de 150 na UTI está ótima."),
    Folha("f_fh_insulina", "Insulina IV", "Hiperglicemia persistente: insulina IV em protocolo, alvo 140–180",
          "Comece a insulina com glicemia ≥ 180 persistente, cheque a cada 1–2 h no início e nunca persiga a normoglicemia."),
    Folha("f_fh_hipo", "Hipoglicemia", "Hipoglicemia: glicose 50% IV, rever a insulina, glicemia de 1/1 h",
          "Na UTI a hipoglicemia é o evento mais perigoso do controle glicêmico: suspenda a insulina e procure a causa (dieta parada?)."),
]

_CTX = ["Pós-operatório de laparotomia, 3º dia de UTI, intubado.", "Pneumonia grave, 2º dia de ventilação mecânica.",
        "Choque séptico de foco urinário, intubado ontem.", "Politrauma, 4º dia de UTI, intubado."]
_TGI = [("obstrução intestinal", "Abdome distendido, sem eliminar flatos, intubado."),
        ("isquemia mesentérica", "Isquemia mesentérica operada ontem, peritoniostomia."),
        ("fístula de alto débito", "Fístula entérica de 1.500 mL/dia, intubado.")]
_SANGRA = ["hemorragia digestiva ativa", "hematoma cerebral recente", "sangrando pelo dreno"]
_PROFUNDA = ["SDRA grave com bloqueador", "hipertensão intracraniana", "estado de mal epiléptico"]


def _gerar_fh(rng, alvo):
    c = {"idade": rng.randint(25, 85), "mulher": rng.random() < 0.5, "tgi": None, "grv": None,
         "nora0": 0.0, "nora1": 0.0, "lac0": round(rng.uniform(1.0, 2.0), 1), "lac1": 0.0, "insulina": False}
    c["peso"] = rng.randint(50, 70) if c["mulher"] else rng.randint(62, 95)
    texto = rng.choice(_CTX)
    # F
    f = rng.choice([0, 0, 1, 2, 3])
    if f == 2:
        c["tgi"], texto = rng.choice(_TGI)
    if f == 1:
        c["nora0"] = round(rng.uniform(0.1, 0.3), 2)
        c["nora1"] = round(c["nora0"] + rng.uniform(0.1, 0.3), 2)
        c["lac1"] = round(c["lac0"] + rng.uniform(1.0, 3.0), 1)
    else:
        if rng.random() < 0.5:                          # em choque, mas controlado: pode a enteral
            c["nora0"] = round(rng.uniform(0.15, 0.35), 2)
            c["nora1"] = round(c["nora0"] - rng.uniform(0.05, 0.12), 2)
        c["lac1"] = round(max(0.8, c["lac0"] - rng.uniform(0.2, 0.8)), 1)
        if f == 3:
            c["grv"] = rng.randrange(550, 900, 50)
        elif f == 0 and rng.random() < 0.5:
            c["grv"] = rng.randrange(150, 450, 50)       # resíduo abaixo de 500 não para a dieta
    # A
    while True:
        c["face"], c["mmss"], c["vm"] = rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4)
        if _bps(c) != 5 or rng.random() < 0.4:           # 5 (o limite) aparece, mas não sempre
            break
    # S
    c["profunda"] = rng.choice(_PROFUNDA) if rng.random() < 0.2 else None
    if c["profunda"]:
        c["rass"] = rng.choice([-4, -5])
        if "bloqueador" in c["profunda"]:
            c["face"], c["mmss"], c["vm"] = 1, 1, 1      # paralisado: BPS sem valor, conta como sem dor
    else:
        c["rass"] = rng.choice([-2, -1, 0, -4, -5, -3, 1, 2, 3])
    # T
    c["sangra"] = rng.choice(_SANGRA) if rng.random() < 0.2 else None
    c["plaq"] = rng.choice([rng.randint(20, 45), rng.randint(90, 350), rng.randint(90, 350), rng.randint(90, 350)])
    for _ in range(200):
        c["cr"] = round(rng.choice([rng.uniform(0.6, 1.3), rng.uniform(2.0, 5.0)]), 1)
        if not 25 <= _clcr(c) <= 35:
            break
    c["inr"] = round(rng.choice([rng.uniform(0.9, 1.3), rng.uniform(0.9, 1.3), rng.uniform(1.8, 2.8)]), 1)
    # H
    c["coluna"] = rng.random() < 0.15
    c["cab"] = rng.choice([0, 10, 15, 20, 30, 35, 45]) if not c["coluna"] else rng.choice([0, 10])
    if c["coluna"]:
        texto = "Politrauma com fratura instável de coluna torácica, intubado."
    # U
    c["hepato"] = rng.random() < 0.15
    c["ibp"] = rng.random() < 0.5
    # G
    if alvo == "f_fh_hipo":
        c["insulina"] = True
        c["g0"], c["g1"] = rng.randint(90, 150), rng.randint(42, 66)
    elif alvo == "f_fh_insulina":
        c["g0"], c["g1"] = rng.randint(185, 260), rng.randint(185, 300)
    else:
        c["g0"], c["g1"] = rng.choice([(rng.randint(120, 175), rng.randint(110, 178)),
                                       (rng.randint(190, 240), rng.randint(130, 175)),      # uma alta isolada
                                       (rng.randint(80, 110), rng.randint(85, 120))])
        c["insulina"] = rng.random() < 0.3
    c["texto"] = texto
    c["mostrar"] = [("Noradrenalina", f"{f2(c['nora0'])} → {f2(c['nora1'])}" if c["nora0"] else "sem"),
                    ("Lactato (6 h)", f"{f1(c['lac0'])} → {f1(c['lac1'])}"),
                    ("Intestino", c["tgi"] or "funcionando"),
                    ("Resíduo gástrico", f"{c['grv']} mL/6 h" if c["grv"] else "sem dieta" if not c["grv"] and (c["tgi"] or _instavel(c)) else "—"),
                    ("BPS", f"face {c['face']} · MMSS {c['mmss']} · VM {c['vm']}"),
                    ("RASS", f"{c['rass']:+d} {_RASS[c['rass']]}".replace("+0", "0")),
                    ("Sed. profunda", c["profunda"] or "não"),
                    ("Idade · peso", f"{c['idade']} a · {'♀' if c['mulher'] else '♂'} · {c['peso']} kg"),
                    ("Creatinina", f"{f1(c['cr'])} mg/dL"),
                    ("Plaquetas · INR", f"{c['plaq']} mil · {f1(c['inr'])}"),
                    ("Sangramento", c["sangra"] or "não"),
                    ("Cabeceira", f"{c['cab']}°" + (" · coluna instável" if c["coluna"] else "")),
                    ("Hepatopatia · IBP", f"{'sim' if c['hepato'] else 'não'} · {'em uso' if c['ibp'] else 'sem'}"),
                    ("Glicemias", f"{c['g0']} → {c['g1']}" + (" (insulina)" if c["insulina"] else ""))]
    return c


FAST_HUG = Arvore("fasthug", "FAST HUG: a visita do leito",
                  f"{VINCENT} · dieta → dor → sedação → TEV → cabeceira → úlcera → glicemia",
                  "dieta", FH_NOS, _gerar_fh, [n.id for n in FH_NOS if n.folha],
                  lambda c: [("BPS", fi(_bps(c))), ("ClCr", f"{fi(_clcr(c))} mL/min")], grupo="uti")
FAST_HUG.plano = True
FAST_HUG.nos["dor"].calc = _c_bps
FAST_HUG.nos["trombo"].calc = _c_clcr

# ================================================================== 2. FAST HUGS BID (desmame e o resto da visita)


def _pf(c):
    return c["pao2"] / (c["fio2"] / 100)


def _apto(c):
    return _pf(c) >= 150 and c["peep"] <= 8 and c["fio2"] <= 40 and c["nora"] <= 0.1 and c["rass_ok"] and c["tosse"]


def _tobin(c):
    return c["f"] / (c["vt"] / 1000)


def _falhou(c):
    return _tobin(c) > 105 or c["fr_tre"] > 35 or c["spo2_tre"] < 90 or c["fc_tre"] > 140


def _pct_queda(c):
    return (c["pct_pico"] - c["pct"]) / c["pct_pico"] * 100


def _c_pf(c):
    v = _pf(c)
    err = [(c["pao2"] / c["fio2"], "dividiu pela FiO₂ em % (use a fração: 40% = 0,4)"),
           (c["pao2"] * c["fio2"] / 100, "multiplicou em vez de dividir"),
           (c["fio2"] / 100 / c["pao2"] * 1000, "inverteu a divisão")]
    return ("Qual a relação PaO₂/FiO₂?", v, err,
            f"{c['pao2']} ÷ {f2(c['fio2'] / 100)} = {fi(v)}", 0)


def _c_tobin(c):
    v = _tobin(c)
    err = [(c["f"] / c["vt"], "deixou o volume em mL (o índice usa litros)"),
           (c["vt"] / c["f"], "inverteu: é frequência ÷ volume"),
           (c["f"] * c["vt"] / 1000, "multiplicou em vez de dividir")]
    return ("Quanto é o índice de Tobin (f/VT)?", v, err,
            f"{c['f']} irpm ÷ {f2(c['vt'] / 1000)} L = {fi(v)}", 0)


def _c_pct(c):
    v = _pct_queda(c)
    err = [(c["pct"] / c["pct_pico"] * 100, "calculou quanto SOBROU, não quanto caiu"),
           ((c["pct_pico"] - c["pct"]) / c["pct"] * 100, "dividiu pelo valor de hoje (a base é o pico)"),
           (c["pct_pico"] - c["pct"], "usou a diferença absoluta como se fosse %")]
    return ("Quanto a procalcitonina caiu desde o pico, em %?", v, err,
            f"({f2(c['pct_pico'])} − {f2(c['pct'])}) ÷ {f2(c['pct_pico'])} × 100 = {fi(v)}%", 0)


def _intestino(c):
    if c["liquidas"] >= 3:
        return 2
    return 1 if c["sem_evac"] >= 3 else 0


def _desc(c):
    if not c["atb"]:
        return 0
    if c["germe"] and c["espectro_maior"]:
        return 1
    if not c["infec"] or c["pct"] < 0.5 or _pct_queda(c) >= 80:
        return 2
    return 3


BID_NOS = [
    No("apto", "S · Apto ao TRE?", "S de Spontaneous breathing trial: cumpre TODOS os critérios do TRE (P/F ≥ 150, PEEP ≤ 8, FiO₂ ≤ 40%, nora ≤ 0,1, desperto, tosse)?",
       [("Apto", "todos os critérios", "tre", None),
        ("Ainda não", "falta um critério", "intestino", "sem critérios para TRE (reavaliar amanhã)")],
       lambda c: 0 if _apto(c) else 1,
       lambda c: (f"P/F {fi(_pf(c))}, PEEP {c['peep']}, FiO₂ {c['fio2']}%, noradrenalina {f2(c['nora'])}, "
                  f"{'desperto' if c['rass_ok'] else 'sedado demais'}, tosse {'eficaz' if c['tosse'] else 'fraca'}. "
                  + ("Tudo cumprido." if _apto(c) else "Basta um critério falhar."))),
    No("tre", "Resultado TRE", "TRE em PSV 5–7 (ou tubo T), 30–120 min. Passou? Falha: f/VT > 105, FR > 35, SpO₂ < 90 ou FC > 140",
       [("Passou", "f/VT ≤ 105, estável", "intestino", "passou no TRE: extubar"),
        ("Falhou", "f/VT > 105 ou sinal", "intestino",
         "falhou no TRE: repouso na VM e buscar a causa")],
       lambda c: 1 if _falhou(c) else 0,
       lambda c: (f"Tobin {c['f']} ÷ {f2(c['vt'] / 1000)} = {fi(_tobin(c))}; durante o teste FR {c['fr_tre']}, "
                  f"SpO₂ {c['spo2_tre']}%, FC {c['fc_tre']}. " + ("Um sinal de falha basta." if _falhou(c) else "Nenhum sinal de falha."))),
    No("intestino", "B · Intestino", "B de Bowel: e o intestino?",
       [("Normal", "evacuando bem", "cateter", "intestino funcionando"),
        ("Constipado", "≥ 3 dias parado", "cateter", "laxativo (≥ 3 dias sem evacuar)"),
        ("Diarreia", "≥ 3 líquidas/dia", "cateter",
         "diarreia: pesquisar C. difficile")],
       _intestino,
       lambda c: f"Sem evacuar há {c['sem_evac']} dia(s); evacuações líquidas nas últimas 24 h: {c['liquidas']}."),
    No("cateter", "I · Cateteres", "I de Indwelling catheters: a sonda vesical e o cateter central ainda têm indicação?",
       [("Indicados", "ainda há motivo", "desc", "dispositivos mantidos (indicados)"),
        ("Sem indicação", "retirar hoje", "desc", "retirar o dispositivo sem indicação")],
       lambda c: 0 if c["indicacao"] else 1,
       lambda c: f"Dispositivos: {c['disp']}. " + (f"Motivo: {c['indicacao']}." if c["indicacao"] else
                                                   "Nenhum motivo atual: cada dia a mais é risco de infecção.")),
    No("desc", "D · Antibiótico", "D de De-escalation: e o antibiótico? (suspender se infecção afastada, PCT < 0,5 ou queda ≥ 80%)",
       [("Sem antibiótico", "nada a ajustar", "f_bid_sem", None),
        ("Descalonar", "germe sensível", "f_bid_descalonar", None),
        ("Suspender", "PCT < 0,5 ou −80%", "f_bid_suspender", None),
        ("Manter", "infecção ativa", "f_bid_manter", None)],
       _desc,
       lambda c: ("Sem antibiótico em uso." if not c["atb"] else
                  f"Em uso: {c['atb']}; cultura: {c['germe'] or 'negativa'}; infecção "
                  f"{'confirmada' if c['infec'] else 'afastada'}; PCT {f2(c['pct_pico'])} → {f2(c['pct'])} "
                  f"(queda de {fi(_pct_queda(c))}%).")),
    Folha("f_bid_sem", "Sem antibiótico", "Sem antibiótico para ajustar",
          "Nem todo febril na UTI tem infecção: antes de começar, colha culturas e procure o foco."),
    Folha("f_bid_descalonar", "Descalonar", "Descalonar o antibiótico pela cultura",
          "Descalonar não aumenta mortalidade e reduz resistência e C. difficile. Olhe o antibiograma todos os dias."),
    Folha("f_bid_suspender", "Suspender", "Suspender o antibiótico",
          "PCT < 0,5 ou queda ≥ 80% do pico, com melhora clínica, autoriza parar. A PCT ajuda a PARAR, não a começar."),
    Folha("f_bid_manter", "Manter", "Manter o antibiótico e marcar a duração (7 dias na maioria)",
          "Marque a data de término já hoje: cursos curtos (5–7 dias) valem para pneumonia, pielonefrite e intra-abdominal controlada."),
]

_ATB = ["meropeném", "piperacilina-tazobactam", "cefepima + vancomicina"]
_GERME = ["E. coli sensível a ceftriaxona", "S. aureus sensível à oxacilina", "Klebsiella sensível a ceftriaxona"]
_DISP = [("sonda vesical", "diurese horária em choque"), ("CVC", "noradrenalina em curso"),
         ("sonda vesical", "retenção urinária"), ("CVC", "nutrição parenteral")]


def _gerar_bid(rng, alvo):
    c = {"pao2": 0, "fio2": 40, "peep": 8, "nora": 0.0, "rass_ok": True, "tosse": True,
         "f": 20, "vt": 450, "fr_tre": 24, "spo2_tre": 95, "fc_tre": 100}
    apto = rng.random() < 0.65
    for _ in range(300):
        c["fio2"] = rng.choice([30, 35, 40, 40, 50, 60])
        c["peep"] = rng.choice([5, 6, 8, 8, 10, 12])
        c["pao2"] = rng.randint(55, 120)
        c["nora"] = rng.choice([0.0, 0.0, 0.0, 0.05, 0.25])
        c["rass_ok"], c["tosse"] = rng.random() < 0.85, rng.random() < 0.85
        if 140 <= _pf(c) <= 160:
            continue
        if _apto(c) == apto:
            break
    if apto:
        falha = rng.random() < 0.45
        for _ in range(300):
            c["f"], c["vt"] = rng.randint(14, 38), rng.randrange(250, 600, 10)
            c["fr_tre"], c["spo2_tre"], c["fc_tre"] = rng.randint(16, 32), rng.randint(91, 99), rng.randint(80, 130)
            if falha and rng.random() < 0.5:
                k = rng.randrange(3)
                if k == 0:
                    c["fr_tre"] = rng.randint(37, 44)
                elif k == 1:
                    c["spo2_tre"] = rng.randint(84, 88)
                else:
                    c["fc_tre"] = rng.randint(145, 160)
            if 95 <= _tobin(c) <= 115:
                continue
            if _falhou(c) == falha:
                break
    c["sem_evac"], c["liquidas"] = rng.choice([(rng.randint(0, 1), 0), (rng.randint(3, 6), 0), (0, rng.randint(3, 7)),
                                               (2, rng.randint(0, 2))])
    disp, motivo = rng.choice(_DISP)
    c["disp"] = disp
    c["indicacao"] = motivo if rng.random() < 0.5 else None
    c.update(atb=None, germe=None, espectro_maior=False, infec=True, pct_pico=0.0, pct=0.0)
    if alvo != "f_bid_sem":
        c["atb"] = rng.choice(_ATB)
        alvo_i = {"f_bid_descalonar": 1, "f_bid_suspender": 2, "f_bid_manter": 3}[alvo]
        for _ in range(300):
            c["pct_pico"] = round(rng.uniform(2.0, 15.0), 2)
            c["pct"] = round(c["pct_pico"] * rng.uniform(0.1, 0.9), 2)
            c["germe"] = rng.choice(_GERME) if rng.random() < 0.6 else None
            c["espectro_maior"] = bool(c["germe"]) and rng.random() < 0.7
            c["infec"] = bool(c["germe"]) or rng.random() < 0.6
            q = _pct_queda(c)
            if 75 <= q <= 85 or 0.4 <= c["pct"] <= 0.6:
                continue
            if _desc(c) == alvo_i:
                break
    c["texto"] = rng.choice(["Pneumonia grave, 5º dia de ventilação mecânica.", "Choque séptico abdominal, 6º dia de UTI.",
                             "Pós-operatório de cirurgia de aorta, 4º dia intubado."])
    c["mostrar"] = [("PaO₂ · FiO₂", f"{c['pao2']} · {c['fio2']}%"), ("PEEP", f"{c['peep']} cmH₂O"),
                    ("Noradrenalina", f2(c["nora"]) if c["nora"] else "sem"),
                    ("Desperto · tosse", f"{'sim' if c['rass_ok'] else 'RASS −4'} · {'eficaz' if c['tosse'] else 'fraca'}"),
                    ("f · VT no TRE", f"{c['f']} irpm · {c['vt']} mL" if apto else "—"),
                    ("FR · SpO₂ · FC", f"{c['fr_tre']} · {c['spo2_tre']}% · {c['fc_tre']}" if apto else "—"),
                    ("Sem evacuar", f"{c['sem_evac']} dia(s)"), ("Líquidas/24 h", fi(c["liquidas"])),
                    ("Dispositivo", c["disp"]), ("Indicação", c["indicacao"] or "nenhuma atual"),
                    ("Antibiótico", c["atb"] or "nenhum"), ("Cultura", c["germe"] or ("negativa" if c["atb"] else "—")),
                    ("Infecção", ("confirmada" if c["infec"] else "afastada") if c["atb"] else "—"),
                    ("PCT pico → hoje", f"{f2(c['pct_pico'])} → {f2(c['pct'])}" if c["atb"] else "—")]
    return c


FAST_HUGS_BID = Arvore("fasthug_bid", "FAST HUGS BID: desmame e o resto",
                       f"{VINCENT} · TRE → intestino → cateteres → antibiótico",
                       "apto", BID_NOS, _gerar_bid, [n.id for n in BID_NOS if n.folha],
                       lambda c: [("P/F", fi(_pf(c))), ("Tobin", fi(_tobin(c)))]
                       + ([("Queda da PCT", f"{fi(_pct_queda(c))}%")] if c["atb"] else []), grupo="uti")
FAST_HUGS_BID.plano = True
FAST_HUGS_BID.nos["apto"].calc = _c_pf
FAST_HUGS_BID.nos["tre"].calc = _c_tobin
FAST_HUGS_BID.nos["desc"].calc = lambda c: _c_pct(c) if c["atb"] else None

UTI = [FAST_HUG, FAST_HUGS_BID]
for _a in UTI:
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None

# ------------------------------------------------------------------ mini-aulas (o porquê de cada passo)
# Molde: a pergunta que a caixa responde → o mecanismo (por quê) → a armadilha da prova.

AULAS = {
    "fasthug": {
        "dieta": "Intestino parado atrofia e deixa bactéria passar para o sangue; por isso a dieta enteral começa cedo, em "
                 "24–48 h. Mas intestino sem sangue (choque piorando) pode necrosar com dieta: adie até estabilizar. "
                 "Armadilha: noradrenalina estável ou caindo NÃO impede a enteral.",
        "dor": "Quem está intubado não diz que dói, e dor parece agitação. A BPS soma face, membros superiores e "
               "adaptação ao ventilador (cada um de 1 a 4). Acima de 5 é dor: trate com opioide ANTES de aumentar o sedativo.",
        "sed": "Sedação profunda sem motivo prolonga a ventilação e aumenta delirium e mortalidade. O alvo é leve (RASS −2 a "
               "0), com despertar diário. Exceção: SDRA grave com bloqueador, hipertensão intracraniana e estado de mal.",
        "trombo": "Todo paciente de UTI tem risco de trombose. Enoxaparina é a padrão, mas acumula se o rim filtra menos de "
                  "30 mL/min: aí use heparina não fracionada. Sangrando ou com plaquetas < 50 mil, só proteção mecânica.",
        "cab": "Deitado reto, o conteúdo do estômago sobe e escorre para o pulmão pelo lado do tubo. Cabeceira a 30–45° "
               "reduz pneumonia associada à ventilação. Coluna instável não dobra: incline a cama inteira (proclive).",
        "up": "Úlcera de estresse sangra em quem tem coagulopatia, choque ou doença hepática crônica (SCCM 2024). Sem esses "
              "fatores, IBP só traz risco: pneumonia e C. difficile. Armadilha: IBP 'de rotina' deve ser suspenso.",
        "glic": "Estresse sobe a glicemia. Trate só a hiperglicemia PERSISTENTE (≥ 180), com alvo de 140–180. O NICE-SUGAR "
                "mostrou que o alvo apertado (80–110) mata por hipoglicemia. Uma medida alta isolada não basta.",
    },
    "fasthug_bid": {
        "apto": "Todo dia, pergunte se ele já pode tentar respirar sozinho. Critérios: oxigena bem com pouco suporte (P/F ≥ "
                "150, PEEP ≤ 8, FiO₂ ≤ 40%), sem vasopressor relevante, desperto e com tosse. Um critério que falha adia.",
        "tre": "No teste ele respira com quase nenhuma ajuda por 30–120 min. Respiração rápida e rasa é sinal de cansaço: "
               "o índice de Tobin (frequência ÷ volume em litros) acima de 105 prevê falha. FR > 35, SpO₂ < 90 ou FC > 140 "
               "também.",
        "intestino": "O paciente de UTI recebe opioide, fica imóvel e para de evacuar: 3 dias sem evacuar pede laxativo. "
                     "Diarreia na UTI com antibiótico pede pesquisa de C. difficile antes de culpar a dieta.",
        "cateter": "Cada dia de sonda vesical aumenta o risco de infecção urinária, e cada dia de cateter central, o de "
                   "infecção de corrente. Pergunte todo dia: ainda há motivo? Se não há, retire hoje.",
        "desc": "Antibiótico de amplo espectro começa sem saber o germe. Com a cultura, troque pelo mais estreito que cobre "
                "(descalonar). Sem infecção, suspenda. A procalcitonina ajuda a PARAR: < 0,5 ou queda ≥ 80% do pico.",
    },
}
for _a in UTI:
    for _nid, _txt in AULAS[_a.id].items():
        _a.nos[_nid].aula = _txt
