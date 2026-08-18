' Lanzador oculto de watchdog.cmd.
'
' El Task Scheduler no tiene una opcion de "ventana oculta" para un .cmd cuando la
' tarea corre en la sesion del usuario, asi que una consola parpadearia cada 3
' minutos encima de la pantalla de recepcion, que suele estar en modo kiosco con un
' cliente mirandola. El `0` del Run es el modo oculto; el `False` es para no esperar
' a que termine.
CreateObject("WScript.Shell").Run _
    "cmd /c """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\watchdog.cmd""", 0, False
