"""Minigame "Fluxogramas": aprender gasometria e distúrbios hidroeletrolíticos percorrendo a árvore de decisão.

Um caso aparece com os números; o jogador percorre o FLUXOGRAMA DESENHADO (caixas e setas, a câmera segue o nó
atual) escolhendo, em cada nó, o ramo que os números mandam. Errou: a regra aplicada aos números do caso.
Chegou à folha: diagnóstico, achados do caminho e o ensinamento. Depois, um caso novo.

Como o método ensina (evidência de psicologia da aprendizagem):
  - EXEMPLO RESOLVIDO primeiro: na 1ª vez em cada fluxograma o jogo resolve um caso com você, passo a passo
    (worked-example effect); depois fica no menu.
  - APOIO RETIRADO AOS POUCOS (faded worked examples), 4 níveis por fluxograma:
      1  mapa inteiro com as regras dos ramos e as contas prontas;
      2  regras e contas somem: nos nós com conta você CALCULA antes de escolher o ramo (AG, Winter, Δ/Δ…);
      3  o mapa só mostra o caminho percorrido e as saídas do nó atual (o resto vira "?");
      4  de memória: sem mapa além do caminho, ramos embaralhados.
    3 casos perfeitos seguidos sobem um nível; 2 erros de ramo num caso descem um.
  - PRÁTICA NOS PONTOS FRACOS: cada nó guarda acertos e erros; o sorteio favorece casos que passam por onde você
    erra, e "Meus pontos fracos" pinta o fluxograma de verde/amarelo/vermelho.
  - PRÁTICA INTERCALADA no modo misto (os 5 fluxogramas misturados).
Os dados (árvores, geradores e contas) ficam em fluxo_dados.py."""
import random

import pygame

from . import edicao
from .fluxo_dados import ARVORES, laudo, opcoes_calc
from .ui import (AMARELO, H, RETRATO, TINTA, VERDE, VERMELHO, W, Estado, Menu, Mensagem, cortar, eh_pad, painel,
                 quebrar, sombra, titulo_px)

NIVEIS = {1: "mapa com regras e contas", 2: "você calcula", 3: "só o caminho e as saídas", 4: "de memória"}
SOBE, MOEDAS = 3, 2
SECOES = {"eletrolitos": "Gasometria, eletrólitos, rim e anemia", "asma": "Asma · GINA 2026",
          "uti": "UTI · checklist FAST HUG", "uti_treino": "UTI · Treino FAST HUG (BPS e RASS)",
          "espiro": "Espirometria · ATS/ERS 2022 e GOLD 2026",
          "internato_asma": "Asma · GINA 2026, PCDT 2026 e SBPT", "internato_dpoc": "DPOC · GOLD 2026 e PCDT 2026",
          "internato_vm": "Ventilação mecânica", "internato_transf": "Suporte transfusional",
          "internato_reumato": "Reumatologia · LES, SAF e gota", "internato_fa": "FA · CHA₂DS₂-VA e dose do DOAC"}
INTERNATO = ("internato_asma", "internato_dpoc", "internato_vm", "internato_transf", "internato_reumato", "internato_fa")   # Internato · CM2: menu próprio, fora da lista geral
MISTOS = {"asma": ("▶ Treino misto da asma", "Os {n} fluxogramas do GINA 2026 intercalados"),
          "uti": ("▶ Treino misto da UTI", "FAST HUG e FAST HUGS BID intercalados"),
          "uti_treino": ("▶ Treino FAST HUG misto", "BPS e RASS intercalados: pontuar dor e sedação pelo comportamento"),
          "espiro": ("▶ Treino misto da espirometria", "Leitura do exame e DPOC intercalados"),
          "internato_asma": ("▶ Treino misto da asma", "Os {n} fluxogramas da aula de asma intercalados"),
          "internato_dpoc": ("▶ Treino misto da DPOC", "Diagnóstico, início e seguimento intercalados"),
          "internato_vm": ("▶ Treino misto da VM", "Os {n} fluxogramas da aula de VM intercalados"),
          "internato_transf": ("▶ Treino misto da transfusão", "Hemácias, plaquetas, plasma/crio e reações intercalados"),
          "internato_reumato": ("▶ Treino misto da reumato", "LES, nefrite, critérios, SAF e gota intercalados"),
          "internato_fa": ("▶ Treino misto da FA", "Anticoagular? e dose do DOAC intercalados")}

COMO = """O FLUXOGRAMA É O CAMINHO QUE O SEU RACIOCÍNIO DEVE FAZER.

Cada caso traz os números. O fluxograma aparece desenhado; a câmera segue a caixa onde você está. Em cada caixa, escolha o ramo que os números mandam. Na primeira vez em cada caixa, uma mini-aula explica o que aquele passo faz e por que ele vem nessa ordem (o botão "?" reabre). Errou: o jogo mostra a regra com os números do caso; errou de novo, mostra a conclusão. No fim, o laudo do caso numa frase.

1) Primeiro um CASO RESOLVIDO: o jogo percorre um caso com você, explicando cada passo.
2) Depois você joga, e o apoio vai sumindo:
Nível 1 · regras dos ramos visíveis e contas prontas.
Nível 2 · você CALCULA (AG corrigido, Winter, Δ/Δ, ganho do VEF₁, PFE em %, BPS, clearance, P/F, Tobin…) antes de escolher o ramo.
Nível 3 · o mapa só mostra o caminho e as saídas da caixa atual.
Nível 4 · de memória, ramos embaralhados.
3 casos perfeitos seguidos sobem um nível; 2 erros num caso descem um.

3) O jogo guarda onde você erra e sorteia mais casos que passam por lá. Veja em "Meus pontos fracos".

4) Treino misto: os fluxogramas intercalados (todos, ou só os de uma seção) — reconhecer QUAL usar é parte do que a prova cobra."""


def _estado(save, aid):
    st = save.d.setdefault("fluxos", {}).setdefault(aid, {"nivel": 1, "seq": 0, "casos": 0, "perfeitos": 0})
    st.setdefault("nos", {})
    st.setdefault("folhas", {})
    st.setdefault("aulas_vistas", [])
    return st


# ------------------------------------------------------------------ menus

