import streamlit as st
from datetime import datetime
import time

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="GlobeCorp Bank ATM", page_icon="🏦", layout="centered")

# Custom CSS to make it look a bit more like an ATM screen
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        font-weight: bold;
    }
    .atm-header {
        text-align: center;
        color: #1E3A8A;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. STATE INITIALIZATION (Mock Database)
# ==========================================
def init_state():
    """Initializes the database and UI state in Streamlit's session_state."""
    if 'db' not in st.session_state:
        st.session_state.db = {
            'accounts': {
                '1001234567': {'balance': 500.0, 'transactions': []},
                '1009876543': {'balance': 1000.0, 'transactions': []}
            },
            'cards': {
                '4000123456789010': {'pin': '1234', 'accountId': '1001234567', 'isLocked': False, 'attempts': 0}
            }
        }
    
    # UI Routing States: IDLE, PIN, MENU, BALANCE, TRANSACTION, SUCCESS
    if 'screen' not in st.session_state:
        st.session_state.screen = 'IDLE'
    if 'current_account_id' not in st.session_state:
        st.session_state.current_account_id = None
    if 'temp_card_number' not in st.session_state:
        st.session_state.temp_card_number = '4000123456789010'
    if 'tx_type' not in st.session_state:
        st.session_state.tx_type = None


# ==========================================
# 3. BUSINESS LOGIC (Mock API Services)
# ==========================================
def process_login(card_number, pin):
    """Validates credentials against the mock DB."""
    db = st.session_state.db
    card = db['cards'].get(card_number)
    
    if not card:
        st.error("Invalid Card Number.")
        return False
    if card['isLocked']:
        st.error("This card is locked due to too many failed attempts.")
        return False
    if card['pin'] != pin:
        card['attempts'] += 1
        if card['attempts'] >= 3:
            card['isLocked'] = True
            st.error("Card locked due to 3 failed attempts.")
        else:
            st.error(f"Invalid PIN. Attempts remaining: {3 - card['attempts']}")
        return False
        
    # Success
    card['attempts'] = 0
    st.session_state.current_account_id = card['accountId']
    st.session_state.screen = 'MENU'
    return True

def process_transaction(amount):
    """Handles Withdrawals and Deposits."""
    acc_id = st.session_state.current_account_id
    account = st.session_state.db['accounts'][acc_id]
    tx_type = st.session_state.tx_type
    
    if amount <= 0:
        st.error("Please enter a valid positive amount.")
        return False
        
    if tx_type == 'WITHDRAW':
        if amount > account['balance']:
            st.error("Insufficient funds.")
            return False
        account['balance'] -= amount
    elif tx_type == 'DEPOSIT':
        account['balance'] += amount
        
    # Record transaction
    account['transactions'].insert(0, {
        'type': tx_type, 
        'amount': amount, 
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    st.session_state.screen = 'SUCCESS'
    return True

def logout():
    """Clears the session and returns to IDLE."""
    st.session_state.current_account_id = None
    st.session_state.screen = 'IDLE'
    st.session_state.temp_card_number = '4000123456789010'


# ==========================================
# 4. UI RENDERING (Screen Routing)
# ==========================================
def render_ui():
    st.markdown("<h1 class='atm-header'>🏦 GLOBECORP BANK ATM</h1>", unsafe_allow_html=True)
    st.divider()

    screen = st.session_state.screen

    # --- IDLE SCREEN ---
    if screen == 'IDLE':
        st.subheader("Welcome! Please insert your card.")
        card_num = st.text_input("Card Number", value=st.session_state.temp_card_number)
        if st.button("Insert Card", type="primary"):
            if card_num:
                st.session_state.temp_card_number = card_num
                st.session_state.screen = 'PIN'
                st.rerun()

    # --- PIN SCREEN ---
    elif screen == 'PIN':
        st.subheader("🔒 Enter your PIN")
        pin = st.text_input("PIN", type="password", max_chars=4)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Enter", type="primary"):
                if process_login(st.session_state.temp_card_number, pin):
                    st.rerun()
        with col2:
            if st.button("Cancel"):
                logout()
                st.rerun()

    # --- MAIN MENU SCREEN ---
    elif screen == 'MENU':
        st.subheader("Please select a transaction")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💵 Withdraw Cash"):
                st.session_state.tx_type = 'WITHDRAW'
                st.session_state.screen = 'TRANSACTION'
                st.rerun()
            if st.button("💰 Deposit Cash"):
                st.session_state.tx_type = 'DEPOSIT'
                st.session_state.screen = 'TRANSACTION'
                st.rerun()
        with col2:
            if st.button("📄 Check Balance"):
                st.session_state.screen = 'BALANCE'
                st.rerun()
            if st.button("🛑 Return Card", type="secondary"):
                logout()
                st.rerun()

    # --- BALANCE SCREEN ---
    elif screen == 'BALANCE':
        acc_id = st.session_state.current_account_id
        balance = st.session_state.db['accounts'][acc_id]['balance']
        
        st.subheader("Available Balance")
        st.metric(label="Current Balance", value=f"${balance:,.2f}")
        
        if st.button("Back to Main Menu"):
            st.session_state.screen = 'MENU'
            st.rerun()

    # --- TRANSACTION (WITHDRAW/DEPOSIT) SCREEN ---
    elif screen == 'TRANSACTION':
        action = "Withdraw" if st.session_state.tx_type == 'WITHDRAW' else "Deposit"
        st.subheader(f"{action} Cash")
        
        amount = st.number_input(f"Enter amount to {action.lower()} ($)", min_value=0.0, step=10.0, format="%.2f")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", type="primary"):
                with st.spinner(f"Processing {action.lower()}..."):
                    time.sleep(0.5) # Simulate network delay
                    if process_transaction(amount):
                        st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.screen = 'MENU'
                st.rerun()

    # --- SUCCESS SCREEN ---
    elif screen == 'SUCCESS':
        st.success("✅ Transaction Successful!")
        
        acc_id = st.session_state.current_account_id
        balance = st.session_state.db['accounts'][acc_id]['balance']
        st.metric(label="New Balance", value=f"${balance:,.2f}")
        
        if st.button("Continue"):
            st.session_state.screen = 'MENU'
            st.rerun()


# ==========================================
# 5. APP ENTRY POINT
# ==========================================
if __name__ == "__main__":
    init_state()
    render_ui()