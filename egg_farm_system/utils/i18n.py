"""
Internationalization (i18n) and Translation Manager for Pashto Support
"""

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QApplication

# Comprehensive Pashto Translations
TRANSLATIONS = {
    "en": {}, # English is the key
    "ps": {
        # --- Sidebar & Navigation ---
        "Dashboard": "ډیش بورډ",
        "Egg Farm Management System": "د هګیو فارم مدیریت سیستم",
        
        # Groups
        "Egg Management": "د هګیو مدیریت",
        "Farm Operations": "د فارم عملیات",
        "Transactions": "مالي معاملات",
        "Reports & Analytics": "راپورونه او تحلیلونه",
        "System": "سیستم",
        "Administration": "اداره",
        
        # Buttons
        "Production": "تولید",
        "Stock": "ذخیره",
        "Expenses": "مصارف",
        "Farm Management": "د فارم مدیریت",
        "Flock Management": "د رمې مدیریت",
        "Feed Management": "د خوړو مدیریت",
        "Inventory": "ګدام / موجودي",
        "Equipment": "تجهیزات",
        "Sales": "پلور",
        "Purchases": "پیرود",
        "Sell Raw Material": "خام مواد پلورل",
        "Parties": "مشتریان / عرضه کوونکي",
        "Reports": "راپورونه",
        "Analytics": "تحلیلونه",
        "Cash Flow": "نغدي جریان",
        "Settings": "تنظیمات",
        "Backup & Restore": "بیڪ اپ او بیا رغونه",
        "Workflow Automation": "د کار اتومات",
        "Audit Trail": "د پلټنې لار",
        "Email Config": "د بریښنالیک تنظیم",
        "Users": "کاروونکي",
        "Employees": "کارمندان",
        "Notifications": "خبرتیاوې",
        "Farm Theme": "د فارم بڼه",
        "Logout": "وتل",
        
        # --- Common UI Elements ---
        "Save": "ثبت",
        "Cancel": "لغوه",
        "Delete": "حذف",
        "Edit": "سمول",
        "Update": "تازه کول",
        "Add": "اضافه کول",
        "New": "نوی",
        "Refresh": "تجدید",
        "Search": "لټون",
        "Filter": "فلټر",
        "Print": "چاپ",
        "Export": "صادرول",
        "Export to PDF": "PDF صادرول",
        "Export to Excel": "Excel صادرول",
        "Export to CSV": "CSV صادرول",
        "Close": "بندول",
        "Back": "شاته",
        "Next": "راتلونکی",
        "View": "کوتل",
        "Actions": "کړنې",
        "Date": "نیټه",
        "Time": "وخت",
        "Description": "تفصیل",
        "Notes": "یادښتونه",
        "Status": "حالت",
        "Total": "ټول",
        "ID": "ID",
        
        # --- Farm & Shed ---
        "Farms": "فارمونه",
        "Sheds": "شیډونه",
        "Add New Farm": "نوی فارم اضافه کړئ",
        "Add Shed": "شیډ اضافه کړئ",
        "Farm Name": "د فارم نوم",
        "Location": "موقعیت",
        "Capacity": "ظرفیت",
        "Capacity (birds)": "ظرفیت (مرغۍ)",
        "Shed Name": "د شیډ نوم",
        
        # --- Flock ---
        "Flock": "رمه",
        "Flocks": "رمې",
        "Add Flock": "رمه اضافه کړئ",
        "Start Date": "د پیل نیټه",
        "Initial Count": "لومړنی شمیر",
        "Live": "ژوندي",
        "Age (Days)": "عمر (ورځې)",
        "Mortality": "مړینه",
        "Bird Count": "د مرغیو شمیر",
        "Current Flocks": "اوسنۍ رمې",
        
        # --- Egg Production ---
        "Daily Production": "ورځنی تولید",
        "Add Production": "تولید ثبت کړئ",
        "Collected": "راټول شوي",
        "Small": "کوچنۍ",
        "Medium": "منځنۍ",
        "Large": "لوی",
        "Broken": "ماتې",
        "Usable": "د کارولو وړ",
        "Trays": "کریتونه",
        "Cartons": "کارتنونه",
        
        # --- Feed ---
        "Feed": "خواړه",
        "Raw Materials": "خام مواد",
        "Formulas": "فارمولونه",
        "Feed Production": "د خوړو تولید",
        "Issue Feed": "خواړه توزیع",
        "Produce Batch": "بیچ تولید کړئ",
        "Formula": "فارمول",
        "Ingredients": "اجزاء",
        "Percentage": "سلنه",
        "Cost (AFG)": "قیمت (افغانۍ)",
        "Cost (USD)": "قیمت (ډالر)",
        "Exchange Rate": "د تبادلې نرخ",
        "Stock": "موجودي",
        "Low Stock": "کمه موجودي",
        "Available": "دسترسی وړ",
        
        # --- Sales & Finance ---
        "Customer": "پیرودونکی",
        "Supplier": "عرضه کونکی",
        "Party": "مشتری/کمپنی",
        "Amount": "مقدار",
        "Rate": "نرخ",
        "Rate (AFG)": "نرخ (افغانۍ)",
        "Rate (USD)": "نرخ (ډالر)",
        "Total (AFG)": "ټول (افغانۍ)",
        "Total (USD)": "ټول (ډالر)",
        "Payment Method": "د تادیې طریقه",
        "Cash": "نغدي",
        "Credit": "قرض",
        "Bank": "بانک",
        "Received": "ترلاسه شوی",
        "Paid": "تادیه شوی",
        "Balance": "بیلنس",
        "Debit": "ډیبټ (قرض)",
        "Credit": "کریډیټ (امانت)",
        "Record Sale": "پلور ثبت کړئ",
        "Record Purchase": "پیرود ثبت کړئ",
        "Record Expense": "لګښت ثبت کړئ",
        "Record Payment": "تادیه ثبت کړئ",
        "Category": "کټګوري",
        "Cash Inflow": "نغدي عاید",
        "Cash Outflow": "نغدي لګښت",
        "Net Cash Flow": "خالص نغدي جریان",
        "Cash Balance": "نغدي بیلنس",
        
        # --- Messages ---
        "Validation Error": "د تایید تېروتنه",
        "Success": "بریالی",
        "Error": "خطا",
        "Warning": "خبرداری",
        "Confirm Delete": "د حذف کولو تایید",
        "Are you sure you want to delete": "ایا تاسو ډاډه یاست چې غواړئ حذف یې کړئ",
        "This action cannot be undone": "دا عمل بیرته نه راګرځي",
        "Saved successfully": "په بریالیتوب سره ثبت شو",
        "Failed to save": "په ثبتولو کې پاتې راغی",
        "Please fill all required fields": "مهرباني وکړئ ټول اړین فیلډونه ډک کړئ",
        "Insufficient stock": "ناکافي موجودي",
        
        # --- Login ---
        "Login": "ننوتل",
        "Username": "کارن نوم",
        "Password": "پټنوم",
        "Welcome": "ښه راغلاست",
    }
}

# Load additional auto-generated Pashto translations if present
try:
    from egg_farm_system.utils.i18n_additional_ps import ADDITIONAL_PS
    TRANSLATIONS.setdefault('ps', {}).update(ADDITIONAL_PS)
except Exception:
    pass

class TranslationManager(QObject):
    language_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_lang = "en"
        self._translations = TRANSLATIONS

    def set_language(self, lang_code):
        if lang_code in self._translations or lang_code == "en":
            self.current_lang = lang_code
            
            # Update Application Layout Direction
            app = QApplication.instance()
            if app:
                if lang_code == "ps":
                    app.setLayoutDirection(Qt.RightToLeft)
                else:
                    app.setLayoutDirection(Qt.LeftToRight)
            
            self.language_changed.emit(lang_code)

    def get(self, text):
        if self.current_lang == "en":
            return text
        
        lang_dict = self._translations.get(self.current_lang, {})
        # Return translated text or original if missing
        return lang_dict.get(text, text)

# Global Instance
_i18n = TranslationManager()

def get_i18n():
    return _i18n

def tr(text):
    """Helper function for quick access"""
    return _i18n.get(text)
