#!/usr/bin/env python3
"""
Dynamischer PDF-Generator für Vampire Journal
Erstellt die PDF von Grund auf neu, sodass sie später leicht angepasst werden kann.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
import os
import json


class DynamicPDFGenerator:
    """Generiert die PDF dynamisch von Grund auf"""
    
    def __init__(self):
        self.page_width = 595.2755737304688  # A4 width in points
        self.page_height = 841.8897705078125  # A4 height in points
        self.total_pages = 125
        
        # Tab-Struktur (rechte Seite, Y-Positionen) - von oben nach unten
        self.tabs = [
            {"name": "Domäne", "y": 65.0, "target_page": 1, "height": 70.0},
            {"name": "Intrigen & Interessen", "y": 143.0, "target_page": 94, "height": 110.0},
            {"name": "Runden", "y": 261.0, "target_page": 93, "height": 70.0},
            {"name": "NPCs", "y": 339.0, "target_page": 90, "height": 70.0},
            {"name": "Orte", "y": 417.0, "target_page": 81, "height": 70.0},
            {"name": "Karten", "y": 495.0, "target_page": 30, "height": 70.0},
            {"name": "Handouts", "y": 573.0, "target_page": 23, "height": 70.0},
            {"name": "Notizen", "y": 651.0, "target_page": 11, "height": 70.0},
            {"name": "Regeln", "y": 729.0, "target_page": 95, "height": 70.0},
        ]
        
        # Tab-Breite und Position
        self.tab_width = 35.0  # Breiter für besseres Design und Text
        self.tab_x = self.page_width - self.tab_width - 5  # Rechter Rand mit 5pt Abstand
        
        # Tab-Design-Farben (RGB 0-1 für PyMuPDF) - Marine-Blau
        self.tab_colors = {
            "background": (0.75, 0.85, 0.95),  # Helles Marine-Blau (inaktiv)
            "border": (0.50, 0.65, 0.80),  # Marine-Blau Rahmen
            "active": (0.50, 0.65, 0.80),  # Dunkles Marine-Blau (aktiv)
            "text": (0.15, 0.15, 0.15),  # Dunkler Text
            "shadow": (0.40, 0.55, 0.70)  # Marine-Blau Schatten
        }
        
        # Seiten-Struktur
        self.page_structure = {
            1: {"section": "Domäne", "subsections": ["Stadt", "Storyline", "Zeitlinien", "Zentraler Konflikt", "Status quo", "Machtstruktur", "Clanlandschaft", "Einfluss & Territorien", "Konfliktherde", "Maskerade & Öffentlichkeit", "Sonstiges"]},
            11: {"section": "Notizen", "subsections": ["Aufträge & Verpflichtungen", "Beziehungen & Schulden", "Geheimnisse", "Gerüchte & Informationen", "Zeitlinien", "Ziele & Ambitionen", "Sonstiges"]},
            23: {"section": "Handouts", "subsections": ["Überblick", "Rundenziel", "Ablauf", "Schlüsselinformationen", "Konsequenzen", "Notizen", "Sonstiges"]},
            30: {"section": "Karten", "subsections": ["Camarilla", "Sabbat", "Anarchen", "Unabhängige", "Blutlinien", "Werwölfe", "Ghule", "Menschen", "Andere"]},
            81: {"section": "Orte", "subsections": ["Clubs & Nachtleben", "Elysien", "Industrie & Verfall", "Kultur & Öffentlichkeit", "Menschliche Infrastruktur", "Outdoor-Orte", "Private Domänen"]},
            90: {"section": "NPCs", "subsections": ["Stadtplan", "Domänenkarte", "Lagepläne"]},
            93: {"section": "Runden", "subsections": []},
            94: {"section": "Intrigen & Interessen", "subsections": []},
            95: {"section": "Regeln", "subsections": ["Grundregeln", "Charakter & Blut", "Disziplinen", "Kampf & Konflikt", "Gesellschaft & Politik", "Maskerade"]},
        }
        
        # Seiten pro Abschnitt
        self.pages_per_section = {
            1: 10, 11: 12, 23: 7, 30: 51, 81: 9, 90: 3, 93: 1, 94: 1, 95: 30
        }
    
    def analyze_source_pdf(self, source_path: str) -> Dict:
        """Analysiert die Original-PDF und extrahiert alle Strukturen"""
        print(f"Analysiere Original-PDF: {source_path}")
        source_doc = fitz.open(source_path)
        
        analysis = {
            "pages": [],
            "fonts": set(),
            "links": {}
        }
        
        for page_num in range(min(10, len(source_doc))):  # Analysiere erste 10 Seiten als Beispiel
            page = source_doc[page_num]
            text_dict = page.get_text("dict")
            
            page_data = {
                "page_num": page_num + 1,
                "text_elements": [],
                "links": []
            }
            
            # Extrahiere Text-Elemente
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            page_data["text_elements"].append({
                                "text": span['text'],
                                "bbox": list(span['bbox']),
                                "font": span['font'],
                                "size": span['size'],
                                "flags": span.get('flags', 0),
                                "color": span.get('color', 0)
                            })
                            analysis["fonts"].add(span['font'])
            
            # Extrahiere Links
            links = page.get_links()
            for link in links:
                target = link.get('page', 0)
                if isinstance(target, str):
                    try:
                        target = int(target)
                    except:
                        target = 0
                page_data["links"].append({
                    "rect": [link['from'].x0, link['from'].y0, link['from'].x1, link['from'].y1],
                    "target_page": target
                })
            
            analysis["pages"].append(page_data)
        
        source_doc.close()
        analysis["fonts"] = list(analysis["fonts"])
        return analysis
    
    def create_page_with_tabs(self, doc: fitz.Document, page_num: int) -> fitz.Page:
        """Erstellt eine Seite mit Tab-Navigation"""
        page = doc.new_page(width=self.page_width, height=self.page_height)
        
        # Füge Tabs hinzu (nachdem alle Seiten existieren)
        return page
    
    def draw_rounded_rect(self, page: fitz.Page, rect: fitz.Rect, fill_color: tuple, border_color: tuple = None, radius: float = 8.0, shadow: bool = False):
        """Zeichnet ein abgerundetes Rechteck mit gegebenem Radius"""
        try:
            import math
            
            # Berechne die Ecken
            x0, y0 = rect.x0, rect.y0
            x1, y1 = rect.x1, rect.y1
            
            # Stelle sicher, dass Radius nicht zu groß ist
            radius = min(radius, min(rect.width, rect.height) / 2)
            
            # Zeichne Schatten zuerst (leicht versetzt nach rechts/unten)
            if shadow:
                shadow_offset = 1.5
                shadow_rect = fitz.Rect(
                    x0 + shadow_offset,
                    y0 + shadow_offset,
                    x1 + shadow_offset,
                    y1 + shadow_offset
                )
                self._draw_rounded_rect_shape(page, shadow_rect, self.tab_colors["shadow"], None, radius)
            
            # Zeichne Hauptrechteck
            self._draw_rounded_rect_shape(page, rect, fill_color, border_color, radius)
            
        except Exception as e:
            # Fallback: normales Rechteck wenn Pfad fehlschlägt
            if shadow:
                shadow_offset = 1.5
                shadow_rect = fitz.Rect(
                    rect.x0 + shadow_offset,
                    rect.y0 + shadow_offset,
                    rect.x1 + shadow_offset,
                    rect.y1 + shadow_offset
                )
                page.draw_rect(shadow_rect, color=self.tab_colors["shadow"], width=0, fill=self.tab_colors["shadow"])
            page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color)
    
    def _draw_rounded_rect_shape(self, page: fitz.Page, rect: fitz.Rect, fill_color: tuple, border_color: tuple, radius: float):
        """Hilfsfunktion zum Zeichnen eines abgerundeten Rechtecks"""
        try:
            x0, y0 = rect.x0, rect.y0
            x1, y1 = rect.x1, rect.y1
            
            # Verwende Shape-Objekt für komplexe Pfade
            shape = page.new_shape()
            
            # Zeichne abgerundetes Rechteck durch Kombination von Rechtecken und Kreisen
            # Hauptrechteck (ohne Ecken)
            inner_rect = fitz.Rect(x0 + radius, y0, x1 - radius, y1)
            shape.draw_rect(inner_rect)
            
            # Obere horizontale Rechtecke
            top_rect = fitz.Rect(x0 + radius, y0, x1 - radius, y0 + radius)
            shape.draw_rect(top_rect)
            
            # Untere horizontale Rechtecke
            bottom_rect = fitz.Rect(x0 + radius, y1 - radius, x1 - radius, y1)
            shape.draw_rect(bottom_rect)
            
            # Linke vertikale Rechtecke
            left_rect = fitz.Rect(x0, y0 + radius, x0 + radius, y1 - radius)
            shape.draw_rect(left_rect)
            
            # Rechte vertikale Rechtecke
            right_rect = fitz.Rect(x1 - radius, y0 + radius, x1, y1 - radius)
            shape.draw_rect(right_rect)
            
            # Zeichne Kreise an den Ecken
            # Obere linke Ecke
            shape.draw_circle(fitz.Point(x0 + radius, y0 + radius), radius)
            
            # Obere rechte Ecke
            shape.draw_circle(fitz.Point(x1 - radius, y0 + radius), radius)
            
            # Untere linke Ecke
            shape.draw_circle(fitz.Point(x0 + radius, y1 - radius), radius)
            
            # Untere rechte Ecke
            shape.draw_circle(fitz.Point(x1 - radius, y1 - radius), radius)
            
            # Fülle alles (ohne Rahmen wenn border_color None ist)
            border_width = 0 if border_color is None else 1.0
            shape.finish(fill=fill_color, color=border_color if border_color else fill_color, width=border_width)
            shape.commit()
            
        except Exception as e:
            # Fallback: normales Rechteck wenn Pfad fehlschlägt
            page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color)
    
    def draw_modern_tab(self, page: fitz.Page, tab: Dict, page_num: int, is_active: bool = False, original_text: Dict = None):
        """Zeichnet einen modernen Journal-Reiter mit Design"""
        tab_rect = fitz.Rect(
            self.tab_x,
            tab["y"],
            self.tab_x + self.tab_width,
            tab["y"] + tab["height"]
        )
        
        # Bestimme Farbe (aktiver Tab ist etwas dunkler)
        bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
        
        # Zeichne Schatten (leicht versetzt nach rechts/unten)
        shadow_rect = fitz.Rect(
            tab_rect.x0 + 1.5,
            tab_rect.y0 + 1.5,
            tab_rect.x1 + 1.5,
            tab_rect.y1 + 1.5
        )
        page.draw_rect(shadow_rect, color=self.tab_colors["shadow"], width=0, fill=self.tab_colors["shadow"])
        
        # Zeichne Tab-Hintergrund (normales Rechteck, keine abgerundeten Ecken)
        page.draw_rect(tab_rect, color=self.tab_colors["border"], width=1.0, fill=bg_color)
        
        # Zeichne innere Highlight-Linie oben für 3D-Effekt
        highlight_rect = fitz.Rect(
            tab_rect.x0 + 0.5,
            tab_rect.y0 + 0.5,
            tab_rect.x1 - 0.5,
            tab_rect.y0 + 2
        )
        page.draw_rect(highlight_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
        
        # Zeichne untere Schatten-Linie für Tiefe
        shadow_line = fitz.Rect(
            tab_rect.x0 + 0.5,
            tab_rect.y1 - 2,
            tab_rect.x1 - 0.5,
            tab_rect.y1 - 0.5
        )
        page.draw_rect(shadow_line, color=self.tab_colors["border"], width=0, fill=self.tab_colors["border"])
        
        # Füge Text hinzu - verwende originalen Text wenn verfügbar
        if original_text:
            # Berechne Position für Text - deutlich nach links verschoben
            # Verschiebe Text um 8-10pt nach links (negativer Wert = nach links)
            text_offset_left = -9.0
            
            # Verwende insert_textbox mit Rotation für vertikalen Text
            try:
                from fitz import Rect
                # Text-Rect deutlich nach links verschoben
                text_rect = Rect(
                    tab_rect.x0 + 2 + text_offset_left,
                    tab_rect.y0 + 2,
                    tab_rect.x1 - 2 + text_offset_left,
                    tab_rect.y1 - 2
                )
                
                # Versuche Text mit Rotation einzufügen
                # rotate=270 bedeutet 270° im Uhrzeigersinn = 90° gegen Uhrzeigersinn
                rc = page.insert_textbox(
                    text_rect,
                    original_text['text'],
                    fontsize=original_text.get('fontsize', 8),
                    fontname=original_text.get('fontname', 'helv-Bold'),
                    color=(0.0, 0.0, 0.0),
                    align=1,  # Zentriert
                    rotate=270  # Vertikal
                )
                
                if rc < 0:
                    # Fallback: Einfacher Text ohne Rotation, nach links verschoben
                    center_x = tab_rect.x0 + self.tab_width / 2 + text_offset_left
                    center_y = tab_rect.y0 + tab["height"] / 2
                    page.insert_text(
                        (center_x, center_y),
                        original_text['text'],
                        fontsize=original_text.get('fontsize', 7),
                        fontname=original_text.get('fontname', 'helv-Bold'),
                        color=(0.0, 0.0, 0.0)
                    )
            except Exception as e:
                # Letzter Fallback: Einfacher Text, nach links verschoben
                try:
                    center_x = tab_rect.x0 + self.tab_width / 2 + text_offset_left
                    center_y = tab_rect.y0 + tab["height"] / 2
                    page.insert_text(
                        (center_x, center_y),
                        original_text['text'][:15] if len(original_text['text']) > 15 else original_text['text'],
                        fontsize=7,
                        fontname='helv-Bold',
                        color=(0.0, 0.0, 0.0)
                    )
                except:
                    pass
        
        # Füge Link hinzu
        link = {
            "kind": fitz.LINK_GOTO,
            "from": tab_rect,
            "page": tab["target_page"] - 1,  # 0-basiert
            "to": fitz.Point(0, 0),
            "zoom": 0.0
        }
        try:
            page.insert_link(link)
        except:
            pass
    
    def extract_tab_texts(self, source_page: fitz.Page) -> List[str]:
        """Extrahiert Tab-Beschriftungen von der Original-Seite"""
        text_dict = source_page.get_text("dict")
        tab_texts = []
        
        # Suche Text auf der rechten Seite (Tab-Bereich)
        # Tabs sind zwischen x=550 und x=595 (rechter Rand)
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_y = None
                    line_x_min = None
                    line_x_max = None
                    
                    for span in line["spans"]:
                        bbox = span['bbox']
                        # Rechte Seite (x > 550) - Tab-Bereich
                        if bbox[0] > 550:
                            if line_y is None:
                                line_y = bbox[1]
                            if line_x_min is None:
                                line_x_min = bbox[0]
                            if line_x_max is None:
                                line_x_max = bbox[2]
                            line_x_min = min(line_x_min, bbox[0])
                            line_x_max = max(line_x_max, bbox[2])
                            line_text += span['text']
                    
                    if line_text and line_y is not None:
                        cleaned_text = line_text.strip()
                        # Filtere sehr kurze Texte (wahrscheinlich keine Tab-Beschriftungen)
                        if len(cleaned_text) > 1:
                            tab_texts.append({
                                'text': cleaned_text,
                                'y': line_y,
                                'x': line_x_min if line_x_min else 560
                            })
        
        # Sortiere nach Y-Position (von oben nach unten)
        tab_texts.sort(key=lambda x: x['y'])
        
        # Debug: Zeige gefundene Texte
        print(f"  Gefundene Tab-Texte (vor Filterung): {len(tab_texts)}")
        for i, txt in enumerate(tab_texts[:12]):
            print(f"    {i+1}. '{txt['text']}' bei Y={txt['y']:.1f}")
        
        # Extrahiere nur die Texte
        texts = [item['text'] for item in tab_texts]
        
        # Erwartete Tab-Namen (falls Extraktion fehlschlägt)
        default_tabs = [
            "Domäne",
            "Intrigen & Interessen",
            "Runden",
            "NPCs",
            "Orte",
            "Karten",
            "Handouts",
            "Notizen",
            "Regeln"
        ]
        
        # Wenn wir weniger als 9 Texte haben, verwende Standard-Namen
        if len(texts) < 9:
            print(f"  Warnung: Nur {len(texts)} Tab-Texte gefunden, verwende Standard-Namen")
            return default_tabs[:len(self.tabs)]
        
        # Nimm die ersten 9 Texte (sollten die Tab-Beschriftungen sein)
        return texts[:9]
    
    def extract_tab_text_elements(self, source_page: fitz.Page) -> List[Dict]:
        """Extrahiert Tab-Text-Elemente mit Positionen von der Original-Seite"""
        text_dict = source_page.get_text("dict")
        tab_texts = []
        
        # Suche Text auf der rechten Seite (Tab-Bereich)
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_y = None
                    line_x_min = None
                    line_x_max = None
                    font_size = None
                    font_name = None
                    
                    for span in line["spans"]:
                        bbox = span['bbox']
                        # Rechte Seite (x > 550) - Tab-Bereich
                        if bbox[0] > 550:
                            if line_y is None:
                                line_y = bbox[1]
                            if line_x_min is None:
                                line_x_min = bbox[0]
                            if line_x_max is None:
                                line_x_max = bbox[2]
                            line_x_min = min(line_x_min, bbox[0])
                            line_x_max = max(line_x_max, bbox[2])
                            if font_size is None:
                                font_size = span.get('size', 8)
                            if font_name is None:
                                font_name = span.get('font', 'helv-Bold')
                            line_text += span['text']
                    
                    if line_text and line_y is not None:
                        cleaned_text = line_text.strip()
                        if len(cleaned_text) > 1:
                            tab_texts.append({
                                'text': cleaned_text,
                                'y': line_y,
                                'x': line_x_min if line_x_min else 560,
                                'x_max': line_x_max if line_x_max else 590,
                                'fontsize': font_size if font_size else 8,
                                'fontname': font_name if font_name else 'helv-Bold'
                            })
        
        # Sortiere nach Y-Position (von oben nach unten)
        tab_texts.sort(key=lambda x: x['y'])
        return tab_texts[:9]  # Nimm die ersten 9 (sollten die Tab-Beschriftungen sein)
    
    def add_tabs_to_page(self, page: fitz.Page, page_num: int, tab_text_elements: List[Dict] = None):
        """Fügt moderne Tab-Reiter zu einer Seite hinzu"""
        # Bestimme welche Seite aktiv ist (basierend auf Tab-Zielen)
        active_tab = None
        for tab in self.tabs:
            if tab["target_page"] == page_num:
                active_tab = tab
                break
        
        # Zeichne alle Tabs
        for i, tab in enumerate(self.tabs):
            is_active = (tab == active_tab)
            self.draw_modern_tab(page, tab, page_num, is_active, tab_text_elements[i] if tab_text_elements and i < len(tab_text_elements) else None)
    
    def add_text_to_page(self, page: fitz.Page, text_elements: List[Dict]):
        """Fügt Text-Elemente zu einer Seite hinzu"""
        for elem in text_elements:
            try:
                bbox = elem['bbox']
                point = fitz.Point(bbox[0], bbox[1])
                
                # Bestimme Font
                fontname = "helv"
                if elem.get('flags', 0) & 16:  # Bold
                    fontname = "helv-Bold"
                
                page.insert_text(
                    point,
                    elem['text'],
                    fontsize=elem['size'],
                    fontname=fontname
                )
            except Exception as e:
                # Ignoriere Fehler bei einzelnen Text-Elementen
                pass
    
    def add_links_to_page(self, page: fitz.Page, links: List[Dict], total_pages: int):
        """Fügt Links zu einer Seite hinzu"""
        for link_data in links:
            try:
                target_page = link_data['target_page']
                if isinstance(target_page, str):
                    try:
                        target_page = int(target_page) - 1
                    except:
                        continue
                elif isinstance(target_page, int):
                    target_page = target_page - 1
                else:
                    continue
                
                if target_page < 0 or target_page >= total_pages:
                    continue
                
                rect_data = link_data['rect']
                link_rect = fitz.Rect(rect_data[0], rect_data[1], rect_data[2], rect_data[3])
                
                link = {
                    "kind": fitz.LINK_GOTO,
                    "from": link_rect,
                    "page": target_page,
                    "to": fitz.Point(0, 0),
                    "zoom": 0.0
                }
                page.insert_link(link)
            except:
                pass
    
    def generate_from_source(self, source_path: str, output_path: str):
        """Generiert PDF basierend auf Original-PDF"""
        print("=" * 60)
        print("DYNAMISCHER PDF-GENERATOR")
        print("=" * 60)
        print()
        
        # Lade Original-PDF
        source_doc = fitz.open(source_path)
        total_pages = len(source_doc)
        
        print(f"Original hat {total_pages} Seiten")
        print(f"Erstelle dynamische Kopie...")
        
        # Erstelle neue PDF
        doc = fitz.open()
        
        print("Extrahiere Tab-Beschriftungen von Original...")
        
        # Extrahiere Tab-Texte von der ersten Seite der Original-PDF
        source_page_0 = source_doc[0]
        tab_texts = self.extract_tab_texts(source_page_0)
        tab_text_elements = self.extract_tab_text_elements(source_page_0)
        
        # Aktualisiere Tab-Namen mit originalen Texten falls verfügbar
        if len(tab_texts) >= len(self.tabs):
            for i, tab in enumerate(self.tabs):
                tab["name"] = tab_texts[i]
            print(f"  Gefunden: {len(tab_texts)} Tab-Beschriftungen")
        else:
            print(f"  Warnung: Nur {len(tab_texts)} Tab-Texte gefunden, verwende Standard-Namen")
        
        # Kopiere alle Seiten - insert_pdf kopiert Inhalte und Design
        doc.insert_pdf(source_doc, from_page=0, to_page=total_pages - 1)
        
        print("Zeichne moderne Tab-Reiter...")
        
        # Zeichne moderne Tabs auf allen Seiten
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.add_tabs_to_page(target_page, page_num + 1, tab_text_elements)
        
        print("Kopiere und repariere Links...")
        
        # Ziel-Position für obere Links: 10px von links, 20px von oben
        target_x = 10.0
        target_y = 20.0
        
        # Kopiere alle Links von Original und setze sie neu (außer Tab-Links, die sind schon gesetzt)
        for page_num in range(total_pages):
            source_page = source_doc[page_num]
            target_page = doc[page_num]
            
            # Hole alle Links von der Original-Seite
            source_links = source_page.get_links()
            
            # Filtere Links auf der linken Seite (obere Links)
            left_links = [l for l in source_links if l['from'].x0 < 500]
            
            if left_links:
                # Sortiere Links nach Y-Position (von oben nach unten)
                left_links.sort(key=lambda l: l['from'].y0)
                
                # Berechne Offset basierend auf erstem Link (oberster)
                first_link_rect = left_links[0]['from']
                avg_x = sum(l['from'].x0 for l in left_links) / len(left_links)
                
                # Stelle sicher, dass Links nicht über den linken Rand hinausgehen
                min_x = min(l['from'].x0 for l in left_links)
                if min_x + (target_x - avg_x) < 10.0:
                    # Anpassen, damit der linkeste Link genau bei 10px ist
                    offset_x = 10.0 - min_x
                else:
                    offset_x = target_x - avg_x
                
                offset_y = target_y - first_link_rect.y0
                
                # Extrahiere Texte auf der linken Seite
                source_text_dict = source_page.get_text("dict")
                left_texts = []
                for block in source_text_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            line_y = None
                            line_x = None
                            line_bbox = None
                            font_size = None
                            font_name = None
                            flags = 0
                            
                            for span in line["spans"]:
                                bbox = span['bbox']
                                if bbox[0] < 500:  # Text auf der linken Seite
                                    if line_y is None:
                                        line_y = bbox[1]
                                        line_x = bbox[0]
                                        line_bbox = bbox
                                    line_text += span['text']
                                    if font_size is None:
                                        font_size = span.get('size', 8)
                                    if font_name is None:
                                        font_name = span.get('font', 'helv')
                                    flags = span.get('flags', 0)
                            
                            if line_text.strip() and line_y is not None and line_x is not None:
                                left_texts.append({
                                    'text': line_text.strip(),
                                    'x': line_x,
                                    'y': line_y,
                                    'bbox': line_bbox,
                                    'font': font_name,
                                    'size': font_size,
                                    'flags': flags
                                })
                
                # Sortiere Texte nach Y-Position
                left_texts.sort(key=lambda t: t['y'])
                
                # Lösche alle alten Links auf der linken Seite
                existing_links = target_page.get_links()
                for existing_link in existing_links:
                    try:
                        link_rect = existing_link.get('from')
                        if link_rect and link_rect.x0 < 500:
                            target_page.delete_link(existing_link)
                    except:
                        pass
                
                # Lösche alte Texte und leere Boxen durch Überzeichnen mit weißem Hintergrund
                # Erweitere den Bereich, um auch leere Boxen zu entfernen
                for text_info in left_texts:
                    try:
                        bbox = text_info['bbox']
                        white_rect = fitz.Rect(bbox[0] - 10, bbox[1] - 5, bbox[2] + 10, bbox[3] + 5)
                        target_page.draw_rect(white_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
                    except:
                        pass
                
                # Lösche auch leere Boxen/Rechtecke im Bereich der Links
                for source_link in left_links:
                    try:
                        link_rect = source_link['from']
                        # Lösche alte Box durch weißes Rechteck
                        white_rect = fitz.Rect(link_rect.x0 - 2, link_rect.y0 - 2, link_rect.x1 + 2, link_rect.y1 + 2)
                        target_page.draw_rect(white_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
                    except:
                        pass
                
                # Erstelle Links und Texte zusammen an neuen Positionen
                for i, source_link in enumerate(left_links):
                    try:
                        link_rect = source_link['from']
                        
                        # Neue Link-Position = alte Position + Offset
                        new_link_rect = fitz.Rect(
                            link_rect.x0 + offset_x,
                            link_rect.y0 + offset_y,
                            link_rect.x1 + offset_x,
                            link_rect.y1 + offset_y
                        )
                        
                        # Stelle sicher, dass Link nicht über den linken Rand hinausgeht
                        if new_link_rect.x0 < 10.0:
                            diff = 10.0 - new_link_rect.x0
                            new_link_rect = fitz.Rect(
                                new_link_rect.x0 + diff,
                                new_link_rect.y0,
                                new_link_rect.x1 + diff,
                                new_link_rect.y1
                            )
                        
                        target_page_num = source_link.get('page', 0)
                        
                        # Konvertiere Seiten-Nummer
                        if isinstance(target_page_num, str):
                            try:
                                target_page_num = int(target_page_num) - 1
                            except:
                                continue
                        elif isinstance(target_page_num, int):
                            target_page_num = target_page_num - 1
                        else:
                            continue
                        
                        # Prüfe ob Zielseite existiert
                        if target_page_num < 0 or target_page_num >= total_pages:
                            continue
                        
                        # Prüfe ob dieser Link aktiv ist (Zielseite = aktuelle Seite)
                        is_active = (target_page_num == page_num)
                        
                        # Bestimme Hintergrundfarbe basierend auf Aktivierung
                        bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
                        
                        # Erstelle Link an neuer Position
                        link = {
                            "kind": fitz.LINK_GOTO,
                            "from": new_link_rect,
                            "page": target_page_num,
                            "to": fitz.Point(0, 0),
                            "zoom": 0.0
                        }
                        target_page.insert_link(link)
                        
                        # Zeichne abgerundetes Rechteck für den Link (Marine-Blau) - leichter Radius, Schatten, keine Linien
                        self.draw_rounded_rect(target_page, new_link_rect, bg_color, border_color=None, radius=3.0, shadow=True)
                        
                        # Finde zugehörigen Text (nächster Text nach Y-Position)
                        if i < len(left_texts):
                            text_info = left_texts[i]
                            
                            # Text-Position: innerhalb des Link-Rechtecks, behalte relative Position
                            text_offset_in_link = text_info['x'] - link_rect.x0
                            new_text_x = new_link_rect.x0 + text_offset_in_link
                            # Stelle sicher, dass Text nicht über den Rand hinausgeht
                            if new_text_x < 10.0:
                                new_text_x = 10.0 + 5  # 5px Padding vom Rand
                            
                            # Y-Position: Mitte des Links (baseline)
                            new_text_y = new_link_rect.y0 + (new_link_rect.height / 2) + (text_info['size'] * 0.3)
                            
                            fontname = "helv"
                            if text_info.get('flags', 0) & 16:  # Bold
                                fontname = "helv-Bold"
                            
                            target_page.insert_text(
                                (new_text_x, new_text_y),
                                text_info['text'],
                                fontsize=text_info.get('size', 8),
                                fontname=fontname,
                                color=(0.0, 0.0, 0.0)
                            )
                    except Exception as e:
                        # Ignoriere Fehler bei einzelnen Links
                        pass
            
            # Füge andere Links hinzu (nicht auf der linken Seite, z.B. Tab-Links)
            for source_link in source_links:
                try:
                    # Prüfe ob es ein Tab-Link ist (rechte Seite)
                    link_rect = source_link['from']
                    if link_rect.x0 > 500:  # Tab-Links sind auf der rechten Seite
                        continue  # Überspringe, da wir sie bereits gezeichnet haben
                    if link_rect.x0 < 500:  # Bereits verarbeitet
                        continue
                    
                    target_page_num = source_link.get('page', 0)
                    
                    # Konvertiere Seiten-Nummer
                    if isinstance(target_page_num, str):
                        try:
                            target_page_num = int(target_page_num) - 1
                        except:
                            continue
                    elif isinstance(target_page_num, int):
                        target_page_num = target_page_num - 1
                    else:
                        continue
                    
                    # Prüfe ob Zielseite existiert
                    if target_page_num < 0 or target_page_num >= total_pages:
                        continue
                    
                    # Erstelle Link
                    link = {
                        "kind": fitz.LINK_GOTO,
                        "from": source_link['from'],
                        "page": target_page_num,
                        "to": fitz.Point(0, 0),
                        "zoom": 0.0
                    }
                    target_page.insert_link(link)
                except Exception as e:
                    # Ignoriere Fehler bei einzelnen Links
                    pass
        
        source_doc.close()
        
        # Speichere PDF
        print(f"Speichere PDF: {output_path}")
        doc.save(output_path)
        doc.close()
        
        print(f"\n✓ PDF erfolgreich generiert: {output_path}")
        print(f"  - Gesamt Seiten: {total_pages}")
        print(f"  - Tabs: {len(self.tabs)}")
        print(f"\nDie PDF kann jetzt per Skript angepasst werden!")
        print(f"\nStruktur-Dokumentation:")
        print(f"  - Tab-Positionen: {self.tab_x} (x), Höhen: {[t['y'] for t in self.tabs]}")
        print(f"  - Seiten-Struktur: {list(self.page_structure.keys())}")
        
        return output_path
    
    def modify_pdf(self, pdf_path: str, modifications: Dict):
        """
        Modifiziert eine bestehende PDF
        
        Args:
            pdf_path: Pfad zur PDF
            modifications: Dict mit Modifikationen
                - "add_text": List[Dict] - Text hinzufügen
                - "remove_links": List[int] - Links entfernen (Seiten-Nummern)
                - "add_links": List[Dict] - Links hinzufügen
                - "modify_tabs": Dict - Tab-Struktur ändern
        """
        doc = fitz.open(pdf_path)
        
        # Beispiel: Text hinzufügen
        if "add_text" in modifications:
            for text_data in modifications["add_text"]:
                page_num = text_data.get("page", 1) - 1
                if 0 <= page_num < len(doc):
                    page = doc[page_num]
                    point = fitz.Point(text_data.get("x", 50), text_data.get("y", 50))
                    page.insert_text(
                        point,
                        text_data.get("text", ""),
                        fontsize=text_data.get("size", 12),
                        fontname=text_data.get("font", "helv")
                    )
        
        # Beispiel: Links entfernen
        if "remove_links" in modifications:
            for page_num in modifications["remove_links"]:
                page_idx = page_num - 1
                if 0 <= page_idx < len(doc):
                    page = doc[page_idx]
                    links = page.get_links()
                    for link in links:
                        page.delete_link(link)
        
        # Beispiel: Links hinzufügen
        if "add_links" in modifications:
            for link_data in modifications["add_links"]:
                page_num = link_data.get("page", 1) - 1
                if 0 <= page_num < len(doc):
                    page = doc[page_num]
                    rect = fitz.Rect(
                        link_data.get("x0", 0),
                        link_data.get("y0", 0),
                        link_data.get("x1", 100),
                        link_data.get("y1", 100)
                    )
                    link = {
                        "kind": fitz.LINK_GOTO,
                        "from": rect,
                        "page": link_data.get("target_page", 1) - 1,
                        "to": fitz.Point(0, 0),
                        "zoom": 0.0
                    }
                    page.insert_link(link)
        
        doc.save(pdf_path, incremental=True)
        doc.close()
        print(f"✓ PDF modifiziert: {pdf_path}")


def main():
    """Hauptfunktion"""
    generator = DynamicPDFGenerator()
    
    source = "vampire_journal.pdf"
    output = "vampire_journal_dynamic.pdf"
    
    if not os.path.exists(source):
        print(f"Fehler: {source} nicht gefunden!")
        return
    
    generator.generate_from_source(source, output)


if __name__ == "__main__":
    main()
