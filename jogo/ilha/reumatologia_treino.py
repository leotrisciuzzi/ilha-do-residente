"""Modo Treino da reumatologia: casos gerados na hora, infinitos.

Cada habilidade sorteia um caso e calcula o gabarito pela REGRA da aula (critérios de classificação,
cortes de laboratório, tabelas de associação e de conduta). Nada de gabarito escrito à mão: o comentário
mostra a conta ou a regra aplicada aos dados do enunciado.

Regras: ACR/EULAR 2010 (artrite reumatoide), EULAR/ACR 2019 (lúpus), cortes clássicos do líquido sinovial,
ACR 2020 (gota), Jones revisado AHA 2015 para população de risco moderado/alto (Brasil), SBC/SBP 2009
(duração da profilaxia), ASAS (lombalgia inflamatória), AHA 2017/2024 (Kawasaki)."""
import random

MATERIA = "Reumatologia"
PREFIXO = "reu-treino"

HABILIDADES = {
    "ar2010": ("Critérios de artrite reumatoide", "Some os pontos ACR/EULAR 2010: 6 ou mais classifica"),
    "les2019": ("Critérios de lúpus", "FAN de entrada, maior item por domínio, 10 pontos com um clínico"),
    "liquido": ("Líquido sinovial", "Leucócitos, neutrófilos e cristais: o que é esta monoartrite?"),
    "anticorpo": ("Anticorpo e doença", "Qual doença ou achado cada autoanticorpo anuncia"),
    "gota": ("Gota: tratar o urato?", "Indicação do hipouricemiante e meta de urato"),
    "jones": ("Critérios de Jones", "Febre reumática em população de risco moderado ou alto"),
    "profilaxia": ("Profilaxia da febre reumática", "Até quando a penicilina benzatina"),
    "vasculite": ("Qual vasculite?", "Idade, vaso e pista de ouro"),
    "lombalgia": ("Lombalgia inflamatória", "Os 5 parâmetros da ASAS: 4 ou mais"),
    "kawasaki": ("Kawasaki", "Dias de febre e critérios: completo, incompleto ou outra causa"),
}


def _montar(rng, habil, enunciado, certa, erradas, coment):
    erradas = [e for e in dict.fromkeys(erradas) if e != certa][:4]
    alts = [certa] + erradas
    rng.shuffle(alts)
    return {"id": f"{PREFIXO}:{habil}", "enunciado": enunciado, "alts": list(zip("ABCDE", alts)),
            "gab": "ABCDE"[alts.index(certa)], "coment": coment, "materia": MATERIA, "subtema": "",
            "assunto": "", "imgs": [], "prev": 0.5, "origem": "caso gerado", "treino": True}


def _vizinhos(rng, n, lo, hi, k=4):
    """k valores próximos de n (distintos de n) dentro de [lo, hi], os mais perto primeiro, embaralhados."""
    cand = sorted((v for v in range(lo, hi + 1) if v != n), key=lambda v: (abs(v - n), rng.random()))[:k]
    rng.shuffle(cand)
    return cand


def _pessoa(rng, idade_min=18, idade_max=70, sexo=None):
    sexo = sexo or rng.choice("MF")
    return sexo, rng.randint(idade_min, idade_max)


def _quem(sexo, idade):
    return f"{'Homem' if sexo == 'M' else 'Mulher'} de {idade} anos"


# ---------------------------------------------------------------- 1. artrite reumatoide 2010

def pontos_ar(grandes, pequenas, soro, fase_aguda, semanas):
    if grandes + pequenas > 10 and pequenas >= 1:
        art = 5
    elif 4 <= pequenas <= 10:
        art = 3
    elif 1 <= pequenas <= 3:
        art = 2
    elif 2 <= grandes <= 10:
        art = 1
    else:
        art = 0
    sor = {"negativos": 0, "positivo baixo": 2, "positivo alto": 3}[soro]
    return art, sor, int(fase_aguda), int(semanas >= 6)


