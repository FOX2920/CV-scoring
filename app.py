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
from bs4 import BeautifulSoup
from config import cleaned_schema, new_schema
from PIL import Image

im = Image.open("aplus.ico")

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
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest',
                                  generation_config={
                                      "response_mime_type": "application/json",
                                      "response_schema": cleaned_schema
                                  })
    response = model.generate_content(prompt + content)
    response_json = json.loads(response.text)
    time.sleep(3)
    return response_json
    
def get_gemini_response2(prompt, content):
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest',
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

def extract_salary(fields):
    for field in fields:
        if field.get('id') == 'muc_luong_mong_muon':  
            salary = extract_numeric_salary(field.get('value', '0'))
            return salary if salary is not None else -1
    return -1  # Return 0 if 'muc_luong_mong_muon' field is not found

def extract_numeric_salary(salary):
    if not salary:
        return 0
    match = re.search(r'(\d{1,3}(?:,\d{3})*)', str(salary))
    return int(match.group(1).replace(',', '')) if match else -1

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
    
    # Filter rows where 'cvs' is not None or "None"
    df = df[df['cvs'].notnull() & (df['cvs'] != "None")]
    
    # Remove columns with all NaN values
    df = df.dropna(axis=1, how='all')
    
    selected_df = df[['id', 'name', 'email', 'status', 'cvs', 'expect_salary']]
    
    return selected_df

def fetch_jd(job_url, access_token):
    opening_id, stage_id = extract_ids_from_url(job_url)
    if not opening_id or not stage_id:
        st.error("URL không hợp lệ. Không thể trích xuất opening_id và stage_id.")
        return None
    api_url = "https://hiring.base.vn/publicapi/v2/opening/get"
    payload = {
        'access_token': access_token,
        'id': opening_id,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(api_url, headers=headers, data=payload)
     # Parse the JSON response
    json_response = response.json()
    
    # Get the 'content' field
    html_content = json_response.get('opening', {}).get('content', '')
    
    # Use BeautifulSoup to convert HTML content to plain text
    soup = BeautifulSoup(html_content, "html.parser")
    plain_text = soup.get_text()
   
    return plain_text

def select_jd(salary, jd_df):
    if salary <= 0:  # If salary is not specified or invalid
        return pd.Series({'Position': "Chưa sắp xếp được vị trí", 'Job_Description': "Không có tiêu chí để chấm nên chấm 0 điểm hết"})
    elif 0 < salary < 500:
        return jd_df.iloc[0]
    elif 500 <= salary < 1000:
        return jd_df.iloc[1]
    elif 1000 <= salary < 1500:
        return jd_df.iloc[2]
    elif salary >= 1500:
        return jd_df.iloc[3]
# Main application

st.set_page_config(page_title="Công Cụ Đánh Giá CV và Lấy Dữ Liệu Công Việc", page_icon=im, layout="wide")
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
Ứng dụng này gồm hai chức năng chính:
1. **🔍 Lấy Thông Tin Ứng Viên và Đánh giá CV**
2. **📈 Dashboard Phân tích**
""")

with st.sidebar.expander("🔍 Hướng dẫn sử dụng chức năng Lấy Thông Tin và Đánh giá CV", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Lấy Dữ Liệu Ứng Viên và Đánh giá CV".
    2. Nhập URL danh sách ứng viên từ hệ thống tuyển dụng Base. URL phải có định dạng:
       `https://hiring.base.vn/opening/candidates/[opening_id]?stage=[stage_id]`
    3. Nhấp vào nút "Lấy Thông Tin Ứng Viên" để bắt đầu quá trình.
    4. Hệ thống sẽ tự động lấy thông tin ứng viên và đánh giá CV.(Khuyến khích sử dụng file CV pdf hoặc docx để lọc và chấm điểm dễ dàng hơn)
    5. Kết quả đánh giá sẽ được hiển thị trong một bảng và bạn có thể tải xuống dưới dạng file CSV.
    """)

with st.sidebar.expander("📈 Hướng dẫn sử dụng chức năng Dashboard", expanded=False):
    st.markdown("""
    1. Chuyển đến tab "Dashboard".
    2. Tải lên file CSV chứa kết quả đánh giá CV (file kết quả từ chức năng Lấy Thông Tin và Đánh giá CV).
    3. Xem các biểu đồ và thống kê về ứng viên, bao gồm:
       - Thông tin tổng quan
       - Phân tích đánh giá theo tiêu chí
       - Biểu đồ kỹ năng ứng viên
       - Lọc và sắp xếp ứng viên
       - Top ứng viên theo vị trí
    4. Sử dụng các công cụ tương tác để phân tích sâu hơn về từng ứng viên.
    """)

st.sidebar.warning("""
**⚠️ Lưu ý:**
- Đảm bảo bạn có quyền truy cập vào hệ thống tuyển dụng Base.
- Công cụ này dùng để hỗ trợ quyết định, không thay thế đánh giá của chuyên gia HR.
- Nếu gặp lỗi, kiểm tra lại cấu hình biến môi trường GOOGLE_API_KEY và BASE_API_KEY, URL danh sách ứng viên.
- Bảo mật thông tin ứng viên và tuân thủ các quy định về bảo vệ dữ liệu cá nhân.
""")

st.sidebar.success("✨ Chúc bạn sử dụng công cụ hiệu quả!")

