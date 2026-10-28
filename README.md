# Nord Kontakt Bridge

> **As explicações deste guia estão também DENTRO DO PROGRAMA**, logo abaixo de cada campo das abas 01 Conversão, 02 Identidade Visual e 03 Editor FX. Este ZIP contém o aplicativo real, não uma prévia HTML.

## Instalação Windows — Portable e Installer

**Para instalar sem configurar Python, Rust ou Cargo**, use o pacote de instalação gerado com `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/GERAR_PORTABLE_E_INSTALLER.bat` (compilação somente no Windows). O projeto acompanha `bin/nord.exe`; o Portable incorpora o decoder e o Installer instala uma cópia em `bin`. Leia `SUPORTE_RECUPERACAO/DOCUMENTACAO/INSTALADOR_LEIA_PRIMEIRO.md` para compilar localmente ou via GitHub Actions.

## Correção da roda do mouse no Editor FX

- A roda do mouse agora rola a aba **03 EDITOR FX** mesmo quando o ponteiro está sobre textos de ajuda, campos, botões ou sobre a prévia visual.
- **01 CONVERSÃO** e **02 IDENTIDADE VISUAL** também usam o mesmo comportamento, cada uma com rolagem independente.
- A barra de rolagem lateral continua disponível normalmente; a roda não desloca outras abas nem o rodapé quando o ponteiro está fora do painel.
- Suporte às mensagens de roda do Windows (`MouseWheel`) e Linux/X11 (`Button-4` e `Button-5`).
- O projeto foi testado com 53 testes automatizados aprovados, incluindo quatro cenários novos para a rolagem.
- Nenhuma alteração foi feita na conversão de áudio, geração do `.nki`, FX, exportação de presets ou visual das bibliotecas.

## Para que serve?

Este programa prepara instrumentos **.nki para o Kontakt 8** a partir de arquivos **.npno da Nord Piano Library**. É dedicado aos pianos Nord e não converte arquivos de outras marcas, formatos `.nsmp` ou `.npmo`. O `.nki` é criado pelo Kontakt 8, usando os arquivos de áudio decodificados e preparados pelo Bridge. A conversão exige o Kontakt 8 instalado no Windows e um decodificador nord-cli compatível.

**Atenção ao nome do formato:** alguns pedidos anteriores mencionaram `.npmo`, mas o projeto utiliza `.npno`, extensão documentada pela Nord para seus arquivos de piano. Não renomeie outro arquivo para `.npno` para tentar convertê-lo.

## Primeira utilização no Windows

1. Extraia o ZIP para uma pasta do computador. Não execute o aplicativo diretamente de dentro do ZIP.
2. Instale Python e Pillow, se for executar a versão `.pyw`. O arquivo `requirements.txt` contém a dependência Python do aplicativo. Para decodificação, disponibilize o `nord.exe` do nord-cli compatível conforme a configuração do projeto. Tenha o Kontakt 8 standalone instalado e suas opções de desenvolvedor configuradas conforme necessário.
3. Dê dois cliques em **`Nord Kontakt Bridge.pyw`**. Se preferir um executável, use **`SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/CRIAR_EXE.pyw`** no próprio Windows para compilar; a pasta original não contém um `.exe` do Windows pronto.
4. Na aba **01 CONVERSÃO**, escolha seu `.npno` Nord, **digite o nome do instrumento**, **selecione a pasta de saída** (o campo começa vazio) e **selecione o arquivo `Kontakt 8.exe`** da instalação.
5. Opcionalmente escolha seu KSP pessoal. A opção de adicionar efeitos automáticos é **recomendada** e não exige conhecimento de KSP.
6. Na aba **02 IDENTIDADE VISUAL**, você pode selecionar wallpaper, ícone e capa da biblioteca; **todos começam vazios** e são opcionais. Se não escolher wallpaper/ícone, o aplicativo usa os recursos visuais padrão. A opção correspondente vem marcada e bloqueada para impedir que fique sem esses padrões.
7. A personalização da imagem/texto do botão **REDEFINIR** é opcional. A opção de **preparar arquivos para Library Manager** é recomendada, mas **não adiciona automaticamente** uma biblioteca a um gerenciador externo.
8. **Arquivo `.nkr`:** é um contêiner de recursos do Kontakt, distinto do áudio `.npno` e da biblioteca `.nki`. Caso você tenha recebido um `.nkr` válido junto com outra distribuição ou possua um `.nkr` de projeto anterior, selecione-o neste campo. O Bridge também pode localizar automaticamente um modelo válido do seu próprio trabalho.
9. Na aba **03 EDITOR FX**, você pode mudar os nomes dos efeitos, fontes, cores, layout, knobs, título principal e as abas Piano/FX. É **opcional**; também é possível salvar/carregar presets e validar previamente o KSP.
10. Feche o Kontakt 8, clique em **CONVERTER PARA NKI** e acompanhe a mensagem de progresso. Ao terminar, mantenha a pasta **Samples** ao lado do NKI e teste som, KSP, arte e carregamento no Kontakt.

