# GhostChatTool v3.0.1 — Deutsche Anleitung

[English — Standard](GUIDE.en.md) · [Italiano](GUIDE.it.md) · [Español](GUIDE.es.md) · [Français](GUIDE.fr.md) · Deutsch

## Welche Version ist das?

v3.0.1 überwacht lokale Protokolle: **Chrome oder ein anderer Browser muss nicht geöffnet sein**. Dies ist weder das manuelle Auswahlwerkzeug v1 noch die Browser-Erweiterung v4. Der ursprüngliche Programmcode bleibt unverändert; dieses Paket ergänzt Startbefehle und Anleitungen. Die mitgelieferten Starter deaktivieren experimentelles automatisches Neuladen und Nudges. Wenn die Liste veraltet bleibt, beenden Sie die App vollständig und öffnen sie selbst erneut.

Dies ist eine inoffizielle, experimentelle Umgehungslösung ohne Verbindung zu OpenAI. Nicht jeder auf einem anderen Gerät gelöschte Chat verschwindet garantiert, auch nicht nach erneutem Öffnen. Eine Reparatur erfolgt nur, wenn dieselbe Protokollzeile die Chat-ID und `conversation_deleted` oder `conversation deleted` enthält. Ohne dieses Ereignis keine Reparatur. Es findet keine direkte Serverprüfung und keine doppelte Serverkontrolle statt.

## Vorbereitung und Installation

Erforderlich: Windows 10/11, Python 3.10+ als `py` oder `python`, Windows PowerShell und `%USERPROFILE%\.codex\sqlite\codex-dev.db`. Keine zusätzlichen Python-Pakete oder Zugangsdaten. Entpacken Sie die ZIP vollständig, bevor Sie Dateien ausführen.

Wenn v3.0.1 bereits funktioniert, installieren Sie keine zweite Kopie. Für einen Wechsel zuerst die alte Überwachung beenden und deren Autostart nach ihrer Anleitung deaktivieren. Windows + R, `shell:startup`, öffnet den Autostartordner. Keine unbekannten Einträge und niemals `.codex` löschen. Der Installer lehnt vorhandene GhostChat-Autostarteinträge, eine laufende Überwachung oder einen vorhandenen Zielordner ab. Er entfernt weder v4 noch Browser-Erweiterungen automatisch.

1. Öffnen Sie `GUIDE.html` zur Sprachauswahl. `DRY_RUN.cmd` zeigt Kandidaten an, ohne selbst die Datenbank zu ändern. Eine andere laufende Instanz kann weiterhin schreiben; für einen vollständig schreibgeschützten Test vorher stoppen.
2. Starten Sie `INSTALL.cmd`, lesen Sie die Warnung und geben Sie `INSTALL` ein. Installation nach `%LOCALAPPDATA%\GhostChatTool-v3.0.1`, Erstellung von `GhostChatTool v3.0.1.lnk` im Benutzer-Autostart und Start der unsichtbaren Überwachung.
3. Verwenden Sie `STATUS.cmd`, `STOP.cmd` und `START.cmd` im **installierten Ordner**. Keine Administratorrechte nötig. Kein Windows-Dienst: Windows und die Benutzersitzung müssen aktiv sein. STOP deaktiviert nicht den Start bei der nächsten Anmeldung.

Bei Fehlern zuerst Meldung und Status prüfen, nicht von einer erfolgreichen Installation ausgehen. Sicherheitsrichtlinien Ihrer Organisation nicht umgehen.

## Mit einem entbehrlichen Chat testen

1. Erstellen Sie außerhalb von Projects einen Testchat und prüfen Sie, ob er am PC sichtbar ist.
2. Löschen Sie nur diesen Testchat am Telefon. Das Löschen auf dem Server ist endgültig. Lassen Sie die PC-App online.
3. Prüfen Sie `STATUS.cmd` auf einen neuen Reparaturzeitpunkt und eine Anzahl größer als null. Das private Manifest nennt den reparierten Chat. Ein früherer Reparatureintrag beweist nichts für diesen Test.
4. Bleibt der Chat sichtbar, beenden Sie die App samt Hintergrundprozessen vollständig und öffnen sie erneut über Start. Eine Schaltfläche zum Neuladen ist nicht erforderlich; GhostChat erzwingt kein Beenden.
5. Ohne neuen Reparatureintrag die Überwachung stoppen, die App schließen und `DRY_RUN.cmd` ausführen. Ohne gültiges Ereignis bleibt der Eintrag unverändert. `REPAIR_ONCE.cmd` repariert bestätigte Kandidaten einmalig, wenn App und Überwachung geschlossen sind. Danach die App öffnen und `START.cmd` verwenden.

Normalerweise wird alle drei Sekunden geprüft und etwa alle fünfzehn Sekunden nach Protokolldateien gesucht. Das ist **keine Zeitgarantie**: Die App erzeugt das nötige Ereignis möglicherweise nie. Löschen Sie zum Testen keine weiteren wichtigen Chats.

## Sicherungen, Wiederherstellung und Deinstallation

Sicherungen: `%USERPROFILE%\.codex\sqlite\ghostchat-backups`. Privater Status, Protokolle und Manifeste: `%USERPROFILE%\.codex\sqlite\ghostchat-patch`. Nach Reparaturen bleiben bis zu 20 Sicherungen erhalten, gemeinsam mit älteren Versionen. Wichtige Kopien separat aufbewahren.

`RESTORE.cmd` stoppt die Überwachung dieses Pakets, verlangt eine vollständig geschlossene App und die Eingabe `RESTORE`. Die neueste Sicherung der **gesamten lokalen Datenbank** wird wiederhergestellt, nicht nur ein Chat; zuvor wird eine weitere Sicherung erstellt. Andere lokale Änderungen können verloren gehen. Die Überwachung bleibt gestoppt, der Autostart jedoch aktiv; beim nächsten Start kann dieselbe Reparatur erneut erfolgen. Zum Deaktivieren während der Wiederherstellung zuerst `UNINSTALL.cmd` nutzen, dann aus den erhaltenen Dateien wiederherstellen.

`UNINSTALL.cmd` stoppt die Überwachung und entfernt nur die Autostartverknüpfung dieses Pakets. Programmdateien, Datenbank, Protokolle und Sicherungen bleiben erhalten. Frühere Reparaturen werden nicht rückgängig gemacht; andere Versionen und Erweiterungen werden nicht entfernt.

## Grenzen und Datenschutz

Die Starter prüfen vor dem Start erforderliche Spalten; der ursprüngliche Code schließt Projects nur bei vorhandener Spalte `project_id` aus. Ein sicheres Abbrechen bei jeder zukünftigen Schemaänderung ist nicht garantiert. Vor der Reparatur entsteht eine Sicherung; `PRAGMA integrity_check` erfolgt erst nach dem bestätigten Datenbankeingriff. Er prüft nicht den Server und garantiert keine automatische Rücknahme. Bei Inkompatibilität nach einem App-Update das Werkzeug nicht weiterverwenden.

Keine Cookies, Tokens oder `auth.json` werden gelesen/exportiert, keine privaten APIs direkt aufgerufen und kein Code in die ausführbare App-Datei injiziert. Protokolle, Manifeste und Sicherungen können persönliche Daten enthalten: niemals unbereinigt teilen. Die Veröffentlichung enthält nur Code, Anleitungen und synthetische Tests. Technische Grenzen und durchgeführte Prüfungen stehen in `README.md` und `TEST_REPORT.md`.
