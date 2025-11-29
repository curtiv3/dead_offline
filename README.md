# deadcase_tools_offline

Offline Toolkit for the DeadCaseAI horror project. The goal is to analyze footage locally and generate edit instructions without any external AI or API calls.

## Struktur
```
deadcase_tools_offline/
  analyze_video.py        # Video analysieren, Shots & Metadaten → JSON
  offline_director.py     # Offline-Regie-Logik: Shots → Edit Map (JSON)
  examples/
    sample_shots.json
    sample_edit_map.json
  resolve/
    apply_edits_in_resolve.py  # DaVinci-Stub: Marker/Platzhalter setzen
```

## Nutzung
1. **Video analysieren:**
   ```bash
   python deadcase_tools_offline/analyze_video.py --input input.mp4 --output shots.json
   ```

2. **Offline-Regieplan erstellen:**
   ```bash
   python deadcase_tools_offline/offline_director.py --shots shots.json --output edit_map.json --style horror_truecrime
   ```
   Unterstützte Styles (heuristisch): `horror_truecrime`, `analog_horror`.

3. **In DaVinci Resolve anwenden (Stub):**
   - Script in der Resolve-Konsole ausführen: `deadcase_tools_offline/resolve/apply_edits_in_resolve.py`
   - Pfad zu `edit_map.json` angeben.
   - Marker erscheinen an den konfigurierten Zeitpunkten. Effekte können später ergänzt werden.

## Beispiele
- `examples/sample_shots.json` liefert 4 Beispiel-Shots.
- `examples/sample_edit_map.json` zeigt die daraus abgeleiteten Edit-Events.

## Anforderungen
- Python 3.10+
- Dependencies: `opencv-python`, `numpy`

Beide Hauptskripte nutzen einfache Heuristiken (Histogramm-Differenzen für Shots, Schwellenwerte für Flash/Glitch/Marker) und laufen komplett offline.
