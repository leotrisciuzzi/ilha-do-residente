"""Fluxos de menu: servidor (Lousa FPS), listas, provas, revisão, estatísticas."""
import threading
import zlib

import pygame

from . import art, data
from .ui import (carteira_txt, titulo_px, Menu, Mensagem, Carregando, EntradaTexto, Estado, painel, sombra,
                 quebrar, W, H, TINTA, AMARELO, VERDE, VERMELHO)
from .personagens import abrir_escolha

POR_FASE = 6
POR_CASTELO = 8

AJUDA = """MOVER: setas / WASD (ou analógico)
PULAR: Z, Espaço ou K — SEGURE no ar para o voo agitado (flutter)
ATAQUE: X ou J (ou clique do mouse) — o pet dá um bote para a frente: abre bichos-questão e derruba germes (que viram moeda). Sem pet, quem anda a pé golpeia com o bastão. Pets, coleiras e chapéus: na Loja, com moedas.
DASH: C, L ou Shift (ou botão direito) — rápido e reto; um por pulo, recarrega no chão ou na parede.
PAREDE: no ar, empurre contra a parede para deslizar devagar; pule para saltar dela (dá para subir pulando de uma parede a outra).
POGO: o pisão quica no inimigo e no espinho sem te ferir.
ALMA (círculo embaixo da estrela): enche batendo em bichos e acertando questões. Com 1/3 cheia, segure ↓ parado no chão para FOCAR e ganhar uma vida.
SOMBRA: ao morrer, as moedas da fase ficam com a sua sombra onde você caiu. Encoste nela para recuperar; morrer de novo antes disso faz perder.
PISÃO: ↓ no ar — esmaga germes e abre bichos
PAUSA: Esc / P · SOM: M · TELA CHEIA: F11
CONTROLE (SNES): B pula (segure = flutter) · Y ataque do pet · A ou X dash · ↓ no ar pisão · ↓ parado no chão foca · START pausa · SELECT volta / corrige gabarito · L/R rolam textos

BICHOS-QUESTÃO (placa ?): acerte com o bote do pet, o bastão ou o pisão para abrir a questão. Acertou: vira FLOR (+3 estrelas). Errou: ele te acerta e o Doutor cai do pônei numa bolha.
DOUTOR: se ele cair, as estrelas viram contagem regressiva. Pegue a bolha antes do zero!
GIGANTE: guarda o anel final. Cada bote, golpe ou pisão nele abre uma questão.
BLOCO AMARELO: bata de baixo e ele solta moedas.
PONTOS (100): estrelas (30) + 5 fichas-coração (20) + acertos (50).
QUIZ: A–E ou 1–5 respondem · G corrige o gabarito ao vivo · I amplia a imagem."""


def _carregar_banco(app):
    if app.banco is None and not getattr(app, "_carregando_banco", False):
        app._carregando_banco = True

        def rodar():
            app.banco = data.Banco()
        threading.Thread(target=rodar, daemon=True).start()


class MenuPrincipal(Menu):
    def __init__(self, app):
        super().__init__(app, "Ilha do Residente", [], "O Doutor montado no pônei branco × questões de residência")
        self._montar()

    def _montar(self):
        app = self.app
        self.subtitulo = carteira_txt(app.save)
        pronto = app.banco is not None
        esp = "" if pronto else "  (carregando banco…)"
        n_err = len(app.save.erradas(app.banco)) if pronto else 0
        from .conta_ui import item_menu
        conta = item_menu(app)                         # servidor da Ilha: progresso igual em todos os aparelhos
        from . import dia
        self.itens = [
            {"label": "Mundo do Dia" + esp, "arcoiris": pronto, "cor": (255, 120, 200),
             "info": dia.resumo_menu(app), "acao": lambda: dia.abrir(app), "desab": not pronto},
            {"label": "Mapa de Estudos", "cor": (110, 200, 255),
             "info": "Tudo num mapa por especialidade: o que já estudou, o que dominou, o que pede revisão",
             "acao": lambda: __import__("ilha.mapa", fromlist=["abrir"]).abrir(app)},
            {"secao": "Siga a sua agenda", "label": ""},
            {"label": "Cronograma de Estudos" + esp, "info": "Sua agenda do Lousa: um mundo por tema, uma fase por videoaula",
             "acao": lambda: abrir_cronograma(app), "desab": not pronto, "cor": (255, 180, 80)},
            {"secao": "Internato", "label": ""},
            {"label": "Internato · Clínica Médica 2", "cor": (255, 210, 120),
             "info": "Tudo o que foi estudado de clínica: prova de CM, casos da enfermaria, mundos dos temas, "
                     "farmacologia, fluxogramas e ECG",
             "acao": lambda: abrir_internato(app)},
            {"label": "Internato · MFC", "cor": (140, 220, 140),
             "info": abrir_mfc_info(app), "acao": lambda: abrir_mfc(app)},
            {"secao": "Questões reais de prova", "label": ""},
            {"label": "Castelos das Provas" + esp, "info": "PSU-MG e SUS-SP reais, na ordem da prova, 8 questões por castelo",
             "acao": lambda: abrir_provas(app), "desab": not pronto, "cor": (240, 160, 110)},
            {"label": "Ilhas das Listas" + esp, "info": "Banco banco de questões: uma ilha por matéria, uma fase por subtema",
             "acao": lambda: abrir_listas(app), "desab": not pronto, "cor": (140, 220, 120)},
            {"label": "Mistão por prevalência" + esp, "info": "Questões de todas as matérias, pesadas pelo que mais cai",
             "acao": lambda: abrir_mistao(app), "desab": not pronto, "cor": (200, 160, 250)},
            {"secao": "Revise", "label": ""},
            {"label": "Revisão dos erros" + esp, "info": f"{n_err} questões cuja última resposta foi errada",
             "acao": lambda: abrir_revisao(app), "desab": not pronto or not n_err, "cor": (250, 120, 150)},
            {"label": "Sessão do Lousa FPS", "info": "Mesma revisão SM-2 e progresso do LousaFPSServer: um tema por fase",
             "acao": lambda: abrir_servidor(app), "cor": (120, 200, 255)},
            {"label": "Estatísticas", "info": "Acertos por matéria e recordes", "acao": lambda: app.push(Estatisticas(app)),
             "desab": not pronto, "cor": (255, 220, 100)},
            {"secao": "Um espaço à parte", "label": ""},
            {"label": "O Mirante", "cor": (190, 170, 255),
             "info": "Feito pelo Claude: um lago à noite cujo céu são as questões que você já respondeu",
             "acao": lambda: __import__("ilha.mirante", fromlist=["abrir"]).abrir(app)},
            {"label": "O Recife", "cor": (110, 210, 230),
             "info": "Feito pelo Claude: nade no fundo do mar; cada coral é um mundo seu, branco onde você errou",
             "acao": lambda: __import__("ilha.recife", fromlist=["abrir"]).abrir(app)},
            {"label": "O Trem da Madrugada", "cor": (240, 180, 120),
             "info": "Feito pelo Claude: quatro vagões, malas com os seus mundos e o dia nascendo pela janela",
             "acao": lambda: __import__("ilha.trem", fromlist=["abrir"]).abrir(app)},
            {"label": "As Ilhas do Céu", "cor": (255, 190, 200),
             "info": "Feito pelo Claude: pule e plane entre ilhas flutuantes, uma por mundo estudado",
             "acao": lambda: __import__("ilha.ilhas_ceu", fromlist=["abrir"]).abrir(app)},
            {"secao": "Seu Doutor e ajustes", "label": ""},
            {"label": "Personagem e loja", "info": "Trocar de personagem e comprar nuvens, bastões e roupas com moedas",
             "acao": lambda: abrir_escolha(app), "cor": (255, 170, 210)},
            *([conta] if conta else []),
            {"label": "Controle", "info": self._info_controle(),
             "acao": app.configurar_controle, "cor": (160, 160, 200)},
            {"label": "Como jogar", "info": "Controles e regras", "acao": lambda: app.push(Mensagem(app, "Como jogar", AJUDA)),
             "cor": (255, 255, 255)},
            {"label": "Sair", "acao": lambda: setattr(app, "rodando", False), "cor": (180, 180, 180)},
        ]
        cont = item_continuar(app, TEMAS + FARMACOS + INTERNATO_CM2 + INTERNATO_MFC)
        if cont:
            self.itens.insert(1, cont)                 # o Mundo do Dia fica sempre em primeiro
            alvo = cont["label"] + cont.get("info", "")
            if alvo != getattr(self, "_cont", None):      # destino novo: já deixa selecionado
                self._cont, self.sel, self._ysel = alvo, 0, 0.0
        self.sel = min(self.sel, len(self.itens) - 1)
        self._pular_desab(1)
        self._pronto = pronto
        self._n_pads = len(app.pad.conectados())

    def _info_controle(self):
        js = self.app.pad.conectados()
        if js:
            return f"Conectado: {js[0].get_name()} · Enter para remapear os botões"
        return "Nenhum controle conectado (é detectado ao plugar, sem reiniciar o jogo)"

    def update(self, inp):
        if self._pronto != (self.app.banco is not None) or self._n_pads != len(self.app.pad.conectados()):
            self._montar()
        super().update(inp)

    def ao_voltar(self):
        self._montar()

    def evento(self, e, inp):
        if inp.foi("voltar"):
            return
        super().evento(e, inp)


def menu_principal(app):
    _carregar_banco(app)
    return MenuPrincipal(app)


def _paleta_de(texto):
    return zlib.crc32(texto.encode()) % 20


def _melhor(app, chave):
    b = app.save.melhor(chave)
    return f"★ {b}" if b is not None else ""


# ------------------------------------------------------------------ cronograma

