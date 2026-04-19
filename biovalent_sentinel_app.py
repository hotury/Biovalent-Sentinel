# Biovalent Sentinel - Stratejik Analiz Motoru
import numpy as np

class BiovalentOrkestra:
    def __init__(self, dizi, hedef_iklim="Sicak"):
        self.dizi = dizi.upper().strip()
        self.hedef_iklim = hedef_iklim
        self.n = len(self.dizi)
        
    def analiz_et(self):
        # 1. Fiziksel Veriler
        isi_direnci = self._hesapla_isi_direnci()
        metabolik_yuk = self.n * 4 # ATP tahmini
        kararlilik = self._hesapla_kararlilik()
        
        # 2. Karar Mekanizması (Çarpıştırma)
        skor = 50
        riskler = []
        firsatlar = []

        # Isı ve İklim Çarpışması
        if self.hedef_iklim == "Sicak":
            if isi_direnci > 110:
                skor += 25
                firsatlar.append("Mükemmel Termal Stabilite")
            else:
                skor -= 20
                riskler.append("Sıcaklık Altında Yapısal Bozulma Riski")

        # Metabolik Yük vs Ticari Değer
        if metabolik_yuk > 1200:
            skor -= 10
            riskler.append("Yüksek Enerji Maliyeti (Verim Düşüklüğü)")
        else:
            skor += 10
            firsatlar.append("Düşük Enerji Maliyeti (Yüksek Verim Potansiyeli)")

        # Kararlılık Kontrolü
        if kararlilik == "Kırılgan":
            skor -= 15
            riskler.append("Kısa Hücresel Ömür")

        return {
            "skor": max(0, min(100, skor)),
            "durum": "YÜKSEK POTANSİYEL" if skor > 75 else "AR-GE RİSKİ",
            "firsatlar": firsatlar,
            "riskler": riskler,
            "veriler": {"Isı Direnci": isi_direnci, "ATP Yükü": metabolik_yuk}
        }

    def _hesapla_isi_direnci(self):
        # A, V, I, L Amino asitlerinin oransal ağırlığı
        a, v, i, l = [self.dizi.count(x)/self.n for x in "AVIL"]
        return round((a + 2.9 * v + 3.9 * (i + l)) * 100, 2)

    def _hesapla_kararlilik(self):
        # Tehlikeli ikililerin taranması
        riskli_ikililer = ["RR", "KK", "PP"]
        bulunan = sum(self.dizi.count(x) for x in riskli_ikililer)
        return "Kırılgan" if bulunan > (self.n / 20) else "Stabil"

# ÖRNEK ÇALIŞTIRMA
orkestra = BiovalentOrkestra("MAVKKSTAGKKRTTLCCKKLLNPQRHHL", hedef_iklim="Sicak")
rapor = orkestra.analiz_et()

print(f"--- BİOVALENT ANALİZ RAPORU ---")
print(f"Genetik Skor: {rapor['skor']} / 100")
print(f"Durum: {rapor['durum']}")
print(f"Fırsatlar: {', '.join(rapor['firsatlar'])}")
print(f"Riskler: {', '.join(rapor['riskler'])}")
import numpy as np

