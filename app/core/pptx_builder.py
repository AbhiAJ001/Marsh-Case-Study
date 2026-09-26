"""
PPTX Builder v2 — Editorial design matching the web app palette.

Slide deck structure:
  Slide 1: Cover            — Half blue panel, company name, date
  Slide 2: Company Profile  — Key data from research
  Slides 3-7: Content       — Each with left accent bar + title + subtitle + bullets
  Slide 8: Recommendation   — Bold close slide with key differentiators
  Slide 9: Thank You        — Clean dark close
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from pathlib import Path
from io import BytesIO
from datetime import date


# ─── Design Tokens — matches web app CSS palette ─────────────────────────────

STEEL_BLUE    = RGBColor(0x1A, 0x78, 0xB4)   # --accent
BLUE_DARK     = RGBColor(0x10, 0x4D, 0x7A)   # dark variant of accent
BLUE_MUTED    = RGBColor(0x9A, 0xB0, 0xC8)   # --accent-muted
NEAR_BLACK    = RGBColor(0x0F, 0x11, 0x17)   # --text-primary
TEXT_SEC      = RGBColor(0x3C, 0x48, 0x58)   # --text-secondary
TEXT_MUTED    = RGBColor(0x8A, 0x97, 0xA8)   # --text-tertiary
BG_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BG_CARD       = RGBColor(0xF7, 0xF8, 0xFA)
BG_LIGHT_BLUE = RGBColor(0xEB, 0xF4, 0xFB)   # --accent-light
BORDER_COLOR  = RGBColor(0xD9, 0xDC, 0xE3)

# Widescreen 16:9
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _solid_rect(slide, left, top, width, height, color: RGBColor):
    """Add a filled rectangle with no border."""
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def _textbox(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    return tf


def _set_para(para, text, size, color, bold=False, align=PP_ALIGN.LEFT, italic=False, space_after=0):
    para.text = text
    para.font.size = Pt(size)
    para.font.color.rgb = color
    para.font.bold = bold
    para.font.italic = italic
    para.alignment = align
    if space_after:
        para.space_after = Pt(space_after)


# ─── Slide builders ───────────────────────────────────────────────────────────

def _add_cover_slide(prs: Presentation, pitch: dict):
    """Cover: left third is deep blue panel, right two-thirds is white."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # White background
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Left blue panel (4.2 inches wide)
    panel_w = Inches(4.4)
    _solid_rect(slide, 0, 0, panel_w, SLIDE_H, STEEL_BLUE)

    # Thin accent stripe at right edge of panel
    _solid_rect(slide, panel_w, 0, Inches(0.06), SLIDE_H, BLUE_MUTED)

    # "MARSH" label inside blue panel
    tf = _textbox(slide, Inches(0.4), Inches(0.55), Inches(3.4), Inches(0.5))
    _set_para(tf.paragraphs[0], "MARSH", 13, BG_WHITE, bold=True, align=PP_ALIGN.LEFT)

    # "Insurance Pitch Generator" inside blue panel
    tf2 = _textbox(slide, Inches(0.4), Inches(1.0), Inches(3.6), Inches(0.4))
    _set_para(tf2.paragraphs[0], "Insurance Pitch Generator", 9.5,
              RGBColor(0xBE, 0xD6, 0xEC), align=PP_ALIGN.LEFT)

    # Company name — large, white, in blue panel
    company = pitch.get("target_company", "Client")
    tf3 = _textbox(slide, Inches(0.4), Inches(2.6), Inches(3.5), Inches(2.0))
    tf3.word_wrap = True
    _set_para(tf3.paragraphs[0], company, 30, BG_WHITE, bold=True, align=PP_ALIGN.LEFT)

    # Date
    tf4 = _textbox(slide, Inches(0.4), Inches(6.6), Inches(3.5), Inches(0.5))
    _set_para(tf4.paragraphs[0], date.today().strftime("%B %Y"),
              10, RGBColor(0xBE, 0xD6, 0xEC), align=PP_ALIGN.LEFT)

    # Right side — pitch title
    title = pitch.get("pitch_title", "Tailored Insurance Proposal")
    tf5 = _textbox(slide, Inches(5.2), Inches(2.2), Inches(7.5), Inches(2.5))
    tf5.word_wrap = True
    _set_para(tf5.paragraphs[0], title, 28, NEAR_BLACK, bold=False, align=PP_ALIGN.LEFT)

    # "Prepared by Marsh" on the right
    tf6 = _textbox(slide, Inches(5.2), Inches(5.0), Inches(7.5), Inches(0.5))
    _set_para(tf6.paragraphs[0], "Prepared by Marsh Advisory", 11,
              TEXT_MUTED, align=PP_ALIGN.LEFT)

    # Confidential tag
    tf7 = _textbox(slide, Inches(5.2), Inches(6.7), Inches(4), Inches(0.4))
    _set_para(tf7.paragraphs[0], "CONFIDENTIAL — NOT FOR DISTRIBUTION",
              8, BORDER_COLOR, align=PP_ALIGN.LEFT)

    # Bottom accent bar (full width)
    _solid_rect(slide, 0, SLIDE_H - Inches(0.07), SLIDE_W, Inches(0.07), STEEL_BLUE)


