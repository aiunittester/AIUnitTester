# AIUnitTester

## Executando a aplicação

Para executar a aplicação, basta executar o seguinte comando:

```shell
python main.py --path <caminho_do_projeto> --language <linguagem_programacao> --exts <extensoes>
```

- **--path**: caminho do projeto que serão gerados os testes (obrigatório). Para node, pode passar apenas um arquivo para gerar os testes.
- **--language**: linguagem de programação em que serão gerados os testes (obrigatório).<br>
    Opções disponíveis: `node`.
- **--no-verbose**: desabilita a exibição de mensagens durante a criação dos testes (opcional).

## Projetos Node.js

### Configurar Jest

Criar na raíz do projeto, o arquivo de configuração `jest.config.js`:
```js
module.exports = {
    moduleFileExtensions: ['js', 'ts'],
    rootDir: 'src',
    testMatch: ['**/*.spec.ts', '**/*.test.ts'],
    testPathIgnorePatterns: ['\\.d\\.ts$', '/node_modules/', '/dist/', '/tests/'],
    transform: {
      '^.+\.ts$': 'ts-jest',
    },
    collectCoverageFrom: ['**/*.(t|j)s'],
    coverageDirectory: '../coverage',
    testEnvironment: 'node',
    coverageReporters: ['text-summary', 'html'],
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  };
```

Criar dentro da pasta `src` ou `app` ou `pasta_com_os_códigos` um arquivo `jest.setup.js`:
```js
beforeEach(() => {
  expect.hasAssertions(); // Força cada teste a ter pelo menos uma asserção
  jest.setTimeout(10000);
});
```

*O arquivo de configuração do jest será criado automaticamente com quais caminhos o `jest` deve ignorar ao rodar o projeto. Alterar `jest.config.js` caso queira mexer em alguma configuração.

*Caso esteja dando erro de arquivo não encontrado por causa do eslint no vs code, adicionar no `settings.json` do próprio vs code:
```json
"eslint.options": {
    "allowDefaultProject": true
  }
```

### Configurar o Stryker Mutator

Após instalar, executar o seguinte comando para iniciar a configuração:

#### yarn
```shell
yarn run stryker init
```

#### npm
```shell
npm run stryker init
```

*O arquivo de configuração do stryker será gerado automaticamente com quais arquivos o stryker deve passar ao rodar o projeto. Alterar `stryker.config.json` caso queira mexer em alguma configuração.

## Erro ao rodar o stryker:

Só é possível rodar o stryker, o jest não encontre nenhum arquivo de teste com erro, por isso é passado uma lista com os arquivos para o stryker rodar e uma lista com os caminhos para o jest ignorar.

## Docker
Para rodar local um ambiente parecido com o do gitlab no VSCode

Criar uma env
```shell
docker build -t ai-dev-env .
```

Montar container com `-v` para atualização dinâmica
```shell
docker run -it --name ai-dev-container \
  -v "C:/repos/your-project/unit-tests:/workspace/unit-tests" \
  -v "C:/repos/your-project/target-project:/workspace/target-project" \
  ai-dev-env
```

No VSCode
- ctrl+shift+p > attach running container

Adiconar as extensões do python para rodar debug e outras coisas
- ms-python.vscode-pylance
- ms-python.python
- ms-python.debugpy
- ms-python.vscode-python-envs