def abrir_cronograma(app):
    from . import agenda

    def tarefa():
        if getattr(app, "_casador", None) is None:
            app._casador = agenda.Casador(app.banco)
            app._casador.indice()
        return agenda.carregar()

    def pronto(mundos, erro):
        if erro or not mundos:
            app.push(Mensagem(app, "Cronograma indisponível",
                              f"Não consegui ler a agenda em {agenda.AGENDA}. {erro or ''}"))
            return
        _menu_cronograma(app, mundos)

    app.push(Carregando(app, "Organizando o cronograma", tarefa, pronto))


def _chave_aula(m, a):
    from .agenda import slug
    return f"agenda:{slug(m['tema'])}:{slug(a['nome'])}"


def _menu_cronograma(app, mundos):
    from . import agenda
    hoje = agenda.indice_hoje(mundos)
    menu = Menu(app, "Cronograma", [], "")

    def montar():
        feitas_total = sum(1 for m in mundos for a in m["aulas"] if app.save.melhor(_chave_aula(m, a)) is not None)
        n_total = sum(len(m["aulas"]) for m in mundos)
        menu.subtitulo = f"{len(mundos)} mundos · {n_total} fases · {feitas_total} concluídas"
        menu.itens = [{"label": "▶ Continuar de onde parei", "info": "Próxima aula ainda não concluída a partir de hoje",
                       "cor": AMARELO, "acao": continuar}]
        for i, m in enumerate(mundos):
            feitas = sum(1 for a in m["aulas"] if app.save.melhor(_chave_aula(m, a)) is not None)
            marca = "HOJE" if i == hoje else ("✔" if feitas == len(m["aulas"]) else "")
            menu.itens.append({
                "label": f"{m['data']:%d/%m} · {m['tema']}",
                "info": f"Mundo {i + 1} · {len(m['aulas'])} aulas · {feitas} concluídas",
                "dir": marca, "cor": art.paleta(_paleta_de(m["materia"]))["acento"],
                "acao": (lambda i=i: abrir_mundo(app, mundos, i))})

    def continuar():
        for i in list(range(hoje, len(mundos))) + list(range(0, hoje)):
            m = mundos[i]
            for k, a in enumerate(m["aulas"]):
                if app.save.melhor(_chave_aula(m, a)) is None:
                    jogar_aula(app, mundos, i, k)
                    return
        app.push(Mensagem(app, "Tudo concluído", "Você já passou por todas as fases do cronograma."))

    menu.ao_voltar = montar
    montar()
    menu.sel = hoje + 1
    app.push(menu)


def abrir_mundo(app, mundos, i):
    m = mundos[i]
    menu = Menu(app, m["tema"].split("—")[-1].strip()[:38], [], f"{m['tema']} · a partir de {m['data']:%d/%m/%Y}")

    def montar():
        menu.itens = []
        for k, a in enumerate(m["aulas"]):
            b = app.save.melhor(_chave_aula(m, a))
            menu.itens.append({"label": f"{k + 1}. {a['nome']}", "info": f"Aula de {a['data']:%d/%m}",
                               "dir": f"★ {b}" if b is not None else "",
                               "cor": VERDE if b is not None else art.paleta(_paleta_de(m["materia"]))["acento"],
                               "acao": (lambda k=k: jogar_aula(app, mundos, i, k))})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def jogar_aula(app, mundos, i, k):
    from . import agenda
    m = mundos[i]
    a = m["aulas"][k]
    pool = app._casador.questoes(m, a)
    qs = data.escolher(pool, POR_FASE, app.save)
    if k + 1 < len(m["aulas"]):
        prox = lambda: jogar_aula(app, mundos, i, k + 1)
    elif i + 1 < len(mundos):
        prox = lambda: jogar_aula(app, mundos, i + 1, 0)
    else:
        prox = None
    titulo = f"{m['materia']} · {a['nome']}"
    app.jogar(qs, titulo, _chave_aula(m, a), f"Mundo {i + 1}-{k + 1}", _paleta_de(m["materia"]),
              proxima=prox, repetir=lambda: jogar_aula(app, mundos, i, k),
              briefing={"titulo": f"Mundo {i + 1}-{k + 1} · {a['nome']}", "materia": m["materia"],
                        "texto": a["nome"], "extra": agenda.assunto_do_tema(m["tema"]),
                        "pdf": agenda.pdf_resumo(a, m)})


# ------------------------------------------------------------------ temas (gasometria, ventilação)

class Tema:
    """Um 'mundo' de três modos: Aprendizado (módulos com aula), Treino (casos gerados) e Bancas
    (questões reais do banco). `pref` monta as chaves de progresso: '<pref>:<módulo>',
    '<pref>-bancas:<grupo>'; o Treino usa as do próprio gerador ('<PREFIXO>:<habilidade>')."""

    def __init__(self, chave, nome, pref, conteudo, treino, bancas, treino_pref, paleta, cor, desc_bancas,
                 roteiro, treino_pilulas):
        self.chave, self.nome, self.pref = chave, nome, pref
        self._c, self._t, self._b = conteudo, treino, bancas
        self.treino_pref, self.paleta, self.cor, self.desc_bancas = treino_pref, paleta, cor, desc_bancas
        self._roteiro, self._treino_pilulas = roteiro, treino_pilulas

    def _mod(self, nome):
        import importlib
        return importlib.import_module("." + nome, __package__)

    @property
    def C(self):
        return self._mod(self._c)

    @property
    def T(self):
        return self._mod(self._t)

    @property
    def B(self):
        return self._mod(self._b)

    def roteiro(self):
        return self._roteiro(self.C)

    def treino_pilulas(self):
        return self._treino_pilulas(self.C)


def _gaso_roteiro(G):
    return [G.MODULOS[5]["aula"][2]]          # a pílula "O roteiro em seis passos" inteira (padrão didático)


GASO = Tema("gaso", "Gasometria", "gaso", "gasometria", "gaso_treino", "gaso_bancas", "gaso-treino", 4, (90, 220, 210),
            "Questões reais com gasometria: provas PSU-MG/SUS-SP + banco banco de questões",
            _gaso_roteiro, lambda G: _gaso_roteiro(G) + [G.MODULOS[7]["aula"][0], G.MODULOS[7]["aula"][1]])
VENT = Tema("vm", "Ventilação Mecânica", "vm", "ventilacao", "vent_treino", "vent_bancas", "vm-treino", 5, (150, 190, 255),
            "Questões reais de ventilação, VNI, via aérea, SDRA e desmame: provas + banco banco de questões",
            lambda V: V.ROTEIRO, lambda V: V.ROTEIRO + [V.MODULOS[8]["aula"][1], V.MODULOS[4]["aula"][1]])
HIPERK = Tema("k", "Hipercalemia", "k", "hipercalemia", "hiperk_treino", "hiperk_bancas", "k-treino", 3, (255, 150, 120),
              "Questões reais de hipercalemia: distúrbios do potássio, ECG, lise, adrenal — provas + banco banco de questões",
              lambda K: K.ROTEIRO, lambda K: K.ROTEIRO + [K.MODULOS[7]["aula"][0], K.MODULOS[8]["aula"][0]])
IC = Tema("ic", "Insuficiência Cardíaca", "ic", "insuf_cardiaca", "ic_treino", "ic_bancas", "ic-treino", 2, (230, 110, 110),
          "Questões reais de IC: aguda e choque, crônica e dispositivos, diagnóstico, Chagas e periparto",
          lambda C: C.ROTEIRO, lambda C: C.ROTEIRO + [C.MODULOS[8]["aula"][0], C.MODULOS[9]["aula"][0]])
REUMATO = Tema("reu", "Reumatologia", "reu", "reumatologia", "reumatologia_treino", "reumatologia_bancas", "reu-treino", 7,
               (250, 180, 90), "Questões reais de reumatologia: lúpus, artrite reumatoide, vasculites, gota e o resto",
               lambda R: R.ROTEIRO, lambda R: R.ROTEIRO + [R.MODULOS[2]["aula"][1], R.MODULOS[7]["aula"][2]])
TEMAS = [GASO, VENT, HIPERK, IC, REUMATO]

# Mundo da Farmacologia: um Tema por grupo de drogas (mesmos três modos)
FARMA_CV = Tema("fc", "Farmacologia Cardiovascular", "fc", "farmaco_cardio", "fc_treino", "fc_bancas", "fc-treino", 6,
                (240, 120, 140), "Questões reais que cobram drogas cardiovasculares: IC, coronária, anticoagulação, HAS, lípides",
                lambda F: F.ROTEIRO, lambda F: F.ROTEIRO + [F.MODULOS[9]["aula"][1], F.MODULOS[5]["aula"][1]])
FARMA_ATB = Tema("fa", "Antibióticos", "fa", "farmaco_atb", "fa_treino", "fa_bancas", "fa-treino", 8, (120, 200, 160),
                 "Questões reais que cobram antibiótico: escolha, duração, toxicidade, resistência e IST",
                 lambda F: F.ROTEIRO, lambda F: F.ROTEIRO + [F.MODULOS[0]["aula"][1], F.MODULOS[10]["aula"][1]])
FARMACOS = [FARMA_CV, FARMA_ATB]

# Internato · Clínica Médica 2: mundos pequenos feitos das aulas (asma, DPOC, VM), num submenu próprio
INTERNATO_ASMA = Tema("uas", "Asma", "uas", "internato_asma", "internato_asma_treino", "internato_asma_bancas", "uas-treino", 1,
                   (120, 200, 255), "Questões reais de asma: provas + banco banco de questões (adulto, crise, grave, pediatria)",
                   lambda A: A.ROTEIRO, lambda A: A.ROTEIRO + [A.MODULOS[3]["aula"][0]])
