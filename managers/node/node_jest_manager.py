import os
import shutil
import subprocess
import re
from sys import exit
from prompts import (
    JEST_CONFIG,
    JEST_BASE_CONFIG
)
from datetime import datetime
from utils import read_file
from pathlib import Path
from bs4 import BeautifulSoup

from logging_config import main_logger

class NodeJestManager():
    def __init__(
        self,
        src_path: str
    ):
        self.src_path = src_path
        self.files_to_ignore = [
            '\\.d\\.ts$', 
            '/node_modules/', 
            '/dist/', 
            '/tests/',
            '/failed_tests/',
            '/migrations/',
            'main\\.ts$',
            'main\\.js$',
            '\\.config\\.ts$',
            '\\.config\\.js$',
            '\\.module\\.ts$',
            '\\.module\\.js$',
            '\\-config\\.ts$',
            '\\-config\\.js$',
            '\\.entity\\.ts$',
            '\\.entity\\.js$',
            '\\.dto\\.ts$',
            '\\.dto\\.js$',
            '\\-swagger\\.ts$',
            '\\-swagger\\.js$',
            "\\.interface\\.ts$",
            "\\.interface\\.js$",
            "\\.interface\\.spec\\.ts$",
            "\\.interface\\.spec\\.js$"
        ]

    def get_jest_config_path(self) -> str:
        path_parts = self.src_path.split(os.sep)

        if "src" in path_parts:
            src_index = path_parts.index("src")
            root_path = os.sep.join(path_parts[:src_index])
            return os.path.join(root_path, "jest.config.js")

        return os.path.join(self.find_root_path(), "jest.config.js")

    def generate_jest_config(self) -> None:
        output_path = self.get_jest_config_path()

        jest_config_file = JEST_CONFIG.format(files_to_ignore=self.files_to_ignore)

        with open(output_path, "w+", encoding="utf-8") as f:
            f.write(jest_config_file)

        print(f"Configuração do Jest gerada em {output_path} com {len(self.files_to_ignore)} caminhos para ignorar.")
        main_logger.info("Configuração do Jest gerada em %s com %s caminhos para ignorar.", output_path, len(self.files_to_ignore))

    def generate_jest_base_config(self):
        output_path = self.get_jest_config_path()

        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.files_to_ignore = content["filesToIgnore"] if "filesToIgnore" in content else self.files_to_ignore

        with open(output_path, "w+", encoding="utf-8") as f:
            f.write(JEST_BASE_CONFIG)

        print(f"Configuração base do Jest gerada em {output_path}.")
        main_logger.info("Configuração base do Jest gerada em %s.", output_path)

    def find_root_path(self) -> str:
        current_path = self.src_path

        found = False

        while not found:
            if os.path.exists(os.path.join(current_path, "package.json")):
                found = True
                return current_path
            
            parent_path = os.path.dirname(current_path)

            if parent_path == current_path:
                break
            
            current_path = parent_path

        return self.src_path
    
    # rodar os testes para gerar o coverage report
    def run_jest_coverage(self, root_path, files_paths):
        print("Building jest coverage for all project, with node ./node_modules/jest/bin/jest.js")
        
        if os.path.exists(f"{root_path}/coverage"):
            shutil.rmtree(f"{root_path}/coverage")
        
        files_to_collect = ""
        files_to_test = ""
        for f in files_paths:
            file_name = Path(f).name
            file_path_rel = (os.path.relpath(f, f"{root_path}/src")).replace(".ts",'')
            files_to_collect += f"**/{file_name},"
            files_to_test += f"{file_path_rel}"
        jest_config_rel = os.path.relpath(self.get_jest_config_path(), root_path)
        command = [
            "bash", "-lc", #linux
            f"cd {root_path} && node ./node_modules/jest/bin/jest.js --config {jest_config_rel} {files_to_test} --coverage --collectCoverageFrom=\"{{{files_to_collect}}}\" --no-cache"]
        print(command)

        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        print("Built jest coverage")
        
        return

    #rodar testes por arquivo
    def run_jest_file(self, report_path, root_path, files_paths, stmts_cov):
        try:
            os.mkdir(report_path)
        except:
            print(f"report {report_path} already exists")
        timestamp = datetime.now().strftime('%Y%m%d-%H-%M')
        report = f"Files state, generated at {timestamp}\n"
        total_files = len(files_paths)
        report += f"Building test files execution for {total_files} files\n"
        report += f"Initial files statement coverage:\n{stmts_cov}\n\n"
        print(f"Building test files execution for {total_files} files")
        for i, p in enumerate(files_paths):
            p = p.removesuffix(".ts")
            print(f"    File {p}")
            report += f"File {i+1}/{total_files}: {p}\n"
            jest_config_rel = os.path.relpath(self.get_jest_config_path(), root_path)
            command = [
                "bash", "-lc", #linux
                f"cd {root_path} && node ./node_modules/jest/bin/jest.js --config {jest_config_rel} {p}"
            ]

            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
            report += f"Output:\n{result.stderr}\n"
        
        print("Built test files execution")
        with open(f"{report_path}/jest.txt", "w", encoding="utf-8") as f:
            f.write(report)

        return

    # parte dos anexos a serem enviados no email
    #TODO: algumas coisas talvez não sejam mais necessárias
    # com o novo comando que roda no run_jest_coverage
    # precisa ver com calma se tem algo aqui que não faz sentido
    # tipo limpar o index e coisas assim, acho que não precisa mais
    def parse_jest_coverage_files(self, report_path, root_path, main_path, files_paths):
        # pegar os arquivos gerados durante a verificação do jest 
        # limpar o html para deixar só o que foi testado de fato
        if os.path.exists(f"{report_path}/jest-coverage"):
            shutil.rmtree(f"{report_path}/jest-coverage")
        if not os.path.exists(f"{root_path}/coverage"):
            return -1
        shutil.copytree(f"{root_path}/coverage", f"{report_path}/jest-coverage")
        match = re.search(r"^.*?\bsrc\b", main_path)
        if match:
            root_path_src = match.group(0)
        else:
            print("O caminho fornecido não está no formato '{root_path}/src/{file_path}'.")
            exit()

        
        files_names = []
        files_pct = {}
        for p in files_paths:
            rel = os.path.relpath(p, root_path).replace("\\", "/")
            files_names.append(Path(p).name)
            d = {"statements": 0.0, "branches": 0.0}
            files_pct[Path(p).name] = d

        with open(f"{report_path}/jest-coverage/index.html", encoding="utf-8") as f:
            html_og = f.read()

        pattern = re.compile(r"<tr>.*?</tr>", re.DOTALL)

        filtered_rows = []
        for tr_block in pattern.findall(html_og):
            m = re.search(r'data-value="([^"]+)"', tr_block)
            if not m:
                continue
            data_value = m.group(1)
            if data_value in files_names: 
                filtered_rows.append(tr_block)

        html_new = re.sub(
            r"(<tbody>).*?(</tbody>)",
            lambda m: f"{m.group(1)}{''.join(filtered_rows)}{m.group(2)}",
            html_og,
            flags=re.DOTALL
        )

        with open(f"{report_path}/jest-coverage/index.html", "w", encoding="utf-8") as f:
            f.write(html_new)
        
        #remover os diretórios e arqvuios de /src que não foram testados
        allowed_relatives = [
            os.path.relpath(p, rf"{root_path_src}").replace("\\", "/") for p in files_paths
        ]
        main_path_rel = os.path.relpath(main_path, rf"{root_path_src}").replace("\\", "/")
        if "." in os.path.basename(main_path_rel):
            main_path_rel = os.path.dirname(main_path_rel).replace("\\", "/")

        allowed_dirs = []
        for rel in allowed_relatives:
            parts = rel.split("/")
            a = []
            for i in range(1, len(parts)):
                a.append("/".join(parts[:i]))
            allowed_dirs.append(a)
        
        dir_path = f"{report_path}/jest-coverage/"
        for root, _, files in os.walk(dir_path):

            for f in files:
                if f.replace(".html","") in files_names:
                    #TODO: deve ter um jeito de pegar as linhas que estão com problema, não é possível
                    with open(f"{root}/{f}", encoding="utf-8") as file:
                        html_og = file.read()

                    soup = BeautifulSoup(html_og, 'html.parser')
                    div = soup.find('div', class_='pad1')
                    # get statements
                    stmts_span = div.find('span', string='Statements')
                    stmts_span = stmts_span.find_previous_sibling('span', class_='strong')
                    stmts_str = stmts_span.get_text(strip=True).replace("%","")
                    stmts_float = float(stmts_str)
                    # get branches
                    brnc_span = div.find('span', string='Branches')
                    brnc_span = brnc_span.find_previous_sibling('span', class_='strong')
                    brnc_str = brnc_span.get_text(strip=True).replace("%","")
                    brnc_float = float(brnc_str)
                    # file dict
                    d = {"statements": stmts_float, "branches": brnc_float}
                    files_pct[f.replace(".html","")] = d

        return files_pct

    def get_uncovered_branches(self, report_path, file_name, limit=20):
        html_path = f"{report_path}/jest-coverage/{file_name}.html"
        if not os.path.exists(html_path):
            return []

        with open(html_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        uncovered = []
        selectors = [".missing-if-branch", ".cbranch-no"]
        for marker in soup.select(", ".join(selectors)):
            line = marker.find_parent("span", class_="cline-any")
            if not line:
                line = marker.find_parent("td")

            text = line.get_text(" ", strip=True) if line else marker.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            if text and text not in uncovered:
                uncovered.append(text)

            if len(uncovered) >= limit:
                break

        return uncovered
