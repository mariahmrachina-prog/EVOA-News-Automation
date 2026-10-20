# Conectar Google no Windows — preparação implementada

## Estado e recursos

Raiz oficial configurada em `config/google.json`: `1in_94_e2fqQ878Xc3dG4vxq1BywnSSqM`. O programa reutiliza as subpastas existentes; não cria pastas, não altera, move ou exclui arquivos. Nomes são comparados ignorando acentos/maiúsculas e espaços repetidos; múltiplas correspondências interrompem a seleção. IDs descobertos ficam em `data/google-folders.json`.

O código oficial Drive v3 e OAuth está implementado, com testes simulados. Nenhuma autenticação Google real, listagem da conta, upload ou leitura Sheets da conta foi feita nesta execução. Instalar SDK e construir seu schema local não valida permissões remotas.

## 1. Preparar projeto e dados na máquina própria

Use Python 3.12+ e abra PowerShell no diretório do projeto, fora da pasta sincronizada do Drive. O commit remoto ainda pode não conter as alterações locais: transfira os arquivos desta implementação por um canal seguro ou integre-os ao repositório somente após autorizar o push. Não transfira `.venv`; recrie-a. O Git não contém o banco de 42 notícias: transfira separadamente um backup consistente e seu manifesto e teste a restauração, conforme `STORAGE_AND_GOOGLE.md`.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-google.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\EVOANews\oauth"
```

Use pasta privada local para banco e journal, não dentro do Drive:

```powershell
New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\EVOANews\data"
$env:EVOA_DATABASE = "$env:LOCALAPPDATA\EVOANews\data\history.sqlite3"
$env:EVOA_BACKUP_DIR = "$env:LOCALAPPDATA\EVOANews\backups"
```

Essas variáveis valem para a sessão PowerShell; reaplique ao abrir outra. Restaure o backup para esse destino inexistente antes de coletar, se quiser manter o histórico. Não use banco ativo em pasta sincronizada, mesmo que o Drive apareça como disco.

## 2. Configurar OAuth no Google Cloud

1. Acesse `https://console.cloud.google.com/` e crie/selecione um projeto seu. Não é necessário contratar API paga para este cliente; quotas e cota de armazenamento Google continuam aplicáveis.
2. Em **APIs e serviços → Biblioteca**, habilite **Google Drive API** e **Google Sheets API**.
3. Configure a tela de consentimento no **Google Auth Platform** (nome, e-mail de suporte, público). Para uso pessoal em teste, escolha público externo e adicione seu e-mail como usuário de teste; organizações podem oferecer público interno. Os rótulos do console podem variar.
4. Em acesso a dados, configure os escopos `https://www.googleapis.com/auth/drive.metadata.readonly` e `https://www.googleapis.com/auth/drive.file`.
5. Crie um **ID de cliente OAuth** do tipo **Aplicativo para computador/Desktop app**, não aplicativo Web nem conta de serviço.
6. Baixe o JSON desse cliente e salve como `%LOCALAPPDATA%\EVOANews\oauth\client_secret.json`. Não envie o JSON, tokens, códigos ou senhas pelo chat e não os coloque no Git.
7. Restrinja a pasta ao seu usuário pelo controle de acesso do Windows. O código não configura ACL do Windows nem criptografia de token: a proteção do perfil e do disco é necessária. Tokens são gravados fora do projeto. Uma aplicação externa em modo teste pode exigir nova autenticação periodicamente (tipicamente sete dias para esses escopos); políticas Workspace podem bloquear consentimento.

**Permissões:** `drive.metadata.readonly` permite descoberta de nomes/metadados de arquivos já existentes e é mais abrangente que a pasta do projeto. O aplicativo filtra a raiz, mas o escopo OAuth não é limitado a essa raiz. `drive.file` permite operar apenas arquivos criados/abertos/autorizados para o aplicativo. Não solicitamos `drive` irrestrito nem um escopo amplo de escrita Sheets. Se esse acesso de metadados não for aceitável, interrompa o consentimento; uma integração com Google Picker será necessária para selecionar itens individualmente.

## 3. Autenticar e descobrir, sem modificar a conta

```powershell
.\.venv\Scripts\python.exe -m evoa_news.google_drive auth
.\.venv\Scripts\python.exe -m evoa_news.google_drive discover
```

O primeiro comando abre o navegador local e recebe o retorno OAuth em uma porta loopback efêmera, usando PKCE. Faça login e revise as permissões. Ele grava `token.json` no mesmo diretório privado do cliente; não imprime o token. Não execute esse fluxo em servidor público ou no Codex em nome da sua sessão Windows.

O segundo verifica a pasta raiz e lista subpastas, paginando todos os filhos diretos. Confira `data/google-folders.json`: IDs em `folders`, problemas em `issues`. Se faltar pasta ou houver nome ambíguo, não será criada cópia automática. Não compartilhe o token; para diagnosticar descoberta, basta informar nomes/erros e IDs não secretos necessários.

A pasta precisa estar acessível pela conta escolhida. Em caso de 403/404, verifique conta, compartilhamento, API habilitada, escopos e política organizacional. **A descoberta por metadados não comprova permissão de escrita `drive.file` numa pasta preexistente.** Para esse caso, pode ser necessário autorizar a pasta por Google Picker/“Abrir com”; essa UI de seleção não foi implementada. Não amplie para acesso irrestrito para contornar falhas. Antes de upload real, validar essa permissão em teste expressamente aprovado; se o Drive recusar, interromper e implementar o fluxo de seleção autorizado.

No ambiente remoto, chamadas Google exigem os destinos oficiais pertinentes, como `accounts.google.com`, `oauth2.googleapis.com`, `www.googleapis.com` e `sheets.googleapis.com`. Eles não foram adicionados automaticamente à política do Codex. No Windows, respeite as regras de firewall/proxy da sua rede. Não desative TLS ou altere rotas para contornar bloqueios.

