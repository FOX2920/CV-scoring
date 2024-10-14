import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_candidate_radar(df, candidate_name):
    categories = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
    candidate_data = df[df['Tên ứng viên'] == candidate_name][categories].values[0]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=candidate_data,
        theta=categories,
        fill='toself',
        name=candidate_name,
        marker=dict(color='blue'),
        line=dict(color='blue')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 40])
        ),
        title=dict(text=f"Biểu đồ kỹ năng mềm của {candidate_name}", font=dict(size=16, color='white')),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def dashboard():
    st.header("📈 Dashboard Phân tích Ứng viên")
    
    uploaded_file = st.file_uploader("Tải lên file CSV đã tải xuống từ tab 'Đánh giá CV'", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.rename(columns={
                'Điểm tổng quát soft skill' : 'Điểm tổng quát theo tiêu chí', 
                'Điểm tổng quát hard skill':'Điểm tổng quát theo CV', 
                'Trục Năng lực soft skill':'Trục Năng lực', 
                'Trục Phù hợp Văn hóa soft skill':'Trục Phù hợp Văn hóa', 
                'Trục Tương lai soft skill':'Trục Tương lai', 
                'Tiêu chí khác soft skill':'Tiêu chí khác', 
                'Điểm cộng soft skill': 'Điểm cộng', 
                'Điểm trừ soft skill': 'Điểm trừ',
                'Mức độ phù hợp hard skill': 'Mức độ phù hợp', 
                'Kỹ năng kỹ thuật hard skill': 'Kỹ năng kỹ thuật', 
                'Kinh nghiệm hard skill' : 'Kinh nghiệm', 
                'Trình độ học vấn hard skill' : 'Trình độ học vấn', 
                'Kỹ năng mềm hard skill' : 'Kỹ năng mềm',
                'Tóm tắt hard skill': 'Tóm tắt theo CV',
                'Tóm tắt soft skill': 'Tóm tắt theo tiêu chí',
                'Đánh giá soft skill': 'Đánh giá theo tiêu chí'
            }, inplace=True)
        df['Mức lương mong muốn'] = pd.to_numeric(df['Mức lương mong muốn'].astype(str).str.replace(r'[^\d.]', ''), errors='coerce')
        
        st.header("📊 Thông tin tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số ứng viên", len(df))
        col2.metric("Điểm tổng quát theo tiêu chí trung bình", f"{df['Điểm tổng quát theo tiêu chí'].mean():.2f}")
        col3.metric("Điểm tổng quát theo CV trung bình", f"{df['Điểm tổng quát theo CV'].mean():.2f}")
        col4.metric("Mức lương trung bình", f"{df['Mức lương mong muốn'].mean():,.0f}")
        
        st.header("📈 Phân tích điểm số")
        col1, col2 = st.columns(2)
        with col1:
            fig_score_distribution_soft = px.histogram(df, x='Điểm tổng quát theo tiêu chí', nbins=20, 
                                                  title="Phân phối Điểm tổng quát theo tiêu chí",
                                                  labels={"Điểm tổng quát theo tiêu chí": "Điểm", "count": "Số lượng ứng viên"})
            fig_score_distribution_soft.add_vline(x=df['Điểm tổng quát theo tiêu chí'].mean(), line_dash="dash", line_color="red", annotation_text="Điểm trung bình")
            fig_score_distribution_soft.update_layout(showlegend=False)
            st.plotly_chart(fig_score_distribution_soft, use_container_width=True)
        with col2:
            fig_score_distribution_hard = px.histogram(df, x='Điểm tổng quát theo CV', nbins=20, 
                                                  title="Phân phối Điểm tổng quát theo CV",
                                                  labels={"Điểm tổng quát theo CV": "Điểm", "count": "Số lượng ứng viên"})
            fig_score_distribution_hard.add_vline(x=df['Điểm tổng quát theo CV'].mean(), line_dash="dash", line_color="red", annotation_text="Điểm trung bình")
            fig_score_distribution_hard.update_layout(showlegend=False)
            st.plotly_chart(fig_score_distribution_hard, use_container_width=True)
        
        st.header("🔍 Phân tích các tiêu chí Đánh giá theo tiêu chí")
        fig_criteria_soft = go.Figure()
        categories_soft = ['Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']
        
        for category in categories_soft:
            fig_criteria_soft.add_trace(go.Box(y=df[category], name=category, boxmean=True))
        
        fig_criteria_soft.update_layout(title="Phân phối điểm các tiêu chí Đánh giá theo tiêu chí", yaxis_title="Điểm")
        st.plotly_chart(fig_criteria_soft, use_container_width=True)
        
        st.header("🔍 Phân tích các tiêu chí đánh giá hard skill")
        fig_criteria_hard = go.Figure()
        categories_hard = ['Mức độ phù hợp', 'Kỹ năng kỹ thuật', 'Kinh nghiệm', 'Trình độ học vấn', 'Kỹ năng mềm']
        
        for category in categories_hard:
            fig_criteria_hard.add_trace(go.Box(y=df[category], name=category, boxmean=True))
        
        fig_criteria_hard.update_layout(title="Phân phối điểm các tiêu chí đánh giá hard skill", yaxis_title="Điểm")
        st.plotly_chart(fig_criteria_hard, use_container_width=True)
        
        st.header("💰 Phân tích Mức lương mong muốn")
        col1, col2 = st.columns(2)
        with col1:
            fig_salary_position = px.box(df, x='Vị trí', y='Mức lương mong muốn', 
                                         title="Mức lương mong muốn theo Vị trí",
                                         labels={"Mức lương mong muốn": "Mức lương", "Vị trí": "Vị trí"})
            st.plotly_chart(fig_salary_position, use_container_width=True)
        with col2:
            fig_salary_score = px.scatter(df, x="Mức lương mong muốn", y="Điểm tổng quát theo tiêu chí", 
                                             hover_data=["Tên ứng viên", "Vị trí"],
                                            color="Vị trí", size="Điểm tổng quát theo CV",
                                             title="Mối quan hệ giữa Điểm tổng quát và Mức lương mong muốn")
            st.plotly_chart(fig_salary_score, use_container_width=True)
        
        st.header("🎭 Phân tích Đánh giá theo tiêu chí")
        col1, col2 = st.columns(2)
        with col1:
            fig_pass_fail = px.pie(df, names="Đánh giá theo tiêu chí", title="Tỷ lệ ứng viên theo Đánh giá theo tiêu chí",
                                   color="Đánh giá theo tiêu chí", color_discrete_map={"Pass": "green", "Fail": "red"})
            st.plotly_chart(fig_pass_fail, use_container_width=True)
        with col2:
            fig_pass_fail_position = px.bar(df, x="Vị trí", color="Đánh giá theo tiêu chí", 
                                            title="Tỷ lệ Đánh giá theo tiêu chí theo Vị trí",
                                            labels={"count": "Số lượng ứng viên", "Vị trí": "Vị trí"},
                                            color_discrete_map={"Pass": "green", "Fail": "red"})
            st.plotly_chart(fig_pass_fail_position, use_container_width=True)
        
        st.header("🎯 Biểu đồ kỹ năng ứng viên")
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_data = df[df['Tên ứng viên'] == selected_candidate].iloc[0]
            
            fig_info = go.Figure(data=[go.Table(
                header=dict(values=['Thông tin', 'Giá trị'],
                            fill_color='rgba(100, 100, 100, 0.8)',
                            font=dict(color='white'),
                            align='left'),
                cells=dict(values=[['Tên', 'Vị trí', 'Điểm tổng quát theo tiêu chí', 'Điểm tổng quát theo CV', 'Mức lương mong muốn'],
                                   [candidate_data['Tên ứng viên'],
                                    candidate_data['Vị trí'],
                                    f"{candidate_data['Điểm tổng quát theo tiêu chí']:.2f}",
                                    f"{candidate_data['Điểm tổng quát theo CV']:.2f}",
                                    f"{candidate_data['Mức lương mong muốn']:,.0f}"]],
                           fill_color='rgba(50, 50, 50, 0.8)',
                           font=dict(color='lightgray'),
                           align='left'))
            ])
            fig_info.update_layout(
                title=dict(text="Thông tin ứng viên", font=dict(color='white')),
                height=250,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_info, use_container_width=True)
    
            candidate_summary_soft = candidate_data['Tóm tắt theo tiêu chí']
            candidate_summary_hard = candidate_data['Tóm tắt theo CV']
            st.subheader("Tóm tắt ứng viên theo tiêu chí")
            st.write(candidate_summary_soft)
            st.subheader("Tóm tắt ứng viên theo CV")
            st.write(candidate_summary_hard)
        with col2:
            st.plotly_chart(plot_candidate_radar(df, selected_candidate), use_container_width=True)
        
        st.header("🔍 Lọc và Sắp xếp ứng viên")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            min_score_soft = st.number_input("Điểm tổng quát theo tiêu chí tối thiểu", min_value=0, max_value=100, value=0)
        with col2:
            min_score_hard = st.number_input("Điểm tổng quát theo CV tối thiểu", min_value=0, max_value=100, value=0)
        with col3:
            selected_position = st.multiselect("Chọn vị trí", df['Vị trí'].unique())
        with col4:
            sort_by = st.selectbox("Sắp xếp theo", ["Điểm tổng quát theo tiêu chí", "Điểm tổng quát theo CV", "Mức lương mong muốn"])
        
        filtered_df = df[(df['Điểm tổng quát theo tiêu chí'] >= min_score_soft) & (df['Điểm tổng quát theo CV'] >= min_score_hard)]
        if selected_position:
            filtered_df = filtered_df[filtered_df['Vị trí'].isin(selected_position)]
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)
        
        st.dataframe(filtered_df[['Tên ứng viên', 'Điểm tổng quát theo CV', 'Tóm tắt theo CV', 'Mức lương mong muốn', 'Vị trí', 'Điểm tổng quát theo tiêu chí', 'Tóm tắt theo tiêu chí', 'Đánh giá theo tiêu chí']])
        st.header("🥇 Top ứng viên theo vị trí")
        positions = ['Tư vấn', 'Quản lý', 'Nhân viên', 'Thực tập sinh']
        for position in positions:
            st.subheader(f"Top 5 ứng viên cho vị trí: {position}")
            top_candidates_position = df[df['Vị trí'] == position].sort_values('Điểm tổng quát theo tiêu chí', ascending=False).head(5)
            st.table(top_candidates_position[['Tên ứng viên', 'Điểm tổng quát theo tiêu chí', 'Điểm tổng quát theo CV', 'Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']])
        
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng tải lên file CSV đã tải xuống từ tab 'Đánh giá CV' để xem dashboard.")
