"""Vision reader (stub): OCR/describe a screenshot into reviewable text.
TODO(agent): implement one multimodal call -> extracted document text."""
from __future__ import annotations
from ..audit import audited
from ..contracts import DocIn, ReviewerInput
from .base import Agent


class VisionReader(Agent[DocIn, ReviewerInput]):
    name = "vision_reader"

    @audited("vision_reader")
    async def run(self, data: DocIn) -> ReviewerInput:
        """Precondition: DocIn with an image. Postcondition: ReviewerInput text."""
        assert isinstance(data, DocIn), "input must be DocIn"
        assert data.jpeg_b64, "vision reader needs an image"

        import base64
        from io import BytesIO
        from PIL import Image
        from ..config import get_settings
        from ..contracts import VisionOutput

        # 1. Decode base64 image
        img_bytes = base64.b64decode(data.jpeg_b64)
        img: Image.Image = Image.open(BytesIO(img_bytes))

        # 2. Downscale if long edge > settings.jpeg_max_edge
        s = get_settings()
        max_edge = s.jpeg_max_edge
        w, h = img.size
        if max(w, h) > max_edge:
            if w > h:
                new_w = max_edge
                new_h = int(h * (max_edge / w))
            else:
                new_h = max_edge
                new_w = int(w * (max_edge / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. Convert to RGB if necessary (e.g. RGBA) and save to base64 jpeg
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        downscaled_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # 4. Construct multimodal payload
        system = "You are a document transcription agent. Extract all text verbatim from the screenshot."
        messages: list[dict[str, object]] = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Transcribe the full, verbatim text from this document screenshot. "
                                "Do not summarize; extract all clauses, headings, and terms exactly as shown."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{downscaled_b64}"}
                    }
                ]
            }
        ]

        # 5. Call structured inference
        out = await self._client.structured(
            messages=messages, out=VisionOutput, max_tokens=s.reviewer_max_tokens)

        # 6. Postconditions and return
        res = ReviewerInput(role="ocr", doc_text=out.extracted_text)
        assert isinstance(res, ReviewerInput), "output must be ReviewerInput"
        assert res.doc_text, "transcribed text must not be empty"
        return res
