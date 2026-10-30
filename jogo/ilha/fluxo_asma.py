"""Fluxogramas da asma pelo GINA 2026 (Global Strategy for Asthma Management and Prevention, maio de 2026).

Cinco árvores, no mesmo molde das de gasometria (fluxo_dados): nós com regra aplicada aos números do caso,
geradores por folha-alvo, contas no nível 2+, mini-aula por caixa.

  1. Diagnóstico ............ Box 1-1 (fluxograma) e Box 1-2 (critérios de variabilidade)
  2. Tratamento inicial ..... Box 4-5 (por onde começar) e Box 4-6 (Track 1 e Track 2)
  3. Consulta de controle ... Box 2-2 (controle em 4 perguntas), p.81 (o que corrigir antes de subir), Box 4-13
  4. Crise ................... Box 9-6 (pronto-socorro) e Box 9-4 (atenção primária)
  5. Asma grave ............. Box 8-2 a 8-5 (difícil × grave, tipo 2, escolha e resposta ao biológico)

Os limiares vêm do texto do GINA 2026; onde o GINA não dá número (ex.: "função pulmonar baixa" no Box 4-5),
os geradores fogem da zona cinzenta em vez de inventar um corte."""
from .fluxo_dados import Arvore, Folha, No, f1, f2, fi

GINA = "GINA 2026"


def _alts_inteiras(certo, erros, maximo=4):
    """Erros como inteiros distintos de 0 a `maximo`; completa com vizinhos se faltar."""
    out, vistos = [], {certo}
    for v, por in erros:
        if 0 <= v <= maximo and v not in vistos:
            vistos.add(v)
            out.append((v, por))
    for v in range(maximo + 1):
        if len(out) >= 3:
            break
        if v not in vistos:
            vistos.add(v)
            out.append((v, "errou a contagem"))
    return out


# ================================================================== 1. DIAGNÓSTICO (Box 1-1, 1-2)

def _bd_ml(c):
    return round((c["vef_pos"] - c["vef_pre"]) * 1000)


def _bd_pct(c):
    return (c["vef_pos"] - c["vef_pre"]) / c["vef_pre"] * 100


def _bd_pos(c):
    return _bd_pct(c) >= 12 and _bd_ml(c) >= 200


def _var_pos(c):
    return (c["pfe_var"] or 0) > 10 or (c["meta"] or 0) >= 20


def _c_bd(c):
    v = _bd_pct(c)
    d = c["vef_pos"] - c["vef_pre"]
    err = [(d / c["vef_pos"] * 100, "dividiu pelo VEF₁ DEPOIS do broncodilatador (a base é o de antes)"),
           (c["vef_pos"] / c["vef_pre"] * 100, "não tirou os 100% da linha de base"),
           (d * 100, "usou a diferença em litros como se fosse porcentagem")]
    form = (f"({f2(c['vef_pos'])} − {f2(c['vef_pre'])}) ÷ {f2(c['vef_pre'])} × 100 = {fi(v)}%; "
            f"em volume: +{_bd_ml(c)} mL")
    return "Quanto o VEF₁ subiu depois do broncodilatador, em %?", v, err, form, 0


DX_NOS = [
    No("tipico", "Sintomas típicos?", "Sintomas respiratórios crônicos ou recorrentes. A história é típica de asma?",
       [("Típica", "variável, noturna, com gatilho", "espiro", None),
        ("Atípica", "outro padrão", "alt", None)],
       lambda c: 0 if c["tipico"] else 1,
       lambda c: f"Padrão: {c['padrao']}. " + ("Sintomas que vão e voltam, à noite e com gatilho, são o retrato da asma."
                                               if c["tipico"] else "Sintoma fixo, sem variação nem gatilho, não é o padrão da asma.")),
    No("alt", "Outro diagnóstico?", "História atípica: investigue diagnósticos alternativos. Algum foi confirmado?",
       [("Confirmado", "achou outra causa", "f_dx_alt", None),
        ("Não confirmado", "volta a pensar em asma", "espiro", "outros diagnósticos investigados e afastados")],
       lambda c: 0 if c["alt"] else 1,
       lambda c: f"Investigação: {c['alt'] or 'nenhum diagnóstico alternativo confirmado'}."),
    No("espiro", "Tem espirometria?", "É preciso provar a obstrução variável. Há espirometria ou medidor de PFE?",
       [("Disponível", "prova antes e após o BD", "bd", None), ("Indisponível", "sem prova de função", "biomarc", None)],
       lambda c: 0 if c["espiro"] else 1,
       lambda c: "Espirometria disponível: prove a variabilidade ANTES de começar o corticoide." if c["espiro"] else
                 "Sem espirometria nem PFE na unidade."),
    No("bd", "Prova broncodilatadora", "Prova com 400 mcg de salbutamol. O VEF₁ subiu ≥ 12% E ≥ 200 mL?",
       [("Positiva", "≥ 12% e ≥ 200 mL", "f_dx_asma", None), ("Negativa", "não cumpriu os dois", "variab", None)],
       lambda c: 0 if _bd_pos(c) else 1,
       lambda c: (f"VEF₁ {f2(c['vef_pre'])} → {f2(c['vef_pos'])} L: +{_bd_ml(c)} mL = +{fi(_bd_pct(c))}%. "
                  + ("Cumpriu os dois critérios." if _bd_pos(c) else
                     "Passou dos 12% mas não dos 200 mL: em pulmão pequeno a % engana." if _bd_pct(c) >= 12 else
                     "Abaixo de 12%."))),
    No("variab", "Outra variabilidade?", "Prova negativa não exclui asma. Outro teste mostrou variabilidade excessiva?",
       [("Sim", "PFE > 10% ou metacolina ≥ 20%", "f_dx_asma", "variabilidade provada por outro teste"),
        ("Não", "todos negativos", "f_dx_nao", None)],
       lambda c: 0 if _var_pos(c) else 1,
       lambda c: (f"Variação diária do PFE: {fi(c['pfe_var']) + '%' if c['pfe_var'] is not None else 'não feita'} (asma se > 10%); "
                  f"metacolina: {'queda de ' + fi(c['meta']) + '%' if c['meta'] is not None else 'não feita'} (asma se ≥ 20%).")),
    No("biomarc", "Biomarcadores", "Sem prova de função. FeNO ou eosinófilos ajudam?",
       [("Elevados", "FeNO > 50 ou eos altos", "empirico", "biomarcador tipo 2 elevado reforçando a hipótese"),
        ("Normais", "não excluem asma", "empirico", None)],
       lambda c: 0 if c["feno"] > 50 or c["eos"] > 500 else 1,
       lambda c: f"FeNO {fi(c['feno'])} ppb, eosinófilos {fi(c['eos'])}/µL. Altos APOIAM asma tipo 2; normais NÃO a excluem."),
    No("empirico", "Resposta ao ICS", "Outros diagnósticos improváveis: tratou com ICS. Melhorou em 1–3 meses?",
       [("Melhorou", "sintomas e função", "f_dx_asma_emp", None), ("Não melhorou", "questione o diagnóstico", "f_dx_encaminhar", None)],
       lambda c: 0 if c["melhorou"] else 1,
       lambda c: "Após 2 meses de corticoide inalatório: " + ("melhora clara dos sintomas." if c["melhorou"] else "sem mudança.")),
    Folha("f_dx_asma", "Asma confirmada", "Asma confirmada por limitação variável ao fluxo expiratório",
          "Registre o exame no prontuário ANTES de iniciar o ICS: com tratamento a variabilidade some e a confirmação fica difícil."),
    Folha("f_dx_alt", "Outro diagnóstico", "Não é asma: tratar o diagnóstico alternativo confirmado",
          "Sintoma fixo e sem variação aponta para outra causa: obstrução laríngea induzível, DPOC, bronquiectasia, IC, tosse por IECA."),
    Folha("f_dx_nao", "Não confirmada", "Asma não confirmada: repetir os testes durante sintomas, sem broncodilatador, ou outros testes",
          "Prova negativa fora de crise (ou logo após usar bombinha) não exclui asma: suspenda SABA 4 h e LABA 24–48 h e repita."),
    Folha("f_dx_asma_emp", "Asma provável", "Asma provável, tratada empiricamente com ICS (respondeu em 1–3 meses)",
          "Sem espirometria, ICS empírico é aceitável se outras causas são improváveis; confirme com PFE ou espirometria assim que der."),
    Folha("f_dx_encaminhar", "Encaminhar", "Sem resposta ao ICS empírico: encaminhar para avaliação especializada",
          "Não aumente a dose às cegas: falta de resposta ao corticoide põe o diagnóstico de asma em dúvida."),
]

