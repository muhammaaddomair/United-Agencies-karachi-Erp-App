[Setup]
AppName=United Agencies karachi
AppVersion=1.0.0
AppPublisher=TechSaws
DefaultDirName={autopf}\United Agencies karachi
DefaultGroupName=United Agencies karachi
DisableProgramGroupPage=no
OutputDir=..\dist\installer_setup
OutputBaseFilename=UnitedAgenciesKarachiSetup
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\installer\United Agencies karachi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\United Agencies karachi"; Filename: "{app}\United Agencies karachi.exe"
Name: "{commondesktop}\United Agencies karachi"; Filename: "{app}\United Agencies karachi.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\United Agencies karachi.exe"; Description: "Launch United Agencies karachi"; Flags: nowait postinstall skipifsilent
