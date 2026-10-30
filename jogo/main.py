"""Ponto de entrada da edição WEB (navegador, via pygbag/WebAssembly) da Ilha do Residente.

É a edição Android rodando no navegador: mesmos menus de pacotes e mesmos gestos (no celular) ou
teclado/controle (no PC). Diferenças do navegador, resolvidas aqui antes de importar o jogo:
- o laço precisa devolver o controle ao navegador a cada quadro (asyncio.sleep(0));
- não há threads: Thread.start() roda a tarefa na hora (as que existem são curtas ou de rede);
- não há internet pelo urllib: o atualizador de conteúdo fica desligado (os pacotes vêm no jogo);
- o disco é de memória: a pasta de dados é espelhada no localStorage do navegador."""
import asyncio
import base64
import os
import sys
import threading

import pygame  # noqa: F401  (o pygbag só embarca o pygame se o main.py o importar)

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
NAVEGADOR = sys.platform == "emscripten"
DADOS = "/data/ilha-do-residente" if NAVEGADOR else os.path.expanduser("~/.local/share/ilha-do-residente-web")
CHAVE = "ilha:"                         # prefixo das chaves no localStorage


def _janela():
    if NAVEGADOR:
        import platform
        return platform.window
    return None


def _restaurar(win):
    """localStorage → pasta de dados (ao abrir)."""
    if win is None:
        return
    try:
        ls = win.localStorage
        for i in range(int(ls.length)):
            k = str(ls.key(i))
            if not k.startswith(CHAVE):
                continue
            arq = os.path.join(DADOS, k[len(CHAVE):])
            os.makedirs(os.path.dirname(arq), exist_ok=True)
            with open(arq, "wb") as f:
                f.write(base64.b64decode(str(ls.getItem(k))))
    except Exception as ex:
        print("restaurar save:", ex)


_vistos = {}


def _espelhar(win):
    """pasta de dados → localStorage (só os arquivos pequenos que mudaram)."""
    if win is None:
        return
    for raiz, _, nomes in os.walk(DADOS):
        for n in nomes:
            if n.endswith(".tmp"):
                continue
            arq = os.path.join(raiz, n)
            try:
                st = os.stat(arq)
                if st.st_size > 512 * 1024 or _vistos.get(arq) == (st.st_mtime, st.st_size):
                    continue
                with open(arq, "rb") as f:
                    win.localStorage.setItem(CHAVE + os.path.relpath(arq, DADOS), base64.b64encode(f.read()).decode())
                _vistos[arq] = (st.st_mtime, st.st_size)
            except Exception as ex:
                print("espelhar save:", ex)


def _preparar(win):
    os.environ["ILHA_SEM_SINCRONIA"] = "1"
    os.environ["ILHA_WEB"] = "1"
    if win is not None:
        try:
            w, h = int(win.innerWidth), int(win.innerHeight)
            os.environ["ILHA_TELA"] = f"{w}x{h}"
            if w > h:
                os.environ["ILHA_PAISAGEM"] = "1"          # PC/tablet deitado: tela larga
            if int(win.navigator.maxTouchPoints or 0) > 0:
                os.environ["ILHA_TOQUE"] = "1"             # celular/tablet: gestos do Super Mario Run
        except Exception as ex:
            print("tela:", ex)
    if NAVEGADOR:
        def _start(self):                                 # sem threads no WebAssembly: roda agora
            try:
                self.run()
            except Exception as ex:
                print("tarefa:", ex)
        threading.Thread.start = _start


async def main():
    win = _janela()
    os.makedirs(DADOS, exist_ok=True)
    _restaurar(win)
    _preparar(win)
    from ilha import edicao
    edicao.ativar_android(DADOS)
    edicao.WEB = True
    from ilha import atualizador

    class SemAtualizar(atualizador.Atualizador):
        def iniciar(self, versoes_atuais=None):
            self.estado = ""
    atualizador.Atualizador = SemAtualizar
    from ilha import android
    android.Atualizador = SemAtualizar
    from ilha.ui import App
    from ilha.android import menu_android
    from ilha.personagens import abrir_escolha
    app = App()
    app.push(menu_android(app))
    abrir_escolha(app)
    n = 0
    while app.rodando and app.pilha:
        app.quadro()
        n += 1
        if n % 120 == 0:
            _espelhar(win)
        await asyncio.sleep(0)
    app.save.salvar()
    _espelhar(win)


asyncio.run(main())
