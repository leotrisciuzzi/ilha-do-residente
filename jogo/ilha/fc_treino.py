"""Modo Treino da farmacologia cardiovascular: casos gerados na hora, infinitos.

O gabarito sai sempre da REGRA ou da CONTA da aula (Cockcroft-Gault, critérios de redução dos DOACs,
CHA2DS2-VA, limites de K⁺/TFG do antagonista mineralocorticoide, critérios da ivabradina, metas de LDL,
creatinina/K⁺ após bloqueio do SRAA, INR da varfarina, dupla antiagregação). O comentário mostra o
raciocínio com os números do enunciado. Cenários em cima de um limiar são re-sorteados.
"""
import random

MATERIA = "Farmacologia cardiovascular"
PREFIXO = "fc-treino"

HABILIDADES = {
    "clcr": ("Clearance de creatinina", "Cockcroft-Gault: (140 − idade) × peso / (72 × Cr) × 0,85 se mulher"),
    "doac": ("Dose do DOAC na FA", "Idade, peso, creatinina e ClCr → dose plena, reduzida ou contraindicado"),
    "chads": ("CHA2DS2-VA", "Somar o escore (ESC 2024) e decidir a anticoagulação"),
    "arm": ("Antagonista mineralocorticoide", "K⁺ e TFG → iniciar, manter, reduzir ou suspender"),
    "sraa": ("Creatinina e K⁺ após IECA/BRA/ARNI", "Até 30% de aumento é esperado; acima, investigar"),
    "ivab": ("Ivabradina: indicada?", "Ritmo sinusal, FC ≥ 70, FE ≤ 35% e betabloqueador otimizado"),
    "alvo": ("Doses-alvo na ICFEr", "As doses dos estudos que mostraram benefício"),
    "ldl": ("Quanto baixar o LDL", "Meta pelo risco → % de redução → estatina, ezetimiba, iPCSK9"),
    "has": ("Anti-hipertensivo por perfil", "Comorbidade → a classe preferida ou a que se deve evitar"),
    "inr": ("INR da varfarina", "INR e sangramento → conduta"),
    "dapt": ("Antiagregação: qual esquema", "Cenário clínico → droga e duração"),
}


def fmt(x, casas=0):
    return f"{x:.{casas}f}".replace(".", ",")


def clcr(idade, peso, cr, sexo):
    v = (140 - idade) * peso / (72 * cr)
    return v * 0.85 if sexo == "F" else v


def _montar(rng, habil, enunciado, certa, erradas, coment):
    erradas = [e for e in dict.fromkeys(erradas) if e != certa][:4]
    alts = [certa] + erradas
    rng.shuffle(alts)
    return {"id": f"{PREFIXO}:{habil}", "enunciado": enunciado, "alts": list(zip("ABCDE", alts)),
            "gab": "ABCDE"[alts.index(certa)], "coment": coment, "materia": MATERIA, "subtema": "",
            "assunto": "", "imgs": [], "prev": 0.5, "origem": "caso gerado", "treino": True}


def _num_alts(rng, certo, passo, fmtf, minimo=None):
    vistos = {fmtf(certo)}
    cand = [certo + k * passo for k in (-3, -2, -1, 1, 2, 3)]
    rng.shuffle(cand)
    out = []
    for v in cand:
        if (minimo is not None and v < minimo) or fmtf(v) in vistos:
            continue
        vistos.add(fmtf(v))
        out.append(fmtf(v))
        if len(out) == 4:
            break
    return fmtf(certo), out


def _pessoa(rng, idade=None):
    sexo = rng.choice("MF")
    idade = idade or rng.randint(45, 92)
    peso = rng.randint(48, 110) if sexo == "M" else rng.randint(42, 95)
    return sexo, idade, peso


def _quem(sexo, idade, peso):
    return f"{'Homem' if sexo == 'M' else 'Mulher'} de {idade} anos, {peso} kg"


# ---------------------------------------------------------------- habilidades

