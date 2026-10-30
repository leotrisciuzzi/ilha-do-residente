"""Modo Treino da ventilação mecânica: casos gerados na hora, infinitos.

Mesmo princípio da gasometria: as cifras são sorteadas e o gabarito sai da CONTA feita
pelas fórmulas das aulas (peso predito, complacência, resistência, driving pressure,
FR × PaCO₂, FiO₂ × PaO₂, P/F, Ti e I:E, IRRS e o protocolo ARDSNet). O comentário mostra
a conta passo a passo com as cifras do enunciado.
"""
import math
import random

MATERIA = "Ventilação mecânica"
PREFIXO = "vm-treino"

HABILIDADES = {
    "peso": ("Peso predito e VT", "Altura e sexo → peso predito → VT de 6 mL/kg"),
    "complacencia": ("Complacência estática", "Cst = VT / (Pplat − PEEP)"),
    "resistencia": ("Resistência", "R = (Ppico − Pplat) / fluxo em L/s"),
    "pico": ("Pico × platô", "Subiu o pico: resistência, complacência ou vazamento?"),
    "protetora": ("Ventilação protetora?", "VT ≤ 8 mL/kg predito, platô ≤ 30, driving ≤ 15"),
    "co2": ("FR para a PaCO₂ alvo", "FR nova = FR × PaCO₂ atual / PaCO₂ alvo"),
    "fio2": ("FiO₂ para a PaO₂ alvo", "FiO₂ nova ≈ FiO₂ × PaO₂ alvo / PaO₂ atual"),
    "pf": ("P/F e Berlim", "PaO₂/FiO₂ e gravidade da SDRA"),
    "ie": ("Tempo inspiratório e I:E", "Ti = VT / fluxo; ciclo = 60 / FR"),
    "irrs": ("Índice de Tobin (IRRS)", "FR / VT em litros: < 105 prediz sucesso"),
    "ardsnet": ("Protocolo ARDSNet: próximo passo", "VT, platô e pH → o que mudar"),
}


def fmt(x, casas=0):
    return f"{x:.{casas}f}".replace(".", ",")


def peso_predito(sexo, alt):
    return (50 if sexo == "M" else 45.5) + 0.91 * (alt - 152.4)


def ph_de(P, H):
    return 6.1 + math.log10(H / (0.03 * P))


# ---------------------------------------------------------------- montagem

def _montar(rng, habil, enunciado, certa, erradas, coment):
    erradas = [e for e in dict.fromkeys(erradas) if e != certa][:4]
    alts = [certa] + erradas
    rng.shuffle(alts)
    return {"id": f"{PREFIXO}:{habil}", "enunciado": enunciado, "alts": list(zip("ABCDE", alts)),
            "gab": "ABCDE"[alts.index(certa)], "coment": coment, "materia": MATERIA, "subtema": "",
            "assunto": "", "imgs": [], "prev": 0.5, "origem": "caso gerado", "treino": True}


def _num_alts(rng, certo, passo, fmtf, minimo=None):
    vistos = {fmtf(certo)}
    cand = [certo + k * passo for k in (-3, -2, -1, 1, 2, 3)]
    rng.shuffle(cand)
    out = []
    for v in cand:
        if (minimo is not None and v < minimo) or fmtf(v) in vistos:
            continue
        vistos.add(fmtf(v))
        out.append(fmtf(v))
        if len(out) == 4:
            break
    return fmtf(certo), out


def _paciente(rng):
    sexo = rng.choice("MF")
    alt = rng.randint(152, 192) if sexo == "M" else rng.randint(148, 178)
    pp = peso_predito(sexo, alt)
    real = round(pp * rng.uniform(1.0, 1.9))
    return sexo, alt, pp, real


def _quem(sexo, alt, real):
    return f"{'Homem' if sexo == 'M' else 'Mulher'} de {fmt(alt / 100, 2)} m e {real} kg"


_CAUSAS = ["pneumonia grave", "choque séptico de foco abdominal", "pancreatite aguda grave", "politrauma",
           "broncoaspiração", "rebaixamento após AVC", "pós-operatório de laparotomia"]


# ---------------------------------------------------------------- habilidades