class StresLab:
    def __init__(self, dizi):
        self.dizi = dizi.upper()
        self.n = len(dizi)

    def termal_simulasyon_verisi(self):
        """
        Proteinin 20°C ile 70°C arasındaki yapısal bütünlüğünü simüle eder.
        Bu veri, arayüzdeki o meşhur 'çöküş grafiği'ni besleyecek.
        """
        # Temel direnç skoru (Isı kilitleri: C, P, W)
        direnc_faktoru = (self.dizi.count('C') * 2) + self.dizi.count('P') + (self.dizi.count('W') * 1.5)
        
        sicakliklar = np.arange(20, 75, 5)
        butunluk_egrisi = []

        for t in sicakliklar:
            # 37 dereceden sonra stres artmaya başlar
            stres_katsayisi = max(0, t - 37) * 0.15
            # Direnç faktörü ne kadar yüksekse, bütünlük o kadar yavaş düşer
            kayip = (stres_katsayisi * 100) / (direnc_faktoru + 5)
            mevcut_butunluk = max(0, 100 - kayip)
            butunluk_egrisi.append(round(mevcut_butunluk, 2))

        return {"sicakliklar": sicakliklar.tolist(), "egri": butunluk_egrisi}

    def kirmizi_bayrak_taramasi(self):
        """
        Dizideki 'Degron' adı verilen ve proteinin hızlı parçalanmasına 
        sebep olan tehlikeli bölgeleri (riskleri) arar.
        """
        riskler = []
        tehlikeli_dizilimler = {
            "RR": "Yüksek Proteolitik Risk (Hücrede hızlı parçalanma)",
            "KK": "Kararsızlık Noktası",
            "PEST": "Hızlı Yıkım Sinyali (P, E, S, T yoğunluğu)"
        }

        for kod, aciklama in tehlikeli_dizilimler.items():
            if kod in self.dizi:
                riskler.append(aciklama)
        
        # PEST dizilimi özel bir kontrol gerektirir (yoğunluk analizi)
        pest_count = sum(self.dizi.count(x) for x in "PEST")
        if (pest_count / self.n) > 0.3:
            riskler.append("Kritik PEST Yoğunluğu: Protein ömrü çok kısa olabilir.")

        return riskler

    def motif_dedektifi(self):
        """
        Bitki ıslahında kritik olan 'fonksiyonel barkodları' arar.
        """
        bulunanlar = []
        motif_kutuphanesi = {
            "GXXXXGKS": "P-Loop (Enerji Transfer Birimi)",
            "HELLH": "Metal Bağlayıcı (Çinko Parmak/Dayanıklılık)",
            "N[ST][^P]": "N-Glikozilasyon (Hücre Dışı Koruma Zırhı)" # Basit regex mantığı
        }
        
        # Basit motif araması (Daha karmaşık taramalar için Regex eklenebilir)
        for motif, tanim in motif_kutuphanesi.items():
            if motif in self.dizi:
                bulunanlar.append(tanim)
        
        return bulunanlar
        class BiovalentStrategist:
    def __init__(self, fiziksel_veri, stres_verisi, hedef_iklim="Sicak"):
        self.fiziksel = fiziksel_veri
        self.stres = stres_verisi
        self.hedef_iklim = hedef_iklim

    def ticari_basari_skoru_hesapla(self):
        """
        Tüm verileri 100 üzerinden tek bir 'Yatırım Değeri' puanına indirger.
        """
        skor = 60  # Baz puan (Nötr)
        analiz_notlari = []

        # 1. Kriter: Isı Uyumu (Ağırlık: %35)
        isi_indeksi = self.fiziksel.get("isi_direnci", 0)
        if self.hedef_iklim == "Sicak":
            if isi_indeksi > 115:
                skor += 25
                analiz_notlari.append("🌟 Üstün Termal Adaptasyon: Sıcak bölgeler için şampiyon aday.")
            elif isi_indeksi < 90:
                skor -= 30
                analiz_notlari.append("🚨 Termal Risk: Bu gen sıcak iklimde verim kaybına neden olur.")
        
        # 2. Kriter: Metabolik Verimlilik (Ağırlık: %25)
        # ATP maliyeti ne kadar düşükse, meyveye giden enerji o kadar artar.
        atp_yuk = self.fiziksel.get("metabolik_yuk", 0)
        if atp_yuk < 800:
            skor += 15
            analiz_notlari.append("💰 Düşük Maliyet: Bitki enerjisini korur, yüksek rekolte potansiyeli.")
        elif atp_yuk > 1500:
            skor -= 15
            analiz_notlari.append("📉 Enerji İsrafı: Protein sentezi çok pahalı, meyve boyutunu küçültebilir.")

        # 3. Kriter: Risk ve Kararlılık (Ağırlık: %40)
        # Stres Lab'dan gelen kırmızı bayraklar skoru doğrudan baltalar.
        risk_sayisi = len(self.stres.get("riskler", []))
        if risk_sayisi > 0:
            ceza = risk_sayisi * 15
            skor -= ceza
            analiz_notlari.append(f"⚠️ Kritik Zafiyet: Dizide {risk_sayisi} adet yapısal risk saptandı.")
        
        # Motif Bonusları
        if len(self.stres.get("motifler", [])) > 0:
            skor += 10
            analiz_notlari.append("🔑 Fonksiyonel Artı: Kritik biyolojik motifler başarı şansını artırıyor.")

        # Skor Sınırlandırma
        final_skor = max(0, min(100, skor))
        
        return {
            "final_skor": final_skor,
            "sinif": self._siniflandir(final_skor),
            "stratejik_notlar": analiz_notlari
        }

    def _siniflandir(self, skor):
        if skor >= 85: return "ELİT VARYETE (Yüksek Yatırım Değeri)"
        if skor >= 70: return "GELECEK VAAD EDEN (Ar-Ge'ye Devam)"
        if skor >= 50: return "ORTALAMA (Geliştirilmesi Gerek)"
        return "RİSKLİ (Elenmesi Tavsiye Edilir)"

    def yonetici_ozeti_uret(self, sonuc):
        """Yatırımcıya sunulacak o 'can alıcı' özeti hazırlar."""
        ozet = f"### STRATEJİK ANALİZ RAPORU\n"
        ozet += f"**Genetik Başarı Puanı:** %{sonuc['final_skor']}\n"
        ozet += f"**Sınıflandırma:** {sonuc['sinif']}\n\n"
        ozet += "**Uzman Görüşü:**\n"
        for not_ in sonuc['stratejik_notlar']:
            ozet += f"- {not_}\n"
        
        return ozet
        import streamlit as st