def _q_clcr(rng):
    sexo, idade, peso = _pessoa(rng)
    cr = rng.choice([0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.9, 2.2, 2.6, 3.0])
    v = clcr(idade, peso, cr, sexo)
    certo = round(v)
    certa, erradas = _num_alts(rng, certo, max(4, round(certo * 0.18)), lambda x: f"{fmt(x)} mL/min", minimo=3)
    conta = (f"({140} − {idade}) × {peso} / (72 × {fmt(cr, 1)}) = {fmt((140 - idade) * peso / (72 * cr), 1)}"
             + (" × 0,85 (mulher)" if sexo == "F" else "") + f" ≈ {fmt(certo)} mL/min.")
    return _montar(rng, "clcr", f"{_quem(sexo, idade, peso)}, creatinina {fmt(cr, 1)} mg/dL. Pelo Cockcroft-Gault, o clearance de creatinina estimado é:",
                   certa, erradas,
                   "Cockcroft-Gault (usado nas bulas para ajustar DOACs e outros fármacos): " + conta +
                   " Atenção: a fórmula usa o PESO REAL e não é a TFG do CKD-EPI.")


def _dose_doac(droga, idade, peso, cr, cl):
    """(texto da dose, justificativa)."""
    if droga == "apixabana":
        if cl < 15:
            return "contraindicada (ClCr < 15)", "ClCr < 15 mL/min"
        crit = [n for n, ok in (("idade ≥ 80", idade >= 80), ("peso ≤ 60 kg", peso <= 60), ("creatinina ≥ 1,5", cr >= 1.5)) if ok]
        if len(crit) >= 2:
            return "2,5 mg 2×/dia", "2 critérios: " + " e ".join(crit)
        if cl < 30:
            return "2,5 mg 2×/dia", "ClCr 15–29 mL/min"
        return "5 mg 2×/dia", ("só 1 critério (" + crit[0] + ") — não reduz" if crit else "nenhum critério de redução")
    if droga == "rivaroxabana":
        if cl < 15:
            return "contraindicada (ClCr < 15)", "ClCr < 15 mL/min"
        return ("15 mg 1×/dia", "ClCr 15–49 mL/min") if cl < 50 else ("20 mg 1×/dia", "ClCr ≥ 50 mL/min")
    if droga == "edoxabana":
        if cl < 15:
            return "contraindicada (ClCr < 15)", "ClCr < 15 mL/min"
        if cl <= 50 or peso <= 60:
            return "30 mg 1×/dia", ("ClCr 15–50" if cl <= 50 else "peso ≤ 60 kg")
        return "60 mg 1×/dia", "ClCr > 50 e peso > 60 kg"
    # dabigatrana
    if cl < 30:
        return "contraindicada (ClCr < 30)", "ClCr < 30 mL/min (eliminação ~80% renal)"
    if idade >= 80:
        return "110 mg 2×/dia", "idade ≥ 80 anos"
    return "150 mg 2×/dia", "< 80 anos e ClCr ≥ 30"


_DOSES = {"apixabana": ["5 mg 2×/dia", "2,5 mg 2×/dia", "2,5 mg 1×/dia", "10 mg 2×/dia"],
          "rivaroxabana": ["20 mg 1×/dia", "15 mg 1×/dia", "10 mg 1×/dia", "15 mg 2×/dia"],
          "edoxabana": ["60 mg 1×/dia", "30 mg 1×/dia", "15 mg 1×/dia", "30 mg 2×/dia"],
          "dabigatrana": ["150 mg 2×/dia", "110 mg 2×/dia", "75 mg 2×/dia", "220 mg 1×/dia"]}


def _q_doac(rng):
    for _ in range(200):
        droga = rng.choice(list(_DOSES))
        sexo, idade, peso = _pessoa(rng, rng.randint(62, 92))
        cr = rng.choice([0.8, 1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.1, 2.6, 3.4])
        cl = clcr(idade, peso, cr, sexo)
        lims = {"apixabana": (15, 30), "rivaroxabana": (15, 50), "edoxabana": (15, 50), "dabigatrana": (30,)}[droga]
        if any(abs(cl - x) < 3 for x in lims) or (droga == "edoxabana" and abs(peso - 60) < 2):
            continue
        break
    certa, porque = _dose_doac(droga, idade, peso, cr, cl)
    erradas = [d for d in _DOSES[droga] if d != certa] + (["contraindicada"] if "contra" not in certa else [])
    rng.shuffle(erradas)
    return _montar(rng, "doac", f"{_quem(sexo, idade, peso)}, creatinina {fmt(cr, 1)} mg/dL (ClCr ≈ {fmt(cl)} mL/min), com FA não valvar. A dose de {droga} é:",
                   certa, erradas,
                   f"{droga.capitalize()}: {porque} → {certa}. Regras: apixabana 2,5 mg 2×/dia com 2 de 3 (≥ 80 anos, ≤ 60 kg, Cr ≥ 1,5) ou ClCr 15–29; "
                   "rivaroxabana 15 mg se ClCr 15–49; edoxabana 30 mg se ClCr 15–50 ou ≤ 60 kg; dabigatrana 110 mg se ≥ 80 anos, contraindicada com ClCr < 30. "
                   "Subdose sem critério aumenta AVC.")


