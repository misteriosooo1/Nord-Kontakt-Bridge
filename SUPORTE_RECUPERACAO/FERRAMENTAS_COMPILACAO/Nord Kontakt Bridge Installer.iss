#define AppName "Nord Kontakt Bridge"
#define AppVersion "1.0"
#define ProjectRoot (AddBackslash(SourcePath) + "..\..\")

[Setup]
AppId={{BC2BDCA6-2F7A-4BB0-BD41-6875CC6D2C39}
AppName=Nord Kontakt Bridge
AppVerName=Nord Kontakt Bridge
AppVersion={#AppVersion}
AppPublisher=Nord Kontakt Bridge
DefaultDirName={localappdata}\Programs\Nord Kontakt Bridge
DefaultGroupName=Nord Kontakt Bridge
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
OutputDir={#ProjectRoot}dist
OutputBaseFilename=Nord Kontakt Bridge Installer
SetupIconFile={#ProjectRoot}assets\NordBridge.ico
UninstallDisplayName=Nord Kontakt Bridge
UninstallDisplayIcon={app}\Nord Kontakt Bridge.exe
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
; Interface principal: PyInstaller com Python/Pillow embarcados
Source: "{#ProjectRoot}build\windows\Nord Kontakt Bridge.exe"; DestDir: "{app}"; Flags: ignoreversion
; Decoder Rust: instalado sem precisar instalar Cargo ou rustc
Source: "{#ProjectRoot}bin\nord.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "{#ProjectRoot}SUPORTE_RECUPERACAO\DOCUMENTACAO\LICENCAS_TERCEIROS.txt"; DestDir: "{app}"; Flags: ignoreversion
; Pasta de recuperacao opcional, para diagnostico e reparo offline.
Source: "{#ProjectRoot}SUPORTE_RECUPERACAO\*"; DestDir: "{app}\SUPORTE_RECUPERACAO"; Excludes: "FERRAMENTAS_COMPILACAO\*,DOCUMENTACAO\*"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}NKR GERAL.nkr"; DestDir: "{app}\resources"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\Nord Kontakt Bridge"; Filename: "{app}\Nord Kontakt Bridge.exe"
Name: "{autodesktop}\Nord Kontakt Bridge"; Filename: "{app}\Nord Kontakt Bridge.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Nord Kontakt Bridge.exe"; Description: "Abrir Nord Kontakt Bridge"; Flags: nowait postinstall skipifsilent
