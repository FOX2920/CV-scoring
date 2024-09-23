import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Hàm để tải và xử lý dữ liệu
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    return df

# Hàm tạo biểu đồ phân phối điểm
def plot_score_distribution(df, column):
    fig = px.histogram(df, x=column, nbins=20, marginal="box", 
                       title=f"Phân phối {column}",
                       labels={column: "Điểm", "count": "Số lượng ứng viên"})
    fig.update_layout(showlegend=False)
    return fig

# Hàm tạo biểu đồ tương quan
def plot_correlation_heatmap(df):
    corr_columns = ['Mức độ phù hợp', 'Kỹ năng kỹ thuật', 'Kinh nghiệm', 
                    'Trình độ học vấn', 'Kỹ năng mềm', 'Điểm tổng quát']
    corr = df[corr_columns].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", 
                    title="Ma trận tương quan giữa các tiêu chí")
    return fig

# Hàm tạo biểu đồ radar cho từng ứng viên
def plot_candidate_radar(df, candidate_name):
    categories = ['Mức độ phù hợp', 'Kỹ năng kỹ thuật', 'Kinh nghiệm', 
                  'Trình độ học vấn', 'Kỹ năng mềm']
    candidate_data = df[df['Tên ứng viên'] == candidate_name][categories].values[0]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=candidate_data,
        theta=categories,
        fill='toself',
        marker=dict(color='blue'),  # Adjust color for better contrast
        line=dict(color='blue')  # Adjust line color for visibility
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10]),
            angularaxis=dict(tickfont=dict(size=12, color='red'))  # Customize tick labels
        ),
        title=dict(text=f"Biểu đồ kỹ năng của {candidate_name}", font=dict(size=16, color='white')),
        font=dict(size=14, color='black'),  # Customize general font size and color
        showlegend=False
    )
    
    return fig


def dashboard():
    # Tiêu đề ứng dụng
    st.header("📈 Dashboard Phân tích")

    # Upload file
    uploaded_file = st.file_uploader("Chọn file CSV chứa dữ liệu ứng viên", type="csv")

    if uploaded_file is not None:
        # Tải dữ liệu
        df = load_data(uploaded_file)
        
        # Thông tin tổng quan
        st.header("📊 Thông tin tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số ứng viên", len(df))
        col2.metric("Điểm trung bình", f"{df['Điểm tổng quát'].mean():.2f}")
        col3.metric("Điểm cao nhất", df['Điểm tổng quát'].max())
        col4.metric("Điểm thấp nhất", df['Điểm tổng quát'].min())
        
        # Phân phối điểm và Ma trận tương quan
        st.header("📈 Phân tích điểm số")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_score_distribution(df, 'Điểm tổng quát'), use_container_width=True)
        with col2:
            st.plotly_chart(plot_correlation_heatmap(df), use_container_width=True)
        
        # So sánh kỹ năng
        st.header("🔍 So sánh kỹ năng")
        skills = ['Mức độ phù hợp', 'Kỹ năng kỹ thuật', 'Kinh nghiệm', 'Trình độ học vấn', 'Kỹ năng mềm']
        fig = go.Figure()
        for skill in skills:
            fig.add_trace(go.Box(y=df[skill], name=skill))
        fig.update_layout(title="So sánh phân phối các kỹ năng", yaxis_title="Điểm")
        st.plotly_chart(fig, use_container_width=True)
        
        # Biểu đồ radar cho từng ứng viên
        st.header("🎯 Biểu đồ kỹ năng ứng viên")
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_summary = df[df['Tên ứng viên'] == selected_candidate]['Tóm tắt'].values[0]
            st.subheader("Tóm tắt ứng viên")
            st.write(candidate_summary)
        with col2:
            st.plotly_chart(plot_candidate_radar(df, selected_candidate), use_container_width=True)
        
        # Top ứng viên
        st.header("🏆 Top ứng viên")
        top_candidates = df.sort_values('Điểm tổng quát', ascending=False).head(5)
        st.table(top_candidates[['Tên ứng viên', 'Điểm tổng quát', 'Mức độ phù hợp', 'Kỹ năng kỹ thuật', 'Kinh nghiệm', 'Trình độ học vấn', 'Kỹ năng mềm']])
        
        # Dữ liệu chi tiết
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng upload file CSV để bắt đầu phân tích.")