_CHADS = [("insuficiência cardíaca", 1), ("hipertensão", 1), ("diabetes", 1), ("AVC/AIT prévio", 2),
          ("doença vascular (IAM prévio ou DAOP)", 1)]


def _q_chads(rng):
    idade = rng.choice([52, 58, 63, 67, 71, 74, 76, 81, 86])
    fat = [f for f in _CHADS if rng.random() < 0.3]
    pts = sum(p for _, p in fat) + (2 if idade >= 75 else 1 if idade >= 65 else 0)
    sexo = rng.choice(["Homem", "Mulher"])
    if pts >= 2:
        certa = f"{pts} pontos — anticoagular (DOAC preferido)"
    elif pts == 1:
        certa = "1 ponto — considerar anticoagulação"
    else:
        certa = "0 ponto — não anticoagular"
    erradas = []
    for v in sorted({pts - 1, pts + 1, pts + 2} - {pts}):
        if v < 0:
            continue
        erradas.append(f"{v} pontos — anticoagular (DOAC preferido)" if v >= 2 else
                       "1 ponto — considerar anticoagulação" if v == 1 else "0 ponto — não anticoagular")
    erradas.append(f"{pts} pontos — AAS em vez de anticoagulante" if pts else "0 ponto — AAS 100 mg/dia")
    erradas.append(f"{pts + (1 if sexo == 'Mulher' else 2)} pontos — anticoagular (DOAC preferido)")
    lista = ", ".join(n for n, _ in fat) or "sem outras comorbidades"
    det = " + ".join([f"{n} ({p})" for n, p in fat] + ([f"idade {idade} ({2 if idade >= 75 else 1})"] if idade >= 65 else [])) or "nada"
    return _montar(rng, "chads", f"{sexo} de {idade} anos com fibrilação atrial não valvar: {lista}. Pelo CHA2DS2-VA, o escore e a conduta são:",
                   certa, erradas,
                   f"CHA2DS2-VA = {det} = {pts}. ESC 2024: sexo não pontua; ≥ 2 → anticoagular; 1 → considerar; 0 → não. "
                   "AAS não substitui o anticoagulante na FA.")


def _q_arm(rng):
    em_uso = rng.random() < 0.55
    for _ in range(100):
        k = round(rng.uniform(3.8, 6.6), 1)
        tfg = rng.choice([18, 24, 28, 35, 42, 55, 68, 80])
        if abs(tfg - 30) < 3 or any(abs(k - x) < 0.05 for x in (5.0, 5.5, 6.0)):
            continue
        break
    if not em_uso:
        ok = k <= 5.0 and tfg > 30
        certa = "iniciar espironolactona 12,5–25 mg/dia" if ok else "não iniciar agora"
        erradas = ["não iniciar agora" if ok else "iniciar espironolactona 12,5–25 mg/dia", "iniciar espironolactona 100 mg/dia",
                   "iniciar e associar cloreto de potássio", "trocar o IECA por espironolactona"]
        motivo = ("K⁺ ≤ 5,0 e TFG > 30" if ok else ("K⁺ > 5,0" if k > 5.0 else "") + (" e " if k > 5.0 and tfg <= 30 else "") +
                  ("TFG ≤ 30" if tfg <= 30 else ""))
        enun = f"Paciente com ICFEr (FE 30%) em IECA e betabloqueador, sem antagonista mineralocorticoide. K⁺ {fmt(k, 1)} mEq/L, TFG {tfg} mL/min. Sobre a espironolactona:"
    else:
        if k > 6.0:
            certa = "suspender a espironolactona"
        elif k > 5.5:
            certa = "reduzir a espironolactona à metade e repetir o K⁺"
        else:
            certa = "manter a dose e monitorar"
        erradas = [x for x in ["suspender a espironolactona", "reduzir a espironolactona à metade e repetir o K⁺",
                               "manter a dose e monitorar", "dobrar a dose", "associar suplemento de potássio"] if x != certa]
        motivo = "K⁺ > 6,0" if k > 6.0 else "K⁺ entre 5,5 e 6,0" if k > 5.5 else "K⁺ ≤ 5,5"
        enun = f"Paciente com ICFEr em espironolactona 25 mg/dia há 3 meses. Controle: K⁺ {fmt(k, 1)} mEq/L, TFG {tfg} mL/min, sem alteração no ECG. A conduta é:"
    return _montar(rng, "arm", enun, certa, erradas,
                   f"{motivo} → {certa}. Regras: iniciar só com K⁺ ≤ 5,0 e TFG > 30; em uso: K⁺ 5,5–6,0 → metade da dose; > 6,0 → suspender. "
                   "Rever sempre AINE, suplemento de K⁺, sal light e trimetoprima.")


