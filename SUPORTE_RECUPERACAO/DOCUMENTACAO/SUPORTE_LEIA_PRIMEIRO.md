# Pasta de suporte offline — Nord Kontakt Bridge

A pasta `SUPORTE_RECUPERACAO/` contém **cópias de reserva do `nord.exe`, imagens padrão, NKR e presets**, além de ferramentas para verificar e repor arquivos externos ausentes. Não contém o executável principal do aplicativo.

## Para quem já tem o `.exe`

1. Coloque a pasta `SUPORTE_RECUPERACAO` **ao lado do seu arquivo** `Nord Kontakt Bridge.exe` ou `Nord Kontakt Bridge Portable.exe`.
2. Execute `SUPORTE_RECUPERACAO/VERIFICAR.bat` para identificar arquivos ausentes.
3. Se houver problemas, execute `SUPORTE_RECUPERACAO/REPARAR.bat` com o aplicativo fechado. O script só copia o que estiver faltando e pede permissão antes de substituir um decoder existente que não execute.
4. Reabra o programa. O relatório do diagnóstico é salvo em `%LOCALAPPDATA%\NordKontaktBridge\Diagnosticos`.

Se o executável estiver em outra pasta, os arquivos BAT pedirão o caminho do EXE. Não é necessário instalar Cargo, Rust ou Python para executar o decoder ou usar um EXE Python empacotado corretamente.

## Para novas compilações

O `nordbridge/core.py` foi atualizado para procurar o decoder na pasta de suporte quando não encontrar o principal e para testar o reserva se a execução do principal gerar um erro do sistema operacional. O `nordbridge/visual_assets.py` procura os gráficos padrão da reserva se os originais estiverem incompletos. O script do Inno Setup também instala a pasta de suporte.

**Não é possível adicionar fallback automático ao `.exe` que já foi compilado apenas copiando arquivos de código**; para isso, compile novamente. O utilitário manual de reparo, entretanto, pode repor `bin/nord.exe` ao lado do EXE antigo sem recompilá-lo.

## Limitações

Isso corrige **dependências externas ausentes**, não erros de KSP, conversão, incompatibilidade de arquivo `.npno`, defeitos do Kontakt ou bug interno do código. O `NKR GERAL.nkr` é apenas uma cópia do arquivo recebido: a compatibilidade com a biblioteca gerada precisa ser confirmada no Kontakt, e pode ser necessário selecioná-lo manualmente. Não substitua seus instrumentos e amostras originais pelos arquivos de suporte.

Para redistribuição, mantenha `LICENCAS_TERCEIROS.txt`.
