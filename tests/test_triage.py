import pytest
import numpy as np
import pandas as pd

def classify_triage(prob, thresh_challenge=0.30, thresh_decline=0.78):
    if prob < thresh_challenge:
        return "APPROVE"
    elif prob < thresh_decline:
        return "CHALLENGE"
    else:
        return "DECLINE"

def test_triage_boundary_conditions():
    assert classify_triage(0.10) == "APPROVE"
    assert classify_triage(0.299) == "APPROVE"
    assert classify_triage(0.30) == "CHALLENGE"
    assert classify_triage(0.55) == "CHALLENGE"
    assert classify_triage(0.779) == "CHALLENGE"
    assert classify_triage(0.78) == "DECLINE"
    assert classify_triage(0.99) == "DECLINE"

def test_triage_partition_consistency():
    np.random.seed(42)
    probs = np.random.uniform(0.0, 1.0, 1000)
    
    actions = [classify_triage(p) for p in probs]
    n_approve = actions.count("APPROVE")
    n_challenge = actions.count("CHALLENGE")
    n_decline = actions.count("DECLINE")
    
    assert n_approve + n_challenge + n_decline == 1000
    assert n_approve > 0 and n_challenge > 0 and n_decline > 0

def test_triage_revenue_recovery():
    y_test = np.array([0, 0, 1, 1, 0, 1])
    probs = np.array([0.1, 0.4, 0.5, 0.85, 0.2, 0.9])
    amounts = np.array([50.0, 100.0, 200.0, 300.0, 40.0, 500.0])
    
    # 0.30 <= prob < 0.78
    is_challenge = (probs >= 0.30) & (probs < 0.78)
    is_decline = probs >= 0.78
    
    # In challenge: indices 1 (clean, $100), 2 (fraud, $200)
    fraud_challenged_val = amounts[(y_test == 1) & is_challenge].sum()
    assert fraud_challenged_val == 200.0
    
    # In decline: indices 3 (fraud, $300), 5 (fraud, $500)
    fraud_declined_val = amounts[(y_test == 1) & is_decline].sum()
    assert fraud_declined_val == 800.0
    
    total_protected = fraud_challenged_val + fraud_declined_val
    assert total_protected == 1000.0
