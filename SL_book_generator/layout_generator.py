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
import glob
import tempfile
import unicodedata
from PIL import Image


class LayoutGenerator:
    """Generates layout elements (tabs, blood splatters, etc.) for PDF pages"""
    
    def __init__(self, page_width: float = 595.2755737304688, page_height: float = 841.8897705078125):
        self.page_width = page_width
        self.page_height = page_height
        
        # Tab width and position
        self.tab_width = 35.0  # Wider for better design and text
        self.tab_x = self.page_width - self.tab_width - 5  # Right margin with 5pt spacing
        
        # Image compression settings
        self.image_quality = 85  # JPEG quality (1-100, lower = smaller file)
        
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
    
    def _compress_image(self, image_path: str, preserve_transparency: bool = False) -> str:
        """
        Compress image to reduce file size.
        If preserve_transparency is True, keeps PNG format with transparency.
        Otherwise converts to JPEG for smaller file size.
        Returns path to compressed image (temporary file or original if compression fails).
        """
        try:
            # Normalize Unicode path to handle NFC/NFD differences
            if not os.path.exists(image_path):
                normalized_nfc = unicodedata.normalize('NFC', image_path)
                normalized_nfd = unicodedata.normalize('NFD', image_path)
                if os.path.exists(normalized_nfc):
                    image_path = normalized_nfc
                elif os.path.exists(normalized_nfd):
                    image_path = normalized_nfd
            
            # Open image
            img = Image.open(image_path)
            original_mode = img.mode
            has_transparency = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
            
            # If we need to preserve transparency, keep PNG format
            if preserve_transparency or has_transparency:
                # Resize if image is very large (reduce to max 2000px on longest side)
                max_dimension = 2000
                if max(img.size) > max_dimension:
                    ratio = max_dimension / max(img.size)
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save as compressed PNG to temporary file (preserves transparency)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                img.save(temp_file.name, 'PNG', optimize=True, compress_level=6)
                temp_file.close()
                
                return temp_file.name
            else:
                # Convert RGBA to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is very large (reduce to max 2000px on longest side)
                max_dimension = 2000
                if max(img.size) > max_dimension:
                    ratio = max_dimension / max(img.size)
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save as compressed JPEG to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                img.save(temp_file.name, 'JPEG', quality=self.image_quality, optimize=True)
                temp_file.close()
                
                return temp_file.name
        except Exception as e:
            print(f"  Warning: Could not compress image {image_path}: {e}")
            # Return original path if compression fails
            return image_path
    
    def draw_blood_splatters(self, page: fitz.Page):
        """Draws random blood stain clusters in the background with custom colors"""
        # Light stains (#49231E = RGB 73/255, 35/255, 30/255) - darker red/brown
        light_color = (73 / 255, 35 / 255, 30 / 255)
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
    
    def draw_rounded_rect(self, page: fitz.Page, rect: fitz.Rect, fill_color: tuple, border_color: tuple = None, radius: float = 8.0, shadow: bool = False, opacity: float = 1.0):
        """Draws a rounded rectangle with given radius and optional opacity"""
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
                self._draw_rounded_rect_shape(page, shadow_rect, self.tab_colors["shadow"], None, radius, opacity)
            
            # Draw main rectangle
            self._draw_rounded_rect_shape(page, rect, fill_color, border_color, radius, opacity)
        
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
                page.draw_rect(shadow_rect, color=self.tab_colors["shadow"], width=0, fill=self.tab_colors["shadow"], fill_opacity=opacity)
            page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color, fill_opacity=opacity)
    
    def _draw_rounded_rect_shape(self, page: fitz.Page, rect: fitz.Rect, fill_color: tuple, border_color: tuple, radius: float, opacity: float = 1.0):
        """Helper function to draw a rounded rectangle with optional opacity"""
        try:
            x0, y0 = rect.x0, rect.y0
            x1, y1 = rect.x1, rect.y1
            
            # If opacity is less than 1.0, use fallback method with fill_opacity
            # because shape.finish() doesn't support opacity directly
            if opacity < 1.0:
                # Use simple rectangle with opacity (rounded corners won't work, but opacity will)
                page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color, fill_opacity=opacity)
                return
            
            # Use Shape object for complex paths (only when opacity is 1.0)
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
            page.draw_rect(rect, color=border_color if border_color else fill_color, width=0 if not border_color else 1.0, fill=fill_color, fill_opacity=opacity)
    
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
                pg_page_index = pg_info.get("page_index", 1)  # Default to 1 if not set
                
                if pg_subsection and not pg_sub_subsection:
                    # This is a subsection page
                    # Only use the first page (page_index=1) as target, even if there are multiple pages
                    if pg_subsection not in subsection_target_pages or pg_page_index == 1:
                        if pg_page_index == 1:
                            subsection_target_pages[pg_subsection] = pg_num
                        elif pg_subsection not in subsection_target_pages:
                            # Fallback: use first found page if page_index is not set
                            subsection_target_pages[pg_subsection] = pg_num
                elif pg_subsection and pg_sub_subsection:
                    # This is a sub-subsection page
                    # Only use the first page (page_index=1) as target, even if there are multiple pages
                    key = (pg_subsection, pg_sub_subsection)
                    if key not in sub_subsection_target_pages or pg_page_index == 1:
                        if pg_page_index == 1:
                            sub_subsection_target_pages[key] = pg_num
                        elif key not in sub_subsection_target_pages:
                            # Fallback: use first found page if page_index is not set
                            sub_subsection_target_pages[key] = pg_num
        
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
            
            # Draw rounded rectangle with shadow (no border) - 70% opacity for upper tabs
            self.draw_rounded_rect(page, tab_rect, bg_color, border_color=None, radius=4.0, shadow=True, opacity=0.7)
            
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
                
                # Draw rounded rectangle with shadow (no border) - 70% opacity for upper tabs
                self.draw_rounded_rect(page, tab_rect, bg_color, border_color=None, radius=3.5, shadow=True, opacity=0.7)
                
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
    
    def _get_lilith_font_path(self):
        """Returns the absolute path to the Lilith Plain font file"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Try different Lilith font variants (prefer Plain, then Regular)
        font_paths = [
            os.path.join(script_dir, "assets", "fonts", "Lilith", "Lilith Plain", "Lilith Plain.ttf"),
            os.path.join(script_dir, "assets", "fonts", "Lilith", "Lilith Regular", "Lilith Regular.ttf"),
            os.path.join(os.getcwd(), "assets", "fonts", "Lilith", "Lilith Plain", "Lilith Plain.ttf"),
            os.path.join(os.getcwd(), "assets", "fonts", "Lilith", "Lilith Regular", "Lilith Regular.ttf"),
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return os.path.abspath(font_path)
        return None
    
    def add_cover_page(self, page: fitz.Page, cover_config: Dict, page_width: float, page_height: float):
        """Adds a cover page with background image, optional center image, and centered text"""
        # Check if this is a full-page image (no background, no text)
        full_page_image = cover_config.get("full_page", False)
        
        if full_page_image:
            # Only insert the image, full page, no background, no text
            image_path = cover_config.get("image")
            if image_path:
                # Resolve path relative to script directory if needed
                if not os.path.isabs(image_path):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    possible_paths = [
                        image_path,  # Try as-is first
                        os.path.join(script_dir, image_path),  # Relative to script
                        os.path.join(os.getcwd(), image_path)  # Relative to cwd
                    ]
                    image_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            image_path = path
                            break
                        # Try Unicode normalization (macOS uses NFD, JSON often uses NFC)
                        normalized_nfc = unicodedata.normalize('NFC', path)
                        normalized_nfd = unicodedata.normalize('NFD', path)
                        if normalized_nfc != path and os.path.exists(normalized_nfc):
                            image_path = normalized_nfc
                            break
                        if normalized_nfd != path and os.path.exists(normalized_nfd):
                            image_path = normalized_nfd
                            break
                
                if image_path and os.path.exists(image_path):
                    try:
                        # Clear page first to ensure no other content interferes
                        # Create a white rectangle to clear the page
                        white_rect = fitz.Rect(0, 0, page_width, page_height)
                        page.draw_rect(white_rect, color=(1, 1, 1), width=0, fill=(1, 1, 1))
                        
                        # Insert image as full page - use keep_proportion=False to fill entire page without white borders
                        # Compress image before insertion to reduce file size (preserve transparency for full-page images)
                        compressed_path = self._compress_image(image_path, preserve_transparency=True)
                        img_rect = fitz.Rect(0, 0, page_width, page_height)
                        page.insert_image(img_rect, filename=compressed_path, keep_proportion=False)
                        # Clean up temporary file if it was created
                        if compressed_path != image_path and os.path.exists(compressed_path):
                            try:
                                os.unlink(compressed_path)
                            except:
                                pass
                        print(f"  ✓ Successfully inserted full-page image: {image_path} (size: {page_width}x{page_height})")
                        return  # Don't add text or background
                    except Exception as e:
                        print(f"  ✗ Warning: Could not load full-page image {image_path}: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"  ✗ Warning: Full-page image not found: {cover_config.get('image')}")
            return
        
        # Load background image if specified
        bg_image_path = cover_config.get("background_image")
        
        # Handle "random" background_image - use random background from assets/images/background/
        if bg_image_path == "random":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            
            # Find all background images (excluding rules subdirectory and basic.png)
            background_images = []
            if os.path.exists(background_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(background_dir, ext))
                    # Filter out subdirectories (like rules/) and basic.png
                    background_images.extend([img for img in all_images 
                                             if os.path.dirname(img) == background_dir 
                                             and 'basic.png' not in img.lower()])
                background_images.sort()
            
            if background_images:
                bg_image_path = random.choice(background_images)
            else:
                # Fallback to basic.png if no other backgrounds found
                bg_image_path = os.path.join(background_dir, "basic.png")
        
        # Handle "random_npc_vampire" background_image - use random background from assets/images/NPCs/vampire/
        if bg_image_path == "random_npc_vampire":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            npc_vampire_dir = os.path.join(script_dir, "assets", "images", "NPCs", "vampire")
            if not os.path.exists(npc_vampire_dir):
                npc_vampire_dir = os.path.join(os.getcwd(), "assets", "images", "NPCs", "vampire")
            
            # Find all NPC vampire images
            npc_vampire_images = []
            if os.path.exists(npc_vampire_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(npc_vampire_dir, ext))
                    npc_vampire_images.extend(all_images)
                npc_vampire_images.sort()
            
            if npc_vampire_images:
                bg_image_path = random.choice(npc_vampire_images)
            else:
                # Fallback to random background if no NPC vampire images found
                script_dir = os.path.dirname(os.path.abspath(__file__))
                background_dir = os.path.join(script_dir, "assets", "images", "background")
                if not os.path.exists(background_dir):
                    background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
                bg_image_path = os.path.join(background_dir, "basic.png")
        
        # Handle "random_rules" background_image - use random background from assets/images/background/rules/
        if bg_image_path == "random_rules":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rules_dir = os.path.join(script_dir, "assets", "images", "background", "rules")
            if not os.path.exists(rules_dir):
                rules_dir = os.path.join(os.getcwd(), "assets", "images", "background", "rules")
            
            # Find all rules background images
            rules_images = []
            if os.path.exists(rules_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(rules_dir, ext))
                    rules_images.extend(all_images)
                rules_images.sort()
            
            if rules_images:
                bg_image_path = random.choice(rules_images)
            else:
                # Fallback to random background if no rules images found
                script_dir = os.path.dirname(os.path.abspath(__file__))
                background_dir = os.path.join(script_dir, "assets", "images", "background")
                if not os.path.exists(background_dir):
                    background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
                bg_image_path = os.path.join(background_dir, "basic.png")
        
        # If basic.png is specified, use random background from assets/images/background/ instead
        # EXCEPT for clan sheets (sub-subsections) which should always use basic.png
        is_clan_sheet = cover_config.get("image") is not None  # Clan sheets have an "image" field
        
        # Check if bg_image_path points to basic.png (any path variant)
        is_basic_png = bg_image_path and "basic.png" in bg_image_path
        
        # For clan sheets, ensure basic.png path points to the correct location
        if is_basic_png and is_clan_sheet:
            # Normalize path: assets/images/basic.png -> assets/images/background/basic.png
            if "background" not in bg_image_path:
                bg_image_path = bg_image_path.replace("images/basic.png", "images/background/basic.png")
                bg_image_path = bg_image_path.replace("assets/images/basic.png", "assets/images/background/basic.png")
        
        if is_basic_png and not is_clan_sheet:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            
            # Find all background images (exclude basic.png itself)
            background_images = []
            if os.path.exists(background_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(background_dir, ext))
                    # Filter out basic.png from random selection
                    background_images.extend([img for img in all_images if 'basic.png' not in img.lower()])
                background_images.sort()
            
            # Use random background if available, otherwise fall back to basic.png
            if background_images:
                bg_image_path = random.choice(background_images)
            # else: keep bg_image_path as basic.png (fallback)
        
        # Resolve path relative to script directory if needed
        if bg_image_path:
            if not os.path.isabs(bg_image_path):
                # Try relative to current working directory first
                script_dir = os.path.dirname(os.path.abspath(__file__))
                possible_paths = [
                    bg_image_path,  # Try as-is first
                    os.path.join(script_dir, bg_image_path),  # Relative to script
                    os.path.join(os.getcwd(), bg_image_path)  # Relative to cwd
                ]
                bg_image_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        bg_image_path = path
                        break
                    # Try Unicode normalization (macOS uses NFD, JSON often uses NFC)
                    normalized_nfc = unicodedata.normalize('NFC', path)
                    normalized_nfd = unicodedata.normalize('NFD', path)
                    if normalized_nfc != path and os.path.exists(normalized_nfc):
                        bg_image_path = normalized_nfc
                        break
                    if normalized_nfd != path and os.path.exists(normalized_nfd):
                        bg_image_path = normalized_nfd
                        break
        
        if bg_image_path:
            # Normalize Unicode path to handle NFC/NFD differences
            normalized_path = unicodedata.normalize('NFC', bg_image_path)
            if not os.path.exists(bg_image_path) and os.path.exists(normalized_path):
                bg_image_path = normalized_path
            elif not os.path.exists(bg_image_path):
                # Try NFD normalization
                normalized_nfd = unicodedata.normalize('NFD', bg_image_path)
                if os.path.exists(normalized_nfd):
                    bg_image_path = normalized_nfd
            
            if os.path.exists(bg_image_path):
                try:
                    # Insert image as background (full page) - use keep_proportion=False to fill entire page
                    # Compress image before insertion to reduce file size
                    compressed_path = self._compress_image(bg_image_path)
                    img_rect = fitz.Rect(0, 0, page_width, page_height)
                    page.insert_image(img_rect, filename=compressed_path, keep_proportion=False)
                    # Clean up temporary file if it was created
                    if compressed_path != bg_image_path and os.path.exists(compressed_path):
                        try:
                            os.unlink(compressed_path)
                        except:
                            pass
                except Exception as e:
                    print(f"Warning: Could not load background image {bg_image_path}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"Warning: Background image path not found: {bg_image_path}")
                # Try to find the file with different normalizations
                script_dir = os.path.dirname(os.path.abspath(__file__))
                possible_base_paths = [
                    bg_image_path,
                    os.path.join(script_dir, bg_image_path),
                    os.path.join(os.getcwd(), bg_image_path)
                ]
                for base_path in possible_base_paths:
                    for norm in ['NFC', 'NFD']:
                        normalized = unicodedata.normalize(norm, base_path)
                        if os.path.exists(normalized):
                            print(f"  Found with {norm} normalization: {normalized}")
                            break
        
        # Load optional center image (for subsections/sub-subsections)
        center_image_path = cover_config.get("image")
        # Resolve path relative to script directory if needed
        if center_image_path:
            if not os.path.isabs(center_image_path):
                # Try relative to current working directory first
                script_dir = os.path.dirname(os.path.abspath(__file__))
                possible_paths = [
                    center_image_path,  # Try as-is first
                    os.path.join(script_dir, center_image_path),  # Relative to script
                    os.path.join(os.getcwd(), center_image_path)  # Relative to cwd
                ]
                center_image_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        center_image_path = path
                        break
                    # Try Unicode normalization (macOS uses NFD, JSON often uses NFC)
                    normalized_nfc = unicodedata.normalize('NFC', path)
                    normalized_nfd = unicodedata.normalize('NFD', path)
                    if normalized_nfc != path and os.path.exists(normalized_nfc):
                        center_image_path = normalized_nfc
                        break
                    if normalized_nfd != path and os.path.exists(normalized_nfd):
                        center_image_path = normalized_nfd
                        break
                if not center_image_path:
                    print(f"  ✗ Warning: Center image not found. Tried paths: {possible_paths}")
        
        if center_image_path and os.path.exists(center_image_path):
            try:
                # Calculate content area (within tab boundaries)
                # Right tabs: tab_width = 35pt, tab_x = page_width - 35 - 5 = page_width - 40
                # Content area ends at: tab_x - 15 = page_width - 55
                # Left margin: 30pt (as requested)
                # Top margin: ~80pt to leave space for upper tabs (tabs start at y=20, height=18, spacing, plus buffer)
                # Bottom margin: 30pt
                
                tab_width = 35.0
                tab_x = page_width - tab_width - 5
                content_right = tab_x - 15  # End of content area (before tabs)
                content_left = 52.0  # 52px left margin (30px original + 22px shift right)
                content_top = 80.0  # Space for upper tabs
                content_bottom = 30.0  # 30px bottom margin
                
                # Calculate available content area
                content_width = content_right - content_left
                content_height = page_height - content_top - content_bottom
                
                # Get image dimensions or use defaults
                # If image_width/image_height not specified, try to get actual image size
                img_width = cover_config.get("image_width")
                img_height = cover_config.get("image_height")
                
                if img_width is None or img_height is None:
                    # Try to get actual image dimensions
                    try:
                        from PIL import Image
                        img = Image.open(center_image_path)
                        img_width_actual, img_height_actual = img.size
                        # Scale to fit content area while maintaining aspect ratio
                        scale = min(content_width / img_width_actual, content_height / img_height_actual)
                        img_width = img_width_actual * scale
                        img_height = img_height_actual * scale
                    except:
                        # Fallback to content area size
                        img_width = img_width or content_width
                        img_height = img_height or content_height
                
                # Center the image within content area
                content_center_x = content_left + content_width / 2
                content_center_y = content_top + content_height / 2
                
                img_rect = fitz.Rect(
                    content_center_x - img_width / 2,
                    content_center_y - img_height / 2,
                    content_center_x + img_width / 2,
                    content_center_y + img_height / 2
                )
                # Compress image before insertion to reduce file size (preserve transparency for transparent sheets)
                compressed_path = self._compress_image(center_image_path, preserve_transparency=True)
                page.insert_image(img_rect, filename=compressed_path, keep_proportion=True)
                # Clean up temporary file if it was created
                if compressed_path != center_image_path and os.path.exists(compressed_path):
                    try:
                        os.unlink(compressed_path)
                    except:
                        pass
                print(f"  ✓ Successfully inserted center image: {center_image_path} (size: {img_width}x{img_height}, area: {content_width}x{content_height})")
            except Exception as e:
                print(f"  ✗ Warning: Could not load center image {center_image_path}: {e}")
                import traceback
                traceback.print_exc()
        
        # Get text configuration
        # If background_image is "random", don't show any text (no title, subtitle, description)
        bg_image_path = cover_config.get("background_image")
        is_random_background = bg_image_path == "random"
        
        title = "" if is_random_background else cover_config.get("title", "")
        subtitle = "" if is_random_background else cover_config.get("subtitle", "")
        description = "" if is_random_background else cover_config.get("description", "")
        
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
        
        # Draw title (centered, bold, large) - using Lilith font
        if title:
            title_y = center_y + title_y_offset
            # Get Lilith font path
            lilith_font_path = self._get_lilith_font_path()
            
            if lilith_font_path:
                try:
                    # Use Lilith font with fontfile parameter
                    page.insert_text(
                        (center_x, title_y),
                        title,
                        fontsize=title_size,
                        fontfile=lilith_font_path,
                        color=(0.0, 0.0, 0.0),
                        align=1  # Center alignment
                    )
                except Exception as e:
                    print(f"Warning: Could not use Lilith font, falling back to helv-Bold: {e}")
                    try:
                        # Fallback to bold font
                        page.insert_text(
                            (center_x, title_y),
                            title,
                            fontsize=title_size,
                            fontname='helv-Bold',
                            color=(0.0, 0.0, 0.0),
                            align=1
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
            else:
                # Fallback to helv-Bold if Lilith not available
                try:
                    page.insert_text(
                        (center_x, title_y),
                        title,
                        fontsize=title_size,
                        fontname='helv-Bold',
                        color=(0.0, 0.0, 0.0),
                        align=1
                    )
                except:
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
            
            # Get list of background images for random selection
            script_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            
            background_images = []
            if os.path.exists(background_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    background_images.extend(glob.glob(os.path.join(background_dir, ext)))
                background_images.sort()
            
            # Helper function to get random background or fallback
            def get_random_background():
                if background_images:
                    return random.choice(background_images)
                # Fallback to basic.png or default_bg
                if default_bg and "basic.png" not in default_bg:
                    return default_bg
                return "images/basic.png"
            
            # Helper function to process background_image: if basic.png, use random background
            # EXCEPT for clan sheets (sub-subsections) which should always use basic.png
            def process_background_image(bg_path, is_clan_sheet=False):
                if bg_path and ("basic.png" in bg_path or bg_path == "images/basic.png") and not is_clan_sheet:
                    return get_random_background()
                return bg_path
            
            # Find first page of each tab and add cover page
            for tab in tabs:
                tab_name = tab.get("name")
                target_page_num = tab.get("target_page", 1) - 1  # Convert to 0-based
                
                if tab_name in cover_pages and 0 <= target_page_num < total_pages:
                    tab_cover_config = cover_pages[tab_name]
                    
                    # Check if tab has page_1, page_2, etc. structure (for tabs with multiple pages)
                    if isinstance(tab_cover_config, dict) and any(key.startswith("page_") for key in tab_cover_config.keys()):
                        # Handle multiple pages for this tab (like Handouts, Notizen with page_count > 1)
                        for pg_num, pg_info in page_structure.items():
                            if (pg_info.get("tab_name") == tab_name and 
                                pg_info.get("subsection") is None and
                                pg_info.get("sub_subsection") is None):
                                page_index = pg_info.get("page_index", 1)
                                page_key = f"page_{page_index}"
                                
                                if page_key in tab_cover_config:
                                    page_num = int(pg_num) - 1  # Convert to 0-based
                                    if 0 <= page_num < total_pages:
                                        cover_config = tab_cover_config[page_key].copy()
                                        # Merge with defaults
                                        if default_bg and "background_image" not in cover_config:
                                            cover_config["background_image"] = process_background_image(default_bg)
                                        elif "background_image" in cover_config:
                                            cover_config["background_image"] = process_background_image(cover_config["background_image"])
                                        if default_font:
                                            cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                                        if text_position:
                                            cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                                        
                                        cover_page = doc[page_num]
                                        print(f"  Adding cover for {tab_name} (page {page_index}) on page {page_num + 1}")
                                        self.add_cover_page(cover_page, cover_config, self.page_width, self.page_height)
                    else:
                        # Old structure: single config for first page
                        cover_config = tab_cover_config.copy()
                        # Merge with defaults
                        if default_bg and "background_image" not in cover_config:
                            cover_config["background_image"] = process_background_image(default_bg)
                        elif "background_image" in cover_config:
                            cover_config["background_image"] = process_background_image(cover_config["background_image"])
                        if default_font:
                            cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                        if text_position:
                            cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                        
                        cover_page = doc[target_page_num]
                        self.add_cover_page(cover_page, cover_config, self.page_width, self.page_height)
            
            # Add cover pages for subsections
            subsections_config = cover_pages.get("subsections", {})
            if subsections_config and page_structure:
                print("Adding subsection cover pages...")
                for tab_name, subsections in subsections_config.items():
                    # Find pages for each subsection
                    for subsection_name, subsection_config in subsections.items():
                        # Check if subsection_config has page_1, page_2, etc. structure
                        if isinstance(subsection_config, dict) and any(key.startswith("page_") for key in subsection_config.keys()):
                            # New structure: page_1, page_2, etc.
                            for pg_num, pg_info in page_structure.items():
                                if (pg_info.get("tab_name") == tab_name and 
                                    pg_info.get("subsection") == subsection_name and
                                    not pg_info.get("sub_subsection")):
                                    page_index = pg_info.get("page_index", 1)
                                    page_key = f"page_{page_index}"
                                    
                                    if page_key in subsection_config:
                                        page_num = int(pg_num) - 1  # Convert to 0-based
                                        if 0 <= page_num < total_pages:
                                            cover_config = subsection_config[page_key].copy()
                                            # Merge with defaults
                                            # Ensure image and full_page fields are preserved (for pages like Garou page_1)
                                            if "image" in subsection_config[page_key]:
                                                cover_config["image"] = subsection_config[page_key]["image"]
                                            if "full_page" in subsection_config[page_key]:
                                                cover_config["full_page"] = subsection_config[page_key]["full_page"]
                                            # Preserve no_upper_tabs flag if present, or set it if background is basic_npc.png
                                            bg_image = cover_config.get("background_image", "")
                                            if "no_upper_tabs" in subsection_config[page_key]:
                                                cover_config["no_upper_tabs"] = subsection_config[page_key]["no_upper_tabs"]
                                                pg_info["no_upper_tabs"] = subsection_config[page_key]["no_upper_tabs"]
                                            elif "basic_npc.png" in bg_image:
                                                cover_config["no_upper_tabs"] = True
                                                pg_info["no_upper_tabs"] = True
                                            if default_bg and "background_image" not in cover_config:
                                                cover_config["background_image"] = process_background_image(default_bg)
                                            elif "background_image" in cover_config:
                                                cover_config["background_image"] = process_background_image(cover_config["background_image"])
                                            
                                            # Check if final background_image is basic_npc.png and set no_upper_tabs
                                            final_bg = cover_config.get("background_image", "")
                                            if "basic_npc.png" in final_bg:
                                                cover_config["no_upper_tabs"] = True
                                                pg_info["no_upper_tabs"] = True
                                            
                                            if default_font:
                                                cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                                            if text_position:
                                                cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                                            
                                            subsection_page = doc[page_num]
                                            print(f"  Adding cover for {tab_name} -> {subsection_name} (page {page_index}) on page {page_num + 1}")
                                            self.add_cover_page(subsection_page, cover_config, self.page_width, self.page_height)
                        else:
                            # Old structure: single config for first page
                            for pg_num, pg_info in page_structure.items():
                                if (pg_info.get("tab_name") == tab_name and 
                                    pg_info.get("subsection") == subsection_name and
                                    not pg_info.get("sub_subsection") and
                                    pg_info.get("page_index", 1) == 1):
                                    # This is the first page of this subsection
                                    page_num = int(pg_num) - 1  # Convert to 0-based
                                    if 0 <= page_num < total_pages:
                                        cover_config = subsection_config.copy()
                                        # Merge with defaults
                                        if default_bg and "background_image" not in cover_config:
                                            cover_config["background_image"] = process_background_image(default_bg)
                                        elif "background_image" in cover_config:
                                            cover_config["background_image"] = process_background_image(cover_config["background_image"])
                                        if default_font:
                                            cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                                        if text_position:
                                            cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                                        
                                        subsection_page = doc[page_num]
                                        print(f"  Adding cover for {tab_name} -> {subsection_name} on page {page_num + 1}")
                                        self.add_cover_page(subsection_page, cover_config, self.page_width, self.page_height)
                                    break
            
            # Add cover pages for sub-subsections
            sub_subsections_config = cover_pages.get("sub_subsections", {})
            if sub_subsections_config and page_structure:
                print("Adding sub-subsection cover pages...")
                for tab_name, subsections in sub_subsections_config.items():
                    for subsection_name, sub_subsections in subsections.items():
                        for sub_subsection_name, sub_subsection_config in sub_subsections.items():
                            # Skip _page_2, _page_3, etc. for Kalender - handled directly in subsection logic
                            if sub_subsection_name.startswith("_page_"):
                                continue
                            
                            # Check if sub_subsection_config has page_1, page_2, etc. structure
                            if isinstance(sub_subsection_config, dict) and any(key.startswith("page_") for key in sub_subsection_config.keys()):
                                # New structure: page_1, page_2, etc.
                                # Iterate through all pages for this sub-subsection
                                for pg_num, pg_info in page_structure.items():
                                    if (pg_info.get("tab_name") == tab_name and 
                                        pg_info.get("subsection") == subsection_name and
                                        pg_info.get("sub_subsection") == sub_subsection_name):
                                        page_index = pg_info.get("page_index", 1)
                                        page_key = f"page_{page_index}"
                                        
                                        if page_key in sub_subsection_config:
                                            page_config = sub_subsection_config[page_key]
                                            page_num = int(pg_num) - 1  # Convert to 0-based
                                            if 0 <= page_num < total_pages:
                                                cover_config = page_config.copy()
                                                # Merge with defaults
                                                # Clan sheets (sub-subsections) should always use basic.png, not random
                                                is_clan_sheet = cover_config.get("image") is not None
                                                if is_clan_sheet:
                                                    print(f"  Debug: Found image for {sub_subsection_name} (page {page_index}): {cover_config.get('image')}")
                                                # Ensure image field is preserved
                                                if "image" in page_config:
                                                    cover_config["image"] = page_config["image"]
                                                # Preserve no_upper_tabs flag if present, or set it if background is basic_npc.png
                                                bg_image = cover_config.get("background_image", "")
                                                if "no_upper_tabs" in page_config:
                                                    cover_config["no_upper_tabs"] = page_config["no_upper_tabs"]
                                                    pg_info["no_upper_tabs"] = page_config["no_upper_tabs"]
                                                elif "basic_npc.png" in bg_image:
                                                    cover_config["no_upper_tabs"] = True
                                                    pg_info["no_upper_tabs"] = True
                                                if default_bg and "background_image" not in cover_config:
                                                    cover_config["background_image"] = process_background_image(default_bg, is_clan_sheet=is_clan_sheet)
                                                elif "background_image" in cover_config:
                                                    cover_config["background_image"] = process_background_image(cover_config["background_image"], is_clan_sheet=is_clan_sheet)
                                                
                                                # Check if final background_image is basic_npc.png and set no_upper_tabs
                                                final_bg = cover_config.get("background_image", "")
                                                if "basic_npc.png" in final_bg:
                                                    cover_config["no_upper_tabs"] = True
                                                    pg_info["no_upper_tabs"] = True
                                                
                                                if default_font:
                                                    cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                                                if text_position:
                                                    cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                                                
                                                sub_subsection_page = doc[page_num]
                                                print(f"  Adding cover for {tab_name} -> {subsection_name} -> {sub_subsection_name} (page {page_index}) on page {page_num + 1}")
                                                self.add_cover_page(sub_subsection_page, cover_config, self.page_width, self.page_height)
                            else:
                                # Normal sub-subsection handling (single page, no page_1/page_2 structure)
                                # Search page_structure for this sub-subsection
                                found = False
                                for pg_num, pg_info in page_structure.items():
                                    if (pg_info.get("tab_name") == tab_name and 
                                        pg_info.get("subsection") == subsection_name and
                                        pg_info.get("sub_subsection") == sub_subsection_name and
                                        pg_info.get("page_index", 1) == 1):  # Only process page_index 1 for old structure
                                        # This is the first page of this sub-subsection
                                        page_num = int(pg_num) - 1  # Convert to 0-based
                                        if 0 <= page_num < total_pages:
                                            cover_config = sub_subsection_config.copy()
                                            # Merge with defaults
                                            # Clan sheets (sub-subsections) should always use basic.png, not random
                                            is_clan_sheet = cover_config.get("image") is not None
                                            if default_bg and "background_image" not in cover_config:
                                                cover_config["background_image"] = process_background_image(default_bg, is_clan_sheet=is_clan_sheet)
                                            elif "background_image" in cover_config:
                                                cover_config["background_image"] = process_background_image(cover_config["background_image"], is_clan_sheet=is_clan_sheet)
                                            if default_font:
                                                cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                                            if text_position:
                                                cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                                            
                                            sub_subsection_page = doc[page_num]
                                            print(f"  Adding cover for {tab_name} -> {subsection_name} -> {sub_subsection_name} on page {page_num + 1}")
                                            self.add_cover_page(sub_subsection_page, cover_config, self.page_width, self.page_height)
                                            found = True
                                        break
                                if not found:
                                    print(f"  Warning: Could not find page for {tab_name} -> {subsection_name} -> {sub_subsection_name}")
            
            # Track which pages have cover pages
            pages_with_covers = set()
            if cover_pages_config:
                cover_pages = cover_pages_config.get("cover_pages", {})
                
                # Track tab cover pages
                for tab in tabs:
                    tab_name = tab.get("name")
                    target_page_num = tab.get("target_page", 1) - 1
                    if tab_name in cover_pages and 0 <= target_page_num < total_pages:
                        pages_with_covers.add(target_page_num)
                
                # Track subsection cover pages
                subsections_config = cover_pages.get("subsections", {})
                if subsections_config and page_structure:
                    for tab_name, subsections in subsections_config.items():
                        for subsection_name, subsection_config in subsections.items():
                            # Track all pages for this subsection (including page_1, page_2, etc.)
                            for pg_num, pg_info in page_structure.items():
                                if (pg_info.get("tab_name") == tab_name and 
                                    pg_info.get("subsection") == subsection_name and
                                    not pg_info.get("sub_subsection")):
                                    page_num = int(pg_num) - 1
                                    if 0 <= page_num < total_pages:
                                        pages_with_covers.add(page_num)
                
                # Track sub-subsection cover pages
                sub_subsections_config = cover_pages.get("sub_subsections", {})
                if sub_subsections_config and page_structure:
                    for tab_name, subsections in sub_subsections_config.items():
                        for subsection_name, sub_subsections in subsections.items():
                            for sub_subsection_name, sub_subsection_config in sub_subsections.items():
                                # Check if sub_subsection_config has page_1, page_2, etc. structure
                                if isinstance(sub_subsection_config, dict) and any(key.startswith("page_") for key in sub_subsection_config.keys()):
                                    # Track all pages for this sub-subsection (including page_1, page_2, etc.)
                                    for pg_num, pg_info in page_structure.items():
                                        if (pg_info.get("tab_name") == tab_name and 
                                            pg_info.get("subsection") == subsection_name and
                                            pg_info.get("sub_subsection") == sub_subsection_name):
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                pages_with_covers.add(page_num)
                                else:
                                    # Old structure: single page
                                    for pg_num, pg_info in page_structure.items():
                                        if (pg_info.get("tab_name") == tab_name and 
                                            pg_info.get("subsection") == subsection_name and
                                            pg_info.get("sub_subsection") == sub_subsection_name and
                                            pg_info.get("page_index", 1) == 1):
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                pages_with_covers.add(page_num)
                                            break
            
            # Add random background from assets/images/background/ to all pages without cover pages
            # Special handling: "Regeln" section uses assets/images/background/rules/
            script_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            
            rules_background_dir = os.path.join(background_dir, "rules")
            
            # Find all background images (excluding rules subdirectory)
            background_images = []
            if os.path.exists(background_dir):
                # Look for PNG files in background directory (but not in subdirectories)
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(background_dir, ext))
                    # Filter out subdirectories (like rules/)
                    background_images.extend([img for img in all_images if os.path.dirname(img) == background_dir])
                background_images.sort()  # Sort for consistent ordering
            
            # Find rules background images
            rules_background_images = []
            if os.path.exists(rules_background_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    rules_background_images.extend(glob.glob(os.path.join(rules_background_dir, ext)))
                rules_background_images.sort()
            
            # Fallback to basic.png if no background images found
            if not background_images:
                basic_bg_path = os.path.join(background_dir, "basic.png")
                if os.path.exists(basic_bg_path):
                    background_images = [basic_bg_path]
            
            if background_images or rules_background_images:
                print(f"Adding random backgrounds to pages without cover pages...")
                pages_with_bg = 0
                pages_with_rules_bg = 0
                for page_num in range(total_pages):
                    if page_num not in pages_with_covers:
                        try:
                            # Check if this page belongs to "Regeln" section
                            # page_structure uses 1-based page numbers as keys (integers)
                            page_info = page_structure.get(page_num + 1, {})
                            # Also try string key in case it's stored as string
                            if not page_info:
                                page_info = page_structure.get(str(page_num + 1), {})
                            
                            tab_name = page_info.get("tab_name", "")
                            is_rules_section = tab_name == "Regeln"
                            is_npcs_section = tab_name == "NPCs"
                            
                            # Select appropriate background directory
                            if is_rules_section and rules_background_images:
                                bg_image_path = random.choice(rules_background_images)
                                pages_with_rules_bg += 1
                            elif is_npcs_section:
                                # For NPCs section, use npc_2.png as default background
                                npc_2_path = os.path.join(script_dir, "assets", "images", "section_cover", "npc_2.png")
                                if not os.path.exists(npc_2_path):
                                    npc_2_path = os.path.join(os.getcwd(), "assets", "images", "section_cover", "npc_2.png")
                                if os.path.exists(npc_2_path):
                                    bg_image_path = npc_2_path
                                elif background_images:
                                    bg_image_path = random.choice(background_images)
                                else:
                                    continue  # Skip if no backgrounds available
                            elif background_images:
                                bg_image_path = random.choice(background_images)
                            else:
                                continue  # Skip if no backgrounds available
                            
                            page = doc[page_num]
                            # Compress image before insertion to reduce file size
                            compressed_path = self._compress_image(bg_image_path)
                            img_rect = fitz.Rect(0, 0, self.page_width, self.page_height)
                            page.insert_image(img_rect, filename=compressed_path, keep_proportion=False)
                            # Clean up temporary file if it was created
                            if compressed_path != bg_image_path and os.path.exists(compressed_path):
                                try:
                                    os.unlink(compressed_path)
                                except:
                                    pass
                            pages_with_bg += 1
                        except Exception as e:
                            print(f"  Warning: Could not add background to page {page_num + 1}: {e}")
                            import traceback
                            traceback.print_exc()
                print(f"  ✓ Added random backgrounds to {pages_with_bg} pages ({pages_with_rules_bg} from rules/)")
            else:
                print("Warning: No background images found in assets/images/background/, skipping background addition")
        
        # Draw blood splatters on all pages
        print("Drawing blood splatters...")
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
                page_info = page_structure.get(page_num + 1)
                # Skip upper tabs if page has no_upper_tabs flag
                if page_info and page_info.get("no_upper_tabs"):
                    continue
                
                # Check if this page uses basic_npc.png background (no upper tabs for these pages)
                # We need to check the cover_pages config to see if this page uses basic_npc.png
                if cover_pages_config:
                    cover_pages = cover_pages_config.get("cover_pages", {})
                    # Check subsections and sub_subsections for this page
                    tab_name = page_info.get("tab_name") if page_info else None
                    subsection_name = page_info.get("subsection") if page_info else None
                    sub_subsection_name = page_info.get("sub_subsection") if page_info else None
                    page_index = page_info.get("page_index", 1) if page_info else 1
                    
                    uses_basic_npc = False
                    if tab_name == "NPCs" and subsection_name:
                        # Check subsections
                        subsections_config = cover_pages.get("subsections", {})
                        if subsections_config and "NPCs" in subsections_config:
                            subsection_config = subsections_config["NPCs"].get(subsection_name)
                            if subsection_config:
                                if isinstance(subsection_config, dict) and any(k.startswith("page_") for k in subsection_config.keys()):
                                    page_key = f"page_{page_index}"
                                    if page_key in subsection_config:
                                        bg_image = subsection_config[page_key].get("background_image", "")
                                        if "basic_npc.png" in bg_image:
                                            uses_basic_npc = True
                        
                        # Check sub_subsections
                        if not uses_basic_npc and sub_subsection_name:
                            sub_subsections_config = cover_pages.get("sub_subsections", {})
                            if sub_subsections_config and "NPCs" in sub_subsections_config:
                                if subsection_name in sub_subsections_config["NPCs"]:
                                    sub_subsection_config = sub_subsections_config["NPCs"][subsection_name].get(sub_subsection_name)
                                    if sub_subsection_config:
                                        if isinstance(sub_subsection_config, dict) and any(k.startswith("page_") for k in sub_subsection_config.keys()):
                                            page_key = f"page_{page_index}"
                                            if page_key in sub_subsection_config:
                                                bg_image = sub_subsection_config[page_key].get("background_image", "")
                                                if "basic_npc.png" in bg_image:
                                                    uses_basic_npc = True
                    
                    if uses_basic_npc:
                        continue
                
                target_page = doc[page_num]
                self.add_upper_tabs_to_page(target_page, page_num + 1, page_structure, tab_subsections, metadata)
