# Manual editorial EVOA News — versão 1

## Missão e fila

Informar empreendedores, lideranças, gestores, startups e profissionais de tecnologia sobre inovação, tecnologia e negócios, com linguagem simples, moderna, direta, curiosa, leve, profissional, natural e jornalística. Entusiasmo sem exagero; sem conclusões didáticas artificiais, sensacionalismo ou promessas de impacto não demonstradas. Evitar “revolucionário”, “imperdível”, “vai mudar tudo” e “isso vai transformar o mercado” sem evidências.

Cobrir IA, inovação, startups, empreendedorismo, negócios/mercado, big techs, investimentos, produtos, transformação digital, automação e tendências globais. Buscar diversidade de fontes brasileiras/internacionais e empresas de portes diferentes. Prioridade para publicações em 24 horas, com janela semanal de até sete dias. Separar publicação, atualização e acontecimento; atualização não torna antiga notícia em lançamento novo.

Todos os itens elegíveis entram na fila; nota serve exclusivamente para ordenar. Todos com evidência suficiente devem receber rascunho, independentemente da pontuação. Itens insuficientes permanecem na fila com limitação explícita, sem texto especulativo. A implementação desses novos fluxos ainda está pendente.

## Notícia individual

- Título com emoji do assunto, específico, atraente e fiel à novidade. Negrito estratégico em nomes, números e conceitos. Não acrescentar números ou promessas para gerar interesse.
- Exatamente dois parágrafos principais. Corpo de no máximo **815 caracteres**, incluindo espaços, pontuação e separação entre parágrafos; título e CTA não contam. O validador futuro contará a string Markdown armazenada (incluindo marcadores de negrito e dois caracteres de quebra entre parágrafos), evitando ambiguidade entre formatos.
- Primeiro parágrafo: acontecimento, envolvidos, novidade e números confirmados relevantes. Segundo: contexto, antecedentes, desdobramentos ou consequências sustentadas. Não repetir informação nem impor a fórmula “o que aconteceu/por que importa”.
- Preferir informação concreta; não preencher espaço para atingir tamanho. Se não houver fatos para dois parágrafos, sinalizar insuficiência em vez de completar.
- CTA curta e específica sobre o conteúdo da matéria original, com URL real e validada. Evitar “Clique aqui”, “Saiba mais” ou “Confira” isolados. A validação de link deve registrar URL final, status HTTP e data de acesso; sintaxe válida não equivale a conteúdo verificado. Não contornar recusas de acesso.
- Guardar título original, fonte, URL, publicação, categoria, fatos/evidências, versão do rascunho, status factual, nota e justificativa. Se o provedor não for IA, não rotular texto como “produzido por IA”.

Não transformar declarações, rumores ou previsões em fatos confirmados. Conteúdo RSS é atribuído à fonte; não comprova verdade independente. Conteúdo estrangeiro pode ser traduzido sem adicionar fatos, com revisão de números, nomes e sentido. Trechos integrais só quando houver permissão.

## Curadoria e aprendizado

Status: pendente, aprovada ou rejeitada. Preservar cada decisão e revisão como evento datado, com notícia/rascunho, responsável, motivo, comentários e versão do ranking. Guardar texto original produzido e todas as edições humanas de título, corpo e CTA, sem sobrescrever versões.

Motivos padronizados de aprovação:

- Relevante para empresários e lideranças.
- Grande impacto no mercado.
- Novidade tecnológica significativa.
- Aplicação prática interessante.
- Tema estratégico para a EVOA.
- Informação exclusiva ou pouco explorada.

Motivos padronizados de rejeição:

- Pouco relevante para o público.
- Notícia repetida.
- Informação superficial.
- Tema excessivamente técnico.
- Notícia desatualizada.
- Fonte pouco confiável.
- Assunto já abordado na newsletter.

Comentários livres complementam esses motivos. Armazenar decisões não significa aprendizado: uma rotina futura deverá usar somente dados de ajuste e comparar ranking personalizado com base em validação temporal separada, conforme o plano de arquitetura. Edições humanas podem gerar exemplos de estilo apenas depois de revisão; não promover alterações isoladas a regras factuais ou de escrita automaticamente.

## Edição semanal

Gerar somente com itens explicitamente selecionados e aprovados; mudanças posteriores no texto exigem nova verificação. Aprovação de notícia não autoriza publicação da edição. Estrutura:

```text
[NÚMERO]ª Edição
Sua dose semanal de inovação! ☕
The future is NOW.
Bom dia, comunidade EVOA!
```

1. **ABERTURA:** um ou dois parágrafos curtos conectando as selecionadas numa narrativa, não uma lista.
2. **SUMÁRIO:** apenas títulos, preservando emojis e negritos.
3. **MUNDO:** todas as notícias externas selecionadas, com dois parágrafos, limite e CTA.
4. **COMUNIDADE:** iniciativas EVOA (eventos, Clube EVOA, Batch, imersões, treinamentos, oportunidades e projetos), mesmo padrão com possível foco em conversão. Datas, inscrições, vagas e condições precisam de evidência institucional confirmada.
5. **ENCERRAMENTO:** texto aprovado abaixo.

```text
Até a próxima!

Esperamos que você tenha curtido esta edição da EVOA News. Continue acompanhando as redes da EVOA para ficar por dentro das principais novidades de tecnologia, inovação, negócios e da nossa comunidade.

Estamos juntos nessa jornada empreendedora. Se tiver sugestões, notícias ou histórias que merecem aparecer por aqui, envie para a gente.

Um grande abraço e excelentes negócios!

Deixe sua opinião: [LINK DO FORMULÁRIO]
```

Sem formulário cadastrado, marcar campo pendente no rascunho; nunca inventar URL ou exportar placeholder como link válido. Não inventar notícias para preencher Comunidade; sinalizar seção sem material aprovado.

## Divulgação LinkedIn

Rascunho com três a cinco parágrafos curtos, abertura forte sustentada, conexão natural entre três ou quatro notícias e linguagem profissional/acessível, sem lista de manchetes. Encerrar com `Leia a [NÚMERO]ª edição da EVOA News: [LINK]`. Se faltar link ou notícias suficientes, indicar pendência, sem inventar. Nenhuma postagem automática.
