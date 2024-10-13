import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def dashboard():
    st.header("📈 Dashboard Phân tích Ứng viên")

    uploaded_file = st.file_uploader("Tải lên file CSV đã tải xuống từ tab 'Đánh giá CV'", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Convert 'Mức lương mong muốn' to numeric, removing any non-numeric characters
        df['Mức lương mong muốn'] = pd.to_numeric(df['Mức lương mong muốn'].astype(str).str.replace(r'[^\d.]', ''), errors='coerce')
        
        st.header("📊 Thông tin tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số ứng viên", len(df))
        col2.metric("Điểm tổng quát trung bình", f"{df['Điểm tổng quát'].mean():.2f}")
        col3.metric("Tỷ lệ Pass", f"{(df['Đánh giá'] == 'Pass').mean():.2%}")
        col4.metric("Mức lương trung bình", f"{df['Mức lương mong muốn'].mean():,.0f}")
        
        st.header("📈 Phân tích điểm số")
        col1, col2 = st.columns(2)
        with col1:
            fig_score_distribution = px.histogram(df, x='Điểm tổng quát', nbins=20, 
                                                  title="Phân phối Điểm tổng quát",
                                                  labels={"Điểm tổng quát": "Điểm", "count": "Số lượng ứng viên"})
            fig_score_distribution.add_vline(x=df['Điểm tổng quát'].mean(), line_dash="dash", line_color="red", annotation_text="Điểm trung bình")
            fig_score_distribution.update_layout(showlegend=False)
            st.plotly_chart(fig_score_distribution, use_container_width=True)
        with col2:
            fig_score_boxplot = px.box(df, y='Điểm tổng quát', x='Vị trí', 
                                       title="Phân phối Điểm tổng quát theo Vị trí",
                                       labels={"Điểm tổng quát": "Điểm", "Vị trí": "Vị trí"})
            st.plotly_chart(fig_score_boxplot, use_container_width=True)
        
        st.header("🔍 Phân tích các tiêu chí đánh giá")
        fig_criteria = go.Figure()
        categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
        
        for category in categories:
            fig_criteria.add_trace(go.Box(y=df[category], name=category, boxmean=True))
        
        fig_criteria.update_layout(title="Phân phối điểm các tiêu chí đánh giá", yaxis_title="Điểm")
        st.plotly_chart(fig_criteria, use_container_width=True)
        
        # st.header("💰 Phân tích Mức lương mong muốn")
        # col1, col2 = st.columns(2)
        # with col1:
        #     fig_salary_position = px.box(df, x='Vị trí', y='Mức lương mong muốn', 
        #                                  title="Mức lương mong muốn theo Vị trí",
        #                                  labels={"Mức lương mong muốn": "Mức lương", "Vị trí": "Vị trí"})
        #     st.plotly_chart(fig_salary_position, use_container_width=True)
        # with col2:
        #     fig_salary_score = px.scatter(df, x="Mức lương mong muốn", y="Điểm tổng quát", 
        #                                   hover_data=["Tên ứng viên", "Vị trí"],
        #                                   color="Vị trí", size="Điểm tổng quát",
        #                                   title="Mối quan hệ giữa Điểm tổng quát và Mức lương mong muốn")
        #     st.plotly_chart(fig_salary_score, use_container_width=True)
        
        st.header("🎭 Phân tích Pass/Fail")
        col1, col2 = st.columns(2)
        with col1:
            fig_pass_fail = px.pie(df, names="Đánh giá", title="Tỷ lệ ứng viên Pass/Fail",
                                   color="Đánh giá", color_discrete_map={"Pass": "green", "Fail": "red"})
            st.plotly_chart(fig_pass_fail, use_container_width=True)
        with col2:
            fig_pass_fail_position = px.bar(df, x="Vị trí", color="Đánh giá", 
                                            title="Tỷ lệ Pass/Fail theo Vị trí",
                                            labels={"count": "Số lượng ứng viên", "Vị trí": "Vị trí"},
                                            color_discrete_map={"Pass": "green", "Fail": "red"})
            st.plotly_chart(fig_pass_fail_position, use_container_width=True)
        
        st.header("🎯 So sánh ứng viên")
        selected_candidates = st.multiselect("Chọn ứng viên để so sánh (tối đa 5)", df['Tên ứng viên'].tolist(), max_selections=5)
        if len(selected_candidates) > 1:
            fig_candidate_comparison = go.Figure()
            categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
            
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
