import os
import re

templates_dir = "cashflex_app/templates"

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Captura /static/... com ou sem aspas
            new_content = re.sub(
                r'([\'"]?)/static/([^\'">\s]+)([\'"]?)',
                r'{{ url_for(\'static\', filename=\'\2\') }}',
                content
            )

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"✔ Corrigido: {path}")