def abrir(app, grupos=None, titulo="Fluxogramas",
          sub="Gasometria, eletrólitos, rim, anemia, asma, UTI e espirometria: percorra o fluxograma caso a caso"):
    """grupos=None: a lista geral (sem os do internato); senão só as seções pedidas."""
    arvs = [a for a in ARVORES if (a.grupo in grupos if grupos else a.grupo not in INTERNATO)]
    menu = Menu(app, titulo, [], sub)

    def montar():
        itens = [{"label": "Como funciona", "cor": (255, 255, 255), "info": "O método e os 4 níveis",
                  "acao": lambda: app.push(Mensagem(app, "Fluxogramas", COMO))},
                 {"label": "▶ Treino misto (intercalado)", "cor": AMARELO, "acao": lambda: app.push(JogoFluxo(app, arvs)),
                  "info": f"Os {len(arvs)} fluxogramas misturados, com mais casos onde você erra"}]
        grupo = None
        for a in arvs:
            if a.grupo != grupo:
                grupo = a.grupo
                itens.append({"secao": SECOES[grupo], "label": ""})
                if grupo in MISTOS:
                    sec = [x for x in arvs if x.grupo == grupo]
                    rot, info = MISTOS[grupo]
                    itens.append({"label": rot, "cor": AMARELO, "acao": lambda sec=sec: app.push(JogoFluxo(app, sec)),
                                  "info": info.format(n=len(sec))})
            st = _estado(app.save, a.id)
            itens.append({"label": a.nome, "cor": (90, 220, 210), "acao": (lambda a=a: _abrir_arvore(app, a)),
                          "info": f"Nível {st['nivel']}/4 ({NIVEIS[st['nivel']]}) · {st['perfeitos']}/{st['casos']} perfeitos"})
        itens.append({"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop})
        menu.itens = itens
        menu._pular_desab(1)

    menu.ao_voltar = montar
    montar()
    app.push(menu)


def _abrir_arvore(app, a):
    st = _estado(app.save, a.id)
    if st["casos"] == 0 and not st.get("viu_exemplo"):           # 1ª vez: começa pelo caso resolvido
        st["viu_exemplo"] = True
        app.push(JogoFluxo(app, [a], exemplo=True))
        return
    itens = [{"label": "▶ Jogar", "cor": AMARELO, "acao": lambda: app.push(JogoFluxo(app, [a])),
              "info": f"Nível {st['nivel']}/4: {NIVEIS[st['nivel']]}"},
             {"label": "Ver um caso resolvido", "cor": (140, 230, 140), "acao": lambda: app.push(JogoFluxo(app, [a], exemplo=True)),
              "info": "O jogo percorre um caso explicando cada passo"},
             {"label": "O fluxograma inteiro", "cor": (200, 160, 250), "acao": lambda: app.push(MapaFluxo(app, a)),
              "info": "Estude a árvore desenhada; toque para aproximar"},
             {"label": "Meus pontos fracos", "cor": (250, 140, 140), "acao": lambda: app.push(MapaFluxo(app, a, calor=True)),
              "info": "O fluxograma pintado pelos seus acertos e erros em cada caixa"},
             {"label": "Voltar", "cor": (180, 180, 180), "acao": app.pop}]
    app.push(Menu(app, a.nome, itens, a.descricao))


# ------------------------------------------------------------------ desenho do fluxograma (caixas e setas)

BW, BH, DX, DY = 156, 46, 176, 128


class Desenho:
    """Layout em camadas (Sugiyama simplificado) do grafo da árvore, em coordenadas de mundo."""

    def __init__(self, arv):
        self.arv = arv
        nos = arv.nos
        prof = {arv.raiz: 0}
        ordem = [arv.raiz]
        mudou = True
        while mudou:                                   # profundidade = caminho mais longo (DAG)
            mudou = False
            for nid in list(prof):
                no = nos[nid]
                if no.folha:
                    continue
                for op in no.opcoes:
                    d = prof[nid] + 1
                    if prof.get(op[2], -1) < d:
                        prof[op[2]] = d
                        mudou = True
                        if op[2] not in ordem:
                            ordem.append(op[2])
        self.prof = prof
        pais = {n: [] for n in prof}
        for nid in prof:
            if not nos[nid].folha:
                for op in nos[nid].opcoes:
                    if nid not in pais[op[2]]:
                        pais[op[2]].append(nid)
        camadas = {}
        for nid in ordem:
            camadas.setdefault(prof[nid], []).append(nid)
        x = {arv.raiz: 0.0}
        for d in sorted(camadas)[1:]:
            cam = camadas[d]
            desejo = {n: sum(x[p] for p in pais[n]) / len(pais[n]) for n in cam}
            cam.sort(key=lambda n: desejo[n])
            pos = []
            for n in cam:
                v = desejo[n]
                if pos and v < pos[-1] + DX:
                    v = pos[-1] + DX
                pos.append(v)
            desvio = sum(desejo[n] for n in cam) / len(cam) - sum(pos) / len(pos)
            for n, v in zip(cam, pos):
                x[n] = v + desvio
        self.pos = {n: (x[n], prof[n] * DY) for n in prof}
        xs = [p[0] for p in self.pos.values()]
        self.xmin, self.xmax = min(xs) - BW, max(xs) + BW
        self.ymax = max(p[1] for p in self.pos.values()) + BH + 40
        self.pais = pais

    def desenhar(self, tela, r, centro, s, f, estilo, rotulo_ramo):
        """estilo(nid) -> None (oculto) ou (fundo, borda, texto, espessura, cor_texto);
        rotulo_ramo(nid, k) -> None ou (texto, destaque: bool)."""
        clip = tela.get_clip()
        tela.set_clip(r)
        cx, cy = centro

        def tp(px, py):
            return int(r.centerx + (px - cx) * s), int(r.centery + (py - cy) * s)
        fonte = f["peq"] if s < 0.95 else f["q"]
        mini = f["peq"]
        # setas primeiro
        rotulos = []
        multi_feitos = set()
        for nid, (px, py) in self.pos.items():
            no = self.arv.nos[nid]
            if no.folha or estilo(nid) is None:
                continue
            n = len(no.opcoes)
            for k, op in enumerate(no.opcoes):
                if estilo(op[2]) is None:
                    continue
                rot = rotulo_ramo(nid, k)
                destaque = bool(rot and rot[1])
                qx, qy = self.pos[op[2]]
                sx = px + (k - (n - 1) / 2) * (BW / max(n, 1)) * 0.8
                y0, y3 = py + BH / 2, qy - BH / 2
                i_cheg, m_cheg = self._indice_chegada(nid, k)
                # ramos que convergem no mesmo destino dividem UM rótulo ("<1 · 1–2"): não se empilham
                grupo = [(j, rotulo_ramo(nid, j)) for j in self._irmaos(nid, k)]
                visiveis = [(j, g) for j, g in grupo if g]
                duas = bool(m_cheg == 1 and rot and len(rot) > 2 and rot[2])
                altas = 2 if duas or len(visiveis) > 1 else 1
                ym = max(y3 - 20 - 18 * altas, y0 + 8)        # o traço horizontal passa acima do rótulo
                ex = qx + (i_cheg - (m_cheg - 1) / 2) * 10          # ramos que convergem chegam lado a lado
                pts = [tp(sx, y0), tp(sx, ym), tp(ex, ym), tp(ex, y3)]
                cor = (70, 150, 80) if destaque else (175, 160, 150)
                pygame.draw.lines(tela, cor, False, pts, max(1, int((4 if destaque else 2) * s)))
                ax, ay = pts[-1]
                pygame.draw.polygon(tela, cor, [(ax, ay), (ax - int(6 * s), ay - int(9 * s)), (ax + int(6 * s), ay - int(9 * s))])
                if s < 0.55 or not rot or visiveis[0][0] != k:
                    continue                                  # pequeno demais, ou o rótulo do grupo já saiu
                if len(self.pais.get(op[2], [])) > 1:
                    # destino com vários pais (RASS → "Alvo"): UM rótulo com todos os ramos que chegam, senão os
                    # rótulos de cada pai caem no mesmo ponto; prefixo comum sai uma vez ("RASS 0 · +1 · −2")
                    if op[2] in multi_feitos:
                        continue
                    multi_feitos.add(op[2])
                    todos = [rotulo_ramo(p, j) for p in self.pais[op[2]] if estilo(p) is not None
                             for j, o in enumerate(self.arv.nos[p].opcoes) if o[2] == op[2]]
                    todos = [g for g in todos if g]
                    txts = [g[0] for g in todos]
                    pref = {t.split(" ", 1)[0] for t in txts}
                    if len(pref) == 1 and next(iter(pref)).isupper() and all(" " in t for t in txts):
                        txts = [txts[0]] + [t.split(" ", 1)[1] for t in txts[1:]]
                    rotulos.append((txts, any(g[1] for g in todos), tp(qx, y3), None))
                elif duas:
                    rotulos.append((rot[0], destaque, tp(qx, y3), rot[2]))
                else:
                    txt = [g[0] for _, g in visiveis] if len(visiveis) > 1 else rot[0]
                    rotulos.append((txt, any(g[1] for _, g in visiveis), tp(qx, y3), None))
        # caixas
        for nid, (px, py) in self.pos.items():
            e = estilo(nid)
            if e is None:
                continue
            fundo, borda, texto, esp, cor_txt = e
            rr = pygame.Rect(0, 0, int(BW * s), int(BH * s))
            rr.center = tp(px, py)
            if not rr.colliderect(r):
                continue
            folha = self.arv.nos[nid].folha
            pygame.draw.rect(tela, fundo, rr, border_radius=int((18 if folha else 8) * s))
            pygame.draw.rect(tela, borda, rr, max(1, int(esp * s)), border_radius=int((18 if folha else 8) * s))
            fc = fonte
            for cand in (fonte, mini):                    # encolhe a letra antes de partir uma palavra no meio
                if all(cand.size(pal)[0] <= rr.w - 8 for pal in texto.split()) and len(quebrar(texto, cand, rr.w - 8)) <= 2:
                    fc = cand
                    break
            else:
                fc = mini
            lns = quebrar(texto, fc, rr.w - 8)[:2]
            for i, ln in enumerate(lns):
                t = fc.render(cortar(ln, fc, rr.w - 6), True, cor_txt)
                tela.blit(t, t.get_rect(center=(rr.centerx, rr.centery + (i - (len(lns) - 1) / 2) * fc.get_height() * 0.95)))
        # rótulos dos ramos por cima de tudo, com fundo
        for txt, destaque, (lx, ly), regra in rotulos:
            lim = int(DX * s * 0.98)
            cor = (30, 90, 40) if destaque else (110, 95, 95)
            if isinstance(txt, list):                      # ramos convergentes: numa linha se couber, senão empilha
                pacote = []                                # junta vizinhos na mesma linha enquanto couber
                for x in txt:
                    if pacote and mini.size(pacote[-1] + " · " + x)[0] <= lim:
                        pacote[-1] += " · " + x
                    else:
                        pacote.append(x)
                linhas = [(x, cor) for x in pacote[:3]]
            else:
                linhas = [(txt, cor)] + ([(regra, (80, 110, 150))] if regra else [])
            ts = [mini.render(cortar(x, mini, lim), True, c) for x, c in linhas]
            w = max(t.get_width() for t in ts) + 8
            hl = ts[0].get_height()
            fundo = pygame.Rect(0, 0, w, hl * len(ts) + 2)
            fundo.midbottom = (lx, ly - max(3, int(10 * s)))      # logo acima da ponta da seta
            pygame.draw.rect(tela, (225, 245, 225) if destaque else (255, 252, 240), fundo, border_radius=6)
            for i, t in enumerate(ts):
                tela.blit(t, t.get_rect(midtop=(fundo.centerx, fundo.y + 1 + i * hl)))
        tela.set_clip(clip)

    def _irmaos(self, nid, k):
        destino = self.arv.nos[nid].opcoes[k][2]
        return [j for j, op in enumerate(self.arv.nos[nid].opcoes) if op[2] == destino]

    def _indice_chegada(self, nid, k):
        """Ramos que chegam ao mesmo nó saem em alturas diferentes (para os rótulos não se sobreporem)."""
        destino = self.arv.nos[nid].opcoes[k][2]
        irmaos = [j for j, op in enumerate(self.arv.nos[nid].opcoes) if op[2] == destino]
        return irmaos.index(k), len(irmaos)


# ------------------------------------------------------------------ o jogo

class JogoFluxo(Estado):
    def __init__(self, app, arvores, exemplo=False):
        super().__init__(app)
        self.arvores = arvores
        self.exemplo = exemplo
        self.rng = random.Random()
        self.t = 0
        self.desenhos = {}
        self.cam = None
        self._novo()

    # -- sorteio adaptativo: mais casos que passam por onde você erra
    def _escolher_alvo(self, arv, st):
        if not hasattr(arv, "_caminhos"):
            arv._caminhos = {a: [n for n, _ in arv.percorrer(arv.gerar(random.Random(7), a))[0]] for a in arv.alvos}
        pesos = []
        for alvo in arv.alvos:
            pior = 0.0
            for nid in arv._caminhos[alvo]:
                c, e = st["nos"].get(nid, [0, 0])
                if c + e:
                    pior = max(pior, e / (c + e))
            visto = st["folhas"].get(alvo, 0)
            pesos.append(1 + 4 * pior + (1.5 if visto == 0 else 0))
        return self.rng.choices(arv.alvos, pesos)[0]

    def _novo(self):
        if len(self.arvores) > 1:
            pesos = [5 - _estado(self.app.save, a.id)["nivel"] for a in self.arvores]
            self.arv = self.rng.choices(self.arvores, pesos)[0]
        else:
            self.arv = self.arvores[0]
        if self.arv.id not in self.desenhos:
            self.desenhos[self.arv.id] = Desenho(self.arv)
        self.des = self.desenhos[self.arv.id]
        self.st = _estado(self.app.save, self.arv.id)
        self.nivel = 1 if self.exemplo else self.st["nivel"]
        alvo = self._escolher_alvo(self.arv, self.st)
        self.caso = self.arv.gerar(self.rng, alvo)
        self.certo, self.folha = self.arv.percorrer(self.caso)
        self.passo = 0
        self.erros = self.erros_calc = 0
        self.erros_no = 0
        self.feedback = ""
        self.ok_msg = ""
        self.errado = None
        self.fim = False
        self.msg_nivel = ""
        self._ordem = {}
        self.rects = []
        self.r_prox = self.r_sair = self.r_passo = pygame.Rect(0, 0, 0, 0)
        self.r_ajuda = self.r_entendi = pygame.Rect(0, 0, 0, 0)
        self.aula_aberta = False
        self.cam = None
        self.sel, self._cols, self._chave_sel = 0, 1, None
        self._entrar_no()

    def _no(self):
        return self.arv.nos[self.certo[self.passo][0]]

    def _entrar_no(self):
        """Ao chegar num nó: na 1ª visita (níveis 1–2) abre a mini-aula do passo; no nível 2+, se o nó tem conta,
        a conta vem antes do ramo."""
        self.calc = None
        self.erros_no = 0
        no = self._no()
        vistas = self.st["aulas_vistas"]
        self.aula_aberta = False
        if not self.exemplo and self.nivel <= 2 and no.id not in vistas:
            vistas.append(no.id)
            self.aula_aberta = True
        if no.calc and self.nivel >= 2 and not self.exemplo:
            self.calc = opcoes_calc(no, self.caso, self.rng)

    def _ordem_opcoes(self, no):
        idx = list(range(len(no.opcoes)))
        if self.nivel >= 4:
            if no.id not in self._ordem:
                self.rng.shuffle(idx)
                self._ordem[no.id] = idx
            return self._ordem[no.id]
        return idx

    def _contar(self, nid, ok):
        reg = self.st["nos"].setdefault(nid, [0, 0])
        reg[0 if ok else 1] += 1

    def escolher(self, i):
        if self.fim or self.exemplo:
            return
        no = self._no()
        if self.calc:                                  # etapa da conta
            pergunta, alts, certo, formula, motivo = self.calc
            if i == certo:
                self.app.audio.tocar("moeda")
                self.ok_msg = f"Isso: {formula}."
                self.feedback, self.errado, self.calc, self.erros_no = "", None, None, 0
            else:
                self.app.audio.tocar("dano")
                self.erros_calc += 1
                self.erros_no += 1
                self.errado = i
                self.feedback = f"{alts[i]}: {motivo.get(alts[i], 'errou a conta')}."
                if self.erros_no >= 2:
                    self.feedback += f" A conta: {formula}."
                else:
                    self.feedback += " Refaça a conta com os números do caso."
            return
        certo = self.certo[self.passo][1]
        if i == certo:
            self.app.audio.tocar("moeda")
            if self.erros_no == 0:
                self._contar(no.id, True)
            self.ok_msg = no.explica(self.caso) if self.nivel <= 2 else ""
            self.feedback, self.errado = "", None
            self.passo += 1
            if self.passo >= len(self.certo):
                self._terminar()
            else:
                self._entrar_no()
        else:
            self.app.audio.tocar("dano")
            if self.erros_no == 0:
                self._contar(no.id, False)
            self.erros += 1
            self.erros_no += 1
            self.errado = i
            self.feedback = no.explica(self.caso)
            if self.erros_no >= 2:                       # 2º erro no mesmo nó: a conclusão (e o ramo certo acende)
                op = no.opcoes[certo]
                self.feedback += f" Portanto: {op[0]} ({op[1]})."

    def _avancar_exemplo(self):
        if self.passo < len(self.certo):
            self.passo += 1
            if self.passo >= len(self.certo):
                self.fim = True
                self.msg_nivel = "Agora é sua vez: o próximo caso você resolve."
            else:
                self._entrar_no()

    def _terminar(self):
        self.fim = True
        st, save = self.st, self.app.save
        st["casos"] += 1
        st["folhas"][self.folha.id] = st["folhas"].get(self.folha.id, 0) + 1
        if self.erros == 0 and self.erros_calc == 0:
            st["perfeitos"] += 1
            st["seq"] += 1
            save.d["carteira"]["moedas"] = save.d["carteira"].get("moedas", 0) + MOEDAS
            if st["seq"] >= SOBE and st["nivel"] < 4:
                st["nivel"] += 1
                st["seq"] = 0
                self.msg_nivel = f"Subiu para o nível {st['nivel']}: {NIVEIS[st['nivel']]}!"
            else:
                self.msg_nivel = f"Caso perfeito (+{MOEDAS} moedas) · {st['seq']}/{SOBE} para subir de nível"
        else:
            st["seq"] = 0
            if self.erros >= 2 and st["nivel"] > 1:
                st["nivel"] -= 1
                self.msg_nivel = f"Voltou para o nível {st['nivel']}: mais apoio até firmar o caminho."
            else:
                partes = []
                if self.erros:
                    partes.append(f"{self.erros} erro(s) de ramo")
                if self.erros_calc:
                    partes.append(f"{self.erros_calc} de conta")
                self.msg_nivel = " e ".join(partes) + ". O próximo caso perfeito recomeça a sequência."
        save.salvar()

    # -- eventos
    def evento(self, e, inp):
        if inp.foi("voltar"):
            self.app.pop()
            return
        clique = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
        if self.fim:
            if (clique and self.r_prox.collidepoint(e.pos)) or inp.foi("ok"):
                self.exemplo = False
                self._novo()
            elif clique and self.r_sair.collidepoint(e.pos):
                self.app.pop()
            return
        if self.exemplo:
            if (clique and self.r_passo.collidepoint(e.pos)) or inp.foi("ok") or inp.foi("dir"):
                self._avancar_exemplo()
            return
        if self.aula_aberta:
            if (clique and self.r_entendi.collidepoint(e.pos)) or inp.foi("ok"):
                self.aula_aberta = False
            return
        if (clique and self.r_ajuda.collidepoint(e.pos)) or (e.type == pygame.KEYDOWN and e.key == pygame.K_SLASH) \
                or eh_pad(e, "Y"):
            self.aula_aberta = True
            return
        if self.rects:                                 # controle/teclado: setas andam pela grade, A/Enter escolhe
            n, c = len(self.rects), max(1, self._cols)
            passo = (-1 if inp.foi("esq") else 1 if inp.foi("dir") else -c if inp.foi("cima") else
                     c if inp.foi("baixo") else 0)
            if passo:
                self.sel = (self.sel + passo) % n
                return
            if inp.foi("ok"):
                self.escolher(self.rects[min(self.sel, n - 1)][1])
                return
        if clique:
            for r, i in self.rects:
                if r.collidepoint(e.pos):
                    self.escolher(i)
                    return
        if e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_4:
            k = e.key - pygame.K_1
            if self.calc:
                if k < 4:
                    self.escolher(k)
            else:
                ordem = self._ordem_opcoes(self._no())
                if k < len(ordem):
                    self.escolher(ordem[k])

    def update(self, inp):
        self.t += 1

    # -- layout
    def _layout(self):
        if RETRATO:
            caso = pygame.Rect(26, 90, W - 52, 300)
            # o desenho do fluxograma ocupa o que a parte de baixo (pergunta, aula) não usou no quadro anterior
            livre = H - 50 - caso.bottom - 20
            usado = getattr(self, "_usado", None)
            alvo = int(H * 0.36) if usado is None or self.fim else max(int(H * 0.3), livre - max(usado, 200))
            atual = getattr(self, "_mapa_h", alvo)
            self._mapa_h = atual + (alvo - atual) * 0.25 if abs(alvo - atual) > 2 else alvo
            mapa = pygame.Rect(26, caso.bottom + 10, W - 52, int(self._mapa_h))
            baixo = pygame.Rect(26, mapa.bottom + 10, W - 52, H - mapa.bottom - 50)
        else:
            caso = pygame.Rect(26, 90, 380, H - 140)
            mapa = pygame.Rect(420, 90, W - 446, 290)
            baixo = pygame.Rect(420, mapa.bottom + 10, W - 446, H - mapa.bottom - 50)
        return caso, mapa, baixo

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        painel(tela, (12, 12, W - 24, H - 24))
        titulo_px(tela, "Caso resolvido" if self.exemplo else "Fluxograma", AMARELO, W // 2, 24, 3)
        cab = (f"{self.arv.nome}  ·  " + ("acompanhe cada passo" if self.exemplo else
               f"nível {self.nivel}/4 ({NIVEIS[self.nivel]})  ·  {self.st['seq']}/{SOBE} seguidos"))
        t = f["peq"].render(cortar(cab, f["peq"], W - 60), True, (120, 100, 100))
        tela.blit(t, (W // 2 - t.get_width() // 2, 62))
        caso_r, mapa_r, baixo_r = self._layout()
        self._desenhar_caso(tela, caso_r)
        self._desenhar_mapa(tela, mapa_r)
        if self.fim:
            self._desenhar_fim(tela, baixo_r)
        elif self.exemplo:
            self._desenhar_exemplo(tela, baixo_r)
        elif self.aula_aberta:
            self._desenhar_aula(tela, baixo_r)
        else:
            self._desenhar_pergunta(tela, baixo_r)
        self._legenda(tela)

    def _legenda(self, tela):
        """Rodapé com os botões do controle (e as teclas) para o que está na tela."""
        if edicao.ANDROID:
            return
        if self.fim:
            txt = "A / Enter: próximo caso  ·  B / Esc: sair"
        elif self.exemplo:
            txt = "A / Enter ou →: próximo passo  ·  B / Esc: sair"
        elif self.aula_aberta:
            txt = "A / Enter: entendi, vamos decidir  ·  B / Esc: sair"
        else:
            txt = "Direcional: escolhe a opção  ·  A / Enter: confirma  ·  Y ou ?: aula do passo  ·  B / Esc: sair"
        f = self.app.f["peq"]
        t = f.render(cortar(txt, f, W - 60), True, (110, 95, 95))
        tela.blit(t, (W // 2 - t.get_width() // 2, H - 22 - t.get_height()))

    def _desenhar_aula(self, tela, r):
        """Mini-aula do passo: o que esta caixa faz e por que ela vem agora."""
        f = self.app.f
        no = self._no()
        tela.blit(f["med"].render(f"Antes de decidir · {no.rotulo}", True, (150, 110, 20)), (r.x + 4, r.y))
        y = self._caixa_texto(tela, r.x, r.y + 32, r.w, no.aula, (255, 246, 205), (226, 196, 90), f["q"]) + 12
        self.r_entendi = pygame.Rect(r.x, min(y, r.bottom - 66), r.w, 60)
        pygame.draw.rect(tela, AMARELO, self.r_entendi, border_radius=14)
        pygame.draw.rect(tela, TINTA, self.r_entendi, 2, border_radius=14)
        t = f["med"].render("Entendi: vamos decidir", True, TINTA)
        tela.blit(t, t.get_rect(center=self.r_entendi.center))
        self._usado = y + 72 - r.y

    def _desenhar_caso(self, tela, r):
        f = self.app.f
        pygame.draw.rect(tela, (250, 244, 228), r, border_radius=12)
        pygame.draw.rect(tela, (210, 196, 170), r, 2, border_radius=12)
        y = r.y + 10
        oculto = self.nivel >= 3 and not self.fim
        texto = ("Contexto escondido neste nível: decida só pelos números." if oculto else self.caso["texto"])
        for ln in quebrar(texto, f["q"], r.w - 24)[:3]:
            tela.blit(f["q"].render(ln, True, (140, 120, 120) if oculto else TINTA), (r.x + 12, y))
            y += 26
        y += 6
        itens = list(self.caso["mostrar"])
        if self.nivel == 1:
            itens += [("» " + n, v) for n, v in self.arv.contas(self.caso)]
        alt = 22
        descritivo = getattr(self.arv, "descritivo", False)   # BPS/RASS: o comportamento descrito é o dado
        colunas = 2 if RETRATO and not descritivo else 1
        larg = (r.w - 24) // colunas
        por_col = -(-len(itens) // colunas)
        if descritivo:                                         # uma coluna, valor quebrado em linhas (nada cortado)
            for nome, valor in itens:
                conta = nome.startswith("» ")
                tn = f["peq"].render(nome.lstrip("» ") + ":", True, (40, 110, 160) if conta else (120, 100, 100))
                tela.blit(tn, (r.x + 12, y))
                for ln in quebrar(str(valor), f["peq"], larg - tn.get_width() - 14):
                    if y + alt > r.bottom - 4:
                        return
                    tela.blit(f["peq"].render(ln, True, (40, 110, 160) if conta else TINTA), (r.x + 18 + tn.get_width(), y))
                    y += alt
                y += 4
            return
        for k, (nome, valor) in enumerate(itens):
            col, lin = divmod(k, por_col)
            x, yy = r.x + 12 + col * larg, y + lin * alt
            if yy + alt > r.bottom - 4:
                continue
            conta = nome.startswith("» ")
            tn = f["peq"].render(cortar(nome.lstrip("» "), f["peq"], larg * 0.55) + ":", True,
                                 (40, 110, 160) if conta else (120, 100, 100))
            tela.blit(tn, (x, yy))
            tv = f["peq"].render(cortar(str(valor), f["peq"], larg - tn.get_width() - 14), True,
                                 (40, 110, 160) if conta else TINTA)
            tela.blit(tv, (x + tn.get_width() + 6, yy))

    def _estilos(self, nivel):
        caminho = [n for n, _ in self.certo[:self.passo]]
        atual = None if self.fim else self.certo[self.passo][0] if self.passo < len(self.certo) else None
        saidas = set()
        if atual:
            saidas = {op[2] for op in self.arv.nos[atual].opcoes}
        final = self.folha.id if self.fim else None
        pulso = abs((self.t % 50) - 25) / 25

        def estilo(nid):
            no = self.arv.nos[nid]
            if nid == final:
                return ((190, 240, 190), (40, 140, 60), no.rotulo, 3, TINTA)
            if nid == atual:
                return (AMARELO, (200, 120 + int(80 * pulso), 30), no.rotulo, 3, TINTA)
            if nid in caminho:
                return ((215, 240, 215), (90, 160, 100), no.rotulo, 2, TINTA)
            if nid in saidas:
                txt = no.rotulo if nivel <= 3 else "?"
                return ((255, 252, 240), (150, 130, 110), txt, 2, (90, 80, 80))
            if nivel <= 2:
                return ((246, 240, 228), (215, 205, 190), no.rotulo, 1, (160, 145, 140))
            if nivel == 3:
                return ((240, 234, 222), (220, 210, 196), "?", 1, (190, 180, 175))
            return None

        def ramo(nid, k):
            no = self.arv.nos[nid]
            no_ok = nid in caminho
            escolhido = no_ok and dict(self.certo).get(nid) == k
            if nivel >= 3 and not (no_ok or nid == atual):
                return None
            if nivel >= 3 and no_ok and not escolhido:
                return None
            return (no.opcoes[k][0], escolhido, no.opcoes[k][1] if nivel == 1 else None)
        return estilo, ramo

    def _desenhar_mapa(self, tela, r):
        pygame.draw.rect(tela, (252, 249, 240), r, border_radius=12)
        pygame.draw.rect(tela, (210, 196, 170), r, 2, border_radius=12)
        alvo_id = self.folha.id if self.fim else self.certo[min(self.passo, len(self.certo) - 1)][0]
        ax, ay = self.des.pos[alvo_id]
        if not self.fim:                                  # mira entre o nó atual e as saídas dele
            ay += DY * 0.45
        s = min(1.0, r.w / (3.9 * DX)) if RETRATO else min(1.0, r.w / (5.2 * DX))
        if self.cam is None:
            self.cam = [ax, ay]
        self.cam[0] += (ax - self.cam[0]) * 0.25
        self.cam[1] += (ay - self.cam[1]) * 0.25
        estilo, ramo = self._estilos(self.nivel)
        self.des.desenhar(tela, r.inflate(-6, -6), self.cam, s, self.app.f, estilo, ramo)

    def _caixa_texto(self, tela, x, y, w, texto, fundo, borda, fonte):
        lns = quebrar(texto, fonte, w - 20)
        h = 14 + (fonte.get_height() + 2) * len(lns)
        rr = pygame.Rect(x, y, w, h)
        pygame.draw.rect(tela, fundo, rr, border_radius=12)
        pygame.draw.rect(tela, borda, rr, 2, border_radius=12)
        for k, ln in enumerate(lns):
            tela.blit(fonte.render(ln, True, TINTA), (x + 10, y + 7 + (fonte.get_height() + 2) * k))
        return rr.bottom

    def _botoes(self, tela, r, y, textos, subs, estilos):
        f = self.app.f
        n = len(textos)
        cols = n if n <= 3 or not RETRATO else 2
        if n == 4 and not RETRATO:
            cols = 4
        self._cols = cols
        chave = (id(self.caso), self.passo, self.calc is None)    # opções novas: o cursor volta para a 1ª
        if chave != self._chave_sel:
            self._chave_sel, self.sel = chave, 0
        self.sel = min(self.sel, n - 1)
        alt = 62
        larg = (r.w - 10 * (cols - 1)) // cols
        rects = []
        for k in range(n):
            c, l = k % cols, k // cols
            rr = pygame.Rect(r.x + c * (larg + 10), y + l * (alt + 10), larg, alt)
            cores = {"opcao": ((255, 252, 240), TINTA), "erro": ((250, 190, 190), TINTA),
                     "dica": ((200, 245, 200), TINTA), "certo": ((190, 240, 190), TINTA)}
            fundo, cor = cores[estilos[k]]
            pygame.draw.rect(tela, fundo, rr, border_radius=12)
            pygame.draw.rect(tela, cor, rr, 2, border_radius=12)
            if k == self.sel and not edicao.ANDROID:                # cursor do controle
                pygame.draw.rect(tela, (230, 160, 20), rr.inflate(8, 8), 4, border_radius=15)
            t = f["med"].render(cortar(f"{k + 1}. {textos[k]}", f["med"], rr.w - 12), True, cor)
            if subs[k]:
                s = f["peq"].render(cortar(subs[k], f["peq"], rr.w - 12), True, (90, 110, 140))
                tela.blit(t, t.get_rect(center=(rr.centerx, rr.centery - 10)))
                tela.blit(s, s.get_rect(center=(rr.centerx, rr.centery + 14)))
            else:
                tela.blit(t, t.get_rect(center=rr.center))
            rects.append(rr)
        return rects, y + (-(-n // cols)) * (alt + 10)

    def _desenhar_pergunta(self, tela, r):
        f = self.app.f
        no = self._no()
        y = r.y
        if self.ok_msg and not self.feedback:
            y = self._caixa_texto(tela, r.x, y, r.w, "Certo. " + self.ok_msg, (226, 245, 226), (120, 180, 120), f["peq"]) + 8
        if self.calc:
            pergunta, alts, certo, formula, motivo = self.calc
            y = self._caixa_texto(tela, r.x, y, r.w, f"Conta antes do ramo · {pergunta}", (226, 238, 255),
                                  (120, 150, 210), f["med"]) + 10
            estilos = ["erro" if k == self.errado else "dica" if self.erros_no >= 2 and k == certo else "opcao"
                       for k in range(len(alts))]
            rects, y = self._botoes(tela, r, y, alts, [""] * len(alts), estilos)
            self.rects = list(zip(rects, range(len(alts))))
        else:
            y0 = y
            y = self._caixa_texto(tela, r.x, y, r.w - 62, no.pergunta, (255, 246, 205), (226, 196, 90), f["med"]) + 10
            self.r_ajuda = pygame.Rect(r.right - 54, y0, 54, max(46, y - y0 - 10))
            pygame.draw.rect(tela, (226, 238, 255), self.r_ajuda, border_radius=12)
            pygame.draw.rect(tela, (120, 150, 210), self.r_ajuda, 2, border_radius=12)
            t = f["grande"].render("?", True, (50, 80, 150))
            tela.blit(t, t.get_rect(center=self.r_ajuda.center))
            ordem = self._ordem_opcoes(no)
            certo = self.certo[self.passo][1]
            textos = [no.opcoes[i][0] for i in ordem]
            subs = [no.opcoes[i][1] if self.nivel == 1 else "" for i in ordem]
            estilos = ["erro" if i == self.errado else "dica" if self.erros_no >= 2 and i == certo else "opcao" for i in ordem]
            rects, y = self._botoes(tela, r, y, textos, subs, estilos)
            self.rects = list(zip(rects, ordem))
        if self.feedback:
            for ln in quebrar("Ainda não: " + self.feedback, f["q"], r.w - 10)[:5]:
                tela.blit(f["q"].render(ln, True, VERMELHO), (r.x + 4, y))
                y += 25
        self._usado = y + 8 - r.y

    def _desenhar_exemplo(self, tela, r):
        f = self.app.f
        no = self._no()
        y = self._caixa_texto(tela, r.x, r.y, r.w, no.pergunta, (255, 246, 205), (226, 196, 90), f["med"]) + 8
        i = self.certo[self.passo][1]
        txt = (f"Por que este passo: {no.aula}\n\nResposta: {no.opcoes[i][0]} ({no.opcoes[i][1]}). "
               f"Com os números do caso: {no.explica(self.caso)}")
        if no.calc:
            pergunta, certo, erros, formula, casas = no.calc(self.caso)
            txt = f"Conta: {formula}. " + txt
        y = self._caixa_texto(tela, r.x, y, r.w, txt, (226, 245, 226), (120, 180, 120), f["q"]) + 10
        self.r_passo = pygame.Rect(r.x, min(y, r.bottom - 66), r.w, 60)
        pygame.draw.rect(tela, AMARELO, self.r_passo, border_radius=14)
        pygame.draw.rect(tela, TINTA, self.r_passo, 2, border_radius=14)
        t = f["med"].render(f"Próximo passo ▶   ({self.passo + 1} de {len(self.certo)})", True, TINTA)
        tela.blit(t, t.get_rect(center=self.r_passo.center))
        self._usado = y + 72 - r.y

    def _desenhar_fim(self, tela, r):
        f = self.app.f
        y = r.y
        perfeito = (self.erros + self.erros_calc == 0) and not self.exemplo
        titulo = "Caso resolvido" if self.exemplo else "Perfeito!" if perfeito else "Chegou!"
        tela.blit(f["grande"].render(titulo, True, (40, 140, 60) if perfeito or self.exemplo else (170, 120, 20)), (r.x + 4, y))
        y += 44
        tela.blit(f["peq"].render("O laudo:", True, (120, 100, 100)), (r.x + 4, y))
        y += 22
        txt = laudo(self.arv, self.certo, self.folha)
        fl, alt = f["med"], 28
        if len(quebrar(txt, fl, r.w - 10)) * alt > r.bottom - 120 - y:   # laudo longo (checklist): letra menor
            fl, alt = f["q"], 25
        for ln in quebrar(txt, fl, r.w - 10):
            tela.blit(fl.render(ln, True, TINTA), (r.x + 4, y))
            y += alt
        y += 4
        for ln in quebrar(self.folha.ensina, f["q"], r.w - 10):
            if y > r.bottom - 120:
                break
            tela.blit(f["q"].render(ln, True, (90, 80, 80)), (r.x + 4, y))
            y += 25
        y = max(y + 6, r.bottom - 112)
        sombra(tela, cortar(self.msg_nivel, f["peq"], r.w - 10), f["peq"], (40, 110, 60) if perfeito else (160, 90, 40),
               (r.x + 4, y))
        bw = (r.w - 12) // 2
        self.r_prox = pygame.Rect(r.x, r.bottom - 70, bw, 62)
        self.r_sair = pygame.Rect(r.x + bw + 12, r.bottom - 70, bw, 62)
        for rr, txt, cor in ((self.r_prox, "Próximo caso" if not self.exemplo else "Agora eu jogo", AMARELO),
                             (self.r_sair, "Sair", (255, 252, 240))):
            pygame.draw.rect(tela, cor, rr, border_radius=14)
            pygame.draw.rect(tela, TINTA, rr, 2, border_radius=14)
            t = f["med"].render(txt, True, TINTA)
            tela.blit(t, t.get_rect(center=rr.center))


# ------------------------------------------------------------------ o fluxograma inteiro (estudo) e os pontos fracos

class MapaFluxo(Estado):
    """A árvore inteira desenhada. Toque/clique aproxima naquele ponto (toque de novo afasta); arrastar ou setas
    movem. Com calor=True, cada caixa é pintada pelo seu desempenho nela (verde ≥ 80%, amarelo 50–79%,
    vermelho < 50%, cinza = ainda sem dados)."""
    passo_rolagem = 30

    def __init__(self, app, arv, calor=False):
        super().__init__(app)
        self.arv = arv
        self.calor = calor
        self.des = Desenho(arv)
        self.zoom = True                                   # começa perto, no topo da árvore
        r = self._area()
        x0, y0 = self.des.pos[arv.raiz]
        self.cam = [x0, y0 + r.h / 2 - 50]
        self.st = _estado(app.save, arv.id)
        self.r_geral = pygame.Rect(0, 0, 0, 0)

    def _area(self):
        return pygame.Rect(26, 84, W - 52, H - 170)

    def _escala_ajuste(self, r):
        return min(r.w / (self.des.xmax - self.des.xmin + 40), r.h / (self.des.ymax + 40), 1.0)

    def evento(self, e, inp):
        r = self._area()
        if inp.foi("voltar"):
            self.app.pop()
            return
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.r_geral.collidepoint(e.pos)) or inp.foi("ok"):
            self.zoom = not self.zoom
            if not self.zoom:
                self.cam = [(self.des.xmin + self.des.xmax) / 2, self.des.ymax / 2]
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and r.collidepoint(e.pos):
            s = self._escala()                             # toque centraliza ali (na visão geral, também aproxima)
            self.cam = [self.cam[0] + (e.pos[0] - r.centerx) / s, self.cam[1] + (e.pos[1] - r.centery) / s]
            self.zoom = True
        elif e.type == pygame.MOUSEWHEEL:
            self.cam[1] -= e.y * 60
        elif inp.foi("esq"):
            self.cam[0] -= 120
        elif inp.foi("dir"):
            self.cam[0] += 120
        elif inp.foi("cima"):
            self.cam[1] -= 100
        elif inp.foi("baixo"):
            self.cam[1] += 100

    def _escala(self):
        return 1.0 if self.zoom else self._escala_ajuste(self._area())

    def _prender(self):
        r, s = self._area(), self._escala()
        mx, my = r.w / 2 / s, r.h / 2 / s
        lo_x, hi_x = self.des.xmin + mx - 40, self.des.xmax - mx + 40
        lo_y, hi_y = -BH + my - 20, self.des.ymax - my + 20
        self.cam[0] = (lo_x + hi_x) / 2 if lo_x > hi_x else min(max(self.cam[0], lo_x), hi_x)
        self.cam[1] = (lo_y + hi_y) / 2 if lo_y > hi_y else min(max(self.cam[1], lo_y), hi_y)

    def draw(self, tela):
        self.app.cenario.draw(tela)
        f = self.app.f
        painel(tela, (12, 12, W - 24, H - 24))
        titulo_px(tela, ("Pontos fracos · " if self.calor else "") + self.arv.nome, AMARELO, W // 2, 26, 3)
        r = self._area()
        self._prender()
        pygame.draw.rect(tela, (252, 249, 240), r, border_radius=12)
        nos_st = self.st["nos"]

        def estilo(nid):
            no = self.arv.nos[nid]
            if self.calor and not no.folha:
                c, e = nos_st.get(nid, [0, 0])
                if c + e == 0:
                    return ((235, 232, 226), (190, 180, 170), f"{no.rotulo} · —", 2, (120, 110, 110))
                taxa = c / (c + e)
                cor = (190, 240, 190) if taxa >= 0.8 else (255, 236, 160) if taxa >= 0.5 else (250, 180, 180)
                return (cor, TINTA, f"{no.rotulo} · {round(100 * taxa)}%", 2, TINTA)
            if no.folha:
                return ((226, 245, 226), (90, 160, 100), no.rotulo, 2, TINTA)
            return ((255, 246, 205), (200, 160, 60), no.rotulo, 2, TINTA)

        def ramo(nid, k):
            op = self.arv.nos[nid].opcoes[k]
            return (op[0], False, op[1])
        self.des.desenhar(tela, r.inflate(-6, -6), self.cam, self._escala(), f, estilo, ramo)
        if self.calor:
            fracos = sorted(((e / (c + e), nid) for nid, (c, e) in nos_st.items() if c + e >= 2 and e), reverse=True)[:3]
            txt = ("Mais erros em: " + ", ".join(f"{self.arv.nos[n].rotulo} ({round(100 * t)}% de erro)" for t, n in fracos)
                   if fracos else "Ainda sem erros registrados: jogue alguns casos.")
        else:
            txt = ("Toque num ponto para ir até ele · arraste para subir e descer." if edicao.ANDROID else
                   "Clique num ponto para ir até ele · setas/direcional e roda movem · A / Enter: ver tudo ou aproximar"
                   " · B / Esc: voltar")
        for k, ln in enumerate(quebrar(txt, f["peq"], W - 300)[:2]):
            sombra(tela, ln, f["peq"], (120, 100, 100), (40, H - 78 + 22 * k))
        self.r_geral = pygame.Rect(W - 250, H - 82, 220, 48)
        pygame.draw.rect(tela, AMARELO, self.r_geral, border_radius=12)
        pygame.draw.rect(tela, TINTA, self.r_geral, 2, border_radius=12)
        t = f["med"].render("Ver tudo" if self.zoom else "Aproximar", True, TINTA)
        tela.blit(t, t.get_rect(center=self.r_geral.center))
