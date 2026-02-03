#!/usr/bin/env python3
"""
Extract pages from PDF, remove tabs (top and bottom), and save as PNGs
named after the active tabs extracted directly from the PDF (e.g., "Eskalation", "Würfelsystem", "Maskeradebruch").
Names are extracted using visual tab detection from the PDF itself.
"""

import fitz  # PyMuPDF
import os
import re
import json
from typing import Optional, List, Dict, Tuple


def sanitize_filename(name: str) -> str:
    """Convert tab name to a valid filename"""
    # Replace Umlaute and special characters
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss',
        ' ': '_',  # Replace spaces with underscores
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces, dots, and underscores
    name = name.strip('. _')
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name if name else "page"


def get_tab_color_from_pixel(pixel_value) -> str:
    """Determine if a pixel color matches active or inactive tab color"""
    # Handle different pixel return types
    if isinstance(pixel_value, int):
        # Single integer: extract RGB
        r = (pixel_value >> 16) & 0xFF
        g = (pixel_value >> 8) & 0xFF
        b = pixel_value & 0xFF
    elif isinstance(pixel_value, (tuple, list)) and len(pixel_value) >= 3:
        r, g, b = pixel_value[0], pixel_value[1], pixel_value[2]
    else:
        return "other"
    
    # Active tab: #D0C4B4 = RGB(208, 196, 180) - dunkleres Grau/Beige
    # Inactive tab: #EEDCC8 = RGB(238, 220, 200) - helleres Beige
    # But PDF rendering might show different values, so we check brightness
    
    brightness = (r + g + b) / 3
    
    # Active tabs are darker (lower brightness)
    # Inactive tabs are lighter (higher brightness)
    # Threshold around 220-230
    
    if brightness < 220:  # Darker = likely active
        return "active"
    elif brightness > 230:  # Lighter = likely inactive
        return "inactive"
    else:
        # Middle range - check if it's more gray (active) or beige (inactive)
        # Active tabs are more gray (R≈G≈B), inactive are more beige (R>G>B)
        gray_diff = max(abs(r-g), abs(g-b), abs(r-b))
        if gray_diff < 15:  # Very gray = likely active
            return "active"
        else:
            return "inactive"


def calculate_page_structure_from_json(structure: Dict) -> Dict:
    """
    Calculate page structure from JSON (same logic as journal_generator.py).
    Uses target_page from upper_tabs to map to actual PDF page numbers.
    Returns: page_structure dict mapping page_num -> {tab_name, subsection, sub_subsection}
    """
    right_tabs_data = structure.get("right_tabs", [])
    upper_tabs = structure.get("upper_tabs", [])
    
    # Create mapping from tab name to target_page
    tab_to_target_page = {}
    for tab in upper_tabs:
        tab_name = tab.get("name", "")
        target_page = tab.get("target_page")
        if target_page:
            tab_to_target_page[tab_name] = target_page
    
    # Also check right_tabs for target_page
    for tab_data in right_tabs_data:
        tab_name = tab_data.get("name", "")
        target_page = tab_data.get("target_page")
        if target_page and tab_name not in tab_to_target_page:
            tab_to_target_page[tab_name] = target_page
    
    page_structure = {}
    
    for tab_data in right_tabs_data:
        tab_name = tab_data.get("name", "")
        subsections = tab_data.get("subsections_left_top_tabs", [])
        
        # Get starting page from target_page mapping, or calculate sequentially
        if tab_name in tab_to_target_page:
            current_page = tab_to_target_page[tab_name]
        else:
            # Fallback: use first available page (shouldn't happen with proper JSON)
            current_page = 1
        
        # First page is the main tab page
        page_structure[current_page] = {
            "tab_name": tab_name,
            "subsection": None,
            "sub_subsection": None
        }
        current_page += 1
        
        # Then pages for each subsection
        for subsection in subsections:
            subsection_name = subsection.get("name", "")
            
            # Get sub-subsections (can be "seconnd_subsections_left_tabs" or "sub_subsections")
            sub_subsections = subsection.get("seconnd_subsections_left_tabs", [])
            if not sub_subsections:
                sub_subsections = subsection.get("sub_subsections", [])
            
            # First page for subsection itself
            page_structure[current_page] = {
                "tab_name": tab_name,
                "subsection": subsection_name,
                "sub_subsection": None,
                "page_index": 1
            }
            current_page += 1
            
            # Check if subsection has page_count > 1
            page_count = subsection.get("page_count", 1)
            if page_count > 1:
                for page_idx in range(2, page_count + 1):
                    page_structure[current_page] = {
                        "tab_name": tab_name,
                        "subsection": subsection_name,
                        "sub_subsection": None,
                        "page_index": page_idx
                    }
                    current_page += 1
            
            # Then pages for each sub-subsection
            for sub_subsection in sub_subsections:
                page_structure[current_page] = {
                    "tab_name": tab_name,
                    "subsection": subsection_name,
                    "sub_subsection": sub_subsection
                }
                current_page += 1
        
        # If no subsections, check for direct second-level subsections
        if not subsections:
            if "seconnd_subsections_left_tabs" in tab_data:
                for sub_subsection in tab_data["seconnd_subsections_left_tabs"]:
                    page_structure[current_page] = {
                        "tab_name": tab_name,
                        "subsection": None,
                        "sub_subsection": sub_subsection
                    }
                    current_page += 1
    
    return page_structure


