param(
    [ValidateSet('Verificar','Reparar')][string]$Acao='Verificar',
    [string]$Destino=''
)
$ErrorActionPreference = 'Stop'
$Suporte = $PSScriptRoot
$AppRoot = Split-Path $Suporte -Parent
$nomes = @('Nord Kontakt Bridge.exe','Nord Kontakt Bridge Portable.exe')
$log = New-Object System.Collections.Generic.List[string]

function Registro([string]$mensagem) {
    Write-Host $mensagem
    $log.Add($mensagem)
}
function ExisteApp([string]$pasta) {
    if (-not (Test-Path -LiteralPath $pasta -PathType Container)) {return $false}
    foreach ($nome in $nomes) {if (Test-Path -LiteralPath (Join-Path $pasta $nome) -PathType Leaf) {return $true}}
    return $false
}
function EscolherDestino([string]$informado) {
    if ($informado.Trim()) {
        $p = $informado.Trim().Trim('"')
        if ([IO.Path]::GetExtension($p) -ieq '.exe') {return (Split-Path $p -Parent)}
        return $p
    }
    $candidatos = @($AppRoot, (Join-Path $AppRoot 'dist'), (Join-Path $AppRoot 'build\windows'))
    foreach ($p in $candidatos) {if (ExisteApp $p) {return $p}}
    Write-Host 'Nenhum executavel principal localizado automaticamente.' -ForegroundColor Yellow
    $manual = Read-Host 'Cole o caminho da pasta OU do EXE Nord Kontakt Bridge'
    if (-not $manual) {throw 'Caminho nao informado.'}
    return (EscolherDestino $manual)
}
function BinarioFunciona([string]$arquivo) {
    if (-not (Test-Path -LiteralPath $arquivo -PathType Leaf)) {return $false}
    try {
        $saida = & $arquivo --version 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch {return $false}
}

try {
    $pasta = EscolherDestino $Destino
    $pasta = [IO.Path]::GetFullPath($pasta)
    if (-not (ExisteApp $pasta)) {
        throw "Nao encontrei Nord Kontakt Bridge.exe (ou Portable.exe) em: $pasta"
    }
    Registro "Nord Kontakt Bridge - $Acao"
    Registro "Aplicativo: $pasta"
    Registro "Suporte: $Suporte"
    Registro '---'
    $mapa = @{}
    $checksum = Join-Path $Suporte 'CHECKSUMS_SHA256.txt'
    if (-not (Test-Path -LiteralPath $checksum)) {throw 'CHECKSUMS_SHA256.txt ausente. Nao vou copiar arquivos sem verificar integridade.'}
    foreach ($linha in Get-Content -LiteralPath $checksum) {
        if ($linha -match '^([0-9a-fA-F]{64})\s{2}(.+)$') { $mapa[$matches[2]] = $matches[1].ToUpperInvariant() }
    }
    $arquivos = @('bin/nord.exe','assets/default_icon.png','assets/default_wallpaper.png',
        'assets/hero_red.png','assets/NordBridge.ico','resources/NKR GERAL.nkr',
        'PRESETS_FX/Grand_Gold.json','PRESETS_FX/Nord_Red.json','PRESETS_FX/Studio_Silver.json',
        'LICENCAS_TERCEIROS.txt')
    $total = 0
    foreach ($rel in $arquivos) {
        $relWin = $rel.Replace('/', '\')
        $origem = Join-Path $Suporte $relWin
        $alvo = Join-Path $pasta $relWin
        if (-not (Test-Path -LiteralPath $origem -PathType Leaf)) { Registro "ERRO: backup ausente: $rel"; continue }
        $sha = (Get-FileHash -LiteralPath $origem -Algorithm SHA256).Hash.ToUpperInvariant()
        if (-not $mapa.ContainsKey($rel) -or $sha -ne $mapa[$rel]) {
            Registro "ERRO: backup com hash inesperado, ignorado: $rel"
            continue
        }
        if (-not (Test-Path -LiteralPath $alvo -PathType Leaf)) {
            Registro "AUSENTE: $rel"
            if ($Acao -eq 'Reparar') {
                $pastaAlvo = Split-Path $alvo -Parent
                if (-not (Test-Path -LiteralPath $pastaAlvo)) {New-Item -ItemType Directory -Path $pastaAlvo -Force | Out-Null}
                Copy-Item -LiteralPath $origem -Destination $alvo
                Registro "  RECUPERADO: $rel"
                $total++
            }
        } elseif ($rel -eq 'bin/nord.exe') {
            if (BinarioFunciona $alvo) {
                Registro 'OK: bin/nord.exe executa --version.'
            } else {
                Registro 'FALHA: bin/nord.exe existe, mas nao executa corretamente.'
                if ($Acao -eq 'Reparar') {
                    $resposta = Read-Host 'Substituir o bin/nord.exe defeituoso pela copia de suporte? (S/N)'
                    if ($resposta -match '^[sSyY]') {
                        Copy-Item -LiteralPath $origem -Destination $alvo -Force
                        Registro '  SUBSTITUIDO: bin/nord.exe'
                        $total++
                    }
                }
            }
        } else {
            Registro "OK: $rel (existente, preservado)"
        }
    }
    Registro '---'
    $decoderFinal = Join-Path $pasta 'bin\nord.exe'
    if (BinarioFunciona $decoderFinal) {
        Registro 'DECODER: disponivel e funcional.'
    } else {
        Registro 'DECODER: ausente ou nao funcional; verifique o arquivo e o relatorio.'
    }
    Registro "Arquivos copiados/substituidos: $total"
    Registro 'NOTA: NKR e imagens externas nao corrigem erros internos de um EXE antigo.'
} catch {
    Registro "ERRO: $($_.Exception.Message)"
    Registro 'Verifique o caminho de destino e as permissoes de escrita na pasta.'
} finally {
    try {
        $out = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'NordKontaktBridge\Diagnosticos'
        New-Item -ItemType Directory -Path $out -Force | Out-Null
        $relatorio = Join-Path $out 'ultimo_diagnostico.txt'
        $log | Out-File -LiteralPath $relatorio -Encoding UTF8 -Force
        Write-Host "Relatorio salvo: $relatorio"
    } catch { Write-Host "Nao foi possivel salvar o relatorio: $_" -ForegroundColor Yellow }
}
