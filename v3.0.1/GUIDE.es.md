# GhostChatTool v3.0.1 — Guía en español

[English — predeterminado](GUIDE.en.md) · [Italiano](GUIDE.it.md) · Español · [Français](GUIDE.fr.md) · [Deutsch](GUIDE.de.md)

## Qué versión es

La v3.0.1 observa los registros locales: **no necesita Chrome ni otro navegador abierto**. No es la herramienta manual v1 ni la extensión v4. El código original se conserva; este paquete añade controles y documentación. Los lanzadores desactivan la recarga automática experimental y los nudges. Si la lista permanece desactualizada, cierra la aplicación completamente y vuelve a abrirla tú mismo.

Es una solución experimental no oficial, sin relación con OpenAI. No garantiza eliminar todos los chats fantasma, ni siquiera después de reiniciar la aplicación. Solo repara si una misma línea del registro contiene el ID del chat y `conversation_deleted` o `conversation deleted`. Sin ese evento no hay reparación. No consulta el servidor ni realiza dos comprobaciones del servidor.

## Preparación e instalación

Necesitas Windows 10/11, Python 3.10+ disponible como `py` o `python`, Windows PowerShell y `%USERPROFILE%\.codex\sqlite\codex-dev.db`. No necesitas paquetes adicionales ni credenciales. Extrae el ZIP completo antes de ejecutar los archivos.

Si ya tienes v3.0.1 funcionando, no instales otra copia. Para migrar, detén la versión anterior y desactiva su inicio automático siguiendo sus instrucciones. Windows + R, `shell:startup`, muestra la carpeta de inicio. No borres entradas desconocidas ni `.codex`. El instalador rechaza entradas GhostChat existentes, un observador activo o una carpeta de destino existente. No elimina automáticamente v4 ni extensiones.

1. Abre `GUIDE.html` para elegir idioma. `DRY_RUN.cmd` muestra candidatos sin que ese comando modifique la base de datos. Otro observador activo todavía puede escribir; detenlo para una prueba completamente de solo lectura.
2. Ejecuta `INSTALL.cmd`, lee la advertencia y escribe `INSTALL`. Se instala en `%LOCALAPPDATA%\GhostChatTool-v3.0.1`, crea `GhostChatTool v3.0.1.lnk` en Inicio del usuario y arranca el observador oculto.
3. Desde la **carpeta instalada**, utiliza `STATUS.cmd`, `STOP.cmd` y `START.cmd`. No requiere administrador. No es un servicio: Windows y la sesión del usuario deben estar activos. STOP no desactiva el próximo inicio de sesión.

Si aparece un error, comprueba el estado antes de asumir que funciona. No eludas las políticas de seguridad de tu organización.

## Prueba con un chat desechable

1. Crea un chat de prueba fuera de Projects y comprueba que aparece en el PC.
2. Elimina únicamente ese chat desde el teléfono. La eliminación en el servidor es permanente. Mantén la aplicación del PC conectada.
3. Busca en `STATUS.cmd` una fecha de reparación nueva y un contador mayor que cero. El manifiesto privado identifica el chat reparado. Una reparación anterior no demuestra que este chat haya sido reparado.
4. Si sigue visible, sal completamente de la aplicación, incluidos los procesos en segundo plano, y vuelve a abrirla desde Inicio. No necesitas un botón Recargar; GhostChat no fuerza el cierre.
5. Sin una reparación nueva, detén el observador, cierra la aplicación y ejecuta `DRY_RUN.cmd`. Sin evento válido, no se elimina la entrada. `REPAIR_ONCE.cmd` permite una reparación puntual de candidatos confirmados, con aplicación y observador cerrados. Después abre la aplicación y ejecuta `START.cmd`.

El sondeo suele ser cada tres segundos y el descubrimiento de registros cada quince, pero **no es una garantía de tiempo**. La aplicación puede no generar nunca el evento. No pruebes eliminando más chats importantes.

## Copias, recuperación y desinstalación

Copias: `%USERPROFILE%\.codex\sqlite\ghostchat-backups`. Estado, registros y manifiestos privados: `%USERPROFILE%\.codex\sqlite\ghostchat-patch`. Se conservan hasta 20 copias tras las reparaciones, compartidas con versiones anteriores. Guarda aparte las importantes.

`RESTORE.cmd` detiene el observador de este paquete, exige cerrar completamente la aplicación y pide escribir `RESTORE`. Restaura la copia más reciente de **toda la base de datos local**, no un solo chat, y crea una copia previa. Puede revertir otros cambios locales. El observador queda detenido, pero el inicio automático sigue activo; al arrancar puede repetir la reparación. Para desactivar ese inicio durante la recuperación, usa primero `UNINSTALL.cmd` y luego restaura desde los archivos conservados.

`UNINSTALL.cmd` detiene el observador y elimina solo el acceso directo de inicio de este paquete. Conserva programa, base de datos, registros y copias. No revierte reparaciones ni desinstala otras versiones o extensiones.

## Límites y privacidad

Los lanzadores comprueban las columnas antes de arrancar; el código original solo excluye Projects si existe `project_id`. No hay garantía universal de bloqueo seguro ante futuros cambios del esquema. La copia precede a la reparación; `PRAGMA integrity_check` se ejecuta después de confirmar el cambio. No verifica el servidor ni garantiza una reversión automática. Deja de usar la herramienta si una actualización rompe la compatibilidad.

No lee/exporta cookies, tokens ni `auth.json`, no llama a API privadas ni modifica/inyecta código en el ejecutable. Los registros, manifiestos y copias pueden contener datos personales: no los compartas sin censurarlos. La publicación contiene solo código, guías y pruebas sintéticas. Consulta `README.md` y `TEST_REPORT.md` para los límites técnicos y las comprobaciones realizadas.
