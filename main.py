import argparse
import sys
from datetime import datetime
import re
from sys import exit
import os

from managers.dotnet import DotnetProjectManager, DotnetTestManager
from managers.java import JavaProjectManager, JavaTestManager
from managers.node import NodeProjectManager, NodeTestManager, NodeStrykerManager, NodeJestManager
from utils import files


def find_project_root(path):
    env_project_root = os.getenv("PROJECT_WORKDIR")
    normalized_path = os.path.abspath(path)

    if env_project_root:
        normalized_project_root = os.path.abspath(env_project_root)
        if normalized_path.startswith(normalized_project_root):
            return normalized_project_root

    current = normalized_path if os.path.isdir(normalized_path) else os.path.dirname(normalized_path)
    markers = {"package.json", "tsconfig.json", ".git"}

    while current and current != os.path.dirname(current):
        if any(os.path.exists(os.path.join(current, marker)) for marker in markers):
            return current
        current = os.path.dirname(current)

    return None

def build_report_dir_name(project_root, path, start_timestamp):
    project_name = os.path.basename(os.path.normpath(project_root)) or "project"
    safe_project_name = re.sub(r"[^A-Za-z0-9._-]+", "-", project_name).strip("-") or "project"

    relative_path = path.replace(project_root, "").replace("/", "_")
    relative_suffix = f"-{relative_path}" if relative_path else ""

    return f"{safe_project_name}{start_timestamp}{relative_suffix}"

def run_main(path, language):
    if language == "java":
        if os.path.isfile(path):
            print("O caminho fornecido é um arquivo, mas o gerador de testes para Java requer um diretório de projeto.")
            exit()

        project_manager = JavaProjectManager(project_path=path, exts=[".java"])
        project_manager.compile_java_files()

        test_manager = JavaTestManager()
        paths = project_manager.paths_to_test
        test_manager.generate_unit_tests(paths=paths)
    elif language == "node":
        project_manager = NodeProjectManager(project_path=path, exts=[".js", ".ts"])

        files_paths = project_manager.paths
        project_root = find_project_root(path)
        if not project_root:
            print("Nao foi possivel determinar a raiz do projeto para o caminho fornecido.")
            exit()
        if not files_paths:
            print("Nenhum arquivo elegivel encontrado para gerar testes.")
            return
        folder_structure = project_manager.get_folder_structure(path)

        jest_manager = NodeJestManager(src_path=path)
        jest_manager.generate_jest_base_config()

        start_timestamp = datetime.now().strftime('%Y%m%d-%H-%M')
        report_dir = build_report_dir_name(project_root, path, start_timestamp)
        if not os.path.exists(f"arquivos/{report_dir}"):
            os.makedirs(f"arquivos/{report_dir}")

        jest_manager.generate_jest_config()
        jest_manager.run_jest_coverage(project_root, files_paths)
        stmts_pcts = jest_manager.parse_jest_coverage_files(f"arquivos/{report_dir}/antes", project_root, path, files_paths)
        jest_manager.run_jest_file(f"arquivos/{report_dir}/antes", project_root, files_paths, stmts_pcts)
        stryker_manager = NodeStrykerManager(report_dir=report_dir, path=path)
        test_manager = NodeTestManager(report_dir, start_timestamp, stryker_manager, jest_manager)
        test_manager.generate_unit_tests(
            paths=files_paths,
            folder_structure=folder_structure,
            project_path=path,
            root_path = project_root
        )

        jest_manager.run_jest_coverage(project_root,files_paths)
        stmts_pcts = jest_manager.parse_jest_coverage_files(f"arquivos/{report_dir}", project_root, path, files_paths)
        jest_manager.run_jest_file(f"arquivos/{report_dir}", project_root, files_paths, stmts_pcts)
        stryker_manager.run_stryker()

    elif language == "dotnet":
        if os.path.isfile(path):
            print("O caminho fornecido é um arquivo, mas o gerador de testes para .NET requer um diretório de projeto.")
            exit()
            
        project_manager = DotnetProjectManager(project_path=path, exts=[".cs"])

        project_manager.create_tests_project()

        test_manager = DotnetTestManager(paths=project_manager.paths, project_path=path, tests_project_path=project_manager.tests_project_path)

        test_manager.generate_unit_tests()
    else:
        print(f"A linguagem de programação {language} não possui suporte.")
        exit()


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("arquivos", exist_ok=True)

    # Se não houver argumentos, abre a GUI
    if len(sys.argv) == 1:
        import tkinter as tk
        from tkinter import filedialog, messagebox

        def on_run():
            path = path_var.get()
            language = language_var.get()
            if not path or not language:
                messagebox.showerror("Erro", "Preencha todos os campos.")
                return
            root.destroy()
            run_main(path, language)

        root = tk.Tk()
        root.title("Gerador de Testes")

        tk.Label(root, text="Caminho do projeto ou arquivo:").pack()
        path_var = tk.StringVar()
        tk.Entry(root, textvariable=path_var, width=40).pack()
        tk.Button(root, text="Selecionar pasta", command=lambda: path_var.set(filedialog.askdirectory())).pack()

        tk.Label(root, text="Linguagem:").pack()
        language_var = tk.StringVar()
        tk.OptionMenu(root, language_var, "java", "node", "dotnet").pack()

        tk.Button(root, text="Executar", command=on_run).pack()

        root.mainloop()
    else:
        parser = argparse.ArgumentParser(description="Gerador de testes")

        parser.add_argument("--path", type=str, required=True, help="Caminho do projeto ou arquivo")
        parser.add_argument(
            "-l",
            "--language",
            type=str,
            required=True,
            help="Linguagem de programação que serão gerados os testes",
        )
        # parser.add_argument(
        #     "-e",
        #     "--exts",
        #     type=str,
        #     nargs="+",
        #     required=True,
        #     help="Extensões de arquivos que serão gerados os testes"
        # )

        args = parser.parse_args()

        path = args.path
        language = args.language.lower()

        run_main(path, language)
