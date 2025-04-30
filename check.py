import os
import pytesseract
from PIL import Image
import csv
import re

# Set Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        # Pre-processing for clearer images
        image = image.resize((image.width * 2, image.height * 2))
        image = image.convert("L")
        extracted_text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        # Remove spaces and special characters to format as a single string
        cleaned_text = re.sub(r'[^A-Za-z0-9]', '', extracted_text)
        return cleaned_text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def process_images_in_folder(folder_path, output_csv):
    image_extensions = ('.png', '.jpg', '.jpeg')
    extracted_data = []
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(folder_path, filename)
            text = extract_text_from_image(image_path)
            if text:
                extracted_data.append([filename, text])
    
    # Save extracted text to CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Image Name", "Extracted Text"])
        writer.writerows(extracted_data)
    
    print(f"Extraction completed. Results saved in {output_csv}")

if __name__ == "__main__":
    folder_path = r"D:\Helmet_Number_Recognition\Images"
    output_csv = r"D:\Helmet_Number_Recognition\extracted_text.csv"
    process_images_in_folder(folder_path, output_csv)
