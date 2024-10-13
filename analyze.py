import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_candidate_radar(df, candidate_name):
    categories = ['Trục Năng lực','Trục Phù hợp Văn hóa','Trục Tương lai','Tiêu chí khác','Điểm cộng','Điểm trừ']
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
        
        st.header("💰 Phân tích Mức lương mong muốn")
        col1, col2 = st.columns(2)
        df['Điểm tổng'] = df['Điểm tổng quát'].clip(lower=0)
        with col1:
            fig_salary_position = px.box(df, x='Vị trí', y='Mức lương mong muốn', 
                                         title="Mức lương mong muốn theo Vị trí",
                                         labels={"Mức lương mong muốn": "Mức lương", "Vị trí": "Vị trí"})
            st.plotly_chart(fig_salary_position, use_container_width=True)
        with col2:
            fig_salary_score = px.scatter(df, x="Mức lương mong muốn", y="Điểm tổng quát", 
                                             hover_data=["Tên ứng viên", "Vị trí"],
                                            color="Vị trí", size=df["Điểm tổng quát"].abs(),
                                             title="Mối quan hệ giữa Điểm tổng quát và Mức lương mong muốn")
            st.plotly_chart(fig_salary_score, use_container_width=True)
        
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
        
        st.header("🎯 Biểu đồ kỹ năng ứng viên")
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_candidate = st.selectbox("Chọn ứng viên", df['Tên ứng viên'].tolist())
            candidate_data = df[df['Tên ứng viên'] == selected_candidate].iloc[0]
            
            # Create a figure for candidate information
            fig_info = go.Figure(data=[go.Table(
                header=dict(values=['Thông tin', 'Giá trị'],
                            fill_color='paleturquoise',
                            align='left'),
                cells=dict(values=[['Tên', 'Vị trí', 'Điểm tổng quát', 'Mức lương mong muốn'],
                                   [candidate_data['Tên ứng viên'],
                                    candidate_data['Vị trí'],
                                    f"{candidate_data['Điểm tổng quát']:.2f}",
                                    f"{candidate_data['Mức lương mong muốn']:,.0f}"]],
                           fill_color='lavender',
                           align='left'))
            ])
            fig_info.update_layout(title="Thông tin ứng viên", height=200, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_info, use_container_width=True)
    
            candidate_summary = candidate_data['Tóm tắt']
            st.subheader("Tóm tắt ứng viên")
            st.write(candidate_summary)
        with col2:
            st.plotly_chart(plot_candidate_radar(df, selected_candidate), use_container_width=True)

        
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
        
        st.header("🥇 Top ứng viên theo vị trí")
        positions = df['Vị trí'].unique()
        for position in positions:
            st.subheader(f"Top 5 ứng viên cho vị trí: {position}")
            top_candidates_position = df[df['Vị trí'] == position].sort_values('Điểm tổng quát', ascending=False).head(5)
            st.table(top_candidates_position[['Tên ứng viên', 'Điểm tổng quát', 'Trục Năng lực', 'Trục Phù hợp Văn hóa', 'Trục Tương lai', 'Tiêu chí khác', 'Điểm cộng', 'Điểm trừ']])
        
        st.header("📋 Dữ liệu chi tiết")
        st.dataframe(df)

    else:
        st.info("Vui lòng tải lên file CSV đã tải xuống từ tab 'Đánh giá CV' để xem dashboard.")
