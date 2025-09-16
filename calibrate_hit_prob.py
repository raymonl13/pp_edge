def main(argv: Optional[list[str]] = None) -> int:
    # IMPORTANT: never parse pytest's argv by default
    args = _build_arg_parser().parse_args(argv or [])
    # Example prod flow (reserved for future calibration)
    # mdl = load_model(args.model_path)
    # df = pd.read_csv(args.input_path) if args.input_path else pd.DataFrame()
    # ... write args.output_path ...
    return calibrate(args.input_path, args.output_path)

