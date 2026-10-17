# mal-att

Gráficos do meu perfil no MyAnimeList (`Vleber_23`), gerados a partir da minha lista pública
e atualizados todo dia por uma GitHub Action.

- `scripts/build.py` lê a lista e desenha `charts/stats.png`, `charts/scores.png` e `charts/genres.png`
- `.github/workflows/update.yml` roda o script diariamente e faz o commit das imagens
- `stats.json` guarda os últimos números (dias, episódios e capítulos vêm da página do perfil; se a leitura falhar, mantém os anteriores)

Rodar localmente: `pip install matplotlib && python scripts/build.py`