def _q_peso(rng):
    sexo, alt, pp, real = _paciente(rng)
    vt = 6 * pp
    certa = f"Peso predito ≈ {fmt(pp)} kg → VT ≈ {fmt(round(vt, -1))} mL"
    outro = peso_predito("F" if sexo == "M" else "M", alt)
    erradas = [f"Peso predito ≈ {fmt(real)} kg → VT ≈ {fmt(round(6 * real, -1))} mL",
               f"Peso predito ≈ {fmt(outro)} kg → VT ≈ {fmt(round(6 * outro, -1))} mL",
               f"Peso predito ≈ {fmt(pp)} kg → VT ≈ {fmt(round(10 * pp, -1))} mL",
               f"Peso predito ≈ {fmt(pp)} kg → VT ≈ {fmt(round(4 * pp, -1))} mL"
               if abs(real - pp) < 4 else f"Peso predito ≈ {fmt(real)} kg → VT ≈ {fmt(round(8 * real, -1))} mL"]
    base = "50" if sexo == "M" else "45,5"
    coment = (f"Peso predito ({'homem' if sexo == 'M' else 'mulher'}) = {base} + 0,91 × ({alt} − 152,4) = "
              f"{base} + {fmt(0.91 * (alt - 152.4), 1)} = {fmt(pp, 1)} kg. VT = 6 × {fmt(pp, 1)} = {fmt(vt)} mL. "
              f"O peso real ({real} kg) não entra: o pulmão acompanha a altura e o sexo.")
    enun = f"{_quem(sexo, alt, real)}, intubado por {rng.choice(_CAUSAS)}. Qual o volume corrente inicial de 6 mL/kg?"
    return _montar(rng, "peso", enun, certa, erradas, coment)


def _q_complacencia(rng):
    peep = rng.choice([5, 6, 8, 10, 12, 14])
    vt = rng.randrange(320, 560, 10)
    cst = rng.choice([rng.uniform(15, 30), rng.uniform(30, 45), rng.uniform(50, 75)])
    dp = round(vt / cst)
    pplat = peep + dp
    ppico = pplat + rng.randint(3, 9)
    cst = vt / dp
    f = lambda x: fmt(x) + " mL/cmH₂O"
    certa = f(cst)
    erradas = [f(vt / pplat), f(vt / (ppico - peep)), f(vt / ppico), f(cst * 1.6), f(vt / (pplat + peep))]
    leitura = ("muito baixa — pulmão 'duro' (SDRA, edema, fibrose)" if cst < 30 else
               "baixa" if cst < 50 else "dentro do esperado no paciente ventilado (~50–80)")
    coment = (f"Cst = VT / (Pplat − PEEP) = {vt} / ({pplat} − {peep}) = {vt} / {dp} = {fmt(cst, 1)} mL/cmH₂O: {leitura}. "
              f"Usar o pico ({vt}/({ppico} − {peep}) = {fmt(vt / (ppico - peep), 1)}) dá a complacência DINÂMICA, que inclui a resistência.")
    enun = f"VCV: VT {vt} mL, Ppico {ppico}, Pplat {pplat}, PEEP {peep} cmH₂O. A complacência ESTÁTICA é:"
    return _montar(rng, "complacencia", enun, certa, erradas, coment)


def _q_resistencia(rng):
    fluxo = rng.choice([30, 40, 45, 50, 60, 72, 90])
    r = rng.choice([rng.randint(5, 10), rng.randint(12, 18), rng.randint(20, 30)])
    pplat = rng.randint(16, 28)
    ppico = round(pplat + r * fluxo / 60)
    r = (ppico - pplat) / (fluxo / 60)
    f = lambda x: fmt(x, 0 if abs(x - round(x)) < 0.05 else 1) + " cmH₂O/L/s"
    certa = f(r)
    erradas = [f((ppico - pplat) / fluxo), f((ppico - pplat) * fluxo / 60), f(ppico / (fluxo / 60)),
               f(r + 10), f(max(r - 7, 1.5))]
    leitura = "normal para o intubado" if r <= 15 else "ALTA: secreção, broncoespasmo, tubo dobrado ou fino"
    coment = (f"Fluxo {fluxo} L/min = {fmt(fluxo / 60, 2)} L/s. R = (Ppico − Pplat) / fluxo = ({ppico} − {pplat}) / {fmt(fluxo / 60, 2)} "
              f"= {fmt(r, 1)} cmH₂O/L/s: {leitura}. Esquecer de converter o fluxo para L/s é o erro clássico.")
    enun = f"VCV com fluxo quadrado de {fluxo} L/min: Ppico {ppico} e Pplat {pplat} cmH₂O. A resistência do sistema é:"
    return _montar(rng, "resistencia", enun, certa, erradas, coment)


