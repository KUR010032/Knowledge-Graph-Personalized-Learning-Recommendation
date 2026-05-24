import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processing.knowledge_graph_builder import KnowledgeGraphBuilder
from data_processing.student_data_loader import StudentDataLoader
from backend.app import app

def setup_database():
    """Initialize the knowledge graph and load student data"""
    print("Setting up database...")
    
    # Build knowledge graph from catalog
    with open("data/studentdata/catalog.txt", "r", encoding="utf-8") as f:
        catalog = f.read()
    
    builder = KnowledgeGraphBuilder()
    builder.build_graph(catalog)
    builder.close()
    
    # Load student data
    loader = StudentDataLoader()
    for filename in os.listdir("data/studentdata"):
        if filename.endswith(".csv"):
            student_id = filename.replace(".csv", "")
            filepath = os.path.join("data/studentdata", filename)
            loader.load_student_from_csv(filepath, student_id)
            print(f"Loaded data for {student_id}")
    
    loader.close()
    print("Database setup complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_database()
    else:
        print("Starting Flask server...")
        print("Open http://127.0.0.1:5000 in your browser")
        app.run(debug=True, host="0.0.0.0", port=5000)
