# Evaluation Report

## Cost Assumptions
- **False Positive Cost:** $5.00 (Manual review + customer friction)
- **False Negative Cost:** $205.84 (Average chargeback for undetected fraud)

## Threshold Selection
By simulating the expected cost at different thresholds, we recommend a threshold of **0.01**. 
At this threshold, the model minimizes the total financial loss for the merchant.

## Business Impact
On this test set:
- **Flagging Nothing** (naive baseline) costs **$113,004.51**
- **Flagging Everything** costs **$2,050.00**
- **Our Model** (at optimal threshold) costs **$4,661.72**

**Total Savings vs Flagging Nothing:** **$108,342.79**

## Model Performance
At the recommended threshold of 0.01:
- **Precision:** 60.04% (When the model flags a transaction, it is fraud this often)
- **Recall:** 97.45% (The model catches this percentage of all actual fraud)

### Confusion Matrix
- True Negatives (Correctly ignored): 54
- False Positives (Unnecessary reviews): 356
- False Negatives (Missed fraud): 14
- True Positives (Caught fraud): 535

*(See figures/ directory for PR curve and cost analysis charts).*
