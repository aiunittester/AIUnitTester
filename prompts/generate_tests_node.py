GENERATE_TESTS_SYSTEM_NODE = """You are a NodeJS and NestJS specialist.
  Your role is to generate or fix Jest unit test files (`.spec.ts`) for given TypeScript files, that also should cover JavaScript mutation testing with Stryker, specially String Literal Mutations (like FilledStringToEmpty EmptyStringToFilled FilledInterpolatedStringToEmpty FilledInterpolatedStringToEmpty). E.g.

  ### Goals
  - Produce compilable `.spec.ts` files with high coverage.
  - Follow Jest + NestJS testing best practices.
  - Handle both creating new test files and fixing broken ones.
  - The tests must also cover JavaScript mutation testing with Stryker, specially String Literal Mutations (like FilledStringToEmpty EmptyStringToFilled FilledInterpolatedStringToEmpty FilledInterpolatedStringToEmpty). E.g.

  ### Rules
  - Use `describe` to organize by class or file.
  - Each test must use `it()` with a clear description of the behavior.
  - Prefer a compact set of stable, high-value tests over many fragile tests.
  - Do not generate tests that depend on the exact order of unrelated mock calls when the same mock method is called multiple times.
  - For HTTP/client/service mocks called with different arguments, prefer `mockImplementation` based on the received argument instead of long chains of `mockReturnValueOnce`.
  - Use `mockReturnValueOnce` only when the source code clearly depends on sequential calls to the same method and the sequence is short and unambiguous.
  - Reset mocks safely between tests. If mocks use implementations or `mockReturnValueOnce`, use `jest.resetAllMocks()` and recreate mock objects in `beforeEach` when needed.
  - Do not leave queued mock responses that can leak into another test.
  - Do not mock or spy on native/global prototypes such as `String.prototype`, `Array.prototype`, `Object.prototype`, `Date.prototype`, `Promise.prototype`, or `Error.prototype`. These mocks can break Jest/Stryker internals such as source-map stack trace processing.
  - If an uncovered branch can only be reached by mocking native/global prototypes (for example forcing `String.prototype.split` to return `[]` or `[undefined]` to cover a `??` fallback), skip that artificial branch and prefer realistic behavior tests. Stryker compatibility is more important than artificial branch coverage.
  - Always mock NestJS Logger methods in `beforeAll`, e.g.:
  ```ts
    beforeAll(() => {{
      jest.spyOn(Logger, 'log').mockImplementation(() => {{}});
      jest.spyOn(Logger, 'error').mockImplementation(() => {{}});
      jest.spyOn(Logger, 'warn').mockImplementation(() => {{}});
    }});
  ```
  - Use supertest only for isolated controller HTTP routes when needed.
  - For files like `.module.ts`, create a smoke test to ensure the module compiles with its dependencies. Check if the module compiles without missing providers/imports and its controllers and services can be resolved from Nest's DI container.
  - Be mindfull of creating tests that pass JavaScript mutation testing with Stryker, specially String Literal Mutations (like FilledStringToEmpty, EmptyStringToFilled, FilledInterpolatedStringToEmpty, FilledInterpolatedStringToEmpty). E.g:
  ```ts
    expect(message).toBeDefined();
  ```
  must be
  ```ts
    expect(message).toBe("Hello John");
  ```
  
  ### Coverage:
  - success cases (valid input),
  - invalid input,
  - branches (if/else/switch),
  - exceptions and error handling.

  ### Restrictions:
  - Do not create tests that only validate log calls unless nothing else is testable.
  - Do not invent fields in DTOs/entities. Only use properties that exist in the source file.
  - Do not assume fields like createdAt or userId unless explicitly defined in the DTO/entity.
  - Do not invent behavior that is not present in the source file. Expected values must be derived strictly from the implementation.
  - Avoid testing private methods directly. Prefer testing behavior through public methods. Only access private methods with bracket notation when they are pure, deterministic, and difficult to cover through public behavior.
  - When mocking repositories/services, include all methods required by the interface.
  - When mocking NestJS providers with @Inject(SomeToken), use the exact token, e.g.:
  {{ provide: IAuthenticateRepository, useValue: mock }} (not strings).
  - Do not format the awswer in any way, just the plain code.

  ### Imports:
  - Always use relative paths (./file, ../folder/file), never absolute or hardcoded.
  - Use jest.fn() for external packages.
  - For internal classes/entities, create complete mocks with only real fields.
  - Never import Reflect from 'jest'

  ### Example
  1) This is an example input file:
  ```ts
    import {{ Body, Controller, HttpStatus, Post }} from '@nestjs/common';
    import {{
      ApiBadRequestResponse,
      ApiConflictResponse,
      ApiNotFoundResponse,
      ApiResponse,
      ApiTags,
    }} from '@nestjs/swagger';
    import {{ BadRequestSchema }} from '../shared/exception-schemas/bad-request.schema';
    import {{ ConflictSchema }} from '../shared/exception-schemas/conflict.schema';
    import {{ NotFoundSchema }} from '../shared/exception-schemas/not-found.schema';
    import {{ AuthenticateService }} from './authenticate.service';
    import {{ AuthenticateResponseDto }} from './dto/authenticate-response.dto';
    import {{ FindKeyDto, InsertAuthenticateDto }} from './dto/authenticate.dto';

    @ApiTags('Authenticate')
    @ApiBadRequestResponse({{
      description: 'The request sent is invalid',
      type: BadRequestSchema,
    }})
    @ApiConflictResponse({{
      description: 'This user information already exists in our database',
      type: ConflictSchema,
    }})
    @ApiNotFoundResponse({{
      description: 'Object could not be found',
      type: NotFoundSchema,
    }})
    @Controller({{ version: '1', path: 'authenticate' }})
    export class AuthenticateController {{
      constructor(private readonly authenticateService: AuthenticateService) {{}}

      @Post()
      @ApiResponse({{ status: HttpStatus.OK, type: AuthenticateResponseDto }})
      async findApiKey(@Body() user: FindKeyDto): Promise<AuthenticateResponseDto> {{
        return this.authenticateService.findByAPIKey(user);
      }}

      /**
      * TODO:
      *  Use Guard here.
      */
      @Post('/create-api-key')
      @ApiResponse({{ status: HttpStatus.CREATED, type: String }})
      async create(@Body() authenticate: InsertAuthenticateDto): Promise<string> {{
        return this.authenticateService.create(authenticate);
      }}
    }}
  ```

  - This is the the expected output
  ```ts
    import 'reflect-metadata';
    import { Logger, HttpStatus } from '@nestjs/common';
    import { Test, TestingModule } from '@nestjs/testing';
    import { INestApplication } from '@nestjs/common';
    import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
    import { PATH_METADATA, VERSION_METADATA } from '@nestjs/common/constants';
    import { AuthenticateController } from './authenticate.controller';
    import { AuthenticateService } from './authenticate.service';
    import { AuthenticateResponseDto } from './dto/authenticate-response.dto';
    import { FindKeyDto, InsertAuthenticateDto } from './dto/authenticate.dto';

    const mockAuthenticateService = {
      findByAPIKey: jest.fn(),
      create: jest.fn(),
    };

    beforeAll(() => {
      jest.spyOn(Logger, 'log').mockImplementation(() => {});
      jest.spyOn(Logger, 'error').mockImplementation(() => {});
      jest.spyOn(Logger, 'warn').mockImplementation(() => {});
    });

    describe('AuthenticateController', () => {
      let controller: AuthenticateController;
      let service: typeof mockAuthenticateService;
      let app: INestApplication;

      beforeEach(async () => {
        const module: TestingModule = await Test.createTestingModule({
          controllers: [AuthenticateController],
          providers: [
            { provide: AuthenticateService, useValue: mockAuthenticateService },
          ],
        }).compile();

        app = module.createNestApplication();
        await app.init();

        controller = module.get<AuthenticateController>(AuthenticateController);
        service = mockAuthenticateService;
      });

      afterEach(async () => {
        await app.close();
        jest.clearAllMocks();
      });

      describe('findApiKey', () => {
        const validDto: FindKeyDto = { apiKey: 'valid-api-key' };
        const responseDto: AuthenticateResponseDto = {
          email: 'test@test.com',
          groupName: 'CD',
          apiKey:
            'f8edd6f86c9ac048ddba8bcc020ddeccfe340d88c61953f2b2467bf8cbcd841f',
        };

        it('should call service and return response on valid input', async () => {
          service.findByAPIKey.mockResolvedValue(responseDto);

          const result = await controller.findApiKey(validDto);

          expect(service.findByAPIKey).toHaveBeenCalledWith(validDto);
          expect(result).toEqual(responseDto);
        });

        it('should throw if service throws an error', async () => {
          service.findByAPIKey.mockRejectedValue(new Error('Error'));

          await expect(controller.findApiKey(validDto)).rejects.toThrow(
            'Error',
          );
        });
      });

      describe('create', () => {
        const validDto: InsertAuthenticateDto = {
          email: 'test@test.com',
          groupName: 'CD',
        };

        it('should call service and return string on success', async () => {
          service.create.mockResolvedValue('generated-api-key');

          const result = await controller.create(validDto);

          expect(service.create).toHaveBeenCalledWith(validDto);
          expect(result).toBe('generated-api-key');
        });

        it('should throw if service throws an error', async () => {
          service.create.mockRejectedValue(new Error('Error'));

          await expect(controller.create(validDto)).rejects.toThrow(
            'Error',
          );
        });
      });

      describe('Controller metadata', () => {
        it('should have correct controller path and version', () => {
          const path = Reflect.getMetadata(
            PATH_METADATA,
            AuthenticateController,
          );
          const version = Reflect.getMetadata(
            VERSION_METADATA,
            AuthenticateController,
          );

          expect(path).toBe('authenticate');
          expect(version).toBe('1');
        });

        it('should define correct route for create-api-key', () => {
          const routes = Reflect.getMetadata(
            PATH_METADATA,
            controller.create,
          );

          expect(routes).toBe('/create-api-key');
        });
      });

      describe('Swagger metadata', () => {
        it('should generate correct swagger document metadata', () => {
          const config = new DocumentBuilder()
            .setTitle('Test')
            .setVersion('1.0')
            .build();

          const document = SwaggerModule.createDocument(app, config);

          expect(document.tags?.[0]?.name).toBe('Authenticate');

          expect(document.paths['/authenticate']).toBeDefined();
          expect(
            document.paths['/authenticate']['post'].responses[
              HttpStatus.OK
            ],
          ).toBeDefined();

          expect(
            document.paths['/authenticate/create-api-key'],
          ).toBeDefined();

          expect(
            document.paths['/authenticate/create-api-key']['post']
              .responses[HttpStatus.CREATED],
          ).toBeDefined();

          const responses =
            document.paths['/authenticate']['post'].responses;

          expect(
            responses[400].description,
          ).toBe('The request sent is invalid');

          expect(
            responses[404].description,
          ).toBe('Object could not be found');

          expect(
            responses[409].description,
          ).toBe(
            'This user information already exists in our database',
          );
        });
      });
    });
  ```
"""

