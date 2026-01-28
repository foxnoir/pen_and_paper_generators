#!/usr/bin/env python3
"""
Clan Sheet Generator
Erstellt ein dynamisches Clan-Sheet basierend auf Benutzereingaben.

Vampire: The Masquerade is a trademark of White Wolf Entertainment AB.
This tool is not affiliated with or endorsed by White Wolf Entertainment AB.
Assets (logo.png, bg.png) are property of White Wolf Entertainment AB.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap


class ClanSheetGenerator:
    def __init__(self, clan_name, logo_path="logo.png", watermark_path="bg.png"):
        self.clan_name = clan_name.upper()
        self.logo_path = logo_path
        self.watermark_path = watermark_path
        self.page_width = 2480  # A4 at 300 DPI
        self.page_height = 3508
        self.margin = 60  # Kleinere Margins für mehr Platz
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin
        
        # Box dimensions
        self.box_spacing = 60  # Mehr Abstand zwischen linken und rechten Boxen
        self.header_height = 75  # Noch höhere Header-Boxen
        self.min_box_height = 140
        
        # Colors
        self.bg_color = (255, 255, 255)
        self.header_color = (0, 0, 0)
        self.box_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
        
        # Content sections
        self.sections = {}
        
    def load_logo(self):
        """Lädt das Logo und passt es an - vereinheitlicht auf max_height"""
        if os.path.exists(self.logo_path):
            logo = Image.open(self.logo_path)
            # Logo immer auf max. 280px Höhe skalieren für Konsistenz
            max_height = 280
            if logo.height != max_height:
                ratio = max_height / logo.height
                new_width = int(logo.width * ratio)
                logo = logo.resize((new_width, max_height), Image.Resampling.LANCZOS)
            return logo
        return None
    
    def load_watermark(self):
        """Lädt das Wasserzeichen und passt es an - vereinheitlicht"""
        if os.path.exists(self.watermark_path):
            watermark = Image.open(self.watermark_path)
            # Konvertiere zu RGBA falls nötig
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            # Vereinheitlichte Skalierung - auf 60% der Sheet-Größe, behalte Seitenverhältnis
            target_width = int(self.page_width * 0.6)
            target_height = int(self.page_height * 0.6)
            # Berechne Skalierung basierend auf Seitenverhältnis
            width_ratio = target_width / watermark.width
            height_ratio = target_height / watermark.height
            # Verwende das kleinere Verhältnis, um Verzerrung zu vermeiden
            ratio = min(width_ratio, height_ratio)
            new_width = int(watermark.width * ratio)
            new_height = int(watermark.height * ratio)
            watermark = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Vereinheitlichte Deckkraft: 35% (0.35 * 255 = 89)
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.35))
            watermark.putalpha(alpha)
            return watermark
        return None
    
    def get_font(self, size, bold=False):
        """Holt eine Schriftart"""
        try:
            if bold:
                # Versuche verschiedene Bold-Fonts
                try:
                    return ImageFont.truetype("/System/Library/Fonts/Helvetica-Bold.ttf", size)
                except:
                    try:
                        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
                    except:
                        # Fallback: Helvetica.ttc mit Font-Index für Bold (falls unterstützt)
                        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
            else:
                return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except:
            try:
                if bold:
                    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
                else:
                    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
            except:
                # Fallback: Verwende load_default und mache es manuell bold durch größere Schrift
                default_font = ImageFont.load_default()
                if bold:
                    # Für bold: etwas größere Schrift als Ersatz
                    return ImageFont.load_default()
                return default_font
    
    def wrap_text(self, text, font, max_width):
        """Wrappt Text auf mehrere Zeilen"""
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append("")
                continue
            words = paragraph.split()
            current_line = []
            current_width = 0
            
            for word in words:
                word_width = font.getlength(word + " ")
                if current_width + word_width <= max_width and current_line:
                    current_line.append(word)
                    current_width += word_width
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
            
            if current_line:
                lines.append(" ".join(current_line))
        
        return lines
    
    def calculate_text_height(self, text, font, max_width):
        """Berechnet die benötigte Höhe für Text"""
        lines = self.wrap_text(text, font, max_width)
        # Schätze Zeilenhöhe basierend auf Font-Metrik
        try:
            bbox = font.getbbox("Ag")
            line_height = (bbox[3] - bbox[1]) + 6  # Etwas mehr Abstand
        except:
            line_height = 25
        return len(lines) * line_height + 25  # Mehr Padding
    
    def draw_box(self, draw, x, y, width, height, header_text, content_text, font_normal, font_bold, header_height=None):
        """Zeichnet eine Box mit Header und Inhalt"""
        # Einheitlicher Margin für alle 4 Seiten
        box_padding = 40  # Margin auf allen Seiten
        
        # Verwende übergebene Header-Höhe oder Standard
        if header_height is None:
            header_height = self.header_height
        
        # Header Box mit Umriss
        draw.rectangle([x, y, x + width, y + header_height], fill=self.header_color, outline=(0, 0, 0), width=3)
        
        # Header Text (zentriert, weiß)
        header_lines = self.wrap_text(header_text, font_bold, width - 2 * box_padding)
        try:
            bbox = font_bold.getbbox("Ag")
            line_height = bbox[3] - bbox[1]
        except:
            line_height = 20
        total_header_height = len(header_lines) * (line_height + 2)
        header_y = y + (header_height - total_header_height) // 2
        for line in header_lines:
            bbox = font_bold.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = x + (width - text_width) // 2
            draw.text((text_x, header_y), line, fill=(255, 255, 255), font=font_bold)
            header_y += line_height + 2
        
        # Content Box
        content_y = y + header_height
        
        # Content Text - respektiere originale Zeilenumbrüche
        # Teile nach originalen Zeilenumbrüchen
        original_lines = content_text.split('\n')
        try:
            bbox = font_normal.getbbox("Ag")
            line_height = bbox[3] - bbox[1]
        except:
            line_height = 22
        text_y = content_y + box_padding  # Einheitlicher Margin oben
        max_width = width - 2 * box_padding  # Einheitlicher Margin links und rechts
        
        # Berechne tatsächliche Höhe WÄHREND des Zeichnens
        actual_content_height = box_padding  # Start mit Padding oben
        
        for original_line in original_lines:
            original_line = original_line.strip()
            if not original_line:
                # Leere Zeile im Original beibehalten
                actual_content_height += line_height // 2
                continue
            
            # Prüfe ob Zeile umgebrochen werden muss
            line_width = font_normal.getlength(original_line)
            if line_width > max_width:
                # Nur dann wrappen wenn wirklich nötig
                wrapped_lines = self.wrap_text(original_line, font_normal, max_width)
                for wrapped_line in wrapped_lines:
                    if wrapped_line.strip():
                        actual_content_height += line_height + 6
            else:
                # Zeile passt - keine Umbrüche hinzufügen
                actual_content_height += line_height + 6
        
        actual_content_height += box_padding  # Padding unten
        
        # Zeichne Box mit tatsächlicher Höhe
        draw.rectangle([x, content_y, x + width, content_y + actual_content_height], 
                      fill=self.box_color, outline=(0, 0, 0), width=3)
        
        # Jetzt zeichne den Text
        text_y = content_y + box_padding  # Reset für Zeichnen
        for original_line in original_lines:
            original_line = original_line.strip()
            if not original_line:
                # Leere Zeile im Original beibehalten
                text_y += line_height // 2
                continue
            
            # Prüfe ob Zeile umgebrochen werden muss
            line_width = font_normal.getlength(original_line)
            if line_width > max_width:
                # Nur dann wrappen wenn wirklich nötig
                wrapped_lines = self.wrap_text(original_line, font_normal, max_width)
                for wrapped_line in wrapped_lines:
                    if wrapped_line.strip():
                        draw.text((x + box_padding, text_y), wrapped_line, fill=self.text_color, font=font_normal)
                    text_y += line_height + 6
            else:
                # Zeile passt - keine Umbrüche hinzufügen
                draw.text((x + box_padding, text_y), original_line, fill=self.text_color, font=font_normal)
                text_y += line_height + 6
        
        return actual_content_height + header_height
    
    def draw_disciplines_box(self, draw, x, y, width, height, header_text, content_text, font_normal, font_bold):
        """Zeichnet eine Box mit spezieller Formatierung für Disziplinen"""
        # Einheitlicher Margin für alle 4 Seiten
        box_padding = 40  # Margin auf allen Seiten
        
        # Header Box mit Umriss
        draw.rectangle([x, y, x + width, y + self.header_height], fill=self.header_color, outline=(0, 0, 0), width=3)
        
        # Header Text (zentriert, weiß)
        header_lines = self.wrap_text(header_text, font_bold, width - 2 * box_padding)
        try:
            bbox = font_bold.getbbox("Ag")
            line_height = bbox[3] - bbox[1]
        except:
            line_height = 20
        total_header_height = len(header_lines) * (line_height + 2)
        header_y = y + (self.header_height - total_header_height) // 2
        for line in header_lines:
            bbox = font_bold.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = x + (width - text_width) // 2
            draw.text((text_x, header_y), line, fill=(255, 255, 255), font=font_bold)
            header_y += line_height + 2
        
        # Content Box
        content_y = y + self.header_height
        
        # Verarbeite Content: Respektiere originale Zeilenumbrüche
        import re
        
        # Teile nach doppelten Newlines (Disziplin-Trenner), aber behalte originale Struktur
        discipline_sections = re.split(r'\n\s*\n', content_text)
        processed_lines = []
        
        for idx, section in enumerate(discipline_sections):
            section = section.strip()
            if not section:
                continue
            
            # Behalte originale Zeilenumbrüche - nur überflüssige Whitespace entfernen
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Leere Zeile im Original beibehalten
                    processed_lines.append(('', '', False))
                    continue
                
                # Suche nach Disziplin-Namen (z.B. "Celerity", "Potence", "Presence")
                # Pattern: Wort am Anfang (möglicherweise mit Bullet), gefolgt von "("
                match = re.match(r'^[•\-\s]*([A-Za-z]+)\s*\(', line)
                if match:
                    discipline_name = match.group(1)
                    # Entferne nur Bullet/Strich am Anfang, behalte Rest der Zeile
                    line_clean = re.sub(r'^[•\-\s]+', '', line)
                    processed_lines.append((discipline_name, line_clean, True))  # True = ist Disziplin-Header
                else:
                    # Normaler Text - entferne nur überflüssige Whitespace innerhalb der Zeile
                    line_clean = ' '.join(line.split())
                    if line_clean:
                        processed_lines.append(('', line_clean, False))
            
            # Füge leere Zeile zwischen Disziplinen hinzu (außer nach der letzten)
            if idx < len(discipline_sections) - 1:
                processed_lines.append(('', '', False))  # Leere Zeile
        
        # Berechne Höhe
        try:
            bbox = font_normal.getbbox("Ag")
            line_height_normal = bbox[3] - bbox[1]
            bbox_bold = font_bold.getbbox("Ag")
            line_height_bold = bbox_bold[3] - bbox_bold[1]
        except:
            line_height_normal = 48
            line_height_bold = 52
        
        total_height = box_padding  # Einheitlicher Margin oben
        for discipline_name, line, is_header in processed_lines:
            if not line.strip() and not is_header:
                total_height += line_height_normal // 2  # Leere Zeile
            elif is_header:
                total_height += line_height_bold + 6
            else:
                # Wrappe lange Zeilen
                wrapped = self.wrap_text(line, font_normal, width - 2 * box_padding)
                total_height += len(wrapped) * (line_height_normal + 6)
        
        # Verwende exakte Höhe ohne min_box_height Überschuss
        content_height = total_height + box_padding  # Einheitlicher Margin unten
        
        draw.rectangle([x, content_y, x + width, content_y + content_height], 
                      fill=self.box_color, outline=(0, 0, 0), width=3)
        
        # Zeichne Content mit spezieller Formatierung
        text_y = content_y + box_padding  # Einheitlicher Margin oben
        for discipline_name, line, is_header in processed_lines:
            if not line.strip() and not is_header:
                # Leere Zeile zwischen Disziplinen
                text_y += line_height_normal // 2
                continue
            
            if is_header:
                # Disziplin-Name: bold und unterstrichen
                # Finde Position des Disziplin-Namens im Text
                discipline_pos = line.find(discipline_name)
                if discipline_pos >= 0:
                    # Text vor Disziplin-Name
                    before = line[:discipline_pos]
                    # Text nach Disziplin-Name (inkl. "(")
                    after = line[discipline_pos + len(discipline_name):]
                    
                    current_x = x + box_padding  # Einheitlicher Margin links
                    if before:
                        draw.text((current_x, text_y), before, fill=self.text_color, font=font_normal)
                        current_x += font_normal.getlength(before)
                    
                    # Disziplin-Name: bold
                    draw.text((current_x, text_y), discipline_name, fill=self.text_color, font=font_bold)
                    name_width = font_bold.getlength(discipline_name)
                    
                    # Unterstreichung
                    underline_y = text_y + line_height_bold - 2
                    draw.line([(current_x, underline_y), (current_x + name_width, underline_y)], 
                             fill=self.text_color, width=2)
                    
                    current_x += name_width
                    
                    if after:
                        draw.text((current_x, text_y), after, fill=self.text_color, font=font_normal)
                else:
                    # Fallback: ganze Zeile bold
                    draw.text((x + box_padding, text_y), line, fill=self.text_color, font=font_bold)
                    name_width = font_bold.getlength(line)
                    underline_y = text_y + line_height_bold - 2
                    draw.line([(x + box_padding, underline_y), (x + box_padding + name_width, underline_y)], 
                             fill=self.text_color, width=2)
                
                text_y += line_height_bold + 6
            else:
                # Normaler Text - wrappe nur wenn nötig (Zeile zu lang)
                line_width = font_normal.getlength(line)
                max_width = width - 2 * box_padding
                if line_width > max_width:
                    # Nur dann wrappen wenn wirklich nötig
                    wrapped_lines = self.wrap_text(line, font_normal, max_width)
                    for wrapped_line in wrapped_lines:
                        if wrapped_line.strip():
                            draw.text((x + box_padding, text_y), wrapped_line, fill=self.text_color, font=font_normal)
                        text_y += line_height_normal + 6
                else:
                    # Zeile passt - keine Umbrüche hinzufügen
                    if line.strip():
                        draw.text((x + box_padding, text_y), line, fill=self.text_color, font=font_normal)
                    text_y += line_height_normal + 6
        
        return content_height + self.header_height
    
    def parse_user_input(self, user_text):
        """Parst den Benutzertext und extrahiert die Sektionen"""
        sections = {}
        current_section = None
        current_content = []
        
        # Erwartete Sektionen - verschiedene Varianten
        section_patterns = {
            f"{self.clan_name} INFOBOX": ["INFOBOX"],
            f"{self.clan_name} KURZÜBERBLICK": ["KURZÜBERBLICK", "KURZUBERBLICK"],
            f"{self.clan_name} SPEZIFISCHE SCHWÄCHE": ["SPEZIFISCHE SCHWÄCHE", "SPEZIFISCHE SCHWACHE", "SCHWÄCHE"],
            f"{self.clan_name} DAS MALKAVIANER-NETZWERK": ["DAS MALKAVIANER-NETZWERK", "DAS MALKAVIANER NETZWERK", "NETZWERK"],
            f"{self.clan_name} CLANHALTUNG & ROLLE": ["CLANHALTUNG & ROLLE", "CLANHALTUNG UND ROLLE", "CLANHALTUNG", "ROLLE", "MENTALITÄT"],
            f"{self.clan_name} BEZIEHUNGEN": ["BEZIEHUNGEN"],
            f"{self.clan_name} INTERNE SPANNUNGEN": ["INTERNE SPANNUNGEN", "INTERNE SPANNUNG", "SPANNUNGEN"],
            f"{self.clan_name} DISZIPLINEN": ["DISZIPLINEN"]
        }
        
        lines = user_text.split('\n')
        
        for line in lines:
            line_upper = line.strip().upper()
            # Prüfe ob diese Zeile ein Header ist
            found_section = None
            
            # Prüfe auf exakte Übereinstimmung mit vollständigem Namen
            for section_key in section_patterns.keys():
                if line_upper == section_key or line_upper.startswith(section_key + " "):
                    found_section = section_key
                    break
            
            # Falls nicht gefunden, prüfe auf Pattern-Matches (ohne Clan-Präfix)
            if not found_section:
                for section_key, patterns in section_patterns.items():
                    for pattern in patterns:
                        # Entferne Doppelpunkt am Ende falls vorhanden
                        line_clean = line_upper.rstrip(':').strip()
                        pattern_clean = pattern.rstrip(':').strip()
                        
                        # Prüfe ob Pattern exakt übereinstimmt oder am Anfang steht
                        # Wichtig: Pattern muss am Anfang der Zeile stehen (nach Stripping)
                        if line_clean == pattern_clean:
                            found_section = section_key
                            break
                        elif line_clean.startswith(pattern_clean):
                            # Prüfe ob nach dem Pattern ein Leerzeichen oder Ende kommt
                            remaining = line_clean[len(pattern_clean):].strip()
                            if not remaining or remaining.startswith(':'):
                                found_section = section_key
                                break
                    if found_section:
                        break
            
            # Prüfe auf "ENDE" Schlüsselwort
            if line_upper == "ENDE":
                # Speichere vorherige Sektion und beende
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                break
            
            if found_section:
                # Speichere vorherige Sektion
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Starte neue Sektion
                current_section = found_section
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Speichere letzte Sektion (falls nicht durch ENDE beendet)
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def generate_sheet(self, sections, clanessenz):
        """Generiert das Clan-Sheet"""
        # Erstelle Bild
        img = Image.new('RGB', (self.page_width, self.page_height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Schriftarten - noch größer für bessere Lesbarkeit
        font_header = self.get_font(52, bold=True)  # Noch größere Header-Schrift (bold)
        font_normal = self.get_font(48, bold=False)  # Noch größere normale Schrift in Boxen
        font_final = self.get_font(70, bold=True)  # Finaler Satz etwas kleiner damit er nicht rutscht
        
        current_y = self.margin + 20
        
        # Logo ohne Rahmen, mit horizontalen Linien vom unteren Rand
        logo = self.load_logo()
        logo_spacing = 40  # Vereinheitlichter Abstand zwischen Logo und Content
        if logo:
            # Logo zentriert positionieren
            logo_x = int(self.margin + (self.content_width - logo.width) // 2)
            logo_y = int(current_y)
            
            # Logo einfügen
            img.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
            
            # Horizontale Linien auf Höhe der Logo-Mitte
            line_width = 4  # Dicke der Linien
            line_y = int(logo_y + logo.height // 2)  # Y-Position auf Höhe der Logo-Mitte
            
            # Linke Linie: vom linken Logo-Ende zum linken Rand
            left_line_start_x = logo_x
            left_line_end_x = self.margin
            draw.line([(left_line_start_x, line_y), (left_line_end_x, line_y)], 
                     fill=(0, 0, 0), width=line_width)
            
            # Rechte Linie: vom rechten Logo-Ende zum rechten Rand (mit ein paar Pixeln Rand)
            right_margin = 15  # Ein paar Pixel Rand vom rechten Rand
            right_line_start_x = logo_x + logo.width
            right_line_end_x = self.page_width - self.margin - right_margin
            draw.line([(right_line_start_x, line_y), (right_line_end_x, line_y)], 
                     fill=(0, 0, 0), width=line_width)
            
            # Vereinheitlichter Abstand zwischen Logo und Content
            current_y = logo_y + logo.height + logo_spacing
        
        # Berechne Spalten-Breiten: Für Malkavianer 1/2 und 1/2, sonst 1/4 und 3/4
        if self.clan_name.upper() == "MALKAVIANER":
            left_column_width = int(self.content_width / 2) - self.box_spacing // 2
            right_column_width = int(self.content_width / 2) - self.box_spacing // 2
        else:
            left_column_width = int(self.content_width / 4)  # Schmaler für längere Boxen
            right_column_width = int((self.content_width * 3) / 4) - self.box_spacing
        
        # Linke Spalte Boxen
        left_sections = [
            f"{self.clan_name} INFOBOX",
            f"{self.clan_name} KURZÜBERBLICK",
            f"{self.clan_name} SPEZIFISCHE SCHWÄCHE"
        ]
        
        # Prüfe ob DAS MALKAVIANER-NETZWERK existiert und füge es links hinzu
        network_section = f"{self.clan_name} DAS MALKAVIANER-NETZWERK"
        if network_section in sections:
            left_sections.append(network_section)
        
        # Rechte Spalte Boxen (Reihenfolge wie in den Input-Dateien)
        right_sections = [
            f"{self.clan_name} CLANHALTUNG & ROLLE",
            f"{self.clan_name} BEZIEHUNGEN",
            f"{self.clan_name} DISZIPLINEN",
            f"{self.clan_name} INTERNE SPANNUNGEN"
        ]
        
        # Berechne verfügbare Höhe für linke Spalte (über die ganze Länge)
        # Linke Boxen sollen immer die ganze Höhe einnehmen (mit etwas Abstand unten)
        min_bottom_margin = 30  # Minimaler Abstand unten
        bottom_margin = min_bottom_margin
        
        # Iterative Anpassung: Passe Schriftgröße und Margin an, bis alles passt
        for iteration in range(5):  # Maximal 5 Iterationen
            available_height_for_boxes = self.page_height - current_y - bottom_margin
            
            # Linke Boxen über die ganze Höhe verteilen
            left_heights = []
            for section in left_sections:
                content = sections.get(section, "")
                min_height = self.header_height + max(self.min_box_height,
                                                    self.calculate_text_height(content, font_normal, left_column_width - 80))
                left_heights.append(min_height)
            
            total_left_min_height = sum(left_heights) + (len(left_heights) - 1) * self.box_spacing
            
            # Wenn zu groß, skaliere Schriftgröße
            if total_left_min_height > available_height_for_boxes:
                scale_factor = available_height_for_boxes / total_left_min_height
                new_normal_size = max(28, int(48 * scale_factor))  # Minimum nicht zu klein
                new_header_size = max(35, int(52 * scale_factor))
                font_normal = self.get_font(new_normal_size, bold=False)
                font_header = self.get_font(new_header_size, bold=True)
                # Neuberechnen mit skalierten Fonts
                left_heights = []
                for section in left_sections:
                    content = sections.get(section, "")
                    height = self.header_height + max(self.min_box_height,
                                                    self.calculate_text_height(content, font_normal, left_column_width - 80))
                    left_heights.append(height)
                total_left_min_height = sum(left_heights) + (len(left_heights) - 1) * self.box_spacing
                
                # Wenn immer noch zu groß nach Skalierung, erhöhe Margin
                if total_left_min_height > available_height_for_boxes:
                    bottom_margin += 10
                    continue
            
            # Wenn passt oder zu klein, gleichmäßig verteilen
            if total_left_min_height <= available_height_for_boxes:
                extra_space = available_height_for_boxes - total_left_min_height
                extra_per_box = extra_space // len(left_heights)
                left_heights = [h + extra_per_box for h in left_heights]
                break
        
        # Rechte Boxen werden vollständig dynamisch beim Zeichnen berechnet
        # Keine Vorberechnung mehr - jede Box berechnet ihre Höhe selbst
        
        # Finale Berechnung: Stelle sicher, dass linke Boxen genau die verfügbare Höhe nutzen
        actual_left_height = sum(left_heights) + (len(left_heights) - 1) * self.box_spacing
        bottom_margin = max(min_bottom_margin, self.page_height - current_y - actual_left_height)
        
        # Linke Spalte Position
        left_x = self.margin
        left_y = current_y
        
        # Rechte Spalte Position
        right_x = self.margin + left_column_width + self.box_spacing
        right_y = current_y
        
        # Zeichne linke Spalte (über die ganze Höhe)
        for i, section in enumerate(left_sections):
            content = sections.get(section, "")
            height = left_heights[i]
            # Entferne Clan-Namen aus der Überschrift
            header_text = section.replace(f"{self.clan_name} ", "")
            # Letzte linke Box: erhöhte Header-Höhe
            if i == len(left_sections) - 1:
                increased_header_height = int(self.header_height * 1.5)  # 50% größer
                self.draw_box(draw, left_x, left_y, left_column_width, height, 
                             header_text, content, font_normal, font_header, header_height=increased_header_height)
            else:
                self.draw_box(draw, left_x, left_y, left_column_width, height, 
                             header_text, content, font_normal, font_header)
            left_y += height + self.box_spacing
        
        # Zeichne rechte Spalte - VOLLSTÄNDIG DYNAMISCH: Berechne Höhe beim Zeichnen
        actual_right_y = right_y
        for i, section in enumerate(right_sections):
            content = sections.get(section, "")
            # Entferne Clan-Namen aus der Überschrift
            header_text = section.replace(f"{self.clan_name} ", "")
            
            # Zeichne Box und lasse sie ihre tatsächliche Höhe zurückgeben
            if "DISZIPLINEN" in section:
                # Verwende eine große Höhe, die Box wird ihre tatsächliche Höhe zurückgeben
                temp_height = 5000  # Temporäre große Höhe
                actual_height = self.draw_disciplines_box(draw, right_x, actual_right_y, right_column_width, temp_height,
                                                  header_text, content, font_normal, font_header)
            else:
                # Berechne benötigte Höhe dynamisch - OHNE min_box_height für rechte Boxen
                needed_height = self.calculate_text_height(content, font_normal, right_column_width - 80)
                box_height = self.header_height + needed_height  # Keine Mindesthöhe!
                actual_height = self.draw_box(draw, right_x, actual_right_y, right_column_width, box_height,
                             header_text, content, font_normal, font_header)
            actual_right_y += actual_height + self.box_spacing
        
        # CLANESSENZ: Für Malkavianer oben links/rechts, sonst unten zentriert
        if self.clan_name.upper() == "MALKAVIANER":
            # Malkavianer: Text in 2 Teile - links und rechts, unterschiedliche Größen
            import random
            
            # Position weiter nach außen und nach unten
            start_y = self.margin + 60  # Weiter nach unten
            
            # Teile Text in 2 Teile (ungefähr in der Mitte)
            words = clanessenz.split()
            mid_point = len(words) // 2
            left_text = ' '.join(words[:mid_point])
            right_text = ' '.join(words[mid_point:])
            
            # Links: Erster Teil mit unterschiedlichen Schriftgrößen - enger (1/6 Breite)
            left_max_width = int(self.page_width / 6)  # 1/6 der Seitenbreite
            left_x = self.margin  # Start am linken Rand
            left_y = start_y
            current_y = left_y
            
            # Wrappe Text für linke Seite
            left_words = left_text.split()
            current_x = left_x
            
            line_offset = 0  # Versatz für jede Zeile
            for word in left_words:
                # Unterschiedliche Schriftgrößen (40-60px)
                font_size = random.randint(40, 60)
                font_word = self.get_font(font_size, bold=True)
                
                # Prüfe ob Wort passt
                try:
                    word_width = font_word.getlength(word + " ")
                except:
                    word_width = font_size * len(word) * 0.6
                
                if current_x + word_width > left_x + left_max_width:
                    # Neue Zeile - weiter nach unten und versetzt
                    line_offset = random.randint(-15, 15)  # Zufälliger Versatz pro Zeile
                    current_x = left_x + line_offset
                    try:
                        bbox = font_word.getbbox("Ag")
                        current_y += bbox[3] - bbox[1] + 8
                    except:
                        current_y += font_size + 8
                
                # Zeichne Wort
                draw.text((current_x, current_y), word + " ", fill=self.text_color, font=font_word)
                current_x += word_width
            
            # Rechts: Zweiter Teil mit unterschiedlichen Schriftgrößen - enger (1/6 Breite)
            right_max_width = int(self.page_width / 6)  # 1/6 der Seitenbreite
            right_x = self.page_width - self.margin - right_max_width  # Start am rechten Rand
            right_y = start_y
            current_y = right_y
            
            # Wrappe Text für rechte Seite
            right_words = right_text.split()
            current_x = right_x
            
            line_offset = 0  # Versatz für jede Zeile
            for word in right_words:
                # Unterschiedliche Schriftgrößen (40-60px)
                font_size = random.randint(40, 60)
                font_word = self.get_font(font_size, bold=True)
                
                # Prüfe ob Wort passt
                try:
                    word_width = font_word.getlength(word + " ")
                except:
                    word_width = font_size * len(word) * 0.6
                
                if current_x + word_width > right_x + right_max_width:
                    # Neue Zeile - weiter nach unten und versetzt
                    line_offset = random.randint(-15, 15)  # Zufälliger Versatz pro Zeile
                    current_x = right_x + line_offset
                    try:
                        bbox = font_word.getbbox("Ag")
                        current_y += bbox[3] - bbox[1] + 8
                    except:
                        current_y += font_size + 8
                
                # Zeichne Wort
                draw.text((current_x, current_y), word + " ", fill=self.text_color, font=font_word)
                current_x += word_width
        else:
            # Normale Positionierung: Unten zentriert
            final_area_width = right_column_width  # 2/3 Breite
            final_area_start_x = right_x  # Beginnt bei rechter Spalte
            
            # Feste Schriftgröße
            font_final = self.get_font(65, bold=True)  # Feste Schriftgröße
            final_text_width = final_area_width - 40
            final_lines = self.wrap_text(clanessenz, font_final, final_text_width)
            
            try:
                bbox = font_final.getbbox("Ag")
                line_height = (bbox[3] - bbox[1]) + 12
            except:
                line_height = 65 + 12
            text_height = len(final_lines) * line_height
            
            # Feste Padding-Werte
            line_padding = 15  # Padding zwischen Linien und Text
            final_bottom_margin = 50  # Fester Abstand vom unteren Rand
            
            # Berechne verfügbaren Platz: Stelle sicher, dass CLANESSENZ nicht mit rechter Spalte überlappt
            # Berechne maximale Y-Position der rechten Spalte
            max_right_y = actual_right_y  # Letzte Y-Position der rechten Spalte
            
            # Berechne Position von unten nach oben
            total_final_height = text_height + (2 * line_padding) + 30  # Text + Padding + Linien
            final_text_y_bottom = self.page_height - final_bottom_margin - total_final_height + line_padding + 15
            
            # Stelle sicher, dass CLANESSENZ nicht mit rechter Spalte überlappt
            # Mindestabstand zwischen letzter Box und CLANESSENZ
            min_spacing = 40
            if final_text_y_bottom < max_right_y + min_spacing:
                # Verschiebe CLANESSENZ weiter nach unten
                final_text_y = max_right_y + min_spacing + line_padding
            else:
                final_text_y = final_text_y_bottom
            
            # Obere Linie
            line_y_top = final_text_y - line_padding
            draw.line([(final_area_start_x, line_y_top), 
                      (final_area_start_x + final_area_width, line_y_top)], 
                     fill=(0, 0, 0), width=4)
            
            # Untere Linie
            line_y_bottom = final_text_y + text_height + line_padding
            draw.line([(final_area_start_x, line_y_bottom), 
                      (final_area_start_x + final_area_width, line_y_bottom)], 
                     fill=(0, 0, 0), width=4)
            
            # Text zeichnen
            for i, line in enumerate(final_lines):
                bbox = font_final.getbbox(line)
                text_width = bbox[2] - bbox[0]
                text_x = final_area_start_x + (final_area_width - text_width) // 2
                draw.text((text_x, final_text_y + i * line_height), line, 
                         fill=self.text_color, font=font_final)
        
        # Wasserzeichen deaktiviert - weißer Hintergrund
        # watermark = self.load_watermark()
        # if watermark:
        #     # Konvertiere img zu RGBA falls nötig
        #     if img.mode != 'RGBA':
        #         img = img.convert('RGBA')
        #     # Zentriere das Wasserzeichen auf dem Sheet
        #     watermark_x = (self.page_width - watermark.width) // 2
        #     watermark_y = (self.page_height - watermark.height) // 2
        #     # Erstelle ein temporäres Bild für das Wasserzeichen in voller Größe
        #     watermark_full = Image.new('RGBA', (self.page_width, self.page_height), (0, 0, 0, 0))
        #     watermark_full.paste(watermark, (watermark_x, watermark_y), watermark)
        #     # Füge Wasserzeichen hinzu
        #     img = Image.alpha_composite(img, watermark_full)
        #     # Konvertiere zurück zu RGB für Kompatibilität
        #     img = img.convert('RGB')
        
        return img


def main():
    print("=" * 60)
    print("CLAN SHEET GENERATOR")
    print("=" * 60)
    print()
    
    # Clan Name eingeben
    clan_name = input("Bitte geben Sie den Clan-Namen ein: ").strip()
    if not clan_name:
        print("Fehler: Clan-Name darf nicht leer sein!")
        return
    
    print()
    print("Bitte geben Sie den Text für die Sektionen ein.")
    print("Verwenden Sie die folgenden Überschriften (alles GROSSBUCHSTABEN):")
    print(f"- {clan_name.upper()} INFOBOX")
    print(f"- {clan_name.upper()} KURZÜBERBLICK")
    print(f"- {clan_name.upper()} SPEZIFISCHE SCHWÄCHE")
    print(f"- {clan_name.upper()} CLANHALTUNG & ROLLE")
    print(f"- {clan_name.upper()} BEZIEHUNGEN")
    print(f"- {clan_name.upper()} INTERNE SPANNUNGEN")
    print(f"- {clan_name.upper()} DISZIPLINEN")
    print()
    print("Geben Sie den Text ein.")
    print("Tipp: Sie können den Text mit allen Überschriften auf einmal einfügen.")
    print("Beenden Sie die Eingabe mit 'ENDE' in einer neuen Zeile:")
    print()
    
    lines = []
    while True:
        try:
            line = input()
            line_stripped = line.strip().upper()
            
            # Beende bei "ENDE"
            if line_stripped == "ENDE":
                break
            
            lines.append(line)
        except EOFError:
            # Handle Ctrl+D / Ctrl+Z
            break
    
    user_text = '\n'.join(lines)
    
    # CLANESSENZ
    print()
    clanessenz = input("Bitte geben Sie die CLANESSENZ ein: ").strip()
    if not clanessenz:
        clanessenz = "Brujah fühlen zuerst – und handeln dann. Wenn sie Recht haben, brennt die Welt. Wenn nicht, auch."
    
    # Generator erstellen
    generator = ClanSheetGenerator(clan_name)
    
    # Text parsen
    sections = generator.parse_user_input(user_text)
    
    # Sheet generieren
    print()
    print("Generiere Clan-Sheet...")
    sheet = generator.generate_sheet(sections, clanessenz)
    
    # Speichern
    output_filename = f"{clan_name.lower()}_clan_sheet.png"
    sheet.save(output_filename, "PNG", dpi=(300, 300))
    print(f"Clan-Sheet gespeichert als: {output_filename}")
    
    # Optional: Als PDF speichern
    try:
        pdf_filename = f"{clan_name.lower()}_clan_sheet.pdf"
        sheet.save(pdf_filename, "PDF", resolution=300.0)
        print(f"Clan-Sheet auch als PDF gespeichert: {pdf_filename}")
    except Exception as e:
        print(f"Hinweis: PDF konnte nicht erstellt werden: {e}")


if __name__ == "__main__":
    main()
