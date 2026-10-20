# Armazenamento local seguro e próxima integração Google

> Registro da primeira etapa. Para a implementação atual do cliente Drive, limites e autenticação, consulte `GOOGLE_WINDOWS.md`; as afirmações abaixo sobre adaptadores ainda não implementados refletem a etapa anterior.

## Implementado e testável agora

SQLite continua operacional local. O coletor aceita `EVOA_DATABASE` como caminho padrão; `--database` tem precedência. Sem configuração, mantém `data/history.sqlite3`. Isso configura um caminho, não provisiona volume nem torna o Codex persistente.

O módulo `evoa_news.storage` cria snapshots consistentes pela API SQLite, incluindo transações já confirmadas em WAL. Cria nomes versionados, arquivo com permissão 0600 em sistemas POSIX, manifesto com SHA-256, contagens por tabela e data UTC. Verifica integridade; restaura somente em destino novo e remove temporários em falhas. Nenhum arquivo operacional é sobrescrito, nenhuma cópia antiga é excluída automaticamente. O manifesto é escrito por último e identifica um backup completo. Cópias sem manifesto podem resultar de interrupção abrupta e não devem ser usadas como backup validado.

SHA-256 detecta corrupção acidental; não fornece autenticidade contra alteração conjunta de banco e manifesto. Backups não são criptografados pelo módulo. Disco cheio, falta de energia, host comprometido ou perda da máquina não são resolvidos por checksum. Proteja o volume, use criptografia de disco e cópia externa protegida. Restauração usa hard link local atômico sem sobrescrita; o filesystem de destino precisa suportá-lo, caso contrário falha de forma segura.

## Operação manual

Na máquina própria, escolha diretório privado em disco local persistente, fora de OneDrive/Dropbox/Google Drive sincronizados e fora de filesystem de rede. Um escritor por vez. Antes de usar dados reais, configure permissões do diretório e do banco existente para o usuário operador; não exponha o banco pelo servidor web. Nunca execute SQLite dentro da pasta sincronizada. Drive será apenas destino de snapshots fechados e exportações.

```bash
# Ajuste para um volume local realmente persistente da sua máquina.
export EVOA_DATABASE=/caminho/local-persistente/evoa/history.sqlite3
export EVOA_BACKUP_DIR=/caminho/local-persistente/evoa/backups

# Backup do banco v1 existente, sem alterar o original.
.venv/bin/python -m evoa_news.storage backup --database data/history.sqlite3 --directory data/backups

# Use o caminho do manifesto retornado pelo comando anterior.
.venv/bin/python -m evoa_news.storage verify data/backups/ARQUIVO.sqlite3.json
.venv/bin/python -m evoa_news.storage restore data/backups/ARQUIVO.sqlite3.json --destination /caminho/local-persistente/evoa/history.sqlite3

# Confirmar caminho e contagens antes de voltar a coletar.
.venv/bin/python -m evoa_news
```

Os nomes acima são placeholders de operação, não arquivos criados. O destino da restauração não pode existir; para substituir um banco operacional, pare os escritores, faça novo backup e planeje troca manual com possibilidade de reversão. Não remova arquivos WAL/SHM de um banco aberto. Não altere o caminho silenciosamente: coletar com um caminho vazio inicia histórico novo.

Backup posterior usa `python -m evoa_news.storage backup` com as variáveis configuradas. Teste restore em arquivo separado após cada mudança de esquema e periodicamente. Meta inicial proposta: backup após sessão editorial, RPO de 24 horas e RTO de quatro horas; ainda não medidos em máquina própria. Retenção proposta: sete diários e quatro semanais, sem exclusão automática nesta versão. Faça cópia externa de snapshot e manifesto, restrinja compartilhamento e teste recuperação a partir dessa cópia, não apenas do arquivo local.

## Google Drive e Sheets: pendentes

A escolha atual é máquina própria para banco ativo e Google Drive para cópias externas, relatórios, rascunhos e histórico exportado. Não há integração Google executável implementada nesta primeira etapa, OAuth configurado ou recurso criado na conta. Não confundir testes locais de backup com upload/restauração no Drive. A próxima etapa implementará adaptadores oficiais com testes simulados antes de conectar a conta.

Recursos propostos para aprovação futura, antes de qualquer criação/modificação externa:

```text
EVOA News Automation/
  01 - Noticias Coletadas/
  02 - Noticias Redigidas/
  03 - Curadoria Editorial/
  04 - Newsletters Semanais/
  05 - Fontes e Evidencias/
  06 - Backups/
  07 - Relatorios/
```

Uma planilha `Painel Editorial EVOA News` em Curadoria terá ID, publicação, coleta, categoria, título original, fonte, URL original, resumo factual, título/texto produzidos (com provedor identificado), CTA, relevância, evidências, estado factual, status editorial, motivo, comentários, texto editado e data da avaliação. Separar colunas geradas e humanas; preservar versões e conflitos. A integração não apagará edições humanas ao reexportar dados.

## Contrato técnico para a próxima etapa

- APIs oficiais Drive v3 e Sheets v4. Cliente OAuth de aplicativo instalado na máquina própria, navegador local e PKCE se suportado pela biblioteca selecionada; não executar fluxo de credenciais em chat. Client config e tokens fora do checkout, com permissões mínimas ou armazenamento seguro do sistema. Não registrar valores em logs.
- Tentar escopo `drive.file` limitado aos arquivos criados/selecionados pelo aplicativo, aceito também por endpoints Sheets pertinentes; confirmar compatibilidade no teste integrado. Não pedir acesso amplo a todo Drive por padrão. Não reutilizar autenticação GitHub como Google.
- Métodos separados de planejamento e aplicação: `plan_resources`, `ensure_resources`, `upload_snapshot`, `upsert_editorial_rows`, `pull_editorial_changes`. Aplicação somente após aprovação explícita da lista de recursos. Adaptador falso em testes não prova acesso ao Google.
- Registro local de sincronização com ID remoto, ID local, versão, hash, último sucesso e token/cursor. ID local estável em colunas e metadados de arquivo; nunca depender apenas de nome ou posição da linha.
- Chaves de idempotência por operação; antes de repetir upload/criação após timeout, reconciliar metadados remotos. Publicar snapshot e manifesto como par e marcar versão completa apenas após ambos; não sobrescrever backup anterior.
- Retentar 429/5xx com backoff limitado e jitter, respeitando Retry-After; 401/403 exigem diagnóstico/permissão, não loop. Falha parcial mantém fila local pendente. Não sobrescrever avaliação humana em conflitos: registrar e apresentar para resolução.
- Ao importar decisões, validar ID/status/motivo/timestamp e anexar evento de avaliação. Reimportação do mesmo evento deve ser inócua. Strings exportadas para Sheets devem ser valores RAW, evitando fórmulas de conteúdo externo.
- Custos: APIs têm quotas e termos; armazenamento consome cota da conta Drive e pode exigir plano pago conforme volume. Não contratar serviços. SQLite, regras locais e testes não exigem API paga. IA futura será opcional, desabilitada por padrão, com limite de notícias/tokens e estimativa antes de habilitar.

## Critérios de ativação externa

Escolher máquina/SO, volume local, conta e pasta de destino; implementar/testar adaptadores falsos; obter aprovação dos recursos; configurar OAuth fora do chat; testar pequena exportação e importação sem duplicação; testar upload e restore real de snapshot; só então considerar Google disponível. Até lá, backup externo é pendência explícita. Agendamento diário pode ser preparado depois, mas não será ativado automaticamente.
