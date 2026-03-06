import streamlit as st
import edge_tts
import asyncio
import tempfile
import os

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Voice Studio AI", page_icon="🎙️", layout="centered")

# --- SŁOWNIK JĘZYKOWY (PL NA 1 MIEJSCU) ---
LANG = {
    "PL": {
        "title": "🎙️ Studio Głosu AI",
        "subtitle": "Zamień dowolny tekst w profesjonalne audio. 100% za darmo.",
        "upload_lbl": "📁 Wgraj dokument (.txt)",
        "text_lbl": "✍️ Lub wklej swój tekst tutaj:",
        "voice_lbl": "🗣️ Wybierz lektora:",
        "speed_lbl": "⚡ Prędkość czytania:",
        "btn_gen": "🎧 Generuj Audio",
        "msg_working": "Trwa nagrywanie w studiu...",
        "msg_success": "✅ Generowanie zakończone!",
        "btn_dl_single": "📥 Pobierz plik MP3",
        "err_no_text": "⚠️ Proszę wpisać tekst lub wgrać plik.",
        "stats_chars": "Znaków:",
        "stats_time": "Szacowany czas:",
        "coffee_msg": "Wesprzyj darmowe narzędzie:"
    },
    "EN": {
        "title": "🎙️ AI Voice Studio",
        "subtitle": "Convert any text into professional studio audio. 100% free.",
        "upload_lbl": "📁 Upload document (.txt)",
        "text_lbl": "✍️ Or paste your text here:",
        "voice_lbl": "🗣️ Select voice:",
        "speed_lbl": "⚡ Reading Speed:",
        "btn_gen": "🎧 Generate Audio",
        "msg_working": "Recording in the studio...",
        "msg_success": "✅ Audio is ready!",
        "btn_dl_single": "📥 Download MP3",
        "err_no_text": "⚠️ Please upload a file or enter text.",
        "stats_chars": "Characters:",
        "stats_time": "Est. Time:",
        "coffee_msg": "Support this free tool:"
    },
    "ES": {
        "title": "🎙️ Estudio de Voz IA",
        "subtitle": "Convierte texto en audio profesional. 100% gratis.",
        "upload_lbl": "📁 Subir documento (.txt)",
        "text_lbl": "✍️ O pega tu texto aquí:",
        "voice_lbl": "🗣️ Seleccionar voz:",
        "speed_lbl": "⚡ Velocidad de lectura:",
        "btn_gen": "🎧 Generar Audio",
        "msg_working": "Grabando en el estudio...",
        "msg_success": "✅ ¡Tu audio está listo!",
        "btn_dl_single": "📥 Descargar MP3",
        "err_no_text": "⚠️ Por favor, ingresa texto o sube un archivo.",
        "stats_chars": "Caracteres:",
        "stats_time": "Tiempo est.:",
        "coffee_msg": "Apoya esta herramienta:"
    },
    "DE": {
        "title": "🎙️ KI-Sprachstudio",
        "subtitle": "Wandeln Sie Text in professionelles Audio um. 100% kostenlos.",
        "upload_lbl": "📁 Dokument hochladen (.txt)",
        "text_lbl": "✍️ Oder Text hier einfügen:",
        "voice_lbl": "🗣️ Stimme wählen:",
        "speed_lbl": "⚡ Lesegeschwindigkeit:",
        "btn_gen": "🎧 Audio generieren",
        "msg_working": "Aufnahme im Studio...",
        "msg_success": "✅ Ihr Audio ist fertig!",
        "btn_dl_single": "📥 MP3 Herunterladen",
        "err_no_text": "⚠️ Bitte geben Sie Text ein.",
        "stats_chars": "Zeichen:",
        "stats_time": "Geschätzte Zeit:",
        "coffee_msg": "Unterstützen Sie uns:"
    },
    "FR": {
        "title": "🎙️ Studio Vocal IA",
        "subtitle": "Convertissez du texte en audio. 100% gratuit.",
        "upload_lbl": "📁 Télécharger le document (.txt)",
        "text_lbl": "✍️ Ou collez votre texte ici:",
        "voice_lbl": "🗣️ Choisir la voix:",
        "speed_lbl": "⚡ Vitesse de lecture:",
        "btn_gen": "🎧 Générer l'audio",
        "msg_working": "Enregistrement en cours...",
        "msg_success": "✅ Votre audio est prêt!",
        "btn_dl_single": "📥 Télécharger MP3",
        "err_no_text": "⚠️ Veuillez entrer du texte.",
        "stats_chars": "Caractères:",
        "stats_time": "Temps estimé:",
        "coffee_msg": "Soutenez cet outil:"
    }
}

