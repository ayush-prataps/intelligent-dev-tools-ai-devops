import re
from typing import List, Dict, Any


def chunk_markdown_document(doc_id: str, markdown_content: str, filename: str = "") -> List[Dict[str, Any]]:
    """
    Semantic-aware chunker that splits a Markdown document along natural section (# and ##)
    and paragraph boundaries, avoiding arbitrary character cuts.
    
    Each chunk preserves hierarchical context (Document Title and Section Name).
    """
    lines = markdown_content.splitlines()
    doc_title = ""
    current_section = "General"
    sections: List[Dict[str, Any]] = []
    current_section_lines: List[str] = []

    # 1. Identify Document Title and parse into logical sections
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not doc_title:
            doc_title = stripped[2:].strip()
            continue
        elif stripped.startswith("## "):
            if current_section_lines:
                body = "\n".join(current_section_lines).strip()
                if body:
                    sections.append({
                        "section": current_section,
                        "body": body
                    })
                current_section_lines = []
            current_section = stripped[3:].strip()
        else:
            current_section_lines.append(line)

    if current_section_lines:
        body = "\n".join(current_section_lines).strip()
        if body:
            sections.append({
                "section": current_section,
                "body": body
            })

    if not doc_title:
        doc_title = filename.replace(".md", "").replace("_", " ").title()

    # 2. Process sections into semantic chunks with natural boundaries
    chunks: List[Dict[str, Any]] = []
    chunk_index = 1

    for sec in sections:
        section_name = sec["section"]
        body_text = sec["body"]
        
        # Split section into paragraphs if large
        paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
        
        for para in paragraphs:
            # Context preservation header
            context_header = f"[{doc_title} > {section_name}]"
            chunk_text = f"{context_header}\n{para}"
            
            chunk_data = {
                "chunk_id": f"{doc_id}_chunk_{chunk_index:02d}",
                "doc_id": doc_id,
                "doc_title": doc_title,
                "section": section_name,
                "text": chunk_text,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split())
            }
            chunks.append(chunk_data)
            chunk_index += 1

    return chunks
