"""Traçados de ECG desenhados por código: tira de DII longo (10 s) em papel milimetrado, 25 mm/s e 10 mm/mV.

Cada ritmo é montado a partir dos instantes das ondas (início da P, início do QRS, largura do QRS), então o que
se mede no papel é exatamente o que o caso diz: 1 quadradinho = 1 mm = 40 ms; 1 quadradão = 5 mm = 200 ms.
Os intervalos (PR, QRS, RR) caem em múltiplos de 40 ms para que a contagem de quadradinhos seja exata.

Ritmos: sinusal, bav1, mobitz1, mobitz2, bavt, fa, flutter, tsv, tv, torsades, fv, assistolia.
A AESP não é um desenho próprio: é qualquer ritmo organizado num paciente SEM pulso.

    spec = montar("mobitz1", rng)          # dict com os instantes e as medidas (pr, qrs, fc, regular…)
    desenhar(tela, rect, spec, px_mm)      # papel + traçado; t0/y0 deslocam a janela (zoom e arraste)"""
import math
import random

import pygame

DUR = 10000                  # ms de tira
PASSO = 4                    # ms por amostra
QD = 40                      # ms por quadradinho
PAPEL = (255, 246, 244)
GRADE_F = (248, 204, 204)
GRADE_G = (232, 150, 155)
TRACO = (25, 25, 35)

NOMES = {"sinusal": "Ritmo sinusal", "bav1": "BAV de 1º grau", "mobitz1": "BAV 2º grau Mobitz I (Wenckebach)",
         "mobitz2": "BAV 2º grau Mobitz II", "bavt": "BAV total (3º grau)", "fa": "Fibrilação atrial",
         "flutter": "Flutter atrial", "tsv": "Taquicardia supraventricular", "tv": "Taquicardia ventricular monomórfica",
         "torsades": "Torsades de pointes", "fv": "Fibrilação ventricular", "assistolia": "Assistolia"}


# ------------------------------------------------------------------ montagem do ritmo

def _bat(qrs, t, larg, tipo, rr):
    qrs.append({"t": t, "larg": larg, "tipo": tipo, "rr": rr})


