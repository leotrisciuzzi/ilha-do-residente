"""Atualização automática do conteúdo (edição Android).

Ao abrir o jogo, em segundo plano: baixa <URL>/indice.json, compara as versões e baixa só os
pacotes novos/alterados para a pasta de dados, conferindo o SHA-256 antes de trocar o arquivo
(gravação atômica: .tmp + os.replace). Sem internet, segue com o que já tem.

indice.json: {"formato": 1, "pacotes": [{"id", "versao", "arquivo", "sha256", "app_min",
"titulo"}]} — app_min é a versão mínima do app (pacote que exige motor novo espera o app
ser atualizado pela loja)."""
import hashlib
import json
import os
import ssl
import threading
import urllib.request

URL_PADRAO = "https://raw.githubusercontent.com/leotrisciuzzi/ilha-do-residente-conteudo/main"
TEMPO = 8


def _versao_tupla(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


_CTX = []


def _contexto():
    """Certificados para HTTPS: o Python do Android não acha os do sistema sozinho. Tenta o
    certifi (vai no APK), depois a pasta de certificados do Android, depois o padrão."""
    if not _CTX:
        ctx = None
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            if os.path.isdir("/system/etc/security/cacerts"):
                try:
                    ctx = ssl.create_default_context(capath="/system/etc/security/cacerts")
                except Exception:
                    ctx = None
        _CTX.append(ctx or ssl.create_default_context())
    return _CTX[0]


def _baixar(url, token=None):
    h = {"User-Agent": "IlhaDoResidente", "Cache-Control": "no-cache"}
    if token:
        h["Authorization"] = "Bearer " + token          # servidor da Ilha: temas só para quem tem conta
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=TEMPO, context=_contexto() if url.startswith("https") else None) as r:
        return r.read()


class Atualizador:
    def __init__(self, pasta, versao_app, url=None, conta=None):
        self.pasta = pasta
        self.conta = conta              # com conta: temas do servidor da Ilha (todos os temas, PC e celular)
        self.versao_app = versao_app
        self.url = (url or os.environ.get("ILHA_CONTEUDO_URL") or URL_PADRAO).rstrip("/")
        self.estado = "parado"          # parado | buscando | ok | offline | erro
        self.novos = []                 # títulos atualizados nesta sessão
        self.mudou = False              # o menu relê os pacotes quando vira True
        self.erro = ""
        self._fio = None

    def locais(self):
        """{id: versao} dos pacotes já baixados."""
        out = {}
        if os.path.isdir(self.pasta):
            for n in os.listdir(self.pasta):
                if n.endswith(".json"):
                    try:
                        with open(os.path.join(self.pasta, n), encoding="utf-8") as f:
                            d = json.load(f)
                        out[d["id"]] = int(d.get("versao", 1))
                    except Exception:
                        pass
        return out

    def iniciar(self, versoes_atuais=None):
        if self._fio and self._fio.is_alive():
            self._de_novo = versoes_atuais or {}       # ex.: entrou na conta durante a busca: busca de novo
            return
        self._de_novo = None
        self._fio = threading.Thread(target=self._rodar_e_repetir, args=(versoes_atuais or {},), daemon=True)
        self._fio.start()

    def _rodar_e_repetir(self, versoes):
        while versoes is not None:
            self.rodar(versoes)
            versoes, self._de_novo = getattr(self, "_de_novo", None), None

    def rodar(self, versoes_atuais):
        self.estado = "buscando"
        url, tok = self.url, None
        if self.conta and self.conta.logado and not os.environ.get("ILHA_CONTEUDO_URL"):
            u = self.conta.endereco()
            if u:
                url, tok = u + "/api/temas", self.conta.d.get("token")
        try:
            indice = json.loads(_baixar(url + "/indice.json", tok).decode("utf-8"))
        except Exception as e:
            self.estado, self.erro = "offline", str(e)[:120]
            return
        try:
            os.makedirs(self.pasta, exist_ok=True)
            atuais = dict(versoes_atuais)
            for k, v in self.locais().items():
                atuais[k] = max(v, atuais.get(k, 0))
            for p in indice.get("pacotes", []):
                if _versao_tupla(p.get("app_min", "0")) > _versao_tupla(self.versao_app):
                    continue
                if int(p["versao"]) <= atuais.get(p["id"], 0):
                    continue
                dados = _baixar(f"{url}/{p['arquivo']}", tok)
                if hashlib.sha256(dados).hexdigest() != p["sha256"]:
                    raise ValueError(f"hash não confere: {p['id']}")
                d = json.loads(dados.decode("utf-8"))
                if d.get("id") != p["id"]:
                    raise ValueError(f"id não confere: {p['id']}")
                destino = os.path.join(self.pasta, f"{p['id']}.json")
                with open(destino + ".tmp", "wb") as f:
                    f.write(dados)
                os.replace(destino + ".tmp", destino)
                self.novos.append(p.get("titulo", p["id"]))
                self.mudou = True
            self.estado = "ok"
        except Exception as e:
            self.estado, self.erro = "erro", str(e)[:120]
