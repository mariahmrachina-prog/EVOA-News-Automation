# Preparação Google e primeiro fluxo editorial — resultado

## Implementado

- Raiz oficial `1in_94_e2fqQ878Xc3dG4vxq1BywnSSqM` em `config/google.json`.
- Cliente oficial Drive v3 e OAuth Desktop com PKCE, navegador local Windows, token fora do checkout e atualização de token.
- Descoberta paginada de subpastas, registro dos IDs, detecção de faltantes/ambíguas, sem criar pastas.
- Upload de arquivos novos com aprovação explícita, snapshots imutáveis, chave por pasta/nome/hash, ID remoto pré-alocado, journal local e reconciliação após falha. Nenhum update/delete.
- Upload de backup aceita manifesto validado e envia snapshot consistente antes do manifesto. O banco ativo não é enviado pelo comando de backup.
- Plano Sheets com 21 colunas, CSV local completo e leitura oficial de planilha explicitamente indicada. Não há criação/escrita Sheets ou importação de decisões implementada.
- Redação extrativa gratuita com validação estrutural e evidências RSS rastreáveis; itens insuficientes continuam pendentes sem corte de nota.
- Provedor Ollama local configurável, com manuais, limite de piloto e revisão obrigatória; não foi executado com modelo real.
- API Python de feedback com eventos imutáveis, motivos, comentários, rascunho original, edições humanas e versão de ranking. Isso não treina nem melhora ranking/redação automaticamente.

## Validação executada

- 40 testes passaram; Google e provedor IA são simulados nos testes. Testes de coleta/backup anteriores preservados.
- Casos Google: paginação, acentos, pasta ambígua, aprovação ausente, repetição idempotente, timeout após criação, perda de journal, conflito remoto, nova versão preservando anterior e erro 403 respeitado.
- SDKs oficiais instalados; configuração PKCE e schemas locais Drive/Sheets carregados sem acessar a conta. `pip check` e `git diff --check` passaram.
- Banco original preservado com 42 artigos e três execuções; snapshot consistente adicional em `/workspace/evoa-preservation/google-preparation/`.
- As 42 notícias foram usadas como arquivo histórico de demonstração, sem alegar nova coleta atual. O modo extrativo produziu oito rascunhos e 34 pendências por insuficiência; todos os registros permanecem na fila.
- Oito links dos rascunhos responderam HTTP 200, registrados com data/hora e URL final; isso valida acesso, não verdade nem licença.
- Demonstração automática: `output/v2-google-demo-final/demo.md`; fila, CSV e evidências em `queue.json`, `editorial.csv` e `evidence.json`.
- Demonstração adicional de cinco rascunhos portugueses, redigidos pelo assistente nesta sessão a partir das mesmas evidências: `five-drafts-pt.md` e `five-drafts-pt.json`. Cada um tem dois parágrafos, com 323, 291, 405, 414 e 433 caracteres. São exemplos assistidos, NÃO saída testada de modelo automatizado. Evidências por parágrafo, publicação, fonte, link e limites ficam no JSON. Todos parcialmente sustentados e pendentes de revisão humana.

## Não realizado / bloqueios reais

Não existem cliente/token OAuth da conta configurados aqui. A pasta e seus IDs reais não foram consultados; seus conteúdos não foram modificados. OAuth Windows, upload, retomada real no Drive e leitura Sheets ainda dependem de autenticação e testes expressamente aprovados. Permissão metadata.readonly para descobrir não garante acesso drive.file à pasta existente: fluxo Picker pode ser necessário e ainda não foi implementado. Não ampliar escopos silenciosamente.

O plano da nova planilha precisa de aprovação ou indicação de uma planilha existente. Não existe sincronização bidirecional Sheets, ranking personalizado, aprendizado de escrita, extração semântica de fatos, verificação factual completa ou montagem semanal pronta nesta etapa.

Não há backup externo comprovado. Tokens não são criptografados pelo código; proteger ACL/perfil/disco no Windows. O banco/journal ativos devem ficar em disco local persistente, fora de pasta sincronizada. Upload incremental pressupõe um escritor; não há lock distribuído. Recuperação de falhas foi testada em simulação, sem prometer recuperação validada na conta.

HEAD permanece `8f08fbd`, com alterações locais da V2 sem novo commit. Nada foi enviado ao GitHub, agendado ou publicado. Nenhuma API paga foi usada.

## Próximo passo do usuário

Seguir `GOOGLE_WINDOWS.md`: instalar dependências na máquina própria, configurar APIs e cliente OAuth Desktop, guardar cliente fora do projeto, autenticar e executar descoberta somente leitura. Depois informar apenas resultado de descoberta/erros não secretos, sem tokens. Proposta de planilha: `Painel Editorial EVOA News`, aba `Noticias`, em `03 - Curadoria Editorial`, com campos listados em `data/sheets-plan.json`; aguarda aprovação antes da implementação/execução de criação remota. O primeiro upload também precisará de aprovação do arquivo e destino.
