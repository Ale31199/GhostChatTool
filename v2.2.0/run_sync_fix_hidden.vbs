Set sh = CreateObject("WScript.Shell")
base = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd.exe /c """ & base & "\sync_fix_now.cmd"""
sh.Run cmd, 0, False
