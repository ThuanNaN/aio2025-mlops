import arxiv
import pandas as pd
import os
from datetime import datetime
import logging
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_arxiv_papers(query="machine learning", max_results=50, output_dir="/tmp/arxiv_data"):
    """
    Args:
        query (str): Search query
        max_results (int): Maximum number of papers
        output_dir (str): Folder to save data (not used in this function)
    
    Returns:
        list: List of papers (will be stored in XCom)
    """
    try:
        logger.info(f"Start scraping data with query: {query}")
        logger.info(f"Target folder: {output_dir}")
        
        # Init client
        client = arxiv.Client()
        
        # Create query object
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        
        # Get papers
        for result in client.results(search):
            paper_info = {
                'id': result.entry_id,
                'title': result.title,
                'authors': ', '.join([author.name for author in result.authors]),
                'abstract': result.summary,
                'published': result.published.strftime('%Y-%m-%d'),
                'updated': result.updated.strftime('%Y-%m-%d'),
                'categories': ', '.join(result.categories),
                'pdf_url': result.pdf_url,
                'doi': result.doi if hasattr(result, 'doi') else None,
                'comment': result.comment if hasattr(result, 'comment') else None,
                'journal_ref': result.journal_ref if hasattr(result, 'journal_ref') else None,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            papers.append(paper_info)
            
        logger.info(f"✅ Successfully scraped {len(papers)} papers")
        logger.info(f"📤 Returning data via XCom to next task")
        
        # Return data - Airflow will automatically store in XCom
        return papers
        
    except Exception as e:
        logger.error(f"Error scraping data: {str(e)}")
        raise e

def save_to_csv(ti, output_dir="/tmp/arxiv_data"):
    """
    Save papers to CSV file.
    Receives cleaned data from previous task via XCom.
    
    Args:
        ti: TaskInstance object (automatically provided by Airflow)
        output_dir (str): Folder to save CSV file
    """
    try:
        logger.info("Pulling cleaned data from previous task via XCom...")
        
        # Get cleaned data from previous task via XCom
        papers = ti.xcom_pull(task_ids='clean_data')
        
        if not papers:
            logger.warning("⚠️ No data to save")
            return
        
        logger.info(f"✅ Received {len(papers)} papers from XCom")
        
        # Create folder if not exists
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"📁 Output directory: {output_dir}")
        
        # Create DataFrame
        df = pd.DataFrame(papers)
        
        # Create file name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"arxiv_papers_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Saved {len(papers)} papers to file: {filepath}")
        
        # Create summary file
        summary_file = os.path.join(output_dir, f"summary_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"ArXiv Papers Scraping Summary\n")
            f.write(f"============================\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Number of papers: {len(papers)}\n")
            f.write(f"File CSV: {filename}\n")
            f.write(f"\nList of categories:\n")
            
            # Statistics categories
            all_categories = []
            for paper in papers:
                if paper['categories']:
                    all_categories.extend(paper['categories'].split(', '))
            
            from collections import Counter
            category_counts = Counter(all_categories)
            for category, count in category_counts.most_common(10):
                f.write(f"- {category}: {count} papers\n")
        
        logger.info(f"📊 Created summary file: {summary_file}")
        logger.info(f"✅ All files saved successfully!")
        
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise e

def clean_string(text):
    """
    Clean and normalize string data.
    
    Args:
        text (str): Input string
        
    Returns:
        str: Cleaned string
    """
    if not text or text == 'None':
        return None
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text if text else None


def clean_paper_data(ti):
    """
    Clean and process paper data.
    Removes duplicates, normalizes strings, handles missing values.
    Receives data from previous task via XCom.
    
    Args:
        ti: TaskInstance object (automatically provided by Airflow)
        
    Returns:
        list: Cleaned list of papers (will be stored in XCom)
    """
    try:
        logger.info("Getting paper data...")
        
        # Get data from previous task via XCom
        papers = ti.xcom_pull(task_ids='scrape_arxiv_papers')
        
        if not papers:
            logger.warning("Not have data to clean")
            return []
        
        logger.info(f"Starting data cleaning with {len(papers)} papers...")
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(papers)
        
        # 1. Remove duplicates based on paper ID
        original_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='first')
        duplicates_removed = original_count - len(df)
        if duplicates_removed > 0:
            logger.info(f" Removed {duplicates_removed} duplicate papers")
        
        # 2. Clean string fields
        string_fields = ['title', 'authors', 'abstract', 'categories', 'comment', 'journal_ref']
        for field in string_fields:
            if field in df.columns:
                df[field] = df[field].apply(lambda x: clean_string(str(x)) if pd.notna(x) else None)

        logger.info(f" Normalized text fields")

        # 3. Handle missing values
        # Replace empty strings with None
        df = df.replace('', None)
        df = df.replace('None', None)
        
        # 4. Validate URLs
        url_pattern = re.compile(r'^https?://')
        if 'pdf_url' in df.columns:
            invalid_urls = ~df['pdf_url'].apply(lambda x: bool(url_pattern.match(str(x))) if pd.notna(x) else True)
            if invalid_urls.any():
                logger.warning(f" Found {invalid_urls.sum()} invalid PDF URLs, setting to None")
                df.loc[invalid_urls, 'pdf_url'] = None
        
        # 5. Ensure consistent date format
        date_fields = ['published', 'updated']
        for field in date_fields:
            if field in df.columns:
                df[field] = pd.to_datetime(df[field], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 6. Remove papers with missing critical fields
        critical_fields = ['id', 'title']
        before_filter = len(df)
        df = df.dropna(subset=critical_fields)
        removed = before_filter - len(df)
        if removed > 0:
            logger.warning(f" Removed {removed} papers missing critical fields")
        
        # 7. Add data quality flag
        df['data_quality'] = 'good'
        missing_abstract = df['abstract'].isna()
        if missing_abstract.any():
            df.loc[missing_abstract, 'data_quality'] = 'missing_abstract'
        
        # Convert back to list of dictionaries
        cleaned_papers = df.to_dict('records')
        
        logger.info(f"✅ Data cleaning completed. Cleaned papers: {len(cleaned_papers)}")
        logger.info(f"📊 Statistics:")
        logger.info(f"  - Original papers: {original_count}")
        logger.info(f"  - Cleaned papers: {len(cleaned_papers)}")
        logger.info(f"  - Removed: {original_count - len(cleaned_papers)}")

        return cleaned_papers
        
    except Exception as e:
        logger.error(f"Error cleaning data: {str(e)}")
        raise e


def get_mongodb_connection():
    """
    Create and return MongoDB connection.
    
    Returns:
        MongoClient: MongoDB client instance
    """
    try:
        # MongoDB connection string
        # Use container name 'mongodb' when running in Docker
        mongo_uri = "mongodb://admin:admin123@mongodb:27017/"
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        logger.info("✅ MongoDB connection successful!")
        
        return client
        
    except ConnectionFailure as e:
        logger.error(f"❌ Cannot connect to MongoDB: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {str(e)}")
        raise e


def save_to_mongodb(ti, db_name="arxiv_db", collection_name="papers"):
    """
    Save cleaned papers to MongoDB.
    Receives data from previous task via XCom.
    
    Args:
        ti: TaskInstance object (automatically provided by Airflow)
        db_name (str): Database name
        collection_name (str): Collection name
    """
    try:
        logger.info("📥 Fetching data from previous task via XCom...")
        
        # Get cleaned data from previous task
        papers = ti.xcom_pull(task_ids='clean_data')
        
        if not papers:
            logger.warning("⚠ No data to save to MongoDB")
            return

        logger.info(f"✅ Received {len(papers)} papers from XCom")

        # Connect to MongoDB
        client = get_mongodb_connection()
        db = client[db_name]
        collection = db[collection_name]
        
        # Create unique index on paper ID to prevent duplicates
        collection.create_index("id", unique=True)
        
        # Insert papers
        inserted_count = 0
        updated_count = 0
        duplicate_count = 0
        
        for paper in papers:
            try:
                # Try to insert
                collection.insert_one(paper)
                inserted_count += 1
            except DuplicateKeyError:
                # If duplicate, update existing document
                try:
                    result = collection.replace_one(
                        {'id': paper['id']},
                        paper,
                        upsert=True
                    )
                    if result.modified_count > 0:
                        updated_count += 1
                    else:
                        duplicate_count += 1
                except Exception as e:
                    logger.warning(f" Error updating paper {paper['id']}: {str(e)}")

        logger.info(f"💾 Data saved to MongoDB:")
        logger.info(f"  - Database: {db_name}")
        logger.info(f"  - Collection: {collection_name}")
        logger.info(f"  - Papers added: {inserted_count}")
        logger.info(f"  - Papers updated: {updated_count}")
        logger.info(f"  - Papers skipped (duplicates): {duplicate_count}")
        logger.info(f"  - Total papers in collection: {collection.count_documents({})}")

        # Close connection
        client.close()
        logger.info("✅ Data saved to MongoDB successfully!")

    except Exception as e:
        logger.error(f"❌ Error saving to MongoDB: {str(e)}")
        raise e


def get_paper_details(paper_id):
    """
    Get details of a specific paper
    
    Args:
        paper_id (str): ID of paper (example: '2301.00001')
    
    Returns:
        dict: Details of paper
    """
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id])
        
        for result in client.results(search):
            return {
                'id': result.entry_id,
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'abstract': result.summary,
                'published': result.published,
                'updated': result.updated,
                'categories': result.categories,
                'pdf_url': result.pdf_url,
                'doi': result.doi if hasattr(result, 'doi') else None,
            }
    except Exception as e:
        logger.error(f"Error getting details of paper {paper_id}: {str(e)}")
        return None
