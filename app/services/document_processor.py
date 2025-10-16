from typing import List, Dict
import logging
from pypdf import PdfReader
import uuid
from datetime import datetime
import os
from ..utils.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles PDF document processing and text extraction"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def chunk_text(self, text: str) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to be chunked
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunk = {
                    "id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "chunk_index": len(chunks),
                    "word_count": len(chunk_words)
                }
                chunks.append(chunk)
            
            # Break if we've reached the end
            if i + self.chunk_size >= len(words):
                break
        
        return chunks
    
    def process_document(self, file_path: str, filename: str) -> Dict:
        """
        Process a PDF document: extract text and create chunks
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Dictionary containing document info and chunks
        """
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(file_path)
            
            if not text.strip():
                raise Exception("No text content found in PDF")
            
            # Create chunks
            chunks = self.chunk_text(text)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document metadata
            document_info = {
                "id": str(uuid.uuid4()),
                "filename": filename,
                "file_path": file_path,
                "size": file_size,
                "upload_time": datetime.now(),
                "chunk_count": len(chunks),
                "status": "processed",
                "full_text": text,
                "chunks": chunks
            }
            
            logger.info(f"Successfully processed document {filename}: {len(chunks)} chunks created")
            return document_info
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise Exception(f"Failed to process document: {str(e)}")
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate if the file is a valid PDF
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                # Check PDF header
                header = file.read(4)
                if header != b'%PDF':
                    return False
            
            # Try to read with pypdf
            reader = PdfReader(file_path)
            if len(reader.pages) == 0:
                return False
                
            return True
            
        except Exception as e:
            logger.warning(f"PDF validation failed for {file_path}: {str(e)}")
            return False
