"""
Task 1: PNML Parser
Đọc file PNML và chuyển thành cấu trúc Petri net nội bộ.
"""

import xmltodict

def ensure_list(x):
    """Đảm bảo phần tử luôn là list"""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

class PetriNet:
    def __init__(self, places, transitions, arcs, initial_marking):
        self.places = places
        self.transitions = transitions
        self.arcs = arcs
        self.initial_marking = initial_marking

    def summary(self):
        print("Places:", self.places)
        print("Transitions:", self.transitions)
        print("Arcs:", self.arcs)
        print("Initial marking:", self.initial_marking)

def load_pnml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = xmltodict.parse(f.read())

    if "pnml" not in data or "net" not in data["pnml"]:
        raise ValueError("Invalid PNML file: missing <pnml> or <net> tag.")

    net_data = data["pnml"]["net"]
    
    # === SỬA ĐỔI QUAN TRỌNG BẮT ĐẦU TỪ ĐÂY ===
    # 1. Lấy thẻ <page> ra trước
    page_data = net_data.get("page")
    if page_data is None:
        # Nếu file không có thẻ <page>, thì mới dùng <net>
        page_data = net_data 
    # ========================================

    # --- Parse places ---
    places = []
    initial_marking = {}
    
    # 2. SỬA: Dùng 'page_data' thay vì 'net'
    for p in ensure_list(page_data.get("place")):
        if "@id" not in p:
            raise ValueError("Invalid <place>: missing id attribute.")
        pid = p["@id"]
        if pid in places:
            raise ValueError(f"Duplicate place ID detected: {pid}")
        places.append(pid)
        
        # initial marking (default 0)
        mark = 0
        # Kiểm tra 'p["initialMarking"]' có None hay không
        if "initialMarking" in p and p["initialMarking"] and "text" in p["initialMarking"]:
            try:
                mark = int(p["initialMarking"]["text"])
            except (ValueError, TypeError):
                 # Bỏ qua nếu 'text' là None hoặc không phải số
                 mark = 0 
        
        # Đề bài yêu cầu 1-safe
        if mark not in [0, 1]:
            print(f"⚠️ Warning: initialMarking for {pid} is {mark}. For 1-safe net, expected 0 or 1.")
            # Bạn có thể quyết định raise lỗi ở đây nếu muốn
            # raise ValueError(f"Invalid initialMarking for {pid}: {mark} (should be 0 or 1 for 1-safe net).")
        
        initial_marking[pid] = mark

    # --- Parse transitions ---
    transitions = []
    # 3. SỬA: Dùng 'page_data' thay vì 'net'
    for t in ensure_list(page_data.get("transition")):
        if "@id" not in t:
            raise ValueError("Invalid <transition>: missing id attribute.")
        tid = t["@id"]
        if tid in transitions:
            raise ValueError(f"Duplicate transition ID detected: {tid}")
        transitions.append(tid)

    # --- Parse arcs ---
    arcs = []
    # 4. SỬA: Dùng 'page_data' thay vì 'net'
    for a in ensure_list(page_data.get("arc")):
        if "@source" not in a or "@target" not in a:
            raise ValueError(f"Invalid <arc>: missing source/target attribute ({a}).")
        src = a["@source"]
        tgt = a["@target"]
        arcs.append((src, tgt))

    # --- Consistency checks (Giữ nguyên) ---
    all_nodes = set(places) | set(transitions)

    # 1️⃣ Missing arcs or nodes
    for src, tgt in arcs:
        if src not in all_nodes or tgt not in all_nodes:
            raise ValueError(f"Inconsistent arc ({src}->{tgt}): node not defined.")

    # 2️⃣ Invalid arc type (must connect place ↔ transition)
    for src, tgt in arcs:
        if (src in places and tgt in places) or (src in transitions and tgt in transitions):
            raise ValueError(f"Invalid arc ({src}->{tgt}): arcs must connect place <-> transition.")

    # 3️⃣ Orphan nodes (optional warning)
    connected_nodes = {src for src, _ in arcs} | {tgt for _, tgt in arcs}
    for node in all_nodes:
        if node not in connected_nodes:
            print(f"⚠️ Warning: Node '{node}' is not connected to any arc.")

    print("✅ PNML loaded successfully.")
    return PetriNet(places, transitions, arcs, initial_marking)

# Giữ nguyên đoạn code main để chạy
if __name__ == "__main__":
    try:
        file_name = "deadlock_example.pnml"
        petri_net = load_pnml(file_name)
        
        print("\n--- TÓM TẮT PETRI NET ---")
        petri_net.summary()

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{file_name}'.")
    except ValueError as e:
        print(f"Lỗi khi xử lý file PNML: {e}")
    except Exception as e:
        print(f"Đã xảy ra lỗi không xác định: {e}")