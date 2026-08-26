import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from config import settings

def safe_float(val: Any, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("PKR", "").replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return default

def safe_int(val: Any, default: int = 0) -> int:
    if val is None or val == "":
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    s = str(val).replace(",", "").strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default

def _clean_product(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Product ID": str(row.get("Product ID", "")).strip(),
        "Name": str(row.get("Name", "")).strip(),
        "Category": str(row.get("Category", "")).strip(),
        "Price": safe_float(row.get("Price", 0)),
        "Discount Percent": safe_float(row.get("Discount Percent", 0)),
        "Stock Quantity": safe_int(row.get("Stock Quantity", 0)),
        "Description": str(row.get("Description", "")).strip()
    }

def _clean_order(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Order ID": str(row.get("Order ID", "")).strip(),
        "Customer Name": str(row.get("Customer Name", "")).strip(),
        "Customer Email": str(row.get("Customer Email", "")).strip(),
        "Product ID": str(row.get("Product ID", "")).strip(),
        "Product Name": str(row.get("Product Name", "")).strip(),
        "Order Date": str(row.get("Order Date", "")).strip(),
        "Status": str(row.get("Status", "")).strip(),
        "Quantity": safe_int(row.get("Quantity", 1)),
        "Total Paid": safe_float(row.get("Total Paid", 0)),
        "Tracking Number": str(row.get("Tracking Number", "")).strip()
    }

class SheetsService:
    def __init__(self):
        self.use_live_sheets = settings.has_google_sheets
        self.products_csv = os.path.join(settings.BASE_DIR, "products.csv")
        self.orders_csv = os.path.join(settings.BASE_DIR, "orders.csv")
        self.logs_csv = os.path.join(settings.BASE_DIR, "logs.csv")
        
        self.gclient = None
        
        if self.use_live_sheets:
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_file(settings.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
                self.gclient = gspread.authorize(creds)
            except Exception as e:
                print(f"Failed to authorize Google Service Account: {e}")
                self.use_live_sheets = False

    def _get_worksheet(self, custom_sheet_id: str, default_name: str):
        if not self.use_live_sheets or not self.gclient:
            return None
        target_id = custom_sheet_id.strip() if custom_sheet_id and custom_sheet_id.strip() else settings.SPREADSHEET_ID.strip()
        if not target_id:
            return None
        try:
            sheet = self.gclient.open_by_key(target_id)
            try:
                return sheet.worksheet(default_name)
            except Exception:
                return sheet.get_worksheet(0)
        except Exception as e:
            print(f"Error opening sheet '{target_id}': {e}")
            return None

    def get_all_products(self) -> List[Dict[str, Any]]:
        ws = self._get_worksheet(settings.PRODUCTS_SPREADSHEET_ID, "Products")
        if ws:
            try:
                records = ws.get_all_records()
                return [_clean_product(r) for r in records]
            except Exception as e:
                print(f"Sheets Products fetch error: {e}")
                
        if not os.path.exists(self.products_csv):
            return []
        products = []
        with open(self.products_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(_clean_product(row))
        return products

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        all_prods = self.get_all_products()
        query_lower = query.lower()
        results = []
        for p in all_prods:
            name = str(p.get("Name", "")).lower()
            cat = str(p.get("Category", "")).lower()
            desc = str(p.get("Description", "")).lower()
            pid = str(p.get("Product ID", "")).lower()
            if query_lower in name or query_lower in cat or query_lower in desc or query_lower in pid:
                results.append(p)
        return results

    def get_all_orders(self) -> List[Dict[str, Any]]:
        ws = self._get_worksheet(settings.ORDERS_SPREADSHEET_ID, "Orders")
        if ws:
            try:
                records = ws.get_all_records()
                return [_clean_order(r) for r in records]
            except Exception as e:
                print(f"Sheets Orders fetch error: {e}")

        if not os.path.exists(self.orders_csv):
            return []
        orders = []
        with open(self.orders_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                orders.append(_clean_order(row))
        return orders

    def lookup_order(self, order_id: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        orders = self.get_all_orders()
        order_id_clean = order_id.strip().upper()
        for o in orders:
            oid = str(o.get("Order ID", "")).strip().upper()
            if oid == order_id_clean:
                if email:
                    o_email = str(o.get("Customer Email", "")).strip().lower()
                    if o_email != email.strip().lower():
                        continue
                return o
        return None

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        order_id_clean = order_id.strip().upper()
        ws = self._get_worksheet(settings.ORDERS_SPREADSHEET_ID, "Orders")
        
        if ws:
            try:
                cell = ws.find(order_id_clean)
                if cell:
                    headers = ws.row_values(1)
                    status_col = headers.index("Status") + 1 if "Status" in headers else 7
                    ws.update_cell(cell.row, status_col, new_status)
                    return True
            except Exception as e:
                print(f"Failed to update status in Google Sheets: {e}")

        if not os.path.exists(self.orders_csv):
            return False
            
        rows = []
        updated = False
        with open(self.orders_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            status_idx = header.index("Status") if "Status" in header else 6
            id_idx = header.index("Order ID") if "Order ID" in header else 0
            
            rows.append(header)
            for row in reader:
                if row[id_idx].strip().upper() == order_id_clean:
                    row[status_idx] = new_status
                    updated = True
                rows.append(row)
                
        if updated:
            with open(self.orders_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            return True
            
        return False

    def log_interaction(
        self,
        customer_email: str,
        order_id: str,
        query: str,
        ai_response: str,
        refund_eligibility: str,
        refund_action: str
    ) -> str:
        asia_tz = ZoneInfo("Asia/Karachi")
        now_asia = datetime.now(asia_tz)
        interaction_id = f"INT-{int(now_asia.timestamp())}"
        timestamp = now_asia.strftime("%Y-%m-%d %H:%M:%S")
        
        row_data = [
            interaction_id,
            timestamp,
            customer_email or "anonymous",
            order_id or "N/A",
            query,
            ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
            refund_eligibility,
            refund_action
        ]
        
        ws = self._get_worksheet(settings.LOGS_SPREADSHEET_ID, "Logs & Refunds")
        if ws:
            try:
                all_values = ws.get_all_values()
                target_row = 2
                if not all_values:
                    headers = ["Interaction ID", "Timestamp", "Customer Email", "Order ID", "Query / Request", "AI Response Summary", "Refund Eligibility", "Refund Action Taken"]
                    try:
                        ws.update(range_name="A1:H1", values=[headers])
                    except Exception:
                        ws.update("A1:H1", [headers])
                    target_row = 2
                else:
                    while target_row <= len(all_values):
                        row_cells = all_values[target_row - 1]
                        is_filled = any(str(cell).strip() for cell in row_cells)
                        if not is_filled:
                            break
                        target_row += 1
                
                cell_range = f"A{target_row}:H{target_row}"
                try:
                    ws.update(range_name=cell_range, values=[row_data])
                except Exception:
                    try:
                        ws.update(cell_range, [row_data])
                    except Exception:
                        ws.update([row_data], cell_range)
                return interaction_id
            except Exception as e:
                print(f"Failed logging to Google Sheets: {e}")
                
        os.makedirs(os.path.dirname(self.logs_csv), exist_ok=True)
        headers = ["Interaction ID", "Timestamp", "Customer Email", "Order ID", "Query / Request", "AI Response Summary", "Refund Eligibility", "Refund Action Taken"]
        
        if not os.path.exists(self.logs_csv):
            rows = [headers, row_data]
        else:
            rows = []
            with open(self.logs_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                rows = [headers]
            
            target_idx = -1
            for idx in range(1, len(rows)):
                row = rows[idx]
                if not any(str(cell).strip() for cell in row):
                    target_idx = idx
                    break
                    
            if target_idx != -1:
                rows[target_idx] = row_data
            else:
                rows.append(row_data)
                
        with open(self.logs_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            
        return interaction_id

    def get_all_logs(self) -> List[Dict[str, Any]]:
        ws = self._get_worksheet(settings.LOGS_SPREADSHEET_ID, "Logs & Refunds")
        if ws:
            try:
                records = ws.get_all_records()
                return [r for r in records if any(str(v).strip() for v in r.values())]
            except Exception as e:
                print(f"Sheets Logs fetch error: {e}")

        if not os.path.exists(self.logs_csv):
            return []
            
        logs = []
        with open(self.logs_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if any(str(v).strip() for v in row.values()):
                    logs.append(dict(row))
        return logs

sheets_service = SheetsService()
