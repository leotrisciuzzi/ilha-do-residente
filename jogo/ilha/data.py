"""Fontes de questões + save local + cliente do LousaFPSServer.

Três fontes:
  - servidor: sessão SM-2 do LousaFPSServer (mesmo progresso do Lousa FPS)
  - listas:   banco banco de questões local, por matéria/subtema
  - provas:   provas reais (PSU-MG, SUS-SP) na ordem original
"""
import json
import os
import random
import re
import subprocess
import time
import urllib.request
import urllib.error

HOME = os.path.expanduser("~")
BANCO_DIR = os.path.join(HOME, "Apps/MedEsfinge/banco_questoes")
BANCO = os.path.join(BANCO_DIR, "banco_questoes.json")
PROVAS = os.path.join(BANCO_DIR, "provas_reais/provas_reais.json")
PSU25 = os.path.join(BANCO_DIR, "provas_reais/psu_mg_2025/psu_mg_2025.json")
SERVER_DIR = os.path.join(HOME, "Apps/LousaFPSServer")
SERVER_URL = os.environ.get("ILHA_SERVER", "http://127.0.0.1:5051")
SAVE_DIR = SAVE_DIR_PADRAO = os.path.join(HOME, ".local/share/ilha-do-residente")
SAVE_FILE = os.path.join(SAVE_DIR, "save.json")
CACHE_DIR = os.path.join(SAVE_DIR, "cache_imagens")

LETRAS = "ABCDE"

# Ligaduras quebradas pela extração dos PDFs ("de*nir", "a :exão", "\x1eho")
_FIXES = [
    (re.compile("\x1e"), "fi"), (re.compile("\x1f"), "fl"),
    (re.compile("ﬁ"), "fi"), (re.compile("ﬂ"), "fl"),
    (re.compile(r"(?<=[A-Za-zÀ-ú(])\*(?=[a-zà-ú])|(?<=[\s(])\*(?=[a-zà-ú])|^\*(?=[a-zà-ú])"), "fi"),
    (re.compile(r"(?<=\s):(?=[a-zà-ú])"), "fl"),
]


