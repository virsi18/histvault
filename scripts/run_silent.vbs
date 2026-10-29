Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName) & "\.."
WshShell.CurrentDirectory = strDir
WshShell.Run "py -m histvault.cli.main watch -i 30", 0, False
Set WshShell = Nothing
Set fso = Nothing
