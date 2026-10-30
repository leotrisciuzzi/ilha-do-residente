"""Treino FAST HUG: as duas escalas que o A e o S do checklist pedem, cada uma como fluxograma próprio.

  1. BPS .................. Behavioral Pain Scale (Payen, Crit Care Med 2001): face + membros superiores +
                            adaptação ao ventilador, cada item de 1 a 4 (total 3 a 12); > 5 é dor relevante
  2. RASS ................. Richmond Agitation-Sedation Scale (Sessler, Am J Respir Crit Care Med 2002): observar,
                            chamar pela voz, estimular fisicamente; de +4 (combativo) a −5 (não desperta)

Diferente das árvores do FAST HUG (que pegam o escore pronto), aqui o caso traz o COMPORTAMENTO descrito e o
jogador pontua item por item. Fontes das condutas: PADIS 2018 e atualização SCCM 2025 (autorrelato é o padrão
quando o paciente comunica; BPS > 5 indica dor; analgesia antes da sedação; sedação leve RASS −2 a 0 salvo
indicação de profunda; CAM-ICU com RASS ≥ −3); Girard, Lancet 2008 (despertar diário + TRE)."""
from .fluxo_dados import Arvore, Folha, No, fi
from .fluxo_uti import _c_bps

# ================================================================== 1. BPS (contar a dor de quem não fala)

_FACE = {1: "relaxada", 2: "parcialmente tensa", 3: "totalmente tensa", 4: "careta"}
_MMSS = {1: "sem movimento", 2: "parcialmente fletidos", 3: "fletidos com os dedos", 4: "retraídos"}
_VM = {1: "tolera", 2: "tosse, mas tolera", 3: "briga com o ventilador", 4: "ventilação impossível"}
# o caso descreve o que se vê; o jogador traduz em ponto (frases diferentes dos rótulos dos ramos)
_DESC_FACE = {1: ["rosto sereno, sem tensão", "expressão neutra"],
              2: ["testa franzida, sobrancelhas abaixadas", "contrai as sobrancelhas"],
              3: ["aperta os olhos com força", "pálpebras cerradas, rosto todo contraído"],
              4: ["boca repuxada e sulco nasolabial marcado", "faz careta"]}
_DESC_MMSS = {1: ["braços largados, imóveis", "membros superiores parados"],
              2: ["dobra um pouco os cotovelos", "flexão parcial dos braços"],
              3: ["braços dobrados e mãos fechadas", "flexão completa, punhos cerrados"],
              4: ["braços colados ao corpo o tempo todo", "retração permanente dos braços"]}
_DESC_VM = {1: ["sincronizado, aceita a mobilização", "ventila sem alarmes"],
            2: ["tosse às vezes, mas ventila a maior parte do tempo", "tosse e volta a sincronizar"],
            3: ["assincronia, dispara alarme de pressão", "luta contra o ventilador"],
            4: ["não deixa o ventilador ciclar", "ventilação incontrolável"]}


def _bps(c):
    return c["face"] + c["mmss"] + c["vm"]


def _escala(c):
    if c["bnm"]:
        return 2
    return 0 if c["comunica"] else 1


def _item(nome, rotulos, prox):
    # o ramo é o ponto; o descritor só aparece no nível 1 (depois a escada é de memória)
    return [(f"{k} ponto{'s' if k > 1 else ''}", rotulos[k], prox, f"{nome} {k} ({rotulos[k]})") for k in (1, 2, 3, 4)]


