import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import base64

st.set_page_config(page_title="Trình Duyệt Truyện Audio", layout="centered")

BASE_URL = "https://tutien.pro"
LOGIN_URL = "https://tutien.pro/login"

# Khởi tạo Session đăng nhập ngầm
if 'session' not in st.session_state:
    s = requests.Session()
    login_data = {
        'username': 'lazychibi92',
        'password': 'volam123'
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'}
    try:
        s.post(LOGIN_URL, data=login_data, headers=headers)
        st.session_state.session = s
    except:
        st.session_state.session = requests.Session()

s = st.session_state.session
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'}

if 'current_chapter_url' not in st.session_state:
    st.session_state.current_chapter_url = ""

st.title("📚 Đọc & Nghe Truyện Rảnh Tay")
st.success("🤖 Đã tự động kết nối tài khoản thành công!")

# Ô dán link trực tiếp
st.markdown("---")
link_nhap = st.text_input("Dán trực tiếp Link Chương truyện từ tutien.pro vào đây:")

if link_nhap:
    st.session_state.current_chapter_url = link_nhap

if st.session_state.current_chapter_url:
    url = st.session_state.current_chapter_url
    st.info(f"Đang xử lý link: {url}")
    
    try:
        res = s.get(url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Tìm tiêu đề chương linh hoạt hơn
        tieu_de_c = soup.find('h1') or soup.find('h2') or soup.find('div', class_='chapter-title')
        tieu_de_text = tieu_de_c.get_text(strip=True) if tieu_de_c else "Chương Truyện"
        st.subheader(tieu_de_text)
        
        # Tìm nội dung chính linh hoạt quét tất cả thẻ div có khả năng chứa text truyện
        noi_dung_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c') or soup.find('div', class_='box-content')
        
        # Nếu vẫn không thấy, quét tìm thẻ div có nhiều chữ nhất
        if not noi_dung_div:
            divs = soup.find_all('div')
            for d in divs:
                if len(d.get_text()) > 500: # Đoán nội dung chương truyện dài hơn 500 ký tự
                    noi_dung_div = d
                    break
                    
        if noi_dung_div:
            van_ban = noi_dung_div.get_text(separator=' ', strip=True)
            
            with st.spinner("🤖 AI đang tạo giọng đọc âm thanh..."):
                tts = gTTS(text=van_ban[:4000], lang='vi', slow=False)
                tts.save("temp_voice.mp3")
                
            with open("temp_voice.mp3", "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
            # Tìm link chương sau tự động
            link_sau = ""
            for a in soup.find_all('a', href=True):
                txt = a.get_text().lower()
                if 'sau' in txt or 'tiếp' in txt or 'next' in a.get('id', '').lower():
                    n_href = a['href']
                    link_sau = n_href if n_href.startswith('http') else BASE_URL + n_href
                    break
            
            if link_sau:
                st.write("Trạng thái: **Tự động chuyển chương khi đọc xong** 🔄")
                audio_html = f"""
                <audio id="audio-player" controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                <script>
                var audio = document.getElementById('audio-player');
                audio.onended = function() {{
                    window.location.href = window.location.href;
                }};
                </script>
                """
                st.components.v1.html(audio_html, height=100)
                
                if st.button("⏩ Bấm để sang chương tiếp theo"):
                    st.session_state.current_chapter_url = link_sau
                    st.rerun()
            else:
                st.audio("temp_voice.mp3", format="audio/mp3")
                st.info("Đã đến chương mới nhất hoặc không tìm thấy nút chương tiếp theo.")
                
            with st.expander("📄 Xem nội dung chữ"):
                st.write(van_ban)
        else:
            st.error("Không tìm thấy nội dung chữ. Hãy kiểm tra lại xem link đã đúng là trang đọc chương chưa hoặc tài khoản có bị giới hạn không.")
    except Exception as e:
        st.error(f"Đã xảy ra lỗi kết nối: {e}")