_PICO = {
    "res": ("Aumento de resistência (secreção, broncoespasmo, tubo dobrado ou mordido)",
            "Só o componente resistivo (pico − platô) cresceu: o caminho do ar estreitou. Aspirar, checar o tubo, broncodilatador."),
    "comp": ("Queda de complacência (pneumotórax, intubação seletiva, atelectasia, edema)",
             "Pico e platô subiram juntos: o pulmão (ou a parede) ficou mais duro. Ausculta, radiografia, pensar em pneumotórax se houver hipotensão."),
    "vaz": ("Vazamento ou desconexão (cuff, circuito, extubação)",
            "Pressões em queda com volume expirado menor que o inspirado: o ar está escapando."),
    "auto": ("Hiperinsuflação dinâmica (auto-PEEP)",
             "Platô e PEEP total subiram com fluxo expiratório que não zera: ar preso. Menos FR, mais tempo expiratório."),
}


def _q_pico(rng):
    tipo = rng.choice(list(_PICO))
    peep = rng.choice([5, 6, 8, 10])
    p0 = rng.randint(peep + 10, peep + 16)
    pk0 = p0 + rng.randint(4, 7)
    vt = rng.randrange(380, 520, 10)
    if tipo == "res":
        p1, pk1 = p0 + rng.choice([-1, 0, 0, 1]), pk0 + rng.randint(12, 22)
        extra = f"volume expirado {vt - rng.randint(0, 10)} mL; PEEP total {peep}"
    elif tipo == "comp":
        d = rng.randint(9, 15)
        p1, pk1 = p0 + d, pk0 + d + rng.randint(0, 2)
        extra = f"volume expirado {vt - rng.randint(0, 10)} mL; PEEP total {peep}"
    elif tipo == "vaz":
        p1, pk1 = p0 - rng.randint(5, 9), pk0 - rng.randint(7, 11)
        extra = f"volume expirado {vt - rng.randrange(150, 260, 10)} mL; PEEP total {max(peep - 3, 0)}"
    else:
        a = rng.randint(6, 12)
        p1, pk1 = p0 + a, pk0 + a + rng.randint(0, 2)
        extra = f"volume expirado {vt - rng.randint(0, 10)} mL; PEEP total {peep + a} (pausa expiratória)"
    enun = (f"Paciente em VCV (VT {vt} mL, PEEP {peep}). Antes: Ppico {pk0}, Pplat {p0}. Agora: Ppico {pk1}, Pplat {p1}; "
            f"{extra}.\nO mecanismo mais provável é:")
    certa = _PICO[tipo][0]
    erradas = [v[0] for k, v in _PICO.items() if k != tipo] + ["Melhora da complacência pulmonar"]
    coment = (f"Componente resistivo (pico − platô): antes {pk0 - p0}, agora {pk1 - p1}. Componente elástico (platô − PEEP): "
              f"antes {p0 - peep}, agora {p1 - peep}. " + _PICO[tipo][1])
    return _montar(rng, "pico", enun, certa, erradas, coment)


_PROT = {
    "ok": "É protetora: VT ≤ 8 mL/kg predito, platô ≤ 30 e driving ≤ 15",
    "vt": "Não: VT acima de 8 mL/kg do peso predito",
    "plat": "Não: pressão de platô acima de 30 cmH₂O",
    "dp": "Não: driving pressure acima de 15 cmH₂O (platô ≤ 30)",
}


def _q_protetora(rng):
    alvo = rng.choice(list(_PROT))
    while True:
        sexo, alt, pp, real = _paciente(rng)
        vt = round((rng.uniform(8.6, 11) if alvo == "vt" else rng.uniform(5, 7.6)) * pp, -1)
        vtkg = vt / pp
        peep = rng.choice([5, 8, 10, 12, 14])
        pplat = {"plat": rng.randint(31, 36), "dp": rng.randint(peep + 16, peep + 22)}.get(alvo, rng.randint(peep + 7, peep + 15))
        viol = "vt" if vtkg > 8 else "plat" if pplat > 30 else "dp" if pplat - peep > 15 else "ok"
        if viol == alvo and (alvo != "vt" or pplat <= 30 and pplat - peep <= 15):
            break
    enun = (f"{_quem(sexo, alt, real)}, com SDRA. VCV: VT {fmt(vt)} mL, PEEP {peep}, Pplat {pplat} cmH₂O.\n"
            "A ventilação está protetora?")
    certa = _PROT[alvo]
    erradas = [v for k, v in _PROT.items() if k != alvo] + ["Não: o VT deve ser de 6 mL/kg do peso REAL"]
    base = "50" if sexo == "M" else "45,5"
    coment = (f"Peso predito = {base} + 0,91 × ({alt} − 152,4) = {fmt(pp, 1)} kg → VT = {fmt(vt)} / {fmt(pp, 1)} = "
              f"{fmt(vtkg, 1)} mL/kg. Platô {pplat} ({'≤' if pplat <= 30 else '>'} 30). Driving = {pplat} − {peep} = "
              f"{pplat - peep} ({'≤' if pplat - peep <= 15 else '>'} 15). Alvos: VT 6 (4–8) mL/kg, platô ≤ 30, driving ≤ 15.")
    return _montar(rng, "protetora", enun, certa, erradas, coment)


