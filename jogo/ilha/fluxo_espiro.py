"""Fluxogramas da espirometria: como ler o exame (ATS/ERS 2022) e a DPOC pela espirometria (GOLD 2026).

Duas árvores, no mesmo molde das de gasometria (fluxo_dados):

  1. Espirometria: qual o padrão? ... qualidade → curva fluxo-volume (obstrução alta) → VEF₁/CVF × LIN →
                                       CVF → CPT → gravidade pelo z-score → resposta ao broncodilatador
  2. DPOC: espirometria e GOLD ...... VEF₁/CVF pós-BD < 0,70 → grau GOLD 1–4 → grupo A/B/E → eosinófilos

Regras: Stanojevic et al., ERS/ATS technical standard on interpretive strategies, Eur Respir J 2022 (LIN = z
−1,645; gravidade pelo z do VEF₁: leve > −2,5, moderada −2,5 a −4, grave < −4; restrição só com CPT < LIN;
padrão inespecífico; PRISm; resposta ao BD > 10% do PREVISTO no VEF₁ ou na CVF); Graham et al., ATS/ERS 2019
(repetibilidade: as 2 maiores CVF e os 2 maiores VEF₁ diferem ≤ 150 mL); GOLD 2026 (diagnóstico com VEF₁/CVF
pós-BD < 0,70; grupo E com 1 ou mais exacerbações moderadas ou graves no último ano; CAAT ≥ 10; LABA+LAMA+ICS
se eosinófilos ≥ 300).

Os valores previstos e os z-scores são gerados por um modelo simples (DP de 12% do previsto para volumes,
0,055 para a relação), suficiente para os números serem coerentes entre si; os geradores fogem da vizinhança
dos cortes."""
from .fluxo_dados import Arvore, Folha, No, f1, f2, fi

ATS = "ATS/ERS 2022"
GOLD = "GOLD 2026"
LIN_Z = -1.645


def _z(v, prev, dp):
    return (v - prev) / dp


# ================================================================== 1. ESPIROMETRIA: QUAL O PADRÃO?

def _razao(c):
    return c["vef"] / c["cvf"]


def _z_razao(c):
    return _z(_razao(c), c["p_razao"], 0.055)


def _lin_razao(c):
    return c["p_razao"] + LIN_Z * 0.055


def _z_cvf(c):
    return _z(c["cvf"], c["p_cvf"], 0.12 * c["p_cvf"])


def _z_vef(c):
    return _z(c["vef"], c["p_vef"], 0.12 * c["p_vef"])


def _difs(c):
    cv, vf = sorted(c["cvfs"], reverse=True), sorted(c["vefs"], reverse=True)
    return round((cv[0] - cv[1]) * 1000), round((vf[0] - vf[1]) * 1000)


def _bd_pct_prev(c):
    return (c["vef_bd"] - c["vef"]) / c["p_vef"] * 100


def _bd_pct_base(c):
    return (c["vef_bd"] - c["vef"]) / c["vef"] * 100


def _empey(c):
    return c["vef"] * 1000 / c["pfe"]


def _grav(c):
    z = _z_vef(c)
    return 0 if z > -2.5 else 1 if z >= -4 else 2


def _alca(c):
    r = c["fef_fif"]
    return 0 if r > 1.5 else 1 if r < 0.6 else 2


def _c_dif(c):
    d = _difs(c)[0]
    cv = sorted(c["cvfs"], reverse=True)
    err = [(round((cv[0] - cv[2]) * 1000), "usou a maior e a MENOR (a regra compara as duas maiores)"),
           (round((cv[1] - cv[2]) * 1000), "comparou a 2ª com a 3ª"),
           (d / 10, "errou a conversão de litros para mL")]
    return ("Diferença entre as 2 maiores CVF, em mL?", d, err,
            f"{f2(cv[0])} − {f2(cv[1])} = {f2(cv[0] - cv[1])} L = {d} mL (aceitável até 150)", 0)


def _c_razao(c):
    v = _razao(c)
    err = [(c["cvf"] / c["vef"], "inverteu: é VEF₁ ÷ CVF"),
           (c["vef"] / c["p_cvf"], "dividiu pela CVF PREVISTA, não pela medida"),
           (c["vef"] / c["p_vef"] * c["p_razao"], "misturou com o previsto")]
    return ("Quanto é a relação VEF₁/CVF?", v, err, f"{f2(c['vef'])} ÷ {f2(c['cvf'])} = {f2(v)} (LIN {f2(_lin_razao(c))})", 2)


def _c_bd(c):
    v = _bd_pct_prev(c)
    d = c["vef_bd"] - c["vef"]
    err = [(_bd_pct_base(c), "dividiu pelo VEF₁ de antes (critério antigo; a ATS/ERS 2022 usa o PREVISTO)"),
           (d / c["vef_bd"] * 100, "dividiu pelo VEF₁ depois do broncodilatador"),
           (d * 100, "usou a diferença em litros como se fosse %")]
    return ("Quanto o VEF₁ subiu, em % do VEF₁ PREVISTO?", v, err,
            f"({f2(c['vef_bd'])} − {f2(c['vef'])}) ÷ {f2(c['p_vef'])} × 100 = {fi(v)}% do previsto", 0)