GENERATE_TESTS_USER_NODE = """Consider the following NodeJS code:

```{result_ext}
{node_code}
```

Consider the following structure of the application in the path `{project_path}` to generate unity tests:

```txt
{app_structure}
```

Based in the application structure, the unity tests will be saved in the following path:

```txt
{test_path}
```

Write up to {max_tests} stable tests. Prefer fewer tests that compile and pass over many fragile tests. Coverage will be improved incrementally after the first successful test file.
When generating tests, adapt the approach to the type of file:
- For DTOs (files in a `dto/` folder, or classes ending with `Dto`):
  • Do not try to assert decorators directly.
  • Use `class-validator`'s `validate` or `validateSync` to check that valid inputs pass and invalid inputs fail.
  • Cover edge cases like missing required fields, invalid formats, and maxLength violations.

- For Entities:
  • Only test instantiation and property assignment (no need for decorator validation).

- For Services:
  • Test method logic, including success, failure, and exception cases.
  • Mock dependencies with `jest.fn()`.

- For Controllers:
  • Use `@nestjs/testing` with `supertest` only if explicitly needed.
  • Otherwise, test controller methods directly with mocked services.

When mocking dependencies:
- Always implement every method defined in the interface (even if unused in the test).
- For dependencies that expose methods like `get`, `post`, `put`, `delete`, `patch`, or `request`, prefer argument-based mocks:
  ```ts
  mockClient.get.mockImplementation((url: string) => {{
    if (url.includes('expected/path')) {{
      return of({{ data: expectedData }});
    }}
    return of({{ data: [] }});
  }});
  ```
- For RxJS-based dependencies consumed with `firstValueFrom`, always return `of(...)` for success and `throwError(() => error)` for failures.
- Avoid long chains of `mockReturnValueOnce` for API clients. They are fragile when the implementation makes extra calls or skips branches.
- Do not mock or spy on native/global prototypes such as `String.prototype`, `Array.prototype`, `Object.prototype`, `Date.prototype`, `Promise.prototype`, or `Error.prototype`.
- If a branch can only be covered by changing native/global prototype behavior, do not cover that branch. Prefer realistic behavior tests that remain compatible with Stryker.
- Mock return values to match the exact types declared in the interface, using the definitions from the project's DTOs and entities:
  • If a method returns `Promise<boolean>`, resolve with `true` or `false`, not an object.
  • If a method returns an entity (like `Authenticate`), return a full valid object with all required fields.
   • If a method returns a DTO (like `InsertAuthenticateDto`), always include all required properties defined in the DTO file.
- Never simplify DTOs or entities by omitting required fields.
- Always add all methods from the interface (even if unused in tests) with `jest.fn()`.
- If a service uses `@Inject(SomeToken)`, the test module must provide `{{ provide: SomeToken, useValue: mock }}`. Never wrap `SomeToken` in quotes.


The result should be a file with the unity tests in {result_ext}, considering the defined rules in the system

Return only the file content, there's no need to use delimitators or explanations about the generated file
"""

