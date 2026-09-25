"""
PPTX Builder — Generates clean PowerPoint presentations from pitch data.

Creates professional slide decks with consistent formatting,
ready for client meetings.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pathlib import Path
from io import BytesIO


# ─── Design tokens ───
BRAND_COLOR = RGBColor(0x47, 0x55, 0x69)       # Slate blue (matches CSS)
TEXT_PRIMARY = RGBColor(0x1C, 0x19, 0x17)       # Dark warm gray
TEXT_SECONDARY = RGBColor(0x57, 0x53, 0x4E)     # Medium gray
TEXT_LIGHT = RGBColor(0xA8, 0xA2, 0x9E)         # Light gray
BG_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT_LIGHT = RGBColor(0xF1, 0xF5, 0xF9)


def build_pptx(pitch: dict) -> BytesIO:
    """Build a PowerPoint presentation from pitch data.
    
    Args:
        pitch: Dict with pitch_title, target_company, slides, etc.
    
    Returns:
        BytesIO buffer containing the .pptx file
    """
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Slide 0: Title slide
    _add_title_slide(prs, pitch)

    # Content slides
    for slide_data in pitch.get("slides", []):
        _add_content_slide(prs, slide_data)

    # Final slide: Recommendation
    if pitch.get("recommended_policy") or pitch.get("key_differentiators"):
        _add_recommendation_slide(prs, pitch)

    # Save to buffer
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer


def _add_title_slide(prs: Presentation, pitch: dict):
    """Add the title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BRAND_COLOR

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(1.5), Inches(2.5), Inches(10), Inches(1.5)
    )
    title_frame = title_box.text_frame
    title_frame.word_wrap = True
    p = title_frame.paragraphs[0]
    p.text = pitch.get("pitch_title", "Insurance Pitch")
    p.font.size = Pt(36)
    p.font.color.rgb = BG_WHITE
    p.font.bold = True
    p.alignment = PP_ALIGN.LEFT

    # Subtitle - company name
    sub_box = slide.shapes.add_textbox(
        Inches(1.5), Inches(4.2), Inches(10), Inches(0.8)
    )
    sub_frame = sub_box.text_frame
    p = sub_frame.paragraphs[0]
    p.text = f"Prepared for {pitch.get('target_company', 'Client')}"
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
    p.alignment = PP_ALIGN.LEFT

    # Marsh branding
    marsh_box = slide.shapes.add_textbox(
        Inches(1.5), Inches(6.0), Inches(4), Inches(0.5)
    )
    marsh_frame = marsh_box.text_frame
    p = marsh_frame.paragraphs[0]
    p.text = "Marsh — Insurance Pitch Generator"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p.alignment = PP_ALIGN.LEFT


def _add_content_slide(prs: Presentation, slide_data: dict):
    """Add a content slide with title and bullet points."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Slide number
    num_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(0.6), Inches(1), Inches(0.4)
    )
    num_frame = num_box.text_frame
    p = num_frame.paragraphs[0]
    p.text = f"0{slide_data.get('slide_number', '')}"
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_LIGHT

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(1.1), Inches(11), Inches(0.8)
    )
    title_frame = title_box.text_frame
    title_frame.word_wrap = True
    p = title_frame.paragraphs[0]
    p.text = slide_data.get("title", "")
    p.font.size = Pt(28)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.bold = True
    p.alignment = PP_ALIGN.LEFT

    # Subtitle
    if slide_data.get("subtitle"):
        sub_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(1.9), Inches(11), Inches(0.5)
        )
        sub_frame = sub_box.text_frame
        p = sub_frame.paragraphs[0]
        p.text = slide_data["subtitle"]
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_SECONDARY

    # Bullet points
    bullets = slide_data.get("bullets", [])
    if bullets:
        bullet_top = Inches(2.6) if slide_data.get("subtitle") else Inches(2.2)
        bullet_box = slide.shapes.add_textbox(
            Inches(1.0), bullet_top, Inches(10.5), Inches(4.0)
        )
        bullet_frame = bullet_box.text_frame
        bullet_frame.word_wrap = True

        for i, bullet in enumerate(bullets):
            if i == 0:
                p = bullet_frame.paragraphs[0]
            else:
                p = bullet_frame.add_paragraph()
            
            p.text = bullet
            p.font.size = Pt(16)
            p.font.color.rgb = TEXT_PRIMARY
            p.space_after = Pt(12)
            p.level = 0

    # Speaker notes
    if slide_data.get("speaker_notes"):
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = slide_data["speaker_notes"]


def _add_recommendation_slide(prs: Presentation, pitch: dict):
    """Add the recommendation/summary slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Accent bar at top
    bar = slide.shapes.add_shape(
        1, Inches(0), Inches(0), prs.slide_width, Inches(0.08)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = BRAND_COLOR
    bar.line.fill.background()

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(1.0), Inches(11), Inches(0.8)
    )
    title_frame = title_box.text_frame
    p = title_frame.paragraphs[0]
    p.text = "Our Recommendation"
    p.font.size = Pt(28)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.bold = True

    # Recommendation text
    if pitch.get("recommended_policy"):
        rec_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(2.0), Inches(10.5), Inches(1.0)
        )
        rec_frame = rec_box.text_frame
        rec_frame.word_wrap = True
        p = rec_frame.paragraphs[0]
        p.text = pitch["recommended_policy"]
        p.font.size = Pt(16)
        p.font.color.rgb = TEXT_SECONDARY

    # Key differentiators
    diffs = pitch.get("key_differentiators", [])
    if diffs:
        diff_box = slide.shapes.add_textbox(
            Inches(1.0), Inches(3.3), Inches(10.5), Inches(3.0)
        )
        diff_frame = diff_box.text_frame
        diff_frame.word_wrap = True

        # Header
        p = diff_frame.paragraphs[0]
        p.text = "Key Differentiators"
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_LIGHT
        p.font.bold = True
        p.space_after = Pt(16)

        for diff in diffs:
            p = diff_frame.add_paragraph()
            p.text = diff
            p.font.size = Pt(16)
            p.font.color.rgb = TEXT_PRIMARY
            p.space_after = Pt(10)


def save_pptx(pitch: dict, output_path: str | Path) -> str:
    """Build and save PPTX to disk.
    
    Returns the absolute path of the saved file.
    """
    buffer = build_pptx(pitch)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        f.write(buffer.read())
    
    return str(output_path.resolve())
