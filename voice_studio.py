import streamlit as st
import edge_tts
import asyncio
import tempfile
import os
import zipfile
from io import BytesIO

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Voice Studio AI", page_icon="🎙️", layout="centered")

# --- SŁOWNIK JĘZYKOWY (GLOBAL) ---
LANG = {
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
        "btn_dl_zip": "📦 Download all as ZIP (.zip)",
        "err_no_text": "⚠️ Please upload a file or enter text.",
        "stats_chars": "Characters:",
        "stats_time": "Est. Time:",
        "coffee_msg": "Support this free tool:"
    },
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
        "btn_dl_single": "📥 Pobierz MP3",
        "btn_dl_zip": "📦 Pobierz wszystko jako ZIP (.zip)",
        "err_no_text": "⚠️ Proszę wpisać tekst lub wgrać plik.",
        "stats_chars": "Znaków:",
        "stats_time": "Szacowany czas:",
        "coffee_msg": "Wesprzyj darmowe narzędzie:"
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
        "btn_dl_zip": "📦 Descargar todo en ZIP (.zip)",
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
        "btn_dl_zip": "📦 Alles als ZIP herunterladen",
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
        "btn_dl_zip": "📦 Tout télécharger en ZIP",
        "err_no_text": "⚠️ Veuillez entrer du texte.",
        "stats_chars": "Caractères:",
        "stats_time": "Temps estimé:",
        "coffee_msg": "Soutenez cet outil:"
    }
}

VOICES = {
    "🇺🇸 English - Guy (Male)": "en-US-GuyNeural",
    "🇺🇸 English - Aria (Female)": "en-US-AriaNeural",
    "🇬🇧 English (UK) - Ryan (Male)": "en-GB-RyanNeural",
    "🇵🇱 Polski - Marek (Męski)": "pl-PL-MarekNeural",
    "🇵🇱 Polski - Zofia (Żeński)": "pl-PL-ZofiaNeural",
    "🇪🇸 Español - Alvaro (Hombre)": "es-ES-AlvaroNeural",
    "🇪🇸 Español - Elvira (Mujer)": "es-ES-ElviraNeural",
    "🇩🇪 Deutsch - Killian (Männlich)": "de-DE-KillianNeural",
    "🇫🇷 Français - Henri (Homme)": "fr-FR-HenriNeural"
}

# --- FUNKCJE SILNIKA ---
def bezpieczne_ciecie_tekstu(tekst, max_znakow=8000):
    akapity = tekst.split('\n')
    paczki, obecna_paczka = [], ""
    for akapit in akapity:
        if len(obecna_paczka) + len(akapit) < max_znakow:
            obecna_paczka += akapit + "\n"
        else:
            if obecna_paczka.strip(): paczki.append(obecna_paczka.strip())
            if len(akapit) >= max_znakow:
                for i in range(0, len(akapit), max_znakow):
                    paczki.append(akapit[i:i+max_znakow])
                obecna_paczka = ""
            else:
                obecna_paczka = akapit + "\n"
    if obecna_paczka.strip(): paczki.append(obecna_paczka.strip())
    return paczki

async def generuj_audio_paczki(paczki, kod_glosu, rate_str, progress_bar, status_text, t):
    wygenerowane_pliki, bledy = [], 0
    for i, fragment in enumerate(paczki):
        status_text.text(f"{t['msg_working']} (Part {i+1} / {len(paczki)})")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            nazwa_mp3 = tmp_audio.name
        try:
            communicate = edge_tts.Communicate(fragment, kod_glosu, rate=rate_str)
            await communicate.save(nazwa_mp3)
            wygenerowane_pliki.append(nazwa_mp3)
        except Exception:
            bledy += 1
        progress_bar.progress((i + 1) / len(paczki))
    return wygenerowane_pliki, bledy

