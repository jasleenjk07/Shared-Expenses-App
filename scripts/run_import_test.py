"""Run CSV import and save report for deliverable #6."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models import Group, User
from backend.services.import_service import import_csv_to_group


def main():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(email="test@test.com", name="Test")
        user.set_password("test")
        db.session.add(user)
        db.session.commit()

        group = Group(name="Flat 4B", created_by=user.id)
        db.session.add(group)
        db.session.commit()

        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Expenses_Export.csv",
        )
        with open(csv_path, "rb") as f:
            content = f.read()

        result = import_csv_to_group(group.id, user.id, content, "Expenses_Export.csv")

        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports",
            "import_report.json",
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as out:
            json.dump(result["report"], out, indent=2)

        print(f"Imported {result['report']['imported_expenses']} expenses")
        print(f"Imported {result['report']['imported_settlements']} settlements")
        print(f"Skipped {result['report']['skipped_rows']} rows")
        print(f"Anomalies: {result['report']['total_anomalies']}")
        print(f"Report saved to {report_path}")

        from backend.services.balance_service import get_balance_summary

        balances = get_balance_summary(group.id)
        print("\nSimplified debts:")
        for d in balances["simplified_debts"]:
            print(f"  {d['from_user_name']} pays {d['to_user_name']}: ₹{d['amount_inr']}")


if __name__ == "__main__":
    main()
