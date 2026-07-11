from email.message import EmailMessage
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from upload_zip import upload_to_dropbox

smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
username = os.getenv("SMTP_USERNAME")
password = os.getenv("SMTP_PASSWORD")

from_email = username
to_email = [addr.strip() for addr in os.getenv("REPORT_RECIPIENTS", "").split(",") if addr.strip()]
project_name = os.getenv("PROJECT_DIR") or os.getenv("MAIN_PROJECT_NAME") or "project"
subject = f"📊 Report Jest - Coverage - {project_name}"

msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = ", ".join(to_email)
msg['Subject'] = subject
# fpath = f'{os.getenv("PROJECT_DIR", "project")}/coverage/lcov-report/index.html'
# if not os.path.exists(fpath):
#     print(f"❌ O arquivo {fpath} não foi encontrado.")
#     fpath = f'{os.getenv("PROJECT_DIR", "project")}/coverage/index.html'
# else:
#     with open(fpath, 'r', encoding='utf-8') as file:
#         attachment = MIMEText(file.read(), 'html')
#         attachment.add_header('Content-Disposition', 'attachment', filename='index.html')
#         msg.attach(attachment)
links, report_id = upload_to_dropbox()
body = f"""Seguem os links para os relatórios da última execução do AIUnitTester 🤖\n\n
Identificador dessa execução é {report_id}\n

🔗 Link público: {links[0]}\n
🔗 Link download direto: {links[1]}
"""
msg.attach(MIMEText(body, 'plain'))

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(username, password)
server.send_message(msg)
server.quit()

print("✅ E-mail enviado com sucesso!")
try:
    os.remove("./files.zip")
    print(f"🗑️ Arquivo .zip deletado.")
except Exception as e:
    print(f"🗑️ Arquivo .zip não pode ser deletado: {e}")
