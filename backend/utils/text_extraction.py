import os
import torch
from transformers import AutoProcessor, AutoModelForTokenClassification
from PIL import Image
import pytesseract
from multiprocessing import Pool
from pdf2image import convert_from_path  # To extract images from PDFs

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load pre-trained LayoutLMv3 model
processor = AutoProcessor.from_pretrained("microsoft/layoutlmv3-base")
model = AutoModelForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")

# Move model to GPU if available & use FP16 for speed
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device).half()
model.eval()

def extract_data_from_image(image_path):
    """Extracts text from a single image using Tesseract and LayoutLMv3."""
    image = Image.open(image_path).convert("RGB")
    
    # Resize for faster processing (optional)
    image = image.resize((image.width // 2, image.height // 2))

    try:
        # 1. Try OCR (Tesseract) first - faster method
        ocr_text = pytesseract.image_to_string(image)
        if len(ocr_text.strip()) > 20:  # If OCR works, return early
            return ocr_text

        # 2. Process image with LayoutLMv3
        encoding = processor(image, return_tensors="pt", truncation=True, max_length=512)
        encoding.pop('offset_mapping', None)  # Remove if present
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            with torch.cuda.amp.autocast():  # Mixed precision for speed
                outputs = model(**encoding)

        # Get predictions
        predictions = torch.argmax(outputs.logits, dim=-1).squeeze().tolist()
        tokens = processor.tokenizer.convert_ids_to_tokens(encoding["input_ids"].squeeze().tolist())

        # Extract meaningful words (ignore special tokens)
        extracted_text = [token for token, pred in zip(tokens, predictions) if token not in ["[CLS]", "[SEP]", "[PAD]"]]

        return " ".join(extracted_text)

    except pytesseract.pytesseract.TesseractNotFoundError:
        print("Tesseract is not installed or not in PATH")
        return ""
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return ""

def process_page(image_path):
    """Helper function for multiprocessing."""
    return extract_data_from_image(image_path)

def extract_data_from_pdf(pdf_path, output_dir="pdf_images", num_workers=4):
    """Converts a PDF into images and extracts text using multiprocessing."""
    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF pages to images
    images = convert_from_path(pdf_path, dpi=200)  # Reduce DPI for speed

    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i + 1}.png")
        image.save(image_path, "PNG")
        image_paths.append(image_path)

    # Process images in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_page, image_paths)

    return "\n".join(results)