def limpar(texto):
    if not texto:
        return ""
    for rx, rep in _FIXES:
        texto = rx.sub(rep, texto)
    # quebras de linha do PDF no meio da frase viram espaço
    texto = re.sub(r"(?<![.:?!;])\n(?![A-E]\))", " ", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


_ALT_RX = re.compile(r"(?:^|\n)\s*\(?([A-E])[\)\.\-]\s+")


def separar_alternativas(enunciado):
    """Fallback quando a questão não tem dict de alternativas: elas estão
    embutidas no enunciado como linhas 'A) ...'."""
    partes = _ALT_RX.split(enunciado)
    if len(partes) < 5:
        return enunciado, {}
    corpo, alts = partes[0], {}
    for i in range(1, len(partes) - 1, 2):
        alts[partes[i]] = partes[i + 1].strip()
    return corpo, alts


def normalizar(qid, enunciado, alternativas, gabarito, imagens=(), materia=None,
               subtema=None, assunto=None, origem="", prev=0.0, extra=None):
    enunciado = enunciado or ""
    if not alternativas:
        enunciado, alternativas = separar_alternativas(enunciado)
    if not alternativas or gabarito not in alternativas:
        return None
    alts = [(k, limpar(alternativas[k])) for k in LETRAS if k in alternativas]
    q = {
        "id": str(qid), "enunciado": limpar(enunciado), "alts": alts,
        "gab": gabarito, "imgs": list(imagens or []), "materia": materia or "",
        "subtema": subtema or "", "assunto": assunto or "", "origem": origem,
        "prev": prev or 0.0,
    }
    if extra:
        q.update(extra)
    return q


# ------------------------------------------------------------- fontes locais

class Banco:
    def __init__(self):
        self.listas = {}     # materia -> subtema -> [q]
        self.provas = []     # [{nome, key, questoes}]
        self.erro = None
        from .gasometria import POR_ID as _gaso
        from .ventilacao import POR_ID as _vm
        from .hipercalemia import POR_ID as _k
        from .farmaco_cardio import POR_ID as _fc
        from .farmaco_atb import POR_ID as _fa
        from .insuf_cardiaca import POR_ID as _ic
        from .reumatologia import POR_ID as _reu
        from .internato_asma import POR_ID as _uas
        from .internato_dpoc import POR_ID as _udp
        from .internato_vm import POR_ID as _uvm
        from .internato_transf import POR_ID as _utr
        from .internato_reum import POR_ID as _urm
        from .internato_fa import POR_ID as _uac
        from .internato_endo import POR_ID as _uen
        from .internato_cognicao import POR_ID as _ucg
        from .internato_parkinson import POR_ID as _upk
        from .internato_nefro import POR_ID as _unf
        from .internato_has import POR_ID as _uha
        from .internato_hemato import POR_ID as _uhm
        from .internato_pneumo import POR_ID as _upn
        from .internato_neuro import POR_ID as _unr
        from .internato_dermato import POR_ID as _udm
        from .internato_hepato import POR_ID as _uhp
        from .internato_relatos import POR_ID as _url
        from .dia_temas import POR_ID as _dia
        from .caso_pneumonia import POR_ID as _cpn
        from .caso_abscesso_renal import POR_ID as _crn
        from .caso_graves import POR_ID as _cgr
        from .caso_coledoco import POR_ID as _cvb
        from .mfc_epidemio import POR_ID as _mep
        from .mfc_sus import POR_ID as _msu
        from .mfc_consulta import POR_ID as _mfc
        from .mfc_vigilancia import POR_ID as _mvg
        from .mfc_trabalhador import POR_ID as _mtr
        from .mfc_indicadores import POR_ID as _mid
        from .mfc_idoso import POR_ID as _mso
        from .mfc_etica import POR_ID as _met
        self.por_id = {**_gaso, **_vm, **_k, **_fc, **_fa, **_ic, **_reu, **_uas, **_udp, **_uvm, **_utr, **_urm, **_uac, **_uen, **_ucg, **_upk, **_unf, **_uha, **_uhm, **_upn, **_unr, **_udm, **_uhp, **_url, **_dia, **_cpn, **_crn, **_cgr, **_cvb, **_mep, **_msu, **_mfc, **_mvg, **_mtr, **_mid, **_mso, **_met}     # erros dos mundos temáticos também entram na "Revisão dos erros"
        try:
            self._carregar_listas()
        except Exception as e:  # banco ausente não impede o modo servidor
            self.erro = f"banco banco de questões: {e}"
        try:
            self._carregar_provas()
        except Exception as e:
            self.erro = (self.erro or "") + f" provas: {e}"

    def _carregar_listas(self):
        d = json.load(open(BANCO, encoding="utf-8"))
        for x in d["questoes"]:
            if x.get("tipo") != "multipla_escolha":
                continue
            q = normalizar(
                x["id"], x["enunciado"], x.get("alternativas"), x.get("gabarito"),
                x.get("imagens_arquivos"), x.get("materia"), x.get("subtema_arquivo"),
                x.get("assunto"), "banco de questões", x.get("prevalencia_geral_pct", 0))
            if q:
                self.listas.setdefault(q["materia"], {}).setdefault(q["subtema"], []).append(q)
                self.por_id[q["id"]] = q

    def _carregar_provas(self):
        provas = json.load(open(PROVAS, encoding="utf-8"))["provas"]
        try:
            p25 = json.load(open(PSU25, encoding="utf-8"))
            provas.append({"nome": "PSU-MG", "ano": p25["ano"], "banca": "PSU-MG",
                           "questoes": p25["questoes"]})
        except Exception:
            pass
        for p in provas:
            nome = f"{p['banca']} {p['ano']}"
            key = nome.lower().replace(" ", "-")
            qs = []
            for x in p["questoes"]:
                if x.get("tipo", "multipla_escolha") != "multipla_escolha" or x.get("anulada"):
                    continue
                q = normalizar(
                    f"{key}-{x['numero']}", x.get("enunciado"), x.get("alternativas"),
                    x.get("gabarito"), x.get("imagens_arquivos"), x.get("materia"),
                    None, x.get("assunto"), f"{nome} · Q{x['numero']}")
                if q:
                    qs.append(q)
                    self.por_id[q["id"]] = q
            if qs:
                self.provas.append({"nome": nome, "key": key, "questoes": qs})
        self.provas.sort(key=lambda p: p["nome"])

    def materias(self):
        return sorted(self.listas)

    def pool_materia(self, materia):
        return [q for qs in self.listas.get(materia, {}).values() for q in qs]

    def todas(self):
        return list(self.por_id.values())


# ---------------------------------------------------------------- save local

class Save:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.d = {"q": {}, "fases": {}, "gabaritos": {}, "config": {}, "jogador": ""}
        try:
            self.d.update(json.load(open(SAVE_FILE, encoding="utf-8")))
        except Exception:
            pass
        if "carteira" not in self.d:          # save antigo: os totais de questões saem do histórico
            c = sum(s.get("c", 0) for s in self.d["q"].values())
            e = sum(s.get("e", 0) for s in self.d["q"].values())
            self.d["carteira"] = {"moedas": 0, "creditos": c, "moedas_total": 0, "questoes_total": c + e, "acertos_total": c}

    # -- carteira: saldos (gastos na lojinha) e totais históricos (nunca diminuem)
    @property
    def carteira(self):
        return self.d["carteira"]

    def ganhar_moedas(self, n):
        if n > 0:
            self.carteira["moedas"] += n
            self.carteira["moedas_total"] += n
            self.salvar()

    def gastar(self, moedas=0, creditos=0):
        """Para a lojinha: debita se houver saldo. Devolve True se conseguiu."""
        c = self.carteira
        if c["moedas"] < moedas or c["creditos"] < creditos:
            return False
        c["moedas"] -= moedas
        c["creditos"] -= creditos
        self.salvar()
        return True

    def salvar(self):
        tmp = SAVE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.d, f, ensure_ascii=False)
        os.replace(tmp, SAVE_FILE)

    @property
    def config(self):
        return self.d["config"]

    def registrar(self, q, acertou):
        s = self.d["q"].setdefault(q["id"], {"c": 0, "e": 0, "ult": 0, "int": 0, "prox": 0})
        agora = time.time()
        if acertou:
            s["c"] += 1
            s["int"] = 1 if s["int"] == 0 else (6 if s["int"] == 1 else round(s["int"] * 2.3))
        else:
            s["e"] += 1
            s["int"] = 0
        s["ult"] = agora
        s["prox"] = agora + s["int"] * 86400
        s["ok"] = acertou
        c = self.carteira
        c["questoes_total"] += 1
        if acertou:
            c["acertos_total"] += 1
            c["creditos"] += 1                 # crédito de questão: 1 por acerto
        self.salvar()

    def stat(self, qid):
        return self.d["q"].get(qid)

    def gabarito(self, q):
        return self.d["gabaritos"].get(q["id"], q["gab"])

    def corrigir_gabarito(self, q, letra):
        self.d["gabaritos"][q["id"]] = letra
        self.salvar()

    def nota_fase(self, chave, pontos):
        antes = self.d["fases"].get(chave, 0)
        if pontos > antes:
            self.d["fases"][chave] = pontos
            self.salvar()
        return antes

    def melhor(self, chave):
        return self.d["fases"].get(chave)

    def erradas(self, banco):
        """Questões cuja última resposta foi erro — fonte do modo Revisão."""
        out = []
        for qid, s in self.d["q"].items():
            if not s.get("ok") and qid in banco.por_id:
                out.append(banco.por_id[qid])
        return out

    def resumo(self, qs):
        c = e = 0
        for q in qs:
            s = self.d["q"].get(q["id"])
            if s:
                c += 1 if s.get("ok") else 0
                e += 0 if s.get("ok") else 1
        return c, e