_TIPICO = ["varia, pior à noite", "pior no exercício", "piora com resfriado"]
_ATIPICO = [("tosse fixa c/ enalapril", "tosse por IECA"), ("estridor, sem chiado", "obstrução laríngea"),
            ("catarro diário, fumante", "DPOC (VEF₁/CVF < 0,7)")]
_ATIPICO_NEG = ["dispneia fixa", "tosse sem variação"]


def _gerar_dx(rng, alvo):
    c = {"idade": rng.randint(18, 60), "tipico": True, "padrao": rng.choice(_TIPICO), "alt": None, "espiro": True,
         "vef_pre": 0.0, "vef_pos": 0.0, "pfe_var": None, "meta": None, "feno": rng.randint(10, 35),
         "eos": rng.randint(100, 350), "melhorou": None}
    if alvo == "f_dx_alt":
        c["tipico"] = False
        c["padrao"], c["alt"] = rng.choice(_ATIPICO)
        texto = "Adulto com queixa respiratória que não se comporta como asma."
    else:
        if rng.random() < 0.25:                       # atípico em que a investigação veio negativa
            c["tipico"], c["padrao"] = False, rng.choice(_ATIPICO_NEG)
        texto = rng.choice(["Jovem com crises de chiado desde a adolescência.", "Mulher de meia-idade com tosse e chiado recorrentes.",
                            "Adulto que nunca teve diagnóstico, com falta de ar episódica."])
    if alvo in ("f_dx_asma_emp", "f_dx_encaminhar"):
        c["espiro"] = False
        c["melhorou"] = alvo == "f_dx_asma_emp"
        if rng.random() < 0.5:
            c["feno"], c["eos"] = rng.randint(55, 90), rng.randint(520, 900)
        texto = "Unidade básica sem espirometria nem medidor de pico de fluxo. " + texto
    elif alvo in ("f_dx_asma", "f_dx_nao"):
        positiva = alvo == "f_dx_asma" and rng.random() < 0.6
        for _ in range(500):
            pre = round(rng.uniform(1.1, 3.6), 2)
            if positiva:
                ml = rng.randrange(220, 700, 10)
            elif rng.random() < 0.4:                  # armadilha: % alta, volume pequeno
                pre = round(rng.uniform(1.0, 1.4), 2)
                ml = rng.randrange(150, 190, 10)
            else:
                ml = rng.randrange(40, 240, 10)
            c["vef_pre"], c["vef_pos"] = pre, round(pre + ml / 1000, 2)
            p, m = _bd_pct(c), _bd_ml(c)
            if 11 <= p < 13 or 190 <= m < 210:       # longe do corte, para a conta arredondada não enganar
                continue
            if _bd_pos(c) == positiva:
                break
        if not positiva:
            if alvo == "f_dx_asma":
                if rng.random() < 0.5:
                    c["pfe_var"] = rng.randint(13, 25)
                else:
                    c["meta"] = rng.randint(22, 40)
            else:
                c["pfe_var"] = rng.randint(3, 8)
                c["meta"] = rng.choice([None, rng.randint(5, 14)])
    c["texto"] = texto
    sem = "sem aparelho"
    c["mostrar"] = [("Idade", f"{c['idade']} anos"), ("Padrão", c["padrao"]),
                    ("Outras causas", c["alt"] or ("negativa" if not c["tipico"] else "não necessária")),
                    ("VEF₁ antes do BD", f"{f2(c['vef_pre'])} L" if c["vef_pre"] else sem if not c["espiro"] else "não feito"),
                    ("VEF₁ após o BD", f"{f2(c['vef_pos'])} L" if c["vef_pre"] else sem if not c["espiro"] else "não feito"),
                    ("Variação PFE", f"{fi(c['pfe_var'])}%" if c["pfe_var"] is not None else "não feita"),
                    ("Metacolina", f"VEF₁ caiu {fi(c['meta'])}%" if c["meta"] is not None else "não feita"),
                    ("FeNO", f"{fi(c['feno'])} ppb"), ("Eosinófilos", f"{fi(c['eos'])}/µL"),
                    ("Após o ICS", "—" if c["melhorou"] is None else "melhorou" if c["melhorou"] else "sem melhora")]
    return c


ASMA_DX = Arvore("asma_dx", "Asma: diagnóstico", f"{GINA} · padrão típico → espirometria → broncodilatador → variabilidade",
                 "tipico", DX_NOS, _gerar_dx, [n.id for n in DX_NOS if n.folha],
                 lambda c: [("Ganho do VEF₁", f"+{_bd_ml(c)} mL · +{fi(_bd_pct(c))}%")] if c["vef_pre"] else [],
                 grupo="asma")
ASMA_DX.nos["bd"].calc = _c_bd

# ================================================================== 2. TRATAMENTO INICIAL (Box 4-5, 4-6)


def _q4(c):
    return c["dias"] == 7 and c["desperta"] >= 1 and (c["vef"] < 70 or c["exac"])


def _q3(c):
    return c["dias"] >= 4 or c["desperta"] >= 1 or c["vef"] < 70