def _add_profile_slide(prs: Presentation, profile: dict):
    """Slide 2: Company profile key data grid."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Top accent bar
    _solid_rect(slide, 0, 0, SLIDE_W, Inches(0.08), STEEL_BLUE)

    # Section label
    tf = _textbox(slide, Inches(1.0), Inches(0.4), Inches(3), Inches(0.35))
    _set_para(tf.paragraphs[0], "COMPANY INTELLIGENCE", 8.5, BLUE_MUTED,
              bold=True, align=PP_ALIGN.LEFT)

    # Title
    tf2 = _textbox(slide, Inches(1.0), Inches(0.75), Inches(11), Inches(0.7))
    company = profile.get("company_name", "")
    _set_para(tf2.paragraphs[0], f"About {company}", 26, NEAR_BLACK, align=PP_ALIGN.LEFT)

    # Description
    desc = profile.get("description", "")
    tf3 = _textbox(slide, Inches(1.0), Inches(1.55), Inches(11.2), Inches(0.8))
    _set_para(tf3.paragraphs[0], desc, 11.5, TEXT_SEC, align=PP_ALIGN.LEFT)

    # Divider
    _solid_rect(slide, Inches(1.0), Inches(2.45), Inches(11.2), Inches(0.018), BORDER_COLOR)

    # Data grid — 4 boxes side by side
    fields = [
        ("Industry",      profile.get("industry", "—")),
        ("Est. Size",     profile.get("estimated_size", "—").title()),
        ("Employees",     profile.get("estimated_employees", "—")),
        ("HQ",            profile.get("headquarters", "—")),
    ]
    box_w = Inches(2.6)
    for i, (label, val) in enumerate(fields):
        x = Inches(1.0) + i * (box_w + Inches(0.22))
        # Box bg
        _solid_rect(slide, x, Inches(2.65), box_w, Inches(1.25), BG_CARD)
        # Value
        tf_v = _textbox(slide, x + Inches(0.18), Inches(2.78), box_w - Inches(0.3), Inches(0.65))
        _set_para(tf_v.paragraphs[0], val, 16, STEEL_BLUE, bold=True)
        # Label
        tf_l = _textbox(slide, x + Inches(0.18), Inches(3.48), box_w - Inches(0.3), Inches(0.35))
        _set_para(tf_l.paragraphs[0], label, 9, TEXT_MUTED)

    # Key risks
    risks = profile.get("key_risks", [])[:5]
    tf_rh = _textbox(slide, Inches(1.0), Inches(4.1), Inches(5.5), Inches(0.35))
    _set_para(tf_rh.paragraphs[0], "KEY RISKS", 8.5, BLUE_MUTED, bold=True)

    y_r = Inches(4.5)
    for risk in risks:
        _solid_rect(slide, Inches(1.0), y_r + Inches(0.06), Inches(0.045), Inches(0.22), STEEL_BLUE)
        tf_r = _textbox(slide, Inches(1.18), y_r, Inches(5.0), Inches(0.35))
        _set_para(tf_r.paragraphs[0], risk, 11, TEXT_SEC)
        y_r += Inches(0.32)

    # Pitch angle box
    pitch_angle = profile.get("pitch_angle", "")
    if pitch_angle:
        _solid_rect(slide, Inches(7.0), Inches(4.0), Inches(5.3), Inches(2.85), BG_LIGHT_BLUE)
        _solid_rect(slide, Inches(7.0), Inches(4.0), Inches(0.07), Inches(2.85), STEEL_BLUE)
        tf_ph = _textbox(slide, Inches(7.25), Inches(4.12), Inches(4.8), Inches(0.35))
        _set_para(tf_ph.paragraphs[0], "PITCH ANGLE", 8.5, STEEL_BLUE, bold=True)
        tf_pa = _textbox(slide, Inches(7.25), Inches(4.55), Inches(4.8), Inches(2.0))
        _set_para(tf_pa.paragraphs[0], pitch_angle, 11.5, TEXT_SEC, italic=True)

    # Bottom bar
    _solid_rect(slide, 0, SLIDE_H - Inches(0.07), SLIDE_W, Inches(0.07), STEEL_BLUE)


def _add_content_slide(prs: Presentation, slide_data: dict, slide_num: int, total: int):
    """Content slide: left accent bar, bold title, subtitle, rich bullets."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Top accent bar
    _solid_rect(slide, 0, 0, SLIDE_W, Inches(0.08), STEEL_BLUE)

    # Left accent stripe
    _solid_rect(slide, Inches(0.55), Inches(0.85), Inches(0.07), Inches(1.35), STEEL_BLUE)

    # Slide counter top-right
    tf_ctr = _textbox(slide, Inches(11.8), Inches(0.18), Inches(1.3), Inches(0.35))
    _set_para(tf_ctr.paragraphs[0], f"{slide_num} / {total}", 9, TEXT_MUTED,
              align=PP_ALIGN.RIGHT)

    # Section label
    tf_lbl = _textbox(slide, Inches(0.9), Inches(0.78), Inches(5), Inches(0.32))
    label = slide_data.get("slide_type", f"SLIDE {slide_num}").upper()
    _set_para(tf_lbl.paragraphs[0], label, 8.5, BLUE_MUTED, bold=True)

    # Title
    tf_title = _textbox(slide, Inches(0.9), Inches(1.08), Inches(11.5), Inches(0.85))
    _set_para(tf_title.paragraphs[0], slide_data.get("title", ""), 26,
              NEAR_BLACK, bold=False, align=PP_ALIGN.LEFT)

    # Subtitle
    subtitle = slide_data.get("subtitle", "")
    if subtitle:
        tf_sub = _textbox(slide, Inches(0.9), Inches(1.92), Inches(11.5), Inches(0.42))
        _set_para(tf_sub.paragraphs[0], subtitle, 12.5, STEEL_BLUE, bold=False)

    # Divider line under title area
    _solid_rect(slide, Inches(0.9), Inches(2.42), Inches(11.3), Inches(0.018), BORDER_COLOR)

    # Bullets
    bullets = slide_data.get("bullets", [])
    if bullets:
        bullet_top = Inches(2.65)
        # Layout: 2 columns if 5+ bullets, else single column
        if len(bullets) >= 5:
            mid = (len(bullets) + 1) // 2
            col1 = bullets[:mid]
            col2 = bullets[mid:]
            _render_bullet_column(slide, col1, Inches(0.9),  bullet_top, Inches(5.9))
            _render_bullet_column(slide, col2, Inches(7.1),  bullet_top, Inches(5.9))
        else:
            _render_bullet_column(slide, bullets, Inches(0.9), bullet_top, Inches(11.5))

    # Speaker notes
    if slide_data.get("speaker_notes"):
        slide.notes_slide.notes_text_frame.text = slide_data["speaker_notes"]

    # Bottom bar
    _solid_rect(slide, 0, SLIDE_H - Inches(0.07), SLIDE_W, Inches(0.07), STEEL_BLUE)