BPS_NOS = [
    No("escala", "Qual escala?", "Antes de pontuar: qual escala de dor serve para ESTE paciente?",
       [("Autorrelato", "ele comunica", "f_bps_auto", None),
        ("BPS", "intubado, não comunica", "face", None),
        ("Nenhuma vale", "bloqueador neuromuscular", "f_bps_bnm", None)],
       _escala,
       lambda c: (f"{c['bnm']}: paralisado não faz careta nem se mexe, então a BPS daria 3 mesmo com dor." if c["bnm"] else
                  f"{c['comunica']}: quem comunica dá a nota da própria dor; a BPS é para quem não consegue." if c["comunica"] else
                  "Intubado, sem conseguir comunicar e sem bloqueador: é o paciente da BPS.")),
    No("face", "Face", "Item 1 · Expressão facial: quantos pontos?", _item("face", _FACE, "mmss"),
       lambda c: c["face"] - 1,
       lambda c: (f"\"{c['d_face']}\" = {_FACE[c['face']]} = {c['face']}. Escada da face: relaxada 1, sobrancelha "
                  "abaixada 2, olhos cerrados 3, careta 4.")),
    No("mmss", "Membros sup.", "Item 2 · Membros superiores: quantos pontos?", _item("membros", _MMSS, "vm"),
       lambda c: c["mmss"] - 1,
       lambda c: (f"\"{c['d_mmss']}\" = {_MMSS[c['mmss']]} = {c['mmss']}. Escada dos braços: parados 1, flexão "
                  "parcial 2, flexão total com os dedos 3, retraídos o tempo todo 4.")),
    No("vm", "Ventilador", "Item 3 · Adaptação ao ventilador: quantos pontos?", _item("ventilador", _VM, "total"),
       lambda c: c["vm"] - 1,
       lambda c: (f"\"{c['d_vm']}\" = {_VM[c['vm']]} = {c['vm']}. Escada do ventilador: tolera 1, tosse mas tolera 2, "
                  "briga 3, impossível ventilar 4.")),
    No("total", "Soma", "Some os três itens (vai de 3 a 12). O que a BPS diz?",
       [("Sem dor relevante", "BPS ≤ 5", "f_bps_sem", None),
        ("Dor", "BPS > 5", "f_bps_dor", None)],
       lambda c: 0 if _bps(c) <= 5 else 1,
       lambda c: (f"Face {c['face']} + membros {c['mmss']} + ventilador {c['vm']} = {_bps(c)}. "
                  + ("Acima de 5: dor." if _bps(c) > 5 else "5 ou menos: sem dor relevante (o corte é MAIOR que 5)."))),
    Folha("f_bps_sem", "Sem dor", "BPS ≤ 5: sem dor relevante, manter a analgesia e reavaliar",
          "Reavalie a cada turno e antes de procedimentos dolorosos (aspiração, mudança de decúbito, curativo): "
          "analgesia antes do procedimento evita o pico de dor."),
    Folha("f_bps_dor", "Dor", "BPS > 5: dor, tratar com opioide antes de mexer no sedativo e reavaliar a BPS",
          "Analgesia primeiro (analgossedação): muito 'agitado' na UTI está com dor. Reavalie a BPS no pico do opioide "
          "(poucos minutos no IV); subir o sedativo para dor só esconde a dor."),
    Folha("f_bps_auto", "Autorrelato", "Paciente comunica: usar o autorrelato (escala numérica 0–10, apontada se intubado)",
          "O autorrelato é o padrão-ouro da dor. Intubado e desperto (RASS perto de 0) aponta a nota numa prancheta: "
          "a BPS só entra quando ele não consegue relatar."),
    Folha("f_bps_bnm", "Bloqueador", "Sob bloqueador neuromuscular a BPS não vale: garantir analgesia e sedação profundas",
          "Paralisado, a BPS dá 3 com qualquer dor. Antes e durante o bloqueio, analgesia e sedação profundas fixas; "
          "taquicardia e hipertensão sugerem, mas não medem, a dor."),
]

_CTX_BPS = ["Pós-operatório de laparotomia, 2º dia de UTI, intubado.", "Politrauma com fratura de fêmur, intubado.",
            "Pneumonia grave em ventilação mecânica, 3º dia.", "Pós-operatório de cirurgia cardíaca, intubado."]
_MOMENTO = ["em repouso", "durante a aspiração traqueal", "na mudança de decúbito", "no curativo da ferida operatória"]
_COMUNICA = ["Intubado, desperto, aponta números numa prancheta", "Traqueostomizado, responde por gestos e escreve",
             "Extubado ontem, conversa normalmente"]
_BNM = ["Cisatracúrio em infusão (SDRA grave)", "Rocurônio em infusão (hipertensão intracraniana)"]