INTERNATO_DPOC = Tema("udp", "DPOC", "udp", "internato_dpoc", "internato_dpoc_treino", "internato_dpoc_bancas", "udp-treino", 9,
                   (170, 210, 140), "Questões reais de DPOC: provas + banco banco de questões (estável, exacerbação, avançada)",
                   lambda D: D.ROTEIRO, lambda D: D.ROTEIRO + [D.MODULOS[1]["aula"][1], D.MODULOS[3]["aula"][1]])
INTERNATO_VM = Tema("uvm", "VM", "uvm", "internato_vm", "internato_vm_treino", "vent_bancas", "uvm-treino", 5,
                 (150, 190, 255), "Questões reais de ventilação, VNI, SDRA, curvas e desmame: provas + banco banco de questões",
                 lambda V: V.ROTEIRO, lambda V: V.ROTEIRO + [V.MODULOS[2]["aula"][1], V.MODULOS[4]["aula"][1]])
INTERNATO_TRANSF = Tema("utr", "Transfusão", "utr", "internato_transf", "internato_transf_treino", "internato_transf_bancas", "utr-treino", 3,
                     (240, 120, 120), "Questões reais de hemoterapia: provas + banco banco de questões (indicação, plaquetas e plasma, reações)",
                     lambda T: T.ROTEIRO, lambda T: T.ROTEIRO + [T.MODULOS[3]["aula"][1], T.MODULOS[4]["aula"][0]])
INTERNATO_REUM = Tema("urm", "Reumato: LES, gota, esclerodermia", "urm", "internato_reum", "internato_reum_treino", "internato_reum_bancas", "urm-treino", 7,
                   (250, 180, 90), "Questões reais de lúpus, SAF, gota, esclerodermia, Sjögren, mãos e osso: provas + banco banco de questões",
                   lambda R: R.ROTEIRO, lambda R: R.ROTEIRO + [R.MODULOS[3]["aula"][0], R.MODULOS[5]["aula"][1]])
INTERNATO_FA = Tema("uac", "FA: CHA2DS2-VASc e anticoagulação", "uac", "internato_fa", "internato_fa_treino", "internato_fa_bancas", "uac-treino", 11,
                 (255, 150, 200), "Questões reais de anticoagulação na FA: provas + banco banco de questões (escore, droga, cardioversão)",
                 lambda F: F.ROTEIRO, lambda F: F.ROTEIRO + [F.MODULOS[1]["aula"][0], F.MODULOS[2]["aula"][0]])
INTERNATO_ENDO = Tema("uen", "Endócrino: as questões da prova", "uen", "internato_endo", "internato_endo_treino", "internato_endo_bancas",
                   "uen-treino", 13, (130, 220, 200),
                   "Questões reais de DM2, remédios do DM, tireoide, Cushing e acromegalia: provas + banco banco de questões",
                   lambda E: E.ROTEIRO, lambda E: E.ROTEIRO + [E.MODULOS[2]["aula"][0], E.MODULOS[5]["aula"][0]])
INTERNATO_COG = Tema("ucg", "Avaliação cognitiva: MEEM, MoCA e BBRC", "ucg", "internato_cognicao", "internato_cognicao_treino",
                  "internato_cognicao_bancas", "ucg-treino", 4, (190, 160, 255),
                  "Questões reais de demências, CCL, rastreio cognitivo e delirium: provas + banco banco de questões",
                  lambda G: G.ROTEIRO, lambda G: G.ROTEIRO + [G.MODULOS[3]["aula"][0], G.MODULOS[5]["aula"][0]])
INTERNATO_PK = Tema("upk", "Doença de Parkinson: ON/OFF, UPDRS e remédios", "upk", "internato_parkinson", "internato_parkinson_treino",
                 "internato_parkinson_bancas", "upk-treino", 10, (120, 210, 230),
                 "Questões reais de Parkinson, parkinsonismo e tremor: provas + banco banco de questões",
                 lambda P: P.ROTEIRO, lambda P: P.ROTEIRO + [P.MODULOS[6]["aula"][0], P.MODULOS[3]["aula"][2]])
# A prova de CM do internato (out/2026): um mundo por especialidade, montado dos relatos das turmas anteriores
INTERNATO_NEFRO = Tema("unf", "Nefro: DRC, IRA, ITU e cálculo", "unf", "internato_nefro", "internato_nefro_treino",
                    "internato_nefro_bancas", "unf-treino", 3, (110, 190, 250),
                    "Questões reais de DRC, IRA, glomerulopatias, ITU, nefrolitíase e potássio: provas + banco banco de questões",
                    lambda N: N.ROTEIRO, lambda N: N.ROTEIRO + [N.MODULOS[3]["aula"][0], N.MODULOS[7]["aula"][1]])
INTERNATO_HAS = Tema("uha", "HAS e cardio da prova", "uha", "internato_has", "internato_has_treino", "internato_has_bancas", "uha-treino",
                  2, (240, 110, 110), "Questões reais de HAS, IC, SCA, síndrome metabólica e ECG: provas + banco banco de questões",
                  lambda H: H.ROTEIRO, lambda H: H.ROTEIRO + [H.MODULOS[2]["aula"][0], H.MODULOS[5]["aula"][1]])
INTERNATO_HEMATO = Tema("uhm", "Hemato: anemias, leucemia e TEV", "uhm", "internato_hemato", "internato_hemato_treino",
                     "internato_hemato_bancas", "uhm-treino", 12, (230, 90, 120),
                     "Questões reais de anemias, leucemias, mieloma, TVP/TEP e hemostasia: provas + banco banco de questões",
                     lambda H: H.ROTEIRO, lambda H: H.ROTEIRO + [H.MODULOS[1]["aula"][0], H.MODULOS[4]["aula"][0]])
INTERNATO_PNEUMO = Tema("upn", "Pneumo e sepse da prova", "upn", "internato_pneumo", "internato_pneumo_treino", "internato_pneumo_bancas",
                     "upn-treino", 9, (140, 210, 170),
                     "Questões reais de pneumonia, sepse e choque, DPOC e semiologia: provas + banco banco de questões",
                     lambda P: P.ROTEIRO, lambda P: P.ROTEIRO + [P.MODULOS[3]["aula"][1], P.MODULOS[4]["aula"][0]])
INTERNATO_NEURO = Tema("unr", "Neuro: epilepsia, AVE e demência", "unr", "internato_neuro", "internato_neuro_treino",
                    "internato_neuro_bancas", "unr-treino", 4, (170, 150, 255),
                    "Questões reais de epilepsia, AVE, demências e Parkinson: provas + banco banco de questões",
                    lambda N: N.ROTEIRO, lambda N: N.ROTEIRO + [N.MODULOS[1]["aula"][0], N.MODULOS[3]["aula"][0]])
INTERNATO_DERMATO = Tema("udm", "Dermato da prova", "udm", "internato_dermato", "internato_dermato_treino", "internato_dermato_bancas",
                      "udm-treino", 8, (240, 170, 120),
                      "Questões reais de câncer de pele, hanseníase, bolhosas e infecções: provas + banco banco de questões",
                      lambda D: D.ROTEIRO, lambda D: D.ROTEIRO + [D.MODULOS[1]["aula"][1], D.MODULOS[3]["aula"][1]])
INTERNATO_HEPATO = Tema("uhp", "Hepato: PBE, varizes e hepatite B", "uhp", "internato_hepato", "internato_hepato_treino",
                     "internato_hepato_bancas", "uhp-treino", 6, (200, 200, 110),
                     "Questões reais de cirrose, PBE, HDA varicosa e hepatites: provas + banco banco de questões",
                     lambda H: H.ROTEIRO, lambda H: H.ROTEIRO + [H.MODULOS[0]["aula"][1], H.MODULOS[2]["aula"][1]])
INTERNATO_RELATOS = Tema("url", "Prova: os relatos, questão a questão", "url", "internato_relatos", "internato_relatos_treino",
                      "internato_relatos_bancas", "url-treino", 14, (255, 220, 90),
                      "Questões reais de DM, CAD, tireoide, cálcio e ventilação, e as provas que tocam os temas relatados",
                      lambda R: R.ROTEIRO, lambda R: R.ROTEIRO + [R.MODULOS[5]["aula"][1], R.MODULOS[7]["aula"][0]])
INTERNATO_PROVA = [INTERNATO_RELATOS, INTERNATO_NEFRO, INTERNATO_HAS, INTERNATO_HEMATO, INTERNATO_PNEUMO, INTERNATO_NEURO, INTERNATO_DERMATO, INTERNATO_HEPATO]
# Casos da enfermaria (CM 2, out/2026): um mundo por paciente real, anonimizado, treinando o FAST HUG no leito
CASO_PNEUMONIA = Tema("cpn", "Leito 42: pneumonia e empiema (75 anos)", "cpn", "caso_pneumonia", "caso_pneumonia_treino",
                      "caso_pneumonia_bancas", "cpn-treino", 9, (150, 210, 255),
                      "Questões reais de derrame pleural e empiema, pneumonia hospitalar, DPOC e profilaxia de TEV",
                      lambda C: C.ROTEIRO, lambda C: C.ROTEIRO + [C.MODULOS[5]["aula"][0], C.MODULOS[6]["aula"][1]])
CASO_ABSCESSO = Tema("crn", "Leito 43: abscesso renal (23 anos)", "crn", "caso_abscesso_renal", "caso_abscesso_renal_treino",
                     "caso_abscesso_renal_bancas", "crn-treino", 3, (120, 220, 190),
                     "Questões reais de abscesso renal, pielonefrite, ITU no homem e bacteremia por S. aureus",
                     lambda C: C.ROTEIRO, lambda C: C.ROTEIRO + [C.MODULOS[3]["aula"][0], C.MODULOS[4]["aula"][0]])
