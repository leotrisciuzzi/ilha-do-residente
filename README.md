# Ilha do Residente

Jogo de plataforma em pixel art para estudar medicina: você corre, pula e enfrenta os
**bichos-questão** — cada um abre uma questão. Cada tema é um *mundo* com três modos:

- **Aprendizado** — módulos com uma aula curta antes e o comentário depois de cada questão;
- **Treino** — casos gerados na hora por regra/fórmula, infinitos (gasometria, VM, doses, escores…);
- **Prova final** — 10 questões de todo o mundo, erros e inéditas primeiro.

Mundos: Insuficiência Cardíaca · Farmacologia Cardiovascular · Antibióticos · Gasometria ·
Ventilação Mecânica · Reumatologia. Mais: fluxogramas do raciocínio (gasometria, eletrólitos, asma,
FAST HUG, espirometria), leitura de ECG, Mapa de Estudos e O Mirante.

## Jogar

**No navegador:** <https://leotrisciuzzi.github.io/ilha-do-residente/> — PC (teclado ou controle) ou
celular (toque: o Doutor corre sozinho; toque pula, deslize para virar/atacar). O progresso fica salvo
no próprio navegador.

**No PC, pelo código:**

```bash
pip install pygame-ce
cd jogo && python main.py
```

## Como é feito

Python + [pygame-ce](https://pyga.me/), compilado para WebAssembly com
[pygbag](https://github.com/pygame-web/pygbag). Arte e sons são gerados pelo código ou próprios; o
conteúdo dos mundos está em `jogo/pacotes/*.json`. A cada push na `main`, o GitHub Actions compila e
publica no GitHub Pages (`.github/workflows/pages.yml`).

## Licença

- Código: **MIT** (`LICENSE`).
- Conteúdo didático (aulas, questões, comentários), arte e trilhas próprias: **CC BY-NC 4.0**
  (`LICENSE-CONTEUDO.md`) — use e compartilhe citando "Ilha do Residente — criado por Leonardo
  Trisciuzzi", sem fins comerciais.
- Componentes de terceiros: `NOTICE.md`.

© 2026 Leonardo Trisciuzzi.

## Aviso

Jogo educativo para estudantes de medicina e residentes. O conteúdo é didático: não substitui o
julgamento clínico, a bula nem as diretrizes vigentes, e não deve ser usado para decidir condutas.
