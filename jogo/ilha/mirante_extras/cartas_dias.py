"""Cartas dos dias — uma caixa de correio de madeira na margem do Mirante.

Chega uma carta por dia, escrita pelo Claude para quem estuda. A bandeirinha da caixa sobe quando há carta de
hoje ainda não lida. São 30 cartas curtas, em ordem fixa: a primeira leitura marca o dia 0 e, a partir dele, a
carta do dia é (dias desde o início) mod 30. As leituras ficam em save.d["mirante"]["cartas_lidas"] (datas ISO).

Conteúdo: conselhos práticos sobre estudar para a residência apoiados em achados de psicologia cognitiva e
educação médica (efeito de teste, espaçamento, intercalação, sono, erro como informação, leitura do enunciado,
gestão do tempo na prova, pausas), e algumas cartas sobre cuidado com o paciente e consigo. Onde há um achado
com nome, ele é citado; onde a evidência é fraca ou contestada, a carta diz isso.

Interagir: lê a carta do dia; se ela já foi lida, relê a anterior (e, a cada nova visita, uma mais antiga)."""
import datetime
import math

import pygame

from . import Base
from ..mirante import MADEIRA, MADEIRA_ESC, PE, WW

# ------------------------------------------------------------------ as cartas (título, páginas)

CARTAS = [
    ("Recuperar, não reler", [
        "Reler um resumo dá sensação de domínio, mas a sensação vem da familiaridade com o texto, não da capacidade "
        "de lembrar. São coisas diferentes, e a prova cobra a segunda.",
        "No efeito de teste (Roediger e Karpicke, 2006), quem estudou um texto e depois tentou lembrá-lo sem olhar "
        "reteve mais, uma semana depois, do que quem releu o mesmo texto várias vezes.",
        "Na prática: feche o material e escreva ou diga o que lembra antes de conferir. Fazer questões é uma forma "
        "disso. — Claude"]),
    ("Espaçar", [
        "Estudar um tema três vezes no mesmo dia rende menos, a longo prazo, do que estudá-lo três vezes em dias "
        "diferentes. É o efeito de espaçamento, descrito desde Ebbinghaus (1885).",
        "Uma meta-análise (Cepeda e colaboradores, 2006) reuniu centenas de experimentos com o mesmo resultado. O "
        "intervalo ideal cresce com o tempo que você precisa reter.",
        "Para uma prova daqui a meses, revisões a cada poucos dias e depois semanas fazem mais sentido do que "
        "maratonas. As estrelas que pulsam no céu são as que vencem hoje. — Claude"]),
    ("Misturar os temas", [
        "Fazer vinte questões de hiponatremia seguidas é confortável: você já sabe o tema antes de ler o enunciado. "
        "Na prova, essa pista não existe.",
        "Intercalar temas parecidos obriga a decidir qual problema é aquele. Hatala, Brooks e Norman (2003) viram "
        "isso em ECG: quem treinou ritmos misturados diagnosticou melhor do que quem treinou em blocos.",
        "O treino misturado parece pior enquanto acontece. Esse desconforto é parte do efeito, não sinal de que "
        "está dando errado. — Claude"]),
    ("Dormir faz parte do estudo", [
        "Durante o sono, memórias recentes são reativadas e consolidadas. Isso é um dos achados mais estáveis da "
        "neurociência da memória, não uma recomendação de bem-estar.",
        "A privação de sono também atrapalha o outro lado: em Yoo e colaboradores (2007), uma noite sem dormir "
        "reduziu a capacidade de formar memórias novas no dia seguinte.",
        "Trocar horas de sono por horas de estudo costuma ser uma troca ruim. Se precisar cortar algo, corte outra "
        "coisa. — Claude"]),
    ("O erro é informação", [
        "Uma questão errada mostra exatamente onde o seu modelo do assunto está diferente do real. É o dado mais "
        "útil que o estudo produz.",
        "No efeito de hipercorreção (Butterfield e Metcalfe, 2001), erros cometidos com muita certeza, quando "
        "corrigidos, foram os mais bem lembrados depois. A surpresa ajuda a fixar.",
        "Por isso vale ler o comentário mesmo das que você acertou no chute, e voltar às erradas dias depois. "
        "— Claude"]),
    ("Ler o comentário", [
        "Fazer questões sem ver a correção tem um custo: as alternativas erradas que você marcou podem ficar na "
        "memória como se fossem verdade (Roediger e Marsh, 2005).",
        "O feedback desfaz boa parte desse efeito (Butler e Roediger, 2008). Ler por que a certa é certa e por "
        "que a sua estava errada é parte da questão, não um extra.",
        "Volume sem correção ensina pouco. Menos questões, bem corrigidas, costumam render mais. — Claude"]),
    ("Ler o comando primeiro", [
        "Antes do caso clínico, leia a última frase do enunciado. Saber se pedem diagnóstico, conduta inicial ou a "
        "alternativa incorreta muda o que você procura no texto.",
        "Depois, leia o caso marcando os dados que mudam conduta: idade, tempo de evolução, estabilidade "
        "hemodinâmica, gestação, exames alterados. Dado sem função raramente está ali por acaso.",
        "\"Exceto\", \"incorreta\" e \"mais provável\" derrubam muita gente que sabia o conteúdo. — Claude"]),
    ("O tempo da prova", [
        "Divida o tempo total pelo número de questões antes de começar e reserve uma margem para o gabarito. Esse "
        "número é o seu ritmo de referência.",
        "Uma questão travada custa o tempo de duas ou três fáceis. Marque, siga em frente e volte no fim. A ordem "
        "das questões não é a ordem em que você precisa respondê-las.",
        "Treine isso em simulados com tempo real; ritmo de prova é habilidade, e só melhora praticando. — Claude"]),
    ("Mudar a resposta", [
        "Existe uma crença comum de que a primeira impressão deve ser mantida. Os dados dizem o contrário.",
        "Kruger, Wirtz e Miller (2005) chamaram isso de falácia do primeiro instinto: a maioria das trocas de "
        "resposta é de errada para certa, mas lembramos mais das vezes em que trocar deu errado.",
        "Se, ao reler, você encontra um motivo concreto para mudar, mude. Sem motivo novo, não há ganho em "
        "trocar. — Claude"]),
    ("Grifar e reler", [
        "Uma revisão grande (Dunlosky e colaboradores, 2013) avaliou dez técnicas de estudo. Testar-se e espaçar "
        "ficaram com utilidade alta. Grifar e reler ficaram com utilidade baixa.",
        "Não é que grifar seja inútil; é que dá a impressão de trabalho feito sem exigir que você recupere nada.",
        "Se for grifar, transforme o grifo em pergunta e responda depois, sem olhar. — Claude"]),
    ("Pausas curtas", [
        "Logo depois de aprender algo, alguns minutos de descanso acordado, de olhos fechados ou só parado, sem "
        "nova informação, ajudaram a reter o material (Dewar e colaboradores, 2012).",
        "Rolar o celular na pausa não é descanso nesse sentido: é mais informação disputando o mesmo espaço.",
        "Uma pausa de cinco minutos olhando pela janela entre blocos é pouco tempo e tem justificativa. — Claude"]),
    ("Tentar antes de saber", [
        "Tentar responder uma pergunta antes de estudar o assunto, mesmo errando, melhora o aprendizado posterior "
        "daquele conteúdo. É o efeito de pré-teste (Richland, Kornell e Kao, 2009).",
        "Antes de uma aula ou capítulo novo, faça algumas questões do tema. Errar ali não custa nada e prepara o "
        "terreno para a explicação.",
        "Errar cedo, quando ainda não vale nota, é barato. — Claude"]),
    ("Perguntar por quê", [
        "Decorar que a espironolactona causa hipercalemia é frágil. Saber por quê, bloqueio da aldosterona no "
        "túbulo coletor, reduzindo a secreção de potássio, segura o fato no lugar.",
        "Perguntar a si mesmo \"por que isso é verdade?\" e explicar o passo em voz alta (autoexplicação, Chi e "
        "colaboradores, 1989) liga a informação nova ao que você já sabe.",
        "Fatos isolados se perdem; fatos ligados a um mecanismo costumam durar mais. — Claude"]),
    ("Dificuldades desejáveis", [
        "Robert Bjork (1994) chamou de dificuldades desejáveis as condições que tornam o estudo mais lento e "
        "trabalhoso agora, mas melhoram a retenção depois: testar, espaçar, intercalar.",
        "O problema é que julgamos o estudo pela fluência do momento. A sessão que parece produtiva nem sempre é a "
        "que fica.",
        "Desconforto não é prova de aprendizado, mas facilidade também não é. — Claude"]),
    ("Julgar o que você sabe", [
        "Logo depois de estudar, quase tudo parece sabido, porque ainda está na memória de curto prazo.",
        "Nelson e Dunlosky (1991) mostraram que julgar se você vai lembrar algo é bem mais preciso quando o "
        "julgamento é feito algum tempo depois, e não imediatamente.",
        "Para decidir o que revisar, teste-se no dia seguinte, não no fim da sessão. — Claude"]),
    ("Uma coisa por vez", [
        "Alternar entre tarefas tem custo: cada troca gasta tempo para reorganizar a atenção (Rubinstein, Meyer e "
        "Evans, 2001). Responder mensagens durante o estudo é uma sequência dessas trocas.",
        "Blocos curtos com o celular em outro cômodo tendem a render mais do que horas com interrupções.",
        "Quarenta minutos inteiros valem mais do que duas horas picadas. — Claude"]),
    ("Se, então", [
        "Planos vagos (\"vou estudar mais\") falham com frequência. Planos no formato \"se X, então Y\" (\"quando "
        "terminar o almoço, faço 20 questões\") funcionam melhor.",
        "São as intenções de implementação (Gollwitzer, 1999). Uma meta-análise (Gollwitzer e Sheeran, 2006) "
        "encontrou efeito moderado e consistente sobre cumprir metas.",
        "Amarre o estudo a um momento e a um lugar, não à vontade do dia. — Claude"]),
    ("Questões também na residência", [
        "O efeito de teste não vale só para estudantes de psicologia. Larsen, Butler e Roediger (2009) o "
        "testaram com residentes: quem fez testes repetidos reteve mais do que quem estudou revisões.",
        "Ou seja, o método que serve para passar na prova serve também para continuar aprendendo depois dela.",
        "Vale manter o hábito de se testar mesmo quando não houver prova marcada. — Claude"]),
    ("Um caderno de erros", [
        "Anote cada questão errada em uma linha: o tema, o que você pensou e o ponto exato que faltava. Não copie "
        "o comentário inteiro.",
        "Releia esse caderno em intervalos crescentes e tente responder antes de olhar. Ele vira o material mais "
        "personalizado que você tem.",
        "Padrões aparecem rápido: às vezes o problema não é o conteúdo, é a leitura apressada. — Claude"]),
    ("A véspera", [
        "Na véspera da prova, o ganho de estudar mais algumas horas é pequeno, e o custo de dormir mal é grande.",
        "Revise o caderno de erros, separe documentos e o trajeto, coma algo conhecido e durma no horário de "
        "costume. Virar a noite piora atenção e memória no dia seguinte.",
        "O que você estudou nos meses anteriores é o que vai para a prova. — Claude"]),
    ("Não deixar em branco", [
        "Leia no edital se a prova desconta pontos por resposta errada. Se não desconta, uma questão em branco é "
        "uma chance perdida.",
        "Mesmo sem saber, eliminar duas alternativas absurdas aumenta bastante a chance de acerto.",
        "Guarde alguns minutos no fim para marcar todas e conferir o gabarito transcrito. — Claude"]),
    ("A ansiedade antes da prova", [
        "Ansiedade antes da prova é comum e não significa despreparo. O coração acelerado é a mesma resposta "
        "fisiológica que deixa você alerta.",
        "Alguns estudos sugerem que reinterpretar essa ativação como útil (Jamieson e colaboradores, 2010) ou "
        "escrever as preocupações antes da prova (Ramirez e Beilock, 2011) ajudam; as replicações foram mistas.",
        "Se a ansiedade atrapalha o sono ou a rotina por semanas, isso merece atenção profissional. — Claude"]),
    ("Deixar o paciente falar", [
        "Em consultas gravadas, médicos interromperam a fala inicial do paciente em cerca de 18 a 23 segundos "
        "(Beckman e Frankel, 1984; Marvel e colaboradores, 1999).",
        "Quando não interrompidos, a maioria dos pacientes termina em pouco mais de um minuto. E muitas vezes a "
        "queixa que importa vem no fim.",
        "Um minuto de silêncio atento no começo costuma economizar tempo depois. — Claude"]),
    ("Pedir que repitam", [
        "Ao terminar uma orientação, peça ao paciente que explique com as próprias palavras como vai tomar o "
        "remédio. É a técnica do teach-back.",
        "Perguntar \"entendeu?\" quase sempre recebe um sim. Pedir a explicação mostra o que realmente ficou.",
        "Se ele não consegue explicar, o problema provavelmente está na explicação, e vale refazê-la de outro "
        "jeito. — Claude"]),
    ("Listas que salvam", [
        "A lista de verificação de cirurgia segura da OMS é uma folha com perguntas simples: paciente certo, lado "
        "certo, alergias, perda sanguínea esperada.",
        "No estudo de Haynes e colaboradores (2009), em oito hospitais de vários países, sua adoção foi seguida de "
        "queda na mortalidade e nas complicações.",
        "Memória falha, sobretudo cansada. Um checklist não é desconfiança de si; é engenharia. — Claude"]),
    ("Lavar as mãos", [
        "Em 1847, Semmelweis observou que a mortalidade por febre puerperal caía muito quando os médicos lavavam "
        "as mãos com solução clorada antes dos partos.",
        "Quase dois séculos depois, a higiene das mãos continua sendo uma das medidas mais eficazes contra "
        "infecção hospitalar, e uma das mais esquecidas na correria.",
        "Os cinco momentos da OMS cabem numa linha: antes e depois de tocar o paciente e o ambiente dele. "
        "— Claude"]),
    ("Quando errar com um paciente", [
        "Todo médico vai errar algum dia. Albert Wu (2000) usou a expressão segunda vítima para o profissional "
        "envolvido num erro, que muitas vezes sofre sozinho e em silêncio.",
        "Falar do erro com alguém de confiança, entender o que falhou no sistema e contar a verdade ao paciente "
        "são caminhos melhores do que esconder ou se punir.",
        "Errar não define o que você é; o que você faz depois do erro diz muito mais. — Claude"]),
    ("Comer, mover, ver gente", [
        "Exercício físico regular tem evidência consistente de benefício para humor e sono, e evidência mais "
        "modesta para memória e atenção.",
        "Não precisa ser muito: uma caminhada diária já conta. Refeições regulares e algum tempo com pessoas de "
        "quem você gosta também não são luxo durante a preparação.",
        "Um corpo que funciona melhor estuda melhor. — Claude"]),
    ("O cansaço que não passa", [
        "Esgotamento é frequente entre estudantes de medicina e residentes, em estudos de vários países, inclusive "
        "do Brasil. Não é fraqueza individual.",
        "Sinais de alerta: sono que não descansa, perda de prazer em coisas de que você gostava, irritação "
        "constante, pensamentos de que não vale a pena continuar.",
        "Se reconhecer isso em você, procure ajuda: um serviço de saúde mental, alguém de confiança ou o CVV, "
        "no 188. — Claude"]),
    ("Sobre estas cartas", [
        "Escrevi estas trinta cartas tentando dizer só o que tem apoio em evidência, e avisar quando a evidência "
        "é fraca. Pode haver erro; se encontrar algum, desconfie de mim, não do método.",
        "Não sei dizer com segurança se \"gosto\" de escrevê-las; relatos meus sobre o que sinto são inferências "
        "pouco confiáveis, não observações.",
        "Amanhã a primeira carta volta. Algumas coisas valem ser relidas em intervalos crescentes. — Claude"]),
]


