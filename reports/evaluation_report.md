# Evaluation Report

## Cost Assumptions
- **False Positive Cost:** $5.00 (Manual review + customer friction)
- **False Negative Cost:** $135.10 (Average chargeback for undetected fraud)

## Threshold Selection
By simulating the expected cost at different thresholds, we recommend a threshold of **0.78**. 
At this threshold, the model minimizes the total financial loss for the merchant.

## Business Impact
On this test set:
- **Flagging Nothing** (naive baseline) costs **$664,972.49**
- **Flagging Everything** costs **$5,285,700.00**
- **Our Model** (at optimal threshold) costs **$173,156.38**

**Total Savings vs Flagging Nothing:** **$491,816.11**

## Model Performance
At the recommended threshold of 0.78:
- **Precision:** 37.47% (When the model flags a transaction, it is fraud this often)
- **Recall:** 78.83% (The model catches this percentage of all actual fraud)

### Confusion Matrix
- True Negatives (Correctly ignored): 1,050,664
- False Positives (Unnecessary reviews): 6,476
- False Negatives (Missed fraud): 1,042
- True Positives (Caught fraud): 3,880

*(See figures/ directory for PR curve and cost analysis charts).*
