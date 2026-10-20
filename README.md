# EVOA News Automation

Primeira versão em Python para curadoria diária de notícias sobre inteligência artificial, tecnologia, inovação, startups, empreendedorismo e negócios. Usa RSS público, sem APIs pagas ou credenciais. Não envia nem publica conteúdo. Toda notícia exige verificação e aprovação editorial.

## Instalação e execução

Python 3.12 ou superior. No diretório do repositório:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m evoa_news
```

No Windows, use `.venv\Scripts\python.exe` em lugar de `.venv/bin/python`.

Opções:

```bash
.venv/bin/python -m evoa_news --sources config/sources.json --database data/history.sqlite3 --output output --max-age-hours 24 --top 20
```

Os caminhos são relativos ao diretório atual. Cada execução cria uma pasta exclusiva em `output/` com:

- `news.csv`: todas as notícias novas elegíveis, ordenadas por pontuação; UTF-8 com BOM e separador `;`, compatível com Excel e importação no Google Sheets. Se necessário, escolha explicitamente esse separador ao importar. Conteúdo que poderia executar fórmulas é prefixado com apóstrofo.
- `report.md`: até 20 notícias mais relevantes, resumos do RSS, links, pontuação e justificativa, mais estado das fontes.
- `status.json`: contagens de itens lidos, novos, duplicados e ignorados, além dos erros por fonte.

O histórico fica em `data/history.sqlite3`, incluindo registros das execuções. Preserve esse arquivo entre dias e faça backup; apagá-lo permite recoletar itens. CSVs, histórico e relatórios locais não são versionados. O histórico é confirmado somente após a gravação dos relatórios; se houver falha de escrita, a execução pode ser repetida. Falhas de disco podem deixar uma pasta incompleta, que não deve ser usada como relatório final sem `status.json`.

A saída do comando é JSON. Código de saída 1 indica que todas as fontes falharam; falha parcial gera relatório com o erro e saída 0. Consulte sempre `sources` em `status.json`: zero notícias pode significar duplicação, janela temporal ou indisponibilidade, não necessariamente ausência de notícias no mundo. Execuções devem ser sequenciais (não agende coletas sobrepostas).

## Fontes e configuração

Edite `config/sources.json`. Cada fonte define `name`, `url`, `category` e `trust` (0 a 100). Foram incluídos TechCrunch, MIT Technology Review, VentureBeat AI e Ars Technica. Os endereços são configurações de feeds públicos conhecidos; disponibilidade não é garantida. As notas de confiabilidade são avaliações editoriais iniciais configuráveis, não certificações ou checagem factual.

Se adicionar um agregador, use `"aggregator": true`: o link permanece em `feed_link`, mas `original_link` fica vazio e o relatório avisa que o original não foi confirmado. As fontes padrão são diretas. Links diretos são os fornecidos pelo RSS da fonte, sem resolução ou verificação automática da página de destino. Não há raspagem das matérias completas. Todos os resumos são trechos fornecidos pelo feed, com HTML removido; podem estar ausentes ou no idioma original. Confirme contexto e direitos de uso antes de reutilizá-los.

A rede precisa permitir HTTPS para os hosts configurados e eventuais destinos de redirecionamento. Instalação usa PyPI. Não desative TLS para contornar erros. Um erro HTTP 403 de túnel pode indicar bloqueio da política de rede; ele é registrado como falha da fonte.

## Seleção e pontuação

- Publicações com data nas últimas 24 horas são elegíveis por padrão; datas futuras e anteriores à janela são ignoradas. A janela pode ser ampliada por opção.
- `published_at` é a **data de publicação informada no RSS**, convertida para UTC. Não é a data do acontecimento. O campo de atualização Atom (`updated`) não substitui publicação.
- Notícias sem data de publicação são mantidas com atualidade não confirmada e zero pontos de atualidade; nenhuma data é inventada.
- Pontuação: até 40 pontos de atualidade (decaimento linear na janela), 35 por palavras-chave de afinidade temática ou 20 pela categoria editorial da fonte, até 25 pela confiabilidade configurada. Total de 0 a 100. É uma heurística, não uma avaliação por IA.
- Categorias são inferidas por palavras-chave em português/inglês; sem correspondência, usa-se a categoria da fonte. A seleção não representa cobertura exaustiva, e a relevância deve ser revisada por uma pessoa.
- Duplicação é detectada por URL sem fragmento e parâmetros de rastreamento, ou título normalizado idêntico, em toda a base histórica. Parámetros que identificam a notícia são preservados. Títulos diferentes sobre o mesmo acontecimento podem passar; títulos iguais sobre acontecimentos distintos podem ser suprimidos. O primeiro item coletado é preservado.

## Execução diária

O coletor executa uma rodada e termina. Para coleta diária em uma máquina Linux permanente, configure no seu `crontab` (ajuste o caminho absoluto):

```cron
0 9 * * * cd /workspace/EVOA-News-Automation && .venv/bin/python -m evoa_news >> data/daily.log 2>&1
```

Crie antes a pasta `data` (`mkdir -p data`). O horário usa o fuso do servidor; datas dos relatórios usam UTC. Configure rotação do log. Cron não foi instalado/ativado automaticamente: máquinas de tarefas na nuvem podem ser encerradas e não garantem execução agendada. Para operação contínua, use um host ou agendador persistente com armazenamento do histórico. Nada é publicado por esse agendamento.

## Arquitetura e testes

- `evoa_news/collector.py`: transporte HTTP com timeout/limite de tamanho, RSS/Atom, normalização, classificação, histórico SQLite e exportação.
- `evoa_news/__main__.py`: interface de linha de comando.
- `evoa_news/editorial.py`: contrato `EditorialWriter` para futura geração de rascunhos por IA; nenhuma integração ou custo nesta versão. A futura implementação deve preservar fontes e exigir aprovação humana.
- `tests/test_collector.py`: fixtures RSS/Atom explicitamente **FICTÍCIAS**, usando `example.org`. Os testes não acessam a rede e não apresentam essas fixtures como notícias reais.

Teste a coleta real separadamente com o comando normal. Dados de teste nunca são usados como substituição automática em produção. Para validar sem afetar o histórico principal, use `--database /tmp/evoa-validation.sqlite3 --output /tmp/evoa-validation`.

Próximas evoluções: calibrar fontes e notas com a equipe editorial, melhorar agrupamento de notícias sobre o mesmo evento e integrar uma IA opcional para rascunhos, sempre sob revisão humana.
