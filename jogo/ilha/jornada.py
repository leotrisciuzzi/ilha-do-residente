"""Jornada: todo o conteúdo do jogo num só mapa, organizado por especialidade (o "reino"), para saber o que já foi
estudado, o que foi dominado e o que pede revisão.

Hierarquia (como o mapa do Super Mario Bros. Wonder): reino (especialidade) → ilha (trilha: um tema do cronograma,
um mundo a fundo, os fluxogramas, as questões por prevalência) → fase (nó do caminho).

Estado de cada fase (escala de domínio no molde da Khan Academy, com o decaimento da revisão espaçada):
    0 · não começou       nenhuma questão respondida
    1 · começou           respondeu parte
    2 · concluída         passou por todas as questões da fase (ou marcou "estudei fora do jogo")
    3 · dominada          a última resposta de todas as questões foi certa
  + pede revisão          alguma questão já respondida errou por último ou venceu o intervalo do SM-2
  + atrasada              aula do cronograma com data já passada e ainda não concluída
O que conta é o save (questões e recordes de fase), que já sincroniza entre PC e celular. A marca manual fica em
save.d["fases"]["marca:<fase>"] como contador de cliques (ímpar = marcada): o recorde de fase sincroniza pelo maior
valor, então desmarcar também chega no outro aparelho."""
import datetime as dt
import time
import unicodedata

REINOS = ["Cardiologia", "Pneumologia", "Terapia Intensiva", "Nefrologia", "Endocrinologia", "Neurologia",
          "Reumatologia", "Hematologia", "Infectologia", "Gastroenterologia", "Hepatologia", "Dermatologia",
          "Psiquiatria", "Cirurgia", "Pediatria", "Ginecologia", "Obstetrícia", "Medicina Preventiva", "Ortopedia",
          "Oftalmologia", "Otorrinolaringologia"]

_NOMES = {"gastrologia": "Gastroenterologia", "preventiva": "Medicina Preventiva", "obstetricia": "Obstetrícia",
          "otorrinologia": "Otorrinolaringologia", "gasometria": "Terapia Intensiva",
          "ventilacao mecanica": "Terapia Intensiva", "antibioticos": "Infectologia",
          "farmacologia cardiovascular": "Cardiologia"}
_TEMA_REINO = {"gaso": "Terapia Intensiva", "vm": "Terapia Intensiva", "uvm": "Terapia Intensiva",
               "fc": "Cardiologia", "fa": "Infectologia"}
_FLUXO_REINO = {"acidobase": "Terapia Intensiva", "hipoxemia": "Pneumologia", "anemias": "Hematologia",
                "eletrolitos": "Nefrologia", "asma": "Pneumologia", "espiro": "Pneumologia", "uti": "Terapia Intensiva",
                "uti_treino": "Terapia Intensiva", "internato_asma": "Pneumologia", "internato_dpoc": "Pneumologia",
                "internato_vm": "Terapia Intensiva", "internato_transf": "Hematologia", "internato_reumato": "Reumatologia",
                "internato_fa": "Cardiologia"}

BIOMAS = ["prado", "cerejeira", "praia", "outono", "neve", "cristal", "selva", "deserto"]
ROTULO = {0: "Ainda não começou", 1: "Começou", 2: "Concluída", 3: "Dominada"}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def reino_de(materia):
    k = sem_acento(materia or "").lower().strip()
    if k in _NOMES:
        return _NOMES[k]
    for r in REINOS:
        if sem_acento(r).lower() == k:
            return r
    return (materia or "Outros").strip() or "Outros"


# ------------------------------------------------------------------ fases

class Fase:
    """Um nó do mapa. tipo: questoes (estado pelas questões), aula (aula do cronograma: estado pelo recorde),
    treino, fluxo, ecg. jogar(app) abre a fase."""

    def __init__(self, fid, nome, tipo, jogar, qs=None, chave=None, data=None, extra=None, icone="fase"):
        self.id, self.nome, self.tipo, self.jogar = fid, nome, tipo, jogar
        self.qs, self.chave, self.data, self.extra, self.icone = qs or [], chave, data, extra, icone


class Trilha:
    def __init__(self, tid, nome, tipo, fases, sub=""):
        self.id, self.nome, self.tipo, self.fases, self.sub = tid, nome, tipo, fases, sub


class Reino:
    def __init__(self, nome):
        self.nome, self.trilhas = nome, []
        self.ordem = 10 ** 6
        self.bioma = BIOMAS[(REINOS.index(nome) if nome in REINOS else len(nome)) % len(BIOMAS)]

    @property
    def fases(self):
        return [f for t in self.trilhas for f in t.fases]


