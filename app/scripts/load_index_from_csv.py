import argparse
import csv
from pathlib import Path
from typing import Dict

from sqlmodel import Session, select

from app.db.engine import engine
from app.models.symbol import Symbol
from app.models.index import Index
from app.models.index_constituent import IndexConstituent

# =====================================================================================#
# THIS IS A STANDALONE SCRIPT THAT WILL BE TRIGGERED EITHER MANUALLY or via a CRON JOB #
# NOT A PART OF FASTAPI                                                                #
# =====================================================================================#

REQUIRED_COLUMNS = {"Symbol", "Company Name"}


def parse_csv(path: Path) -> Dict[str, dict]:
    """
    Returns:
        {
          SYMBOL: {
            "name": Company Name
          }
        }
    """
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        rows = {}
        for row in reader:
            symbol = row["Symbol"].strip().upper()
            if not symbol:
                continue

            if symbol in rows:
                raise ValueError(f"Duplicate symbol in CSV: {symbol}")

            company_name = row["Company Name"].strip()
            if not company_name:
                raise ValueError(f"Missing Company Name for symbol {symbol}")

            rows[symbol] = {
                "name": company_name
            }

        if not rows:
            raise ValueError("CSV contains no valid rows")

        return rows


def main(index_name: str, description: str, csv_path: Path):
    data = parse_csv(csv_path)

    with Session(engine) as session:
        # 1️⃣ Upsert Index
        index = session.exec(
            select(Index).where(Index.name == index_name)
        ).first()

        if not index:
            index = Index(name=index_name, description=description)
            session.add(index)
            session.commit()
            session.refresh(index)
            print(f"✅ Created index: {index_name}")
        else:
            if index.description != description:
                index.description = description
                session.add(index)
                session.commit()
                print(f"🔄 Updated description for index: {index_name}")

        # 2️⃣ Resolve Symbols
        symbols: Dict[str, Symbol] = {}
        for sym, meta in data.items():
            symbol = session.exec(
                select(Symbol).where(Symbol.symbol == sym)
            ).first()

            if not symbol:
                symbol = Symbol(
                    symbol=sym,
                    name=meta["name"],
                )
                session.add(symbol)
                session.commit()
                session.refresh(symbol)
                print(f"➕ Added symbol: {sym}")

            symbols[sym] = symbol

        # 3️⃣ Fetch existing constituents for this index
        existing = session.exec(
            select(IndexConstituent)
            .where(IndexConstituent.index_id == index.id)
        ).all()

        existing_symbol_ids = {ic.symbol_id for ic in existing}

        # 4️⃣ Insert missing index constituents (weightage = NULL)
        for sym, symbol in symbols.items():
            if symbol.id not in existing_symbol_ids:
                ic = IndexConstituent(
                    index_id=index.id,
                    symbol_id=symbol.id,
                    weightage=None,  # 👈 explicitly NULL
                )
                session.add(ic)
                print(f"➕ Added constituent: {sym}")

        session.commit()
        print("✅ Index membership load complete (weightage = NULL)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load index symbols from CSV (weightage set to NULL)"
    )
    parser.add_argument("--index", required=True, help="Index name (e.g. NIFTY50)")
    parser.add_argument("--description", required=True, help="Index description")
    parser.add_argument("--csv", required=True, type=Path, help="Path to CSV file")

    args = parser.parse_args()

    main(
        index_name=args.index,
        description=args.description,
        csv_path=args.csv,
    )


# === STANDALONE SCRIPT USAGE ====

# uv run python app/scripts/load_index_from_csv.py \
#   --index NIFTY50 \
#   --description "NIFTY 50 Index" \
#   --csv ./resources/ind_nifty50list.csv
