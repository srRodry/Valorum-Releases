# Protocolo de atualizações — Valorum

O repositório `srRodry/Valorum-Releases` publica versões Android verificadas.

## Manifesto ativo

Local esperado: [update.json](../update.json).

Este arquivo **não deve existir com valores de exemplo**. Ele será criado automaticamente depois que o primeiro APK assinando o canal GitHub for publicado e verificado no próprio GitHub Releases.

Esquema JSON esperado:

```json
{
  "tag": "v1.0.0-beta.7",
  "version_name": "1.0.0-beta.7",
  "version_code": 45,
  "apk_url": "https://github.com/srRodry/Valorum-Releases/releases/download/v1.0.0-beta.7/Valorum-1.0.0-beta.7.apk",
  "sha256": "<64 caracteres hexadecimais, obtidos do APK real>",
  "size_bytes": 0,
  "notes": "<resumo público da versão>"
}
```

**Exemplo de esquema, não uma atualização disponível.** O arquivo real deve conter o SHA-256 e o tamanho exatos de um APK assinado publicado; `size_bytes` deve ser maior que zero.

## Regras de publicação

- Publicar apenas APKs assinados pelo projeto Valorum e compilados a partir de um workflow aprovado.
- Usar tags imutáveis (ex.: `v1.0.0-beta.7`) e não substituir arquivos de um Release já publicado.
- Publicar `SHA256SUMS.txt` e conferir o hash do APK distribuído.
- Publicar ou atualizar `update.json` **somente depois** de confirmar que o APK está disponível no Release correspondente.
- Não publicar neste repositório keystores, chaves privadas, tokens, dados financeiros reais ou código-fonte privado.
- O canal Google Play utiliza atualizações gerenciadas pelo Google, não este instalador de APKs.

## Recuperação

Se um APK apresentar falhas, não altere o conteúdo de uma tag existente. Publique uma versão corretiva com `version_code` superior. A autorização do Android e a compatibilidade de assinatura continuam obrigatórias.
