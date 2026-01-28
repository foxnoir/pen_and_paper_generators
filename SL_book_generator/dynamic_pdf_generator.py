#!/usr/bin/env python3
"""
Dynamic PDF Generator for Vampire Journal
Creates the PDF from scratch so it can be easily modified later.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
import os
import json
import random
import math


class DynamicPDFGenerator:
    """Generates the PDF dynamically from scratch"""
    
    def __init__(self):
        self.page_width = 595.2755737304688  # A4 width in points
        self.page_height = 841.8897705078125  # A4 height in points
        self.total_pages = 125
        
        # Tab structure (right side, Y positions) - from top to bottom
        self.tabs = [
            {"name": "Domäne", "y": 65.0, "target_page": 1, "height": 70.0},  # Correct
            {"name": "Intrigen & Interessen", "y": 143.0, "target_page": 11, "height": 110.0},  # Should have content from Notizen (page 11)
            {"name": "Runden", "y": 261.0, "target_page": 23, "height": 70.0},  # Should have content from Handouts (page 23)
            {"name": "NPCs", "y": 339.0, "target_page": 90, "height": 70.0},  # Should have content from NPCs (page 90)
            {"name": "Orte", "y": 417.0, "target_page": 81, "height": 70.0},  # Correct
            {"name": "Karten", "y": 495.0, "target_page": 30, "height": 70.0},  # Should have content from Karten (page 30)
            {"name": "Handouts", "y": 573.0, "target_page": 93, "height": 70.0},  # Should be empty, points to empty page 93
            {"name": "Notizen", "y": 651.0, "target_page": 94, "height": 70.0},  # Should be empty, points to empty page 94
            {"name": "Regeln", "y": 729.0, "target_page": 95, "height": 70.0},  # Correct
        ]
        
        # Tab width and position
        self.tab_width = 35.0  # Wider for better design and text
        self.tab_x = self.page_width - self.tab_width - 5  # Right margin with 5pt spacing
        
        # Tab design colors (RGB 0-1 for PyMuPDF) - Jade green
        self.tab_colors = {
            "background": (0.75, 0.90, 0.80),  # Light jade green (inactive)
            "border": (0.50, 0.75, 0.60),  # Jade green border
            "active": (0.50, 0.75, 0.60),  # Darker jade green (active)
            "text": (0.15, 0.15, 0.15),  # Dark text
            "shadow": (0.40, 0.65, 0.50)  # Jade green shadow
        }
        
        # Page structure
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
        
        # Pages per section
        self.pages_per_section = {
            1: 10, 11: 12, 23: 7, 30: 51, 81: 9, 90: 3, 93: 1, 94: 1, 95: 30
        }
    
    def analyze_source_pdf(self, source_path: str) -> Dict:
        """Analyzes the original PDF and extracts all structures"""
        print(f"Analyzing original PDF: {source_path}")
        source_doc = fitz.open(source_path)
        
        analysis = {
            "pages": [],
            "fonts": set(),
            "links": {}
        }
        
        for page_num in range(min(10, len(source_doc))):  # Analyze first 10 pages as example
            page = source_doc[page_num]
            text_dict = page.get_text("dict")
            
            page_data = {
                "page_num": page_num + 1,
                "text_elements": [],
                "links": []
            }
            
            # Extract text elements
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
            
            # Extract links
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
        """Creates a page with tab navigation"""
        page = doc.new_page(width=self.page_width, height=self.page_height)
        
        # Add tabs (after all pages exist)
        return page
    
    def draw_blood_splatters(self, page: fitz.Page):
        """Draws random ink stain clusters in the background (pure grayscale)"""
        # First light stains (#D4D3D3 = RGB 212/255, 211/255, 211/255)
        # Average = (212+211+211)/3 = 211.33 -> true grayscale
        base_gray_light = (212 + 211 + 211) / 3 / 255
        self._draw_ink_clusters(page, base_gray=base_gray_light, variation=0.05)
        
        # Then darker stains (#7C7979 = RGB 124/255, 121/255, 121/255)
        # Average = (124+121+121)/3 = 122 -> true grayscale
        base_gray_dark = (124 + 121 + 121) / 3 / 255
        # Dark ones can overlap the light ones
        self._draw_ink_clusters(page, base_gray=base_gray_dark, variation=0.06)
    
    def _draw_ink_clusters(self, page: fitz.Page, base_gray: float, variation: float):
        """Draws ink stain clusters with given grayscale value (pure grayscale, no color)"""
        # Number of clusters per run (1-3 spots, so max. 6 clusters total)
        num_clusters = random.randint(1, 3)
        
        for _ in range(num_clusters):
            # Random position for cluster center
            cluster_x = random.uniform(80, self.page_width - 80)
            cluster_y = random.uniform(80, self.page_height - 80)
            
            # Number of spots in this cluster (4-19)
            num_spots = random.randint(4, 19)
            
            # Cluster radius (how far spots are from center)
            cluster_radius = random.uniform(15, 40)
            
            for _ in range(num_spots):
                # Position relative to cluster center
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, cluster_radius)
                x = cluster_x + math.cos(angle) * distance
                y = cluster_y + math.sin(angle) * distance
                
                # Ensure spots are not outside the page
                x = max(10, min(x, self.page_width - 10))
                y = max(10, min(y, self.page_height - 10))
                
                # Random grayscale value based on base gray with variation
                # All RGB channels have the same value for pure grayscale
                gray_value = max(0, min(1, base_gray + random.uniform(-variation, variation)))
                color = (gray_value, gray_value, gray_value)
                
                # Random size (smaller stains)
                base_size = random.uniform(1.5, 6)
                
                # Random form: drop or ink stain
                splatter_type = random.choice(['drop', 'stain', 'small_stain'])
                
                try:
                    if splatter_type == 'drop':
                        # Single drop - small and subtle
                        width = base_size * random.uniform(0.8, 1.2)
                        height = base_size * random.uniform(1.5, 2.2)
                        
                        # Use ellipse for drop shape
                        rect = fitz.Rect(x - width/2, y - height/2, x + width/2, y + height/2)
                        page.draw_oval(rect, color=color, fill=color, width=0)
                        
                    elif splatter_type == 'stain':
                        # Ink stain - irregular, organic shape
                        shape = page.new_shape()
                        num_points = random.randint(8, 14)
                        points = []
                        for i in range(num_points):
                            angle = (2 * math.pi * i) / num_points
                            # Irregular radius for organic shape
                            radius_variation = random.uniform(0.7, 1.2)
                            radius = base_size * radius_variation
                            # Slight irregularity
                            noise = random.uniform(-0.2, 0.2)
                            px = x + math.cos(angle + noise) * radius
                            py = y + math.sin(angle + noise) * radius
                            points.append(fitz.Point(px, py))
                        
                        shape.draw_polyline(points)
                        shape.finish(fill=color, color=color, width=0)
                        shape.commit()
                        
                    elif splatter_type == 'small_stain':
                        # Small ink stain - compact
                        width = base_size * random.uniform(0.9, 1.3)
                        height = base_size * random.uniform(0.9, 1.3)
                        rect = fitz.Rect(x - width/2, y - height/2, x + width/2, y + height/2)
                        page.draw_oval(rect, color=color, fill=color, width=0)
                        
                except Exception as e:
                    # Fallback: simple drop
                    try:
                        width = base_size * random.uniform(0.7, 1.0)
                        height = base_size * random.uniform(1.3, 2.0)
                        rect = fitz.Rect(x - width/2, y - height/2, x + width/2, y + height/2)
                        page.draw_oval(rect, color=color, fill=color, width=0)
                    except:
                        pass
    
    def draw_rounded_rect(self, page: fitz.Page, rect: fitz.Rect, fill_color: tuple, border_color: tuple = None, radius: float = 8.0, shadow: bool = False):
        """Draws a rounded rectangle with given radius"""
        try:
            import math
            
            # Calculate corners
            x0, y0 = rect.x0, rect.y0
            x1, y1 = rect.x1, rect.y1
            
            # Ensure radius is not too large
            radius = min(radius, min(rect.width, rect.height) / 2)
            
            # Draw shadow first (slightly offset to right/bottom)
            if shadow:
                shadow_offset = 1.5
                shadow_rect = fitz.Rect(
                    x0 + shadow_offset,
                    y0 + shadow_offset,
                    x1 + shadow_offset,
                    y1 + shadow_offset
                )
                self._draw_rounded_rect_shape(page, shadow_rect, self.tab_colors["shadow"], None, radius)
            
            # Draw main rectangle
            self._draw_rounded_rect_shape(page, rect, fill_color, border_color, radius)
            
        except Exception as e:
            # Fallback: normal rectangle if path fails
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
        """Helper function to draw a rounded rectangle"""
        try:
            x0, y0 = rect.x0, rect.y0
            x1, y1 = rect.x1, rect.y1
            
            # Use Shape object for complex paths
            shape = page.new_shape()
            
            # Draw rounded rectangle by combining rectangles and circles
            # Main rectangle (without corners)
            inner_rect = fitz.Rect(x0 + radius, y0, x1 - radius, y1)
            shape.draw_rect(inner_rect)
            
            # Top horizontal rectangles
            top_rect = fitz.Rect(x0 + radius, y0, x1 - radius, y0 + radius)
            shape.draw_rect(top_rect)
            
            # Bottom horizontal rectangles
            bottom_rect = fitz.Rect(x0 + radius, y1 - radius, x1 - radius, y1)
            shape.draw_rect(bottom_rect)
            
            # Left vertical rectangles
            left_rect = fitz.Rect(x0, y0 + radius, x0 + radius, y1 - radius)
            shape.draw_rect(left_rect)
            
            # Right vertical rectangles
            right_rect = fitz.Rect(x1 - radius, y0 + radius, x1, y1 - radius)
            shape.draw_rect(right_rect)
            
            # Draw circles at corners
            # Top left corner
            shape.draw_circle(fitz.Point(x0 + radius, y0 + radius), radius)
            
            # Top right corner
            shape.draw_circle(fitz.Point(x1 - radius, y0 + radius), radius)
            
            # Bottom left corner
            shape.draw_circle(fitz.Point(x0 + radius, y1 - radius), radius)
            
            # Bottom right corner
            shape.draw_circle(fitz.Point(x1 - radius, y1 - radius), radius)
            
            # Fill everything (without border if border_color is None)
            border_width = 0 if border_color is None else 1.0
            shape.finish(fill=fill_color, color=border_color if border_color else fill_color, width=border_width)
            shape.commit()
            
        except Exception as e:
            # Fallback: normal rectangle if path fails
            page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color)
    
    def draw_modern_tab(self, page: fitz.Page, tab: Dict, page_num: int, is_active: bool = False, original_text: Dict = None):
        """Draws a modern journal tab with design"""
        tab_rect = fitz.Rect(
            self.tab_x,
            tab["y"],
            self.tab_x + self.tab_width,
            tab["y"] + tab["height"]
        )
        
        # Determine color (active tab is darker)
        bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
        
        # Draw shadow (slightly offset to right/bottom)
        shadow_rect = fitz.Rect(
            tab_rect.x0 + 1.5,
            tab_rect.y0 + 1.5,
            tab_rect.x1 + 1.5,
            tab_rect.y1 + 1.5
        )
        page.draw_rect(shadow_rect, color=self.tab_colors["shadow"], width=0, fill=self.tab_colors["shadow"])
        
        # Draw tab background (normal rectangle, no rounded corners)
        page.draw_rect(tab_rect, color=self.tab_colors["border"], width=1.0, fill=bg_color)
        
        # Draw inner highlight line at top for 3D effect
        highlight_rect = fitz.Rect(
            tab_rect.x0 + 0.5,
            tab_rect.y0 + 0.5,
            tab_rect.x1 - 0.5,
            tab_rect.y0 + 2
        )
        page.draw_rect(highlight_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
        
        # Draw bottom shadow line for depth
        shadow_line = fitz.Rect(
            tab_rect.x0 + 0.5,
            tab_rect.y1 - 2,
            tab_rect.x1 - 0.5,
            tab_rect.y1 - 0.5
        )
        page.draw_rect(shadow_line, color=self.tab_colors["border"], width=0, fill=self.tab_colors["border"])
        
        # Add text - use original text if available
        if original_text:
            # Calculate position for text - significantly shifted to left
            # Shift text 8-10pt to left (negative value = to left)
            text_offset_left = -9.0
            
            # Use insert_textbox with rotation for vertical text
            try:
                from fitz import Rect
                # Text-Rect significantly shifted to left
                text_rect = Rect(
                    tab_rect.x0 + 2 + text_offset_left,
                    tab_rect.y0 + 2,
                    tab_rect.x1 - 2 + text_offset_left,
                    tab_rect.y1 - 2
                )
                
                # Try to insert text with rotation
                # rotate=270 means 270° clockwise = 90° counter-clockwise
                rc = page.insert_textbox(
                    text_rect,
                    original_text['text'],
                    fontsize=original_text.get('fontsize', 8),
                    fontname=original_text.get('fontname', 'helv-Bold'),
                    color=(0.0, 0.0, 0.0),
                    align=1,  # Centered
                    rotate=270  # Vertical
                )
                
                if rc < 0:
                    # Fallback: Simple text without rotation, shifted to left
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
                # Last fallback: Simple text, shifted to left
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
        
        # Add link
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
        """Extracts tab labels from the original page"""
        text_dict = source_page.get_text("dict")
        tab_texts = []
        
        # Search for text on the right side (tab area)
        # Tabs are between x=550 and x=595 (right edge)
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_y = None
                    line_x_min = None
                    line_x_max = None
                    
                    for span in line["spans"]:
                        bbox = span['bbox']
                        # Right side (x > 550) - tab area
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
                        # Filter very short texts (probably not tab labels)
                        if len(cleaned_text) > 1:
                            tab_texts.append({
                                'text': cleaned_text,
                                'y': line_y,
                                'x': line_x_min if line_x_min else 560
                            })
        
        # Sort by Y position (from top to bottom)
        tab_texts.sort(key=lambda x: x['y'])
        
        # Debug: Show found texts
        print(f"  Found tab texts (before filtering): {len(tab_texts)}")
        for i, txt in enumerate(tab_texts[:12]):
            print(f"    {i+1}. '{txt['text']}' at Y={txt['y']:.1f}")
        
        # Extract only the texts
        texts = [item['text'] for item in tab_texts]
        
        # Expected tab names (if extraction fails)
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
        
        # If we have less than 9 texts, use default names
        if len(texts) < 9:
            print(f"  Warning: Only {len(texts)} tab texts found, using default names")
            return default_tabs[:len(self.tabs)]
        
        # Take the first 9 texts (should be the tab labels)
        return texts[:9]
    
    def extract_tab_text_elements(self, source_page: fitz.Page) -> List[Dict]:
        """Extracts tab text elements with positions from the original page"""
        text_dict = source_page.get_text("dict")
        tab_texts = []
        
        # Search for text on the right side (tab area)
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
                        # Right side (x > 550) - tab area
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
        
        # Sort by Y position (from top to bottom)
        tab_texts.sort(key=lambda x: x['y'])
        return tab_texts[:9]  # Take the first 9 (should be the tab labels)
    
    def add_tabs_to_page(self, page: fitz.Page, page_num: int, tab_text_elements: List[Dict] = None):
        """Adds modern tab tabs to a page"""
        # Determine which page is active (based on tab targets)
        active_tab = None
        for tab in self.tabs:
            if tab["target_page"] == page_num:
                active_tab = tab
                break
        
        # Draw all tabs
        for i, tab in enumerate(self.tabs):
            is_active = (tab == active_tab)
            self.draw_modern_tab(page, tab, page_num, is_active, tab_text_elements[i] if tab_text_elements and i < len(tab_text_elements) else None)
    
    def add_text_to_page(self, page: fitz.Page, text_elements: List[Dict]):
        """Adds text elements to a page"""
        for elem in text_elements:
            try:
                bbox = elem['bbox']
                point = fitz.Point(bbox[0], bbox[1])
                
                # Determine font
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
                # Ignore errors for individual text elements
                pass
    
    def add_links_to_page(self, page: fitz.Page, links: List[Dict], total_pages: int):
        """Adds links to a page"""
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
        """Generates PDF based on original PDF"""
        print("=" * 60)
        print("DYNAMIC PDF GENERATOR")
        print("=" * 60)
        print()
        
        # Load original PDF
        source_doc = fitz.open(source_path)
        total_pages = len(source_doc)
        
        print(f"Original has {total_pages} pages")
        print(f"Creating dynamic copy...")
        
        # Create new PDF
        doc = fitz.open()
        
        print("Extracting tab labels from original...")
        
        # Extract tab texts from the first page of the original PDF
        source_page_0 = source_doc[0]
        tab_texts = self.extract_tab_texts(source_page_0)
        tab_text_elements = self.extract_tab_text_elements(source_page_0)
        
        # Update tab names with original texts if available
        if len(tab_texts) >= len(self.tabs):
            # Create mapping from tab names to target_page
            # Based on description: NPCs and Karten are swapped
            name_to_target = {
                "Domäne": 1,
                "Intrigen & Interessen": 11,
                "Runden": 23,
                "NPCs": 90,  # NPCs should point to page 90
                "Orte": 81,
                "Karten": 30,  # Karten should point to page 30
                "Handouts": 93,
                "Notizen": 94,
                "Regeln": 95
            }
            
            for i, tab in enumerate(self.tabs):
                if i < len(tab_texts):
                    extracted_name = tab_texts[i]
                    tab["name"] = extracted_name
                    # Set target_page based on extracted name
                    if extracted_name in name_to_target:
                        tab["target_page"] = name_to_target[extracted_name]
            print(f"  Found: {len(tab_texts)} tab labels")
        else:
            print(f"  Warning: Only {len(tab_texts)} tab texts found, using default names")
        
        # Copy all pages - insert_pdf copies content and design
        doc.insert_pdf(source_doc, from_page=0, to_page=total_pages - 1)
        
        print("Drawing blood splatters in background...")
        
        # Draw blood splatters on all pages (BEFORE tabs are drawn)
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.draw_blood_splatters(target_page)
        
        print("Drawing modern tab tabs...")
        
        # Draw modern tabs on all pages
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.add_tabs_to_page(target_page, page_num + 1, tab_text_elements)
        
        print("Copying and repairing links...")
        
        # Target position for upper links: 10px from left, 20px from top
        target_x = 10.0
        target_y = 20.0
        
        # Copy all links from original and reset them (except tab links, which are already set)
        for page_num in range(total_pages):
            source_page = source_doc[page_num]
            target_page = doc[page_num]
            
            # Hole alle Links von der Original-Seite
            source_links = source_page.get_links()
            
            # Filter links on the left side (upper links)
            left_links = [l for l in source_links if l['from'].x0 < 500]
            
            if left_links:
                # Sort links by Y position (from top to bottom)
                left_links.sort(key=lambda l: l['from'].y0)
                
                # Calculate offset based on first link (topmost)
                first_link_rect = left_links[0]['from']
                avg_x = sum(l['from'].x0 for l in left_links) / len(left_links)
                
                # Ensure links don't go beyond the left edge
                min_x = min(l['from'].x0 for l in left_links)
                if min_x + (target_x - avg_x) < 10.0:
                    # Adjust so leftmost link is exactly at 10px
                    offset_x = 10.0 - min_x
                else:
                    offset_x = target_x - avg_x
                
                offset_y = target_y - first_link_rect.y0
                
                # Extract texts on the left side
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
                                if bbox[0] < 500:  # Text on the left side
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
                
                # Sort texts by Y position
                left_texts.sort(key=lambda t: t['y'])
                
                # Delete all old links on the left side
                existing_links = target_page.get_links()
                for existing_link in existing_links:
                    try:
                        link_rect = existing_link.get('from')
                        if link_rect and link_rect.x0 < 500:
                            target_page.delete_link(existing_link)
                    except:
                        pass
                
                # Delete old texts and empty boxes by drawing over with white background
                # Extend the area to also remove empty boxes
                for text_info in left_texts:
                    try:
                        bbox = text_info['bbox']
                        white_rect = fitz.Rect(bbox[0] - 10, bbox[1] - 5, bbox[2] + 10, bbox[3] + 5)
                        target_page.draw_rect(white_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
                    except:
                        pass
                
                # Also delete empty boxes/rectangles in the link area
                for source_link in left_links:
                    try:
                        link_rect = source_link['from']
                        # Delete old box with white rectangle
                        white_rect = fitz.Rect(link_rect.x0 - 2, link_rect.y0 - 2, link_rect.x1 + 2, link_rect.y1 + 2)
                        target_page.draw_rect(white_rect, color=(1.0, 1.0, 1.0), width=0, fill=(1.0, 1.0, 1.0))
                    except:
                        pass
                
                # Create links and texts together at new positions
                for i, source_link in enumerate(left_links):
                    try:
                        link_rect = source_link['from']
                        
                        # New link position = old position + offset
                        new_link_rect = fitz.Rect(
                            link_rect.x0 + offset_x,
                            link_rect.y0 + offset_y,
                            link_rect.x1 + offset_x,
                            link_rect.y1 + offset_y
                        )
                        
                        # Ensure link doesn't go beyond the left edge
                        if new_link_rect.x0 < 10.0:
                            diff = 10.0 - new_link_rect.x0
                            new_link_rect = fitz.Rect(
                                new_link_rect.x0 + diff,
                                new_link_rect.y0,
                                new_link_rect.x1 + diff,
                                new_link_rect.y1
                            )
                        
                        target_page_num = source_link.get('page', 0)
                        
                        # Convert page number
                        if isinstance(target_page_num, str):
                            try:
                                target_page_num = int(target_page_num) - 1
                            except:
                                continue
                        elif isinstance(target_page_num, int):
                            target_page_num = target_page_num - 1
                        else:
                            continue
                        
                        # Check if target page exists
                        if target_page_num < 0 or target_page_num >= total_pages:
                            continue
                        
                        # Check if this link is active (target page = current page)
                        is_active = (target_page_num == page_num)
                        
                        # Determine background color based on activation
                        bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
                        
                        # Create link at new position
                        link = {
                            "kind": fitz.LINK_GOTO,
                            "from": new_link_rect,
                            "page": target_page_num,
                            "to": fitz.Point(0, 0),
                            "zoom": 0.0
                        }
                        target_page.insert_link(link)
                        
                        # Draw rounded rectangle for the link (Navy blue) - light radius, shadow, no lines
                        self.draw_rounded_rect(target_page, new_link_rect, bg_color, border_color=None, radius=3.0, shadow=True)
                        
                        # Find associated text (next text by Y position)
                        if i < len(left_texts):
                            text_info = left_texts[i]
                            
                            # Text position: within link rectangle, keep relative position
                            text_offset_in_link = text_info['x'] - link_rect.x0
                            new_text_x = new_link_rect.x0 + text_offset_in_link
                            # Ensure text doesn't go beyond the edge
                            if new_text_x < 10.0:
                                new_text_x = 10.0 + 5  # 5px padding from edge
                            
                            # Y position: center of link (baseline)
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
                        # Ignore errors for individual links
                        pass
            
            # Add other links (not on the left side, e.g. tab links)
            for source_link in source_links:
                try:
                    # Check if it's a tab link (right side)
                    link_rect = source_link['from']
                    if link_rect.x0 > 500:  # Tab links are on the right side
                        continue  # Skip, as we already drew them
                    if link_rect.x0 < 500:  # Already processed
                        continue
                    
                    target_page_num = source_link.get('page', 0)
                    
                    # Convert page number
                    if isinstance(target_page_num, str):
                        try:
                            target_page_num = int(target_page_num) - 1
                        except:
                            continue
                    elif isinstance(target_page_num, int):
                        target_page_num = target_page_num - 1
                    else:
                        continue
                    
                    # Check if target page exists
                    if target_page_num < 0 or target_page_num >= total_pages:
                        continue
                    
                    # Create link
                    link = {
                        "kind": fitz.LINK_GOTO,
                        "from": source_link['from'],
                        "page": target_page_num,
                        "to": fitz.Point(0, 0),
                        "zoom": 0.0
                    }
                    target_page.insert_link(link)
                except Exception as e:
                    # Ignore errors for individual links
                    pass
        
        source_doc.close()
        
        # Save PDF
        print(f"Saving PDF: {output_path}")
        doc.save(output_path)
        doc.close()
        
        print(f"\n✓ PDF successfully generated: {output_path}")
        print(f"  - Total pages: {total_pages}")
        print(f"  - Tabs: {len(self.tabs)}")
        print(f"\nThe PDF can now be modified via script!")
        print(f"\nStructure documentation:")
        print(f"  - Tab positions: {self.tab_x} (x), heights: {[t['y'] for t in self.tabs]}")
        print(f"  - Page structure: {list(self.page_structure.keys())}")
        
        return output_path
    
    def modify_pdf(self, pdf_path: str, modifications: Dict):
        """
        Modifies an existing PDF
        
        Args:
            pdf_path: Path to PDF
            modifications: Dict with modifications
                - "add_text": List[Dict] - Add text
                - "remove_links": List[int] - Remove links (page numbers)
                - "add_links": List[Dict] - Add links
                - "modify_tabs": Dict - Change tab structure
        """
        doc = fitz.open(pdf_path)
        
        # Example: Add text
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
        
        # Example: Remove links
        if "remove_links" in modifications:
            for page_num in modifications["remove_links"]:
                page_idx = page_num - 1
                if 0 <= page_idx < len(doc):
                    page = doc[page_idx]
                    links = page.get_links()
                    for link in links:
                        page.delete_link(link)
        
        # Example: Add links
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
        print(f"✓ PDF modified: {pdf_path}")


def main():
    """Main function"""
    generator = DynamicPDFGenerator()
    
    source = "vampire_journal.pdf"
    output = "vampire_journal_dynamic.pdf"
    
    if not os.path.exists(source):
        print(f"Error: {source} not found!")
        return
    
    generator.generate_from_source(source, output)


if __name__ == "__main__":
    main()
