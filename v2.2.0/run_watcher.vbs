Set sh = CreateObject("WScript.Shell")
base = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd.exe /c """ & base & "\start_ghostchat_watcher_hidden.cmd"""
sh.Run cmd, 0, False
