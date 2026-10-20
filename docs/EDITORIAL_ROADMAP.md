# Evolução editorial — plano para revisão

Este documento é um projeto de evolução, não uma afirmação de funcionalidades implementadas. A versão 1 mantém sua coleta, pontuação, SQLite e exportação. Nenhum envio, publicação ou agendamento será ativado nesta etapa.

## Fluxo proposto

Coleta → registro da origem e evidências → rascunho de cada item elegível → verificação de suporte por afirmação → fila de curadoria ordenada → decisão humana → seleção da edição semanal → exportação de rascunho.

Elegibilidade deve depender de janela de publicação configurável, assuntos e permissões da fonte, nunca de nota mínima. Notícias sem data ficam explicitamente identificadas, seguindo a política atual. Pontuação apenas ordena. O limite `--top` atual afeta o relatório Markdown, não a coleta/CSV; na evolução não limitará a geração de rascunhos nem a fila. Todas as notícias elegíveis terão rascunho, inclusive com nota baixa. Se não houver evidência suficiente, o rascunho exibirá a limitação sem completar fatos por inferência.

## Módulos e responsabilidades

| Módulo proposto | Responsabilidade e critério de aceite |
| --- | --- |
| collection | Adaptar o coletor existente, conservar IDs estáveis, publicação, primeira coleta, origem e logs de falha; testar três editores independentes. |
| evidence | Guardar trechos permitidos e afirmações vinculadas a URL, localização, data de acesso e hash do conteúdo; distinguir publicação de data do evento. Não copiar matéria integral sem permissão. |
| drafting | Criar rascunho para todos os itens elegíveis. Começar com montagem extrativa de título e trechos atribuídos, identificada como rascunho; regras editoriais versionadas. IA opcional só depois de exemplos editoriais e autorização de custos. |
| verification | Mapear cada afirmação à evidência e marcar suportada, contradita ou não verificada. Similaridade e pontuação não provam veracidade; suporte em uma fonte não equivale a confirmação independente. Sem suporte, bloquear aprovação para publicação e exigir revisão. |
| curation | Streamlit, filtros, texto, evidências, links e decisão humana; validação no servidor e proteção de acesso. |
| feedback | Histórico imutável de avaliações e revisões, motivos padronizados e comentários livres. Não sobrescrever decisões antigas. |
| recommendation | Ranking explicável por categoria, fonte e temas, com versão, fatores e conjunto de dados usados. Não suprimir itens. |
| weekly | Seleção manual de aprovadas, versão congelada da edição e exportação Markdown. Aprovar notícia não autoriza envio/publicação de edição. |

## Estrutura de dados proposta

Migrar com backup verificado, migrações versionadas e reversão testada. Não recriar ou apagar o SQLite existente. Preservar artigos e execuções atuais; gerar IDs novos com tabela de correspondência para URLs legadas.

| Entidade | Campos essenciais |
| --- | --- |
| articles | id estável, title, category, source_id, canonical_url única, feed_url, published_at anulável, event_at anulável e evidência específica, collected_at, current_status (pending/approved/rejected) |
| sources | id, nome, domínio, feed, nota de confiabilidade, política de uso, data de revisão da permissão |
| evidence | id, article_id, URL, retrieved_at, published_at, trecho permitido ou fato extraído atribuído, localizador, hash, tipo de conteúdo, permissão/licença e limitações |
| claims | id, article_id, texto da afirmação, status de suporte, responsável e data da verificação |
| claim_evidence | claim_id, evidence_id, relação (suporta/contradiz), observação; relação muitos para muitos |
| drafts | id, article_id, texto, versão, created_at, regra/modelo e versão do prompt, evidence_ids; preservar revisões |
| evaluations | id, article_id, draft_id, status, motivo padronizado, comentários editoriais, evaluated_at, reviewer_id; eventos anexados sem sobrescrita |
| scores | id, article_id, score 0–100, fatores, regra/modelo_version, feature_snapshot, scored_at; separar score base e personalizado |
| ranker_versions | versão, configuração, IDs/hash do conjunto de ajuste, cutoff, versão das features, created_at |
| recommendation_impressions | article_id, ranker_version, posição, shown_at; registra exposição para investigar viés das avaliações |
| evaluation_splits | article/event_group_id, finalidade (ajuste/validação), atribuição e cutoff; grupos de mesmo evento nunca cruzam conjuntos |
| evaluation_runs | versão candidata e base, período, IDs avaliados, métricas, tamanho da amostra, intervalo de incerteza e decisão de adoção |
| editions / edition_items | semana, versão, itens e ordem escolhidos manualmente, responsável, aprovação específica da edição |

Status corrente pode ser uma projeção do último evento de avaliação; histórico é a fonte de verdade. Comentários e identidade do editor são dados privados e não entram no Git, logs públicos ou prompts externos sem autorização.

## Recomendação gratuita e explicável

Começar sem personalização, com a regra atual como base. Depois de haver feedback suficiente, calcular preferências por categoria, fonte e tema usando taxa de aprovação com suavização Beta(2,2): (aprovações + 2)/(avaliadas + 4). Pendentes não contam como rejeição. Centralizar em 0,5 e limitar cada contribuição e o ajuste total (por exemplo ±15 pontos); registrar contagens e contribuição por fator em cada recomendação. Poucos exemplos produzem ajuste pequeno. Não usar o nome do autor da avaliação ou texto da decisão como atributo da notícia. Sem nota de corte e sem treinamento complexo.

