# Rotina diária do Mapa das Ideias

Roteiro seguido pela rotina agendada no Claude Code, que roda duas vezes por dia
(carrossel de manhã, imagem avulsa à tarde) sem usar chave paga da API. O dono do
repositório autorizou esta rotina a gravar direto no branch `main`.

O formato do dia vem na mensagem que dispara a rotina: `carrossel` ou `imagem`.

## 1. Preparar

```bash
cd <pasta do repositório patricksouzapaiva-crypto/jogo>   # clone se não existir
git fetch origin main && git checkout main && git reset --hard origin/main
pip install -q -r requirements.txt
python -m assistente contexto --formato <FORMATO>
```

O comando `contexto` imprime o briefing completo: perfil, regras do guia, pilares, temas já
publicados (não repita), mundos visuais recentes (evite), estrutura dos slides, checklist e o
formato exato do `post.json`. **Siga o briefing à risca.**

## 2. Pesquisar

- Escolha o tema conforme o briefing (equilíbrio de pilares, livros conhecidos, sem repetir).
- Use as ferramentas de busca e leitura na web para confirmar **cada** fato, data, número e
  citação em fontes confiáveis. Descarte o que não conseguir confirmar.
- Nunca invente nada. Na dúvida, deixe de fora.

## 3. Escrever

```bash
python -m assistente nova-pasta --formato <FORMATO> --tema "<tema curto>"
```

O comando mostra a pasta criada (ex.: `posts/2026-10-08_092301_carrossel_dracula`). Nela, crie:

- `dossie.md`: o dossiê da pesquisa, com as URLs das fontes.
- `post.json`: o post, exatamente no formato mostrado no briefing (UTF-8, JSON válido).

## 4. Revisar e validar

Releia o post como editor-chefe, pelo checklist do briefing. Depois:

```bash
python -m assistente validar <pasta>
```

Corrija tudo o que o validador apontar e rode de novo até aparecer `OK: post pronto.`

## 5. Enviar

```bash
git add <pasta>/post.json <pasta>/dossie.md
git commit -m "Post do dia (<FORMATO>): <tema>"
git push origin main
```

Envie **só** a pasta do post novo; não mexa no código nem em outros posts. Se o push falhar por
rede, tente de novo (até 4 vezes, esperando 2, 4, 8 e 16 segundos). Se falhar porque o `main`
andou, faça `git pull --rebase origin main` e envie de novo.

## 6. Acompanhar e avisar o dono

O push dispara o workflow **Publicar posts** no GitHub, que gera as imagens, monta os slides e
publica no Instagram (se já estiver configurado).

1. Com as ferramentas do GitHub, acompanhe a execução de `publicar-posts.yml` do seu commit até
   terminar (costuma levar de 2 a 5 minutos; espere com um `sleep` em segundo plano, sem
   consultar sem parar).
2. Baixe o artefato `posts-prontos`, descompacte numa pasta temporária e olhe os slides.
3. Mande ao dono, numa mensagem só (com aviso no celular):
   - as imagens dos slides, em ordem;
   - a legenda pronta para copiar (o arquivo `legenda.txt`);
   - se foi publicado (com o link) ou se está pronto para ele publicar à mão, porque o
     Instagram ainda não foi configurado.
4. Se algo falhar em qualquer etapa, explique em poucas palavras o que aconteceu e o que fazer.
