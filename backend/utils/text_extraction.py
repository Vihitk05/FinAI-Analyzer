from transformers import AutoProcessor, AutoModelForTokenClassification
from PIL import Image
import torch
import pytesseract

# Load pre-trained LayoutLMv3 model
processor = AutoProcessor.from_pretrained("microsoft/layoutlmv3-base")
model = AutoModelForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")

def extract_data_from_image(image_path):
    image = Image.open(image_path).convert("RGB")

    try:
        # Process image with tesseract
        encoding = processor(image, return_tensors="pt", truncation=True, max_length=512)

        # Remove offset_mapping if present
        if 'offset_mapping' in encoding:
            del encoding['offset_mapping']

        # Ensure tensors are on the same device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = model(**encoding)

        # Get predictions
        predictions = torch.argmax(outputs.logits, dim=-1).squeeze().tolist()

        # Convert tokens back to words
        tokens = processor.tokenizer.convert_ids_to_tokens(encoding["input_ids"].squeeze().tolist())

        # Extract meaningful words (ignore special tokens)
        extracted_text = []
        for token, pred in zip(tokens, predictions):
            if token not in ["[CLS]", "[SEP]", "[PAD]"]:
                extracted_text.append(token)

        return " ".join(extracted_text)

    except pytesseract.pytesseract.TesseractNotFoundError:
        print("Tesseract is not installed or not in PATH")
        return ""
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return ""
