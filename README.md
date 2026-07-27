# 🏦 ATM Simulation System
A robust, multi-language ATM simulation system built to demonstrate advanced Software Engineering best practices. 
This project goes beyond a simple script by implementing **Clean Architecture (Domain-Driven Design)**, **SOLID principles**, and **Dependency Injection**. It includes three distinct interfaces: a Python Command-Line Interface, a Java Desktop GUI, and a modern Streamlit Web Application.

## ✨ Key Features

* **Multi-Role Access:** Distinct flows for Customers (withdraw, deposit, transfer) and Administrators (refill cash, view logs, unlock cards).
* **Robust Domain Model:** Uses `Decimal` for precise financial calculations and `UUID` for entity tracking.
* **Security:** Implements SHA-256 hashing for PINs and automatic account lockouts after 3 failed attempts.
* **Hardware Simulation:** The `CashService` strictly ensures the physical ATM has the correct bill denominations before debiting an account.
* **JSON Persistence:** Custom-built generic repositories that save state dynamically to local JSON files.

## 🏗️ Architecture & Design Patterns

This project heavily utilizes Object-Oriented Programming (OOP) concepts:
* **Encapsulation:** Entities like `Account` and `Card` strictly protect their internal state.
* **Dependency Inversion:** Application services rely on abstract `Repository` interfaces, not concrete database implementations.
* **Single Responsibility Principle:** Separated the `Account` (financial ledger) from the `Card` (authentication token).
* **Composition:** Services are built by injecting dependencies (Repositories) via constructors.

## 🚀 Getting Started
Used python to test the working logic, as working in java or cpp with the SOLID principles and implementing this architecture was a very tricky task. I've implemented it in both Java and Python, but to test, I have used the Python library Streamlit.
### 1. Python CLI and Java oops code(Core Architecture)
Requires Python 3.12+. Run the composition root to start the terminal interface.
```bash
python main.py
ATM-Simulation-System/
├── app/
│   ├── application/     # Services (BankService, AuthService)
│   ├── domain/          # Entities (Account, Card, Transaction) & Interfaces
│   ├── exceptions/      # Custom Domain Exceptions
│   ├── infrastructure/  # JSON Repository implementation
│   └── presentation/    # CLI Menu
├── data/                # Auto-generated JSON storage
├── app.py               # Streamlit Web App
├── main.py              # Composition Root & Entry Point
├── ATMSimulation.java   # Complete Java Core & CLI
└── ATMGUI.java          # Java Swing Desktop Interface
javac ATMSimulation.java ATMGUI.java
java ATMGUI
pip install streamlit
streamlit run app.py
