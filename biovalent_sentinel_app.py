import streamlit as st
import numpy as np
import plotly.graph_objects as go

# SAYFA AYARLARI (En üstte olmalı)
st.set_page_config(page_title="Biovalent Sentinel", layout="wide")

# ==========================================
# MOTORLAR (Sınıf tanımları)
# ==========================================
class BiovalentEngine:
    def __init__(self, sequence):
        self.seq = sequence.upper().strip().replace(" ", "")
        self.n = len(self.seq) if len(self.seq) > 0 else 1

    def fiziksel_analiz(self):
        a = self.seq.count('A') / self.n
        v = self.seq.count('V') / self.n
        i = self.seq.count('I') / self.n
        l = self.seq.count('L') / self.n
        isi_indeksi = (a + 2.9 * v + 3.9 * (i + l)) * 100
        atp_maliyeti = self.n * 4 
        return {"isi_direnci": round(isi_indeksi, 2), "metabolik_yuk": atp_maliyeti}

    def stres_testi(self):
        direnc = (self.seq.count('C') * 2) + self.seq.count('P') + 5
        sicakliklar = np.arange(20, 75, 5)
        egri = [max(0, min(100, 100 - ((max(0, t - 37) * 0.15 * 100) / direnc))) for t in sicakliklar]
        riskler = []
        if "RR" in self.seq or "KK" in self.seq: riskler.append("Yüksek Parçalanma Riski (RR/KK)")
        return {"sicakliklar": sicakliklar.tolist(), "egri": egri, "riskler": riskler}

class BiovalentStrategist:
    def __init__(self, f_veri, s_veri, iklim):
        self.f = f_veri
        self.s = s_veri
        self.iklim = iklim

    def skorla(self):
        skor = 60
        notlar = []
        if self.iklim == "Sıcak":
            if self.f['isi_direnci'] > 110:
                skor += 20
                notlar.append("✅ Sıcak iklim adaptasyonu yüksek.")
            else:
                skor -= 25
                notlar.append("⚠️ Isı stresi altında çökme riski!")
        skor -= (len(self.s['riskler']) * 15)
        final_skor = max(0, min(100, skor))
        durum = "ELİT" if final_skor > 80 else "RİSKLİ" if final_skor < 50 else "STANDART"
        return {"skor": final_skor, "durum": durum, "notlar": notlar}

# ==========================================
# ARAYÜZ (Görsel kısım)
# ==========================================
st.title("🧬 Biovalent Sentinel v1.0")
st.write("Vista Seeds Stratejik Analiz Paneli")

# Sol Panel (Sidebar)
with st.sidebar:
    st.header("Analiz Girişi")
    dizi_input = st.text_area("Gen Dizisini Buraya Yapıştırın:", height=200)
    iklim_input = st.selectbox("Hedef İklim:", ["Sıcak", "Ilıman", "Soğuk"])
    analiz_butonu = st.button("ANALİZİ BAŞLAT")

# Ana Ekran Faaliyeti
if analiz_butonu:
    if dizi_input:
        # Hesaplamaları Başlat
        motor = BiovalentEngine(dizi_input)
        f_sonuc = motor.fiziksel_analiz()
        s_sonuc = motor.stres_testi()
        strateji = BiovalentStrategist(f_sonuc, s_sonuc, iklim_input)
        final = strateji.skorla()

        # Dashboard Kartları
        c1, c2, c3 = st.columns(3)
        c1.metric("Başarı Skoru", f"%{final['skor']}")
        c2.metric("Sınıflandırma", final['durum'])
        c3.metric("Enerji Maliyeti (ATP)", f_sonuc['metabolik_yuk'])

        # Grafik
        st.subheader("🌡️ Termal Dayanıklılık Simülasyonu")
        fig = go.Figure(go.Scatter(x=s_sonuc['sicakliklar'], y=s_sonuc['egri'], 
                                 mode='lines+markers', line=dict(color='#00FFCC', width=3)))
        fig.update_layout(template="plotly_dark", xaxis_title="Sıcaklık (°C)", yaxis_title="Bütünlük (%)")
        st.plotly_chart(fig, use_container_width=True)

        # Rapor
        st.subheader("📋 Stratejik Analiz Raporu")
        for n in final['notlar']:
            st.success(n) if "✅" in n else st.warning(n)
        for r in s_sonuc['riskler']:
            st.error(f"RİSK: {r}")
    else:
        st.error("Lütfen bir gen dizisi girmeden analizi başlatmayın!")
else:
    st.info("👈 Analize başlamak için sol paneldeki bilgileri doldurup 'Analizi Başlat' butonuna tıklayın.")
