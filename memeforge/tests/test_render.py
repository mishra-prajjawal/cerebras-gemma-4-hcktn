from __future__ import annotations
import base64
import io
from PIL import Image
from memeforge.contracts import RankedCaption
from memeforge.render import overlay


def test_overlay_renders_image() -> None:
    # Create a small dummy white image
    img = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64_in = base64.b64encode(buf.getvalue()).decode()

    caption = RankedCaption(text="TOP TEXT | BOTTOM TEXT", score=95, reason="hilarious")
    b64_out = overlay(b64_in, caption)

    assert b64_out, "should return base64 string"
    assert b64_out != b64_in, "should have burned in text"

    # Decode and verify it is a valid image
    out_data = base64.b64decode(b64_out)
    out_img = Image.open(io.BytesIO(out_data))
    assert out_img.size == (200, 200)
    assert out_img.mode == "RGB"