def _q_ar2010(rng):
    while True:
        grandes = rng.choice([0, 0, 1, 2, 3, 4])
        pequenas = rng.choice([0, 1, 2, 3, 4, 6, 8, 10, 12])
        if grandes + pequenas:
            break
    soro = rng.choice(["negativos", "positivo baixo", "positivo alto"])
    fase = rng.random() < 0.6
    semanas = rng.choice([3, 4, 5, 6, 8, 12, 20])
    a, s, f, d = pontos_ar(grandes, pequenas, soro, fase, semanas)
    tot = a + s + f + d
    sexo, idade = _pessoa(rng, 25, 70)
    sor_txt = {"negativos": "fator reumatoide e anti-CCP negativos",
               "positivo baixo": "anti-CCP positivo até 3 vezes o limite superior",
               "positivo alto": "anti-CCP positivo mais de 3 vezes o limite superior"}[soro]
    juntas = []
    if pequenas:
        juntas.append(f"{pequenas} articulação(ões) pequena(s) (MCF, IFP, punhos ou MTF)")
    if grandes:
        juntas.append(f"{grandes} articulação(ões) grande(s)")
    en = (f"{_quem(sexo, idade)} com sinovite em {' e '.join(juntas)} há {semanas} semanas, {sor_txt}, "
          f"{'PCR elevada' if fase else 'PCR e VHS normais'}. Sem outra doença que explique. Pelos critérios ACR/EULAR 2010:")

    def txt(n):
        return f"{n} pontos: {'classifica' if n >= 6 else 'não classifica'} como artrite reumatoide"
    certa = txt(tot)
    erradas = [txt(n) for n in _vizinhos(rng, tot, 0, 10)]
    coment = (f"Articulações {a} + sorologia {s} + fase aguda {f} + duração {d} = {tot}. "
              f"{'Com 6 ou mais pontos, classifica.' if tot >= 6 else 'Abaixo de 6, não classifica (reavaliar com o tempo).'} "
              "Lembre: mais de 10 articulações com ao menos uma pequena vale 5; 4 a 10 pequenas vale 3; 1 a 3 pequenas vale 2; "
              "2 a 10 grandes vale 1.")
    return _montar(rng, "ar2010", en, certa, erradas, coment)


# ---------------------------------------------------------------- 2. lúpus 2019

_LES = [  # (domínio, item, pontos, clínico?)
    ("constitucional", "febre acima de 38,3 °C", 2, True),
    ("hematológico", "leucopenia abaixo de 4.000/mm³", 3, True),
    ("hematológico", "plaquetopenia abaixo de 100.000/mm³", 4, True),
    ("hematológico", "anemia hemolítica autoimune", 4, True),
    ("neuropsiquiátrico", "delirium", 2, True),
    ("neuropsiquiátrico", "psicose", 3, True),
    ("neuropsiquiátrico", "convulsão", 5, True),
    ("mucocutâneo", "alopecia não cicatricial", 2, True),
    ("mucocutâneo", "úlceras orais", 2, True),
    ("mucocutâneo", "lúpus cutâneo subagudo ou discoide", 4, True),
    ("mucocutâneo", "lúpus cutâneo agudo (eritema malar)", 6, True),
    ("serosas", "derrame pleural ou pericárdico", 5, True),
    ("serosas", "pericardite aguda", 6, True),
    ("musculoesquelético", "artrite em 2 ou mais articulações", 6, True),
    ("renal", "proteinúria acima de 0,5 g/24 h", 4, True),
    ("renal", "nefrite classe II ou V na biópsia", 8, True),
    ("renal", "nefrite classe III ou IV na biópsia", 10, True),
    ("antifosfolípides", "anticardiolipina ou anticoagulante lúpico positivo", 2, False),
    ("complemento", "C3 ou C4 baixo (só um)", 3, False),
    ("complemento", "C3 e C4 baixos", 4, False),
    ("anticorpos específicos", "anti-DNA de dupla hélice ou anti-Sm", 6, False),
]


def pontos_les(itens):
    por_dom = {}
    for dom, _, p, _ in itens:
        por_dom[dom] = max(por_dom.get(dom, 0), p)
    return sum(por_dom.values()), any(c for *_, c in itens)


