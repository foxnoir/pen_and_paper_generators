#!/usr/bin/env python3
"""
Content Processor for Character Journal PDF
Handles content extraction, page copying, and link processing.
"""

import fitz  # PyMuPDF
from typing import List, Dict


class ContentProcessor:
    """Processes PDF content: extracts text, copies pages, handles links"""
    
    def __init__(self, page_width: float = 595.2755737304688, page_height: float = 841.8897705078125):
        self.page_width = page_width
        self.page_height = page_height
    
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
            return default_tabs[:9]
        
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
    
    def copy_pages_from_source(self, source_doc: fitz.Document, target_doc: fitz.Document):
        """Copies all pages from source PDF to target PDF"""
        total_pages = len(source_doc)
        print(f"Original has {total_pages} pages")
        print(f"Copying pages...")
        
        # Copy all pages - insert_pdf copies content and design
        target_doc.insert_pdf(source_doc, from_page=0, to_page=total_pages - 1)
        
        return total_pages
    
    def process_links(self, source_doc: fitz.Document, target_doc: fitz.Document, layout_generator, total_pages: int):
        """Processes and repairs links from source PDF"""
        print("Copying and repairing links...")
        
        # Target position for upper links: 10px from left, 20px from top
        target_x = 10.0
        target_y = 20.0
        
        # Tab colors for link backgrounds
        tab_colors = layout_generator.tab_colors
        
        # Copy all links from original and reset them (except tab links, which are already set)
        for page_num in range(total_pages):
            source_page = source_doc[page_num]
            target_page = target_doc[page_num]
            
            # Get all links from the original page
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
                        bg_color = tab_colors["active"] if is_active else tab_colors["background"]
                        
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
                        layout_generator.draw_rounded_rect(target_page, new_link_rect, bg_color, border_color=None, radius=3.0, shadow=True)
                        
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
