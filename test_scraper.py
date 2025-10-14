"""
Script test để kiểm tra ArXiv scraper hoạt động
Chạy script này để test trước khi sử dụng với Airflow
"""

import sys
import os

# Thêm dags folder vào Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'dags'))

from arxiv_scraper import scrape_arxiv_papers, save_to_csv
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraper():
    """Test function để kiểm tra scraper hoạt động"""
    try:
        logger.info("Bắt đầu test ArXiv scraper...")
        
        # Test với query đơn giản
        query = "machine learning"
        max_results = 5  # Chỉ lấy 5 papers để test
        
        logger.info(f"Test với query: {query}, max_results: {max_results}")
        
        # Test cào dữ liệu
        papers = scrape_arxiv_papers(
            query=query,
            max_results=max_results,
            output_dir="./test_output"
        )
        
        if papers:
            logger.info(f"✅ Đã cào được {len(papers)} papers")
            
            # Hiển thị thông tin papers đầu tiên
            if len(papers) > 0:
                first_paper = papers[0]
                logger.info("📄 Paper đầu tiên:")
                logger.info(f"  - Title: {first_paper['title'][:100]}...")
                logger.info(f"  - Authors: {first_paper['authors'][:100]}...")
                logger.info(f"  - Published: {first_paper['published']}")
                logger.info(f"  - Categories: {first_paper['categories']}")
            
            # Test lưu dữ liệu
            logger.info("Test lưu dữ liệu...")
            save_to_csv(output_dir="./test_output")
            logger.info("✅ Đã lưu dữ liệu thành công")
            
        else:
            logger.warning("⚠️ Không cào được papers nào")
            
    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình test: {str(e)}")
        raise e

def test_imports():
    """Test import các modules cần thiết"""
    try:
        logger.info("Test import các modules...")
        
        import arxiv
        logger.info("✅ arxiv module imported successfully")
        
        import pandas as pd
        logger.info("✅ pandas module imported successfully")
        
        from datetime import datetime
        logger.info("✅ datetime module imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Lỗi import module: {str(e)}")
        logger.error("Hãy chạy: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    logger.info("🚀 Bắt đầu test ArXiv Scraper")
    logger.info("=" * 50)
    
    # Test imports trước
    if test_imports():
        # Test scraper
        test_scraper()
        logger.info("=" * 50)
        logger.info("✅ Test hoàn thành! Scraper hoạt động bình thường.")
        logger.info("📁 Kiểm tra thư mục ./test_output để xem kết quả")
    else:
        logger.error("❌ Test thất bại do lỗi import modules")
        sys.exit(1)

