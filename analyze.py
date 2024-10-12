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
                    'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ', 'Điểm tổng quát']
    corr = df[corr_columns].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", 
                    title="Ma trận tương quan giữa các tiêu chí")
    return fig

def plot_candidate_radar(df, candidate_name):
    categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
    max_values = [40, 30, 20, 10, 30, 40]  # Maximum values for each axis
    candidate_data = df[df['Tên ứng viên'] == candidate_name][categories].values[0]
    
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
        title=dict(text=f"Biểu đồ đánh giá của {candidate_name}", font=dict(size=16)),
        showlegend=False
    )
    
    return fig

def plot_score_comparison(df):
    fig = go.Figure()
    categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
    max_values = [40, 30, 20, 10, 30, 40]  # Maximum values for each axis
    
    for category, max_value in zip(categories, max_values):
        fig.add_trace(go.Box(y=df[category], name=category, boxmean=True))
        fig.add_shape(type="line", x0=category, y0=0, x1=category, y1=max_value,
                      line=dict(color="red", width=2, dash="dash"))
    
    fig.update_layout(title="So sánh phân phối các tiêu chí đánh giá", yaxis_title="Điểm")
    return fig

def plot_candidate_comparison(df, selected_candidates):
    categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
    fig = go.Figure()
    
    for candidate in selected_candidates:
        candidate_data = df[df['Tên ứng viên'] == candidate][categories].values[0]
        fig.add_trace(go.Scatterpolar(
            r=candidate_data,
            theta=categories,
            fill='toself',
            name=candidate
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 40])),
        title="So sánh ứng viên"
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
        
        st.header("🔍 So sánh các tiêu chí đánh giá")
        st.plotly_chart(plot_score_comparison(df), use_container_width=True)
        
        st.header("🎯 Biểu đồ đánh giá ứng viên")
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_summary = df[df['Tên ứng viên'] == selected_candidate]['Tóm tắt'].values[0]
            st.subheader("Tóm tắt ứng viên")
            st.write(candidate_summary)
        with col2:
            st.plotly_chart(plot_candidate_radar(df, selected_candidate), use_container_width=True)
        
        st.header("🔄 So sánh ứng viên")
        selected_candidates = st.multiselect("Chọn ứng viên để so sánh", df['Tên ứng viên'].tolist(), max_selections=5)
        if len(selected_candidates) > 1:
            st.plotly_chart(plot_candidate_comparison(df, selected_candidates), use_container_width=True)
        
        st.header("🏆 Top ứng viên")
        top_candidates = df.sort_values('Điểm tổng quát', ascending=False).head(5)
        st.table(top_candidates[['Tên ứng viên', 'Điểm tổng quát', 'Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']])
        
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng upload file CSV để bắt đầu phân tích.")
