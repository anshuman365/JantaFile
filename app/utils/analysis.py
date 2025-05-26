import re
import hashlib
import PyPDF2 # Import the main PyPDF2 module
from io import BytesIO
from docx import Document
from PIL import Image
import exifread # Used for image metadata, though not directly in the PDF fix

class DocumentAnalyzer:
    @staticmethod
    def extract_text_from_file(file_stream, filename):
        """Extract text from various document formats"""
        text = ""
        if filename.endswith('.pdf'):
            # Use PyPDF2.PdfReader instead of PdfFileReader
            reader = PyPDF2.PdfReader(file_stream)
            for page in reader.pages: # Iterate through reader.pages
                text += page.extract_text() # Use page.extract_text()
        elif filename.endswith('.docx'):
            doc = Document(file_stream)
            text = '\n'.join([para.text for para in doc.paragraphs])
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            # OCR capability placeholder
            text = "[Image content - OCR not implemented]"
        return text.strip()

    @staticmethod
    def calculate_document_hash(content):
        """Create SHA-256 hash of document content"""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def sanitize_metadata(file_stream, filename):
        """Remove metadata from files"""
        clean_content_stream = BytesIO() # Use a new BytesIO object for cleaned content
        
        if filename.endswith('.pdf'):
            # PDF metadata sanitization
            # Use PyPDF2.PdfReader and PyPDF2.PdfWriter
            reader = PyPDF2.PdfReader(file_stream)
            writer = PyPDF2.PdfWriter()
            
            for page in reader.pages: # Iterate through reader.pages
                writer.add_page(page) # Add page directly
            
            # Note: PyPDF2.PdfWriter does not have a direct removeLinks() method like PdfFileWriter did.
            # If link removal is critical, you might need to iterate through annotations
            # on each page and remove/modify link annotations.
            # For basic metadata removal, just rewriting the PDF often suffices.
            
            writer.write(clean_content_stream) # Write to the BytesIO stream
            clean_content_stream.seek(0) # Rewind the stream to the beginning
            return clean_content_stream.getvalue() # Return the bytes content
            
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            # Image metadata removal
            # exifread is imported but not used for removal, only reading.
            # This logic correctly re-saves the image without EXIF data.
            img = Image.open(file_stream)
            data = list(img.getdata()) # Get pixel data
            clean_img = Image.new(img.mode, img.size) # Create new image with same mode and size
            clean_img.putdata(data) # Put pixel data back (this effectively removes metadata)
            
            clean_image_bytes = BytesIO()
            # Ensure correct format for saving. Use 'JPEG' for .jpg/.jpeg, 'PNG' for .png
            save_format = img.format if img.format in ['PNG', 'JPEG'] else 'PNG' 
            clean_img.save(clean_image_bytes, format=save_format)
            clean_image_bytes.seek(0) # Rewind the stream
            return clean_image_bytes.getvalue() # Return the bytes content
        
        else:
            # For other file types, return the original content as bytes
            file_stream.seek(0) # Ensure stream is at the beginning
            return file_stream.getvalue()

    @staticmethod
    def find_similar_documents(text, threshold=0.8):
        """Basic text similarity check (placeholder for ML implementation)"""
        # Implementation using TF-IDF or embeddings would go here
        return []


