from __future__ import annotations
import base64, json, mimetypes, os
from typing import Any
from openai import OpenAI

MODEL_DEFAULT = "gpt-4.1-mini"
SCHEMA = {
  "type":"object",
  "properties":{
    "project_name":{"type":["string","null"]},
    "units":{"type":"string","enum":["mm"]},
    "overall_dimensions_mm":{"type":"object","properties":{
      "length":{"type":["number","null"]},"width":{"type":["number","null"]},"height":{"type":["number","null"]}
    },"required":["length","width","height"],"additionalProperties":False},
    "parts":{"type":"array","items":{"type":"object","properties":{
      "name":{"type":"string"},"quantity":{"type":"integer","minimum":1},
      "length_mm":{"type":["number","null"]},"width_mm":{"type":["number","null"]},
      "thickness_mm":{"type":["number","null"]},"material":{"type":["string","null"]},
      "confidence":{"type":"string","enum":["high","medium","low"]},"notes":{"type":"string"}
    },"required":["name","quantity","length_mm","width_mm","thickness_mm","material","confidence","notes"],"additionalProperties":False}},
    "visible_dimensions":{"type":"array","items":{"type":"string"}},
    "questions":{"type":"array","items":{"type":"string"}},
    "summary":{"type":"string"}
  },
  "required":["project_name","units","overall_dimensions_mm","parts","visible_dimensions","questions","summary"],
  "additionalProperties":False
}
INSTRUCTIONS = """
You are a careful furniture technical-drawing assistant. Inspect the sketch and
identify individual physical panels, not only the outside dimensions. Return JSON.
List visible pieces such as top, bottom, side panels, back panel, shelves, doors,
drawer parts, dividers and rails. Read labelled dimensions when legible. All output
dimensions must be mm; convert clearly labelled cm to mm. Never invent unreadable
dimensions: use null and ask a question. Keep cabinet outside dimensions separate
from cut dimensions. Use board thickness only if explicitly labelled or provided.
Do not assume joinery/overlap rules without instructions. Mark confidence low when
uncertain. A perspective sketch alone cannot reliably establish missing dimensions.
"""
def _data_url(data: bytes, filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    if not mime or not mime.startswith("image/"): mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

def _api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not key:
        raise RuntimeError("Nedostaje OPENAI_API_KEY. Dodaj ga u Streamlit Secrets; ne stavljaj ga u kod.")
    return key

def analyze_image(image_bytes: bytes, filename: str = "drawing.jpg", *,
                  extra_instructions: str = "", board_thickness_mm: float | None = None,
                  model: str | None = None) -> dict[str, Any]:
    client = OpenAI(api_key=_api_key())
    prompt = (INSTRUCTIONS + "\nUser instructions: " + (extra_instructions or "None") +
              "\nKnown board thickness in mm: " + str(board_thickness_mm or "not provided") +
              "\nReturn every identifiable part and explicitly list missing measurements in questions.")
    response = client.responses.create(
      model=model or os.getenv("OPENAI_VISION_MODEL", MODEL_DEFAULT),
      input=[{"role":"user","content":[
        {"type":"input_text","text":prompt},
        {"type":"input_image","image_url":_data_url(image_bytes, filename)}
      ]}],
      text={"format":{"type":"json_schema","name":"furniture_drawing_analysis","strict":True,"schema":SCHEMA}}
    )
    try: return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI nije vratio ispravan JSON. Pokušaj ponovo.") from exc

def analyze_pdf_pages(pdf_bytes: bytes, *, max_pages: int = 3, **kwargs) -> list[dict[str, Any]]:
    """Analyze up to three PDF pages separately; page results are not auto-merged."""
    import fitz
    from PIL import Image
    import io
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    results = []
    for i, page in enumerate(doc):
        if i >= max_pages: break
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        buf = io.BytesIO(); img.save(buf, format="PNG")
        results.append(analyze_image(buf.getvalue(), f"page_{i+1}.png", **kwargs))
    return results
