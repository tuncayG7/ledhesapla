import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image

# --- AYARLAR ---
SHEET_ID = "1HWfvaJgo_F-JrbQPbQahSUL9EeU8COTo-n1xxkaLfF0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOGO_URL = "https://raw.githubusercontent.com/tuncayG7/ledhesapla/main/G7_logo_lacivert.png"

def tr(text):
    mapping = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}
    for t, e in mapping.items(): text = str(text).replace(t, e)
    return text

# --- PDF SINIFI ---
class PDF(FPDF):
    def header(self):
        try:
            resp = requests.get(LOGO_URL)
            img = Image.open(BytesIO(resp.content))
            self.image(img, 10, 8, 45)
            self.set_x(60)
        except: pass
        self.set_font('Arial', 'B', 20); self.set_text_color(22, 43, 72)
        self.cell(0, 10, 'G7 TEKNOLOJI', ln=True, align='L')
        self.set_font('Arial', 'I', 9); self.set_text_color(100, 100, 100)
        if self.get_x() > 10: self.set_x(60)
        self.cell(0, 5, 'Profesyonel LED Ekran Cozumleri', ln=True, align='L')
        self.set_draw_color(22, 43, 72); self.line(10, 32, 200, 32); self.ln(10)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'G7 TEKNOLOJI | Teklif No: {datetime.now().strftime("%Y%m%d")} | Sayfa {self.page_no()}', 0, 0, 'C')

