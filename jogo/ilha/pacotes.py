"""Pacotes de conteúdo (um tema por arquivo JSON) — o que a edição Android baixa e atualiza.

Formato (pacotes/<id>/pacote.json), mais "versao":
  id, versao (int), titulo, descricao, sabor (paleta), cor [r,g,b], materia, niveis {"1": nome},
  gerador (opcional: nome em GERADORES — o modo Treino é código e só vem com o app),
  roteiro (opcional: [módulo, aula] — resumo da prova final e do Treino),
  treino_pilulas (opcional: [[módulo, aula], ...]), referencias [str],
  modulos [{id, nivel, titulo, aula [{titulo, pontos}], questoes}]
Questão: {id, enunciado, alts [[letra, texto]], gab, coment?}

Só dados: nada aqui executa código vindo de fora (regra do Google Play). Um tema novo chega
inteiro pelo pacote (Aprendizado + prova final); o Treino aparece se o app já tiver o gerador.

Ordem de busca: pacotes embutidos no app (pacotes/ na raiz) e os baixados (pasta de dados);
para o mesmo id vale a maior versão."""
import importlib
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBUTIDOS = os.path.join(RAIZ, "pacotes")
FORMATO = 1                      # versão do formato que este app entende

# nome do gerador no pacote -> módulo do Treino dentro do app
GERADORES = {"hipercalemia": "hiperk_treino", "gasometria": "gaso_treino", "ventilacao": "vent_treino",
             "farmaco_cardio": "fc_treino", "farmaco_atb": "fa_treino", "insuf_cardiaca": "ic_treino",
             "reumatologia": "reumatologia_treino", "internato_endo": "internato_endo_treino",
             "internato_cognicao": "internato_cognicao_treino", "internato_parkinson": "internato_parkinson_treino",
             "caso_pneumonia": "caso_pneumonia_treino", "caso_abscesso_renal": "caso_abscesso_renal_treino",
             "caso_graves": "caso_graves_treino", "caso_coledoco": "caso_coledoco_treino",
             "mfc_epidemio": "mfc_epidemio_treino", "mfc_sus": "mfc_sus_treino", "mfc_consulta": "mfc_consulta_treino", "mfc_vigilancia": "mfc_vigilancia_treino", "mfc_trabalhador": "mfc_trabalhador_treino", "mfc_indicadores": "mfc_indicadores_treino", "mfc_idoso": "mfc_idoso_treino", "mfc_etica": "mfc_etica_treino"}


class _Conteudo:
    """Imita a interface dos módulos de conteúdo (gasometria.py etc.) que menus.py usa."""

    def __init__(self, d):
        self.MATERIA = d.get("materia", d["titulo"])
        self.NIVEIS = {int(k): v for k, v in d.get("niveis", {}).items()} or {1: ""}
        self.MODULOS = []
        for m in d["modulos"]:
            m = dict(m)
            qs = []
            for q in m["questoes"]:
                q = dict(q)
                q["alts"] = [tuple(a) for a in q["alts"]]
                q.setdefault("coment", "")
                q.setdefault("imgs", [])
                q["materia"] = self.MATERIA
                q["subtema"] = m["titulo"]
                q.setdefault("assunto", d["titulo"])
                qs.append(q)
            m["questoes"] = qs
            m.setdefault("nivel", 1)
            m.setdefault("aula", [])
            self.MODULOS.append(m)
        self.POR_ID = {q["id"]: q for m in self.MODULOS for q in m["questoes"]}

    def todas(self):
        return [q for m in self.MODULOS for q in m["questoes"]]


class TemaPacote:
    """Adaptador: um pacote com a mesma cara do menus.Tema (C, T, pref, paleta, roteiro...)."""

    def __init__(self, d, origem):
        self.dados, self.origem = d, origem
        self.id, self.versao = d["id"], int(d.get("versao", 1))
        self.nome, self.descricao = d["titulo"], d.get("descricao", "")
        self.titulo_mundo = d.get("titulo_mundo") or f"Mundo da {self.nome}"
        self.chave = self.pref = d.get("prefixo", d["id"])
        self.paleta = d.get("sabor", 0)
        self.cor = tuple(d.get("cor", (120, 210, 255)))
        self.grupo = d.get("grupo")      # estágio do internato ("cm2", "mfc"); sem grupo = menu simples (edição pública)
        self.C = _Conteudo(d)
        self.T = None
        mod = GERADORES.get(d.get("gerador") or "")
        if mod:
            try:
                self.T = importlib.import_module("." + mod, __package__)
            except ImportError:
                self.T = None
        self.treino_pref = getattr(self.T, "PREFIXO", f"{self.pref}-treino") if self.T else None

    def _aula(self, par):
        try:
            return self.C.MODULOS[par[0]]["aula"][par[1]]
        except (IndexError, KeyError, TypeError):
            return None

    def roteiro(self):
        if self.dados.get("roteiro_pilulas"):        # resumo próprio do tema (ex.: ventilação)
            return list(self.dados["roteiro_pilulas"])
        a = self._aula(self.dados.get("roteiro"))
        return [a] if a else []

    def treino_pilulas(self):
        extra = [self._aula(p) for p in self.dados.get("treino_pilulas", [])]
        return self.roteiro() + [a for a in extra if a]


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    if int(d.get("formato", 1)) > FORMATO:
        raise ValueError("pacote de formato mais novo que o app")
    if not d.get("id") or not d.get("modulos"):
        raise ValueError("pacote sem id ou sem módulos")
    return d


def _da_pasta(pasta, origem):
    out = {}
    if not os.path.isdir(pasta):
        return out
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".json") or nome == "indice.json":
            continue
        try:
            d = ler(os.path.join(pasta, nome))
            out[d["id"]] = TemaPacote(d, origem)
        except Exception:
            continue                          # pacote corrompido/incompatível: ignora
    return out


def carregar(pasta_baixados=None):
    """Lista de TemaPacote, na ordem do campo 'ordem' (depois título)."""
    temas = _da_pasta(EMBUTIDOS, "app")
    if pasta_baixados:
        for k, t in _da_pasta(pasta_baixados, "baixado").items():
            if k not in temas or t.versao > temas[k].versao:
                temas[k] = t
    return sorted(temas.values(), key=lambda t: (t.dados.get("ordem", 99), t.nome))
