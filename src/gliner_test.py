import spacy
from gliner_spacy.pipeline import GlinerSpacy

test_file = "data/output/1. long tribunal report.txt"

# Load English tokenizer, tagger, parser, NER, and Gliner
nlp = spacy.load("en_core_web_sm")
gliner = Gliner()


def extract_addresses(text):
    doc = nlp(text)
    addresses = []
    for ent in doc.ents:
        if ent.label_ == "GPE":  # General location entities
            address = gliner.parse(ent.text)
            if address:
                addresses.append(address)
    return addresses


if __name__ == "__main__":
    text = test_file

    addresses = extract_addresses(text)
    if addresses:
        print("Addresses found:")
        for address in addresses:
            print(address)
    else:
        print("No addresses found.")
