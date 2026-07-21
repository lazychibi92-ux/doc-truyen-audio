import streamlit as st
from gtts import gTTS
import base64

st.set_page_config(page_title="Đọc Truyện Audio Rảnh Tay", layout="centered")

st.title("🎧 Trình Đọc Truyện Audio Nhanh")
st.write("Dán nội dung chương truyện bất kỳ để nghe đọc rảnh tay.")

# Ô nhập văn bản trực tiếp
noi_dung_nhap = st.text_area("Dán nội dung chương truyện vào đây:", height=200, placeholder="Copy nội dung từ web tutien.pro rồi dán vào đây...")

if noi_dung_nhap:
    if st.button("▶ Bắt đầu đọc Audio"):
        with st.spinner("🤖 AI đang chuyển nội dung thành giọng đọc..."):
            # Chuyển văn bản thành giọng nói
            tts = gTTS(text=noi_dung_nhap, lang='vi', slow=False)
            tts.save("temp_voice.mp3")
        
        # Phát audio trực tiếp trên web
        st.audio("temp_voice.mp3", format="audio/mp3")
        st.success("Đã tạo xong audio! Bạn có thể bấm nút Play ở trên để nghe.")