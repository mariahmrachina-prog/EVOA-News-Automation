# V2 — resultado da primeira etapa

## Estado preservado

HEAD continua `8f08fbd25fabc2e4b8c4067dff42f3d340afad20` na branch `main`. A rodada começou com os dois documentos de diagnóstico/arquitetura não versionados; foram preservados. Não houve push, migração de esquema, substituição do banco ou exclusão de relatórios. Alterações desta etapa estão locais e ainda sem novo commit.

## Implementado

- Manuais editorial e factual com regras oficiais, estados de verificação, restrições e revisão humana.
- `evoa_news/storage.py`: backup consistente SQLite versionado, manifesto, checksum, contagens, verificação e restauração somente em destino novo; comandos CLI.
- Configuração operacional por `EVOA_DATABASE`, precedência de `--database`, e backup por `EVOA_BACKUP_DIR`; padrão da v1 preservado.
- Regras de exclusão Git para bancos/sidecars e credenciais locais. Isso previne inclusão acidental pelos padrões, mas não substitui revisão de segurança antes de commit.
- Testes de armazenamento sem acesso a contas externas ou dados de produção.

## Evidências executadas em 20/10/2026

- `python -m unittest discover -s tests -v`: 23 testes aprovados (12 da coleta e 11 de armazenamento).
- Testes incluem WAL confirmado, versionamento, arquivo corrompido, origem ausente/inválida, caminho de manifesto indevido, falha de restauração, destino existente, configuração por variáveis e CLI completa.
- `pip check`: dependências consistentes; nenhuma dependência nova instalada nesta etapa.
- Banco original: 42 artigos, três execuções; backup e restauração reais conferidos com `integrity_check` e contagens.
- Manifesto do backup real: `/workspace/evoa-preservation/v2-backups/history-20261020T133820492576Z-6139ceb8b77a40ab974ae2f5853fd433.sqlite3.json`.
- Restauração real: `/workspace/evoa-preservation/v2-restored.sqlite3`.
- Coleta real na cópia restaurada, às 10:38:41 de São Paulo (13:38:41 UTC): quatro fontes lidas sem erro, zero itens novos; 20 duplicados TechCrunch, sete MIT, 14 Ars. Itens antigos foram ignorados, inclusive os sete VentureBeat. O banco original não recebeu essa execução de validação.
- Resultados da validação: `/workspace/evoa-preservation/v2-validation-output/2026-10-20T133841Z-y_8kgwdc/`.
- Nenhum conteúdo fictício foi apresentado como notícia real.

## Pendências e limites

Backup e restore foram locais; não há comprovação de persistência independente do Codex. Não há criptografia de backup implementada nem sincronização externa. Volume da máquina própria, OAuth, Drive/Sheets e restauração a partir do Drive não foram configurados/testados.

Não há adaptador Google executável ou teste simulado de integração ainda; há apenas contrato técnico e inventário para a próxima etapa. Nenhum recurso foi criado/modificado na conta. A lista será apresentada para aprovação antes de qualquer operação externa. Não foram solicitadas credenciais no chat.

Extração estruturada de fatos, rascunhos com IA, validação editorial automática, curadoria, aprendizado e montagem semanal seguem pendentes. As regras estão documentadas, não implementadas nem alegadas como prontas. Não há agendamento, publicação ou envio ativados.

## Próximo conjunto de implementação

1. Adaptadores Drive/Sheets com transporte simulado: planejamento de recursos, fila incremental idempotente, importação de decisões, proteção de edições humanas e testes de falha/reconciliação. Nenhum acesso externo antes de aprovação; OAuth será configurado de forma segura na máquina própria.
2. Migrações com backup para IDs, fatos/evidências e versões de rascunhos/avaliações, preservando dados v1. Testar migração e restauração em cópia.
3. Provedor de redação configurável e validador dos dois parágrafos/815 caracteres/CTA; modo sem IA e insuficiência explícita. Somente ativar provedor pago após estimativa e autorização; medir piloto limitado antes de processar todos.
4. Curadoria e ranking explicável com ajuste/validação separados; depois composição semanal e LinkedIn apenas como rascunhos.