def _track(rot):
    return [("Track 1", "há ICS-formoterol (preferido)", "f_in_t1_" + rot, None),
            ("Track 2", "sem ICS-formoterol", "f_in_t2_" + rot, None)]


def _ex_track(c):
    return ("Há budesonida-formoterol: Track 1, o preferido, porque cada alívio já leva corticoide." if c["formot"] else
            "Sem ICS-formoterol disponível: Track 2, com alívio por ICS-SABA (ou SABA, nunca sozinho).")


IN_NOS = [
    No("crise", "Está em crise?", "Asma confirmada, sem tratamento. Ele chegou em crise aguda?",
       [("Em crise", "tratar a crise primeiro", "f_in_crise", None), ("Estável", "escolher o tratamento", "q4", None)],
       lambda c: 0 if c["crise"] else 1,
       lambda c: "Chegou " + ("com crise: primeiro o fluxograma da crise (Box 9-4)." if c["crise"] else "estável, sem crise.")),
    No("q4", "Quadro de passo 4?", "Sintomas DIÁRIOS e despertar ≥ 1×/semana, COM função baixa ou exacerbação recente?",
       [("Sim", "começa no passo 4", "t4", None), ("Não", "ver o passo 3", "q3", None)],
       lambda c: 0 if _q4(c) else 1,
       lambda c: (f"Sintomas {c['dias']}×/semana, desperta {c['desperta']}×/semana, VEF₁ {c['vef']}%, "
                  f"exacerbação recente: {'sim' if c['exac'] else 'não'}. O passo 4 exige TUDO isso junto.")),
    No("q3", "Quadro de passo 3?", "Sintomas na maioria dos dias, OU despertar ≥ 1×/semana, OU função baixa?",
       [("Sim", "começa no passo 3", "t3", None), ("Não", "passos 1–2", "t12", None)],
       lambda c: 0 if _q3(c) else 1,
       lambda c: f"Sintomas {c['dias']}×/semana, desperta {c['desperta']}×/semana, VEF₁ {c['vef']}%. Basta UM desses."),
    No("t4", "Track 1 ou 2?", "Passo 4. Qual track?", _track("4"), lambda c: 0 if c["formot"] else 1, _ex_track),
    No("t3", "Track 1 ou 2?", "Passo 3. Qual track?", _track("3"), lambda c: 0 if c["formot"] else 1, _ex_track),
    No("t12", "Track 1 ou 2?", "Passos 1–2. Qual track?", _track("12"), lambda c: 0 if c["formot"] else 1, _ex_track),
    Folha("f_in_crise", "Tratar a crise", "Em crise: tratar a exacerbação (Box 9-4) e já sair com ICS de manutenção",
          "A alta da crise é o melhor momento para começar a prevenção: de preferência MART com ICS-formoterol."),
    Folha("f_in_t1_12", "T1 · passos 1–2", "Track 1, passos 1–2: budesonida-formoterol baixa dose SÓ quando precisar (AIR)",
          "Sem manutenção diária: cada alívio leva corticoide, e isso corta as crises graves em relação ao SABA sozinho."),
    Folha("f_in_t2_12", "T2 · passos 1–2", "Track 2, passos 1–2: ICS-SABA quando precisar (passo 1) ou ICS baixa dose diário (passo 2)",
          "Mesmo no Track 2, nunca SABA sozinho: cada jato de alívio vem com ICS, junto (budesonida-salbutamol) ou em inalador separado."),
    Folha("f_in_t1_3", "T1 · passo 3", "Track 1, passo 3: MART com ICS-formoterol baixa dose (manutenção + alívio)",
          "O mesmo inalador mantém e alivia. Procurar atendimento se precisar de mais de 12 inalações em 24 horas."),
    Folha("f_in_t2_3", "T2 · passo 3", "Track 2, passo 3: ICS-LABA baixa dose + alívio com ICS-SABA (ou SABA)",
          "Se o alívio for SABA puro, vigie a adesão à manutenção: SABA sem ICS é o que mata na asma."),
    Folha("f_in_t1_4", "T1 · passo 4", "Track 1, passo 4: MART com ICS-formoterol dose média",
          "Comece já no passo 4 quando há sintoma diário com despertar e função baixa ou crise recente; reavalie em 2–3 meses."),
    Folha("f_in_t2_4", "T2 · passo 4", "Track 2, passo 4: ICS-LABA dose média + alívio com ICS-SABA (ou SABA)",
          "Dose média, não alta: alta dose fica reservada ao passo 5, por curto período e com fenotipagem."),
]


def _gerar_in(rng, alvo):
    c = {"idade": rng.randint(14, 65), "crise": False, "formot": "_t1_" in alvo or (alvo == "f_in_crise" and rng.random() < 0.5),
         "dias": 1, "desperta": 0, "vef": rng.randint(85, 100), "exac": False}
    passo = alvo.rsplit("_", 1)[-1]
    if alvo == "f_in_crise":
        c["crise"] = True
        c.update(dias=7, desperta=rng.randint(1, 4), vef=rng.randint(45, 65), exac=True)
        texto = "Chega à UBS com falta de ar há 2 dias e chiado audível."
    elif passo == "4":
        c.update(dias=7, desperta=rng.randint(1, 5))
        if rng.random() < 0.5:
            c["vef"] = rng.randint(50, 65)
        else:
            c["exac"] = True
        texto = "Asma recém-confirmada; usou corticoide oral há 3 semanas." if c["exac"] else "Asma recém-confirmada, muito sintomática."
    elif passo == "3":
        k = rng.randrange(3)
        if k == 0:
            c["dias"] = rng.randint(4, 6)
        elif k == 1:                                  # desperta, mas sem sintoma diário: não é passo 4
            c.update(dias=rng.choice([2, 4, 5]), desperta=rng.randint(1, 2))
        else:
            c.update(dias=rng.choice([2, 4, 5, 7]), vef=rng.randint(50, 65))
        texto = "Asma recém-confirmada, sintomas frequentes."
    else:
        c.update(dias=rng.randint(0, 2), desperta=0)
        texto = "Asma recém-confirmada, sintomas ocasionais."
    if alvo != "f_in_crise" and _q4(c) != (passo == "4"):
        return _gerar_in(rng, alvo)
    c["texto"] = texto
    c["mostrar"] = [("Idade", f"{c['idade']} anos"), ("Hoje", "em crise" if c["crise"] else "estável"),
                    ("Dias c/ sintoma", f"{c['dias']}/semana"),
                    ("Despertares", f"{c['desperta']}/semana" if c["desperta"] else "nenhum"),
                    ("VEF₁", f"{c['vef']}% previsto"), ("Crise recente", "sim" if c["exac"] else "não"),
                    ("ICS-formoterol", "disponível" if c["formot"] else "indisponível")]
    return c