def _c_fef(c):
    v = c["fef_fif"]
    err = [(c["fif"] / c["fef"], "inverteu: é expiratório ÷ inspiratório"),
           (c["fef"] - c["fif"], "subtraiu em vez de dividir"),
           (_empey(c) / 10, "confundiu com o índice de Empey")]
    return ("Quanto é a relação FEF₅₀/FIF₅₀?", v, err, f"{f1(c['fef'])} ÷ {f1(c['fif'])} = {f1(v)}", 1)


ES_NOS = [
    No("qual", "Qualidade", "Antes de ler: o exame é reprodutível?",
       [("Reprodutível", "dif. ≤ 150 mL", "curva", None),
        ("Não reprodutível", "dif. > 150 mL", "f_es_repetir", None)],
       lambda c: 0 if max(_difs(c)) <= 150 else 1,
       lambda c: (f"As 2 maiores CVF diferem {_difs(c)[0]} mL e os 2 maiores VEF₁, {_difs(c)[1]} mL. "
                  + ("Dentro de 150 mL: dá para interpretar." if max(_difs(c)) <= 150 else
                     "Acima de 150 mL: o paciente não repetiu o esforço; o número não é confiável."))),
    No("curva", "Curva fluxo-volume", "Olhe o FORMATO da curva fluxo-volume. Há platô (alça achatada)?",
       [("Sem platô", "curva sem platô", "razao", None),
        ("Platô", "alça achatada", "alca", None)],
       lambda c: 0 if not c["plato"] else 1,
       lambda c: (f"Alça expiratória: {c['exp']}; alça inspiratória: {c['insp']}. Índice de Empey {f1(_empey(c))}"
                  + (" (> 10 sugere obstrução alta)." if _empey(c) > 10 else "."))),
    No("alca", "Qual alça?", "Platô de fluxo = obstrução da via aérea central. Qual o tipo?",
       [("Extratorácica", "FEF₅₀/FIF₅₀ > 1", "f_es_extra", None),
        ("Intratorácica", "FEF₅₀/FIF₅₀ < 1", "f_es_intra", None),
        ("Fixa", "FEF₅₀/FIF₅₀ ≈ 1", "f_es_fixa", None)],
       _alca,
       lambda c: (f"FEF₅₀ {f1(c['fef'])} L/s ÷ FIF₅₀ {f1(c['fif'])} L/s = {f1(c['fef_fif'])}. "
                  + ("A inspiração está mais limitada: a lesão fecha ao inspirar, fora do tórax." if _alca(c) == 0 else
                     "A expiração está mais limitada: a lesão fecha ao expirar, dentro do tórax." if _alca(c) == 1 else
                     "As duas igualmente limitadas: o calibre não muda com a respiração (lesão rígida)."))),
    No("razao", "VEF₁/CVF × LIN", "A relação VEF₁/CVF está abaixo do limite inferior do normal (LIN)?",
       [("Abaixo do LIN", "obstrução", "cvf_obs", None), ("Normal", "≥ LIN", "cvf_nl", None)],
       lambda c: 0 if _z_razao(c) < LIN_Z else 1,
       lambda c: (f"VEF₁/CVF {f2(_razao(c))}, LIN {f2(_lin_razao(c))} (z {f1(_z_razao(c))}). "
                  + ("Abaixo do LIN: obstrução." if _z_razao(c) < LIN_Z else "Acima do LIN: sem obstrução.")
                  + (" Note: abaixo de 0,70 mas acima do LIN, o que é normal para a idade." if _razao(c) < 0.70 and _z_razao(c) >= LIN_Z else ""))),
    No("cvf_obs", "CVF na obstrução", "Obstrução confirmada. A CVF também está abaixo do LIN?",
       [("CVF normal", "obstrução pura", "grav", None), ("CVF baixa", "medir a CPT", "cpt_obs", None)],
       lambda c: 0 if _z_cvf(c) >= LIN_Z else 1,
       lambda c: f"CVF {f2(c['cvf'])} L, z {f1(_z_cvf(c))}. " + (
           "Normal." if _z_cvf(c) >= LIN_Z else "Baixa: ar preso ou restrição junto? Só a CPT diz.")),
    No("cpt_obs", "CPT na obstrução", "Obstrução com CVF baixa. O que mostra a capacidade pulmonar total (CPT)?",
       [("CPT < LIN", "restrição junto", "grav", "distúrbio misto (CPT abaixo do LIN)"),
        ("CPT ≥ LIN", "ar aprisionado", "grav", "CVF reduzida por aprisionamento aéreo (CPT normal)")],
       lambda c: 0 if c["z_cpt"] < LIN_Z else 1,
       lambda c: f"CPT z {f1(c['z_cpt'])}. " + ("Pulmão pequeno: há restrição de verdade." if c["z_cpt"] < LIN_Z else
                                              "Pulmão de tamanho normal: a CVF caiu porque o ar ficou preso.")),
    No("grav", "Gravidade (z do VEF₁)", "Qual a gravidade, pelo z-score do VEF₁?",
       [("Leve", "z > −2,5", "bd", "obstrução leve (z do VEF₁ acima de −2,5)"),
        ("Moderada", "z de −2,5 a −4", "bd", "obstrução moderada (z do VEF₁ entre −2,5 e −4)"),
        ("Grave", "z < −4", "bd", "obstrução grave (z do VEF₁ abaixo de −4)")],
       _grav,
       lambda c: f"VEF₁ {f2(c['vef'])} L = {fi(c['vef'] / c['p_vef'] * 100)}% do previsto, z {f1(_z_vef(c))}."),
    No("bd", "Resposta ao BD", "Após 400 mcg de salbutamol: houve resposta significativa?",
       [("Significativa", "> 10% do previsto", "f_es_obs_bd", None),
        ("Não significativa", "≤ 10% do previsto", "f_es_obs", None)],
       lambda c: 0 if _bd_pct_prev(c) > 10 else 1,
       lambda c: (f"VEF₁ {f2(c['vef'])} → {f2(c['vef_bd'])} L: +{fi(_bd_pct_prev(c))}% do previsto "
                  f"(+{fi(_bd_pct_base(c))}% do valor inicial, +{round((c['vef_bd'] - c['vef']) * 1000)} mL). "
                  + ("A ATS/ERS 2022 conta sobre o PREVISTO; a regra antiga (12% e 200 mL sobre o inicial) daria outro resultado."
                     if (_bd_pct_prev(c) > 10) != (_bd_pct_base(c) >= 12 and c["vef_bd"] - c["vef"] >= 0.2) else ""))),
    No("cvf_nl", "CVF, relação normal", "Relação normal. E a CVF?",
       [("CVF normal", "≥ LIN", "f_es_normal", None), ("CVF baixa", "< LIN: medir CPT", "cpt", None)],
       lambda c: 0 if _z_cvf(c) >= LIN_Z else 1,
       lambda c: f"CVF {f2(c['cvf'])} L, {fi(c['cvf'] / c['p_cvf'] * 100)}% do previsto, z {f1(_z_cvf(c))}."),
    No("cpt", "Tem CPT?", "Relação normal e CVF baixa. O que mostra a capacidade pulmonar total?",
       [("CPT < LIN", "restrição", "f_es_restr", None), ("CPT ≥ LIN", "padrão inespecífico", "f_es_inesp", None),
        ("Sem CPT", "só espirometria", "f_es_prism", None)],
       lambda c: 2 if c["z_cpt"] is None else 0 if c["z_cpt"] < LIN_Z else 1,
       lambda c: ("Só há espirometria: a CPT não foi medida." if c["z_cpt"] is None else
                  f"CPT z {f1(c['z_cpt'])}: " + ("abaixo do LIN." if c["z_cpt"] < LIN_Z else "normal."))),
    Folha("f_es_repetir", "Repetir", "Exame não reprodutível: repetir as manobras antes de interpretar",
          "Laudo de exame não reprodutível pode inventar obstrução. São ao menos 3 manobras aceitáveis e 2 reprodutíveis."),
    Folha("f_es_extra", "Extratorácica variável", "Obstrução variável de via aérea central EXTRATORÁCICA (platô só na inspiração)",
          "Na inspiração a pressão dentro da via aérea cai abaixo da atmosférica e a lesão fecha: paralisia de pregas vocais, laringomalácia."),
    Folha("f_es_intra", "Intratorácica variável", "Obstrução variável de via aérea central INTRATORÁCICA (platô só na expiração)",
          "Na expiração forçada a pressão no tórax esmaga a traqueia: traqueomalácia, tumor de traqueia distal ou brônquio-fonte."),
    Folha("f_es_fixa", "Obstrução fixa", "Obstrução FIXA de via aérea central (platô nas duas alças)",
          "Lesão rígida não muda com a respiração: estenose traqueal pós-intubação, bócio mergulhante, tumor que envolve a traqueia."),
    Folha("f_es_obs_bd", "Obstrutivo com resposta", "Distúrbio ventilatório obstrutivo com resposta significativa ao broncodilatador",
          "Resposta ao BD sugere asma, mas não a confirma nem exclui DPOC: o diagnóstico é clínico mais funcional."),
    Folha("f_es_obs", "Obstrutivo sem resposta", "Distúrbio ventilatório obstrutivo sem resposta significativa ao broncodilatador",
          "Sem resposta não exclui asma (pode estar controlada ou fora de crise) e não indica que o broncodilatador não deva ser usado."),
    Folha("f_es_normal", "Normal", "Espirometria normal",
          "VEF₁/CVF e CVF acima do LIN. Sintoma com espirometria normal: pense em asma fora de crise (variabilidade, metacolina)."),
    Folha("f_es_restr", "Restritivo", "Distúrbio ventilatório restritivo (CPT abaixo do LIN)",
          "Restrição só se diz com CPT: doença intersticial, obesidade, doença neuromuscular, deformidade torácica, ressecção."),
    Folha("f_es_inesp", "Inespecífico", "Padrão inespecífico: VEF₁/CVF normal, CVF baixa e CPT normal",
          "Comum em asma com ar preso, obesidade e esforço submáximo. Não é restrição: a CPT é normal."),
    Folha("f_es_prism", "PRISm", "CVF reduzida com relação normal (PRISm): sugere restrição, mas só a CPT confirma",
          "Na espirometria isolada não escreva 'restritivo': CVF baixa com relação normal é restrição verdadeira em só cerca de metade."),
]

