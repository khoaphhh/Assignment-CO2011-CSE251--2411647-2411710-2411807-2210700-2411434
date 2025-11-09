# Tạo và kích hoạt môi trường ảo
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate

# Tải thư viện cần thiết 
    Tải: pip install -r requirements.txt
    cập nhật thư viện: pip install --upgrade -r requirements.txt

# Test thử
    python -m src.main --task parse --input examples/simple_net.pnml
    python -m src.main --task parse --input examples/deadlock_example.pnml