VOICES = {
    "🇵🇱 Polski - Marek (Męski)": "pl-PL-MarekNeural",
    "🇵🇱 Polski - Zofia (Żeński)": "pl-PL-ZofiaNeural",
    "🇺🇸 English - Guy (Male)": "en-US-GuyNeural",
    "🇺🇸 English - Aria (Female)": "en-US-AriaNeural",
    "🇬🇧 English (UK) - Ryan (Male)": "en-GB-RyanNeural",
    "🇪🇸 Español - Alvaro (Hombre)": "es-ES-AlvaroNeural",
    "🇪🇸 Español - Elvira (Mujer)": "es-ES-ElviraNeural",
    "🇩🇪 Deutsch - Killian (Männlich)": "de-DE-KillianNeural",
    "🇫🇷 Français - Henri (Homme)": "fr-FR-HenriNeural"
}

# --- LOGIKA SILNIKA (SKLEJANIE PLIKÓW W LOCIE) ---
def bezpieczny_podzial_tekstu(tekst, max_znakow=3500):
    """Dzieli tekst na akapity, by nie zablokować serwera, ale zwraca jako sekwencję do jednego pliku."""
    akapity = tekst.replace('\r\n', '\n').split('\n\n')
    paczki, obecna_paczka = [], ""
    for akapit in akapity:
        if not akapit.strip(): continue
        if len(obecna_paczka) + len(akapit) < max_znakow:
            obecna_paczka += akapit + "\n\n"
        else:
            if obecna_paczka.strip(): paczki.append(obecna_paczka.strip())
            if len(akapit) >= max_znakow:
                for i in range(0, len(akapit), max_znakow):
                    paczki.append(akapit[i:i+max_znakow])
                obecna_paczka = ""
            else:
                obecna_paczka = akapit + "\n\n"
    if obecna_paczka.strip(): paczki.append(obecna_paczka.strip())
    if not paczki and tekst.strip(): paczki = [tekst.strip()]
    return paczki

async def generuj_z_paskiem_postepu(tekst, plik_wyjsciowy, kod_glosu, rate_str, progress_bar, status_text, msg_working):
    paczki = bezpieczny_podzial_tekstu(tekst)
    liczba_paczek = len(paczki)
    
    # Otwieramy jeden plik binarnie i dopisujemy do niego po kawałku
    with open(plik_wyjsciowy, 'wb') as plik_docelowy:
        for i, fragment in enumerate(paczki):
            procent = int(((i) / liczba_paczek) * 100)
            status_text.text(f"{msg_working} ({procent}%)")
            
            communicate = edge_tts.Communicate(fragment, kod_glosu, rate=rate_str)
            # Binarne pobieranie strumienia audio i sklejanie na żywo
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    plik_docelowy.write(chunk["data"])
                    
            progress_bar.progress((i + 1) / liczba_paczek)
            
    status_text.text(f"{msg_working} (100%)")

