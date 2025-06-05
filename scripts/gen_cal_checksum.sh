#!/usr/bin/env bash
set -euo pipefail
sha256sum  model_assets/calibration_params_v2.yaml \
  > model_assets/calibration_params_v2.sha256
echo "✓  checksum written to model_assets/calibration_params_v2.sha256"