def montar(ritmo, rng=None, **kw):
    """Sorteia um traçado do ritmo. kw força medidas: n_rr (quadradinhos do RR), pr_q (quadradinhos do PR),
    qrs_q (largura do QRS em quadradinhos), conducao (flutter), bloqueio (mobitz: 1 P bloqueada a cada n),
    fv ("grossa"/"fina"), escape ("juncional"/"ventricular")."""
    rng = rng or random.Random()
    s = {"ritmo": ritmo, "p": [], "qrs": [], "base": None, "seed": rng.randrange(10 ** 6), "pr": None, "qrs_ms": None,
         "regular": True, "n_rr": None}
    p, qrs = s["p"], s["qrs"]
    ini = rng.randrange(4, 16) * QD                               # a tira começa em algum ponto do ciclo
    if ritmo in ("sinusal", "bav1", "tsv"):
        n = kw.get("n_rr") or (rng.randint(7, 9) if ritmo == "tsv" else rng.randint(17, 26))
        pr_q = kw.get("pr_q") or (rng.choice([3, 4]) if ritmo == "sinusal" else rng.choice([6, 7, 8]))
        qq = kw.get("qrs_q") or 2
        rr = n * QD
        t = ini
        while t < DUR + rr:
            if ritmo != "tsv":
                p.append(t - pr_q * QD)
            _bat(qrs, t, qq * QD, "n", rr)
            t += rr
        s.update(n_rr=n, pr=None if ritmo == "tsv" else pr_q * QD, qrs_ms=qq * QD)
    elif ritmo == "tv":
        n = kw.get("n_rr") or rng.randint(8, 10)
        qq = kw.get("qrs_q") or rng.choice([4, 5])
        t = ini
        while t < DUR + n * QD:
            _bat(qrs, t, qq * QD, "v", n * QD)
            t += n * QD
        s.update(n_rr=n, qrs_ms=qq * QD)
    elif ritmo in ("mobitz1", "mobitz2"):
        pp = (kw.get("n_pp") or rng.randint(19, 23)) * QD
        bloq = kw.get("bloqueio") or rng.choice([3, 4])            # 1 P bloqueada a cada `bloq`
        if ritmo == "mobitz1":
            base = kw.get("pr_q") or rng.choice([4, 5])
            prs = [base, base + 3, base + 4, base + 5][:bloq - 1]  # alonga cada vez menos, até bloquear
        else:
            prs = [kw.get("pr_q") or rng.choice([4, 5])] * (bloq - 1)
        qq = 2 if ritmo == "mobitz1" else (kw.get("qrs_q") or rng.choice([2, 3]))
        k, t = 0, ini - pp
        while t < DUR + pp:
            p.append(t)
            i = k % bloq
            if i < bloq - 1:
                _bat(qrs, t + prs[i] * QD, qq * QD, "n", None)
            k += 1
            t += pp
        s.update(pr=prs[0] * QD, prs=[x * QD for x in prs], qrs_ms=qq * QD, regular=False, bloqueio=bloq, pp=pp)
    elif ritmo == "bavt":
        pp = (kw.get("n_pp") or rng.randint(18, 22)) * QD
        esc = kw.get("escape") or rng.choice(["juncional", "ventricular"])
        n = kw.get("n_rr") or (rng.randint(32, 37) if esc == "juncional" else rng.randint(38, 46))
        qq = 2 if esc == "juncional" else 4
        t = ini - rng.randrange(0, pp // QD) * QD
        while t < DUR + pp:
            p.append(t)
            t += pp
        t = ini + rng.randrange(2, 12) * QD
        while t < DUR + n * QD:
            _bat(qrs, t, qq * QD, "n" if esc == "juncional" else "v", n * QD)
            t += n * QD
        s.update(n_rr=n, qrs_ms=qq * QD, escape=esc, pp=pp)
    elif ritmo == "fa":
        lo, hi = kw.get("faixa", (9, 16))
        t = ini
        while t < DUR + 1000:
            n = rng.randint(lo, hi)
            _bat(qrs, t, 2 * QD, "n", n * QD)
            t += n * QD
        s.update(qrs_ms=2 * QD, regular=False, base=("fa",))
    elif ritmo == "flutter":
        cond = kw.get("conducao") or 2
        fper = 5 * QD                                               # ondas F a 300/min
        n = 5 * cond
        t = ini
        while t < DUR + n * QD:
            _bat(qrs, t, 2 * QD, "n", n * QD)
            t += n * QD
        s.update(n_rr=n, qrs_ms=2 * QD, base=("flutter", ini % fper - 2 * QD, fper), conducao=cond)
    elif ritmo == "torsades":
        s.update(regular=False, base=("torsades", rng.uniform(3.6, 4.4), rng.uniform(2200, 2800), rng.uniform(0, 6)))
        _bat(qrs, ini, 2 * QD, "n", 1100)                           # 2 batimentos de QT longo antes do disparo
        p.append(ini - 4 * QD)
        _bat(qrs, ini + 1100, 2 * QD, "n", 1100)
        p.append(ini + 1100 - 4 * QD)
        s["inicio_tdp"] = ini + 1100 + 560
        s["qrs_ms"] = 6 * QD
    elif ritmo == "fv":
        amp = (rng.uniform(0.45, 0.8) if kw.get("fv", "grossa") == "grossa" else rng.uniform(0.1, 0.2))
        s.update(regular=False, base=("fv", amp, [(rng.uniform(4.2, 7.0), rng.uniform(0, 6.28), rng.uniform(0.4, 1))
                                                  for _ in range(4)]))
    elif ritmo == "assistolia":
        s["base"] = ("linha",)
    else:
        raise ValueError(ritmo)
    s["fc"] = fc(s)
    return s


def fc(s):
    """FC ventricular como se mede: regular → 1500 ÷ quadradinhos do RR; irregular → QRS em 10 s × 6."""
    if s["ritmo"] in ("fv", "assistolia"):
        return 0
    if s["ritmo"] == "torsades":
        return 240
    if s["regular"] and s["n_rr"]:
        return round(1500 / s["n_rr"])
    return contar_qrs(s) * 6


def contar_qrs(s):
    return sum(1 for b in s["qrs"] if 0 <= b["t"] < DUR)


# ------------------------------------------------------------------ o sinal (mV ao longo do tempo)

def _g(t, c, sd, a):
    x = (t - c) / sd
    return a * math.exp(-0.5 * x * x) if -5 < x < 5 else 0.0


def _onda_qrs(t, b):
    q0, d = b["t"], b["larg"]
    if t < q0 - 60 or t > q0 + d + 700:
        return 0.0
    rr = b["rr"] or 800
    if b["tipo"] == "v":
        v = _g(t, q0 + 0.35 * d, 0.16 * d, 1.25) + _g(t, q0 + 0.78 * d, 0.13 * d, -0.55)
        v += _g(t, q0 + d + 150, 65, -0.42)
        return v
    v = _g(t, q0 + 0.12 * d, 0.07 * d, -0.1) + _g(t, q0 + 0.45 * d, 0.1 * d, 1.15) + _g(t, q0 + 0.8 * d, 0.08 * d, -0.28)
    qt = min(460, max(260, 400 * math.sqrt(rr / 1000)))
    if b["rr"] == 1100:                                          # QT longo que precede a torsades
        qt = 560
    return v + _g(t, q0 + qt - 85, 42, 0.3)


def amostras(s):
    if "_am" in s:
        return s["_am"]
    r = random.Random(s["seed"])
    ruido = [r.uniform(-0.012, 0.012) for _ in range(DUR // PASSO + 1)]
    fw = r.uniform(0, 6.28)
    base = s["base"]
    out = []
    for k in range(DUR // PASSO + 1):
        t = k * PASSO
        v = 0.03 * math.sin(2 * math.pi * 0.22 * t / 1000 + fw) + ruido[k]
        if base:
            if base[0] == "fa":
                v += 0.045 * (math.sin(2 * math.pi * 5.3 * t / 1000 + fw) + 0.7 * math.sin(2 * math.pi * 7.1 * t / 1000 + 2 * fw)
                              + 0.5 * math.sin(2 * math.pi * 6.2 * t / 1000 + 1.3))
            elif base[0] == "flutter":
                fase = ((t - base[1]) % base[2]) / base[2]
                v += -0.3 * (fase / 0.78) if fase < 0.78 else -0.3 * (1 - (fase - 0.78) / 0.22)
                v += 0.15
            elif base[0] == "torsades" and t >= s["inicio_tdp"]:
                tt = t - s["inicio_tdp"]
                env = math.sin(math.pi * tt / base[2] + 0.35) * 0.8
                sobe = min(1.0, tt / 250)
                v += sobe * env * math.sin(2 * math.pi * base[1] * tt / 1000 + base[3]) + 0.12 * math.sin(2 * math.pi * base[1] * 2 * tt / 1000)
            elif base[0] == "fv":
                amp, comps = base[1], base[2]
                mod = 0.65 + 0.35 * math.sin(2 * math.pi * 0.45 * t / 1000 + fw)
                v += amp * mod * sum(a * math.sin(2 * math.pi * f * t / 1000 + ph) for f, ph, a in comps) / 1.6
            elif base[0] == "linha":
                v *= 0.6
        for p0 in s["p"]:
            if p0 - 20 < t < p0 + 120:
                v += _g(t, p0 + 50, 19, 0.15)
        for b in s["qrs"]:
            v += _onda_qrs(t, b)
        out.append(v)
    s["_am"] = out
    return out


# ------------------------------------------------------------------ desenho

def desenhar(tela, rect, s, px_mm, t0=0.0, y0=0.0, grade=True, rotulo="DII"):
    """Papel milimetrado + traçado. t0 = ms no canto esquerdo; y0 = mV deslocados (arraste vertical).
    A linha de base fica a 62% da altura (o QRS sobe mais do que desce)."""
    clip = tela.get_clip()
    tela.set_clip(rect)
    pygame.draw.rect(tela, PAPEL, rect)
    base_y = rect.y + rect.h * 0.62 + y0 * 10 * px_mm
    if grade:
        mm0 = int(t0 / QD)
        off = (mm0 - t0 / QD) * px_mm
        fina = px_mm >= 2.6
        n = int(rect.w / px_mm) + 2
        for i in range(n):
            x = rect.x + off + i * px_mm
            g = (mm0 + i) % 5 == 0
            if g or fina:
                pygame.draw.line(tela, GRADE_G if g else GRADE_F, (x, rect.y), (x, rect.bottom), 2 if g and px_mm >= 6 else 1)
        k0 = math.floor((rect.y - base_y) / px_mm)
        k1 = math.ceil((rect.bottom - base_y) / px_mm)
        for k in range(k0, k1 + 1):
            y = base_y + k * px_mm
            g = k % 5 == 0
            if g or fina:
                pygame.draw.line(tela, GRADE_G if g else GRADE_F, (rect.x, y), (rect.right, y), 2 if g and px_mm >= 6 else 1)
    am = amostras(s)
    esc_x = px_mm / QD
    i0 = max(0, int(t0 / PASSO) - 1)
    i1 = min(len(am) - 1, int((t0 + rect.w / esc_x) / PASSO) + 2)
    pts = [(rect.x + (k * PASSO - t0) * esc_x, base_y - am[k] * 10 * px_mm) for k in range(i0, i1 + 1)]
    if len(pts) > 1:
        pygame.draw.lines(tela, TRACO, False, pts, 2 if px_mm < 7 else 3)
    if rotulo:
        f = _fonte(max(14, int(px_mm * 3.2)))
        t = f.render(rotulo, True, (150, 60, 70))
        tela.blit(t, (rect.x + 6, rect.y + 4))
    tela.set_clip(clip)


_FONTES = {}


def _fonte(tam):
    tam = min(tam, 30)
    if tam not in _FONTES:
        from .ui import fonte
        _FONTES[tam] = fonte(tam, bold=True)
    return _FONTES[tam]