## Limitação importante do arquivo NKR

**Este pacote contém `NKR GERAL.nkr` fornecido pelo autor.** O modelo é incluído na pasta `resources` do instalador, mas ainda precisa ser selecionado ou reconhecido pelo fluxo do Kontakt conforme necessário. A presença do arquivo não garante a criação/vinculação automática de recursos sem erros. Use apenas arquivos sobre os quais possua direitos de distribuição. Alguns recursos gráficos dependem de o Kontakt conseguir criar ou reconhecer seu Resource Container.

## Campos obrigatórios e opcionais

| Campo | Regra | Estado inicial |
| --- | --- | --- |
| Arquivo Nord `.npno` | Obrigatório | Vazio |
| Nome do instrumento | Obrigatório | Vazio; usuário digita |
| Pasta de saída | Obrigatório | Vazio; usuário escolhe |
| Kontakt 8.exe | Obrigatório | Pode reutilizar caminho escolhido e salvo anteriormente; sem detecção presumida |
| KSP personalizado | Opcional | Vazio |
| Adicionar FX básicos | Opcional, recomendado | Marcado por padrão, se não houver preferência salva |
| Wallpaper | Opcional | Vazio |
| Ícone | Opcional | Vazio |
| Capa | Opcional | Vazio |
| Personalizar botão REDEFINIR | Opcional | Estilo e nome padrão |
| Preparar Library Manager | Opcional, recomendado | Marcado por padrão, se não houver preferência salva |
| Modelo `.nkr` | Opcional, mas necessário para alguns recursos quando exigido pelo Kontakt | Caminho salvo, se houver |
| Usar wallpaper e ícone padrão | Sempre obrigatório | Marcado e bloqueado |
| Editor FX | Opcional | Personalizações existentes preservadas |

## O que foi alterado nesta edição

- Textos de ajuda dentro das três abas reais do programa.
- Aba Conversão com rolagem para não cortar as explicações; Identidade Visual e Editor FX continuam com rolagem.
- Campos de saída, wallpaper, ícone e capa começam vazios, mesmo quando havia escolhas anteriores.
- Nome do instrumento passou a ser exigido pela interface e pela etapa de preparação.
- Wallpaper e ícone padrão agora são ativados de maneira obrigatória, com opção bloqueada.
- Validação inicial para arquivo Nord, nome, destino, executável do Kontakt e KSP opcional.
- Correção das instruções de formato e do comportamento do Library Manager (prepara arquivos, não registra automaticamente).
- Nenhum código da geração de áudio, KSP, recursos visuais ou exportação foi removido.

---

## Histórico técnico das versões anteriores

# Nord Kontakt Bridge v0.7.0 — Editor visual FX + Library Manager

Esta versão adiciona novos controles à aba **02 IDENTIDADE VISUAL**:

