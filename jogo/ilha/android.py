"""Menus da edição Android: um mundo por pacote de conteúdo (Aprendizado + Treino + Prova final),
atualizados sozinhos pela internet (atualizador.py)."""
import os

import pygame

from . import edicao, pacotes
from .atualizador import Atualizador
from .menus import abrir_aprendizado, abrir_treino, prova_tema, _dominadas, item_continuar, escolher_estilo, _estilo_item
from .ui import Menu, Mensagem
from .personagens import abrir_escolha
try:
    from .conta_ui import item_menu          # conta no servidor da Ilha: só no APK pessoal
except ImportError:
    def item_menu(app):
        return None

AJUDA = """NA FASE (como no Super Mario Run, sem controle na tela): o Doutor corre sozinho. TOQUE em qualquer lugar pula; segure para pular mais alto e, no ar, planar. DESLIZE o dedo: ← ou → vira e volta a correr · ↓ para (no ar: pisão; continue segurando para abaixar) · ↑ ataque do pet (o gato dá um bote: derruba o germe e abre o bicho-questão; sem pet, quem anda a pé golpeia com o bastão) · na diagonal ataca para esse lado · → de novo no sentido em que já corre: DASH. No ar contra a parede: desliza; toque para pular da parede. O pisão quica no inimigo e no espinho (pogo). ALMA (círculo no alto): enche batendo e acertando; com 1/3, deslize ↓ e segure parado para focar e ganhar uma vida. Ao morrer, as moedas ficam com a sua SOMBRA: encoste nela para recuperar. Pets e acessórios: na Loja, com moedas. II no canto pausa (o botão voltar do Android também).

NOS MENUS: toque para escolher, arraste para rolar. Voltar do Android volta.

QUESTÕES: toque na alternativa para marcar e depois em CONFIRMAR; leia o comentário e toque em CONTINUAR.

BICHOS-QUESTÃO (placa ?): acerte com o bote do pet, o bastão ou o pisão para abrir a questão. Acertou: vira FLOR (+3 estrelas). Errou: ele te acerta e o Doutor cai do pônei numa bolha — pegue a bolha antes de a contagem zerar.
GIGANTE: guarda o anel final; cada bote, golpe ou pisão nele abre uma questão.
PONTOS (100): estrelas (30) + 5 fichas-coração (20) + acertos (50).

Controle Bluetooth/USB também funciona."""

AVISO = ("Jogo educativo para estudantes de medicina e residentes. O conteúdo é didático: não substitui o "
         "julgamento clínico, a bula nem as diretrizes vigentes, e não deve ser usado para decidir condutas.")


def _pasta_pacotes():
    from . import data
    return os.path.join(data.SAVE_DIR, "pacotes")


def _creditos(temas):
    linhas = [f"{edicao.NOME} · versão {edicao.VERSAO}", f"Criado por {edicao.AUTOR}.", "", AVISO, ""]
    for t in temas:
        linhas.append(f"{t.nome}: conteúdo v{t.versao} ({'atualizado pela internet' if t.origem == 'baixado' else 'do app'})")
    linhas += ["", "Feito com Python, pygame-ce (LGPL 2.1), SDL 2 (zlib), NumPy (BSD) e a fonte DejaVu. "
               "Trilhas: composições originais e arranjos de obras em domínio público.", "",
               edicao.LICENCA]
    return "\n".join(linhas)


def abrir_mundo(app, t):
    """Ao selecionar o tema: primeiro o estilo (com diversão ou sem risadinha), depois os modos."""
    escolher_estilo(app, t.titulo_mundo[:38], lambda: _abrir_modos(app, t))


