#!/usr/bin/env python3
"""
Layout Generator for Vampire Journal PDF
Handles all visual design elements: tabs, blood splatters, rounded rectangles, etc.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Optional
import random
import math
import os


class LayoutGenerator:
    """Generates layout elements (tabs, blood splatters, etc.) for PDF pages"""
    
    def __init__(self, page_width: float = 595.2755737304688, page_height: float = 841.8897705078125):
        self.page_width = page_width
        self.page_height = page_height
        
        # Tab width and position
        self.tab_width = 35.0  # Wider for better design and text
        self.tab_x = self.page_width - self.tab_width - 5  # Right margin with 5pt spacing
        
        # Tab design colors (RGB 0-1 for PyMuPDF)
        # #EEDCC8 = RGB(238, 220, 200) - inactive (beige/cream)
        # #D0C4B4 = RGB(208, 196, 180) - active (darker beige)
        self.tab_colors = {
            "background": (238 / 255, 220 / 255, 200 / 255),  # #EEDCC8 (inactive)
            "border": (208 / 255, 196 / 255, 180 / 255),  # #D0C4B4 border
            "active": (208 / 255, 196 / 255, 180 / 255),  # #D0C4B4 (active)
            "text": (0.15, 0.15, 0.15),  # Dark text
            "shadow": (200 / 255, 190 / 255, 175 / 255)  # Slightly darker shadow
        }
    
    def draw_blood_splatters(self, page: fitz.Page):
        """Draws random blood stain clusters in the background with custom colors"""
        # Light stains (#CD2103 = RGB 205/255, 33/255, 3/255) - brighter red
        light_color = (205 / 255, 33 / 255, 3 / 255)
        self._draw_ink_clusters(page, base_color=light_color, variation=0.05, is_color=True)
        
        # Darker stains (#772616 = RGB 119/255, 38/255, 22/255) - darker red/brown
        dark_color = (119 / 255, 38 / 255, 22 / 255)
        # Dark ones can overlap the light ones
        self._draw_ink_clusters(page, base_color=dark_color, variation=0.06, is_color=True)
    
    def _draw_ink_clusters(self, page: fitz.Page, base_color=None, base_gray=None, variation: float=0.05, is_color: bool=False):
        """Draws blood stain clusters with given color or grayscale value"""
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
                
                # Calculate color based on type
                if is_color and base_color:
                    # Color mode: apply variation to each RGB channel independently
                    r = max(0, min(1, base_color[0] + random.uniform(-variation, variation)))
                    g = max(0, min(1, base_color[1] + random.uniform(-variation, variation)))
                    b = max(0, min(1, base_color[2] + random.uniform(-variation, variation)))
                    color = (r, g, b)
                elif base_gray is not None:
                    # Grayscale mode (backward compatibility)
                    gray_value = max(0, min(1, base_gray + random.uniform(-variation, variation)))
                    color = (gray_value, gray_value, gray_value)
                else:
                    # Fallback to default gray
                    color = (0.5, 0.5, 0.5)
                
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
        
        # Add text - use tab name from JSON (not from original_text!)
        # original_text is only used for font styling
        tab_name = tab.get("name", "")
        if tab_name:
            # Calculate position for text - significantly shifted to left
            # Shift text 8-10pt to left (negative value = to left)
            text_offset_left = -9.0
            
            # Get font styling from original_text if available, otherwise use defaults
            # Make text larger and bold for right-side tabs
            fontsize = 11  # Increased from 8 to 11 for better visibility and bold appearance
            fontname = 'helv-Bold'  # Always use bold
            if original_text:
                # Use larger size from original if available, but ensure minimum 11
                original_size = original_text.get('fontsize', 8)
                fontsize = max(11, original_size)  # At least 11pt for bold appearance
                # Always use bold for right tabs
                fontname = 'helv-Bold'
            
            # Use insert_textbox with rotation (most reliable method)
            from fitz import Rect
            # Text-Rect for vertical text (rotated 90° counter-clockwise)
            # The rect should be tall and narrow for vertical text
            text_rect = Rect(
                tab_rect.x0 + 2 + text_offset_left,
                tab_rect.y0 + 2,
                tab_rect.x1 - 2 + text_offset_left,
                tab_rect.y1 - 2
            )
            
            # Use insert_textbox with rotation - ensure fonts are available
            # First, ensure helv-Bold font is available by inserting invisible text
            try:
                page.insert_text((0, 0), "", fontsize=0.1, fontname='helv-Bold', render_mode=3)
            except:
                pass
            
            from fitz import Rect
            text_rect = Rect(
                tab_rect.x0 + 2 + text_offset_left,
                tab_rect.y0 + 2,
                tab_rect.x1 - 2 + text_offset_left,
                tab_rect.y1 - 2
            )
            
            # Try insert_textbox with rotation and bold font
            # Note: insert_textbox may not support fontname parameter with rotation
            # So we'll try multiple approaches
            rc = -1
            
            # Calculate center position for text
            center_x = tab_rect.x0 + self.tab_width / 2 + text_offset_left
            center_y = tab_rect.y0 + tab["height"] / 2
            
            # Method 1: Try using TextWriter for bold rotated text (most reliable for bold)
            rc = -1
            try:
                writer = fitz.TextWriter(page.rect)
                writer.append(
                    fitz.Point(center_x, center_y),
                    tab_name,
                    fontsize=fontsize,
                    fontname='helv-Bold',
                    color=(0.0, 0.0, 0.0)
                )
                # Rotate 90° counter-clockwise around center
                writer.transform((0, -1, 1, 0, center_x + center_y, center_y - center_x))
                writer.write_text(page)
                rc = 0  # Success
            except:
                rc = -1
            
            # Method 2: If TextWriter fails, try insert_textbox with rotation
            if rc < 0:
                try:
                    rc = page.insert_textbox(
                        text_rect,
                        tab_name,
                        fontsize=fontsize,
                        fontname='helv-Bold',
                        color=(0.0, 0.0, 0.0),
                        align=1,
                        rotate=270
                    )
                except:
                    rc = -1
            
            # Method 3: If that fails, try without fontname but with larger size
            if rc < 0:
                try:
                    rc = page.insert_textbox(
                        text_rect,
                        tab_name,
                        fontsize=fontsize,  # Larger size makes it appear bolder
                        color=(0.0, 0.0, 0.0),
                        align=1,
                        rotate=270
                    )
                except:
                    rc = -1
            
            # Method 4: Final fallback - insert_text with bold (no rotation)
            if rc < 0:
                try:
                    page.insert_text(
                        (center_x, center_y),
                        tab_name,
                        fontsize=fontsize,
                        fontname='helv-Bold',
                        color=(0.0, 0.0, 0.0)
                    )
                except:
                    # Last resort: without fontname
                    try:
                        page.insert_text(
                            (center_x, center_y),
                            tab_name,
                            fontsize=fontsize,
                            color=(0.0, 0.0, 0.0)
                        )
                    except:
                        pass
        
        # Add link
        link = {
            "kind": fitz.LINK_GOTO,
            "from": tab_rect,
            "page": tab["target_page"] - 1,  # 0-based
            "to": fitz.Point(0, 0),
            "zoom": 0.0
        }
        try:
            page.insert_link(link)
        except:
            pass
    
    def add_tabs_to_page(self, page: fitz.Page, page_num: int, tabs: List[Dict], tab_text_elements: List[Dict] = None, page_structure: Dict = None):
        """Adds modern tab tabs to a page"""
        # Determine which tab is active
        # A tab is active if:
        # 1. The page is the exact target_page, OR
        # 2. The page belongs to this tab (based on page_structure)
        active_tab = None
        
        # First check exact target_page match
        for tab in tabs:
            if tab["target_page"] == page_num:
                active_tab = tab
                break
        
        # If no exact match and we have page_structure, check by tab_name
        # This ensures tabs stay active when viewing their subsections
        if active_tab is None and page_structure:
            page_info = page_structure.get(page_num)
            if page_info:
                current_tab_name = page_info.get("tab_name")
                if current_tab_name:
                    for tab in tabs:
                        if tab["name"] == current_tab_name:
                            active_tab = tab
                            break
        
        # Draw all tabs
        for i, tab in enumerate(tabs):
            is_active = (tab == active_tab)
            text_element = tab_text_elements[i] if tab_text_elements and i < len(tab_text_elements) else None
            self.draw_modern_tab(page, tab, page_num, is_active, text_element)
    
    def add_upper_tabs_to_page(self, page: fitz.Page, page_num: int, page_structure: Dict, tab_subsections: Dict, metadata: Dict):
        """Adds upper tabs (left top) based on page structure and subsections from JSON"""
        # Get page info
        page_info = page_structure.get(page_num)
        if not page_info:
            return
        
        tab_name = page_info.get("tab_name")
        subsection_name = page_info.get("subsection")
        sub_subsection_name = page_info.get("sub_subsection")
        
        # Get subsections for this tab
        tab_info = tab_subsections.get(tab_name)
        if not tab_info:
            return
        
        # Get subsections dynamically - check multiple possible locations
        subsections = tab_info.get("subsections", [])
        
        # If no subsections in "subsections", check tab_data directly
        if not subsections:
            tab_data = tab_info.get("tab_data", {})
            if tab_data:
                # Check for subsections_left_top_tabs (most common location)
                subsections = tab_data.get("subsections_left_top_tabs", [])
        
        # If still no subsections, return early
        if not subsections:
            return
        
        # Get position from metadata
        upper_tabs_pos = metadata.get("upper_tabs_position", {"x": 10.0, "y": 20.0})
        start_x = upper_tabs_pos.get("x", 10.0)
        start_y = upper_tabs_pos.get("y", 20.0)
        
        # Tab dimensions - optimized
        tab_height = 18.0
        tab_width_base = 55.0  # Optimized base width
        tab_spacing = 3.5  # Optimized spacing
        row_spacing = 6.0
        
        # Maximum width to avoid overlapping with right tabs
        max_width = self.tab_x - 15  # Increased available width to allow wider tabs (was 20)
        
        current_x = start_x
        current_y = start_y
        
        # First row: subsections_left_top_tabs
        # IMPORTANT: Don't show active subsection in first row!
        first_row_tabs = []
        second_row_tabs = []
        
        # Find target pages for subsections and sub-subsections
        subsection_target_pages = {}  # subsection_name -> page_num
        sub_subsection_target_pages = {}  # (subsection_name, sub_subsection_name) -> page_num
        
        # Search through page_structure to find target pages
        for pg_num, pg_info in page_structure.items():
            if pg_info.get("tab_name") == tab_name:
                pg_subsection = pg_info.get("subsection")
                pg_sub_subsection = pg_info.get("sub_subsection")
                
                if pg_subsection and not pg_sub_subsection:
                    # This is a subsection page
                    subsection_target_pages[pg_subsection] = pg_num
                elif pg_subsection and pg_sub_subsection:
                    # This is a sub-subsection page
                    sub_subsection_target_pages[(pg_subsection, pg_sub_subsection)] = pg_num
        
        for subsection in subsections:
            subsection_name_curr = subsection.get("name", "")
            # Get sub-subsections - check multiple possible field names dynamically
            sub_subsections = subsection.get("seconnd_subsections_left_tabs", [])
            if not sub_subsections:
                sub_subsections = subsection.get("sub_subsections", [])
            if not sub_subsections:
                # Also check for alternative spelling
                sub_subsections = subsection.get("second_subsections_left_tabs", [])
            
            # Always add subsection to first row (show all, active ones in active color)
            target_page = subsection_target_pages.get(subsection_name_curr)
            is_subsection_active = (subsection_name_curr == subsection_name)
            first_row_tabs.append({
                "name": subsection_name_curr,
                "is_active": is_subsection_active,  # Active ones stay visible but in active color
                "target_page": target_page
            })
            
            # Only add sub-subsections to second row if this subsection is active
            # If subsection_name is None, don't show any sub-subsections
            if subsection_name is not None and subsection_name_curr == subsection_name:
                for sub_subsection in sub_subsections:
                    target_page = sub_subsection_target_pages.get((subsection_name, sub_subsection))
                    second_row_tabs.append({
                        "name": sub_subsection,
                        "is_active": (sub_subsection == sub_subsection_name),
                        "target_page": target_page
                    })
        
        # Draw first row
        row_y = current_y
        row_start_x = start_x
        
        for tab_data in first_row_tabs:
            tab_name_upper = tab_data["name"]
            is_active = tab_data["is_active"]
            
            # Calculate tab width dynamically based on actual text width
            font_size = 9
            text_width_pt = None
            
            # Try multiple methods to get accurate text width
            # Method 1: Use fitz.get_text_length (most accurate) - try Bold first
            try:
                text_width_pt = fitz.get_text_length(tab_name_upper, fontname='helv-Bold', fontsize=font_size)
            except:
                pass
            
            # Method 2: Try with regular helv font if Bold fails
            if text_width_pt is None:
                try:
                    text_width_pt = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                except:
                    pass
            
            # Method 3: Improved character-based estimation (more accurate for special cases)
            if text_width_pt is None:
                # More accurate character width mapping for helv-Bold
                # Based on actual font metrics - these are multipliers for font_size
                char_widths = {
                    # Wide characters (need more space)
                    '&': 0.90, 'W': 0.90, 'M': 0.90, 'w': 0.75, 'm': 0.75,
                    'Q': 0.85, 'D': 0.80, 'O': 0.80, 'G': 0.80,
                    'A': 0.75, 'V': 0.70, 'Y': 0.70,
                    # Narrow characters (need less space)
                    'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                    'j': 0.25, 'I': 0.25,
                    # Space
                    ' ': 0.30,
                    # Special characters (Umlaute and special chars)
                    'ö': 0.65, 'ä': 0.65, 'ü': 0.65, 'ß': 0.60,
                    'Ö': 0.80, 'Ä': 0.80, 'Ü': 0.80,
                    # Other common characters
                    'h': 0.60, 'n': 0.55, 'u': 0.55, 'o': 0.60, 'a': 0.55,
                    'e': 0.55, 's': 0.50, 'c': 0.50, 'd': 0.60, 'g': 0.60,
                    'b': 0.60, 'p': 0.60, 'q': 0.60, 'k': 0.55, 'v': 0.55,
                    'x': 0.55, 'y': 0.55, 'z': 0.50
                }
                estimated_width = 0
                for char in tab_name_upper:
                    # Use uppercase for lookup, but keep original case for width
                    char_lower = char.lower()
                    char_upper = char.upper()
                    # Check both cases
                    char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.60)))
                    estimated_width += char_width * font_size
                text_width_pt = estimated_width
            
            # Dynamic padding based on text length + 4px extra on each side (8px total)
            # Special handling for texts with "&" and longer texts like "Freies Gelände"
            has_ampersand = '&' in tab_name_upper
            text_length = len(tab_name_upper)
            
            # Extra padding for "&" characters - they need significantly more breathing room
            if has_ampersand:
                if text_width_pt > 50:  # Long texts with "&" like "Ziele & Ambitionen"
                    extra_ampersand_padding = 16
                else:
                    extra_ampersand_padding = 12
            else:
                extra_ampersand_padding = 0
            
            # Extra padding for longer texts without "&" (like "Freies Gelände", "Menschliche Infrastruktur")
            # Increased padding for texts longer than 10 characters to prevent truncation
            if not has_ampersand and text_length > 10:
                extra_length_padding = (text_length - 10) * 1.0  # Increased from 0.8 to 1.0 for better spacing
            else:
                extra_length_padding = 0
            
            if text_width_pt < 25:
                padding = 14 + 8 + extra_ampersand_padding + extra_length_padding
            elif text_width_pt < 40:
                padding = 12 + 8 + extra_ampersand_padding + extra_length_padding
            elif text_width_pt < 60:
                padding = 10 + 8 + extra_ampersand_padding + extra_length_padding
            else:
                padding = 8 + 8 + extra_ampersand_padding + extra_length_padding
            
            # Calculate final tab width
            tab_width_actual = text_width_pt + padding
            # Ensure minimum width
            tab_width_actual = max(tab_width_base, tab_width_actual)
            
            # Check if tab fits in current row, wrap if needed BEFORE drawing
            available_width = max_width - (row_start_x - start_x)
            if tab_width_actual > available_width and row_start_x > start_x:
                # Wrap to next row BEFORE calculating tab_rect
                row_y += tab_height + row_spacing
                row_start_x = start_x
                # Recalculate available width for new row
                available_width = max_width
            
            # DO NOT limit tab width - allow tabs to be as wide as needed
            # This ensures longer texts like "Freies Gelände" are never truncated
            # The wrapping logic above handles overflow by moving to next row
            
            tab_rect = fitz.Rect(
                row_start_x,
                row_y,
                row_start_x + tab_width_actual,
                row_y + tab_height
            )
            
            # Determine color (active tab is darker)
            bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
            
            # Draw rounded rectangle with shadow (no border)
            self.draw_rounded_rect(page, tab_rect, bg_color, border_color=None, radius=4.0, shadow=True)
            
            # Add link if target_page is available
            if tab_data.get("target_page") is not None:
                try:
                    link = {
                        "kind": fitz.LINK_GOTO,
                        "from": tab_rect,
                        "page": tab_data["target_page"] - 1,  # 0-based
                        "to": fitz.Point(0, 0),
                        "zoom": 0.0
                    }
                    page.insert_link(link)
                except:
                    pass
            
            # Add text - calculate text width and center manually (like old code)
            # Use the SAME text width calculation as for tab width to ensure consistency
            font_size = 9
            text_width = None
            
            # Use the same method as tab width calculation
            try:
                text_width = fitz.get_text_length(tab_name_upper, fontname='helv-Bold', fontsize=font_size)
            except:
                pass
            
            if text_width is None:
                try:
                    text_width = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                except:
                    pass
            
            # If still None, use the same character-based estimation
            if text_width is None:
                char_widths = {
                    '&': 0.80, 'W': 0.90, 'M': 0.90, 'w': 0.75, 'm': 0.75,
                    'Q': 0.85, 'D': 0.80, 'O': 0.80, 'G': 0.80,
                    'A': 0.75, 'V': 0.70, 'Y': 0.70,
                    'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                    'j': 0.25, 'I': 0.25,
                    ' ': 0.30,
                    'ö': 0.65, 'ä': 0.65, 'ü': 0.65, 'ß': 0.60,
                    'Ö': 0.80, 'Ä': 0.80, 'Ü': 0.80,
                    'h': 0.60, 'n': 0.55, 'u': 0.55, 'o': 0.60, 'a': 0.55,
                    'e': 0.55, 's': 0.50, 'c': 0.50, 'd': 0.60, 'g': 0.60,
                    'b': 0.60, 'p': 0.60, 'q': 0.60, 'k': 0.55, 'v': 0.55,
                    'x': 0.55, 'y': 0.55, 'z': 0.50
                }
                estimated_width = 0
                for char in tab_name_upper:
                    char_lower = char.lower()
                    char_upper = char.upper()
                    char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.60)))
                    estimated_width += char_width * font_size
                text_width = estimated_width
            
            # Calculate center position: tab center minus half text width
            tab_center_x = row_start_x + tab_width_actual / 2
            text_x = tab_center_x - (text_width / 2)  # Start position for centered text
            
            # Vertical center with baseline offset
            text_y = row_y + tab_height / 2 + (font_size * 0.35)
            
            # Insert text WITHOUT align=1 (text starts at position, we calculated center manually)
            try:
                page.insert_text(
                    (text_x, text_y),
                    tab_name_upper,
                    fontsize=font_size,
                    fontname='helv-Bold',
                    color=(0.0, 0.0, 0.0)
                )
            except Exception as e1:
                # Fallback 1: Try with helv (recalculate text_width)
                try:
                    text_width_helv = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                    if text_width_helv:
                        text_width = text_width_helv
                    text_x = tab_center_x - (text_width / 2)
                    page.insert_text(
                        (text_x, text_y),
                        tab_name_upper,
                        fontsize=font_size,
                        fontname='helv',
                        color=(0.0, 0.0, 0.0)
                    )
                except Exception as e2:
                    # Fallback 2: Use character-based estimation (same as tab width calculation)
                    try:
                        char_widths = {
                            '&': 0.80, 'W': 0.90, 'M': 0.90, 'w': 0.75, 'm': 0.75,
                            'Q': 0.85, 'D': 0.80, 'O': 0.80, 'G': 0.80,
                            'A': 0.75, 'V': 0.70, 'Y': 0.70,
                            'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                            'j': 0.25, 'I': 0.25, ' ': 0.30,
                            'ö': 0.65, 'ä': 0.65, 'ü': 0.65, 'ß': 0.60,
                            'Ö': 0.80, 'Ä': 0.80, 'Ü': 0.80,
                            'h': 0.60, 'n': 0.55, 'u': 0.55, 'o': 0.60, 'a': 0.55,
                            'e': 0.55, 's': 0.50, 'c': 0.50, 'd': 0.60, 'g': 0.60,
                            'b': 0.60, 'p': 0.60, 'q': 0.60, 'k': 0.55, 'v': 0.55,
                            'x': 0.55, 'y': 0.55, 'z': 0.50
                        }
                        estimated_width = 0
                        for char in tab_name_upper:
                            char_lower = char.lower()
                            char_upper = char.upper()
                            char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.60)))
                            estimated_width += char_width * font_size
                        text_width = estimated_width
                        text_x = tab_center_x - (text_width / 2)
                        page.insert_text(
                            (text_x, text_y),
                            tab_name_upper,
                            fontsize=font_size,
                            color=(0.0, 0.0, 0.0)
                        )
                    except:
                        pass
            
            row_start_x += tab_width_actual + tab_spacing
        
        # Draw second row (sub-subsections)
        if second_row_tabs:
            row_y = row_y + tab_height + row_spacing
            row_start_x = start_x
            
            for tab_data in second_row_tabs:
                tab_name_upper = tab_data["name"]
                is_active = tab_data["is_active"]
                
                # Calculate tab width dynamically based on actual text width
                font_size = 8
                text_width_pt = None
                
                # Try multiple methods to get accurate text width
                # Method 1: Use fitz.get_text_length (most accurate) - try Bold first
                try:
                    text_width_pt = fitz.get_text_length(tab_name_upper, fontname='helv-Bold', fontsize=font_size)
                except:
                    pass
                
                # Method 2: Try with regular helv font if Bold fails
                if text_width_pt is None:
                    try:
                        text_width_pt = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                    except:
                        pass
                
                # Method 3: Improved character-based estimation (more accurate for special cases)
                if text_width_pt is None:
                    # More accurate character width mapping for helv
                    # Based on actual font metrics - these are multipliers for font_size
                    char_widths = {
                        # Wide characters (need more space)
                        '&': 0.75, 'W': 0.85, 'M': 0.85, 'w': 0.70, 'm': 0.70,
                        'Q': 0.80, 'D': 0.75, 'O': 0.75, 'G': 0.75,
                        'A': 0.70, 'V': 0.65, 'Y': 0.65,
                        # Narrow characters (need less space)
                        'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                        'j': 0.25, 'I': 0.25,
                        # Space
                        ' ': 0.30,
                        # Special characters (Umlaute and special chars)
                        'ö': 0.60, 'ä': 0.60, 'ü': 0.60, 'ß': 0.55,
                        'Ö': 0.75, 'Ä': 0.75, 'Ü': 0.75,
                        # Other common characters
                        'h': 0.55, 'n': 0.50, 'u': 0.50, 'o': 0.55, 'a': 0.50,
                        'e': 0.50, 's': 0.45, 'c': 0.45, 'd': 0.55, 'g': 0.55,
                        'b': 0.55, 'p': 0.55, 'q': 0.55, 'k': 0.50, 'v': 0.50,
                        'x': 0.50, 'y': 0.50, 'z': 0.45
                    }
                    estimated_width = 0
                    for char in tab_name_upper:
                        # Use uppercase for lookup, but keep original case for width
                        char_lower = char.lower()
                        char_upper = char.upper()
                        # Check both cases
                        char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.55)))
                        estimated_width += char_width * font_size
                    text_width_pt = estimated_width
                
                # Dynamic padding based on text length + 4px extra on each side (8px total)
                # Use the same improved logic as first row for consistency
                has_ampersand = '&' in tab_name_upper
                text_length = len(tab_name_upper)
                
                # Extra padding for "&" characters - they need significantly more breathing room
                if has_ampersand:
                    if text_width_pt > 40:  # Long texts with "&"
                        extra_ampersand_padding = 12
                    else:
                        extra_ampersand_padding = 8
                else:
                    extra_ampersand_padding = 0
                
                # Extra padding for longer texts without "&" (like "Private Domänen")
                if not has_ampersand and text_length > 10:
                    extra_length_padding = (text_length - 10) * 0.7  # Add padding for longer texts
                else:
                    extra_length_padding = 0
                
                if text_width_pt < 20:
                    padding = 12 + 8 + extra_ampersand_padding + extra_length_padding
                elif text_width_pt < 35:
                    padding = 10 + 8 + extra_ampersand_padding + extra_length_padding
                elif text_width_pt < 50:
                    padding = 8 + 8 + extra_ampersand_padding + extra_length_padding
                else:
                    padding = 6 + 8 + extra_ampersand_padding + extra_length_padding
                
                # Calculate final tab width
                tab_width_actual = text_width_pt + padding
                # Ensure minimum width (but allow longer texts to be wider)
                min_width = tab_width_base * 0.7
                tab_width_actual = max(min_width, tab_width_actual)
                
                # Check if tab fits in current row, wrap if needed BEFORE drawing
                available_width = max_width - (row_start_x - start_x)
                if tab_width_actual > available_width and row_start_x > start_x:
                    # Wrap to next row BEFORE calculating tab_rect
                    row_y += tab_height * 0.85 + row_spacing
                    row_start_x = start_x
                
                tab_rect = fitz.Rect(
                    row_start_x,
                    row_y,
                    row_start_x + tab_width_actual,
                    row_y + tab_height * 0.85  # Smaller height
                )
                
                # Determine color (active tab is darker)
                bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
                
                # Draw rounded rectangle with shadow (no border)
                self.draw_rounded_rect(page, tab_rect, bg_color, border_color=None, radius=3.5, shadow=True)
                
                # Add link if target_page is available
                if tab_data.get("target_page") is not None:
                    try:
                        link = {
                            "kind": fitz.LINK_GOTO,
                            "from": tab_rect,
                            "page": tab_data["target_page"] - 1,  # 0-based
                            "to": fitz.Point(0, 0),
                            "zoom": 0.0
                        }
                        page.insert_link(link)
                    except:
                        pass
                
                # Add text - calculate text width and center manually (like old code)
                # Use the SAME text width calculation as for tab width to ensure consistency
                font_size = 8
                text_width = None
                
                # Use the same method as tab width calculation
                try:
                    text_width = fitz.get_text_length(tab_name_upper, fontname='helv-Bold', fontsize=font_size)
                except:
                    pass
                
                if text_width is None:
                    try:
                        text_width = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                    except:
                        pass
                
                # If still None, use the same character-based estimation
                if text_width is None:
                    char_widths = {
                        '&': 0.75, 'W': 0.85, 'M': 0.85, 'w': 0.70, 'm': 0.70,
                        'Q': 0.80, 'D': 0.75, 'O': 0.75, 'G': 0.75,
                        'A': 0.70, 'V': 0.65, 'Y': 0.65,
                        'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                        'j': 0.25, 'I': 0.25,
                        ' ': 0.30,
                        'ö': 0.60, 'ä': 0.60, 'ü': 0.60, 'ß': 0.55,
                        'Ö': 0.75, 'Ä': 0.75, 'Ü': 0.75,
                        'h': 0.55, 'n': 0.50, 'u': 0.50, 'o': 0.55, 'a': 0.50,
                        'e': 0.50, 's': 0.45, 'c': 0.45, 'd': 0.55, 'g': 0.55,
                        'b': 0.55, 'p': 0.55, 'q': 0.55, 'k': 0.50, 'v': 0.50,
                        'x': 0.50, 'y': 0.50, 'z': 0.45
                    }
                    estimated_width = 0
                    for char in tab_name_upper:
                        char_lower = char.lower()
                        char_upper = char.upper()
                        char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.55)))
                        estimated_width += char_width * font_size
                    text_width = estimated_width
                
                # Calculate center position: tab center minus half text width
                tab_center_x = row_start_x + tab_width_actual / 2
                text_x = tab_center_x - (text_width / 2)  # Start position for centered text
                
                # Vertical center with baseline offset
                text_y = row_y + (tab_height * 0.85) / 2 + (font_size * 0.35)
                
                # Insert text WITHOUT align=1 (text starts at position, we calculated center manually)
                try:
                    page.insert_text(
                        (text_x, text_y),
                        tab_name_upper,
                        fontsize=font_size,
                        fontname='helv',
                        color=(0.0, 0.0, 0.0)
                    )
                except Exception as e1:
                    # Fallback 1: Use character-based estimation (same as tab width calculation)
                    try:
                        char_widths = {
                            '&': 0.75, 'W': 0.85, 'M': 0.85, 'w': 0.70, 'm': 0.70,
                            'Q': 0.80, 'D': 0.75, 'O': 0.75, 'G': 0.75,
                            'A': 0.70, 'V': 0.65, 'Y': 0.65,
                            'i': 0.20, 'l': 0.20, 't': 0.30, 'f': 0.30, 'r': 0.30,
                            'j': 0.25, 'I': 0.25, ' ': 0.30,
                            'ö': 0.60, 'ä': 0.60, 'ü': 0.60, 'ß': 0.55,
                            'Ö': 0.75, 'Ä': 0.75, 'Ü': 0.75,
                            'h': 0.55, 'n': 0.50, 'u': 0.50, 'o': 0.55, 'a': 0.50,
                            'e': 0.50, 's': 0.45, 'c': 0.45, 'd': 0.55, 'g': 0.55,
                            'b': 0.55, 'p': 0.55, 'q': 0.55, 'k': 0.50, 'v': 0.50,
                            'x': 0.50, 'y': 0.50, 'z': 0.45
                        }
                        estimated_width = 0
                        for char in tab_name_upper:
                            char_lower = char.lower()
                            char_upper = char.upper()
                            char_width = char_widths.get(char, char_widths.get(char_lower, char_widths.get(char_upper, 0.55)))
                            estimated_width += char_width * font_size
                        text_width = estimated_width
                        text_x = tab_center_x - (text_width / 2)
                        page.insert_text(
                            (text_x, text_y),
                            tab_name_upper,
                            fontsize=font_size,
                            color=(0.0, 0.0, 0.0)
                        )
                    except:
                        pass
                
                row_start_x += tab_width_actual + tab_spacing
    
    def add_cover_page(self, page: fitz.Page, cover_config: Dict, page_width: float, page_height: float):
        """Adds a cover page with background image and centered text"""
        # Load background image if specified
        bg_image_path = cover_config.get("background_image")
        if bg_image_path and os.path.exists(bg_image_path):
            try:
                # Insert image as background (full page)
                img_rect = fitz.Rect(0, 0, page_width, page_height)
                page.insert_image(img_rect, filename=bg_image_path)
            except Exception as e:
                print(f"Warning: Could not load background image {bg_image_path}: {e}")
        
        # Get text configuration
        title = cover_config.get("title", "")
        subtitle = cover_config.get("subtitle", "")
        description = cover_config.get("description", "")
        
        # Get font sizes from config or use defaults
        font_config = cover_config.get("default_font", {})
        title_size = font_config.get("title_size", 48)
        subtitle_size = font_config.get("subtitle_size", 24)
        description_size = font_config.get("description_size", 14)
        
        # Get text position offsets
        pos_config = cover_config.get("text_position", {})
        title_y_offset = pos_config.get("title_y_offset", -100)
        subtitle_y_offset = pos_config.get("subtitle_y_offset", -50)
        description_y_offset = pos_config.get("description_y_offset", 50)
        
        # Calculate center position
        center_x = page_width / 2
        center_y = page_height / 2
        
        # Draw title (centered, bold, large)
        if title:
            title_y = center_y + title_y_offset
            try:
                # Try bold font first
                page.insert_text(
                    (center_x, title_y),
                    title,
                    fontsize=title_size,
                    fontname='helv-Bold',
                    color=(0.0, 0.0, 0.0),
                    align=1  # Center alignment
                )
            except:
                # Fallback to regular font
                try:
                    page.insert_text(
                        (center_x, title_y),
                        title,
                        fontsize=title_size,
                        color=(0.0, 0.0, 0.0),
                        align=1
                    )
                except:
                    pass
        
        # Draw subtitle (centered, medium size)
        if subtitle:
            subtitle_y = center_y + subtitle_y_offset
            try:
                text_width = fitz.get_text_length(subtitle, fontname='helv', fontsize=subtitle_size)
            except:
                text_width = len(subtitle) * subtitle_size * 0.6
            
            subtitle_x = center_x - (text_width / 2)
            try:
                page.insert_text(
                    (subtitle_x, subtitle_y),
                    subtitle,
                    fontsize=subtitle_size,
                    fontname='helv',
                    color=(0.3, 0.3, 0.3)
                )
            except:
                try:
                    page.insert_text(
                        (subtitle_x, subtitle_y),
                        subtitle,
                        fontsize=subtitle_size,
                        color=(0.3, 0.3, 0.3)
                    )
                except:
                    pass
        
        # Draw description (centered, smaller, wrapped if needed)
        if description:
            desc_y = center_y + description_y_offset
            # Use textbox for better text wrapping and centering
            desc_rect = fitz.Rect(
                center_x - 200,  # Left margin
                desc_y - 50,     # Top margin
                center_x + 200,  # Right margin
                desc_y + 100     # Bottom margin
            )
            try:
                rc = page.insert_textbox(
                    desc_rect,
                    description,
                    fontsize=description_size,
                    fontname='helv',
                    color=(0.2, 0.2, 0.2),
                    align=1  # Center alignment
                )
                if rc < 0:
                    # Fallback to simple text insertion
                    try:
                        text_width = fitz.get_text_length(description, fontname='helv', fontsize=description_size)
                    except:
                        text_width = len(description) * description_size * 0.5
                    desc_x = center_x - (text_width / 2)
                    page.insert_text(
                        (desc_x, desc_y),
                        description,
                        fontsize=description_size,
                        fontname='helv',
                        color=(0.2, 0.2, 0.2)
                    )
            except:
                try:
                    text_width = fitz.get_text_length(description, fontname='helv', fontsize=description_size)
                except:
                    text_width = len(description) * description_size * 0.5
                desc_x = center_x - (text_width / 2)
                try:
                    page.insert_text(
                        (desc_x, desc_y),
                        description,
                        fontsize=description_size,
                        color=(0.2, 0.2, 0.2)
                    )
                except:
                    pass
    
    def apply_layout_to_pdf(self, doc: fitz.Document, tabs: List[Dict], tab_text_elements: List[Dict] = None, page_structure: Dict = None, tab_subsections: Dict = None, metadata: Dict = None, cover_pages_config: Dict = None):
        """Applies layout (blood splatters and tabs) to all pages of a PDF"""
        total_pages = len(doc)
        
        # Add cover pages BEFORE blood splatters and tabs
        if cover_pages_config:
            print("Adding cover pages...")
            cover_pages = cover_pages_config.get("cover_pages", {})
            default_bg = cover_pages_config.get("default_background", "")
            default_font = cover_pages_config.get("default_font", {})
            text_position = cover_pages_config.get("text_position", {})
            
            # Find first page of each tab and add cover page
            for tab in tabs:
                tab_name = tab.get("name")
                target_page_num = tab.get("target_page", 1) - 1  # Convert to 0-based
                
                if tab_name in cover_pages and 0 <= target_page_num < total_pages:
                    cover_config = cover_pages[tab_name].copy()
                    # Merge with defaults
                    if default_bg and "background_image" not in cover_config:
                        cover_config["background_image"] = default_bg
                    if default_font:
                        cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                    if text_position:
                        cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                    
                    cover_page = doc[target_page_num]
                    self.add_cover_page(cover_page, cover_config, self.page_width, self.page_height)
        
        print("Drawing blood splatters in background...")
        # Draw blood splatters on all pages (BEFORE tabs are drawn)
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.draw_blood_splatters(target_page)
        
        print("Drawing modern tab tabs...")
        # Draw modern tabs on all pages
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.add_tabs_to_page(target_page, page_num + 1, tabs, tab_text_elements, page_structure)
        
        # Draw upper tabs (left top) if we have the structure
        if page_structure and tab_subsections and metadata:
            print("Drawing upper tabs (left top)...")
            for page_num in range(total_pages):
                target_page = doc[page_num]
                self.add_upper_tabs_to_page(target_page, page_num + 1, page_structure, tab_subsections, metadata)