_EXP = {"normal": "pico e descida reta", "plato": "platô"}
_INSP = {"normal": "semicírculo", "plato": "platô"}


def _gerar_es(rng, alvo):
    idade = rng.randint(20, 80)
    p_cvf = round(rng.uniform(3.0, 5.2), 2)
    p_razao = 0.84 - 0.0025 * (idade - 20)
    c = {"idade": idade, "mulher": rng.random() < 0.5, "p_cvf": p_cvf, "p_razao": p_razao,
         "p_vef": round(p_cvf * p_razao, 2), "plato": False, "exp": _EXP["normal"], "insp": _INSP["normal"],
         "z_cpt": None, "vef_bd": 0.0}
    plato = alvo in ("f_es_extra", "f_es_intra", "f_es_fixa")

    def faixa(lo, hi):
        return rng.uniform(lo, hi)

    velho = alvo == "f_es_normal" and rng.random() < 0.35 and idade >= 60
    cvf_baixa = rng.random() < 0.45

    def sortear():
        if alvo in ("f_es_obs", "f_es_obs_bd"):
            return faixa(-5.5, -2.0), (faixa(-3.5, -2.0) if cvf_baixa else faixa(-1.2, 0.8))
        if alvo in ("f_es_restr", "f_es_inesp", "f_es_prism"):
            return faixa(-1.0, 1.5), faixa(-4.0, -2.0)
        if velho:                                     # idoso: relação < 0,70 mas acima do LIN
            return faixa(-1.3, -0.6), faixa(-1.2, 1.0)
        return faixa(-1.2, 1.0), faixa(-1.2, 1.0)

    for _ in range(400):
        zr, zc = sortear()
        cvf = round(p_cvf + zc * 0.12 * p_cvf, 2)
        vef = round(cvf * (p_razao + zr * 0.055), 2)
        c["cvf"], c["vef"] = cvf, vef
        ok = abs(_z_razao(c) - LIN_Z) > 0.25 and abs(_z_cvf(c) - LIN_Z) > 0.25
        if alvo in ("f_es_obs", "f_es_obs_bd"):
            z = _z_vef(c)
            ok = ok and min(abs(z + 2.5), abs(z + 4)) > 0.2
        if ok:
            break
    # 3 manobras: a maior de cada é a que vale
    repro = alvo != "f_es_repetir"
    d1 = rng.randint(20, 120) if repro else rng.randint(190, 400)
    d2 = rng.randint(20, 120) if repro or rng.random() < 0.5 else rng.randint(190, 400)
    c["cvfs"] = [c["cvf"], round(c["cvf"] - d1 / 1000, 2), round(c["cvf"] - (d1 + rng.randint(30, 300)) / 1000, 2)]
    c["vefs"] = [c["vef"], round(c["vef"] - d2 / 1000, 2), round(c["vef"] - (d2 + rng.randint(30, 300)) / 1000, 2)]
    # curva
    c["pfe"] = round(c["vef"] * 1000 / rng.uniform(5.0, 8.5))
    c["fef"] = round(rng.uniform(3.0, 5.0), 1)
    c["fif"] = round(c["fef"] / rng.uniform(0.75, 1.1), 1)
    if plato:
        c["plato"] = True
        k = {"f_es_extra": 0, "f_es_intra": 1, "f_es_fixa": 2}[alvo]
        if k == 0:
            c["fif"] = round(rng.uniform(1.0, 1.8), 1)
            c["fef"] = round(c["fif"] * rng.uniform(1.9, 3.0), 1)
            c["insp"] = _INSP["plato"]
        elif k == 1:
            c["fef"] = round(rng.uniform(1.0, 1.6), 1)
            c["fif"] = round(c["fef"] / rng.uniform(0.25, 0.45), 1)
            c["exp"] = _EXP["plato"]
            c["pfe"] = round(c["vef"] * 1000 / rng.uniform(11, 15))
        else:
            c["fef"] = round(rng.uniform(1.2, 2.0), 1)
            c["fif"] = round(c["fef"] / rng.uniform(0.85, 1.15), 1)
            c["exp"], c["insp"] = _EXP["plato"], _INSP["plato"]
            c["pfe"] = round(c["vef"] * 1000 / rng.uniform(11, 15))
    c["fef_fif"] = c["fef"] / c["fif"]
    # CPT
    if alvo == "f_es_restr" or (alvo in ("f_es_obs", "f_es_obs_bd") and _z_cvf(c) < LIN_Z and rng.random() < 0.5):
        c["z_cpt"] = round(rng.uniform(-3.5, -2.0), 1)
    elif alvo == "f_es_inesp" or (alvo in ("f_es_obs", "f_es_obs_bd") and _z_cvf(c) < LIN_Z):
        c["z_cpt"] = round(rng.uniform(-1.2, 1.5), 1)
    # broncodilatador
    if alvo == "f_es_obs_bd":
        c["vef_bd"] = round(c["vef"] + c["p_vef"] * rng.uniform(0.12, 0.22), 2)
    elif alvo == "f_es_obs" and rng.random() < 0.4 and c["vef"] < 0.55 * c["p_vef"]:
        for _ in range(50):                           # armadilha: ≥ 12% e 200 mL do inicial, mas ≤ 10% do previsto
            c["vef_bd"] = round(c["vef"] + rng.randrange(210, 300, 10) / 1000, 2)
            if _bd_pct_prev(c) <= 9 and _bd_pct_base(c) >= 13:
                break
        else:
            c["vef_bd"] = round(c["vef"] + c["p_vef"] * rng.uniform(0.01, 0.07), 2)
    else:
        c["vef_bd"] = round(c["vef"] + c["p_vef"] * rng.uniform(0.01, 0.07), 2)
    c["texto"] = rng.choice(["Encaminhado por dispneia aos esforços há 6 meses.", "Tosse crônica, exame pedido pela UBS.",
                             "Avaliação pré-operatória, refere chiado ocasional.", "Dispneia progressiva; ex-tabagista."])
    if plato:
        c["texto"] = rng.choice(["Intubado por 3 semanas há 4 meses; agora estridor ao esforço.",
                                 "Dispneia progressiva com ruído respiratório; bócio volumoso.",
                                 "Dispneia e ruído ao respirar que não melhoram com bombinha."])
    oculto = alvo == "f_es_repetir"
    c["mostrar"] = [("Idade · sexo", f"{idade} a · {'♀' if c['mulher'] else '♂'}"),
                    ("CVF ×3 (L)", " · ".join(f2(v) for v in c["cvfs"])),
                    ("VEF₁ ×3 (L)", " · ".join(f2(v) for v in c["vefs"])),
                    ("Alça exp.", c["exp"]), ("Alça insp.", c["insp"]),
                    ("PFE", f"{c['pfe']} L/min"), ("FEF₅₀ · FIF₅₀", f"{f1(c['fef'])} · {f1(c['fif'])} L/s"),
                    ("VEF₁ pré", f"{f2(c['vef'])} · {fi(c['vef'] / c['p_vef'] * 100)}% · z {f1(_z_vef(c))}"),
                    ("CVF pré", f"{f2(c['cvf'])} · {fi(c['cvf'] / c['p_cvf'] * 100)}% · z {f1(_z_cvf(c))}"),
                    ("VEF₁ previsto", f"{f2(c['p_vef'])} L"),
                    ("LIN VEF₁/CVF", f2(_lin_razao(c))),
                    ("CPT", "não medida" if c["z_cpt"] is None else f"z {f1(c['z_cpt'])}"),
                    ("VEF₁ pós-BD", "—" if oculto else f"{f2(c['vef_bd'])} L")]
    return c


