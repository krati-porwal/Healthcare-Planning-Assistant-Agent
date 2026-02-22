"""
ChromaDB setup: initialize collections, embed and store disease guidelines
and hospital summaries from JSON knowledge files for semantic retrieval.
"""
import json
import os
import sys

# Add backend to path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import chromadb
from chromadb.utils import embedding_functions
from backend.config import CHROMA_PERSIST_DIR

# Paths to knowledge files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "..", "knowledge")
DISEASE_FILE = os.path.join(KNOWLEDGE_DIR, "disease_guidelines.json")
HOSPITAL_FILE = os.path.join(KNOWLEDGE_DIR, "hospital_data.json")


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_embedding_function():
    """Use sentence-transformers for embeddings (no external API key needed)."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


def seed_disease_guidelines(client: chromadb.PersistentClient):
    """Load disease guidelines from JSON and embed into ChromaDB."""
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name="disease_guidelines",
        embedding_function=ef,
        metadata={"description": "Disease treatment guidelines by type and stage"}
    )

    with open(DISEASE_FILE, "r") as f:
        data = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for disease in data["diseases"]:
        for stage_info in disease["stages"]:
            doc_text = (
                f"Disease: {disease['disease_type']}. "
                f"Stage: {stage_info['stage']}. "
                f"Description: {stage_info['description']}. "
                f"Treatments: {', '.join(stage_info['recommended_treatments'])}. "
                f"Timeline: {stage_info['timeline']}. "
                f"Notes: {stage_info['notes']}."
            )
            doc_id = f"{disease['disease_type'].replace(' ', '_')}_{stage_info['stage'].replace(' ', '_')}"
            documents.append(doc_text)
            metadatas.append({
                "disease_type": disease["disease_type"],
                "stage": stage_info["stage"],
                "hospital_type": disease["hospital_type"],
                "specialist": disease["specialist"],
                "surgery_required": str(stage_info["surgery_required"]),
                "timeline": stage_info["timeline"]
            })
            ids.append(doc_id)

    # Upsert to avoid duplicate errors on re-seed
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[ChromaDB] Seeded {len(documents)} disease guideline entries.")


def seed_hospital_summaries(client: chromadb.PersistentClient):
    """Load hospital data from JSON and embed summaries into ChromaDB."""
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name="hospital_summaries",
        embedding_function=ef,
        metadata={"description": "Hospital specialization summaries for semantic search"}
    )

    with open(HOSPITAL_FILE, "r") as f:
        data = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for hospital in data["hospitals"]:
        doc_text = (
            f"Hospital: {hospital['name']}. "
            f"Location: {hospital['location']}, {hospital['state']}. "
            f"Type: {hospital['type']}. "
            f"Specializations: {', '.join(hospital['specializations'])}. "
            f"Budget: {hospital['budget_category']}. "
            f"Rating: {hospital['rating']}. "
            f"Summary: {hospital['summary']}"
        )
        documents.append(doc_text)
        metadatas.append({
            "hospital_id": hospital["hospital_id"],
            "name": hospital["name"],
            "type": hospital["type"],
            "location": hospital["location"],
            "budget_category": hospital["budget_category"],
            "rating": str(hospital["rating"]),
            "accepts_insurance": str(hospital["accepts_insurance"])
        })
        ids.append(hospital["hospital_id"])

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[ChromaDB] Seeded {len(documents)} hospital summary entries.")


def query_disease_guidelines(query: str, n_results: int = 3) -> list[dict]:
    """Semantic search on disease guidelines collection."""
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name="disease_guidelines", embedding_function=ef
    )
    results = collection.query(query_texts=[query], n_results=n_results)
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "document": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    return output


def query_hospital_summaries(query: str, n_results: int = 5) -> list[dict]:
    """Semantic search on hospital summaries collection."""
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name="hospital_summaries", embedding_function=ef
    )
    results = collection.query(query_texts=[query], n_results=n_results)
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "document": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    return output


def initialize_chroma():
    """Main entrypoint: initialize and seed all ChromaDB collections."""
    print("[ChromaDB] Initializing persistent client...")
    client = get_chroma_client()
    print("[ChromaDB] Seeding disease guidelines...")
    seed_disease_guidelines(client)
    print("[ChromaDB] Seeding hospital summaries...")
    seed_hospital_summaries(client)
    print("[ChromaDB] Initialization complete.")


if __name__ == "__main__":
    initialize_chroma()
