import streamlit as st
import math

# --- GENİŞLETİLMİŞ VERİ TABANI ---
DATA = {
    "İç Mekan (Indoor)": {
        "Qiangli Q1.8": {"w": 320, "h": 160, "res_w": 172, "res_h": 86, "power": 30, "price": 45, "bright": "800 nit"},
        "Qiangli Q2.5": {"w": 320, "h": 160, "res_w": 128, "res_h": 64, "power": 35, "price": 25, "bright": "1000 nit"},
        "Qiangli Q3": {"w": 192, "h": 192, "res_w": 64, "res_h": 64, "power": 25, "price": 18, "bright": "1100 nit"}
    },
    "Dış Mekan (Outdoor)": {
        "Qiangli P4 Outdoor": {"w": 320, "h": 160, "res_w": 80, "res_h": 40, "power": 45, "price": 35, "bright": "5500 nit"},
        "Qiangli P5 Outdoor": {"w": 320, "h": 160, "res_w": 64, "res_h": 32, "power": 50, "price": 28, "bright": "6000 nit"},
        "Qiangli P10 Outdoor": {"w": 320, "h": 160, "res_w": 32, "res_h": 16, "power": 40, "price": 20, "bright": "6500 nit"}
    }
}

st.set_page_config(page_title="LED Pro Enterprise", layout="wide")
st.title("🏗️ Profesyonel LED Ekran Projelendirme ve Teklif Sistemi")

# --- YAN PANEL (GİRDİLER) ---
with st.sidebar:
    st.header("1. Teknik Konfigürasyon")
    env_type = st.radio("Kullanım Alanı", ["İç Mekan (Indoor)", "Dış Mekan (Outdoor)"])
    selected_modul = st.selectbox("Modül Seçin", list(DATA[env_type].keys()))
    
    target_w = st.number_input("Genişlik (mm)", value=3840, step=160)
    target_h = st.number_input("Yükseklik (mm)", value=2160, step=160)
    
    st.divider()
    st.header("2. Kontrol & Girişler")
    multi_input = st.toggle("Birden Fazla Video Girişi (HDMI/SDI/DP)", value=False)
    
    st.divider()
    st.header("3. Operasyonel Giderler ($)")
    labor_cost = st.number_input("Montaj ve İşçilik", value=250)
    shipping_cost = st.number_input("Nakliye ve Lojistik", value=100)
    fixed_overhead = st.number_input("Diğer Sabit Giderler", value=50)
    
    st.divider()
    profit_margin = st.slider("Hedef Kar Marjı (%)", 5, 100, 25)

# --- HESAPLAMA MOTORU ---
mod = DATA[env_type][selected_modul]

nw = math.ceil(target_w / mod["w"])
nh = math.ceil(target_h / mod["h"])
total_mod = nw * nh

res_w, res_h = nw * mod["res_w"], nh * mod["res_h"]
total_px = res_w * res_h

# Donanım Seçimi
psu_count = math.ceil((total_mod * mod["power"]) / 220)
recv_count = math.ceil(total_px / (128 * 256)) # Güvenli sınır

if multi_input:
    sender_name = "Novastar VX400 (Processor)" if total_px < 2.3e6 else "Novastar VX600 (Processor)"
    sender_price = 650 if total_px < 2.3e6 else 1150
else:
    sender_name = "Novastar MSD300 (Sender)" if total_px < 1.3e6 else "Novastar MCTRL660 (Box)"
    sender_price = 180 if total_px < 1.3e6 else 480

# --- MALİYET ANALİZİ ---
items = [
    {"Ürün": f"{selected_modul} Modül", "Adet": total_mod, "Birim $": mod["price"]},
    {"Ürün": "Güç Kaynağı (5V 40A/60A)", "Adet": psu_count, "Birim $": 14},
    {"Ürün": "Novastar Alıcı Kart", "Adet": recv_count, "Birim $": 18},
    {"Ürün": f"Kontrolcü: {sender_name}", "Adet": 1, "Birim $": sender_price},
    {"Ürün": "Mıknatıs / Bağlantı Aparatı", "Adet": total_mod * 4, "Birim $": 0.45},
]

material_cost = sum(i["Adet"] * i["Birim $"] for i in items)
total_expense = material_cost + labor_cost + shipping_cost + fixed_overhead
final_sale_price = total_expense * (1 + profit_margin / 100)

# --- ARAYÜZ ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Gerçek Ölçü", f"{nw * mod['w']} x {nh * mod['h']} mm")
c2.metric("Toplam Modül", f"{total_mod} Adet")
c3.metric("Çözünürlük", f"{res_w}x{res_h} px")
c4.metric("Net Maliyet", f"${total_expense:,.0f}")

st.divider()

col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("📋 Detaylı Malzeme Listesi")
    st.table(items)
    
with col_b:
    st.subheader("💰 Finansal Özet")
    st.write(f"**Malzeme Toplamı:** ${material_cost:,.2f}")
    st.write(f"**Operasyonel Giderler:** ${labor_cost + shipping_cost + fixed_overhead:,.2f}")
    st.write(f"**Hedef Kar:** ${final_sale_price - total_expense:,.2f}")
    st.info(f"### Önerilen Satış: ${final_sale_price:,.2f}")

st.divider()
st.caption(f"ℹ️ {sender_name} seçildi. Toplam yönetilen piksel: {total_px:,}. {env_type} standartlarında hesaplanmıştır.")