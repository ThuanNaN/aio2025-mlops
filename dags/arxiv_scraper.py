import arxiv
import pandas as pd
import os
from datetime import datetime
import logging

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_arxiv_papers(query="machine learning", max_results=50, output_dir="/tmp/arxiv_data"):
    """
    Scrape papers from ArXiv API and return the list.
    Data will be passed to next task via XCom.
    
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
        logger.error(f"❌ Error scraping data: {str(e)}")
        raise e

def save_to_csv(ti, output_dir="/tmp/arxiv_data"):
    """
    Save papers to CSV file.
    Receives data from previous task via XCom.
    
    Args:
        ti: TaskInstance object (automatically provided by Airflow)
        output_dir (str): Folder to save CSV file
    """
    try:
        logger.info("📥 Pulling data from previous task via XCom...")
        
        # Get data from previous task via XCom
        papers = ti.xcom_pull(task_ids='scrape_arxiv_papers')
        
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
        
        logger.info(f"💾 Saved {len(papers)} papers to file: {filepath}")
        
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
        logger.error(f"❌ Error saving data: {str(e)}")
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

# Note: No longer using global variables.
# Data is passed between tasks via Airflow XCom mechanism.

