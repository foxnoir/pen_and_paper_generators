#!/usr/bin/env python3
"""
Layout Generator for Vampire Journal PDF
Handles all visual design elements: tabs, blood splatters, rounded rectangles, etc.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Optional
import random
import math


class LayoutGenerator:
    """Generates layout elements (tabs, blood splatters, etc.) for PDF pages"""
    
    def __init__(self, page_width: float = 595.2755737304688, page_height: float = 841.8897705078125):
        self.page_width = page_width
        self.page_height = page_height
        
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
        
        # Add text - use tab name from JSON (not from original_text!)
        # original_text is only used for font styling
        tab_name = tab.get("name", "")
        if tab_name:
            # Calculate position for text - significantly shifted to left
            # Shift text 8-10pt to left (negative value = to left)
            text_offset_left = -9.0
            
            # Get font styling from original_text if available, otherwise use defaults
            fontsize = 8
            fontname = 'helv-Bold'
            if original_text:
                fontsize = original_text.get('fontsize', 8)
                fontname = original_text.get('fontname', 'helv-Bold')
            
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
                # Use tab name from JSON, not original_text!
                rc = page.insert_textbox(
                    text_rect,
                    tab_name,  # Use name from JSON!
                    fontsize=fontsize,
                    fontname=fontname,
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
                        tab_name,  # Use name from JSON!
                        fontsize=fontsize,
                        fontname=fontname,
                        color=(0.0, 0.0, 0.0)
                    )
            except Exception as e:
                # Last fallback: Simple text, shifted to left
                try:
                    center_x = tab_rect.x0 + self.tab_width / 2 + text_offset_left
                    center_y = tab_rect.y0 + tab["height"] / 2
                    page.insert_text(
                        (center_x, center_y),
                        tab_name[:15] if len(tab_name) > 15 else tab_name,  # Use name from JSON!
                        fontsize=fontsize,
                        fontname=fontname,
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
    
    def add_tabs_to_page(self, page: fitz.Page, page_num: int, tabs: List[Dict], tab_text_elements: List[Dict] = None):
        """Adds modern tab tabs to a page"""
        # Determine which page is active (based on tab targets)
        active_tab = None
        for tab in tabs:
            if tab["target_page"] == page_num:
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
        
        subsections = tab_info.get("subsections", [])
        if not subsections:
            return
        
        # Get position from metadata
        upper_tabs_pos = metadata.get("upper_tabs_position", {"x": 10.0, "y": 20.0})
        start_x = upper_tabs_pos.get("x", 10.0)
        start_y = upper_tabs_pos.get("y", 20.0)
        
        # Tab dimensions - SMALLER!
        tab_height = 18.0  # Reduced from 25.0
        tab_width_base = 60.0  # Reduced from 80.0
        tab_spacing = 4.0  # Reduced from 5.0
        row_spacing = 6.0  # Reduced from 8.0
        
        # Maximum width to avoid overlapping with right tabs
        max_width = self.tab_x - 20  # Leave 20pt margin before right tabs
        
        current_x = start_x
        current_y = start_y
        
        # First row: subsections_left_top_tabs
        first_row_tabs = []
        second_row_tabs = []
        
        for subsection in subsections:
            subsection_name_curr = subsection.get("name", "")
            sub_subsections = subsection.get("seconnd_subsections_left_tabs", [])
            if not sub_subsections:
                sub_subsections = subsection.get("sub_subsections", [])
            
            # Add subsection to first row
            first_row_tabs.append({
                "name": subsection_name_curr,
                "is_active": (subsection_name_curr == subsection_name),
                "target_page": None  # Will be calculated
            })
            
            # Add sub-subsections to second row
            for sub_subsection in sub_subsections:
                second_row_tabs.append({
                    "name": sub_subsection,
                    "is_active": (sub_subsection == sub_subsection_name),
                    "target_page": None  # Will be calculated
                })
        
        # Draw first row
        row_y = current_y
        row_start_x = start_x
        
        for tab_data in first_row_tabs:
            tab_name_upper = tab_data["name"]
            is_active = tab_data["is_active"]
            
            # Calculate tab width based on text length (smaller font = smaller width)
            text_width = len(tab_name_upper) * 4.0  # Reduced from 5.5
            tab_width_actual = max(tab_width_base, text_width + 8)  # Reduced padding
            tab_width_actual = min(tab_width_actual, max_width - (row_start_x - start_x))  # Don't exceed max width
            
            # Check if we need to wrap to next row
            if row_start_x + tab_width_actual > max_width and row_start_x > start_x:
                row_y += tab_height + row_spacing
                row_start_x = start_x
            
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
            
            # Add text - calculate text width and center manually (like old code)
            # Calculate text width to properly center it
            font_size = 9
            try:
                # Get text width using font metrics
                text_width = fitz.get_text_length(tab_name_upper, fontname='helv-Bold', fontsize=font_size)
            except:
                # Fallback: estimate text width (rough approximation)
                text_width = len(tab_name_upper) * (font_size * 0.6)
            
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
                # Fallback 1: Try with helv
                try:
                    text_width = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                    text_x = tab_center_x - (text_width / 2)
                    page.insert_text(
                        (text_x, text_y),
                        tab_name_upper,
                        fontsize=font_size,
                        fontname='helv',
                        color=(0.0, 0.0, 0.0)
                    )
                except Exception as e2:
                    # Fallback 2: Use estimated width
                    try:
                        text_width = len(tab_name_upper) * (font_size * 0.6)
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
                
                # Calculate tab width based on text length (even smaller)
                text_width = len(tab_name_upper) * 3.5
                tab_width_actual = max(tab_width_base * 0.7, text_width + 6)  # Smaller
                tab_width_actual = min(tab_width_actual, max_width - (row_start_x - start_x))
                
                # Check if we need to wrap to next row
                if row_start_x + tab_width_actual > max_width and row_start_x > start_x:
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
                
                # Add text - calculate text width and center manually (like old code)
                # Calculate text width to properly center it
                font_size = 8
                try:
                    # Get text width using font metrics
                    text_width = fitz.get_text_length(tab_name_upper, fontname='helv', fontsize=font_size)
                except:
                    # Fallback: estimate text width (rough approximation)
                    text_width = len(tab_name_upper) * (font_size * 0.6)
                
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
                    # Fallback 1: Use estimated width
                    try:
                        text_width = len(tab_name_upper) * (font_size * 0.6)
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
    
    def apply_layout_to_pdf(self, doc: fitz.Document, tabs: List[Dict], tab_text_elements: List[Dict] = None, page_structure: Dict = None, tab_subsections: Dict = None, metadata: Dict = None):
        """Applies layout (blood splatters and tabs) to all pages of a PDF"""
        total_pages = len(doc)
        
        print("Drawing blood splatters in background...")
        # Draw blood splatters on all pages (BEFORE tabs are drawn)
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.draw_blood_splatters(target_page)
        
        print("Drawing modern tab tabs...")
        # Draw modern tabs on all pages
        for page_num in range(total_pages):
            target_page = doc[page_num]
            self.add_tabs_to_page(target_page, page_num + 1, tabs, tab_text_elements)
        
        # Draw upper tabs (left top) if we have the structure
        if page_structure and tab_subsections and metadata:
            print("Drawing upper tabs (left top)...")
            for page_num in range(total_pages):
                target_page = doc[page_num]
                self.add_upper_tabs_to_page(target_page, page_num + 1, page_structure, tab_subsections, metadata)