1. **Enquadramento da arte superior (633 × 320)**: Preencher largura (padrão, corta as bordas quando necessário) ou Mostrar imagem inteira (pode criar barras). O painel completo de efeitos continua 633 × 620.
2. **Botão REDEFINIR personalizável**: escolha um arquivo PNG/JPG opcional, escreva o texto que deve aparecer no botão e escolha Nord Red / Dourado / Cinza. O aplicativo gera um sprite PNG de 144 × 240 com seis quadros (144 × 40 cada), o TXT de animações e as instruções KSP de imagem. A ação do botão continua sendo redefinir os oito controles.
3. **Library Manager externo v8.8.0**: ao converter, cria `Nome do Instrumento_info.nkx` (arquivo de 0 bytes), `wallpaper.png` e `COMO_ADICIONAR_NO_LIBRARY_MANAGER.txt` na pasta do novo NKI, conforme a opção “Add unencoded libraries created by the empty registration file method” mostrada no próprio gerenciador. Para adicioná-la, ative essa opção em Options > Libraries, use **ADD**, selecione a pasta do instrumento, e depois **SAVE**. Para alterar a imagem da capa, use o botão **Wallpaper** do gerenciador.

**O programa NÃO altera registro Windows, não instala licenças, não cria .nicnt e não registra no Native Access.** É um cadastro específico do programa externo; sua compatibilidade pode variar. Alternativa oficial: Kontakt 8 > Import Content > Custom Libraries > Add.

**Importante sobre NKR e gráficos:** o KSP com imagem do botão depende de um NKR válido contendo o sprite. Se o Kontakt não conseguir vincular o Resource Container, o conversor tenta usar o painel FX básico sem arte gráfica. A existência de arquivos PNG, TXT e NKR não comprova que o instrumento reabrirá sem Content Missing. O workflow do Kontakt real não pôde ser testado neste ambiente.

O programa continua gerando os WAVs em Samples e scripts KSP/Lua na pasta final, sem BAT/F11 no fluxo esperado. O formato .npno ainda exige decodificação de áudio e o NKI é salvo pelo Kontakt.

## Como executar

Extraia o ZIP, dê duplo clique em `Nord Kontakt Bridge.pyw` (Python com Pillow instalado), escolha o .npno, Kontakt 8.exe e destino; personalize as imagens na aba Identidade Visual e converta. Feche o Kontakt antes de iniciar a conversão. Opcionalmente use `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/CRIAR_EXE.pyw` para compilar EXE no Windows (requer PyInstaller).

---

# Nord Kontakt Bridge v0.6.4 — Correção da importação KSP por código

No Kontakt 8.9.0 informado, a API chegou a devolver aproximadamente 92 bytes após a importação: era apenas o caminho do arquivo KSP, não o código. Nesta versão a importação tenta primeiro o caminho absoluto (conforme documentação oficial da Native Instruments). Se a API não confirmar que o conteúdo completo está no slot, tenta automaticamente o texto integral do arquivo `.ksp`.

O aplicativo compara a fonte recuperada do Kontakt ao script original; NÃO considera 92 bytes de caminho como uma importação bem-sucedida. Também mantém o KSP na pasta definitiva do instrumento.

## Utilização sem BAT/F11
1. Extraia o ZIP inteiro em uma nova pasta.
2. Feche o Kontakt 8, salvando trabalhos abertos.
3. Abra `Nord Kontakt Bridge.pyw`, selecione `.npno`, destino, Kontakt e artes (opcionais).
4. Clique em Converter. O programa reutiliza cache de samples, copia para `Samples` e tenta gerar o NKI.
5. Se apresentar erro, procure `KSP RETORNO API [CAMINHO]` e `KSP RETORNO API [TEXTO]` em `LOG_KONTAKT_*.txt` na pasta do timbre; erros de compilação KSP podem aparecer no terminal.

