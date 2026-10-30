"""Figuras da ventilação mecânica: curvas de pressão, fluxo e
volume desenhadas a partir de um pulmão de um compartimento (Paw = PEEP + R·fluxo + V/C), para que pico, platô,
resistência, complacência e auto-PEEP nos gráficos batam com as contas da aula.

Estáticas (pílulas e questões): vm_vcv, vm_modos, vm_tela, vm_rva_cst, vm_resist_compl, vm_autopeep, vm_tabela_peep.
Paramétrica (Treino): "vm_caso:<pico>:<platô>:<peep>:<auto 0/1>" — VCV com VC de 500 mL e fluxo de 60 L/min."""
import math

import pygame

from .figuras import AZUL, BW, CINZA, CLARO, LARANJA, PAPEL, ROXO, TINTA, VERDE, VERMELHO, Eixos, Tela, _fonte, _v

AMARELO_P = (225, 165, 30)                 # pressão (amarelo do ventilador, escurecido para o papel)
VERDE_F = (40, 150, 90)                    # fluxo
AZUL_V = (60, 120, 200)                    # volume


# ------------------------------------------------------------------ simulação

def simular(modo="VCV", ciclos=2, R=10.0, C=0.05, peep=5.0, fluxo=1.0, vt=0.5, pausa=0.4, dp=15.0, ti=1.0,
            tciclo=4.0, ps=10.0, dt=0.004, inicio=0.3):
    """Lista de (t, Paw, fluxo L/s, volume L). R em cmH2O/L/s, C em L/cmH2O, volume acima da CRF na PEEP.
    VCV: fluxo quadrado até vt, pausa, expiração passiva. PCV: pressão quadrada por ti. PSV: pressão de suporte que
    cicla quando o fluxo cai a 25% do pico, com esforço do paciente (queda de pressão) no disparo."""
    out, t, v = [], 0.0, 0.0
    fim = inicio + ciclos * tciclo
    ciclou = {}                                     # PSV: ciclo k já passou para a expiração
    while t <= fim:
        tc = t - inicio
        k = math.floor(tc / tciclo) if tc >= 0 else -1
        s = tc - k * tciclo if k >= 0 else -1
        if s < 0:                                   # repouso antes do 1º ciclo
            f, paw = -v / C / R, peep
        elif modo == "VCV":
            tins = vt / fluxo
            if s < tins:
                f = fluxo
                paw = peep + R * f + (v + f * dt) / C
            elif s < tins + pausa:
                f, paw = 0.0, peep + v / C
            else:
                f, paw = -v / C / R, peep
        elif modo == "PCV":
            if s < ti:
                f = (dp - v / C) / R
                paw = peep + dp
            else:
                f, paw = -v / C / R, peep
        else:                                       # PSV
            if s < 0.12:                            # esforço do paciente: a pressão cai abaixo da PEEP e dispara
                f, paw = 0.02, peep - 2.0 * math.sin(math.pi * s / 0.12)
            else:
                pico = ps / R
                f = (ps - v / C) / R
                if not ciclou.get(k) and f > 0.25 * pico:
                    paw = peep + ps
                else:
                    ciclou[k] = True
                    f, paw = -v / C / R, peep
        out.append((t, paw, f, v))
        v = max(0.0, v + f * dt)
        t += dt
    return out


def _painel(t, r, dados, idx, yr, cor, ylab, yt, fy=None, escala=1.0, tmax=None):
    tmax = tmax or dados[-1][0]
    e = Eixos(t, r, (0, tmax), yr, "", ylab, (), yt, fy=fy or (lambda v: _v(round(v))))
    if yr[0] < 0 < yr[1]:
        t.linha((r[0], e.py(0)), (r[0] + r[2], e.py(0)), CINZA, 1)
    t.curva([e.p(d[0], min(yr[1], max(yr[0], d[idx] * escala))) for d in dados if d[0] <= tmax], cor, 3)   # corta na borda
    return e


# ------------------------------------------------------------------ figuras estáticas

