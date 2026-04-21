import streamlit as st
import random

# ==========================================
# GÜÇLENDİRİLMİŞ BİYOLOJİK MOTOR
# ==========================================
class BiovalentEngineV4:
    def __init__(self, sequence):
        self.seq = sequence.upper().strip().replace(" ", "")
        self.n = len(self.seq) if len(self.seq) > 0 else 1

    def full_analysis(self):
        # Parametre Hesaplamaları
        a, v, i, l = [self.seq.count(x)/self.n for x in "AVIL"]
        isi = (a + 2.9 * v + 3.9 * (i + l)) * 100
        instability = sum([self.seq.count(x) * 1.8 for x in "MSTNQ"]) / self.n * 10
        asidik, bazik = self.seq.count('D') + self.seq.count('E'), self.seq.count('K') + self.seq.count('R')
        pi = 7.0 + (bazik - asidik) * 0.1
        
        # 1. SICAKLIK DİRENCİ YORUMU
        if isi > 110: termal_durum = "🔥 Yüksek Sıcaklık Direnci (Ekstrem Koşullar)"
        elif isi > 85: termal_durum = "☀️ Orta-Yüksek Direnç (Yaz Mevsimi Uygun)"
        else: termal_durum = "❄️ Düşük Sıcaklık Direnci (Sadece Serin İklim)"
        
        # 2. HASTALIK VE STABİLİTE YORUMU
        if instability < 35: stabilite_durum = "🛡️ Yüksek Bağışıklık (Hücrede Uzun Süre Aktif)"
        elif instability < 45: stabilite_durum = "⚠️ Orta Hassasiyet (Stres Altında Bozulabilir)"
        else: stabilite_durum = "❌ Düşük Direnç (Hücresel Parçalanma Riski Yüksek)"

        # 3. SİSTEM UYUMU (HİDROPONİK)
        if 5.5 <= pi <= 6.8: pi_durum = "💧 Hidroponik / Topraksız Tarım İçin Kusursuz"
        else: pi_durum = "🪴 Sadece Topraklı Tarım (pH Hassasiyeti Var)"

        # GENEL SKORLAMA
        puan = 50
        if isi > 90: puan += 20
        if instability < 40: puan += 20
        if 5.5 <= pi <= 6.8: puan += 10
        
        status = "PLATINUM (ELİT TOHUM)" if puan >= 85 else "ALTIN (TİCARİ POTANSİYEL)" if puan >= 65 else "ELENDİ (ZAYIF VARYETE)"
        
        return {
            "Skor": puan, "Durum": status, "Isı": termal_durum, 
            "Stabilite": stabilite_durum, "Sistem": pi_durum, "pI_Val": round(pi, 2)
        }

# ==========================================
# UI: BİOVALENT KARAR PANELİ
# ==========================================
st.set_page_config(page_title="Biovalent Sentinel V4", layout="wide")
st.title("🧬 Biovalent Sentinel V4.0")
st.write("Bilmediğiniz gen dizilerini analiz edin ve biyolojik yorumlarını alın.")

col1, col2 = st.columns([1, 1.5])

with col1:
    dizi = st.text_area("Gen Dizisini Buraya Yapıştırın:", height=200)
    user_gen_adi = st.text_input("Gen Adı (Boş Bırakılabilir):", placeholder="Bilinmiyor")
    analiz_btn = st.button("STRATEJİK ANALİZİ BAŞLAT", type="primary")

if analiz_btn:
    if dizi:
        # İsim boşsa otomatik ata
        final_gen_adi = user_gen_adi if user_gen_adi else f"Biyovalent-Gen-{random.randint(100, 999)}"
        
        engine = BiovalentEngineV4(dizi)
        res = engine.full_analysis()
        
        with col2:
            st.header(f"📋 Rapor: {final_gen_adi}")
            
            # Ana Sonuç Kutusu
            color = "#00FFCC" if "PLATINUM" in res['Durum'] else "#FFD700" if "ALTIN" in res['Durum'] else "#FF4B4B"
            st.markdown(f"<div style='padding:20px; border-radius:10px; border: 2px solid {color};'>"
                        f"<h2 style='color:{color}; margin:0;'>{res['Durum']}</h2>"
                        f"<h3 style='margin:0;'>Elite Uyumluluk Skoru: %{res['Skor']}</h3>"
                        f"</div>", unsafe_allow_html=True)
            
            st.divider()
            
            # Detaylı Yorumlar
            st.subheader("🔍 Biyolojik Değerlendirme")
            st.info(res['Isı'])
            st.info(res['Stabilite'])
            st.info(res['Sistem'])
            
            st.write(f"**Teknik pH Değeri:** {res['pI_Val']}")
            
            if "PLATINUM" in res['Durum']:
                st.success("🎯 **Stratejik Tavsiye:** Bu gen, Vista Seeds'in 'Final 5' listesine girmeye adaydır. Derhal laboratuvar testlerine başlanması önerilir.")
    else:
        st.error("Lütfen bir dizi girin!")
