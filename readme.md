# How to run and work locally
Basic setup guide - feel free to add if I missed anything

## Requirements

- **Python**: `3.8+` (Ensure it's installed and available in your system's PATH)
- **pip**: Latest version (`pip install --upgrade pip`)
- **virtualenv**: (`pip install virtualenv`)

---

## Setup Instructions

### **1. Clone the Repository**
Use any method you prefer

### **2. Create a Virtual Environment**
Run these based on your OS:
**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```
**macOS/Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies & Django**
```bash
pip install -r requirements.txt
```

### **4. Apply Database Migrations**
```bash
python manage.py migrate
```

### **5. Run the Local Development Server**
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/ in your browser to test.