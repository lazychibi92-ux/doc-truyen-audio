import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import base64

st.set_page_config(page_title="Trình Duyệt Truyện Audio", layout="centered")

BASE_URL = "https://tutien.pro"

if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'current_story_url' not in st.session_state:
    st.session_state.current_story_url = ""
if 'current_chapter_url' not in st.session_state:
    st.session_state.current_chapter_url = ""

# --- PHẦN ĐĂNG NHẬP TRỰC TIẾP QUA IFRAME ---
with st.expander("🔑 Đăng nhập trực tiếp tài khoản Tutien.pro"):
    st.write("Nếu trang web cho phép, bạn có thể đăng nhập ngay tại đây:")
    # Nhúng trang đăng nhập gốc vào app
    login_html = f"""
    <iframe src="{BASE_URL}/login" width="100%" height="400px" style="border:none; border-radius: 8px;"></iframe>
    """
    st.components.v1.html(login_html, height=420)
    st.info("Sau khi đăng nhập thành công ở khung trên, nếu trang web bị chặn hiển thị, bạn vui lòng dùng cách dán Cookie như cũ hoặc chuyển sang web mở.")

# Cài đặt Cookie dự phòng
with st.expander("🔑 Hoặc dán Cookie thủ công (Nếu khung trên bị trắng/chặn)"):
    cookie_nhap = st.text_area("Dán Cookie vào đây:", value=st.session_state.get('cookie', ''))
    if cookie_nhap:
        st.session_state.cookie = cookie_nhap

my_cookie = st.session_state.get('cookie', '')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36',
    'Cookie': my_cookie
}

# ================= TRANG 1: TRANG CHỦ & TÌM KIẾM =================
if st.session_state.page == "home":
    st.title("📚 Kho Truyện Tiên Hiệp")
    st.write("Duyệt truyện và nghe audio từ Tutien.pro")

    tu_khoa = st.text_input("🔍 Tìm kiếm tên truyện...")
    if tu_khoa:
        try:
            search_url = f"{BASE_URL}/tim-kiem?keyword={tu_khoa}"
            res = requests.get(search_url, headers=HEADERS)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            found = False
            for a in soup.find_all('a', href=True):
                if '/truyen/' in a['href'] and a.get_text(strip=True):
                    t_name = a.get_text(strip=True)
                    t_link = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                    if st.button(f"📖 {t_name}", key=t_link):
                        st.session_state.current_story_url = t_link
                        st.session_state.page = "detail"
                        st.rerun()
                    found = True
            if not found:
                st.info("Không tìm thấy kết quả. Hãy kiểm tra lại từ khóa hoặc đăng nhập tài khoản.")
        except Exception as e:
            st.error(f"Lỗi tìm kiếm: {e}")
            
    st.markdown("---")
    direct_link = st.text_input("Hoặc dán trực tiếp link truyện / chương vào đây:")
    if direct_link:
        if "chuong" in direct_link:
            st.session_state.current_chapter_url = direct_link
            st.session_state.page = "reader"
            st.rerun()
        else:
            st.session_state.current_story_url = direct_link
            st.session_state.page = "detail"
            st.rerun()

# ================= TRANG 2: CHI TIẾT TRUYỆN =================
elif st.session_state.page == "detail":
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.page = "home"
        st.rerun()
        
    try:
        res = requests.get(st.session_state.current_story_url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tieu_de_truyen = soup.find('h1') or soup.find('h2', class_='title')
        st.title(tieu_de_truyen.get_text(strip=True) if tieu_de_truyen else "Thông tin truyện")
        
        st.subheader("📑 Danh sách chương:")
        list_chuong = []
        for a in soup.find_all('a', href=True):
            if 'chuong-' in a['href']:
                c_name = a.get_text(strip=True)
                c_link = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                if (c_name, c_link) not in list_chuong:
                    list_chuong.append((c_name, c_link))
                    
        if list_chuong:
            chon_chuong = st.selectbox("Chọn chương:", list_chuong, format_func=lambda x: x[0])
            if st.button("🚀 Bắt đầu nghe chương này"):
                st.session_state.current_chapter_url = chon_chuong[1]
                st.session_state.page = "reader"
                st.rerun()
        else:
            st.warning("Chưa tải được danh sách chương. Vui lòng đảm bảo bạn đã đăng nhập thành công.")
    except Exception as e:
        st.error(f"Lỗi tải trang truyện: {e}")

# ================= TRANG 3: ĐỌC & AUDIO =================
elif st.session_state.page == "reader":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Về mục lục"):
            st.session_state.page = "detail"
            st.rerun()
    with col2:
        if st.button("🏠 Về trang chủ"):
            st.session_state.page = "home"
            st.rerun()
            
    try:
        res = requests.get(st.session_state.current_chapter_url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tieu_de_c = soup.find('h2', class_='chapter-title') or soup.find('a', class_='chapter-title')
        st.subheader(tieu_de_c.get_text(strip=True) if tieu_de_c else "Chương Truyện")
        
        noi_dung_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')
        if not noi_dung_div:
            noi_dung_div = soup.find('div', class_='box-content')
            
        if noi_dung_div:
            van_ban = noi_dung_div.get_text(separator=' ', strip=True)
            
            with st.spinner("🤖 AI đang tạo giọng đọc âm thanh..."):
                tts = gTTS(text=van_ban[:3500], lang='vi', slow=False)
                tts.save("temp_voice.mp3")
                
            with open("temp_voice.mp3", "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
            link_sau = ""
            nut_sau = soup.find('a', id='next-chapter') or soup.find('a', class_=['btn', 'next'])
            if not nut_sau:
                for a in soup.find_all('a', href=True):
                    if 'sau' in a.get_text().lower() or 'tiếp' in a.get_text().lower():
                        nut_sau = a
                        break
            if nut_sau and nut_sau.get('href'):
                n_href = nut_sau['href']
                link_sau = n_href if n_href.startswith('http') else BASE_URL + n_href
                
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
                
                if st.button("⏩ Chuyển chương tiếp theo"):
                    st.session_state.current_chapter_url = link_sau
                    st.rerun()
            else:
                st.audio("temp_voice.mp3", format="audio/mp3")
                st.info("Đã đến chương mới nhất.")
                
            with st.expander("📄 Xem chữ của chương"):
                st.write(van_ban)
        else:
            st.error("Không tìm thấy nội dung. Có thể trang web đã chặn quyền truy cập do chưa đăng nhập.")
    except Exception as e:
        st.error(f"Lỗi: {e}")