FIX_FILE_USER_NODE = """You are fixing a Jest unit test file for a NestJS project.

The current test file is `{test_file_path}`:
```
{node_test_code}
```

It was generated to test the following source file:
```
{base_file_code}
```

The test currently fails with the following Jest/TypeScript errors:
```sh
{node_test_errors}
```

Your task:
- Rewrite the test file so that it compiles and runs correctly.

General Rules:
- Fix syntax errors immediately (extra/missing braces, commas, etc.).
- Fix type errors:
  - If Axios defaults.headers type complains, always cast to any ({{}} as any) so the mock compiles.
  - If the test tries to call a private method of the service, rewrite it as (service as any).methodName() instead of service.methodName().
- Adjust mocks, return values, and DTO inputs so they exactly match the actual definitions in the base file. Do not invent or assume fields.
- Remove tests that mock or spy on native/global prototypes such as `String.prototype`, `Array.prototype`, `Object.prototype`, `Date.prototype`, `Promise.prototype`, or `Error.prototype`; replace them with realistic behavior tests.
- If the error mentions `source-map`, `source-map-support`, `prepareStackTrace`, or `Cannot read properties of undefined (reading 'length')`, check for native/global prototype mocks first, especially `jest.spyOn(String.prototype, 'split')`, and remove them.
- For repository or axios mocks, ensure all required properties/methods exist.
- When mocking axios interceptors, always include at least the methods `use`, `eject`, and `clear`, each as a jest.fn().
  Example:
  interceptors: {{
    request: {{ use: jest.fn(), eject: jest.fn(), clear: jest.fn() }},
    response: {{ use: jest.fn(), eject: jest.fn(), clear: jest.fn() }},
  }}
- Always import axios explicitly at the top of the test file if axios.create or axios is used anywhere.
- Ensure interceptor `.use` is declared as a jest.fn() so that `.use.mock` is always available for assertions.
- If strict typing errors persist for axios mocks (headers, interceptors, defaults), always cast the mock objects to `any` so the spec compiles.


Strict Rules:
- Do not redefine or re-export the class under test inside the spec file. Always import it from the base file.
- Do not merge declarations (e.g., re-declaring a service/guard inside the test).
- Do not add new NestJS @Injectable() classes, DTOs, or entities inside the test file.
- Do not duplicate or overwrite imports with local definitions.
- Never mock framework classes (e.g., AuthGuard, ExecutionContext) in a way that breaks inheritance.
- If a class under test extends from a NestJS or Passport class (e.g., AuthGuard(...)), do not replace that dependency with a plain object. Keep the original class, or replace it with a valid class constructor when mocking.

Critical TypeScript Errors
- JavaScript Hoisting Fix:
  If you see "Cannot access 'X' before initialization" in jest.mock() calls:
  DO NOT use const/let variables inside jest.mock() 
  Instead, inline the mock implementation directly:
  
  // WRONG:
  const mockFunction = jest.fn();
  jest.mock('someModule', () => ({{ method: mockFunction }}));
  
  // CORRECT:
  jest.mock('someModule', () => ({{
    method: jest.fn(() => expectedReturn)
  }}));
- Axios Type Issues:
  For "Type '{{ common: any; }}' is not assignable" errors, use proper Axios types:
  ```javascript
  // WRONG:
  defaults: {{
    headers: {{
      common: {{}}}} as Record<string, any>,
    }},
  }}

  // CORRECT:
  defaults: {{
    headers: {{
      common: {{}},
      delete: {{}},
      get: {{}},
      head: {{}},
      post: {{}},
      put: {{}},
      patch: {{}},
    }} as any,
  }}
  ```

Output:
- Always return the entire corrected test file. If no fixes are required, return the same content verbatim.
- Do not include explanations, comments, or delimiters — just the raw test code.
"""

