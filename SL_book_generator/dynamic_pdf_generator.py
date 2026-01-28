#!/usr/bin/env python3
"""
Dynamic PDF Generator for Vampire Journal
Main orchestrator that combines content processing and layout generation.
"""

import fitz  # PyMuPDF
from typing import List, Dict
import os
from layout_generator import LayoutGenerator
from content_processor import ContentProcessor


class DynamicPDFGenerator:
    """Generates the PDF dynamically from scratch"""
    
    def __init__(self):
        self.page_width = 595.2755737304688  # A4 width in points
        self.page_height = 841.8897705078125  # A4 height in points
        
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
        
        # Initialize layout and content processors
        self.layout_generator = LayoutGenerator(self.page_width, self.page_height)
        self.content_processor = ContentProcessor(self.page_width, self.page_height)
    
    def generate_from_source(self, source_path: str, output_path: str):
        """Generates PDF based on original PDF"""
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
        
        # Update tab names with original texts if available
        if len(tab_texts) >= len(self.tabs):
            # Create mapping from tab names to target_page
            # IMPORTANT: NPCs and Karten are swapped in the source PDF
            # NPCs tab currently shows Karten content (page 30), should show NPCs content (page 90)
            # Karten tab currently shows NPCs content (page 90), should show Karten content (page 30)
            name_to_target = {
                "Domäne": 1,
                "Intrigen & Interessen": 11,
                "Runden": 23,
                "NPCs": 90,  # NPCs should point to page 90 (NPCs content)
                "Orte": 81,
                "Karten": 30,  # Karten should point to page 30 (Karten content)
                "Handouts": 93,
                "Notizen": 94,
                "Regeln": 95
            }
            
            for i, tab in enumerate(self.tabs):
                if i < len(tab_texts):
                    extracted_name = tab_texts[i]
                    tab["name"] = extracted_name
                    # Set target_page based on extracted name (this fixes the swap)
                    if extracted_name in name_to_target:
                        tab["target_page"] = name_to_target[extracted_name]
                        print(f"  Tab '{extracted_name}' -> page {name_to_target[extracted_name]}")
            print(f"  Found: {len(tab_texts)} tab labels")
        else:
            print(f"  Warning: Only {len(tab_texts)} tab texts found, using default names")
        
        # Copy pages from source (content processing)
        total_pages = self.content_processor.copy_pages_from_source(source_doc, doc)
        
        # Apply layout (blood splatters and tabs)
        self.layout_generator.apply_layout_to_pdf(doc, self.tabs, tab_text_elements)
        
        # Process links (content processing)
        self.content_processor.process_links(source_doc, doc, self.layout_generator, total_pages)
        
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
        print(f"  - Tab positions: {self.layout_generator.tab_x} (x), heights: {[t['y'] for t in self.tabs]}")
        
        return output_path


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
