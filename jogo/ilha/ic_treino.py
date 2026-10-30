"""Modo Treino da insuficiência cardíaca: casos gerados na hora, infinitos.

O gabarito sai da REGRA da aula: perfil de Stevenson pelos sinais, NYHA, estágio ACC/AHA, fenótipo pela FE,
peptídeos (cortes de exclusão e por idade), H2FPEF, Framingham, dose/resposta do diurético, ferro IV,
CDI/ressincronização — e duas regras de farmacologia reaproveitadas (antagonista mineralocorticoide e
ivabradina). Cenários ambíguos (em cima do corte) são re-sorteados.
"""
import random

from . import fc_treino

MATERIA = "Cardiologia"
PREFIXO = "ic-treino"

HABILIDADES = {
    "perfil": ("Perfil hemodinâmico", "Sinais de congestão e de perfusão → A, B, C ou L e a conduta"),
    "nyha": ("Classe NYHA", "O que o paciente consegue fazer → I a IV"),
    "estagio": ("Estágio ACC/AHA", "Risco, doença estrutural, sintomas, refratariedade → A a D"),
    "fe": ("Fenótipo pela FE", "ICFEr, ICFElr, ICFEp ou FE melhorada"),
    "pept": ("BNP / NT-proBNP", "Contexto, idade e valor → exclui, confirma ou zona cinzenta"),
    "h2fpef": ("Escore H2FPEF", "Somar e interpretar a probabilidade de ICFEp"),
    "fram": ("Critérios de Framingham", "2 maiores, ou 1 maior + 2 menores"),
    "diur": ("Diurético na IC aguda", "Dose IV inicial e resposta pela natriurese/diurese"),
    "ferro": ("Ferro intravenoso", "Ferritina e saturação de transferrina → tratar ou não"),
    "disp": ("CDI e ressincronização", "FE, QRS, morfologia, NYHA e tempo de terapia → dispositivo"),
    "arm": ("Antagonista mineralocorticoide", "K⁺ e TFG → iniciar, manter, reduzir, suspender"),
    "ivab": ("Ivabradina: indicada?", "Ritmo sinusal, FC ≥ 70, FE ≤ 35%, betabloqueador otimizado"),
}


def fmt(x, casas=0):
    return f"{x:.{casas}f}".replace(".", ",")


def _montar(rng, habil, enunciado, certa, erradas, coment):
    erradas = [e for e in dict.fromkeys(erradas) if e != certa]
    rng.shuffle(erradas)
    alts = [certa] + erradas[:4]
    rng.shuffle(alts)
    return {"id": f"{PREFIXO}:{habil}", "enunciado": enunciado, "alts": list(zip("ABCDE", alts)),
            "gab": "ABCDE"[alts.index(certa)], "coment": coment, "materia": MATERIA, "subtema": "",
            "assunto": "", "imgs": [], "prev": 0.5, "origem": "caso gerado", "treino": True}


_CONG = ["ortopneia", "turgência jugular a 45°", "estertores até terço médio", "edema de membros inferiores 3+/4+", "refluxo hepatojugular"]
_SECO = ["sem ortopneia", "jugulares planas", "pulmões limpos", "sem edema"]
_FRIO = ["extremidades frias e pegajosas", "PA 84×66 mmHg (convergente)", "sonolência", "diurese de 15 mL/h", "lactato 4,2 mmol/L"]
_QUENTE = ["extremidades quentes", "PA 128×76 mmHg", "lúcido", "boa diurese"]
_PERFIS = {
    ("q", "s"): "A (quente-seco): compensado — otimizar a terapia oral",
    ("q", "u"): "B (quente-úmido): diurético de alça IV ± vasodilatador",
    ("f", "u"): "C (frio-úmido): inotrópico (dobutamina) ± vasopressor e diurético",
    ("f", "s"): "L (frio-seco): reposição volêmica cautelosa",
}


