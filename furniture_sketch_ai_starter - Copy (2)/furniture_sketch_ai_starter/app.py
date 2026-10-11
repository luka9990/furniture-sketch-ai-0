import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO

from ai_analyzer import analyze_image, analyze_pdf_pages
from calculations import (
    parts_to_dataframe, validate_parts, add_area_and_volume,
    estimate_board_cost, export_cut_list_csv
)
from pdf_export import make_report_pdf

st.set_page_config(page_title="Furniture Sketch AI", page_icon="📐", layout="wide")
st.title("Furniture Sketch AI")
st.caption("Analiza skica namještaja, provjera dimenzija i izrada liste za rezanje.")

with st.sidebar:
    st.header("Postavke projekta")
    project_name = st.text_input("Naziv projekta", "Moj ormar")
    unit = st.selectbox("Jedinica za ručni proračun", ["mm", "cm"], index=0)
    st.caption("AI rezultati su prikazani u milimetrima (mm).")
    st.divider()
    st.subheader("AI postavke")
    board_thickness = st.number_input("Poznata debljina ploče (mm)", min_value=0.0, value=18.0, step=1.0)
    extra_instructions = st.text_area(
        "Dodatne upute AI-ju",
        placeholder="Npr. označi leđa ormara; materijal je 18 mm iverica.",
        help="AI koristi ove upute kao dodatni kontekst. Provjeri sve rezultate ručno."
    )

tab_ai, tab_manual = st.tabs(["🤖 AI analiza skice", "📐 Ručni proračun"])