ASMA_INICIO = Arvore("asma_inicio", "Asma: por onde começar", f"{GINA} · crise? → gravidade do quadro → passo → Track 1 ou 2",
                     "crise", IN_NOS, _gerar_in, [n.id for n in IN_NOS if n.folha],
                     lambda c: [("Itens do passo 4", f"{sum([c['dias'] == 7, c['desperta'] >= 1, c['vef'] < 70 or c['exac']])}/3")],
                     grupo="asma")

# ================================================================== 3. CONSULTA DE CONTROLE (Box 2-2, p.81, Box 4-13)


def _n_ctrl(c):
    return sum([c["diurno"] > 2, c["noturno"] > 0, c["saba"] > 2 and not c["saba_exerc"] and not c["air"], c["limita"]])


def _c_ctrl(c):
    n = _n_ctrl(c)
    err = []
    if c["saba"] > 2 and c["saba_exerc"]:
        err.append((n + 1, "contou o SABA usado só antes do exercício (ele não conta)"))
    if c["saba"] > 2 and c["air"]:
        err.append((n + 1, "contou o alívio com ICS-formoterol (o GINA conta só o SABA)"))
    if c["diurno"] == 2:
        err.append((n + 1, "contou sintomas 2×/semana (o critério é MAIS de 2)"))
    err += [(n - 1, "deixou de contar um item"), (n + 2, "errou a contagem")]
    form = (f"diurnos {c['diurno']}×/sem ({'sim' if c['diurno'] > 2 else 'não'}) · noturno ({'sim' if c['noturno'] else 'não'}) · "
            f"SABA ({'sim' if c['saba'] > 2 and not c['saba_exerc'] and not c['air'] else 'não'}) · "
            f"limitação ({'sim' if c['limita'] else 'não'}) = {n}")
    alts = _alts_inteiras(n, err)
    return "Quantas das 4 perguntas do controle são “sim”?", n, alts, form, 0


def _riscos(c):
    return c["exac_ano"] >= 1 or c["vef"] < 60 or c["frascos"] >= 3


CT_NOS = [
    No("ctrl", "Controle (4 perguntas)", "Nas últimas 4 semanas, quantas das 4 perguntas do controle são “sim”?",
       [("Nenhuma", "bem controlada", "descer", None),
        ("1–2", "parcialmente controlada", "tecnica", "asma parcialmente controlada"),
        ("3–4", "não controlada", "tecnica", "asma não controlada")],
       lambda c: 0 if _n_ctrl(c) == 0 else 1 if _n_ctrl(c) <= 2 else 2,
       lambda c: (f"Diurnos > 2×/sem, despertar, SABA > 2×/sem, limitação: {_n_ctrl(c)} “sim”."
                  + (" SABA só antes do exercício não conta." if c["saba_exerc"] and c["saba"] > 2 else "")
                  + (" Alívio com ICS-formoterol não conta." if c["air"] and c["saba"] > 2 else ""))),
    No("descer", "Dá para reduzir?", "Bem controlada. Dá para reduzir o tratamento agora?",
       [("Reduzir", "≥ 3 meses e sem risco", "f_ct_descer", None),
        ("Manter", "< 3 meses ou com risco", "f_ct_manter", None)],
       lambda c: 0 if c["meses"] >= 3 and not _riscos(c) else 1,
       lambda c: (f"Controlada há {c['meses']} meses; exacerbações graves no último ano: {c['exac_ano']}; VEF₁ {c['vef']}%; "
                  f"SABA {c['frascos']} frascos/ano. Fator de risco: exacerbação grave no ano, VEF₁ < 60% ou ≥ 3 frascos.")),
    No("tecnica", "Técnica e adesão", "Antes de subir de etapa: a técnica inalatória e a adesão estão certas?",
       [("Corretas", "seguir investigando", "fatores", None), ("Erradas", "corrigir primeiro", "f_ct_tecnica", None)],
       lambda c: 0 if c["tecnica"] is None else 1,
       lambda c: "Técnica e adesão conferidas: corretas." if c["tecnica"] is None else f"Na consulta: {c['tecnica']}."),
    No("fatores", "Fator modificável?", "Técnica certa. Há exposição ou comorbidade não tratada piorando a asma?",
       [("Sim", "tratar o fator", "f_ct_fatores", None), ("Não", "ver a etapa atual", "etapa", None)],
       lambda c: 0 if c["fator"] else 1,
       lambda c: f"Exposições e comorbidades: {c['fator'] or 'nenhuma encontrada'}."),
    No("etapa", "Em que etapa está?", "Tudo corrigido e segue sem controle. Ele já usa ICS-LABA em ALTA dose?",
       [("Ainda não", "etapas 1–4", "f_ct_subir", None), ("Já usa", "alta dose otimizada", "f_ct_grave", None)],
       lambda c: 0 if not c["alta"] else 1,
       lambda c: f"Tratamento atual: {c['trat']}."),
    Folha("f_ct_descer", "Reduzir", "Bem controlada há ≥ 3 meses e sem risco: reduzir o ICS em 25–50%",
          "Desça devagar (a cada 3 meses), nunca suspenda o ICS de vez no adulto e entregue um plano de ação escrito."),
    Folha("f_ct_manter", "Manter", "Bem controlada, mas há pouco tempo ou com fator de risco: manter a etapa",
          "Sintoma controlado não é risco controlado: crise grave no último ano já basta para não reduzir agora."),
    Folha("f_ct_tecnica", "Corrigir técnica/adesão", "Sem controle por técnica inalatória ou adesão: corrigir antes de subir",
          "A maioria dos “não controlados” usa a bombinha errado ou não usa. Peça para demonstrar; agite o spray antes de cada jato."),
    Folha("f_ct_fatores", "Tratar o fator", "Sem controle por fator modificável: tratar a exposição ou a comorbidade antes de subir",
          "Tabaco, alérgeno, betabloqueador, AINE, rinossinusite, refluxo, obesidade: subir a dose não resolve a causa."),
    Folha("f_ct_subir", "Subir uma etapa", "Sem controle com tudo corrigido: subir uma etapa e reavaliar em 2–3 meses",
          "Só depois de checar técnica, adesão, exposições, comorbidades e o próprio diagnóstico."),
    Folha("f_ct_grave", "Asma grave", "Asma grave: sem controle com ICS-LABA alta dose e tudo corrigido; encaminhar para fenotipagem",
          "Antes era “difícil de tratar”; agora, com adesão e fatores resolvidos, é grave. Próximos passos: LAMA e biológico (fluxograma da asma grave)."),
]

_TECNICAS = ["não agita o spray", "esquece metade das doses", "pó seco sem força", "só usa em crise"]
_FATORES = ["fuma 10 cig/dia", "usa propranolol", "rinossinusite", "gato no quarto (alérgico)", "refluxo sem tratar"]
_TRAT_BAIXO = ["MART baixa dose", "ICS-LABA média", "ICS baixa + SABA"]
_TRAT_ALTO = ["ICS-LABA alta dose", "ICS-LABA alta dose + LAMA"]


