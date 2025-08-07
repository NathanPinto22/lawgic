from transformers import (
    DistilBertTokenizerFast,
    DistilBertForQuestionAnswering,
    pipeline
)

def run():
    model_path = "../pyProcessing/models/legal-distilbert"

    # Explicitly load model and tokenizer from local path
    tokenizer = DistilBertTokenizerFast.from_pretrained(model_path, local_files_only=True)
    model = DistilBertForQuestionAnswering.from_pretrained(model_path, local_files_only=True)

    # Create QA pipeline
    qa = pipeline("question-answering", model=model, tokenizer=tokenizer)

    sample_context = """Power of Government to declare certain monuments, etc. to be protected
monuments or areas.— (1) Where the Government is of opinion that any ancient
monument or archaeological site and remains, which has not been declared by or under
law made by Parliament to be of national importance, requires protection under this Act,
it may, by notification, give two months‟ notice of its intention to declare such ancient
monument or archaeological site and remains to be protected monument or a protected
area, as the case may be, and a copy of every such notification shall be affixed in a
conspicuous place near the monument or the site and remains, as the case may be.
(2) Any person interested in any such ancient and historical monument or
archaeological site and remains may, within two months after the issue of the notification
under sub-section (1), object to the declaration of the monument or the archaeological
site and remains to be a protected monument or a protected area."""

    question = "What is an archaeological monument"
    response = qa(question=question, context=sample_context)

    print("Q:", question)
    print("A:", response["answer"])

if __name__ == "__main__":
    run()

