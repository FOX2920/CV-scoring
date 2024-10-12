cleaned_schema = {
    "type": "object",
    "properties": {
        "truc_nang_luc": {
            "type": "integer",
            "description": "Đánh giá mức độ theo  Trục Năng lực trong JD theo điểm từ khoảng từ 0 đến 40.",
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
            "description": "Đánh giá mức độ theo mục Điểm cộng của Ứng viên trong JD .",
        },
        "diem_tru": {
            "type": "integer",
            "description": "Đánh giá mức độ theo mục Điểm trừ của Ứng viên trong JD .",
        },
        "tom_tat": {
            "type": "string",
            "description": "Tóm tắt điểm mạnh và điểm yếu chính của ứng viên dựa trên CV với công việc trong JD trong 2 hoặc 3 câu."
        }
    },
    "required": ["truc_nang_luc", "truc_van_hoa", "truc_tuong_lai", "tieu_chi_khac", "tom_tat"]
}
