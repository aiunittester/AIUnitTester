import os
from typing import List, Optional
from pathlib import Path

TARGET_DIR = "node_files"


class NodeProjectManager:
    def __init__(
        self,
        project_path: str,
        exts: Optional[List[str]] = None,
    ):
        self.project_path = project_path
        self.exts = exts

        self.paths = self._load_file_paths()

    def _should_ignore_file(self, file_path: str) -> bool:
        normalized_path = file_path.replace(os.sep, "/").lower()
        file_name = os.path.basename(normalized_path)

        ignored_suffixes = (
            "spec.ts",
            "test.js",
            "main.ts",
            ".module.ts",
            "env-config.ts",
            ".setup.js",
            ".dto.ts",
            ".dto.js",
            ".interface.ts",
            ".interface.js",
        )

        return file_name.endswith(ignored_suffixes)

    def __is_valid_path(self, root: str, paths_to_ignore: List[str]) -> bool:
        for path in paths_to_ignore:
            if path in root:
                return False

        return True

    def _load_file_paths(self) -> List[str]:
        paths = []

        if os.path.isfile(self.project_path):
            _, ext = os.path.splitext(self.project_path)
            if self.exts and ext not in self.exts:
                return paths
            if self._should_ignore_file(self.project_path):
                return paths
            return [self.project_path]

        for root, _, files in os.walk(self.project_path):
            if not self.__is_valid_path(root, ["\\node_modules",
                                               "\\dist", 
                                               "\\build", 
                                               "\\test", 
                                               "\\tests",
                                               "\\infra"]):
                continue

            for file_name in files:
                _, ext = os.path.splitext(file_name)

                if (
                    ext not in self.exts
                    or self._should_ignore_file(os.path.join(root, file_name))
                ):
                    continue

                paths.append(os.path.join(root, file_name).replace(os.sep, "/"))

                # if not self.exts or ext in self.exts:
                #     paths.append(os.path.join(root, file_name))
        print(len(paths))
        return paths

    def get_folder_structure(self, path: str, prefix: str = "") -> str:        
        result = ""

        if os.path.isfile(path):
            path_splitted = path.split(os.sep)
            for i in range (len(path_splitted)):
                result += "    " * i + "└──" + path_splitted[i] + "\n"
            return result

        try:
            items = os.listdir(path)
            total_items = len(items)

            if prefix != "": 
                dash = prefix.replace(" ", "-")
                folder_name = os.path.basename(path)
                result += f"+{dash}{folder_name}\n"

            for index, item in enumerate(items):
                if item == "node_modules":
                    continue

                ext = os.path.splitext(item)[1]
                if ext not in self.exts and ext != '':
                    continue
                
                if ext == '':
                    new_prefix = f"    " if prefix == '' else f"{prefix}    "
                    new_path = f"{path}/{item}"
                    sub_result = self.get_folder_structure(new_path, new_prefix)
                    result += sub_result
                    continue

                item_path = os.path.join(path, item)
                
                connector = "├──" if index < total_items - 1 else "└──"
                result += f"{prefix}{connector} {item}\n"
                
                if os.path.isdir(item_path):
                    new_prefix = prefix + ("│   " if index < total_items - 1 else "    ")
                    result += self.get_folder_structure(item_path, new_prefix)
        except PermissionError:
            result += f"{prefix}└── [Permission Denied]\n"

        return result
