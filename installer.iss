[Setup]
AppName=FimozBot
AppVersion=1.0
DefaultDirName={pf}\FimozBot
DefaultGroupName=FimozBot
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\run.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config\*"; DestDir: "{app}\config"; Flags: recursesubdirs createallsubdirs
Source: "tokens.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FimozBot"; Filename: "{app}\run.exe"

[Run]
Filename: "{app}\run.exe"; Description: "Run FimozBot"; Flags: nowait postinstall skipifsilent