with tab_ai:
    st.subheader("1. Učitaj skicu ili tehnički crtež")
    drawing = st.file_uploader(
        "Podržani formati: PNG, JPG, WEBP ili PDF (PDF: najviše prve 3 stranice)",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        key="ai_drawing"
    )
    if drawing:
        if drawing.name.lower().endswith(".pdf"):
            st.info(f"Učitan PDF: {drawing.name}. AI će analizirati do 3 stranice.")
        else:
            try:
                preview = Image.open(BytesIO(drawing.getvalue()))
                st.image(preview, caption="Učitana skica", use_container_width=True)
            except Exception:
                st.error("Ne mogu prikazati sliku. Probaj PNG ili JPG.")
    if st.button("Pokreni AI analizu", type="primary", disabled=(drawing is None)):
        try:
            with st.spinner("AI analizira crtež. Ovo može potrajati i može se naplatiti preko API računa."):
                if drawing.name.lower().endswith(".pdf"):
                    analyses = analyze_pdf_pages(
                        drawing.getvalue(),
                        max_pages=3,
                        extra_instructions=extra_instructions,
                        board_thickness_mm=board_thickness or None
                    )
                    st.session_state["ai_analyses"] = analyses
                else:
                    result = analyze_image(
                        drawing.getvalue(),
                        drawing.name,
                        extra_instructions=extra_instructions,
                        board_thickness_mm=board_thickness or None
                    )
                    st.session_state["ai_analyses"] = [result]
                st.session_state["ai_source_name"] = drawing.name
        except Exception as exc:
            st.error(f"Analiza nije uspjela: {exc}")
            st.caption("Provjeri OPENAI_API_KEY u lokalnom okruženju ili Streamlit Secrets, internet vezu i API pristup.")

    analyses = st.session_state.get("ai_analyses", [])
    if analyses:
        st.success(f"Analiza spremna: {len(analyses)} rezultat(a).")
        if len(analyses) > 1:
            page_choice = st.selectbox(
                "Odaberi stranicu PDF-a",
                options=list(range(len(analyses))),
                format_func=lambda i: f"Stranica {i+1}",
                key="ai_page_choice"
            )
        else:
            page_choice = 0
        analysis = analyses[page_choice]
        st.markdown("#### Sažetak")
        st.write(analysis.get("summary") or "AI nije dao sažetak.")
        dims = analysis.get("overall_dimensions_mm", {}) or {}
        st.markdown("#### Prepoznate vanjske dimenzije (mm)")
        d1, d2, d3 = st.columns(3)
        d1.metric("Dužina", dims.get("length") if dims.get("length") is not None else "Nije prepoznato")
        d2.metric("Širina", dims.get("width") if dims.get("width") is not None else "Nije prepoznato")
        d3.metric("Visina", dims.get("height") if dims.get("height") is not None else "Nije prepoznato")
        visible = analysis.get("visible_dimensions") or []
        if visible:
            with st.expander("Dimenzije koje AI vidi na crtežu"):
                for item in visible:
                    st.write(f"• {item}")
        st.markdown("#### Lista dijelova — provjeri i po potrebi uredi")
        st.caption("Nepoznate mjere ostaju prazne. AI može pogrešno pročitati crtež; nemoj rezati materijal bez ručne provjere.")
        parts_df = parts_to_dataframe(analysis)
        edited = st.data_editor(
            parts_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "name": st.column_config.TextColumn("Dio", required=True),
                "quantity": st.column_config.NumberColumn("Količina", min_value=1, step=1),
                "length_mm": st.column_config.NumberColumn("Dužina (mm)", min_value=0.0),
                "width_mm": st.column_config.NumberColumn("Širina (mm)", min_value=0.0),
                "thickness_mm": st.column_config.NumberColumn("Debljina (mm)", min_value=0.0),
                "material": st.column_config.TextColumn("Materijal"),
                "confidence": st.column_config.SelectboxColumn("AI pouzdanost", options=["high", "medium", "low"]),
                "notes": st.column_config.TextColumn("Napomene")
            },
            key=f"edited_parts_{page_choice}"
        )
        warnings = validate_parts(edited)
        if warnings:
            st.warning("Potrebna je ručna provjera:")
            for warning in warnings:
                st.write(f"• {warning}")
        else:
            st.success("Osnovne vrijednosti u tabeli izgledaju popunjeno. I dalje provjeri mjere prema crtežu.")
        calculated = add_area_and_volume(edited)
        st.markdown("#### Procjena materijala")
        price = st.number_input("Cijena ploče po m² (opcionalno)", min_value=0.0, value=0.0, step=1.0, key=f"price_{page_choice}")
        total_area = calculated["total_area_m2"].fillna(0).sum()
        total_volume = calculated["total_volume_m3"].fillna(0).sum()
        c1, c2 = st.columns(2)
        c1.metric("Ukupna površina dijelova", f"{total_area:.3f} m²")
        c2.metric("Ukupna zapremina dijelova", f"{total_volume:.4f} m³")
        if price > 0:
            st.metric("Gruba procjena cijene materijala", f"{estimate_board_cost(edited, price):.2f}")
            st.caption("Procjena ne uključuje otpad, raspored rezanja, kantovanje, okove ni rad.")
        csv_data = export_cut_list_csv(edited)
        st.download_button(
            "Preuzmi listu dijelova (CSV)",
            data=csv_data,
            file_name=f"lista_dijelova_stranica_{page_choice+1}.csv",
            mime="text/csv",
            key=f"csv_{page_choice}"
        )
        try:
            pdf_data = make_report_pdf(analysis, edited)
            st.download_button(
                "Preuzmi izvještaj (PDF)",
                data=pdf_data,
                file_name=f"izvjestaj_namjestaj_stranica_{page_choice+1}.pdf",
                mime="application/pdf",
                key=f"pdf_{page_choice}"
            )
        except Exception as exc:
            st.error(f"PDF izvještaj nije moguće napraviti: {exc}")
        questions = analysis.get("questions") or []
        if questions:
            st.markdown("#### Šta treba potvrditi")
            for question in questions:
                st.write(f"• {question}")

