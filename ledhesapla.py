import streamlit as st
import pandas as pd
import math
from fpdf import FPDF

# --- AYARLAR ---
# Sizin verdiğiniz Google Sheet Linki üzerinden CSV çekme yapısı
SHEET_ID = "1HWfvaJgo_F-JrbQPbQahSUL9EeU8COTo-n1xxkaLfF0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- TÜRKÇE KARAKTER DÜZELTME ---
def tr(text):
    mapping = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}
    for t, e in mapping.items():
        text = str(text).replace(t, e)
    return text

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Knexxons LED Configurator", layout="wide", page_icon="🏗️")

# --- VERİ ÇEKME ---
@st.cache_data(ttl=60) # Listeyi her 1 dakikada bir kontrol eder
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip() # Sütun isimlerindeki boşlukları temizler
        return df
    except Exception as e:
        st.error(f"Google Sheets bağlantısı başarısız: {e}")
        return None

inventory_df = load_data()

if inventory_df is not None:
    # --- YAN PANEL (INPUTS) ---
    with st.sidebar:
        st.title("🛡️ Knexxons Admin")
        project_name = st.text_input("Proje / Müşteri Adı", "Örnek Teklif")
        
        st.divider()
        st.subheader("📦 Model Seçimi")
        # Google Sheet'teki "Marka_Model" sütununu baz alır
        selected_model = st.selectbox("Envanterden Seçin", inventory_df["Marka_Model"].tolist())
        
        # Seçili modelin tüm teknik verilerini çek
        m = inventory_df[inventory_df["Marka_Model"] == selected_model].iloc[0]
        
        st.divider()
        st.subheader("📐 Ekran Ölçüleri")
        target_w = st.number_input("Hedef Genişlik (mm)", value=3840, step=int(m["Genişlik"]))
        target_h = st.number_input("Hedef Yükseklik (mm)", value=2160, step=int(m["Yükseklik"]))
        
        st.divider()
        st.subheader("⚙️ Donanım & Kar")
        psu_amp = st.selectbox("PSU Amper", [40, 60, 80], index=0)
        profit_pct = st.slider("Kar Marjı (%)", 0, 100, 30)

    # --- HESAPLAMA MOTORU ---
    # Adetler
    nw = math.ceil(target_w / m["Genişlik"])
    nh = math.ceil(target_h / m["Yükseklik"])
    total_mod = nw * nh
    
    # Çözünürlük ve Teknik Veriler
    res_w, res_h = nw * int(m["Res_W"]), nh * int(m["Res_H"])
    total_px = res_w * res_h
    
    # Güç Kaynağı (PSU) Hesabı: (Adet * Watt) / (5V * Amper * 0.8 Emniyet)
    psu_count = math.ceil((total_mod * m["Watt"]) / (5 * psu_amp * 0.8))
    
    # Novastar Receiver Hesabı
    recv_count = math.ceil(total_px / 40000)

    # --- ANA EKRAN TASARIMI ---
    st.header(f"🏗️ Proje Analizi: {project_name}")
    st.info(f"Seçili Modül: **{selected_model}** | Parlaklık: **{m['Nit']} Nit**")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Toplam Modül", f"{total_mod} Adet", f"{nw}W x {nh}H")
    with c2: st.metric("Çözünürlük", f"{res_w} x {res_h}")
    with c3: st.metric("Güç Kaynağı", f"{psu_count} Adet", f"5V {psu_amp}A")
    with c4: st.metric("Gerçek Ölçü", f"{nw*m['Genişlik']} x {nh*m['Yükseklik']} mm")

    st.divider()

    # --- MALZEME TABLOSU ---
    st.subheader("📋 Teknik Teklif Detayları")
    items = [
        {"Bileşen": f"Knexxons LED Modül ({selected_model})", "Adet": f"{total_mod} Adet", "Teknik Özellik": f"{m['Res_W']}x{m['Res_H']} px / {m['Nit']} Nit"},
        {"Bileşen": f"5V {psu_amp}A Güç Kaynağı", "Adet": f"{psu_count} Adet", "Teknik Özellik": f"Verimlilik Odaklı %80 Load"},
        {"Bileşen": "Novastar Alıcı Kart (MRV Serisi)", "Adet": f"{recv_count} Adet", "Teknik Özellik": "Yüksek Tazeleme Hızı"},
        {"Bileşen": "Knexxons M4 Mıknatıs / Vida Seti", "Adet": f"{total_mod * 4} Adet", "Teknik Özellik": "Kolay Kurulum"},
    ]
    st.table(items)

    # --- FİYATLANDIRMA ---
    # Sheet'teki "Fiyat" sütununu kullanarak maliyet hesabı
    material_cost = (total_mod * m["Fiyat"]) + (psu_count * 16) + (recv_count * 22) + (total_mod * 2)
    final_sale = material_cost * (1 + profit_pct/100)
    
    st.success(f"### 💰 TAHMİNİ SATIŞ BEDELİ: ${final_sale:,.2f}")

    # --- PDF FONKSİYONU ---
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(190, 15, tr("KNEXXONS LED EKRAN TEKLIF FORMU"), ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 8, f"Proje: {tr(project_name)}", ln=True)
        pdf.cell(190, 8, f"Modul Tipi: {tr(selected_model)}", ln=True)
        pdf.cell(190, 8, f"Ekran Boyutu: {nw*m['Genişlik']}mm x {nh*m['Yükseklik']}mm", ln=True)
        pdf.cell(190, 8, f"Toplam Cozunurluk: {res_w} x {res_h} px", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(190, 10, tr("MALZEME LISTESI"), ln=True)
        pdf.set_font("Arial", "", 10)
        for item in items:
            pdf.cell(190, 7, f"- {tr(item['Bileşen'])}: {item['Adet']}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(190, 12, f"TOPLAM TEKLIF BEDELI: ${final_sale:,.2f}", ln=True, align='R')
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    # --- PDF İNDİRME BUTONU ---
    with st.sidebar:
        st.divider()
        st.download_button(
            label="📥 PDF TEKLİF DOSYASI",
            data=generate_pdf(),
            file_name=f"{tr(project_name)}_teklif.pdf",
            mime="application/pdf",
            use_container_width=True
        )

else:
    st.error("⚠️ Veri yüklenemedi. Lütfen Google Sheet linkini ve sütun isimlerini kontrol edin.")
