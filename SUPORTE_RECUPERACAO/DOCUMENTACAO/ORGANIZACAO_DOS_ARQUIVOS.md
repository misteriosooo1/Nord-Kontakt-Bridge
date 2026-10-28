# Organização dos arquivos — Nord Kontakt Bridge

## O que foi organizado

Esta versão mantém na pasta principal os arquivos NKR, imagens de prévia e KSP, conforme solicitado.Os manuais, as instruções de instalação, as licenças e as ferramentas para compilar o Windowsforam agrupados em `SUPORTE_RECUPERACAO/DOCUMENTACAO` e `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO`.

## O que deve continuar na pasta principal

- `Nord Kontakt Bridge.pyw`: entrada do aplicativo quando executado via Python.
- `nordbridge/`: código-fonte principal do programa.
- `bin/nord.exe`: decoder principal procurado pelo aplicativo.
- `assets/`: recursos de interface usados durante a compilação.
- `NKR GERAL.nkr`, os `.png` de prévias e o `.ksp`: arquivos de conteúdo solicitados.
- `README.md`: documentação de apresentação necessária na raiz do GitHub.
- `requirements.txt`: dependências padrão para executar ou construir a versão Python.
- `.github/`: automação de compilação do GitHub Actions.

A pasta `SUPORTE_RECUPERACAO` continua contendo os backups do decoder, NKR, imagens erecursos indispensáveis ao reparo manual. Essas cópias são intencionais: não são os arquivos principais.

## Como gerar os executáveis

1. Abra `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO`.
2. Execute `GERAR_PORTABLE_E_INSTALLER.bat` no Windows.
3. Os dois `.exe` serão gravados na pasta `dist/` da raiz.

O BAT volta à pasta principal antes de compilar. O script Python e o arquivo Inno Setupforam ajustados para usar os novos caminhos.

## Recuperação do aplicativo já compilado

- Execute `SUPORTE_RECUPERACAO/VERIFICAR.bat` e depois `REPARAR.bat`, se necessário.
- A pasta de suporte **não modifica automaticamente um `.exe` antigo**.
- O reparo copia arquivos externos ausentes, mas não corrige erros internos de KSP e código.

## Para a versão EXE que você já tem

Se o seu `.exe` principal já está pronto, deixe-o em uma pasta com a subpasta`SUPORTE_RECUPERACAO` ao lado. O instalador novo só é necessário para distribuira versão atualizada aos usuários. A parte de construção é voltada para desenvolvedores.