Avaliação periódica será uma ação manual no início, sem agendamento: usar validação temporal por grupos de acontecimento. Ajustar somente em decisões anteriores ao cutoff; congelar a versão e suas features antes de observar decisões do período seguinte. Notícias duplicadas/sindicadas ficam no mesmo grupo. Não reutilizar validação para ajustar pesos e alegar ganho no mesmo conjunto; uma nova candidata precisa de um período futuro ainda não usado.

Comparar ranking base e personalizado nos mesmos itens avaliados usando Precision@10, NDCG@10 e cobertura/diversidade de fontes/categorias. Documentar tamanho da amostra, quantidade de aprovadas/rejeitadas e bootstrap por grupo de evento para incerteza. Só adotar se houver ganho sustentado e cobertura aceitável definidos previamente; caso contrário manter base. Sem decisões suficientes ou com amostra apenas dos itens mais bem ranqueados, declarar evidência insuficiente. Oferecer avaliação de uma pequena amostra aleatória de posições inferiores para reduzir viés de exposição; nunca aprovar automaticamente. Avaliação offline não comprova qualidade factual.

## Interface Streamlit proposta

Tela diária com tabela completa, ordenação e filtros por publicação/coleta, assunto, nota e status. Detalhe com rascunho, fonte original e painel de afirmações/evidências. Aprovar/rejeitar com motivo rápido (aderência, impacto, novidade, fonte, duplicidade, fora do tema) e comentário opcional; revisão de decisão gera novo evento. Abas de histórico aprovado, recomendações com fatores explicados e montagem semanal. Não renderizar HTML não confiável de feeds. Usar consultas parametrizadas, transações, autenticação e autorização; serviço privado até controle de acesso estar configurado. Proteger contra edição concorrente com número de versão. Nenhum botão de envio automático.

## Armazenamento: pré-requisito para uso editorial

O SQLite atual é local e ignorado pelo Git. Snapshot do ambiente e Git bundle não são backup contínuo das decisões. Não começar avaliações reais dependendo apenas do ambiente Codex.

Opção inicial: SQLite em volume persistente de máquina própria/servidor permanente, com um escritor, permissões restritas e backup remoto criptografado. Não usar pasta de sincronização ou filesystem de rede como banco ativo. Alternativa para múltiplos usuários: PostgreSQL gerenciado com TLS, autenticação, papéis mínimos e backups; planos gratuitos podem ter quotas, pausa e retenção limitada. Provedor e orçamento ainda não foram escolhidos. Não há credencial externa de banco/backup identificada nesta execução.

Usar `sqlite3.Connection.backup` (não cópia simples do arquivo aberto), verificar `PRAGMA integrity_check`, checksum, contagens e restauração em banco separado. Para PostgreSQL, usar backup consistente suportado pelo provedor/pg_dump e testar restore. Proposta inicial: backup após sessão editorial e diário em host persistente, sete cópias diárias e quatro semanais, RPO 24 h e RTO 4 h; são metas a validar, não garantias implementadas. Antes de fechar a sessão temporária, exportar backup por canal seguro para armazenamento independente e testar restauração. Segredos apenas em configuração segura, nunca neste documento. Nenhuma rotina agendada foi ativada.

## Sequência e custos

1. **Acesso real e preservação:** validar RSS de três editores e resultados, backup local consistente e cópia externa. RSS e bibliotecas gratuitos; persistência externa depende do serviço escolhido. A cópia externa é o bloqueio antes de decisões de produção.
2. **Dados e evidências:** migrações e testes de restauração/deduplicação; só conteúdo permitido. Python/SQLite gratuitos; exige volume persistente ou PostgreSQL.
3. **Rascunhos e segurança:** redação extrativa para todos, evidências por afirmação, revisão humana. Sem APIs pagas. Redação generativa local exigiria hardware e avaliação próprios; APIs têm custo variável e ficam fora do escopo inicial.
4. **Curadoria:** Streamlit gratuito e testes do ciclo decisão/histórico, controle de acesso e concorrência. Hospedagem pode ter custo; camada gratuita exige verificar persistência e privacidade.
5. **Recomendação:** contagens explicáveis e avaliação temporal separada; sem custo de API. Depende de decisões reais e amostra suficiente, sem promessa antecipada de ganho.
6. **Edição semanal:** seleção e exportação manual, com aprovação específica. Nenhum envio/publicação ou automação nesta execução.

Escolhas que faltam antes da implantação: destino persistente e backup, número de usuários e acesso, exemplos do padrão editorial EVOA e política de elegibilidade. Elas não impedem diagnóstico/testes locais, mas impedem alegar que a operação editorial em produção está pronta.

## Decisão de armazenamento confirmada

O usuário escolheu SQLite em máquina própria, com volume persistente e backup externo. Esta passa a ser a arquitetura inicial; PostgreSQL fica como alternativa futura para concorrência maior. Ainda falta identificar a máquina, o caminho absoluto do volume persistente e o destino externo de backup. Não foi provisionado armazenamento nem transferido qualquer banco para fora do Codex.

Na implantação: manter um escritor por vez, usar permissões restritas no diretório do banco, criar backups consistentes com a API SQLite, criptografar a cópia externa e testar restauração. A aplicação deve receber explicitamente o caminho persistente por `--database`; não usar o caminho temporário do Codex como banco de produção. Transferir uma cópia consistente, conferir checksum/integridade e contagens no destino e preservar o original até validar a migração. Agendamento e publicação continuam desabilitados até autorização específica.