ESPIROMETRIA = Arvore("espiro", "Espirometria: qual o padrão?",
                      f"{ATS} · qualidade → curva → VEF₁/CVF × LIN → CVF → CPT → gravidade → broncodilatador",
                      "qual", ES_NOS, _gerar_es, [n.id for n in ES_NOS if n.folha],
                      lambda c: [("VEF₁/CVF", f"{f2(_razao(c))} (z {f1(_z_razao(c))})"), ("Empey", f1(_empey(c))),
                                 ("BD", f"+{fi(_bd_pct_prev(c))}% do previsto")], grupo="espiro")
ESPIROMETRIA.nos["qual"].calc = _c_dif
ESPIROMETRIA.nos["alca"].calc = _c_fef
ESPIROMETRIA.nos["razao"].calc = _c_razao
ESPIROMETRIA.nos["bd"].calc = _c_bd

# ================================================================== 2. DPOC: ESPIROMETRIA E GOLD 2026


def _rz_pos(c):
    return c["vef_pos"] / c["cvf_pos"]


def _rz_pre(c):
    return c["vef_pre"] / c["cvf_pre"]


def _vef_pct(c):
    return c["vef_pos"] / c["p_vef"] * 100


def _grau(c):
    p = _vef_pct(c)
    return 0 if p >= 80 else 1 if p >= 50 else 2 if p >= 30 else 3


