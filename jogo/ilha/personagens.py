"""Telas de escolha de personagem (ao abrir o jogo) e da loja de itens (nuvens, bastões, roupas).
Os itens são só visuais: depois da escolha, o jogo segue igual. Lógica de compra em loja.py."""
import math

import pygame

from . import edicao, heroi, loja, pets
from .ui import AMARELO, TINTA, VERMELHO, W, H, Estado, painel, quebrar, sombra, titulo_px

CINZA = (150, 140, 140)


def _moedas(app):
    return f"Moedas: {app.save.carteira['moedas']:,}".replace(",", ".")


def _botao(tela, f, r, txt, foco, cor=AMARELO):
    pygame.draw.rect(tela, cor if foco else (255, 252, 240), r, border_radius=14)
    pygame.draw.rect(tela, TINTA, r, 3 if foco else 2, border_radius=14)
    t = f["med"].render(txt, True, TINTA)
    tela.blit(t, t.get_rect(center=r.center))


def _sprite(estado, frame, escala, visual):
    sp = heroi.heroi(estado, frame, True, 1, visual=visual)
    return pygame.transform.scale(sp, (sp.get_width() * escala, sp.get_height() * escala))


class EscolhaPersonagem(Estado):
    """Cartões lado a lado; esq/dir escolhe, cima/baixo alterna entre o botão principal e a Loja.
    Personagem bloqueado: o botão principal compra (com confirmação) e já escolhe."""

    def __init__(self, app, ao_jogar=None):
        super().__init__(app)
        self.ids = list(heroi.PERSONAGENS)
        atual = loja.personagem(app.save)
        self.sel = self.ids.index(atual) if atual in self.ids else 0
        self.foco = 0                    # 0 = Jogar/Comprar, 1 = Loja
        self.confirmar = None
        self.ao_jogar = ao_jogar
        self.t = 0
        n = len(self.ids)
        # páginas de cartões: em pé, grade de 3 colunas com as linhas que couberem; deitado, uma fileira de 6
        cols = min(n, 3) if edicao.RETRATO else min(n, 6)
        linhas = max(1, min(-(-n // cols), (H - 112 - 330) // 302)) if edicao.RETRATO else 1
        self.por_pag = cols * linhas
        larg = min(260, (W - 64 - 8 * (cols - 1)) // cols)
        x0 = (W - (larg * cols + 8 * (cols - 1))) // 2
        self.slots = [pygame.Rect(x0 + (i % cols) * (larg + 8), 112 + (i // cols) * 302, larg, 290)
                      for i in range(self.por_pag)]
        self.paginas = -(-n // self.por_pag)
        y = 112 + 302 * linhas
        self.setas = []
        if self.paginas > 1:             # ◀ 1/3 ▶ embaixo dos cartões
            self.setas = [pygame.Rect(W // 2 - 170, y, 96, 44), pygame.Rect(W // 2 + 74, y, 96, 44)]
            y += 52
        self.y_desc = y + 14
        self.botoes = [pygame.Rect(W // 2 - 220, self.y_desc + 72, 440, 56),
                       pygame.Rect(W // 2 - 220, self.y_desc + 140, 440, 56)]

    @property
    def pagina(self):
        return self.sel // self.por_pag

    @property
    def cartoes(self):
        """(índice do personagem, retângulo) dos cartões da página atual."""
        i0 = self.pagina * self.por_pag
        return [(i0 + k, r) for k, r in enumerate(self.slots) if i0 + k < len(self.ids)]

    @property
    def pid(self):
        return self.ids[self.sel]

    def _seu(self, pid=None):
        return loja.possui(self.app.save, "personagem", pid or self.pid)

    def _mudar(self, d):
        self.sel = (self.sel + d) % len(self.ids)
        self.confirmar = None
        if self._seu():
            loja.escolher_personagem(self.app.save, self.pid)
        self.app.audio.tocar("menu")

    def _ativar(self):
        app = self.app
        if self.foco == 1:
            app.audio.tocar("ovo")
            app.push(Loja(app))
            return
        if not self._seu():
            preco = heroi.PERSONAGENS[self.pid]["preco"]
            if app.save.carteira["moedas"] < preco:
                app.audio.tocar("dano")
                app.toast(f"Faltam {preco - app.save.carteira['moedas']} moedas para desbloquear")
                return
            if self.confirmar != self.pid:
                self.confirmar = self.pid
                app.audio.tocar("menu")
                return
            loja.comprar(app.save, "personagem", self.pid)
            app.audio.tocar("moeda")
            app.toast(f"Desbloqueado: {heroi.PERSONAGENS[self.pid]['nome']}")
            self.confirmar = None
            loja.escolher_personagem(app.save, self.pid)
            return
        app.audio.tocar("ovo")
        loja.escolher_personagem(app.save, self.pid)
        app.pop()
        if self.ao_jogar:
            self.ao_jogar()

    def evento(self, e, inp):
        if inp.foi("esq"):
            self._mudar(-1)
        elif inp.foi("dir"):
            self._mudar(1)
        elif inp.foi("cima") or inp.foi("baixo"):
            self.foco = 1 - self.foco
            self.app.audio.tocar("menu")
        elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self._ativar()
        elif inp.foi("voltar"):          # volta com o último personagem que é seu
            if not self._seu():
                self.sel = self.ids.index(loja.personagem(self.app.save))
            self.foco = 0
            self._ativar()
        elif e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for i, b in enumerate(self.botoes):
                if b.collidepoint(e.pos):
                    self.foco = i
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        self._ativar()
                    return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for d, r in zip((-1, 1), self.setas):
                    if r.collidepoint(e.pos):
                        self.foco = 0
                        alvo = (self.pagina + d) % self.paginas * self.por_pag
                        self._mudar(alvo - self.sel)
                        return
                for i, c in self.cartoes:
                    if c.collidepoint(e.pos) and i != self.sel:
                        self.foco = 0
                        self._mudar(i - self.sel)

    def update(self, inp):
        self.t += 1

    def draw(self, tela):
        app, f = self.app, self.app.f
        app.cenario.draw(tela)
        titulo_px(tela, "Escolha seu personagem", (255, 255, 255), W // 2, 26, 3)
        sombra(tela, _moedas(app) + " · os itens da loja servem para todos", f["peq"], (255, 255, 240),
               (W // 2, 86), centro=True)
        if self.setas:
            for r, txt in zip(self.setas, ("◀", "▶")):
                painel(tela, r, (255, 252, 240))
                t = f["med"].render(txt, True, TINTA)
                tela.blit(t, t.get_rect(center=r.center))
            sombra(tela, f"{self.pagina + 1}/{self.paginas}", f["med"], (255, 255, 255),
                   (W // 2, self.setas[0].centery), centro=True)
        for i, r in self.cartoes:
            pid = self.ids[i]
            sel = i == self.sel
            seu = self._seu(pid)
            # o escolhido pula um pouco (dá vida à tela)
            pulo = int(abs(math.sin(self.t / 9)) * 8) if sel else 0
            painel(tela, r.move(0, -pulo // 2), AMARELO if sel else (255, 252, 240))
            v = loja.visual_atual(app.save, pid)
            esc = 4 if r.w < 230 else 5
            sp = _sprite("andar" if sel else "parado", (self.t // 8) % 4 if sel else self.t % 40, esc, v)
            if not seu:
                sp = sp.copy()
                sp.fill((70, 70, 90), special_flags=pygame.BLEND_RGB_MULT)
            tela.blit(sp, (r.centerx - sp.get_width() // 2, r.y + 6 - pulo))
            dados = heroi.PERSONAGENS[pid]
            nome = f["med"].render(dados["nome"], True, TINTA)
            if nome.get_width() > r.w - 12:
                nome = pygame.transform.smoothscale(nome, (r.w - 12, nome.get_height()))
            tela.blit(nome, nome.get_rect(center=(r.centerx, r.bottom - 52 - pulo // 2)))
            st, cor = ("Seu", (40, 140, 60)) if seu else (f"{dados['preco']} moedas", TINTA if
                                                      app.save.carteira["moedas"] >= dados["preco"] else VERMELHO)
            t = f["peq"].render(st, True, cor)
            tela.blit(t, t.get_rect(center=(r.centerx, r.bottom - 24 - pulo // 2)))
        dados = heroi.PERSONAGENS[self.pid]
        for k, linha in enumerate(quebrar(dados["desc"], f["med"], W - 80 if edicao.RETRATO else W - 200)[:2]):
            sombra(tela, linha, f["med"], (255, 255, 255), (W // 2, self.y_desc + k * 30), centro=True)
        art_ = dados["artigo"]
        if self._seu():
            txt, cor = f"▶ Jogar com {art_} {dados['nome']}", AMARELO
        elif app.save.carteira["moedas"] < dados["preco"]:
            txt, cor = f"Faltam {dados['preco'] - app.save.carteira['moedas']} moedas", (240, 200, 200)
        elif self.confirmar == self.pid:
            txt, cor = f"Confirmar: gastar {dados['preco']} moedas?", (255, 170, 90)
        else:
            txt, cor = f"Desbloquear por {dados['preco']} moedas", AMARELO
        _botao(tela, f, self.botoes[0], txt, self.foco == 0, cor)
        _botao(tela, f, self.botoes[1], "Loja de itens", self.foco == 1, (140, 230, 140))
        dica = ("Toque no personagem e depois no botão" if edicao.ANDROID else
                "◀ ▶ escolhe · ▲ ▼ botão/Loja · Enter confirma")
        sombra(tela, dica, f["peq"], (255, 255, 255), (W // 2, H - 22), centro=True)


class Loja(Estado):
    """Abas (esq/dir), lista (cima/baixo) e prévia do personagem com o item. OK equipa o que já é seu;
    para comprar, OK duas vezes (a segunda confirma)."""
    LINHA, VIS = 58, 8
    passo_rolagem = LINHA

    def __init__(self, app):
        super().__init__(app)
        self.aba = 0
        self.sel = 0
        self.topo = 0
        self.confirmar = None
        self.t = 0
        self._montar()

    def _montar(self):
        cat = loja.CATEGORIAS[self.aba][0]
        self.itens = [(k, d) for k, d in heroi.CATALOGO[cat].items() if not d.get("oculta")]
        eq = loja.equipado(self.app.save, cat)
        self.sel = next((i for i, (k, _) in enumerate(self.itens) if k == eq), 0)
        self.topo = max(0, self.sel - self.VIS + 1)
        self.confirmar = None

    @property
    def cat(self):
        return loja.CATEGORIAS[self.aba][0]

    def _rect_aba(self, i):
        if edicao.RETRATO:                       # em pé: duas fileiras de três abas
            larg = (W - 108 - 16) // 3
            return pygame.Rect(54 + (i % 3) * (larg + 8), 84 + (i // 3) * 38, larg, 34)
        larg = (652 - 16) // 3                   # deitado: duas fileiras de três abas, acima da lista
        return pygame.Rect(54 + (i % 3) * (larg + 8), 74 + (i // 3) * 42, larg, 38)

    def _rect_linha(self, k):
        return pygame.Rect(70, 168 + k * self.LINHA, 620, self.LINHA - 6)

    def _ativar(self):
        app, cat = self.app, self.cat
        item, dados = self.itens[self.sel]
        if loja.possui(app.save, cat, item):
            if loja.equipado(app.save, cat) != item:
                loja.equipar(app.save, cat, item)
                app.audio.tocar("ovo")
                app.toast(f"Equipado: {dados['nome']}")
            return
        if app.save.carteira["moedas"] < dados["preco"]:
            app.audio.tocar("dano")
            app.toast(f"Faltam {dados['preco'] - app.save.carteira['moedas']} moedas para {dados['nome']}")
            return
        if self.confirmar != item:
            self.confirmar = item
            app.audio.tocar("menu")
            return
        if loja.comprar(app.save, cat, item):
            loja.equipar(app.save, cat, item)
            app.audio.tocar("moeda")
            app.toast(f"Comprado e equipado: {dados['nome']}")
        self.confirmar = None

    def evento(self, e, inp):
        n = len(self.itens)
        if inp.foi("esq") or inp.foi("dir"):
            self.aba = (self.aba + (-1 if inp.foi("esq") else 1)) % len(loja.CATEGORIAS)
            self._montar()
            self.app.audio.tocar("menu")
        elif inp.foi("cima") or inp.foi("baixo"):
            self.sel = (self.sel + (-1 if inp.foi("cima") else 1)) % n
            self.confirmar = None
            self.app.audio.tocar("menu")
        elif inp.foi("ok") or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self._ativar()
        elif inp.foi("voltar"):
            self.app.pop()
        elif e.type == pygame.MOUSEWHEEL:
            self.topo = max(0, min(max(0, n - self.VIS), self.topo - e.y))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(len(loja.CATEGORIAS)):
                if self._rect_aba(i).collidepoint(e.pos):
                    self.aba = i
                    self._montar()
                    return
            for k in range(self.VIS):
                i = self.topo + k
                if i < n and self._rect_linha(k).collidepoint(e.pos):
                    if i == self.sel:
                        self._ativar()
                    else:
                        self.sel, self.confirmar = i, None
                    return
            if self.r_acao.collidepoint(e.pos):
                self._ativar()

    def update(self, inp):
        self.t += 1
        if self.sel < self.topo:
            self.topo = self.sel
        elif self.sel >= self.topo + self.VIS:
            self.topo = self.sel - self.VIS + 1

    # prévia: à direita da lista (deitado) ou embaixo dela (em pé)
    if edicao.RETRATO:
        PREVIA = pygame.Rect(54, 158 + LINHA * VIS + 34, W - 108, H - (158 + LINHA * VIS + 34) - 60)
        r_acao = pygame.Rect(W // 2 - 240, PREVIA.bottom - 76, 480, 60)
    else:
        PREVIA = pygame.Rect(730, 104, 500, 560)
        r_acao = pygame.Rect(760, 600, 440, 52)

    def _icone(self, item):
        cat = self.cat
        if cat in loja.PET_CATS:
            pet, col, cha = pets.visual(self.app.save)
            if cat == "pet":
                if item == "nenhum":
                    return None
                pet = item
            elif cat == "coleira":
                col = item
            else:
                cha = item
            return pets.icone(pet, col, cha, 3)
        if cat == "nuvem":
            nv = heroi.nuvem(("icone", item), estilo=item)
            return pygame.transform.scale(nv.subsurface((0, 26, 34, 18)), (68, 36))
        if cat == "bastao":
            b = heroi.bastao(item)
            return pygame.transform.rotate(pygame.transform.scale(b, (16, 68)), -90) if b else None
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, heroi.ROUPAS[item]["cor"], (20, 20), 16)
        pygame.draw.circle(s, TINTA, (20, 20), 16, 2)
        return s

    def draw(self, tela):
        app, f, save = self.app, self.app.f, self.app.save
        app.cenario.draw(tela)
        titulo_px(tela, "Loja", (255, 255, 255), W // 2, 22, 4)
        sombra(tela, _moedas(app), f["med"], (255, 230, 120), (W - 110, 44) if edicao.RETRATO else (W - 150, 44),
               centro=True)
        for i, (_, nome) in enumerate(loja.CATEGORIAS):
            _botao(tela, f, self._rect_aba(i), nome, i == self.aba)
        painel(tela, (54, 158, 652, self.LINHA * self.VIS + 22))
        eq = loja.equipado(save, self.cat)
        for k in range(self.VIS):
            i = self.topo + k
            if i >= len(self.itens):
                break
            item, dados = self.itens[i]
            r = self._rect_linha(k)
            if i == self.sel:
                pygame.draw.rect(tela, AMARELO, r, border_radius=12)
                pygame.draw.rect(tela, TINTA, r, 2, border_radius=12)
            ic = self._icone(item)
            if ic:
                tela.blit(ic, ic.get_rect(center=(r.x + 46, r.centery)))
            tela.blit(f["med"].render(dados["nome"], True, TINTA), (r.x + 92, r.y + 4))
            if item == eq:
                st, cor = "✔ Equipado", (40, 140, 60)
            elif loja.possui(save, self.cat, item):
                st, cor = "Seu — OK equipa", TINTA
            else:
                st = f"{dados['preco']} moedas"
                cor = TINTA if save.carteira["moedas"] >= dados["preco"] else VERMELHO
            tela.blit(f["peq"].render(st, True, cor), (r.x + 92, r.y + 30))
        # prévia
        pv = self.PREVIA
        painel(tela, pv)
        cx = pv.centerx
        item, dados = self.itens[self.sel]
        v = dict(loja.visual_atual(save))
        if self.cat not in loja.PET_CATS:
            v[self.cat] = item
        esc = 5 if edicao.RETRATO else 7
        sp = _sprite("andar", (self.t // 8) % 4, esc, v)
        pet, col, cha = pets.visual(save)                     # o pet (com o item da prévia) anda ao lado
        if self.cat == "pet":
            pet = item
        elif self.cat == "coleira":
            col = item
        elif self.cat == "chapeu":
            cha = item
        if self.cat in loja.PET_CATS and pet == "nenhum":
            pet = "gato_branco" if self.cat != "pet" else pet
        if pet != "nenhum":
            ps = pygame.transform.scale_by(pets.sprite(pet, col, cha, "andar", self.t // 6), esc - 1)
            tela.blit(sp, (cx - sp.get_width() // 2 + 40, pv.y + 8))
            tela.blit(ps, (cx - sp.get_width() // 2 - ps.get_width() + 30, pv.y + 8 + sp.get_height() - ps.get_height()))
        else:
            tela.blit(sp, (cx - sp.get_width() // 2, pv.y + 8))
        pers = heroi.PERSONAGENS[v["personagem"]]["nome"]
        t = f["grande"].render(dados["nome"], True, TINTA)
        y = pv.y + 8 + sp.get_height() + 30 if edicao.RETRATO else 438
        tela.blit(t, t.get_rect(center=(cx, y)))
        y += 28
        for linha in quebrar(dados["desc"], f["peq"], pv.w - 60)[:2]:
            tt = f["peq"].render(linha, True, TINTA)
            tela.blit(tt, tt.get_rect(center=(cx, y + 10)))
            y += 22
        nota = ("Um pet por vez: ele ataca no botão da antiga língua" if self.cat == "pet" else
                "O item vale para o pet equipado" if self.cat in loja.PET_CATS else
                f"Prévia: {pers} (troque de personagem na tela inicial)")
        tt = f["peq"].render(nota, True, CINZA)
        tela.blit(tt, tt.get_rect(center=(cx, self.r_acao.y - 18 if edicao.RETRATO else 560)))
        if item == eq:
            txt, cor = "Equipado", (200, 230, 200)
        elif loja.possui(save, self.cat, item):
            txt, cor = "Equipar", AMARELO
        elif save.carteira["moedas"] < dados["preco"]:
            txt, cor = f"Faltam {dados['preco'] - save.carteira['moedas']} moedas", (240, 200, 200)
        elif self.confirmar == item:
            txt, cor = f"Confirmar: gastar {dados['preco']} moedas?", (255, 170, 90)
        else:
            txt, cor = f"Comprar por {dados['preco']} moedas", AMARELO
        _botao(tela, f, self.r_acao, txt, True, cor)
        dica = ("Toque no item; toque de novo (ou no botão) para equipar/comprar" if edicao.ANDROID else
                "◀ ▶ abas · ▲ ▼ itens · Enter equipa/compra · Esc volta")
        sombra(tela, dica, f["peq"], (255, 255, 255), (W // 2, H - 22), centro=True)


def abrir_escolha(app, ao_jogar=None):
    app.push(EscolhaPersonagem(app, ao_jogar))


def abrir_loja(app):
    app.push(Loja(app))
