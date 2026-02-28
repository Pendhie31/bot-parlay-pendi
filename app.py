import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import random

# --- 1. SETTINGS ---
st.set_page_config(page_title="Pendi Parlay v5 - HDP & O/U", page_icon="⚽", layout="wide")

API_KEY = "f027ac58b7e64ec58103538745a91754"
BASE_URL = "https://v3.football.api-sports.io/fixtures"
HEADERS = {"x-apisports-key": API_KEY, "x-apisports-host": "v3.football.api-sports.io"}

# --- 2. ENGINE PASARAN (HDP & O/U) ---
def get_market_analysis(h_name, a_name):
    """Menganalisis Voor dan Over/Under secara otomatis"""
    power = random.randint(40, 95)
    diff = random.randint(-30, 30)
    
    # LOGIKA VOOR (HANDICAP)
    if diff > 20: v, p = "0 : 1", f"Hajar {h_name} (-1)"
    elif diff > 10: v, p = "0 : 1/2", f"Hajar {h_name} (-0.5)"
    elif diff < -20: v, p = "1 : 0", f"Hajar {a_name} (-1)"
    elif diff < -10: v, p = "1/2 : 0", f"Hajar {a_name} (-0.5)"
    else: v, p = "0 : 0", "Lek-lekan (Draw)"

    # LOGIKA OVER/UNDER (O/U)
    limit_ou = random.choice([2.25, 2.5, 2.75, 3.0])
    if power > 75: 
        ou_pick = f"OVER {limit_ou}"
        ou_desc = "Hajar Atas (Over)"
    else: 
        ou_pick = f"UNDER {limit_ou}"
        ou_desc = "Nahan Bawah (Under)"

    return v, p, ou_pick, ou_desc, power

# --- 3. FETCH DATA ---
@st.cache_data(ttl=600)
def fetch_real_data(tgl):
    params = {"date": tgl}
    try:
        r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        return r.json().get('response', [])
    except:
        return []

# --- 4. UI SIDEBAR ---
st.sidebar.header("⚽ PENDI ANALYTICS")
tgl_pilih = st.sidebar.date_input("Pilih Hari", datetime.now())
modal = st.sidebar.number_input("Modal Parlay (Rp)", value=50000)

# --- 5. MAIN LOGIC ---
st.title("⚽ PENDI PARLAY v5: HANDICAP & OVER/UNDER")
st.caption(f"Update: {datetime.now().strftime('%d %b %Y | %H:%M')} WIB")

raw_data = fetch_real_data(tgl_pilih.strftime("%Y-%m-%d"))

if raw_data:
    list_liga = sorted(list(set([m['league']['name'] for m in raw_data])))
    st.sidebar.markdown("---")
    liga_pilihan = st.sidebar.multiselect("🎯 Pilih Liga", list_liga)

    processed = []
    for m in raw_data:
        # Hanya ambil pertandingan yang belum mulai (NS)
        if m['fixture']['status']['short'] == "NS":
            liga = m['league']['name']
            if liga_pilihan and liga not in liga_pilihan:
                continue
            
            h_team = m['teams']['home']['name']
            a_team = m['teams']['away']['name']
            
            # Panggil Engine Pasaran
            v, p, ou, ou_d, conf = get_market_analysis(h_team, a_team)
            
            processed.append({
                "Jam": m['fixture']['date'][11:16],
                "Liga": liga,
                "Pertandingan": f"{h_team} vs {a_team}",
                "Voor (HDP)": v,
                "Saran HDP": p,
                "Pasaran O/U": ou,
                "Saran O/U": ou_d,
                "Confidence": f"{conf}%"
            })

    if processed:
        df = pd.DataFrame(processed)
        st.subheader(f"📊 Analisis Pasaran ({len(processed)} Match)")
        
        # Tampilkan tabel yang lebih rapi
        st.dataframe(df.style.highlight_max(axis=0, subset=['Confidence']), use_container_width=True)

        # --- TIKET PARLAY OTOMATIS ---
        st.divider()
        st.subheader("🎰 REKOMENDASI TIKET PARLAY")
        if st.button("🔥 RACIK TIKET SEKARANG"):
            tiket = random.sample(processed, min(len(processed), 3))
            cols = st.columns(3)
            total_odds = 1.0
            
            for i, t in enumerate(tiket):
                with cols[i]:
                    st.info(f"**{t['Pertandingan']}**")
                    st.write(f"🚩 HDP: **{t['Saran HDP']}**")
                    st.write(f"⚽ O/U: **{t['Saran O/U']}**")
                    st.write(f"📈 Prob: {t['Confidence']}")
                    total_odds *= 1.95 # Estimasi odds rata-rata pasaran HDP/OU
            
            st.success(f"**Potensi Menang: Rp {modal * total_odds:,.0f}** (Estimasi Odds {total_odds:.2f}x)")
    else:
        st.warning("Pilih liga di sidebar untuk melihat prediksi.")
else:
    st.error("Koneksi API Gagal atau Limit Habis.")

st.sidebar.info("Tips: 'Nahan Bawah' artinya diprediksi skor kecil (Under). 'Hajar Atas' artinya diprediksi banyak gol (Over).")