def _q_perfil(rng):
    perf = rng.choice(["q", "f"])
    cong = rng.choice(["s", "u"])
    sinais = rng.sample(_CONG if cong == "u" else _SECO, 2) + rng.sample(_FRIO if perf == "f" else _QUENTE, 2)
    rng.shuffle(sinais)
    certa = _PERFIS[(perf, cong)]
    erradas = [v for k, v in _PERFIS.items() if k != (perf, cong)] + ["B (quente-úmido): betabloqueador IV em bolus"]
    return _montar(rng, "perfil", f"IC descompensada: {', '.join(sinais)}. Perfil hemodinâmico e conduta:", certa, erradas,
                   f"Congestão: {'sim' if cong == 'u' else 'não'}; perfusão: {'ruim' if perf == 'f' else 'adequada'} → {certa}. "
                   "Úmido = ortopneia, jugular, estertores, edema, refluxo hepatojugular; frio = extremidades frias, PA convergente, sonolência, oligúria, lactato.")


_NYHA = [
    ("sobe dois lances de escada e joga futebol sem sintomas", "I"),
    ("tem dispneia ao subir dois lances de escada ou caminhar rápido, mas não nas atividades leves", "II"),
    ("tem dispneia ao caminhar meio quarteirão no plano ou ao se vestir", "III"),
    ("tem dispneia em repouso, deitado ou sentado", "IV"),
    ("cansa ao tomar banho e ao caminhar dentro de casa", "III"),
    ("está assintomático no dia a dia, só cansa em corrida intensa", "I"),
]


def _q_nyha(rng):
    desc, certa = rng.choice(_NYHA)
    return _montar(rng, "nyha", f"Paciente com IC que {desc}. Classe funcional NYHA:", certa, ["I", "II", "III", "IV", "Não classificável"],
                   f"NYHA {certa}. I: sem limitação; II: esforços habituais; III: esforços menores que os habituais; IV: em repouso.")


_EST = [
    ("hipertenso e diabético, eco normal, sem sintomas", "A"),
    ("em quimioterapia com antraciclina, eco normal, sem sintomas", "A"),
    ("IAM há 1 ano, FE 38%, nunca teve sintomas", "B"),
    ("hipertrofia ventricular esquerda no eco, sem sintomas", "B"),
    ("internou por IC há 6 meses e hoje está assintomático com o tratamento", "C"),
    ("dispneia aos esforços com FE 32%", "C"),
    ("três internações em 6 meses, dependente de inotrópico, apesar da terapia otimizada", "D"),
]


def _q_estagio(rng):
    desc, certa = rng.choice(_EST)
    return _montar(rng, "estagio", f"Paciente {desc}. Estágio da IC (ACC/AHA):", certa, ["A", "B", "C", "D", "Sem IC, não se classifica"],
                   f"Estágio {certa}. A risco; B doença estrutural sem sintomas; C sintomas atuais ou prévios (não regride); D refratária/avançada.")


def _q_fe(rng):
    prev = rng.random() < 0.3
    for _ in range(50):
        fe = rng.choice([22, 28, 33, 38, 44, 47, 52, 58, 63])
        if not prev or fe > 40:
            break
    if prev:
        antes = rng.choice([25, 30, 35])
        certa = "IC com FE melhorada" if fe - antes >= 10 else ("ICFElr (41–49%)" if fe < 50 else "ICFEp (≥ 50%)")
        enun = f"Paciente com IC cuja FE era {antes}% e hoje, após tratamento, é {fe}%. Classificação:"
    else:
        certa = "ICFEr (≤ 40%)" if fe <= 40 else "ICFElr (41–49%)" if fe < 50 else "ICFEp (≥ 50%)"
        enun = f"Paciente sintomático com peptídeo elevado e FE de {fe}% no eco (sem medida anterior). Classificação:"
    erradas = ["ICFEr (≤ 40%)", "ICFElr (41–49%)", "ICFEp (≥ 50%)", "IC com FE melhorada", "IC curada"]
    return _montar(rng, "fe", enun, certa, erradas,
                   "FE ≤ 40% reduzida; 41–49% levemente reduzida; ≥ 50% preservada; FE melhorada = era ≤ 40% e subiu > 40% com ganho ≥ 10 pontos "
                   "(manter a terapia). Classificação da AHA/ACC 2022 e da diretriz brasileira; a ESC 2026 juntou tudo abaixo "
                   "de 50% como FE reduzida, com o mesmo tratamento.")


