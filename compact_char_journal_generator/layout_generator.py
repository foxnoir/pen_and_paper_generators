#!/usr/bin/env python3
"""
Layout Generator for Character Journal PDF
Handles all visual design elements: tabs, rounded rectangles, etc.
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
    """Generates layout elements (tabs, etc.) for PDF pages"""

    TAB_LABEL_FONT_NAME = "TabLabelFont"
    TAB_LABEL_MEASURE_FONT_NAME = "TabLabelFontMeasure"
    COVER_FONT_NAME = "CoverFont"
    TAB_LABEL_ROTATE = 270
    MAIN_COVER_TEXT_COLOR_HEX = "#514328"
    SUB_SECTION_COVER_TEXT_COLOR_HEX = "#43201F"
    COVER_GOLDEN_RATIO_PHI = (1.0 + math.sqrt(5.0)) / 2.0
    
    def __init__(self, page_width: float = 595.2755737304688, page_height: float = 841.8897705078125):
        self.page_width = page_width
        self.page_height = page_height
        
        # Tab width and position
        self.tab_width = 35.0  # Wider for better design and text
        self.tab_x = self.page_width - self.tab_width - 5  # Right margin with 5pt spacing
        self.right_tab_start_y = 65.0
        self.right_tab_spacing = 8.0
        self.right_tab_min_height = 40.0
        self.right_tab_max_height = 120.0
        self.right_tab_vertical_padding = 14.0
        self.right_tab_label_max_font = 12.5
        
        # Image compression settings
        self.image_quality = 85  # JPEG quality (1-100, lower = smaller file)

        self._tab_label_font = None
        self._cover_font = None
        self._tab_label_anchor_cache = {}
        self._registered_tab_font_page_keys = set()
        self._registered_cover_font_page_keys = set()
        self._impressions_once_index = 0
        self._impressions_once_queue: Optional[List[str]] = None
        self._refuge_once_index = 0
        self._refuge_once_queue: Optional[List[str]] = None
        self._last_random_image: Optional[str] = None
        
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
    
    RANDOM_FOLDER_MAP = {
        "random": ("dossier",),
        "random_dossier": ("dossier",),
        "random_favors": ("favors",),
        "random_gefallen": ("favors",),
        "random_my_missions": ("my_missions",),
        "random_meine_aufträge": ("my_missions",),
        "random_missions": ("missions",),
        "random_aufträge": ("missions",),
        "random_my_favors": ("my_favors",),
        "random_meine_gefallen": ("my_favors",),
        "random_contacts": ("contacts",),
        "random_allies": ("allies",),
        "random_enemies": ("enemies",),
        "random_weapons": ("weapons",),
        "random_research": ("research",),
        "random_audio": ("audio",),
        "random_refuge": ("refuge",),
        "random_locations": ("locations",),
        "random_notes": ("notes",),
        "random_npc": ("NPCs",),
        "random_npc_vampire": ("NPCs", "vampire"),
        "random_rules": ("background", "rules"),
    }

    @staticmethod
    def parse_sub_subsection_entries(sub_subsections_raw: list) -> List[Dict]:
        """Parse flat strings or nested {name, seconnd_subsections_left_tabs} entries."""
        entries: List[Dict] = []
        for item in sub_subsections_raw or []:
            if isinstance(item, str):
                entries.append({"name": item, "children": None})
            elif isinstance(item, dict):
                name = item.get("name", "")
                children = (
                    item.get("seconnd_subsections_left_tabs")
                    or item.get("sub_subsections")
                    or item.get("second_subsections_left_tabs")
                    or []
                )
                entries.append({"name": name, "children": children or None})
        return entries

    @staticmethod
    def page_count_from_config(config: Dict) -> int:
        if not isinstance(config, dict):
            return 0
        page_numbers = []
        for key in config:
            if key.startswith("page_"):
                try:
                    page_numbers.append(int(key.split("_")[1]))
                except ValueError:
                    pass
        return max(page_numbers) if page_numbers else 0

    @staticmethod
    def is_nested_group_config(config: Dict) -> bool:
        if not isinstance(config, dict):
            return False
        return any(
            not key.startswith("page_") and isinstance(config.get(key), dict)
            for key in config
        )
    
    def _images_dir(self, *folder_parts: str) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "assets", "images", *folder_parts)
        if not os.path.exists(path):
            path = os.path.join(os.getcwd(), "assets", "images", *folder_parts)
        return path

    def _get_folder_images(self, *folder_parts: str) -> List[str]:
        folder = self._images_dir(*folder_parts)
        images = []
        if os.path.exists(folder):
            for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                all_images = glob.glob(os.path.join(folder, ext))
                images.extend([img for img in all_images if os.path.dirname(img) == folder])
            images.sort()
        return images

    def _reset_random_pick_history(self) -> None:
        self._last_random_image = None

    def _pick_random_avoiding_consecutive(self, images: List[str]) -> Optional[str]:
        """Pick from pool; never the same file as the previous random background."""
        if not images:
            return None
        if len(images) == 1:
            picked = images[0]
        else:
            last = self._last_random_image
            candidates = [img for img in images if img != last]
            if not candidates:
                candidates = images
            picked = random.choice(candidates)
        self._last_random_image = picked
        return picked

    @staticmethod
    def _shuffle_no_consecutive(items: List[str], avoid_adjacent_to: Optional[str] = None) -> List[str]:
        """Reorder so no two adjacent entries are equal (best effort)."""
        if len(items) <= 1:
            return list(items)
        result = list(items)
        random.shuffle(result)
        if avoid_adjacent_to and result[0] == avoid_adjacent_to:
            for j in range(1, len(result)):
                if result[j] != avoid_adjacent_to:
                    result[0], result[j] = result[j], result[0]
                    break
        for i in range(1, len(result)):
            if result[i] == result[i - 1]:
                for j in range(i + 1, len(result)):
                    if result[j] != result[i - 1]:
                        result[i], result[j] = result[j], result[i]
                        break
        return result

    def _pick_random_from_folder(self, *folder_parts: str) -> Optional[str]:
        images = self._get_folder_images(*folder_parts)
        return self._pick_random_avoiding_consecutive(images)

    def _pick_random_folder_background(self, *folder_parts: str) -> str:
        picked = self._pick_random_from_folder(*folder_parts)
        if picked:
            return picked
        picked = self._pick_random_dossier()
        if picked:
            return picked
        return os.path.join(self._images_dir("background"), "basic.png")

    def _dossier_dir(self) -> str:
        return self._images_dir("dossier")

    def _get_dossier_images(self) -> List[str]:
        return self._get_folder_images("dossier")

    def _pick_random_dossier(self) -> Optional[str]:
        return self._pick_random_from_folder("dossier")

    IMPRESSIONS_FIRST_NAME = "1.png"
    IMPRESSIONS_FIXED_ORDER = ("3.png", "4.png", "5.png", "6.png")
    IMPRESSIONS_DOSSIER_EXTRA_PAGES = 10

    def impressions_image_count(self) -> int:
        return len(self._get_folder_images("impressions"))

    def impressionen_tab_page_count(self) -> int:
        """1 cover + all impressions images + dossier extras."""
        return 1 + self.impressions_image_count() + self.IMPRESSIONS_DOSSIER_EXTRA_PAGES

    def _reset_impressions_once(self) -> None:
        self._impressions_once_index = 0
        self._impressions_once_queue = None

    def _build_impressions_once_queue(self) -> List[str]:
        """All images once: 1 first, then 3–6, then remaining files in random order."""
        images = self._get_folder_images("impressions")
        by_name = {os.path.basename(img): img for img in images}
        queue: List[str] = []
        if self.IMPRESSIONS_FIRST_NAME in by_name:
            queue.append(by_name[self.IMPRESSIONS_FIRST_NAME])
        for name in self.IMPRESSIONS_FIXED_ORDER:
            if name in by_name:
                queue.append(by_name[name])
        reserved = {self.IMPRESSIONS_FIRST_NAME, *self.IMPRESSIONS_FIXED_ORDER}
        rest = [img for img in images if os.path.basename(img) not in reserved]
        avoid = queue[-1] if queue else None
        queue.extend(self._shuffle_no_consecutive(rest, avoid_adjacent_to=avoid))
        return queue

    def sync_impressionen_cover_pages(self, cover_pages_config: Dict) -> None:
        """Build Impressionen page_N entries from assets/images/impressions/ at generate time."""
        if not cover_pages_config:
            return
        cover_pages = cover_pages_config.get("cover_pages", {})
        if "Impressionen" not in cover_pages:
            return
        n = self.impressions_image_count()
        page_1 = cover_pages["Impressionen"].get(
            "page_1",
            {
                "background_image": "assets/images/section_cover/main_cover.png",
                "title": "Impressionen",
            },
        )
        imp: Dict = {"page_1": page_1}
        for i in range(2, n + 2):
            imp[f"page_{i}"] = {"background_image": "impressions_once"}
        dossier_start = n + 2
        for i in range(dossier_start, dossier_start + self.IMPRESSIONS_DOSSIER_EXTRA_PAGES):
            imp[f"page_{i}"] = {"background_image": "random"}
        cover_pages["Impressionen"] = imp

    def _next_impressions_once(self) -> str:
        if self._impressions_once_queue is None:
            self._impressions_once_queue = self._build_impressions_once_queue()
        if self._impressions_once_index < len(self._impressions_once_queue):
            path = self._impressions_once_queue[self._impressions_once_index]
            self._impressions_once_index += 1
            self._last_random_image = path
            return path
        picked = self._pick_random_dossier()
        if picked:
            return picked
        return self._pick_random_folder_background("dossier")

    def _reset_refuge_once(self) -> None:
        self._refuge_once_index = 0
        self._refuge_once_queue = None

    def _next_refuge_once(self) -> str:
        """Each refuge/ image once (sorted), then dossier fallback."""
        if self._refuge_once_queue is None:
            self._refuge_once_queue = self._get_folder_images("refuge")
        if self._refuge_once_index < len(self._refuge_once_queue):
            path = self._refuge_once_queue[self._refuge_once_index]
            self._refuge_once_index += 1
            self._last_random_image = path
            return path
        picked = self._pick_random_dossier()
        if picked:
            return picked
        return self._pick_random_folder_background("dossier")
    
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
    
    def _get_tab_label_font_path(self) -> Optional[str]:
        """Return path to the decorative tab label font (Alex Brush)."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = [
            os.path.join(script_dir, "assets", "fonts", "alex.ttf"),
            os.path.join(os.getcwd(), "assets", "fonts", "alex.ttf"),
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                return os.path.abspath(font_path)
        return None

    def _get_tab_label_font(self) -> fitz.Font:
        """Return the decorative tab label font, cached on the instance."""
        if self._tab_label_font is None:
            font_path = self._get_tab_label_font_path()
            if font_path:
                self._tab_label_font = fitz.Font(fontfile=font_path)
            else:
                self._tab_label_font = fitz.Font("heit")
        return self._tab_label_font

    def _tab_font_page_key(self, page: fitz.Page) -> tuple:
        """Stable key for per-page font registration (PyMuPDF reuses page object ids)."""
        return (id(page.parent), page.number)

    def _register_tab_label_font(self, page: fitz.Page) -> bool:
        """Embed the custom tab font on a page once."""
        page_key = self._tab_font_page_key(page)
        if page_key in self._registered_tab_font_page_keys:
            return True

        font_path = self._get_tab_label_font_path()
        if not font_path:
            return False

        try:
            page.insert_font(fontname=self.TAB_LABEL_FONT_NAME, fontfile=font_path)
        except Exception:
            font = self._get_tab_label_font()
            page.insert_font(fontname=self.TAB_LABEL_FONT_NAME, fontbuffer=font.buffer)

        self._registered_tab_font_page_keys.add(page_key)
        return True

    def _measure_tab_label_text_width(self, text: str, fontsize: float) -> float:
        """Measure horizontal text width using the journal tab font."""
        return self._get_tab_label_font().text_length(text, fontsize=fontsize)

    def _draw_horizontal_tab_label_text(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        text: str,
        fontsize: float,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Draw horizontal tab label text using the journal font."""
        self._register_tab_label_font(page)
        page.insert_text(
            (x, y),
            text,
            fontsize=fontsize,
            fontname=self.TAB_LABEL_FONT_NAME,
            color=color,
        )

    def _draw_centered_tab_label_text(
        self,
        page: fitz.Page,
        center_x: float,
        y: float,
        text: str,
        fontsize: float,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Draw horizontally centered tab text using Alex Brush."""
        text_width = self._measure_tab_label_text_width(text, fontsize)
        self._draw_horizontal_tab_label_text(page, center_x - text_width / 2, y, text, fontsize, color)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)

    def _is_sub_section_cover(self, cover_config: Dict) -> bool:
        return "sub_section_cover" in (cover_config.get("background_image") or "")

    def _cover_text_color(self, cover_config: Dict) -> tuple:
        if self._is_sub_section_cover(cover_config):
            return self._hex_to_rgb(self.SUB_SECTION_COVER_TEXT_COLOR_HEX)
        bg = cover_config.get("background_image") or ""
        if "main_cover" in bg:
            return self._hex_to_rgb(self.MAIN_COVER_TEXT_COLOR_HEX)
        return (0.0, 0.0, 0.0)

    def _cover_font_sizes(self, cover_config: Dict) -> tuple:
        """Return (title_size, subtitle_size, description_size); sub covers slightly smaller."""
        font_config = cover_config.get("default_font", {})
        title_size = font_config.get("title_size", 48)
        subtitle_size = font_config.get("subtitle_size", 24)
        description_size = font_config.get("description_size", 14)
        if self._is_sub_section_cover(cover_config):
            title_size = round(title_size * 0.875)
            subtitle_size = round(subtitle_size * 0.875)
            description_size = round(description_size * 0.857)
        return title_size, subtitle_size, description_size

    def _get_cover_font_path(self) -> Optional[str]:
        """Return path to the cover page font (Whispering Signature)."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = [
            os.path.join(script_dir, "assets", "fonts", "WhisperingSignature.ttf"),
            os.path.join(os.getcwd(), "assets", "fonts", "WhisperingSignature.ttf"),
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                return os.path.abspath(font_path)
        return None

    def _get_cover_font(self) -> fitz.Font:
        """Return the cover page font, cached on the instance."""
        if self._cover_font is None:
            font_path = self._get_cover_font_path()
            if font_path:
                self._cover_font = fitz.Font(fontfile=font_path)
            else:
                self._cover_font = fitz.Font("heit")
        return self._cover_font

    def _register_cover_font(self, page: fitz.Page) -> bool:
        """Embed the cover page font on a page once."""
        page_key = self._tab_font_page_key(page)
        if page_key in self._registered_cover_font_page_keys:
            return True

        font_path = self._get_cover_font_path()
        if not font_path:
            return False

        try:
            page.insert_font(fontname=self.COVER_FONT_NAME, fontfile=font_path)
        except Exception:
            font = self._get_cover_font()
            page.insert_font(fontname=self.COVER_FONT_NAME, fontbuffer=font.buffer)

        self._registered_cover_font_page_keys.add(page_key)
        return True

    def _measure_cover_text_width(self, text: str, fontsize: float) -> float:
        """Measure horizontal text width using the cover page font."""
        return self._get_cover_font().text_length(text, fontsize=fontsize)

    def _draw_horizontal_cover_text(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        text: str,
        fontsize: float,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Draw horizontal cover text using Whispering Signature."""
        self._register_cover_font(page)
        page.insert_text(
            (x, y),
            text,
            fontsize=fontsize,
            fontname=self.COVER_FONT_NAME,
            color=color,
        )

    def _draw_centered_cover_text(
        self,
        page: fitz.Page,
        center_x: float,
        y: float,
        text: str,
        fontsize: float,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Draw horizontally centered cover text using Whispering Signature."""
        text_width = self._measure_cover_text_width(text, fontsize)
        self._draw_horizontal_cover_text(page, center_x - text_width / 2, y, text, fontsize, color)

    def _get_rotated_label_anchor_offset(self, font_path: str, text: str, fontsize: float) -> tuple:
        """Measure anchor offset so rotated text is centered at the insertion point."""
        cache_key = (font_path, text, fontsize, self.TAB_LABEL_ROTATE)
        if cache_key in self._tab_label_anchor_cache:
            return self._tab_label_anchor_cache[cache_key]

        measure_doc = fitz.open()
        measure_page = measure_doc.new_page(width=400, height=400)
        try:
            measure_page.insert_font(fontname=self.TAB_LABEL_MEASURE_FONT_NAME, fontfile=font_path)
        except Exception:
            font = self._get_tab_label_font()
            measure_page.insert_font(fontname=self.TAB_LABEL_MEASURE_FONT_NAME, fontbuffer=font.buffer)
        origin = fitz.Point(200, 200)
        measure_page.insert_text(
            origin,
            text,
            fontsize=fontsize,
            fontname=self.TAB_LABEL_MEASURE_FONT_NAME,
            rotate=self.TAB_LABEL_ROTATE,
        )

        bbox = None
        for block in measure_page.get_text("dict")["blocks"]:
            if block.get("lines"):
                for span in block["lines"][0]["spans"]:
                    if text[:3] in span["text"]:
                        bbox = span["bbox"]
                        break
            if bbox:
                break
        measure_doc.close()

        if not bbox:
            offset = (0.0, 0.0)
        else:
            bbox_center_x = (bbox[0] + bbox[2]) / 2
            bbox_center_y = (bbox[1] + bbox[3]) / 2
            offset = (origin.x - bbox_center_x, origin.y - bbox_center_y)

        self._tab_label_anchor_cache[cache_key] = offset
        return offset

    def compute_right_tab_height(self, tab_name: str) -> float:
        """Tab height from label width at max font size (vertical text), plus padding."""
        if not tab_name:
            return self.right_tab_min_height
        font = self._get_tab_label_font()
        text_len = font.text_length(tab_name, fontsize=self.right_tab_label_max_font)
        height = text_len + self.right_tab_vertical_padding
        return max(self.right_tab_min_height, min(self.right_tab_max_height, height))

    def layout_right_tabs(self, tab_names: List[str], start_y: Optional[float] = None, spacing: Optional[float] = None) -> List[Dict]:
        """Stack right tabs with uniform spacing; y and height derived from each name."""
        start_y = self.right_tab_start_y if start_y is None else start_y
        spacing = self.right_tab_spacing if spacing is None else spacing
        tabs: List[Dict] = []
        current_y = start_y
        for name in tab_names:
            height = self.compute_right_tab_height(name)
            tabs.append({"name": name, "y": current_y, "height": height})
            current_y += height + spacing
        return tabs

    def _fit_right_tab_fontsize(
        self,
        tab_name: str,
        tab_height: float,
        font: fitz.Font,
        max_fontsize: float = 12.5,
        min_fontsize: float = 6.0,
    ) -> float:
        """Scale font size so vertical tab labels fit within the tab height."""
        available = max(tab_height - 8.0, min_fontsize)
        fontsize = max_fontsize
        while fontsize >= min_fontsize:
            if font.text_length(tab_name, fontsize=fontsize) <= available:
                return fontsize
            fontsize -= 0.25
        return min_fontsize

    def _draw_vertical_right_tab_text(self, page: fitz.Page, tab_rect: fitz.Rect, tab_name: str, tab_height: float, page_num: int):
        """Draw right-side tab label vertically, centered in the tab (top-to-bottom)."""
        font = self._get_tab_label_font()
        fontsize = self._fit_right_tab_fontsize(tab_name, tab_height, font)
        text_color = self.tab_colors["text"]
        font_path = self._get_tab_label_font_path()

        if self._register_tab_label_font(page):
            try:
                offset_x, offset_y = self._get_rotated_label_anchor_offset(font_path, tab_name, fontsize)
                center_x = tab_rect.x0 + self.tab_width / 2
                center_y = tab_rect.y0 + tab_height / 2
                page.insert_text(
                    fitz.Point(center_x + offset_x, center_y + offset_y),
                    tab_name,
                    fontsize=fontsize,
                    fontname=self.TAB_LABEL_FONT_NAME,
                    color=text_color,
                    rotate=self.TAB_LABEL_ROTATE,
                )
                return
            except Exception:
                pass

        text_rect = fitz.Rect(
            tab_rect.x0 + 2,
            tab_rect.y0 + 2,
            tab_rect.x1 - 2,
            tab_rect.y1 - 2,
        )

        while fontsize >= 6.0:
            rc = page.insert_textbox(
                text_rect,
                tab_name,
                fontsize=fontsize,
                fontname="heit",
                color=text_color,
                rotate=self.TAB_LABEL_ROTATE,
                align=fitz.TEXT_ALIGN_CENTER,
            )
            if rc >= 0:
                return
            fontsize -= 0.25

        page.insert_textbox(
            text_rect,
            tab_name,
            fontsize=6.0,
            fontname="heit",
            color=text_color,
            rotate=self.TAB_LABEL_ROTATE,
            align=fitz.TEXT_ALIGN_CENTER,
        )

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
        tab_name = tab.get("name", "")
        if tab_name:
            self._draw_vertical_right_tab_text(page, tab_rect, tab_name, tab["height"], page_num)
        
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
        self._register_tab_label_font(page)
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
        sub_subsection_group_name = page_info.get("sub_subsection_group")
        
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

        self._register_tab_label_font(page)
        
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
        third_row_tabs = []
        
        # Find target pages for subsections and sub-subsections
        subsection_target_pages = {}  # subsection_name -> page_num
        sub_subsection_target_pages = {}  # (subsection_name, sub_subsection_name) -> page_num
        group_target_pages = {}  # (subsection_name, group_name) -> page_num
        nested_target_pages = {}  # (subsection_name, group_name, leaf_name) -> page_num
        
        # Search through page_structure to find target pages
        for pg_num, pg_info in page_structure.items():
            if pg_info.get("tab_name") == tab_name:
                pg_subsection = pg_info.get("subsection")
                pg_sub_subsection = pg_info.get("sub_subsection")
                pg_group = pg_info.get("sub_subsection_group")
                pg_page_index = pg_info.get("page_index", 1)  # Default to 1 if not set
                
                if pg_subsection and not pg_sub_subsection and not pg_group:
                    # This is a subsection page
                    # Only use the first page (page_index=1) as target, even if there are multiple pages
                    if pg_subsection not in subsection_target_pages or pg_page_index == 1:
                        if pg_page_index == 1:
                            subsection_target_pages[pg_subsection] = pg_num
                        elif pg_subsection not in subsection_target_pages:
                            # Fallback: use first found page if page_index is not set
                            subsection_target_pages[pg_subsection] = pg_num
                elif pg_subsection and pg_group and pg_sub_subsection:
                    key = (pg_subsection, pg_group, pg_sub_subsection)
                    if key not in nested_target_pages or pg_page_index == 1:
                        if pg_page_index == 1:
                            nested_target_pages[key] = pg_num
                        elif key not in nested_target_pages:
                            nested_target_pages[key] = pg_num
                elif pg_subsection and pg_group and not pg_sub_subsection:
                    key = (pg_subsection, pg_group)
                    if key not in group_target_pages or pg_page_index == 1:
                        if pg_page_index == 1:
                            group_target_pages[key] = pg_num
                        elif key not in group_target_pages:
                            group_target_pages[key] = pg_num
                elif pg_subsection and pg_sub_subsection:
                    # This is a flat sub-subsection page
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
                for entry in self.parse_sub_subsection_entries(sub_subsections):
                    entry_name = entry["name"]
                    if entry["children"]:
                        target_page = group_target_pages.get((subsection_name, entry_name))
                        is_active = sub_subsection_group_name == entry_name
                        second_row_tabs.append({
                            "name": entry_name,
                            "is_active": is_active,
                            "target_page": target_page,
                        })
                    else:
                        target_page = sub_subsection_target_pages.get((subsection_name, entry_name))
                        is_active = (
                            sub_subsection_name == entry_name and not sub_subsection_group_name
                        )
                        second_row_tabs.append({
                            "name": entry_name,
                            "is_active": is_active,
                            "target_page": target_page,
                        })

                if sub_subsection_group_name:
                    for entry in self.parse_sub_subsection_entries(sub_subsections):
                        if entry["children"] and entry["name"] == sub_subsection_group_name:
                            for child_name in entry["children"]:
                                target_page = nested_target_pages.get(
                                    (subsection_name, sub_subsection_group_name, child_name)
                                )
                                third_row_tabs.append({
                                    "name": child_name,
                                    "is_active": sub_subsection_name == child_name,
                                    "target_page": target_page,
                                })
                            break
        
        # Draw first row
        row_y = current_y
        row_start_x = start_x
        
        for tab_data in first_row_tabs:
            tab_name_upper = tab_data["name"]
            is_active = tab_data["is_active"]
            
            # Calculate tab width dynamically based on actual text width
            font_size = 9
            text_width_pt = self._measure_tab_label_text_width(tab_name_upper, font_size)
            
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
            
            # Add text - calculate text width and center manually
            font_size = 9
            text_width = self._measure_tab_label_text_width(tab_name_upper, font_size)
            tab_center_x = row_start_x + tab_width_actual / 2
            text_x = tab_center_x - (text_width / 2)
            text_y = row_y + tab_height / 2 + (font_size * 0.35)
            try:
                self._draw_horizontal_tab_label_text(page, text_x, text_y, tab_name_upper, font_size)
            except Exception:
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
                text_width_pt = self._measure_tab_label_text_width(tab_name_upper, font_size)
                
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
                
                # Add text - calculate text width and center manually
                font_size = 8
                text_width = self._measure_tab_label_text_width(tab_name_upper, font_size)
                tab_center_x = row_start_x + tab_width_actual / 2
                text_x = tab_center_x - (text_width / 2)
                text_y = row_y + (tab_height * 0.85) / 2 + (font_size * 0.35)
                try:
                    self._draw_horizontal_tab_label_text(page, text_x, text_y, tab_name_upper, font_size)
                except Exception:
                    pass
                
                row_start_x += tab_width_actual + tab_spacing
        
        # Draw third row (nested sub-subsections, e.g. Inspiration -> Ja/Nein/...)
        if third_row_tabs:
            row_y = row_y + tab_height * 0.85 + row_spacing
            row_start_x = start_x
            
            for tab_data in third_row_tabs:
                tab_name_upper = tab_data["name"]
                is_active = tab_data["is_active"]
                
                font_size = 8
                text_width_pt = self._measure_tab_label_text_width(tab_name_upper, font_size)
                has_ampersand = '&' in tab_name_upper
                text_length = len(tab_name_upper)
                
                if has_ampersand:
                    extra_ampersand_padding = 8 if text_width_pt <= 40 else 12
                else:
                    extra_ampersand_padding = 0
                
                if not has_ampersand and text_length > 10:
                    extra_length_padding = (text_length - 10) * 0.7
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
                
                tab_width_actual = max(tab_width_base * 0.7, text_width_pt + padding)
                
                available_width = max_width - (row_start_x - start_x)
                if tab_width_actual > available_width and row_start_x > start_x:
                    row_y += tab_height * 0.85 + row_spacing
                    row_start_x = start_x
                
                tab_rect = fitz.Rect(
                    row_start_x,
                    row_y,
                    row_start_x + tab_width_actual,
                    row_y + tab_height * 0.85,
                )
                
                bg_color = self.tab_colors["active"] if is_active else self.tab_colors["background"]
                self.draw_rounded_rect(page, tab_rect, bg_color, border_color=None, radius=3.5, shadow=True, opacity=0.7)
                
                if tab_data.get("target_page") is not None:
                    try:
                        page.insert_link({
                            "kind": fitz.LINK_GOTO,
                            "from": tab_rect,
                            "page": tab_data["target_page"] - 1,
                            "to": fitz.Point(0, 0),
                            "zoom": 0.0,
                        })
                    except Exception:
                        pass
                
                text_width = self._measure_tab_label_text_width(tab_name_upper, font_size)
                tab_center_x = row_start_x + tab_width_actual / 2
                text_x = tab_center_x - (text_width / 2)
                text_y = row_y + (tab_height * 0.85) / 2 + (font_size * 0.35)
                try:
                    self._draw_horizontal_tab_label_text(page, text_x, text_y, tab_name_upper, font_size)
                except Exception:
                    pass
                
                row_start_x += tab_width_actual + tab_spacing
    
    def _get_lilith_font_path(self):
        """Returns the absolute path to the cover page font file (Whispering Signature)."""
        return self._get_cover_font_path()
    
    def add_cover_page(self, page: fitz.Page, cover_config: Dict, page_width: float, page_height: float, sub_subsection_name: str = None):
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
        
        # Resolve random_* keywords to a random image from the matching assets/images/ folder
        if bg_image_path == "impressions_once":
            bg_image_path = self._next_impressions_once()
        elif bg_image_path == "refuge_once":
            bg_image_path = self._next_refuge_once()
        elif bg_image_path in self.RANDOM_FOLDER_MAP:
            bg_image_path = self._pick_random_folder_background(*self.RANDOM_FOLDER_MAP[bg_image_path])
        
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
            picked = self._pick_random_dossier()
            if picked:
                bg_image_path = picked
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
                            bg_image_path = normalized
                            break
                    if bg_image_path and os.path.exists(bg_image_path):
                        break
                
                # If still not found, use fallback background
                if not bg_image_path or not os.path.exists(bg_image_path):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    background_dir = os.path.join(script_dir, "assets", "images", "background")
                    if not os.path.exists(background_dir):
                        background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
                    fallback_path = os.path.join(background_dir, "basic.png")
                    if os.path.exists(fallback_path):
                        bg_image_path = fallback_path
                        print(f"  Using fallback background: {bg_image_path}")
                    else:
                        # Try default_background from config if available
                        default_bg = cover_config.get("default_background")
                        if default_bg:
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            possible_paths = [
                                default_bg,
                                os.path.join(script_dir, default_bg),
                                os.path.join(os.getcwd(), default_bg)
                            ]
                            for path in possible_paths:
                                if os.path.exists(path):
                                    bg_image_path = path
                                    print(f"  Using default_background: {bg_image_path}")
                                    break
                
                # If we now have a valid bg_image_path, try to insert it
                if bg_image_path and os.path.exists(bg_image_path):
                    try:
                        compressed_path = self._compress_image(bg_image_path)
                        img_rect = fitz.Rect(0, 0, page_width, page_height)
                        page.insert_image(img_rect, filename=compressed_path, keep_proportion=False)
                        if compressed_path != bg_image_path and os.path.exists(compressed_path):
                            try:
                                os.unlink(compressed_path)
                            except:
                                pass
                    except Exception as e:
                        print(f"Warning: Could not load fallback background image: {e}")
        
        # If bg_image_path is still None or empty, use default fallback
        if not bg_image_path:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            fallback_path = os.path.join(background_dir, "basic.png")
            if os.path.exists(fallback_path):
                bg_image_path = fallback_path
                try:
                    compressed_path = self._compress_image(bg_image_path)
                    img_rect = fitz.Rect(0, 0, page_width, page_height)
                    page.insert_image(img_rect, filename=compressed_path, keep_proportion=False)
                    if compressed_path != bg_image_path and os.path.exists(compressed_path):
                        try:
                            os.unlink(compressed_path)
                        except:
                            pass
                    print(f"  Using default fallback background: {bg_image_path}")
                except Exception as e:
                    print(f"Warning: Could not load default fallback background: {e}")
        
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
        
        title_size, subtitle_size, description_size = self._cover_font_sizes(cover_config)
        
        # Vertical anchor: between page center and lower golden ratio (~55% from top)
        pos_config = cover_config.get("text_position", {})
        center_y = page_height / 2
        lower_golden_y = page_height / self.COVER_GOLDEN_RATIO_PHI
        golden_anchor_y = (center_y + lower_golden_y) / 2 - 65
        title_y = golden_anchor_y + pos_config.get("title_y_offset", 0)
        subtitle_y = golden_anchor_y + pos_config.get("subtitle_y_offset", 40)
        description_y = golden_anchor_y + pos_config.get("description_y_offset", 85)
        cover_text_color = self._cover_text_color(cover_config)
        
        center_x = page_width / 2
        
        # Draw title (centered, large) - using Whispering Signature
        if title:
            self._register_cover_font(page)
            try:
                self._draw_centered_cover_text(
                    page, center_x, title_y, title, title_size, color=cover_text_color
                )
            except Exception as e:
                print(f"Warning: Could not use cover font for title, falling back to helv-Bold: {e}")
                try:
                    text_width = fitz.get_text_length(title, fontname='helv-Bold', fontsize=title_size)
                    page.insert_text(
                        (center_x - text_width / 2, title_y),
                        title,
                        fontsize=title_size,
                        fontname='helv-Bold',
                        color=cover_text_color,
                    )
                except Exception:
                    pass
        
        # Draw subtitle (centered, medium size) — skip when identical to title
        if subtitle and subtitle.strip() != (title or "").strip():
            try:
                self._draw_centered_cover_text(
                    page, center_x, subtitle_y, subtitle, subtitle_size, color=cover_text_color
                )
            except Exception:
                try:
                    text_width = fitz.get_text_length(subtitle, fontname='helv', fontsize=subtitle_size)
                    page.insert_text(
                        (center_x - text_width / 2, subtitle_y),
                        subtitle,
                        fontsize=subtitle_size,
                        fontname='helv',
                        color=cover_text_color,
                    )
                except Exception:
                    pass
        
        # Draw description (centered, smaller, wrapped if needed)
        if description:
            desc_rect = fitz.Rect(
                center_x - 200,
                description_y - 50,
                center_x + 200,
                description_y + 100,
            )
            try:
                self._register_cover_font(page)
                font_path = self._get_cover_font_path()
                textbox_kwargs = {
                    "fontsize": description_size,
                    "fontname": self.COVER_FONT_NAME,
                    "color": cover_text_color,
                    "align": fitz.TEXT_ALIGN_CENTER,
                }
                if font_path:
                    textbox_kwargs["fontfile"] = font_path
                rc = page.insert_textbox(desc_rect, description, **textbox_kwargs)
                if rc < 0:
                    self._draw_centered_cover_text(
                        page, center_x, description_y, description, description_size, color=cover_text_color
                    )
            except Exception:
                try:
                    self._draw_centered_cover_text(
                        page, center_x, description_y, description, description_size, color=cover_text_color
                    )
                except Exception:
                    pass
    
    def apply_layout_to_pdf(self, doc: fitz.Document, tabs: List[Dict], tab_text_elements: List[Dict] = None, page_structure: Dict = None, tab_subsections: Dict = None, metadata: Dict = None, cover_pages_config: Dict = None):
        """Applies layout (tabs) to all pages of a PDF"""
        total_pages = len(doc)
        self._reset_random_pick_history()
        self._reset_refuge_once()
        
        # Add cover pages BEFORE tabs
        if cover_pages_config:
            print("Adding cover pages...")
            cover_pages = cover_pages_config.get("cover_pages", {})
            default_bg = cover_pages_config.get("default_background", "")
            default_font = cover_pages_config.get("default_font", {})
            text_position = cover_pages_config.get("text_position", {})
            
            # Add title page if it exists (page 1, 0-based index 0)
            if "title_page" in cover_pages and total_pages > 0:
                title_page_config = cover_pages["title_page"]
                cover_config = title_page_config.copy()
                # Merge with defaults
                if default_bg and "background_image" not in cover_config:
                    cover_config["background_image"] = default_bg
                elif "background_image" in cover_config:
                    cover_config["background_image"] = cover_config["background_image"]
                if default_font:
                    cover_config["default_font"] = {**default_font, **cover_config.get("default_font", {})}
                if text_position:
                    cover_config["text_position"] = {**text_position, **cover_config.get("text_position", {})}
                
                title_page = doc[0]
                print(f"  Adding title page on page 1")
                self.add_cover_page(title_page, cover_config, self.page_width, self.page_height)
            
            # Get list of dossier images for random selection
            dossier_images = self._get_dossier_images()
            
            # Helper function to get random dossier background or fallback
            def get_random_background():
                picked = self._pick_random_avoiding_consecutive(dossier_images)
                if picked:
                    return picked
                # Fallback to basic.png or default_bg
                if default_bg and "basic.png" not in default_bg:
                    return default_bg
                script_dir = os.path.dirname(os.path.abspath(__file__))
                background_dir = os.path.join(script_dir, "assets", "images", "background")
                if not os.path.exists(background_dir):
                    background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
                return os.path.join(background_dir, "basic.png")
            
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
                        if tab_name == "Impressionen":
                            self._reset_impressions_once()
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

                            if (
                                isinstance(sub_subsection_config, dict)
                                and self.is_nested_group_config(sub_subsection_config)
                            ):
                                child_names = [
                                    key for key in sub_subsection_config
                                    if not key.startswith("page_")
                                    and isinstance(sub_subsection_config.get(key), dict)
                                ]
                                for pg_num, pg_info in page_structure.items():
                                    if (
                                        pg_info.get("tab_name") == tab_name
                                        and pg_info.get("subsection") == subsection_name
                                        and pg_info.get("sub_subsection_group") == sub_subsection_name
                                        and not pg_info.get("sub_subsection")
                                    ):
                                        page_index = pg_info.get("page_index", 1)
                                        page_key = f"page_{page_index}"
                                        if page_key in sub_subsection_config:
                                            page_config = sub_subsection_config[page_key]
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                cover_config = page_config.copy()
                                                is_clan_sheet = cover_config.get("image") is not None
                                                if default_bg and "background_image" not in cover_config:
                                                    cover_config["background_image"] = process_background_image(
                                                        default_bg, is_clan_sheet=is_clan_sheet
                                                    )
                                                elif "background_image" in cover_config:
                                                    cover_config["background_image"] = process_background_image(
                                                        cover_config["background_image"], is_clan_sheet=is_clan_sheet
                                                    )
                                                if default_font:
                                                    cover_config["default_font"] = {
                                                        **default_font,
                                                        **cover_config.get("default_font", {}),
                                                    }
                                                if text_position:
                                                    cover_config["text_position"] = {
                                                        **text_position,
                                                        **cover_config.get("text_position", {}),
                                                    }
                                                print(
                                                    f"  Adding cover for {tab_name} -> {subsection_name} -> "
                                                    f"{sub_subsection_name} (page {page_index}) on page {page_num + 1}"
                                                )
                                                self.add_cover_page(
                                                    doc[page_num],
                                                    cover_config,
                                                    self.page_width,
                                                    self.page_height,
                                                    sub_subsection_name,
                                                )
                                for child_name in child_names:
                                    child_config = sub_subsection_config.get(child_name, {})
                                    for pg_num, pg_info in page_structure.items():
                                        if (
                                            pg_info.get("tab_name") == tab_name
                                            and pg_info.get("subsection") == subsection_name
                                            and pg_info.get("sub_subsection_group") == sub_subsection_name
                                            and pg_info.get("sub_subsection") == child_name
                                        ):
                                            page_index = pg_info.get("page_index", 1)
                                            page_key = f"page_{page_index}"
                                            if page_key not in child_config:
                                                continue
                                            page_config = child_config[page_key]
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                cover_config = page_config.copy()
                                                is_clan_sheet = cover_config.get("image") is not None
                                                if "image" in page_config:
                                                    cover_config["image"] = page_config["image"]
                                                bg_image = cover_config.get("background_image", "")
                                                if "no_upper_tabs" in page_config:
                                                    cover_config["no_upper_tabs"] = page_config["no_upper_tabs"]
                                                    pg_info["no_upper_tabs"] = page_config["no_upper_tabs"]
                                                elif "basic_npc.png" in bg_image:
                                                    cover_config["no_upper_tabs"] = True
                                                    pg_info["no_upper_tabs"] = True
                                                if default_bg and "background_image" not in cover_config:
                                                    cover_config["background_image"] = process_background_image(
                                                        default_bg, is_clan_sheet=is_clan_sheet
                                                    )
                                                elif "background_image" in cover_config:
                                                    cover_config["background_image"] = process_background_image(
                                                        cover_config["background_image"], is_clan_sheet=is_clan_sheet
                                                    )
                                                final_bg = cover_config.get("background_image", "")
                                                if "basic_npc.png" in final_bg:
                                                    cover_config["no_upper_tabs"] = True
                                                    pg_info["no_upper_tabs"] = True
                                                if default_font:
                                                    cover_config["default_font"] = {
                                                        **default_font,
                                                        **cover_config.get("default_font", {}),
                                                    }
                                                if text_position:
                                                    cover_config["text_position"] = {
                                                        **text_position,
                                                        **cover_config.get("text_position", {}),
                                                    }
                                                print(
                                                    f"  Adding cover for {tab_name} -> {subsection_name} -> "
                                                    f"{sub_subsection_name} -> {child_name} (page {page_index}) "
                                                    f"on page {page_num + 1}"
                                                )
                                                self.add_cover_page(
                                                    doc[page_num],
                                                    cover_config,
                                                    self.page_width,
                                                    self.page_height,
                                                    child_name,
                                                )
                                continue
                            
                            # Check if sub_subsection_config has page_1, page_2, etc. structure
                            if isinstance(sub_subsection_config, dict) and any(key.startswith("page_") for key in sub_subsection_config.keys()):
                                # New structure: page_1, page_2, etc.
                                # Iterate through all pages for this sub-subsection
                                for pg_num, pg_info in page_structure.items():
                                    if (pg_info.get("tab_name") == tab_name and 
                                        pg_info.get("subsection") == subsection_name and
                                        pg_info.get("sub_subsection") == sub_subsection_name and
                                        not pg_info.get("sub_subsection_group")):
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
                                                self.add_cover_page(sub_subsection_page, cover_config, self.page_width, self.page_height, sub_subsection_name)
                            else:
                                # Normal sub-subsection handling (single page, no page_1/page_2 structure)
                                # Search page_structure for this sub-subsection
                                found = False
                                for pg_num, pg_info in page_structure.items():
                                    if (pg_info.get("tab_name") == tab_name and 
                                        pg_info.get("subsection") == subsection_name and
                                        pg_info.get("sub_subsection") == sub_subsection_name and
                                        not pg_info.get("sub_subsection_group") and
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
                                            self.add_cover_page(sub_subsection_page, cover_config, self.page_width, self.page_height, sub_subsection_name)
                                            found = True
                                        break
                                if not found:
                                    print(f"  Warning: Could not find page for {tab_name} -> {subsection_name} -> {sub_subsection_name}")
            
            # Track which pages have cover pages
            pages_with_covers = set()
            if cover_pages_config:
                cover_pages = cover_pages_config.get("cover_pages", {})
                
                # Track title page
                if "title_page" in cover_pages:
                    pages_with_covers.add(0)  # Title page is page 1 (0-based index 0)
                
                # Track tab cover pages
                for tab in tabs:
                    tab_name = tab.get("name")
                    target_page_num = tab.get("target_page", 1) - 1
                    if tab_name in cover_pages and 0 <= target_page_num < total_pages:
                        tab_cover_config = cover_pages[tab_name]
                        # Multi-page tabs (page_1, page_2, …): track all tab pages, not just the first
                        if isinstance(tab_cover_config, dict) and any(key.startswith("page_") for key in tab_cover_config.keys()):
                            for pg_num, pg_info in page_structure.items():
                                if (pg_info.get("tab_name") == tab_name and
                                    pg_info.get("subsection") is None and
                                    pg_info.get("sub_subsection") is None):
                                    page_num = int(pg_num) - 1
                                    if 0 <= page_num < total_pages:
                                        pages_with_covers.add(page_num)
                        else:
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
                                if isinstance(sub_subsection_config, dict) and self.is_nested_group_config(sub_subsection_config):
                                    for pg_num, pg_info in page_structure.items():
                                        if (
                                            pg_info.get("tab_name") == tab_name
                                            and pg_info.get("subsection") == subsection_name
                                            and pg_info.get("sub_subsection_group") == sub_subsection_name
                                        ):
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                pages_with_covers.add(page_num)
                                    continue
                                # Check if sub_subsection_config has page_1, page_2, etc. structure
                                if isinstance(sub_subsection_config, dict) and any(key.startswith("page_") for key in sub_subsection_config.keys()):
                                    # Track all pages for this sub-subsection (including page_1, page_2, etc.)
                                    for pg_num, pg_info in page_structure.items():
                                        if (pg_info.get("tab_name") == tab_name and 
                                            pg_info.get("subsection") == subsection_name and
                                            pg_info.get("sub_subsection") == sub_subsection_name and
                                            not pg_info.get("sub_subsection_group")):
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                pages_with_covers.add(page_num)
                                else:
                                    # Old structure: single page
                                    for pg_num, pg_info in page_structure.items():
                                        if (pg_info.get("tab_name") == tab_name and 
                                            pg_info.get("subsection") == subsection_name and
                                            pg_info.get("sub_subsection") == sub_subsection_name and
                                            not pg_info.get("sub_subsection_group") and
                                            pg_info.get("page_index", 1) == 1):
                                            page_num = int(pg_num) - 1
                                            if 0 <= page_num < total_pages:
                                                pages_with_covers.add(page_num)
                                            break
            
            # Add random dossier background to all pages without cover pages
            # Special handling: "Regeln" section uses assets/images/background/rules/
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dossier_images = self._get_dossier_images()
            background_dir = os.path.join(script_dir, "assets", "images", "background")
            if not os.path.exists(background_dir):
                background_dir = os.path.join(os.getcwd(), "assets", "images", "background")
            
            rules_background_dir = os.path.join(background_dir, "rules")
            
            # Find all background images (excluding rules subdirectory) - legacy fallback only
            background_images = []
            if os.path.exists(background_dir):
                for ext in ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
                    all_images = glob.glob(os.path.join(background_dir, ext))
                    background_images.extend([img for img in all_images if os.path.dirname(img) == background_dir])
                background_images.sort()
            
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
            
            if dossier_images or background_images or rules_background_images:
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
                                bg_image_path = self._pick_random_avoiding_consecutive(rules_background_images)
                                pages_with_rules_bg += 1
                            elif is_npcs_section:
                                # For NPCs section, use npc_2.png as default background
                                npc_2_path = os.path.join(script_dir, "assets", "images", "section_cover", "npc_2.png")
                                if not os.path.exists(npc_2_path):
                                    npc_2_path = os.path.join(os.getcwd(), "assets", "images", "section_cover", "npc_2.png")
                                if os.path.exists(npc_2_path):
                                    bg_image_path = npc_2_path
                                    self._last_random_image = npc_2_path
                                elif dossier_images:
                                    bg_image_path = self._pick_random_avoiding_consecutive(dossier_images)
                                elif background_images:
                                    bg_image_path = self._pick_random_avoiding_consecutive(background_images)
                                else:
                                    continue  # Skip if no backgrounds available
                            elif dossier_images:
                                bg_image_path = self._pick_random_avoiding_consecutive(dossier_images)
                            elif background_images:
                                bg_image_path = self._pick_random_avoiding_consecutive(background_images)
                            else:
                                continue  # Skip if no backgrounds available
                            
                            if not bg_image_path:
                                continue
                            
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
                print("Warning: No dossier images found in assets/images/dossier/, skipping background addition")
        
        print("Drawing modern tab tabs...")
        self._tab_label_anchor_cache = {}
        # Draw modern tabs on all pages (skip title page on page 1)
        start_page = 0
        if cover_pages_config:
            cover_pages = cover_pages_config.get("cover_pages", {})
            if "title_page" in cover_pages:
                start_page = 1  # Skip title page
        
        for page_num in range(start_page, total_pages):
            target_page = doc[page_num]
            self.add_tabs_to_page(target_page, page_num + 1, tabs, tab_text_elements, page_structure)
        
        # Draw upper tabs (left top) if we have the structure
        if page_structure and tab_subsections and metadata:
            print("Drawing upper tabs (left top)...")
            start_page = 0
            if cover_pages_config:
                cover_pages = cover_pages_config.get("cover_pages", {})
                if "title_page" in cover_pages:
                    start_page = 1  # Skip title page
            
            for page_num in range(start_page, total_pages):
                page_info = page_structure.get(page_num + 1)
                # Skip upper tabs if page has no_upper_tabs flag or is title page
                if page_info and (page_info.get("no_upper_tabs") or page_info.get("is_title_page")):
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
