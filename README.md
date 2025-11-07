# Create and activate virtual environment
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate

# Install required libraries
    pip install -r requirements.txt

# Test Task 1
    python -m src.main --task parse --input examples/simple_net.pnml
    python -m src.main --task parse --input examples/deadlock_example.pnml