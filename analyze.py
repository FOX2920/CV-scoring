import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    return df

def plot_score_distribution(df, column):
    fig = px.histogram(df, x=column, nbins=20, marginal="box", 
                       title=f"Phân phối {column}",
                       labels={column: "Điểm", "count": "Số lượng ứng viên"})
    fig.update_layout(showlegend=False)
    return fig

def plot_correlation_heatmap(df):
    corr_columns = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 
                    'Tiêu chí khác', 'Điểm tổng quát']
    corr = df[corr_columns].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", 
                    title="Ma trận tương quan giữa các tiêu chí")
    return fig

def plot_candidate_radar(df, candidate_name):
    categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác']
    candidate_data = df[df['Tên ứng viên'] == candidate_name][categories].values[0]
    max_values = [40, 30, 20, 10]  # Maximum values for each axis
    
    fig = go.Figure(data=go.Scatterpolar(
        r=candidate_data,
        theta=categories,
        fill='toself',
        marker=dict(color='blue'),
        line=dict(color='blue')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(max_values)]),
            angularaxis=dict(tickfont=dict(size=12, color='red'))
        ),
        title=dict(text=f"Biểu đồ đánh giá của {candidate_name}", font=dict(size=16, color='white')),
        font=dict(size=14, color='black'),
        showlegend=False
    )
    
    return fig

def dashboard():
    st.header("📈 Dashboard Phân tích")

    uploaded_file = st.file_uploader("Chọn file CSV chứa dữ liệu ứng viên", type="csv")

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        st.header("📊 Thông tin tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số ứng viên", len(df))
        col2.metric("Điểm trung bình", f"{df['Điểm tổng quát'].mean():.2f}")
        col3.metric("Điểm cao nhất", df['Điểm tổng quát'].max())
        col4.metric("Điểm thấp nhất", df['Điểm tổng quát'].min())
        
        st.header("📈 Phân tích điểm số")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_score_distribution(df, 'Điểm tổng quát'), use_container_width=True)
        with col2:
            st.plotly_chart(plot_correlation_heatmap(df), use_container_width=True)
        
        st.header("🔍 So sánh các trục đánh giá")
        axes = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác']
        fig = go.Figure()
        for axis in axes:
            fig.add_trace(go.Box(y=df[axis], name=axis))
        fig.update_layout(title="So sánh phân phối các trục đánh giá", yaxis_title="Điểm")
        st.plotly_chart(fig, use_container_width=True)
        
        st.header("🎯 Biểu đồ đánh giá ứng viên")
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_summary = df[df['Tên ứng viên'] == selected_candidate]['Tóm tắt'].values[0]
            st.subheader("Tóm tắt ứng viên")
            st.write(candidate_summary)
        with col2:
            st.plotly_chart(plot_candidate_radar(df, selected_candidate), use_container_width=True)
        
        st.header("🏆 Top ứng viên")
        top_candidates = df.sort_values('Điểm tổng quát', ascending=False).head(5)
        st.table(top_candidates[['Tên ứng viên', 'Điểm tổng quát', 'Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác']])
        
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng upload file CSV để bắt đầu phân tích.")