def _q_co2(rng):
    while True:
        fr = rng.randint(10, 22)
        pa = rng.randint(28, 70)
        alvo = rng.choice([35, 40, 40, 45])
        nova = fr * pa / alvo
        if abs(nova - fr) >= 3 and 6 <= nova <= 35:
            break
    vt = rng.randrange(350, 520, 10)
    certa, erradas = _num_alts(rng, round(nova), 3, lambda x: f"FR {int(round(x))}", minimo=6)
    erradas.append(f"FR {round(fr * alvo / pa)}")
    coment = (f"PaCO₂ ∝ 1 / ventilação alveolar. Com o VT fixo: FR nova = FR × PaCO₂ atual / PaCO₂ alvo = "
              f"{fr} × {pa} / {alvo} = {fmt(nova, 1)} ≈ {round(nova)}. "
              + ("Subir a FR encurta a expiração: vigie auto-PEEP. " if nova > fr else "Baixar a FR reduz a ventilação: confira o pH depois. ")
              + "Colha nova gasometria em 20–30 min.")
    enun = (f"Paciente em VCV com VT {vt} mL e FR {fr}: PaCO₂ {pa} mmHg. Para PaCO₂ de {alvo} mmHg mantendo o VT, "
            "a nova frequência é aproximadamente:")
    return _montar(rng, "co2", enun, certa, erradas[:5], coment)


def _q_fio2(rng):
    while True:
        fio2 = rng.choice([0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 1.0])
        pao2 = rng.randint(50, 220)
        alvo = rng.choice([70, 80, 90])
        nova = fio2 * alvo / pao2
        if 0.21 <= nova <= 1.0 and abs(nova - fio2) >= 0.08:
            break
    f = lambda x: f"FiO₂ ≈ {int(round(x * 100))}%"
    certa, erradas = _num_alts(rng, nova, 0.08, f, minimo=0.21)
    erradas = [e for e in erradas if int(e.split("≈ ")[1][:-1]) <= 100]
    erradas += [f(min(fio2 * pao2 / alvo, 1.0)), f(min(nova + 0.2, 1.0)), f(max(nova - 0.15, 0.21))]
    coment = (f"Supondo P/F constante: FiO₂ nova = FiO₂ atual × PaO₂ desejada / PaO₂ atual = {fmt(fio2, 2)} × {alvo} / {pao2} = "
              f"{fmt(nova, 2)} (~{int(round(nova * 100))}%). P/F atual = {fmt(pao2 / fio2)}. É uma estimativa: com shunt grande a "
              "relação não é linear — confirme pela SpO₂" + (". Se a FiO₂ precisa ficar ≥ 60%, priorize PEEP e recrutamento."
                                                          if nova >= 0.6 else "."))
    enun = f"Paciente ventilado em FiO₂ {int(fio2 * 100)}% com PaO₂ {pao2} mmHg. Para PaO₂ de ~{alvo} mmHg, a FiO₂ estimada é:"
    return _montar(rng, "fio2", enun, certa, erradas, coment)