CASO_GRAVES = Tema("cgr", "Leito 39: Graves, DM1 e pancitopenia (21 anos)", "cgr", "caso_graves", "caso_graves_treino",
                   "caso_graves_bancas", "cgr-treino", 13, (255, 170, 210),
                   "Questões reais de Graves, cetoacidose, adrenal, AHAI, hipocalcemia e emergência hipertensiva",
                   lambda C: C.ROTEIRO, lambda C: C.ROTEIRO + [C.MODULOS[4]["aula"][1], C.MODULOS[5]["aula"][0]])
CASO_COLEDOCO = Tema("cvb", "Leito 41: ITU, próstata e colédoco (77 anos)", "cvb", "caso_coledoco", "caso_coledoco_treino",
                     "caso_coledoco_bancas", "cvb-treino", 6, (240, 200, 110),
                     "Questões reais de colangite, coledocolitíase, colecistite, pielonefrite, HPB e cirrose",
                     lambda C: C.ROTEIRO, lambda C: C.ROTEIRO + [C.MODULOS[3]["aula"][0], C.MODULOS[4]["aula"][1]])
CASOS_CM2 = [CASO_PNEUMONIA, CASO_ABSCESSO, CASO_GRAVES, CASO_COLEDOCO]
INTERNATO_CM2 = INTERNATO_PROVA + [INTERNATO_REUM, INTERNATO_ENDO, INTERNATO_COG, INTERNATO_PK, INTERNATO_ASMA, INTERNATO_DPOC, INTERNATO_VM,
                             INTERNATO_TRANSF, INTERNATO_FA] + CASOS_CM2
# Internato · Medicina de Família e Comunidade (nov/2026): por prevalência nas provas reais de Preventiva/MFC
MFC_EPIDEMIO = Tema("mep", "Epidemiologia clínica", "mep", "mfc_epidemio", "mfc_epidemio_treino", "mfc_epidemio_bancas",
                    "mep-treino", 4, (120, 200, 255), "Questões reais de desenhos de estudo, RR, OR, NNT, testes e estatística",
                    lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[1]["aula"][1], M.MODULOS[3]["aula"][1]])
MFC_SUS = Tema("msu", "SUS e Atenção Primária", "msu", "mfc_sus", "mfc_sus_treino", "mfc_sus_bancas", "msu-treino", 9,
               (140, 220, 140), "Questões reais de princípios, leis, APS, financiamento e políticas de saúde",
               lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[0]["aula"][0], M.MODULOS[4]["aula"][1]])
MFC_CONSULTA = Tema("mfc", "Consulta do médico de família", "mfc", "mfc_consulta", "mfc_consulta_treino",
                    "mfc_consulta_bancas", "mfc-treino", 13, (255, 200, 120),
                    "Questões reais de MCCP, comunicação, rastreamento, prevenção quaternária, família e tabagismo",
                    lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[0]["aula"][0], M.MODULOS[4]["aula"][1]])
MFC_VIGILANCIA = Tema("mvg", "Vigilância e epidemias", "mvg", "mfc_vigilancia", "mfc_vigilancia_treino",
                      "mfc_vigilancia_bancas", "mvg-treino", 6, (240, 150, 120),
                      "Questões reais de notificação, epidemias, sistemas de informação e declaração de óbito",
                      lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[1]["aula"][0], M.MODULOS[2]["aula"][1]])
MFC_TRABALHADOR = Tema("mtr", "Saúde do trabalhador", "mtr", "mfc_trabalhador", "mfc_trabalhador_treino",
                       "mfc_trabalhador_bancas", "mtr-treino", 8, (200, 180, 120),
                       "Questões reais de acidente de trabalho, CAT, nexo, doenças ocupacionais e NRs",
                       lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[1]["aula"][0], M.MODULOS[3]["aula"][1]])
MFC_INDICADORES = Tema("mid", "Indicadores e prevenção", "mid", "mfc_indicadores", "mfc_indicadores_treino",
                       "mfc_indicadores_bancas", "mid-treino", 12, (190, 160, 255),
                       "Questões reais de incidência, prevalência, mortalidade infantil e materna e níveis de prevenção",
                       lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[0]["aula"][0], M.MODULOS[1]["aula"][0]])
MFC_IDOSO = Tema("mso", "Saúde do idoso", "mso", "mfc_idoso", "mfc_idoso_treino", "mfc_idoso_bancas", "mso-treino", 10,
                 (120, 210, 230), "Questões reais de funcionalidade, fragilidade, quedas, polifarmácia e Estatuto",
                 lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[1]["aula"][0], M.MODULOS[2]["aula"][0]])
MFC_ETICA = Tema("met", "Ética médica e prescrição", "met", "mfc_etica", "mfc_etica_treino", "mfc_etica_bancas",
                 "met-treino", 14, (255, 170, 210), "Questões reais de sigilo, recusa terapêutica, receituário e fim de vida",
                 lambda M: M.ROTEIRO, lambda M: M.ROTEIRO + [M.MODULOS[1]["aula"][0], M.MODULOS[2]["aula"][0]])
INTERNATO_MFC = [MFC_EPIDEMIO, MFC_SUS, MFC_CONSULTA, MFC_VIGILANCIA, MFC_INDICADORES, MFC_TRABALHADOR, MFC_IDOSO, MFC_ETICA]


