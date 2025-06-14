import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import tempfile

# --------------------- CSS Edukatif ---------------------
st.markdown("""
    <style>
        html, body, .main {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', sans-serif;
        }

        .block-container {
            padding: 2rem 2rem;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }

        h1, h2, h3 {
            color: #2c3e50;
        }

        .stButton>button {
            background-color: #2e86de;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            padding: 8px 16px;
        }

        .stButton>button:hover {
            background-color: #1e70bf;
        }

        .stRadio > div {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------- Load dari Excel ---------------------
# @st.cache_data
def load_questions_from_excel(file_path):
    q_df = pd.read_excel(file_path, sheet_name='Questions')
    a_df = pd.read_excel(file_path, sheet_name='Answers')
    
    merged = q_df.merge(a_df, left_on='id', right_on='question_id')
    
    questions = {}
    for _, row in merged.iterrows():
        qid = row['id']
        if qid not in questions:
            questions[qid] = {
                'id': qid,
                'text': row['question_text'],
                'options': []
            }
        questions[qid]['options'].append({
            'personality_type': row['personality_type'],
            'answer_text': row['answer_text']
        })
    
    # Ubah dict ke list
    questions_list = list(questions.values())
    
    # Acak pilihan jawaban setiap pertanyaan
    for q in questions_list:
        random.shuffle(q['options'])
    
    # Acak urutan pertanyaan
    random.shuffle(questions_list)
    
    return questions_list

def tampilkan_info_mbti(kode_tipe):
    # Baca file Excel
    df = pd.read_excel("Deskripsi_Tipe_Kepribadian_MBTI.xlsx")

    # Filter berdasarkan kode tipe
    hasil = df[df['Tipe MBTI'].str.upper() == kode_tipe.upper()]
    
    if not hasil.empty:
        return hasil.to_string(index=False)
    else:
        return f"Tipe MBTI '{kode_tipe}' tidak ditemukan."
# --------------------- Fungsi PDF ---------------------
def generate_pdf(name, counts, chart_buf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    ls_judul = f"Hasil Kuesioner Jenis Kepribadian  {name}"
    pdf.cell(200, 10, txt=ls_judul, ln=1, align="C")
    pdf.ln(5)
    pdf.ln(5)
    for k, label in zip(['M','S','K','P'], ['Melankolis', 'Sanguinis', 'Kloris', 'Plegmatis']):
        pdf.cell(200, 10, txt=f"{label}: {counts[k]}", ln=1)
    

    # Simpan chart ke file sementara
    if chart_buf is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            tmpfile.write(chart_buf.getbuffer())
            tmpfile_path = tmpfile.name
        pdf.image(tmpfile_path, x=30, w=150)

    # ✅ Simpan hasil PDF ke BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    output = BytesIO(pdf_bytes)
    return output

# --------------------- App Utama ---------------------
st.title("📝 Kuesioner Jenis Kepribadian MBTI")

st.markdown("""
Selamat datang di kuesioner **Jenis Kepribadian MBTI** – 

Kuesioner ini dirancang untuk membantu Anda memahami tipe kepribadian Anda berdasarkan kerangka kerja MBTI (Myers-Briggs Type Indicator).
🔍 MBTI merupakan alat psikologi populer yang digunakan untuk mengenal cara Anda:

🧭 Memusatkan perhatian

📥 Menerima informasi

⚖️ Membuat keputusan

🗓️ Mengatur hidup

🔑 Empat Dimensi MBTI:
💬 Ekstrovert (E) vs 🤫 Introvert (I)
→ Fokus energi: ke dunia luar atau dalam diri sendiri?

👀 Sensing (S) vs 🔮 Intuition (N)
→ Cara memahami informasi: fakta konkret atau pola & kemungkinan?

🧠 Thinking (T) vs ❤️ Feeling (F)
→ Dasar pengambilan keputusan: logika atau nilai & perasaan?

📅 Judging (J) vs 🌀 Perceiving (P)
→ Gaya hidup: terstruktur atau fleksibel?

🎯 Tujuan Kuesioner:
🪞 Mengenal diri sendiri lebih dalam

🚀 Mengembangkan potensi pribadi dan profesional

👥 Meningkatkan hubungan sosial dan kerja tim

💼 Membantu dalam perencanaan karier

📝 Petunjuk Pengisian:
✅ Jawablah secara jujur dan spontan — tidak ada jawaban salah atau benar!

⏱️ Waktu pengisian: sekitar 10–15 menit

💡 Fokus pada kebiasaan Anda yang paling alami
""")

name = st.text_input("📛 Masukkan Nama Lengkap Anda:")

questions = load_questions_from_excel("mbti_kuesioner.xlsx")

responses = {}
with st.form("quiz_form"):
    st.subheader("📚 Pertanyaan Kuesioner")

    for idx, q in enumerate(questions, 1):
        st.markdown(f"**{idx}. {q['text']}**")
        labels = [opt['answer_text'] for opt in q['options']]
        values = [opt['personality_type'] for opt in q['options']]
        selected = st.radio("", options=labels, key=f"q{idx}")
        responses[idx] = values[labels.index(selected)]

    submitted = st.form_submit_button("📤 Kirim Jawaban")

# --------------------- Hasil ---------------------
if submitted and name:
    counts = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    for ans in responses.values():
        counts[ans] += 1

     # Tentukan MBTI (mengambil nilai tertinggi dari pasangan)
    result = ""
    result += "E" if counts["E"] >= counts["I"] else "I"
    result += "S" if counts["S"] >= counts["N"] else "N"
    result += "T" if counts["T"] >= counts["F"] else "F"
    result += "J" if counts["J"] >= counts["P"] else "P"
    
    st.success("✅ Jawaban berhasil dikirim!")
    deskripsi_tipe = tampilkan_info_mbti(result)
    julukan = deskripsi_tipe["Julukan"]    

    st.subheader(f"Jenis Kepribadian untuk **{name}** dijuluki **{julukan}**")    

    '''st.subheader(f"Jenis Kepribadian untuk **{name}** dijuluki **{deskripsi_tipe['Julukan']}**")
    
    

elif submitted:
    st.warning("⚠️ Silakan isi nama terlebih dahulu sebelum mengirim.")