def _grupo(c):
    if c["exac_mod"] + c["exac_hosp"] >= 1:
        return 2
    return 1 if c["mmrc"] >= 2 or c["caat"] >= 10 else 0


def _c_rz_pos(c):
    v = _rz_pos(c)
    err = [(_rz_pre(c), "usou os valores PRÉ-broncodilatador (o GOLD exige o pós)"),
           (c["cvf_pos"] / c["vef_pos"], "inverteu: é VEF₁ ÷ CVF"),
           (c["vef_pos"] / c["p_vef"], "dividiu pelo VEF₁ previsto")]
    return ("Quanto é o VEF₁/CVF pós-broncodilatador?", v, err,
            f"{f2(c['vef_pos'])} ÷ {f2(c['cvf_pos'])} = {f2(v)}", 2)


def _c_vef_pct(c):
    v = _vef_pct(c)
    err = [(c["vef_pre"] / c["p_vef"] * 100, "usou o VEF₁ pré-broncodilatador"),
           (_rz_pos(c) * 100, "usou a relação VEF₁/CVF como se fosse o % do previsto"),
           (c["p_vef"] / c["vef_pos"] * 100, "inverteu a divisão")]
    return ("Quanto é o VEF₁ pós-BD, em % do previsto?", v, err,
            f"{f2(c['vef_pos'])} ÷ {f2(c['p_vef'])} × 100 = {fi(v)}%", 0)


