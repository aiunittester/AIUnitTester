import os
import json
from pathlib import Path
import shutil
import shlex

from prompts import (
    STRYKER_CONFIG
)
import subprocess

from utils import (
    salvar_arquivo,
    create_empty_file
)

from logging_config import main_logger

class NodeStrykerManager():
    
    def __init__(self, report_dir:str, path:str):
        self.report_dir = f"arquivos/{report_dir}/stryker"
        if not os.path.exists(self.report_dir):
            os.mkdir(self.report_dir)
        self.root_path = self.find_stryker_root(Path(path))
        self.file = f"{self.report_dir}/stryker.txt"
        create_empty_file(self.file)
        
        # gerar config do stryker
        files_to_mutate = []
        
        self.project_root = self.find_root(self.root_path)
        schema_abs = f"{self.project_root}/node_modules/@stryker-mutator/core/schema/stryker-schema.json"
        schema_rel = os.path.relpath(schema_abs, self.root_path)

        config = STRYKER_CONFIG.format(mutate=files_to_mutate,schema=schema_rel).replace("'", '"')
        self.config_file = f"stryker.{self.root_path.name}.config.json"
        self.config_path = os.path.join(self.root_path, self.config_file)
        
        with open(self.config_path, "w+", encoding="utf-8") as f:
            json.dump(json.loads(config), f, indent=2)
        
        l = f"Configuração do Stryker gerada em {self.config_path} com {len(files_to_mutate)} arquivos mutáveis.\n"
        print(l)
        salvar_arquivo(self.file, l)

    def add_file_to_mutate(self, file_to_mutate:str) -> None:
        rel_path = os.path.relpath(file_to_mutate, self.project_root)
        salvar_arquivo(self.file, f"Adicionando arquivo {rel_path} na lista de mutação")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["mutate"].append(rel_path)

        with open(self.config_path, "w", encoding="utf-8") as f:    
            json.dump(config, f, indent=2)
    
        len_mutate = len(config["mutate"])
        r = f"    Configuração do Stryker alterada com {len_mutate} arquivos mutáveis."
        print(r)
        salvar_arquivo(self.file, r)

    def build_stryker_command(self, config_relative_path: str) -> str:
        local_bin = Path(self.project_root) / "node_modules" / ".bin" / "stryker"
        legacy_runner = Path(self.project_root) / "node_modules" / "@stryker-mutator" / "core" / "bin" / "stryker.js"
        quoted_config = shlex.quote(config_relative_path)

        if local_bin.exists():
            return f"{shlex.quote(str(local_bin))} run {quoted_config} --logLevel debug --fileLogLevel trace"

        if legacy_runner.exists():
            return f"node {shlex.quote(str(legacy_runner))} run {quoted_config} --logLevel debug --fileLogLevel trace"

        return f"npx --no-install stryker run {quoted_config} --logLevel debug --fileLogLevel trace"
    
    def run_stryker(self) -> None:
        if self.get_total_mutants() == 0:
            salvar_arquivo(self.file, f"Não há arquivos para mutação no arquivo de config {self.config_path}")
            return
        
        if os.path.exists(f"{self.project_root}/stryker.log"):
            os.remove(f"{self.project_root}/stryker.log")
        if os.path.exists(f"{self.project_root}/reports"):
            shutil.rmtree(f"{self.project_root}/reports")

        l = f"\nExecutando Stryker com {self.get_total_mutants()} arquivos para mutação:\n    {self.get_mutants()}"
        print(l)
        salvar_arquivo(self.file, l)
        
        rel = os.path.relpath(self.config_path, self.project_root)
        stryker_command = self.build_stryker_command(rel)
        command = [
            "bash", "-lc", #linux
            f"cd {shlex.quote(str(self.project_root))} && {stryker_command}",
        ]
        salvar_arquivo(self.file, f"\nComandos executados:\n{command}\n")

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors='ignore'
        )
        salvar_arquivo(self.file, f"\nExecução finalizada com código {result.returncode}\n    Erro: {result.stderr}")
        if result.returncode != 0 and "npx canceled due to missing packages and no YES option" in result.stderr:
            salvar_arquivo(
                self.file,
                "\nStryker nao foi executado porque o binario local nao foi encontrado. "
                "Instale a dependencia '@stryker-mutator/core' no projeto para habilitar essa etapa."
            )
        if os.path.exists(f"{self.project_root}/reports"):
            shutil.copytree(
                f"{self.project_root}/reports",
                f"{self.report_dir}/reports"
            )
        stryker_log_path = f"{self.project_root}/stryker.log"
        if os.path.exists(stryker_log_path):
            shutil.copy(
                stryker_log_path,
                f"{self.report_dir}/stryker.log"
            )
            salvar_arquivo(self.file, f"\nLog detalhado salvo em {self.report_dir}/stryker.log")
        else:
            salvar_arquivo(self.file, f"\nStryker finalizou sem gerar arquivo de log em {stryker_log_path}")

    def get_total_mutants(self) -> int:
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return len(config["mutate"])

    def get_mutants(self) -> list:
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config["mutate"]
    
    def find_stryker_root(self, path:Path) -> Path:
        if path.is_file():
            current = path.parent
        else:
            current = path

        while True:
            if current.parent.name == "src":
                break
            if any(current.glob("*.module.ts")):
                return current
            current = current.parent

        return current
    
    def find_root(self, path: Path) -> Path:
        env_project_root = os.getenv("PROJECT_WORKDIR")
        if env_project_root:
            return Path(env_project_root).resolve()

        current = path.resolve()
        markers = ("package.json", "tsconfig.json", ".git")

        while True:
            if any((current / marker).exists() for marker in markers):
                return current

            if current.parent == current:
                break

            current = current.parent

        raise RuntimeError(f"Nao foi possivel determinar a raiz do projeto para {path}")
