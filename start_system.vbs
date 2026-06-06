' ============================================================================
' Smart Traffic Agent System - Launcher (No Window Version)
' ============================================================================

Option Explicit

Dim WshShell, objFSO
Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

Dim goExe, mainGoPath, htmlPath
goExe = "C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe"
mainGoPath = scriptDir & "\go_backend\main.go"
htmlPath = scriptDir & "\web\html\index.html"

If Not objFSO.FileExists(goExe) Then
    MsgBox "Error: Go compiler not found" & vbCrLf & goExe, vbCritical
    WScript.Quit 1
End If

If Not objFSO.FileExists(mainGoPath) Then
    MsgBox "Error: main.go not found" & vbCrLf & mainGoPath, vbCritical
    WScript.Quit 1
End If

If Not objFSO.FileExists(htmlPath) Then
    MsgBox "Error: index.html not found" & vbCrLf & htmlPath, vbCritical
    WScript.Quit 1
End If

Dim cmd
cmd = """" & goExe & """ run """ & mainGoPath & """"

WshShell.Run cmd, 0, True

WScript.Sleep 3000

Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

Set WshShell = Nothing
Set objFSO = Nothing
