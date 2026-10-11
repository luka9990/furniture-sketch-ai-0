FURNITURE SKETCH AI — DODATNI MODULI
====================================

Ovaj ZIP sadrži dodatne module, ne zamjenu za postojeći app.py:
- ai_analyzer.py: analiza slike i PDF-a pomoću OpenAI vision modela
- calculations.py: tabela elemenata, validacija, površina/zapremina, procjena cijene, CSV
- pdf_export.py: PDF izvještaj
- requirements_additions.txt: paketi za postojeći requirements.txt

BITNO: Nemam sadržaj tvoje trenutne verzije app.py, pa nisam mogao sigurno spojiti
ove funkcije s postojećim dugmadima i prikazom. Ako pošalješ app.py i requirements.txt,
mogu napraviti precizno povezanu verziju.

KAKO DODATI
1. Raspakuj ove fajlove u isti folder gdje je postojeći app.py.
2. Dodaj pakete iz requirements_additions.txt u postojeći requirements.txt
   (izbaci duplikate ako ih ima).
3. U aktivnom virtual environmentu pokreni:
   python -m pip install -r requirements.txt
4. U Streamlit Cloud → App → Settings → Secrets dodaj:
   OPENAI_API_KEY = "tvoj_api_kljuc"
   Ne stavljaj ključ u kod ili GitHub repozitorij.

IMPORTI ZA app.py
-----------------
from ai_analyzer import analyze_image, analyze_pdf_pages
from calculations import parts_to_dataframe, validate_parts, add_area_and_volume, estimate_board_cost, export_cut_list_csv
from pdf_export import make_report_pdf

Primjer:
analysis = analyze_image(uploaded_file.getvalue(), uploaded_file.name,
                         board_thickness_mm=18,
                         extra_instructions="Sve mjere su u mm.")
df = parts_to_dataframe(analysis)
warnings = validate_parts(df)
csv_bytes = export_cut_list_csv(df)
pdf_bytes = make_report_pdf(analysis, df)

PDF:
page_results = analyze_pdf_pages(pdf_uploaded_file.getvalue(), max_pages=3,
                                 board_thickness_mm=18)
PDF stranice se analiziraju odvojeno; rezultati se ne spajaju automatski.

OGRANIČENJA
- AI može pogrešno pročitati rukopis, perspektivu ili dimenzije.
- Ne može pouzdano zaključiti skrivene mjere koje nisu označene.
- Pravila spojeva/preklapanja i oduzimanje debljine ploča treba posebno definisati.
- Procjena cijene računa površinu ploča i ne uključuje otpad, optimizaciju rezanja,
  kant traku, okov, rad ili dostavu.
- Prije rezanja obavezno provjeri sve mjere ručno.
- OpenAI API naplata je odvojena od ChatGPT pretplate; budžet postavi uz roditelja/staratelja.
