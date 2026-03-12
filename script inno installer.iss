[Setup]
AppName=Gestiune clienti
AppVersion=1.0
AppPublisher=Ciprian Pop
DefaultDirName={pf}\GestiuneClienti
DefaultGroupName=Gestiune clienti
OutputDir=Output
OutputBaseFilename=Setup_GestiuneClienti
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Creează icon pe Desktop"; Flags: unchecked

[Files]
Source: "dist\Gestiune_clienti_sqlite_portabil_v3\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gestiune clienti"; Filename: "{app}\Gestiune_clienti_sqlite_portabil_v3.exe"
Name: "{commondesktop}\Gestiune clienti"; Filename: "{app}\Gestiune_clienti_sqlite_portabil_v3.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Gestiune_clienti_sqlite_portabil_v3.exe"; Description: "Pornește aplicația"; Flags: nowait postinstall skipifsilent