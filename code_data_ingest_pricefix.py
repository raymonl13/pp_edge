import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    pricefix_data = []  # TODO: fetch your real PriceFix records here

    with open(args.out, "w") as f:
        json.dump(pricefix_data, f)

if __name__ == "__main__":
    main()
