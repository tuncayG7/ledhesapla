import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image

# --- KONFİGÜRASYON ---
SHEET_ID = "1HWfvaJgo_F-JrbQPbQahSUL9EeU8COTo-n1xxkaLfF0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# Logo için doğrudan RAW bağlantısı
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
            self.image(img, 10, 8, 45) # Logo boyutu ayarlandı
            self.set_x(60)
        except: pass
        
        self.set_font('Arial', 'B', 22); self.set_text_color(22, 43, 72)
        self.cell(0, 10, 'G7 TEKNOLOJI', ln=True, align='L')
        self.set_font('Arial', 'I', 10); self.set_text_color(100, 100, 100)
        if self.get_x() > 10: self.set_x(60)
        self.cell(0, 5, 'Endustriyel LED Ekran ve Goruntu Teknolojileri', ln=True, align='L')
        self.set_draw_color(22, 43, 72); self.line(10, 32, 200, 32); self.ln(12)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'G7 TEKNOLOJI | Teklif Formu | Sayfa {self.page_no()}', 0, 0, 'C')

# --- ANA PROGRAM ---
st.set_page_config(page_title="G7 TEKNOLOJİ | Teklif Paneli", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    return df

inventory_df = load_data()

if inventory_df is not None:
    with st.sidebar:
        st.header("🏢 PROJE AYARLARI")
        customer_name = st.text_input("Müşteri / Firma", "Sayın Müşteri")
        project_name = st.text_input("Proje Tanımı", "Knexxons Pro Serisi Kurulumu")
        
        selected_model = st.selectbox("LED Modül Modeli", inventory_df["Marka_Model"].tolist())
        m = inventory_df[inventory_df["Marka_Model"] == selected_model].iloc[0]
        
        target_w = st.number_input("Ekran Genişliği (mm)", value=3840, step=int(m["Genişlik"]))
        target_h = st.number_input("Ekran Yüksekliği (mm)", value=2160, step=int(m["Yükseklik"]))
        
        st.divider()
        st.subheader("⚡ Donanım Tercihleri")
        # PSU Seçimi Geri Eklendi
        psu_amp = st.selectbox("PSU Amper Seçimi (A)", [40, 60, 80], index=0)
        hizmet_bedeli = st.number_input("Kurulum ve Lojistik ($)", value=750)
        profit_pct = st.slider("Kar Oranı (%)", 0, 100, 25)

    # --- HESAPLAMALAR ---
    nw, nh = math.ceil(target_w / m["Genişlik"]), math.ceil(target_h / m["Yükseklik"])
    total_mod = nw * nh
    res_w, res_h = nw * int(m["Res_W"]), nh * int(m["Res_H"])
    total_px = res_w * res_h
    aspect_ratio = round(res_w / res_h, 2)
    total_kva = round((total_mod * m["Watt"] * 1.2) / 1000, 1)

    # Kontrolcü Zekası
    if total_px > 2300000:
        processor = "Novastar VX600 All-in-One"
    elif total_px > 1300000:
        processor = "Novastar VX400 All-in-One"
    else:
        processor = "Novastar MCTRL300 Sending Box"
    
    # PSU Adet Hesabı: Toplam Watt / (Voltaj(5V) * Amper * %80 Verim)
    psu_count = math.ceil((total_mod * m["Watt"]) / (5 * psu_amp * 0.8))

    # --- EKRAN DASHBOARD ---
    st.title(f"📊 G7 Teknoloji Analiz Paneli")
    st.info(f"Seçili Ürün: **{selected_model}** | Güç Kaynağı: **5V {psu_amp}A**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Çözünürlük", f"{res_w}x{res_h}", f"{total_px:,} Toplam Px")
    col2.metric("Ekran Ölçüsü", f"{nw*m['Genişlik']}x{nh*m['Yükseklik']} mm", f"{aspect_ratio}:1 Format")
    col3.metric("Enerji İhtiyacı", f"{total_kva} kVA", "Max Tüketim")
    col4.metric("Donanım", f"{psu_count} Adet PSU", f"{psu_amp} Amper")

    st.divider()

    # --- TEKNİKLER TABLOSU ---
    st.subheader("📝 Teklif Kalemleri")
    table_items = [
        {"Bileşen": "LED Ekran Modülü", "Marka / Model": f"Knexxons {selected_model}", "Adet": f"{total_mod} Adet", "Açıklama": f"{m['Nit']} Nit / 3840Hz"},
        {"Bileşen": "Video İşlemci (Processor)", "Marka / Model": processor, "Adet": "1 Adet", "Açıklama": "Görüntü Yönetim Ünitesi"},
        {"Bileşen": "Alıcı Kart (Receiver)", "Marka / Model": "Novastar MRV336", "Adet": f"{math.ceil(total_px/32000)} Adet", "Açıklama": "Piksel Sürme Kartı"},
        {"Bileşen": "Güç Kaynağı (PSU)", "Marka / Model": f"5V {psu_amp}A High Efficiency", "Adet": f"{psu_count} Adet", "Açıklama": "Slim Tip Güç Ünitesi"},
        {"Bileşen": "Hizmet Paketi", "Marka / Model": "G7 TEKNOLOJİ", "Adet": "1 Proje", "Açıklama": "Mühendislik, Nakliye, Kablolama, Kurulum"},
    ]
    st.table(table_items)
    st.write("> *Not: Kurulum hizmetine Kabin Dışı Kablolama dahildir. Vinç ve Platform Müşteriye Aittir.*")

    # --- PDF OLUŞTURMA ---
    def generate_pdf():
        pdf = PDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 11); pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 8, tr("PROJE VE MUSTERI DETAYLARI"), ln=True, fill=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(40, 7, " Musteri:"); pdf.cell(150, 7, tr(customer_name), ln=True)
        pdf.cell(40, 7, " Proje:"); pdf.cell(150, 7, tr(project_name), ln=True)
        pdf.cell(40, 7, " Tarih:"); pdf.cell(150, 7, datetime.now().strftime("%d/%m/%Y"), ln=True)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(22, 43, 72); pdf.set_text_color(255, 255, 255)
        pdf.cell(75, 10, tr(" Urun / Hizmet"), 1, 0, 'L', True)
        pdf.cell(70, 10, tr(" Marka / Model"), 1, 0, 'L', True)
        pdf.cell(45, 10, tr(" Miktar"), 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 8)
        for row in table_items:
            pdf.cell(75, 8, tr(f" {row['Bileşen']}"), 1)
            pdf.cell(70, 8, tr(f" {row['Marka / Model']}"), 1)
            pdf.cell(45, 8, tr(f" {row['Adet']}"), 1, 1, 'C')

        pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 8, "TEKNIK VERILER:", ln=True)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 6, tr(f"- Cozunurluk: {res_w}x{res_h} px (Toplam {total_px:,} Piksel)"), ln=True)
        pdf.cell(0, 6, tr(f"- Enerji Tuketimi: {total_kva} kVA (Max Load)"), ln=True)
        pdf.cell(0, 6, tr(f"- Parlaklik: {m['Nit']} Nit | Yenileme Hizi: 3840 Hz"), ln=True)

        pdf.ln(10)
        # Basit fiyat hesabı (Hizmet bedeli dahil)
        material_sum = (total_mod * m["Fiyat"]) + (psu_count * 20) + (math.ceil(total_px/32000) * 25)
        total_price = (material_sum + hizmet_bedeli) * (1 + profit_pct/100)
        
        pdf.set_font('Arial', 'B', 14); pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 12, f"TOPLAM TEKLIF BEDELI: ${total_price:,.2f}", 1, 1, 'R')
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    st.sidebar.divider()
    st.sidebar.download_button("📥 PROFESYONEL PDF'İ İNDİR", generate_pdf(), f"G7_{tr(customer_name)}.pdf", "application/pdf", use_container_width=True)