def get_page_name_from_structure(page_structure: Dict, page_num: int) -> Optional[str]:
    """
    Get the page name from page_structure.
    Priority: sub_subsection > subsection > tab_name
    If page_num not in structure, try to find by matching active tabs.
    """
    page_info = page_structure.get(page_num)
    if not page_info:
        # Page not in structure - return None, will use visual detection as fallback
        return None
    
    # Priority: sub_subsection > subsection > tab_name
    if page_info.get("sub_subsection"):
        name = page_info["sub_subsection"]
        # Clean up compound names
        if " & " in name:
            name = name.split(" & ")[0].strip()
        elif " und " in name.lower():
            parts = name.split(" und ", 1)
            if len(parts) > 1 and len(parts[0].strip()) >= 4:
                name = parts[0].strip()
        return name
    elif page_info.get("subsection"):
        return page_info["subsection"]
    elif page_info.get("tab_name"):
        return page_info["tab_name"]
    
    return None


def find_name_in_structure(structure: Dict, tab_name: str, subsection_name: Optional[str] = None, sub_subsection_name: Optional[str] = None) -> Optional[str]:
    """
    Find a name in the JSON structure given tab/subsection/sub_subsection names.
    Returns the sub_subsection name if found, otherwise subsection, otherwise tab_name.
    """
    right_tabs_data = structure.get("right_tabs", [])
    
    for tab_data in right_tabs_data:
        if tab_data.get("name") != tab_name:
            continue
        
        # If we have a sub_subsection, find it
        if sub_subsection_name:
            subsections = tab_data.get("subsections_left_top_tabs", [])
            for subsection in subsections:
                if subsection.get("name") == subsection_name:
                    sub_subsections = subsection.get("seconnd_subsections_left_tabs", [])
                    if not sub_subsections:
                        sub_subsections = subsection.get("sub_subsections", [])
                    if sub_subsection_name in sub_subsections:
                        name = sub_subsection_name
                        # Clean up compound names
                        if " & " in name:
                            name = name.split(" & ")[0].strip()
                        elif " und " in name.lower():
                            parts = name.split(" und ", 1)
                            if len(parts) > 1 and len(parts[0].strip()) >= 4:
                                name = parts[0].strip()
                        return name
        
        # If we have a subsection, return it
        if subsection_name:
            subsections = tab_data.get("subsections_left_top_tabs", [])
            for subsection in subsections:
                if subsection.get("name") == subsection_name:
                    return subsection_name
        
        # Otherwise return tab name
        return tab_name
    
    return None


