import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_recall_curve, confusion_matrix
from src.utils import get_project_root, load_config
import joblib
import json

def main():
    print("Running Evaluation (Module 5)...")
    config = load_config()
    eval_cfg = config['evaluation']
    
    root = get_project_root()
    proc_dir = root / 'data' / 'processed'
    models_dir = root / 'models'
    reports_dir = root / 'reports'
    figures_dir = reports_dir / 'figures'
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading test data and models...")
    test = pd.read_parquet(proc_dir / 'test.parquet')
    
    with open(models_dir / 'feature_columns.json', 'r') as f:
        features = json.load(f)
        
    X_test = test[features]
    y_test = test[config['model']['target_col']]
    
    clf = joblib.load(models_dir / 'model.pkl')
    lr = joblib.load(models_dir / 'baseline_lr.pkl')
    
    # Predict probabilities
    y_pred_lgb = clf.predict_proba(X_test)[:, 1]
    y_pred_lr = lr.predict_proba(X_test)[:, 1]
    
    # Cost definitions
    cost_fp = eval_cfg['cost_false_positive']
    fraud_txs = test[y_test == 1]
    cost_fn = fraud_txs['TX_AMOUNT'].mean() if not fraud_txs.empty else 150.0
    
    print(f"Cost Assumptions: FP=${cost_fp:.2f}, FN=${cost_fn:.2f}")
    
    # PR Curve
    prec_lgb, rec_lgb, thresholds_lgb = precision_recall_curve(y_test, y_pred_lgb)
    prec_lr, rec_lr, _ = precision_recall_curve(y_test, y_pred_lr)
    baseline_pr = y_test.mean()
    
    plt.figure(figsize=(8,6))
    plt.plot(rec_lgb, prec_lgb, label='LightGBM')
    plt.plot(rec_lr, prec_lr, label='Logistic Regression')
    plt.axhline(baseline_pr, color='r', linestyle='--', label=f'No-skill ({baseline_pr*100:.2f}%)')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(figures_dir / 'pr_curve.png')
    plt.close()
    
    # Cost minimization to find optimal threshold for LightGBM
    best_threshold = 0.5
    min_cost = float('inf')
    best_cm = None
    
    costs = []
    thresholds = np.linspace(0.01, 0.99, 99)
    for t in thresholds:
        preds = (y_pred_lgb >= t).astype(int)
        cm = confusion_matrix(y_test, preds)
        
        # In case cm is 1x1
        if cm.shape == (1,1):
            if y_test.iloc[0] == 0:
                tn, fp, fn, tp = cm[0,0], 0, 0, 0
            else:
                tn, fp, fn, tp = 0, 0, 0, cm[0,0]
        else:
            tn, fp, fn, tp = cm.ravel()
            
        cost = fp * cost_fp + fn * cost_fn
        costs.append(cost)
        
        if cost < min_cost:
            min_cost = cost
            best_threshold = t
            best_cm = (tn, fp, fn, tp)
            
    plt.figure(figsize=(8,6))
    plt.plot(thresholds, costs)
    plt.axvline(best_threshold, color='r', linestyle='--', label=f'Min cost threshold: {best_threshold:.2f}')
    plt.xlabel('Threshold')
    plt.ylabel('Expected Cost ($)')
    plt.title('Expected Cost vs Threshold')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(figures_dir / 'cost_vs_threshold.png')
    plt.close()
    
    # Baseline costs
    cost_flag_nothing = len(fraud_txs) * cost_fn
    cost_flag_everything = (len(test) - len(fraud_txs)) * cost_fp
    
    print(f"Cost Flag Nothing: ${cost_flag_nothing:,.2f}")
    print(f"Cost Flag Everything: ${cost_flag_everything:,.2f}")
    print(f"Min Cost (Our Model): ${min_cost:,.2f} at threshold {best_threshold:.2f}")
    
    tn, fp, fn, tp = best_cm
    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0
    
    # Confusion matrix plot
    cm_matrix = np.array([[tn, fp], [fn, tp]])
    plt.figure(figsize=(6,5))
    sns.heatmap(cm_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Legitimate', 'Fraud'], yticklabels=['Legitimate', 'Fraud'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix at Threshold {best_threshold:.2f}')
    plt.tight_layout()
    plt.savefig(figures_dir / 'confusion_matrix.png')
    plt.close()
    
    # Compute 3-tier triage statistics
    thresh_high = float(best_threshold)
    thresh_low = 0.30 if thresh_high > 0.30 else round(thresh_high * 0.5, 2)
    
    is_approve = y_pred_lgb < thresh_low
    is_challenge = (y_pred_lgb >= thresh_low) & (y_pred_lgb < thresh_high)
    is_decline = y_pred_lgb >= thresh_high
    total_tx = len(y_test)
    
    clean_challenged = int(((y_test == 0) & is_challenge).sum())
    fraud_challenged = int(((y_test == 1) & is_challenge).sum())
    
    amounts = test['TX_AMOUNT'] if 'TX_AMOUNT' in test.columns else pd.Series(128.44, index=test.index)
    recovered_fraud_val = float(amounts[(y_test == 1) & is_challenge].sum())
    caught_decline_val = float(amounts[(y_test == 1) & is_decline].sum())
    total_protected_val = recovered_fraud_val + caught_decline_val
    
    triage_metrics = {
        'threshold_challenge': float(thresh_low),
        'threshold_decline': float(thresh_high),
        'approve': {
            'count': int(is_approve.sum()),
            'percentage': round(float(is_approve.sum() / total_tx * 100), 2),
            'clean_count': int(((y_test == 0) & is_approve).sum()),
            'fraud_missed': int(((y_test == 1) & is_approve).sum())
        },
        'challenge': {
            'count': int(is_challenge.sum()),
            'percentage': round(float(is_challenge.sum() / total_tx * 100), 2),
            'clean_verified': clean_challenged,
            'fraud_prevented': fraud_challenged,
            'recovered_fraud_amount': round(recovered_fraud_val, 2)
        },
        'decline': {
            'count': int(is_decline.sum()),
            'percentage': round(float(is_decline.sum() / total_tx * 100), 2),
            'fraud_caught': int(((y_test == 1) & is_decline).sum()),
            'false_positives': int(((y_test == 0) & is_decline).sum())
        },
        'total_protected_amount': round(total_protected_val, 2)
    }

    # Save test metrics
    metrics = {
        'recommended_threshold': float(best_threshold),
        'precision': float(precision),
        'recall': float(recall),
        'cost_flag_nothing': float(cost_flag_nothing),
        'cost_model': float(min_cost),
        'savings': float(cost_flag_nothing - min_cost),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        },
        'triage': triage_metrics
    }
    with open(models_dir / 'metrics_test.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
    # Write report
    report = f"""# Evaluation Report

## Cost Assumptions
- **False Positive Cost:** ${cost_fp:.2f} (Manual review + customer friction)
- **False Negative Cost:** ${cost_fn:.2f} (Average chargeback for undetected fraud)

## Threshold Selection
By simulating the expected cost at different thresholds, we recommend a threshold of **{best_threshold:.2f}**. 
At this threshold, the model minimizes the total financial loss for the merchant.

## Business Impact
On this test set:
- **Flagging Nothing** (naive baseline) costs **${cost_flag_nothing:,.2f}**
- **Flagging Everything** costs **${cost_flag_everything:,.2f}**
- **Our Model** (at optimal threshold) costs **${min_cost:,.2f}**

**Total Savings vs Flagging Nothing:** **${cost_flag_nothing - min_cost:,.2f}**

## Model Performance
At the recommended threshold of {best_threshold:.2f}:
- **Precision:** {precision*100:.2f}% (When the model flags a transaction, it is fraud this often)
- **Recall:** {recall*100:.2f}% (The model catches this percentage of all actual fraud)

### Confusion Matrix
- True Negatives (Correctly ignored): {tn:,}
- False Positives (Unnecessary reviews): {fp:,}
- False Negatives (Missed fraud): {fn:,}
- True Positives (Caught fraud): {tp:,}

*(See figures/ directory for PR curve and cost analysis charts).*
"""
    with open(reports_dir / 'evaluation_report.md', 'w') as f:
        f.write(report)
        
    print("Evaluation complete!")

if __name__ == "__main__":
    main()