## 4. Preparar painel e demonstração local

```powershell
.\.venv\Scripts\python.exe -m evoa_news.sheets
.\.venv\Scripts\python.exe -m evoa_news.drafting --output output\demonstracao --validate-links
```

O primeiro gera somente `data/sheets-plan.json`. O segundo lê o banco operacional sem modificá-lo e gera `queue.json`, `editorial.csv` e `demo.md` num diretório novo. O CSV contém as 21 colunas planejadas (inclusive dois parágrafos, provedor e campos humanos), todos os itens, pendências e evidências. Pode ser importado manualmente por você, se desejar; isso não é sincronização com Sheets.

**Planilha proposta:** `Painel Editorial EVOA News`, aba `Noticias`, na subpasta `03 - Curadoria Editorial`. Ainda não foi criada. Antes de implementarmos/executarmos sua criação na conta, é necessária sua aprovação ou o ID de uma planilha existente que deseja reutilizar. O adaptador atual lê uma planilha indicada (`python -m evoa_news.sheets --spreadsheet-id ID`), mas não cria nem escreve planilhas. A aba precisa se chamar `Noticias`; a conta e o aplicativo precisam ter acesso ao arquivo via `drive.file`. Importação de decisões e upsert das colunas geradas continuam pendentes.

## 5. Uploads futuros: somente após aprovação específica

Nenhum comando abaixo foi executado na sua conta. Antes de autorizar, revise arquivos, conteúdo e pastas de destino. O sinalizador é uma barreira operacional; não substitui sua aprovação no contexto da tarefa.

```powershell
# Exemplo de relatório NOVO em 07 - Relatorios, sem atualizar arquivos existentes:
.\.venv\Scripts\python.exe -m evoa_news.google_drive upload output\demonstracao\demo.md --kind reports --journal "$env:LOCALAPPDATA\EVOANews\data\google-sync.sqlite3" --approve-upload

# Cria backup LOCAL; não envia nada:
.\.venv\Scripts\python.exe -m evoa_news.storage backup

# Após aprovar o par de arquivos, substitua MANIFESTO pelo caminho retornado:
.\.venv\Scripts\python.exe -m evoa_news.google_drive upload MANIFESTO --kind backups --journal "$env:LOCALAPPDATA\EVOANews\data\google-sync.sqlite3" --approve-upload
```

Mapeamento de `--kind`: `collected`, `drafts`, `curation`, `weekly`, `evidence`, `backups`, `reports`. Envie CSV de notícias para collected, rascunhos/queue para drafts, evidências para evidence e relatórios para reports. O comando de backup verifica manifesto, hash e integridade, envia snapshot fechado e só depois o manifesto. Nunca envie diretamente o banco operacional.

Sincronização é incremental de arquivos imutáveis: mesma pasta/nome/conteúdo é reconciliada, não reenviada; versão alterada cria outro arquivo e preserva a anterior. ID remoto pré-alocado e journal persistido antes da escrita permitem retomar resposta perdida. Há reconciliação por metadados mesmo se o journal desaparecer. Não apagar metadados ou editar manualmente arquivos gerenciados: conflitos interrompem o envio. Um único escritor por vez; não há garantia de exclusão mútua entre duas máquinas.

Em falha, não apague o journal; repita o comando depois de resolver a causa. GETs têm retries limitados do SDK; escrita tem zero retry automático e é retomada por nova execução com o mesmo ID. Nenhum update/delete é chamado. Arquivos existentes sem metadados do aplicativo não são considerados gerenciados nem alterados. O journal deve ficar no disco persistente local. Snapshot e manifesto são um par; falha no segundo deixa apenas snapshot no Drive, e a retomada não duplica o primeiro. Validação real de recuperação no Drive ainda depende de teste aprovado após OAuth.

Para revogar, remova a conexão nas permissões da Conta Google e exclua o token local. Não envie credenciais para suporte.

## 6. Redação sem API paga

Modo padrão: extrativo determinístico, sem IA, mantendo o idioma do RSS e trechos literais. Não é uma redação portuguesa final no padrão EVOA. Apenas registros com duas frases completas e conteúdo mínimo recebem rascunho; todos os demais ficam pendentes. A heurística de suficiência não verifica verdade nem licença. Os rascunhos trazem evidências, hash, origem, status e limitações.

Para testar IA gratuita em máquina própria, instale e avalie um modelo local compatível com Ollama (licença e hardware dependem do modelo). Nenhum modelo foi baixado ou testado nesta execução. Depois de instalado e servido localmente:

```powershell
$env:EVOA_OLLAMA_MODEL = "NOME_DO_MODELO_LOCAL_JA_INSTALADO"
.\.venv\Scripts\python.exe -m evoa_news.drafting --provider ollama --ai-limit 5 --validate-links --output output\piloto-ia
```

O provedor lê ambos os manuais e usa somente as evidências fornecidas. Não usa API paga, nem envia dados a provedor externo pelo código; requer servidor local na porta 11434. Valida estrutura, tamanho e URL; não valida semanticamente toda afirmação. Saída de IA permanece parcialmente sustentada e exige revisão humana. Itens fora do piloto continuam pendentes, nunca eliminados por nota. O ranking só ordena. Revise o comportamento/licença do servidor/modelo que instalar; não ativamos processamento diário.

Registro de feedback local em `evoa_news.feedback` conserva decisões e edições imutáveis, motivos padronizados e versão do ranking. Ainda não há importador Sheets nem algoritmo que use essas decisões para aprender; armazenar eventos não significa aprendizado. Escrita por IA e recomendação personalizada precisam de avaliação separada antes de alegar melhoria.