# --- PANEL BOCZNY ---
with st.sidebar:
    st.write("") # Puste miejsce zamiast Settings
    
    # Lista języków (PL domyślnie - index 0)
    lang_choice = st.selectbox("🌐 Language / Język", ["PL", "EN", "ES", "DE", "FR"], index=0, label_visibility="collapsed")
    t = LANG[lang_choice]
    
    st.divider()
    
    # Przełącznik bez napisu
    theme_choice = st.radio("Theme", ["🌙 Dark Mode", "☀️ Light Mode"], label_visibility="collapsed")
    
    # Dynamiczny CSS
    if "Light" in theme_choice:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            .stApp { background-color: #FFFFFF; color: #111827; }
            [data-testid="stSidebar"] { background-color: #F8F9FA !important; border-right: 1px solid #E5E7EB !important; }
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #111827 !important; }
            .stTextArea textarea { background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; }
            div.stButton > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: bold !important; border: none !important; border-radius: 8px !important; }
            div.stButton > button:hover { background-color: #FFC107 !important; transform: scale(1.02) !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            .stApp { background-color: #0A0A0A; color: #F5F5F5; }
            [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #222222 !important; }
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #F5F5F5 !important; }
            .stTextArea textarea { background-color: #1A1A1A !important; color: #F5F5F5 !important; border: 1px solid #333333 !important; }
            div.stButton > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: bold !important; border: none !important; border-radius: 8px !important; }
            div.stButton > button:hover { background-color: #FFC107 !important; box-shadow: 0px 0px 15px rgba(255, 215, 0, 0.4) !important; transform: scale(1.02) !important; }
            </style>
            """, unsafe_allow_html=True)

    st.divider()
    
    st.markdown(f"*{t['coffee_msg']}*")
    st.markdown("""
    <a href="https://buycoffee.to/sportnotes.ai" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important; border-radius: 5px;" >
    </a>
    """, unsafe_allow_html=True)

# --- SOCIAL MEDIA (WYŚRODKOWANA STOPKA KONTAKTOWA) ---
# UWAGA: Podmień link do Facebooka na swój prawdziwy adres!
social_html = """
<div style="position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%); text-align: center; z-index: 1000; background-color: rgba(17,17,17,0.85); padding: 8px 20px; border-radius: 25px; border: 1px solid #333; backdrop-filter: blur(8px); box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
    <span style="font-size: 13px; color: #F5F5F5; font-weight: bold; margin-right: 12px;">Contact 🚀</span>
    <a href="https://www.facebook.com/profile.php?id=61588513657984" target="_blank" style="color: #FFD700; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 500;">Facebook</a> <span style="color: #555;">|</span>
    <a href="https://www.linkedin.com/in/dawid-kowszewicz/" target="_blank" style="color: #FFD700; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 500;">LinkedIn</a> <span style="color: #555;">|</span>
    <a href="mailto:kowszewiczdawidd@gmail.com" target="_blank" style="color: #FFD700; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 500;">Email</a>
</div>
"""
st.markdown(social_html, unsafe_allow_html=True)

# --- GŁÓWNA APLIKACJA ---
st.title(t["title"])
st.markdown(f"<span style='opacity: 0.7;'>{t['subtitle']}</span>", unsafe_allow_html=True)
st.write("") 

uploaded_file = st.file_uploader(t["upload_lbl"], type=["txt"])
tekst_startowy = ""
if uploaded_file:
    tekst_startowy = uploaded_file.getvalue().decode("utf-8")

tekst_uzytkownika = st.text_area(t["text_lbl"], value=tekst_startowy, height=220)

liczba_znakow = len(tekst_uzytkownika)
szacowane_minuty = round(liczba_znakow / 900, 1)

col1, col2 = st.columns(2)
with col1:
    st.caption(f"📝 {t['stats_chars']} **{liczba_znakow}**")
with col2:
    if liczba_znakow > 0:
        st.caption(f"⏱️ {t['stats_time']} **~{szacowane_minuty} min**")

st.write("")

col_glos, col_speed = st.columns([2, 1])
with col_glos:
    wybrany_glos_etykieta = st.selectbox(t["voice_lbl"], list(VOICES.keys()))
    kod_glosu = VOICES[wybrany_glos_etykieta]
with col_speed:
    predkosc = st.slider(t["speed_lbl"], min_value=-50, max_value=50, value=0, step=5, format="%d%%")
    rate_str = f"{predkosc:+d}%" if predkosc != 0 else "+0%"

# --- AKCJA GENEROWANIA ---
if st.button(t["btn_gen"], type="primary", use_container_width=True):
    if liczba_znakow == 0:
        st.error(t["err_no_text"])
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            nazwa_mp3 = tmp_audio.name
        
        try:
            asyncio.run(generuj_z_paskiem_postepu(
                tekst_uzytkownika, nazwa_mp3, kod_glosu, rate_str, progress_bar, status_text, t["msg_working"]
            ))
            
            st.success(t["msg_success"])
            st.balloons()
            
            st.audio(nazwa_mp3, format="audio/mp3")
            with open(nazwa_mp3, "rb") as audio_file:
                st.download_button(
                    label=t["btn_dl_single"], 
                    data=audio_file, 
                    file_name="Voice_Studio_Audiobook.mp3", 
                    mime="audio/mpeg", 
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Wystąpił błąd podczas generowania: {str(e)}")
        finally:
            status_text.empty()
