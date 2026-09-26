#define AppName "LimitsHalo"
#define AppVersion "0.1.0-beta"
#define AppExe "LimitsHalo.exe"

[Setup]
AppId={{B383A087-86D8-4B7E-9829-BA30F137747F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Arden Works Project
AppPublisherURL=https://arden.ws
AppSupportURL=https://github.com/arden-works/
AppUpdatesURL=https://github.com/arden-works/
AppCopyright=Copyright (c) 2026 Arden Works
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=..\artifacts\release
OutputBaseFilename=LimitsHalo-0.1.0-beta-Setup
SetupIconFile=..\assets\limitshalo-brand.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
CloseApplications=yes

[Messages]
BeveledLabel=Arden Works Project

[Files]
Source: "..\dist\LimitsHalo\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\LimitsHalo"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall LimitsHalo"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch LimitsHalo"; Flags: nowait postinstall skipifsilent

[Code]
procedure WelcomeLinkClick(Sender: TObject; const Link: String; LinkType: TSysLinkType);
var
  ErrorCode: Integer;
begin
  if LinkType = sltURL then
    ShellExec('open', Link, '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

procedure InitializeWizard;
var
  BrandLabel: TNewStaticText;
  LinkLabel: TNewLinkLabel;
begin
  BrandLabel := TNewStaticText.Create(WizardForm);
  BrandLabel.Parent := WizardForm.WelcomePage;
  BrandLabel.Left := WizardForm.WelcomeLabel2.Left;
  BrandLabel.Top := WizardForm.WelcomeLabel2.Top + WizardForm.WelcomeLabel2.Height + ScaleY(16);
  BrandLabel.AutoSize := True;
  BrandLabel.Caption := 'Arden Works Project';
  BrandLabel.Font.Assign(WizardForm.WelcomeLabel1.Font);
  BrandLabel.Font.Style := [fsBold];

  LinkLabel := TNewLinkLabel.Create(WizardForm);
  LinkLabel.Parent := WizardForm.WelcomePage;
  LinkLabel.Left := BrandLabel.Left;
  LinkLabel.Top := BrandLabel.Top + BrandLabel.Height + ScaleY(4);
  LinkLabel.AutoSize := True;
  LinkLabel.Caption := '<a href="https://arden.ws">arden.ws</a>  |  <a href="https://github.com/arden-works/">GitHub</a>';
  LinkLabel.OnLinkClick := @WelcomeLinkClick;
end;