def _render_bullet_column(slide, bullets, left, top, width):
    """Render a list of bullet strings as styled items with a blue dot."""
    y = top
    row_h = Inches(0.55)
    for bullet in bullets:
        # Blue dot accent
        _solid_rect(slide, left, y + Inches(0.155), Inches(0.07), Inches(0.07), STEEL_BLUE)
        # Bullet text
        tf = _textbox(slide, left + Inches(0.2), y, width - Inches(0.2), row_h)
        _set_para(tf.paragraphs[0], str(bullet), 13, TEXT_SEC)
        y += row_h + Inches(0.04)


def _add_recommendation_slide(prs: Presentation, pitch: dict):
    """Recommendation close slide — bold blue panel on right."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_WHITE

    # Top accent bar
    _solid_rect(slide, 0, 0, SLIDE_W, Inches(0.08), STEEL_BLUE)

    # Right blue panel
    panel_start = Inches(8.0)
    _solid_rect(slide, panel_start, Inches(0.08), SLIDE_W - panel_start, SLIDE_H - Inches(0.15), STEEL_BLUE)

    # Section label
    tf_lbl = _textbox(slide, Inches(0.9), Inches(0.75), Inches(6), Inches(0.35))
    _set_para(tf_lbl.paragraphs[0], "OUR RECOMMENDATION", 8.5, BLUE_MUTED, bold=True)

    # Title
    tf_title = _textbox(slide, Inches(0.9), Inches(1.1), Inches(6.8), Inches(1.0))
    _set_para(tf_title.paragraphs[0], "Why Partner with Marsh?", 26, NEAR_BLACK, bold=False)

    # Recommended policy
    if pitch.get("recommended_policy"):
        _solid_rect(slide, Inches(0.9), Inches(2.3), Inches(6.8), Inches(0.018), BORDER_COLOR)
        tf_rp = _textbox(slide, Inches(0.9), Inches(2.45), Inches(6.8), Inches(0.35))
        _set_para(tf_rp.paragraphs[0], "RECOMMENDED POLICY", 8.5, STEEL_BLUE, bold=True)
        tf_rv = _textbox(slide, Inches(0.9), Inches(2.82), Inches(6.8), Inches(0.7))
        _set_para(tf_rv.paragraphs[0], pitch["recommended_policy"], 13, TEXT_SEC)

    # Key differentiators on left
    diffs = pitch.get("key_differentiators", [])
    if diffs:
        tf_dh = _textbox(slide, Inches(0.9), Inches(3.7), Inches(6.8), Inches(0.35))
        _set_para(tf_dh.paragraphs[0], "KEY DIFFERENTIATORS", 8.5, BLUE_MUTED, bold=True)
        y = Inches(4.1)
        for diff in diffs[:5]:
            _solid_rect(slide, Inches(0.9), y + Inches(0.13), Inches(0.07), Inches(0.07), STEEL_BLUE)
            tf_d = _textbox(slide, Inches(1.14), y, Inches(6.5), Inches(0.48))
            _set_para(tf_d.paragraphs[0], str(diff), 12.5, TEXT_SEC)
            y += Inches(0.52)

    # Right panel: "Next Steps" header
    tf_ns = _textbox(slide, panel_start + Inches(0.45), Inches(1.2), Inches(4.5), Inches(0.42))
    _set_para(tf_ns.paragraphs[0], "NEXT STEPS", 9, RGBColor(0xBE, 0xD6, 0xEC), bold=True)

    steps = [
        "Schedule a consultation call with our team",
        "Review policy terms and coverage details",
        "Customise plan to your workforce profile",
        "Finalise onboarding and employee comms",
    ]
    y_s = Inches(1.7)
    for i, step in enumerate(steps, 1):
        # Number circle bg
        _solid_rect(slide, panel_start + Inches(0.4), y_s + Inches(0.04),
                    Inches(0.35), Inches(0.35), BLUE_DARK)
        # Number
        tf_n = _textbox(slide, panel_start + Inches(0.44), y_s + Inches(0.03),
                        Inches(0.28), Inches(0.38))
        _set_para(tf_n.paragraphs[0], str(i), 10.5, BG_WHITE, bold=True, align=PP_ALIGN.CENTER)
        # Step text
        tf_s = _textbox(slide, panel_start + Inches(0.9), y_s, Inches(3.9), Inches(0.45))
        _set_para(tf_s.paragraphs[0], step, 11.5, RGBColor(0xD6, 0xE8, 0xF5))
        y_s += Inches(0.7)

    # Bottom bar
    _solid_rect(slide, 0, SLIDE_H - Inches(0.07), SLIDE_W, Inches(0.07), STEEL_BLUE)


def _add_thank_you_slide(prs: Presentation, pitch: dict):
    """Final slide — deep blue, clean close."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = STEEL_BLUE

    # Marsh wordmark
    tf_m = _textbox(slide, Inches(1.5), Inches(0.55), Inches(4), Inches(0.5))
    _set_para(tf_m.paragraphs[0], "MARSH", 14, BG_WHITE, bold=True)

    # Thank you
    tf_ty = _textbox(slide, Inches(1.5), Inches(2.5), Inches(10), Inches(1.1))
    _set_para(tf_ty.paragraphs[0], "Thank you.", 44, BG_WHITE, bold=False)

    # Subline
    company = pitch.get("target_company", "")
    tf_sub = _textbox(slide, Inches(1.5), Inches(3.7), Inches(10), Inches(0.6))
    _set_para(tf_sub.paragraphs[0],
              f"We look forward to protecting {company} with world-class coverage.",
              14, RGBColor(0xBE, 0xD6, 0xEC), italic=True)

    # Contact line
    tf_c = _textbox(slide, Inches(1.5), Inches(5.5), Inches(10), Inches(0.45))
    _set_para(tf_c.paragraphs[0], "contact@marsh.com  ·  www.marsh.com",
              11, RGBColor(0x7A, 0xAD, 0xD6))

    # Bottom light bar
    _solid_rect(slide, 0, SLIDE_H - Inches(0.15), SLIDE_W, Inches(0.15), BLUE_DARK)


