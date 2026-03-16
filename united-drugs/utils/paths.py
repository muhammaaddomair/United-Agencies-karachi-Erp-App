import os
import sys

APP_NAME = "United Agencies karachi"
COMPANY = "TechSaws"


def is_frozen():
    return getattr(sys, "frozen", False)


def get_app_root():
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isdir(meipass):
            return meipass
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_app_data_dir():
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        path = os.path.join(appdata, COMPANY, APP_NAME)
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            pass

    path = os.path.join(get_app_root(), "data")
    os.makedirs(path, exist_ok=True)
    return path


def get_invoices_dir():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    path = os.path.join(docs, "UnitedAgenciesKarachiInvoices")
    os.makedirs(path, exist_ok=True)
    return path


def get_asset_path(filename):
    """Get the path to an asset file in the assets folder."""
    return os.path.join(get_app_root(), "assets", filename)