# Tabs for different functionalities
tab1, tab3 = st.tabs(["🔍 Lấy Dữ Liệu Ứng Viên và 📊 Đánh giá CV", "📈 Dashboard"])
    
with tab1:
    st.header("🔍 Lấy Dữ Liệu Ứng Viên")
    
    candidate_url = st.text_input("🔗 Nhập URL danh sách ứng viên:")
    access_token = os.getenv('BASE_API_KEY')
    if st.button("🔎 Lấy Thông Tin Ứng Viên"):
        if candidate_url and access_token:
            if is_valid_url(candidate_url):
                data = process_data(fetch_data(candidate_url, access_token))
                st.success("✅ Đã lấy thông tin ứng viên thành công!")
                st.header("📊 Đánh giá và Lọc CV")
                jd_df = pd.read_csv('JD_tc.csv')
                jd2 = fetch_jd(candidate_url, access_token)
                results = []
                progress_bar = st.progress(0)
                    
                for i, (_, row) in enumerate(data.iterrows()):
                    name = row['name']
                    cv_url = row['cvs']
                    expect_salary = row.get('expect_salary', -1)
                    
                    cv_text = get_cv_text_from_url(cv_url)
                
                    if cv_text:
                        # Always evaluate using prompt 2
                        prompt2 = f"""
                        Bạn là một chuyên gia nhân sự và tuyển dụng. Hãy đánh giá CV dưới đây dựa trên mô tả công việc và cung cấp phản hồi chính xác theo schema JSON được định nghĩa.
                        Mô tả công việc:
                        {jd2}
                        CV:
                        {cv_text}
                        Vui lòng trả về kết quả đánh giá theo đúng schema JSON đã định nghĩa.
                        """
                        try:
                            response2 = get_gemini_response2(prompt2, cv_text)
                            main_CV_score = round((response2["muc_do_phu_hop"] + response2["ky_nang_ky_thuat"] + response2["kinh_nghiem"] + response2["trinh_do_hoc_van"] + response2["ky_nang_mem"])/5, 2)
                
                            if expect_salary > 0:
                                # If salary is specified, evaluate using prompt 1 and assign position
                                jd_row = select_jd(expect_salary, jd_df)
                                position = jd_row['Position']
                                jd1 = jd_row['Job_Description']
                                
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
                                response1 = get_gemini_response1(prompt1, cv_text)
                                main_criteria_score = response1["truc_nang_luc"] + response1["truc_van_hoa"] + response1["truc_tuong_lai"] + response1["tieu_chi_khac"] + response1["diem_cong"] - response1["diem_tru"]
                                
                                # Determine Pass/Fail based on salary and main criteria score
                                if expect_salary < 500:
                                    pass_fail = "Pass" if main_criteria_score >= 70 else "Fail"
                                elif 500 <= expect_salary < 1000:
                                    pass_fail = "Pass" if main_criteria_score >= 75 else "Fail"
                                elif 1000 <= expect_salary < 1500:
                                    pass_fail = "Pass" if main_criteria_score >= 80 else "Fail"
                                else:  # expect_salary >= 1500
                                    pass_fail = "Pass" if main_criteria_score >= 85 else "Fail"
                            else:
                                # If no salary is specified, use default values and don't assign a position
                                position = "Chưa sắp xếp được vị trí"
                                response1 = {
                                    "truc_nang_luc": 0,
                                    "truc_van_hoa": 0,
                                    "truc_tuong_lai": 0,
                                    "tieu_chi_khac": 0,
                                    "diem_cong": 0,
                                    "diem_tru": 0,
                                    "tom_tat": "Không có mức lương kỳ vọng, chỉ đánh giá kỹ năng chung"
                                }
                                main_criteria_score = 0
                                pass_fail = "N/A"
                
                            uv = {
                                'Tên ứng viên': name,
                                'Vị trí': position,
                                'Trục Năng lực soft skill': response1["truc_nang_luc"],
                                'Trục Phù hợp Văn hóa soft skill': response1["truc_van_hoa"],
                                'Trục Tương lai soft skill': response1["truc_tuong_lai"],
                                'Tiêu chí khác soft skill': response1["tieu_chi_khac"],
                                'Điểm cộng soft skill': response1["diem_cong"],
                                'Điểm trừ soft skill': response1["diem_tru"],
                                'Điểm tổng quát soft skill': main_criteria_score,
                                'Đánh giá soft skill': pass_fail,
                                'Tóm tắt soft skill': response1["tom_tat"],
                                'Mức độ phù hợp hard skill': response2["muc_do_phu_hop"],
                                'Kỹ năng kỹ thuật hard skill': response2["ky_nang_ky_thuat"],
                                'Kinh nghiệm hard skill': response2["kinh_nghiem"],
                                'Trình độ học vấn hard skill': response2["trinh_do_hoc_van"],
                                'Kỹ năng mềm hard skill': response2["ky_nang_mem"],
                                'Điểm tổng quát hard skill': main_CV_score,
                                'Tóm tắt hard skill': response2["tom_tat"]
                            }
                
                            results.append(uv)
                        except Exception as e:
                            st.error(f"❌ Lỗi khi xử lý CV từ {cv_url}: {str(e)}")
                            continue
            
                    progress_bar.progress(min(1.0, (i + 1) / len(data)))
                    
            if results:
                st.subheader("📊 Kết quả đánh giá CV")
                df_results = pd.DataFrame(results)
                final_df = pd.merge(data, df_results, left_on='name', right_on='Tên ứng viên', how='inner')
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