# ─── Main entry point ─────────────────────────────────────────────────────────

def build_pptx(pitch: dict, profile: dict = None) -> BytesIO:
    """Build a polished PowerPoint from pitch (+ optional profile) data.

    Args:
        pitch:   Full pitch dict from PitchOrchestrator
        profile: Optional company profile dict for the profile slide

    Returns:
        BytesIO buffer with .pptx content
    """
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    # Slide 1: Cover
    _add_cover_slide(prs, pitch)

    # Slide 2: Company Profile (if profile data is embedded in pitch or passed separately)
    embedded_profile = profile or pitch.get("_profile")
    if embedded_profile:
        _add_profile_slide(prs, embedded_profile)

    # Slides 3–N: Content slides
    slides = pitch.get("slides", [])
    total_content = len(slides)
    for i, slide_data in enumerate(slides, 1):
        _add_content_slide(prs, slide_data, i, total_content)

    # Recommendation slide
    if pitch.get("recommended_policy") or pitch.get("key_differentiators"):
        _add_recommendation_slide(prs, pitch)

    # Thank You
    _add_thank_you_slide(prs, pitch)

    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer


def save_pptx(pitch: dict, output_path: str | Path, profile: dict = None) -> str:
    """Build and save PPTX to disk. Returns absolute path."""
    buffer = build_pptx(pitch, profile)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(buffer.read())
    return str(output_path.resolve())