def marcada(save, fase):
    return save.d["fases"].get("marca:" + fase.id, 0) % 2 == 1


def alternar_marca(save, fase):
    save.d["fases"]["marca:" + fase.id] = save.d["fases"].get("marca:" + fase.id, 0) + 1
    save.salvar()
    return marcada(save, fase)


def estado(save, fase, agora=None, hoje=None):
    """{nivel 0–3, revisar (nº de questões vencidas/erradas), atrasada, feitas, total, dom, ult (timestamp)}."""
    agora = agora or time.time()
    hoje = hoje or dt.date.today()
    e = {"nivel": 0, "revisar": 0, "atrasada": False, "feitas": 0, "total": 0, "dom": 0, "ult": 0,
         "marcada": marcada(save, fase)}
    q = save.d["q"]
    if fase.tipo == "questoes":
        e["total"] = len(fase.qs)
        for qid in fase.qs:
            s = q.get(qid)
            if not s or s.get("c", 0) + s.get("e", 0) == 0:
                continue
            e["feitas"] += 1
            e["dom"] += 1 if s.get("ok") else 0
            e["revisar"] += 1 if s.get("prox", 0) <= agora else 0
            e["ult"] = max(e["ult"], s.get("ult", 0))
        if e["total"] and e["dom"] == e["total"]:
            e["nivel"] = 3
        elif e["total"] and e["feitas"] == e["total"]:
            e["nivel"] = 2
        elif e["feitas"]:
            e["nivel"] = 1
    elif fase.tipo == "aula":
        b = save.d["fases"].get(fase.chave)
        e["total"] = 1
        if b is not None:
            e["feitas"] = 1
            e["nivel"] = 3 if b >= 80 else 2
            e["dom"] = 1 if b >= 80 else 0
    elif fase.tipo == "treino":
        habs = fase.extra["habilidades"]
        e["total"] = len(habs)
        bons = 0
        for h in habs:
            s = q.get(f"{fase.extra['pref']}:{h}") or {}
            n = s.get("c", 0) + s.get("e", 0)
            e["feitas"] += 1 if n >= 3 else 0
            bons += 1 if n >= 5 and s.get("c", 0) >= 0.8 * n else 0
            e["ult"] = max(e["ult"], s.get("ult", 0))
            if n:
                e["nivel"] = max(e["nivel"], 1)
        e["dom"] = bons
        if bons == len(habs):
            e["nivel"] = 3
        elif e["feitas"] == len(habs):
            e["nivel"] = 2
    elif fase.tipo == "fluxo":
        st = save.d.get("fluxos", {}).get(fase.extra, {})
        e["total"], e["feitas"] = 4, min(4, st.get("nivel", 1)) if st.get("casos") else 0
        if st.get("casos"):
            e["nivel"] = 3 if st.get("nivel", 1) >= 3 else (2 if st.get("perfeitos", 0) >= 3 or st.get("nivel", 1) >= 2 else 1)
        e["dom"] = 1 if e["nivel"] == 3 else 0
    elif fase.tipo == "ecg":
        st = save.d.get("ecg", {})
        ritmos = fase.extra
        e["total"] = len(ritmos)
        e["feitas"] = sum(1 for r in ritmos if sum(st.get(r, [0, 0])) > 0)
        e["dom"] = sum(1 for r in ritmos if sum(st.get(r, [0, 0])) >= 3 and st[r][0] >= 0.8 * sum(st[r]))
        if e["dom"] == len(ritmos):
            e["nivel"] = 3
        elif e["feitas"] == len(ritmos):
            e["nivel"] = 2
        elif e["feitas"]:
            e["nivel"] = 1
    if e["marcada"] and e["nivel"] < 2:
        e["nivel"] = 2
    if fase.data and fase.data < hoje and e["nivel"] < 2:
        e["atrasada"] = True
    if e["nivel"] < 2:
        e["revisar"] = 0          # revisão só conta no que você já passou inteiro: antes disso, é continuar
    return e


def resumo(save, fases, agora=None):
    """Totais de um conjunto de fases (uma ilha, um reino, o mapa todo)."""
    agora = agora or time.time()
    es = [estado(save, f, agora) for f in fases]
    return {"n": len(es), "comecou": sum(1 for e in es if e["nivel"] >= 1),
            "concl": sum(1 for e in es if e["nivel"] >= 2), "dom": sum(1 for e in es if e["nivel"] == 3),
            "revisar": sum(1 for e in es if e["revisar"]), "atrasadas": sum(1 for e in es if e["atrasada"]),
            "ult": max([e["ult"] for e in es] or [0])}


