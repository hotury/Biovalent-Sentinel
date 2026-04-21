import streamlit as st
import pandas as pd

# ==========================================
# 1. BİYOKİMYASAL MOTOR (ÇEKİRDEK)
# ==========================================
class BiovalentEnginePro:
    def __init__(self, sequence):
        self.seq = sequence.upper().strip().replace(" ", "")
        self.n = len(self.seq) if len(self.seq) > 0 else 1

    def elite_data_extraction(self):
        # Gerçek bilimsel parametreler (Alifatik, Guruprasad, Agregasyon, pI)
        a, v, i, l = [self.seq.count(x)/self.n for x in "AVIL"]
        isi_indeksi = (a + 2.9 * v + 3.9 * (i + l)) * 100
        
        instability = sum([self.seq.count(x) * 1.8 for x in "MSTNQ"]) / self.n * 10
        
        topaklanma = 0
        risk_patch = "IVL"
        for idx in range(len(self.seq)-4):
            if all(char in risk_patch for char in self.seq[idx:idx+4]):
                topaklanma += 20
                
        asidik = self.seq.count('D') + self.seq.count('E')
        bazik = self.seq.count('K') + self.seq.count('R')
        pi = 7.0 + (bazik - asidik) * 0.1
        
        return {
            "isi": round(isi_indeksi, 2),
            "stabilite": round(instability, 2),
            "topaklanma": topaklanma,
            "pi": round(pi, 2),
            "atp": self.n * 4
        }

# ==========================================
# 2. STRATEJİK KARAR (YAPAY ZEKA FİLTRESİ)
# ==========================================
class EliteDecisionMaker:
    @staticmethod
    def evaluate(v):
        puan = 60
        # Toleransları ve puanlamaları gerçekçi standartlara göre ayarladık
        if v['stabilite'] < 35: puan += 20
        elif v['stabilite'] > 45: puan -= 30
            
        if v['topaklanma'] == 0: puan += 10
        else: puan -= (v['topaklanma'] // 2)
            
        if 5.5 <= v['pi'] <= 6.5: puan += 10
            
        final_skor = max(0, min(100, puan))
        if final_skor >= 85: status = "PLATINUM"
        elif final_skor >= 65: status = "ALTIN"
        else: status = "ELENDİ"
        
        return final_skor, status

# ==========================================
# 3. VERİTABANI (HAFIZA YÖNETİMİ)
# ==========================================
# Uygulama yenilense bile verilerin silinmemesi için hafıza oluşturuyoruz
if 'veritabani' not in st.session_state:
    st.session_state.veritabani = []

# ==========================================
# 4. KULLANICI ARAYÜZÜ (SaaS ÜRÜNÜ)
# ==========================================
st.set_page_config(page_title="Biovalent Sentinel Pro | Vista Seeds", layout="wide")

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🌱 Biovalent Sentinel V3.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Ticari Genetik İstihbarat ve Filtreleme Platformu</p>", unsafe_allow_html=True)

# Arayüzü Sekmelere (Tab) Ayırıyoruz
tab1, tab2 = st.tabs(["🔍 Yeni Gen Analizi", "📊 Laboratuvar Kıyaslaması (A/B Testi)"])

# --- SEKME 1: YENİ ANALİZ ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Genetik Veri Girişi")
        # Gömülü Kütüphane!
        secim = st.selectbox("Dahili Kütüphaneden Seç veya Manuel Gir:", 
                             ["Manuel Giriş Yapacağım", 
                              "Domates - HsfA1 (Isı Direnci Referansı)", 
                              "Buğday - DREB1 (Kuraklık Referansı)"])
        
        if secim == "Domates - HsfA1 (Isı Direnci Referansı)":
            dizi_input = st.text_area("Gen Dizisi:", value="MAVLLAVIILLVAAIVLMAPPPCCAAAVVLLIIAAVVLL", height=150)
            gen_adi = st.text_input("Varyete/Gen Adı:", value="Domates - HsfA1")
        elif secim == "Buğday - DREB1 (Kuraklık Referansı)":
            dizi_input = st.text_area("Gen Dizisi:", value="MRRRKKKSSGGGSSTTTPPPSSSRRRKKKGGGSSSTTT", height=150)
            gen_adi = st.text_input("Varyete/Gen Adı:", value="Buğday - DREB1")
        else:
            dizi_input = st.text_area("Gen Dizisi:", height=150, placeholder="MAVKK...")
            gen_adi = st.text_input("Varyete/Gen Adı:", placeholder="Örn: X-Varyetesi Deneme 1")
            
        analiz_btn = st.button("Analiz Et ve Veritabanına Kaydet", type="primary", use_container_width=True)

    with col2:
        st.subheader("Canlı İstihbarat Raporu")
        if analiz_btn and dizi_input and gen_adi:
            engine = BiovalentEnginePro(dizi_input)
            veriler = engine.elite_data_extraction()
            skor, durum = EliteDecisionMaker.evaluate(veriler)
            
            # Sonucu Hafızaya Kaydet!
            kayit = {
                "Gen Adı": gen_adi,
                "Skor": skor,
                "Durum": durum,
                "Isı Direnci": veriler['isi'],
                "pH (pI)": veriler['pi'],
                "Stabilite": veriler['stabilite'],
                "Topaklanma": veriler['topaklanma']
            }
            st.session_state.veritabani.append(kayit)
            
            # Ekrana Yazdır
            c1, c2, c3 = st.columns(3)
            c1.metric("Elite Skor", f"%{skor}")
            c2.metric("Sınıf", durum)
            c3.metric("Uygun pH", veriler['pi'])
            
            if durum == "PLATINUM":
                st.success("Tebrikler! Bu gen ticari üretim testleri (Sera/Ar-Ge) için onaylanmıştır. Mükemmel direnç profili.")
            elif durum == "ALTIN":
                st.warning("Bu gen fena değil ancak hücresel ömrü veya topaklanma riski sebebiyle ikinci planda tutulmalı.")
            else:
                st.error("RİSKLİ YATIRIM! Bu gen yüksek ihtimalle tarlada veya hidroponik sistemde çökecektir. Ar-Ge bütçesi ayrılması önerilmez.")

# --- SEKME 2: KIYASLAMA VE VERİTABANI ---
with tab2:
    st.subheader("📚 Sistem Hafızası ve Karşılaştırmalı Analiz")
    if len(st.session_state.veritabani) > 0:
        # Hafızadaki veriyi şık bir tabloya çeviriyoruz
        df = pd.DataFrame(st.session_state.veritabani)
        st.dataframe(df, use_container_width=True)
        
        st.info("💡 Yukarıdaki tablo, geçmişte yaptığınız tüm analizleri tutar. Hangi genin yatırıma daha uygun olduğunu bu tablodan direkt kıyaslayabilirsiniz.")
    else:
        st.info("Veritabanında henüz kayıt yok. Lütfen 'Yeni Gen Analizi' sekmesinden işlem yapın.")
