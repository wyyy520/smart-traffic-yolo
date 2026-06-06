' ============================================================================
' Smart Traffic Agent System - Launcher
' ============================================================================

Option Explicit

Dim WshShell, objFSO
Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 路径配置
Dim goExe, mainGoPath, htmlPath, dashboardPyPath
goExe = "C:\Users\13069\go\pkg\mod\golang.org\toolchain@v0.0.1-go1.26.3.windows-amd64\bin\go.exe"
mainGoPath = scriptDir & "\go_backend\main.go"
htmlPath = scriptDir & "\web\html\index.html"
dashboardPyPath = scriptDir & "\dashboard.py"

' 检查文件
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

' 启动 Go 后端（无窗口）
Dim goCmd
goCmd = """" & goExe & """ run """ & mainGoPath & """"
WshShell.Run goCmd, 0, True

' 等待后端启动
WScript.Sleep 3000

' 打开 index.html
Dim htmlUrl
htmlUrl = "file:///" & Replace(htmlPath, "\", "/")
WshShell.Run "cmd /c start " & htmlUrl, 1, False

' 检查是否需要启动 Dashboard
If objFSO.FileExists(dashboardPyPath) Then
    ' 启动 Streamlit Dashboard（新窗口）
    Dim streamlitCmd
    streamlitCmd = "cmd /c start cmd /k streamlit run """ & dashboardPyPath & """"
    WshShell.Run streamlitCmd, 1, False
    
    ' 提示用户 Dashboard 地址
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "- Main Interface: index.html (已打开)" & vbCrLf & _
           "- Dashboard: http://localhost:8501 (即将打开)" & vbCrLf & vbCrLf & _
           "注意: Dashboard 需要安装依赖:" & vbCrLf & _
           "  pip install -r requirements.txt", vbInformation, "Smart Traffic System"
Else
    MsgBox "System Started!" & vbCrLf & vbCrLf & _
           "Main Interface: index.html (已打开)" & vbCrLf & vbCrLf & _
           "Dashboard 文件未找到，请手动启动:" & vbCrLf & _
           "  streamlit run dashboard.py", vbInformation, "Smart Traffic System"
End If

Set WshShell = Nothing
Set objFSO = Nothing