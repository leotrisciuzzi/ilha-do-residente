"""Peças do Mirante (plugins). Cada módulo deste pacote define uma classe `Extra(Base)`; o Mirante carrega todas.

Coordenadas: o mundo é desenhado numa superfície de baixa resolução LW×LH (320×180 deitado), depois escalada ESC×
para a tela. O mundo tem largura WW (a câmera `cam` desliza de 0 a WW−LW). O céu (altura HZ) desliza com paralaxe
`ox = cam * PAR_CEU` e tem largura SW. GY = topo da margem, PE = onde a Lume pisa.

Ganchos (todos opcionais; um erro desliga só a peça que errou):
    lugares                      [(nome, x_mundo, "rótulo da dica")] — a Lume chega perto e aperta ↑ / toca
    interagir(nome)              chamado ao usar um dos seus lugares
    update()                     1× por quadro
    draw_ceu(ceu, ox)            no céu (antes dos montes), coordenadas do céu
    draw_lago(m, cam)            depois do lago (reflexo), antes da margem
    draw_margem(m, cam)          depois da margem e do observatório, antes da Lume
    draw_frente(m, cam)          por cima de tudo no mundo (frente da Lume)
    draw_tela(tela)              na tela em alta resolução (W×H), depois do mundo
    modal: chame self.mirante.abrir_modal(self) para tomar a tela; então evento_modal(e, inp) recebe a entrada
           (devolva False para fechar) e draw_modal(tela) desenha por cima.
Utilidades do Mirante: self.mirante.app (save em .app.save.d, banco em .app.banco — pode ser None),
self.mirante._falar([páginas]), self.mirante.app.audio.tocar(nome), self.mirante.t (quadros), self.mirante.x (Lume)."""
import importlib
import pkgutil
import sys
import traceback


class Base:
    nome = "?"
    lugares = ()

    def __init__(self, mirante):
        self.mirante = mirante

    def interagir(self, nome):
        pass

    def update(self):
        pass

    def draw_ceu(self, ceu, ox):
        pass

    def draw_lago(self, m, cam):
        pass

    def draw_margem(self, m, cam):
        pass

    def draw_frente(self, m, cam):
        pass

    def draw_tela(self, tela):
        pass

    def evento_modal(self, e, inp):
        return False

    def draw_modal(self, tela):
        pass


def carregar(mirante):
    out = []
    for mod in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        try:
            m = importlib.import_module(f"{__name__}.{mod.name}")
            if hasattr(m, "Extra"):
                ex = m.Extra(mirante)
                ex.nome = mod.name
                out.append(ex)
        except Exception:
            print(f"[mirante] peça {mod.name} desligada:\n{traceback.format_exc()}", file=sys.stderr)
    return out
