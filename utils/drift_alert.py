import os, requests
from sklearn.metrics import roc_auc_score
from scipy.stats import ks_2samp
def drift_metrics(y_true,p_old,p_new):
    auc_old = roc_auc_score(y_true,p_old); auc_new = roc_auc_score(y_true,p_new)
    ks = ks_2samp(p_old,p_new).statistic
    return auc_old,auc_new,ks
def send_slack(text):
    hook = os.getenv("PPEDGE_WEBHOOK") or os.getenv("SLACK_WEBHOOK")
    if hook: requests.post(hook,json=dict(text=text),timeout=10)
def alert_if_drift(y,p_old,p_new,drop=0.03,ks_thr=0.05):
    auc_o,auc_n,ks = drift_metrics(y,p_old,p_new)
    if (auc_o-auc_n)>drop or ks>ks_thr:
        send_slack(f":rotating_light: Drift detected AUC Δ={(auc_o-auc_n):.3f}, KS={ks:.3f}")