def _abrir_modos(app, t):
    menu = Menu(app, t.titulo_mundo[:38], [], t.descricao)

    def montar():
        C = t.C
        tot = len(C.todas())
        ok = sum(_dominadas(app, m) for m in C.MODULOS)
        menu.itens = [{"label": "Modo Aprendizado", "cor": (120, 210, 255), "acao": lambda: abrir_aprendizado(app, t),
                       "info": f"{len(C.MODULOS)} módulos com aula antes e comentário depois · {ok}/{tot} dominadas"}]
        if t.T:
            tr_c = tr_e = 0
            for h in t.T.HABILIDADES:
                s = app.save.stat(f"{t.treino_pref}:{h}") or {}
                tr_c, tr_e = tr_c + s.get("c", 0), tr_e + s.get("e", 0)
            tr = (f"{tr_c + tr_e} casos · {round(100 * tr_c / (tr_c + tr_e))}% de acerto" if tr_c + tr_e
                  else "nenhum caso ainda")
            menu.itens.append({"label": "Modo Treino", "cor": (140, 230, 140), "acao": lambda: abrir_treino(app, t),
                               "info": f"Casos gerados na hora, infinitos · {tr}"})
        menu.itens.append({"label": "Prova final", "cor": (200, 160, 250), "acao": lambda: prova_tema(app, t),
                           "info": "10 questões de todos os módulos, erros e inéditas primeiro"})
        menu.itens.append(_estilo_item(app, t, abrir_mundo))
        menu.itens.append({"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


class MenuAndroid(Menu):
    def __init__(self, app):
        super().__init__(app, "Ilha do Residente", [], "")
        self.baixador = None              # código novo do app pelo servidor (só APK pessoal, com conta)
        try:
            from . import atualiza_app, data
            atualiza_app.marcar_ok(data.SAVE_DIR)    # chegou ao menu: a versão que está rodando abriu bem
            if app.conta:
                self.baixador = atualiza_app.Baixador(app.conta, data.SAVE_DIR)
                self.baixador.iniciar()
        except ImportError:
            pass
        self.atual = Atualizador(_pasta_pacotes(), edicao.VERSAO, conta=app.conta)
        self.temas = pacotes.carregar(self.atual.pasta)
        self.atual.iniciar({t.id: t.versao for t in self.temas})
        self._estado_visto = None
        self._montar()

    def _status(self):
        a = self.atual
        if a.estado == "buscando":
            return "Buscando conteúdo…"
        if a.estado == "ok":
            return ("Novo: " + ", ".join(a.novos))[:40] if a.novos else "Conteúdo em dia"
        if a.estado == "offline":
            return "Sem internet"
        if a.estado == "erro":
            return "Conteúdo não atualizado"
        return ""

    def _montar(self):
        app = self.app
        c = app.save.carteira
        pct = f" ({round(100 * c['acertos_total'] / c['questoes_total'])}%)" if c["questoes_total"] else ""
        cart = f"Moedas: {c['moedas']:,} · Créditos: {c['creditos']:,} · {c['questoes_total']:,} questões{pct}".replace(",", ".")
        self.subtitulo = " · ".join(x for x in (cart, self._status(), self._sinc()) if x)
        self.itens = []
        cont = item_continuar(app, self.temas)
        if cont:
            self.itens.append(cont)
            alvo = cont["label"] + cont.get("info", "")
            if alvo != getattr(self, "_cont", None):      # destino novo: já deixa selecionado
                self._cont, self.sel, self._ysel = alvo, 0, 0.0
        self.itens.append({"label": "Mapa de Estudos", "cor": (110, 200, 255),
                           "info": "Tudo num mapa: o que já estudou, o que dominou, o que pede revisão",
                           "acao": lambda: __import__("ilha.mapa", fromlist=["abrir"]).abrir(app, self.temas)})
        if any(t.grupo for t in self.temas):        # APK pessoal: um item por estágio do internato
            cm2 = [t for t in self.temas if t.grupo != "mfc"]
            mfc = [t for t in self.temas if t.grupo == "mfc"]
            self.itens += [
                {"secao": "Internato", "label": ""},
                {"label": "Internato · Clínica Médica 2", "cor": (255, 210, 120),
                 "info": _resumo(app, cm2, "Prova, casos da enfermaria, mundos, fluxogramas e ECG"),
                 "acao": lambda: _abrir_estagio(app, "Internato · Clínica Médica 2", cm2, True)},
                {"label": "Internato · MFC", "cor": (140, 220, 140),
                 "info": _resumo(app, mfc, "Medicina de Família e Comunidade: os mundos entram conforme as aulas"),
                 "acao": lambda: _abrir_estagio(app, "Internato · MFC", mfc, False)},
            ]
        else:
            self.itens.append({"secao": "Aprenda um tema a fundo", "label": ""})
            self.itens += _itens_mundos(app, self.temas)
            if not self.temas:
                self.itens.append({"label": "Nenhum tema ainda", "desab": True,
                                   "info": "Conecte-se à internet e abra o jogo de novo para baixar os temas"})
            self.itens += [{"secao": "Treine o raciocínio", "label": ""}] + _itens_raciocinio(app)
        self.itens += [
            {"secao": "Um espaço à parte", "label": ""},
            {"label": "O Mirante", "cor": (190, 170, 255),
             "info": "Feito pelo Claude: um lago à noite cujo céu são as questões que você já respondeu",
             "acao": lambda: __import__("ilha.mirante", fromlist=["abrir"]).abrir(app)},
            {"secao": "Seu Doutor e ajustes", "label": ""},
            {"label": "Personagem e loja", "info": "Trocar de personagem e comprar nuvens, bastões e roupas com moedas",
             "acao": lambda: abrir_escolha(app), "cor": (255, 170, 210)},
        ]
        conta = item_menu(app)
        if conta:
            self.itens.append(conta)
        self.itens += [
            {"label": "Como jogar", "cor": (255, 255, 255), "info": "Gestos (sem controle na tela) e regras",
             "acao": lambda: app.push(Mensagem(app, "Como jogar", AJUDA))},
            {"label": f"Som: {'desligado' if app.audio.mudo else 'ligado'}", "cor": (140, 230, 140),
             "info": "Música e efeitos", "acao": self._som},
            {"label": "Sobre", "cor": (255, 220, 100), "info": f"Versão {edicao.VERSAO} · aviso e créditos",
             "acao": lambda: app.push(Mensagem(app, "Sobre", _creditos(self.temas)))},
        ]
        self.sel = min(self.sel, len(self.itens) - 1)
        self._pular_desab(1)

    def _som(self):
        self.app.save.config["mudo"] = self.app.audio.alternar_mudo()
        self.app.save.salvar()
        self._montar()

    def update(self, inp):
        b = self.baixador
        if b and b.estado == "baixada" and not b.avisado:
            b.avisado = True
            self.app.toast(f"Versão {b.versao_nova} baixada: feche e abra o jogo para usar")
        if self.atual.mudou:
            self.atual.mudou = False
            self.temas = pacotes.carregar(self.atual.pasta)
            self.sel = 0
            self._montar()
            self.app.toast("Conteúdo novo: " + ", ".join(self.atual.novos))
        elif self._estado_visto != (self.atual.estado, self._sinc()):
            self._estado_visto = (self.atual.estado, self._sinc())
            self._montar()
        super().update(inp)

    def _sinc(self):
        return self.app.sincronia.status(curto=True) if self.app.sincronia else ""

    def ao_voltar(self):
        self._montar()

    def ao_conectar(self):
        """Entrou numa conta: busca os temas (e o código novo do app) no servidor da Ilha."""
        if self.baixador:
            self.baixador.iniciar()
        self.atual.conta = self.app.conta
        self.atual.iniciar({t.id: t.versao for t in self.temas})

    def evento(self, e, inp):
        if inp.foi("voltar"):            # padrão do Android: voltar duas vezes (em 2 s) sai do jogo
            agora = pygame.time.get_ticks()
            if agora - getattr(self, "_voltar_t", -10000) < 2000:
                self.app.save.salvar()
                self.app.rodando = False
            else:
                self._voltar_t = agora
                self.app.toast("Toque em voltar de novo para sair")
            return
        super().evento(e, inp)


def _resumo(app, temas, padrao):
    if not temas:
        return padrao
    tot = sum(len(t.C.todas()) for t in temas)
    ok = sum(_dominadas(app, m) for t in temas for m in t.C.MODULOS)
    return f"{len(temas)} mundos · {ok}/{tot} dominadas · {padrao}"


def _itens_mundos(app, temas):
    itens = []
    for t in temas:
        tot = len(t.C.todas())
        ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
        itens.append({"label": t.titulo_mundo, "cor": t.cor, "acao": (lambda t=t: abrir_mundo(app, t)),
                      "info": f"{t.descricao[:70]} · {ok}/{tot} dominadas"})
    return itens


def _itens_raciocinio(app):
    return [
        {"label": "Fluxogramas do raciocínio", "cor": (120, 200, 255),
         "info": "Gasometria, eletrólitos, asma, FAST HUG e espirometria: caso a caso",
         "acao": lambda: __import__("ilha.fluxograma", fromlist=["abrir"]).abrir(app)},
        {"label": "Leitura de ECG", "cor": (255, 140, 140),
         "info": "Tira de DII longo: bloqueios, FA, flutter, taquicardias e ritmos de parada, com as medidas do traçado",
         "acao": lambda: __import__("ilha.ecg_treino", fromlist=["abrir"]).abrir(app)}]


def _abrir_estagio(app, titulo, temas, raciocinio):
    """Submenu de um estágio do internato: os mundos dele (e, na CM 2, os fluxogramas e o ECG)."""
    menu = Menu(app, titulo, [], "")

    def montar():
        menu.itens = [{"secao": "Mundos", "label": ""}] + _itens_mundos(app, temas)
        if not temas:
            menu.itens.append({"label": "Nenhum mundo ainda", "desab": True,
                               "info": "Os módulos entram aqui a partir das aulas do estágio"})
        if raciocinio:
            menu.itens += [{"secao": "Treine o raciocínio", "label": ""}] + _itens_raciocinio(app)
        menu.itens.append({"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop})
        menu._pular_desab(1)

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def _fluxos_internato(app):
    from . import fluxograma
    fluxograma.abrir(app, grupos=fluxograma.INTERNATO, titulo="Fluxogramas",
                     sub="Asma, DPOC, VM, transfusão e reumatologia: percorra o fluxograma caso a caso")


def menu_android(app):
    return MenuAndroid(app)
