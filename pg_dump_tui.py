import sys
import os
import time
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
import questionary
from pg_dump_core import PostgresDumper

console = Console()

CONFIG_FILE = "config.json"

# ================= CẤU HÌNH MẶC ĐỊNH =================
DEFAULT_CONFIG = {
    "db_host": "192.168.18.111",
    "db_port": "5432",
    "db_name": "postgres",
    "db_user": "postgres",
    "db_password": "postgres",
    "schema_name": "tmp20261",
    "output_dir": "tmp20261",
    "pg_dump_path": r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
}
# =======================================================

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Ghép với default để lỡ file config bị thiếu key
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(dumper):
    config = {
        "db_host": dumper.db_host,
        "db_port": dumper.db_port,
        "db_name": dumper.db_name,
        "db_user": dumper.db_user,
        "db_password": dumper.db_password,
        "schema_name": dumper.schema_name,
        "output_dir": dumper.output_dir,
        "pg_dump_path": dumper.pg_dump_path
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi lưu cấu hình file: {e}[/bold red]")

def print_header(dumper):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    header_text = Text()
    header_text.append("🔗 Database: ", style="bold blue")
    header_text.append(f"{dumper.db_user}@{dumper.db_host}:{dumper.db_port}/{dumper.db_name}\n")
    header_text.append("📂 Schema: ", style="bold yellow")
    header_text.append(f"{dumper.schema_name}   ")
    header_text.append("| Output: ", style="bold yellow")
    header_text.append(f"{dumper.output_dir}")
    
    console.print(Panel(header_text, title="[bold green]POSTGRES DUMP CUSTOM TUI", expand=False))

def ui_progress_callback(message):
    """Log trực tiếp các dòng xuất."""
    if "✅" in message:
        console.print(message, style="green")
    elif "❌" in message:
        console.print(message, style="bold red")
    else:
        console.print(message, style="dim")

def update_config(dumper):
    console.print("\n[bold cyan]Cập nhật cấu hình hiện tại:[/bold cyan]")
    
    questions = [
        {"type": "text", "name": "db_host", "message": "Host:", "default": dumper.db_host},
        {"type": "text", "name": "db_port", "message": "Port:", "default": dumper.db_port},
        {"type": "text", "name": "db_name", "message": "DB Name:", "default": dumper.db_name},
        {"type": "text", "name": "db_user", "message": "User:", "default": dumper.db_user},
        {"type": "password", "name": "db_password", "message": "Password:", "default": dumper.db_password},
        {"type": "text", "name": "schema_name", "message": "Schema:", "default": dumper.schema_name},
        {"type": "text", "name": "output_dir", "message": "Output Dir:", "default": dumper.output_dir},
    ]
    
    answers = questionary.prompt(questions)
    
    if answers:
        dumper.db_host = answers['db_host']
        dumper.db_port = answers['db_port']
        dumper.db_name = answers['db_name']
        dumper.db_user = answers['db_user']
        dumper.db_password = answers['db_password']
        dumper.schema_name = answers['schema_name']
        dumper.output_dir = answers['output_dir']
        
        # Lưu vào tệp config.json
        save_config(dumper)
        
        if not os.path.exists(dumper.output_dir):
            os.makedirs(dumper.output_dir)
            
        console.print(Panel("✅ Cấu hình đã được lưu và cập nhật vào file `config.json`!", style="bold green", expand=False))

def main_menu():
    config = load_config()
    dumper = PostgresDumper(**config)

    while True:
        print_header(dumper)
        
        choice = questionary.select(
            "Vui lòng chọn một thao tác:",
            choices=[
                "Xuất tất cả Tables (DDL)",
                "Xuất tất cả Functions",
                "Xuất dữ liệu bằng SQL SELECT query",
                "Xuất dữ liệu tách file theo nhóm",
                "Cập nhật cấu hình DB",
                "Mở thư mục Output hiện tại",
                "Thoát"
            ]
        ).ask()
        
        if choice is None or "Thoát" in choice:
            console.print("\n[bold cyan]👋 Tạm biệt![/bold cyan]")
            break
            
        elif "Xuất tất cả Tables" in choice:
            with console.status("[bold green]Đang chạy pg_dump..."):
                success, msg = dumper.export_all_tables(progress_callback=ui_progress_callback)
            
            p_style = "bold green" if success else "bold red"
            console.print(Panel(msg, style=p_style, expand=False))
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()

        elif "Xuất tất cả Functions" in choice:
            with console.status("[bold green]Đang truy vấn DB..."):
                success, msg = dumper.export_all_functions(progress_callback=ui_progress_callback)
                
            p_style = "bold green" if success else "bold red"
            console.print(Panel(msg, style=p_style, expand=False))
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()

        elif "Xuất dữ liệu bằng SQL SELECT" in choice:
            query = questionary.text("Query >").ask()
            if query and query.strip().lower() != 'cancel':
                with console.status("[bold green]Đang thực thi query và ghi file..."):
                    success, msg = dumper.export_data_by_query(query, progress_callback=ui_progress_callback)
                
                p_style = "bold green" if success else "bold red"
                console.print(Panel(msg, title="[bold white]Kết quả", style=p_style, expand=False))
                
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()

        elif "Xuất dữ liệu tách file theo nhóm" in choice:
            table_name = questionary.text("Tên bảng (vd: allcode):").ask()
            if table_name and table_name.strip().lower() != 'cancel':
                cols_input = questionary.text("Các cột distinct (cách nhau dấu phẩy, vd: cdname,cdtype):").ask()
                if cols_input and cols_input.strip().lower() != 'cancel':
                    with console.status(f"[bold green]Đang xuất dữ liệu bảng {table_name}..."):
                        success, msg = dumper.export_data_by_distinct_cols(table_name.strip(), cols_input.strip(), progress_callback=ui_progress_callback)
                    
                    p_style = "bold green" if success else "bold red"
                    console.print(Panel(msg, title="[bold white]Kết quả", style=p_style, expand=False))
                    
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()

        elif "Cập nhật cấu hình DB" in choice:
            update_config(dumper)
            questionary.press_any_key_to_continue("Nhấn phím bất kỳ để quay lại...").ask()
            
        elif "Mở thư mục Output hiện tại" in choice:
            out_path = os.path.abspath(dumper.output_dir)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
                
            if sys.platform == "win32":
                os.startfile(out_path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", out_path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", out_path])
                
            console.print(f"[green]Đã mở {out_path}[/green]")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.exit(0)
