#define APP_NAME "Transcriber"
#define APP_VERSION "1.0.0"
#define APP_PUBLISHER "Transcriber Project"
#define APP_EXE "Transcriber.exe"

[Setup]
AppId={{7D8A91B1-466A-4B89-9678-40BB7F470EC4}
AppName={#APP_NAME}
AppVersion={#APP_VERSION}
AppVerName={#APP_NAME} {#APP_VERSION}
AppPublisher={#APP_PUBLISHER}
DefaultDirName={localappdata}\Programs\{#APP_NAME}
DefaultGroupName={#APP_NAME}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=Transcriber-Setup-{#APP_VERSION}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
UninstallDisplayIcon={app}\{#APP_EXE}
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Ярлыки:"; Flags: unchecked
Name: "contextmenu"; Description: "Добавить команды в контекстное меню Проводника"; GroupDescription: "Интеграция с Проводником:"; Flags: checkedonce

[Files]
Source: "..\dist\Transcriber\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Transcriber"; Filename: "{app}\{#APP_EXE}"
Name: "{group}\Документация"; Filename: "{app}\README.md"
Name: "{autodesktop}\Transcriber"; Filename: "{app}\{#APP_EXE}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp3\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.wav\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.ogg\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.opus\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.m4a\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.aac\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.flac\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mp4\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.mkv\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.webm\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.html\shell\TranscriberChatExport"; ValueType: string; ValueName: ""; ValueData: "Добавить транскрипции в экспорт чата"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.html\shell\TranscriberChatExport"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.html\shell\TranscriberChatExport\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ChatExportParser.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.htm\shell\TranscriberChatExport"; ValueType: string; ValueName: ""; ValueData: "Добавить транскрипции в экспорт чата"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.htm\shell\TranscriberChatExport"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.htm\shell\TranscriberChatExport\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ChatExportParser.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberChatExport"; ValueType: string; ValueName: ""; ValueData: "Добавить транскрипции в экспорт чата"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberChatExport"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\shell\TranscriberChatExport\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ChatExportParser.exe"" ""%1"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToMarkdown"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в Markdown"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToMarkdown"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToMarkdown\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format md --force ""%V"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToJson"; ValueType: string; ValueName: ""; ValueData: "Транскрибировать в JSON"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToJson"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberToJson\command"; ValueType: string; ValueName: ""; ValueData: """{app}\TranscriberCLI.exe"" --format json --force ""%V"""; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberChatExport"; ValueType: string; ValueName: ""; ValueData: "Добавить транскрипции в экспорт чата"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberChatExport"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Transcriber.exe"; Tasks: contextmenu
Root: HKA; Subkey: "Software\Classes\Directory\Background\shell\TranscriberChatExport\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ChatExportParser.exe"" ""%V"""; Tasks: contextmenu
[Run]
Filename: "{app}\Transcriber.exe"; Description: "Запустить Transcriber"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"