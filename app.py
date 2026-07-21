import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import base64

st.set_page_config(page_title="Trình Duyệt Truyện Audio AI", layout="centered")

BASE_URL = "https://tutien.pro"

st.title("📚 Trình Duyệt & Đọc Truyện Audio (Có Đăng Nhập)")
st.write("Đọc truyện từ Tutien.pro vượt qua lớp bảo mật.")

# --- PHẦN 1: CÀI ĐẶT COOKIE ĐĂNG NHẬP ---
with st.expander("🔑 Cài đặt tài khoản (Chỉ cần làm 1 lần)"):
    st.write("Vì web yêu cầu đăng nhập, hãy dán chuỗi **Cookie** tài khoản của bạn vào đây để ứng dụng có quyền xem nội dung.")
    cookie_nhap = st.text_area("Dán Cookie của bạn vào đây:")
    if cookie_nhap:
        st.session_state.cookie = cookie_nhap
        st.success("Đã lưu Cookie!")
    else:
        if 'cookie' not in st.session_state:
            st.session_state.cookie = ""

# Lấy cookie nếu có
my_cookie = st.session_state.get('cookie', '')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36',
    'Cookie': my_cookie  # Gắn cookie vào đây để vượt qua đăng nhập
}

# --- PHẦN 2: NHẬP LINK CHƯƠNG ---
st.markdown("---")
link_chuong = st.text_input("Dán link chương truyện từ tutien.pro vào đây:")

if link_chuong:
    try:
        res = requests.get(link_chuong, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Kiểm tra xem có bị văng về trang đăng nhập không
        if "login" in res.url or not soup.find('div', id='chapter-content'):
            st.error("⚠️ Không thể lấy nội dung. Có thể bạn chưa dán Cookie hoặc Cookie đã hết hạn!")
        else:
            # Lấy tiêu đề chương
            tieu_de = soup.find('h2', class_='chapter-title') or soup.find('a', class_='chapter-title')
            tieu_de_text = tieu_de.get_text(strip=True) if tieu_de else "Chương Truyện"
            st.subheader(tieu_de_text)
            
            # Lấy nội dung chữ
            noi_dung_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')
            if not noi_dung_div:
                noi_dung_div = soup.find('div', class_='box-content')
                
            if noi_dung_div:
                van_ban = noi_dung_div.get_text(separator=' ', strip=True)
                
                with st.spinner("🤖 AI đang chuyển nội dung thành giọng đọc..."):
                    tts = gTTS(text=van_ban[:3000], lang='vi', slow=False)
                    tts.save("temp_voice.mp3")
                
                with open("temp_voice.mp3", "rb") as f:
                    audio_bytes = f.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                # Tìm link chương tiếp theo
                link_chuong_tiep = ""
                nut_sau = soup.find('a', id='next-chapter') or soup.find('a', class_=['btn', 'next'])
                if not nut_sau:
                    for a in soup.find_all('a', href=True):
                        if 'sau' in a.get_text().lower() or 'tiếp' in a.get_text().lower():
                            nut_sau = a
                            break
                if nut_sau and nut_sau.get('href'):
                    next_href = nut_sau['href']
                    link_chuong_tiep = next_href if next_href.startswith('http') else BASE_URL + next_href

                if link_chuong_tiep:
                    st.write("Chế độ: **Tự động chuyển chương khi đọc xong đang bật** 🔄")
                    audio_html = f"""
                    <audio id="audio-player" controls autoplay style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                    <script>
                    var audio = document.getElementById('audio-player');
                    audio.onended = function() {{
                        window.parent.postMessage({{type: 'streamlit:set_widget_value', from: 'link_chuong', value: '{link_chuong_tiep}'}}, '*');
                    }};
                    </script>
                    """
                    st.components.v1.html(audio_html, height=100)
                else:
                    st.audio("temp_voice.mp3", format="audio/mp3")
                    st.info("Đã đến chương mới nhất.")
                
                with st.expander("📄 Xem nội dung chữ của chương"):
                    st.write(van_ban)
            else:
                st.error("Không tìm thấy nội dung chữ trong trang này.")
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")