import tempfile
import re
import pyocr
import fitz
from pdf2image import convert_from_path


class PdfContentReader:
    @staticmethod
    def ocr_pdf_content(file_path):
        """
        Extract text content from PDF file.
        :param file_path:
        :return: pdf text content
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(file_path, output_folder=temp_dir)

            # Initialize OCR tool
            tool = pyocr.get_available_tools()[0]
            lang = tool.get_available_languages()[0]

            # Extract text content from each image
            content_list = []
            for img in images:
                txt = tool.image_to_string(
                    img,
                    lang=lang,
                    builder=pyocr.builders.TextBuilder(),
                )
                new_txt = re.sub(r'\s{2,}', ' ', txt)  # Replace multiple spaces with a single space
                content_list.append(new_txt)

            # Merge all text content and return
            return ''.join(content_list)

    @staticmethod
    def get_pdf_content(file_path):
        """
        Extracts text content from a PDF file using PyMuPDF (fitz) library.
        Args:
            file_path (str): The path to the PDF file to extract text from.
        Returns:
            str: A string representing the text content of the PDF file.
        """
        with fitz.open(file_path) as pdf:
            file_content = ""
            for page in pdf:
                # Judging the length of the word count of the PDF file page ,Please modify according to your actual situation!
                if len(page.get_text()) <= 48:
                    print(
                        f"{file_path}The resume is in picture format and the OCR is being used to recognize the content. Please wait....")
                    file_content = ocr_pdf_content(file_path)
                    print(file_content)
                else:
                    file_content += page.get_text()
                    lprint\
                        (file_content)
        return file_content
