import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image

# --- AYARLAR ---
SHEET_ID = "1a6P6Jr_yaiDvbnh3OJ8z_whw1txGOjmyzT0U0jWZTDw"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOGO_URL = "https://raw.githubusercontent.com/tuncayG7/ledhesapla/main/G7_logo_lacivert.png"

st.set_page_config(page_title="G7 TEKNOLOJI | Teklif Paneli", layout="wide")

def tr(text):
    m = {"ç":"c","Ç":"C","ğ":"g","Ğ":"G","ı":"i","İ":"I","ö":"o","Ö":"O","ş":"s","Ş":"S","ü":"u","Ü":"U"}
    for k, v in m.items(): text = str(text).replace(k, v)
    return text

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

df = load_data()

# --- SOL MENU (FILTRELER) ---
if df is not None:
    with st.sidebar:
        st.header("🔍 URUN SECIMI")
        customer = st.text_input("Musteri Adi", "Sayin Musteri")
        
        # Filtreleme Hiyerarsisi
        env_list = sorted(df[df['tip'].str.contains('modul', case=False, na=False)]['ortam'].unique())
        env_choice = st.selectbox("Kullanim Ortami", env_list)
        
        tech_list = sorted(df[(df['tip'].str.contains('modul', case=False, na=False)) & (df['ortam'] == env_choice)]['teknoloji'].unique())
        tech_choice = st.selectbox("LED Teknolojisi", tech_list)
        
        final_list = df[(df['tip'].str.contains('modul', case=False, na=False)) & 
                        (df['ortam'] == env_choice) & 
                        (df['teknoloji'] == tech_choice)]['model'].tolist()
        
        if final_list:
            sel_model = st.selectbox("Model Secin", final_list)
            st.divider()
            st.header("📐 EKRAN BOYUTLARI")
            w_mm = st.number_input("Genislik (mm)", value=3840)
            h_mm = st.number_input("Yukseklik (mm)", value=2160)
            profit = st.slider("Kar Marji (%)", 0, 100, 25)
            has_box = st.checkbox("Kasa Dahil", value=True)
        else:
            st.error("Bu kriterlerde model bulunamadi.")
            st.stop()

    # --- ANA SAYFA HESAPLAMA VE GORSELLESTIRME (SAG TARAF) ---
    m = df[df['model'] == sel_model].iloc[0]
    
    # Teknik Analiz
    nw, nh = math.ceil(w_mm / m['genislik']), math.ceil(h_mm / m['yukseklik'])
    total_mod = nw * nh
    total_px = (nw * m['res_w']) * (nh * m['res_h'])
    m2 = (w_mm * h_mm) / 1_000_000
    
    # Islemci Secimi
    procs = df[df['tip'].str.contains('processor', case=False, na=False)].sort_values('res_w')
    selected_proc = procs[procs['res_w'] >= total_px].iloc[0]
    
    # Maliyetler
    mod_p = float(m['msrp'])
    proc_p = float(selected_proc['msrp'])
    recv_p = 35.0 # Tablodan dinamik de cekilebilir
    psu_p = 22.0
    
    elek_maliyet = (total_mod * mod_p) + (math.ceil(total_px/32000) * recv_p) + (math.ceil(total_mod/8) * psu_p) + proc_p
    box_unit = 170 if env_choice == "Outdoor" else 80
    box_maliyet = (m2 * box_unit) if has_box else 0
    
    hizmet = (elek_maliyet + box_maliyet) * 0.10
    final_sale = (elek_maliyet + box_maliyet + hizmet) * (1 + profit/100)

    # --- SAG TARAF TASARIMI ---
    st.title(f"🚀 G7 TEKNOLOJI | Teklif Dashboard")
    st.markdown(f"### **{sel_model}** - {env_choice} / {tech_choice}")
    
    # Ust Metrikler
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOPLAM SATIS", f"$ {final_sale:,.2f}")
    c2.metric("Hizmet Bedeli", f"$ {hizmet*(1+profit/100):,.2f}")
    c3.metric("Cozunurluk", f"{int(nw*m['res_w'])}x{int(nh*m['res_h'])}")
    c4.metric("Toplam Modul", f"{total_mod} Adet")
    
    st.divider()

    # Icerik Tablosu ve Detaylar
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📦 Teklif Detaylari")
        data = [
            {"Bilesen": "Elektronik Paket", "Detay": f"{sel_model} + {selected_proc['model']}", "Tutar": f"$ {elek_maliyet*(1+profit/100):,.2f}"},
            {"Bilesen": "Kasa / Kabinet", "Detay": f"{env_choice} Standart ({m2:.2f} m2)", "Tutar": f"$ {box_maliyet*(1+profit/100):,.2f}"},
            {"Bilesen": "G7 Sistem Hizmetleri", "Detay": "Montaj, Lojistik, Teknik Destek", "Tutar": f"$ {hizmet*(1+profit/100):,.2f}"}
        ]
        st.table(data)
        
    with col_right:
        st.subheader("📝 Teknik Ozellikler")
        st.write(f"**Modul Boyutu:** {m['genislik']} x {m['yukseklik']} mm")
        st.write(f"**Panel Cozunurlugu:** {m['res_w']} x {m['res_h']} px")
        st.write(f"**Secilen Islemci:** {selected_proc['model']}")
        st.write(f"**Guc Kaynagi Ihtiyaci:** {math.ceil(total_mod/8)} Adet (5V 40A)")
        
        # PDF Butonu
        st.download_button("📥 Teklifi PDF Olarak Indir", "PDF Icerigi Burada Olacak", use_container_width=True)

    st.success(f"Bilgi: Kasa birim fiyati {env_choice} ortam kriterine gore ${box_unit}/m2 olarak otomatik uygulanmistir.")
