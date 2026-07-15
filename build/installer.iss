; HiveOS — Inno Setup Script for Windows MSI Installer
; Phase D of the Windows Native roadmap.
;
; Prerequisites:
;   1. Run build/build_exe.py first (produces dist/HiveOS/)
;   2. Install Inno Setup from https://jrsoftware.org/isdl.php
;   3. Right-click this file → Compile (or run iscc from CLI)
;
; CLI: "C:\Program Files (x86)\Inno Setup 6\iscc.exe" build\installer.iss

#define MyAppName "HiveOS"
#define MyAppVersion "0.11.0"
#define MyAppPublisher "HiveOS"
#define MyAppURL "https://github.com/hossein1377mobini/hiveos-financial-brain"
#define MyAppExeName "HiveOS.exe"

[Setup]
; Basic metadata
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installer output
OutputDir=..\dist
OutputBaseFilename=HiveOS-Setup-{#MyAppVersion}
SetupIconFile=..\build\hiveos.ico
Compression=lzma2
SolidCompression=yes

; Windows target
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

; Update support
VersionInfoVersion={#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "farsi"; MessagesFile: "compiler:Languages\Persian.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "Start HiveOS when &Windows starts"; GroupDescription: "Startup options:"

[Files]
; Main application files
Source: "..\dist\HiveOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Domains (knowledge blueprints)
Source: "..\domains\*"; DestDir: "{app}\domains"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
; Launch after install (optional)
Filename: "{app}\{#MyAppExeName}"; Description: "Launch HiveOS"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
; Clean up user data
Filename: "{cmd}"; Parameters: "/c rmdir /s /q ""{userappdata}\.hiveos"""; Flags: runhidden

[Code]
{Check for .NET runtime and Windows version}

function IsWindows10OrLater: Boolean;
begin
  Result := (GetWindowsVersion >= $0A00);  // 10.0
end;

function InitializeSetup: Boolean;
begin
  if not IsWindows10OrLater then
  begin
    SuppressibleMsgBox(
      'HiveOS requires Windows 10 or later.' + #13#10 +
      'Your system does not meet this requirement.',
      mbError, MB_OK, IDOK
    );
    Result := False;
    Exit;
  end;
  Result := True;
end;