with tab_manual:
    st.subheader("Ručna provjera jednostavnog ormara")
    st.caption("Ovaj proračun je odvojen od AI analize i ostaje dostupan i bez API ključa.")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("1. Skica")
        manual_upload = st.file_uploader(
            "Ubaci fotografiju ili sliku crteža",
            type=["png", "jpg", "jpeg", "webp"],
            key="manual_drawing"
        )
        if manual_upload:
            try:
                image = Image.open(manual_upload)
                st.image(image, caption="Učitana skica", use_container_width=True)
            except Exception:
                st.error("Ne mogu otvoriti ovu sliku. Probaj PNG ili JPG datoteku.")
        else:
            st.write("Ovdje će se prikazati tvoja skica.")
        st.subheader("2. Vanjske dimenzije")
        width = st.number_input(f"Širina ormara ({unit})", min_value=1.0, value=800.0, step=10.0, key="manual_width")
        height = st.number_input(f"Visina ormara ({unit})", min_value=1.0, value=2000.0, step=10.0, key="manual_height")
        depth = st.number_input(f"Dubina ormara ({unit})", min_value=1.0, value=600.0, step=10.0, key="manual_depth")
        thickness = st.number_input(f"Debljina ploče ({unit})", min_value=1.0, value=18.0, step=1.0, key="manual_thickness")
        shelves = st.number_input("Broj unutrašnjih polica", min_value=0, max_value=30, value=3, step=1, key="manual_shelves")
    with right:
        st.subheader("3. Rezultati provjere")
        issues = []
        if thickness * 2 >= width:
            issues.append("Debljina dvije bočne ploče je jednaka ili veća od ukupne širine.")
        if thickness * 2 >= height:
            issues.append("Debljina gornje i donje ploče je jednaka ili veća od ukupne visine.")
        if thickness >= depth:
            issues.append("Debljina ploče je jednaka ili veća od dubine ormara.")
        inner_width = width - 2 * thickness
        inner_height = height - 2 * thickness
        inner_depth = depth - thickness
        if inner_width > 0 and inner_depth > 0 and inner_height > 0:
            shelf_width, shelf_depth, usable_height = inner_width, inner_depth, inner_height
        else:
            shelf_width = shelf_depth = usable_height = 0
        if issues:
            st.error("Pronađene moguće greške")
            for issue in issues:
                st.write(f"• {issue}")
        else:
            st.success("Osnovne dimenzije su matematički moguće.")
            st.caption("Ovo nije potpuna provjera konstrukcije ili sigurnosti namještaja.")
        st.metric("Unutrašnja širina", f"{inner_width:.1f} {unit}" if inner_width > 0 else "Provjeri dimenzije")
        st.metric("Unutrašnja visina", f"{inner_height:.1f} {unit}" if inner_height > 0 else "Provjeri dimenzije")
        st.metric("Procijenjena unutrašnja dubina", f"{inner_depth:.1f} {unit}" if inner_depth > 0 else "Provjeri dimenzije")
        if shelves > 0 and usable_height > 0:
            clear_gap = (usable_height - shelves * thickness) / (shelves + 1)
            if clear_gap < 0:
                st.warning("Police i razmaci ne staju u raspoloživu visinu prema ovom jednostavnom modelu.")
            else:
                st.write(f"Približan jednak razmak između polica: **{clear_gap:.1f} {unit}**")
    st.divider()
    st.subheader("4. Početna lista za rezanje")
    st.caption("Pretpostavka: jednostavan pravougaoni ormar. Ne uključuje leđa, vrata, kantovanje, spojeve, zazore ni optimizaciju rasporeda na ploči.")
    cut_rows = [
        {"Dio": "Bočna stranica", "Količina": 2, f"Širina ({unit})": height, f"Dužina ({unit})": depth},
        {"Dio": "Gornja ploča", "Količina": 1, f"Širina ({unit})": inner_width, f"Dužina ({unit})": depth},
        {"Dio": "Donja ploča", "Količina": 1, f"Širina ({unit})": inner_width, f"Dužina ({unit})": depth},
    ]
    if shelves > 0:
        cut_rows.append({"Dio": "Polica", "Količina": int(shelves), f"Širina ({unit})": shelf_width, f"Dužina ({unit})": shelf_depth})
    cut_df = pd.DataFrame(cut_rows)
    st.dataframe(cut_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Preuzmi listu za rezanje (CSV)",
        data=cut_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="lista_za_rezanje.csv",
        mime="text/csv",
        key="manual_csv"
    )

st.divider()
st.caption("Prototip za učenje i testiranje. AI rezultat nije proizvodni plan — prije rezanja obavezno ručno provjeri sve mjere, spojeve i konstrukciju.")
