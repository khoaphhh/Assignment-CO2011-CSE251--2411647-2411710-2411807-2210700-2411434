from pnml_parser import PetriNet

class ReachabilityNet(PetriNet):
    def __init__(self):
        super().__init__()
        self.pre = {}   # {transition: {place: weight}}
        self.post = {}  # {transition: {place: weight}}

    def build_pre_post(self):
        for t in self.transitions:
            self.pre[t] = {}
            self.post[t] = {}

        for src, tgt in self.arcs:
            if src in self.places and tgt in self.transitions:
                self.pre[tgt][src] = 1
            elif src in self.transitions and tgt in self.places:
                self.post[src][tgt] = 1

    def get_initial_marking(self):
        return {p: self.places[p]["initial"] for p in self.places}

    def enabled(self, marking, t):
        for p, w in self.pre[t].items():
            if marking[p] < w:
                return False
        return True

    def fire(self, marking, t):
        new_m = marking.copy()
        for p, w in self.pre[t].items():
            new_m[p] -= w
        for p, w in self.post[t].items():
            new_m[p] += w
        return new_m

    def bfs(self):
        from collections import deque

        init = self.get_initial_marking()
        queue = deque([init])

        seen = set()
        def encode(m): return tuple(m[p] for p in sorted(self.places))

        seen.add(encode(init))
        reachable = [init]

        while queue:
            m = queue.popleft()

            for t in self.transitions:
                if self.enabled(m, t):
                    new_m = self.fire(m, t)
                    sig = encode(new_m)
                    if sig not in seen:
                        seen.add(sig)
                        reachable.append(new_m)
                        queue.append(new_m)

        return reachable


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        exit(1)

    net = ReachabilityNet()
    net.parse_pnml(sys.argv[1])
    net.build_pre_post()

    reachable = net.bfs()
    print(f"Reachable markings ({len(reachable)}):")
    for m in reachable:
        print(m)
