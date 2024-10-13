import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def dashboard():
    st.header("📈 Dashboard Phân tích")

    uploaded_file = st.file_uploader("Tải lên file CSV đã tải xuống từ tab 'Đánh giá CV'", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        st.header("📊 Thông tin tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số ứng viên", len(df))
        col2.metric("Điểm trung bình", f"{df['Điểm tổng quát'].mean():.2f}")
        col3.metric("Điểm cao nhất", df['Điểm tổng quát'].max())
        col4.metric("Điểm thấp nhất", df['Điểm tổng quát'].min())
        
        st.header("📈 Phân tích điểm số")
        col1, col2 = st.columns(2)
        with col1:
            fig_score_distribution = px.histogram(df, x='Điểm tổng quát', nbins=20, marginal="box", 
                                                  title="Phân phối Điểm tổng quát",
                                                  labels={"Điểm tổng quát": "Điểm", "count": "Số lượng ứng viên"})
            fig_score_distribution.update_layout(showlegend=False)
            st.plotly_chart(fig_score_distribution, use_container_width=True)
        with col2:
            corr_columns = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 
                            'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ', 'Điểm tổng quát']
            corr = df[corr_columns].corr()
            fig_correlation = px.imshow(corr, text_auto=True, aspect="auto", 
                                        title="Ma trận tương quan giữa các tiêu chí")
            st.plotly_chart(fig_correlation, use_container_width=True)
        
        st.header("🔍 So sánh các tiêu chí đánh giá")
        fig_score_comparison = go.Figure()
        categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
        max_values = [40, 30, 20, 10, 30, 40]  # Maximum values for each axis
        
        for category, max_value in zip(categories, max_values):
            fig_score_comparison.add_trace(go.Box(y=df[category], name=category, boxmean=True))
            fig_score_comparison.add_shape(type="line", x0=category, y0=0, x1=category, y1=max_value,
                                           line=dict(color="red", width=2, dash="dash"))
        
        fig_score_comparison.update_layout(title="So sánh phân phối các tiêu chí đánh giá", yaxis_title="Điểm")
        st.plotly_chart(fig_score_comparison, use_container_width=True)
        
        st.header("💰 Điểm tổng quát vs Mức lương mong muốn")
        fig_salary_score = px.scatter(df, x="Mức lương mong muốn", y="Điểm tổng quát", 
                                      hover_data=["Tên ứng viên", "Vị trí"],
                                      color="Vị trí", size="Điểm tổng quát",
                                      title="Mối quan hệ giữa Điểm tổng quát và Mức lương mong muốn")
        st.plotly_chart(fig_salary_score, use_container_width=True)
        
        st.header("🎭 Tỷ lệ Pass/Fail")
        fig_pass_fail = px.pie(df, names="Đánh giá", title="Tỷ lệ ứng viên Pass/Fail",
                               color="Đánh giá", color_discrete_map={"Pass": "green", "Fail": "red"})
        st.plotly_chart(fig_pass_fail, use_container_width=True)
        
        st.header("🎯 Biểu đồ đánh giá ứng viên")
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_info = df[df['Tên ứng viên'] == selected_candidate].iloc[0]
            st.subheader("Thông tin ứng viên")
            st.write(f"Vị trí: {candidate_info['Vị trí']}")
            st.write(f"Email: {candidate_info['Email']}")
            st.write(f"Mức lương mong muốn: {candidate_info['Mức lương mong muốn']}")
            st.write(f"Đánh giá: {candidate_info['Đánh giá']}")
            st.subheader("Tóm tắt ứng viên")
            st.write(candidate_info['Tóm tắt'])
        with col2:
            categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
            max_values = [40, 30, 20, 10, 30, 40]  # Maximum values for each axis
            candidate_data = df[df['Tên ứng viên'] == selected_candidate][categories].values[0]
            
            fig_candidate_radar = go.Figure(data=go.Scatterpolar(
                r=candidate_data,
                theta=categories,
                fill='toself',
                marker=dict(color='blue'),
                line=dict(color='blue')
            ))
            
            fig_candidate_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max(max_values)]),
                    angularaxis=dict(tickfont=dict(size=12, color='red'))
                ),
                title=dict(text=f"Biểu đồ đánh giá của {selected_candidate}", font=dict(size=16)),
                showlegend=False
            )
            
            st.plotly_chart(fig_candidate_radar, use_container_width=True)
        
        st.header("🔄 So sánh ứng viên")
        selected_candidates = st.multiselect("Chọn ứng viên để so sánh", df['Tên ứng viên'].tolist(), max_selections=5)
        if len(selected_candidates) > 1:
            fig_candidate_comparison = go.Figure()
            
            for candidate in selected_candidates:
                candidate_data = df[df['Tên ứng viên'] == candidate][categories].values[0]
                fig_candidate_comparison.add_trace(go.Scatterpolar(
                    r=candidate_data,
                    theta=categories,
                    fill='toself',
                    name=candidate
                ))
            
            fig_candidate_comparison.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 40])),
                title="So sánh ứng viên"
            )
            st.plotly_chart(fig_candidate_comparison, use_container_width=True)
        
        st.header("🔍 Lọc và Sắp xếp ứng viên")
        col1, col2, col3 = st.columns(3)
        with col1:
            min_score = st.number_input("Điểm tổng quát tối thiểu", min_value=0, max_value=100, value=0)
        with col2:
            selected_position = st.multiselect("Chọn vị trí", df['Vị trí'].unique())
        with col3:
            sort_by = st.selectbox("Sắp xếp theo", ["Điểm tổng quát", "Mức lương mong muốn"])
        
        filtered_df = df[df['Điểm tổng quát'] >= min_score]
        if selected_position:
            filtered_df = filtered_df[filtered_df['Vị trí'].isin(selected_position)]
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)
        
        st.dataframe(filtered_df[['Tên ứng viên', 'Vị trí', 'Điểm tổng quát', 'Mức lương mong muốn', 'Đánh giá']])
        
        st.header("🏆 Top ứng viên")
        top_candidates = df.sort_values('Điểm tổng quát', ascending=False).head(5)
        st.table(top_candidates[['Tên ứng viên', 'Vị trí', 'Điểm tổng quát', 'Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']])
        
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng tải lên file CSV đã tải xuống từ tab 'Đánh giá CV' để xem dashboard.")