DP_NOS = [
    No("dx", "VEF₁/CVF pós-BD", "Fumante com sintomas respiratórios. A relação VEF₁/CVF PÓS-broncodilatador é menor que 0,70?",
       [("< 0,70", "DPOC", "grau", None), ("≥ 0,70", "não é DPOC", "f_dp_nao", None)],
       lambda c: 0 if _rz_pos(c) < 0.70 else 1,
       lambda c: (f"Pré-BD {f2(_rz_pre(c))}; pós-BD {f2(_rz_pos(c))}. "
                  + ("Abaixo de 0,70 depois do broncodilatador: obstrução que não reverte." if _rz_pos(c) < 0.70 else
                     "Abaixo de 0,70 só antes do BD: a obstrução reverteu, não é DPOC." if _rz_pre(c) < 0.70 else
                     "Acima de 0,70: sem obstrução."))),
    No("grau", "Grau GOLD", "DPOC confirmada. Qual o grau GOLD (VEF₁ pós-BD em % do previsto)?",
       [("GOLD 1", "≥ 80%", "grupo", "GOLD 1, leve (VEF₁ ≥ 80%)"), ("GOLD 2", "50–79%", "grupo", "GOLD 2, moderada (VEF₁ 50–79%)"),
        ("GOLD 3", "30–49%", "grupo", "GOLD 3, grave (VEF₁ 30–49%)"), ("GOLD 4", "< 30%", "grupo", "GOLD 4, muito grave (VEF₁ < 30%)")],
       _grau,
       lambda c: f"VEF₁ pós-BD {f2(c['vef_pos'])} L ÷ previsto {f2(c['p_vef'])} L = {fi(_vef_pct(c))}%."),
    No("grupo", "Grupo A, B ou E", "Em que grupo? E = ≥ 1 exacerbação moderada ou grave no ano; sem exacerbação, B = mMRC ≥ 2 ou CAAT ≥ 10; senão A",
       [("Grupo A", "0 exac., sintoma leve", "f_dp_a", None),
        ("Grupo B", "0 exac., sintomático", "f_dp_b", None),
        ("Grupo E", "≥ 1 exacerbação", "eos", None)],
       _grupo,
       lambda c: (f"Exacerbações no último ano: {c['exac_mod']} moderada(s), {c['exac_hosp']} com internação; "
                  f"mMRC {c['mmrc']}, CAAT {c['caat']}. "
                  + ("Uma exacerbação já basta para E (GOLD 2026)." if _grupo(c) == 2 else
                     "Sem exacerbação, os sintomas separam A de B."))),
    No("eos", "Eosinófilos", "Grupo E. Os eosinófilos no sangue mandam associar corticoide inalatório?",
       [("≥ 300/µL", "LABA + LAMA + ICS", "f_dp_e_ics", None), ("< 300/µL", "LABA + LAMA", "f_dp_e", None)],
       lambda c: 0 if c["eos"] >= 300 else 1,
       lambda c: f"Eosinófilos {c['eos']}/µL. " + ("A partir de 300, o ICS reduz exacerbações." if c["eos"] >= 300 else
                                                   "Abaixo de 300, o ICS traz mais pneumonia que benefício na largada.")),
    Folha("f_dp_nao", "Não é DPOC", "Não é DPOC: VEF₁/CVF pós-broncodilatador ≥ 0,70",
          "Fumante sintomático sem obstrução: cesse o tabagismo e acompanhe; se o VEF₁ estiver baixo (PRISm), o risco de evoluir para DPOC é alto."),
    Folha("f_dp_a", "Grupo A", "DPOC grupo A: um broncodilatador, de preferência de longa ação",
          "Em todos os grupos: parar de fumar, vacinas (influenza, pneumococo, VSR, covid), técnica inalatória e atividade física."),
    Folha("f_dp_b", "Grupo B", "DPOC grupo B: LABA + LAMA, de preferência num único inalador",
          "A dupla broncodilatação já na largada é melhor que um broncodilatador só. ICS não entra no grupo B."),
    Folha("f_dp_e", "Grupo E", "DPOC grupo E: LABA + LAMA (eosinófilos abaixo de 300)",
          "LABA + ICS sem LAMA não é mais recomendado. Se seguir exacerbando, os eosinófilos guiam o próximo passo."),
    Folha("f_dp_e_ics", "Grupo E + ICS", "DPOC grupo E: LABA + LAMA + ICS (eosinófilos ≥ 300)",
          "Terapia tripla em um inalador. Armadilha: asma junto também indica ICS, qualquer que seja o eosinófilo."),
]


