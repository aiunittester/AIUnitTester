#!/usr/bin/env python3
"""
Simular o passo a passo do pipeline do GitLab
"""

import os
import subprocess
from pathlib import Path

def process_files(changed_files, base_path):
    for file_path in changed_files:
        file_path_str = str(file_path)
        
        if file_path_str.endswith('.ts'):
            if "spec" in file_path_str:
                print(f"Ignorando arquivo de teste: {file_path_str}")
            else:
                print(f"Gerar testes para o {file_path_str}")
                print(file_path_str)
                
                full_path = os.path.join(base_path, file_path_str)
                full_path = full_path.replace("\\","/")
                try:
                    subprocess.run(
                        ['python3', 'main.py', '--path', full_path, '--language', 'node'],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Error running test generation for {file_path_str}: {e}")
                except FileNotFoundError:
                    print("Error: python or main.py not found")
        else:
            print(f"Ignorar arquivo {file_path_str}")

def main():
    
    changed_files = [
        "src/client-modules/mo/mo.module.ts",
        "src/client-modules/mo/mo.service.ts",
        "src/client-modules/mo/notification/mo-notification.controller.ts",
        "src/client-modules/mo/notification/mo-notification.module.ts",
        "src/client-modules/mo/notification/mo-notification.service.ts",
    ]
    print(f"Processing {len(changed_files)} file(s)...")
    # process_files(changed_files, base_path="C:/repos/login/target-project")
    process_files(changed_files, base_path="/workspace/target-project")

if __name__ == "__main__":
    main()