def _q_les2019(rng):
    fan = rng.random() < 0.85
    itens = rng.sample(_LES, rng.randint(2, 5))
    tot, clinico = pontos_les(itens)
    sexo, idade = _pessoa(rng, 16, 45, sexo="F" if rng.random() < 0.85 else "M")
    en = (f"{_quem(sexo, idade)} com {', '.join(i[1] for i in itens)}. FAN em HEp-2 "
          f"{'1:320, homogêneo' if fan else 'negativo'}. Pelos critérios EULAR/ACR 2019:")
    if not fan:
        certa = "não classifica: falta o critério de entrada (FAN 1:80 ou mais)"
        erradas = [f"{tot} pontos: classifica como lúpus", f"{tot + 2} pontos: classifica como lúpus",
                   f"{max(0, tot - 3)} pontos: não classifica", "classifica, porque o anti-DNA dispensa o FAN"]
        coment = "Sem FAN igual ou maior que 1:80 em HEp-2, a classificação não começa, qualquer que seja a soma."
    else:
        ok = tot >= 10 and clinico

        def txt(n):
            return f"{n} pontos: {'classifica' if n >= 10 and clinico else 'não classifica'} como lúpus"
        certa = txt(tot)
        soma_bruta = sum(i[2] for i in itens)              # erro típico: somar dois itens do mesmo domínio
        erradas = ([txt(soma_bruta)] if soma_bruta != tot else []) + [txt(n) for n in _vizinhos(rng, tot, 0, 40)]
        por_dom = {}
        for dom, nome, p, _ in itens:
            if p > por_dom.get(dom, (0, ""))[0]:
                por_dom[dom] = (p, nome)
        conta = " + ".join(f"{p} ({dom})" for dom, (p, _) in por_dom.items())
        coment = (f"Conta-se só o maior item de cada domínio: {conta} = {tot}. "
                  + ("Com 10 ou mais pontos e item clínico, classifica." if ok else
                     "Não chega a 10 pontos com item clínico: não classifica.")
                  + (" Atenção: dois itens do mesmo domínio não se somam." if len(por_dom) < len(itens) else ""))
    return _montar(rng, "les2019", en, certa, erradas, coment)


# ---------------------------------------------------------------- 3. líquido sinovial

_LIQ = ["não inflamatório: osteoartrite ou trauma", "inflamatório por gota",
        "inflamatório por pirofosfato de cálcio (pseudogota)",
        "inflamatório sem cristais: artrite reumatoide ou espondiloartrite",
        "séptico: tratar como artrite infecciosa"]


def _q_liquido(rng):
    tipo = rng.choice(["nao", "gota", "ppc", "infl", "septico", "septico_cristal"])
    if tipo == "nao":
        leuc, pmn, cristal, gram = rng.randint(200, 1800), rng.randint(5, 25), "ausentes", "negativo"
        certa = _LIQ[0]
    elif tipo == "septico" or tipo == "septico_cristal":
        leuc, pmn = rng.randint(55, 180) * 1000, rng.randint(85, 98)
        cristal = "cristais em agulha com birrefringência negativa" if tipo == "septico_cristal" else "ausentes"
        gram = rng.choice(["cocos Gram-positivos em cachos", "negativo"])
        certa = _LIQ[4]
    else:
        leuc, pmn = rng.randint(4, 45) * 1000, rng.randint(50, 80)
        gram = "negativo"
        cristal = {"gota": "cristais em agulha com birrefringência negativa forte",
                   "ppc": "cristais romboides com birrefringência positiva fraca", "infl": "ausentes"}[tipo]
        certa = {"gota": _LIQ[1], "ppc": _LIQ[2], "infl": _LIQ[3]}[tipo]
    sexo, idade = _pessoa(rng, 25, 85)
    milhar = f"{leuc:,}".replace(",", ".")
    cr = "cristais ausentes" if cristal == "ausentes" else cristal
    en = (f"{_quem(sexo, idade)} com monoartrite aguda de joelho. Líquido sinovial: {milhar} leucócitos/mm³, "
          f"{pmn}% de neutrófilos, {cr}, Gram {gram}. A interpretação é:")
    coment = ("Cortes: abaixo de 2.000 leucócitos é não inflamatório; de 2.000 a 50.000 é inflamatório (o cristal diz "
              "qual); acima de 50.000 com neutrófilos, ou Gram positivo, é séptico até prova em contrário. ")
    if tipo == "septico_cristal":
        coment += "Aqui há cristal de urato, mas com contagem séptica: cristal não exclui infecção, e a cultura manda."
    elif tipo == "ppc":
        coment += "Romboide com birrefringência positiva fraca é pirofosfato; agulha negativa forte seria urato."
    elif tipo == "gota":
        coment += "Agulha com birrefringência negativa forte é urato, a gota."
    return _montar(rng, "liquido", en, certa, [x for x in _LIQ if x != certa], coment)