def _gerar_bps(rng, alvo):
    c = {"comunica": None, "bnm": None, "momento": rng.choice(_MOMENTO)}
    texto = rng.choice(_CTX_BPS)
    if alvo == "f_bps_auto":
        c["comunica"] = rng.choice(_COMUNICA)
    elif alvo == "f_bps_bnm":
        c["bnm"] = rng.choice(_BNM)
        texto = "SDRA grave, intubado." if "SDRA" in c["bnm"] else "TCE grave com hipertensão intracraniana, intubado."
    if c["bnm"]:
        c["face"] = c["mmss"] = c["vm"] = 1              # paralisado: tudo "relaxado", a armadilha
    else:
        # sorteia o total primeiro (o corte 5 × 6 aparece mais) e depois três itens que somam isso
        alvo_n = (rng.randint(3, 12) if c["comunica"] else
                  rng.choice([6, 6, 7, 7, 8, 9, 10, 11, 12]) if alvo == "f_bps_dor" else rng.choice([3, 4, 4, 5, 5]))
        while True:
            c["face"], c["mmss"], c["vm"] = rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4)
            if _bps(c) == alvo_n:
                break
    for k, d in (("face", _DESC_FACE), ("mmss", _DESC_MMSS), ("vm", _DESC_VM)):
        c["d_" + k] = rng.choice(d[c[k]])
    if c["bnm"]:
        c["d_face"], c["d_mmss"], c["d_vm"] = "imóvel", "imóveis", "sincronizado (paralisado)"
    c["texto"] = f"{texto} Avaliação {c['momento']}."
    c["mostrar"] = [("Comunicação", c["comunica"] or "não comunica"), ("Bloqueador", c["bnm"] or "não"),
                    ("Rosto", c["d_face"]), ("Braços", c["d_mmss"]), ("Ventilador", c["d_vm"])]
    return c


BPS = Arvore("bps", "1 · BPS: pontuar a dor do intubado",
             "Treino FAST HUG · escala certa → face → membros superiores → ventilador → soma (> 5 é dor)",
             "escala", BPS_NOS, _gerar_bps,
             ["f_bps_dor", "f_bps_sem", "f_bps_dor", "f_bps_sem", "f_bps_auto", "f_bps_bnm"],   # mais casos de contar
             lambda c: [] if c["comunica"] or c["bnm"] else [("BPS", fi(_bps(c)))], grupo="uti_treino")
BPS.nos["total"].calc = _c_bps
BPS.descritivo = True

# ================================================================== 2. RASS (a profundidade da sedação)

_RASS = {4: "combativo", 3: "muito agitado", 2: "agitado", 1: "inquieto", 0: "alerta e calmo", -1: "sonolento",
         -2: "sedação leve", -3: "sedação moderada", -4: "sedação profunda", -5: "não desperta"}


def _r(n):
    return f"RASS {n:+d} ({_RASS[n]})".replace("+0", "0").replace("-", "−")


def _alvo(c):
    return (-5, -4) if c["profunda"] else (-2, 0)


def _conduta(c):
    lo, hi = _alvo(c)
    if c["rass"] >= 1:
        return 2
    if lo <= c["rass"] <= hi:
        return 0
    return 1 if c["rass"] < lo else 3


