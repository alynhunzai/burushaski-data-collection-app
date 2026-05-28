import os
import uuid
from datasets import load_dataset
from dotenv import load_dotenv

# Import your existing database architecture
from database import SessionLocal
from models import SourceSentence

# Load cloud connection strings from your local .env file
load_dotenv()

def populate_flores():
    """
    Fetches the FLORES-200 English evaluation evaluation strings.
    Contains exactly 3,001 universally standard benchmark sentences.
    """
    print("🛰️ Loading FLORES-200 English dataset from Hugging Face...")
    # 'eng_Latn' specifies the standard English text split
    dataset = load_dataset("facebook/flores", "eng_Latn", trust_remote_code=True)
    
    # Combine sentences from standard dev and devtest evaluation sets
    dev_sentences = dataset["dev"]["sentence"]
    devtest_sentences = dataset["devtest"]["sentence"]
    
    # Deduplicate text blocks
    all_sentences = list(set(dev_sentences + devtest_sentences))
    
    print(f"📋 Found {len(all_sentences)} unique FLORES-200 sentences. Processing...")
    insert_sentences(all_sentences, "FLORES-200")


def populate_tatoeba(limit=3000):
    """
    Extracts high-quality conversational text slices from the Tatoeba database.
    Applies strict word constraints to guarantee optimal mobile crowdsourcing.
    """
    print("🛰️ Loading Tatoeba English dataset from Hugging Face...")
    dataset = load_dataset("agentlans/tatoeba-english-translations", split="train", trust_remote_code=True)
    
    print(f"🧹 Filtering clean conversational sentences (Target limit: {limit})...")
    filtered_sentences = []
    
    for row in dataset:
        text = row["English"].strip()
        word_count = len(text.split())
        
        # QUALITY FILTER CRITERIA: 
        # Sentences between 4 and 12 words prevent translation fatigue.
        # Excluding questions initially keeps the target baseline sentences uniform.
        if 4 <= word_count <= 12 and not text.endswith("?"):
            filtered_sentences.append(text)
            
        if len(filtered_sentences) >= limit:
            break
            
    insert_sentences(filtered_sentences, "Tatoeba")


def insert_sentences(sentence_list, dataset_name):
    """
    Handles robust batch insertion directly into the target SQL database.
    """
    db = SessionLocal()
    batch_size = 500  # Limits connection overhead on serverless nodes
    added_count = 0
    
    try:
        for text in sentence_list:
            text = text.strip()
            
            # 1. Idempotency Check: Prevent duplicate string processing
            exists = db.query(SourceSentence).filter(SourceSentence.text == text).first()
            if exists:
                continue
                
            # 2. Build model object adhering strictly to your schema configurations
            sentence = SourceSentence(
                id=uuid.uuid4(),
                text=text,
                language="English",
                is_active=True
            )
            db.add(sentence)
            added_count += 1
            
            # 3. Batch commit to safely persist rows without database timeouts
            if added_count % batch_size == 0:
                db.commit()
                print(f"💾 Progress: Committed {added_count} records to database...")
                
        # Commit remaining records
        db.commit()
        print(f"🎉 Success! Populated database with {added_count} source sentences from {dataset_name}.")
        
    except Exception as e:
        print(f"❌ Transaction failure encountered: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # TOGGLE HARVEST MODE: Uncomment the dataset strategy you want to ingest
    
    # populate_flores()
    populate_tatoeba(limit=3000)