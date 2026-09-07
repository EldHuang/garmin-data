import os
import shutil
from datetime import datetime


class GarminExporter:

    BASE_GRAPH_DIR = "./graphs"
    DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

    def __init__(self):
        self.month_year = datetime.now().strftime("%B_%Y")
        self.source_dir = os.path.join(
            self.BASE_GRAPH_DIR,
            self.month_year
        )

    def confirm_export(self):
        print()
        print("=" * 60)
        print("EXPORT GARMIN GRAPHS")
        print("=" * 60)
        print(f"Source : {self.source_dir}")
        print(f"Target : {self.DOWNLOADS_DIR}")
        print()

        response = input(
            "Export this month's graphs to Downloads? [y/N]: "
        ).strip().lower()

        return response in ("y", "yes")

    def export(self):
        if not self.confirm_export():
            print("\nExport cancelled.")
            return False

        if not os.path.exists(self.source_dir):
            print()
            print(
                f"No graph folder was found for {self.month_year}."
            )
            print(
                "Run GarminGraphs.generate_all() first."
            )
            return False

        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)

        files = [
            filename
            for filename in os.listdir(self.source_dir)
            if filename.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not files:
            print("\nNo graph images found to export.")
            return False

        print()
        print("Exporting...")

        exported = 0

        for filename in files:
            source = os.path.join(
                self.source_dir,
                filename
            )

            destination = os.path.join(
                self.DOWNLOADS_DIR,
                filename
            )

            try:
                shutil.copy2(source, destination)
                print(f"  ✓ {filename}")
                exported += 1
            except OSError as error:
                print(
                    f"  ✗ Could not export {filename}: {error}"
                )

        print()
        print("=" * 60)
        print(f"Exported {exported} image(s)")
        print(f"Location: {self.DOWNLOADS_DIR}")
        print("=" * 60)

        return exported > 0
