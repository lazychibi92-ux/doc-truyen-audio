import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import base64

st.set_page_config(page_title="Trình Duyệt Truyện Audio", layout="centered")

BASE_URL = "https://tutien.pro"

# Quản lý Session State để lưu trạng thái điều hướng
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'current_story_url' not in st.session_state:
    st.session_state.current_story_url = ""
if 'current_chapter_url' not in st.session_state:
    st.session_state.current_chapter_url = ""

# --- PHẦN 0: CÀI ĐẶT COOKIE (VƯỢT ĐĂNG NHẬP) ---
with st.expander("🔑 Cài đặt Cookie tài khoản (Bắt buộc nếu web yêu cầu đăng nhập)"):
    cookie_nhap = st.text_area("Dán Cookie tutien.pro của bạn vào đây:", value=st.session_state.get('cookie', ''))
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
    st.write("Duyệt truyện và nghe audio rảnh tay từ Tutien.pro")

    # Thanh tìm kiếm
    tu_khoa = st.text_input("🔍 Tìm kiếm tên truyện...")
    if tu_khoa:
        try:
            search_url = f"{BASE_URL}/tim-kiem?keyword={tu_khoa}"
            res = requests.get(search_url, headers=HEADERS)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            items = soup.find_all('div', class_='item-truyen') or soup.find_all('h3', class_='title')
            st.subheader("Kết quả tìm kiếm:")
            
            # Quét tìm link truyện
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
                st.info("Không tìm thấy kết quả hoặc từ khóa chưa chính xác.")
        except Exception as e:
            st.error(f"Lỗi tìm kiếm: {e}")
            
    st.markdown("---")
    st.subheader("💡 Hoặc dán trực tiếp link truyện / chương bất kỳ:")
    direct_link = st.text_input("Dán link vào đây:")
    if direct_link:
        if "chuong" in direct_link:
            st.session_state.current_chapter_url = direct_link
            st.session_state.page = "reader"
            st.rerun()
        else:
            st.session_state.current_story_url = direct_link
            st.session_state.page = "detail"
            st.rerun()

# ================= TRANG 2: CHI TIẾT TRUYỆN & MỤC LỤC =================
elif st.session_state.page == "detail":
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.page = "home"
        st.rerun()
        
    try:
        res = requests.get(st.session_state.current_story_url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Lấy tên truyện
        tieu_de_truyen = soup.find('h1') or soup.find('h2', class_='title')
        st.title(tieu_de_truyen.get_text(strip=True) if tieu_de_truyen else "Thông tin truyện")
        
        st.subheader("📑 Danh sách chương:")
        
        # Lấy danh sách các chương
        list_chuong = []
        for a in soup.find_all('a', href=True):
            if 'chuong-' in a['href']:
                c_name = a.get_text(strip=True)
                c_link = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                if (c_name, c_link) not in list_chuong:
                    list_chuong.append((c_name, c_link))
                    
        if list_chuong:
            # Hiển thị dạng chọn dropdown hoặc các nút bấm danh sách
            chon_chuong = st.selectbox("Chọn chương để đọc/nghe:", list_chuong, format_func=lambda x: x[0])
            if st.button("🚀 Bắt đầu nghe chương này"):
                st.session_state.current_chapter_url = chon_chuong[1]
                st.session_state.page = "reader"
                st.rerun()
        else:
            st.warning("Chưa tải được danh sách chương. Hãy kiểm tra lại Cookie đăng nhập.")
    except Exception as e:
        st.error(f"Lỗi tải trang truyện: {e}")

# ================= TRANG 3: TRÌNH ĐỌC & PHÁT AUDIO TỰ ĐỘNG =================
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
        
        # Tiêu đề chương
        tieu_de_c = soup.find('h2', class_='chapter-title') or soup.find('a', class_='chapter-title')
        st.subheader(tieu_de_c.get_text(strip=True) if tieu_de_c else "Chương Truyện")
        
        # Nội dung chữ
        noi_dung_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')
        if not noi_dung_div:
            noi_dung_div = soup.find('div', class_='box-content')
            
        if noi_dung_div:
            van_ban = noi_dung_div.get_text(separator=' ', strip=True)
            
            with st.spinner("🤖 AI đang tạo giọng đọc âm thanh..."):
                tts = gTTS(text=van_ban[:3500], lang='vi', slow=False) # Lấy 3500 ký tự đầu mỗi chương
                tts.save("temp_voice.mp3")
                
            with open("temp_voice.mp3", "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
            # Tìm link chương sau để tự động chuyển
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
                
            # Trình phát audio kèm lệnh tự động chạy chương tiếp theo
            if link_sau:
                st.write("Trạng thái: **Tự động chuyển chương khi đọc xong** 🔄")
                audio_html = f"""
                <audio id="audio-player" controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                <script>
                var audio = document.getElementById('audio-player');
                audio.onended = function() {{
                    window.location.href = window.location.href; // Tải lại để nhận chương mới
                }};
                </script>
                """
                st.components.v1.html(audio_html, height=100)
                
                if st.button("⏩ Chuyển sang chương tiếp theo ngay lập tức"):
                    st.session_state.current_chapter_url = link_sau
                    st.rerun()
            else:
                st.audio("temp_voice.mp3", format="audio/mp3")
                st.info("Đã đến chương mới nhất.")
                
            with st.expander("📄 Xem chữ của chương"):
                st.write(van_ban)
        else:
            st.error("Không tìm thấy nội dung chương. Hãy kiểm tra lại Cookie tài khoản của bạn.")
    except Exception as e:
        st.error(f"Lỗi: {e}")