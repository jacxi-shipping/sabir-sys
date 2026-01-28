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
        "Login Failed": "ننوتل پاتې راغی",
        "Account Locked": "حساب قفل شوی",
        "Too many failed login attempts. Account locked for 15 minutes.": "د ناکامه ننوتلو ډیرې هڅې. حساب د 15 دقیقو لپاره قفل شو.",
        
        # --- User Management ---
        "New User": "نوی کاروونکی",
        "Add User": "کاروونکی اضافه کړئ",
        "Role": "رول",
        "Change Password": "پټنوم بدل کړئ",
        "Old Password": "پخوانی پټنوم",
        "New Password": "نوی پټنوم",
        "Confirm Password": "پټنوم تایید کړئ",
        
        # --- Common Forms ---
        "Required field": "اړین فیلډ",
        "Optional": "اختیاري",
        "(optional)": "(اختیاري)",
        "Description (optional)": "تفصیل (اختیاري)",
        "Select": "انتخاب",
        "Selection": "انتخاب",
        "Choose": "غوره کړئ",
        "Browse": "لټون",
        "Apply": "تطبیق",
        "Reset": "بیا تنظیم",
        "Confirm": "تایید",
        "Submit": "وسپارئ",
        "Yes": "هو",
        "No": "نه",
        "OK": "سمه ده",
        
        # --- Farm & Shed Management ---
        "Add New Farm": "نوی فارم اضافه کړئ",
        "Add a new farm": "یو نوی فارم اضافه کړئ",
        "Add a new shed": "یو نوی شیډ اضافه کړئ",
        "Shed": "شیډ",
        "Capacity must be greater than 0.": "ظرفیت باید له 0 څخه زیات وي.",
        "birds": "مرغۍ",
        
        # --- Flock Management ---
        "Add Flock": "رمه اضافه کړئ",
        "Record Mortality": "مړینه ثبت کړئ",
        "Record Medication": "درمل ثبت کړئ",
        "Failed to record mortality": "د مړینې ثبت کول پاتې راغی",
        "Failed to record medication": "د درملو ثبت کول پاتې راغی",
        "Count:": "شمیر:",
        "Dose Unit:": "د دوا واحد:",
        "Administered By:": "د خوا پر لاره اچول شوی:",
        "Days:": "ورځې:",
        
        # --- Production Forms ---
        "Collected:": "راټول شوي:",
        "Broken:": "ماتې:",
        "Cartons:": "کارتنونه:",
        "Cartons: 0.00": "کارتنونه: 0.00",
        "Checking stock...": "موجودي کتل کیږي...",
        "Current Stock:": "اوسنی موجودي:",
        "Current stock: N/A": "اوسنی موجودي: شتون نلري",
        
        # --- Sales & Purchases ---
        "Calculated Rate:": "محاسبه شوی نرخ:",
        "At least one rate (AFG or USD) must be greater than 0.": "لږ تر لږه یو نرخ (افغانۍ یا ډالر) باید له 0 څخه زیات وي.",
        "Customer:": "پیرودونکی:",
        "Address:": "پته:",
        "Conversion Preview": "د بدلون مخکتنه",
        
        # --- Party Management ---
        "Add New Party": "نوی ګوند اضافه کړئ",
        "Add a new party (Ctrl+N)": "یو نوی ګوند اضافه کړئ (Ctrl+N)",
        "Add credit/debit transaction to a party": "یوې ګوند ته کریډیټ/ډیبټ معامله اضافه کړئ",
        "Add Party Transaction": "د ګوند معامله اضافه کړئ",
        "Credit": "کریډیټ (امانت)",
        
        # --- Inventory & Materials ---
        "Add Material": "مواد اضافه کړئ",
        "Add Ingredient": "جزء اضافه کړئ",
        "Add Equipment": "تجهیزات اضافه کړئ",
        "Available: N/A": "دسترس: شتون نلري",
        "Available: 0.00 units": "دسترس: 0.00 واحدونه",
        
        # --- Analytics & Reports ---
        "ABC Analysis": "ABC تحلیل",
        "Advanced Analytics": "پرمختللي تحلیلونه",
        "Analytics & Forecasting": "تحلیلونه او وړاندوینه",
        "Calculate Analytics": "تحلیلونه محاسبه کړئ",
        "Calculate ROI": "ROI محاسبه کړئ",
        "Cost Breakdown": "د لګښت تفصیل",
        "Compare Sheds": "شیډونه پرتله کړئ",
        "Daily Egg Production (Last 30 Days)": "ورځنی هګیو تولید (تیرې 30 ورځې)",
        "Avg. Live Birds: Not calculated": "اوسط ژوندي مرغۍ: محاسبه شوي نه دي",
        "Birds at Start: Not calculated": "په پیل کې مرغۍ: محاسبه شوي نه دي",
        "Cost of Goods Sold (Feed): Not calculated": "د پلورل شوي توکو قیمت (خواړه): محاسبه شوي نه دي",
        "Analyze Anomalies": "بې نظمۍ تحلیل کړئ",
        "Analysis Period:": "د تحلیل موده:",
        
        # --- Backup & Restore ---
        "Backup & Restore": "بیک اپ او بیا رغونه",
        "Create Backup Now": "اوس بیک اپ جوړ کړئ",
        "Creating Backup": "بیک اپ جوړیږي",
        "Available Backups:": "دسترس بیک اپونه:",
        "Confirm Restore": "بیا رغونه تایید کړئ",
        "Cleanup Old Backups": "زاړه بیک اپونه پاک کړئ",
        "Cleanup Complete": "پاکول بشپړ شول",
        
        # --- Email & Settings ---
        "Email Config": "د بریښنالیک تنظیم",
        "Settings": "تنظیمات",
        "All Settings:": "ټول تنظیمات:",
        "Advanced settings editor. Use this to view and edit all application settings ": "پرمختللي تنظیماتو ایډیټر. دا د ټولو اپلیکیشن تنظیماتو لیدو او سمولو لپاره وکاروئ ",
        "Save All Settings": "ټول تنظیمات ثبت کړئ",
        "Configure egg packaging expenses. These values are used when calculating ": "د هګیو بسته بندۍ لګښتونه تنظیم کړئ. دا ارزښتونه د محاسبې پرمهال کارول کیږي ",
        
        # --- Workflow & Automation ---
        "Workflow Automation": "د کار جریان اتومات",
        "Audit Trail": "د پلټنې لار",
        "Audit Log Details": "د پلټنې ریکارډ تفصیلات",
        "Action Type:": "د عمل ډول:",
        "Date & Time:": "نیټه او وخت:",
        
        # --- Messages & Dialogs ---
        "Confirm Deletion": "د حذف تایید",
        "Are you sure you want to delete": "ایا تاسو ډاډه یاست چې غواړئ حذف کړئ",
        "This action cannot be undone": "دا عمل بیرته نه راګرځي",
        "Access Denied": "لاسرسی منع شوی",
        "Admin only": "یوازې اډمین",
        "Complete": "بشپړ",
        "Failed": "پاتې راغی",
        "Created": "جوړ شو",
        "Deleted": "حذف شو",
        "Not Found": "ونه موندل شو",
        
        # --- Common UI Actions ---
        "Delete Selected": "انتخاب شوي حذف کړئ",
        "Edit Selected": "انتخاب شوي سمول کړئ",
        "Delete Setting": "تنظیم حذف کړئ",
        "Delete Failed": "حذف کول پاتې راغی",
        "Clear All": "ټول پاک کړئ",
        "Refresh": "تازه کړئ",
        "Search...": "لټون...",
        "View": "کتل",
        
        # --- Employee Management ---
        "Add Employee": "کارمند اضافه کړئ",
        "Employee & Salary Management": "د کارمندانو او معاش مدیریت",
        "Employee Management": "د کارمندانو مدیریت",
        
        # --- Egg Management ---
        "Egg Sale - Carton Based": "د هګیو پلور - د کارتن پر بنسټ",
        "Egg Stock Management": "د هګیو موجودي مدیریت",
        "Egg Production Tracking": "د هګیو تولید تعقیب",
        "Egg Production Forecast (Next 7 Days)": "د هګیو تولید وړاندوینه (راتلونکې 7 ورځې)",
        "Egg Expense Management": "د هګیو لګښت مدیریت",
        "Egg Grade:": "د هګیو درجه:",
        "0 eggs": "0 هګۍ",
        "<b>Eggs</b>": "<b>هګۍ</b>",
        "= 0 eggs": "= 0 هګۍ",
        
        # --- Trays & Cartons ---
        "0 trays": "0 کریتونه",
        "<b>Trays</b>": "<b>کریتونه</b>",
        "= 0 trays": "= 0 کریتونه",
        "= 0.00 trays": "= 0.00 کریتونه",
        "= 0.00 cartons": "= 0.00 کارتنونه",
        "<b>Grade</b>": "<b>درجه</b>",
        "<b>Total:</b>": "<b>ټول:</b>",
        
        # --- Numbers & Amounts ---
        "0.00": "0.00",
        "0.00 AFG": "0.00 افغانۍ",
        "0.00 USD": "0.00 ډالر",
        "Amount (AFG):": "مقدار (افغانۍ):",
        "Amount (AFG): <span style='color: red;'>*</span>": "مقدار (افغانۍ): <span style='color: red;'>*</span>",
        "Amount (USD):": "مقدار (ډالر):",
        "Category: <span style='color: red;'>*</span>": "کټګوري: <span style='color: red;'>*</span>",
        "Date: <span style='color: red;'>*</span>": "نیټه: <span style='color: red;'>*</span>",
        "Date:": "نیټه:",
        
        # --- Additional UI Elements ---
        "Add Transaction": "معامله اضافه کړئ",
        "Add any additional notes here...": "دلته کوم اضافي یادښتونه اضافه کړئ...",
        "Any additional notes...": "کوم اضافي یادښتونه...",
        "Cash Flow Management": "د نغدو جریان مدیریت",
        "Daily Average: 0": "ورځنی اوسط: 0",
        "Current Balance: N/A": "اوسنی بیلنس: شتون نلري",
        "Avg Price: N/A": "اوسط قیمت: شتون نلري",
        
        # --- Export Options ---
        "Export CSV": "CSV صادرول",
        "Export Excel": "Excel صادرول", 
        "Export PDF": "PDF صادرول",
        
        # --- Additional Common ---
        "Create": "جوړول",
        "Change": "بدلول",
        "Enable/Disable": "فعالول/غیرفعالول",
        "Validation": "تایید",
        
        # --- Language Settings ---
        "Language Settings": "د ژبې تنظیمات",
        "Interface Language:": "د انٹرفیس ژبه:",
        "Note: Changing the language will update the interface immediately. The application will switch to Right-to-Left layout for Pashto.": "یادښت: د ژبې بدلول به سمدستي انټرفیس تازه کړي. اپلیکیشن به د پښتو لپاره ښي څخه کیڼ ته ترتیب ته بدل شي.",
        "Language Changed": "ژبه بدله شوه",
        "Language has been changed to {0}. Some parts of the interface will update immediately, while others may require restarting the application.": "ژبه {0} ته بدله شوه. د انټرفیس ځینې برخې به سمدستي تازه شي، پداسې حال کې چې نورې ممکن د اپلیکیشن بیا پیل کولو ته اړتیا ولري.",
        
        # --- Currency Settings ---
        "Currency Settings": "د اسعارو تنظیمات",
        "Exchange Rate (AFG/USD):": "د تبادلې نرخ (افغانۍ/ډالر):",
        
        # --- Additional Settings ---
        "Egg Management": "د هګیو مدیریت",
        "Egg Packaging Expenses": "د هګیو بسته بندۍ لګښتونه",
        "Tray Expense:": "د کریټ لګښت:",
        "Carton Expense:": "د کارټن لګښت:",
        "Conversion Information": "د بدلون معلومات",
        "General": "عمومي",
        "Advanced": "پرمختللي",
        "Save All Settings": "ټول تنظیمات ثبت کړئ",
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
