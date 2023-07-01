import json
import os
import re

if __name__ == '__main__':
    regex = "using .* = .*;.*"
    depara = {

    }

    for root, dirs, files in os.walk(
            "PATH"
    ):
        for file in files:
            file_path = os.path.join(root, file)

            if '/test/' in file_path or 'moc_' in file_path:
                continue

            if file_path.endswith(".h"):
                alias = []

                with open(file_path, 'r') as arquivo:
                    for line in arquivo:
                        match = re.match(regex, line)
                        if match:
                            line = line[line.index(' ') + 1:]
                            line = line[0:line.index(' ')]
                            alias.append(line)

                if len(alias) > 0:
                    name_include = file_path[file_path.rindex('/') + 1:]
                    name_include = name_include[0:name_include.index('.')]
                    depara[name_include] = alias

    with open("arquivo.json", 'w') as json_file:
        json.dump(depara, json_file, indent=True)
