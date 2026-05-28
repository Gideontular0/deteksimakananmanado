import streamlit as st
from ultralytics import YOLO
from PIL import Image
import io

# ==========================================
# 1. KONFIGURASI HALAMAN (Wajib di Paling Atas)
# ==========================================
st.set_page_config(
    page_title="Manado Deteksi Makanan",
    page_icon="🍲",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. INJEKSI CSS KELAS ENTERPRISE (AUTO DARK/LIGHT MODE)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Header & Typography */
    .app-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-title {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
    }
    .sub-title {
        color: var(--text-color);
        opacity: 0.8;
        font-size: 1.2rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    /* Tombol Utama (Primary Button) */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
        width: 100%;
        box-shadow: 0 10px 20px -10px rgba(255, 107, 107, 0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 25px -10px rgba(255, 107, 107, 0.6);
        color: white !important; /* Memastikan teks tetap putih saat di-hover */
    }

    /* Styling Gambar */
    .img-container img {
        border-radius: 16px;
        box-shadow: 0 10px 30px -15px rgba(0,0,0,0.2);
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* Custom Recipe Card - Auto menyesuaikan tema terang/gelap */
    .recipe-card {
        background-color: var(--secondary-background-color); 
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 20px;
        height: 100%;
        transition: transform 0.2s ease;
    }
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    .recipe-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px dashed rgba(128, 128, 128, 0.3);
        padding-bottom: 12px;
        margin-bottom: 20px; /* Jarak dari header ke item pertama diperlebar */
    }
    .recipe-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-color); 
        margin: 0;
    }
    .recipe-badge {
        background: #DEF7EC;
        color: #03543F;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* REVISI BAGIAN LIST BAHAN */
    .ingredient-list {
        list-style: none !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex;
        flex-direction: column;
        gap: 12px; /* Mengunci jarak spasi konsisten ke bawah antar item sebesar 12px */
    }
    .ingredient-item {
        display: block !important; /* Memaksa setiap bahan membuat baris baru ke bawah */
        background-color: var(--background-color);
        color: var(--text-color); 
        padding: 10px 16px; /* Spasi dalam box bahan diperluas sedikit */
        border-radius: 8px;
        font-size: 0.95rem;
        border-left: 4px solid #FF8E53; /* Garis aksen dipertebal menjadi 4px */
        margin: 0 !important; /* Reset margin bawaan browser */
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 4rem;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.9rem;
    }
    
    /* Responsive font resizing */
    @media (max-width: 768px) {
        .main-title { font-size: 2.2rem; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE BAHAN MAKANAN
# ==========================================
kumpulan_bahan = {
    "ayamrica": ["Ayam", "Cabai merah", "Cabai rawit", "Bawang merah", "Bawang putih", "Jahe", "Serai", "Daun jeruk", "Perasan jeruk nipis", "Garam", "Gula", "Minyak sayur"],
    "cakalangfufu": ["Ikan cakalang segar", "Garam", "Bumbu halus (bawang dan cabai)", "Pengasapan tradisional sabut kelapa"],
    "ikanwoku": ["Ikan (Tuna/Kerapu/Mujair)", "Daun kemangi", "Daun kunyit", "Daun pandan", "Daun jeruk", "Serai", "Cabai hijau/merah", "Bawang merah", "Bawang putih", "Jahe", "Kunyit", "Kemiri", "Tomat", "Perasan jeruk nipis"],
    "lalampa": ["Beras ketan", "Santan kelapa", "Daun pisang (sebagai pembungkus)", "Isian: Ikan cakalang pampis", "Cabai", "Bawang merah", "Bawang putih", "Serai", "Daun kemangi", "Daun jeruk"],
    "nasijaha": ["Beras ketan", "Beras putih", "Santan kelapa", "Jahe", "Serai", "Bawang merah", "Daun jeruk", "Daun pandan", "Dibakar di dalam buluh bambu berlapis daun pisang"],
    "panada": ["Adonan luar: Tepung terigu, ragi, gula, mentega, telur", "Isian: Ikan cakalang pampis, santan, cabai, bawang merah, bawang putih, daun kemangi, daun jeruk"],
    "tinutuan": ["Beras", "Labu kuning", "Ubi jalar", "Jagung manis", "Daun gedi (sayuran endemik Sulut)", "Bayam", "Kangkung", "Kemangi", "Serai", "Garam", "Pelengkap: Ikan asin dan sambal roa"]
}

# ==========================================
# 4. LOAD MODEL YOLO
# ==========================================
@st.cache_resource
def load_model():
    return YOLO("best.pt")

try:
    model = load_model()
    model_loaded = True
except Exception as e:
    st.error("⚠️ File model 'best.pt' belum ditemukan di direktori yang sama.")
    model_loaded = False

# ==========================================
# 5. SIDEBAR PENGATURAN (PROFESSIONAL TOUCH)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    # Informasi bahwa threshold sudah dikunci (slider dihilangkan)
    st.info("🔒 **Tingkat Keyakinan (Confidence): 75%**\n\n*Threshold dikunci secara sistem untuk memastikan akurasi deteksi maksimal.*")
    conf_threshold = 0.75
    
    st.markdown("---")
    st.markdown("### 📋 Objek Terdaftar")
    for item in kumpulan_bahan.keys():
        st.write(f"✓ {item.title().replace(' ', '')}")

# ==========================================
# 6. HEADER APLIKASI UTAMA
# ==========================================
st.markdown('<div class="app-header">', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">Deteksi Makanan Manado</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sistem Visi Komputer untuk Deteksi Kuliner Khas Manado dan bahan</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. LOGIKA UI & DETEKSI
# ==========================================
upload_col1, upload_col2, upload_col3 = st.columns([1, 2, 1])
with upload_col2:
    uploaded_file = st.file_uploader("Unggah foto masakan dari perangkat Anda", type=["jpg", "jpeg", "png"])

if uploaded_file is not None and model_loaded:
    image = Image.open(uploaded_file)
    
    act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
    with act_col2:
        analyze_btn = st.button("✨ Mulai Analisis AI")

    st.markdown("<br>", unsafe_allow_html=True)

    if analyze_btn:
        with st.spinner("Menganalisis piksel gambar..."):
            # Proses YOLO menggunakan threshold 0.75 yang sudah dikunci
            results = model.predict(image, conf=conf_threshold)
            res_image = results[0].plot()
            detected_image = Image.fromarray(res_image[..., ::-1])
            boxes = results[0].boxes

            tab1, tab2 = st.tabs(["🤖 Hasil Deteksi YOLO", "🖼️ Gambar Asli"])
            
            with tab1:
                st.markdown('<div class="img-container">', unsafe_allow_html=True)
                st.image(detected_image, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                st.markdown('<div class="img-container">', unsafe_allow_html=True)
                st.image(image, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("---")
            
            if len(boxes) > 0:
                st.success(f"Berhasil mengidentifikasi {len(boxes)} hidangan!")
                st.markdown("### 📋 Rincian Komposisi")
                
                cols = st.columns(2)
                
                for idx, box in enumerate(boxes):
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0]) * 100
                    
                    display_name = class_name.replace(" ", " ").title()
                    if display_name.lower() == "ayamrica": display_name = "Ayam Rica"
                    if display_name.lower() == "cakalangfufu": display_name = "Cakalang Fufu"
                    if display_name.lower() == "ikanwoku": display_name = "Ikan Woku"
                    if display_name.lower() == "nasijaha": display_name = "Nasi Jaha"
                    
                    bahan_list = kumpulan_bahan.get(class_name, ["Data tidak ditemukan."])
                    
                    # Membuat elemen list terpisah secara bersih ke bawah
                    ingredients_html = "".join([f'<div class="ingredient-item">💡 {item}</div>' for item in bahan_list])
                    
                    card_html = f"""
                    <div class="recipe-card">
                        <div class="recipe-header">
                            <h3 class="recipe-title">🍲 {display_name}</h3>
                            <span class="recipe-badge">Akurasi: {confidence:.1f}%</span>
                        </div>
                        <div class="ingredient-list">
                            {ingredients_html}
                        </div>
                    </div>
                    """
                    
                    with cols[idx % 2]:
                        st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.warning("Model tidak menemukan makanan yang sesuai kriteria dengan tingkat keyakinan minimal 75%.")

# ==========================================
# 8. FOOTER
# ==========================================
st.markdown(
    '<div class="footer">'
    '<b>Manado Deteksi Makanan</b><br>'
    'Dikembangkan oleh GideoN Tular | Universitas Prisma'
    '</div>', 
    unsafe_allow_html=True
)