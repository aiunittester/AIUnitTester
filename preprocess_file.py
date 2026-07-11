import re
from unittest.mock import MagicMock

def extrair_imports_ts(path_arquivo: str):
    # Captura a linha inteira de import até o ";"
    padrao = re.compile(r'^\s*import\s+.*?;', re.MULTILINE)
    with open(path_arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()
    return padrao.findall(conteudo)  

def separar_imports(imports):
    internos, externos = [], []
    for imp in imports:
        if imp.startswith('.') or imp.startswith('@meuprojeto'):  # regra para internos
            internos.append(imp)
        else:
            externos.append(imp)
    return internos, externos

def gerar_mocks(internos):
    mocks = {}
    for modulo in internos:
        mocks[modulo] = MagicMock(name=modulo)
    return mocks



# print(imports)
# print('\n'.join(imports))