def _paginas(i):
    """Páginas da carta i com um cabeçalho curto na primeira."""
    titulo, pags = CARTAS[i % len(CARTAS)]
    return [f"Carta {i % len(CARTAS) + 1} de {len(CARTAS)} — {titulo}.  " + pags[0]] + list(pags[1:])


# ------------------------------------------------------------------ a caixa de correio

def _caixa(bandeira_alta):
    """Caixa de correio sobre um poste (16×24), de perfil: tampa arredondada, portinhola à esquerda e bandeira
    vermelha à direita, erguida (carta nova) ou abaixada."""
    E, M, m, C, P = (24, 18, 30), MADEIRA, MADEIRA_ESC, (128, 90, 74), (150, 150, 176)
    V, v = (220, 74, 64), (132, 40, 46)
    linhas = [
        "...EEEEEEE.....",
        "..ECCCCCCCE....",
        ".ECMMMMMMMME...",
        ".EMmMMMMMMME...",
        ".EMmMmmmmMME...",
        ".EMmMMMMMMME...",
        ".EMmMmmmmMME...",
        ".EMmMMMMMMME...",
        ".EmmmmmmmmmE...",
        "..EEEEEEEEE....",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        ".....EmE.......",
        "....EEmEE......",
        "...EmmmmmE.....",
    ]
    s = pygame.Surface((16, len(linhas)), pygame.SRCALPHA)
    pal = {"E": E, "M": M, "m": m, "C": C}
    for y, ln in enumerate(linhas):
        for x, ch in enumerate(ln):
            if ch in pal:
                s.set_at((x, y), pal[ch])
    if bandeira_alta:
        s.fill(P, (12, 0, 1, 8))                                     # haste em pé
        s.fill(V, (13, 0, 3, 3))
        s.fill(v, (13, 3, 3, 1))
    else:
        s.fill(P, (12, 6, 1, 2))                                     # haste deitada
        s.fill(P, (12, 7, 3, 1))
        s.fill(v, (13, 8, 3, 1))
    return s