**Avisos:** Este ajuste é direcionado ao problema que o seu log demonstrou. A documentação oficial descreve a importação por caminho; a alternativa de texto integral é um procedimento experimental de compatibilidade, ainda não testado em Kontakt real neste ambiente. Confirmar que a fonte está no slot NÃO comprova que o KSP compilou ou que o NKI reabre sem avisos. A organização dos WAVs e do NKR mantém o funcionamento de v0.6.3, com suas limitações anteriores. Não apague as versões estáveis, nem o cache.

---

# Nord Kontakt Bridge v0.6.3 — Diagnóstico e fallback automático do KSP

**Novidade:** a versão 0.6.2 podia parar com `KSP NAO FOI CARREGADO`. O programa agora tenta primeiro o painel com recursos gráficos e, se não houver confirmação do Kontakt, tenta o painel básico sem dependência de ícone. Também registra a resposta de `get_instrument_script_source` para diagnosticar o motivo real.

**Não foi possível executar o Kontakt 8.9.0 neste ambiente.** Uma tentativa de fallback não garante que a API aceitará o script; nesse caso, consulte `LOG_KONTAKT_*.txt` e `LOG_KONTAKT_*_TERMINAL.txt` dentro da pasta do instrumento e compartilhe os trechos `KSP RESPOSTA ENVIO`, `KSP RETORNO API` e `ERRO`.

# Nord Kontakt Bridge v0.6.2 — Correção do Wallpaper Automático

A versão 0.6.2 corrige o problema em que os knobs são criados, mas a imagem de fundo não aparece no Kontakt.

**Estratégia:** a API `Kontakt.set_instrument_options(inst, {wallpaper=...})` aplica o PNG diretamente às Instrument Options, sem depender do NKR para esse wallpaper. A imagem continua na pasta `Resources/pictures` do instrumento. O KSP gerado não substitui mais esse wallpaper com a diretiva `INST_WALLPAPER_ID`. O ícone personalizado continua dependente do Resource Container.

- Copie ou mantenha o PNG `Resources/pictures/NB_..._WALL.png` na pasta final junto do NKI.
- O Lua confere a existência do PNG e registra se a API aceitou o wallpaper.
- O NKR ainda pode ser necessário para o ícone e demais recursos de KSP, e o problema `Content Missing` de NKIs antigos não é reparado retroativamente.
- O conversor não muda o som, os WAVs ou as funções FX.

**Atenção:** a API Lua e a reabertura do NKI com o wallpaper não puderam ser testadas dentro do Kontakt 8.9.0 neste ambiente. O log deve conter `WALLPAPER APLICADO VIA API` ou `AVISO WALLPAPER` para diagnóstico. A imagem referenciada usa caminho local; transportar a biblioteca para outro PC pode exigir relocalização/re-salvamento.

## Testar

1. Extraia o ZIP completo em uma pasta nova.
2. Abra `Nord Kontakt Bridge.pyw`, selecione seu NPNo e uma imagem.
3. Feche o Kontakt e converta normalmente.
4. Abra o NKI novo e confira wallpaper, knobs e efeitos.
5. Se ainda não aparecer, verifique `Instrument Options > Instrument > Instrument Wallpaper` e a linha do log correspondente.

# Nord Kontakt Bridge v0.6.1 — Lua e KSP junto do instrumento

**O que corrigimos nesta versao:** o erro `path doesn't exist` durante o salvamento pode ocorrer quando o Kontakt recebe `mode="samples"` sem a pasta `Samples` presente. Agora o aplicativo copia previamente os WAVs do cache para a pasta final `Samples`, usando arquivos temporarios + renomeacao atomica. O script Lua importa somente esses WAVs e salva com `mode="patch", absolute_paths=false` para manter referencias relativas, sem mandar o Kontakt tentar criar/copiar a pasta durante o salvamento.

