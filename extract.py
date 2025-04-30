import os
import pytesseract
import csv
from PIL import Image
from datetime import datetime

def extract_text_from_image(image_path):
    try:
        with Image.open(image_path) as img:
            extracted_text = pytesseract.image_to_string(img)
            
            # Remove unwanted characters
            extracted_text = extracted_text.replace('.', '').replace(',', '').replace(' ', '').replace('-', '')
            
            return extracted_text.strip()
    except Exception as e:
        print(f"Error processing image '{image_path}': {e}")
        return ''

def get_image_metadata(image_path):
    try:
        timestamp = os.path.getmtime(image_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error retrieving metadata for '{image_path}': {e}")
        return 'Unknown'

folder_path = 'number_plates'
output_csv = 'extracted_number_plates.csv'

if not os.path.exists(folder_path):
    print(f"Folder '{folder_path}' not found.")
else:
    extracted_data = []
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png')):
            image_path = os.path.join(folder_path, filename)
            extracted_text = extract_text_from_image(image_path)
            image_date_time = get_image_metadata(image_path)
            
            if extracted_text:
                extracted_data.append([filename, extracted_text, image_date_time])
                print(f"Image name: {filename}, Number plate: {extracted_text}, Date/Time: {image_date_time}")
    
    if extracted_data:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Image Name", "Number Plate", "Date/Time"])
            writer.writerows(extracted_data)
        print(f"Extracted data saved to '{output_csv}'.")
    else:
        print("No valid number plates found.")