RASS_NOS = [
    No("olhar", "1 · Observar", "Passo 1 · Observe sem tocar nem chamar: ele está acordado?",
       [("Acordado", "olhos abertos sozinho", "acordado", None),
        ("Não está alerta", "olhos fechados", "voz", None)],
       lambda c: 0 if c["rass"] >= 0 else 1,
       lambda c: f"Ao observar: \"{c['d_obs']}\". " + ("Acordado sem estímulo: RASS de 0 a +4." if c["rass"] >= 0 else
                                                      "Não está alerta: chame pela voz (passo 2).")),
    No("acordado", "Acordado", "Acordado: como ele se comporta?",
       [("RASS 0", "calmo", "conduta", _r(0)),
        ("RASS +1", "inquieto, sem vigor", "conduta", _r(1)),
        ("RASS +2", "sem propósito, briga c/ VM", "conduta", _r(2)),
        ("Agressivo", "arranca tubo ou agride", "agressivo", None)],
       lambda c: min(c["rass"], 3),
       lambda c: (f"\"{c['d_obs']}\": {_r(c['rass'])}. Ansioso sem vigor é +1; movimentos frequentes sem propósito ou "
                  "brigar com o ventilador é +2; puxar tubo ou agredir já é +3/+4.")),
    No("agressivo", "+3 ou +4?", "Agressivo: ele puxa dispositivos ou já é perigo imediato para a equipe?",
       [("RASS +3", "puxa tubo ou cateter", "f_rass_perigo", _r(3)),
        ("RASS +4", "violento, perigo à equipe", "f_rass_perigo", _r(4))],
       lambda c: c["rass"] - 3,
       lambda c: f"\"{c['d_obs']}\": {_r(c['rass'])}. Puxar ou arrancar dispositivo é +3; violência contra a equipe é +4."),
    No("voz", "2 · Voz", "Passo 2 · Chame pelo nome e peça para abrir os olhos e olhar para você. O que acontece?",
       [("RASS −1", "olha ≥ 10 s", "conduta", _r(-1)),
        ("RASS −2", "olha < 10 s", "conduta", _r(-2)),
        ("RASS −3", "abre sem olhar", "conduta", _r(-3)),
        ("Sem resposta", "→ estímulo físico", "fisico", None)],
       lambda c: min(-c["rass"] - 1, 3),
       lambda c: (f"Ao chamar: \"{c['d_voz']}\". " + (f"{_r(c['rass'])}." if c["rass"] >= -3 else
                  "Nenhuma resposta à voz: passe ao estímulo físico.")
                  + " A régua é o OLHAR: 10 s ou mais −1, menos de 10 s −2, abre sem olhar para você −3.")),
    No("fisico", "3 · Estímulo", "Passo 3 · Sacuda o ombro ou friccione o esterno. Responde?",
       [("RASS −4", "mexe ao toque", "conduta", _r(-4)),
        ("RASS −5", "nada, nem ao toque", "conduta", _r(-5))],
       lambda c: -c["rass"] - 4,
       lambda c: f"Ao estímulo físico: \"{c['d_fis']}\". {_r(c['rass'])}."),
    No("conduta", "Alvo", "Com o RASS na mão: como ele está em relação ao alvo deste paciente?",
       [("No alvo", "manter", "f_rass_alvo", None),
        ("Sedado demais", "abaixo do alvo", "f_rass_profundo", None),
        ("Agitado", "RASS +1 ou +2", "f_rass_agitado", None),
        ("Superficial", "pede profunda", "f_rass_leve", None)],
       _conduta,
       lambda c: (f"{_r(c['rass'])}; " + (f"há indicação de sedação profunda ({c['profunda']}): alvo −4 a −5." if c["profunda"] else
                                         "sem indicação de sedação profunda: alvo −2 a 0."))),
    Folha("f_rass_alvo", "No alvo", "RASS no alvo: manter a menor dose que o sustenta",
          "Com RASS de −3 para cima, aplique o CAM-ICU: delirium aparece justamente em quem está acordado o bastante "
          "para ser avaliado."),
    Folha("f_rass_profundo", "Sedado demais", "Sedado além do alvo: reduzir o sedativo (despertar diário) e reavaliar",
          "Sedação profunda sem indicação prolonga ventilação e UTI. Despertar diário junto com o TRE reduziu a "
          "mortalidade (Girard, Lancet 2008)."),
    Folha("f_rass_agitado", "Agitado", "Agitação: buscar a causa (dor pela BPS, delirium pelo CAM-ICU, hipóxia, abstinência) antes de sedar mais",
          "Agitação na UTI é sintoma: muitas vezes é dor ou delirium. Trate a causa; se precisar sedar, propofol ou "
          "dexmedetomidina em vez de benzodiazepínico."),
    Folha("f_rass_perigo", "Risco imediato", "RASS +3/+4: proteger o paciente e a equipe agora e tratar a causa",
          "Com +3/+4 não se compara com alvo: é risco de autoextubação e de agressão. Fixe tubo e cateteres, chame ajuda, "
          "trate dor, hipóxia e abstinência; se precisar sedar, prefira propofol ou dexmedetomidina ao benzodiazepínico."),
    Folha("f_rass_leve", "Superficial", "Indicação de sedação profunda e RASS acima do alvo: aprofundar até −4 a −5",
          "SDRA grave com bloqueador, hipertensão intracraniana e estado de mal pedem sedação profunda. Nunca paralise "
          "quem não está profundamente sedado: paralisado acordado é a pior experiência da UTI."),
]

