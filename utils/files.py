import os, shutil

def salvar_arquivo(file_name, content):
    with open(file_name, "r", encoding="utf-8") as arquivo:
        file_content = arquivo.readlines()

    file_content.append(f"{content}\n")

    with open(file_name, "w", encoding="utf-8") as arquivo:
        arquivo.writelines(file_content)


def read_file(file_name):
    with open(file_name, "r", encoding="utf-8") as arquivo:
        return arquivo.readlines()
    

def create_empty_file(file_name):
    with open(file_name, "w", encoding="utf-8") as arquivo:
        arquivo.write("")


def clean_reports_history(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed {file_path}: {e}')
