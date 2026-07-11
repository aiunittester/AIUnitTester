import logging
import datetime
import os

os.makedirs("logs", exist_ok=True)

# logging.basicConfig(
#     filename=f"logs/{datetime.datetime.now().date()}.log",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     datefmt="%d-%m-%y %H:%M:%S"
# )

main_handler = logging.FileHandler(f"logs/{datetime.datetime.now().date()}.log", "w", encoding='utf-8')
main_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

main_logger = logging.getLogger()
main_logger.setLevel(logging.DEBUG)
main_logger.addHandler(main_handler)