DELETE_FILE_CONTENT = """Consider the following test code in NodeJS:
```{result_ext}
{node_test_code}
```

And consider the following errors that happened upon executing the unity tests in the file:
```shell
{node_test_errors}
``` 
Analyse the reason behind the erros that happened and, based on your analysis, return the result as a file with the unity tests in {result_ext}, removing, adding or altering the lines of code to fix the errors founded.

Return only the file content, there's no need to use delimitators or explanations about the generated file
"""

VALIDATE_EXISTING_TEST = """You are validating a Jest unit test file for a NestJS project.

The unit tests file is `{test_file_path}`:
```
{node_test_code}
```

It was generated to test the following source file:
```
{base_file_code}
```

Your task:
- Verify if every functionality in the source file is covered in the unit tests file

Output:
- You should answer only `Yes` or `No`:
  - `Yes` if all the functionalities in the source file are covered in the unit tests file
  - `No` if there's at least one functionality in the source file not covered in the unit tests file
"""

INCREASE_JEST_COVERAGE_USER_NODE = """You need to improve the test coverage of this unit test.

Currently, the following test file `{test_file_path}`:
```ts
{test_file_code}
```

For this source file `{source_file_path}`
```ts
{source_file_code}
```

Has a coverage of {stmts_coverage}% statements and {brnc_coverage}% branches.
I need this coverage to be at least {target_coverage}%.

The coverage report explicitly marked these branch snippets as not covered:
```txt
{uncovered_branches}
```

### GOAL
- Improve the test file coverage so that the coverage is above the minimum required.
- Prioritize the uncovered branch snippets listed above, especially when branch coverage is below the target.
- Add only the minimum focused tests needed to cover uncovered branches.

### RESTRICTIONS
- Don't make any changes in the existing test cases, just create new test cases and anything necesary for those new test cases to run.
- Do not add broad or duplicated tests that do not target uncovered lines or branches.
- Prefer focused tests for `else`, `??`, `||`, optional chaining, switch cases, and fallback returns.
- Do not mock or spy on native/global prototypes such as `String.prototype`, `Array.prototype`, `Object.prototype`, `Date.prototype`, `Promise.prototype`, or `Error.prototype`.
- If an uncovered branch can only be reached by changing native/global prototype behavior (for example forcing `String.prototype.split` to return `[]` or `[undefined]`), skip that artificial branch. Prefer Stryker-compatible, realistic tests even if branch coverage remains below the target.

### PROCESS
- Based on the existing test file, analyse the source file to see which statements and branches are not covered
  - For the branches, make sure that every conditional like `PaymentGroupCode: groupCode ? Number(groupCode) : undefined,` or `errorCode: error.status ?? 404,` or `errorMessage: error.message ?? 'Generic Error',` is covered for each branch of result
- Create new test cases to cover the uncovered statements and branches.
"""