def _gerar_ct(rng, alvo):
    c = {"idade": rng.randint(16, 70), "diurno": 0, "noturno": 0, "saba": 0, "saba_exerc": False, "air": False,
         "limita": False, "meses": rng.randint(1, 12), "exac_ano": 0, "vef": rng.randint(75, 100), "frascos": rng.randint(0, 2),
         "tecnica": None, "fator": None, "alta": False, "trat": rng.choice(_TRAT_BAIXO)}
    if alvo in ("f_ct_descer", "f_ct_manter"):
        c["diurno"] = rng.choice([0, 1, 2])
        if rng.random() < 0.4:                       # usa a bombinha, mas não conta
            c["saba"] = rng.randint(3, 4)
            c["saba_exerc"] = rng.random() < 0.6
            c["air"] = not c["saba_exerc"]
        if alvo == "f_ct_descer":
            c["meses"] = rng.randint(3, 12)
        elif rng.random() < 0.4:
            c["meses"] = rng.randint(1, 2)
        else:
            k = rng.randrange(3)
            c["meses"] = rng.randint(3, 12)
            if k == 0:
                c["exac_ano"] = rng.randint(1, 2)
            elif k == 1:
                c["vef"] = rng.randint(45, 58)
            else:
                c["frascos"] = rng.randint(3, 6)
    else:
        for _ in range(100):
            c.update(diurno=rng.choice([1, 2, 3, 5, 7]), noturno=rng.choice([0, 0, 1, 2]), saba=rng.choice([1, 3, 5]),
                     limita=rng.random() < 0.4, saba_exerc=False, air=False)
            if c["saba"] > 2 and rng.random() < 0.25:
                c["saba_exerc"] = True
            if _n_ctrl(c) >= 1:
                break
        if alvo == "f_ct_tecnica":
            c["tecnica"] = rng.choice(_TECNICAS)
        else:
            if alvo in ("f_ct_fatores",):
                c["fator"] = rng.choice(_FATORES)
            if alvo == "f_ct_grave":
                c["alta"], c["trat"] = True, rng.choice(_TRAT_ALTO)
    saba_txt = f"SABA {c['saba']}×/sem" if c["saba"] else "não usa"
    if c["saba_exerc"]:
        saba_txt += ", só pré-futebol"
    if c["air"]:
        saba_txt = f"ICS-formoterol {c['saba']}×/sem"
    c["texto"] = rng.choice(["Retorno de rotina na UBS.", "Consulta de seguimento no ambulatório de pneumologia.",
                             "Volta para reavaliação após 3 meses de tratamento."])
    c["mostrar"] = [("Sintoma diurno", f"{c['diurno']}×/semana" if c["diurno"] else "nenhum"),
                    ("Despertares", f"{c['noturno']}×/mês" if c["noturno"] else "não"),
                    ("Alívio", saba_txt), ("Limitação", "sim" if c["limita"] else "não"),
                    ("Controlada há", (f"{c['meses']} meses" if c["meses"] > 1 else "1 mês") if _n_ctrl(c) == 0 else "—"),
                    ("Crises graves/ano", fi(c["exac_ano"])), ("VEF₁", f"{c['vef']}% previsto"),
                    ("SABA/ano", f"{c['frascos']} frascos"),
                    ("Técnica/adesão", c["tecnica"] or "corretas"), ("Fatores", c["fator"] or "nenhum"),
                    ("Tratamento", c["trat"])]
    return c


ASMA_CONTROLE = Arvore("asma_controle", "Asma: consulta de controle",
                       f"{GINA} · 4 perguntas → reduzir? → técnica → fatores → subir ou asma grave",
                       "ctrl", CT_NOS, _gerar_ct, [n.id for n in CT_NOS if n.folha],
                       lambda c: [("“Sim” no controle", fi(_n_ctrl(c)))], grupo="asma")
ASMA_CONTROLE.nos["ctrl"].calc = _c_ctrl

# ================================================================== 4. CRISE (Box 9-6, 9-4)


def _pct(c, k="pef"):
    return c[k] / c["pef_ref"] * 100


def _gravidade(c):
    if c["fala"] == "palavras" or c["spo2"] < 92 or c["fr"] > 30 or _pct(c) < 50:
        return 2
    if c["fala"] == "frases" and c["spo2"] >= 94 and _pct(c) > 70 and c["fr"] <= 24:
        return 0
    return 1


def _resposta(c):
    if c["pef1h"] < c["pef"]:
        return 2
    return 0 if _pct(c, "pef1h") > 70 and c["spo2_1h"] >= 92 and not c["saba_1h"] else 1


def _c_pfe(c, k, quando):
    v = _pct(c, k)
    err = [(c["pef_ref"] / c[k] * 100, "inverteu a divisão"), (100 - v, "calculou quanto FALTA, não quanto tem"),
           (c[k] / c["pef_ref"] * 10, "errou a vírgula")]
    form = f"{fi(c[k])} ÷ {fi(c['pef_ref'])} × 100 = {fi(v)}%"
    return f"Quanto é o PFE {quando}, em % do melhor pessoal/previsto?", v, err, form, 0