def vm_vcv():
    """As três curvas em VCV com pausa inspiratória: pico, platô, PEEP; fluxo quadrado; volume. Fases 1–4 do ciclo."""
    t = Tela(560, "VCV (volume controlado, fluxo quadrado e pausa): as três curvas do ventilador")
    d = simular("VCV", ciclos=2, R=8, C=0.05, peep=5, fluxo=1.0, vt=0.5, pausa=0.4, tciclo=3.4)
    tm = d[-1][0]
    ep = _painel(t, (120, 60, 730, 140), d, 1, (0, 30), AMARELO_P, "Pressão", (0, 5, 15, 25))
    ef = _painel(t, (120, 235, 730, 130), d, 2, (-90, 75), VERDE_F, "Fluxo", (-60, 0, 60), escala=60)
    ev = _painel(t, (120, 400, 730, 110), d, 3, (0, 600), AZUL_V, "Volume", (0, 500), escala=1000)
    # rótulos: pico, platô e PEEP
    pico = max(x[1] for x in d)
    tp = next(x[0] for x in d if x[1] == pico)
    plat = 5 + 0.5 / 0.05
    ep.ponto(tp, pico, VERMELHO, f"pico {_v(round(pico))}", -12, -4, "br", guias=False)
    ep.ponto(tp + 0.3, plat, ROXO, f"platô {_v(round(plat))}", 10, -4, "bl", guias=False)
    t.txt("PEEP 5", ep.px(tm) - 6, ep.py(5) - 4, CINZA, 14, "br", True)
    t.txt("60 L/min constante", ef.px(0.8), ef.py(60) - 4, VERDE_F, 14, "bm", True)
    t.txt("expiração passiva", ef.px(1.75), ef.py(-60), VERDE_F, 14, "tl", True)
    t.txt("VC 500 mL", ev.px(0.92), ev.py(500) - 4, AZUL_V, 14, "bm", True)
    # fases do ciclo (1 inspiração, 2 ciclagem, 3 expiração, 4 disparo), no 2º ciclo
    for x, y, n in [(3.7, 9, "4"), (3.95, 19, "1"), (4.6, 25, "2"), (5.3, 9, "3")]:
        p = ep.p(x, y)
        pygame.draw.circle(t.s, AMARELO_P, p, 11)
        t.txt(n, p[0], p[1], PAPEL, 14, "mm", True)
    t.txt("1 inspiração · 2 ciclagem (fim da inspiração e da pausa) · 3 expiração passiva · 4 disparo (abre a válvula inspiratória)",
          BW // 2, 530, TINTA, 14, "tm")
    return t.s


def vm_modos():
    """VCV × PCV × PSV lado a lado: o que é constante, o que varia e o que faz ciclar."""
    t = Tela(470, "Reconheça o modo pelo desenho: quem é quadrado?")
    cols = [("VCV", dict(modo="VCV", R=8, C=0.05, fluxo=1.0, vt=0.5, pausa=0.3, tciclo=2.6),
             "Fluxo quadrado e volume fixo; a pressão sobe em rampa. Cicla pelo volume."),
            ("PCV", dict(modo="PCV", R=8, C=0.05, dp=15, ti=1.0, tciclo=2.6),
             "Pressão quadrada; o fluxo desacelera e o volume varia. Cicla pelo tempo (Ti)."),
            ("PSV", dict(modo="PSV", R=8, C=0.05, ps=10, tciclo=2.6),
             "O paciente dispara (queda antes) e o fluxo cai a 25% do pico: cicla pelo fluxo.")]
    for i, (nome, kw, leg) in enumerate(cols):
        x0 = 95 + i * 280
        d = simular(ciclos=1, peep=5, inicio=0.25, **kw)
        t.txt(nome, x0 + 105, 46, TINTA, 20, "tm", True)
        _painel(t, (x0, 82, 210, 120), d, 1, (0, 30), AMARELO_P, "Pressão" if i == 0 else "", (5, 20))
        _painel(t, (x0, 232, 210, 120), d, 2, (-80, 80), VERDE_F, "Fluxo" if i == 0 else "", (0,), escala=60)
        t.txt(leg, x0 + 105, 372, TINTA, 13, "tm", larg=230)
    return t.s


def vm_tela():
    """A tela do ventilador do slide da aula (PCV): curvas à esquerda e os números à direita, e o que cada um quer dizer."""
    t = Tela(500, "Lendo a tela do ventilador (PCV, peso predito 50 kg)")
    tela = pygame.Rect(30, 48, 840, 360)
    pygame.draw.rect(t.s, (28, 30, 34), tela, border_radius=10)
    d = simular("PCV", ciclos=2, R=9, C=0.022, peep=8, dp=14, ti=1.3, tciclo=4.0)
    for k, (idx, yr, cor, rot, esc) in enumerate([(1, (0, 30), (240, 190, 80), "PRESSÃO", 1),
                                                  (2, (-60, 60), (110, 210, 140), "FLUXO", 60),
                                                  (3, (0, 400), (110, 170, 240), "VOLUME", 1000)]):
        r = pygame.Rect(48, 66 + k * 112, 470, 96)
        t.txt(rot, r.x, r.y - 6, (190, 190, 190), 12, "tl", True)
        tm = d[-1][0]
        pts = [(r.x + x[0] / tm * r.w, r.bottom - (x[idx] * esc - yr[0]) / (yr[1] - yr[0]) * r.h) for x in d]
        if yr[0] < 0:
            y0 = r.bottom - (0 - yr[0]) / (yr[1] - yr[0]) * r.h
            pygame.draw.line(t.s, (90, 90, 90), (r.x, y0), (r.right, y0), 1)
        pygame.draw.lines(t.s, cor, False, pts, 3)
    caixas = [("Ppico", "22", (240, 190, 80)), ("PEEP", "8", (240, 190, 80)), ("Pdrive", "14", (240, 190, 80)),
              ("FR", "15", (110, 210, 140)), ("I:E", "1:2", (110, 210, 140)), ("FiO2", "40%", (220, 220, 220)),
              ("VTe", "300", (110, 170, 240)), ("VMe", "4,3 L", (110, 170, 240)), ("VT/PBW", "6,0", (110, 170, 240)),
              ("Cdyn", "21,9", (220, 220, 220))]
    for i, (nome, val, cor) in enumerate(caixas):
        r = pygame.Rect(540 + (i % 2) * 160, 62 + (i // 2) * 68, 150, 60)
        pygame.draw.rect(t.s, (45, 48, 54), r, border_radius=6)
        t.txt(nome, r.x + 8, r.y + 5, (190, 190, 190), 13, "tl")
        t.txt(val, r.right - 10, r.bottom - 5, cor, 24, "br", True)
    t.txt("VMe = VT × FR ≈ 0,3 L × 15 = 4,5 L/min · VT/PBW = 300 ÷ 50 = 6 mL/kg · Pdrive = pressão acima da PEEP "
          "(no platô) ≈ 14 · Cdyn = VT ÷ (Ppico − PEEP) ≈ 300 ÷ 14 ≈ 21 mL/cmH2O, baixa (normal 60–80)",
          BW // 2, 420, TINTA, 14, "tm", larg=BW - 60)
    return t.s


def vm_rva_cst():
    """O exemplo da aula: VC 500 mL, fluxo 60 L/min (1 L/s), pico 40, platô 30, PEEP 5 → Rva 10 e Cst 20."""
    t = Tela(470, "Pausa inspiratória: pico, platô e as duas contas da aula (VCV, fluxo quadrado)")
    d = simular("VCV", ciclos=1, R=10, C=0.02, peep=5, fluxo=1.0, vt=0.5, pausa=0.6, tciclo=3.2, inicio=0.3)
    e = _painel(t, (120, 60, 470, 300), d, 1, (0, 45), AMARELO_P, "Pressão (cmH2O)", (0, 5, 30, 40))
    pico = max(x[1] for x in d)
    tp = next(x[0] for x in d if x[1] == pico)
    e.ponto(tp, pico, VERMELHO, "pico 40", -12, -6, "br")
    e.ponto(tp + 0.4, 30, ROXO, "platô 30", 12, -6, "bl")
    t.txt("PEEP 5", e.px(2.4), e.py(5) - 4, CINZA, 14, "bm", True)
    t.seta(e.p(tp - 0.05, 30.5), e.p(tp - 0.05, 39.5), VERMELHO, 2, 8, dupla=True)
    t.txt("vence a resistência", e.px(tp - 0.1), e.py(35), VERMELHO, 13, "mr")
    t.seta(e.p(tp + 0.8, 5.5), e.p(tp + 0.8, 29.5), ROXO, 2, 8, dupla=True)
    t.txt("distende o pulmão", e.px(tp + 0.85), e.py(17), ROXO, 13, "ml")
    t.caixa((615, 70, 265, 120), "Rva = (pico − platô) ÷ fluxo\n(40 − 30) ÷ 1 L/s = 10\nnormal 4 a 8 cmH2O/L/s",
            (255, 236, 236), VERMELHO, tam=15)
    t.caixa((615, 205, 265, 120), "Cst = VC ÷ (platô − PEEP)\n500 ÷ (30 − 5) = 20\nnormal 60 a 80 mL/cmH2O",
            (240, 232, 252), ROXO, tam=15)
    t.txt("Fluxo em L/s: 60 L/min = 1 L/s. Sem pausa não há platô, e sem platô não há complacência estática.",
          BW // 2, 420, TINTA, 14, "tm", larg=BW - 60)
    return t.s


def vm_resist_compl():
    """Normal × resistência alta × complacência baixa: o que acontece com o pico e com o platô."""
    t = Tela(430, "O pico subiu: é a via aérea ou o pulmão? Olhe o platô")
    casos = [("Normal", 7, 0.05, "pico 22 · platô 15\ndiferença 7"),
             ("Resistência alta", 20, 0.05, "pico 35 · platô 15\nsó o pico sobe\nbroncoespasmo, secreção,\ntubo dobrado ou mordido"),
             ("Complacência baixa", 7, 0.02, "pico 37 · platô 30\nos dois sobem juntos\nSDRA, edema, pneumotórax,\ndistensão abdominal")]
    for i, (nome, R, C, leg) in enumerate(casos):
        x0 = 95 + i * 280
        d = simular("VCV", ciclos=1, R=R, C=C, peep=5, fluxo=1.0, vt=0.5, pausa=0.5, tciclo=2.4, inicio=0.2)
        t.txt(nome, x0 + 105, 46, (VERDE, VERMELHO, ROXO)[i], 18, "tm", True)
        e = _painel(t, (x0, 80, 210, 170), d, 1, (0, 42), AMARELO_P, "Pressão" if i == 0 else "", (5, 15, 30))
        pico = max(x[1] for x in d)
        plat = 5 + 0.5 / C
        t.tracejada((x0, e.py(pico)), (x0 + 210, e.py(pico)), VERMELHO)
        t.tracejada((x0, e.py(plat)), (x0 + 210, e.py(plat)), ROXO)
        t.txt(leg, x0 + 105, 270, TINTA, 14, "tm", larg=250)
    return t.s


def vm_autopeep():
    """Auto-PEEP: o fluxo expiratório não volta a zero antes do próximo ciclo; a pausa expiratória mede."""
    t = Tela(480, "Auto-PEEP: o ar não termina de sair antes do próximo ciclo")
    d = simular("VCV", ciclos=3, R=22, C=0.06, peep=5, fluxo=1.0, vt=0.5, pausa=0.2, tciclo=1.7, inicio=0.2)
    tm = d[-1][0]
    e1 = _painel(t, (120, 60, 730, 150), d, 1, (0, 45), AMARELO_P, "Pressão", (0, 5, 20, 40))
    e2 = _painel(t, (120, 250, 730, 150), d, 2, (-80, 75), VERDE_F, "Fluxo", (-60, 0, 60), escala=60)
    for k in (1, 2):                                    # o fluxo ainda negativo quando o próximo ciclo começa
        x = 0.2 + k * 1.7 - 0.01
        f = next(v[2] for v in d if v[0] >= x) * 60
        pygame.draw.circle(t.s, VERMELHO, e2.p(x, f), 8, 3)
    t.txt("o fluxo não chega a zero", e2.px(3.6) + 14, e2.py(-25), VERMELHO, 14, "ml", True)
    t.txt("PEEP programada 5", e1.px(tm) - 6, e1.py(5) - 4, CINZA, 14, "br", True)
    t.txt("Pausa expiratória: a pressão medida no fim da expiração menos a PEEP programada = auto-PEEP. Corrige-se "
          "dando mais tempo para expirar: menos FR, menos Ti (fluxo maior), I:E de 1:3 ou mais, broncodilatador.",
          BW // 2, 420, TINTA, 14, "tm", larg=BW - 60)
    return t.s


_TAB_FIO2 = [30, 30, 40, 40, 50, 50, 60, 60, 70, 70, 80, 80, 90, 90, 100, 100]
_TAB_PEEP = ["6", "7", "7", "8", "8", "9", "9", "10", "10", "11", "11", "12", "12", "13", "14", "14–24"]


def vm_tabela_peep():
    """Tabela PEEP × FiO2 do slide da aula: começa em FiO2 60% e PEEP 10; anda à esquerda se a saturação está acima do
    alvo e à direita se está abaixo."""
    t = Tela(330, "Tabela PEEP × FiO2 da aula (SDRA): ande pela tabela conforme a saturação")
    x0, w = 30, 48
    for i, (fi, pe) in enumerate(zip(_TAB_FIO2, _TAB_PEEP)):
        cor = (110, 190, 110) if i < 4 else (240, 225, 100) if i < 11 else (235, 110, 80)
        r1 = pygame.Rect(x0 + i * w, 120, w - 3, 44)
        r2 = pygame.Rect(x0 + i * w, 170, w - 3, 44)
        for r, s in ((r1, f"{fi}%"), (r2, pe)):
            pygame.draw.rect(t.s, cor, r, border_radius=4)
            t.txt(s, r.centerx, r.centery, TINTA, 14 if len(s) < 4 else 12, "mm", True)
        if i == 7:
            pygame.draw.rect(t.s, AZUL, (r1.x - 3, r1.y - 3, r1.w + 6, 100), 3, border_radius=4)
            t.txt("ajuste inicial", r1.centerx, 222, AZUL, 13, "tm", True)
    t.txt("FiO2", x0 + 16 * w + 6, 142, TINTA, 15, "ml", True)
    t.txt("PEEP", x0 + 16 * w + 6, 192, TINTA, 15, "ml", True)
    t.caixa((30, 50, 640, 50), "◄ saturação ACIMA do alvo: anda para a esquerda (menos FiO2 e PEEP)", (225, 236, 255), AZUL,
            tam=14)
    t.caixa((240, 250, 640, 50), "saturação ABAIXO do alvo: anda para a direita (mais FiO2 e PEEP) ►", (225, 236, 255),
            AZUL, tam=14)
    t.txt("Alvo de SatO2: 90% a 95% até FiO2 80%; 90% a 93% na zona vermelha.", 30, 262, TINTA, 13, "tl", larg=200)
    return t.s


# ------------------------------------------------------------------ paramétrica (Treino)

def vm_caso(pico, plato, peep, auto):
    """VCV com VC 500 mL e fluxo 1 L/s ajustada para dar o pico, o platô e a PEEP pedidos; auto = 1 encurta a expiração
    para o fluxo não zerar. Os números ficam escritos no gráfico."""
    pico, plato, peep, auto = float(pico), float(plato), float(peep), auto == "1"
    R, C = pico - plato, 0.5 / (plato - peep)
    tc = max(1.5, 3 * R * C + 0.9) if not auto else 0.55 + 0.2 + 1.3 * R * C
    d = simular("VCV", ciclos=2, R=R, C=C, peep=peep, fluxo=1.0, vt=0.5, pausa=0.2, tciclo=tc, inicio=0.2)
    t = Tela(430, "VCV: VC 500 mL, fluxo 60 L/min (1 L/s), pausa inspiratória de 0,2 s")
    topo = max(45, pico + 8)
    e1 = _painel(t, (120, 55, 730, 170), d, 1, (0, topo), AMARELO_P, "Pressão", (0, round(peep), round(plato), round(pico)))
    e2 = _painel(t, (120, 262, 730, 120), d, 2, (-110, 75), VERDE_F, "Fluxo", (-60, 0, 60), escala=60)
    p1 = max(x[1] for x in d if x[0] < 0.2 + tc)
    tp = next(x[0] for x in d if x[1] == p1)
    e1.ponto(tp, p1, VERMELHO, f"pico {_v(round(p1))}", -12, -6, "br", guias=False)
    e1.ponto(tp + 0.12, plato, ROXO, f"platô {_v(round(plato))}", 12, -6, "bl", guias=False)
    t.txt(f"PEEP {_v(round(peep))}", e1.px(d[-1][0]) - 6, e1.py(peep) - 4, CINZA, 14, "br", True)
    return t.s                                      # sem marcar a auto-PEEP: o Treino pede para o aluno achar


FIGURAS_VM = {"vm_vcv": vm_vcv, "vm_modos": vm_modos, "vm_tela": vm_tela, "vm_rva_cst": vm_rva_cst,
              "vm_resist_compl": vm_resist_compl, "vm_autopeep": vm_autopeep, "vm_tabela_peep": vm_tabela_peep}
PARAMETRICAS = {"vm_caso": vm_caso}