# ---------------------------------------------------------------- 4. anticorpo e doença

_ANTICORPOS = [
    ("anti-CCP", "artrite reumatoide, com maior risco de erosão"),
    ("anti-DNA de dupla hélice", "lúpus ativo, com risco de nefrite"),
    ("anti-Sm", "lúpus, com alta especificidade"),
    ("anti-histona", "lúpus induzido por drogas"),
    ("anti-Ro (SSA)", "Sjögren e lúpus neonatal com bloqueio cardíaco congênito"),
    ("anti-U1RNP em título alto", "doença mista do tecido conjuntivo"),
    ("anticentrômero", "esclerose sistêmica limitada, com hipertensão pulmonar tardia"),
    ("anti-Scl-70 (topoisomerase I)", "esclerose sistêmica difusa com doença intersticial"),
    ("anti-RNA polimerase III", "esclerose sistêmica difusa com crise renal"),
    ("anti-Jo-1", "síndrome antissintetase"),
    ("anti-MDA5", "dermatomiosite amiopática com pneumopatia rapidamente progressiva"),
    ("anti-TIF1-gama", "dermatomiosite do adulto associada a câncer"),
    ("anti-HMGCR", "miopatia necrosante após estatina"),
    ("c-ANCA anti-PR3", "granulomatose com poliangiite"),
    ("p-ANCA anti-MPO", "poliangiite microscópica"),
    ("anti-P ribossomal", "psicose lúpica"),
    ("anticoagulante lúpico", "síndrome antifosfolípide, com trombose e perda gestacional"),
]


def _q_anticorpo(rng):
    ac, certa = rng.choice(_ANTICORPOS)
    erradas = [d for a, d in _ANTICORPOS if a != ac]
    rng.shuffle(erradas)
    modelo = rng.choice(["Qual associação é a mais característica do {}?", "Paciente com {} positivo. O anticorpo aponta para:",
                         "O {} é o marcador clássico de:"])
    coment = f"{ac[0].upper() + ac[1:]} → {certa}. Associações de prova: veja a pílula 'Anticorpo e doença'."
    return _montar(rng, "anticorpo", modelo.format(ac), certa, erradas, coment)


# ---------------------------------------------------------------- 5. gota

_G_CERTO = {
    "alvo5": "iniciar alopurinol em dose baixa e subir até urato abaixo de 5 mg/dL",
    "alvo6": "iniciar alopurinol em dose baixa e subir até urato abaixo de 6 mg/dL",
    "considerar": "pode-se considerar hipouricemiante (indicação condicional), com meta abaixo de 6 mg/dL",
    "nao": "não iniciar hipouricemiante: tratar a crise e orientar fatores de risco",
    "assint": "não tratar: hiperuricemia sem gota não tem indicação de hipouricemiante",
}


