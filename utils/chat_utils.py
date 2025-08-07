import random
def generate_chat_id():
    hexDig = ['1', '2', '3','4','5','6','7','8','9', 'a', 'b', 'c', 'd', 'e', 'f']
    chat_id = ""
    for i in range(16):
        chat_id += random.choices(hexDig, k=1)[0]
    return chat_id