def _q_pf(rng):
    fio2 = rng.choice([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0])
    pf = rng.choice([rng.uniform(55, 98), rng.uniform(104, 196), rng.uniform(204, 296), rng.uniform(305, 420)])
    pao2 = round(pf * fio2)
    pf = pao2 / fio2
    peep = rng.choice([5, 8, 10, 12, 14])
    if pf <= 100:
        cls = "SDRA grave"
    elif pf <= 200:
        cls = "SDRA moderada"
    elif pf <= 300:
        cls = "SDRA leve"
    else:
        cls = "não preenche o critério de oxigenação"
    classes = ["SDRA grave", "SDRA moderada", "SDRA leve", "não preenche o critério de oxigenação"]
    certa = f"P/F ≈ {fmt(pf)} — {cls}"
    erradas = [f"P/F ≈ {fmt(pf)} — {k}" for k in classes if k != cls] + [f"P/F ≈ {fmt(pao2 / (fio2 * 100), 1)} — {cls}"]
    prona = (" P/F < 150 com FiO₂ ≥ 0,6: indicação de PRONA precoce (≥ 16 h/dia)." if pf < 150 and fio2 >= 0.6 else "")
    coment = (f"P/F = {pao2} / {fmt(fio2, 2)} = {fmt(pf)} (FiO₂ em fração). Berlim, com PEEP ≥ 5: leve 200–300, "
              f"moderada 100–200, grave ≤ 100.{prona}")
    enun = (f"{rng.choice(_CAUSAS).capitalize()}, opacidades bilaterais sem disfunção cardíaca, intubado com PEEP {peep}. "
            f"FiO₂ {int(fio2 * 100)}%, PaO₂ {pao2} mmHg. Relação P/F e classificação:")
    return _montar(rng, "pf", enun, certa, erradas, coment)


def _q_ie(rng):
    vt = rng.randrange(360, 600, 20)
    fluxo = rng.choice([30, 36, 40, 45, 48, 60, 72, 80])
    fr = rng.choice([10, 12, 14, 15, 16, 18, 20, 24])
    ti = vt / 1000 / (fluxo / 60)
    ciclo = 60 / fr
    te = ciclo - ti
    if te <= ti * 0.8:
        return _q_ie(rng)
    rel = te / ti
    f = lambda t, r: f"Ti {fmt(t, 2)} s · I:E 1:{fmt(r, 1)}"
    certa = f(ti, rel)
    erradas = [f(ti, ciclo / ti), f(vt / fluxo / 60, (ciclo - vt / fluxo / 60) / (vt / fluxo / 60)),
               f(ti * 2, (ciclo - 2 * ti) / (2 * ti)) if ciclo > 3 * ti else f(ti / 2, (ciclo - ti / 2) / (ti / 2)),
               f(ti, rel + 1.5), f(ti, max(rel - 1.2, 0.5))]
    coment = (f"Fluxo {fluxo} L/min = {fmt(fluxo / 60, 2)} L/s. Ti = VT / fluxo = {fmt(vt / 1000, 2)} L / {fmt(fluxo / 60, 2)} L/s = {fmt(ti, 2)} s "
              f"(sem pausa). Ciclo = 60 / {fr} = {fmt(ciclo, 2)} s → Te = {fmt(te, 2)} s → I:E = 1:{fmt(rel, 1)}. "
              "Para alongar a expiração no obstrutivo: FR menor ou fluxo maior.")
    enun = f"VCV com fluxo quadrado: VT {vt} mL, fluxo {fluxo} L/min, FR {fr}, sem pausa inspiratória. Tempo inspiratório e relação I:E:"
    return _montar(rng, "ie", enun, certa, erradas, coment)


def _q_irrs(rng):
    while True:
        fr = rng.randint(14, 42)
        vt = rng.randrange(180, 600, 10)
        i = fr / (vt / 1000)
        if 40 <= i <= 200 and abs(i - 105) >= 6:
            break
    ok = i < 105
    lado = "sugere SUCESSO no desmame (< 105)" if ok else "sugere FALHA (≥ 105: respiração rápida e superficial)"
    certa = f"{fmt(i)} — {lado}"
    oposto = "sugere FALHA (≥ 105: respiração rápida e superficial)" if ok else "sugere SUCESSO no desmame (< 105)"
    erradas = [f"{fmt(i)} — {oposto}", f"{fmt(fr * vt / 1000, 1)} — {lado}", f"{fmt(vt / fr)} — {oposto}",
               f"{fmt(fr / vt, 2)} — {lado}"]
    coment = (f"IRRS = FR / VT em LITROS = {fr} / {fmt(vt / 1000, 2)} = {fmt(i)} respirações/min/L. Corte de Yang-Tobin: 105. "
              "É medido em respiração espontânea e não decide sozinho: o TRE (PSV 5–7 ou tubo T, 30–120 min) é o teste.")
    enun = f"No primeiro minuto do teste de respiração espontânea: FR {fr} irpm, VT {vt} mL. O índice de Tobin e sua leitura:"
    return _montar(rng, "irrs", enun, certa, erradas, coment)


