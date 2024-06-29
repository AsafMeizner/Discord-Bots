import os

current_directory = os.getcwd()

def get_truth():
    truth_file = os.path.join(current_directory,"game_night", "games", "TOD", "truth_file.txt")
    with open(truth_file, "r") as file:
        questions = file.readlines()
    return questions

def get_dare():
    dare_file = os.path.join(current_directory, "game_night", "games", "TOD", "dare_file.txt")
    with open(dare_file, "r") as file:
        questions = file.readlines()
    return questions

def get_RICE():
    rice_purity_file = current_directory + "\\game_night\\games\\RICE\\rice_purity_questions.txt"
    with open(rice_purity_file, "r", encoding="utf-8") as file:
        questions = file.readlines()
    return questions