def _q_gota(rng):
    while True:
        crises = rng.choice([0, 1, 1, 2, 3, 4])
        tofo = rng.random() < 0.3
        dano = rng.random() < 0.25
        urato = rng.choice([6.8, 7.4, 8.2, 8.9, 9.6, 10.5])
        drc = rng.random() < 0.25
        lito = rng.random() < 0.15
        if crises == 0 and (tofo or dano):
            continue
        break
    if crises == 0:
        chave = "assint"
    elif tofo:
        chave = "alvo5"
    elif dano or crises >= 2:
        chave = "alvo6"
    elif drc or urato > 9 or lito:
        chave = "considerar"
    else:
        chave = "nao"
    sexo, idade = _pessoa(rng, 35, 75, sexo="M" if rng.random() < 0.8 else "F")
    partes = [f"urato sérico de {str(urato).replace('.', ',')} mg/dL"]
    partes.append("nenhuma crise de artrite até hoje" if crises == 0 else
                  f"{crises} crise(s) de gota nos últimos 12 meses")
    if tofo:
        partes.append("tofos em cotovelos")
    if dano:
        partes.append("erosões gotosas no raio X")
    if drc:
        partes.append("doença renal crônica estágio 3")
    if lito:
        partes.append("cálculos renais de ácido úrico")
    en = f"{_quem(sexo, idade)}, fora de crise, com {', '.join(partes)}. A conduta sobre o urato é:"
    erradas = [v for k, v in _G_CERTO.items() if k != chave] + ["iniciar alopurinol só após 4 crises por ano"]
    regra = {"assint": "Hiperuricemia assintomática não se trata com hipouricemiante (ACR 2020).",
             "alvo5": "Tofo é indicação forte; com tofos, a meta da EULAR é urato abaixo de 5 mg/dL.",
             "alvo6": "Duas ou mais crises por ano ou dano radiográfico são indicação forte; meta abaixo de 6 mg/dL.",
             "considerar": "Uma crise só, mas com doença renal 3 ou mais, urato acima de 9 ou litíase: indicação condicional.",
             "nao": "Uma crise isolada sem fator agravante: em geral não se inicia hipouricemiante ainda."}[chave]
    coment = regra + " O alopurinol começa com 100 mg/dia ou menos, com profilaxia anti-inflamatória por 3 a 6 meses."
    return _montar(rng, "gota", en, _G_CERTO[chave], erradas, coment)


# ---------------------------------------------------------------- 6. Jones (risco moderado/alto)

def _q_jones(rng):
    """Brasil = população de risco moderado/alto (AHA 2015)."""
    maiores_pool = ["cardite com insuficiência mitral no ecocardiograma", "poliartrite migratória de grandes articulações",
                    "monoartrite de joelho", "coreia de Sydenham", "eritema marginado", "nódulos subcutâneos"]
    menores_pool = ["febre de 38,2 °C", "VHS de 70 mm/h", "intervalo PR prolongado no ECG", "monoartralgia de tornozelo"]
    while True:
        nM = rng.choice([0, 1, 1, 2])
        nm = rng.choice([0, 1, 2, 3])
        M = rng.sample(maiores_pool, nM)
        m = rng.sample(menores_pool, nm)
        artic_M = any("artrite" in x for x in M)
        if artic_M and "monoartralgia de tornozelo" in m:
            continue                     # articulação não conta como maior e menor
        if any("cardite" in x for x in M) and "intervalo PR prolongado no ECG" in m:
            continue                     # PR não conta se a cardite já é maior
        if sum("artrite" in x for x in M) > 1:
            continue
        break
    coreia_so = M == ["coreia de Sydenham"]
    estrep = coreia_so and rng.random() < 0.5 or rng.random() < 0.8
    ok = coreia_so or (estrep and (len(M) >= 2 or (len(M) == 1 and len(m) >= 2)))
    sexo, idade = _pessoa(rng, 6, 15)
    en = (f"{'Menino' if sexo == 'M' else 'Menina'} de {idade} anos, morador de região de risco moderado ou alto, com "
          f"{', '.join(M + m) if M + m else 'apenas dor de garganta há 3 semanas'}. "
          f"{'ASLO elevado' if estrep else 'ASLO normal e cultura de orofaringe negativa'}. Pelos critérios de Jones (2015):")
    certa = "fecha o diagnóstico de febre reumática" if ok else "não fecha o diagnóstico de febre reumática"
    erradas = ["fecha o diagnóstico de febre reumática" if not ok else "não fecha o diagnóstico de febre reumática",
               "só fecha com cardite", "exige dois critérios maiores obrigatoriamente", "exige cultura de orofaringe positiva"]
    if coreia_so:
        coment = "A coreia isolada basta para o diagnóstico, mesmo sem prova de infecção, porque surge tarde."
    else:
        coment = (f"{len(M)} maior(es) e {len(m)} menor(es), {'com' if estrep else 'sem'} prova de infecção estreptocócica. "
                  "Primeiro surto: 2 maiores, ou 1 maior e 2 menores, sempre com prova de infecção recente. "
                  "Em risco moderado ou alto, monoartrite conta como maior e monoartralgia como menor.")
    return _montar(rng, "jones", en, certa, erradas, coment)


