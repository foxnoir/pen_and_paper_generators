#!/usr/bin/env python3
"""
Dynamic PDF Generator for Vampire Journal
Main orchestrator that combines content processing and layout generation.
Dynamically builds pages from JSON structure without destroying layout.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Tuple
import os
import json
from layout_generator import LayoutGenerator
from content_processor import ContentProcessor


class DynamicPDFGenerator:
    """Generates the PDF dynamically from JSON structure"""
    
    def __init__(self):
        self.page_width = 595.2755737304688  # A4 width in points
        self.page_height = 841.8897705078125  # A4 height in points
        
        # Initialize layout and content processors
        self.layout_generator = LayoutGenerator(self.page_width, self.page_height)
        self.content_processor = ContentProcessor(self.page_width, self.page_height)
        
        # Will be populated from JSON
        self.tabs = []
        self.page_structure = {}  # Maps page_num -> {tab_name, subsection, sub_subsection}
        self.tab_subsections = {}  # Maps tab_name -> {subsections_left_top_tabs, ...}
    
    def load_structure_from_json(self, json_path: str) -> Dict:
        """Loads tab structure from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate_pages_from_structure(self, structure: Dict, cover_pages_config: Dict = None) -> Tuple[List[Dict], Dict, Dict]:
        """
        Calculates page structure from JSON and returns tabs with target pages
        Returns: (tabs_list, page_structure_dict, tab_subsections_dict)
        """
        right_tabs_data = structure.get("right_tabs", [])
        metadata = structure.get("metadata", {})
        
        # Load cover_pages.json if not provided
        if cover_pages_config is None:
            json_path = getattr(self, '_json_path', None)
            if json_path:
                cover_pages_path = os.path.join(os.path.dirname(json_path), "cover_pages.json")
                if os.path.exists(cover_pages_path):
                    with open(cover_pages_path, 'r', encoding='utf-8') as f:
                        cover_pages_config = json.load(f)
        
        # Get sub_subsections config if available
        sub_subsections_config = None
        subsections_config = None
        if cover_pages_config:
            sub_subsections_config = cover_pages_config.get("cover_pages", {}).get("sub_subsections", {})
            subsections_config = cover_pages_config.get("cover_pages", {}).get("subsections", {})
        
        # Update dimensions from metadata if available
        if "page_width" in metadata:
            self.page_width = metadata["page_width"]
        if "page_height" in metadata:
            self.page_height = metadata["page_height"]
        
        # Reinitialize layout generator with correct dimensions
        self.layout_generator = LayoutGenerator(self.page_width, self.page_height)
        
        # Update tab width and position from metadata
        if "tab_width" in metadata:
            self.layout_generator.tab_width = metadata["tab_width"]
        if "right_tab_x_position" in metadata:
            self.layout_generator.tab_x = metadata["right_tab_x_position"]
        
        tabs = []
        page_structure = {}
        tab_subsections = {}  # Store subsections for each tab
        current_page = 1
        
        # Calculate Y positions dynamically based on tabs from JSON
        start_y = 65.0
        tab_spacing = 8.0
        base_height = 70.0
        
        current_y = start_y
        
        for tab_data in right_tabs_data:
            # Read tab name directly from JSON (no hardcoded names!)
            tab_name = tab_data.get("name", "")
            
            # Get y_position from JSON if available, otherwise use current_y (calculated from previous tab)
            y_position = tab_data.get("y_position")
            if y_position is not None:
                current_y = y_position
            # If no y_position in JSON, current_y is already set from previous iteration
            
            # Get height from JSON if available, otherwise calculate based on name length
            height = tab_data.get("height")
            if height is None:
                # Calculate height based on name length (fallback)
                if len(tab_name) > 20:  # Very long names like "Intrigen & Interessen"
                    height = 110.0
                elif len(tab_name) > 15:
                    height = 85.0
                else:
                    height = base_height
            
            # Calculate pages for this tab
            subsections = tab_data.get("subsections_left_top_tabs", [])
            
            # Check if tab has page_count (for tabs without subsections, like Handouts, Notizen)
            tab_page_count = tab_data.get("page_count", 1)
            
            # First page is the main tab page - this is the target_page for the tab
            target_page = current_page
            page_structure[current_page] = {
                "tab_name": tab_name,
                "subsection": None,
                "sub_subsection": None,
                "page_index": 1
            }
            current_page += 1
            
            # Add additional pages if tab has page_count > 1 (for tabs with or without subsections)
            if tab_page_count > 1:
                for page_idx in range(2, tab_page_count + 1):
                    page_structure[current_page] = {
                        "tab_name": tab_name,
                        "subsection": None,
                        "sub_subsection": None,
                        "page_index": page_idx
                    }
                    current_page += 1
            
            # Then pages for each subsection
            for subsection in subsections:
                subsection_name = subsection.get("name", "")
                
                # Get sub-subsections (can be "seconnd_subsections_left_tabs" or "sub_subsections")
                sub_subsections = subsection.get("seconnd_subsections_left_tabs", [])
                if not sub_subsections:
                    sub_subsections = subsection.get("sub_subsections", [])
                
                # Check if this is Ghule, Menschen, or Garou subsection (should have pages, even without sub-subsections)
                is_ghule_subsection = (tab_name == "NPCs" and subsection_name == "Ghule")
                is_menschen_subsection = (tab_name == "NPCs" and subsection_name == "Menschen")
                is_garou_subsection = (tab_name == "NPCs" and subsection_name == "Garou")
                
                if is_ghule_subsection:
                    # Generate 9 pages for Ghule subsection:
                    # page_1: ghule info sheet
                    # page_2,4,6,8: ghule.png sheet (as image with basic.png background)
                    # page_3,5,7,9: basic_npc (page_9 without upper tabs)
                    for page_idx in range(1, 10):  # page_index 1-9
                        page_structure[current_page] = {
                            "tab_name": tab_name,
                            "subsection": subsection_name,
                            "sub_subsection": None,
                            "page_index": page_idx,
                            "no_upper_tabs": (page_idx == 9)  # Last page has no upper tabs
                        }
                        current_page += 1
                elif is_menschen_subsection:
                    # Generate 5 pages for Menschen subsection (all basic_npc, last without upper tabs)
                    for page_idx in range(1, 6):  # page_index 1-5
                        page_structure[current_page] = {
                            "tab_name": tab_name,
                            "subsection": subsection_name,
                            "sub_subsection": None,
                            "page_index": page_idx,
                            "no_upper_tabs": (page_idx == 5)  # Last page has no upper tabs
                        }
                        current_page += 1
                elif is_garou_subsection:
                    # Read pages from cover_pages.json subsections config
                    if subsections_config:
                        tab_config = subsections_config.get(tab_name, {})
                        subsection_config = tab_config.get(subsection_name, {})
                        if isinstance(subsection_config, dict):
                            # Count pages (page_1, page_2, etc.)
                            page_keys = [k for k in subsection_config.keys() if k.startswith("page_")]
                            if page_keys:
                                # Extract page numbers and sort
                                page_numbers = []
                                for key in page_keys:
                                    try:
                                        num = int(key.split("_")[1])
                                        page_numbers.append(num)
                                    except:
                                        pass
                                if page_numbers:
                                    max_page = max(page_numbers)
                                    for page_idx in range(1, max_page + 1):
                                        page_structure[current_page] = {
                                            "tab_name": tab_name,
                                            "subsection": subsection_name,
                                            "sub_subsection": None,
                                            "page_index": page_idx
                                        }
                                        current_page += 1
                                    continue
                    # Fallback: Generate 2 pages if config not found
                    for page_idx in range(1, 3):  # page_index 1-2
                        page_structure[current_page] = {
                            "tab_name": tab_name,
                            "subsection": subsection_name,
                            "sub_subsection": None,
                            "page_index": page_idx
                        }
                        current_page += 1
                else:
                    # First page for subsection itself
                    page_structure[current_page] = {
                        "tab_name": tab_name,
                        "subsection": subsection_name,
                        "sub_subsection": None,
                        "page_index": 1
                    }
                    current_page += 1
                    
                    # Check if subsection has page_count > 1 (for multiple pages like Kalender)
                    page_count = subsection.get("page_count", 1)
                    if page_count > 1:
                        # Add additional pages for this subsection
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
                    # Check if this is a NPCs subsection (Camarilla, Sabbat, Anarchen, Unabhängige, Blutlinien)
                    # that should have multiple pages
                    is_npc_subsection = (tab_name == "NPCs" and 
                                        subsection_name in ["Camarilla", "Sabbat", "Anarchen", "Unabhängige", "Blutlinien"])
                    
                    # Check if this is Garou sub-subsection (should have multiple pages)
                    is_garou_sub_subsection = (tab_name == "NPCs" and subsection_name == "Garou")
                    
                    if is_npc_subsection:
                        # Generate 11 pages for each NPC sub-subsection:
                        # page_1: clan sheet
                        # page_2,4,6,8,10: random_npc_vampire
                        # page_3,5,7,9,11: basic_npc (page_11 without upper tabs)
                        for page_idx in range(1, 12):  # page_index 1-11
                            page_structure[current_page] = {
                                "tab_name": tab_name,
                                "subsection": subsection_name,
                                "sub_subsection": sub_subsection,
                                "page_index": page_idx,
                                "no_upper_tabs": (page_idx == 11)  # Last page has no upper tabs
                            }
                            current_page += 1
                    elif is_garou_sub_subsection:
                        # Generate pages for each Garou sub-subsection (read from config)
                        # page_1,3,5,7,9: garou.png sheet (as image with basic.png background)
                        # page_2,4,6,8,10: basic_npc (page_10 without upper tabs)
                        for page_idx in range(1, 11):  # page_index 1-10
                            page_structure[current_page] = {
                                "tab_name": tab_name,
                                "subsection": subsection_name,
                                "sub_subsection": sub_subsection,
                                "page_index": page_idx,
                                "no_upper_tabs": (page_idx == 10)  # Last page has no upper tabs
                            }
                            current_page += 1
                    else:
                        # Regular sub-subsection - check if there's a configuration in cover_pages.json
                        # For "Regeln" section, use only the pages defined in config (no minimum)
                        # For other sections, default to 4 pages minimum
                        is_rules_tab = (tab_name == "Regeln")
                        page_count = 4 if not is_rules_tab else 0  # Default: 4 for non-Rules, 0 for Rules
                        
                        if sub_subsections_config:
                            tab_config = sub_subsections_config.get(tab_name, {})
                            subsection_config = tab_config.get(subsection_name, {})
                            sub_subsection_config = subsection_config.get(sub_subsection, {})
                            if isinstance(sub_subsection_config, dict):
                                # Count pages (page_1, page_2, etc.)
                                page_keys = [k for k in sub_subsection_config.keys() if k.startswith("page_")]
                                if page_keys:
                                    # Extract page numbers and find the maximum
                                    page_numbers = []
                                    for key in page_keys:
                                        try:
                                            num = int(key.split("_")[1])
                                            page_numbers.append(num)
                                        except:
                                            pass
                                    if page_numbers:
                                        page_count = max(page_numbers)
                                        # Only enforce minimum of 4 for non-Rules sections
                                        if not is_rules_tab:
                                            page_count = max(page_count, 4)
                        
                        # Only generate pages if page_count > 0 (for Rules, this means config exists)
                        if page_count > 0:
                            for page_idx in range(1, page_count + 1):
                                page_structure[current_page] = {
                                    "tab_name": tab_name,
                                    "subsection": subsection_name,
                                    "sub_subsection": sub_subsection,
                                    "page_index": page_idx
                                }
                                current_page += 1
            
            # If no subsections, still need at least one page
            if not subsections:
                # Check if there are any second-level subsections directly
                if "seconnd_subsections_left_tabs" in tab_data:
                    for sub_subsection in tab_data["seconnd_subsections_left_tabs"]:
                        page_structure[current_page] = {
                            "tab_name": tab_name,
                            "subsection": None,
                            "sub_subsection": sub_subsection
                        }
                        current_page += 1
            
            tabs.append({
                "name": tab_name,  # Name read directly from JSON - no hardcoded names!
                "y": current_y,
                "target_page": target_page,
                "height": height
            })
            
            # Store subsections for this tab (for upper tabs)
            tab_subsections[tab_name] = {
                "subsections": subsections,
                "tab_data": tab_data  # Store full tab_data for access to all fields
            }
            
            # Update current_y for next tab (always, so next tab can use it if no y_position)
            current_y += height + tab_spacing
        
        return tabs, page_structure, tab_subsections
    
    def create_empty_pages(self, doc: fitz.Document, total_pages: int):
        """Creates empty pages with proper dimensions"""
        for _ in range(total_pages):
            page = doc.new_page(width=self.page_width, height=self.page_height)
            # Initialize fonts on the page (needed for new pages)
            # Insert a tiny invisible text to initialize fonts
            try:
                page.insert_text((0, 0), "", fontsize=0.1, fontname='helv', render_mode=3)  # Invisible
                page.insert_text((0, 0), "", fontsize=0.1, fontname='helv-Bold', render_mode=3)  # Invisible
            except:
                pass
    
    def generate_from_json(self, json_path: str, output_path: str, source_pdf_path: str = None):
        """
        Generates PDF dynamically from JSON structure
        
        Args:
            json_path: Path to JSON structure file
            output_path: Output PDF path
            source_pdf_path: Optional source PDF to extract tab text styles from
        """
        print("=" * 60)
        print("DYNAMIC PDF GENERATOR FROM JSON")
        print("=" * 60)
        print()
        
        # Load structure from JSON
        print(f"Loading structure from {json_path}...")
        structure = self.load_structure_from_json(json_path)
        
        # Load cover pages configuration if available (needed for page count calculation)
        cover_pages_config = None
        cover_pages_path = os.path.join(os.path.dirname(json_path), "cover_pages.json")
        if os.path.exists(cover_pages_path):
            print(f"Loading cover pages configuration from {cover_pages_path}...")
            with open(cover_pages_path, 'r', encoding='utf-8') as f:
                cover_pages_config = json.load(f)
        
        # Store json_path for later use
        self._json_path = json_path
        
        # Calculate page structure and tabs (pass cover_pages_config to determine page counts)
        print("Calculating page structure from JSON...")
        self.tabs, self.page_structure, self.tab_subsections = self.calculate_pages_from_structure(structure, cover_pages_config)
        
        total_pages = max(self.page_structure.keys()) if self.page_structure else 1
        
        print(f"Total pages needed: {total_pages}")
        print("Tab positions and sizes:")
        for tab in self.tabs:
            print(f"  {tab['name']:25s} -> page {tab['target_page']:3d}, Y={tab['y']:6.1f}, height={tab['height']:5.1f}")
        
        # Create new PDF
        doc = fitz.open()
        
        # Create empty pages
        print("Creating empty pages...")
        self.create_empty_pages(doc, total_pages)
        
        # Extract tab text elements from source PDF if available (for font styling only)
        # DO NOT overwrite tab names from JSON - use names directly from JSON!
        tab_text_elements = None
        if source_pdf_path and os.path.exists(source_pdf_path):
            print("Extracting tab text styles from source PDF (for font styling only)...")
            source_doc = fitz.open(source_pdf_path)
            if len(source_doc) > 0:
                source_page_0 = source_doc[0]
                tab_text_elements = self.content_processor.extract_tab_text_elements(source_page_0)
                # Match tab_text_elements to JSON tabs by position, but keep JSON names
                if tab_text_elements and len(tab_text_elements) >= len(self.tabs):
                    # Update font info but keep JSON names
                    for i, tab in enumerate(self.tabs):
                        if i < len(tab_text_elements):
                            # Keep the name from JSON, just update font styling info if needed
                            pass  # Names stay from JSON!
            source_doc.close()
        
        # Apply layout (tabs) - this preserves layout!
        print("Applying layout (tabs)...")
        metadata = structure.get("metadata", {})
        self.layout_generator.apply_layout_to_pdf(doc, self.tabs, tab_text_elements, self.page_structure, self.tab_subsections, metadata, cover_pages_config)
        
        # Save PDF with compression
        print(f"Saving PDF: {output_path}")
        # Enable maximum compression to reduce file size
        doc.save(
            output_path,
            deflate=True,  # Compress PDF streams
            deflate_images=True,  # Compress images
            deflate_fonts=True,  # Compress fonts
            garbage=4,  # Maximum garbage collection
            clean=True,  # Clean up unused objects
            ascii=False,  # Binary format (smaller)
            no_new_id=True,  # Don't create new ID (smaller)
            encryption=0  # No encryption (smaller)
        )
        doc.close()
        
        print(f"\n✓ PDF successfully generated: {output_path}")
        print(f"  - Total pages: {total_pages}")
        print(f"  - Tabs: {len(self.tabs)}")
        print(f"\nThe PDF structure is now dynamically built from JSON!")
        print(f"\nStructure documentation:")
        print(f"  - Tab positions: {self.layout_generator.tab_x} (x), heights: {[t['y'] for t in self.tabs]}")
        print(f"  - Page structure: {len(self.page_structure)} pages mapped")
        
        return output_path
    
    def generate_from_source(self, source_path: str, output_path: str):
        """Generates PDF based on original PDF (legacy method)"""
        print("=" * 60)
        print("DYNAMIC PDF GENERATOR")
        print("=" * 60)
        print()
        
        # Load original PDF
        source_doc = fitz.open(source_path)
        
        # Create new PDF
        doc = fitz.open()
        
        print("Extracting tab labels from original...")
        
        # Extract tab texts from the first page of the original PDF
        source_page_0 = source_doc[0]
        tab_texts = self.content_processor.extract_tab_texts(source_page_0)
        tab_text_elements = self.content_processor.extract_tab_text_elements(source_page_0)
        
        # Initialize tabs with default structure
        self.tabs = [
            {"name": "Domäne", "y": 65.0, "target_page": 1, "height": 70.0},
            {"name": "Intrigen & Interessen", "y": 143.0, "target_page": 11, "height": 110.0},
            {"name": "Runden", "y": 261.0, "target_page": 23, "height": 70.0},
            {"name": "NPCs", "y": 339.0, "target_page": 90, "height": 70.0},
            {"name": "Orte", "y": 417.0, "target_page": 81, "height": 70.0},
            {"name": "Karten", "y": 495.0, "target_page": 30, "height": 70.0},
            {"name": "Handouts", "y": 573.0, "target_page": 93, "height": 70.0},
            {"name": "Notizen", "y": 651.0, "target_page": 94, "height": 70.0},
            {"name": "Regeln", "y": 729.0, "target_page": 95, "height": 70.0},
        ]
        
        # Update tab names with original texts if available
        if len(tab_texts) >= len(self.tabs):
            # Create mapping from tab names to target_page
            name_to_target = {
                "Domäne": 1,
                "Intrigen & Interessen": 11,
                "Runden": 23,
                "NPCs": 90,
                "Orte": 81,
                "Karten": 30,
                "Handouts": 93,
                "Notizen": 94,
                "Regeln": 95
            }
            
            for i, tab in enumerate(self.tabs):
                if i < len(tab_texts):
                    extracted_name = tab_texts[i]
                    tab["name"] = extracted_name
                    if extracted_name in name_to_target:
                        tab["target_page"] = name_to_target[extracted_name]
                        print(f"  Tab '{extracted_name}' -> page {name_to_target[extracted_name]}")
            print(f"  Found: {len(tab_texts)} tab labels")
        else:
            print(f"  Warning: Only {len(tab_texts)} tab texts found, using default names")
        
        # Copy pages from source (content processing)
        total_pages = self.content_processor.copy_pages_from_source(source_doc, doc)
        
        # Apply layout (tabs)
        self.layout_generator.apply_layout_to_pdf(doc, self.tabs, tab_text_elements)
        
        # Process links (content processing)
        self.content_processor.process_links(source_doc, doc, self.layout_generator, total_pages)
        
        source_doc.close()
        
        # Save PDF with compression
        print(f"Saving PDF: {output_path}")
        # Enable maximum compression to reduce file size
        doc.save(
            output_path,
            deflate=True,  # Compress PDF streams
            deflate_images=True,  # Compress images
            deflate_fonts=True,  # Compress fonts
            garbage=4,  # Maximum garbage collection
            clean=True,  # Clean up unused objects
            ascii=False,  # Binary format (smaller)
            no_new_id=True,  # Don't create new ID (smaller)
            encryption=0  # No encryption (smaller)
        )
        doc.close()
        
        print(f"\n✓ PDF successfully generated: {output_path}")
        print(f"  - Total pages: {total_pages}")
        print(f"  - Tabs: {len(self.tabs)}")
        print(f"\nThe PDF can now be modified via script!")
        print(f"\nStructure documentation:")
        print(f"  - Tab positions: {self.layout_generator.tab_x} (x), heights: {[t['y'] for t in self.tabs]}")
        
        return output_path


def main():
    """Main function"""
    generator = DynamicPDFGenerator()
    
    # Try JSON first, fallback to source PDF
    json_path = "tab_structure.json"
    source = "vampire_journal.pdf"
    output = "SL_journal.pdf"
    
    if os.path.exists(json_path):
        print("Using JSON structure file...")
        generator.generate_from_json(json_path, output, source_pdf_path=source)
    elif os.path.exists(source):
        print("Using source PDF method...")
        generator.generate_from_source(source, output)
    else:
        print(f"Error: Neither {json_path} nor {source} found!")
        return


if __name__ == "__main__":
    main()