_ARDS = {
    "vt": "Reduzir o VT para 6 mL/kg do peso predito",
    "plat": "Reduzir o VT (até 4 mL/kg) para trazer o platô a ≤ 30",
    "fr": "Aumentar a FR (até 35), mantendo o VT",
    "manter": "Manter: hipercapnia permissiva aceitável",
    "vt_sobe": "FR já em 35: subir o VT 1 mL/kg (tolerando platô > 30) e/ou considerar bicarbonato",
}


def _q_ardsnet(rng):
    sexo, alt, pp, real = _paciente(rng)
    alvo = rng.choice(list(_ARDS))
    peep = rng.choice([8, 10, 12, 14])
    hco3 = rng.randint(22, 27)
    if alvo == "vt":
        vtkg, pplat, fr = rng.uniform(8.5, 11), rng.randint(24, 30), rng.randint(14, 20)
        pa = rng.randint(36, 48)
    elif alvo == "plat":
        vtkg, pplat, fr = rng.uniform(5.8, 6.3), rng.randint(32, 36), rng.randint(20, 28)
        pa = rng.randint(40, 55)
    else:
        vtkg, pplat = rng.uniform(5.8, 6.3), rng.randint(peep + 10, 30)
        if alvo == "manter":
            fr = rng.randint(22, 30)
            pa = None
            while pa is None or not 7.30 <= ph_de(pa, hco3) <= 7.38:
                hco3 = rng.randint(26, 32)
                pa = rng.randint(48, 62)
        elif alvo == "fr":
            fr = rng.randint(18, 28)
            pa = None
            while pa is None or not 7.16 <= ph_de(pa, hco3) <= 7.27:
                pa = rng.randint(50, 80)
        else:
            fr = 35
            pa = None
            while pa is None or not 7.00 <= ph_de(pa, hco3) <= 7.13:
                pa = rng.randint(70, 110)
    vt = round(vtkg * pp, -1)
    ph = round(ph_de(pa, hco3), 2)
    enun = (f"{_quem(sexo, alt, real)}, SDRA por {rng.choice(_CAUSAS)}. VCV: VT {fmt(vt)} mL, FR {fr}, PEEP {peep}, "
            f"Pplat {pplat} cmH₂O. Gasometria: pH {fmt(ph, 2)}, PaCO₂ {pa}, HCO₃⁻ {hco3}.\nPelo protocolo ARDSNet, o próximo passo é:")
    certa = _ARDS[alvo]
    erradas = [v for k, v in _ARDS.items() if k != alvo]
    base = "50" if sexo == "M" else "45,5"
    coment = (f"Peso predito = {base} + 0,91 × ({alt} − 152,4) = {fmt(pp, 1)} kg → VT atual = {fmt(vt / pp, 1)} mL/kg. "
              f"Platô {pplat}. pH {fmt(ph, 2)}.\nOrdem do protocolo: 1) VT 6 mL/kg; 2) platô > 30 → baixar o VT até 4; "
              "3) pH 7,15–7,30 → FR até 35; 4) pH < 7,15 com FR 35 → VT +1 mL/kg (platô pode passar de 30), bicarbonato opcional; "
              "pH ≥ 7,30 → manter (hipercapnia permissiva).")
    return _montar(rng, "ardsnet", enun, certa, erradas, coment)


_FUNC = {"peso": _q_peso, "complacencia": _q_complacencia, "resistencia": _q_resistencia, "pico": _q_pico,
         "protetora": _q_protetora, "co2": _q_co2, "fio2": _q_fio2, "pf": _q_pf, "ie": _q_ie,
         "irrs": _q_irrs, "ardsnet": _q_ardsnet}


def questao(rng, habil):
    return _FUNC[habil](rng)


def taxa_erro(save, habil):
    s = save.stat(f"{PREFIXO}:{habil}")
    if not s or s["c"] + s["e"] == 0:
        return None
    return s["e"] / (s["c"] + s["e"])


def fase(save, habil=None, n=6, rng=None):
    """n questões. Sem habilidade: mistura, pesando mais as habilidades com mais erro."""
    rng = rng or random.Random()
    if habil:
        return [questao(rng, habil) for _ in range(n)]
    hs = list(HABILIDADES)
    pesos = [1 + 3 * (taxa_erro(save, h) if taxa_erro(save, h) is not None else 0.5) for h in hs]
    return [questao(rng, rng.choices(hs, pesos)[0]) for _ in range(n)]