def proxima(save, fases):
    """Índice da fase recomendada: a atrasada mais antiga; senão a primeira não concluída; senão a que pede revisão."""
    es = [estado(save, f) for f in fases]
    for cond in (lambda e: e["atrasada"], lambda e: e["nivel"] < 2, lambda e: e["revisar"]):
        for i, e in enumerate(es):
            if cond(e):
                return i
    return 0


# ------------------------------------------------------------------ catálogo

def _trilhas_temas(reinos, temas=None):
    """temas: os mundos a fundo (no PC, os do menu; no Android, os pacotes baixados, que têm a mesma interface)."""
    from . import menus
    internato = {t.chave for t in menus.INTERNATO_CM2}
    for t in temas if temas is not None else menus.TEMAS + menus.FARMACOS + menus.INTERNATO_CM2:
        try:
            C, T = t.C, t.T
        except Exception:
            continue                       # edição sem este mundo
        fases = []
        for k, m in enumerate(C.MODULOS):
            fases.append(Fase(f"{t.pref}:{m['id']}", f"{m['nivel']}-{k + 1}. {m['titulo']}", "questoes",
                              (lambda app, t=t, k=k: menus.jogar_modulo(app, t, k)),
                              qs=[q["id"] for q in m["questoes"]], chave=f"{t.pref}:{m['id']}"))
        if T:
            fases.append(Fase(f"{t.pref}:treino", "Treino infinito", "treino",
                              (lambda app, t=t: menus.abrir_treino(app, t)),
                              extra={"pref": t.treino_pref, "habilidades": list(T.HABILIDADES)}, icone="treino"))
        fases.append(Fase(f"{t.pref}:final", "Prova final", "questoes", (lambda app, t=t: menus.prova_tema(app, t)),
                          qs=[q["id"] for q in C.todas()], chave=f"{t.pref}:final", icone="castelo"))
        r = _TEMA_REINO.get(t.chave) or reino_de(C.MATERIA)
        u = t.chave in internato
        _reino(reinos, r).trilhas.append(Trilha("tema:" + t.chave, t.nome, "internato" if u else "tema", fases,
                                                "Internato · aula, treino e prova" if u else
                                                "Mundo a fundo · aula, treino e prova"))


def _trilhas_fluxos(reinos):
    try:
        from . import fluxograma
        from .fluxo_dados import ARVORES
    except Exception:
        return
    por = {}
    for a in ARVORES:
        r = _FLUXO_REINO.get(a.id) or _FLUXO_REINO.get(a.grupo) or "Terapia Intensiva"
        por.setdefault(r, []).append(Fase("fluxo:" + a.id, a.nome, "fluxo",
                                          (lambda app, a=a: fluxograma._abrir_arvore(app, a)), extra=a.id,
                                          icone="fluxo"))
    for r, fases in por.items():
        _reino(reinos, r).trilhas.append(Trilha("fluxos:" + r, "Fluxogramas", "fluxo", fases,
                                                "O raciocínio caixa a caixa, do mapa aberto ao de memória"))


def _trilha_ecg(reinos):
    try:
        from . import ecg_treino
    except Exception:
        return
    _reino(reinos, "Cardiologia").trilhas.append(Trilha("ecg", "Leitura de ECG", "ecg", [
        Fase("ecg", "Os 12 ritmos do DII longo", "ecg", lambda app: ecg_treino.abrir(app),
             extra=list(ecg_treino.CRITERIO), icone="ecg")], "Bloqueios, FA, flutter, taquicardias e parada"))


def _trilhas_clinica(reinos):
    try:
        from . import menus
        cp = menus._clinica()
    except Exception:
        return
    for i, a in enumerate(cp["areas"]):
        fases = [Fase(f"cm-prev:{a['materia']}:{k}", " + ".join(f["subtemas"]), "questoes",
                      (lambda app, i=i, k=k: menus.jogar_clinica(app, i, k)), qs=[q["id"] for q in f["questoes"]],
                      chave=f"cm-prev:{a['materia']}:{k}", icone="prova")
                 for k, f in enumerate(a["fases"])]
        _reino(reinos, reino_de(a["materia"])).trilhas.append(
            Trilha("prev:" + a["materia"], "O que mais cai na prova", "prev", fases,
                   f"Questões reais 2024–2026 · {a['pct']:.0f}% da clínica"))


