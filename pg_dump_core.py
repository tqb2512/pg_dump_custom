import os
import subprocess
import psycopg2
import re

class PostgresDumper:
    def __init__(self, db_host, db_port, db_name, db_user, db_password, schema_name, output_dir, pg_dump_path):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.schema_name = schema_name
        self.output_dir = output_dir
        self.pg_dump_path = pg_dump_path
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_connection(self):
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                options=f"-c search_path={self.schema_name}" if self.schema_name else None
            )
            return conn
        except Exception as e:
            raise Exception(f"Database connection error: {e}")

    def export_all_functions(self, progress_callback=None):
        """Xuất tất cả các function ra mỗi file riêng biệt .sql"""
        if progress_callback:
            progress_callback("Đang lấy danh sách các functions...")
            
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            conn = self.get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT p.oid, p.proname 
                FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = %s
            """
            cur.execute(query, (self.schema_name,))
            functions = cur.fetchall()
            
            success_count = 0
            for oid, proname in functions:
                cur.execute("SELECT pg_get_functiondef(%s)", (oid,))
                func_def = cur.fetchone()[0]
                
                file_path = os.path.join(self.output_dir, f"{proname}.sql")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(func_def)
                    f.write(";\n")
                
                if progress_callback:
                    progress_callback(f"✅ Đã xuất function: {proname} -> {file_path}")
                success_count += 1
                
            cur.close()
            conn.close()
            return True, f"Thành công! Đã xuất {success_count} functions."
        except Exception as e:
            return False, f"❌ Lỗi khi xuất functions: {e}"

    def export_all_tables(self, progress_callback=None):
        """Xuất cấu trúc (DDL) của tất cả tables ra mỗi file riêng biệt .sql"""
        if progress_callback:
            progress_callback("Đang lấy danh sách các tables...")
            
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            conn = self.get_connection()
            cur = conn.cursor()
            query = """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = %s
            """
            cur.execute(query, (self.schema_name,))
            tables = cur.fetchall()
            cur.close()
            conn.close()
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            success_count = 0
            for (tablename,) in tables:
                file_path = os.path.join(self.output_dir, f"{tablename}.sql")
                cmd = [
                    self.pg_dump_path,
                    "-h", self.db_host,
                    "-p", str(self.db_port),
                    "-U", self.db_user,
                    "-d", self.db_name,
                    "--table", f"{self.schema_name}.{tablename}" if self.schema_name else tablename,
                    "--schema-only", 
                    "-f", file_path
                ]
                
                subprocess.run(cmd, env=env, check=True, stderr=subprocess.PIPE, text=True)
                if progress_callback:
                    progress_callback(f"✅ Đã xuất table: {tablename} -> {file_path}")
                success_count += 1
                
            return True, f"Thành công! Đã xuất {success_count} tables."
        except subprocess.CalledProcessError as e:
             return False, f"❌ Lỗi lệnh pg_dump (Table: {tablename}): {e.stderr}"
        except Exception as e:
             return False, f"❌ Lỗi: {e}"

    def export_data_by_query(self, query, progress_callback=None):
        """Xuất dữ liệu table dựa theo câu lệnh SQL thành các lệnh INSERT."""
        match = re.search(r"from\s+([a-zA-Z0-9_.]+)", query, re.IGNORECASE)
        if not match:
            return False, f"❌ Không thể phân tích tên bảng từ câu SQL: {query}"
            
        table_name = match.group(1).split('.')[-1]
        
        where_part = re.split(r'\bwhere\b', query, flags=re.IGNORECASE)
        if len(where_part) > 1:
            values = re.findall(r"=\s*['\"]?([^'\"\s;]+)", where_part[1])
            file_suffix = "_".join(values) if values else "data"
        else:
            file_suffix = "data"
            
        file_path = os.path.join(self.output_dir, f"{table_name}_{file_suffix}.sql")
        
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            
            col_names = [desc[0] for desc in cur.description]
            target_table = f"{self.schema_name}.{table_name}" if self.schema_name else table_name
            
            with open(file_path, "w", encoding="utf-8") as f:
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            val_str = str(val).replace("'", "''")
                            values.append(f"'{val_str}'")
                    
                    insert_sql = f"INSERT INTO {target_table} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n"
                    f.write(insert_sql)
            
            if progress_callback:
                progress_callback(f"✅ Đã xuất {len(rows)} dòng thành công -> {file_path}")
            
            cur.close()
            conn.close()
            return True, f"Thành công! Đã xuất {len(rows)} dòng vào {file_path}"
        except Exception as e:
            return False, f"❌ Lỗi khi xuất data: {e}"
