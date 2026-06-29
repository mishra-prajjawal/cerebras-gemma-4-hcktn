"""Caption overlay: impact-font top/bottom text via Pillow."""
from __future__ import annotations
import base64
import io
import os
from PIL import Image, ImageDraw, ImageFont
from .contracts import RankedCaption


def _resize_image(img: Image.Image) -> Image.Image:
    """Precondition: img is a PIL Image. Postcondition: resized image under 1080px."""
    assert isinstance(img, Image.Image), "input must be a PIL Image"
    w, h = img.size
    assert w > 0 and h > 0, "dimensions must be positive"
    max_edge = 1080
    if w > max_edge or h > max_edge:
        if w > h:
            new_h = int(h * max_edge / w)
            new_w = max_edge
        else:
            new_w = int(w * max_edge / h)
            new_h = max_edge
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    assert img.width <= max_edge and img.height <= max_edge, "resize failed constraints"
    return img


def _load_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Precondition: font_size > 0. Postcondition: returns a valid font."""
    assert font_size > 0, "font size must be positive"
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    assert len(font_paths) <= 5, "bounded font paths list"
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                assert font is not None, "failed to load font from path"
                return font
            except OSError:
                pass
    fallback = ImageFont.load_default()
    assert fallback is not None, "fallback font failed"
    return fallback


def _wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> list[str]:
    """Precondition: max_width > 0. Postcondition: lines wrapped to fit max_width."""
    assert max_width > 0, "max_width must be positive"
    assert len(text) < 1000, "text is too long"
    words = text.split()
    assert len(words) < 200, "too many words to wrap safely"
    lines: list[str] = []
    current_line: list[str] = []
    for i, word in enumerate(words):
        assert i < 200, "word loop limit exceeded"
        test_line = " ".join(current_line + [word])
        try:
            line_width = font.getlength(test_line)
        except AttributeError:
            line_width = float(len(test_line) * (max_width // 40))
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    assert len(lines) <= len(words), "output lines cannot exceed word count"
    return lines


def overlay(jpeg_b64: str, caption: RankedCaption) -> str:
    """Return a new base64 jpeg with the caption burned in.
    Precondition: inputs present. Postcondition: returns a base64 string."""
    assert jpeg_b64, "image required"
    assert caption.text, "caption required"
    img_data = base64.b64decode(jpeg_b64)
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    assert img is not None, "failed to load image"
    img = _resize_image(img)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font_size = max(20, int(h * 0.07))
    font = _load_font(font_size)
    text_str = caption.text.upper()
    top_part, bottom_part = text_str.split("|", 1) if "|" in text_str else ("", text_str)
    if top_part.strip():
        top_lines = _wrap_text(top_part.strip(), font, int(w * 0.9))
        assert len(top_lines) <= 10, "too many top lines"
        y = int(h * 0.05)
        for i, line in enumerate(top_lines):
            assert i < 10, "top line limit exceeded"
            try:
                line_w = font.getlength(line)
            except AttributeError:
                line_w = float(len(line) * (font_size // 2))
            x = int((w - line_w) // 2)
            draw.text((x, y), line, fill="white", font=font,
                      stroke_width=max(2, font_size // 15), stroke_fill="black")
            y += int(font_size * 1.2)
    if bottom_part.strip():
        bottom_lines = _wrap_text(bottom_part.strip(), font, int(w * 0.9))
        assert len(bottom_lines) <= 10, "too many bottom lines"
        line_height = int(font_size * 1.2)
        y = h - int(h * 0.05) - (len(bottom_lines) * line_height)
        for i, line in enumerate(bottom_lines):
            assert i < 10, "bottom line limit exceeded"
            try:
                line_w = font.getlength(line)
            except AttributeError:
                line_w = float(len(line) * (font_size // 2))
            x = int((w - line_w) // 2)
            draw.text((x, y), line, fill="white", font=font,
                      stroke_width=max(2, font_size // 15), stroke_fill="black")
            y += line_height
    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=85)
    out_b64 = base64.b64encode(out_buf.getvalue()).decode()
    assert out_b64, "failed to encode output image"
    return out_b64