def extract_page_title(page: fitz.Page, page_width: float, page_height: float) -> Optional[str]:
    """
    Einfach: Finde die grauen (aktiven) Tabs oben, nimm den Namen.
    Returns names like "Eskalation", "Würfelsystem", "Maskeradebruch", etc.
    """
    # Tab-Bereich oben: x von 10 bis ~500, y von 20 bis ~100
    tab_area_rect = fitz.Rect(10, 20, min(500, page_width - 50), 100)
    
    # Render Tab-Bereich für Farbanalyse
    try:
        tab_pix = page.get_pixmap(clip=tab_area_rect, matrix=fitz.Matrix(2, 2))
    except:
        return None
    
    # Text aus Tab-Bereich extrahieren
    text_dict = page.get_text("dict", clip=tab_area_rect)
    
    active_tabs = []
    
    # Durch alle Text-Spans gehen
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text or len(text) < 2:
                    continue
                
                bbox = span.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = bbox
                
                # Nur Tabs im Tab-Bereich
                if not (10 <= x0 <= 500 and 20 <= y0 <= 100):
                    continue
                
                # Prüfe ob Tab aktiv (grau) ist
                pix_x0 = int((x0 - 10) * 2)
                pix_y0 = int((y0 - 20) * 2)
                pix_x1 = int((x1 - 10) * 2)
                pix_y1 = int((y1 - 20) * 2)
                
                # Pixel um den Text herum prüfen
                active_count = 0
                total_count = 0
                
                for py in range(max(0, pix_y0 - 3), min(tab_pix.height, pix_y1 + 3), 3):
                    for px in range(max(0, pix_x0 - 2), min(tab_pix.width, pix_x1 + 2), 3):
                        try:
                            pixel = tab_pix.pixel(px, py)
                            color_type = get_tab_color_from_pixel(pixel)
                            total_count += 1
                            if color_type == "active":
                                active_count += 1
                        except:
                            pass
                
                # Tab ist aktiv wenn mehr als 26% aktive Pixel (erste Reihe)
                # Oder mehr als 20% aktive Pixel (zweite Reihe - niedrigere Schwelle für Subsection-Tabs)
                if total_count > 0:
                    ratio = active_count / total_count
                    threshold = 0.20 if y0 > 50 else 0.26  # Niedrigere Schwelle für zweite Reihe
                    if ratio > threshold:
                        active_tabs.append({
                            "text": text,
                            "y0": y0,
                            "x0": x0,
                            "width": x1 - x0,
                            "ratio": ratio  # Speichere Ratio für später
                        })
    
    # Wenn aktive Tabs gefunden: Intelligente Auswahl
    if active_tabs:
        second_row = [t for t in active_tabs if t["y0"] > 50]
        first_row = [t for t in active_tabs if t["y0"] <= 50]
        
        if second_row:
            # Zweite Reihe: nimm den kleinsten (spezifischsten) Tab
            # Wenn gleich groß, nimm den mit höchster Ratio
            # Wenn Ratios gleich, nimm den rechten
            second_row.sort(key=lambda t: (t["width"], -t.get("ratio", 0), -t.get("x0", 0)))
            name = second_row[0]["text"]
        elif first_row:
            # Nur erste Reihe: nimm den mit höchster Ratio
            # Wenn Ratios gleich, nimm den rechten
            first_row.sort(key=lambda t: (-t.get("ratio", 0), -t.get("x0", 0)))
            name = first_row[0]["text"]
        else:
            # Fallback: höchste Ratio
            active_tabs.sort(key=lambda t: -t.get("ratio", 0))
            name = active_tabs[0]["text"]
        
        # Namen bereinigen
        if " & " in name:
            name = name.split(" & ")[0].strip()
        elif " und " in name.lower():
            parts = name.split(" und ", 1)
            if len(parts) > 1 and len(parts[0].strip()) >= 4:
                name = parts[0].strip()
        
        return name
    
    return None


def crop_page_content(page: fitz.Page, page_width: float, page_height: float) -> fitz.Rect:
    """
    Calculate the crop box to remove tabs:
    - Top: ~100pt (to remove upper tabs completely)
    - Bottom: ~50pt (to remove bottom tabs if any)
    - Right: ~60pt (to remove right tabs completely)
    - Left: ~5pt (to trim left margin)
    """
    top_margin = 100.0  # Increased to remove all top tabs (was 90pt)
    bottom_margin = -150.0  # Reduced by 200px: was 50.0, now -150.0 (keeps more bottom content)
    right_margin = 60.0  # Right margin (was 65pt, reduced by 5pt)
    left_margin = 7.0  # Trim left margin (was 5pt)
    
    crop_rect = fitz.Rect(
        left_margin,
        top_margin,
        page_width - right_margin,
        page_height - bottom_margin
    )
    
    return crop_rect