CR_NOS = [
    No("vida", "Risco de vida?", "Crise de asma no pronto-socorro. Há sonolência, confusão, cianose ou tórax silencioso?",
       [("Sim", "risco de vida", "f_cr_vida", None), ("Não", "ver a gravidade", "grav", None)],
       lambda c: 0 if c["vida"] else 1,
       lambda c: f"Consciência: {c['consc']}; ausculta: {c['ausculta']}." + (" Tórax silencioso = quase não entra ar." if c["vida"] else "")),
    No("grav", "Gravidade", "Sem risco de vida. Qual a gravidade da crise?",
       [("Leve", "frases, SpO₂ ≥ 94%, PFE > 70%", "resp", "crise leve tratada com salbutamol 4 jatos (ou budesonida-formoterol 2 jatos)"),
        ("Moderada", "frases curtas, PFE 50–70%", "resp",
         "crise moderada tratada com salbutamol 4–6 jatos + ipratrópio até 3 vezes e corticoide sistêmico"),
        ("Grave", "palavras, SpO₂<92, FR>30, PFE<50", "resp",
         "crise grave tratada com salbutamol 6–10 jatos + ipratrópio, O₂ alvo 92–95% e corticoide sistêmico")],
       lambda c: _gravidade(c),
       lambda c: (f"Fala {c['fala']}, FR {c['fr']}, SpO₂ {c['spo2']}%, PFE {fi(_pct(c))}% do esperado. "
                  + ("Um único critério grave basta." if _gravidade(c) == 2 else
                     "Leve exige TODOS os critérios leves." if _gravidade(c) == 0 else "Nem todos leves, nenhum grave."))),
    No("resp", "Resposta em 1 hora", "Reavaliação em 1 hora. Como respondeu?",
       [("Melhora acentuada", "PFE > 70%, SpO₂ ≥ 92%, sem SABA", "f_cr_alta", None),
        ("Melhora parcial", "melhorou sem chegar lá", "f_cr_parcial", None),
        ("Piora", "PFE menor que na chegada", "f_cr_piora", None)],
       lambda c: _resposta(c),
       lambda c: (f"PFE {fi(c['pef'])} → {fi(c['pef1h'])} ({fi(_pct(c, 'pef1h'))}%), SpO₂ em ar {c['spo2_1h']}%, "
                  f"{'ainda pedindo SABA' if c['saba_1h'] else 'sem precisar de SABA'}.")),
    Folha("f_cr_vida", "Risco de vida", "Crise com risco de vida: salbutamol + ipratrópio nebulizados, O₂, corticoide sistêmico e chamar UTI",
          "Acesso venoso, O₂ por máscara não reinalante, sulfato de magnésio IV, raio X e gasometria. Se há anafilaxia, adrenalina IM primeiro."),
    Folha("f_cr_alta", "Alta", "Melhora acentuada: alta com prednisolona 40–50 mg/dia por 5–7 dias, ICS iniciado ou aumentado e retorno em 2–7 dias",
          "Na alta, de preferência MART com ICS-formoterol (≥ 12 anos), revisar a técnica e entregar plano de ação escrito."),
    Folha("f_cr_parcial", "Observar", "Melhora parcial: reavaliar a cada hora; internar se SpO₂ < 92%, SABA mais que a cada 1–2 h ou dispneia 4–6 h após o corticoide",
          "Mais ipratrópio, corticoide se ainda não deu, e cuidado com a toxicidade do salbutamol (taquicardia, hipocalemia, lactato)."),
    Folha("f_cr_piora", "Piora", "Piora: mais salbutamol e ipratrópio, sulfato de magnésio 2 g IV em 20 min e considerar UTI",
          "O magnésio IV não é rotina: entra em quem não responde ao tratamento inicial e segue hipoxêmico."),
]


def _gerar_cr(rng, alvo):
    ref = rng.choice([380, 420, 450, 500, 550])
    c = {"idade": rng.randint(14, 60), "pef_ref": ref, "vida": False, "consc": "alerta", "ausculta": "sibilos difusos",
         "fala": "frases", "fr": 20, "fc": 100, "spo2": 96, "pef": 0, "pef1h": 0, "spo2_1h": 96, "saba_1h": False}
    if alvo == "f_cr_vida":
        c["consc"], c["ausculta"] = rng.choice([("sonolento", "tórax silencioso"), ("confuso, cianótico", "quase sem murmúrio")])
        c.update(vida=True,
                 fala="palavras", fr=rng.randint(32, 40), fc=rng.randint(125, 145), spo2=rng.randint(84, 89))
        c["pef"] = round(ref * rng.uniform(0.2, 0.33))
        c["pef1h"] = c["pef"]
        c["spo2_1h"] = c["spo2"]
        c["saba_1h"] = True
        texto = "Asmático trazido pela família após horas de falta de ar."
    else:
        g = rng.choice([0, 1, 2])
        for _ in range(300):
            if g == 0:
                c.update(fala="frases", fr=rng.randint(16, 22), fc=rng.randint(80, 105), spo2=rng.randint(94, 98))
                pct = rng.uniform(0.73, 0.9)
            elif g == 1:
                c.update(fala=rng.choice(["frases curtas", "frases"]), fr=rng.randint(22, 30), fc=rng.randint(100, 120),
                         spo2=rng.randint(92, 95))
                pct = rng.uniform(0.52, 0.68)
            else:
                c.update(fala=rng.choice(["palavras", "frases curtas"]), fr=rng.randint(24, 36), fc=rng.randint(110, 135),
                         spo2=rng.randint(88, 94))
                pct = rng.uniform(0.3, 0.6)
            c["pef"] = round(ref * pct / 10) * 10
            p = _pct(c)
            if 48 <= p <= 52 or 68 <= p <= 72:
                continue
            if _gravidade(c) == g:
                break
        r = {"f_cr_alta": 0, "f_cr_parcial": 1, "f_cr_piora": 2}[alvo]
        for _ in range(300):
            if r == 0:
                c["pef1h"] = round(ref * rng.uniform(0.74, 0.95) / 10) * 10
                c["spo2_1h"], c["saba_1h"] = rng.randint(93, 98), False
            elif r == 1:
                c["pef1h"] = round(ref * rng.uniform(max(_pct(c) / 100, 0.45), 0.8) / 10) * 10
                c["spo2_1h"], c["saba_1h"] = rng.randint(90, 96), rng.random() < 0.6
            else:
                c["pef1h"] = round(c["pef"] * rng.uniform(0.75, 0.92) / 10) * 10
                c["spo2_1h"], c["saba_1h"] = rng.randint(86, 92), True
            p = _pct(c, "pef1h")
            if 68 <= p <= 72:
                continue
            if _resposta(c) == r:
                break
        texto = rng.choice(["Asmático com chiado desde ontem após resfriado.", "Jovem com crise após faxina com poeira.",
                            "Mulher asmática que ficou sem a bombinha de manutenção há 1 mês."])
    c["texto"] = texto
    c["mostrar"] = [("Idade", f"{c['idade']} anos"), ("Consciência", c["consc"]), ("Ausculta", c["ausculta"]), ("Fala", c["fala"]),
                    ("FR", f"{c['fr']} irpm"), ("FC", f"{c['fc']} bpm"), ("SpO₂ (ar)", f"{c['spo2']}%"),
                    ("PFE", f"{fi(c['pef'])} L/min"), ("Melhor PFE", f"{fi(ref)} L/min"),
                    ("PFE em 1 h", f"{fi(c['pef1h'])} L/min"), ("SpO₂ em 1 h", f"{c['spo2_1h']}%"),
                    ("SABA em 1 h", "ainda usa" if c["saba_1h"] else "não usou")]
    return c


ASMA_CRISE = Arvore("asma_crise", "Asma: crise no pronto-socorro", f"{GINA} · risco de vida? → gravidade → resposta em 1 hora",
                    "vida", CR_NOS, _gerar_cr, [n.id for n in CR_NOS if n.folha],
                    lambda c: [("PFE na chegada", f"{fi(_pct(c))}%"), ("PFE em 1 h", f"{fi(_pct(c, 'pef1h'))}%")], grupo="asma")
ASMA_CRISE.nos["grav"].calc = lambda c: _c_pfe(c, "pef", "na chegada")
ASMA_CRISE.nos["resp"].calc = lambda c: _c_pfe(c, "pef1h", "depois de 1 hora")

# ================================================================== 5. ASMA GRAVE E BIOLÓGICOS (Box 8-2 a 8-5)


def _t2(c):
    return c["eos"] >= 150 or c["feno"] >= 20 or c["alergica"] or c["ocs"]