import plotly.graph_objects as go
# Önceki bölümlerdeki sınıfların burada import edildiğini varsayıyoruz
# (Gerçek kullanımda tüm kodları tek dosyada toplayabilir veya import edebilirsin)

# SAYFA AYARLARI
st.set_page_config(page_title="Biovalent Sentinel v1.0", layout="wide")

st.title("🧬 Biovalent Sentinel: Stratejik Genetik Analiz")
st.markdown("---")

# YAN PANEL (INPUTLAR)
st.sidebar.header("📥 Analiz Parametreleri")
gen_dizisi = st.sidebar.text_area("Gen Dizisini Yapıştırın (Amino Asit):", 
                                 placeholder="Örn: MAVKKSTAG...", height=200)

hedef_iklim = st.sidebar.selectbox("Hedef Üretim İklimi:", 
                                  ["Sıcak (Örn: Antalya/Çukurova)", "Ilıman (Örn: Ege/Marmara)", "Soğuk"])

analiz_butonu = st.sidebar.button("Stratejik Analizi Başlat")

if analiz_butonu and gen_dizisi:
    # 1. BÖLÜM: ANALİZ MOTORLARINI ÇALIŞTIR
    # Not: Burada önceki bölümlerde yazdığımız sınıfları çağırıyoruz
    # (Kodun çalışması için sınıfların bu dosyanın üstünde tanımlı olması gerekir)
    
    with st.spinner('Genetik istihbarat toplanıyor...'):
        # Mock Nesneler (Önceki sınıfların mantığını burada simüle ediyoruz)
        orkestra = BiovalentOrkestra(gen_dizisi, hedef_iklim="Sicak" if "Sıcak" in hedef_iklim else "Normal")
        rapor_verisi = orkestra.analiz_et()
        
        stres_merkezi = StresLab(gen_dizisi)
        grafik_verisi = stres_merkezi.termal_simulasyon_verisi()
        riskler = stres_merkezi.kirmizi_bayrak_taramasi()

    # 2. BÖLÜM: GÖRSEL SONUÇLAR (DASHBOARD)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Genetik Başarı Skoru", f"%{rapor_verisi['skor']}")
    with col2:
        st.subheader("Stratejik Durum")
        st.info(rapor_verisi['durum'])
    with col3:
        st.subheader("Metabolik Yük")
        st.warning(f"{rapor_verisi['veriler']['ATP Yükü']} ATP / Sentez")

    st.markdown("---")

    # 3. BÖLÜM: STRES TESTİ GRAFİĞİ
    st.subheader("🌡️ In-silico Termal Dayanıklılık Eğrisi")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=grafik_verisi['sicakliklar'], y=grafik_verisi['egri'],
                             mode='lines+markers', name='Yapısal Bütünlük',
                             line=dict(color='#00ffcc', width=4)))
    
    fig.update_layout(template="plotly_dark", xaxis_title="Sıcaklık (°C)", yaxis_title="Bütünlük (%)")
    st.plotly_chart(fig, use_container_width=True)

    # 4. BÖLÜM: RİSK VE FIRSAT ANALİZİ
    c1, c2 = st.columns(2)
    with c1:
        st.success("✅ Fırsatlar ve Avantajlar")
        for f in rapor_verisi['firsatlar']:
            st.write(f"- {f}")
    with c2:
        st.error("🚨 Saptanan Riskler")
        for r in riskler + rapor_verisi['riskler']:
            st.write(f"- {r}")

    st.markdown("---")
    st.subheader("📝 Yönetici Özeti")
    st.write(f"Bu gen varyetesi, yapılan **{hedef_iklim}** simülasyonu sonucunda **%{rapor_verisi['skor']}** başarı puanı almıştır. "
             "Özellikle termal stabilite ve metabolik maliyet dengesi göz önüne alındığında, ticari üretim için "
             f"{'yüksek potansiyel taşımaktadır' if rapor_verisi['skor'] > 70 else 'bazı modifikasyonlar gerektirmektedir'}.")

else:
    st.info("Analizi başlatmak için lütfen sol tarafa bir gen dizisi girin ve iklimi seçin.")
        
