import pdfplumber
import logging
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentParser:
    @staticmethod
    def extract_text_from_pdf(file_stream: BytesIO) -> str:
        """
        Extracts raw text from a PDF file stream.
        Designed to handle Streamlit's InMemoryUploadedFile objects securely
        without writing temporary files to the server's disk.
        """
        logging.info("Starting PDF text extraction...")
        extracted_text = ""
        
        try:
            # pdfplumber is chosen over PyPDF2 for its superior handling of multi-column CV layouts
            with pdfplumber.open(file_stream) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    # Append text only if the page is not empty/scanned image
                    if page_text:
                        extracted_text += page_text + "\n"
                        
            if not extracted_text.strip():
                logging.warning("Extracted text is empty. The PDF might be an image-based scan.")
            else:
                logging.info(f"PDF text extraction completed successfully. Extracted {len(extracted_text)} characters.")
                
            return extracted_text.strip()
            
        except Exception as e:
            logging.error(f"Failed to parse PDF document: {e}")
            raise

if __name__ == "__main__":
    logging.info("DocumentParser module is ready for integration.")