# ---------------------------------------------------------------- 7. profilaxia secundária

def fim_profilaxia(idade, cat):
    if cat == 0:
        return f"até os {max(21, idade + 5)} anos"
    if cat == 1:
        return f"até os {max(25, idade + 10)} anos"
    return "até os 40 anos ou por toda a vida" if idade < 40 else "por toda a vida"


def _q_profilaxia(rng):
    cat = rng.choice([0, 0, 1, 2])
    idade = rng.randint(6, 30)
    desc = ["sem cardite", "com cardite leve que regrediu, sem lesão residual importante",
            "com lesão valvar residual moderada (insuficiência mitral moderada)"][cat]
    en = (f"Paciente teve o último surto de febre reumática aos {idade} anos, {desc}. "
          "Até quando manter a penicilina benzatina?")
    certa = fim_profilaxia(idade, cat)
    erradas = [f"até os {n} anos" for n in sorted({21, 25, 18, idade + 5, idade + 10, max(21, idade + 5),
                                                     max(25, idade + 10), 30}) if f"até os {n} anos" != certa]
    erradas += ["por toda a vida", "por 1 ano após o surto", "até os 40 anos ou por toda a vida"]
    rng.shuffle(erradas)
    regra = ["sem cardite: até 21 anos ou 5 anos após o último surto, o que for mais longo",
             "cardite leve resolvida: até 25 anos ou 10 anos após o último surto, o que for mais longo",
             "lesão residual moderada ou grave: até os 40 anos ou por toda a vida"][cat]
    coment = f"Regra ({regra}). Surto aos {idade} anos → {certa}."
    return _montar(rng, "profilaxia", en, certa, erradas, coment)


# ---------------------------------------------------------------- 8. qual vasculite

_VASC = [
    ("arterite de células gigantes", ["idade acima de 50 anos", "cefaleia temporal nova", "claudicação de mandíbula",
                                       "sinal do halo no ultrassom", "VHS acima de 50 mm/h"]),
    ("arterite de Takayasu", ["mulher de 24 anos", "pulso radial ausente à esquerda", "diferença de 25 mmHg entre os braços",
                              "claudicação de membro superior"]),
    ("granulomatose com poliangiite", ["sinusite crônica com nariz em sela", "nódulos pulmonares cavitados", "c-ANCA anti-PR3",
                                       "glomerulonefrite pauci-imune"]),
    ("poliangiite microscópica", ["hemorragia alveolar", "glomerulonefrite rapidamente progressiva", "p-ANCA anti-MPO",
                                  "ausência de granulomas na biópsia"]),
    ("granulomatose eosinofílica com poliangiite", ["asma de início na vida adulta", "eosinofilia de 20%", "mononeurite múltipla",
                                                    "infiltrados pulmonares migratórios"]),
    ("poliarterite nodosa", ["hepatite B", "microaneurismas renais", "orquite", "ANCA negativo e pulmão poupado"]),
    ("vasculite por IgA (Henoch-Schönlein)", ["criança de 6 anos", "púrpura palpável em nádegas", "plaquetas normais",
                                              "dor abdominal em cólica"]),
    ("doença de Kawasaki", ["criança de 2 anos", "febre há 6 dias", "conjuntivite sem secreção", "língua em framboesa"]),
    ("crioglobulinemia mista", ["hepatite C", "púrpura com artralgia e fraqueza", "C4 muito baixo", "fator reumatoide positivo"]),
    ("doença de Behçet", ["úlceras orais recorrentes", "úlceras genitais", "uveíte", "teste de patergia positivo"]),
]