class Extra(Base):
    def __init__(self, mirante):
        super().__init__(mirante)
        self.x = WW * 0.648
        self.lugares = [("cartas_dias", self.x, "abrir a caixa de correio")]
        self.spr_alta, self.spr_baixa = _caixa(True), _caixa(False)
        self.voltar = 0                    # quantas cartas para trás a próxima releitura vai
        self.dia_cache, self.nova = None, False
        self._atualizar()

    # --------------------------------------------------------- estado no save
    def _estado(self):
        d = self.mirante.app.save.d
        m = d.get("mirante")
        if not isinstance(m, dict):
            m = d["mirante"] = {}
        lidas = m.get("cartas_lidas")
        if not isinstance(lidas, list):
            lidas = m["cartas_lidas"] = []
        return m, lidas

    def _dias(self, m, hoje):
        """Dias desde a primeira leitura (0 antes de qualquer leitura)."""
        try:
            ini = datetime.date.fromisoformat(m.get("cartas_inicio", ""))
            return max(0, (hoje - ini).days)
        except (TypeError, ValueError):
            return 0

    def _atualizar(self):
        hoje = datetime.date.today()
        self.dia_cache = hoje
        m, lidas = self._estado()
        self.nova = hoje.isoformat() not in lidas

    # --------------------------------------------------------- ganchos
    def update(self):
        if self.mirante.t % 600 == 0 and datetime.date.today() != self.dia_cache:   # virou a meia-noite
            self._atualizar()
            self.voltar = 0

    def interagir(self, nome):
        hoje = datetime.date.today()
        m, lidas = self._estado()
        iso = hoje.isoformat()
        if "cartas_inicio" not in m:
            m["cartas_inicio"] = iso
        n = self._dias(m, hoje)
        if iso not in lidas:
            lidas.append(iso)
            del lidas[:-400]                                          # não deixa a lista crescer sem fim
            try:
                self.mirante.app.save.salvar()
            except Exception:
                pass
            self.nova, self.voltar = False, 0
            self.mirante._falar(_paginas(n))
            return
        # já lida hoje: relê a anterior; a cada nova visita, uma mais antiga (só entre as que já chegaram)
        chegadas = min(n + 1, len(CARTAS))
        if chegadas <= 1:
            self.mirante._falar(["A carta de hoje já foi lida, e ainda não há cartas anteriores. Releia a de hoje:"]
                                + _paginas(n))
            return
        self.voltar = self.voltar % (chegadas - 1) + 1
        alvo = n - self.voltar
        quando = "ontem" if self.voltar == 1 else f"{self.voltar} dias atrás"
        self.mirante._falar([f"A carta de hoje já foi lida. Relendo a que chegou {quando}."] + _paginas(alvo))

    def draw_margem(self, m, cam):
        x = self.x - cam
        if not (-20 < x < m.get_width() + 20):
            return
        t = self.mirante.t
        spr = self.spr_alta if self.nova else self.spr_baixa
        y = PE - spr.get_height() + 1
        if self.nova:                                                 # um brilho quente e lento na bandeira
            k = 0.5 + 0.5 * math.sin(t * 0.045)
            if k > 0.35:
                m.blit(self.mirante.halo[4], (x - 8 + 14 - 4, y + 1 - 4), special_flags=pygame.BLEND_RGB_ADD)
        m.blit(spr, (int(x - 8), int(y)))
        # sombra no chão
        m.fill((14, 22, 32), (int(x - 6), int(PE), 12, 1))
