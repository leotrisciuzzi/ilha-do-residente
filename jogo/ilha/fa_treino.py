"""Modo Treino dos antibióticos: casos gerados na hora, infinitos.

Cada habilidade sorteia de uma TABELA da aula (germe → droga que cobre, efeito → droga, síndrome → duração,
cenário → empírico...) ou calcula pela regra (CURB-65, gravidade do C. difficile). As alternativas erradas
são escolhas plausíveis que NÃO satisfazem a regra (droga que não cobre o germe, duração de outra síndrome).
"""
import random

MATERIA = "Antibióticos"
PREFIXO = "fa-treino"

HABILIDADES = {
    "cobre": ("Quem cobre esse germe?", "Germe → antibiótico que funciona (e os que falham)"),
    "toxi": ("Toxicidade → droga", "Efeito adverso típico → antibiótico responsável"),
    "renal": ("Ajuste renal", "ClCr baixo: quem precisa e quem não precisa ajustar"),
    "gesta": ("Antibiótico na gestação", "Seguro × evitar"),
    "curb": ("CURB-65 e local de tratamento", "Somar o escore pelo caso e decidir"),
    "duracao": ("Quanto tempo tratar", "Síndrome → duração recomendada"),
    "pkpd": ("PK/PD", "Tempo-dependente × concentração-dependente"),
    "empirico": ("Empírico por cenário", "Síndrome + risco → esquema"),
    "alergia": ("Alergia a betalactâmico", "Tipo de reação → o que pode usar"),
    "interacao": ("Interações", "Antibiótico + outra droga → o que acontece"),
    "cdiff": ("C. difficile pela gravidade", "Episódio e gravidade → tratamento"),
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


# ---------------------------------------------------------------- tabelas

_COBRE = [
    ("MRSA", "vancomicina", ["oxacilina", "cefazolina", "ceftriaxona", "meropenem", "amoxicilina-clavulanato"],
     "PBP2a: nenhum betalactâmico clássico age (só a ceftarolina)."),
    ("Pseudomonas aeruginosa", "piperacilina-tazobactam", ["ceftriaxona", "ertapenem", "amoxicilina-clavulanato", "cefazolina", "oxacilina"],
     "Antipseudomonas: pipe-tazo, cefepime, ceftazidima, meropenem/imipenem, cipro/levofloxacino, aminoglicosídeo. Ceftriaxona e ertapenem não."),
    ("Listeria monocytogenes", "ampicilina", ["ceftriaxona", "cefepime", "ceftazidima", "cefazolina", "oxacilina"],
     "Nenhuma cefalosporina cobre Listeria. Alternativa à ampicilina: SMX-TMP."),
    ("Enterococcus faecalis", "ampicilina", ["ceftriaxona", "cefepime", "cefazolina", "ceftazidima", "oxacilina"],
     "Cefalosporinas não cobrem enterococo. Endocardite: ampicilina + ceftriaxona (sinergia)."),
    ("Mycoplasma pneumoniae", "azitromicina", ["amoxicilina", "ceftriaxona", "cefalexina", "meropenem", "oxacilina"],
     "Sem parede celular: betalactâmicos não agem. Macrolídeo, doxiciclina ou quinolona respiratória."),
    ("Bacteroides fragilis (anaeróbio abdominal)", "metronidazol", ["ceftriaxona", "cefepime", "ciprofloxacino", "gentamicina", "vancomicina IV"],
     "Anaeróbios abaixo do diafragma: metronidazol, pipe-tazo, carbapenêmico, amoxi-clav."),
    ("Rickettsia rickettsii (febre maculosa)", "doxiciclina", ["ceftriaxona", "amoxicilina", "cefalexina", "gentamicina", "oxacilina"],
     "Intracelular: doxiciclina para todas as idades nas formas graves."),
    ("Pneumocystis jirovecii", "sulfametoxazol-trimetoprima", ["ceftriaxona", "azitromicina", "vancomicina", "amoxicilina", "meropenem"],
     "SMX-TMP trata e previne pneumocistose (+ corticoide se PaO₂ < 70)."),
    ("Stenotrophomonas maltophilia", "sulfametoxazol-trimetoprima", ["meropenem", "imipenem", "ceftriaxona", "ertapenem", "cefazolina"],
     "Intrinsecamente resistente a carbapenêmicos (metalo-betalactamase L1)."),
    ("Treponema pallidum", "penicilina benzatina", ["ciprofloxacino", "gentamicina", "metronidazol", "nitrofurantoína", "vancomicina"],
     "Penicilina é a droga da sífilis; gestante alérgica dessensibiliza."),
    ("E. coli ESBL em bacteremia", "meropenem", ["ceftriaxona", "cefepime", "amoxicilina-clavulanato", "ampicilina", "cefazolina"],
     "ESBL hidrolisa cefalosporinas até a 4ª geração; MERINO: carbapenêmico é superior a pipe-tazo."),
    ("Pasteurella multocida (mordedura de gato)", "amoxicilina-clavulanato", ["cefalexina", "clindamicina", "oxacilina", "vancomicina", "metronidazol"],
     "Pasteurella é resistente a cefalexina, clindamicina e oxacilina isoladas."),
    ("Legionella pneumophila", "levofloxacino", ["ceftriaxona", "amoxicilina", "cefazolina", "vancomicina", "oxacilina"],
     "Intracelular: quinolona respiratória ou azitromicina."),
    ("Klebsiella produtora de KPC", "ceftazidima-avibactam", ["meropenem", "ertapenem", "ceftriaxona", "piperacilina-tazobactam", "cefepime"],
     "KPC hidrolisa carbapenêmicos; o avibactam (e vaborbactam, relebactam) a inibe."),
]

_TOXI = [
    ("ruptura de tendão e risco de aneurisma/dissecção de aorta", "levofloxacino"),
    ("ototoxicidade irreversível e nefrotoxicidade", "gentamicina"),
    ("plaquetopenia após 2 semanas e síndrome serotoninérgica com ISRS", "linezolida"),
    ("rubor em face e tronco durante infusão rápida", "vancomicina"),
    ("hipercalemia e aumento da creatinina sem lesão renal", "sulfametoxazol-trimetoprima"),
    ("gosto metálico, neuropatia periférica e efeito antabuse", "metronidazol"),
    ("elevação de CPK e falha no tratamento de pneumonia", "daptomicina"),
    ("pseudolitíase biliar e precipitação com cálcio no recém-nascido", "ceftriaxona"),
    ("queda do nível de valproato com convulsões", "meropenem"),
    ("fotossensibilidade, esofagite e manchas dentárias na criança", "doxiciclina"),
    ("maior risco de colite por C. difficile", "clindamicina"),
    ("encefalopatia e mioclonia na insuficiência renal", "cefepime"),
    ("fibrose pulmonar no uso prolongado e hemólise na deficiência de G6PD", "nitrofurantoína"),
    ("hepatite e interação por indução enzimática (anticoncepcional, varfarina)", "rifampicina"),
]
_TOXI_DROGAS = sorted({d for _, d in _TOXI})

_SEM_AJUSTE = ["ceftriaxona", "oxacilina", "clindamicina", "doxiciclina", "azitromicina", "linezolida", "moxifloxacino", "metronidazol"]
_COM_AJUSTE = ["vancomicina", "gentamicina", "piperacilina-tazobactam", "meropenem", "cefepime", "sulfametoxazol-trimetoprima",
               "aciclovir", "levofloxacino", "amicacina", "ampicilina"]

_GESTA_OK = ["cefalexina", "amoxicilina", "azitromicina", "ceftriaxona", "nitrofurantoína (longe do termo)", "clindamicina", "fosfomicina",
             "penicilina benzatina"]
_GESTA_EVITAR = ["ciprofloxacino", "levofloxacino", "doxiciclina", "gentamicina", "tetraciclina", "sulfametoxazol-trimetoprima no 1º trimestre"]

_DURACAO = [
    ("cistite não complicada tratada com nitrofurantoína", "5 dias"),
    ("cistite não complicada tratada com fosfomicina", "dose única"),
    ("pielonefrite em mulher tratada com ciprofloxacino, boa resposta", "7 dias"),
    ("PAC estável e afebril há 48 h", "5 dias"),
    ("bacteremia por E. coli de foco urinário, controlada", "7 dias"),
    ("bacteremia por S. aureus não complicada (eco normal, hemocultura negativa em 72 h)", "14 dias"),
    ("endocardite de valva nativa por S. aureus (MSSA)", "4–6 semanas"),
    ("osteomielite sem ressecção do osso infectado", "6 semanas"),
    ("celulite não purulenta com melhora", "5–6 dias"),
    ("meningite meningocócica", "7 dias"),
    ("ITU febril em homem com suspeita de prostatite", "10–14 dias"),
    ("pneumonia associada à ventilação mecânica com boa resposta", "7 dias"),
    ("sífilis latente tardia (penicilina benzatina)", "3 doses semanais"),
]
_DURS = sorted({d for _, d in _DURACAO})

_PKPD = [("piperacilina-tazobactam", "tempo-dependente (infusão prolongada ajuda)"),
         ("meropenem", "tempo-dependente (infusão prolongada ajuda)"),
         ("cefepime", "tempo-dependente (infusão prolongada ajuda)"),
         ("oxacilina", "tempo-dependente (infusão prolongada ajuda)"),
         ("gentamicina", "concentração-dependente (dose única diária)"),
         ("amicacina", "concentração-dependente (dose única diária)"),
         ("levofloxacino", "concentração-dependente (dose única diária)"),
         ("daptomicina", "concentração-dependente (dose única diária)"),
         ("vancomicina", "dependente da AUC/CIM (alvo 400–600)")]
_PK_OPC = ["tempo-dependente (infusão prolongada ajuda)", "concentração-dependente (dose única diária)", "dependente da AUC/CIM (alvo 400–600)",
           "independente da dose", "dependente só do volume de distribuição"]

_EMP = [
    ("PAC ambulatorial, 30 anos, sem comorbidade", "amoxicilina", ["meropenem", "ceftriaxona + vancomicina", "ciprofloxacino", "piperacilina-tazobactam"]),
    ("PAC em enfermaria, 72 anos, DPOC, sem risco de Pseudomonas", "ceftriaxona + azitromicina", ["amoxicilina isolada", "meropenem + vancomicina", "ciprofloxacino isolado", "clindamicina"]),
    ("pneumonia associada à ventilação, antibiótico IV há 10 dias", "meropenem + vancomicina", ["ceftriaxona + azitromicina", "amoxicilina-clavulanato", "ertapenem", "levofloxacino isolado"]),
    ("neutropenia febril estável, sem foco", "cefepime", ["ceftriaxona", "vancomicina isolada", "amoxicilina oral", "azitromicina"]),
    ("meningite bacteriana em adulto de 70 anos", "ceftriaxona + vancomicina + ampicilina (+ dexametasona)", ["ceftriaxona isolada", "meropenem + fluconazol", "penicilina cristalina", "aciclovir isolado"]),
    ("peritonite secundária comunitária após controle cirúrgico", "ceftriaxona + metronidazol", ["vancomicina", "azitromicina", "amoxicilina", "fluconazol"]),
    ("celulite não purulenta sem sinais sistêmicos", "cefalexina", ["SMX-TMP isolado", "ciprofloxacino", "vancomicina IV", "meropenem"]),
    ("fasciite necrosante com choque (após cirurgia)", "meropenem + vancomicina + clindamicina", ["cefalexina", "ceftriaxona isolada", "doxiciclina", "azitromicina"]),
    ("uretrite gonocócica não complicada", "ceftriaxona 500 mg IM + azitromicina 1 g VO", ["ciprofloxacino 500 mg", "amoxicilina 3 g", "penicilina benzatina", "doxiciclina isolada por 3 dias"]),
    ("cistite em mulher não gestante", "nitrofurantoína", ["ciprofloxacino por 14 dias", "ceftriaxona IM", "meropenem", "amoxicilina por 1 dia"]),
]

_ALERGIA = [
    ("rash maculopapular leve na infância com amoxicilina, há 25 anos; precisa de cefazolina profilática", "usar cefazolina",
     ["usar vancomicina", "contraindicar todo betalactâmico", "dessensibilizar antes", "usar clindamicina"]),
    ("anafilaxia com penicilina; precisa de antibiótico para pielonefrite por Pseudomonas", "aztreonam (sem reatividade cruzada)",
     ["piperacilina-tazobactam", "amoxicilina", "ampicilina", "oxacilina"]),
    ("Stevens-Johnson com amoxicilina; precisa tratar celulite", "evitar betalactâmicos e usar clindamicina ou doxiciclina",
     ["cefalexina", "amoxicilina com corticoide", "dessensibilizar à amoxicilina", "teste de provocação com penicilina"]),
    ("gestante com sífilis e anafilaxia à penicilina", "dessensibilizar e usar penicilina benzatina",
     ["ceftriaxona", "azitromicina", "doxiciclina", "eritromicina"]),
    ("urticária imediata com penicilina há 2 anos; precisa de carbapenêmico para ESBL", "usar meropenem (reatividade cruzada < 1%)",
     ["contraindicar carbapenêmicos", "usar ceftriaxona", "usar amoxicilina-clavulanato", "usar ertapenem só após dessensibilizar"]),
]

_INTER = [
    ("claritromicina + sinvastatina", "rabdomiólise (inibição do CYP3A4)"),
    ("linezolida + sertralina", "síndrome serotoninérgica"),
    ("metronidazol + varfarina", "aumento do INR e sangramento"),
    ("meropenem + valproato", "queda do valproato e convulsões"),
    ("rifampicina + anticoncepcional oral", "falha contraceptiva por indução enzimática"),
    ("SMX-TMP + espironolactona", "hipercalemia"),
    ("levofloxacino + carbonato de cálcio", "redução da absorção da quinolona"),
    ("claritromicina + colchicina", "toxicidade da colchicina"),
    ("vancomicina + piperacilina-tazobactam", "mais lesão renal aguda"),
]
_INTER_EFEITOS = sorted({e for _, e in _INTER})


# ---------------------------------------------------------------- habilidades

def _q_cobre(rng):
    germe, certa, erradas, porque = rng.choice(_COBRE)
    return _montar(rng, "cobre", f"Antibiótico ativo contra {germe}:", certa, list(erradas),
                   f"{germe}: {certa}. {porque}")


def _q_toxi(rng):
    efeito, certa = rng.choice(_TOXI)
    erradas = [d for d in _TOXI_DROGAS if d != certa]
    return _montar(rng, "toxi", f"Efeito adverso típico — {efeito}. O antibiótico responsável é:", certa, erradas,
                   f"{efeito.capitalize()} → {certa}.")


def _q_renal(rng):
    clcr = rng.choice([12, 18, 22, 25])
    if rng.random() < 0.5:
        certa = rng.choice(_SEM_AJUSTE)
        erradas = rng.sample(_COM_AJUSTE, 6)
        enun = f"Paciente com clearance de creatinina de {clcr} mL/min. Qual antibiótico NÃO precisa de ajuste de dose?"
    else:
        certa = rng.choice(_COM_AJUSTE)
        erradas = rng.sample(_SEM_AJUSTE, 6)
        enun = f"Paciente com clearance de creatinina de {clcr} mL/min. Qual antibiótico PRECISA de ajuste de dose?"
    return _montar(rng, "renal", enun, certa, erradas,
                   "Sem ajuste: ceftriaxona, oxacilina, clindamicina, doxiciclina, azitromicina, linezolida, moxifloxacino, metronidazol. "
                   "Com ajuste: vancomicina e aminoglicosídeos (com nível sérico), pipe-tazo, meropenem, cefepime, SMX-TMP, aciclovir, levofloxacino, ampicilina.")


def _q_gesta(rng):
    if rng.random() < 0.5:
        certa = rng.choice(_GESTA_OK)
        erradas = rng.sample(_GESTA_EVITAR, 5)
        enun = "Gestante de 14 semanas precisa de antibiótico. Qual é considerado seguro?"
    else:
        certa = rng.choice(_GESTA_EVITAR)
        erradas = rng.sample(_GESTA_OK, 6)
        enun = "Gestante de 14 semanas precisa de antibiótico. Qual deve ser EVITADO?"
    return _montar(rng, "gesta", enun, certa, erradas,
                   "Seguros: penicilinas, cefalosporinas, azitromicina, clindamicina, fosfomicina, nitrofurantoína (evitar perto do termo). "
                   "Evitar: quinolonas (cartilagem), tetraciclinas (dente/osso), aminoglicosídeos (ototoxicidade fetal), SMX-TMP no 1º trimestre e no termo.")


def _q_curb(rng):
    idade = rng.choice([38, 52, 61, 66, 72, 81])
    conf = rng.random() < 0.3
    ureia = rng.choice([28, 36, 44, 58, 72, 96])
    fr = rng.choice([18, 22, 26, 31, 34])
    pas, pad = rng.choice([(128, 78), (118, 70), (100, 58), (86, 54), (134, 82)])
    pts = conf + (ureia > 50) + (fr >= 30) + (pas < 90 or pad <= 60) + (idade >= 65)
    local = ("ambulatorial (se condição social e sem hipoxemia)" if pts <= 1 else
             "internação em enfermaria" if pts == 2 else "internação, avaliar UTI (pneumonia grave)")
    certa = f"{pts} — {local}"
    def loc(v):
        return ("ambulatorial (se condição social e sem hipoxemia)" if v <= 1 else
                "internação em enfermaria" if v == 2 else "internação, avaliar UTI (pneumonia grave)")
    outros = sorted((v for v in range(6) if v != pts), key=lambda v: abs(v - pts))[:3]
    erradas = [f"{v} — {loc(v)}" for v in outros]
    erradas += [f"{pts} — {l}" for l in ("ambulatorial (se condição social e sem hipoxemia)", "internação em enfermaria",
                                         "internação, avaliar UTI (pneumonia grave)") if l != local][:1]
    itens = [n for n, ok in (("confusão", conf), (f"ureia {ureia} > 50", ureia > 50), (f"FR {fr} ≥ 30", fr >= 30),
                             (f"PA {pas}×{pad}", pas < 90 or pad <= 60), (f"idade {idade} ≥ 65", idade >= 65)) if ok]
    return _montar(rng, "curb", f"PAC em paciente de {idade} anos, {'confuso' if conf else 'orientado'}, ureia {ureia} mg/dL, FR {fr} irpm, "
                   f"PA {pas}×{pad} mmHg, SpO₂ 95% em ar ambiente. CURB-65 e local de tratamento:", certa, erradas,
                   f"CURB-65 = {len(itens)}" + (f" ({', '.join(itens)})" if itens else "") + f" → {local}. "
                   "0–1 ambulatorial; 2 enfermaria; ≥ 3 grave. Hipoxemia, comorbidade descompensada ou falta de suporte social mudam o local.")


def _q_duracao(rng):
    sind, certa = rng.choice(_DURACAO)
    erradas = [d for d in _DURS if d != certa]
    return _montar(rng, "duracao", f"Duração recomendada do antibiótico: {sind}.", certa, erradas,
                   f"{sind.capitalize()}: {certa}. Cursos curtos são a regra (PAC 5, pielonefrite/Gram-negativo 7); longos para S. aureus na "
                   "corrente sanguínea (≥ 14), endocardite (4–6 semanas) e osso (6 semanas).")


def _q_pkpd(rng):
    droga, certa = rng.choice(_PKPD)
    return _montar(rng, "pkpd", f"Do ponto de vista farmacodinâmico, {droga} é:", certa, [o for o in _PK_OPC if o != certa],
                   f"{droga}: {certa}. Betalactâmicos: tempo acima da CIM. Aminoglicosídeos, quinolonas e daptomicina: pico/CIM "
                   "ou AUC (dose única diária). Vancomicina: AUC/CIM.")


def _q_empirico(rng):
    cen, certa, erradas = rng.choice(_EMP)
    return _montar(rng, "empirico", f"Cenário: {cen}. Esquema empírico adequado:", certa, list(erradas),
                   f"{cen.capitalize()} → {certa}. Amplie o espectro só pelo risco (internação/antibiótico recente, colonização, gravidade) "
                   "e descalone com as culturas.")


def _q_alergia(rng):
    cen, certa, erradas = rng.choice(_ALERGIA)
    return _montar(rng, "alergia", f"Paciente com {cen}. Conduta:", certa, list(erradas),
                   f"{certa.capitalize()}. Reação leve e remota: risco mínimo (cefazolina tem cadeia lateral única). Anafilaxia: aztreonam não cruza "
                   "(exceto com ceftazidima); carbapenêmico < 1%. SJS/DRESS: evitar a classe. Sífilis na gestante: só penicilina.")


def _q_interacao(rng):
    par, certa = rng.choice(_INTER)
    return _montar(rng, "interacao", f"Associação {par}. O risco principal é:", certa, [e for e in _INTER_EFEITOS if e != certa],
                   f"{par}: {certa}.")


def _q_cdiff(rng):
    tipo = rng.choice(["1º episódio leve", "1º episódio grave", "fulminante", "1ª recorrência", "2ª recorrência"])
    leuc = {"1º episódio leve": 9800, "1º episódio grave": 18500, "fulminante": 26000}.get(tipo, rng.choice([9000, 12000]))
    cr = {"1º episódio leve": 0.9, "1º episódio grave": 1.8, "fulminante": 2.4}.get(tipo, 1.0)
    extra = {"fulminante": ", hipotensão e distensão com íleo", "1ª recorrência": "; tratado com vancomicina oral há 6 semanas, voltou a ter diarreia",
             "2ª recorrência": "; já teve dois episódios tratados (vancomicina e fidaxomicina)"}.get(tipo, "")
    certa = {"1º episódio leve": "fidaxomicina (ou vancomicina oral) por 10 dias",
             "1º episódio grave": "fidaxomicina (ou vancomicina oral) por 10 dias",
             "fulminante": "vancomicina oral/retal em dose alta + metronidazol IV e avaliação cirúrgica",
             "1ª recorrência": "fidaxomicina (ou vancomicina oral em esquema prolongado/regressivo)",
             "2ª recorrência": "transplante de microbiota fecal (após curso de vancomicina/fidaxomicina)"}[tipo]
    todas = ["fidaxomicina (ou vancomicina oral) por 10 dias", "vancomicina oral/retal em dose alta + metronidazol IV e avaliação cirúrgica",
             "fidaxomicina (ou vancomicina oral em esquema prolongado/regressivo)", "transplante de microbiota fecal (após curso de vancomicina/fidaxomicina)",
             "vancomicina intravenosa", "loperamida e observação", "metronidazol oral como primeira escolha"]
    erradas = [x for x in todas if x != certa and not (tipo.startswith("1º") and x == todas[0])]
    if tipo.startswith("1º"):
        erradas = [x for x in erradas if x != todas[2]]
    return _montar(rng, "cdiff", f"Colite por C. difficile — {tipo}: leucócitos {leuc}/mm³, creatinina {fmt(cr, 1)} mg/dL{extra}. Tratamento:",
                   certa, erradas,
                   "IDSA/SHEA 2021: 1º episódio (grave = leucócitos ≥ 15 mil ou Cr > 1,5) → fidaxomicina ou vancomicina ORAL; fulminante (choque, íleo, "
                   "megacólon) → vancomicina oral/retal 500 mg 6/6 h + metronidazol IV ± cirurgia; recorrência → fidaxomicina ou vanco prolongada; "
                   "múltiplas recorrências → microbiota fecal. Vancomicina IV não chega ao cólon.")


_FUNC = {"cobre": _q_cobre, "toxi": _q_toxi, "renal": _q_renal, "gesta": _q_gesta, "curb": _q_curb, "duracao": _q_duracao,
         "pkpd": _q_pkpd, "empirico": _q_empirico, "alergia": _q_alergia, "interacao": _q_interacao, "cdiff": _q_cdiff}


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
