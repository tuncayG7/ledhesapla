import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO

# --- AYARLAR ---
SHEET_ID = "1HWfvaJgo_F-JrbQPbQahSUL9EeU8COTo-n1xxkaLfF0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# GitHub logo ham bağlantısı (RAW formatı)
LOGO_URL = "https://raw.githubusercontent.com/tuncayG7/ledhesapla/main/G7_logo_lacivert.png"

# --- TÜRKÇE KARAKTER DÜZELTME ---
def tr(text):
    mapping = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}
    for t, e in mapping.items():
        text = str(text).replace(t, e)
    return text

# --- PDF SINIFI (G7 TEKNOLOJİ ÖZEL ŞABLON) ---
class PDF(FPDF):
    def header(self):
        try:
            # Logoyu internet üzerinden çekip ekleme
            response = requests.get(LOGO_URL)
            if response.status_code == 200:
                logo_data = BytesIO(response.content)
                self.image(logo_data, 10, 8, 35) # Logo boyutu
                self.set_x(50)
        except:
            pass # Logo yüklenemezse hata verme, devam et
        
        self.set_font('Arial', 'B', 22)
        self.set_text_color(22, 43, 72) # G7 Lacivert tonu
        self.cell(0, 10, 'G7 TEKNOLOJI', ln=True, align='L' if self.get_x() > 10 else 'L')
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        if self.get_x() > 10: self.set_x(50)
        self.cell(0, 5, 'Profesyonel LED Ekran Cozumleri', ln=True, align='L')
        
        # Kurumsal çizgi
        self.set_draw_color(22, 43, 72)
        self.line(10, 32, 200, 32)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Sayfa {self.page_no()} | G7 TEKNOLOJI - {datetime.now().strftime("%d/%m/%Y")}', 0, 0, 'C')

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="G7 TEKNOLOJİ | Teklif Sistemi", layout="wide", page_icon="🏢")

# --- VERİ ÇEKME ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Google Sheets verisi alınamadı: {e}")
        return None

inventory_df = load_data()

if inventory_df is not None:
    # --- YAN PANEL ---
    with st.sidebar:
        st.header("🏢 G7 TEKNOLOJİ PANEL")
        customer_name = st.text_input("Müşteri / Firma Adı", "Sayın Müşteri")
        project_name = st.text_input("Proje Adı", "Knexxons LED Ekran Kurulumu")
        
        st.divider()
        selected_model = st.selectbox("Model Seçin", inventory_df["Marka_Model"].tolist())
        m = inventory_df[inventory_df["Marka_Model"] == selected_model].iloc[0]
        
        target_w = st.number_input("Ekran Genişliği (mm)", value=3840, step=int(m["Genişlik"]))
        target_h = st.number_input("Ekran Yüksekliği (mm)", value=2160, step=int(m["Yükseklik"]))
        
        psu_amp = st.selectbox("Güç Kaynağı Amper", [40, 60, 80], index=0)
        profit_pct = st.slider("Kar Oranı (%)", 0, 100, 30)

    # --- HESAPLAMALAR ---
    nw = math.ceil(target_w / m["Genişlik"])
    nh = math.ceil(target_h / m["Yükseklik"])
    total_mod = nw * nh
    res_w, res_h = nw * int(m["Res_W"]), nh * int(m["Res_H"])
    psu_count = math.ceil((total_mod * m["Watt"]) / (5 * psu_amp * 0.8))
    recv_count = math.ceil((res_w * res_h) / 40000)

    # Fiyatlandırma
    material_cost = (total_mod * m["Fiyat"]) + (psu_count * 18) + (recv_count * 25) + (total_mod * 2)
    final_sale = material_cost * (1 + profit_pct/100)

    # --- EKRAN ÇIKTILARI ---
    st.subheader(f"📄 Teklif Özeti: {customer_name} / {project_name}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gerçek Boyut", f"{nw*m['Genişlik']}x{nh*m['Yükseklik']} mm")
    c2.metric("Çözünürlük", f"{res_w}x{res_h} px")
    c3.metric("Modül Sayısı", f"{total_mod} Adet")
    c4.metric("Satış Fiyatı", f"${final_sale:,.2f}")

    st.divider()

    # Tablo Verisi
    table_data = [
        {"Ürün Açıklaması": f"Knexxons {selected_model} LED Modül ({m['Nit']} Nit)", "Adet": f"{total_mod} Adet"},
        {"Ürün Açıklaması": f"5V {psu_amp}A Yüksek Verimli Güç Kaynağı", "Adet": f"{psu_count} Adet"},
        {"Ürün Açıklaması": "Novastar Alıcı Kart / Receiver Card", "Adet": f"{recv_count} Adet"},
        {"Ürün Açıklaması": "Knexxons M4 Mıknatıs / Montaj Seti", "Adet": f"{total_mod * 4} Adet"},
        {"Ürün Açıklaması": "Data ve Enerji Kablo/Soket Grubu", "Adet": "1 Takım"}
    ]
    st.table(table_data)

    # --- PDF FONKSİYONU ---
    def generate_pdf():
        pdf = PDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(190, 8, tr("TEKLIF DETAYLARI"), ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, tr(" Musteri:"), 0); pdf.cell(150, 7, tr(customer_name), ln=True)
        pdf.cell(40, 7, tr(" Proje Adi:"), 0); pdf.cell(150, 7, tr(project_name), ln=True)
        pdf.cell(40, 7, tr(" Tarih:"), 0); pdf.cell(150, 7, datetime.now().strftime("%d/%m/%Y"), ln=True)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(22, 43, 72); pdf.set_text_color(255, 255, 255)
        pdf.cell(150, 10, tr(" Urun Aciklamasi"), 1, 0, 'L', True)
        pdf.cell(40, 10, tr(" Miktar"), 1, 1, 'C', True)

        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
        for row in table_data:
            pdf.cell(150, 8, tr(f" {row['Ürün Açıklaması']}"), 1)
            pdf.cell(40, 8, tr(row['Adet']), 1, 1, 'C')

        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 12, f"TOPLAM TEKLIF BEDELI: ${final_sale:,.2f}", 1, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    with st.sidebar:
        st.divider()
        st.download_button(
            label="📥 G7 TEKNOLOJİ PDF OLUŞTUR",
            data=generate_pdf(),
            file_name=f"G7_Teknoloji_{tr(customer_name)}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
