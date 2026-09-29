from pipeline.pipeline import process_message


message = "I ka kene?"

response = process_message(message)

print("Utilisateur :", message)
print("KOUMA AI    :", response)