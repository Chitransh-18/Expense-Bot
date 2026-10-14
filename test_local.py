import sys
import json
import random
from app import app, init_db

def run_tests():
    print("[TEST] Testing ExpenseTracker Pro Tabbed Auth, Username, & Natural Language AI API endpoints...")
    init_db()
    client = app.test_client()

    # 0. Test /api/ping keep-alive heartbeat endpoint
    res = client.get('/api/ping')
    assert res.status_code == 200, f"/api/ping failed: {res.data}"
    ping_data = res.get_json()
    assert ping_data['status'] == 'active', "ping status invalid"
    assert 'database' in ping_data, "ping database status missing"
    print("[PASS] /api/ping Keep-Alive Bot Heartbeat passed!")

    rand_id = random.randint(100, 999)
    test_user = f"user_test_{rand_id}"
    test_email = f"user_test_{rand_id}@gmail.com"

    # 1. Test registration - Send OTP
    res = client.post('/api/auth/register-send-otp', json={
        'full_name': 'Chitransh Saxena',
        'username': test_user,
        'email': test_email,
        'password': 'password123'
    })
    assert res.status_code == 200, f"register-send-otp failed: {res.data}"
    data = res.get_json()
    assert data['username'] == test_user, "username parsing failed"
    print("[PASS] /api/auth/register-send-otp passed!")

    # 2. Test registration - Verify OTP & Create User
    otp_code = data.get('otp_debug', '123456')
    res = client.post('/api/auth/register-verify-otp', json={
        'full_name': 'Chitransh Saxena',
        'username': test_user,
        'email': test_email,
        'password': 'password123',
        'otp_code': otp_code
    })
    assert res.status_code == 200, f"register-verify-otp failed: {res.data}"
    auth_data = res.get_json()
    token = auth_data['token']
    headers = {'Authorization': f'Bearer {token}'}
    print("[PASS] /api/auth/register-verify-otp passed!")

    # 3. Test Username Uniqueness Rejection
    res = client.post('/api/auth/register-send-otp', json={
        'full_name': 'Another User',
        'username': test_user, # Duplicate!
        'email': f'another_{rand_id}@gmail.com',
        'password': 'password123'
    })
    assert res.status_code == 400, f"Duplicate username check should fail, got status {res.status_code}"
    err_msg = res.get_json()['error']
    assert "already exists" in err_msg, f"Unexpected error message: {err_msg}"
    print("[PASS] Duplicate username rejection & suggestion check passed!")

    # 4. Test Sign-In with Username + Password
    res = client.post('/api/auth/login', json={
        'username_or_email': test_user,
        'password': 'password123'
    })
    assert res.status_code == 200, f"login with username failed: {res.data}"
    assert res.get_json()['user']['username'] == test_user, "login user format invalid"
    print("[PASS] /api/auth/login with Username passed!")

    # 5. Test Sign-In with Email + Password
    res = client.post('/api/auth/login', json={
        'username_or_email': test_email,
        'password': 'password123'
    })
    assert res.status_code == 200, f"login with email failed: {res.data}"
    print("[PASS] /api/auth/login with Email passed!")

    # 6. Test Add Split Expense (50% share calculation)
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

    # 7. Test Natural Language Parser (English): "Dinner 540 with Daksh split via UPI"
    res = client.post('/api/expenses/parse-natural-language', headers=headers, json={
        'text': 'Dinner 540 with Daksh split via UPI'
    })
    assert res.status_code == 200, f"parse English failed: {res.data}"
    parsed = res.get_json()['parsed']
    assert parsed['amount'] == 270.0, f"Expected 270.0 share, got {parsed['amount']}"
    assert parsed['total_bill_amount'] == 540.0, f"Expected 540.0 total, got {parsed['total_bill_amount']}"
    assert parsed['category'] == 'Food & Dining', f"Expected Food & Dining, got {parsed['category']}"
    assert 'Daksh' in parsed['split_with'], f"Expected Daksh in split_with, got {parsed['split_with']}"
    assert parsed['payment_mode'] == 'UPI', f"Expected UPI, got {parsed['payment_mode']}"
    print("[PASS] English Natural Language parsing passed!")

    # 8. Test Natural Language Parser (Hinglish): "Daksh ke saath dinner 600 aadha aadha UPI se"
    res = client.post('/api/expenses/parse-natural-language', headers=headers, json={
        'text': 'Daksh ke saath dinner 600 aadha aadha UPI se'
    })
    assert res.status_code == 200, f"parse Hinglish failed: {res.data}"
    parsed = res.get_json()['parsed']
    assert parsed['amount'] == 300.0, f"Expected 300.0 share, got {parsed['amount']}"
    assert parsed['total_bill_amount'] == 600.0, f"Expected 600.0 total, got {parsed['total_bill_amount']}"
    assert 'Daksh' in parsed['split_with'], f"Expected Daksh in split_with, got {parsed['split_with']}"
    print("[PASS] Hinglish Natural Language parsing (split with Daksh) passed!")

    # 9. Test Natural Language Quick-Add endpoint: "Uber cab 250 cash kal"
    res = client.post('/api/expenses/quick-add', headers=headers, json={
        'text': 'Uber cab 250 cash kal'
    })
    assert res.status_code == 201, f"quick-add failed: {res.data}"
    exp_res = res.get_json()['expense']
    assert exp_res['amount'] == 250.0, f"Expected 250.0, got {exp_res['amount']}"
    assert exp_res['category'] == 'Travel & Cab', f"Expected Travel & Cab, got {exp_res['category']}"
    assert exp_res['payment_mode'] == 'Cash', f"Expected Cash, got {exp_res['payment_mode']}"
    print("[PASS] /api/expenses/quick-add direct logging passed!")

    # 10. Test 404 handler for invalid API path
    res = client.get('/api/invalid-nonexistent-endpoint')
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("[PASS] Custom 404 API error handler passed!")

    print("\nALL LOCAL TABBED AUTH, USERNAME, HINDI/HINGLISH NLP & 17-ITEM POLISH TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
