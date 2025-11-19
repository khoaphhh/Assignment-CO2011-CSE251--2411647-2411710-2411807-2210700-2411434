import time
import sys
from pyeda.inter import bddvar, One, Zero
from pnml_parser import PetriNet

class SymbolicReachabilityPyEDA(PetriNet):
    def __init__(self):
        super().__init__()
        self.place_to_curr_var = {}  # p -> x
        self.place_to_next_var = {}  # p -> x'

    def setup_variables(self):
        """
        Tạo biến BDD trong PyEDA.
        """
        sorted_places = sorted(self.places.keys())
        for i, p in enumerate(sorted_places):
            # Tạo biến x (hiện tại) và x' (tiếp theo)
            # Trong PyEDA, bddvar tạo biến BDD
            self.place_to_curr_var[p] = bddvar(f'x_{p}')
            self.place_to_next_var[p] = bddvar(f'x_{p}_prime')

    def encode_initial_marking(self):
        """
        Mã hóa trạng thái ban đầu: M0(x)
        """
        expr = One # True
        for p, info in self.places.items():
            curr_var = self.place_to_curr_var[p]
            if info['initial'] > 0:
                expr &= curr_var       # AND x
            else:
                expr &= ~curr_var      # AND NOT x
        return expr

    def encode_transition_relation(self):
        """
        Tạo quan hệ chuyển đổi R(x, x') dùng PyEDA.
        """
        full_relation = Zero # False
        all_places = set(self.places.keys())

        for t_id in self.transitions:
            # 1. Xác định Pre và Post sets
            pre_places = {src for src, tgt in self.arcs if tgt == t_id}
            post_places = {tgt for src, tgt in self.arcs if src == t_id}

            # 2. Xây dựng công thức R_t
            trans_rel = One
            
            # Điều kiện đầu vào (Input): x_p = 1
            for p in pre_places:                            # x_pre luôn là 1
                trans_rel &= self.place_to_curr_var[p]

            # Điều kiện đầu ra (Output): x'_p = 1 (nếu trong Post), x'_p = 0 (nếu chỉ trong Pre)
            changed_places = pre_places | post_places
            
            for p in post_places:                           # post luôn là 1
                trans_rel &= self.place_to_next_var[p]
            
            for p in pre_places - post_places:              #những thằng pre nhưng khồn phải là post ->mất token -> 0
                trans_rel &= ~self.place_to_next_var[p]

            # Frame Condition: Các place không đổi giữ nguyên giá trị (x <-> x')
            unchanged_places = all_places - changed_places          
            for p in unchanged_places:
                x = self.place_to_curr_var[p]
                x_next = self.place_to_next_var[p]
                # (x & x') | (~x & ~x') tương đương (x XNOR x')
                trans_rel &= (x & x_next) | (~x & ~x_next)

            full_relation |= trans_rel

        # Thêm Identity Relation (cho trường hợp không bắn transition nào)
        identity = One
        for p in all_places:
            x = self.place_to_curr_var[p]
            x_next = self.place_to_next_var[p]
            identity &= (x & x_next) | (~x & ~x_next)
            
        return full_relation | identity

    def compute_reachable(self):
        print("   [PyEDA] Đang khởi tạo biến...")
        self.setup_variables()
        
        print("   [PyEDA] Mã hóa Initial Marking...")
        current_set = self.encode_initial_marking()
        
        print("   [PyEDA] Mã hóa Transition Relation...")
        trans_relation = self.encode_transition_relation()

        # Tạo map đổi tên biến cho bước chuyển (x' -> x)
        # PyEDA dùng dictionary {biến_cũ: biến_mới} cho hàm compose
        rename_map = {self.place_to_next_var[p]: self.place_to_curr_var[p] for p in self.places}
        
        # Tập hợp các biến hiện tại để khử (Quantify Existential)
        current_vars = set(self.place_to_curr_var.values())

        print("   [PyEDA] Bắt đầu Symbolic BFS...")
        start_time = time.time()
        
        while True:
            # 1. Image Computation: Next = Exist x . (Current & Relation)
            # Trong PyEDA, 'smoothing' chính là Existential Quantification
            step1 = current_set & trans_relation
            next_states_prime = step1.smoothing(current_vars)
            
            # 2. Đổi tên x' -> x
            # Dùng hàm compose để thay thế biến
            next_states = next_states_prime.compose(rename_map)
            
            # 3. Hợp nhất
            new_set = current_set | next_states
            
            # 4. Kiểm tra hội tụ
            # PyEDA hỗ trợ so sánh trực tiếp bằng equivalent
            if new_set.equivalent(current_set):
                break
            current_set = new_set

        end_time = time.time()
        
        # Đếm số nghiệm (satisfying assignments)
        # Lưu ý: PyEDA count trả về float, cần cast về int
        count = int(current_set.satisfy_count())
        
        return count, (end_time - start_time)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python src/reachability_symbolic_pyeda.py <file.pnml>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    net = SymbolicReachabilityPyEDA()
    
    if net.parse_pnml(file_path):
        count, duration = net.compute_reachable()
        print(f"✅ Task 3 (PyEDA) Hoàn thành.")
        print(f"   Tổng số trạng thái: {count}")
        print(f"   Thời gian: {duration:.4f}s")
    else:
        sys.exit(1)