**Importante:** nao confunda *Patch Only* com ausencia de samples. Neste fluxo os WAVs ja estao fisicamente na pasta Samples antes de o Kontakt montar o instrumento, e o NKI deve referenciar esses WAVs. **A compatibilidade da referencia relativa precisa ser validada reabrindo o NKI no Kontakt 8.9.0**, pois nao executamos o Kontakt neste ambiente. Se aparecer Content Missing, nao exclua Samples nem cache; envie o log da nova versao.

**Preserva:** tema Nord Red, efeitos e NKR opcional, sem BAT/F11. Se o NKR ainda falhar, o app deve exportar o NKI com efeitos sem recursos graficos.


**Mudança principal:** cada conversão cria uma pasta com o nome do timbre e nela um `*.nki` e uma pasta `Samples/` com os WAVs necessários. Os WAVs sao copiados pelo aplicativo antes de iniciar o Kontakt. O Lua salva com `save_instrument(...,{mode="patch", absolute_paths=false})`, apontando para os WAVs locais. O Lua verifica todas as amostras antes de registrar sucesso. **Nao usa Monolith nesta versao.**

Exemplo de saída:

```text
Destino/
  Astoria Grand XL/
    Astoria Grand XL.nki
    PAINEL_KONTAKT_Astoria Grand XL.ksp
    CRIAR_NKI_Astoria Grand XL.lua
    LOG_KONTAKT_Astoria Grand XL.txt
    Samples/
      060-b0-l00.wav
      ...
    Astoria Grand XL_Resources.nkr   (se disponível)
    Resources/pictures/              (quando arte habilitada)
```

Se converter outro timbre, ele recebe sua própria pasta `Samples`, evitando substituir WAVs com nomes semelhantes. Se a pasta já existir, cria `Nome (2)` automaticamente, preservando versões anteriores.

O Lua verifica se o primeiro slot do Script Editor contém código KSP real (incluindo `on init` e `end on`) antes de salvar; se encontrar apenas o caminho do arquivo, tenta outra forma de instalação e interrompe o salvamento se a instalação não for confirmada. Este teste verifica conteúdo, mas não comprova ausência de erros na compilação KSP.

A conversão e os efeitos continuam automáticos; o Kontakt precisa executar o Lua na inicialização. Sem BAT/F11 no fluxo esperado. O áudio ainda é decodificado pelo nord-cli no cache. O próprio Nord Kontakt Bridge copia esses WAVs para a pasta final antes de iniciar o Kontakt. Não limpe o cache antes de abrir o NKI e testar o som.

**Importante:** o `.nkr` da interface é separado dos WAVs; a versão 0.6.0 não garante reparo de vínculos antigos de `.nkr`. Se não houver recurso válido, tenta criar um NKI com WAVs e efeitos básicos sem a arte, como no fluxo anterior.

### Executar

1. Extraia o ZIP completo no Windows.
2. Abra `Nord Kontakt Bridge.pyw` com Python instalado. Pillow, nord-cli e Kontakt 8 completo com Developer Options são necessários.
3. Escolha `.npno`, pasta de saída, Kontakt 8.exe e imagens (opcional).
4. Feche o Kontakt e clique em **CONVERTER PARA NKI**.
5. Verifique `NOME/NOME.nki` e `NOME/Samples/*.wav`, abra o NKI e toque.

`SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/CRIAR_EXE.pyw` pode compilar no Windows sem arquivo BAT. Não há EXE Windows pré-compilado no ZIP.

**Como corrigir um NKI anterior que pediu WAVs:** na janela Content Missing do Kontakt, clique **Browse for folder**, escolha a pasta `%LOCALAPPDATA%\NordKontaktBridge\Work\<id>\Samples`, abra o instrumento e faça **Save as → Patch + Samples**, indicando a pasta final desejada. Não apague o cache até salvar e reabrir sem aviso.

**Validação:** testes de preparação de arquivos e geração Lua; a escrita real de NKI/WAV depende do Kontakt no Windows.


### Novo nesta versão (v0.6.1)

