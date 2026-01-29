#!/usr/bin/env python3
"""
Clan Sheet Generator
Creates a dynamic clan sheet based on user input.

Vampire: The Masquerade is a trademark of White Wolf Entertainment AB.
This tool is not affiliated with or endorsed by White Wolf Entertainment AB.
Assets ({clan_name}.png logos or clan_name.png, watermark.png) are property of White Wolf Entertainment AB.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap


class ClanSheetGenerator:
    def __init__(self, clan_name, logo_path=None, watermark_path="watermark.png"):
        self.clan_name = clan_name.upper()
        # Logo path: first search for clan_name.png, then fallback to clan_name.png (generic logo)
        if logo_path is None:
            clan_logo_path = f"{self.clan_name.lower()}.png"
            if os.path.exists(clan_logo_path):
                self.logo_path = clan_logo_path
            else:
                self.logo_path = "clan_name.png"
        else:
            self.logo_path = logo_path
        self.watermark_path = watermark_path
        self.page_width = 2480  # A4 at 300 DPI
        self.page_height = 3508
        self.margin = 60  # Smaller margins for more space
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin
        
        # Box dimensions
        self.box_spacing = 60  # More spacing between left and right boxes
        self.header_height = 75  # Even higher header boxes
        self.min_box_height = 140
        
        # Colors
        self.bg_color = (255, 255, 255)
        self.header_color = (0, 0, 0)
        self.box_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
        
        # Content sections
        self.sections = {}
        
    def load_logo(self):
        """Loads the logo and adapts it - removes white/light background, standardizes to max_height"""
        if os.path.exists(self.logo_path):
            logo = Image.open(self.logo_path)
            # Convert to RGBA if necessary
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Remove white/light/gray background: Make light pixels transparent
            # Use a lower threshold (200 instead of 240) for better detection
            # Use numpy for better performance (if available) or manual
            try:
                import numpy as np
                # Convert to numpy array for better performance
                img_array = np.array(logo)
                # Calculate brightness for each pixel
                brightness = (img_array[:, :, 0].astype(float) + img_array[:, :, 1].astype(float) + img_array[:, :, 2].astype(float)) / 3.0
                # Create mask for light pixels (lower threshold 200 for better detection)
                # Also check for similar RGB values (gray pixels)
                mask = brightness > 200
                # Additionally: If R, G, B are very similar (gray background), also make transparent
                r_diff = np.abs(img_array[:, :, 0].astype(float) - img_array[:, :, 1].astype(float))
                g_diff = np.abs(img_array[:, :, 1].astype(float) - img_array[:, :, 2].astype(float))
                b_diff = np.abs(img_array[:, :, 0].astype(float) - img_array[:, :, 2].astype(float))
                gray_mask = (r_diff < 30) & (g_diff < 30) & (b_diff < 30) & (brightness > 180)
                # Combine both masks
                final_mask = mask | gray_mask
                # Set alpha channel to 0 for light/gray pixels (make them transparent)
                img_array[final_mask, 3] = 0
                logo = Image.fromarray(img_array.astype(np.uint8))
            except ImportError:
                # Fallback without numpy: manual processing
                data = logo.getdata()
                new_data = []
                
                for item in data:
                    r, g, b, a = item
                    brightness = (r + g + b) / 3
                    # Check if pixel is light (lower threshold 200)
                    # Or if it's a gray pixel (similar R, G, B values)
                    r_diff = abs(r - g)
                    g_diff = abs(g - b)
                    b_diff = abs(r - b)
                    is_gray = (r_diff < 30) and (g_diff < 30) and (b_diff < 30) and (brightness > 180)
                    
                    if brightness > 200 or is_gray:
                        # Light/gray pixel -> transparent
                        new_data.append((r, g, b, 0))
                    else:
                        # Dark pixel -> keep as is
                        new_data.append(item)
                
                logo.putdata(new_data)
            
            # Ensure logo has RGBA mode
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Scale logo: For Setites larger (350px), otherwise 280px
            if self.clan_name.upper() == "SETITEN":
                max_height = 350
            else:
                max_height = 280
            if logo.height != max_height:
                ratio = max_height / logo.height
                new_width = int(logo.width * ratio)
                logo = logo.resize((new_width, max_height), Image.Resampling.LANCZOS)
            return logo
        return None
    
    def load_watermark(self):
        """Loads the watermark and adapts it - removes white/gray background, keeps only black pixels"""
        if os.path.exists(self.watermark_path):
            watermark = Image.open(self.watermark_path)
            # Convert to RGBA if necessary
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            
            # Remove white/gray background: Make light pixels transparent
            # Create a new image with transparent background
            data = watermark.getdata()
            new_data = []
            
            for item in data:
                r, g, b = item[0], item[1], item[2]
                brightness = (r + g + b) / 3
                
                # Check if pixel is white or gray (light background)
                # If R, G, B are similar (gray) or all above a threshold (white)
                # Threshold for background: > 180 for gray, > 240 for white
                is_gray = abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30
                is_background = (brightness > 180 and is_gray) or (brightness > 240)
                
                if is_background:
                    # White/gray background pixel -> transparent
                    new_data.append((0, 0, 0, 0))
                else:
                    # Dark pixel -> keep, but with reduced opacity
                    # Set to black with alpha based on brightness
                    # The darker, the higher the alpha (max 35% opacity)
                    alpha_value = int((255 - brightness) * 0.35)
                    new_data.append((0, 0, 0, alpha_value))
            
            watermark.putdata(new_data)
            
            # Unified scaling - to 60% of sheet size, maintain aspect ratio
            target_width = int(self.page_width * 0.6)
            target_height = int(self.page_height * 0.6)
            # Calculate scaling based on aspect ratio
            width_ratio = target_width / watermark.width
            height_ratio = target_height / watermark.height
            # Use the smaller ratio to avoid distortion
            ratio = min(width_ratio, height_ratio)
            new_width = int(watermark.width * ratio)
            new_height = int(watermark.height * ratio)
            watermark = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return watermark
        return None
    
    def get_font(self, size, bold=False):
        """Gets a font"""
        try:
            if bold:
                # Try various bold fonts
                try:
                    return ImageFont.truetype("/System/Library/Fonts/Helvetica-Bold.ttf", size)
                except:
                    try:
                        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
                    except:
                        # Fallback: Helvetica.ttc with font index for Bold (if supported)
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
                # Fallback: Use load_default and make it manually bold by larger font size
                default_font = ImageFont.load_default()
                if bold:
                    # For bold: slightly larger font as replacement
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
        """Calculates the required height for text"""
        lines = self.wrap_text(text, font, max_width)
        # Estimate line height based on font metrics
        try:
            bbox = font.getbbox("Ag")
            line_height = (bbox[3] - bbox[1]) + 6  # A bit more spacing
        except:
            line_height = 25
        return len(lines) * line_height + 25  # More padding
    
    def draw_box(self, draw, x, y, width, height, header_text, content_text, font_normal, font_bold, header_height=None):
        """Draws a box with header and content"""
        # Unified margin for all 4 sides
        box_padding = 40  # Margin on all sides
        
        # Use passed header height or default
        if header_height is None:
            header_height = self.header_height
        
        # Header box with outline
        draw.rectangle([x, y, x + width, y + header_height], fill=self.header_color, outline=(0, 0, 0), width=3)
        
        # Header text (centered, white)
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
        
        # Content box
        content_y = y + header_height
        
        # Content text - respect original line breaks
        # Split by original line breaks
        original_lines = content_text.split('\n')
        try:
            bbox = font_normal.getbbox("Ag")
            line_height = bbox[3] - bbox[1]
        except:
            line_height = 22
        text_y = content_y + box_padding  # Unified margin top
        max_width = width - 2 * box_padding  # Unified margin left and right
        
        # Calculate actual height WHILE drawing
        actual_content_height = box_padding  # Start with padding top
        
        for original_line in original_lines:
            original_line = original_line.strip()
            if not original_line:
                # Keep empty line from original
                actual_content_height += line_height // 2
                continue
            
            # Check if line needs to be wrapped
            line_width = font_normal.getlength(original_line)
            if line_width > max_width:
                # Only wrap if really necessary
                wrapped_lines = self.wrap_text(original_line, font_normal, max_width)
                for wrapped_line in wrapped_lines:
                    if wrapped_line.strip():
                        actual_content_height += line_height + 6
            else:
                # Line fits - don't add breaks
                actual_content_height += line_height + 6
        
        actual_content_height += box_padding  # Padding bottom
        
        # Draw box with actual height
        draw.rectangle([x, content_y, x + width, content_y + actual_content_height], 
                      fill=self.box_color, outline=(0, 0, 0), width=3)
        
        # Now draw the text
        text_y = content_y + box_padding  # Reset for drawing
        for original_line in original_lines:
            original_line = original_line.strip()
            if not original_line:
                # Keep empty line from original
                text_y += line_height // 2
                continue
            
            # Check if line needs to be wrapped
            line_width = font_normal.getlength(original_line)
            if line_width > max_width:
                # Only wrap if really necessary
                wrapped_lines = self.wrap_text(original_line, font_normal, max_width)
                for wrapped_line in wrapped_lines:
                    if wrapped_line.strip():
                        draw.text((x + box_padding, text_y), wrapped_line, fill=self.text_color, font=font_normal)
                    text_y += line_height + 6
            else:
                # Line fits - don't add breaks
                draw.text((x + box_padding, text_y), original_line, fill=self.text_color, font=font_normal)
                text_y += line_height + 6
        
        return actual_content_height + header_height
    
    def draw_disciplines_box(self, draw, x, y, width, height, header_text, content_text, font_normal, font_bold):
        """Draws a box with special formatting for disciplines"""
        # Unified margin for all 4 sides
        box_padding = 40  # Margin on all sides
        
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
        """Parses the user text and extracts the sections"""
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
        """Generates the clan sheet"""
        # Create image
        img = Image.new('RGB', (self.page_width, self.page_height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fonts - even larger for better readability
        font_header = self.get_font(52, bold=True)  # Even larger header font (bold)
        font_normal = self.get_font(48, bold=False)  # Even larger normal font in boxes
        font_final = self.get_font(70, bold=True)  # Final sentence slightly smaller so it doesn't slip
        
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
        
        # Berechne Spalten-Breiten: Für Malkavianer 1/3 und 2/3, sonst 1/4 und 3/4
        if self.clan_name.upper() == "MALKAVIANER":
            left_column_width = int(self.content_width / 3) - self.box_spacing // 2
            right_column_width = int((self.content_width * 2) / 3) - self.box_spacing // 2
        else:
            left_column_width = int(self.content_width / 4)  # Schmaler für längere Boxen
            right_column_width = int((self.content_width * 3) / 4) - self.box_spacing
        
        # Linke Spalte Boxen
        left_sections = [
            f"{self.clan_name} INFOBOX",
            f"{self.clan_name} KURZÜBERBLICK",
            f"{self.clan_name} SPEZIFISCHE SCHWÄCHE"
        ]
        
        # Rechte Spalte Boxen (Reihenfolge wie in den Input-Dateien)
        right_sections = [
            f"{self.clan_name} CLANHALTUNG & ROLLE",
            f"{self.clan_name} DISZIPLINEN"
        ]
        
        # Bei Malkavianern: BEZIEHUNGEN und INTERNE SPANNUNGEN nach rechts verschieben
        if self.clan_name.upper() == "MALKAVIANER":
            right_sections.insert(1, f"{self.clan_name} BEZIEHUNGEN")
            right_sections.append(f"{self.clan_name} INTERNE SPANNUNGEN")
        else:
            # Bei anderen Clans: BEZIEHUNGEN und INTERNE SPANNUNGEN bleiben rechts
            right_sections.insert(1, f"{self.clan_name} BEZIEHUNGEN")
            right_sections.append(f"{self.clan_name} INTERNE SPANNUNGEN")
        
        # Prüfe ob DAS MALKAVIANER-NETZWERK existiert
        # Bei Malkavianern: füge es rechts hinzu (nach CLANHALTUNG & ROLLE)
        # Bei anderen Clans: füge es links hinzu (falls vorhanden)
        network_section = f"{self.clan_name} DAS MALKAVIANER-NETZWERK"
        if network_section in sections:
            if self.clan_name.upper() == "MALKAVIANER":
                # Bei Malkavianern: rechts nach CLANHALTUNG & ROLLE einfügen
                right_sections.insert(1, network_section)
            else:
                # Bei anderen Clans: links hinzufügen
                left_sections.append(network_section)
        
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
            
            # Für Malkavianer: kleinerer Abstand für Berechnung
            left_box_spacing_calc = 40 if self.clan_name.upper() == "MALKAVIANER" else self.box_spacing
            total_left_min_height = sum(left_heights) + (len(left_heights) - 1) * left_box_spacing_calc
            
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
                # Für Malkavianer: kleinerer Abstand für Berechnung
                left_box_spacing_calc = 40 if self.clan_name.upper() == "MALKAVIANER" else self.box_spacing
                total_left_min_height = sum(left_heights) + (len(left_heights) - 1) * left_box_spacing_calc
                
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
        
        # Für Malkavianer: kleinerer, einheitlicher Abstand zwischen linken Boxen
        left_box_spacing = 40 if self.clan_name.upper() == "MALKAVIANER" else self.box_spacing
        
        # Finale Berechnung: Stelle sicher, dass linke Boxen genau die verfügbare Höhe nutzen
        actual_left_height = sum(left_heights) + (len(left_heights) - 1) * left_box_spacing
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
            left_y += height + left_box_spacing
        
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
            
            # Feste Schriftgröße - kleiner für VENTRUE_ANTITRIBU
            if self.clan_name.upper() == "VENTRUE_ANTITRIBU":
                font_final = self.get_font(55, bold=True)  # Kleinere Schriftgröße
            else:
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
            
            # Spezielle Anpassung für Ventrue: CLANESSENZ 80px nach oben verschieben
            if self.clan_name.upper() == "VENTRUE":
                final_text_y -= 80
            
            # Spezielle Anpassung für Ventrue Antitribu: CLANESSENZ 80px nach oben verschieben
            if self.clan_name.upper() == "VENTRUE_ANTITRIBU":
                final_text_y -= 80
            
            # Spezielle Anpassung für Salubri: CLANESSENZ 90px nach oben verschieben
            if self.clan_name.upper() == "SALUBRI":
                final_text_y -= 90
            
            
            # Spezielle Anpassung für Gangrel: CLANESSENZ 70px nach oben verschieben
            if self.clan_name.upper() == "GANGREL":
                final_text_y -= 70
            
            # Spezielle Anpassung für Giovanni: CLANESSENZ 70px nach oben verschieben
            if self.clan_name.upper() == "GIOVANNI":
                final_text_y -= 70
            
            # Spezielle Anpassung für Wahre Brujah: CLANESSENZ 80px nach oben verschieben
            if self.clan_name.upper() == "WAHRE_BRUJAH":
                final_text_y -= 80
            
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
        
        # Wasserzeichen hinzufügen
        watermark = self.load_watermark()
        if watermark:
            # Konvertiere img zu RGBA falls nötig
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            # Zentriere das Wasserzeichen auf dem Sheet
            watermark_x = (self.page_width - watermark.width) // 2
            watermark_y = (self.page_height - watermark.height) // 2
            # Erstelle ein temporäres Bild für das Wasserzeichen in voller Größe
            watermark_full = Image.new('RGBA', (self.page_width, self.page_height), (0, 0, 0, 0))
            watermark_full.paste(watermark, (watermark_x, watermark_y), watermark)
            # Füge Wasserzeichen hinzu
            img = Image.alpha_composite(img, watermark_full)
            # Konvertiere zurück zu RGB für Kompatibilität
            img = img.convert('RGB')
        
        return img
