import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import urllib.request
from io import BytesIO

# --- YAPILANDIRMA ---
SHEET_ID = "1HWfvaJgo_F-JrbQPbQahSUL9EeU8COTo-n1xxkaLfF0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# Logoyu ham (raw) formatta çekiyoruz
LOGO_URL = "https://raw.githubusercontent.com/tuncayG7/ledhesapla/main/G7_logo_lacivert.png"

def tr(text):
    mapping = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}
    for t, e in mapping.items(): text = str(text).replace(t, e)
    return text

class PDF(FPDF):
    def header(self):
        try:
            req = urllib.request.Request(LOGO_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                logo_data = BytesIO(response.read())
                self.image(logo_data, 10, 8, 40)
            self.set_x(55)
        except: pass
        
        self.set_font('Arial', 'B', 20)
        self.set_text_color(22, 43, 72)
        self.cell(0, 10, 'G7 TEKNOLOJI', ln=True, align='L' if self.get_x() > 10 else 'C')
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        if self.get_x() > 10: self.set_x(55)
        self.cell(0, 5, 'Endustriyel LED Ekran Sistemleri ve Goruntu Teknolojileri', ln=True, align='L')
        self.set_draw_color(22, 43, 72)
        self.line(10, 32, 200, 32)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'G7 TEKNOLOJI | www.g7.com.tr | Sayfa {self.page_no()}', 0, 0, 'C')

# --- VERİ VE ARAYÜZ ---
st.set_page_config(page_title="G7 TEKNOLOJİ | Teklif Sistemi", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

inventory_df = load_data()
if inventory_df is not None:
    with st.sidebar:
        st.header("🏢 TEKLİF YÖNETİMİ")
        customer_name = st.text_input("Müşteri / Firma", "Sayın Müşteri")
        project_name = st.text_input("Proje Tanımı", "İç Mekan LED Ekran Projesi")
        selected_model = st.sidebar.selectbox("Model Seçin", inventory_df["Marka_Model"].tolist())
        m = inventory_df[inventory_df["Marka_Model"] == selected_model].iloc[0]
        
        target_w = st.number_input("Genişlik (mm)", value=3840, step=int(m["Genişlik"]))
        target_h = st.number_input("Yükseklik (mm)", value=2160, step=int(m["Yükseklik"]))
        profit_pct = st.slider("Kar Oranı (%)", 0, 100, 30)

    # --- HESAPLAMALAR ---
    nw, nh = math.ceil(target_w / m["Genişlik"]), math.ceil(target_h / m["Yükseklik"])
    total_mod = nw * nh
    res_w, res_h = nw * int(m["Res_W"]), nh * int(m["Res_H"])
    total_px = res_w * res_h
    aspect_ratio = round(res_w / res_h, 2)
    
    # Güç ve Enerji (kVA Hesabı: (Watt * Modül) / 1000 * 1.2 verimlilik)
    total_kva = round((total_mod * m["Watt"] * 1.2) / 1000, 1)
    
    # Donanım
    psu_count = math.ceil((total_mod * m["Watt"]) / 220) # 5V 40A PSU bazlı
    recv_count = math.ceil(total_px / 40000)
    
    # Fiyat
    unit_cost = (total_mod * m["Fiyat"]) + (psu_count * 18) + (recv_count * 25) + (total_mod * 2.5)
    final_sale = unit_cost * (1 + profit_pct/100)

    # --- EKRAN GÖRÜNÜMÜ ---
    st.title(f"🔍 Teknik İnceleme: {selected_model}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Piksel", f"{total_px:,}")
    col2.metric("Görüntü Formatı", f"{aspect_ratio}:1")
    col3.metric("Maks. Güç", f"{total_kva} kVA")
    col4.metric("Yenileme Hızı", "3840 Hz")

    # --- PDF OLUŞTURMA ---
    def generate_pro_pdf():
        pdf = PDF()
        pdf.add_page()
        
        # Müşteri Bilgileri
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 8, tr("PROJE VE MUSTERI BILGILERI"), ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, " Musteri:"); pdf.cell(150, 7, tr(customer_name), ln=True)
        pdf.cell(40, 7, " Proje Adi:"); pdf.cell(150, 7, tr(project_name), ln=True)
        pdf.cell(40, 7, " Teklif Tarihi:"); pdf.cell(150, 7, datetime.now().strftime("%d/%m/%Y"), ln=True)
        pdf.ln(5)

        # Teknik Tablo
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(190, 8, tr("TEKNIK SPEKTRUM VE DONANIM"), ln=True)
        pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(22, 43, 72); pdf.set_text_color(255, 255, 255)
        pdf.cell(130, 8, tr(" Urun / Donanim Tanimi"), 1, 0, 'L', True)
        pdf.cell(60, 8, tr(" Teknik Detay / Adet"), 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0)
        specs = [
            (f"{selected_model} LED Ekran Modulu", f"{total_mod} Adet"),
            ("Cozunurluk Yapisi", f"{res_w} x {res_h} (Toplam: {total_px:,} Px)"),
            ("Goruntu Formati / Orani", f"{aspect_ratio}:1"),
            ("Yenileme Hizi (Refresh Rate)", "3840 Hz"),
            ("Maksimum Parlaklik", f"> {m['Nit']} cd/m2"),
            ("Enerji Gereksinimi (Max)", f"{total_kva} kVA"),
            ("Novastar Kontrol Sistemi", f"{recv_count} Alici Kart / 1 Adet Master"),
            ("Montaj Ekipmanlari", "Knexxons Magnetik M4 Set")
        ]
        for spec, val in specs:
            pdf.cell(130, 7, tr(f" {spec}"), 1)
            pdf.cell(60, 7, tr(f" {val}"), 1, 1, 'C')

        # Fiyat Paneli
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14); pdf.set_text_color(22, 43, 72)
        pdf.cell(190, 15, f"TOPLAM PROJE BEDELI: ${final_sale:,.2f}", 1, 1, 'R')
        
        pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, tr("\n* Fiyatlara KDV dahil degildir. \n* Knexxons moduller G7 TEKNOLOJI garantisi altindadir. \n* Teklif 10 gun sureyle gecerlidir."))
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    st.sidebar.divider()
    st.sidebar.download_button("📥 TEKNİK TEKLİFİ İNDİR (PDF)", generate_pro_pdf(), f"G7_{tr(customer_name)}.pdf", "application/pdf", use_container_width=True)