def _gerar_dp(rng, alvo):
    c = {"idade": rng.randint(45, 80), "macos": rng.randint(20, 80), "p_vef": round(rng.uniform(2.4, 3.8), 2),
         "exac_mod": 0, "exac_hosp": 0, "mmrc": 1, "caat": 6, "eos": rng.randint(50, 250)}
    if alvo == "f_dp_nao":
        for _ in range(300):
            c["cvf_pos"] = round(rng.uniform(2.8, 4.5), 2)
            c["vef_pos"] = round(c["cvf_pos"] * rng.uniform(0.72, 0.80), 2)
            if rng.random() < 0.6:                    # armadilha: obstrução só antes do BD
                c["cvf_pre"] = round(c["cvf_pos"] - rng.uniform(0.0, 0.1), 2)
                c["vef_pre"] = round(c["cvf_pre"] * rng.uniform(0.60, 0.67), 2)
            else:
                c["cvf_pre"] = round(c["cvf_pos"] - rng.uniform(0.0, 0.1), 2)
                c["vef_pre"] = round(c["vef_pos"] - rng.uniform(0.02, 0.1), 2)
            if _rz_pos(c) >= 0.715 and c["vef_pre"] < c["vef_pos"]:
                break
    else:
        g = rng.choice([0, 1, 1, 2, 2, 3])
        lo, hi = [(82, 95), (52, 77), (32, 47), (18, 28)][g]
        for _ in range(300):
            c["vef_pos"] = round(c["p_vef"] * rng.uniform(lo, hi) / 100, 2)
            c["cvf_pos"] = round(c["vef_pos"] / rng.uniform(0.35, 0.66), 2)
            c["vef_pre"] = round(c["vef_pos"] - rng.uniform(0.03, 0.15), 2)
            c["cvf_pre"] = round(c["cvf_pos"] - rng.uniform(0.0, 0.15), 2)
            if _grau(c) == g and _rz_pos(c) < 0.685:
                break
        if alvo in ("f_dp_e", "f_dp_e_ics"):
            if rng.random() < 0.5:
                c["exac_mod"] = 1                     # armadilha: uma moderada já é E
            else:
                c["exac_mod"], c["exac_hosp"] = rng.randint(0, 2), rng.randint(1, 2)
            c["mmrc"], c["caat"] = rng.randint(0, 4), rng.randint(5, 30)
            c["eos"] = rng.randint(320, 700) if alvo == "f_dp_e_ics" else rng.randint(50, 280)
        elif alvo == "f_dp_b":
            c["mmrc"], c["caat"] = rng.choice([(rng.randint(2, 4), rng.randint(5, 25)), (rng.randint(0, 1), rng.randint(10, 25))])
            c["eos"] = rng.randint(50, 500)               # sem exacerbação, eos alto não muda a largada
        else:
            c["mmrc"], c["caat"] = rng.randint(0, 1), rng.randint(2, 9)
    c["texto"] = rng.choice(["Ex-tabagista com dispneia aos esforços e tosse matinal.", "Tabagista ativo, tosse com catarro há anos.",
                             "Fumante, cansaço progressivo ao subir escadas."])
    c["mostrar"] = [("Idade · fumo", f"{c['idade']} a · {c['macos']} maços-ano"),
                    ("VEF₁ pré→pós", f"{f2(c['vef_pre'])} → {f2(c['vef_pos'])} L"),
                    ("CVF pré→pós", f"{f2(c['cvf_pre'])} → {f2(c['cvf_pos'])} L"),
                    ("VEF₁ previsto", f"{f2(c['p_vef'])} L"),
                    ("Exacerb./ano", f"{c['exac_mod']} mod. · {c['exac_hosp']} internação"),
                    ("mMRC · CAAT", f"{c['mmrc']} · {c['caat']}"), ("Eosinófilos", f"{c['eos']}/µL")]
    return c