# --- PANEL BOCZNY ---
with st.sidebar:
    st.header("⚙️ Settings")
    lang_choice = st.selectbox("🌐 Language / Język", ["EN", "PL", "ES", "DE", "FR"], index=0)
    t = LANG[lang_choice]
    
    st.divider()
    
    theme_choice = st.radio("🌗 Theme", ["🌙 Dark Mode", "☀️ Light Mode"])
    
    # Dynamiczny CSS oparty na wyborze motywu (Naprawiony pasek i kolory!)
    if "Light" in theme_choice:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            /* Usunięto 'header {visibility: hidden;}' aby ikona > była widoczna */
            
            /* Jasne tło główne */
            .stApp { background-color: #FFFFFF; color: #111827; }
            
            /* Wymuszamy jasny wygląd bocznego paska */
            [data-testid="stSidebar"] { background-color: #F8F9FA !important; border-right: 1px solid #E5E7EB !important; }
            
            /* Kontrast tekstu w całym interfejsie i na bocznym pasku */
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #111827 !important; }
            
            /* Jasne pola tekstowe */
            .stTextArea textarea { background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; }
            
            /* Główny złoty przycisk */
            div.stButton > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: bold !important; border: none !important; border-radius: 8px !important; }
            div.stButton > button:hover { background-color: #FFC107 !important; transform: scale(1.02) !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            
            /* Ciemne tło główne */
            .stApp { background-color: #0A0A0A; color: #F5F5F5; }
            
            /* Wymuszamy ciemny wygląd bocznego paska */
            [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #222222 !important; }
            
            /* Kontrast tekstu w całym interfejsie i na bocznym pasku */
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #F5F5F5 !important; }
            
            /* Ciemne pola tekstowe */
            .stTextArea textarea { background-color: #1A1A1A !important; color: #F5F5F5 !important; border: 1px solid #333333 !important; }
            
            /* Główny złoty przycisk */
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

# SOCIAL MEDIA W ROGU
social_html = """
<div style="position: fixed; bottom: 20px; right: 20px; text-align: right; z-index: 1000; background-color: rgba(17,17,17,0.7); padding: 10px; border-radius: 8px; border: 1px solid #333; backdrop-filter: blur(5px);">
    <p style="margin:0; font-size: 11px; color: #E2E8F0; font-weight: bold;">Built by Dawid 🚀</p>
    <a href="https://www.linkedin.com/in/dawid-kowszewicz/" target="_blank" style="color: #38BDF8; font-size: 12px; text-decoration: none; margin-right: 5px;">LinkedIn</a> |
    <a href="mailto:kowszewiczdawidd@gmail.com" target="_blank" style="color: #38BDF8; font-size: 12px; text-decoration: none; margin-left: 5px;">Contact</a>
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

if st.button(t["btn_gen"], type="primary", use_container_width=True):
    if liczba_znakow == 0:
        st.error(t["err_no_text"])
    else:
        paczki = bezpieczne_ciecie_tekstu(tekst_uzytkownika)
        if len(paczki) > 1:
            st.info(f"File is large. Splitting into **{len(paczki)}** parts for safety.")
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        wygenerowane_pliki, bledy = asyncio.run(generuj_audio_paczki(paczki, kod_glosu, rate_str, progress_bar, status_text, t))
        
        status_text.empty()
        if wygenerowane_pliki:
            st.success(t["msg_success"])
            st.balloons()
            if bledy > 0:
                st.warning(f"Recorded {bledy} errors on some chunks.")
            
            if len(wygenerowane_pliki) == 1:
                st.audio(wygenerowane_pliki[0], format="audio/mp3")
                with open(wygenerowane_pliki[0], "rb") as audio_file:
                    st.download_button(label=t["btn_dl_single"], data=audio_file, file_name="Voice_Studio.mp3", mime="audio/mpeg", use_container_width=True)
            else:
                st.audio(wygenerowane_pliki[0], format="audio/mp3") 
                st.caption("Player shows Part 1 only. Download ZIP for the full audio.")
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for idx, plik in enumerate(wygenerowane_pliki):
                        zf.write(plik, arcname=f"Audio_Part_{idx+1}.mp3")
                
                zip_buffer.seek(0)
                st.download_button(label=t["btn_dl_zip"], data=zip_buffer, file_name="Voice_Studio_Full.zip", mime="application/zip", use_container_width=True)