def abrir_temas_hard(app):
    """Os mundos de tema único (do zero ao herói, em três modos)."""
    desc = {"gaso": "13 módulos com aula, Treino (casos infinitos) e Bancas",
            "vm": "13 módulos com aula, Treino (11 contas do ventilador) e Bancas",
            "k": "12 módulos com aula, Treino (10 regras do plantão) e Bancas",
            "ic": "12 módulos com aula (inclui Chagas e choque), Treino (12 regras: perfil, BNP, H2FPEF, diurético, dispositivos) e Bancas",
            "reu": "17 módulos do que mais cai ao que menos cai, Treino (10 regras: critérios, líquido, anticorpos) e Bancas"}
    menu = Menu(app, "Mundos dos temas", [], "Um tema difícil do zero ao herói: Aprendizado, Treino e Bancas")

    def montar():
        menu.itens = []
        for t in TEMAS:
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": f"Mundo da {t.nome}", "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": f"{desc.get(t.chave, '')} · {ok}/{tot} dominadas"})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def abrir_internato(app):
    """Internato · Clínica Médica 2: tudo o que foi estudado de clínica — a prova, os casos da enfermaria, os fluxogramas
    das aulas e, no fim, os estudos de antes do internato (mundos dos temas, farmacologia, fluxogramas gerais, ECG)."""
    from . import fluxograma
    desc = {"uas": "Inflamação T2, diagnóstico, do SABA ao MART, etapas do PCDT, asma grave e biológicos",
            "udp": "GOLD 2026: espirometria, grupos A/B/E, PCDT 2026, seguimento, exacerbação e risco cardiopulmonar",
            "uvm": "VNI × IOT, ajuste, mecânica, SDRA, desmame + GRÁFICOS: curvas, modos, pico × platô, auto-PEEP",
            "utr": "Limiares 7/7,5/8, plaquetas, plasma × crio e reações",
            "urm": "LES por metas, nefrite, critérios LES/SAF, gota",
            "uac": "CHA₂DS₂-VA(Sc) letra a letra, decisão, exceções, HAS-BLED e dose do DOAC",
            "ucg": "Queixa → síndrome, CCL × demência, MEEM pela escolaridade, MoCA e MIS, Bateria Breve",
            "upk": "ON/OFF e diário, padrões de OFF, MDS-UPDRS item a item, levodopa, adjuvantes e clozapina",
            "uen": "★ CAI NA PROVA: risco CV, pré-DM, metformina, iSGLT2, caneta, insulina, tireoide, Cushing, acromegalia",
            "unf": "DRC G×A, HAS na DRC, EPO e PTH, IRA, nefrótica × nefrítica, ITU, cálculo, K⁺, Cockcroft-Gault",
            "uha": "Aferição única, metas 2025, efeitos colaterais, feocromo, síndrome metabólica, IC (aula 23/09), SCA, ECG",
            "uhm": "Micro × macro (B12 e metformina), hemograma urgente, leucemia, mieloma, TVP/TEP, cirrótico que sangra",
            "upn": "Semiologia, CURB-65 e ATB, PAV, sepse e choque, O₂ no DPOC, asma/DPOC da prova, tabagismo",
            "unr": "Epilepsia (tratar ou não, gestante), estado de mal, AVE agudo, Lewy × Alzheimer, encefalite, amitriptilina",
            "udm": "Lesões elementares, CBC × CEC × melanoma, pênfigo, herpes, hanseníase, corticoide, isotretinoína, B3",
            "uhp": "PBE, HDA varicosa (sem betabloqueador agudo), sorologia da hepatite B, ascite e encefalopatia",
            "url": "★ As 60 questões relatadas pelas turmas, na ordem, + DM, CAD, nódulo, hiperpara e ventilador",
            "cpn": "Empiema e dreno, DPOC + PIU, baricitinibe, iSGLT2 e acidose, rivaroxabana e o dreno, polimixina",
            "crn": "Abscesso cortical × corticomedular, tamanho e drenagem, fator R, e o FAST HUG do 'não se aplica'",
            "cgr": "Tapazol e tireoidectomia, poliglandular, cortisol antes da tireoide, CAD e K⁺, AHAI, IgA, PRES",
            "cvb": "Retenção por HPB, dois alfabloqueadores, Tokyo e CPRE, TTPA estranho, Child-Pugh, candidíase"}
    desc["urm"] = "LES, SAF, gota + esclerodermia (anticorpos), Sjögren, AR × artrose, reativa, túnel do carpo, osteoporose"
    n_fx = sum(1 for a in fluxograma.ARVORES if a.grupo in fluxograma.INTERNATO)
    menu = Menu(app, "Internato · Clínica Médica 2", [], "Estágio concluído: a prova, os casos, os fluxogramas e o resto da clínica, guardados para revisar")

    def montar():
        prova = INTERNATO_PROVA + [INTERNATO_REUM, INTERNATO_ENDO]
        menu.barra = progresso_prova(app, prova)
        menu.itens = [
            {"secao": "A prova de CM: o que cai", "label": ""},
            {"label": "▶ Estudar o que falta", "cor": AMARELO, "acao": lambda: _proximo_da_prova(app, prova),
             "info": "Abre o primeiro módulo da prova com questão ainda não dominada"}]
        for t in prova:
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": f"Mundo da {t.nome}", "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": desc[t.chave], "dir": f"{ok}/{tot}", "prog": ok / tot if tot else 0})
        menu.itens += [
            {"secao": "Fluxogramas das aulas", "label": ""},
            {"label": "Fluxogramas das aulas", "cor": (120, 200, 255),
             "info": f"{n_fx} fluxogramas caso a caso: asma, DPOC, VM, transfusão, LES, SAF, gota e FA",
             "acao": lambda: fluxograma.abrir(app, grupos=fluxograma.INTERNATO, titulo="Fluxogramas CM 2",
                                              sub="Asma, DPOC, VM, transfusão, reumatologia e FA: percorra o fluxograma caso a caso")},
            {"secao": "Casos da enfermaria: FAST HUG no leito", "label": ""}]
        for t in CASOS_CM2:
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": t.nome, "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": desc[t.chave], "dir": f"{ok}/{tot}", "prog": ok / tot if tot else 0})
        menu.itens.append({"secao": "Outros mundos das aulas", "label": ""})
        for t in INTERNATO_CM2:
            if t in prova or t in CASOS_CM2:
                continue
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": f"Mundo da {t.nome}", "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": f"{desc[t.chave]} · {ok}/{tot} dominadas", "prog": ok / tot if tot else 0})
        menu.itens += [
            {"secao": "Mais clínica médica", "label": ""},
            {"label": "Mundos dos temas", "cor": (90, 220, 210),
             "info": ", ".join(t.nome for t in TEMAS) + ": aula, treino infinito e questões reais",
             "acao": lambda: abrir_temas_hard(app)},
            {"label": "Mundo da Farmacologia", "cor": (240, 120, 140),
             "info": "Drogas que mudam a doença, ligadas à clínica: aula, treino de doses e bancas",
             "acao": lambda: abrir_farmacologia(app)},
            {"label": "Fluxogramas do raciocínio", "cor": (120, 200, 255),
             "info": "Gasometria, eletrólitos, rim, anemia, asma, FAST HUG e espirometria: caso a caso, com mini-aula",
             "acao": lambda: fluxograma.abrir(app)},
            {"label": "Leitura de ECG", "cor": (255, 140, 140),
             "info": "Tira de DII longo: bloqueios, FA, flutter, taquicardias e ritmos de parada",
             "acao": lambda: __import__("ilha.ecg_treino", fromlist=["abrir"]).abrir(app)},
            {"label": "Clínica Médica por prevalência", "cor": (255, 120, 120),
             "info": "Questões reais 2024–2026 (SUS-SP, USP, UNIFESP, ENARE, ENAMED): o que mais cai primeiro",
             "acao": lambda: abrir_clinica(app)},
            {"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop}]
        menu._pular_desab(1)

    menu.ao_voltar = montar
    montar()
    app.push(menu)


MFC_DESC = {"mep": "23% das questões de Preventiva: desenhos de estudo, RR/OR/NNT, testes diagnósticos, estatística",
            "msu": "23%: princípios, Leis 8.080/8.142, Decreto 7.508, atributos da APS, eSF/eMulti, pisos, CAPS",
            "mfc": "12%: MCCP, más notícias, prevenção quaternária, rastreamento 2025, família, tabagismo, adolescente",
            "mvg": "11%: notificação compulsória, epidemia × surto, curva epidêmica, SIM/SINASC/SINAN, DO, R0",
            "mtr": "9%: acidente de trabalho e CAT, Schilling, PAIR, benzeno, NR-1 (2026), PCMSO, material biológico",
            "mid": "10%: incidência × prevalência, letalidade, mortalidade infantil e materna, Leavell e Clark, Rose",
            "mso": "6%: Katz × Lawton, IVCF-20, Fried, quedas, Beers 2023, Estatuto da Pessoa Idosa",
            "met": "Sigilo, recusa terapêutica, prontuário, receituário da Portaria 344, ortotanásia × eutanásia"}


def abrir_mfc_info(app):
    tot = sum(len(t.C.todas()) for t in INTERNATO_MFC)
    ok = sum(_dominadas(app, m) for t in INTERNATO_MFC for m in t.C.MODULOS)
    return f"Medicina de Família e Comunidade por prevalência: {len(INTERNATO_MFC)} mundos · {ok}/{tot} dominadas"


def abrir_mfc(app):
    """Internato · MFC: os mundos de Preventiva/MFC na ordem do que mais cai nas provas reais."""
    menu = Menu(app, "Internato · MFC", [], "Medicina de Família e Comunidade: do que mais cai ao que menos cai nas provas")

    def montar():
        menu.barra = progresso_prova(app, INTERNATO_MFC, "MFC")
        menu.itens = [
            {"secao": "Por prevalência nas provas reais", "label": ""},
            {"label": "▶ Estudar o que falta", "cor": AMARELO, "acao": lambda: _proximo_da_prova(app, INTERNATO_MFC),
             "info": "Abre o primeiro módulo, na ordem da prevalência, com questão ainda não dominada"}]
        for i, t in enumerate(INTERNATO_MFC, 1):
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": f"{i}. Mundo da {t.nome}", "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": MFC_DESC[t.chave], "dir": f"{ok}/{tot}", "prog": ok / tot if tot else 0})
        menu.itens.append({"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop})
        menu._pular_desab(1)

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def progresso_prova(app, temas, nome="Prova de CM"):
    """Quanto falta para a prova: questões dominadas (acertadas) sobre o total das aulas dos mundos da prova, com a
    estimativa de tempo (≈ 40 s por questão, com a leitura do comentário). Devolve o dicionário que Menu.barra desenha."""
    tot = sum(len(t.C.todas()) for t in temas)
    ok = sum(_dominadas(app, m) for t in temas for m in t.C.MODULOS)
    vistas = sum(1 for t in temas for q in t.C.todas() if app.save.stat(q["id"]))
    falta = tot - ok
    minutos = round(falta * 40 / 60)
    tempo = f"{minutos // 60} h {minutos % 60:02d} min" if minutos >= 60 else f"{minutos} min"
    texto = (f"{nome}: {ok}/{tot} dominadas · faltam {falta} (≈ {tempo})" if falta else
             f"{nome}: todas as {tot} questões dominadas!")
    return {"frac": ok / tot if tot else 1.0, "vistas": vistas / tot if tot else 1.0, "texto": texto}


def _proximo_da_prova(app, temas):
    """Primeiro módulo (na ordem dos mundos da prova) com questão ainda não dominada."""
    for t in temas:
        for k, m in enumerate(t.C.MODULOS):
            if _dominadas(app, m) < len(m["questoes"]):
                jogar_modulo(app, t, k)
                return
    app.push(Mensagem(app, "Tudo dominado", "Todas as questões dos mundos da prova estão dominadas. Vá para Treino e Bancas."))


def abrir_farmacologia(app):
    """Os grupos de drogas, cada um com Aprendizado, Treino e Bancas."""
    desc = {"fc": "Bloqueio neuro-hormonal, iSGLT2, antiplaquetários, anticoagulantes, lípides, HAS",
            "fa": "Classes, espectro e toxicidade; PAC, ITU, sepse, pele, SNC/endocardite; resistência, IST, alergia"}
    menu = Menu(app, "Mundo da Farmacologia", [], "Indicação, mecanismo, dose, efeito adverso e interação — sempre ligados à clínica")

    def montar():
        menu.itens = []
        for t in FARMACOS:
            tot = len(t.C.todas())
            ok = sum(_dominadas(app, m) for m in t.C.MODULOS)
            menu.itens.append({"label": t.nome, "cor": t.cor, "acao": (lambda t=t: abrir_tema(app, t)),
                               "info": f"{desc.get(t.chave, '')} · {ok}/{tot} dominadas"})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


# ------------------------------------------------------------------ clínica médica por prevalência

def _clinica():
    from . import clinica_prevalencia as CP
    return CP.carregar()


def CP_pilulas(subtemas):
    from . import clinica_prevalencia as CP
    return CP.pilulas(subtemas)


def _fase_ok(app, f):
    return sum(1 for q in f["questoes"] if (app.save.stat(q["id"]) or {}).get("ok"))


def abrir_clinica(app):
    """Grandes áreas da clínica médica, da que mais cai para a que menos cai."""
    try:
        cp = _clinica()
    except Exception as e:
        app.push(Mensagem(app, "Sem provas", f"Não consegui ler as provas reais: {e}"))
        return
    menu = Menu(app, "Clínica Médica", [], "")

    def continuar():
        for i, a in enumerate(cp["areas"]):
            for k, f in enumerate(a["fases"]):
                if _fase_ok(app, f) < len(f["questoes"]):
                    jogar_clinica(app, i, k)
                    return
        app.push(Mensagem(app, "Tudo dominado", "Você acertou todas as questões de clínica médica deste mundo. "
                                                 "Revise os erros ou jogue de novo as áreas."))

    def montar():
        todas = [q for a in cp["areas"] for f in a["fases"] for q in f["questoes"]]
        ok = sum(1 for q in todas if (app.save.stat(q["id"]) or {}).get("ok"))
        menu.subtitulo = (f"Por prevalência · {cp['total']} questões reais de {len(cp['provas'])} provas "
                          f"(2024–2026) · {ok} dominadas")
        menu.itens = [{"label": "▶ Continuar", "cor": AMARELO, "acao": continuar,
                       "info": "Primeira fase com questão ainda não dominada, na ordem da prevalência"}]
        for i, a in enumerate(cp["areas"]):
            qs = [q for f in a["fases"] for q in f["questoes"]]
            d = sum(1 for q in qs if (app.save.stat(q["id"]) or {}).get("ok"))
            tops = ", ".join(s["nome"] for s in a["subtemas"][:3])
            menu.itens.append({"label": ("✔ " if d == len(qs) else "") + f"{i + 1}. {a['materia']}",
                               "info": f"{a['pct']:.0f}% da clínica · {len(a['fases'])} fases · {d}/{len(qs)} · {tops}",
                               "cor": VERDE if d == len(qs) else (255, 120, 120), "acao": (lambda i=i: abrir_area(app, i))})
        erradas = [q for q in todas if app.save.stat(q["id"]) and not app.save.stat(q["id"]).get("ok")]
        menu.itens.append({"label": "Revisar erros de clínica médica", "cor": (250, 120, 150), "desab": not erradas,
                           "info": f"{len(erradas)} questões com a última resposta errada",
                           "acao": lambda: _revisar_clinica(app, erradas)})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def abrir_area(app, i):
    a = _clinica()["areas"][i]
    menu = Menu(app, a["materia"], [], "")

    def montar():
        menu.subtitulo = f"Do subtema que mais cai ao que menos cai · {a['n']} questões · mais recentes primeiro"
        menu.itens = []
        for k, f in enumerate(a["fases"]):
            n, d = len(f["questoes"]), _fase_ok(app, f)
            anos = sorted({q["origem"].split(" · ")[0].split()[-1] for q in f["questoes"]}, reverse=True)
            menu.itens.append({"label": ("✔ " if d == n else "") + f"{k + 1}. " + " + ".join(f["subtemas"]),
                               "info": f"{n} {'questão' if n == 1 else 'questões'} · {', '.join(anos)} · {d}/{n} dominadas",
                               "dir": _melhor(app, f"cm-prev:{a['materia']}:{k}"),
                               "cor": VERDE if d == n else (255, 160, 140), "acao": (lambda k=k: jogar_clinica(app, i, k))})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def _proxima_clinica(i, k):
    areas = _clinica()["areas"]
    if k + 1 < len(areas[i]["fases"]):
        return i, k + 1
    if i + 1 < len(areas):
        return i + 1, 0
    return None


def jogar_clinica(app, i, k):
    a = _clinica()["areas"][i]
    f = a["fases"][k]
    prox = _proxima_clinica(i, k)
    titulo = " + ".join(f["subtemas"])
    app.jogar(list(f["questoes"]), f"{a['materia']} · {titulo}", f"cm-prev:{a['materia']}:{k}",
              f"Clínica {i + 1}-{k + 1}", _paleta_de(a["materia"]),
              proxima=(lambda: jogar_clinica(app, *prox)) if prox else None,
              repetir=lambda: jogar_clinica(app, i, k),
              briefing={"titulo": f"Clínica {i + 1}-{k + 1} · {a['materia']} · {titulo}", "materia": a["materia"],
                        "texto": titulo, "pilulas": CP_pilulas(f["subtemas"]),
                        "cabecalho": "Resumo e bizus da fase"})


def _revisar_clinica(app, erradas):
    app.jogar(data.escolher(erradas, POR_FASE, app.save), "Clínica médica · Revisão dos erros", "cm-prev:revisao",
              "Clínica · Revisão", 7, briefing={"titulo": "Revisão dos erros · clínica médica", "materia": "Clínica Médica",
                                                "texto": " ".join({q["subtema"] for q in erradas})[:200]})


def _dominadas(app, m):
    return sum(1 for q in m["questoes"] if (app.save.stat(q["id"]) or {}).get("ok"))


def abrir_gasometria(app):
    abrir_tema(app, GASO)


def abrir_ventilacao(app):
    abrir_tema(app, VENT)


def abrir_hipercalemia(app):
    abrir_tema(app, HIPERK)


def abrir_reumatologia(app):
    abrir_tema(app, REUMATO)


ESTILOS = {"jogo": "Com diversão", "questoes": "Sem risadinha"}


def escolher_estilo(app, titulo, depois):
    """Ao abrir um tema: 'Com diversão' (o jogo normal, com fase) ou 'Sem risadinha' (só as questões, uma atrás da
    outra, com comentário). Fica salvo em save.config['estilo'] e vale para as fases abertas a partir dali."""
    def escolher(estilo):
        app.save.config["estilo"] = estilo
        app.save.salvar()
        app.pop()
        depois()

    menu = Menu(app, "Como quer jogar?", [
        {"label": "Com diversão", "cor": (140, 230, 140), "acao": lambda: escolher("jogo"),
         "info": "Jogo normal: corra, pule e enfrente os bichos-questão da fase"},
        {"label": "Sem risadinha", "cor": (120, 190, 255), "acao": lambda: escolher("questoes"),
         "info": "Só as questões: uma atrás da outra na tela, com o comentário, sem a fase"},
    ], titulo)
    menu.sel = 1 if app.save.config.get("estilo") == "questoes" else 0
    app.push(menu)


def _estilo_item(app, t, reabrir):
    est = app.save.config.get("estilo", "jogo")
    return {"label": f"Estilo: {ESTILOS.get(est, 'Com diversão')} (trocar)", "cor": (200, 200, 200),
            "info": "Com diversão = jogo normal · Sem risadinha = só as questões",
            "acao": lambda: (app.pop(), reabrir(app, t))}


def abrir_tema(app, t):
    """Ao selecionar o tema: primeiro o estilo (com diversão ou sem risadinha), depois os três modos."""
    escolher_estilo(app, f"Mundo da {t.nome}", lambda: _abrir_modos(app, t))


def _abrir_modos(app, t):
    """Menu do mundo: os três modos."""
    C, T = t.C, t.T
    menu = Menu(app, f"Mundo da {t.nome}", [], "Escolha o modo")

    def montar():
        tot = len(C.todas())
        ok = sum(_dominadas(app, m) for m in C.MODULOS)
        tr_c = tr_e = 0
        for h in T.HABILIDADES:
            s = app.save.stat(f"{t.treino_pref}:{h}") or {}
            tr_c, tr_e = tr_c + s.get("c", 0), tr_e + s.get("e", 0)
        tr = f"{tr_c + tr_e} casos resolvidos · {round(100 * tr_c / (tr_c + tr_e))}% de acerto" if tr_c + tr_e else "nenhum caso ainda"
        pronto = app.banco is not None
        menu.itens = [
            {"label": "Modo Aprendizado", "cor": (120, 210, 255), "acao": lambda: abrir_aprendizado(app, t),
             "info": f"Do zero ao herói: {len(C.MODULOS)} módulos com aula antes e comentário depois · {ok}/{tot} dominadas"},
            {"label": "Modo Treino", "cor": (140, 230, 140), "acao": lambda: abrir_treino(app, t),
             "info": f"Casos gerados na hora, infinitos, com a conta passo a passo · {tr}"},
            {"label": "Modo Bancas" + ("" if pronto else "  (carregando banco…)"), "cor": (255, 190, 90),
             "desab": not pronto, "acao": lambda: abrir_bancas(app, t), "info": t.desc_bancas},
            _estilo_item(app, t, abrir_tema),
        ]
        menu._pronto = pronto

    upd = menu.update

    def update(inp):
        if menu._pronto != (app.banco is not None):
            montar()
        upd(inp)
    menu.update = update
    menu.ao_voltar = montar
    montar()
    app.push(menu)


def abrir_aprendizado(app, t):
    C = t.C
    menu = Menu(app, f"{t.nome} · Aprendizado", [], "")
    cores = {1: (120, 210, 255), 2: (255, 200, 90), 3: (250, 120, 150), 4: (190, 140, 255)}

    def montar():
        tot = len(C.todas())
        ok = sum(_dominadas(app, m) for m in C.MODULOS)
        erradas = [q for q in C.todas() if app.save.stat(q["id"]) and not app.save.stat(q["id"]).get("ok")]
        menu.subtitulo = f"Do zero ao herói · {len(C.MODULOS)} módulos · {ok}/{tot} questões dominadas"
        menu.itens = [{"label": "▶ Continuar", "info": "Primeiro módulo que ainda tem questão não dominada",
                       "cor": AMARELO, "acao": continuar}]
        for k, m in enumerate(C.MODULOS):
            n, d = len(m["questoes"]), _dominadas(app, m)
            menu.itens.append({
                "label": ("✔ " if d == n else "") + f"{m['nivel']}-{k + 1}. {m['titulo']}",
                "info": f"Nível {m['nivel']}: {C.NIVEIS[m['nivel']]} · {d}/{n} dominadas",
                "dir": _melhor(app, f"{t.pref}:{m['id']}"), "cor": VERDE if d == n else cores[m["nivel"]],
                "acao": (lambda k=k: jogar_modulo(app, t, k))})
        menu.itens.append({"label": "★ Prova final (mistura todos os módulos)", "info": "10 questões, erros e inéditas primeiro",
                           "cor": (200, 160, 250), "dir": _melhor(app, f"{t.pref}:final"), "acao": lambda: prova_tema(app, t)})
        menu.itens.append({"label": f"Revisar erros ({t.nome.lower()})", "info": f"{len(erradas)} questões com a última resposta errada",
                           "cor": (250, 120, 150), "desab": not erradas, "acao": lambda: revisar_tema(app, t)})

    def continuar():
        for k, m in enumerate(C.MODULOS):
            if _dominadas(app, m) < len(m["questoes"]):
                jogar_modulo(app, t, k)
                return
        prova_tema(app, t)

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def abrir_treino(app, t):
    T = t.T
    menu = Menu(app, f"{t.nome} · Treino", [], "Casos gerados na hora: nunca acabam e nunca se repetem iguais")

    def info(h):
        s = app.save.stat(f"{t.treino_pref}:{h}")
        if not s or s["c"] + s["e"] == 0:
            return "ainda não treinado"
        return f"{s['c'] + s['e']} feitos · {round(100 * s['c'] / (s['c'] + s['e']))}% de acerto"

    def montar():
        menu.itens = [{"label": "▶ Treino misto (adaptativo)", "cor": AMARELO, "dir": _melhor(app, f"{t.treino_pref}:*"),
                       "info": "Mistura todas as habilidades; as que você mais erra aparecem mais",
                       "acao": lambda: jogar_treino(app, t, None)}]
        for h, (nome, desc) in T.HABILIDADES.items():
            menu.itens.append({"label": nome, "info": f"{desc} · {info(h)}", "cor": (140, 230, 140),
                               "dir": _melhor(app, f"{t.treino_pref}:{h}"), "acao": (lambda h=h: jogar_treino(app, t, h))})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def jogar_treino(app, t, habil):
    T = t.T
    qs = T.fase(app.save, habil, POR_FASE)
    nome = "Treino misto" if habil is None else T.HABILIDADES[habil][0]
    app.jogar(qs, f"{t.nome} · {nome}", f"{t.treino_pref}:{habil or '*'}", f"Treino · {nome}", t.paleta + 5,
              proxima=lambda: jogar_treino(app, t, habil), repetir=lambda: jogar_treino(app, t, habil),
              briefing={"titulo": f"Treino · {nome}", "materia": t.C.MATERIA, "cabecalho": "Treino",
                        "pilulas": t.treino_pilulas()})


def _bancas(app, t):
    cache = app.__dict__.setdefault("_bancas", {})
    if t.chave not in cache:
        cache[t.chave] = t.B.coletar(app.banco)
    return cache[t.chave]


def abrir_bancas(app, t):
    B = t.B
    grupos = _bancas(app, t)
    todas = [q for qs in grupos.values() for q in qs]
    menu = Menu(app, f"{t.nome} · Bancas", [], "")

    def montar():
        c, e = app.save.resumo(todas)
        menu.subtitulo = f"{len(todas)} questões reais · {c} certas / {e} erradas"
        erradas = [q for q in todas if app.save.stat(q["id"]) and not app.save.stat(q["id"]).get("ok")]
        menu.itens = [{"label": "▶ Mistão de bancas", "cor": AMARELO, "dir": _melhor(app, f"{t.pref}-bancas:*"),
                       "info": "Todas as fontes; erradas antes, depois inéditas", "acao": lambda: jogar_bancas(app, t, None)}]
        for g, nome, desc in B.GRUPOS:
            qs = grupos[g]
            if not qs:
                continue
            c, e = app.save.resumo(qs)
            menu.itens.append({"label": nome, "info": f"{desc} · {len(qs)} questões · {c} certas / {e} erradas",
                               "cor": (255, 190, 90), "dir": _melhor(app, f"{t.pref}-bancas:{g}"),
                               "acao": (lambda g=g: jogar_bancas(app, t, g))})
        menu.itens.append({"label": "Revisar erros de banca", "info": f"{len(erradas)} questões com a última resposta errada",
                           "cor": (250, 120, 150), "desab": not erradas, "acao": lambda: jogar_bancas(app, t, "erros")})

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def jogar_bancas(app, t, grupo):
    B = t.B
    grupos = _bancas(app, t)
    todas = [q for qs in grupos.values() for q in qs]
    if grupo is None:
        pool, nome = todas, "Mistão de bancas"
    elif grupo == "erros":
        pool = [q for q in todas if app.save.stat(q["id"]) and not app.save.stat(q["id"]).get("ok")]
        nome = "Erros de banca"
    else:
        pool, nome = grupos[grupo], dict((g, n) for g, n, _ in B.GRUPOS)[grupo]
    if not pool:
        app.push(Mensagem(app, "Nada aqui", "Não há questões neste grupo agora."))
        return
    qs = data.escolher(pool, POR_FASE, app.save)
    app.jogar(qs, f"{t.nome} · {nome}", f"{t.pref}-bancas:{grupo or '*'}", f"Bancas · {nome}", t.paleta + 10,
              proxima=(lambda: jogar_bancas(app, t, grupo)) if grupo != "erros" else None,
              repetir=lambda: jogar_bancas(app, t, grupo),
              briefing={"titulo": f"Bancas · {nome}", "materia": t.C.MATERIA, "cabecalho": "Questões de banca",
                        "pilulas": t.roteiro() + [B.SOBRE]})


def item_continuar(app, temas):
    """Item "▶ Continuar" do menu principal: próximo módulo ainda não dominado do último mundo jogado
    (a chave do mundo é a mesma no PC e no celular)."""
    t = next((t for t in temas if t.chave == app.save.d.get("continuar")), None)
    if not t:
        return None
    mods = t.C.MODULOS
    k = next((i for i, m in enumerate(mods) if _dominadas(app, m) < len(m["questoes"])), None)
    if k is None:
        return {"label": f"▶ Continuar: {t.nome}", "info": "Todos os módulos dominados: Prova final",
                "cor": AMARELO, "acao": lambda: prova_tema(app, t)}
    return {"label": f"▶ Continuar: {t.nome}", "cor": AMARELO, "acao": lambda: jogar_modulo(app, t, k),
            "info": f"Módulo {k + 1} de {len(mods)} · {mods[k]['titulo']}"}


def jogar_modulo(app, t, k):
    app.save.d["continuar"] = t.chave      # o "▶ Continuar" do menu principal volta aqui
    C = t.C
    m = C.MODULOS[k]
    if any(app.save.stat(q["id"]) is None for q in m["questoes"]):
        qs = list(m["questoes"])           # 1ª passada: o módulo inteiro, na ordem didática
    else:
        qs = data.escolher(m["questoes"], POR_FASE, app.save)
    prox = (lambda: jogar_modulo(app, t, k + 1)) if k + 1 < len(C.MODULOS) else (lambda: prova_tema(app, t))
    app.jogar(qs, f"{t.nome} · {m['titulo']}", f"{t.pref}:{m['id']}", f"{t.nome} {m['nivel']}-{k + 1}",
              t.paleta + m["nivel"] * 5, proxima=prox, repetir=lambda: jogar_modulo(app, t, k),
              briefing={"titulo": f"{t.nome} {m['nivel']}-{k + 1} · {m['titulo']}", "materia": C.MATERIA,
                        "pilulas": m["aula"], "cabecalho": "Aula antes da fase"})


def prova_tema(app, t):
    qs = data.escolher(t.C.todas(), 10, app.save)
    app.jogar(qs, f"{t.nome} · Prova final", f"{t.pref}:final", f"{t.nome} · Final", t.paleta + 15,
              repetir=lambda: prova_tema(app, t),
              briefing={"titulo": f"Prova final · {t.nome}", "materia": t.C.MATERIA, "cabecalho": "Prova final",
                        "pilulas": t.roteiro()})


def revisar_tema(app, t):
    C = t.C
    pool = [q for q in C.todas() if app.save.stat(q["id"]) and not app.save.stat(q["id"]).get("ok")]
    if not pool:
        app.push(Mensagem(app, "Nada para revisar", f"Nenhum erro pendente em {t.nome.lower()}."))
        return
    app.jogar(data.escolher(pool, POR_FASE, app.save), f"{t.nome} · Revisão dos erros", f"{t.pref}:revisao",
              f"{t.nome} · Revisão", t.paleta + 9, repetir=lambda: revisar_tema(app, t),
              briefing={"titulo": f"Revisão dos erros · {t.nome}", "materia": t.C.MATERIA, "cabecalho": "Revisão",
                        "pilulas": t.roteiro()})


# ------------------------------------------------------------------ servidor

def abrir_servidor(app):
    srv = app.servidor

    def conectado(ok, erro):
        if not ok:
            app.push(Mensagem(app, "Servidor indisponível",
                              f"Não consegui falar com o LousaFPSServer em {srv.url}. "
                              "Inicie-o pelo atalho 'Lousa FPS - Servidor' ou confira ~/Apps/LousaFPSServer."))
            return
        nome_padrao = app.save.d.get("jogador") or "Leo"
        app.push(EntradaTexto(app, "Seu nome no Lousa FPS", nome_padrao, entrar))

    def entrar(nome):
        app.save.d["jogador"] = nome
        app.save.salvar()

        def tarefa():
            srv.entrar(nome)
            return srv.temas_da_sessao()
        app.push(Carregando(app, "Montando sua sessão SM-2", tarefa, montou))

    def montou(res, erro):
        if erro:
            app.push(Mensagem(app, "Erro", f"Falha ao montar a sessão: {erro}"))
            return
        mapa, temas = res
        if not temas:
            app.push(Mensagem(app, "Sessão vazia",
                              "O servidor não tem questões novas nem revisões devidas para você agora. "
                              "Ative listas em /admin/fila ou volte mais tarde."))
            return
        fases = []
        for t in temas:
            qs = t["questoes"]
            partes = [qs[i:i + POR_FASE] for i in range(0, len(qs), POR_FASE)]
            for k, p in enumerate(partes):
                rot = t["nome"] + (f" ({k + 1}/{len(partes)})" if len(partes) > 1 else "")
                fases.append({"nome": rot, "area": t["area"], "qs": p, "tema_id": t["tema_id"], "k": k})
        menu = Menu(app, f"Sessão de {srv.nome}", [],
                    f"{mapa.get('n_novas', 0)} novas · {mapa.get('n_revisao', 0)} revisões "
                    f"(pendentes no total: {mapa.get('revisao_pendente_total', 0)})")
        feitas = set()

        def montar_itens():
            menu.itens = []
            for i, f in enumerate(fases):
                n_rev = sum(1 for q in f["qs"] if q.get("revisao"))
                menu.itens.append({
                    "label": ("✔ " if i in feitas else "") + f["nome"],
                    "info": f"{f['area']} · {len(f['qs'])} questões" + (f" · {n_rev} revisão" if n_rev else ""),
                    "cor": art.paleta(_paleta_de(f["area"] or f["nome"]))["acento"],
                    "dir": _melhor(app, f"srv:{f['tema_id']}:{f['k']}"),
                    "acao": (lambda i=i: jogar(i))})
            menu.itens.append({"label": "Recarregar sessão do servidor", "info": "Busca a próxima leva SM-2",
                               "acao": lambda: (app.pop(), entrar(srv.nome)), "cor": (200, 200, 200)})

        def jogar(i):
            f = fases[i]
            feitas.add(i)
            montar_itens()
            app.jogar(f["qs"], f"Lousa FPS · {f['nome']}", f"srv:{f['tema_id']}:{f['k']}",
                      f"Lousa FPS · {f['nome']}", _paleta_de(f["area"] or f["nome"]),
                      proxima=(lambda: jogar(i + 1)) if i + 1 < len(fases) else None)

        montar_itens()
        app.push(menu)

    app.push(Carregando(app, "Conectando ao LousaFPSServer", srv.garantir_online, conectado))


# ------------------------------------------------------------------ listas

def abrir_listas(app):
    b = app.banco
    materias = b.materias()
    itens = []
    for i, m in enumerate(materias):
        pool = b.pool_materia(m)
        c, e = app.save.resumo(pool)
        itens.append({"label": m, "info": f"{len(pool)} questões · {len(b.listas[m])} subtemas · {c} certas / {e} erradas",
                      "cor": art.paleta(i)["acento"], "acao": (lambda m=m, i=i: abrir_materia(app, m, i))})
    app.push(Menu(app, "Ilhas das Listas", itens, "Escolha a ilha (matéria)"))


def abrir_materia(app, materia, idx):
    b = app.banco
    subs = sorted(b.listas[materia].items(), key=lambda kv: -len(kv[1]))
    menu = Menu(app, materia, [], "Cada fase sorteia 6 questões: erradas antes, depois as mais prevalentes")

    def montar():
        menu.itens = [{"label": f"Mistão de {materia}", "info": "Todos os subtemas juntos",
                       "dir": _melhor(app, f"lista:{materia}:*"), "cor": AMARELO,
                       "acao": lambda: jogar(None)}]
        for k, (sub, qs) in enumerate(subs):
            c, e = app.save.resumo(qs)
            menu.itens.append({"label": sub, "info": f"{len(qs)} questões · {c} certas / {e} erradas",
                               "dir": _melhor(app, f"lista:{materia}:{sub}"),
                               "cor": art.paleta(idx)["acento"], "acao": (lambda k=k: jogar(k))})

    def jogar(k):
        if k is None:
            pool, sub = b.pool_materia(materia), "*"
        else:
            sub, pool = subs[k]
        qs = data.escolher(pool, POR_FASE, app.save)
        nome = f"{materia} · {'Mistão' if sub == '*' else sub}"
        prox_k = 0 if k is None else k + 1
        app.jogar(qs, nome, f"lista:{materia}:{sub}", nome, idx,
                  proxima=(lambda: jogar(prox_k)) if prox_k < len(subs) else None,
                  repetir=lambda: jogar(k))

    menu.ao_voltar = montar
    montar()
    app.push(menu)


# ------------------------------------------------------------------ provas

def abrir_provas(app):
    itens = []
    for i, p in enumerate(app.banco.provas):
        c, e = app.save.resumo(p["questoes"])
        n = len(p["questoes"])
        pct = f" · {round(100 * c / (c + e))}% de acerto" if c + e else ""
        itens.append({"label": p["nome"], "info": f"{n} questões · {c + e} respondidas{pct}",
                      "cor": art.paleta(20 + i)["acento"], "acao": (lambda p=p, i=i: abrir_prova(app, p, 20 + i))})
    app.push(Menu(app, "Castelos das Provas", itens, "Provas reais, na ordem original"))


def abrir_prova(app, prova, idx):
    qs = prova["questoes"]
    blocos = [qs[i:i + POR_CASTELO] for i in range(0, len(qs), POR_CASTELO)]
    menu = Menu(app, prova["nome"], [], f"{len(qs)} questões em {len(blocos)} castelos")

    def montar():
        c, e = app.save.resumo(qs)
        menu.subtitulo = f"{len(qs)} questões em {len(blocos)} castelos · nota até agora: {c}/{c + e}"
        menu.itens = []
        for k, bl in enumerate(blocos):
            c, e = app.save.resumo(bl)
            num = lambda q: q["id"].rsplit("-", 1)[1]
            menu.itens.append({"label": f"Castelo {k + 1}: Q{num(bl[0])}–Q{num(bl[-1])}",
                               "info": f"{c} certas / {e} erradas de {len(bl)}",
                               "dir": _melhor(app, f"prova:{prova['key']}:{k}"),
                               "cor": VERDE if c + e == len(bl) else art.paleta(idx)["acento"],
                               "acao": (lambda k=k: jogar(k))})

    def jogar(k):
        nome = f"{prova['nome']} · Castelo {k + 1}"
        app.jogar(blocos[k], nome, f"prova:{prova['key']}:{k}", nome, idx,
                  proxima=(lambda: jogar(k + 1)) if k + 1 < len(blocos) else None,
                  repetir=lambda: jogar(k))

    menu.ao_voltar = montar
    montar()
    app.push(menu)


# ------------------------------------------------------------------ revisão / mistão

def abrir_revisao(app):
    pool = app.save.erradas(app.banco)
    if not pool:
        app.push(Mensagem(app, "Nada para revisar", "Nenhuma questão com erro pendente. Bom sinal."))
        return
    qs = data.escolher(pool, POR_FASE, app.save)
    app.jogar(qs, "Revisão dos erros", "revisao", "Revisão", 13, repetir=lambda: abrir_revisao(app))


def abrir_mistao(app):
    qs = data.escolher(app.banco.todas(), POR_FASE, app.save)
    app.jogar(qs, "Mistão por prevalência", "mistao", "Mistão", 7, repetir=lambda: abrir_mistao(app))


# ------------------------------------------------------------------ estatísticas

class Estatisticas(Estado):
    def __init__(self, app):
        super().__init__(app)
        b = app.banco
        self.linhas = []
        tot_c = tot_e = 0
        for i, m in enumerate(b.materias()):
            c, e = app.save.resumo(b.pool_materia(m))
            tot_c += c
            tot_e += e
            self.linhas.append((m, c, e, len(b.pool_materia(m)), art.paleta(i)["acento"]))
        for i, p in enumerate(b.provas):
            c, e = app.save.resumo(p["questoes"])
            if c + e:
                self.linhas.append((p["nome"], c, e, len(p["questoes"]), art.paleta(20 + i)["acento"]))
        self.tot = (tot_c, tot_e)
        self.rol = 0

    def evento(self, e, inp):
        if inp.foi("voltar") or inp.foi("ok"):
            self.app.pop()
        elif inp.foi("baixo") or (e.type == pygame.MOUSEWHEEL and e.y < 0):
            self.rol = min(max(0, len(self.linhas) - 14), self.rol + 1)
        elif inp.foi("cima") or (e.type == pygame.MOUSEWHEEL and e.y > 0):
            self.rol = max(0, self.rol - 1)

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        painel(tela, (80, 30, W - 160, H - 60))
        c, e = self.tot
        titulo_px(tela, "Estatísticas", AMARELO, W // 2, 44)
        pct = f"{round(100 * c / (c + e))}%" if c + e else "–"
        t = f["med"].render(f"Listas: {c} certas · {e} erradas · aproveitamento {pct}", True, TINTA)
        tela.blit(t, (W // 2 - t.get_width() // 2, 110))
        y = 155
        for nome, c, e, n, cor in self.linhas[self.rol:self.rol + 14]:
            tela.blit(f["peq"].render(nome[:26], True, TINTA), (120, y))
            x0, larg = 400, 560
            pygame.draw.rect(tela, (235, 228, 210), (x0, y + 2, larg, 20), border_radius=6)
            if c + e:
                wc = int(larg * c / (c + e))
                pygame.draw.rect(tela, VERDE, (x0, y + 2, wc, 20), border_radius=6)
                pygame.draw.rect(tela, VERMELHO, (x0 + wc, y + 2, larg - wc, 20), border_radius=6)
            pygame.draw.rect(tela, TINTA, (x0, y + 2, larg, 20), 2, border_radius=6)
            info = f"{c}/{c + e}" + (f" ({round(100 * c / (c + e))}%)" if c + e else "") + f" · de {n}"
            tela.blit(f["peq"].render(info, True, TINTA), (x0 + larg + 14, y))
            y += 34
        sombra(tela, "Barra = certas (verde) / erradas (vermelho) entre as respondidas · Esc volta",
               f["peq"], (255, 255, 255), (W // 2, H - 26), centro=True)