- O programa grava `.lua`, `.ksp`, logs e scripts de contingência diretamente na pasta do novo instrumento, não em `%LOCALAPPDATA%/NordKontaktBridge/Work`. O cache de decodificação continua separado para desempenho.
- Em cada execução, cria uma pasta própria, como `Destino/Astoria Grand XL/`, evitando sobrescrever versões antigas.
- A geração Lua tenta passar o conteúdo KSP ao Kontakt, consulta `get_instrument_script_source` e também testa o modo por caminho para acomodar diferenças entre versões. Se o primeiro slot contiver somente um caminho, interrompe a conversão em vez de criar um NKI sem painel de efeitos.
- O `.nkr` continua separado; os problemas de vinculação do `.nkr` e de `Content Missing` em versões antigas não são reparados por essa alteração.

**Validação:** testes automatizados da organização de arquivos e da geração de Lua; a execução no Kontakt 8.9.0 real ainda precisa ser testada.


### Correcao da versao 0.6.1

- O KSP criado na 0.6.0 declarava `$OriginalVolume` atribuindo uma chamada `get_engine_par(...)` na mesma linha. O compilador KSP nao aceita essa forma; agora declaramos a variavel e atribuimos o retorno na instrucao seguinte. Corrige a mensagem `Variable $OriginalVolume was not declared` ao clicar em Apply.
- Importacao via Lua agora passa diretamente o caminho completo do arquivo KSP, de acordo com a documentacao oficial `Kontakt.set_instrument_script_source`. Continua conferindo o texto retornado pela API, mas isso NAO substitui um teste de compilacao real no Kontakt.
- Para reparar o NKI da versao anterior sem refazer a conversao, copie o codigo do `PAINEL_KONTAKT_....ksp` para o primeiro slot do Script Editor do instrumento e aplique. Se esse KSP veio da 0.6.0, altere `declare $OriginalVolume := get_engine_par(...)` para duas instrucoes: `declare $OriginalVolume` e `$OriginalVolume := get_engine_par(...)`. Salve outra copia do instrumento.
- **Content Missing / NKR:** continua sendo um problema independente. A 0.6.1 nao comprova que o Kontakt conseguira reabrir o NKI sem perguntar por um container. Nao elimine os WAVs nem o NKR. Confira Instrument Options > Instrument > Resource Container e salve o instrumento apos recuperar um caminho valido.
- O NKR usado como modelo ainda pode exigir `Repack` quando os PNGs selecionados diferem dos recursos gravados nele.

**Verificacao:** testes unitarios e estrutura Lua/KSP em Python. A compilacao KSP no Kontakt 8.9.0 precisa ser testada no Windows; nao ha execucao do Kontakt no ambiente de build.

---

# Nord Kontakt Bridge v0.7.0 — Editor visual FX (novo)

Agora o aplicativo possui **03 EDITOR FX**, além de CONVERSÃO e IDENTIDADE VISUAL. A opção **Ativar editor visual FX** vem ligada. É possível:

- Definir título principal (ex.: `SOUND / FX`, `CONTROLES`, `EFEITOS`).
- Escrever **nomes individuais** para os oito controles: Reverb, Delay, Chorus, EQ Brilho, Volume, Dinâmica, Tune, Pan.
- Selecionar entre seis famílias de fonte suportadas pelo gerador (Segoe UI, Arial, Georgia, Consolas, Trebuchet MS, Times New Roman).
- Ajustar **quatro cores** (fundo, detalhes, título e nomes dos controles), no seletor de cores.
- Selecionar visual dos knobs: Nord Red, Dourado, Prata ou Minimal; escolher disposição 3 colunas ou 4 colunas.
- Habilitar ou desabilitar **duas abas PIANO / FX**. O próprio KSP gerado cria botões de navegação e mantém os controles ocultos na aba PIANO. Os botões são criados como imagens de 6 estados, e os knobs usam sprites verticais de 101 quadros.
- Conferir a prévia da tela PIANO e da tela FX ANTES de converter.
- Salvar/carregar presets do editor como `.json` sem alterar amostras do instrumento.