def _fenotipo(c):
    if c["alergica"] and c["ige_ok"]:
        return 0
    if c["eos"] >= 300:
        return 1
    return 2


BIO_NOS = [
    No("conf", "É grave mesmo?", "Asma sem controle. Já foram otimizados adesão, técnica, comorbidades e ICS-LABA alta dose?",
       [("Sim", "asma grave", "t2", None), ("Não", "asma difícil de tratar", "f_bio_otimizar", None)],
       lambda c: 0 if c["otimizado"] else 1,
       lambda c: "Tudo otimizado há mais de 3 meses." if c["otimizado"] else f"Ainda falta: {c['falta']}."),
    No("t2", "Inflamação tipo 2?", "Asma grave confirmada. Há sinal de inflamação tipo 2?",
       [("Sim", "eos ≥ 150, FeNO ≥ 20, alergia, OCS", "fenotipo", None),
        ("Não", "nenhum marcador", "resp", "anti-TSLP (tezepelumabe) como biológico, o único sem exigir marcador tipo 2")],
       lambda c: 0 if _t2(c) else 1,
       lambda c: (f"Eosinófilos {fi(c['eos'])}/µL, FeNO {fi(c['feno'])} ppb, alergia relevante: {'sim' if c['alergica'] else 'não'}, "
                  f"corticoide oral diário: {'sim' if c['ocs'] else 'não'}. Repita eos/FeNO até 3 vezes antes de dizer “não tipo 2”.")),
    No("fenotipo", "Qual biológico primeiro?", "Tipo 2 com exacerbações no último ano. Qual traço domina?",
       [("Alérgica", "alérgico, IgE na faixa, infância", "resp", "anti-IgE (omalizumabe) como biológico"),
        ("Eosinofílica", "eos ≥ 300, polipose, adulto", "resp",
         "anti-IL5/5R (mepolizumabe, benralizumabe, reslizumabe ou depemoquimabe) como biológico"),
        ("FeNO alto", "FeNO ≥ 25, eos < 1.500, OCS", "resp", "anti-IL4Rα (dupilumabe) como biológico")],
       lambda c: _fenotipo(c),
       lambda c: (f"Prick/IgE específica {'positivos' if c['alergica'] else 'negativos'}, IgE total {fi(c['ige'])} UI/mL, "
                  f"eos {fi(c['eos'])}/µL, FeNO {fi(c['feno'])} ppb, início {c['inicio']}, polipose: {'sim' if c['polipo'] else 'não'}. "
                  "Escolha pelo melhor preditor de resposta.")),
    No("resp", "Resposta ao biológico", "Teste de pelo menos 4 meses. A resposta foi boa?",
       [("Boa", "menos crises e menos OCS", "f_bio_manter", None), ("Incerta", "difícil dizer", "f_bio_estender", None),
        ("Pouca ou nenhuma", "nada mudou", "f_bio_trocar", None)],
       lambda c: c["resposta"],
       lambda c: f"Em 4 meses: exacerbações {c['exac']} → {c['exac_dep']}/ano; {c['ocs_dep']}."),
    Folha("f_bio_otimizar", "Difícil, não grave", "Asma difícil de tratar, ainda não grave: otimizar antes de pensar em biológico",
          "Grave é quem segue sem controle mesmo COM tudo corrigido. Biológico em quem usa a bombinha errado é desperdício."),
    Folha("f_bio_manter", "Manter", "Boa resposta: manter o biológico e reavaliar a cada 3–6 meses; tentar reduzir primeiro o OCS",
          "Depois, reduza devagar o ICS para dose média, sem suspender."),
    Folha("f_bio_estender", "Estender o teste", "Resposta incerta: estender o teste para 6–12 meses",
          "Alguns respondem devagar. Depemoquimabe já começa com teste de 6 meses."),
    Folha("f_bio_trocar", "Trocar", "Pouca resposta: suspender e trocar por outro biológico tipo 2, se elegível",
          "Antes da troca, reveja adesão, técnica e o diagnóstico (outra doença imitando asma grave?)."),
]


def _gerar_bio(rng, alvo):
    c = {"otimizado": True, "falta": "", "eos": rng.randint(30, 120), "feno": rng.randint(8, 18), "alergica": False,
         "ige_ok": False, "ige": rng.randint(20, 90), "ocs": False, "inicio": "na vida adulta", "polipo": False,
         "exac": rng.randint(2, 5), "resposta": 0}
    if alvo == "f_bio_otimizar":
        c["otimizado"] = False
        c["falta"] = rng.choice(["adesão 40%", "técnica errada", "rinossinusite", "ICS-LABA média"])
    else:
        c["resposta"] = {"f_bio_manter": 0, "f_bio_estender": 1, "f_bio_trocar": 2}[alvo]
        f = [0, 1, 2, 0, 1, 2, None][rng.randrange(7)]             # 1 em 7 sem tipo 2 (anti-TSLP)
        if f == 0:
            c.update(alergica=True, ige_ok=True, ige=rng.randint(120, 700), inicio="na infância",
                     eos=rng.randint(150, 280), feno=rng.randint(20, 35))
        elif f == 1:
            c.update(eos=rng.randint(400, 1200), feno=rng.randint(20, 45), polipo=True)
        elif f == 2:
            c.update(eos=rng.randint(150, 280), feno=rng.randint(45, 90), ocs=rng.random() < 0.6)
    c["exac_dep"] = {0: 0, 1: max(1, c["exac"] - 1), 2: c["exac"]}[c["resposta"]]
    c["ocs_dep"] = {0: "parou o OCS", 1: "quase igual", 2: "sem mudança"}[c["resposta"]]
    c["texto"] = rng.choice(["Adulto com asma desde sempre, várias idas ao PS no ano.", "Mulher com asma iniciada aos 40 anos e muitas crises.",
                             "Asmático encaminhado ao ambulatório de asma grave."])
    c["mostrar"] = [("Otimização", "completa" if c["otimizado"] else "incompleta"), ("Pendência", c["falta"] or "nenhuma"),
                    ("Crises no ano", fi(c["exac"])), ("Eosinófilos", f"{fi(c['eos'])}/µL"), ("FeNO", f"{fi(c['feno'])} ppb"),
                    ("Prick/IgE esp.", "positiva" if c["alergica"] else "negativa"), ("IgE total", f"{fi(c['ige'])} UI/mL"),
                    ("Início da asma", c["inicio"]), ("Polipose nasal", "sim" if c["polipo"] else "não"),
                    ("OCS diário", "sim" if c["ocs"] else "não"),
                    ("Crises/ano após", f"{c['exac_dep']}/ano" if c["otimizado"] else "—"),
                    ("Evolução", c["ocs_dep"] if c["otimizado"] else "—")]
    return c


