import os
import re
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from subprocess import CompletedProcess
from typing import List

from clients import OpenAIClient
from preprocess_file import extrair_imports_ts, separar_imports
from prompts import (
    FIX_FILE_USER_NODE,
    GENERATE_TESTS_SYSTEM_NODE,
    GENERATE_TESTS_USER_NODE,
    VALIDATE_EXISTING_TEST,
    INCREASE_JEST_COVERAGE_USER_NODE
)
from logging_config import main_logger
from utils import (
    salvar_arquivo,
    create_empty_file
)

class NodeTestManager:
    def __init__(self, report_dir: str, start_timestamp: str, stryker_manager, jest_manager):
        self.stryker_manager = stryker_manager
        self.jest_manager = jest_manager
        self.openai_client = OpenAIClient()
        self.max_fix_attempts = 4
        self.max_generated_tests_per_file = 8
        self.coverage_target = 95.0
        self.report_steps = "\n"
        # Contabilizar o tempo
        self.start_time = datetime.now()
        self.start_timestamp = start_timestamp
        self.end_time = 0
        self.end_timestamp = ""
        self.report_dir = report_dir
        self.report_files = f"arquivos/{self.report_dir}/files-{self.start_timestamp}.txt"
        self.report_success = f"arquivos/{self.report_dir}/success-{self.start_timestamp}.txt"
        self.report_errors = f"arquivos/{self.report_dir}/errors-{self.start_timestamp}.txt"
        
        if not os.path.isdir(f"arquivos/{self.report_dir}"):
            os.mkdir(f"arquivos/{self.report_dir}")
        create_empty_file(self.report_files)
        create_empty_file(self.report_success)
        create_empty_file(self.report_errors)

    def _has_stryker_incompatible_test_patterns(self, test_code: str) -> bool:
        native_prototypes = "String|Array|Object|Date|Promise|Error"
        patterns = [
            rf"jest\s*\.\s*spyOn\(\s*(?:{native_prototypes})\.prototype",
            rf"\.spyOn\(\s*(?:{native_prototypes})\.prototype",
        ]
        return any(re.search(pattern, test_code) for pattern in patterns)

    def generate_unit_tests(
        self,
        paths: List[str],
        folder_structure: str,
        project_path: str,
        root_path: str
    ) -> None:
        if os.path.isfile(project_path):
            project_path = os.path.dirname(project_path)

        especificacoes = f"Especificações: modelo = {self.openai_client.model} | temperatura = {self.openai_client.temp} | max_attempts = {self.max_fix_attempts} | max_generated_tests = {self.max_generated_tests_per_file} | project_path = {project_path}\n\n"
        
        salvar_arquivo(self.report_files,especificacoes)
        
        # initialize Open AI system for both corrections and new tests
        system_prompt = GENERATE_TESTS_SYSTEM_NODE
        self.openai_client.history.append(
            {"role": "system", "content": system_prompt}
        )

        for path in paths:
            generate_test_file = True
            self.report_steps = "\n"
            # target = [
            #     'C:/repos/login/target-project/src/client-modules/accountfy/accountfy.module.ts'
            # ]
            # if not any(path.startswith(target) for target in target):
            #     continue

            #clean previous calls, leave only system
            if len(self.openai_client.history) > 1: 
                self.openai_client.history = self.openai_client.history[:1]

            file_name = os.path.basename(path)

            base_name, ext = os.path.splitext(file_name)
            ext = ext.replace(".", "")

            test_suffix = "spec" if ext == "ts" else "test"

            test_file_name = f"{base_name}.{test_suffix}.{ext}"

            path_dir = os.path.dirname(path)
            test_file_path = os.path.join(path_dir, test_file_name)

            print(f"#### PATH: {test_file_path}")
            self.report_steps += f"#### PATH: {test_file_path}\n"
            salvar_arquivo(self.report_files,f"#### PATH: {test_file_path}")
            with open(path, "r", encoding="utf-8") as f:
                file_content = f.read()

            internos = extrair_imports_ts(path)
            corrigidos = []
            for imp in internos:
                corrigidos.append(imp.replace("{", "{{").replace("}", "}}"))
            imports_arquivo = '\n'.join(corrigidos)
            import_files_code = self.get_import_files_code(imports_arquivo, path_dir)

            if os.path.exists(test_file_path):
                print(f"Arquivo de teste {test_file_path} já existe, verificando teste e cobertura...")
                self.report_steps += f"Arquivo de teste {test_file_path} já existe, verificando teste e cobertura...\n"

                execution_result = self.validate_node_test(test_file_path, root_path)
                print(f"Verificação do estado do arquivo de teste\nMensagem do teste:\n{execution_result.stderr}")
                self.report_steps += f"Verificação do estado do arquivo de teste\nMensagem do teste:\n{execution_result.stderr}\n"
                # salvar_arquivo(self.report_path, f"Arquivo de teste {test_file_path} já existe, validando...")
                with open(test_file_path, "r", encoding="utf-8") as f:
                    test_file_code_og = f.read()

                self.jest_manager.run_jest_coverage(root_path, [path])
                stmts_pcts = self.jest_manager.parse_jest_coverage_files(f"arquivos/{self.report_dir}", root_path, path, [path])
                stmts_pct_og = stmts_pcts[Path(path).name]["statements"]
                brnc_pct_og = stmts_pcts[Path(path).name]["branches"]
                self.report_steps += f"cobertura de {stmts_pct_og}% statements e {brnc_pct_og}% branches\n"
                if (stmts_pct_og == 100 and brnc_pct_og == 100):
                    generate_test_file = False
                    m = f"Arquivo de teste {test_file_path} verificado. Cobertura atual de {stmts_pct_og} nos statements e {brnc_pct_og} nas branches, não precisa de atualizações\n"
                    print(m)
                    self.report_steps += m
                    # salvar_arquivo(self.report_path, f"Arquivo de teste {test_file_path} validado com sucesso")
                elif stmts_pct_og > 0: # se a cobertura for 0 melhor construir do zero um arquivo novo
                    generate_test_file = False
                    m = f"Arquivo de teste {test_file_path} verificado. Cobertura atual de {stmts_pct_og} nos statements e {brnc_pct_og} nas branches, precisa de atualizações\n"
                    print(m)
                    self.report_steps += m
                    l = f"Fluxo para aumentar cobertura.\n"
                    self.report_steps += l
                    improve_result,message = self.improve_jest_coverage(path, file_content,test_file_path, root_path, paths, execution_result,ext,import_files_code)
                    # salvar_arquivo(self.report_path, f"Arquivo de teste {test_file_path} precisa de atualizações")
                # main_logger.info("Arquivo de teste %s já existe, testando...", test_path)
                # salvar_arquivo("arquivos/relatorio.txt", "1- Arquivo de teste já criado: '" + test_path + "'")

            if (generate_test_file):
                print(f"Criando testes para {path}")
                self.report_steps += f"Criando testes para {path}\n"
                # salvar_arquivo(self.report_path,f"Gerando testes para {path}")
                # main_logger.info("Gerando testes para %s", path)
                # salvar_arquivo("arquivos/relatorio.txt", "2- Criando arquivo de teste: '" + test_file_path + "'")

                # print(path)
                # print(corrigidos)
                # print(imports_arquivo)
                user_prompt_init = GENERATE_TESTS_USER_NODE.format(
                    node_code=file_content,
                    project_path=project_path,
                    app_structure=folder_structure,
                    test_path=test_file_path,
                    result_ext=ext,
                    max_tests=self.max_generated_tests_per_file
                )
                user_prompt_complete = self.add_reference_files(user_prompt_init, import_files_code)
                self.openai_client.history.append(
                    {"role": "user", "content": user_prompt_complete}
                )

                result = self.openai_client.completion()
                result = self.normalize_generated_test_code(result)
                self.openai_client.history.append(
                    {"role": "assistant", "content": result}
                )

                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(result)

                print(f"Arquivo de teste {test_file_path} criado, testando...")
                self.report_steps += f"Arquivo de teste {test_file_path} criado, testando...\n"
                # salvar_arquivo(self.report_path, f"Arquivo de teste {test_file_path} criado, testando...")
                # self.openai_client.history = [] #pq tirar? dá para usar esse histórico para o fix tbm
            
            execution_result = self.validate_node_test(test_file_path, root_path)
            print(f"Verificação do estado do arquivo de teste\nMensagem do teste:\n{execution_result.stderr}")
            self.report_steps += f"Verificação do estado do arquivo de teste\nMensagem do teste:\n{execution_result.stderr}\n"

            fix = False
            if not execution_result.returncode == 0:
                fix = True
                print(f"Fixing branch")
                self.report_steps += f"Fixing branch\n"
                execution_result,attempts = self._fix_test_failures(
                    path, file_content, test_file_path, execution_result, ext, import_files_code, root_path
                )

            if execution_result.returncode == 0:
                with open(test_file_path, "r", encoding="utf-8") as f:
                    accepted_test_code = f.read()
                if self._has_stryker_incompatible_test_patterns(accepted_test_code):
                    self.report_steps += (
                        "Arquivo de testes ainda possui mocks/spies em prototypes globais "
                        "incompativeis com Stryker. O arquivo nao sera adicionado ao Stryker.\n"
                    )
                    salvar_arquivo(
                        self.report_files,
                        "    ⚠ Arquivo de testes passa no Jest, mas possui mocks/spies em prototypes globais incompativeis com Stryker.",
                    )
                    salvar_arquivo(self.report_errors, self.report_steps)
                    continue

                test_file_path = test_file_path.replace("\\", "/")
                self.report_steps += f"Arquivo de testes {test_file_path} criado com sucesso e sem erros.\n"
                salvar_arquivo(self.report_files, f"    ✅ Arquivo de testes criado com sucesso e sem erros.")
                if fix:
                    salvar_arquivo(self.report_files, f"        Arquivo passou pelo fix com {attempts} tentativas para ajuste.")
                else:
                    salvar_arquivo(self.report_files, f"        Arquivo não precisou passar pelo fix.")
                self.stryker_manager.add_file_to_mutate(file_to_mutate=path)
                l = f"Arquivo original {path} adicionado ao Stryker para mutação.\n"
                self.report_steps += l
                
                l = f"Fluxo para aumentar cobertura.\n"
                self.report_steps += l
                improve_bool,message = self.improve_jest_coverage(path, file_content,test_file_path, root_path, paths, execution_result,ext,import_files_code)
                if improve_bool:
                    salvar_arquivo(self.report_files, f"    ✅ Arquivo passou pelo fluxo de melhoria sem problemas.\n {message}")
                    self.report_steps += message
                    salvar_arquivo(self.report_success,self.report_steps)
                else:
                    salvar_arquivo(self.report_files, f"    ⚠ Arquivo passou pelo fluxo de melhoria com erros.")
                    salvar_arquivo(self.report_files, f"        A versão do arquivo é a última que ainda funciona.")
                    self.report_steps += message
                    salvar_arquivo(self.report_success,self.report_steps)
            else:
                self.report_steps += f"\nNão foi possível criar o arquivo de testes {test_file_path}.\n"
                failed_artifacts = self.save_failed_test_artifacts(test_file_path, execution_result)
                if failed_artifacts:
                    self.report_steps += (
                        "Artefatos da última tentativa salvos para envio por e-mail:\n"
                        f"  Arquivo: {failed_artifacts['test_file']}\n"
                        f"  Log: {failed_artifacts['error_log']}\n"
                        f"  Resumo: {failed_artifacts['summary']}\n"
                    )
                salvar_arquivo(self.report_errors, self.report_steps)
                salvar_arquivo(self.report_files, f"    ❌ Arquivo de testes criado sem sucesso.")
                print("Delete file")
                try:
                    os.remove(test_file_path)
                    salvar_arquivo(self.report_files, f"    🗑️ Arquivo de testes deletado.")
                    salvar_arquivo(self.report_errors, "\nArquivo de testes deletado.")
                except Exception as e:
                    salvar_arquivo(self.report_files, f"    🗑️ Arquivo de testes não pode ser deletado.")
                    salvar_arquivo(self.report_errors, f"\nArquivo de testes não pode ser deletado: {e}")

        
        salvar_arquivo(self.report_files,f"\n\nTotal OpenAI calls: {self.openai_client.calls} for {len(paths)} files")
        salvar_arquivo(
            self.report_files,
            "OpenAI tokens: "
            f"prompt={self.openai_client.prompt_tokens} | "
            f"completion={self.openai_client.completion_tokens} | "
            f"total={self.openai_client.total_tokens}"
        )
        self.end_time = datetime.now()
        self.end_timestamp = datetime.now().strftime('%Y%m%d-%H-%M')
        time_elapsed = self.end_time - self.start_time
        salvar_arquivo(self.report_files,f"Start: {self.start_timestamp}\nEnd: {self.end_timestamp}\nElapsed: {time_elapsed}")

    def save_failed_test_artifacts(self, test_path: str, execution_result: CompletedProcess) -> dict:
        failed_dir = f"arquivos/{self.report_dir}/failed-tests"
        os.makedirs(failed_dir, exist_ok=True)

        test_name = os.path.basename(test_path)
        artifact_test_path = os.path.join(failed_dir, test_name)
        artifact_log_path = os.path.join(failed_dir, f"{test_name}.log")
        artifact_summary_path = os.path.join(failed_dir, f"{test_name}.failure-summary.txt")

        if os.path.exists(test_path):
            shutil.copy2(test_path, artifact_test_path)

        with open(artifact_log_path, "w", encoding="utf-8") as f:
            f.write(f"Arquivo de teste: {test_path}\n")
            f.write(f"Return code: {execution_result.returncode}\n\n")
            f.write("STDOUT:\n")
            f.write(execution_result.stdout or "")
            f.write("\n\nSTDERR:\n")
            f.write(execution_result.stderr or "")

        summary = self.build_failure_summary(test_path, execution_result)
        with open(artifact_summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        return {
            "test_file": artifact_test_path,
            "error_log": artifact_log_path,
            "summary": artifact_summary_path,
        }

    def build_failure_summary(self, test_path: str, execution_result: CompletedProcess) -> str:
        error_output = "\n".join(
            part for part in [execution_result.stderr, execution_result.stdout] if part
        )
        normalized_error = re.sub(r"\[[0-9;]*[mK]", "", error_output)
        normalized_error = re.sub(r"[\x1b]", "", normalized_error)
        classification, explanation, suggestion = self.classify_test_failure(normalized_error)

        return (
            f"Arquivo de teste: {test_path}\n"
            f"Tentativas de correcao: {self.max_fix_attempts}\n"
            f"Return code final: {execution_result.returncode}\n\n"
            f"Classificacao provavel: {classification}\n\n"
            f"Resumo:\n{explanation}\n\n"
            f"Proxima acao sugerida:\n{suggestion}\n\n"
            f"Evidencia principal:\n{self.extract_failure_evidence(normalized_error)}\n"
        )

    def classify_test_failure(self, error_output: str) -> tuple:
        error_lower = error_output.lower()

        if "nest can't resolve dependencies" in error_lower or "can't resolve dependencies" in error_lower:
            return (
                "Dependencia NestJS nao resolvida",
                "A ultima tentativa ainda falhou ao montar o TestingModule. Isso normalmente acontece quando algum provider, service, repository ou token injetado nao foi mockado/importado corretamente.",
                "Identificar a dependencia indicada no erro do Nest e adiciona-la em providers com mock, ou importar o modulo que exporta essa dependencia.",
            )

        if "cannot find module" in error_lower or "module not found" in error_lower:
            return (
                "Modulo ou import nao encontrado",
                "A ultima tentativa ainda possui import, mock ou dependencia que o Jest nao conseguiu resolver.",
                "Conferir o caminho/import indicado no erro e ajustar o mock, alias de modulo ou dependencia ausente.",
            )

        if "syntaxerror" in error_lower or "ts-jest" in error_lower or "typescript" in error_lower:
            return (
                "Erro de sintaxe ou TypeScript",
                "O teste final gerado nao compilou corretamente antes da execucao das assercoes.",
                "Revisar o trecho indicado pelo Jest/TypeScript e corrigir tipos, imports, mocks ou sintaxe invalida.",
            )

        if "typeerror" in error_lower and "is not a function" in error_lower:
            return (
                "Mock incompleto ou contrato incorreto",
                "A ultima tentativa chamou uma funcao que nao existe no mock ou no objeto usado durante o teste.",
                "Adicionar a funcao esperada ao mock ou ajustar o teste para usar o contrato real da dependencia.",
            )

        if "expect(" in error_lower or "expected" in error_lower or "received" in error_lower:
            return (
                "Assercao incorreta",
                "O teste executou, mas a expectativa gerada nao correspondeu ao comportamento real do codigo.",
                "Revisar a assercao falha e alinhar o valor esperado com o comportamento observado no erro.",
            )

        if "timeout" in error_lower or "exceeded timeout" in error_lower or "detectopenhandles" in error_lower:
            return (
                "Timeout ou recurso assincrono aberto",
                "A ultima tentativa provavelmente deixou Promise, timer, conexao ou observable sem finalizacao adequada.",
                "Garantir awaits corretos, mocks para chamadas externas e encerramento de recursos assincronos.",
            )

        return (
            "Falha nao classificada automaticamente",
            "A ultima tentativa continuou falhando, mas o erro nao bateu com os padroes conhecidos de classificacao.",
            "Abrir o log completo salvo junto deste resumo e revisar a primeira stack trace relevante do Jest.",
        )

    def extract_failure_evidence(self, error_output: str) -> str:
        lines = [line.strip() for line in error_output.splitlines() if line.strip()]
        if not lines:
            return "Sem stdout/stderr disponivel na ultima execucao."

        relevant_markers = (
            "error:",
            "cannot find module",
            "can't resolve dependencies",
            "nest can't resolve dependencies",
            "typeerror:",
            "syntaxerror:",
            "expected:",
            "received:",
            "timeout",
            "failed",
        )
        for line in lines:
            if any(marker in line.lower() for marker in relevant_markers):
                return line

        return lines[0]

    def normalize_generated_test_code(self, code: str) -> str:
        return code.replace("jest.clearAllMocks();", "jest.resetAllMocks();")

    def save_fix_attempt_artifact(self, test_path: str, content: str, attempt: int) -> None:
        attempts_dir = f"arquivos/{self.report_dir}/fix-attempts"
        os.makedirs(attempts_dir, exist_ok=True)

        test_name = os.path.basename(test_path)
        artifact_path = os.path.join(attempts_dir, f"attempt-{attempt}-{test_name}")

        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_fix_guidance(self, error: str) -> str:
        error_lower = error.lower()

        if "unit " in error_lower and "not found" in error_lower:
            return (
                "The test may have incorrect or misordered API/client mocks. "
                "Avoid long chains of mockReturnValueOnce. Rewrite repeated client mocks "
                "using mockImplementation based on the URL or argument received."
            )

        if "cannot read properties of undefined" in error_lower and "subscribe" in error_lower:
            return (
                "A dependency method consumed as an Observable returned undefined. "
                "Ensure RxJS dependencies always return of({ data: ... }) or throwError(() => error)."
            )

        if "received promise resolved instead of rejected" in error_lower:
            return (
                "The expected error path was not reached. Check whether previous mocks return data "
                "that makes the source code skip the failing branch."
            )

        if "received promise rejected instead of resolved" in error_lower:
            return (
                "The success path was expected, but the source threw an error. Check required mocks "
                "for dependencies executed before the expected assertion path."
            )

        if "expected" in error_lower and "received" in error_lower:
            return (
                "The test assertion is likely not aligned with the actual implementation. "
                "Derive expected values strictly from the source code behavior."
            )

        return (
            "Fix the test according to the actual source behavior. Do not change expectations "
            "unless they are directly supported by the implementation."
        )

    def validate_node_test(self, test_path: str, root_path:str) -> CompletedProcess:

        cl_test_path = test_path.replace("\\", "/")
        directory_path = os.path.dirname(test_path)
        directory_path = directory_path.replace("\\", "/")
        command = [
            "bash", "-lc", #linux
            f"cd {root_path} && node ./node_modules/jest/bin/jest.js --config jest.config.js --forceExit --detectOpenHandles {cl_test_path}",
        ]

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors='ignore'
        )

        return result

    def validate_all_tests(self, project_path: str) -> CompletedProcess:
        print("Executando todos os testes unitários")
        main_logger.info("Executando todos os testes unitários")

        command = [
            "cd",
            project_path,
            "&&",
            "npm",
            "test",
            "--forceExit",
            "--detectOpenHandles",
        ]

        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )

        return result

    def _fix_test_failures(
        self,
        file_path: str,
        base_file: str,
        test_path: str,
        execution_result: CompletedProcess,
        result_ext: str,
        import_files_code: dict,
        root_path: str
    ) -> None:
        self.openai_client.history = self.openai_client.history[:1]
        attempts = 0
        print(f'### Fluxo de correção de erros')
        self.report_steps += f'### Fluxo de correção de erros\n'
        while execution_result.returncode != 0 and attempts < self.max_fix_attempts:
            print(f'#Tentativa {attempts + 1}')
            self.report_steps += f'\n#Tentativa {attempts + 1} -> fluxo de correção\n'

            with open(test_path, "r", encoding="utf-8") as f:
                test_file = f.read()

            try:
                print('passo 1 - separação do erro do teste do jest')
                self.report_steps += 'passo 1 - separação do erro do teste do jest\n'
                error = ''
                if execution_result.stderr is not None:
                    error = execution_result.stderr
                    error = re.sub(r"\[[0-9;]*[mK]", "", error)
                    error = re.sub(r"[\u2190]", "", error)
                    error = re.sub(r"[\x1b]", "", error)
                error_guidance = self.get_fix_guidance(error)
                self.report_steps += f'  {error}\n'
                self.report_steps += f'  Orientação adicional: {error_guidance}\n'

                print('passo 2 - llm')
                self.report_steps += 'passo 2 - novo arquivo da llm\n'
                fix_file_user_init = FIX_FILE_USER_NODE.format(
                    test_file_path=test_path,
                    node_test_code=test_file,
                    base_file_code=base_file,
                    node_test_errors=f"{error}\n\nAdditional guidance:\n{error_guidance}",
                    result_ext=result_ext
                )
                fix_file_user_complete = self.add_reference_files(fix_file_user_init, import_files_code)
                self.openai_client.history.append({"role": "user", "content": fix_file_user_complete})
                
                new_result = self.openai_client.completion()
                new_result = self.normalize_generated_test_code(new_result)
                self.openai_client.history.append(
                    {"role": "assistant", "content": new_result}
                )
                self.save_fix_attempt_artifact(test_path, new_result, attempts + 1)

                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(new_result)

                print(f"passo 3 - verificar se resultado obtido passa no teste")
                self.report_steps += f"passo 3 - verificar se resultado obtido passa no teste\n"
                execution_result = self.validate_node_test(test_path, root_path)
            except Exception as e:
                print(f"Erro ao aplicar correções1: {e}")
                salvar_arquivo(self.report_files,f"Erro ao aplicar correções1: {e}")
            attempts += 1

        return execution_result,attempts
    
    def find_root_path(self, project_path) -> str:
        current_path = project_path

        found = False

        while not found:
            if os.path.exists(os.path.join(current_path, "package.json")):
                found = True
                return current_path
            
            parent_path = os.path.dirname(current_path)

            if parent_path == current_path:
                break
            
            current_path = parent_path

        return project_path
    
    def get_import_files_code(self, source_file_imports: str, module_path: str) -> dict:
        files_content_dict = {}
        
        pattern = r"from\s+['\"](?!@)([^'\"]+)['\"]"
        specifiers = re.findall(pattern, source_file_imports)
        is_target = False

        for spec in specifiers:
            absolute_path = os.path.normpath(os.path.join(module_path, spec))
            if not absolute_path.endswith('.ts'): absolute_path += '.ts'
            absolute_path_obj = Path(absolute_path).resolve()
            module_path_obj = Path(module_path).resolve()

            try:
                absolute_path_obj.relative_to(module_path_obj)
                is_target = True
            except ValueError:
                is_target = False

            if not is_target:
                continue

            if absolute_path not in files_content_dict:
                try:
                    with open(absolute_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    files_content_dict[absolute_path] = content
                except Exception as e:
                    print(f"Error reading {absolute_path}: {e}")

        return files_content_dict


    def add_reference_files(self, prompt: str, files_to_add: dict) -> str:
        new_prompt = prompt
        if len(files_to_add) > 0:
            new_prompt += "\nConsider the following imported files for reference: \n\n"

            for key in files_to_add:
                new_prompt += f"File `{key}`: \n```\n{files_to_add[key]}```\n"

        return new_prompt
    
    #TODO: no caso de passar um módulo inteiro isso aqui pode ficar meio redudante
    # vai rodar sempre para muitos arquivos, talvez tenha onde melhorar
    def improve_jest_coverage(self, 
            path, file_content,test_file_path, root_path, paths, result_ext,
            ext,import_files_code):
        self.report_steps += "### Fluxo de melhoria de cobertura\n"
        self.jest_manager.run_jest_coverage(root_path, paths)
        files_pcts = self.jest_manager.parse_jest_coverage_files(f"arquivos/{self.report_dir}", root_path, path, paths)
        if files_pcts == -1:
            l = f"Não tem arquivo de coverage para basear os dados\n"
            return False, l
        stmts_pct = files_pcts[Path(path).name]["statements"]
        brnc_pct = files_pcts[Path(path).name]["branches"]

        if stmts_pct >= self.coverage_target and brnc_pct >= self.coverage_target:
            l = f"Cobertura de {stmts_pct}% maior ou igual que o alvo de {self.coverage_target}%\n"
            return True, l

        l = f"Cobertura de {stmts_pct}% de statements ou de {brnc_pct}% de branches é menor que o alvo de {self.coverage_target}%. Fluxo para melhoria de cobertura iniciado\n"
        self.report_steps += l

        self.openai_client.history = self.openai_client.history[:1]
        execution_result = result_ext
        attempts = 0
        no_improvement_attempts = 0
        while (stmts_pct < self.coverage_target or brnc_pct < self.coverage_target) and attempts < self.max_fix_attempts:
            self.report_steps += f'#Tentativa {attempts + 1} -> Fluxo de melhoria de cobertura\n'

            with open(f"{test_file_path}", "r", encoding="utf-8") as f:
                test_file_content = f.read()
            original_has_incompatible_patterns = self._has_stryker_incompatible_test_patterns(test_file_content)

            try:
                self.report_steps += 'passo 1 - novo arquivo da llm\n'
                uncovered_branches = self.jest_manager.get_uncovered_branches(
                    f"arquivos/{self.report_dir}",
                    Path(path).name,
                )
                uncovered_branches_text = "\n".join(f"- {branch}" for branch in uncovered_branches)
                if not uncovered_branches_text:
                    uncovered_branches_text = "No uncovered branch snippets were extracted from the HTML report."
                self.report_steps += f"Branches descobertos informados ao prompt:\n{uncovered_branches_text}\n"
                improve_file_user_init = INCREASE_JEST_COVERAGE_USER_NODE.format(
                    test_file_path=test_file_path,
                    test_file_code=test_file_content,
                    source_file_path=path,
                    source_file_code=file_content,
                    stmts_coverage=stmts_pct,
                    brnc_coverage=brnc_pct,
                    target_coverage=self.coverage_target,
                    uncovered_branches=uncovered_branches_text
                )
                self.openai_client.history.append({"role": "user", "content": improve_file_user_init})
                
                result = self.openai_client.completion()
                result = self.normalize_generated_test_code(result)
                self.openai_client.history.append(
                    {"role": "assistant", "content": result}
                )

                with open(f"{test_file_path}", "w", encoding="utf-8") as f:
                    f.write(result)

                self.report_steps += f"passo 2 - Verifica se o teste ainda funciona\n"
                execution_result = self.validate_node_test(test_file_path, root_path)
                self.report_steps += f"  Return code: {execution_result.returncode}\n"
                if not execution_result.returncode == 0:
                    l = f"Tentativa de melhoria criou erros. Tentando arrumar no fluxo de correção\n"
                    self.report_steps += l
                    execution_result,fix_attempts = self._fix_test_failures(
                        path, file_content, f"{test_file_path}", execution_result, ext, import_files_code, root_path)
                    # self.jest_manager.run_jest_coverage(root_path, paths)
                    # files_pcts = self.jest_manager.parse_jest_coverage_files(f"arquivos/{self.report_dir}", root_path, path, paths)
                    if not execution_result.returncode == 0:
                        l = f"Tentativa de correção falhou. Voltando para a última versão funcional do arquivo.\n  Último retorno do Jest:\n  returncode: {execution_result.returncode}\n  {execution_result.stdout}\n"
                        self.report_steps += l
                        with open(f"{test_file_path}", "w", encoding="utf-8") as f:
                            f.write(test_file_content)
                        return False,l

                with open(f"{test_file_path}", "r", encoding="utf-8") as f:
                    current_test_content = f.read()
                current_has_incompatible_patterns = self._has_stryker_incompatible_test_patterns(current_test_content)
                if current_has_incompatible_patterns:
                    l = (
                        "Tentativa manteve mocks/spies em prototypes globais incompativeis com Stryker. "
                        "Voltando para a ultima versao funcional do arquivo.\n"
                    )
                    self.report_steps += l
                    with open(f"{test_file_path}", "w", encoding="utf-8") as f:
                        f.write(test_file_content)
                    return False, l

                self.report_steps += f"passo 3 - verificar se a cobertura aumentou\n"
                self.jest_manager.run_jest_coverage(root_path, paths)
                files_pcts = self.jest_manager.parse_jest_coverage_files(f"arquivos/{self.report_dir}", root_path, path, paths)
                stmts_temp = files_pcts[Path(path).name]["statements"]
                brnc_temp = files_pcts[Path(path).name]["branches"]
                self.report_steps += f"Nova cobertura após fix é {stmts_temp}% nos statements e {brnc_temp}% nas branches\n"
                if stmts_pct > stmts_temp or brnc_pct > brnc_temp:
                    if original_has_incompatible_patterns and not current_has_incompatible_patterns:
                        l = (
                            "Tentativa reduziu cobertura, mas removeu mocks/spies em prototypes globais "
                            "incompativeis com Stryker. Mantendo versao Stryker-compatible.\n"
                        )
                        self.report_steps += l
                        return True, l
                    l = f"Tentativa de correção gerou um resultado pior que o anterior. Voltando para a última versão melhor do arquivo.\n  Último retorno do Jest:\n  returncode: {execution_result.returncode}\n  {execution_result.stdout}\n"
                    self.report_steps += l
                    with open(f"{test_file_path}", "w", encoding="utf-8") as f:
                        f.write(test_file_content)
                    return False,l
                if stmts_temp == stmts_pct and brnc_temp == brnc_pct:
                    no_improvement_attempts += 1
                    self.report_steps += f"Tentativa sem ganho de cobertura. Total consecutivo: {no_improvement_attempts}\n"
                    if no_improvement_attempts >= 2:
                        return True, (
                            f"Fluxo de melhoria encerrado após {attempts + 1} tentativas "
                            "porque a cobertura não aumentou em 2 tentativas consecutivas"
                        )
                else:
                    no_improvement_attempts = 0
                stmts_pct = files_pcts[Path(path).name]["statements"]
                brnc_pct = files_pcts[Path(path).name]["branches"]
            except Exception as e:
                l = f"Erro ao melhorar cobertura:\n    {e}\n\n"
                return False,l
            attempts += 1

        return True,f"Fluxo de melhoria encerrado com sucesso em {attempts} tentativas"