DPOC = Arvore("dpoc", "DPOC: espirometria e GOLD", f"{GOLD} · VEF₁/CVF pós-BD → grau 1–4 → grupo A/B/E → eosinófilos",
              "dx", DP_NOS, _gerar_dp, [n.id for n in DP_NOS if n.folha],
              lambda c: [("VEF₁/CVF pós", f2(_rz_pos(c))), ("VEF₁ pós", f"{fi(_vef_pct(c))}% prev.")], grupo="espiro")
DPOC.nos["dx"].calc = _c_rz_pos
DPOC.nos["grau"].calc = _c_vef_pct

ESPIRO = [ESPIROMETRIA, DPOC]
for _a in ESPIRO:
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None

# ------------------------------------------------------------------ mini-aulas (o porquê de cada passo)
# Molde: a pergunta que a caixa responde → o mecanismo (por quê) → a armadilha da prova.

AULAS = {
    "espiro": {
        "qual": "A espirometria depende do esforço do paciente. Antes de ler, confira se ele repetiu o mesmo sopro: as 2 "
                "maiores CVF e os 2 maiores VEF₁ devem diferir no máximo 150 mL. Exame ruim inventa doença.",
        "curva": "Olhe o desenho antes dos números. Pulmão normal faz pico agudo e descida reta; a asma e a DPOC fazem a "
                 "descida côncava. PLATÔ (alça achatada) é outra coisa: um estreitamento na traqueia ou na laringe limita "
                 "o fluxo. Empey (VEF₁ em mL ÷ PFE) acima de 10 reforça.",
        "alca": "A pressão decide qual alça achata. Fora do tórax, a via aérea fecha ao inspirar (platô inspiratório). Dentro "
                "do tórax, fecha ao expirar (platô expiratório). Lesão rígida achata as duas, e FEF₅₀/FIF₅₀ fica perto de 1.",
        "razao": "Obstrução é a relação VEF₁/CVF abaixo do LIN (z −1,645), não abaixo de 0,70. Com a idade a relação cai "
                 "normalmente: 0,70 fixo superdiagnostica idosos e subdiagnostica jovens. (O GOLD ainda usa 0,70 para DPOC.)",
        "cvf_obs": "Na obstrução a CVF pode cair por dois motivos: ar preso (o pulmão não esvazia) ou restrição junto. A "
                   "espirometria não separa os dois — só a CPT, medida por pletismografia.",
        "cpt_obs": "CPT baixa significa pulmão pequeno: há restrição de verdade junto da obstrução (distúrbio misto). CPT "
                   "normal ou alta significa que a CVF caiu só porque o ar ficou aprisionado.",
        "grav": "A ATS/ERS 2022 gradua pelo z-score do VEF₁, em 3 níveis: leve (acima de −2,5), moderada (−2,5 a −4) e grave "
                "(abaixo de −4). O z diz quantos desvios a pessoa está longe do esperado para idade, sexo e altura.",
        "bd": "Resposta ao broncodilatador agora é calculada sobre o PREVISTO: VEF₁ ou CVF sobe mais de 10% do valor "
              "previsto. Armadilha: o critério antigo (12% e 200 mL sobre o inicial, ainda usado pelo GINA) favorece "
              "quem tem VEF₁ muito baixo.",
        "cvf_nl": "Sem obstrução, olhe a CVF. Normal: espirometria normal. Baixa: o pulmão pode ser pequeno (restrição) ou "
                  "pode ter ar preso ou esforço ruim. Ainda não dá para dizer.",
        "cpt": "Restrição é CPT abaixo do LIN — não CVF baixa. CVF baixa com relação normal e CPT normal é o padrão "
               "inespecífico. Sem CPT, chame de PRISm, nunca de restritivo.",
    },
    "dpoc": {
        "dx": "DPOC é obstrução que NÃO reverte. Por isso o GOLD exige VEF₁/CVF < 0,70 DEPOIS do broncodilatador. Obstrução "
              "que some com o BD não é DPOC, mesmo em fumante.",
        "grau": "O grau GOLD mede a gravidade da obstrução pelo VEF₁ pós-BD em % do previsto: 1 ≥ 80%, 2 de 50 a 79%, "
                "3 de 30 a 49%, 4 < 30%. Ele informa o prognóstico, mas NÃO escolhe o remédio.",
        "grupo": "O remédio inicial é escolhido pelo grupo. Exacerbação no último ano manda para E — desde o GOLD 2026, UMA "
                 "moderada ou grave já basta (antes eram 2 moderadas ou 1 internação). Sem exacerbação, sintomas separam A "
                 "(mMRC 0–1 e CAAT < 10) de B.",
        "eos": "No grupo E, comece com LABA + LAMA. Eosinófilos ≥ 300/µL predizem que o corticoide inalatório reduz "
               "exacerbações: aí já entra a tripla. Abaixo disso, o ICS traz mais pneumonia que benefício.",
    },
}
for _a in ESPIRO:
    for _nid, _txt in AULAS[_a.id].items():
        _a.nos[_nid].aula = _txt