def _q_sraa(rng):
    for _ in range(100):
        base = round(rng.uniform(0.8, 1.8), 1)
        aum = rng.choice([0.05, 0.12, 0.2, 0.26, 0.38, 0.45, 0.6, 0.9])
        k = round(rng.uniform(4.0, 6.5), 1)
        nova = round(base * (1 + aum), 1)
        pct = (nova - base) / base * 100
        if abs(pct - 30) < 4 or abs(pct - 50) < 4 or any(abs(k - x) < 0.05 for x in (5.5, 6.0)):
            continue
        break
    droga = rng.choice(["enalapril", "losartana", "sacubitril-valsartana"])
    if pct > 50 or k > 6.0:
        certa = "suspender e investigar a causa (estenose de artéria renal, hipovolemia, AINE)"
        motivo = "aumento > 50%" if pct > 50 else "K⁺ > 6,0"
    elif pct > 30 or k > 5.5:
        certa = "reduzir a dose, rever diurético/AINE/suplementos e repetir em 1–2 semanas"
        motivo = "aumento entre 30% e 50%" if pct > 30 else "K⁺ entre 5,5 e 6,0"
    else:
        certa = "manter a dose: alteração esperada"
        motivo = "aumento ≤ 30% com K⁺ ≤ 5,5"
    erradas = [x for x in ["manter a dose: alteração esperada",
                           "reduzir a dose, rever diurético/AINE/suplementos e repetir em 1–2 semanas",
                           "suspender e investigar a causa (estenose de artéria renal, hipovolemia, AINE)",
                           "associar outro bloqueador do SRAA para proteção renal", "dobrar a dose"] if x != certa]
    return _montar(rng, "sraa", f"Duas semanas após iniciar {droga}, a creatinina foi de {fmt(base, 1)} para {fmt(nova, 1)} mg/dL e o K⁺ é {fmt(k, 1)} mEq/L. A conduta é:",
                   certa, erradas,
                   f"Aumento de {fmt(pct)}% ({motivo}) → {certa.split(':')[0]}. Até ~30% (com K⁺ ≤ 5,5) é queda hemodinâmica da pressão intraglomerular — o benefício de longo prazo se mantém. "
                   "Nunca associar IECA + BRA.")


def _q_ivab(rng):
    for _ in range(100):                    # no máximo UM motivo de contraindicação: pergunta sem ambiguidade
        ritmo = rng.choice(["sinusal", "sinusal", "sinusal", "fibrilação atrial"])
        fc = rng.choice([58, 64, 72, 78, 86, 94])
        fe = rng.choice([25, 30, 33, 40, 48])
        bb = rng.choice(["bisoprolol 10 mg/dia (dose máxima)", "carvedilol 25 mg 2×/dia (dose-alvo)",
                         "carvedilol 3,125 mg 2×/dia, tolerando bem e sem hipotensão"])
        n = (ritmo != "sinusal") + (fc < 70) + (fe > 35) + ("3,125" in bb)
        if n <= 1:
            break
    falhas = []
    if ritmo != "sinusal":
        falhas.append("não está em ritmo sinusal (a ivabradina age no nó sinusal)")
    if fc < 70:
        falhas.append("FC < 70 bpm")
    if fe > 35:
        falhas.append("FE > 35%")
    if "3,125" in bb:
        falhas.append("o betabloqueador ainda não foi titulado (aumente-o primeiro)")
    certa = "indicada para reduzir internação" if not falhas else "não indicada: " + falhas[0]
    erradas = ["indicada para reduzir internação", "não indicada: não está em ritmo sinusal (a ivabradina age no nó sinusal)",
               "não indicada: FC < 70 bpm", "não indicada: FE > 35%",
               "não indicada: o betabloqueador ainda não foi titulado (aumente-o primeiro)", "indicada para substituir o betabloqueador"]
    erradas = [e for e in erradas if e != certa and not (falhas and e.startswith("não indicada") and e[len("não indicada: "):] in falhas)]
    return _montar(rng, "ivab", f"Paciente com IC sintomática, FE {fe}%, ritmo {ritmo}, FC {fc} bpm em repouso, em {bb}, sacubitril-valsartana, espironolactona e dapagliflozina. Sobre a ivabradina:",
                   certa, erradas,
                   "Critérios (SHIFT): ritmo sinusal, FC ≥ 70 apesar de betabloqueador na dose máxima tolerada, FE ≤ 35%, sintomático. "
                   + ("Todos presentes." if not falhas else "Falha: " + "; ".join(falhas) + ".")
                   + " A ivabradina complementa, nunca substitui, o betabloqueador.")


