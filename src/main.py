import os
from src.pnml_parser import PetriNet

def main():
    base = os.path.dirname(os.path.dirname(__file__))        # thư mục gốc project
    examples = os.path.join(base, "examples")

    for f in os.listdir(examples):
        if f.endswith(".pnml"):
            path = os.path.join(examples, f)
            print(f"\n=== Parsing {f} ===")

            net = PetriNet()
            net.parse_pnml(path)
            net.summary()

if __name__ == "__main__":
    main()