def escolher(pool, n, save, rng=None):
    """Escolhe n questões: erradas antes primeiro, depois nunca vistas
    pesadas por prevalência, por último as já acertadas há mais tempo."""
    rng = rng or random.Random()
    erradas, novas, vistas = [], [], []
    for q in pool:
        s = save.stat(q["id"])
        if s is None:
            novas.append(q)
        elif not s.get("ok"):
            erradas.append(q)
        else:
            vistas.append(q)
    rng.shuffle(erradas)
    out = erradas[: max(1, n // 3)] if erradas else []
    # amostragem ponderada sem reposição (Efraimidis-Spirakis)
    chave = lambda q: rng.random() ** (1.0 / (0.3 + q.get("prev", 0)))
    novas.sort(key=chave, reverse=True)
    out += novas[: n - len(out)]
    if len(out) < n:
        vistas.sort(key=lambda q: save.stat(q["id"])["ult"])
        out += vistas[: n - len(out)]
    if len(out) < n:
        out += erradas[len(out):n]
    rng.shuffle(out)
    return out[:n]


# ------------------------------------------------------- LousaFPSServer

class Servidor:
    """Cliente mínimo do LousaFPSServer — usa a mesma sessão SM-2 do Lousa FPS."""

    def __init__(self, url=SERVER_URL):
        self.url = url.rstrip("/")
        self.jogador_id = None
        self.nome = None
        self.processo = None  # se fomos nós que subimos o servidor

    def _req(self, caminho, corpo=None, timeout=8):
        dados = None if corpo is None else json.dumps(corpo).encode()
        req = urllib.request.Request(self.url + caminho, data=dados,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def online(self):
        try:
            self._req("/api/versao", timeout=1.5)
            return True
        except Exception:
            return False

    def garantir_online(self):
        """Sobe o servidor local se ele não estiver rodando (e derruba ao sair)."""
        if self.online():
            return True
        py = os.path.join(SERVER_DIR, "venv/bin/python")
        if not os.path.exists(py) or "127.0.0.1" not in self.url:
            return False
        log = open(os.path.join(SAVE_DIR, "servidor.log"), "a")
        self.processo = subprocess.Popen(
            [py, "fps_server.py", "--porta", self.url.rsplit(":", 1)[1]],
            cwd=SERVER_DIR, stdout=log, stderr=log, start_new_session=True)
        for _ in range(40):
            time.sleep(0.25)
            if self.online():
                return True
        return False

    def encerrar(self):
        if self.processo and self.processo.poll() is None:
            self.processo.terminate()

    def entrar(self, nome):
        r = self._req("/api/jogador", {"nome": nome})
        self.jogador_id, self.nome = r["jogador_id"], r["nome"]
        return r

    def mapa(self):
        return self._req(f"/api/mapa?jogador_id={self.jogador_id}", timeout=30)

    def responder(self, q, acertou):
        try:
            self._req("/api/resposta", {"jogador_id": self.jogador_id,
                                        "questao_id": q["server_qid"],
                                        "tema_id": q["tema_id"], "acertou": acertou})
            return True
        except Exception:
            return False

    def corrigir_gabarito(self, q, letra):
        try:
            self._req("/api/corrigir_gabarito", {"questao_id": q["server_qid"], "gabarito": letra})
            return True
        except Exception:
            return False

    def pontuacao(self, pontos, extra=""):
        try:
            self._req("/api/recursos", {"jogador_id": self.jogador_id,
                                        "moedas": int(pontos), "xp": int(pontos)})
        except Exception:
            pass

    def imagem_local(self, caminho):
        os.makedirs(CACHE_DIR, exist_ok=True)
        destino = os.path.join(CACHE_DIR, caminho.strip("/").replace("/", "_") + ".png")
        if not os.path.exists(destino):
            try:
                with urllib.request.urlopen(self.url + caminho, timeout=8) as r:
                    open(destino, "wb").write(r.read())
            except Exception:
                return None
        return destino

    def temas_da_sessao(self):
        """Converte o mapa (pirâmide de temas) em fases: um tema = uma fase."""
        m = self.mapa()
        fases = []
        pontos = {p["id"]: p for p in m.get("pontos", [])}
        for tema_id, itens in m.get("questoes_por_tema", {}).items():
            p = pontos.get(tema_id) or {}
            qs = []
            for it in itens:
                if it.get("anulada"):
                    continue
                imgs = [i for i in (self.imagem_local(c) for c in it.get("imagens", [])) if i]
                q = normalizar(
                    f"srv-{it['questao_id']}", it.get("enunciado"), it.get("alternativas"),
                    it.get("gabarito"), imgs, p.get("disciplina"), p.get("label"), None,
                    f"{it.get('prova') or ''} {it.get('ano') or ''} · Q{it.get('numero')}".strip(),
                    extra={"server_qid": it["questao_id"], "tema_id": tema_id,
                           "revisao": bool(it.get("revisao"))})
                if q:
                    qs.append(q)
            if qs:
                fases.append({"tema_id": tema_id, "nome": p.get("label", f"Tema {tema_id}"),
                              "area": p.get("area") or p.get("disciplina") or "",
                              "nivel": p.get("nivel", 0), "questoes": qs})
        fases.sort(key=lambda f: (f["nivel"], -len(f["questoes"])))
        return m, fases


class SemServidor:
    """Edição sem rede: mesma interface do Servidor, sem fazer nada."""
    jogador_id = None
    nome = None

    def __getattr__(self, nome):
        return lambda *a, **k: None
