import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. KONFIGURASI & STYLE (PREMIUM LOOK)
# ==========================================
st.set_page_config(
    page_title="Sistem Monitoring & Intervensi Akademik",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Kustom (Card Style & Typography)
st.markdown("""
<style>
    .stApp {background-color: #f4f7f6;}
    .main-header {font-size: 24px; font-weight: 800; color: #2c3e50; margin-bottom: 20px;}
    
    /* Metric Cards */
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #3498db;
        text-align: center; transition: transform 0.2s;
    }
    .metric-card:hover {transform: translateY(-5px);}
    .metric-val {font-size: 28px; font-weight: bold; color: #2c3e50;}
    .metric-lbl {font-size: 12px; color: #7f8c8d; text-transform: uppercase; font-weight: 600;}
    
    /* Insight Boxes */
    .insight-box {padding: 15px; border-radius: 8px; margin-bottom: 10px; font-size: 14px; line-height: 1.5;}
    .box-danger {background-color: #ffebee; border: 1px solid #ef9a9a; color: #c62828;}
    .box-warning {background-color: #fff8e1; border: 1px solid #ffe082; color: #f57f17;}
    .box-success {background-color: #e8f5e9; border: 1px solid #a5d6a7; color: #2e7d32;}
    
    /* Custom Button */
    .stButton>button {width: 100%; border-radius: 8px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SMART DATA LOADER (ANTI-ERROR)
# ==========================================
GARIS_KEMISKINAN = 928278  # BPS Jaksel
UMK_DKI = 5396761          # UMK 2025

@st.cache_data
def load_data():
    try:
        # Coba load file final
        df = pd.read_csv('processed_data_final.csv')
    except FileNotFoundError:
        try:
            # Fallback ke file draft jika final tidak ada
            df = pd.read_csv('processed_data_for_dashboard.csv')
        except:
            return None

    # --- [CRITICAL FIX] AUTO-RENAME COLUMN ---
    # Ini obat untuk error KeyError 'IPK' atau 'Indeks Ekonomi'
    rename_map = {
        'IPK_Clean': 'IPK',
        'Indeks_Ekonomi': 'Indeks Ekonomi',
        'Manajemen_Stres': 'Manajemen Stres',
        'Beban_SKS': 'Beban SKS',
        'Program Studi (Prodi)': 'Prodi'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # --- [CRITICAL FIX] BUAT KOLOM STATUS ---
    # Wajib ada agar grafik tidak crash
    def get_status(row):
        # Handle potential missing columns gracefully
        try:
            if row['Indeks Ekonomi'] < 1.0: return 'Rentan Ekonomi'
            elif row['Manajemen Stres'] < 2.5: return 'Rentan Stres'
            else: return 'Aman'
        except:
            return 'Unknown'
            
    df['Status'] = df.apply(get_status, axis=1)
    return df

df = load_data()

if df is None:
    st.error("⚠️ Data tidak ditemukan! Jalankan script Jupyter Notebook terlebih dahulu untuk menghasilkan file CSV.")
    st.stop()

# Cek apakah kolom IPK benar-benar ada setelah rename
if 'IPK' not in df.columns:
    st.error(f"⚠️ Kolom 'IPK' tidak ditemukan. Kolom yang tersedia: {list(df.columns)}")
    st.stop()

AVG_IPK = df['IPK'].mean()

# ==========================================
# 3. SIDEBAR NAVIGASI
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/9502/9502623.png", width=60)
st.sidebar.title("Sistem Akademik")
menu = st.sidebar.radio("Menu Utama", ["🏠 Beranda", "📊 Dashboard Eksekutif", "🔍 Simulasi Konseling", "📄 Export Laporan"])

st.sidebar.markdown("---")

# ==========================================
# 4. MODUL 1: BERANDA
# ==========================================
if menu == "🏠 Beranda":
    st.title("Selamat Datang di Sistem Intervensi Akademik")
    st.markdown("""
    Sistem deteksi dini risiko akademik berbasis **Data-Driven Decision Making**. 
    Menggabungkan profil akademik, psikologis, dan data sosio-ekonomi regional (BPS).
    
    ### 🎯 Fitur Unggulan:
    1. **Dashboard Makro:** Peta sebaran risiko Prodi secara real-time.
    2. **Analisis Mikro:** Simulasi konseling per mahasiswa dengan rekomendasi spesifik.
    3. **Validasi Kontekstual:** Menggunakan standar Garis Kemiskinan & UMK DKI Jakarta.
    """)
    
    c1, c2 = st.columns(2)
    with c1: st.info("✅ **Metode:** XGBoost Ensemble & Clustering K-Means")
    with c2: st.success(f"✅ **Data Terkini:** {len(df)} Mahasiswa Terdaftar")

# ==========================================
# 5. MODUL 2: DASHBOARD EKSEKUTIF
# ==========================================
elif menu == "📊 Dashboard Eksekutif":
    st.markdown("<div class='main-header'>🏛️ Dashboard Monitoring Program Studi</div>", unsafe_allow_html=True)
    
    # Filter Data
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_prodi = st.multiselect("Filter Prodi:", df['Prodi'].unique(), default=df['Prodi'].unique())
    with col_f2:
        f_status = st.multiselect("Filter Status:", df['Status'].unique(), default=df['Status'].unique())
        
    df_view = df[df['Prodi'].isin(f_prodi) & df['Status'].isin(f_status)]
    
    # Scorecards
    c1, c2, c3, c4 = st.columns(4)
    total = len(df_view)
    risiko = len(df_view[df_view['Status'] != 'Aman'])
    avg_ipk_v = df_view['IPK'].mean() if total > 0 else 0
    
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Total Mahasiswa</div><div class="metric-val">{total}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Rata-rata IPK</div><div class="metric-val">{avg_ipk_v:.2f}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card" style="border-top-color:#e74c3c;"><div class="metric-lbl">Mahasiswa Berisiko</div><div class="metric-val" style="color:#c0392b;">{risiko}</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="metric-card" style="border-top-color:#27ae60;"><div class="metric-lbl">Kondisi Aman</div><div class="metric-val" style="color:#27ae60;">{total-risiko}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # Charts
    c_chart, c_table = st.columns([2, 1])
    
    with c_chart:
        st.subheader("📍 Peta Zonasi Risiko")
        fig = px.scatter(
            df_view, x="Indeks Ekonomi", y="Manajemen Stres", color="Status",
            size="Beban SKS", hover_data=['IPK', 'Prodi'],
            color_discrete_map={'Rentan Ekonomi': '#e74c3c', 'Rentan Stres': '#f39c12', 'Aman': '#27ae60'},
            title="Sebaran: Ekonomi vs Resiliensi Mental"
        )
        # Garis BPS
        fig.add_vline(x=1.0, line_dash="dash", line_color="red", annotation_text="Garis Kemiskinan")
        fig.update_layout(height=450, plot_bgcolor="white", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
    with c_table:
        st.subheader("📋 Top Mahasiswa Berisiko")
        risk_list = df_view[df_view['Status'] != 'Aman'][['Prodi', 'IPK', 'Indeks Ekonomi']].sort_values('Indeks Ekonomi').head(10)
        st.dataframe(risk_list, height=400)

# ==========================================
# 6. MODUL 3: SIMULASI KONSELING (MIKRO)
# ==========================================
elif menu == "🔍 Simulasi Konseling":
    st.sidebar.header("Input Profil Mahasiswa")
    with st.sidebar.form("simulasi_form"):
        st.markdown("**A. Identitas**")
        nama = st.text_input("Nama", "Mahasiswa Simulasi")
        col1, col2 = st.columns(2)
        sem = col1.selectbox("Semester", [3, 5, 7], index=1)
        ipk = col2.number_input("IPK Kumulatif", 0.0, 4.0, 3.15, step=0.01)
        sks = st.slider("SKS Semester Ini", 10, 24, 21)
        
        st.markdown("**B. Ekonomi Keluarga**")
        gaji_total = st.number_input("Total Pendapatan Ortu (Rp)", 0, 100000000, 3000000, step=500000)
        tanggungan = st.number_input("Jumlah Tanggungan", 1, 10, 4)
        
        st.markdown("**C. Psikologis**")
        stres_lvl = st.select_slider("Tingkat Stres", options=["Sangat Rendah", "Rendah", "Sedang", "Tinggi", "Sangat Tinggi"], value="Sedang")
        waktu_lvl = st.select_slider("Manajemen Waktu", options=["Sangat Buruk", "Buruk", "Cukup", "Baik", "Sangat Baik"], value="Cukup")
        
        btn_calc = st.form_submit_button("🚀 Analisis Risiko", type="primary")

    if btn_calc:
        # --- ENGINE CALCULATION ---
        income_capita = gaji_total / tanggungan
        ratio_eko = income_capita / GARIS_KEMISKINAN
        
        map_val = {"Sangat Rendah": 5, "Rendah": 4, "Sedang": 3, "Tinggi": 2, "Sangat Tinggi": 1}
        score_stres = map_val[stres_lvl]
        
        # Risk Score Logic
        risk_score = 10
        if ratio_eko < 1.0: risk_score += 50
        elif ratio_eko < 1.5: risk_score += 25
        if score_stres <= 2: risk_score += 30
        if ipk < 2.75: risk_score += 15
        risk_score = min(99, risk_score)
        
        # --- REPORT VIEW ---
        st.markdown(f"<div class='main-header'>Laporan Analisis: {nama}</div>", unsafe_allow_html=True)
        
        # 1. Gauge & Summary
        c_gauge, c_sum = st.columns([1, 2])
        with c_gauge:
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = risk_score,
                title = {'text': "Skor Risiko Drop Out"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#c0392b" if risk_score > 60 else "#f39c12"},
                         'steps': [{'range': [0, 30], 'color': '#e8f5e9'}, {'range': [30, 100], 'color': '#fdedec'}]}
            ))
            fig_g.update_layout(height=250, margin=dict(t=30, b=20, l=30, r=30))
            st.plotly_chart(fig_g, use_container_width=True)
            
        with c_sum:
            st.markdown("### 📊 Ringkasan Kondisi")
            k1, k2 = st.columns(2)
            
            # Status Ekonomi BPS
            stat_eko = "KRITIS (MBR)" if ratio_eko < 1.0 else ("RENTAN" if ratio_eko < 1.5 else "SEJAHTERA")
            col_eko = "#c0392b" if ratio_eko < 1.0 else ("#d35400" if ratio_eko < 1.5 else "#27ae60")
            
            with k1: st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Status Ekonomi</div><div class="metric-val" style="color:{col_eko}">{stat_eko}</div><small>Vs Garis Kemiskinan</small></div>""", unsafe_allow_html=True)
            
            # Status Mental
            stat_ment = "BURNOUT" if score_stres <= 2 else "STABIL"
            col_ment = "#c0392b" if score_stres <= 2 else "#27ae60"
            
            with k2: st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Kesehatan Mental</div><div class="metric-val" style="color:{col_ment}">{stat_ment}</div><small>Skor: {score_stres}/5</small></div>""", unsafe_allow_html=True)

        # 2. Deep Insight & Validation
        st.subheader("💡 Analisis Mendalam")
        if ratio_eko < 1.0:
            st.markdown(f"""<div class="insight-box box-danger"><b>🛑 PERINGATAN EKONOMI SERIUS:</b><br>Pendapatan per kapita Rp {int(income_capita):,.0f} berada <b>DI BAWAH</b> Garis Kemiskinan Jakarta Selatan (Rp {GARIS_KEMISKINAN:,.0f}). Mahasiswa ini berisiko tinggi putus kuliah karena ketidakmampuan memenuhi kebutuhan dasar.</div>""", unsafe_allow_html=True)
        
        if score_stres <= 2 and sks > 20:
            st.markdown(f"""<div class="insight-box box-danger"><b>🧠 INDIKASI BURNOUT:</b><br>Mahasiswa mengambil beban berat ({sks} SKS) dengan ketahanan stres yang sangat rendah. Potensi kegagalan studi di semester ini sangat tinggi.</div>""", unsafe_allow_html=True)

        # 3. Action Plan (Netral)
        st.subheader("📋 Rencana Intervensi (Action Plan)")
        r1, r2 = st.columns(2)
        
        with r1:
            st.markdown("#### 🔴 Intervensi Wajib")
            if ratio_eko < 1.5:
                st.info("💰 **Bantuan Finansial:** Arahkan ke Biro Kemahasiswaan/Prodi untuk opsi Bantuan UKT, Cicilan, atau Beasiswa Pemerintah/Yayasan.")
            if score_stres <= 2:
                st.info("🧠 **Konseling:** Wajibkan konsultasi dengan Psikolog Kampus atau Dosen PA minimal 2x bulan ini.")
            if risk_score < 30:
                st.success("✅ Tidak ada intervensi mendesak.")
                
        with r2:
            st.markdown("#### 🔵 Pengembangan")
            if ratio_eko < 2.0: st.write("- **Pekerjaan Kampus:** Tawarkan posisi part-time (Asisten Lab/Perpustakaan).")
            if ipk > 3.0: st.write("- **Akselerasi Karir:** Ikuti program Magang MSIB.")

    else:
        st.info("👈 Silakan isi form di sidebar untuk memulai analisis.")

# ==========================================
# MODUL 4: EXPORT LAPORAN
# ==========================================
elif menu == "📄 Export Laporan":
    st.title("📄 Cetak Laporan")
    st.info("Unduh ringkasan analisis statistik Prodi.")
    
    txt_data = f"""
    LAPORAN MONITORING AKADEMIK
    ---------------------------
    Tanggal Cetak: {datetime.now().strftime("%Y-%m-%d")}
    Total Mahasiswa: {len(df)}
    Rata-rata IPK: {AVG_IPK:.2f}
    
    MAHASISWA BERISIKO:
    - Rentan Ekonomi: {len(df[df['Indeks Ekonomi'] < 1.0])} orang
    - Rentan Stres: {len(df[df['Manajemen Stres'] <= 2])} orang
    """
    st.download_button("📥 Download Laporan (TXT)", txt_data, "laporan_akademik.txt")