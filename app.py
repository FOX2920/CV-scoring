import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import pandas as pd
import requests
from io import BytesIO
import os
import time
import re
from html import unescape
import json
from analyze import dashboard
from config import cleaned_schema

# Function definitions
def is_valid_url(url):
    pattern = r'https://hiring\.base\.vn/opening/candidates/(\d+)\?stage=(\d+)$'
    return re.match(pattern, url) is not None

def load_job_descriptions(csv_file):
    df = pd.read_csv(csv_file)
    return dict(zip(df['Job_name'], df['Job_Description']))

def get_pdf_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return text
    except Exception as e:
        st.error(f"Lỗi khi tải hoặc trích xuất văn bản từ URL {url}: {str(e)}")
        return None

def get_gemini_response(prompt, content):
    model = genai.GenerativeModel('gemini-1.5-flash',
                                    generation_config={
                                        "response_mime_type": "application/json",
                                        "response_schema": cleaned_schema # Dùng schema đã làm sạch
                                    }
                                    )

    response = model.generate_content(prompt + content)
    response_json = json.loads(response.text)
    time.sleep(3)
    return response_json

def extract_ids_from_url(url):
    match = re.search(r'candidates/(\d+)\?stage=(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def fetch_data(job_url, access_token):
    opening_id, stage_id = extract_ids_from_url(job_url)
    if not opening_id or not stage_id:
        st.error("URL không hợp lệ. Không thể trích xuất opening_id và stage_id.")
        return None
    api_url = "https://hiring.base.vn/publicapi/v2/candidate/list"
    payload = {
        'access_token': access_token,
        'opening_id': opening_id,
        'num_per_page': '10000',
        'stage_id': stage_id,
        'start_date': '2023-11-01',
        'end_date': ''
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(api_url, headers=headers, data=payload)
    return response.json()

def process_data(data):
    if 'candidates' not in data:
        st.error("Không tìm thấy ứng viên trong phản hồi.")
        return None
    df = pd.DataFrame(data['candidates'])
    
    df['cvs'] = df['cvs'].apply(lambda x: x[0] if len(x) > 0 else None)
    df['title'] = df['title'].apply(lambda x: re.sub(r'<.*?>', '', x) if isinstance(x, str) else x)
    df['name'] = df['name'].apply(lambda x: unescape(x))
    df.drop(columns=['dob_day', 'dob_month', 'dob_year'], inplace=True)
    df = df[df['cvs'].notnull()]
    df = df.dropna(axis=1, how='any')
    selected_df = df[['id', 'name', 'email', 'status', 'cvs']]
    
    return selected_df

# Main application

st.set_page_config(page_title="Công Cụ Đánh Giá CV và Lấy Dữ Liệu Công Việc", layout="wide")
st.title("🚀 Công Cụ Đánh Giá CV và Lấy Dữ Liệu Công Việc")

# Configure Google API
api_key = st.secrets["GOOGLE_API_KEY"]
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Không tìm thấy GOOGLE_API_KEY trong biến môi trường. Vui lòng kiểm tra cấu hình trước khi sử dụng ứng dụng.")
    st.stop()

st.sidebar.header("📚 Hướng dẫn sử dụng")

st.sidebar.markdown("""
### 👋 Chào mừng bạn đến với Công cụ Đánh giá CV và Lấy Thông Tin Ứng Viên!
Ứng dụng này gồm ba chức năng chính:
1. **🔍 Lấy Thông Tin Ứng Viên**
2. **📊 Đánh giá CV**
3. **📈 Dashboard Phân tích**
""")

with st.sidebar.expander("🔍 Hướng dẫn sử dụng chức năng Lấy Thông Tin Ứng Viên", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Lấy Thông Tin Ứng Viên".
    2. Nhập URL danh sách ứng viên từ hệ thống tuyển dụng. URL phải có định dạng:
       `https://hiring.base.vn/opening/candidates/[opening_id]?stage=[stage_id]`
    3. Nhấp vào nút "Lấy Thông Tin Ứng Viên" để bắt đầu quá trình.
    4. Thông tin ứng viên sẽ được hiển thị trong một bảng và bạn có thể tải xuống dưới dạng file CSV.
    """)

with st.sidebar.expander("📊 Hướng dẫn sử dụng chức năng Đánh giá CV", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Đánh giá CV".
    2. Nhập JD(Job description) công việc mà bạn muốn đánh giá.
    3. Tải lên file CSV chứa thông tin CV. File CSV cần có cột "name" (tên ứng viên) và "cvs" (link đến file CV).
    4. Nhấn "Đánh Giá CV" để bắt đầu. Hệ thống sẽ trả về kết quả đánh giá chi tiết, bao gồm điểm số và tóm tắt.
    """)

with st.sidebar.expander("📈 Hướng dẫn sử dụng chức năng Dashboard", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Dashboard".
    2. Tải lên file CSV chứa kết quả đánh giá CV (có thể sử dụng file kết quả từ chức năng Đánh giá CV).
    3. Xem các biểu đồ và thống kê về ứng viên, bao gồm phân phối điểm, ma trận tương quan, và so sánh kỹ năng.
    4. Sử dụng các công cụ tương tác để phân tích sâu hơn về từng ứng viên.
    """)

st.sidebar.warning("""
**⚠️ Lưu ý:**
- Đảm bảo bạn có quyền truy cập vào các file CV được liên kết trong file CSV và vào hệ thống tuyển dụng.
- Công cụ này dùng để hỗ trợ quyết định, không thay thế đánh giá của chuyên gia HR.
- Nếu gặp lỗi, kiểm tra lại cấu hình biến môi trường GOOGLE_API_KEY, định dạng file CSV, URL danh sách ứng viên.
- Bảo mật thông tin ứng viên và tuân thủ các quy định về bảo vệ dữ liệu cá nhân.
""")

st.sidebar.success("✨ Chúc bạn sử dụng công cụ hiệu quả!")

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🔍 Lấy Dữ Liệu Ứng Viên", "📊 Đánh giá CV", "📈 Dashboard"])
    
with tab1:
    st.header("🔍 Lấy Dữ Liệu Ứng Viên")
    
    candidate_url = st.text_input("🔗 Nhập URL danh sách ứng viên:")
    access_token = st.secrets["BASE_API_KEY"]
    if st.button("🔎 Lấy Thông Tin Ứng Viên"):
        if candidate_url and access_token:
            if is_valid_url(candidate_url):
                with st.spinner("⏳ Đang lấy thông tin ứng viên..."):
                    data = fetch_data(candidate_url, access_token)
                    if data:
                        df = process_data(data)
                        if df is not None:
                            st.success("✅ Đã lấy thông tin ứng viên thành công!")
                            st.dataframe(df)
                            
                            csv = df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 Tải xuống CSV",
                                data=csv,
                                file_name="thong_tin_ung_vien.csv",
                                mime="text/csv",
                            )
            else:
                st.error("❌ URL không hợp lệ. Vui lòng nhập URL theo định dạng: https://hiring.base.vn/opening/candidates/[opening_id]?stage=[stage_id]")
        else:
            st.warning("⚠️ Vui lòng nhập cả URL danh sách ứng viên và mã truy cập.")

with tab2:
    st.header("📊 Đánh giá và Lọc CV")
    
    col1, col2 = st.columns(2)

    with col1:
        jd = st.text_area("Nhập thông tin công việc: ", height=500)

    with col2:
        st.subheader("📁 Tải lên file CSV chứa link CV")
        uploaded_file = st.file_uploader("Chọn file CSV", type=['csv'])

    if st.button("🔍 Đánh giá CV"):
        if not jd:
            st.error("❌ Vui lòng nhập mô tả công việc.")
        elif not uploaded_file:
            st.error("❌ Vui lòng tải lên file CSV chứa link CV.")
        else:
            df = pd.read_csv(uploaded_file)
            results = []
            progress_bar = st.progress(0)
            
            for i, row in df.iterrows():
                name = row['name']
                cv_url = row['cvs']
                cv_text = get_pdf_text_from_url(cv_url)

                if cv_text:
                    prompt = f"""
                    Bạn là một chuyên gia nhân sự và tuyển dụng. Hãy đánh giá CV dưới đây dựa trên mô tả công việc và cung cấp phản hồi chính xác theo schema JSON được định nghĩa.
                    Mô tả công việc:
                    {jd}

                    CV:
                    {cv_text}

                    Vui lòng trả về kết quả đánh giá theo đúng schema JSON đã định nghĩa.
                    """

                    try:
                        response = get_gemini_response(prompt, cv_text)
                        

                        uv = {
                            'Tên ứng viên': name,
                            'Mức độ phù hợp': response["muc_do_phu_hop"],
                            'Kỹ năng kỹ thuật': response["ky_nang_ky_thuat"],
                            'Kinh nghiệm': response["kinh_nghiem"],
                            'Trình độ học vấn': response["trinh_do_hoc_van"],
                            'Kỹ năng mềm': response["ky_nang_mem"],
                            'Điểm tổng quát': round( response["diem_tong_quat"], 2),
                            'Tóm tắt': response["tom_tat"]
                        }

                        results.append(uv)

                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý CV từ {cv_url}: {str(e)}")

                progress_bar.progress((i + 1) / len(df))


            # Xử lý kết quả và hiển thị như trước
            if results:
                st.subheader("📊 Kết quả đánh giá CV")
                df_results = pd.DataFrame(results)
                final_df = pd.merge(df, df_results, left_on='name', right_on='Tên ứng viên', how='inner')
                final_df.drop(columns=['Tên ứng viên'], inplace=True)
                final_df.rename(columns={
                    'id': 'Mã ứng viên',
                    'name': "Tên ứng viên",
                    'email': 'Email',
                    'status': 'Trạng thái',
                    'cvs': 'Link CV',
                }, inplace=True)
                
                st.header("📋 Dữ liệu chi tiết")
                st.dataframe(final_df)

                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Tải xuống kết quả đánh giá CSV",
                    data=csv,
                    file_name="ket_qua_danh_gia_cv.csv",
                    mime="text/csv",
                )
            else:
                st.warning("⚠️ Không có kết quả nào được tạo. Vui lòng kiểm tra API key và thử lại.")
with tab3:
    dashboard()

st.markdown("---")
st.markdown("🚀 Powered by Streamlit | 💼 Created for HR professionals")