def _q_pept(rng):
    for _ in range(100):
        cont = rng.choice(["crônico", "agudo"])
        tipo = rng.choice(["BNP", "NT-proBNP"])
        idade = rng.choice([42, 58, 68, 79, 86])
        if cont == "crônico":
            corte = 35 if tipo == "BNP" else 125
            valor = rng.choice([corte // 2, int(corte * 0.7), corte * 3, corte * 8])
            certa = "IC improvável (abaixo do corte de exclusão)" if valor < corte else "compatível com IC — prosseguir com ecocardiograma"
            regra = f"ambulatório: exclui se {tipo} < {corte} pg/mL"
        else:
            if tipo == "BNP":
                valor = rng.choice([45, 70, 400, 900])
                if abs(valor - 100) < 10:
                    continue
                certa = "IC aguda improvável" if valor < 100 else "compatível com IC aguda"
                regra = "agudo: BNP < 100 exclui"
            else:
                conf = 450 if idade < 50 else 900 if idade <= 75 else 1800
                valor = rng.choice([180, 250, 600, 1200, 2600, 5200])
                if valor < 300:
                    certa = "IC aguda improvável"
                elif valor > conf:
                    certa = "compatível com IC aguda"
                else:
                    certa = "zona cinzenta: depende da clínica e do eco"
                regra = f"agudo: NT-proBNP < 300 exclui; confirma acima de {conf} para {idade} anos (450 < 50; 900 50–75; 1.800 > 75)"
        break
    erradas = ["IC improvável (abaixo do corte de exclusão)", "compatível com IC — prosseguir com ecocardiograma", "IC aguda improvável",
               "compatível com IC aguda", "zona cinzenta: depende da clínica e do eco", "exame inválido sem troponina"]
    contexto = "no ambulatório, com dispneia aos esforços" if cont == "crônico" else "no pronto-socorro, com dispneia aguda"
    return _montar(rng, "pept", f"Paciente de {idade} anos {contexto}: {tipo} = {valor} pg/mL. Interpretação:", certa, erradas,
                   f"Regra — {regra}. Lembre: obesidade baixa os peptídeos; idade, DRC, FA, TEP e sepse elevam; com sacubitril use o NT-proBNP.")


def _q_h2fpef(rng):
    imc = rng.choice([24, 28, 31, 36])
    drogas = rng.choice([0, 1, 2, 3])
    fa = rng.random() < 0.4
    psap = rng.choice([28, 33, 38, 46])
    idade = rng.choice([52, 58, 66, 74, 81])
    ee = rng.choice([7, 8, 11, 15])
    pts = 2 * (imc > 30) + (drogas >= 2) + 3 * fa + (psap > 35) + (idade > 60) + (ee > 9)
    interp = "alta probabilidade de ICFEp" if pts >= 6 else "baixa probabilidade" if pts <= 1 else "probabilidade intermediária (investigar: teste de esforço/diastólico)"
    certa = f"{pts} pontos — {interp}"
    def interp_de(v):
        return ("alta probabilidade de ICFEp" if v >= 6 else "baixa probabilidade" if v <= 1 else
                "probabilidade intermediária (investigar: teste de esforço/diastólico)")
    outros = sorted((v for v in range(10) if v != pts), key=lambda v: abs(v - pts))[:3]
    erradas = [f"{v} pontos — {interp_de(v)}" for v in outros]
    erradas += [f"{pts} pontos — {i}" for i in ("alta probabilidade de ICFEp", "baixa probabilidade",
                                               "probabilidade intermediária (investigar: teste de esforço/diastólico)") if i != interp][:1]
    det = [n for n, ok in ((f"IMC {imc} > 30 (2)", imc > 30), (f"{drogas} anti-hipertensivos (1)", drogas >= 2), ("FA (3)", fa),
                           (f"PSAP {psap} > 35 (1)", psap > 35), (f"idade {idade} > 60 (1)", idade > 60), (f"E/e' {ee} > 9 (1)", ee > 9)) if ok]
    return _montar(rng, "h2fpef", f"Dispneia com FE 60%: IMC {imc}, {drogas} anti-hipertensivo(s), {'com' if fa else 'sem'} FA, PSAP {psap} mmHg, "
                   f"{idade} anos, E/e' {ee}. Pelo H2FPEF:", certa, erradas,
                   f"H2FPEF = {' + '.join(det) or 'nenhum item'} = {pts}. ≥ 6 alta; 0–1 baixa; 2–5 intermediária.")


_MAIORES = ["dispneia paroxística noturna", "turgência jugular", "estertores pulmonares", "cardiomegalia na radiografia", "B3", "refluxo hepatojugular"]
_MENORES = ["edema bilateral de tornozelos", "tosse noturna", "dispneia aos esforços habituais", "hepatomegalia", "derrame pleural", "FC de 124 bpm"]


def _q_fram(rng):
    nM, nm = rng.choice([(2, 0), (1, 2), (1, 1), (0, 3), (3, 1), (0, 2), (1, 0)])
    achados = rng.sample(_MAIORES, nM) + rng.sample(_MENORES, nm)
    rng.shuffle(achados)
    ok = nM >= 2 or (nM == 1 and nm >= 2)
    certa = "preenche os critérios de Framingham para IC" if ok else "não preenche os critérios de Framingham"
    erradas = ["preenche os critérios de Framingham para IC", "não preenche os critérios de Framingham",
               "preenche apenas se o BNP for normal", "critérios de Framingham não se aplicam a adultos", "precisa de 3 critérios maiores obrigatoriamente"]
    return _montar(rng, "fram", f"Paciente com: {', '.join(achados)}. Pelos critérios de Framingham:", certa, erradas,
                   f"{nM} maior(es) e {nm} menor(es). Regra: 2 maiores, ou 1 maior + 2 menores. Maiores: DPN, turgência jugular, estertores, "
                   "cardiomegalia, EAP, B3, refluxo hepatojugular. Menores: edema de tornozelos, tosse noturna, dispneia aos esforços, hepatomegalia, "
                   "derrame pleural, FC > 120.")


def _q_diur(rng):
    if rng.random() < 0.5:
        oral = rng.choice([0, 40, 80, 120, 160])
        if oral == 0:
            certa = "20–40 mg IV"
            erradas = ["40–100 mg IV", "120–300 mg IV", "400–600 mg IV em bolus", "manter só via oral"]
            enun = "Paciente congesto, sem uso prévio de diurético. Dose inicial de furosemida:"
        else:
            certa = f"{oral}–{int(oral * 2.5)} mg/dia IV (1 a 2,5× a dose oral)"
            erradas = [f"{max(10, oral // 4)} mg/dia IV", f"{oral}–{int(oral * 2.5)} mg/dia por via oral", "20 mg IV, dose única", f"{oral * 10} mg IV em bolus"]
            enun = f"Paciente congesto que usa furosemida {oral} mg/dia por via oral. Dose de furosemida IV para as primeiras 24 h:"
        regra = "virgem: 20–40 mg IV; em uso crônico: 1 a 2,5× a dose oral diária, IV (DOSE)"
    else:
        na = rng.choice([22, 35, 44, 85, 110])
        diurese = rng.choice([40, 70, 180, 250])
        boa = na >= 70 or diurese >= 150
        ruim = na < 50 and diurese < 100
        if not (boa or ruim):
            na, diurese = 30, 60
            ruim = True
        certa = "manter a dose e reavaliar" if boa else "dobrar a dose do diurético de alça"
        erradas = ["manter a dose e reavaliar", "dobrar a dose do diurético de alça", "suspender o diurético", "iniciar soro fisiológico", "reduzir a dose à metade"]
        enun = f"Duas horas após furosemida IV: sódio urinário {na} mEq/L; diurese de {diurese} mL/h. Conduta:"
        regra = "resposta adequada: Na urinário ≥ 50–70 mEq/L em 2 h ou diurese ≥ 100–150 mL/h; insuficiente → dobrar a dose"
    return _montar(rng, "diur", enun, certa, erradas, f"Regra — {regra}. Resistência persistente: acetazolamida ou tiazídico (bloqueio sequencial).")


def _q_ferro(rng):
    for _ in range(100):
        ferr = rng.choice([45, 80, 140, 220, 290, 360, 520])
        tsat = rng.choice([9, 14, 18, 24, 31])
        if not (abs(ferr - 100) < 6 or abs(ferr - 300) < 6 or abs(tsat - 20) < 2):
            break
    defic = ferr < 100 or (ferr < 300 and tsat < 20)
    certa = "ferro intravenoso (carboximaltose ou derisomaltose)" if defic else "não há deficiência de ferro: não repor"
    erradas = ["ferro intravenoso (carboximaltose ou derisomaltose)", "não há deficiência de ferro: não repor", "sulfato ferroso oral por 3 meses",
               "transfusão de hemácias", "eritropoietina"]
    return _montar(rng, "ferro", f"ICFEr sintomática, Hb 12,8 g/dL, ferritina {ferr} ng/mL, saturação de transferrina {tsat}%. Conduta:", certa, erradas,
                   f"Deficiência de ferro na IC = ferritina < 100, ou 100–299 com saturação < 20% → {'presente' if defic else 'ausente'}. "
                   "Ferro IV melhora sintomas e reduz internação; ferro oral não funciona (IRONOUT-HF).")


def _q_disp(rng):
    for _ in range(100):
        fe = rng.choice([25, 30, 33, 40])
        qrs = rng.choice([100, 118, 140, 156, 172])
        morf = rng.choice(["BRE", "BRD"]) if qrs >= 130 else "QRS estreito"
        nyha = rng.choice(["II", "III"])
        meses = rng.choice([1, 6, 6])
        if (morf == "BRE" and 140 <= qrs < 150):
            continue
        break
    trc = fe <= 35 and morf == "BRE" and qrs >= 150 and meses >= 3
    cdi = fe <= 35 and meses >= 3
    if meses < 3:
        certa = "nenhum ainda: otimizar a terapia por ≥ 3 meses e reavaliar a FE"
    elif trc:
        certa = "ressincronização (TRC, em geral com CDI)"
    elif cdi:
        certa = "CDI para prevenção primária"
    else:
        certa = "nenhum dispositivo (FE > 35%)"
    erradas = ["ressincronização (TRC, em geral com CDI)", "CDI para prevenção primária", "nenhum dispositivo (FE > 35%)",
               "nenhum ainda: otimizar a terapia por ≥ 3 meses e reavaliar a FE", "marca-passo convencional VVI"]
    qrs_txt = f"{morf} com QRS de {qrs} ms" if morf != "QRS estreito" else f"QRS estreito ({qrs} ms)"
    return _montar(rng, "disp", f"ICFEr isquêmica, FE {fe}%, ritmo sinusal, {qrs_txt}, NYHA {nyha}, há {meses} {'mês' if meses == 1 else 'meses'} em terapia otimizada. Indicação:",
                   certa, erradas,
                   "CDI primário: FE ≤ 35% com NYHA II–III após ≥ 3 meses de terapia otimizada. TRC (indicação forte): FE ≤ 35%, sinusal, BRE com QRS ≥ 150 ms. "
                   "BRD ou QRS estreito: TRC não traz benefício claro.")


def _q_arm(rng):
    q = fc_treino.questao(rng, "arm")
    q["id"] = f"{PREFIXO}:arm"
    q["materia"] = MATERIA
    return q


def _q_ivab(rng):
    q = fc_treino.questao(rng, "ivab")
    q["id"] = f"{PREFIXO}:ivab"
    q["materia"] = MATERIA
    return q


_FUNC = {"perfil": _q_perfil, "nyha": _q_nyha, "estagio": _q_estagio, "fe": _q_fe, "pept": _q_pept, "h2fpef": _q_h2fpef,
         "fram": _q_fram, "diur": _q_diur, "ferro": _q_ferro, "disp": _q_disp, "arm": _q_arm, "ivab": _q_ivab}


def questao(rng, habil):
    return _FUNC[habil](rng)


def taxa_erro(save, habil):
    s = save.stat(f"{PREFIXO}:{habil}")
    if not s or s["c"] + s["e"] == 0:
        return None
    return s["e"] / (s["c"] + s["e"])


def fase(save, habil=None, n=6, rng=None):
    rng = rng or random.Random()
    if habil:
        return [questao(rng, habil) for _ in range(n)]
    hs = list(HABILIDADES)
    pesos = [1 + 3 * (taxa_erro(save, h) if taxa_erro(save, h) is not None else 0.5) for h in hs]
    return [questao(rng, rng.choices(hs, pesos)[0]) for _ in range(n)]
