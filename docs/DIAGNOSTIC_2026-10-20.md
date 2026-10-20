# Diagnóstico de acesso, Git e preservação — 20/10/2026

## Git

- Commit local confirmado: `8f08fbd25fabc2e4b8c4067dff42f3d340afad20`.
- `git fetch origin main` funcionou com a autenticação HTTPS fornecida pelo ambiente, sem token novo.
- Remoto `origin/main`: `24f8c1821f56ace6c40f309b99a8fce095713373`.
- Comparação `origin/main...main`: 0 commits exclusivos do remoto e 1 exclusivo local. Atualização seria fast-forward, conforme o estado remoto observado nesta execução.
- Árvore estava limpa antes do diagnóstico. Arquivos existentes e commit foram preservados. Os dois documentos em `docs/` foram acrescentados sem alterar a versão 1.
- 12 testes aprovados novamente; `git diff --check HEAD` sem erro. O commit contém apenas fontes/configuração/testes/documentação; dados e .venv permanecem ignorados.
- Pronto como commit da versão 1 para um push sujeito à confirmação do usuário. Leitura Git não comprova permissão de escrita ou aprovação pelas regras do GitHub; não foi feita operação de escrita remota nem push de teste.

## Diagnóstico do HTTP 403

Nas tentativas anteriores, o erro era `Tunnel connection failed: 403 Forbidden`: o túnel HTTPS falhava antes da resposta RSS. Isso aponta para o proxy/política do ambiente, sem demonstrar recusa pelos editores. A configuração original tinha acesso restrito com presets de gerenciadores de pacotes; os domínios RSS foram depois salvos no rascunho.

Nesta execução, o rascunho lido é revisão 1 e contém os hosts personalizados `techcrunch.com`, `www.technologyreview.com`, `venturebeat.com`, `feeds.arstechnica.com`, `arstechnica.com`, além do preset de pacotes. Nenhuma exigência de credencial aparece nessa configuração. A existência do rascunho não prova publicação. Não há ferramenta disponível de status do runtime para comparar diretamente sua política efetiva com a configuração salva.

Variáveis de proxy estão presentes (somente nomes foram inspecionados). Os testes usaram `urllib` e o proxy já configurado, TLS verificado e identificação normal do coletor. Não foram usados conexão direta para evitar proxy, IP alternativo, proxy externo, cookies extraídos, rotação de identidade, desativação de TLS ou outro contorno de acesso.

Resultado atual: HTTP 200 nas quatro fontes e no controle PyPI. VentureBeat redirecionou normalmente para a mesma URL sem barra final. A mudança é compatível com liberação da rede, mas o mecanismo e momento exato da aplicação/publicação não são observáveis. Não é necessário ampliar para acesso irrestrito ou mudar o transporte para obter os feeds testados.

## Coleta real

Execução: `2026-10-20T13:27:30.015981+00:00` (10:27:30 em São Paulo). Comando: `.venv/bin/python -m evoa_news`. Saída 0.

| Fonte independente | HTTP | Itens lidos | Novos | Ignorados |
| --- | --- | --- | --- | --- |
| TechCrunch | 200 | 20 | 20 | 0 |
| MIT Technology Review | 200 | 10 | 7 | 3 |
| VentureBeat AI | 200 | 7 | 0 | 7 |
| Ars Technica | 200 | 20 | 15 | 5 |

Foram exportadas 42 notícias reais elegíveis de três editores independentes. Os sete itens da VentureBeat tinham publicação entre janeiro e agosto de 2026 e foram excluídos pela janela de 24 horas; sucesso HTTP não garante atualização editorial do feed. Isso não é indisponibilidade de rede.

Resultados locais preservados em `output/2026-10-20T132730Z-8_3c1x4e/`: `news.csv`, `report.md`, `status.json`. Leitura do CSV confirmou 42 registros, três fontes, todas as datas de publicação e links originais preenchidos, notas de 42 a 97. O Markdown mostra até 20 itens conforme o comportamento atual; o CSV contém todos os 42. Não foram inventadas notícias nem usadas fixtures como dados reais.

As datas são as declaradas pelos feeds, não comprovação da data dos acontecimentos. Testar RSS não valida a veracidade das matérias, a disponibilidade de cada página original, permissões de republicação ou redação editorial. O sistema ainda não produz redação no padrão EVOA nem verificação de afirmações; essas são próximas etapas descritas no plano.

Solução segura adotada: manter RSS público via HTTPS nos domínios explícitos. Se um site recusar acesso no futuro, registrar erro e suspender essa fonte, consultar suas condições e preferir feed/API pública oficialmente autorizada. Não foi necessário nem testado substituir por APIs nesta execução.

## Preservação e persistência

Antes da coleta foi feito backup consistente SQLite (`Connection.backup`, integridade `ok`) com zero artigos e duas execuções. Após coleta: banco com 42 artigos e três execuções. Novo backup e restauração em arquivo separado confirmaram integridade e contagens. Não foi sobrescrito o banco ativo.

Cópias locais em `/workspace/evoa-preservation/`:

- `repository.bundle`: histórico Git completo, verificado por `git bundle verify`.
- `history-20261020T132712366674Z.sqlite3`: estado anterior.
- `history-20261020T132903664721Z.sqlite3`: estado após coleta.
- `restore-test-20261020T132903664721Z.sqlite3`: restauração testada do estado após coleta.
- `latest-manifest.json`: caminhos, contagens e SHA-256 do backup atual.

SHA-256 do backup atual: `8051ca1815c794bc8b93139de8a407dae32fd718855e213dcf4c91baa89eafed`.

Essas cópias permanecem na mesma máquina temporária. Não existe comprovação de armazenamento externo persistente, nem destino/credencial de banco ou backup identificados nas configurações e nomes de variáveis examinados. A ausência desses nomes não prova que o usuário não possui um serviço externo. O bundle não contém os dados ignorados. É necessário escolher destino externo, transferir o backup por canal seguro e testar restauração nesse destino antes de iniciar avaliações editoriais reais. Nenhuma chave foi solicitada em chat.

## O que fica pendente

- Escolha e provisionamento do armazenamento durável e backup independente; recomendações em `EDITORIAL_ROADMAP.md`.
- Confirmação explícita para push. Não publicar ou sobrescrever a branch remota por conta própria.
- Implementação futura dos módulos editoriais, migrações, rascunhos de todos os elegíveis, Streamlit e avaliação temporal do ranking. Nenhuma dessas funcionalidades foi alegada como pronta nesta execução.
- Snapshot/publicação do ambiente é ação do produto, distinta de validação atual. Coleta em tarefa nova ainda não foi validada.

Nenhum agendamento, envio, publicação de notícias ou push foi executado. Não houve mudança adicional de rede ou scripts nesta execução: a configuração já existente permitiu os testes atuais.
