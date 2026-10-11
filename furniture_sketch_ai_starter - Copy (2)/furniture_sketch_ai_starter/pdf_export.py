from __future__ import annotations
from io import BytesIO
import pandas as pd

def make_report_pdf(analysis: dict, parts_df: pd.DataFrame) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("Furniture Sketch AI — izvještaj", styles["Title"]), Spacer(1, 4*mm)]
    story.append(Paragraph(str(analysis.get("summary", "")), styles["BodyText"]))
    dims = analysis.get("overall_dimensions_mm", {}) or {}
    story += [Spacer(1, 3*mm), Paragraph(
      f"Vanjske dimenzije (mm): dužina {dims.get('length')}, širina {dims.get('width')}, visina {dims.get('height')}",
      styles["BodyText"]), Spacer(1, 4*mm)]
    cols = ["name","quantity","length_mm","width_mm","thickness_mm","material","confidence"]
    data = [["Element","Kom.","Dužina mm","Širina mm","Debljina mm","Materijal","Pouzdanost"]]
    for _, row in parts_df.iterrows():
        data.append([str(row.get(c,"")) if pd.notna(row.get(c)) else "" for c in cols])
    table = Table(data, repeatRows=1, colWidths=[48*mm,14*mm,24*mm,24*mm,27*mm,43*mm,25*mm])
    table.setStyle(TableStyle([
      ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e7edf3")),("GRID",(0,0),(-1,-1),0.4,colors.grey),
      ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")
    ]))
    story += [table, Spacer(1, 4*mm), Paragraph(
      "VAŽNO: AI nacrt nije proizvodni plan. Ručno provjeri sve mjere i spojeve prije rezanja.",
      styles["BodyText"])]
    qs = analysis.get("questions", []) or []
    if qs:
        story += [Spacer(1,3*mm), Paragraph("Potrebno potvrditi", styles["Heading2"])]
        story += [Paragraph("• " + str(q), styles["BodyText"]) for q in qs]
    doc.build(story)
    return buffer.getvalue()