## Como foi implementado

A pasta `PRESETS_FX/` traz três pontos de partida (Nord Red, Grand Gold e Studio Silver).

As fontes e cores dos títulos são **desenhadas em PNGs pelo Pillow**, e não carregadas como fontes independentes pelo Kontakt; isso permite escolher famílias e cores visualmente sem depender dos limites de fontes KSP. Valores numéricos e controles continuam como widgets KSP. Ao gerar o instrumento, criamos `DESIGN_FX.json`, `PREVIA_FX.png`, `PAINEL_KONTAKT_*.ksp`, sprites de knobs/abas, arquivos TXT de configuração e um wallpaper vertical de duas páginas dentro da pasta `Resources/pictures`.

**Importante:** os gráficos personalizados exigem um `.nkr` funcional contendo ou enxergando os PNGs/TXTs. Se a API do Kontakt 8.9.0 falhar no NKR ou na compilação do KSP, o aplicativo preserva a tentativa de painel FX básico, sem os gráficos, em `PAINEL_SEM_NKR_*.ksp`. A conversão do `.npno` e o áudio são independentes do visual. Não está garantida a compilação final de KSP no Kontakt 8.9.0 sem testá-la no próprio Windows.

Na interface: selecione o `.npno` em **01 CONVERSÃO**, escolha a fotografia em **02 IDENTIDADE VISUAL**, personalize controles na **03 EDITOR FX** e clique em **CONVERTER PARA NKI**. Os arquivos finais ficam na pasta selecionada, com WAVs em Samples e Lua/KSP junto ao NKI. Não há necessidade de BAT para usar o programa.


## v0.7.1 — Correção de tipos de controles no Editor FX

- Removido `set_text($Controle, "")` de `ui_slider`. O gerador agora usa `$CONTROL_PAR_LABEL` para os controles, preservando as legendas de fonte/cor escolhidas no wallpaper PNG. Esse erro causava `set_text(): $Pan was not declared or is not an appropriate control type`.
- Novo `ksp_validation.py` checa incompatibilidade de `set_text` com `ui_slider`, controles UI sem declaração, callbacks repetidos e blocos `on`/`function` sem fechamento.
- Também confere as escolhas do editor visual (número de nomes, cores, fonte, estilo e layout), impedindo exportação de valores fora do conjunto suportado.
- A validação é **preventiva e parcial**: só o compilador KSP do Kontakt 8.9.0 pode confirmar compilação completa. Scripts personalizados arbitrários ainda podem conter comandos fora do escopo desses testes.
- Não é preciso converter WAVs de novo para aplicar a correção a um NKI existente: substitua o KSP com o gerado pela nova versão ou remova linhas `set_text($Reverb/Delay/Chorus/Brilho/Volume/Dinamica/Tune/Pan,"" )` somente se seus controles forem `ui_slider`; clique Apply e salve nova cópia.


## Correção do layout real do Kontakt

- Nomes dos oito efeitos e titulo do painel FX sao `ui_label` KSP, nas mesmas
  coordenadas de widgets e valores. Deixamos de desenha-los no wallpaper,
  que comeca sob o cabecalho no Kontakt e causava sobreposicao ou sumico.
- Titulo fica a esquerda e botoes PIANO/FX a direita, sem cruzar textos.
- A previa do app usa o mesmo gerador da previa que e exportada para a pasta.
- Nome/cores customizados aparecem na previa. A fonte exata e a cor das
  letras ao vivo ainda dependem da fonte nativa do Kontakt: KSP nao aplica
  livremente fontes TTF e cores de textos como um app Windows.
- A validacao Python nao substitui compilar/testar com Kontakt 8.9.0.

Para testar sem reconverter os WAVs: gere uma versao com o novo conversor,
abra o NKI, verifique PIANO/FX e salve com novo nome, mantendo o anterior.
