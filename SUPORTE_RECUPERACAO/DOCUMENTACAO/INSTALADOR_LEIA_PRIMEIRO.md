# Nord Kontakt Bridge — geração do instalador Windows (.exe)

Este projeto inclui `bin/nord.exe`, o decodificador nord-cli compilado em Rust. O instalador **não precisa instalar** Python nem Cargo no computador do usuário final. O app inclui Python via PyInstaller, e o setup instala uma cópia do decoder em `bin/nord.exe`.

## Compilar no seu Windows

1. Instale Python 3.12 ou mais recente, com pip (só no computador usado para compilar).
2. Instale **Inno Setup 6**: https://jrsoftware.org/isdl.php (só no computador usado para compilar).
3. Extraia o projeto inteiro; confira se existe `bin/nord.exe`.
4. Dê dois cliques em **`SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/GERAR_PORTABLE_E_INSTALLER.bat`**. Ele instala PyInstaller e Pillow pelo pip, caso necessário, compila o aplicativo e executa o Inno Setup.
5. Na pasta `dist`, procure:
    - `Nord Kontakt Bridge Portable.exe` — versão portátil, com decoder incluso;
    - `Nord Kontakt Bridge Installer.exe` — instalador do Windows, com atalhos, desinstalador e `bin/nord.exe`.

Alternativa sem BAT: execute `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/CRIAR_EXE.pyw` no Windows ou `python build_windows.py ambos` em um terminal.

## Compilar na nuvem (GitHub Actions)

Faça upload de todo o projeto em seu repositório (incluindo `bin/nord.exe` e `.github/workflows/build-windows.yml`). No GitHub, vá até **Actions → Windows - Nord Kontakt Bridge EXEs → Run workflow**. Quando a execução terminar, baixe o artefato `Nord-Kontakt-Bridge-Windows`, que contém os dois `.exe`.

**Atenção:** o arquivo ZIP distribuído aqui é um **projeto preparado para compilação**, não é ainda o `.exe` final. A compilação do Inno Setup e do PyInstaller para Windows precisa executar em Windows, como no seu PC ou no GitHub Actions.

## Requisitos de execução

- Windows 10/11 64 bits;
- Kontakt 8 instalado separadamente para gerar `.nki`;
- Arquivos `.npno` da Nord Piano Library (não `.npmo`);
- Recursos KSP/NKR seguem as limitações funcionais do projeto original.

## Avisos de licença

`bin/nord.exe` corresponde à ferramenta nord-cli do projeto drawbar. Leia `LICENCAS_TERCEIROS.txt`. Preserve os avisos BSD-3-Clause quando redistribuir os executáveis. Os direitos sobre bibliotecas Nord e conteúdo Kontakt seguem suas próprias licenças.