_ALVOS = [("carvedilol (paciente de 70 kg)", "25 mg 2×/dia", ["6,25 mg 2×/dia", "50 mg 1×/dia", "100 mg 2×/dia", "12,5 mg 1×/dia"]),
          ("bisoprolol", "10 mg 1×/dia", ["2,5 mg 1×/dia", "5 mg 2×/dia", "20 mg 1×/dia", "1,25 mg 1×/dia"]),
          ("succinato de metoprolol", "200 mg 1×/dia", ["50 mg 1×/dia", "100 mg 2×/dia", "25 mg 2×/dia", "400 mg 1×/dia"]),
          ("sacubitril-valsartana", "97/103 mg 2×/dia", ["24/26 mg 2×/dia", "49/51 mg 1×/dia", "97/103 mg 1×/dia", "200 mg 2×/dia"]),
          ("enalapril", "10–20 mg 2×/dia", ["2,5 mg 1×/dia", "40 mg 3×/dia", "5 mg 1×/dia", "50 mg 2×/dia"]),
          ("espironolactona", "25–50 mg 1×/dia", ["100–200 mg 1×/dia", "6,25 mg 2×/dia", "12,5 mg 3×/dia", "400 mg 1×/dia"]),
          ("dapagliflozina", "10 mg 1×/dia (sem titulação)", ["5 mg 1×/dia, titulando até 20", "25 mg 1×/dia", "10 mg 2×/dia", "2,5 mg 1×/dia"]),
          ("valsartana", "160 mg 2×/dia", ["40 mg 1×/dia", "320 mg 2×/dia", "80 mg 1×/dia", "20 mg 2×/dia"]),
          ("losartana", "150 mg 1×/dia", ["25 mg 1×/dia", "50 mg 3×/dia", "300 mg 1×/dia", "12,5 mg 1×/dia"]),
          ("ivabradina", "7,5 mg 2×/dia", ["2,5 mg 1×/dia", "15 mg 2×/dia", "5 mg 1×/dia", "10 mg 3×/dia"])]


def _q_alvo(rng):
    droga, certa, erradas = rng.choice(_ALVOS)
    return _montar(rng, "alvo", f"Na insuficiência cardíaca com FE reduzida, a dose-alvo de {droga} é:", certa, list(erradas),
                   f"{droga.capitalize()}: alvo {certa}. Começar baixo e dobrar a cada 2–4 semanas até o alvo ou a máxima tolerada — "
                   "o benefício de mortalidade foi obtido nessas doses. iSGLT2 não se titula.")


_RISCOS = [("muito alto risco (IAM prévio)", 50), ("risco extremo (IAM prévio + novo evento em uso de estatina)", 40),
           ("alto risco (diabetes com lesão de órgão-alvo)", 70), ("risco intermediário", 100)]