_DESC_OBS = {4: ["chuta e tenta bater na equipe: perigo imediato", "violento, agrediu a enfermeira"],
             3: ["tenta arrancar o tubo e a sonda, agressivo", "puxou o cateter central, grita e empurra"],
             2: ["se debate sem objetivo e briga com o ventilador", "movimentos frequentes sem propósito, assincronia"],
             1: ["ansioso, mexe as mãos sem parar, sem agressividade", "inquieto, olha para todo lado, movimentos leves"],
             0: ["olhos abertos, calmo, acompanha a equipe com o olhar", "acordado e tranquilo, obedece comandos"]}
_OBS_DORME = ["olhos fechados, imóvel", "parado, olhos fechados, respira com o ventilador"]
_DESC_VOZ = {-1: ["abre os olhos e sustenta o olhar em você por mais de 10 s", "acorda e mantém o contato visual enquanto você fala"],
             -2: ["abre os olhos, olha para você e volta a dormir em segundos", "contato visual breve, menos de 10 s"],
             -3: ["mexe a cabeça e abre os olhos, mas não olha para você", "abre os olhos sem fixar o olhar em ninguém"],
             -4: ["nenhuma resposta ao chamado", "não se mexe ao ouvir o nome"]}
_DESC_FIS = {-4: ["ao friccionar o esterno, abre os olhos e mexe o braço", "mexe-se quando você sacode o ombro"],
             -5: ["nenhuma resposta nem à fricção do esterno", "imóvel mesmo com estímulo físico"]}
_CTX_RASS = ["Pneumonia grave, 4º dia de ventilação mecânica.", "Choque séptico em melhora, intubado.",
             "Pós-operatório de esofagectomia, intubado.", "Exacerbação de DPOC, intubado há 2 dias."]
_PROFUNDA = ["SDRA grave com bloqueador neuromuscular", "hipertensão intracraniana", "estado de mal epiléptico"]


def _gerar_rass(rng, alvo):
    c = {"profunda": None}
    if alvo == "f_rass_agitado":
        c["rass"] = rng.choice([1, 2])
        c["profunda"] = rng.choice(_PROFUNDA[1:]) if rng.random() < 0.15 else None
    elif alvo == "f_rass_perigo":
        c["rass"] = rng.choice([3, 4, 3])
    elif alvo == "f_rass_leve":
        c["profunda"] = rng.choice(_PROFUNDA)
        c["rass"] = rng.choice([-3, -2, -1, 0, -3])
    elif alvo == "f_rass_profundo":
        c["rass"] = rng.choice([-3, -4, -5, -3, -4])
    else:
        if rng.random() < 0.3:
            c["profunda"] = rng.choice(_PROFUNDA)
            c["rass"] = rng.choice([-4, -5])
        else:
            c["rass"] = rng.choice([0, -1, -2, -2, -1])
    n = c["rass"]
    c["d_obs"] = rng.choice(_DESC_OBS[n]) if n >= 0 else rng.choice(_OBS_DORME)
    c["d_voz"] = rng.choice(_DESC_VOZ[max(n, -4)]) if n < 0 else "não precisou: já está acordado"
    c["d_fis"] = rng.choice(_DESC_FIS[n]) if n <= -4 else "não precisou"
    c["texto"] = rng.choice(_CTX_RASS)
    if c["profunda"]:
        c["texto"] = {"SDRA grave com bloqueador neuromuscular": "SDRA grave, P/F 80, programado bloqueador neuromuscular.",
                      "hipertensão intracraniana": "TCE grave com PIC elevada, intubado.",
                      "estado de mal epiléptico": "Estado de mal epiléptico refratário, intubado."}[c["profunda"]]
    c["mostrar"] = [("1 · Ao observar", c["d_obs"]), ("2 · Ao chamar", c["d_voz"]), ("3 · Ao estímulo", c["d_fis"]),
                    ("Sed. profunda", c["profunda"] or "sem indicação")]
    return c