def _trilhas_agenda(reinos, mundos):
    from . import agenda, menus
    for i, m in enumerate(mundos):
        fases = [Fase("agenda:" + menus._chave_aula(m, a).split(":", 1)[1], a["nome"], "aula",
                      (lambda app, i=i, k=k: jogar_aula(app, mundos, i, k)), chave=menus._chave_aula(m, a),
                      data=a["data"], icone="aula")
                 for k, a in enumerate(m["aulas"])]
        vistos = set()                     # duas grafias da mesma aula dão a mesma chave de progresso: fica uma
        fases = [f for f in fases if not (f.id in vistos or vistos.add(f.id))]
        r = _reino(reinos, reino_de(m["materia"]))
        r.ordem = min(r.ordem, m["data"].toordinal())
        nome = agenda.assunto_do_tema(m["tema"]).strip(" -—")
        if sum(ch.isalpha() for ch in nome) < 6:            # tema sem nome na agenda (ex.: "NEURO -")
            nome = f"{m['materia']} · {m['data']:%d/%m}"
        r.trilhas.append(Trilha("agenda:" + agenda.slug(m["tema"]), nome.title()[:60],
                                "agenda", fases, f"Cronograma · a partir de {m['data']:%d/%m}"))


def jogar_aula(app, mundos, i, k):
    """Aula do cronograma: precisa do casador (índice do banco); na 1ª vez monta com a tela de espera."""
    from . import agenda, menus
    from .ui import Carregando
    if getattr(app, "_casador", None) is not None and app._casador._idx is not None:
        menus.jogar_aula(app, mundos, i, k)
        return

    def tarefa():
        if getattr(app, "_casador", None) is None:
            app._casador = agenda.Casador(app.banco)
        app._casador.indice()

    app.push(Carregando(app, "Separando as questões da aula", tarefa,
                        lambda _r, erro: None if erro else menus.jogar_aula(app, mundos, i, k)))


def _reino(reinos, nome):
    if nome not in reinos:
        reinos[nome] = Reino(nome)
    return reinos[nome]


def catalogo(com_agenda=True, temas=None, com_clinica=True):
    """[Reino] na ordem do cronograma (o reino que aparece primeiro na agenda vem primeiro); os que não estão na
    agenda seguem a ordem de REINOS. Dentro do reino: cronograma (por data), mundos a fundo, fluxogramas, ECG,
    prevalência."""
    reinos = {}
    mundos = []
    if com_agenda:
        try:
            from . import agenda
            mundos = agenda.carregar()
        except Exception:
            mundos = []
        _trilhas_agenda(reinos, mundos)
    _trilhas_temas(reinos, temas)
    _trilhas_fluxos(reinos)
    _trilha_ecg(reinos)
    if com_clinica:
        _trilhas_clinica(reinos)
    ordem_tipo = {"agenda": 0, "tema": 1, "internato": 2, "fluxo": 3, "ecg": 4, "prev": 5}
    out = []
    for r in reinos.values():
        r.trilhas.sort(key=lambda t: ordem_tipo.get(t.tipo, 9))
        r.trilhas = [t for t in r.trilhas if t.fases]
        if r.trilhas:
            out.append(r)
    pos = {n: i for i, n in enumerate(REINOS)}
    out.sort(key=lambda r: (r.ordem, pos.get(r.nome, 99), r.nome))
    return out


# ------------------------------------------------------------------ diário: o que estudei em cada dia

def diario(save, reinos, dias=14, hoje=None):
    """[(data, [(reino, trilha, fase, respondidas, certas)])] dos últimos dias, pelo horário da última resposta de
    cada questão (o save guarda só a última, então uma questão revista hoje sai do dia em que foi vista antes)."""
    hoje = hoje or dt.date.today()
    dono = {}
    for r in reinos:
        for t in r.trilhas:
            for f in t.fases:
                for qid in f.qs:
                    if f.icone != "castelo":            # a prova final repete as questões dos módulos
                        dono.setdefault(qid, (r, t, f))
    por_dia = {}
    for qid, s in save.d["q"].items():
        if not s.get("ult") or qid not in dono:
            continue
        d = dt.date.fromtimestamp(s["ult"])
        if (hoje - d).days >= dias:
            continue
        r, t, f = dono[qid]
        c = por_dia.setdefault(d, {}).setdefault(f.id, [r, t, f, 0, 0])
        c[3] += 1
        c[4] += 1 if s.get("ok") else 0
    return [(d, sorted((tuple(v) for v in por_dia[d].values()), key=lambda x: -x[3])) for d in sorted(por_dia, reverse=True)]