# --- PROGRAM ---
st.set_page_config(page_title="G7 TEKNOLOJİ | Teklif Paneli", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

inventory_df = load_data()

if inventory_df is not None:
    with st.sidebar:
        st.header("🏢 PROJE YAPILANDIRMA")
        customer_name = st.text_input("Müşteri / Firma", "Sayın Müşteri")
        project_name = st.text_input("Proje Tanımı", "İç Mekan Kurulum")
        
        # Ekran Tipi
        usage_type = st.radio("Ekran Kullanım Alanı", ["Indoor (İç Mekan)", "Outdoor (Dış Mekan)"])
        
        selected_model = st.selectbox("Model Seçin", inventory_df["Marka_Model"].tolist())
        m = inventory_df[inventory_df["Marka_Model"] == selected_model].iloc[0]
        
        target_w = st.number_input("Genişlik (mm)", value=3840, step=int(m["Genişlik"]))
        target_h = st.number_input("Yükseklik (mm)", value=2160, step=int(m["Yükseklik"]))
        
        st.divider()
        st.subheader("📺 Kontrol Sistemi")
        input_sources = st.slider("İhtiyaç Duyulan Giriş Sayısı (HDMI/DP/SDI)", 1, 6, 1)
        
        st.divider()
        st.subheader("⚡ Donanım & Finans")
        psu_amp = st.selectbox("PSU Amper", [40, 60, 80], index=0)
        hizmet_bedeli = st.number_input("Hizmet & Lojistik Bedeli ($)", value=1000)
        profit_pct = st.slider("Kar Marjı (%)", 0, 100, 25)

    # --- TEKNİK HESAPLAR ---
    nw, nh = math.ceil(target_w / m["Genişlik"]), math.ceil(target_h / m["Yükseklik"])
    total_mod = nw * nh
    res_w, res_h = nw * int(m["Res_W"]), nh * int(m["Res_H"])
    total_px = res_w * res_h
    aspect_ratio = round(res_w / res_h, 2)
    total_kva = round((total_mod * m["Watt"] * 1.25) / 1000, 1)

    # --- PROCESSOR KARAR MEKANİZMASI ---
    if input_sources > 2 or total_px > 3800000:
        processor_name = "Novastar VX1000 All-in-One Controller"
        proc_cost = 1400
    elif input_sources > 1 or total_px > 2300000:
        processor_name = "Novastar VX600 Video Processor"
        proc_cost = 950
    elif total_px > 1300000:
        processor_name = "Novastar VX400 Video Processor"
        proc_cost = 650
    else:
        processor_name = "Novastar MCTRL300 Sending Box"
        proc_cost = 250

    # PSU ve Receiver
    psu_count = math.ceil((total_mod * m["Watt"]) / (5 * psu_amp * 0.8))
    recv_count = math.ceil(total_px / 32000)

    # --- FİYAT DASHBOARD ---
    material_cost = (total_mod * m["Fiyat"]) + (psu_count * 22) + (recv_count * 30) + proc_cost + (total_mod * 4)
    final_sale_price = (material_cost + hizmet_bedeli) * (1 + profit_pct/100)

    st.title(f"🚀 G7 TEKNOLOJİ | Teklif Analizi")
    
    # Üst Bilgi Kartları
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("TOPLAM SATIŞ FİYATI", f"${final_sale_price:,.2f}")
    with c2: st.metric("Ekran Çözünürlüğü", f"{res_w}x{res_h}", f"{total_px:,} Px")
    with c3: st.metric("Enerji (kVA)", f"{total_kva} kVA")
    with c4: st.metric("Modül Sayısı", f"{total_mod} Adet")

    st.divider()

    # --- MALZEME TABLOSU ---
    st.subheader("📋 Teknik Teklif İçeriği")
    table_data = [
        {"Kalem": "LED Ekran Modul", "Marka / Model": f"Knexxons {selected_model}", "Miktar": f"{total_mod} Adet", "Teknik Aciklama": f"{usage_type} / {m['Nit']} Nit"},
        {"Kalem": "Video Processor", "Marka / Model": processor_name, "Miktar": "1 Adet", "Teknik Aciklama": f"{input_sources} Kaynak Girisi Destekli"},
        {"Kalem": "Receiver Card", "Marka / Model": "Novastar MRV336", "Miktar": f"{recv_count} Adet", "Teknik Aciklama": "3840Hz High Refresh"},
        {"Kalem": "Guc Kaynagi (PSU)", "Marka / Model": f"5V {psu_amp}A High Efficiency", "Miktar": f"{psu_count} Adet", "Teknik Aciklama": "Akilli Fan Sogutmali"},
        {"Kalem": "Hizmet ve Kurulum", "Marka / Model": "G7 TEKNOLOJI", "Miktar": "1 Proje", "Teknik Aciklama": "Muhendislik, Nakliye, Kablolama, Kurulum"},
    ]
    st.table(table_data)
    st.info("**Sistem Mühendisliği, Nakliye, Kablolama, Kurulum (Kabin Dışı Kablolama, Vinç ve Platform Müşteriye Ait)**")

    # --- PDF FONKSİYONU ---
    def generate_pdf():
        pdf = PDF()
        pdf.add_page()
        # PDF içeriği aynı mantıkla devam eder...
        pdf.set_font('Arial', 'B', 11); pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 8, tr("PROJE OZETI"), ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, " Musteri:"); pdf.cell(150, 7, tr(customer_name), ln=True)
        pdf.cell(40, 7, " Proje:"); pdf.cell(150, 7, tr(project_name), ln=True)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(22, 43, 72); pdf.set_text_color(255, 255, 255)
        pdf.cell(75, 10, tr(" Urun / Hizmet"), 1, 0, 'L', True)
        pdf.cell(75, 10, tr(" Marka / Model"), 1, 0, 'L', True)
        pdf.cell(40, 10, tr(" Miktar"), 1, 1, 'C', True)

        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 8)
        for row in table_data:
            pdf.cell(75, 8, tr(f" {row['Kalem']}"), 1)
            pdf.cell(75, 8, tr(f" {row['Marka / Model']}"), 1)
            pdf.cell(40, 8, tr(f" {row['Miktar']}"), 1, 1, 'C')

        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14); pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 12, f"TOPLAM TEKLIF BEDELI: ${final_sale_price:,.2f}", 1, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    with st.sidebar:
        st.divider()
        st.download_button("📥 G7 TEKNOLOJİ PROFESYONEL PDF İNDİR", generate_pdf(), f"G7_Teklif_{tr(customer_name)}.pdf", "application/pdf", use_container_width=True)
