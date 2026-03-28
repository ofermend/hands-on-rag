import spacy

# Load a pre-trained English model
nlp = spacy.load("en_core_web_sm")

text = "Mr. Wang is a teacher. He teaches A.I. (?). Does he love his work? Of course!"
doc = nlp(text)

# Iterate over sentences
for sent in doc.sents:
    print(sent.text)