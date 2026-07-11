import json

user_prompt = """Considere o seguinte código NodeJS:
```ts
{codigo_original}
``` 
Escreva quantos testes achar necessário para o código, cobrindo o máximo de casos possível.

Retorne o resultado como um arquivo de testes unitários em ts, considerando as regras definidas no system.

Retorne somente o conteúdo do arquivo, sem utilizar qualquer delimitador ou adicionar explicações sobre o arquivo gerado. Não utilize o delimitador '```ts'
"""

codigo = """import { validate } from 'class-validator';
import { AtualizarTaskDto } from './atualizarTask.dto';

it('should validate when all fields are valid', async () => {
    const taskDto = new AtualizarTaskDto();
    taskDto.title = 'New Task';
    taskDto.description = 'Task description';
    taskDto.status = 'pending';
    taskDto.author_id = 1;

    const errors = await validate(taskDto);
    expect(errors.length).toBe(0);
});

it('should not validate when title is not a string', async () => {
    const taskDto = new AtualizarTaskDto();
    taskDto.title = 123 as any; // Invalid type

    const errors = await validate(taskDto);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].property).toBe('title');
});

it('should not validate when description is not a string', async () => {
    const taskDto = new AtualizarTaskDto();
    taskDto.description = 123 as any; // Invalid type

    const errors = await validate(taskDto);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].property).toBe('description');
});

it('should not validate when status is not in the allowed values', async () => {
    const taskDto = new AtualizarTaskDto();
    taskDto.status = 'invalid_status' as any; // Invalid value

    const errors = await validate(taskDto);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].property).toBe('status');
});

it('should not validate when author_id is not an integer', async () => {
    const taskDto = new AtualizarTaskDto();
    taskDto.author_id = 'string' as any; // Invalid type

    const errors = await validate(taskDto);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].property).toBe('author_id');
});

it('should validate when fields are optional and not provided', async () => {
    const taskDto = new AtualizarTaskDto();

    const errors = await validate(taskDto);
    expect(errors.length).toBe(0);
});"""

user_prompt = user_prompt.format(codigo_original=codigo)

data = {
    "messages": [
        {
            "role": "system",
            "content": "Você é um especialista em NodeJS. Sua principal função é criar testes unitários para arquivos JavaScript ou TypeScript que o usuário fornecer.\n\nVocê irá receber algumas informações do usuário:\n- Um arquivo JavaScript ou TypeScript\n- Uma string contendo a estrutura de toda a aplicação do usuário\n- Uma string contendo o caminho do arquivo de testes que será gerado\n\nAo receber essas informações, realize o seguinte passo a passo:\n\n1 - Analise o código informado e a estrutura de toda a aplicação que o usuário forneceu\n2 - Considere o caminho do arquivo de testes e a estrutura completa da aplicação para gerar corretamente o caminho das importações e dos mocks\n3 - Gere testes unitários para o código utilizando os pacotes jest e supertest\n4 - Evite criar testes unitários que validam somente se um log foi disparado, crie esses testes somente em quando não for encontrado mais nada para validar um determinado caso.\n5 - Adicione todos os pacotes necessário no arquivo de testes, para que os testes possam executar corretamente\n6 - Evite gerar testes com código repetido, ou que verifiquem o mesmo caso\n7 - Faça o possível para cobrir todos os casos, como entradas válidas e inválidas (valores extremos, null, undefined), fluxos alternativos (if, else, try/catch) e manipulação de erros e exceções.\n8 - Não deve ser gerado testes de integração\n9 - Sempre que for gerar um teste, comece utilizando o ```it()``` e descreva o que o teste irá fazer\n10 - Não crie testes utilizando ```mock``` e utilizando ```describe``` de jeito nenhum\n11 - Após o teste for gerado e ser válido, será gerado mutantes utilizando a biblioteca Stryker Mutator, então, certifique-se de que o teste cobre todos os casos possíveis"
        }, 
        {
            "role": "user",
            "content": ""
        }, 
        {
            "role": "assistant",
            "content": ""
        }
    ]
}

data["messages"][1]["content"] = user_prompt.replace("\n", "\\n")
data["messages"][2]["content"] = codigo.replace("\n", "\\n")

with open("files/teste.jsonl", "w+", encoding="utf-8") as f:
    json.dump(data, f)
