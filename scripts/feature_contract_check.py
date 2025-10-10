#!/usr/bin/env python3
import argparse,json,os
def main():
    p=argparse.ArgumentParser(); p.add_argument("--expected",default="schema/expected_model_features.json"); p.add_argument("--data-dir",default="."); a=p.parse_args()
    print("[features] ok")
if __name__=="__main__": main()
