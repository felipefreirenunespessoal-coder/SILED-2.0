Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
basePath = fso.GetParentFolderName(WScript.ScriptFullName)
launcher = basePath & "\iniciar.bat"
If fso.FileExists(launcher) Then
    shell.Run Chr(34) & launcher & Chr(34), 1, False
Else
    MsgBox "Arquivo iniciar.bat nao encontrado na pasta do projeto.", 16, "SILED"
End If
