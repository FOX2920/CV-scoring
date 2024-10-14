# config.py

cleaned_schema = {
    "type": "object",
    "properties": {
        "truc_nang_luc": {
            "type": "integer",
            "description": "Đánh giá mức độ theo Trục Năng lực trong JD theo điểm từ khoảng từ 0 đến 40.",
        },
        "truc_van_hoa": {
            "type": "integer",
            "description": "Đánh giá mức độ theo Trục Phù hợp Văn hóa trong JD theo điểm từ khoảng từ 0 đến 30.",
        },
        "truc_tuong_lai": {
            "type": "integer",
            "description": "Đánh giá mức độ theo Trục Tương lai của Ứng viên trong JD theo điểm từ khoảng từ 0 đến 20.",
        },
        "tieu_chi_khac": {
            "type": "integer",
            "description": "Đánh giá mức độ theo Tiêu chuẩn gợi ý khác của Ứng viên trong JD theo điểm từ khoảng từ 0 đến 10.",
        },
        "diem_cong": {
            "type": "integer",
            "description": "Đánh giá mức độ theo mục Điểm cộng của Ứng viên trong JD từ khoảng từ 0 đến 30 (mỗi tiêu chí 5 điểm).",
        },
        "diem_tru": {
            "type": "integer",
            "description": "Đánh giá mức độ theo mục Điểm trừ của Ứng viên trong JD từ khoảng từ 0 đến 40 (mỗi tiêu chí 5 điểm).",
        },
        "tom_tat": {
            "type": "string",
            "description": "Tóm tắt điểm mạnh và điểm yếu chính của ứng viên dựa trên CV với công việc trong JD trong 2 hoặc 3 câu."
        }
    },
    "required": ["truc_nang_luc", "truc_van_hoa", "truc_tuong_lai", "tieu_chi_khac", "diem_cong", "diem_tru", "tom_tat"]
}

new_schema = {
    "type": "object",
    "properties": {
        "muc_do_phu_hop": {
            "type": "integer",
            "description": "Đánh giá mức độ phù hợp của kinh nghiệm và trình độ của ứng viên với trách nhiệm công việc trong khoảng từ 0 đến 10.",
        },
        "ky_nang_ky_thuat": {
            "type": "integer",
            "description": "Đánh giá khả năng thành thạo của ứng viên đối với các kỹ năng kỹ thuật cần thiết trong công việc trong khoảng từ 0 đến 10.",
        },
        "kinh_nghiem": {
            "type": "integer",
            "description": "Đánh giá kinh nghiệm làm việc của ứng viên, bao gồm số năm và mức độ phù hợp với vai trò trong khoảng từ 0 đến 10.",
        },
        "trinh_do_hoc_van": {
            "type": "integer",
            "description": "Đánh giá học vấn của ứng viên, xem xét mức độ đáp ứng yêu cầu của công việc trong khoảng từ 0 đến 10.",
        },
        "ky_nang_mem": {
            "type": "integer",
            "description": "Đánh giá các kỹ năng mềm của ứng viên, bao gồm giao tiếp, làm việc nhóm và kỹ năng lãnh đạo trong khoảng từ 0 đến 10.",
        },
        "diem_tong_quat": {
            "type": "number",
            "description": "Trung bình của các điểm đánh giá ở 5 tiêu chí trên.",
        },
        "tom_tat": {
            "type": "string",
            "description": "Tóm tắt điểm mạnh và điểm yếu chính của ứng viên dựa trên CV trong 2 hoặc 3 câu."
        }
    },
    "required": ["muc_do_phu_hop", "ky_nang_ky_thuat", "kinh_nghiem", "trinh_do_hoc_van", "ky_nang_mem", "diem_tong_quat", "tom_tat"]
}
