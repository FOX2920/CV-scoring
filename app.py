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
from docx import Document
from analyze import dashboard
from config import cleaned_schema, new_schema

# Function definitions
def is_valid_url(url):
    pattern = r'https://hiring\.base\.vn/opening/candidates/(\d+)\?stage=(\d+)$'
    return re.match(pattern, url) is not None

def load_job_descriptions(csv_file):
    df = pd.read_csv(csv_file)
    return dict(zip(df['Position'], df['Job_Description']))

def get_pdf_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return ' '.join(text.split()) # Xóa khoảng trắng thừa nếu có
    except Exception as e:
        st.error(f"Lỗi khi tải hoặc trích xuất văn bản từ URL {url}: {str(e)}")
        return None

def get_docx_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with BytesIO(response.content) as f:
            document = Document(f)
            text = ""
            for para in document.paragraphs:
                text += para.text + "\n"
        return ' '.join(text.split()) # Xóa khoảng trắng thừa nếu có
    except Exception as e:
        print(f"Lỗi khi tải hoặc trích xuất văn bản từ URL {url}: {str(e)}")
        return None

# Hàm kiểm tra định dạng file và chọn hàm tương ứng
def get_cv_text_from_url(cv_url):
    if not isinstance(cv_url, str):
        print(f"Invalid URL format: {cv_url}. Expected string, got {type(cv_url)}.")
        return None
    
    cv_url = cv_url.strip()  # Remove any leading/trailing whitespace
    
    if not cv_url:  # Check if the URL is empty after stripping
        print("Empty URL provided.")
        return None

    if cv_url.lower().endswith('.pdf'):
        return get_pdf_text_from_url(cv_url)
    elif cv_url.lower().endswith('.docx'):
        return get_docx_text_from_url(cv_url)
    else:
        print(f"Unsupported file format for URL: {cv_url}")
        return None

def get_gemini_response1(prompt, content):
    model = genai.GenerativeModel('gemini-1.5-flash',
                                    generation_config={
                                        "response_mime_type": "application/json",
                                        "response_schema": cleaned_schema # Dùng schema đã làm sạch
                                    }
                                    )
