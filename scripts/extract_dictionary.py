import os
import re
import json
import PyPDF2

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PDF = os.path.join(ROOT_DIR, "data", "petit_dictionnaire.pdf")
DEFAULT_JSON = os.path.join(ROOT_DIR, "data", "glossaire_dioula.json")

def extract_dictionary(pdf_path=DEFAULT_PDF, output_json=DEFAULT_JSON):
    reader = PyPDF2.PdfReader(pdf_path)
    glossary = {}
    
    print("Analyse du PDF en cours...")
    for i in range(10, len(reader.pages)):
        text = reader.pages[i].extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            match = re.match(r"^([A-Z][a-zàâéèêîôùûçA-Z\- \']+),\s*(.+)[.]$", line)
            if match:
                fr_word = match.group(1).strip().lower()
                dioula_word = match.group(2).strip().lower().rstrip('.')
                dioula_word = dioula_word.split(',')[0].strip()
                
                if len(fr_word) > 2:
                    glossary[fr_word] = dioula_word

    print(f"{len(glossary)} mots extraits avec succès !")
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(glossary, f, ensure_ascii=False, indent=4)
    print(f"Glossaire sauvegardé dans {output_json}")

if __name__ == "__main__":
    extract_dictionary()
