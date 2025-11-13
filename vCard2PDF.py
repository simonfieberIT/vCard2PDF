#!/usr/bin/env python3
"""
vCard2PDF v1.0

Konvertiert vCard-Dateien (.vcf) in lesbare PDF-Kontaktblätter für macOS.

Copyright (c) 2014-2025 Fieber IT
Lizenz: Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)
Siehe: https://creativecommons.org/licenses/by-nc/4.0/
"""
from datetime import datetime
from pathlib import Path
from io import BytesIO
import base64

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def parse_vcard(vcf_path: Path) -> dict:
    """
    Parst eine vCard-Datei (.vcf) und gibt die Kontaktinformationen
    als Dictionary mit strukturierten Feldern zurück.
    """
    data = {
        "FN": None,
        "ORG": None,
        "DEPT": None,
        "TITLE": None,
        "TEL": [],           # Liste aus {"value": str, "params": [str, ...]}
        "EMAIL": [],         # Liste aus {"value": str, "params": [str, ...]}
        "ADR": [],           # Liste aus {"value": str, "params": [str, ...]}
        "URL": [],           # Liste aus {"value": str, "params": [str, ...]}
        "NOTE": [],
        "SOCIAL": [],        # Liste aus {"value": str, "params": [str, ...]}
        "PHOTO": None,
        "VERSION": None,
        "PRODID": None,
    }

    text = vcf_path.read_text(encoding="utf-8", errors="ignore")

    # Zeilen gemäß vCard-Standard "entfalten" (Zeilenumbrüche zusammenführen)
    raw_lines = text.splitlines()
    unfolded = []
    for line in raw_lines:
        if not line.strip():
            continue
        if line[0] in (" ", "\t") and unfolded:
            # Fortsetzung der vorherigen Zeile
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line.rstrip("\n"))

    def unescape(s: str) -> str:
        return (
            s.replace("\\n", "\n")
             .replace("\\N", "\n")
             .replace("\\,", ",")
             .replace("\\;", ";")
        )

    def split_key_and_params(key_part: str):
        pieces = key_part.split(";")
        base = pieces[0].upper()
        params = []
        for p in pieces[1:]:
            p = p.strip()
            if not p:
                continue
            if "=" in p:
                _, val = p.split("=", 1)
                params.append(val.upper())
            else:
                params.append(p.upper())
        return base, params

    for line in unfolded:
        if ":" not in line:
            continue

        key_part, value = line.split(":", 1)
        key, params = split_key_and_params(key_part)
        value = value.strip()

        if key == "FN":
            if not data["FN"]:
                data["FN"] = value
        elif key == "ORG":
            if not data["ORG"]:
                org_clean = value.rstrip(";")
                parts = org_clean.split(";")
                data["ORG"] = parts[0]
                if len(parts) > 1 and parts[1].strip():
                    data["DEPT"] = parts[1].strip()
        elif key == "TITLE":
            if not data["TITLE"]:
                data["TITLE"] = value
        elif key == "TEL":
            data["TEL"].append({"value": value, "params": params})
        elif key == "EMAIL":
            data["EMAIL"].append({"value": value, "params": params})
        elif key == "ADR":
            data["ADR"].append({"value": unescape(value), "params": params})
        elif key == "URL" or key.endswith(".URL"):
            data["URL"].append({"value": value, "params": params})
        elif key == "NOTE":
            data["NOTE"].append(unescape(value))
        elif key == "X-SOCIALPROFILE":
            data["SOCIAL"].append({"value": value, "params": params})
        elif key == "PHOTO":
            try:
                data["PHOTO"] = base64.b64decode(value)
            except Exception:
                pass
        elif key == "VERSION":
            data["VERSION"] = value
        elif key == "PRODID":
            data["PRODID"] = value
        elif key in ("BEGIN", "END"):
            # Rahmenzeilen BEGIN:VCARD / END:VCARD ignorieren
            continue
        else:
            # übrige Felder werden ignoriert
            pass

    return data


