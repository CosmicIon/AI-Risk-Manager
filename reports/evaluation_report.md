# Evaluation Report

## Cost Assumptions
- **False Positive Cost:** $5.00 (Manual review + customer friction)
- **False Negative Cost:** $197.94 (Average chargeback for undetected fraud)

## Threshold Selection
By simulating the expected cost at different thresholds, we recommend a threshold of **0.01**. 
At this threshold, the model minimizes the total financial loss for the merchant.

## Business Impact
On this test set:
- **Flagging Nothing** (naive baseline) costs **$107,282.53**
- **Flagging Everything** costs **$2,220.00**
- **Our Model** (at optimal threshold) costs **$4,989.07**

**Total Savings vs Flagging Nothing:** **$102,293.46**

## Model Performance
At the recommended threshold of 0.01:
- **Precision:** 56.61% (When the model flags a transaction, it is fraud this often)
- **Recall:** 97.23% (The model catches this percentage of all actual fraud)

### Confusion Matrix
- True Negatives (Correctly ignored): 40
- False Positives (Unnecessary reviews): 404
- False Negatives (Missed fraud): 15
- True Positives (Caught fraud): 527

*(See figures/ directory for PR curve and cost analysis charts).*
