Set WshShell = CreateObject("WScript.Shell")
If WScript.Arguments.Count = 0 Then
  WScript.Quit 1
End If
cmd = "cmd /c """ & WScript.Arguments(0) & """"
WshShell.Run cmd, 0, False