def _q_ldl(rng):
    # sorteia primeiro a faixa de redução necessária (as 4 respostas ficam equilibradas), depois o LDL
    faixas = [(12, 26), (34, 46), (54, 61), (69, 82)]
    for _ in range(200):
        nome, meta = rng.choice(_RISCOS)
        lo, hi = rng.choice(faixas)
        nec_alvo = rng.uniform(lo, hi) / 100
        ldl = int(round(meta / (1 - nec_alvo) / 2) * 2)
        nec = (1 - meta / ldl) * 100
        if ldl <= 300 and not any(abs(nec - x) < 3 for x in (30, 50, 65)):
            break
    if nec <= 30:
        certa = "estatina de moderada intensidade"
    elif nec <= 50:
        certa = "estatina de alta intensidade"
    elif nec <= 65:
        certa = "estatina de alta intensidade + ezetimiba"
    else:
        certa = "estatina de alta intensidade + ezetimiba + inibidor de PCSK9"
    erradas = [x for x in ["estatina de moderada intensidade", "estatina de alta intensidade", "estatina de alta intensidade + ezetimiba",
                           "estatina de alta intensidade + ezetimiba + inibidor de PCSK9", "fibrato isolado"] if x != certa]
    return _montar(rng, "ldl", f"Paciente de {nome}, sem tratamento, LDL {ldl} mg/dL. Pela Diretriz Brasileira 2025 (meta < {meta}), a estratégia mínima esperada para atingir a meta é:",
                   certa, erradas,
                   f"Redução necessária = 1 − {meta}/{ldl} = {fmt(nec)}%. Referência: estatina moderada 30–49%, alta ≈ 50%, + ezetimiba ≈ 65%, "
                   "+ iPCSK9 ≈ 85%. Na prática, inicia-se a estatina e reavalia-se em 4–12 semanas.")


_HAS = [
    ("hipertenso com gota recorrente", "losartana", ["hidroclorotiazida", "clortalidona", "furosemida", "indapamida"]),
    ("gestante de 24 semanas com hipertensão crônica", "nifedipina de liberação prolongada ou metildopa", ["enalapril", "losartana", "espironolactona", "aliscireno"]),
    ("diabético com albuminúria de 300 mg/g", "IECA ou BRA", ["hidralazina", "clonidina", "atenolol", "doxazosina"]),
    ("hipertensão resistente em 3 drogas plenas com diurético", "espironolactona", ["clonidina", "atenolol", "hidralazina", "doxazosina"]),
    ("hipertenso com asma grave", "anlodipino (evitar betabloqueador não seletivo)", ["propranolol", "carvedilol", "nadolol", "sotalol"]),
    ("hipertenso com BAV de 2º grau sem marca-passo", "anlodipino", ["verapamil", "diltiazem", "atenolol", "metoprolol"]),
    ("hipertenso com ICFEr (FE 30%)", "sacubitril-valsartana", ["diltiazem", "verapamil", "doxazosina", "moxonidina"]),
    ("hipertenso com hiperplasia prostática sintomática, já em 3 classes de 1ª linha e PA no alvo", "manter e tratar a próstata com tansulosina", ["trocar tudo por doxazosina", "suspender o diurético", "associar clonidina", "associar minoxidil"]),
    ("hipertensa com angioedema prévio por enalapril", "anlodipino ou tiazídico (evitar inibir o SRAA com IECA/ARNI)", ["captopril", "sacubitril-valsartana", "ramipril", "lisinopril"]),
    ("hipertenso com hipocalemia espontânea e HAS resistente", "rastrear hiperaldosteronismo e usar espironolactona", ["aumentar a hidroclorotiazida", "associar furosemida", "associar clonidina", "suspender o potássio da dieta"]),
]


def _q_has(rng):
    perfil, certa, erradas = rng.choice(_HAS)
    return _montar(rng, "has", f"Paciente: {perfil}. A escolha mais adequada é:", certa, list(erradas),
                   f"{perfil.capitalize()} → {certa}. Regras: gota → losartana (tiazídico/alça elevam ácido úrico); gestação → metildopa/nifedipina "
                   "(SRAA é fetotóxico); albuminúria → IECA/BRA; resistente → espironolactona; asma → evitar betabloqueador não seletivo; "
                   "BAV → evitar betabloqueador e verapamil/diltiazem; ICFEr → os pilares; angioedema → nada de IECA/ARNI.")


