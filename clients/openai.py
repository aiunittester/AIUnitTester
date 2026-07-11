from decouple import config
from openai import OpenAI

API_KEY = config("OPENAI_API_KEY")


class OpenAIClient:
    def __init__(self):
        self.openai_client = OpenAI(api_key=API_KEY)
        self.history = []
        self.temp = 1
        self.model = "gpt-5.2-2025-12-11"
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def _track_usage(self, response) -> None:
        usage = getattr(response, "usage", None)
        if not usage:
            return

        self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0) or 0
        self.completion_tokens += getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0) or 0
        self.total_tokens += getattr(usage, "total_tokens", 0) or 0

    def completion( self ) -> str:
        if "codex" not in self.model:
            # chat usage
            chat_completions = self.openai_client.chat.completions.create(
                messages=self.history,
                model=self.model,
                temperature=self.temp
            )
            self.calls+=1
            self._track_usage(chat_completions)
            return chat_completions.choices[0].message.content
        else:
            #codex usage
            #TODO: ainda precisa adaptar, não está funcionando certinho
            # precisa atualizar o pacote da openai para algo >2.x
            # eu tentei trocar mas começou a quebrar o completions tbm 
            response = self.openai_client.responses.create(
                model=self.model,
                input=self.history,
                temperature=self.temp
            )

        self.calls += 1
        self._track_usage(response)
        return response.output_text

    def upload_file(self, file_src: str, purpose: str):
        """
        - file_src: caminho do arquivo
        - purpose: uma das seguintes opções:
            - assistants: Used in the Assistants API 
            - batch: Used in the Batch API 
            - fine-tune: Used for fine-tuning 
            - vision: Images used for vision fine-tuning 
            - user_data: Flexible file type for any purpose 
            - evals: Used for eval data sets

        Envia um arquivo para a openai e 
        retorna o objeto do arquivo enviado
        """
        res = self.openai_client.files.create(
            file=open(file_src, "rb"),
            purpose=purpose
        )

        return res
    
    def get_all_files(self):
        """
        Retorna uma lista com todos os arquivos
        que foram enviados a openai
        """
        return self.openai_client.files.list()
    
    def get_file(self, file_id: str):
        """
        - file_id: id do arquivo

        Retorna um arquivo específico
        """
        return self.openai_client.files.retrieve(file_id)
    
    def get_file_content(self, file_id: str):
        """
        - file_id: id do arquivo

        Retorna uma lista com o conteúdo de um arquivo específico
        """
        res = self.openai_client.files.content(file_id)

        content_bytes = res.read()
        content_str = content_bytes.decode("utf-8")
        content_list = content_str.split("\n")

        return content_list
    
    def delete_file(self, file_id: str):
        """
        - file_id: id do arquivo

        Deleta um arquivo específico e
        retorna o status da operação
        """
        return self.openai_client.files.delete(file_id)

    def create_fine_tuning_job(self, file_id: str):
        """
        - file_id: id do arquivo na openai
        """
        job = self.openai_client.fine_tuning.jobs.create(
            training_file=file_id,
            model="gpt-4o-mini-2024-07-18"
        )

        return job
    
    def get_all_jobs(self):
        """
        Retorna uma lista com todos os jobs de fine-tuning
        """
        return self.openai_client.fine_tuning.jobs.list()
    
    def get_latest_job(self):
        """
        Retorna o último job de fine-tuning
        """
        return self.openai_client.fine_tuning.jobs.list(limit=1)
    
    def get_job(self, job_id: str):
        """
        - job_id: id do job

        Retorna um job específico
        """
        return self.openai_client.fine_tuning.jobs.retrieve(job_id)
    
    def cancel_job(self, job_id: str):
        """
        - job_id: id do job

        Cancela um job específico e
        retorna o status da operação
        """
        return self.openai_client.fine_tuning.jobs.cancel(job_id)
