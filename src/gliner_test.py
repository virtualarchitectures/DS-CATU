import spacy
from gliner_spacy.pipeline import GlinerSpacy

test_file = "data/output/1. long tribunal report.txt"

# Load English tokenizer, tagger, parser, NER, and Gliner
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("gliner_spacy", config={"labels": ["address"]})


def extract_addresses(text):
    doc = nlp(text)
    for ent in doc.ents:
        print(ent.text, ent.label_)


if __name__ == "__main__":
    f = open(test_file, "r")
    text = f.read()

    extract_addresses(text)
