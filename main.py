from garmin_exporter import collect_data
from data_manager import DataManager
from garmin_graphs import GarminGraphs
from export import GarminExporter

def main():
    collect_data()

    manager = DataManager()
    data = manager.main()

    graphs = GarminGraphs(data)

    exporter = GarminExporter()

    graphs.generate_all()
    exporter.export()

# if __name__ == "__main__":
#     main()

manager = DataManager()
data = manager.main()
print(data)