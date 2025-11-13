

# vCard2PDF v1.0

vCard2PDF ist ein kleines, aber sehr praktisches Tool für macOS, um eine oder mehrere `.vcf`‑Visitenkarten automatisch in sauber formatierte PDF‑Dateien umzuwandeln.  
Der Fokus liegt auf einer klaren, deutschsprachigen Darstellung im Stil einer strukturierten Kontaktkarte – inklusive Foto, einheitlicher Einrückung, Social‑Media‑Links und korrekter Typ‑Erkennung (Geschäftlich/Privat/Mobil usw.).

---

## ✨ Funktionen

- Liest **vCard 3.0** Dateien (`.vcf`)
- Konvertiert jeden Kontakt in eine **einzelne, schön strukturierte PDF**
- Unterstützt:
  - Telefonnummern
  - E‑Mail‑Adressen
  - Adressen
  - Websites
  - Social‑Media‑Profile
- Erkennt automatisch alle TYPE‑Parameter des vCard‑Standards
- Klickbare Social‑Media‑Links im PDF
- Foto aus der vCard wird automatisch eingebettet
- Einheitliche typografische Struktur (Labels fett, Werte bündig ausgerichtet)
- Terminal‑Ausgabe in klarer Form:
  - Produktname
  - Status pro Datei
  - Lesbare Trennungen der einzelnen Verarbeitungsschritte

---

## 📦 Installation

### 1. Repository klonen

```
git clone https://github.com/simonfieberIT/VCF2PDF.git
cd VCF2PDF
```

### 2. Virtuelle Umgebung erstellen

```
python3 -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```
pip install reportlab
```

*(ReportLab wird für die PDF‑Erzeugung benötigt.)*

---

## ▶️ Nutzung

Lege eine oder mehrere `.vcf`‑Dateien in deinen **Downloads‑Ordner** und starte dann das Script:

```
python3 vcf_to_pdf.py
```

Das Script verarbeitet automatisch:

- alle `.vcf`‑Dateien im Downloads‑Ordner  
- erstellt zu jeder Datei eine PDF  
- legt die PDFs ebenfalls im Downloads‑Ordner ab

---

## 🗂 Ausgabestruktur der PDF

Die PDF enthält – sofern in der vCard vorhanden – folgende Felder:

1. **Name**
2. **Firma**
3. **Position / Abteilung**
4. **Telefonnummern**
5. **E‑Mail‑Adressen**
6. **Postadressen**
7. **Websites**
8. **Social‑Media‑Profile**
9. **Notizen**

---

## 📝 Hinweise

- vCard2PDF verarbeitet aktuell **vCard Version 3.0**.  
- Unbekannte Felder werden ignoriert, sofern sie keinem sinnvollen Kontext zugeordnet werden können.

---

## 📄 Lizenz

© Fieber IT  
Dieses Projekt steht unter der **Creative Commons Attribution–NonCommercial 4.0 International (CC BY‑NC 4.0)** Lizenz.

Das bedeutet:
- Nutzung, Veränderung und Weitergabe sind erlaubt.
- **Kommerzielle Nutzung ist ausdrücklich untersagt.**
- Bei Weitergabe oder Modifikation muss der Urheber („Fieber IT“) genannt werden.

Den vollständigen Lizenztext findest du hier:  
https://creativecommons.org/licenses/by-nc/4.0/deed.de

---

## 💡 Ideen für zukünftige Versionen

- Layout‑Varianten (kompakt / erweitert)
- QR‑Code‑Erzeugung für Kontakt-Download
- Mehrspaltige PDF‑Layouts
- Unterstützung für vCard 4.0