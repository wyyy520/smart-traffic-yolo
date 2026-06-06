' Smart Traffic Agent System - Launcher
Option Explicit

Dim WshShell, objFSO
Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

Dim goExe, mainGoPath, htmlPath, dashboardPyPath, reqFile
goExe = "C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe"
mainGoPath = scriptDir & "\go_backend\main.go"
htmlPath = scriptDir & "\web\html\index.html"
dashboardPyPath = scriptDir & "\dashboard.py"
reqFile = scriptDir & "\requirements.txt"

' Check Go
If Not objFSO.FileExists(goExe) Then
    MsgBox "Error: Go compiler not found" & vbCrLf & goExe, vbCritical
    WScript.Quit 1
End If

' Check main.go
If Not objFSO.FileExists(mainGoPath) Then
    MsgBox "Error: main.go not found", vbCritical
    WScript.Quit 1
End If

' Check dashboard.py
If Not objFSO.FileExists(dashboardPyPath) Then
    MsgBox "Error: dashboard.py not found", vbCritical
    WScript.Quit 1
End If

' Install dependencies using python -m pip
MsgBox "Checking and installing dependencies...", vbInformation
WshShell.Run "python -m pip install -r """ & reqFile & """", 1, True

' Start Go backend
Dim goCmd
goCmd = """" & goExe & """ run """ & mainGoPath & """"
WshShell.Run goCmd, 0, True

' Wait
WScript.Sleep 3000

' Open index.html
Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

' Start Dashboard using python -m streamlit
If objFSO.FileExists(dashboardPyPath) Then
    Dim streamlitCmd
    streamlitCmd = "cmd /c start cmd /k python -m streamlit run """ & dashboardPyPath & """"
    WshShell.Run streamlitCmd, 1, False
    
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "1. Main Interface: index.html" & vbCrLf & _
           "2. Dashboard: http://localhost:8501", vbInformation
End If

Set WshShell = Nothing
Set objFSO = Nothing