ASMA_GRAVE = Arvore("asma_grave", "Asma grave: biológico", f"{GINA} · difícil × grave → tipo 2 → qual biológico → resposta",
                    "conf", BIO_NOS, _gerar_bio, [n.id for n in BIO_NOS if n.folha], lambda c: [], grupo="asma")

ASMA = [ASMA_DX, ASMA_INICIO, ASMA_CONTROLE, ASMA_CRISE, ASMA_GRAVE]
for _a in ASMA:
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None

# ------------------------------------------------------------------ mini-aulas (o porquê de cada passo)
# Molde: a pergunta que a caixa responde → o mecanismo (por quê) → a armadilha da prova.

AULAS = {
    "asma_dx": {
        "tipico": "Primeiro pergunte se o PADRÃO é de asma. A asma é inflamação que oscila, então o sintoma vai e volta, piora "
                  "à noite e tem gatilho. Sintoma fixo, sem variação, manda procurar outra causa.",
        "alt": "Quadro atípico pede investigação de outra doença: tosse por IECA, DPOC, obstrução laríngea, IC. Só se nada se "
               "confirmar a asma volta a ser hipótese — e precisa da mesma prova de função.",
        "espiro": "Asma é diagnóstico de FUNÇÃO, não de ausculta: precisa mostrar obstrução que varia. Faça a prova antes do "
                  "corticoide, porque o tratamento tira a variabilidade e apaga a evidência.",
        "bd": "O broncodilatador abre o brônquio que estava contraído. Positivo exige as DUAS coisas: ≥ 12% e ≥ 200 mL. A "
              "armadilha é o pulmão pequeno: 150 mL num VEF₁ de 1,2 L dá 12,5%, e não basta.",
        "variab": "Prova negativa fora de crise não exclui asma, porque o brônquio pode estar aberto naquele dia. Procure a "
                  "variação por outro caminho: PFE duas vezes ao dia por 2 semanas (> 10%) ou metacolina (queda ≥ 20%).",
        "biomarc": "Sem espirometria, FeNO e eosinófilos medem a inflamação tipo 2. Altos apoiam asma; normais NÃO excluem, "
                   "porque parte das asmas não é tipo 2. O biomarcador reforça, não decide.",
        "empirico": "Sem prova de função, trate com ICS e use a resposta como teste. Melhora em 1–3 meses sustenta asma; "
                    "sem melhora, o problema provavelmente é outro — não suba a dose às cegas.",
    },
    "asma_inicio": {
        "crise": "Crise primeiro: quem chega sufocado precisa do fluxograma da exacerbação, não da escolha de manutenção. "
                 "Mas a alta da crise é exatamente quando se começa o ICS.",
        "q4": "O GINA começa alto quando a doença já está pesada: sintoma diário com despertar semanal E (função baixa ou "
              "crise recente). A armadilha é o “E”: sintoma diário sozinho não leva ao passo 4.",
        "q3": "Passo 3 basta UM sinal de doença ativa: sintomas na maioria dos dias, despertar semanal ou função baixa. "
              "Menos que isso (poucos dias por semana, função normal) é passos 1–2.",
        "t4": "Track 1 usa budesonida-formoterol para manter e para aliviar: cada alívio leva corticoide, por isso é o "
              "preferido. Track 2 só se não houver ICS-formoterol.",
        "t3": "Mesma escolha: Track 1 (MART com ICS-formoterol baixa dose) se disponível; senão Track 2 (ICS-LABA baixa dose "
              "+ alívio com ICS-SABA).",
        "t12": "Nos passos 1–2 não há SABA sozinho em nenhum track: o alívio sem corticoide aumenta crise grave e morte. "
               "Track 1 = ICS-formoterol só quando precisa; Track 2 = ICS-SABA (novidade 2026) ou ICS diário.",
    },
    "asma_controle": {
        "ctrl": "Controle de sintomas são 4 perguntas sobre as últimas 4 semanas: diurno > 2×/sem, despertar, SABA > 2×/sem "
                "e limitação. Armadilhas: SABA só antes do exercício e alívio com ICS-formoterol não contam.",
        "descer": "Bem controlado não significa sem risco. Reduzir exige controle há ≥ 3 meses e nenhum fator de risco: crise "
                  "grave no último ano, VEF₁ < 60% ou ≥ 3 frascos de SABA por ano.",
        "tecnica": "Antes de subir a dose, confira se o remédio está chegando ao pulmão. Técnica errada e falta de adesão "
                   "são as causas mais comuns de “asma não controlada”. Peça para o paciente mostrar.",
        "fatores": "Depois, procure o que alimenta a inflamação: fumo, alérgeno, betabloqueador, AINE, rinossinusite, "
                   "refluxo, obesidade. Mais corticoide não compensa um gatilho que continua presente.",
        "etapa": "Com tudo corrigido, a etapa atual decide: abaixo de ICS-LABA alta dose, suba uma etapa por 2–3 meses. Já "
                 "em alta dose otimizada, isso é asma GRAVE e pede fenotipagem.",
    },
    "asma_crise": {
        "vida": "Antes de medir, olhe a pessoa: sonolência, confusão, cianose ou tórax silencioso indicam fadiga e pouco ar "
                "entrando. Chiado alto engana menos que silêncio — o silêncio é o mais grave.",
        "grav": "A gravidade decide a dose. Leve exige TODOS os critérios leves; grave basta UM: fala em palavras, SpO₂ < 92%, "
                "FR > 30 ou PFE < 50%. Calcule o PFE sobre o melhor pessoal (ou o previsto).",
        "resp": "Em 1 hora, a resposta decide o destino. Alta só com PFE > 70%, SpO₂ ≥ 92% em ar ambiente e sem precisar de "
                "mais SABA. Melhorou pouco: observar. PFE caiu: escalar (magnésio, UTI).",
    },
    "asma_grave": {
        "conf": "Difícil de tratar não é grave. Grave é quem segue sem controle COM adesão, técnica, comorbidades e ICS-LABA "
                "alta dose resolvidos. A maioria dos “graves” encaminhados é difícil, não grave.",
        "t2": "Inflamação tipo 2 (eos ≥ 150, FeNO ≥ 20, alergia ou corticoide oral diário) abre a porta a todos os "
              "biológicos. Sem tipo 2, o anti-TSLP é o único que funciona sem marcador.",
        "fenotipo": "Escolha pelo melhor preditor: alérgica com IgE na faixa → anti-IgE; eos alto e polipose → anti-IL5; "
                    "FeNO alto e OCS-dependente → anti-IL4Rα. Eos ≥ 1.500 contraindica o dupilumabe.",
        "resp": "Todo biológico é um teste: avalie após pelo menos 4 meses (6 para depemoquimabe). Boa resposta: manter. "
                "Incerta: estender. Nenhuma: trocar de classe, revendo o diagnóstico.",
    },
}
for _a in ASMA:
    for _nid, _txt in AULAS[_a.id].items():
        _a.nos[_nid].aula = _txt
