# Postgres Dump Custom TUI

A custom Python interactive terminal interface (TUI) designed to automate and simplify PostgreSQL database exporting tasks. It allows users to smoothly export database schemas, functions, and subset query data directly to individual `.sql` files without remembering complicated `pg_dump` CLI commands.

## Features

- **Interactive UI**: A rich, robust arrow-key-guided menu eliminating the need for manual command-line typing.
- **Export Tables (DDL)**: Extracts the full structure of all tables within your provided schema. Each table is saved into its own `.sql` file.
- **Export Functions**: Extracts all Postgres functions within your schema to individual files.
- **Data Export by Query**: Input a custom SQL string right in the console (e.g. `select * from appmap where id = '200'`), and it will extract all results dynamically into `.sql` INSERT statements.
- **Persistent Configuration**: Host, database names, and output directories automatically save to a `config.json` file for future executions.
- **Cross-Platform**: The tool and output-folder openers work seamlessly on Windows, macOS, and Linux.

## Requirements

- Python 3.7+
- **Database Client Component**: You must have `pg_dump` installed on your machine. On Windows, this is typically included with your PostgreSQL server installation (e.g., `C:\Program Files\PostgreSQL\18\bin\pg_dump.exe`). On Linux, install `postgresql-client`.

## Installation

1. Clone or download the repository.
2. Install the lightweight Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## First Time Configuration

The very first time you run the tool on Linux or macOS, you will likely need to adjust the location of the `pg_dump` binary path.
Select `Cập nhật cấu hình DB` from the main menu and set your `pg_dump_path` to:
- Windows (default): `C:\Program Files\PostgreSQL\18\bin\pg_dump.exe`
- Linux: `pg_dump` (or `/usr/bin/pg_dump` if specifically needed)

## Usage

Start the interactive terminal UI with:

```bash
python pg_dump_tui.py
```

Use the **Up/Down Arrow keys** to navigate the menu and press **Enter** to make a selection. You can easily adjust your database connection or open your output folder directory right from the built-in UI!