def find_regeln_start_page(doc, json_path: Optional[str] = None) -> int:
    """
    Find the page number where "Regeln" tab starts.
    First tries to load from JSON, then falls back to visual detection.
    Returns 1-based page number (1 = first page).
    """
    # Try to load from JSON first
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            
            # Check upper_tabs for "Regeln"
            upper_tabs = structure.get("upper_tabs", [])
            for tab in upper_tabs:
                if tab.get("name") == "Regeln":
                    target_page = tab.get("target_page")
                    if target_page:
                        print(f"Found 'Regeln' tab at page {target_page} from JSON")
                        return target_page
            
            # Also check right_tabs
            right_tabs = structure.get("right_tabs", [])
            for tab in right_tabs:
                if tab.get("name") == "Regeln":
                    target_page = tab.get("target_page")
                    if target_page:
                        print(f"Found 'Regeln' tab at page {target_page} from JSON")
                        return target_page
        except Exception as e:
            print(f"Warning: Could not load JSON structure: {e}")
    
    # Fallback: Visual detection - search for "Regeln" tab in right tabs
    print("Searching for 'Regeln' tab visually...")
    page_width = doc[0].rect.width
    page_height = doc[0].rect.height
    
    # Right tabs area: right side of page, vertical
    right_tab_area = fitz.Rect(page_width - 60, 0, page_width, page_height)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_index = page_num + 1
        
        # Extract text from right tab area
        text_dict = page.get_text("dict", clip=right_tab_area)
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text == "Regeln":
                        print(f"Found 'Regeln' tab visually at page {page_index}")
                        return page_index
    
    # If not found, default to page 1 (extract all)
    print("Warning: 'Regeln' tab not found, extracting from page 1")
    return 1


def extract_pages_from_pdf(pdf_path: str, output_dir: str = "extracted_pages", json_path: Optional[str] = None):
    """
    Extract all pages from PDF starting from "Regeln" tab, remove tabs, and save as PNGs.
    Extracts page names directly from PDF using visual tab detection.
    JSON is optional and used to find the "Regeln" tab start page.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Open PDF
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # Find start page (where "Regeln" tab begins)
    # Default json_path if not provided
    if not json_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_json = os.path.join(script_dir, "tab_structure.json")
        if os.path.exists(default_json):
            json_path = default_json
    
    start_page = find_regeln_start_page(doc, json_path)
    start_page_index = start_page - 1  # Convert to 0-based index
    
    print(f"\nExtracting pages starting from 'Regeln' tab (page {start_page})...")
    print(f"Total pages in PDF: {total_pages}")
    print(f"Pages to extract: {total_pages - start_page_index}")
    print(f"Output directory: {output_dir}")
    
    page_width = doc[0].rect.width
    page_height = doc[0].rect.height
    
    print(f"Page dimensions: {page_width} x {page_height} points\n")
    
    extracted_count = 0
    for page_num in range(start_page_index, total_pages):
        page = doc[page_num]
        page_index = page_num + 1
        
        # Einfach nach Seitenzahl benennen
        filename = f"page_{page_index:04d}"
        
        # 3. Bild beschneiden
        crop_rect = crop_page_content(page, page_width, page_height)
        
        # 4. Bild rendern
        zoom = 2.5
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=crop_rect)
        
        # 5. Bild speichern
        output_path = os.path.join(output_dir, f"{filename}.png")
        pix.save(output_path)
        
        extracted_count += 1
        print(f"  Page {page_index:4d}/{total_pages}: {filename}.png")
    
    doc.close()
    print(f"\nDone! Extracted {extracted_count} pages (from page {start_page} onwards) to {output_dir}/")


if __name__ == "__main__":
    import sys
    
    pdf_path = "vampire_journal.pdf"
    output_dir = "extracted_pages"
    json_path = None  # Optional, defaults to tab_structure.json in same directory
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        json_path = sys.argv[3]
    
    extract_pages_from_pdf(pdf_path, output_dir, json_path)
