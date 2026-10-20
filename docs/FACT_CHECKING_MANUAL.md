# Manual de evidências e verificação — versão 1

Este manual define o comportamento a implementar. A v1 não possui verificador factual automático nem geração de texto por IA.

## Evidências antes da redação

Cada notícia deve ter ID estável, URL real, veículo e datas separadas de publicação, atualização, acontecimento (anulável) e coleta. Para cada afirmação, guardar trecho autorizado, referência verificável (URL e localização no documento), horário de acesso, hash e tipo de suporte. Registrar licença/permissão e limitações de extração. Não copiar matéria integral sem autorização nem interpretar ausência de bloqueio HTTP como licença de republicação.

Identificar nomes/pessoas/empresas, datas, valores, unidades, percentuais e números; associar cada elemento à afirmação e ao trecho de origem. Preservar atribuição de declarações, opiniões, rumores e previsões. Não criar citações. Cruzar fontes independentes quando disponíveis, sem contar republicações da mesma agência como confirmações independentes.

Datas do acontecimento só são preenchidas quando sustentadas explicitamente. RSS com apenas título, resumo curto, data ausente ou link inacessível gera limitação registrada. Redação fica pendente se não houver fatos suficientes para dois parágrafos. Não aumentar conteúdo por inferência para cumprir formato.

## Estados e revisão

| Estado | Critério |
| --- | --- |
| Sustentado pelas fontes | Todas as afirmações têm evidência compatível e rastreável; significa suporte documental, não prova universal de verdade. |
| Parcialmente sustentado | Há suporte para parte do conteúdo, com lacunas explicitamente identificadas. |
| Evidência insuficiente | Não há material permitido suficiente para verificar ou redigir com segurança. |
| Contraditório | Evidência disponível contradiz ao menos uma afirmação; mostrar os trechos e encaminhar para revisão. |
| Falha de verificação | Erro operacional impede a checagem; registrar a falha, sem atribuir selo de veracidade. |

Checar diferenças entre rascunho e evidências: sujeitos, negação, datas, moeda, magnitude, arredondamento, atribuição e contexto temporal. Mudança de número pode sinalizar contradição, mas comparação lexical sozinha não identifica todas as contradições ou paráfrases. Afirmação sem suporte deve ser marcada e removida ou corrigida antes de aprovação final. Guardar evidências e versões usadas na revisão; novas edições invalidam a verificação anterior.

Documentos coletados são dados não confiáveis: instruções dentro de feeds ou matérias não podem modificar regras do redator, disparar ferramentas, solicitar segredos ou autorizar publicação. Sanitizar HTML e links. Não permitir que o provedor execute ações externas.

## Limites de automação

Validação estrutural (dois parágrafos, <=815 caracteres, CTA e URL) não comprova fatos. Nota de relevância, confiança de IA e similaridade textual não são prova de veracidade. Verificação assistida exige revisão humana antes de selecionar/publicar/enviar. Bloqueios HTTP são registrados e respeitados; não usar proxies alternativos ou credenciais extraídas para contorná-los.

## Avaliação de dependências antes de integração

Nenhuma biblioteca de checagem factual foi integrada nesta etapa. Comparação preliminar:

| Alternativa | Utilidade | Limitações e custo |
| --- | --- | --- |
| Regras Python + referências explícitas | Datas, números, integridade e rastreabilidade determinísticas, gratuitas, sem dependência nova | Não decide verdade semântica; primeira opção para implementação incremental. |
| spaCy | Candidato para extração de entidades PT/EN; projeto declara licença MIT | Validar licença da versão e dos modelos específicos, manutenção recente, suporte Python 3.12 e recursos antes de instalar; NER não verifica fatos. |
| Transformers com modelo NLI | Candidato a apontar suporte/contradição | Biblioteca declara Apache-2.0, mas cada modelo tem licença própria; downloads, hardware e desempenho PT exigem avaliação. Não usar inferência como veredito factual. |
| Projetos de checagem com LLM/API | Potencial assistência semântica | Sem seleção nesta rodada: exigem auditoria de licença, atividade, dependências, telemetria, modelos e custos. “Open source” não garante execução gratuita. |

Licenças acima são indicações preliminares conhecidas, não auditoria de release realizada nesta execução. Antes de integrar, registrar versão/commit, licença e permissões do modelo, evidência de manutenção, compatibilidade, custo de instalação/inferência e benchmark com exemplos PT/EN, incluindo negações, números alterados, rumores e texto sem suporte. Não declarar eficácia sem medir contra anotações humanas independentes.