RASS = Arvore("rass", "2 · RASS: classificar a sedação",
              "Treino FAST HUG · observar → chamar pela voz → estímulo físico → comparar com o alvo",
              "olhar", RASS_NOS, _gerar_rass, ["f_rass_alvo", "f_rass_profundo", "f_rass_agitado", "f_rass_perigo", "f_rass_leve"],
              lambda c: [("Alvo", "−4 a −5" if c["profunda"] else "−2 a 0")],   # o RASS em si é a resposta
              grupo="uti_treino")

RASS.descritivo = True
UTI_TREINO = [BPS, RASS]
for _a in UTI_TREINO:
    for _n in _a.nos.values():
        if not _n.folha and not hasattr(_n, "calc"):
            _n.calc = None

# ------------------------------------------------------------------ mini-aulas (o porquê de cada passo)

AULAS = {
    "bps": {
        "escala": "A melhor medida de dor é o próprio paciente dizer. Se ele comunica (fala, escreve ou aponta), use a "
                  "escala numérica. A BPS é para o intubado que não consegue. Sob bloqueador neuromuscular, nenhuma "
                  "escala comportamental funciona.",
        "face": "O rosto denuncia a dor primeiro. Suba a escada: relaxado 1; sobrancelha abaixada (parcialmente tenso) 2; "
                "olhos apertados (totalmente tenso) 3; careta 4. Cada item vai de 1 a 4, nunca de 0.",
        "mmss": "Dor faz o braço se encolher. Parado 1; cotovelo um pouco dobrado 2; braço todo dobrado e dedos fechados 3; "
                "braços retraídos o tempo todo 4.",
        "vm": "Dor tira o paciente do ritmo do ventilador. Tolera 1; tosse mas tolera a maior parte do tempo 2; briga com o "
              "ventilador 3; impossível ventilar 4.",
        "total": "Some os três: vai de 3 (nada) a 12 (máximo). O corte é MAIOR que 5: 5 ainda não trata, 6 já é dor. "
                 "Armadilha: contar de 0 a 3 e achar que 3 de total é 'sem dor'.",
    },
    "rass": {
        "olhar": "O RASS se faz em 3 passos, do menor ao maior estímulo. Primeiro só olhe por uns 30 s: se está de olhos "
                 "abertos sem que ninguém chame, o RASS é 0 ou positivo.",
        "acordado": "Acordado, o que diferencia é o vigor. Calmo 0; ansioso com movimentos leves +1; movimentos frequentes "
                    "sem propósito ou brigando com o ventilador +2.",
        "agressivo": "+3 puxa ou arranca tubo, sonda e cateter; +4 é violência e perigo imediato para a equipe. Nos "
                     "dois, a conduta é imediata: nem se compara com o alvo.",
        "voz": "Não está alerta: chame pelo nome e peça para olhar para você. O que conta é o CONTATO VISUAL: 10 s ou mais "
               "−1; menos de 10 s −2; abre os olhos ou se mexe sem olhar para você −3.",
        "fisico": "Só se a voz falhou, toque: sacuda o ombro ou friccione o esterno. Qualquer movimento ou abertura ocular "
                  "−4; nada −5. Armadilha: estimular fisicamente quem respondeu à voz.",
        "conduta": "O alvo padrão é sedação leve, RASS −2 a 0. Só SDRA grave com bloqueador, hipertensão intracraniana e "
                   "estado de mal pedem −4 a −5. RASS +1 ou +2 é agitação, qualquer que seja o alvo.",
    },
}
for _a in UTI_TREINO:
    for _nid, _txt in AULAS[_a.id].items():
        _a.nos[_nid].aula = _txt