def get_gemini_response2(prompt, content):
    model = genai.GenerativeModel('gemini-1.5-flash',
                                    generation_config={
                                        "response_mime_type": "application/json",
                                        "response_schema": new_schema # Dùng schema đã làm sạch
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

# Extract numeric value from 'expect_salary' (e.g., '2,000 (USD/tháng)' => 2000)
def extract_numeric_salary(salary):
    match = re.search(r'(\d{1,3}(?:,\d{3})*)', salary)
    return int(match.group(1).replace(',', '')) if match else None
# Extract 'Mức lương mong muốn' (expected salary) from the 'fields' column
def extract_salary(fields):
    for field in fields:
        if field.get('id') == 'muc_luong_mong_muon':
            return extract_numeric_salary(field.get('value'))
    return None

def process_data(data):
    if 'candidates' not in data:
        st.error("Không tìm thấy ứng viên trong phản hồi.")
        return None
    df = pd.DataFrame(data['candidates'])
    
    df['cvs'] = df['cvs'].apply(lambda x: x[0] if len(x) > 0 else None)
    df['cvs'] = df['cvs'].astype(str) 
    df['title'] = df['title'].apply(lambda x: re.sub(r'<.*?>', '', x) if isinstance(x, str) else x)
    df['name'] = df['name'].apply(lambda x: unescape(x))
    df['expect_salary'] = df['form'].apply(extract_salary)
    # Filter rows where 'cvs' is not None
    df = df[df['cvs'].notnull()]
    df = df[df['cvs']!="None"]
    # Save to CSV
    df = df[df['expect_salary'].notnull()]
    df = df[df['expect_salary']!=""]
    df = df.dropna(axis=1, how='any')
    selected_df = df[['id', 'name', 'email', 'status', 'cvs', 'expect_salary']]
    
    return selected_df

def load_job_descriptions():
    jd_df = pd.read_csv('JD_tc.csv')
    return jd_df

def select_jd(salary, jd_df):
    if salary < 500:
        return jd_df.iloc[0]
    elif 500 <= salary < 1000:
        return jd_df.iloc[1]
    elif 1000 <= salary < 1500:
        return jd_df.iloc[2]
    else:  # salary >= 1500
        return jd_df.iloc[3]

def process_data(data):
    if 'candidates' not in data:
        st.error("Không tìm thấy ứng viên trong phản hồi.")
        return None
    df = pd.DataFrame(data['candidates'])
    
    df['cvs'] = df['cvs'].apply(lambda x: x[0] if len(x) > 0 else None)
    df['cvs'] = df['cvs'].astype(str) 
    df['title'] = df['title'].apply(lambda x: re.sub(r'<.*?>', '', x) if isinstance(x, str) else x)
    df['name'] = df['name'].apply(lambda x: unescape(x))
    df['expect_salary'] = df['form'].apply(extract_salary)
    df = df[df['cvs'].notnull()]
    df = df[df['cvs']!="None"]
    df = df[df['expect_salary'].notnull()]
    df = df[df['expect_salary']!=""]
    df = df.dropna(axis=1, how='any')
    selected_df = df[['id', 'name', 'email', 'status', 'cvs', 'expect_salary']]
    
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
    2. Nhập URL danh sách ứng viên từ hệ thống tuyển dụng Base. URL phải có định dạng:
       `https://hiring.base.vn/opening/candidates/[opening_id]?stage=[stage_id]`
    3. Nhấp vào nút "Lấy Thông Tin Ứng Viên" để bắt đầu quá trình.
    4. Thông tin ứng viên sẽ được hiển thị trong một bảng và bạn có thể tải xuống dưới dạng file CSV.
    """)

with st.sidebar.expander("📊 Hướng dẫn sử dụng chức năng Đánh giá CV", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Đánh giá CV".
    2. Tải lên file CSV chứa thông tin CV. File CSV cần có các cột sau:
       - "name" (tên ứng viên)
       - "cvs" (link đến file CV)
       - "expect_salary" (mức lương mong muốn)
    3. Nhấn "Đánh Giá CV" để bắt đầu. Hệ thống sẽ tự động chọn JD phù hợp dựa trên mức lương mong muốn và trả về kết quả đánh giá chi tiết, bao gồm điểm số và tóm tắt.
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
- Đảm bảo bạn có quyền truy cập vào các file CV được liên kết trong file CSV và vào hệ thống tuyển dụng Base.
- Công cụ này dùng để hỗ trợ quyết định, không thay thế đánh giá của chuyên gia HR.
- Nếu gặp lỗi, kiểm tra lại cấu hình biến môi trường GOOGLE_API_KEY và BASE_API_KEY, định dạng file CSV, URL danh sách ứng viên.
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
    
    st.subheader("📁 Tải lên file CSV chứa link CV")
    uploaded_file = st.file_uploader("Chọn file CSV", type=['csv'])

    if st.button("🔍 Đánh giá CV"):
        if not uploaded_file:
            st.error("❌ Vui lòng tải lên file CSV chứa link CV.")
        else:
            df = pd.read_csv(uploaded_file)
            jd_df = load_job_descriptions()
            results = []
            progress_bar = st.progress(0)
            
            for i, row in df.iterrows():
                name = row['name']
                cv_url = row.get('cvs')
                expect_salary = row.get('expect_salary', 0)
                
                jd_row = select_jd(expect_salary, jd_df)
                jd1 = jd_row['Job_Description']
                position = jd_row['Position']
                
                cv_text = get_cv_text_from_url(cv_url)
        
                if cv_text:
                    prompt1 = f"""
                    Bạn là một chuyên gia nhân sự và tuyển dụng. Hãy đánh giá CV dưới đây dựa trên mô tả công việc và cung cấp phản hồi chính xác theo schema JSON được định nghĩa.
                    Mô tả công việc:
                    {jd1}

                    Điểm trừ ( mỗi tiêu chí +5 điểm) nếu hồ sơ có các điểm sau : 
                    1.	Thiếu kinh nghiệm: Không có đủ kinh nghiệm làm việc liên quan đến vị trí ứng tuyển cho các vị trí nhân viên trở lên. 
                    2.	Lỗi chính tả và ngữ pháp: Hồ sơ có nhiều lỗi chính tả hoặc ngữ pháp, thể hiện sự thiếu cẩn thận.
                    3.	Thời gian nghỉ việc dài: Có khoảng thời gian dài không làm việc mà không có lý do rõ ràng.
                    4.	Thay đổi công việc thường xuyên: Có nhiều lần thay đổi công việc trong thời gian ngắn, có thể gây lo ngại về tính ổn định.
                    5.	Thiếu thông tin quan trọng: Hồ sơ không cung cấp đủ thông tin về quá trình học tập, kinh nghiệm làm việc hoặc kỹ năng.
                    6.	Thiếu thông tin liên hệ: Không cung cấp thông tin liên lạc đầy đủ hoặc chính xác.
                    7.	Không rõ ràng về mục tiêu nghề nghiệp: Mục tiêu nghề nghiệp không rõ ràng hoặc không phù hợp với vị trí ứng tuyển.
                    8.	Thái độ không chuyên nghiệp: Sử dụng ngôn ngữ không phù hợp hoặc có những bình luận tiêu cực về công việc trước đây.
                    
                    Điểm cộng  ( Mỗi tiêu chí +5 điểm ) nếu hồ sơ thể hiện : 
                    1.	Kinh nghiệm làm việc phong phú: Có nhiều năm kinh nghiệm trong lĩnh vực liên quan hoặc trong các vị trí tương tự.
                    2.	Kỹ năng chuyên môn mạnh: Sở hữu các kỹ năng chuyên môn cần thiết cho công việc, như kỹ năng phân tích, lập trình, hay quản lý dự án.
                    3.	Chứng chỉ và bằng cấp phù hợp: Có các chứng chỉ và bằng cấp liên quan đến vị trí ứng tuyển, thể hiện sự cam kết trong nghề nghiệp.
                    4.	Kỹ năng giao tiếp tốt:  Khả năng giao tiếp rõ ràng và hiệu quả, có thể làm việc với nhiều đối tượng khác nhau.
                    5.	Thành tích nổi bật: Có thành tích đáng chú ý trong công việc trước đây, như tăng hiệu quả, cải thiện quy trình làm việc, hoặc dự án thành công.
                    6.	Thái độ tích cực và chuyên nghiệp: Thể hiện sự nhiệt tình, trách nhiệm và thái độ tích cực trong công việc.
                    
                    CV:
                    {cv_text}
        
                    Vui lòng trả về kết quả đánh giá theo đúng schema JSON đã định nghĩa.
                    Chú ý: Các tiêu chí mà bạn không chắc hoặc không ghi rõ trong CV thì bạn sẽ +0 điểm.
                    """
                    prompt1 = ' '.join(prompt1.split())
                    # prompt 2
                    prompt2 = f"""
                        Bạn là một chuyên gia nhân sự và tuyển dụng. Hãy đánh giá CV dưới đây dựa trên mô tả công việc và cung cấp phản hồi **chính xác** theo định dạng dưới đây mà không thêm bất kỳ thông tin nào khác.
                        Các tiêu chí đánh giá bao gồm:
                        
                        1. **Mức độ phù hợp với vai trò** (trên thang điểm 0-10): Đánh giá mức độ phù hợp của kinh nghiệm và trình độ của ứng viên so với trách nhiệm công việc.
                        2. **Kỹ năng kỹ thuật** (trên thang điểm 0-10): Đánh giá mức độ thành thạo của ứng viên đối với các kỹ năng kỹ thuật được yêu cầu trong mô tả công việc.
                        3. **Kinh nghiệm** (trên thang điểm 0-10): Đánh giá kinh nghiệm của ứng viên về số năm và tính phù hợp với vai trò.
                        4. **Trình độ học vấn** (trên thang điểm 0-10): Đánh giá trình độ học vấn của ứng viên so với yêu cầu công việc.
                        5. **Kỹ năng mềm** (trên thang điểm 0-10): Đánh giá các kỹ năng mềm của ứng viên như giao tiếp, làm việc nhóm, và lãnh đạo.
                        
                        Sau khi đánh giá, cung cấp phản hồi **chính xác** theo định dạng dưới đây, không thêm bất kỳ nội dung nào khác:
                        
                        **Định dạng phản hồi:**
                        - Mức độ phù hợp: [điểm trên 10]
                        - Kỹ năng kỹ thuật: [điểm trên 10]
                        - Kinh nghiệm: [điểm trên 10]
                        - Trình độ học vấn: [điểm trên 10]
                        - Kỹ năng mềm: [điểm trên 10]
                        - Điểm tổng quát: [điểm tổng quát trên 10]
                        - Tóm tắt: [giải thích ngắn gọn về điểm mạnh và điểm yếu của ứng viên]
                        
                        **Mô tả công việc:**
                        {jd2}
                        
                        **CV:**
                        {cv_text}
                        
                        Vui lòng chỉ trả về các thông tin được yêu cầu trong đúng định dạng trên, không thêm bất kỳ thông tin hoặc nhận xét nào khác.
                        """
                    prompt2 = ' '.join(prompt2.split())
                    try:
                        response1 = get_gemini_response1(prompt1, cv_text)
                        time.sleep(2)
                        response2 = get_gemini_response2(prompt2, cv_text)
                        
                        main_criteria_score = response1["truc_nang_luc"] + response1["truc_van_hoa"] + response1["truc_tuong_lai"] + response1["tieu_chi_khac"]
                        total_score = main_criteria_score + response1["diem_cong"] - response1["diem_tru"]
                        
                        # Determine pass/fail based on salary and main criteria score
                        if expect_salary < 500:
                            pass_fail = "Pass" if main_criteria_score >= 70 else "Fail"
                        elif 500 <= expect_salary < 1000:
                            pass_fail = "Pass" if main_criteria_score >= 75 else "Fail"
                        elif 1000 <= expect_salary < 1500:
                            pass_fail = "Pass" if main_criteria_score >= 80 else "Fail"
                        else:  # expect_salary >= 1500
                            pass_fail = "Pass" if main_criteria_score >= 85 else "Fail"
        
                        uv = {
                            'Tên ứng viên': name,
                            'Vị trí': position,
                            'Trục Năng lực soft skill': response1["truc_nang_luc"],
                            'Trục Phù hợp Văn hóa soft skill': response1["truc_van_hoa"],
                            'Trục Tương lai soft skill': response1["truc_tuong_lai"],
                            'Tiêu chí khác soft skill': response1["tieu_chi_khac"],
                            'Điểm cộng soft skill': response1["diem_cong"],
                            'Điểm trừ soft skill': response1["diem_tru"],
                            'Điểm tổng quát soft skill': total_score,
                            'Đánh giá soft skill': pass_fail,
                            'Tóm tắt soft skill': response1["tom_tat"],
                            'Mức độ phù hợp hard skill': int((str(response2).split('\n')[0]).split(':')[1].strip()),
                            'Kỹ năng kỹ thuật hard skill': int((str(response2).split('\n')[1]).split(':')[1].strip()),
                            'Kinh nghiệm hard skill': int((str(response2).split('\n')[2]).split(':')[1].strip()),
                            'Trình độ học vấn hard skill': int((str(response2).split('\n')[3]).split(':')[1].strip()),
                            'Kỹ năng mềm hard skill': int((str(response2).split('\n')[4]).split(':')[1].strip()),
                            'Điểm tổng quát hard skill': round(float((str(response2).split('\n')[5]).split(':')[1].strip()), 2),
                            'Tóm tắt hard skill': (str(response2).split('\n')[6]).split(':')[1].strip()
                        }
        
                        results.append(uv)
        
                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý CV từ {cv_url}: {str(e)}")
        
                progress_bar.progress((i + 1) / len(df))

            if results:
                st.subheader("📊 Kết quả đánh giá CV")
                df_results = pd.DataFrame(results)
                final_df = pd.merge(df, df_results, left_on='name', right_on='Tên ứng viên', how='inner')
                final_df.drop(columns=['Tên ứng viên'], inplace=True)
                final_df.rename(columns={
                    'id': 'Mã ứng viên',
                    'name': "Tên ứng viên",
                    'email': 'Email',
                    'expect_salary': "Mức lương mong muốn",
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
