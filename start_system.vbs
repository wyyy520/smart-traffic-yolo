' Smart Traffic Agent System - Launcher
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
    MsgBox "Error: Go not found", vbCritical
    WScript.Quit 1
End If

If Not objFSO.FileExists(mainGoPath) Then
    MsgBox "Error: main.go not found", vbCritical
    WScript.Quit 1
End If

' Start Go backend
Dim goCmd
goCmd = """" & goExe & """ run """ & mainGoPath & """"
WshShell.Run goCmd, 0, True

WScript.Sleep 3000

' Open index.html
Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

' Open Dashboard
Dim dashboardPyPath
dashboardPyPath = scriptDir & "\dashboard.py"
If objFSO.FileExists(dashboardPyPath) Then
    WshShell.Run "cmd /c start cmd /k streamlit run """ & dashboardPyPath & """", 1, False
    MsgBox "System Started!" & vbCrLf & vbCrLf & "1. Main Interface: index.html" & vbCrLf & "2. Dashboard: http://localhost:8501", vbInformation
End If

Set WshShell = Nothing
Set objFSO = Nothing