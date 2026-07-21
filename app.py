import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import base64

# Cấu hình giao diện hiển thị trên điện thoại
st.set_page_config(page_title="Trình Duyệt Truyện Audio AI", layout="centered")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'}
BASE_URL = "https://tutien.pro"

# Khởi tạo các biến lưu trữ trạng thái nếu chưa có
if 'url_hien_tai' not in st.session_state:
    st.session_state.url_hien_tai = ""
if 'tu_khoa_tim' not in st.session_state:
    st.session_state.tu_khoa_tim = ""

st.title("📚 Trình Duyệt & Đọc Truyện Audio")
st.write("Tìm kiếm truyện từ Tutien.pro và tự động đọc rảnh tay.")

# --- PHẦN 1: TÌM KIẾM TRUYỆN ---
st.subheader("🔍 Tìm kiếm truyện")
tu_khoa = st.text_input("Nhập tên truyện cần tìm:", value=st.session_state.tu_khoa_tim)

if tu_khoa:
    st.session_state.tu_khoa_tim = tu_khoa
    # Giả lập đường dẫn tìm kiếm của web (thay đổi tùy theo cấu trúc thực tế của tutien.pro)
    search_url = f"{BASE_URL}/tim-kiem?keyword={tu_khoa}"
    
    try:
        res = requests.get(search_url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Tìm danh sách kết quả (Ví dụ tìm các thẻ chứa link truyện)
        items = soup.find_all('a', class_='story-title') or soup.find_all('h3', class_='title')
        
        if items:
            st.write("Kết quả tìm thấy:")
            for item in items[:5]: # Hiển thị 5 kết quả đầu tiên
                link_a = item if item.name == 'a' else item.find('a')
                if link_a and link_a.get('href'):
                    ten_truyen = link_a.get_text(strip=True)
                    href = link_a['href']
                    full_link = href if href.startswith('http') else BASE_URL + href
                    
                    if st.button(f"📖 {ten_truyen}", key=full_link):
                        st.session_state.url_hien_tai = full_link
        else:
            st.info("Nhập link trực tiếp nếu không tìm thấy qua thanh tìm kiếm:")
    except:
        st.error("Không thể kết nối bộ tìm kiếm. Bạn có thể dán trực tiếp link chương truyện vào ô bên dưới.")

# Ô nhập link trực tiếp phòng trường hợp tìm kiếm lỗi
link_truoc = st.text_input("Hoặc dán trực tiếp link Chương truyện vào đây:", value=st.session_state.url_hien_tai)
if link_truoc:
    st.session_state.url_hien_tai = link_truoc

# --- PHẦN 2: XỬ LÝ ĐỌC TRUYỆN & TỰ ĐỘNG CHUYỂN CHƯƠNG ---
if st.session_state.url_hien_tai:
    url = st.session_state.url_hien_tai
    st.markdown("---")
    st.warning(f"Đang xem: {url}")
    
    try:
        res = requests.get(url, headers=HEADERS)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Lấy tiêu đề chương
        tiei_de = soup.find('h2', class_='chapter-title') or soup.find('a', class_='chapter-title')
        tieu_de_text = tiei_de.get_text(strip=True) if tiei_de else "Chương Truyện"
        st.subheader(tieu_de_text)
        
        # Lấy nội dung chữ
        noi_dung_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')
        if not noi_dung_div:
            noi_dung_div = soup.find('div', class_='box-content')
            
        if noi_dung_div:
            van_ban = noi_dung_div.get_text(separator=' ', strip=True)
            
            # Tạo Audio bằng AI Google miễn phí
            with st.spinner("🤖 AI đang chuyển nội dung thành giọng đọc..."):
                tts = gTTS(text=van_ban[:3000], lang='vi', slow=False) # Giới hạn 3000 ký tự đầu để load nhanh, có thể bỏ [:3000] nếu muốn đọc hết sạch chương dài
                tts.save("temp_voice.mp3")
            
            # Đọc file audio để nhúng vào giao diện
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

            # HIỂN THỊ TRÌNH PHÁT AUDIO VÀ TỰ ĐỘNG CHUYỂN CHƯƠNG BẰNG JAVASCRIPT
            if link_chuong_tiep:
                st.write("Chế độ: **Tự động chuyển chương khi đọc xong đang bật** 🔄")
                # Đoạn code JavaScript này sẽ phát hiện khi audio kết thúc và tự động tải trang mới
                audio_html = f"""
                <audio id="audio-player" controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                <script>
                var audio = document.getElementById('audio-player');
                audio.onended = function() {{
                    window.parent.postMessage({{type: 'streamlit:set_widget_value', from: 'link_truoc', value: '{link_chuong_tiep}'}}, '*');
                    st.experimental_rerun();
                }};
                </script>
                """
                st.components.v1.html(audio_html, height=100)
                
                if st.button("▶ Chuyển nhanh sang chương tiếp theo"):
                    st.session_state.url_hien_tai = link_chuong_tiep
                    st.rerun()
            else:
                st.audio("temp_voice.mp3", format="audio/mp3")
                st.info("Đã đến chương mới nhất của bộ truyện này.")
            
            # Hiển thị chữ bên dưới để vừa nghe vừa đọc nếu muốn
            with st.expander("📄 Xem nội dung chữ của chương"):
                st.write(van_ban)
                
        else:
            st.error("Không tìm thấy nội dung chữ của chương truyện này.")
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi tải chương: {e}")