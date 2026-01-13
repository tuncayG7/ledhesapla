import streamlit as st
import math
from fpdf import FPDF

# --- TÜRKÇE KARAKTER DÜZELTME ---
def tr(text):
    mapping = {"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U"}
    for t, e in mapping.items():
        text = str(text).replace(t, e)
    return text

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="LED Pro", layout="wide")

# --- VERİ TABANI ---
DATA = {
    "İç Mekan (Indoor)": {
        "Qiangli Q1.8": {"w": 320, "h": 160, "res_w": 172, "res_h": 86, "power": 30, "price": 45},
        "Qiangli Q2.5": {"w": 320, "h": 160, "res_w": 128, "res_h": 64, "power": 35, "price": 25},
        "Qiangli Q3": {"w": 192, "h": 192, "res_w": 64, "res_h": 64, "power": 25, "price": 18}
    },
    "Dış Mekan (Outdoor)": {
        "Qiangli P4 Outdoor": {"w": 320, "h": 160, "res_w": 80, "res_h": 40, "power": 45, "price": 35},
        "Qiangli P10 Outdoor": {"w": 320, "h": 160, "res_w": 32, "res_h": 16, "power": 40, "price": 20}
    }
}

# --- SOL PANEL (INPUTS) ---
st.sidebar.header("🔧 PROJE AYARLARI")
project_name = st.sidebar.text_input("Proje Adı", "Yeni Proje")
env_type = st.sidebar.radio("Ortam", list(DATA.keys()))
selected_modul = st.sidebar.selectbox("Modül Seçin", list(DATA[env_type].keys()))

target_w = st.sidebar.number_input("Genişlik (mm)", value=3200)
target_h = st.sidebar.number_input("Yükseklik (mm)", value=1920)

multi_input = st.sidebar.toggle("Çoklu Giriş (Processor Gerekir)", value=False)
labor = st.sidebar.number_input("İşçilik Maliyeti ($)", value=200)
shipping = st.sidebar.number_input("Nakliye ($)", value=100)
profit = st.sidebar.slider("Kar Oranı (%)", 0, 100, 25)

# --- HESAPLAMALAR ---
mod = DATA[env_type][selected_modul]
nw = math.ceil(target_w / mod["w"])
nh = math.ceil(target_h / mod["h"])
total_mod = nw * nh
res_w, res_h = nw * mod["res_w"], nh * mod["res_h"]
total_px = res_w * res_h

psu_count = math.ceil((total_mod * mod["power"]) / 220)
recv_count = math.ceil(total_px / 40000) # Güvenli bölge

if multi_input:
    sender_name = "Novastar VX400 (Processor)"
    sender_price = 650
else:
    sender_name = "Novastar MSD300" if total_px < 1.3e6 else "Novastar MCTRL660"
    sender_price = 180 if total_px < 1.3e6 else 450

# MALİYET TABLOSU
material_cost = (total_mod * mod["price"]) + (psu_count * 15) + (recv_count * 20) + sender_price + (total_mod * 2)
total_expense = material_cost + labor + shipping
final_price = total_expense * (1 + profit/100)

# --- ANA EKRAN GÖRÜNÜMÜ ---
st.header(f"📊 {project_name} - Özet")
c1, c2, c3 = st.columns(3)
c1.metric("Toplam Modül", f"{total_mod} Adet")
c2.metric("Çözünürlük", f"{res_w}x{res_h}")
c3.metric("Satış Fiyatı", f"${final_price:,.2f}")

st.divider()
st.subheader("📦 Malzeme Listesi")
st.write(f"- **Modül:** {total_mod} Adet {selected_modul}")
st.write(f"- **Güç Kaynağı:** {psu_count} Adet 5V 40A")
st.write(f"- **Alıcı Kart:** {recv_count} Adet Novastar MRV")
st.write(f"- **Kontrolcü:** 1 Adet {sender_name}")

# --- PDF HAZIRLAMA BÖLÜMÜ ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, tr("LED EKRAN TEKLIF FORMU"), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Proje: {tr(project_name)}", ln=True)
    pdf.cell(190, 10, f"Modul: {tr(selected_modul)}", ln=True)
    pdf.cell(190, 10, f"Boyut: {nw*mod['w']}mm x {nh*mod['h']}mm", ln=True)
    pdf.cell(190, 10, f"Cozunurluk: {res_w}x{res_h} px", ln=True)
    pdf.cell(190, 10, f"Kontrolcu: {tr(sender_name)}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, f"TOPLAM TEKLIF: ${final_price:,.2f}", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# BUTONUN YERİ: Sidebar'ın en üstüne veya altına koyabiliriz. 
# Burada hem ana sayfada hem sidebar'da gösteriyoruz ki kaçmasın.
with st.sidebar:
    st.divider()
    st.subheader("📑 Doküman")
    pdf_file = create_pdf()
    st.download_button(
        label="📥 PDF OLARAK İNDİR",
        data=pdf_file,
        file_name="teklif.pdf",
        mime="application/pdf",
        use_container_width=True
    )
