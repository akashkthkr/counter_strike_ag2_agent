#!/usr/bin/env python3
"""
Script to inspect and extract data from ChromaDB.
"""
import os

from counter_strike_ag2_agent.rag_vector import ChromaRAG


def inspect_chromadb():
    """Inspect the ChromaDB database and show all stored data."""
    print("🔍 Inspecting ChromaDB Database...")
    
    # Check if .chroma directory exists
    if not os.path.exists('.chroma'):
        print("❌ No .chroma directory found. Run the game first to create data.")
        return
    
    try:
        # Connect to the default collection
        rag = ChromaRAG()
        
        print(f"✅ Connected to ChromaDB")
        print(f"📁 Collection: {rag.col.name}")
        
        # Get collection info
        try:
            count = rag.col.count()
            print(f"📊 Total documents: {count}")
            
            if count > 0:
                # Get all documents
                results = rag.col.get()
                
                print("\n📄 All Documents:")
                print("-" * 50)
                
                for i, (doc_id, document, metadata) in enumerate(zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                )):
                    print(f"{i+1}. ID: {doc_id}")
                    print(f"   Content: {document}")
                    print(f"   Metadata: {metadata}")
                    print()
                
                # Test a sample query
                print("\n🔍 Sample Query Test:")
                print("-" * 30)
                sample_query = "strategy"
                result = rag.ask(sample_query)
                print(f"Query: '{sample_query}'")
                print(f"Result: {result}")
                
            else:
                print("📭 No documents found in the database.")
                print("\n💡 To add data, run the game and use:")
                print("   kb:add Your tactical knowledge here")
                print("   kb:load filename.txt")
        
        except Exception as e:
            print(f"❌ Error accessing collection: {e}")
    
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")


def export_chromadb_to_text():
    """Export all ChromaDB data to a text file."""
    try:
        rag = ChromaRAG()
        results = rag.col.get()
        
        if not results['documents']:
            print("📭 No documents to export.")
            return
        
        with open('chromadb_export.txt', 'w') as f:
            f.write("ChromaDB Export\n")
            f.write("=" * 50 + "\n\n")
            
            for i, (doc_id, document, metadata) in enumerate(zip(
                results['ids'], 
                results['documents'], 
                results['metadatas']
            )):
                f.write(f"Document {i+1}\n")
                f.write(f"ID: {doc_id}\n")
                f.write(f"Content: {document}\n")
                f.write(f"Metadata: {metadata}\n")
                f.write("-" * 30 + "\n\n")
        
        print(f"✅ Exported {len(results['documents'])} documents to chromadb_export.txt")
    
    except Exception as e:
        print(f"❌ Export failed: {e}")


def search_chromadb(query):
    """Search ChromaDB with a specific query."""
    try:
        rag = ChromaRAG()
        
        # Direct search with similarity
        results = rag.col.query(
            query_texts=[query],
            n_results=5
        )
        
        print(f"🔍 Search Results for: '{query}'")
        print("-" * 50)
        
        if results['documents'][0]:
            for i, (doc, distance) in enumerate(zip(
                results['documents'][0], 
                results['distances'][0]
            )):
                print(f"{i+1}. Similarity: {1-distance:.3f}")
                print(f"   Content: {doc}")
                print()
        else:
            print("📭 No results found.")
    
    except Exception as e:
        print(f"❌ Search failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "export":
            export_chromadb_to_text()
        elif command == "search":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                search_chromadb(query)
            else:
                print("Usage: python inspect_chromadb.py search <your query>")
        else:
            print("Usage: python inspect_chromadb.py [export|search <query>]")
    else:
        inspect_chromadb()