def _q_vasculite(rng):
    nome, pistas = rng.choice(_VASC)
    usar = rng.sample(pistas, 3)
    en = f"Quadro com {', '.join(usar)}. A vasculite mais provável é:"
    erradas = [n for n, _ in _VASC if n != nome]
    rng.shuffle(erradas)
    coment = f"Pistas de {nome}: {', '.join(pistas)}."
    return _montar(rng, "vasculite", en, nome, erradas, coment)


# ---------------------------------------------------------------- 9. lombalgia inflamatória (ASAS)

_ASAS = [("início antes dos 40 anos", "início após os 50 anos"),
         ("início insidioso", "início súbito após carregar peso"),
         ("melhora com exercício", "piora com exercício"),
         ("não melhora com repouso", "melhora com repouso"),
         ("dor à noite que melhora ao levantar", "dor apenas no fim do dia")]


def _q_lombalgia(rng):
    tem = [rng.random() < 0.6 for _ in _ASAS]
    n = sum(tem)
    achados = [s if t else nao for (s, nao), t in zip(_ASAS, tem)]
    rng.shuffle(achados)
    sexo, idade = _pessoa(rng, 22, 60)
    en = f"{_quem(sexo, idade)} com lombalgia há 6 meses: {', '.join(achados)}. Pelos critérios da ASAS, a dor é:"
    certa = (f"inflamatória: {n} de 5 parâmetros" if n >= 4 else f"não preenche lombalgia inflamatória: {n} de 5 parâmetros")
    erradas = [f"inflamatória: {k} de 5 parâmetros" for k in range(6) if k != n] + \
              [f"não preenche lombalgia inflamatória: {k} de 5 parâmetros" for k in range(6) if k != n]
    rng.shuffle(erradas)
    coment = (f"Parâmetros presentes: {n}. A ASAS define dor inflamatória com 4 ou mais de 5: início antes dos 40, "
              "insidioso, melhora com exercício, não melhora com repouso e dor noturna que melhora ao levantar.")
    return _montar(rng, "lombalgia", en, certa, erradas, coment)


# ---------------------------------------------------------------- 10. Kawasaki

_KAW = ["conjuntivite bilateral sem secreção", "lábios fissurados e língua em framboesa", "exantema polimorfo",
        "edema e eritema de mãos e pés", "linfonodo cervical de 2 cm"]
_K_CERTO = ["Kawasaki completo: imunoglobulina venosa 2 g/kg e AAS",
            "possível Kawasaki incompleto: PCR, VHS, exames e ecocardiograma",
            "Kawasaki improvável por ora: buscar outra causa da febre"]


def _q_kawasaki(rng):
    dias = rng.randint(5, 8)
    n = rng.choice([0, 1, 2, 3, 4, 5])
    crit = rng.sample(_KAW, n)
    idade = rng.choice(["8 meses", "1 ano", "2 anos", "3 anos", "4 anos"])
    en = (f"Criança de {idade} com febre há {dias} dias" + (f" e {', '.join(crit)}" if crit else ", sem outros achados")
          + ". A interpretação e a conduta são:")
    certa = _K_CERTO[0] if n >= 4 else _K_CERTO[1] if n >= 2 else _K_CERTO[2]
    erradas = [x for x in _K_CERTO if x != certa] + ["escarlatina: penicilina benzatina", "AAS isolado sem imunoglobulina"]
    coment = (f"Febre de {dias} dias com {n} de 5 critérios. Com 4 ou mais, é Kawasaki completo. Com 2 ou 3, pensa-se em "
              "Kawasaki incompleto e se usam laboratório e ecocardiograma (AHA). A imunoglobulina previne aneurisma coronário.")
    return _montar(rng, "kawasaki", en, certa, erradas, coment)


_FUNC = {"ar2010": _q_ar2010, "les2019": _q_les2019, "liquido": _q_liquido, "anticorpo": _q_anticorpo,
         "gota": _q_gota, "jones": _q_jones, "profilaxia": _q_profilaxia, "vasculite": _q_vasculite,
         "lombalgia": _q_lombalgia, "kawasaki": _q_kawasaki}


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
