# Online Food Ordering System

A beginner-friendly Flask + SQLite web project for a college mini-project.

## Features
- Food menu with search and category filter
- User registration, login, and logout
- Session-based shopping cart with quantity updates/removal
- Checkout with delivery details
- Order confirmation and order history
- Admin dashboard to add menu items, enable/disable items, view orders, and update order status
- SQLite database created automatically on first run
- Passwords stored as hashes

## Requirements
- Python 3.10 or newer
- Internet connection is optional; sample food images use external image URLs

## Run on Windows (PowerShell)
1. Extract the ZIP file.
2. Open the extracted folder in VS Code.
3. Open Terminal in VS Code.
4. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and use `.\.venv\Scripts\python.exe app.py`.
6. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open this address in your browser: http://127.0.0.1:5000

## Run on Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

## Demo admin login
- Email: `admin@foodie.local`
- Password: `Admin@123`

Use the admin account to add menu items and manage orders. Change the demo credentials and `app.secret_key` before any real deployment. This is an educational demo and is not production-hardened.

## Project structure
```text
online_food_ordering_system/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── cart.html
│   ├── checkout.html
│   ├── order_success.html
│   ├── orders.html
│   ├── admin.html
│   └── 404.html
└── static/
    └── style.css
```

## Database tables
- `users`: customer and admin accounts
- `foods`: food menu items
- `orders`: delivery and order status details
- `order_items`: items purchased in each order

## Notes
- This demo does not process real payments; checkout places a demo order.
- The Flask development server is for local learning only, not public production hosting.
