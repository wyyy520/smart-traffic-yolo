' Smart Traffic Agent System - Launcher
Option Explicit

Dim WshShell, objFSO
Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

Dim goExe, mainGoPath, htmlPath, dashboardPyPath
goExe = "C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe"
mainGoPath = scriptDir & "\go_backend\main.go"
htmlPath = scriptDir & "\web\html\index.html"
dashboardPyPath = scriptDir & "\dashboard.py"

' Check files exist
If Not objFSO.FileExists(goExe) Then
    MsgBox "Error: Go not found at:" & vbCrLf & goExe, vbCritical
    WScript.Quit 1
End If

If Not objFSO.FileExists(mainGoPath) Then
    MsgBox "Error: main.go not found", vbCritical
    WScript.Quit 1
End If

' Step 1: Start Go backend in background (no window)
Dim goCmd
goCmd = """" & goExe & """ run """ & mainGoPath & """"
WshShell.Run goCmd, 0, True

' Wait for backend to start
WScript.Sleep 3000

' Step 2: Open index.html
Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

' Step 3: Start Streamlit Dashboard
If objFSO.FileExists(dashboardPyPath) Then
    Dim streamlitCmd
    streamlitCmd = "cmd /c start cmd /k streamlit run """ & dashboardPyPath & """ --server.headless true"
    WshShell.Run streamlitCmd, 1, False
    
    ' Show success message
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "1. Main Interface: index.html (opened)" & vbCrLf & _
           "2. Dashboard: http://localhost:8501 (starting...)" & vbCrLf & vbCrLf & _
           "Note: If Dashboard shows error, run:" & vbCrLf & _
           "  pip install -r requirements.txt", vbInformation, "Smart Traffic System"
Else
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "Main Interface: index.html (opened)" & vbCrLf & vbCrLf & _
           "Dashboard file not found.", vbInformation, "Smart Traffic System"
End If

Set WshShell = Nothing
Set objFSO = Nothing