# Furniture Sketch AI — početni prototip

## Šta radi ova verzija
- Učitava sliku skice i prikazuje je.
- Omogućava ručni unos vanjskih dimenzija ormara.
- Radi nekoliko osnovnih matematičkih provjera.
- Računa jednostavnu početnu listu dijelova.
- Omogućava preuzimanje liste za rezanje u CSV formatu.

## Važno ograničenje
Ovo još nije AI model i ne čita automatski dimenzije sa slike. Lista za rezanje je pojednostavljena i ne uzima u obzir sve spojeve, vrata, leđa, zazore ili pravila izrade. Nemoj koristiti rezultat za stvarno rezanje bez provjere od strane iskusne osobe.

## Pokretanje na Windowsu

1. Instaliraj Python 3.11 ili noviji sa https://www.python.org/downloads/
2. Tokom instalacije označi **Add Python to PATH**.
3. Raspakuj ZIP u folder, npr. `C:\FurnitureSketchAI`.
4. Otvori taj folder u File Exploreru.
5. Klikni na adresnu traku foldera, upiši `cmd` i pritisni Enter.
6. U terminalu pokreni ove komande jednu po jednu:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

7. Browser bi trebao otvoriti aplikaciju. Ako se ne otvori, terminal će prikazati lokalnu adresu, obično `http://localhost:8501`. Kopiraj je u browser.
8. Da zaustaviš aplikaciju, vrati se u terminal i pritisni `Ctrl+C`.

## Ako nešto ne radi
- Ako `py` nije prepoznat, Python vjerovatno nije instaliran ili nije dodat u PATH. Instaliraj ga ponovo i označi tu opciju.
- Ako instalacija paketa ne uspije, kopiraj cijelu poruku greške i zatraži pomoć.
- Ne zatvaraj terminal dok koristiš aplikaciju.

## Plan nadogradnje
1. Dodati bolji model podataka za dijelove ormara.
2. Dodati OCR za čitanje teksta i dimenzija.
3. Tražiti potvrdu korisnika za nesigurno pročitane vrijednosti.
4. Dodati 3D geometrijske provjere.
5. Napraviti označeni skup primjera i evaluirati postojeći model prije fine-tuninga.