def _q_inr(rng):
    sang = rng.random() < 0.25
    inr = rng.choice([1.4, 1.7, 2.4, 2.8, 3.6, 4.0, 5.2, 6.8, 8.5, 11.2, 13.0])
    if sang:
        certa = "suspender a varfarina, vitamina K IV e complexo protrombínico"
        enun_s = "com sangramento digestivo volumoso e instabilidade"
    else:
        enun_s = "sem sangramento"
        if inr < 2:
            certa = "aumentar a dose semanal em ~10–15% e repetir o INR"
        elif inr <= 3:
            certa = "manter a dose"
        elif inr <= 4.5:
            certa = "reduzir a dose ou omitir uma tomada e repetir o INR"
        elif inr <= 10:
            certa = "suspender 1–2 doses e reavaliar (vitamina K oral se alto risco de sangramento)"
        else:
            certa = "suspender e dar vitamina K oral (2,5–5 mg)"
    todas = ["aumentar a dose semanal em ~10–15% e repetir o INR", "manter a dose",
             "reduzir a dose ou omitir uma tomada e repetir o INR",
             "suspender 1–2 doses e reavaliar (vitamina K oral se alto risco de sangramento)",
             "suspender e dar vitamina K oral (2,5–5 mg)", "suspender a varfarina, vitamina K IV e complexo protrombínico"]
    erradas = [x for x in todas if x != certa]
    rng.shuffle(erradas)
    return _montar(rng, "inr", f"Paciente em varfarina por FA (alvo 2–3), INR {fmt(inr, 1)}, {enun_s}. A conduta é:",
                   certa, erradas,
                   f"INR {fmt(inr, 1)} {enun_s} → {certa}. Faixas: < 2 aumentar; 2–3 manter; 3–4,5 reduzir/omitir; 4,5–10 suspender doses; "
                   "> 10 vitamina K oral; sangramento grave com qualquer INR → vitamina K IV + complexo protrombínico (plasma se não houver).")


_DAPT = [
    ("SCA com angioplastia, 60 anos, sem alto risco de sangramento nem AVC prévio", "AAS + ticagrelor (ou prasugrel) por 12 meses",
     ["AAS + clopidogrel por 1 mês", "AAS isolado", "AAS + ticagrelor por 3 anos obrigatoriamente", "rivaroxabana isolada"]),
    ("IAM com supra tratado com alteplase, 64 anos", "AAS + clopidogrel",
     ["AAS + prasugrel", "AAS + ticagrelor com ataque de 180 mg", "AAS isolado", "clopidogrel isolado"]),
    ("SCA com angioplastia em paciente com AVC isquêmico prévio", "AAS + ticagrelor (prasugrel contraindicado)",
     ["AAS + prasugrel 10 mg", "AAS + prasugrel 5 mg", "prasugrel isolado", "nenhum antiplaquetário"]),
    ("angioplastia eletiva por angina estável", "AAS + clopidogrel por 6 meses, depois AAS",
     ["AAS + ticagrelor por 12 meses", "AAS + prasugrel por 12 meses", "clopidogrel por 1 semana", "rivaroxabana + AAS por 5 anos"]),
    ("FA em apixabana que fez angioplastia com stent", "apixabana + clopidogrel (AAS só até ~1 semana)",
     ["apixabana + AAS + ticagrelor por 12 meses", "AAS + clopidogrel sem anticoagulante", "varfarina + AAS + prasugrel", "apixabana isolada desde o dia 1"]),
    ("SCA com angioplastia e alto risco de sangramento (anemia, DRC avançada)", "DAPT curta (1–3 meses) e depois monoterapia com P2Y12",
     ["DAPT com prasugrel por 24 meses", "terapia tripla por 12 meses", "nenhum antiplaquetário", "AAS em dose de 500 mg/dia"]),
]


def _q_dapt(rng):
    cen, certa, erradas = rng.choice(_DAPT)
    return _montar(rng, "dapt", f"Cenário: {cen}. O esquema antitrombótico mais adequado é:", certa, list(erradas),
                   f"{cen.capitalize()} → {certa}. Regras: SCA → 12 meses, ticagrelor/prasugrel preferidos; fibrinólise → clopidogrel; AVC/AIT prévio → "
                   "sem prasugrel; DAC estável → clopidogrel 6 meses; com anticoagulante → anticoagulante + clopidogrel; alto sangramento → encurtar.")


_FUNC = {"clcr": _q_clcr, "doac": _q_doac, "chads": _q_chads, "arm": _q_arm, "sraa": _q_sraa, "ivab": _q_ivab,
         "alvo": _q_alvo, "ldl": _q_ldl, "has": _q_has, "inr": _q_inr, "dapt": _q_dapt}


def questao(rng, habil):
    return _FUNC[habil](rng)


def taxa_erro(save, habil):
    s = save.stat(f"{PREFIXO}:{habil}")
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
