[Setup]
AppName=FimozBot
AppVersion=1.0.0
AppPublisher=FimozBot
AppPublisherURL=https://github.com/portwavexm/FimozBot
AppSupportURL=https://github.com/portwavexm/FimozBot/issues
AppUpdatesURL=https://github.com/portwavexm/FimozBot/releases
DefaultDirName={pf}\FimozBot
DefaultGroupName=FimozBot
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\FimozBot.ico
OutputDir=dist
OutputBaseFilename=FimozBot-Setup
SetupIconFile=
WizardStyle=modern
WizardResizable=yes

; Installation requires approximately 500MB
ExtraDiskSpaceRequired=536870912

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Components]
Name: "bot"; Description: "FimozBot Application"; Types: full compact custom; Flags: fixed
Name: "shortcut"; Description: "Desktop Shortcut"; Types: full
Name: "startmenu"; Description: "Start Menu Shortcut"; Types: full compact

[Types]
Name: "full"; Description: "Full Installation"
Name: "compact"; Description: "Compact Installation"
Name: "custom"; Description: "Custom Installation"; Flags: iscustom

[Files]
; Bot files
Source: ".git\*"; DestDir: "{app}\.git"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "cogs\*"; DestDir: "{app}\cogs"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "config\*"; DestDir: "{app}\config"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "lavalink-server\*"; DestDir: "{app}\lavalink-server"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "scripts\*"; DestDir: "{app}\scripts"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "utils\*"; DestDir: "{app}\utils"; Flags: recursesubdirs createallsubdirs ignoreversion

; Main files
Source: "main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "run.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: ".gitignore"; DestDir: "{app}"; Flags: ignoreversion
Source: "Dockerfile"; DestDir: "{app}"; Flags: ignoreversion
Source: "docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_DEPLOY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_shortcuts.md"; DestDir: "{app}"; Flags: ignoreversion

; Scripts
Source: "install.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "install.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "start_bot.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "start_bot.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "create_shortcuts.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\.venv"
Name: "{app}\config"

[Icons]
Name: "{group}\FimozBot"; Filename: "{app}\start_bot.bat"; WorkingDir: "{app}"; Comment: "Start Discord Music Bot"; IconFilename: "{sys}\cmd.exe"
Name: "{group}\README"; Filename: "{app}\README.md"
Name: "{group}\Uninstall FimozBot"; Filename: "{uninstallexe}"
Name: "{commondesktop}\FimozBot"; Filename: "{app}\start_bot.bat"; Components: "shortcut"; WorkingDir: "{app}"; Comment: "Start Discord Music Bot"; IconFilename: "{sys}\cmd.exe"

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\install.ps1"""; Description: "Complete Installation"; Flags: postinstall skipifsilent runhidden
Filename: "{app}\README.md"; Description: "View README"; Flags: postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\.git"

[Code]
procedure InitializeWizard;
begin
  WizardForm.LicenseAcceptedRadio.Checked := True;
  WizardForm.LicenseNotAcceptedRadio.Visible := False;
  WizardForm.LicenseAcceptedRadio.Visible := False;
end;
