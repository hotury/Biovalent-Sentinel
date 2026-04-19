import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ==========================================
# BÖLÜM 1 & 2: ANALİZ VE STRES MOTORU
# ==========================================
class BiovalentEngine:
    def __init__(self, sequence):
        self.seq = sequence.upper().strip()
        self.n = len(self.seq)

    def fiziksel_analiz(self):
        """Isı direnci ve metabolik yükü hesaplar."""
        # Alifatik İndeks (Isı Direnci)
        a, v, i, l = [self.seq.count(x)/self.n if self.n > 0 else 0 for x in "AVIL"]
        isi_indeksi = (a + 2.9 * v + 3.9 * (i + l)) * 100
        
        # Metabolik Maliyet (ATP tahmini)
        atp_maliyeti = self.n * 4 
        
        return {"isi_direnci": round(isi_indeksi, 2), "metabolik_yuk": atp_maliyeti}

    def stres_testi(self):
        """Termal dayanıklılık eğrisi ve riskleri üretir."""
        # Termal Simülasyon
        direnc = (self.seq.count('C') * 2) + self.seq.count('P') + 5
        sicakliklar = np.arange(20, 75, 5)
        egri = [max(0, min(100, 100 - ((max(0, t - 37) * 0.15 * 100) / direnc))) for t in sicakliklar]
        
        # Risk Taraması (Red Flags)
        riskler = []
        if "RR" in self.seq or "KK" in self.seq: riskler.append("Yüksek Parçalanma Riski (RR/KK)")
        if (sum(self.seq.count(x) for x in "PEST") / self.n) > 0.3: riskler.append("Kritik PEST Yoğunluğu")
        
        return {"sicakliklar": sicakliklar.tolist(), "egri": egri, "riskler": riskler}

# ==========================================
# BÖLÜM 3: STRATEJİST (KARAR MERKEZİ)
# ==========================================
class BiovalentStrategist:
    def __init__(self, fiziksel, stres, hedef_iklim):
        self.fiziksel = fiziksel
        self.stres = stres
        self.hedef_iklim = hedef_iklim

    def skorla(self):
        skor = 60
        notlar = []
        
        # Isı vs İklim
        if self.hedef_iklim == "Sıcak":
            if self.fiziksel['isi_direnci'] > 110:
                skor += 20
                notlar.append("✅ Sıcak iklim adaptasyonu yüksek.")
            else:
                skor -= 25
                notlar.append("⚠️ Isı stresi altında çökme riski!")
        
        # Verimlilik
        if self.fiziksel['metabolik_yuk'] > 1500:
            skor -= 15
            notlar.append("📉 Yüksek enerji maliyeti.")
            
        # Riskler
        skor -= (len(self.stres['riskler']) * 15)
        
        final_skor = max(0, min(100, skor))
        durum = "ELİT" if final_skor > 80 else "RİSKLİ" if final_skor < 50 else "STANDART"
        
        return {"skor": final_skor, "durum": durum, "notlar": notlar}

# ==========================================
# BÖLÜM 4: ARAYÜZ (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Biovalent Sentinel", layout="wide")
st.title("🧬 Biovalent Sentinel v1.0")

with st.sidebar:
    st.header("Giriş Paneli")
    dizi = st.text_area("Gen Dizisi:", height=150).upper().replace(" ", "")
    iklim = st.selectbox("Hedef İklim:", ["Sıcak", "Ilıman", "Soğuk"])
    btn = st.button("Analizi Başlat")

if btn and dizi:
    # Motorları Çalıştır
    engine = BiovalentEngine(dizi)
    f_veri = engine.fiziksel_analiz()
    s_veri = engine.stres_testi()
    
    strat = BiovalentStrategist(f_veri, s_veri, iklim)
    sonuc = strat.skorla()
    
    # Dashboard
    c1, c2, c3 = st.columns(3)
    c1.metric("Başarı Skoru", f"%{sonuc['skor']}")
    c2.metric("Sınıf", sonuc['durum'])
    c3.metric("ATP Yükü", f_veri['metabolik_yuk'])
    
    # Grafik
    st.subheader("🌡️ Termal Dayanıklılık Simülasyonu")
    fig = go.Figure(go.Scatter(x=s_veri['sicakliklar'], y=s_veri['egri'], mode='lines+markers', line=dict(color='#00FFCC')))
    fig.update_layout(template="plotly_dark", xaxis_title="Sıcaklık (°C)", yaxis_title="Bütünlük (%)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Detaylar
    st.subheader("📋 Stratejik Analiz Notları")
    for n in sonuc['notlar']: st.write(f"- {n}")
    for r in s_veri['riskler']: st.error(f"Risk: {r}")