def build_pdf(vcard: dict, source_name: str, pdf_path: Path) -> None:
    """
    Erstellt ein A4-PDF mit den wichtigsten Kontaktinformationen
    aus der geparsten vCard.
    """
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    x_margin = 50
    y = height - 60

    label_font_name = "Helvetica-Bold"
    label_font_size = 11
    value_font_name = "Helvetica"
    value_font_size = 11
    section_spacing = 24

    known_labels = [
        "Position",
        "Abteilung",
        "Mobil",
        "Zentrale",
        "Geschäftlich",
        "Privat",
        "Adresse",
        "Homepage",
        "Website",
        "Facebook",
        "XING",
        "LinkedIn",
        "Instagram",
        "Twitter",
    ]
    global_label_width = 0
    for lbl in known_labels:
        w = c.stringWidth(f"{lbl}:", label_font_name, label_font_size)
        if w > global_label_width:
            global_label_width = w

    # Foto (falls vorhanden) oben rechts einbinden
    if vcard.get("PHOTO"):
        try:
            img_data = BytesIO(vcard["PHOTO"])
            img = ImageReader(img_data)
            iw, ih = img.getSize()
            max_w, max_h = 150, 150
            scale = min(max_w / iw, max_h / ih, 1.0)
            w, h = iw * scale, ih * scale
            c.drawImage(img, width - x_margin - w, height - 80 - h, w, h)
        except Exception:
            # Bei Problemen mit dem Bild ignorieren wir es einfach
            pass

    title = vcard.get("FN") or source_name
    c.setFont("Helvetica-Bold", 20)
    c.drawString(x_margin, y, title)
    y -= 14

    def new_page_if_needed(min_y: float = 70):
        nonlocal y
        if y < min_y:
            c.showPage()
            y = height - 60

    def draw_heading(text: str):
        nonlocal y
        new_page_if_needed()
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x_margin, y, text)
        y -= 14

    def draw_lines(text: str, font: str = "Helvetica", size: int = 11, leading: int = 14):
        nonlocal y
        if not text:
            return
        lines = text.split("\n")
        for line in lines:
            new_page_if_needed()
            c.setFont(font, size)
            c.drawString(x_margin, y, line)
            y -= leading

    def add_spacing(amount: int = 12):
        nonlocal y
        y -= amount

    def draw_label_paragraph(label: str, lines, leading: int = 14):
        nonlocal y
        if not lines:
            return
        new_page_if_needed()
        label_text = f"{label}:"
        label_font = label_font_name
        label_size = label_font_size
        value_font = value_font_name
        value_size = value_font_size
        value_x = x_margin + global_label_width + 6
        for idx, line in enumerate(lines):
            new_page_if_needed()
            if idx == 0:
                c.setFont(label_font, label_size)
                c.drawString(x_margin, y, label_text)
            c.setFont(value_font, value_size)
            c.drawString(value_x, y, line)
            y -= leading

    def build_social_url(network: str, handle: str) -> str | None:
        h = handle.strip()
        if not h:
            return None
        # Bereits vollständige URL?
        if h.lower().startswith("http://") or h.lower().startswith("https://"):
            return h
        if h.lower().startswith("www."):
            return "https://" + h
        if network == "FACEBOOK":
            return f"https://www.facebook.com/{h}"
        if network == "XING":
            return f"https://www.xing.com/profile/{h}"
        if network == "LINKEDIN":
            return f"https://www.linkedin.com/in/{h}"
        if network == "INSTAGRAM":
            return f"https://www.instagram.com/{h}"
        if network == "TWITTER":
            return f"https://twitter.com/{h}"
        return None

    def classify_from_params(params, kind):
        tokens = [p.upper() for p in params]
        if kind == "TEL":
            if any(t in ("CELL", "MOBILE", "IPHONE") for t in tokens):
                return "MOBILE"
            if any(t in ("MAIN", "WORK", "BUSINESS") for t in tokens):
                return "WORK"
            if any(t in ("HOME", "PRIVATE") for t in tokens):
                return "HOME"
            return "OTHER"
        if kind == "EMAIL" or kind == "ADR" or kind == "URL":
            if any(t in ("WORK", "BUSINESS") for t in tokens):
                return "WORK"
            if any(t in ("HOME", "PRIVATE") for t in tokens):
                return "HOME"
            return "OTHER"
        if kind == "SOCIAL":
            if any("FACEBOOK" in t for t in tokens):
                return "FACEBOOK"
            if any("XING" in t for t in tokens):
                return "XING"
            if any("LINKEDIN" in t for t in tokens):
                return "LINKEDIN"
            if any("INSTAGRAM" in t for t in tokens):
                return "INSTAGRAM"
            if any("TWITTER" in t for t in tokens):
                return "TWITTER"
            return "OTHER"
        return "OTHER"

    if vcard.get("ORG"):
        draw_lines(vcard["ORG"], size=12)

    # Leere Zeile zwischen Firma und Position
    if vcard.get("TITLE") or vcard.get("DEPT"):
        add_spacing(14)

    if vcard.get("TITLE"):
        draw_label_paragraph("Position", [vcard["TITLE"]], leading=14)
    if vcard.get("DEPT"):
        draw_label_paragraph("Abteilung", [vcard["DEPT"]], leading=14)

    add_spacing(section_spacing)

    if vcard.get("TEL"):
        draw_heading("Telefon")
        entries = []
        seen_work = False
        for entry in vcard["TEL"]:
            tel_value = entry["value"]
            kind = classify_from_params(entry.get("params", []), "TEL")
            if kind == "MOBILE":
                label = "Mobil"
            elif kind == "WORK":
                if not seen_work:
                    label = "Zentrale"
                    seen_work = True
                else:
                    label = "Geschäftlich"
            elif kind == "HOME":
                label = "Privat"
            else:
                label = None
            entries.append((label, tel_value))
        label_font = label_font_name
        label_size = label_font_size
        value_font = value_font_name
        value_size = value_font_size
        value_x = x_margin + global_label_width + 6
        for label, tel_value in entries:
            new_page_if_needed()
            if label:
                c.setFont(label_font, label_size)
                c.drawString(x_margin, y, f"{label}:")
                c.setFont(value_font, value_size)
                c.drawString(value_x, y, tel_value)
            else:
                c.setFont(value_font, value_size)
                c.drawString(x_margin, y, tel_value)
            y -= 14
        add_spacing(section_spacing)

    if vcard.get("EMAIL"):
        heading = "E-Mail" if len(vcard["EMAIL"]) == 1 else "E-Mail(s)"
        draw_heading(heading)
        entries = []
        for entry in vcard["EMAIL"]:
            mail_value = entry["value"]
            kind = classify_from_params(entry.get("params", []), "EMAIL")
            if kind == "WORK":
                label = "Geschäftlich"
            elif kind == "HOME":
                label = "Privat"
            else:
                label = None
            entries.append((label, mail_value))
        label_font = label_font_name
        label_size = label_font_size
        value_font = value_font_name
        value_size = value_font_size
        value_x = x_margin + global_label_width + 6
        for label, mail_value in entries:
            new_page_if_needed()
            if label:
                c.setFont(label_font, label_size)
                c.drawString(x_margin, y, f"{label}:")
                c.setFont(value_font, value_size)
                c.drawString(value_x, y, mail_value)
            else:
                c.setFont(value_font, value_size)
                c.drawString(x_margin, y, mail_value)
            y -= 14
        add_spacing(section_spacing)

    if vcard.get("ADR"):
        adrs = vcard["ADR"]
        heading = "Adresse" if len(adrs) == 1 else "Adressen"
        draw_heading(heading)
        for entry in adrs:
            adr_value = entry["value"]
            kind = classify_from_params(entry.get("params", []), "ADR")
            if kind == "WORK":
                label = "Geschäftlich"
            elif kind == "HOME":
                label = "Privat"
            else:
                label = "Adresse"
            parts = adr_value.split(";")
            street = parts[2] if len(parts) > 2 else ""
            city = parts[3] if len(parts) > 3 else ""
            postal = parts[5] if len(parts) > 5 else ""
            line1 = street.strip()
            line2 = f"{postal.strip()} {city.strip()}".strip()
            lines = []
            if line1:
                lines.append(line1)
            if line2:
                lines.append(line2)
            if lines:
                draw_label_paragraph(label, lines, leading=14)
            add_spacing(6)
        add_spacing(section_spacing)

    if vcard.get("URL"):
        urls = vcard["URL"]
        heading = "Website" if len(urls) == 1 else "Website(s)"
        draw_heading(heading)
        entries = []
        for entry in urls:
            url_value = entry["value"]
            kind = classify_from_params(entry.get("params", []), "URL")
            if kind == "WORK":
                label = "Geschäftlich"
            elif kind == "HOME":
                label = "Privat"
            else:
                label = None
            entries.append((label, url_value))

        label_font = label_font_name
        label_size = label_font_size
        value_font = value_font_name
        value_size = value_font_size
        value_x = x_margin + global_label_width + 6

        single_url = len(entries) == 1

        for label, url_value in entries:
            new_page_if_needed()
            # Fallback-Label, wenn keins aus TYPE kommt
            effective_label = label
            if not effective_label:
                effective_label = "Homepage" if single_url else "Website"

            c.setFont(label_font, label_size)
            c.drawString(x_margin, y, f"{effective_label}:")
            c.setFont(value_font, value_size)
            c.drawString(value_x, y, url_value)
            y -= 14

        add_spacing(section_spacing)

    if vcard.get("SOCIAL"):
        draw_heading("Social Media")
        label_font = label_font_name
        label_size = label_font_size
        value_font = value_font_name
        value_size = value_font_size
        bullet_text = "• "
        bullet_width = c.stringWidth(bullet_text, value_font, value_size)
        value_x_base = x_margin + global_label_width + 6

        for entry in vcard["SOCIAL"]:
            value = entry["value"]
            network = classify_from_params(entry.get("params", []), "SOCIAL")
            handle = value.split(":")[-1]
            if network == "FACEBOOK":
                label = "Facebook"
            elif network == "XING":
                label = "XING"
            elif network == "LINKEDIN":
                label = "LinkedIn"
            elif network == "INSTAGRAM":
                label = "Instagram"
            elif network == "TWITTER":
                label = "Twitter"
            else:
                label = None

            new_page_if_needed()
            # Bullet
            c.setFont(value_font, value_size)
            c.drawString(x_margin, y, bullet_text)
            x_after_bullet = x_margin + bullet_width

            # Label in der gleichen Spalte wie andere Labels
            if label:
                c.setFont(label_font, label_size)
                label_text = f"{label}:"
                c.drawString(x_after_bullet, y, label_text)

            # Wert in der gleichen Spalte wie andere Werte
            value_x = value_x_base
            c.setFont(value_font, value_size)
            c.drawString(value_x, y, handle)

            url = build_social_url(network, handle)
            if url:
                text_width = c.stringWidth(handle, value_font, value_size)
                c.linkURL(url, (value_x, y - 2, value_x + text_width, y + 10), relative=0)

            y -= 14

        add_spacing(section_spacing)

    if vcard.get("NOTE"):
        add_spacing(section_spacing)
        draw_heading("Notizen")
        for note in vcard["NOTE"]:
            draw_lines(note)

    footer_year = datetime.now().year
    footer_y = 30

    c.setFont("Helvetica", 8)
    c.drawString(x_margin, footer_y + 10, "Generiert durch vCard2PDF v1.0")
    c.drawString(x_margin, footer_y, f"© Fieber IT 2014 - {footer_year}")

    meta_parts = []
    if vcard.get("VERSION"):
        meta_parts.append(f"vCard-Version {vcard['VERSION']}")
    if vcard.get("PRODID"):
        meta_parts.append(f"PRODID {vcard['PRODID']}")

    if meta_parts:
        c.drawRightString(width - x_margin, footer_y, " · ".join(meta_parts))

    c.save()


def main():
    print("🟡 Starte vCard2PDF v1.0")
    print(f"⏰ Zeitpunkt: {datetime.now()}")

    home = Path.home()
    downloads = home / "Downloads"

    source_dir = downloads
    target_dir = downloads

    print(f"📂 Quelle:  {source_dir}")
    print(f"📁 Ziel:    {target_dir}")

    vcf_files = sorted(source_dir.glob("*.vcf"))

    if not vcf_files:
        print("❌ Keine .vcf Dateien im Downloads Ordner gefunden.")
        return

    for vcf_file in vcf_files:
        print()
        print(f"➡️  Bearbeite {vcf_file.name}")

        vcard = parse_vcard(vcf_file)

        if vcard.get("FN"):
            base_name = vcard["FN"]
        else:
            base_name = vcf_file.stem

        for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
            base_name = base_name.replace(ch, "_")

        pdf_path = target_dir / f"{base_name}.pdf"

        try:
            build_pdf(vcard, vcf_file.name, pdf_path)
            print(f"✔️  PDF erstellt: {pdf_path.name}")
            print()
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der PDF für {vcf_file.name}: {e}")

    print("🟢 Script beendet.")


if __name__ == "__main__":
    main()