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

' Check Go exists
If Not objFSO.FileExists(goExe) Then
    MsgBox "Error: Go compiler not found" & vbCrLf & goExe, vbCritical
    WScript.Quit 1
End If

' Check main.go exists
If Not objFSO.FileExists(mainGoPath) Then
    MsgBox "Error: main.go not found", vbCritical
    WScript.Quit 1
End If

' Check if dependencies are installed
Dim pipCmd, result
pipCmd = "pip show streamlit"
On Error Resume Next
result = WshShell.Run(pipCmd, 0, True)
On Error GoTo 0

If result <> 0 Then
    ' Streamlit not installed, install dependencies
    MsgBox "Installing dependencies... This may take a few minutes.", vbInformation
    WshShell.Run "pip install -r """ & reqFile & """", 1, True
End If

' Step 1: Start Go backend in background
Dim goCmd
goCmd = """" & goExe & """ run """ & mainGoPath & """"
WshShell.Run goCmd, 0, True

' Wait for backend
WScript.Sleep 3000

' Step 2: Open index.html
Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

' Step 3: Start Streamlit Dashboard
If objFSO.FileExists(dashboardPyPath) Then
    Dim streamlitCmd
    streamlitCmd = "cmd /c start cmd /k streamlit run """ & dashboardPyPath & """"
    WshShell.Run streamlitCmd, 1, False
    
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "1. Main Interface: index.html" & vbCrLf & _
           "2. Dashboard: http://localhost:8501", vbInformation
Else
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "Main Interface: index.html", vbInformation
End If

Set WshShell = Nothing
Set objFSO = Nothing