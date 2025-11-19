# Tạo và kích hoạt môi trường ảo
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate

# Tải thư viện cần thiết 
    Tải: pip install -r requirements.txt
    cập nhật thư viện: pip install --upgrade -r requirements.txt

# Test task 1
    python src/pnml_parser.py examples/simple_example.pnml 
    python src/pnml_parser.py examples/deadlock_example.pnml
    python src/pnml_parser.py examples/invalid_example.pnml
# chạy chương trình
    python src/main.py