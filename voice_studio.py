import streamlit as st
import edge_tts
import asyncio
import tempfile
import os

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Voice Studio AI", page_icon="🎙️", layout="centered")

# --- SŁOWNIK JĘZYKOWY ---
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
        "coffee_msg": "Wesprzyj darmowe narzędzie:",
        "theme_light": "☀️ Jasny",
        "theme_dark": "🌙 Ciemny",
        "contact_txt": "Kontakt 🚀"
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
        "coffee_msg": "Support this free tool:",
        "theme_light": "☀️ Light",
        "theme_dark": "🌙 Dark",
        "contact_txt": "Contact 🚀"
    }
}

VOICES = {
    "🇵🇱 Polski - Marek (Męski)": "pl-PL-MarekNeural",
    "🇵🇱 Polski - Zofia (Żeński)": "pl-PL-ZofiaNeural",
    "🇺🇸 English - Guy (Male)": "en-US-GuyNeural",
    "🇺🇸 English - Aria (Female)": "en-US-AriaNeural",
    "🇬🇧 English (UK) - Ryan (Male)": "en-GB-RyanNeural",
    "🇪🇸 Español - Alvaro (Hombre)": "es-ES-AlvaroNeural",
    "🇩🇪 Deutsch - Killian (Männlich)": "de-DE-KillianNeural",
    "🇫🇷 Français - Henri (Homme)": "fr-FR-HenriNeural"
}

# --- LOGIKA SILNIKA ---
def bezpieczny_podzial_tekstu(tekst, max_znakow=3500):
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
    with open(plik_wyjsciowy, 'wb') as plik_docelowy:
        for i, fragment in enumerate(paczki):
            procent = int(((i) / liczba_paczek) * 100)
            status_text.markdown(f"**{msg_working} ({procent}%)**")
            communicate = edge_tts.Communicate(fragment, kod_glosu, rate=rate_str)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    plik_docelowy.write(chunk["data"])
            progress_bar.progress((i + 1) / liczba_paczek)
    status_text.markdown(f"**{msg_working} (100%)**")

# --- PANEL BOCZNY ---
with st.sidebar:
    lang_choice = st.radio("Język", ["PL", "EN"], horizontal=True, label_visibility="collapsed")
    t = LANG[lang_choice]
    
    st.write("")
    
    theme_choice = st.radio("Motyw", [t["theme_light"], t["theme_dark"]], index=0, horizontal=True, label_visibility="collapsed")
    
    if theme_choice == t["theme_light"]:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            .stApp { background-color: #FAFAFA; color: #111827; }
            [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E7EB !important; }
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #111827 !important; }
            
            /* Pola wpisywania */
            .stTextArea textarea, .stFileUploader, div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; }
            div[data-baseweb="select"] span { color: #111827 !important; }
            
            /* Przycisk Browse Files - JASNY MOTYW */
            [data-testid="stFileUploader"] button { background-color: #E5E7EB !important; color: #111827 !important; border: 1px solid #D1D5DB !important; font-weight: bold !important; }
            [data-testid="stFileUploader"] button:hover { background-color: #D1D5DB !important; }
            
            /* Złoty Przycisk Akcji */
            div.stButton > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: 900 !important; border: none !important; border-radius: 8px !important; transition: all 0.2s !important; padding: 10px !important;}
            div.stButton > button:hover { background-color: #FFC107 !important; box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.4) !important; transform: scale(1.01) !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;}
            .stApp { background-color: #0F172A; color: #F8FAFC; }
            [data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid #1E293B !important; }
            h1, h2, h3, p, label, .stMarkdown span, [data-testid="stSidebar"] * { color: #F8FAFC !important; }
            
            /* Pola wpisywania */
            .stTextArea textarea, .stFileUploader, div[data-baseweb="select"] > div { background-color: #1E293B !important; color: #F8FAFC !important; border: 1px solid #334155 !important; }
            div[data-baseweb="select"] span { color: #F8FAFC !important; }
            
            /* Przycisk Browse Files - CIEMNY MOTYW */
            [data-testid="stFileUploader"] button { background-color: #334155 !important; color: #F8FAFC !important; border: 1px solid #475569 !important; font-weight: bold !important; }
            [data-testid="stFileUploader"] button:hover { background-color: #475569 !important; }
            
            /* Złoty Przycisk Akcji */
            div.stButton > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: 900 !important; border: none !important; border-radius: 8px !important; transition: all 0.2s !important; padding: 10px !important;}
            div.stButton > button:hover { background-color: #FFC107 !important; box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.3) !important; transform: scale(1.01) !important; }
            </style>
            """, unsafe_allow_html=True)

    st.divider()
    
    st.markdown(f"*{t['coffee_msg']}*")
    st.markdown("""
    <a href="https://buycoffee.to/sportnotes.ai" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important; border-radius: 5px;" >
    </a>
    """, unsafe_allow_html=True)

# --- SOCIAL MEDIA (BEZPIECZNA STOPKA) ---
social_html = f"""
<div style="position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%); text-align: center; z-index: 1000; background-color: #111111 !important; padding: 8px 24px; border-radius: 25px; border: 1px solid #333 !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
    <span style="font-size: 13px; color: #F5F5F5 !important; font-weight: bold; margin-right: 12px;">{t['contact_txt']}</span>
    <a href="https://www.facebook.com/profile.php?id=61588513657984" target="_blank" style="color: #FFD700 !important; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 600; letter-spacing: 0.5px;">Facebook</a> <span style="color: #555 !important;">|</span>
    <a href="https://www.linkedin.com/in/dawid-kowszewicz/" target="_blank" style="color: #FFD700 !important; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 600; letter-spacing: 0.5px;">LinkedIn</a> <span style="color: #555 !important;">|</span>
    <a href="mailto:kowszewiczdawidd@gmail.com" target="_blank" style="color: #FFD700 !important; font-size: 13px; text-decoration: none; margin: 0 6px; font-weight: 600; letter-spacing: 0.5px;">Email</a>
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

st.write("")

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
                    file_name="Voice_Studio_Audio.mp3", 
                    mime="audio/mpeg", 
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Wystąpił błąd podczas generowania: {str(e)}")
        finally:
            status_text.empty()
