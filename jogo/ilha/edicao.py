"""Edição do jogo. A edição pessoal (padrão) tem tudo; a edição de venda (Steam, Tucano —
chamada de "Steam" no código) é só o Mundo da
Gasometria (Aprendizado + Treino), sem rede, sem banco de questões de terceiros e sem
os atalhos de manutenção (corrigir gabarito). `ativar_steam()` tem de rodar ANTES de
importar ui/controle, porque eles leem as pastas de save na importação."""
import os

STEAM = False
ANDROID = False
VESTIBULANDO = False
NOME = "Ilha do Residente"
VERSAO = "1.40.0"
AUTOR = "Leonardo Trisciuzzi"
LICENCA = (f"© 2026 {AUTOR}. Código: licença MIT. Conteúdo didático: CC BY-NC 4.0 "
           "(use e compartilhe citando o autor, sem fins comerciais).")
WEB = False
PASTA = os.path.dirname(os.path.abspath(__file__))
FONTES = os.path.join(PASTA, "fontes")


def ativar_steam():
    global STEAM, NOME
    STEAM = True
    NOME = "Ilha do Residente: Gasometria"
    from . import data
    if os.name == "nt":                  # Windows: %APPDATA%\IlhaDoResidente-Gasometria
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    data.SAVE_DIR = os.path.join(base, "IlhaDoResidente-Gasometria")
    data.SAVE_FILE = os.path.join(data.SAVE_DIR, "save.json")
    data.CACHE_DIR = os.path.join(data.SAVE_DIR, "cache_imagens")
    from . import controle
    controle.ARQ = os.path.join(data.SAVE_DIR, "controles.json")
    # Padrão Xbox/Steam Deck: o botão A (de baixo) pula e confirma, B (direita) lança ovo e volta,
    # X (esquerda) língua, Y (cima) ovo. Os nomes na tela passam a ser os impressos no controle.
    controle.ACOES.clear()
    controle.ACOES.update({"UP": ["cima"], "DOWN": ["baixo"], "LEFT": ["esq"], "RIGHT": ["dir"],
                           "A": ["pulo", "ok"], "B": ["ovo", "voltar"], "X": ["lingua"], "Y": ["ovo"],
                           "START": ["pausa", "ok"], "SELECT": ["voltar"], "L": ["pgup"], "R": ["pgdn"]})
    controle.NOMES.update({"SELECT": "VIEW", "START": "MENU", "L": "LB", "R": "RB"})


RETRATO = False      # tela em pé (Android); precisa ser ativado antes de importar game/ui
ALTURA_MUNDO = 320   # em pé: altura do mundo (px de pixel art); acompanha o formato do celular
MARGEM_CIMA = 0      # em pé: faixa (px da tela lógica) livre para o furo da câmera / barra de status
MARGEM_BAIXO = 0     # em pé: faixa livre para a barra de gestos do Android
SEGURO_CIMA, SEGURO_BAIXO = 44, 28   # mínimos (px lógicos, 720 de largura): câmera e barra de gestos


def _tela_aparelho():
    """(largura, altura) da tela do aparelho em pé. ILHA_TELA=1080x2340 simula um aparelho (testes)."""
    tela = os.environ.get("ILHA_TELA")
    if tela:
        w, h = (int(v) for v in tela.lower().split("x"))
    else:
        import pygame
        pygame.display.init()
        w, h = pygame.display.get_desktop_sizes()[0]
    return (h, w) if w > h else (w, h)


def _layout_retrato():
    """Tela lógica de 720 de largura com a altura do aparelho: a área útil (múltiplo de 4, até a altura da
    fase = 384 px de mundo) fica no meio; o que sobra vira margem segura em cima e embaixo, preenchida com
    o próprio cenário. Devolve (altura do mundo, margem de cima, margem de baixo)."""
    try:
        w, h = _tela_aparelho()
        total = round(720 * h / w)
    except Exception:
        total = 1280 + SEGURO_CIMA + SEGURO_BAIXO
    util = max(1280, min(1536, (total - SEGURO_CIMA - SEGURO_BAIXO) // 4 * 4))
    sobra = max(0, total - util)
    baixo = min(sobra, max(SEGURO_BAIXO, sobra * SEGURO_BAIXO // (SEGURO_CIMA + SEGURO_BAIXO)))
    return util // 4, sobra - baixo, baixo


def ativar_android(pasta_dados):
    """Edição Android (Google Play, gratuita): as mesmas restrições da edição de venda, menus de
    pacotes de conteúdo (baixados/atualizados pela internet) e controles de toque."""
    global ANDROID, NOME, RETRATO
    ativar_steam()
    ANDROID = True
    RETRATO = not os.environ.get("ILHA_PAISAGEM")    # celular em pé, como o Super Mario Run
    # dicas do SDL antes de qualquer pygame.display.init (algumas só valem se lidas na inicialização)
    os.environ["SDL_ACCELEROMETER_AS_JOYSTICK"] = "0"      # senão o acelerômetro vira um "controle"
    os.environ["SDL_IOS_ORIENTATIONS"] = "Portrait" if RETRATO else "LandscapeLeft LandscapeRight"
    # o SCALED do pygame-ce só amplia em múltiplos inteiros, a não ser que esta dica exista: num celular
    # de 1080 px a tela de 720 ficava em 1x (pequena no meio) e os toques caíam fora do lugar
    os.environ["SDL_HINT_RENDER_SCALE_QUALITY"] = "1"
    os.environ["SDL_RENDER_SCALE_QUALITY"] = "1"
    global ALTURA_MUNDO, MARGEM_CIMA, MARGEM_BAIXO
    if RETRATO:
        ALTURA_MUNDO, MARGEM_CIMA, MARGEM_BAIXO = _layout_retrato()
    NOME = "Ilha do Residente"
    from . import data, controle
    data.SAVE_DIR = pasta_dados
    data.SAVE_FILE = os.path.join(pasta_dados, "save.json")
    data.CACHE_DIR = os.path.join(pasta_dados, "cache_imagens")
    controle.ARQ = os.path.join(pasta_dados, "controles.json")
    os.makedirs(pasta_dados, exist_ok=True)


def ativar_vestibulando():
    """Ilha do Vestibulando (Windows/Linux): mundos de vestibular (ENEM) no mesmo motor, com as
    restrições da edição de venda e save próprio (%APPDATA%\\IlhaDoVestibulando no Windows)."""
    global VESTIBULANDO, NOME
    ativar_steam()
    VESTIBULANDO = True
    NOME = "Ilha do Vestibulando"
    from . import data, controle
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        pasta = os.path.join(base, "IlhaDoVestibulando")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        pasta = os.path.join(base, "ilha-do-vestibulando")
    data.SAVE_DIR = pasta
    data.SAVE_FILE = os.path.join(pasta, "save.json")
    data.CACHE_DIR = os.path.join(pasta, "cache_imagens")
    controle.ARQ = os.path.join(pasta, "controles.json")
    os.makedirs(pasta, exist_ok=True)
    from . import estudantes
    estudantes.ativar()          # elenco de estudantes no lugar dos médicos


def no_steam_deck():
    return os.environ.get("SteamDeck") == "1"
