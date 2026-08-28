import sys
import json
from app import app, init_db

def run_tests():
    print("[TEST] Testing ExpenseTracker Pro API endpoints locally...")
    init_db()
    client = app.test_client()

    # 1. Test check-user endpoint (New User)
    res = client.post('/api/auth/check-user', json={'email': 'testuser_local@gmail.com'})
    assert res.status_code == 200, f"check-user failed: {res.data}"
    data = res.get_json()
    assert data['exists'] == False or data['exists'] == True, "check-user response format invalid"
    print("[PASS] /api/auth/check-user passed!")

    # 2. Test send-otp endpoint
    res = client.post('/api/auth/send-otp', json={'email': 'testuser_local@gmail.com'})
    assert res.status_code == 200, f"send-otp failed: {res.data}"
    data = res.get_json()
    assert 'email' in data, "send-otp response format invalid"
    print("[PASS] /api/auth/send-otp passed!")

    # 3. Test verify-otp-set-password endpoint
    otp_code = data.get('otp_debug', '123456')
    res = client.post('/api/auth/verify-otp-set-password', json={
        'email': 'testuser_local@gmail.com',
        'otp_code': otp_code,
        'password': 'testpassword123',
        'full_name': 'Test User Local'
    })
    assert res.status_code == 200, f"verify-otp-set-password failed: {res.data}"
    auth_data = res.get_json()
    token = auth_data['token']
    headers = {'Authorization': f'Bearer {token}'}
    print("[PASS] /api/auth/verify-otp-set-password passed!")

    # 4. Test login-password endpoint
    res = client.post('/api/auth/login-password', json={
        'email': 'testuser_local@gmail.com',
        'password': 'testpassword123'
    })
    assert res.status_code == 200, f"login-password failed: {res.data}"
    print("[PASS] /api/auth/login-password passed!")

    # 5. Test add split expense (₹450 split equally -> ₹225 share)
    res = client.post('/api/expenses', headers=headers, json={
        'expense_type': 'Split',
        'category': 'Food & Dining',
        'amount': 450.0,
        'payment_mode': 'UPI',
        'date': '2026-08-28',
        'split_with': 'Friend',
        'description': 'Dinner split test'
    })
    assert res.status_code == 201, f"add-expense failed: {res.data}"
    exp_data = res.get_json()['expense']
    assert exp_data['amount'] == 225.0, f"Expected share 225.0, got {exp_data['amount']}"
    assert exp_data['total_bill_amount'] == 450.0, f"Expected total 450.0, got {exp_data['total_bill_amount']}"
    print("[PASS] /api/expenses Split calculation (50% share = 225) passed!")

    # 6. Test fetch expenses
    res = client.get('/api/expenses', headers=headers)
    assert res.status_code == 200, f"get-expenses failed: {res.data}"
    expenses = res.get_json()['expenses']
    assert len(expenses) >= 1, "Expenses list empty"
    print("[PASS] /api/expenses list fetch passed!")

    print("\nALL LOCAL API & DATABASE INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
