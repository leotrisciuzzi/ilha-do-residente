"""Personagem escolhido, itens comprados e itens equipados (o desenho está em heroi.py).

No save:
  visual = {"personagem": "doutor", "equip": {"doutor": {nuvem, bastao, roupa}, "doutora": {...}}, "t": quando}
  itens  = ["nuvem:algodao", "bastao:luz", "personagem:cirurgiao", ...]   (comprados; preço 0 já vem com o jogo)
Personagens novos também se compram (na tela de escolha) e trazem o próprio kit (nuvem, bastão, roupa).
Cada personagem guarda o próprio conjunto equipado. Os itens comprados servem para todos.
Pets, coleiras e chapéus (pets.py) usam a mesma lista de itens; o que está equipado neles fica em save.d["pet"].
A sincronia (sincronia.py) junta os itens dos aparelhos e fica com o visual escolhido por último."""
import time

from . import heroi, pets

heroi.CATALOGO.update(pets.CATALOGO)            # possui/comprar valem também para pets, coleiras e chapéus
CATEGORIAS = [("nuvem", "Nuvens"), ("bastao", "Bastões"), ("roupa", "Roupas")] + pets.CATEGORIAS
PET_CATS = {c for c, _ in pets.CATEGORIAS}


def _visual(save):
    v = save.d.setdefault("visual", {})
    v.setdefault("personagem", heroi.PADRAO)
    eq = v.setdefault("equip", {})
    for p, dados in heroi.PERSONAGENS.items():
        eq.setdefault(p, dict(dados["padrao"]))
    return v


def personagem(save):
    p = _visual(save)["personagem"]
    return p if p in heroi.PERSONAGENS and possui(save, "personagem", p) else heroi.PADRAO


def visual_atual(save, p=None):
    """Visual completo (personagem + itens equipados dele), pronto para heroi.heroi(visual=)."""
    p = p or personagem(save)
    return heroi.visual_valido({"personagem": p, **_visual(save)["equip"].get(p, {})})


def aplicar(save):
    heroi.equipar(visual_atual(save))


def _tocar(save):
    _visual(save)["t"] = time.time()
    save.salvar()
    aplicar(save)


def escolher_personagem(save, p):
    if p in heroi.PERSONAGENS and possui(save, "personagem", p):
        _visual(save)["personagem"] = p
        _tocar(save)


def possui(save, cat, item):
    dados = heroi.CATALOGO[cat].get(item)
    if not dados:
        return False
    if dados["preco"] == 0 or f"{cat}:{item}" in save.d.get("itens", []):
        return True
    # o kit de um personagem que você tem também é seu
    return cat != "personagem" and any(d["padrao"].get(cat) == item and possui(save, "personagem", pid)
                                       for pid, d in heroi.PERSONAGENS.items())


def comprar(save, cat, item):
    """Debita as moedas e guarda o item. Devolve True se já tinha ou se comprou."""
    if possui(save, cat, item):
        return True
    dados = heroi.CATALOGO[cat].get(item)
    if not dados or not save.gastar(moedas=dados["preco"]):
        return False
    save.d.setdefault("itens", []).append(f"{cat}:{item}")
    save.salvar()
    return True


def equipar(save, cat, item, p=None):
    if cat in PET_CATS:
        return pets.equipar(save, cat, item)
    if not possui(save, cat, item):
        return False
    p = p or personagem(save)
    _visual(save)["equip"][p][cat] = item
    _tocar(save)
    return True


def equipado(save, cat, p=None):
    if cat in PET_CATS:
        return pets.equipado(save, cat)
    return visual_atual(save, p)[cat]
